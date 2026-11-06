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
from . import emit, guard, h7, inversion, inversion_diag, law, margins, metrics, negcontrol, selectors, semi, stats_step, subsets, synth, tuning
from .arms import ARMS, H1B_POOL, NEURAL, OUT_OF_SCOPE_ARMS, default_hp, make_arm
from .data import WindowRule, apply_subset, grid_ks, load_split, prepare_many, sha256_file, window_capped_cells
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
            "include_at": False, "include_storage_0406": False, "min_fc_points": 1, "m": None, "subset": "maxmin", "subset_draw": 0, "k": None, "design": "R2", "inversion_config_sha256": None, "inversion_diagnostics": None, "extraction_audit_sha256": None, "calibration_rule_sha256": None, "nc1_scramble_k": None, "symbolic": {}, "endpoint": "ensemble", "inner_k_thin": 2, "p6b_decision": None, "law_overrides": {}, "throughput_fallback": "none", "forecast_failure": False, "lab_indicator": False, "score_blinded_cells": False}
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


def build_data(cfg, root, role, runs_dir=None):
    """-> dict(spec, train, test, split_info, manifest). role 'train' never builds an outer-test cell."""
    ds = cfg["dataset"]
    if ds == "synthetic":
        sc = cfg.get("synthetic", {})
        S = synth.make_synthetic(sc.get("kind", "G0"), sc.get("n_cyc_cond", 20), sc.get("n_sto_cond", 8), sc.get("reps", 2), sc.get("seed", 0))
        tr, te = synth.split_synthetic(S.cells, cfg["test"], sc.get("test_frac", 0.25), sc.get("seed", 0))
        tr, sub = apply_subset(tr, "synthetic", cfg["test"], {}, cfg["fold"], cfg["m"], cfg["subset"], cfg["subset_draw"], ids={c.cond for c in tr if c.kind == "cycling"})
        return {"spec": SPECS["synthetic"], "train": tr, "test": te if role != "train" else None, "synth": S, "subset": sub,
                "split": {"file": "synthetic (generated)", "note": "no outer test fold of real data exists", "subset": sub}, "manifest": []}
    sv = load_split(ds, cfg["test"], cfg["fold"], role=role, root=root, retain_all=cfg["retain_all"], throughput=cfg["throughput"], include_at=cfg["include_at"],
                    throughput_fallback=cfg["throughput_fallback"], include_storage_0406=cfg["include_storage_0406"], m=cfg["m"], subset=cfg["subset"], subset_draw=cfg["subset_draw"], runs_dir=runs_dir, score_blinded_cells=cfg["score_blinded_cells"])
    return {"spec": sv.spec, "train": sv.train, "test": sv.test_cells, "sv": sv, "subset": sv.subset_info,
            "split": {"file": os.path.relpath(sv.split_file, root).replace("\\", "/"), "sha256_file": sv.split_sha256, "fold_hash_stored": sv.fold_hash_stored,
                      "fold_hash_recomputed": sv.fold_hash_recomputed, "fold_hash_ok": sv.hash_ok, "pinned_at_freeze": sv.pinned, "missing_train_conditions": sv.missing_train_conditions, "test_conditions": sv.test_conditions,
                      "n_train_cells": len(sv.train), "n_train_conditions": len(sv.train_conditions), "blinding_excluded_cells": sv.blinding_excluded}, "manifest": sv.input_files}


class NotBuiltError(RuntimeError):
    """a preregistered option that cannot be built faithfully from the text (listed in RESULT.md section 7 for the lead: strike or specify before the freeze)"""


LAW_OVERRIDE_ARMS = {"tau": {"A2"}, "Y0": {"A2"}, "gamma": {"A2"}, "delta_scope": {"A1"}}   # rows (m) and (l): the arms the prereg names


def run(cfg_in, root=None, runs_dir=None):
    cfg = {**DEFAULTS, **cfg_in}
    if cfg["forecast_failure"]:
        raise NotBuiltError("forecast_failure (PREREG 3.3(8)): the rule scores cells whose record ends inside the window 'as forecast failures (retention carried forward "
                            "from the last observation)', but the text gives no forecast times for a cell without post-window check-ups, so the scored set is undefined. "
                            "Specify the forecast times (or strike the row) before the freeze.")
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


