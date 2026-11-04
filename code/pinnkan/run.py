"""Run writer and driver:  python -P -m pinnkan.run --config <json|yaml>   (from ROOT, CPU only, 1 thread)

Modes
  inner         tuning + out-of-fold scores on TRAINING conditions only (this is what smoke runs use). No outer test cell is ever built.
  timing        one fit per arm at default settings, no scoring, no predictions (forced for Samsung before the FROZEN flag: retention blinding, prereg 3.3(9))
  confirmatory  tune on training conditions -> tuning_done.json + margins_inputs.json -> refit seeds on the full training side -> predict and score the
                outer test cells. Real datasets: needs runs/prereg/FROZEN (guard) and refuses the PROVISIONAL A10 form. Synthetic data have no outer test fold.

Run record (runs/<run_id>/): config.json, env.json, git.json (commit + dirty files), split.json (file, sha256, fold-hash check), manifest.json (inputs: path, size,
sha256), seeds.json, guard.json, tuning_<arm>.json, tuning_done.json, margins_inputs.json, timings.json, metrics.json, condition_scores.json,
predictions.csv (phase, arm, seed, cell, cond, t, pred, true), RUN.log.
"""
import argparse
import csv
import dataclasses
import json
import os
import platform
import subprocess
import sys
import time

import numpy as np
import torch

from . import ROOT as _ROOT
from . import emit, guard, h7, law, margins, metrics, negcontrol, semi, stats_step, synth, tuning
from .arms import ARMS, H1B_POOL, NEURAL, default_hp, make_arm
from .data import WindowRule, load_split, prepare_many, sha256_file
from .law import TAU
from .specs import SPECS

torch.set_num_threads(1)

DEFAULTS = {"mode": "inner", "test": "B", "fold": 0, "arms": ["A1", "A2", "A9", "R1", "R2"], "seeds": [0, 1, 2, 3, 4], "n_trials": 20, "inner_k": 3,
            "backbone": "self_limiting", "steps_scale": 1.0, "window": {}, "oracle_throughput": False, "per_cell_factor": True, "twins": "auto",
            "refit_timing": False, "overwrite": False, "retain_all": False, "throughput": "analytic", "target_kind": None, "auto_budget": False, "permute_stress": False, "pinn": {}, "diagnostics": True, "mc_seed_root": negcontrol.MC_SEED_ROOT, "nc1_scramble_test": False,
            # sensitivity-row options (PREREG 9.8; default = the primary analysis). include_at: AT check-ups join the forecast set (i); include_storage_0406: storage
            # cells 04-06 as two-point records (i); min_fc_points: scored cells need this many forecast points (i, "cells with >= 3 forecast points" -> 3);
            # law_overrides: {Y0, gamma, tau} for the A2-only tournament row (m), {delta_scope: "total"} for row (l); throughput_fallback: "analytic" lets a
            # cycling cell without ZYK entries use the designed throughput under throughput="zyk" (otherwise ZykDataMissing)
            "include_at": False, "include_storage_0406": False, "min_fc_points": 1, "law_overrides": {}, "throughput_fallback": "none", "forecast_failure": False, "lab_indicator": False}
TARGET_BY_TEST = {"B": "cycling", "C": "cycling", "A": "cycling", "S2": "storage", "S3": "storage"}   # the tuned task is the scored task (review M3)


class ConfigError(RuntimeError):
    pass


class DeviceError(RuntimeError):
    pass


class ScoredRunError(RuntimeError):
    """an outer-test-scored run would be replaced or repeated (stop rules 4 and 6)"""


def git_info(root):
    def g(*a):
        try:
            return subprocess.run(["git", *a], cwd=root, capture_output=True, text=True, timeout=30).stdout.strip()
        except Exception as e:  # noqa: BLE001
            return f"unavailable: {e}"
    dirty = [l for l in g("status", "--porcelain").splitlines()]
    return {"commit": g("rev-parse", "HEAD"), "branch": g("rev-parse", "--abbrev-ref", "HEAD"), "dirty_files": dirty[:300], "n_dirty": len(dirty),
            "dirty_code": [l for l in dirty if "code/" in l.replace("\\", "/")]}


def env_info():
    import optuna, scipy, sklearn  # noqa: E401
    return {"python": sys.version.split()[0], "platform": platform.platform(), "torch": torch.__version__, "numpy": np.__version__, "scipy": scipy.__version__,
            "sklearn": sklearn.__version__, "optuna": optuna.__version__, "torch_threads": torch.get_num_threads(),
            "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"), "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS"),
            "cuda_available": bool(torch.cuda.is_available()), "interpreter": sys.executable}


