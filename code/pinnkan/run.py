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
import json
import os
import platform
import subprocess
import sys
import time

import numpy as np
import torch

from . import ROOT as _ROOT
from . import guard, margins, metrics, semi, synth, tuning
from .arms import ARMS, H1B_POOL, NEURAL, default_hp, make_arm
from .data import WindowRule, load_split, prepare_many, sha256_file
from .specs import SPECS

torch.set_num_threads(1)

DEFAULTS = {"mode": "inner", "test": "B", "fold": 0, "arms": ["A1", "A2", "A9", "R1", "R2"], "seeds": [0, 1, 2, 3, 4], "n_trials": 20, "inner_k": 3,
            "backbone": "self_limiting", "steps_scale": 1.0, "window": {}, "oracle_throughput": False, "per_cell_factor": True, "twins": "auto",
            "refit_timing": False, "overwrite": False, "retain_all": False, "throughput": "analytic", "target_kind": "cycling", "auto_budget": False}


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
        tr, te = synth.split_conditions(S.cells, sc.get("test_frac", 0.25), sc.get("seed", 0))
        return {"spec": SPECS["synthetic"], "train": tr, "test": te if role != "train" else None, "synth": S,
                "split": {"file": "synthetic (generated)", "note": "no outer test fold of real data exists"}, "manifest": []}
    sv = load_split(ds, cfg["test"], cfg["fold"], role=role, root=root, retain_all=cfg["retain_all"], throughput=cfg["throughput"])
    return {"spec": sv.spec, "train": sv.train, "test": sv.test_cells, "sv": sv,
            "split": {"file": os.path.relpath(sv.split_file, root).replace("\\", "/"), "sha256_file": sv.split_sha256, "fold_hash_stored": sv.fold_hash_stored,
                      "fold_hash_recomputed": sv.fold_hash_recomputed, "fold_hash_ok": sv.hash_ok, "test_conditions": sv.test_conditions,
                      "n_train_cells": len(sv.train), "n_train_conditions": len(sv.train_conditions)}, "manifest": sv.input_files}