def validate_config(cfg_in, root=None):
    """every static ConfigError check of a run configuration, without loading data, touching the freeze or creating anything -> the merged config (DEFAULTS + the file's keys, with target_kind
    and the derived inner_k filled in). `_run` calls it first; the confirmatory config set is checked through it (code/tests/test_c14_confirmatory_configs.py)."""
    cfg = {**DEFAULTS, **cfg_in}
    ds, mode_ = cfg["dataset"], cfg["mode"]
    if cfg["permute_stress"] and cfg["test"] != "B":
        raise ConfigError("permute_stress (NC-2) is defined on Test B only, not on Test C (NEGCONTROL_RULING section 3)")
    if cfg["mc_seed_root"] != negcontrol.MC_SEED_ROOT:
        raise ConfigError("mc_seed_root is fixed by the NEGCONTROL ruling (20261105)")
    if cfg["endpoint"] not in ("ensemble", "per_seed"):
        raise ConfigError("endpoint must be 'ensemble' (D020 C1, Design R2) or 'per_seed' (the V3 rule)")
    sc_ = cfg["symbolic"] or {}
    if set(sc_) - {"cap", "refit_frac"}:
        raise ConfigError(f"unknown symbolic keys {sorted(set(sc_) - {'cap', 'refit_frac'})}: allowed cap, refit_frac")
    if sc_.get("cap") is not None:
        from . import symbolic as _sym
        fcap = _sym.library_file_cap()
        if fcap is not None and int(sc_["cap"]) != int(fcap):
            raise ConfigError(f"symbolic.cap = {sc_['cap']} disagrees with max_coeffs_per_edge = {fcap} in symbolic_library.json: the cap is pinned in the library file (PREREG_v4 7.3, D021); remove the config value or change the file")
    if {"A15", "G15"} & set(cfg["arms"]):                                   # D022 2.2a item 5: the audit thresholds and the calibration rule are config keys (hence in the config hash)
        from . import extraction_audit as _xa
        rule_file = os.path.join(root or _ROOT, "debates", "D022_datasets_kan", "calibration_rule_v2.md")
        for key, path in (("extraction_audit_sha256", _xa.THRESHOLDS_FILE), ("calibration_rule_sha256", rule_file)):
            if cfg[key] is None:
                if cfg["mode"] == "confirmatory" and ds != "synthetic":
                    raise ConfigError(f"{key} is required in a real-data confirmatory run with A15 / G15 (sha256 of {os.path.basename(path)})")
            elif not os.path.isfile(path) or cfg[key] != _xa.sha256_file(path):
                raise ConfigError(f"{key} does not match the file {os.path.basename(path)} in this tree")
    if {"A1", "A2", "A4", "A5", "A9", "A13", "A15", "G15"} & set(cfg["arms"]):         # D023: the inversion constants are a config key (hence in the config hash)
        if cfg["inversion_config_sha256"] is None:
            if cfg["mode"] == "confirmatory" and ds != "synthetic":
                raise ConfigError("inversion_config_sha256 is required in a real-data confirmatory run (sha256 of inversion.config_dict(); D023 action 2)")
        elif cfg["inversion_config_sha256"] != inversion.config_sha256():
            raise ConfigError("inversion_config_sha256 does not match inversion.CONFIG (tolerance, cap, damping constants, dtype, z-prior weight)")
    if cfg["design"] not in ("R2", "V3_legacy"):
        raise ConfigError("design must be 'R2' (PREREG_v4) or 'V3_legacy' (history only)")
    if cfg["design"] == "R2" and (cfg["mode"] in ("confirmatory", "nc1_full", "h7") or cfg["m"] is not None or cfg["k"] is not None):
        bad = sorted(set(cfg["arms"]) & set(OUT_OF_SCOPE_ARMS)) if cfg["mode"] != "h7" else []
        if bad:
            raise ConfigError(f"arms {bad} are out of scope for Design R2 (A3, A7 off the grid; A6, A8, A14 not on the list; PREREG_v4 7.1): use design 'V3_legacy' for history runs")
        if cfg["mode"] == "h7":
            gens = list((cfg.get("h7") or {}).get("gens") or ("G0", "G1", "G2"))
            if gens != ["G0"]:
                raise ConfigError("under Design R2 the synthetic driver runs the well-specified generator G0 only (PC-1); G1, G2, H3 and the 'KAN win' are struck (PREREG_v4 13). Set h7.gens = ['G0']")
    tk = TARGET_BY_TEST.get(cfg["test"], "cycling")
    if cfg.get("target_kind") not in (None, tk):
        raise ConfigError(f"target_kind {cfg['target_kind']!r} contradicts test {cfg['test']!r} (scored kind is {tk!r})")
    cfg["target_kind"] = tk
    if cfg["m"] is not None:
        if int(cfg["m"]) not in subsets.GRID_M:
            raise ConfigError(f"m must be one of {subsets.GRID_M} (PREREG_v4 4.1), not {cfg['m']!r}")
        if cfg["subset"] not in ("maxmin", "random") or (cfg["subset"] == "random" and int(cfg["subset_draw"]) not in (0, 1, 2)):
            raise ConfigError("subset must be 'maxmin' or 'random' (draw 0, 1 or 2)")
        if cfg["test"] not in ("B", "C"):
            raise ConfigError("the training-subset grid (m) is defined for Test B (and the Test C variant), not for tests A, S2, S3")
        if "A5" in cfg["arms"] and int(cfg["m"]) < 32:
            raise ConfigError("A5 (interaction GAM) runs at m = 32 only: its tensor terms cannot be supported by fewer conditions (PREREG_v4 7.1); at m < 32 AG = A4")
        thin = int(cfg["inner_k_thin"])
        if thin not in (2, 4):
            raise ConfigError("inner_k_thin must be 2 (default) or 4 (only if runs/pilot_P6b/decision.json says adopt; D020 C2)")
        if thin == 4:
            dec = cfg["p6b_decision"]
            if not dec or not os.path.isfile(dec) or json.load(open(dec, encoding="utf8")).get("adopt") is not True:
                raise ConfigError("inner_k_thin = 4 needs p6b_decision pointing at a decision.json with adopt = true (D020 C2: the default is 2)")
            if cfg_in.get("p6b_decision_sha256") != sha256_file(dec):
                raise ConfigError("inner_k_thin = 4: the config must carry p6b_decision_sha256 equal to the sha256 of the decision file, so that the decision is part of the hashed config (review M2)")
            cfg["p6b_decision_sha256"] = sha256_file(dec)
        if "inner_k" not in cfg_in:
            cfg["inner_k"] = tuning.inner_k_for_m(int(cfg["m"]), thin_folds=thin)       # 2 for m in {8, 16}, 3 for m = 32 (PREREG_v4 4.1)
    if mode_ == "confirmatory" and ds != "synthetic":      # the config-only part of the real-data confirmatory refusals (the freeze and the item (f) record are checked in _run)
        if cfg["steps_scale"] != 1.0:
            raise ConfigError("steps_scale != 1 is not allowed in a confirmatory run on real data")
        if cfg["overwrite"]:
            raise ConfigError("overwrite is not allowed in a confirmatory run on real data (stop rule 4)")
        if cfg["auto_budget"]:
            raise ConfigError("auto_budget is wall-clock dependent and unhashed: a confirmatory run on real data takes N and inner_k from the config, fixed from the FB-8 timing run's budget_rule.json (review M4)")
    wk = cfg["window"]
    if ds != "synthetic" and (cfg["m"] is not None or cfg["k"] is not None) and SPECS[ds].window[0] == "count" and (wk.get("k_cycling") is None or wk.get("k_storage") is None):
        raise ConfigError("a Design R2 grid run on real data needs window.k_cycling (= k_full) and window.k_storage from the counted listings [FB-6]; the placeholder defaults 4 and 2 are not used (review M3)")
    return cfg