def _json(path, obj):
    def default(o):
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
        return str(o)
    with open(path, "w", encoding="utf8") as fh:
        json.dump(obj, fh, indent=1, default=default)


def strip_rows(rows):
    return [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]


def twins_from_conditions(conds):
    """(T, SOC_mid) of cycling condition keys 'T35|SOCmax0.55|DoD0.25|Cch..|Cdch..' (identifiers only; label-free)"""
    out = []
    for c in conds:
        p = c.split("|")
        if len(p) == 5:
            T, smax, dod = float(p[0][1:]), float(p[1][6:]), float(p[2][3:])
            out.append((T, smax - dod / 2.0))
    return out


class Recorder:
    def __init__(self, run_dir, run_id):
        self.dir, self.run_id = run_dir, run_id
        self.pred_rows = []
        self.log_fh = open(os.path.join(run_dir, "RUN.log"), "a", encoding="utf8")

    def log(self, msg):
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        self.log_fh.write(line + "\n")
        self.log_fh.flush()

    def add_preds(self, phase, arm, seed, rows):
        for r in rows:
            for t, p, y in zip(r["_t"], r["_pred"], r["_true"]):
                self.pred_rows.append((phase, arm, seed, r["cell"], r["cond"], float(t), float(p), float(y)))

    def flush_preds(self):
        if not self.pred_rows:
            return
        with open(os.path.join(self.dir, "predictions.csv"), "w", newline="", encoding="utf8") as fh:
            w = csv.writer(fh)
            w.writerow(["phase", "arm", "seed", "cell_id", "cond", "t", "pred_retention", "true_retention"])
            w.writerows(self.pred_rows)


def build_data(cfg, root, role):
    """-> dict(spec, train, test, split_info, manifest). role 'train' never builds an outer-test cell."""
    ds = cfg["dataset"]
    if ds == "synthetic":
        sc = cfg.get("synthetic", {})
        S = synth.make_synthetic(sc.get("kind", "G0"), sc.get("n_cyc_cond", 20), sc.get("n_sto_cond", 8), sc.get("reps", 2), sc.get("seed", 0))
        tr, te = synth.split_synthetic(S.cells, cfg["test"], sc.get("test_frac", 0.25), sc.get("seed", 0))
        return {"spec": SPECS["synthetic"], "train": tr, "test": te if role != "train" else None, "synth": S,
                "split": {"file": "synthetic (generated)", "note": "no outer test fold of real data exists"}, "manifest": []}
    sv = load_split(ds, cfg["test"], cfg["fold"], role=role, root=root, retain_all=cfg["retain_all"], throughput=cfg["throughput"], include_at=cfg["include_at"],
                    throughput_fallback=cfg["throughput_fallback"], include_storage_0406=cfg["include_storage_0406"])
    return {"spec": sv.spec, "train": sv.train, "test": sv.test_cells, "sv": sv,
            "split": {"file": os.path.relpath(sv.split_file, root).replace("\\", "/"), "sha256_file": sv.split_sha256, "fold_hash_stored": sv.fold_hash_stored,
                      "fold_hash_recomputed": sv.fold_hash_recomputed, "fold_hash_ok": sv.hash_ok, "pinned_at_freeze": sv.pinned, "missing_train_conditions": sv.missing_train_conditions, "test_conditions": sv.test_conditions,
                      "n_train_cells": len(sv.train), "n_train_conditions": len(sv.train_conditions)}, "manifest": sv.input_files}


class NotBuiltError(RuntimeError):
    """a preregistered option that cannot be built faithfully from the text (listed in RESULT.md section 7 for the lead: strike or specify before the freeze)"""


LAW_OVERRIDE_ARMS = {"tau": {"A2"}, "Y0": {"A2"}, "gamma": {"A2"}, "delta_scope": {"A1"}}   # rows (m) and (l): the arms the prereg names


