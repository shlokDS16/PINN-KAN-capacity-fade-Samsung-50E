"""Negative control (runs/prereg/NEGCONTROL_RULING.md, D014).

NC-1 (gate G): label invariance. Every held-out cell's post-window retention is replaced by garbage (`scramble_cells`) and the SAME fitted arms predict again;
the predictions must be bit-identical (max |diff| = 0, same forecast times). In every confirmatory run this is the predict-stage check (`check_invariance` -> invariance.json);
`run_nc1_full` repeats the whole pipeline (tuning included) on synthetic data with scrambled test labels and compares predictions, tuning_done.json and margins_inputs.json.
NC-2 (interpretive, not gating) is computed in stats_step.nc2 from a `permute_stress` run on Test B.
Seed rule for every Monte Carlo step: SeedSequence([20261105, crc32(label)]) (`mc_rng`)."""
import copy
import json
import os
import zlib

import numpy as np

from .data import prepare_many

MC_SEED_ROOT = 20261105


def mc_rng(label):
    return np.random.default_rng(np.random.SeedSequence([MC_SEED_ROOT, zlib.crc32(label.encode())]))


class InvarianceError(RuntimeError):
    """gate G tripped: predictions changed when held-out post-window labels were replaced by garbage"""


def scramble_cells(cells, rule, spec):
    """Copies of `cells` whose retention AFTER the window is garbage: ret_new = ret[w] - k (ret[w] - ret) + eps, k ~ U(0.3, 2.5) per cell, eps ~ N(0, 0.02^2), clipped to
    [0, 1.1]; with a life level L: ret_new = L + k (ret - L) + eps so that the forecast set (it ends at the first point below L) is unchanged (asserted). Window points are untouched."""
    out = []
    L = spec.life_level
    for c in cells:
        w = rule.window_end(c)
        if w < 0 or w >= c.n - 1:
            out.append(c)
            continue
        rng = mc_rng("NC1|" + c.cell_id)
        k = float(rng.uniform(0.3, 2.5))
        eps = rng.normal(0.0, 0.02, c.n)
        idx = np.arange(w + 1, c.n)
        ret = c.ret.copy()
        if L is None:
            new = ret[w] - k * (ret[w] - c.ret[idx]) + eps[idx]
        else:
            new = L + k * (c.ret[idx] - L) + eps[idx]
        ret[idx] = np.clip(new, 0.0, 1.1)
        if L is not None:
            below = np.where(c.ret < L)[0]
            last = int(below[0]) if len(below) else None
            for i in idx:
                if last is None or i < last:
                    ret[i] = max(ret[i], L + 1e-6)
                elif i == last:
                    ret[i] = min(ret[i], L - 1e-6)
            nb = np.where(ret < L)[0]
            assert (int(nb[0]) if len(nb) else None) == last, "scramble changed the forecast set"
        n = copy.copy(c)
        n.ret = ret
        out.append(n)
    return out


def check_invariance(predict_fn, cells, rule, spec, oracle=False, predict_rule=None, base_preds=None, base_prepared=None):
    """Re-predict with scrambled post-window labels. `predict_fn(list[WindowCell]) -> {cell_id: array}`. `predict_rule` (default `rule`) builds the windows given to the
    predictor; a leaky predict_rule (window one check-up too long) must be caught. Returns dict(passed, max_abs_diff, n_rows, forecast_sets_equal)."""
    pr = predict_rule or rule
    p0 = base_prepared if (base_prepared is not None and predict_rule is None) else prepare_many(cells, pr, oracle)
    p1 = prepare_many(scramble_cells(cells, rule, spec), pr, oracle)
    same_ids = [p.cell.cell_id for p in p0] == [p.cell.cell_id for p in p1]
    same_times = same_ids and all(np.array_equal(a.win.t_fc, b.win.t_fc) for a, b in zip(p0, p1))
    if not same_times:
        return dict(passed=False, max_abs_diff=float("nan"), n_rows=0, forecast_sets_equal=False)
    a = base_preds if (base_preds is not None and predict_rule is None) else predict_fn([p.win for p in p0])
    b = predict_fn([p.win for p in p1])
    diffs = [float(np.max(np.abs(np.asarray(a[k]) - np.asarray(b[k])))) if len(a[k]) else 0.0 for k in a]
    n = int(sum(len(a[k]) for k in a))
    mx = max(diffs) if diffs else 0.0
    return dict(passed=bool(mx == 0.0), max_abs_diff=float(mx), n_rows=n, forecast_sets_equal=True)


def summarise(records):
    """records: {'arm|seed': check dict} -> invariance.json body"""
    mx = max((r["max_abs_diff"] for r in records.values()), default=0.0)
    return dict(passed=bool(all(r["passed"] for r in records.values())), max_abs_diff=float(mx), n_rows=int(sum(r["n_rows"] for r in records.values())), tolerance=0.0,
                per_arm_seed=records, scramble="post-window retention replaced by garbage (NEGCONTROL_RULING section 3), same fitted arms and seeds, predict stage")


def compare_runs(dir_a, dir_b):
    """full-pipeline NC-1 on two run directories (clean vs scrambled test labels): prediction columns, tuning_done.json, margins_inputs.json must be identical"""
    import pandas as pd
    pa, pb = pd.read_csv(os.path.join(dir_a, "predictions.csv")), pd.read_csv(os.path.join(dir_b, "predictions.csv"))
    keys = ["phase", "arm", "seed", "cell_id", "cond", "t"]
    same_keys = len(pa) == len(pb) and bool((pa[keys].astype(str).values == pb[keys].astype(str).values).all())
    mx = float(np.max(np.abs(pa[pa.phase == "outer_test"].pred_retention.values - pb[pb.phase == "outer_test"].pred_retention.values))) if same_keys else float("nan")
    # the inner OOF predictions use only training labels: also identical
    mi = float(np.max(np.abs(pa[pa.phase == "inner_oof"].pred_retention.values - pb[pb.phase == "inner_oof"].pred_retention.values))) if same_keys else float("nan")
    same = {}
    for f in ("tuning_done.json", "margins_inputs.json"):
        same[f] = json.load(open(os.path.join(dir_a, f))) == json.load(open(os.path.join(dir_b, f)))
    return dict(passed=bool(same_keys and mx == 0.0 and mi == 0.0 and all(same.values())), same_row_keys=same_keys, max_abs_diff_outer=mx, max_abs_diff_inner_oof=mi,
                n_outer_rows=int((pa.phase == "outer_test").sum()), identical_records=same)