def _run(cfg_in, root=None, runs_dir=None):
    if torch.cuda.is_available():            # D013 C4: a wrong environment must not silently produce GPU numbers
        raise DeviceError("CUDA is available to torch: runs are CPU only (CUDA_VISIBLE_DEVICES=-1 is forced by the package); no GPU use without the lead's instruction")
    root = root or _ROOT
    cfg = validate_config(cfg_in, root)          # every static ConfigError check (also used by the confirmatory config set test)
    runs_dir = runs_dir or os.path.join(root, "runs")
    run_id = cfg["run_id"]
    run_dir = os.path.join(runs_dir, run_id)
    ds, mode = cfg["dataset"], cfg["mode"]
    tk = cfg["target_kind"]
    chash, item_f_sha = None, None
    if mode == "confirmatory" and ds != "synthetic":      # checks before anything is created or read (review M2)
        guard.require_frozen("confirmatory run", root)
        chash = guard.check_config_frozen({**DEFAULTS, **cfg_in}, root)     # hash of the config as written (DEFAULTS + file keys)
        if ds == "samsung":                                                 # D026: the item (f) record is verified before build_data / load_split can release any test fold
            item_f_sha = guard.require_item_f_record(root, runs_dir)
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
        labels = json.load(open(os.path.join(dA, "metrics.json"), encoding="utf8")).get("k_labels")
        if not labels:                                                     # single legacy window: scramble after it
            dB = run({**base, "run_id": run_id + "_scrambled", "mode": "confirmatory", "nc1_scramble_test": True}, root=root, runs_dir=runs_dir)
            res = negcontrol.compare_runs(dA, dB)
            dBs = {None: dB}
        else:                                                              # grid: one scrambled pipeline per k, labels scrambled after THAT window (k = 0 sees no post-reference label) (review M6)
            dBs, parts = {}, {}
            for kl in labels:
                dBs[kl] = run({**base, "run_id": run_id + f"_scrambled_k{kl}", "mode": "confirmatory", "nc1_scramble_test": True, "nc1_scramble_k": kl}, root=root, runs_dir=runs_dir)
                parts[kl] = negcontrol.compare_runs(dA, dBs[kl], outer_phase=kl)
            res = {"passed": bool(all(p["passed"] for p in parts.values())), "per_k": parts, "n_outer_rows": int(sum(p["n_outer_rows"] for p in parts.values())),
                   "max_abs_diff_outer": float(max(p["max_abs_diff_outer"] for p in parts.values()))}
        _json(os.path.join(run_dir, "config.json"), cfg)
        _json(os.path.join(run_dir, "nc1_full.json"), {**res, "clean_run": dA, "scrambled_runs": dBs})
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
    if cfg["design"] == "V3_legacy":
        open(os.path.join(run_dir, "OUT_OF_SCOPE_V3_LEGACY"), "w").write("run of the PREREG_v3 design kept for history: not a Design R2 result and not read by stats_v4\n")
    if ds == "synthetic":
        open(os.path.join(run_dir, "SYNTHETIC"), "w").write("synthetic data: invented ageing laws, not results\n")
    guard.GUARD_LOG.clear()
    if item_f_sha:                          # D026 review m3: the verified item (f) record stays in guard.json
        guard.GUARD_LOG.append({"what": "item (f) record", "verified": True, "item_f_sha256": item_f_sha})
    t_start = time.time()
    _json(os.path.join(run_dir, "config.json"), {**cfg, "mode_effective": mode, "blinded_samsung_pre_freeze": blinded,
                                                 "config_sha256": guard.canonical_config_hash({**DEFAULTS, **cfg_in}), "config_input": cfg_in})      # D026: the hash as pinned (DEFAULTS + the file's keys) and the input it was computed from (stats_v4.build_item_f recomputes it)
    _json(os.path.join(run_dir, "env.json"), env_info())
    _json(os.path.join(run_dir, "git.json"), git_info(root))
    _json(os.path.join(run_dir, "seeds.json"), {"final_refit_seeds": cfg["seeds"], "tuning_seed": "1000 + outer fold", "tpe_sampler_seed": "outer fold",
                                                "mc_seed_root": cfg["mc_seed_root"], "mc_seed_rule": "np.random.default_rng(SeedSequence([root, zlib.crc32(label)])) for every Monte Carlo step; labels such as 'B|H1a|BCa_mean_pp' are listed in the contrasts files",
                                                "permute_stress_stream": "[20261107, 31, fold] (train), fold + 1000 (test)", "nc1_scramble_stream": "mc_rng('NC1|' + cell_id)"})
    role = "test" if mode == "confirmatory" else "train"
    D = build_data(cfg, root, role, runs_dir=runs_dir)          # the test-fold guard is inside load_split (role != 'train')
    spec, train = D["spec"], D["train"]
    if mode == "confirmatory" and D.get("sv") is not None and D["sv"].missing_train_conditions:
        raise ConfigError(f"incomplete training set, missing conditions {D['sv'].missing_train_conditions[:3]} (complete download required)")
    if cfg["permute_stress"]:                              # negative control: separate permutations of train and test stress vectors
        train = metrics.permute_stress(train, spec, cfg["fold"])
        if D["test"] is not None:
            D["test"] = metrics.permute_stress(D["test"], spec, cfg["fold"] + 1000)
    _json(os.path.join(run_dir, "split.json"), D["split"])
    _json(os.path.join(run_dir, "manifest.json"), D["manifest"])
    if D.get("subset"):
        _json(os.path.join(run_dir, "subsets.json"), D["subset"])
        sf = os.path.join(root, "runs", "prereg", "subsets.json")
        if ds == "samsung" and cfg["m"] is not None and cfg["subset"] == "maxmin" and os.path.isfile(sf):      # review M2: the pinned subsets file and this run's subset must agree
            pin = json.load(open(sf, encoding="utf8"))["folds"][str(cfg["fold"])]["subsets"][str(int(cfg["m"]))]
            if list(pin) != list(D["subset"]["kept"]) and D["subset"]["thinned"]:
                raise ConfigError(f"the max-min subset of this run differs from runs/prereg/subsets.json (fold {cfg['fold']}, m {cfg['m']})")
            D["split"]["subsets_file_sha256"] = sha256_file(sf)
            _json(os.path.join(run_dir, "split.json"), D["split"])      # nested training subset of this (fold, m): ids, order, hash (identifiers only)
    rec.log(f"run {run_id}: dataset {ds} test {cfg['test']} fold {cfg['fold']} mode {mode} (requested {cfg['mode']}) blinded={blinded}")
    rec.log(f"train cells {len(train)}: {sum(c.kind == 'cycling' for c in train)} cycling, {sum(c.kind == 'storage' for c in train)} storage; conditions {len({c.cond for c in train})}")
    if D["split"].get("missing_train_conditions"):
        rec.log(f"NOTE: {len(D['split']['missing_train_conditions'])} training conditions of the split have no cells on disk (partial download)")
    wk = cfg["window"]          # the FB-6 window-count check is in validate_config
    rule = WindowRule.for_spec(spec, k_cycling=wk.get("k_cycling"), k_storage=wk.get("k_storage"), W=wk.get("W"), shift=wk.get("shift", 0))
    _capped = window_capped_cells(list(train) + list(D.get("test") or []), rule)      # D025: capped cells are kept and listed (identifiers only)
    _json(os.path.join(run_dir, "window_capped.json"), {"rule": "D025: window = min(k, n - 1) intermediate check-ups", "cells": _capped})
    rec.log(f"D025 window cap binds for {len(_capped)} cell(s): {_capped[:10]}")
    rule_test = dataclasses.replace(rule, min_fc_points=int(cfg["min_fc_points"]))      # scored cells only (sensitivity row "cells with >= 3 forecast points"); training windows keep `rule`
    if cfg["nc1_scramble_test"]:
        if ds != "synthetic" or D["test"] is None:
            raise ConfigError("nc1_scramble_test is for synthetic confirmatory runs only")
        rule_scr = rule_test if cfg["nc1_scramble_k"] is None else WindowRule.for_grid(spec, "full" if cfg["nc1_scramble_k"] == "full" else int(cfg["nc1_scramble_k"]), rule_test)
        D["test"] = negcontrol.scramble_cells(D["test"], rule_scr, spec)
    extra = None
    if (cfg["twins"] == "c35") or (cfg["twins"] == "auto" and cfg["test"] == "C" and ds == "samsung"):
        extra = twins_from_conditions(D["split"].get("test_conditions", []))
    rule_tune = rule if cfg["m"] is None else WindowRule.for_grid(spec, 2 if int(cfg["m"]) < 32 else "full", rule)      # PREREG_v4 4.1: inner CV scored at k = 2 for m < 32, at k_full for m = 32
    ctx = {"backbone": cfg["backbone"] if cfg["backbone"] != "tournament" else "self_limiting", "steps_scale": cfg["steps_scale"], "rule": rule_tune, "extra_twin_raw": extra,
           "oracle": cfg["oracle_throughput"], "per_cell_factor": cfg["per_cell_factor"], "lab_indicator": bool(cfg["lab_indicator"]), "symbolic": dict(cfg["symbolic"] or {}), "a10_starts": cfg.get("a10_starts", 8), "pinn": cfg["pinn"]}
    arms = list(cfg["arms"])
    if mode == "confirmatory" and ds != "synthetic" and ({"A10", "A10P"} & set(arms)):
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
        cfg["n_trials"], cfg["inner_k"] = bud["n_trials"], (bud["inner_k"] if cfg["m"] is None else tuning.inner_k_for_m(int(cfg["m"]), partial=bud["inner_k"] == 2, thin_folds=int(cfg["inner_k_thin"])))
        _json(os.path.join(run_dir, "budget_rule.json"), {**bud, "median_fit_seconds": med})
        rec.log(f"budget fixed before tuning: {bud}")
    if cfg["backbone"] == "tournament":
        tb = tuning.backbone_tournament(train, spec, rule_tune, cfg["inner_k"], cfg["fold"], ctx, tk)
        ctx["backbone"] = tb["chosen"]
        _json(os.path.join(run_dir, "backbone_tournament.json"), tb)
        rec.log(f"backbone tournament: chosen {tb['chosen']} (best {tb['best']})")
    tuned = {}
    inversion.LOG.clear()
    for a in arms:
        t0 = time.time()
        inversion.TAG.clear()
        inversion.TAG.update({"arm": a, "k": "inner"})
        r = tuning.tune(a, train, spec, rule_tune, cfg["n_trials"], cfg["inner_k"], cfg["fold"], ctx, tk)
        tuned[a] = r
        timings[a] = {"tuning_seconds": time.time() - t0, "median_fit_seconds": r["median_fit_seconds"], "n_trials": r["n_trials"], "n_failed": r["n_failed"]}
        rec.add_preds("inner_oof", a, 1000 + cfg["fold"], r["rows"])
        _json(os.path.join(run_dir, f"tuning_{a}.json"), {k: (strip_rows(v) if k == "rows" else v) for k, v in r.items()})
        rec.log(f"tuned {a}: inner-CV {r['inner_cv_pp']:.3f} pp, best {r['best_hp']}, median fit {r['median_fit_seconds']:.1f} s, failed {r['n_failed']}")
    inner_inv = inversion.drain_log()                      # every inversion of the tuning (count only)
    inversion.TAG.clear()
    metrics_out["k_full"] = rule.k_cycling if rule.W is None else None
    _json(os.path.join(run_dir, "train_condition_meta.json"), metrics.train_condition_meta(train))      # identifiers only: laboratory of each training condition (item (f) dependence estimate)
    metrics_out["tuning_window"] = {"k_cycling": rule_tune.k_cycling, "k_storage": rule_tune.k_storage, "W": rule_tune.W, "m": cfg["m"]}
    _json(os.path.join(run_dir, "inner_folds.json"), tuning.inner_folds(train, cfg["inner_k"], 1000 + int(cfg["fold"]), spec, tk))      # the inner fold of every training condition (item (f), review M5)
    inner = {a: {"inner_cv_pp": tuned[a]["inner_cv_pp"], "cond_scores": tuned[a]["cond_scores"], "best_hp": tuned[a]["best_hp"]} for a in arms}
    _json(os.path.join(run_dir, "tuning_done.json"), {"backbone": ctx["backbone"], "arms": inner, "budget": {"n_trials": cfg["n_trials"], "inner_k": cfg["inner_k"]}})
    metrics_out["inner_cv_pp"] = {a: inner[a]["inner_cv_pp"] for a in arms}
    comp = selectors.select_comparators({a: inner[a]["inner_cv_pp"] for a in arms}, cfg["m"])     # D* and AG by inner-CV score on the training conditions only (never by outer test error)
    _json(os.path.join(run_dir, "comparators.json"), comp)
    metrics_out["comparators"] = {k: v["arm"] for k, v in comp.items() if isinstance(v, dict) and "arm" in v}
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
    kcells = _score_windows(cfg, rule_test, spec)                       # [(label, WindowRule)]; legacy single window: [(None, rule_test)]
    KC = {}
    for kl, rk in kcells:
        pk = prepare_many(D["test"], rk, oracle=cfg["oracle_throughput"])
        KC[kl] = {"rule": rk, "prep": pk, "wc": [p.win for p in pk]}
    primary = "full" if "full" in KC else kcells[-1][0]
    prep = KC[primary]["prep"]
    if ds != "synthetic":
        guard.require_frozen("score outer test fold", root)      # the scoring side of the guard
        guard.record_scoring(chash, run_id, git_info(root)["commit"], root, dataset=ds, item_f_sha256=item_f_sha)     # a second scoring of the same config is refused
    bad = {c.kind for c in D["test"]} - {tk}
    if bad:
        raise ConfigError(f"test cells of kind {sorted(bad)} but the tuned and scored kind is {tk}")
    cond_scores_out, per_arm, cell_scores_out = {kl: {} for kl in KC}, {kl: {} for kl in KC}, {kl: {} for kl in KC}
    seed_scores_out = {kl: {} for kl in KC}            # per-seed condition scores (mean over seeds of the per-seed condition RMSE): K1 / K2 and the descriptive row
    fitted, inv_records, law_records = {}, {}, []
    inv_calls, seed0_arms = [], {}
    for a in arms:
        ks_a = [kl for kl in KC if not (kl == "0" and a in ("R1", "R2"))]            # R1 and R2 need a window check-up (k >= 1): k = 0 is its own reference
        per_seed = {kl: ([], []) for kl in ks_a}
        for sd_ in cfg["seeds"]:
            t0, fit_s = time.time(), 0.0
            arm = None
            for kl in ks_a:
                if arm is None or ARMS[a].family == "p3":                           # A11 / A12 retrain per k (window features differ); every other arm is fitted once
                    tf0 = time.time()
                    arm = make_arm(a, spec, tuned[a]["best_hp"], sd_, dict(ctx, rule=KC[kl]["rule"])).fit(train)
                    fit_s += time.time() - tf0                                      # the fit alone: predict and the NC-1 re-predict are not part of the reported wall clock (review M1)
                inversion.LOG.clear()
                inversion.TAG.clear()
                inversion.TAG.update({"arm": a, "k": kl, "seed": sd_})
                preds = arm.predict(KC[kl]["wc"])
                inv_calls += [dict(r, fold=cfg["fold"], m=cfg["m"]) for r in inversion.drain_log()]          # convergence of every inversion call of the primary prediction
                rows = metrics.score_prepared(preds, KC[kl]["prep"])
                per_seed[kl][0].append(rows)
                per_seed[kl][1].append(preds)
                key = f"{a}|{sd_}" if kl is None else f"{a}|{sd_}|k{kl}"
                inversion.TAG.clear()
                inv_records[key] = negcontrol.check_invariance(arm.predict, D["test"], KC[kl]["rule"], spec, cfg["oracle_throughput"], base_preds=preds, base_prepared=KC[kl]["prep"])
                if kl == primary and a in ("A1", "A2", "A4", "A10"):
                    fitted.setdefault(a, []).append(arm)
                rec.add_preds("outer_test" if kl is None else f"outer_test_k{kl}", a, sd_, rows)
            if a in ("A15", "G15") and arm is not None:                          # the extraction audit reads one record per fold-by-seed law (D022 2.2a)
                from . import extraction_audit as _xa
                akey = _xa.arm_key(a, tuned[a]["best_hp"])                                  # unknown arm or missing h is an error (D022a m3)
                law_records.append(_xa.law_record(akey, cfg["fold"], sd_, arm.report, spec, arm.model.law.cyc, arm.parent_cyc, arm.s_cyc_train))
            inversion.LOG.clear()                                                          # the invariance re-predictions are not part of the diagnostics
            if sd_ == cfg["seeds"][0] and arm is not None:
                seed0_arms[a] = arm
            timings[a][f"refit_seed{sd_}_seconds"] = fit_s
            timings[a][f"refit_seed{sd_}_total_seconds"] = time.time() - t0     # fit + predict + invariance re-predict, for the record
        for kl in ks_a:
            per_seed_rows, per_seed_preds = per_seed[kl]
            cs, sd = metrics.seed_condition_scores(per_seed_rows)
            ens_rows = metrics.ensemble_rows(per_seed_preds, KC[kl]["prep"])
            ens_cs = metrics.condition_scores(ens_rows)
            rec.add_preds("outer_test" if kl is None else f"outer_test_k{kl}", a, "ens", ens_rows)       # predictions.csv carries the per-seed rows and the ensemble ('ens')
            seed_scores_out[kl][a] = cs
            if cfg["endpoint"] == "ensemble":
                cond_scores_out[kl][a] = ens_cs
                cell_scores_out[kl][a] = metrics.cell_scores_from_rows(ens_rows)
            else:
                cond_scores_out[kl][a] = cs
                cell_scores_out[kl][a] = metrics.seed_cell_scores(per_seed_rows)
            cs_main = cond_scores_out[kl][a]
            per_arm[kl][a] = {"primary_pp": float(np.mean(list(cs_main.values()))), "primary_pp_ensemble": float(np.mean(list(ens_cs.values()))), "primary_pp_per_seed": float(np.mean(list(cs.values()))),
                              "n_nonfinite_by_seed": [int(sum(r["n_nonfinite"] for r in rows)) for rows in per_seed_rows],
                              "fit_seconds_one_fit": float(np.mean([timings[a][f"refit_seed{s_}_seconds"] for s_ in cfg["seeds"]])), "fit_seconds_ensemble": float(sum(timings[a][f"refit_seed{s_}_seconds"] for s_ in cfg["seeds"])),
                              "seed_sd_of_mean": sd, "n_conditions": len(cs_main),
                              "mae_pp_mean": float(np.mean([r["mae_pp"] for rows in per_seed_rows for r in rows])),
                              "n_nonfinite": int(sum(r["n_nonfinite"] for rows in per_seed_rows for r in rows)), "n_params": int(arm.n_params),
                              "n_train_used": arm.n_train_used, **outer_extras(KC[kl]["prep"], per_seed_preds, per_seed_rows)}
            rec.log(f"outer test {a} k={kl}: {per_arm[kl][a]['primary_pp']:.3f} pp ({cfg['endpoint']}; per-seed {per_arm[kl][a]['primary_pp_per_seed']:.3f}, seed SD {sd:.3f}) over {len(cs)} conditions")
    metrics_out["outer_test"] = per_arm[primary]
    if None not in KC:
        metrics_out["outer_test_by_k"] = {kl: per_arm[kl] for kl in KC}
        metrics_out["k_labels"] = list(KC)
        metrics_out["k_primary"] = primary
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
    for kl in KC:
        suf = "" if kl == primary else f"_k{kl}"                                     # the primary cell keeps the file names the statistics step reads
        _json(os.path.join(run_dir, f"cell_scores{suf}.json"), cell_scores_out[kl])        # per scored cell: mean over seeds of the cell RMSE (two-stage bootstrap, sensitivity row (d))
        _json(os.path.join(run_dir, f"condition_meta{suf}.json"), metrics.condition_meta(KC[kl]["prep"]))     # identifiers only: scored cells, laboratory and stage per condition
        _json(os.path.join(run_dir, f"condition_scores_seed{suf}.json"), seed_scores_out[kl])      # per-seed endpoint: K1 / K2 and the descriptive row (D020 C1 item 4, 5)
        if kl != primary:
            _json(os.path.join(run_dir, f"condition_scores{suf}.json"), cond_scores_out[kl])
    if law_records:
        from . import extraction_audit as _xa
        _json(os.path.join(run_dir, "extracted_laws.json"), {"m": 32 if cfg["m"] is None else int(cfg["m"]), "fold": cfg["fold"], "laws": law_records,
                                                            "levels": _xa.distinct_levels(sorted({c.cond for c in train if c.kind == "cycling"})), "extraction_audit_sha256": _xa.thresholds_sha256()})
    _json(os.path.join(run_dir, "condition_scores.json"), cond_scores_out[primary])     # written last: its presence marks a scored run
    _inversion_diagnostics(cfg, run_dir, rec, spec, arms, KC, seed0_arms, inv_calls, inner_inv, comp)
    _finish(rec, run_dir, timings, metrics_out, t_start)
    return run_dir