def run(cfg_in, root=None, runs_dir=None):
    cfg = {**DEFAULTS, **cfg_in}
    if cfg["forecast_failure"]:
        raise NotBuiltError("forecast_failure (PREREG 3.3(8)): the rule scores cells whose record ends inside the window 'as forecast failures (retention carried forward "
                            "from the last observation)', but the text gives no forecast times for a cell without post-window check-ups, so the scored set is undefined. "
                            "Specify the forecast times (or strike the row) before the freeze.")
    if cfg["lab_indicator"]:
        raise NotBuiltError("lab_indicator (PREREG 9.8(f), the lab-indicator rows for A1, A9, A12 on Test B and Test C): the text says 'a lab indicator in the per-cell prior/inputs' "
                            "without fixing where it enters each arm (prior mean of delta_c / z_c for A1 and A9, an input column for A12), the coding of the three laboratories or the "
                            "reference level; building one reading would be a guess. Specify the construction (or strike the row) before the freeze.")
    lo = {k: v for k, v in (cfg.get("law_overrides") or {}).items() if v is not None}
    if lo:
        bad = set(lo) - set(LAW_OVERRIDE_ARMS)
        if bad:
            raise ConfigError(f"unknown law_overrides {sorted(bad)}; allowed {sorted(LAW_OVERRIDE_ARMS)}")
        allowed = set.union(*[LAW_OVERRIDE_ARMS[k] for k in lo]) | {"R1", "R2"}
        extra = set(cfg["arms"]) - allowed
        if extra:
            raise ConfigError(f"law_overrides {sorted(lo)} are sensitivity rows of the arm(s) {sorted(set.union(*[LAW_OVERRIDE_ARMS[k] for k in lo]))} only; remove {sorted(extra)}")
        with law.overrides(Y0=lo.get("Y0"), gamma=lo.get("gamma"), tau=lo.get("tau"), delta_scope=lo.get("delta_scope")):
            return _run(cfg_in, root, runs_dir)
    return _run(cfg_in, root, runs_dir)


