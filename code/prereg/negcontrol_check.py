"""Statistician check for NEGCONTROL_RULING.md: one leak-free and two deliberately leaking variants of the real pinnkan pipeline on the
synthetic G2 demo (CPU, 1 thread, synthetic data only, never FROZEN, nothing here is a result).

Variants (all with permute_stress = True unless noted; arms A1, A9, R2; budgets of the builder's demo: 2 TPE trials, 2 inner folds, steps_scale 0.15):
  clean   : the pipeline as built
  leakA   : the outer-test cells are also put into the training set (grouping error)
  leakB   : the model's window of every test cell is one check-up longer than the window the forecast set assumes (off-by-one: the first
            forecast label is in the window)
  real    : clean, stress NOT permuted (for the stress-attribution contrast)
Each non-real variant is run twice: unmodified (X) and with every test cell's post-window labels replaced by garbage (Xs: a random
rescaling of the post-window loss plus noise, applied to the underlying cell so that a training duplicate carries the same garbage).
Label-invariance (NC-1): max |pred(X) - pred(Xs)| over all predictions (inner-CV and outer-test rows).
Usage: python -P negcontrol_check.py <ROOT> <synthetic seeds, comma list> [n_cyc_cond]
"""
import copy
import dataclasses
import json
import os
import sys

import numpy as np

ROOT = sys.argv[1]
SEEDS = [int(s) for s in sys.argv[2].split(",")]
NCYC = int(sys.argv[3]) if len(sys.argv) > 3 else 40
os.environ["PINNKAN_ROOT"] = ROOT
sys.path.insert(0, f"{ROOT}/code")
import pandas as pd  # noqa: E402
from pinnkan import run as R  # noqa: E402
from pinnkan.data import Prepared, WindowRule, prepare  # noqa: E402

OUT = f"{ROOT}/runs/prereg/stats_ruling/negctl"
os.makedirs(OUT, exist_ok=True)
_orig_build, _orig_prep = R.build_data, R.prepare_many
TEST_IDS = set()


def scramble(cells, rule, rng):
    for c in cells:
        w = rule.window_end(c)
        if w + 1 < c.n:
            tail = c.ret[w + 1:]
            k = rng.uniform(0.3, 2.5)
            new = c.ret[w] - k * (c.ret[w] - tail) + 0.02 * rng.standard_normal(len(tail))
            c.ret = np.concatenate([c.ret[: w + 1], np.clip(new, 0.0, 1.1)])


def install(variant, scr):
    def build(cfg, root, role):
        D = _orig_build(cfg, root, role)
        te = D["test"]
        if te:
            TEST_IDS.clear(); TEST_IDS.update(c.cell_id for c in te)
            rule = WindowRule.for_spec(D["spec"])
            if scr:
                scramble(te, rule, np.random.default_rng(99))
            if variant == "leakA":
                D["train"] = list(D["train"]) + [dataclasses.replace(copy.deepcopy(c), cell_id="dup_" + c.cell_id) for c in te]
        return D

    def prep_many(cells, rule, oracle=False):
        out = _orig_prep(cells, rule, oracle)
        if variant != "leakB":
            return out
        rule2 = dataclasses.replace(rule, k_cycling=(rule.k_cycling or 0) + 1, k_storage=(rule.k_storage or 0) + 1)
        res = []
        for p in out:
            if p.cell.cell_id not in TEST_IDS:
                res.append(p); continue
            p2 = prepare(p.cell, rule2, oracle)
            if p2 is None:
                res.append(p); continue
            w = dataclasses.replace(p.win, t_win=p2.win.t_win, y_win=p2.win.y_win, efc_win=p2.win.efc_win, efc_curve=p2.win.efc_curve)
            res.append(Prepared(p.cell, w, p.fc_true, p2.w_idx))
        return res
    R.build_data, R.prepare_many = build, prep_many


def do_run(seed, variant, scr):
    rid = f"nc_s{seed}_{variant}{'_scr' if scr else ''}"
    d = os.path.join(OUT, rid)
    if os.path.exists(os.path.join(d, "metrics.json")):
        return d
    install("clean" if variant == "real" else variant, scr)
    cfg = {"run_id": rid, "dataset": "synthetic", "mode": "confirmatory", "n_trials": 2, "inner_k": 2, "steps_scale": 0.15, "seeds": [0, 1, 2],
           "backbone": "tournament", "test": "B", "arms": ["A1", "A9", "R2"], "permute_stress": variant != "real", "diagnostics": False,
           "synthetic": {"kind": "G2", "n_cyc_cond": NCYC, "n_sto_cond": 19, "reps": 3, "seed": seed, "test_frac": 0.25}}
    R.run(cfg, root=ROOT, runs_dir=OUT)
    return d


def preds(d):
    p = pd.read_csv(os.path.join(d, "predictions.csv"))
    return p.set_index(["phase", "arm", "seed", "cell_id", "t"])


if __name__ == "__main__":
    for s in SEEDS:
        res = {"seed": s}
        try:
            do_run(s, "clean", False)
        except AssertionError as e:
            print("seed", s, "skipped:", e, flush=True)
            continue
        dirs = {}
        for v in ("clean", "leakA", "leakB"):
            dirs[v] = do_run(s, v, False)
            dirs[v + "_s"] = do_run(s, v, True)
        dirs["real"] = do_run(s, "real", False)
        for v in ("clean", "leakA", "leakB"):
            a, b = preds(dirs[v]), preds(dirs[v + "_s"])
            common = a.index.intersection(b.index)
            same_index = bool(a.index.equals(b.index))
            dp = (a.loc[common, "pred_retention"] - b.loc[common, "pred_retention"]).abs()
            outer = [i for i in common if i[0] == "outer_test"]
            res[v] = dict(n_rows=len(a), same_rows=same_index, max_abs_dpred=float(dp.max()), max_abs_dpred_outer=float(dp.loc[outer].max()) if outer else None,
                          cond_scores=json.load(open(os.path.join(dirs[v], "condition_scores.json"))),
                          negative_control=json.load(open(os.path.join(dirs[v], "metrics.json"))).get("negative_control"),
                          tuning_same=bool(json.load(open(os.path.join(dirs[v], "tuning_done.json")))["arms"] == json.load(open(os.path.join(dirs[v + "_s"], "tuning_done.json")))["arms"]))
        res["real"] = dict(cond_scores=json.load(open(os.path.join(dirs["real"], "condition_scores.json"))))
        json.dump(res, open(os.path.join(OUT, f"summary_s{s}.json"), "w"), indent=1)
        print("seed", s, "done", flush=True)