def _score_windows(cfg, rule_test, spec):
    """[(label, WindowRule)] of the grid cells scored in this run. cfg['k'] None: the single legacy window. 'grid': (0, 2, 'full') from k_full (data.grid_ks; k_full < 2 raises
    DesignReopenError). A list names the cells explicitly (ints, 'full'; time-window datasets: W values)."""
    k = cfg["k"]
    if k is None:
        return [(None, rule_test)]
    if k == "grid":
        if rule_test.W is not None:
            raise ConfigError("k = 'grid' is the count-window grid; name the W values explicitly for ISU / SNL (for example [0, 2, 'full'])")
        k = list(grid_ks(rule_test.k_cycling))
    k = list(k) if isinstance(k, (list, tuple)) else [k]
    out = []
    for x in k:
        if x != "full" and (not isinstance(x, (int, float)) or x < 0):
            raise ConfigError(f"bad k {x!r}: use 0, 2, 'full' (or a window length)")
        out.append(("full" if x == "full" else str(x), WindowRule.for_grid(spec, x, rule_test)))
    if len({l for l, _ in out}) != len(out):
        raise ConfigError("duplicate k cells")
    return out


def _inversion_diagnostics(cfg, run_dir, rec, spec, arms, KC, seed0_arms, inv_calls, inner_inv, comp):
    """D023 section 4, after the primary scores are written: pooled convergence (inner-CV calls as a count), cap doubling, start spread, basin shares, rows (v) and (vi). Window cells only."""
    want = cfg["inversion_diagnostics"]
    if want is None:
        want = bool(cfg["mode"] == "confirmatory" and cfg["dataset"] != "synthetic")
    p = os.path.join(run_dir, "diagnostics.json")
    d = json.load(open(p, encoding="utf8")) if os.path.exists(p) else {}
    inv = {"config": inversion.config_dict(), "config_sha256": inversion.config_sha256(), "z_prior_weight": inversion.Z_PRIOR_WEIGHT,
           "inner_cv": inversion.pooled_convergence(inner_inv), "primary": inversion_diag.summarise(inv_calls), "n_calls": len(inv_calls),
           "nonconverged_by_call": [{k: r[k] for k in ("arm", "k", "seed", "fold", "m", "n_inverted", "n_nonconverged", "gnorm_max")} for r in inv_calls if r["n_nonconverged"]],
           "diagnostics_computed": bool(want)}
    if want:
        agname = (comp.get("AG") or {}).get("arm")
        full_arms = {"A1", "A9", agname} - {None}
        out, sens = [], {}
        for a in arms:
            arm = seed0_arms.get(a)
            if arm is None or not inversion_diag.inverts(arm):
                continue
            for kl, kc in KC.items():
                if kl in (None, "0"):
                    continue
                full = a in full_arms
                g1g4 = (cfg["m"] == 8 and kl == "2") or ((cfg["m"] in (None, 32)) and kl == "full")
                r = inversion_diag.diagnose(arm, kc["wc"], a, cfg["fold"], cfg["m"], kl, full=full, rows=bool(full and g1g4))
                fc = r.pop("forecasts", None)
                out.append(r)
                if fc:
                    for row, d_ in fc.items():
                        for tag, preds in d_.items():
                            sens.setdefault(f"{row}{tag}_k{kl}", {})[a] = metrics.condition_scores(metrics.score_prepared(preds, kc["prep"]))
        inv["per_arm_cell"] = out
        for name, sc in sens.items():                      # descriptive rows (v) and (vi), seed 0 of the final refit; no consequence for any state or tier
            _json(os.path.join(run_dir, f"condition_scores_sens_{name}.json"), sc)
        inv["sensitivity_rows_written"] = sorted(sens)
    d["inversion"] = inv
    _json(p, d)


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