def _run(cfg_in, root=None, runs_dir=None):
    cfg = {**DEFAULTS, **cfg_in}
    if torch.cuda.is_available():            # D013 C4: a wrong environment must not silently produce GPU numbers
        raise DeviceError("CUDA is available to torch: runs are CPU only (CUDA_VISIBLE_DEVICES=-1 is forced by the package); no GPU use without the lead's instruction")
    root = root or _ROOT
    runs_dir = runs_dir or os.path.join(root, "runs")
    run_id = cfg["run_id"]
    run_dir = os.path.join(runs_dir, run_id)
    ds, mode = cfg["dataset"], cfg["mode"]
    if cfg["permute_stress"] and cfg["test"] != "B":
        raise ConfigError("permute_stress (NC-2) is defined on Test B only, not on Test C (NEGCONTROL_RULING section 3)")
    if cfg["mc_seed_root"] != negcontrol.MC_SEED_ROOT:
        raise ConfigError("mc_seed_root is fixed by the NEGCONTROL ruling (20261105)")
    tk = TARGET_BY_TEST.get(cfg["test"], "cycling")
    if cfg.get("target_kind") not in (None, tk):
        raise ConfigError(f"target_kind {cfg['target_kind']!r} contradicts test {cfg['test']!r} (scored kind is {tk!r})")
    cfg["target_kind"] = tk
    chash = None
    if mode == "confirmatory" and ds != "synthetic":      # checks before anything is created or read (review M2)
        if cfg["steps_scale"] != 1.0:
            raise ConfigError("steps_scale != 1 is not allowed in a confirmatory run on real data")
        if cfg["overwrite"]:
            raise ConfigError("overwrite is not allowed in a confirmatory run on real data (stop rule 4)")
        guard.require_frozen("confirmatory run", root)
        chash = guard.check_config_frozen({**DEFAULTS, **cfg_in}, root)     # hash of the config as written (DEFAULTS + file keys)
    if os.path.exists(run_dir):
        if os.path.exists(os.path.join(run_dir, "condition_scores.json")):
            raise ScoredRunError(f"{run_dir} holds a scored outer-test run; it is never replaced")
        if not cfg["overwrite"] and not (mode == "h7" and (cfg.get("h7") or {}).get("resume")):      # the H7 batch is resumable and shared by up to three shard processes
            raise FileExistsError(run_dir)
    os.makedirs(run_dir, exist_ok=True)
    blinded = ds == "samsung" and not guard.is_valid_freeze(root)
    if mode == "nc1_full":                                    # mandatory pre-freeze check: whole pipeline with scrambled test labels (synthetic only)
        if ds != "synthetic":
            raise ConfigError("mode nc1_full is synthetic only")
        base = {k: v for k, v in cfg.items() if k not in ("run_id", "mode", "overwrite")}
        dA = run({**base, "run_id": run_id + "_clean", "mode": "confirmatory", "nc1_scramble_test": False}, root=root, runs_dir=runs_dir)
        dB = run({**base, "run_id": run_id + "_scrambled", "mode": "confirmatory", "nc1_scramble_test": True}, root=root, runs_dir=runs_dir)
        res = negcontrol.compare_runs(dA, dB)
        _json(os.path.join(run_dir, "config.json"), cfg)
        _json(os.path.join(run_dir, "nc1_full.json"), {**res, "clean_run": dA, "scrambled_run": dB})
        if not res["passed"]:
            raise negcontrol.InvarianceError(f"NC-1 full pipeline: {res}")
        return run_dir
    if mode == "h7":                                        # identifiability driver, synthetic only (PREREG_v2 13)
        if ds != "synthetic":
            raise ConfigError("mode h7 is synthetic only")
        shard = (cfg.get("h7") or {}).get("shard") or [0, 1]
        _json(os.path.join(run_dir, "config.json" if shard == [0, 1] or not os.path.exists(os.path.join(run_dir, "config.json")) else f"config_shard{shard[0]}of{shard[1]}.json"), cfg)
        hk = {k: v for k, v in (cfg.get("h7") or {}).items() if k in ("gens", "n_draws", "arms", "n_trials", "inner_k", "steps_scale", "design", "shard", "arms_by_gen")}
        if "shard" in hk:
            hk["shard"] = tuple(hk["shard"])
        h7.run_h7(run_dir, backbone=cfg["backbone"] if cfg["backbone"] != "tournament" else "self_limiting", **hk)
        return run_dir
    if blinded and mode not in ("timing", "confirmatory"):
        mode = "timing"        # retention blinding before the freeze: no retention-derived number is written under runs/
        # (a confirmatory request is NOT downgraded: it goes to the guard, which refuses it)
    rec = Recorder(run_dir, run_id)
    if ds == "synthetic":
        open(os.path.join(run_dir, "SYNTHETIC"), "w").write("synthetic data: invented ageing laws, not results\n")
    guard.GUARD_LOG.clear()
    t_start = time.time()
    _json(os.path.join(run_dir, "config.json"), {**cfg, "mode_effective": mode, "blinded_samsung_pre_freeze": blinded})
    _json(os.path.join(run_dir, "env.json"), env_info())
    _json(os.path.join(run_dir, "git.json"), git_info(root))
    _json(os.path.join(run_dir, "seeds.json"), {"final_refit_seeds": cfg["seeds"], "tuning_seed": "1000 + outer fold", "tpe_sampler_seed": "outer fold",
                                                "mc_seed_root": cfg["mc_seed_root"], "mc_seed_rule": "np.random.default_rng(SeedSequence([root, zlib.crc32(label)])) for every Monte Carlo step; labels such as 'B|H1a|BCa_mean_pp' are listed in the contrasts files",
                                                "permute_stress_stream": "[20261107, 31, fold] (train), fold + 1000 (test)", "nc1_scramble_stream": "mc_rng('NC1|' + cell_id)"})
    role = "test" if mode == "confirmatory" else "train"
    D = build_data(cfg, root, role)          # the test-fold guard is inside load_split (role != 'train')
    spec, train = D["spec"], D["train"]
    if mode == "confirmatory" and D.get("sv") is not None and D["sv"].missing_train_conditions:
        raise ConfigError(f"incomplete training set, missing conditions {D['sv'].missing_train_conditions[:3]} (complete download required)")
    if cfg["permute_stress"]:                              # negative control: separate permutations of train and test stress vectors
        train = metrics.permute_stress(train, spec, cfg["fold"])
        if D["test"] is not None:
            D["test"] = metrics.permute_stress(D["test"], spec, cfg["fold"] + 1000)
    _json(os.path.join(run_dir, "split.json"), D["split"])
    _json(os.path.join(run_dir, "manifest.json"), D["manifest"])
    rec.log(f"run {run_id}: dataset {ds} test {cfg['test']} fold {cfg['fold']} mode {mode} (requested {cfg['mode']}) blinded={blinded}")
    rec.log(f"train cells {len(train)}: {sum(c.kind == 'cycling' for c in train)} cycling, {sum(c.kind == 'storage' for c in train)} storage; conditions {len({c.cond for c in train})}")
    if D["split"].get("missing_train_conditions"):
        rec.log(f"NOTE: {len(D['split']['missing_train_conditions'])} training conditions of the split have no cells on disk (partial download)")
    wk = cfg["window"]
    rule = WindowRule.for_spec(spec, k_cycling=wk.get("k_cycling"), k_storage=wk.get("k_storage"), W=wk.get("W"), shift=wk.get("shift", 0))
    rule_test = dataclasses.replace(rule, min_fc_points=int(cfg["min_fc_points"]))      # scored cells only (sensitivity row "cells with >= 3 forecast points"); training windows keep `rule`
    if cfg["nc1_scramble_test"]:
        if ds != "synthetic" or D["test"] is None:
            raise ConfigError("nc1_scramble_test is for synthetic confirmatory runs only")
        D["test"] = negcontrol.scramble_cells(D["test"], rule_test, spec)
    extra = None
    if (cfg["twins"] == "c35") or (cfg["twins"] == "auto" and cfg["test"] == "C" and ds == "samsung"):
        extra = twins_from_conditions(D["split"].get("test_conditions", []))
    ctx = {"backbone": cfg["backbone"] if cfg["backbone"] != "tournament" else "self_limiting", "steps_scale": cfg["steps_scale"], "rule": rule, "extra_twin_raw": extra,
           "oracle": cfg["oracle_throughput"], "per_cell_factor": cfg["per_cell_factor"], "a10_starts": cfg.get("a10_starts", 8), "pinn": cfg["pinn"]}
    arms = list(cfg["arms"])
    if mode == "confirmatory" and ds != "synthetic" and "A10" in arms:
        semi.require_verified()
    timings, metrics_out = {}, {"blinded": blinded, "mode": mode}
    if mode != "timing":
        metrics_out["n_train_cells"] = len(train)
        metrics_out["n_train_scorable_cells"] = len(prepare_many(train, rule))      # A11/A12 train only on these (review m6)
    # ---------------------------------------------------------------- timing (and Samsung before the freeze)
    if mode == "timing":
        for a in arms:
            t0 = time.time()
            arm = make_arm(a, spec, default_hp(a) if ARMS[a].tuned else {}, 1000 + cfg["fold"], ctx).fit(train)
            timings[a] = {"fit_seconds": time.time() - t0, "n_params": int(arm.n_params), "n_train_used": arm.n_train_used}
            rec.log(f"timing {a}: {timings[a]['fit_seconds']:.1f} s, {arm.n_params} parameters")
        metrics_out["note"] = "timing only; no scoring, no predictions (retention blinding before the freeze)" if blinded else "timing only"
        _json(os.path.join(run_dir, "timings.json"), timings)
        _json(os.path.join(run_dir, "metrics.json"), metrics_out)
        _json(os.path.join(run_dir, "guard.json"), guard.GUARD_LOG)
        rec.log(f"done in {time.time() - t_start:.0f} s")
        return run_dir
    # ---------------------------------------------------------------- tuning on training conditions
    if cfg["auto_budget"]:                                  # N and inner folds are fixed BEFORE tuning from one timing fit per neural arm (review m8)
        med = {}
        for a in arms:
            if a in NEURAL:
                t0 = time.time()
                make_arm(a, spec, default_hp(a) if ARMS[a].tuned else {}, 1000 + cfg["fold"], ctx).fit(train)
                med[a] = time.time() - t0
        bud = tuning.choose_budget(med)
        cfg["n_trials"], cfg["inner_k"] = bud["n_trials"], bud["inner_k"]
        _json(os.path.join(run_dir, "budget_rule.json"), {**bud, "median_fit_seconds": med})
        rec.log(f"budget fixed before tuning: {bud}")
    if cfg["backbone"] == "tournament":
        tb = tuning.backbone_tournament(train, spec, rule, cfg["inner_k"], cfg["fold"], ctx, tk)
        ctx["backbone"] = tb["chosen"]
        _json(os.path.join(run_dir, "backbone_tournament.json"), tb)
        rec.log(f"backbone tournament: chosen {tb['chosen']} (best {tb['best']})")
    tuned = {}
    for a in arms:
        t0 = time.time()
        r = tuning.tune(a, train, spec, rule, cfg["n_trials"], cfg["inner_k"], cfg["fold"], ctx, tk)
        tuned[a] = r
        timings[a] = {"tuning_seconds": time.time() - t0, "median_fit_seconds": r["median_fit_seconds"], "n_trials": r["n_trials"], "n_failed": r["n_failed"]}
        rec.add_preds("inner_oof", a, 1000 + cfg["fold"], r["rows"])
        _json(os.path.join(run_dir, f"tuning_{a}.json"), {k: (strip_rows(v) if k == "rows" else v) for k, v in r.items()})
        rec.log(f"tuned {a}: inner-CV {r['inner_cv_pp']:.3f} pp, best {r['best_hp']}, median fit {r['median_fit_seconds']:.1f} s, failed {r['n_failed']}")
    inner = {a: {"inner_cv_pp": tuned[a]["inner_cv_pp"], "cond_scores": tuned[a]["cond_scores"], "best_hp": tuned[a]["best_hp"]} for a in arms}
    _json(os.path.join(run_dir, "tuning_done.json"), {"backbone": ctx["backbone"], "arms": inner, "budget": {"n_trials": cfg["n_trials"], "inner_k": cfg["inner_k"]}})
    metrics_out["inner_cv_pp"] = {a: inner[a]["inner_cv_pp"] for a in arms}
    if cfg["diagnostics"]:
        diag, diag_arms = diagnostics(arms, tuned, train, spec, ctx, cfg["fold"])
        _json(os.path.join(run_dir, "diagnostics.json"), diag)
        metrics_out["diagnostics_file"] = "diagnostics.json"
        rec.log("diagnostics: " + json.dumps({a: {k: round(v, 3) for k, v in d.items() if isinstance(v, float)} for a, d in diag["arms"].items()}))
    metrics_out["backbone"] = ctx["backbone"]
    if cfg["refit_timing"]:
        for a in arms:
            t0 = time.time()
            arm = make_arm(a, spec, tuned[a]["best_hp"], 0, ctx).fit(train)
            timings[a].update(refit_seconds=time.time() - t0, n_params=int(arm.n_params), n_train_used=arm.n_train_used)
    if mode == "inner":
        if cfg["diagnostics"]:
            scored_ids = {r["cell"] for a in arms for r in tuned[a]["rows"]}
            prep_in = [p for p in prepare_many(train, rule, oracle=cfg["oracle_throughput"]) if p.cell.cell_id in scored_ids]
            emit_artifacts(run_dir, rec, spec, train, [], {a: [x] for a, x in diag_arms.items()}, ctx["backbone"], prep_in)
        write_reference(run_dir, train, rule, blinded, cfg, rec)
        for a in arms:
            if tuned[a]["rows"]:
                metrics_out.setdefault("inner_nonfinite", {})[a] = int(sum(r["n_nonfinite"] for r in tuned[a]["rows"]))
        _finish(rec, run_dir, timings, metrics_out, t_start)
        return run_dir
    # ---------------------------------------------------------------- confirmatory: margins inputs, then refits and the outer test
    pool_best = min((a for a in H1B_POOL if a in inner), key=lambda a: inner[a]["inner_cv_pp"], default=None)
    n_test = len({c.cond for c in D["test"]})
    contr = {f"E_{a}": [[n_test, inner[a]["inner_cv_pp"]]] for a in arms}
    _json(os.path.join(run_dir, "margins_inputs.json"), {"per_arm_E_by_fold": contr, "h1b_comparator_by_inner_cv": pool_best,
                                                          "h1c_comparator_by_inner_cv": min((a for a in ("A11", "A12") if a in inner), key=lambda a: inner[a]["inner_cv_pp"], default=None),
                                                          "note": "margins.json is formed from these after all folds finish (stats step); tuning is complete before any test condition is scored"})
    margins.write_margins(os.path.join(run_dir, "margins.json"), contr)
    prep = prepare_many(D["test"], rule_test, oracle=cfg["oracle_throughput"])
    wc = [p.win for p in prep]
    if ds != "synthetic":
        guard.require_frozen("score outer test fold", root)      # the scoring side of the guard
        guard.record_scoring(chash, run_id, git_info(root)["commit"], root)     # a second scoring of the same config is refused
    bad = {c.kind for c in D["test"]} - {tk}
    if bad:
        raise ConfigError(f"test cells of kind {sorted(bad)} but the tuned and scored kind is {tk}")
    cond_scores_out, per_arm, cell_scores_out = {}, {}, {}
    fitted, inv_records = {}, {}
    for a in arms:
        per_seed_rows, per_seed_preds = [], []
        for s in cfg["seeds"]:
            t0 = time.time()
            arm = make_arm(a, spec, tuned[a]["best_hp"], s, ctx).fit(train)
            preds = arm.predict(wc)
            rows = metrics.score_prepared(preds, prep)
            per_seed_rows.append(rows)
            per_seed_preds.append(preds)
            inv_records[f"{a}|{s}"] = negcontrol.check_invariance(arm.predict, D["test"], rule_test, spec, cfg["oracle_throughput"], base_preds=preds, base_prepared=prep)
            if a in ("A1", "A2", "A4", "A10"):
                fitted.setdefault(a, []).append(arm)
            rec.add_preds("outer_test", a, s, rows)
            timings[a][f"refit_seed{s}_seconds"] = time.time() - t0
        cs, sd = metrics.seed_condition_scores(per_seed_rows)
        cond_scores_out[a] = cs
        cell_scores_out[a] = metrics.seed_cell_scores(per_seed_rows)
        per_arm[a] = {"primary_pp": float(np.mean(list(cs.values()))), "seed_sd_of_mean": sd, "n_conditions": len(cs),
                      "mae_pp_mean": float(np.mean([r["mae_pp"] for rows in per_seed_rows for r in rows])),
                      "n_nonfinite": int(sum(r["n_nonfinite"] for rows in per_seed_rows for r in rows)), "n_params": int(arm.n_params),
                      "n_train_used": arm.n_train_used, **outer_extras(prep, per_seed_preds, per_seed_rows)}
        rec.log(f"outer test {a}: {per_arm[a]['primary_pp']:.3f} pp (seed SD {sd:.3f}) over {len(cs)} conditions")
    metrics_out["outer_test"] = per_arm
    emit_artifacts(run_dir, rec, spec, train, prep, fitted, ctx["backbone"], prep)
    write_reference(run_dir, train, rule, blinded, cfg, rec)
    inv = negcontrol.summarise(inv_records)
    _json(os.path.join(run_dir, "invariance.json"), inv)
    metrics_out["nc1_invariance_passed"] = inv["passed"]
    if not inv["passed"]:
        open(os.path.join(run_dir, "GATE_G_TRIPPED"), "w").write("NC-1: predictions changed when held-out post-window labels were replaced by garbage (see invariance.json)\n")
        rec.log("GATE G TRIPPED (NC-1)")
        _finish(rec, run_dir, timings, metrics_out, t_start)
        raise negcontrol.InvarianceError(f"NC-1 label-invariance failed: max |diff| = {inv['max_abs_diff']} (see {run_dir}/invariance.json)")
    if cfg["permute_stress"]:
        metrics_out["permuted_stress_run"] = "NC-2 input: scored by stats_step.nc2 against the real Test B run (exact one-sided sign test)"
    _json(os.path.join(run_dir, "cell_scores.json"), cell_scores_out)                 # per scored cell: mean over seeds of the cell RMSE (two-stage bootstrap, sensitivity row (d))
    _json(os.path.join(run_dir, "condition_meta.json"), metrics.condition_meta(prep))  # identifiers only: scored cells, laboratory and stage per condition (rows (a)-(c))
    _json(os.path.join(run_dir, "condition_scores.json"), cond_scores_out)
    _finish(rec, run_dir, timings, metrics_out, t_start)
    return run_dir