def run(cfg_in, root=None, runs_dir=None):
    cfg = {**DEFAULTS, **cfg_in}
    root = root or _ROOT
    runs_dir = runs_dir or os.path.join(root, "runs")
    run_id = cfg["run_id"]
    run_dir = os.path.join(runs_dir, run_id)
    if os.path.exists(run_dir) and not cfg["overwrite"]:
        raise FileExistsError(run_dir)
    os.makedirs(run_dir, exist_ok=True)
    ds, mode = cfg["dataset"], cfg["mode"]
    blinded = ds == "samsung" and not guard.is_frozen(root)
    if blinded and mode != "timing":
        mode = "timing"        # retention blinding before the freeze: no retention-derived number is written under runs/
    rec = Recorder(run_dir, run_id)
    guard.GUARD_LOG.clear()
    t_start = time.time()
    _json(os.path.join(run_dir, "config.json"), {**cfg, "mode_effective": mode, "blinded_samsung_pre_freeze": blinded})
    _json(os.path.join(run_dir, "env.json"), env_info())
    _json(os.path.join(run_dir, "git.json"), git_info(root))
    _json(os.path.join(run_dir, "seeds.json"), {"final_refit_seeds": cfg["seeds"], "tuning_seed": "1000 + outer fold", "tpe_sampler_seed": "outer fold",
                                                "permutation_test_rng_seed": "set by the statistics step (prereg 9.3)"})
    role = "test" if mode == "confirmatory" else "train"
    D = build_data(cfg, root, role)          # the test-fold guard is inside load_split (role != 'train')
    spec, train = D["spec"], D["train"]
    _json(os.path.join(run_dir, "split.json"), D["split"])
    _json(os.path.join(run_dir, "manifest.json"), D["manifest"])
    rec.log(f"run {run_id}: dataset {ds} test {cfg['test']} fold {cfg['fold']} mode {mode} (requested {cfg['mode']}) blinded={blinded}")
    rec.log(f"train cells {len(train)}: {sum(c.kind == 'cycling' for c in train)} cycling, {sum(c.kind == 'storage' for c in train)} storage; conditions {len({c.cond for c in train})}")
    if D["split"].get("fold_hash_ok") is False:
        rec.log("WARNING: stored fold hash differs from the recomputed one")
    wk = cfg["window"]
    rule = WindowRule.for_spec(spec, k_cycling=wk.get("k_cycling"), k_storage=wk.get("k_storage"), W=wk.get("W"), shift=wk.get("shift", 0))
    extra = None
    if (cfg["twins"] == "c35") or (cfg["twins"] == "auto" and cfg["test"] == "C" and ds == "samsung"):
        extra = twins_from_conditions(D["split"].get("test_conditions", []))
    ctx = {"backbone": cfg["backbone"] if cfg["backbone"] != "tournament" else "self_limiting", "steps_scale": cfg["steps_scale"], "rule": rule, "extra_twin_raw": extra,
           "oracle": cfg["oracle_throughput"], "per_cell_factor": cfg["per_cell_factor"], "a10_starts": cfg.get("a10_starts", 8)}
    arms = list(cfg["arms"])
    if mode == "confirmatory" and ds != "synthetic" and "A10" in arms:
        semi.require_verified()
    timings, metrics_out = {}, {"blinded": blinded, "mode": mode}
    # ---------------------------------------------------------------- timing (and Samsung before the freeze)
    if mode == "timing":
        for a in arms:
            t0 = time.time()
            arm = make_arm(a, spec, default_hp(a) if ARMS[a].tuned else {}, 1000 + cfg["fold"], ctx).fit(train)
            timings[a] = {"fit_seconds": time.time() - t0, "n_params": int(arm.n_params)}
            rec.log(f"timing {a}: {timings[a]['fit_seconds']:.1f} s, {arm.n_params} parameters")
        metrics_out["note"] = "timing only; no scoring, no predictions (retention blinding before the freeze)" if blinded else "timing only"
        _json(os.path.join(run_dir, "timings.json"), timings)
        _json(os.path.join(run_dir, "metrics.json"), metrics_out)
        _json(os.path.join(run_dir, "guard.json"), guard.GUARD_LOG)
        rec.log(f"done in {time.time() - t_start:.0f} s")
        return run_dir
    # ---------------------------------------------------------------- tuning on training conditions
    tk = cfg["target_kind"]
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
    if cfg["auto_budget"]:
        _json(os.path.join(run_dir, "budget_rule.json"), tuning.choose_budget({a: tuned[a]["median_fit_seconds"] for a in arms}))
    metrics_out["inner_cv_pp"] = {a: inner[a]["inner_cv_pp"] for a in arms}
    metrics_out["backbone"] = ctx["backbone"]
    if cfg["refit_timing"]:
        for a in arms:
            t0 = time.time()
            arm = make_arm(a, spec, tuned[a]["best_hp"], 0, ctx).fit(train)
            timings[a].update(refit_seconds=time.time() - t0, n_params=int(arm.n_params))
    if mode == "inner":
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
    prep = prepare_many(D["test"], rule, oracle=cfg["oracle_throughput"])
    wc = [p.win for p in prep]
    if ds != "synthetic":
        guard.require_frozen("score outer test fold", root)      # the scoring side of the guard
    cond_scores_out, per_arm = {}, {}
    for a in arms:
        per_seed_rows = []
        for s in cfg["seeds"]:
            t0 = time.time()
            arm = make_arm(a, spec, tuned[a]["best_hp"], s, ctx).fit(train)
            preds = arm.predict(wc)
            rows = metrics.score_prepared(preds, prep)
            per_seed_rows.append(rows)
            rec.add_preds("outer_test", a, s, rows)
            timings[a][f"refit_seed{s}_seconds"] = time.time() - t0
        cs, sd = metrics.seed_condition_scores(per_seed_rows)
        cond_scores_out[a] = cs
        per_arm[a] = {"primary_pp": float(np.mean(list(cs.values()))), "seed_sd_of_mean": sd, "n_conditions": len(cs),
                      "mae_pp_mean": float(np.mean([r["mae_pp"] for rows in per_seed_rows for r in rows])),
                      "n_nonfinite": int(sum(r["n_nonfinite"] for rows in per_seed_rows for r in rows)), "n_params": int(arm.n_params)}
        rec.log(f"outer test {a}: {per_arm[a]['primary_pp']:.3f} pp (seed SD {sd:.3f}) over {len(cs)} conditions")
    metrics_out["outer_test"] = per_arm
    _json(os.path.join(run_dir, "condition_scores.json"), cond_scores_out)
    _finish(rec, run_dir, timings, metrics_out, t_start)
    return run_dir


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