LAM_GRID = ARMS["A1"].space["lam_res"][1]


def diagnostics(arms, tuned, train, spec, ctx, fold):
    """D013 C7, per fold: tuned lam_res and whether it sits on a grid edge; sd of the fitted delta_c on the training cells against TAU (flag outside [0.5, 2]);
    share of clipped steps (A1, A9 and the other gradient-trained arms). One refit per arm at its tuned settings, seed 0, training cells only."""
    out, lam_edges, kept = {}, [], {}
    for a in arms:
        hp = tuned[a]["best_hp"]
        d = {}
        if "lam_res" in hp:
            lo, hi = min(LAM_GRID), max(LAM_GRID)
            d.update(lam_res=hp["lam_res"], lam_res_at_lower_edge=bool(hp["lam_res"] == lo), lam_res_at_upper_edge=bool(hp["lam_res"] == hi))
            lam_edges.append(d["lam_res_at_lower_edge"] or d["lam_res_at_upper_edge"])
        if ARMS[a].family in ("pinn", "hard", "data"):
            arm = make_arm(a, spec, hp, 0, ctx).fit(train)
            d.update(arm.diagnostics())
            kept[a] = arm
        if d:
            out[a] = d
    return {"arms": out, "lam_res_edge_share_over_arms": (float(np.mean(lam_edges)) if lam_edges else None), "lam_res_grid": list(LAM_GRID), "tau": TAU,
            "outer_fold": fold, "tournament_table": "see backbone_tournament.json"}, kept


def emit_artifacts(run_dir, rec, spec, train, prep, fitted, backbone, window_prep):
    """window.csv for every run with scored cells; stress_functions.json, residual_map.npz, superposition.csv for datasets with a calendar term
    (Samsung layout) when the fitted A1 (and A2 / A4 / A10) models are available. `fitted`: {arm_id: [fitted arms]}."""
    try:
        _emit_artifacts(run_dir, rec, spec, train, prep, fitted, backbone, window_prep)
    except Exception as e:  # noqa: BLE001  (secondary artefacts must not destroy a scored run; the failure is recorded, not hidden)
        rec.log(f"EMIT FAILED: {type(e).__name__}: {e}")
        _json(os.path.join(run_dir, "emit_errors.json"), {"error": f"{type(e).__name__}: {e}"})


def _emit_artifacts(run_dir, rec, spec, train, prep, fitted, backbone, window_prep):
    if window_prep:
        emit.window_rows(window_prep).to_csv(os.path.join(run_dir, "window.csv"), index=False)
    if "A1" not in fitted or not emit.supports_calendar_maps(spec):
        rec.log("no stress_functions / residual_map / superposition: needs A1 and the Samsung stress layout with a calendar term")
        return
    a10 = fitted["A10"][0] if "A10" in fitted else None
    _json(os.path.join(run_dir, "stress_functions.json"), emit.stress_functions(fitted["A1"], spec, train, backbone, fitted.get("A4", ()), a10))
    np.savez(os.path.join(run_dir, "residual_map.npz"), **emit.residual_map(fitted["A1"], spec, train))
    one = {a: v[0] for a, v in fitted.items() if a in ("A1", "A2")}
    if prep and one:
        emit.superposition(one, prep, spec, backbone).to_csv(os.path.join(run_dir, "superposition.csv"), index=False)
    rec.log("emitted window.csv, stress_functions.json, residual_map.npz" + (", superposition.csv" if prep and one else ""))


def write_reference(run_dir, train, rule, blinded, cfg, rec):
    """training-side R_LOO / R_WARP for the stats step (descriptive). Not written for Samsung before a valid freeze (retention blinding)."""
    if blinded:
        return
    prep_tr = prepare_many(train, rule, oracle=cfg["oracle_throughput"])
    _json(os.path.join(run_dir, "reference_values.json"), stats_step.reference_values(prep_tr))


def outer_extras(prep, per_seed_preds, per_seed_rows, rul_level=0.8):
    """secondary metrics of prereg 6, seed means: pooled R^2, MAPE, error by horizon after the window, RUL error (cells whose truth crosses the level)"""
    r2 = float(np.mean([metrics.r2_pooled(p, prep) for p in per_seed_preds]))
    mape = float(np.mean([r["mape_pct"] for rows in per_seed_rows for r in rows]))
    hz = [metrics.horizon_errors([(metrics.clean_forecast(p[x.cell.cell_id], x.win.y_last)[0], x.fc_true) for x in prep]) for p in per_seed_preds]
    hmean = {h: {"rmse_pp": float(np.mean([d[h]["rmse_pp"] for d in hz])), "n": hz[0][h]["n"]} for h in hz[0]}
    rul = [[metrics.rul_error(x, metrics.clean_forecast(p[x.cell.cell_id], x.win.y_last)[0], rul_level) for x in prep] for p in per_seed_preds]
    vals = [[v for v in seed if v is not None] for seed in rul]
    return {"r2_pooled": r2, "mape_pct_mean": mape, "horizon_rmse_pp": hmean,
            "rul": {"level": rul_level, "n_cells_crossing": len(vals[0]),
                    "mean_abs_error_time_units": float(np.mean([np.mean(np.abs(v)) for v in vals if v])) if vals[0] else None}}


def _finish(rec, run_dir, timings, metrics_out, t_start):
    _json(os.path.join(run_dir, "timings.json"), timings)
    _json(os.path.join(run_dir, "metrics.json"), metrics_out)
    _json(os.path.join(run_dir, "guard.json"), guard.GUARD_LOG)
    rec.flush_preds()
    rec.log(f"done in {time.time() - t_start:.0f} s")


def load_config(path):
    txt = open(path, encoding="utf8").read()
    if path.endswith((".yaml", ".yml")):
        import yaml
        return yaml.safe_load(txt)
    return json.loads(txt)


def main(argv=None):
    ap = argparse.ArgumentParser(description="PINN-KAN confirmatory run writer")
    ap.add_argument("--config", required=True)
    ap.add_argument("--runs-dir", default=None)
    a = ap.parse_args(argv)
    run(load_config(a.config), runs_dir=a.runs_dir)


if __name__ == "__main__":
    main()
