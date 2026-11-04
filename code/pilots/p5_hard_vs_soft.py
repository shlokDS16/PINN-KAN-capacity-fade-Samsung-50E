"""P5: hard ODE vs soft PINN under misspecification (G1) on the ISU design, 5 draws.
Same law (A/(1+y), A = exp(c + KAN[3,3,1](x)) nu_norm exp(delta_c)), same KAN, same per-cell offset, same data, same inner-CV budget (3 values of the one
regulariser per arm, 2 inner folds by condition, training conditions only).  Hard ODE: exact integration, delta_c MAP from the 4-check-up window.
Soft PINN: F(t,x,z) = t g(.) with residual dF/dt - A/(1+F); lambda_res in {0.01, 0.1, 1}; fixed label-free collocation sets; test cells: (z_c, delta_c)
inferred from the window plus the residual over (window end, t_max].  Endpoint: forecast RMSE beyond the window (pp, per cell, mean within condition,
then over conditions) on 12 held-out conditions.  Primary PINN variant = D010 section 2 collocation (a) from the end of each training record;
sensitivity variant = whole time axis.

python -P code/pilots/p5_hard_vs_soft.py --draws 0,1 --out runs/pilot_P5 ;  python -P code/pilots/p5_hard_vs_soft.py --aggregate --out runs/pilot_P5
"""
import argparse
import glob
import json
import os
import sys
import time

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import numpy as np  # noqa: E402
import torch  # noqa: E402

import p45_common as PC  # noqa: E402
from p45_common import M, SG, ROOT  # noqa: E402

torch.set_num_threads(1)
torch.set_num_interop_threads(1)

LAMS = [0.01, 0.1, 1.0]
L2S = [1e-4, 1e-3, 1e-2]
PINN_L2 = 1e-3
PINN_STEPS = 2500
HARD_STEPS = 1200


def t_end_of(d):
    return torch.zeros(d["cell_cond"].shape[0]).scatter_reduce(0, d["obs_cell"], d["obs_t"], "amax")


def pinn_predict(m, d, z):
    xo = d["x_cond"][d["cell_cond"]][d["obs_cell"]]
    with torch.no_grad():
        return m.net(d["obs_t"].unsqueeze(1), xo, z[d["obs_cell"]])[:, 0]


def make_col(design, d, variant, seed):
    lhs = design.hull_lhs(256, seed=777)
    hx = torch.tensor(lhs, dtype=torch.float32)
    hl = torch.log(torch.tensor(design.nu_norm_of_x(lhs), dtype=torch.float32))
    return M.make_collocation(d, t_end_of(d), hx, hl, seed, variant=variant)


def pinn_fit_and_forecast(design, ds, tr_cells, ev_cells, lam, variant, seed):
    d = PC.tensors(design, ds, tr_cells)
    col = make_col(design, d, variant, seed)
    m = M.fit_pinn(d, col, lam, PINN_L2, seed, steps=PINN_STEPS)
    de = PC.tensors(design, ds, ev_cells)
    dwe, fmask, twe = PC.window_forecast_split(de)
    z, delta = M.invert_pinn(m, dwe, lam, twe, seed + 5, pts_per_cell=d["obs_y"].numel() / d["cell_cond"].shape[0])
    pred = pinn_predict(m, de, z)
    return m, de, fmask, pred


def hard_fit_and_forecast(design, ds, tr_cells, ev_cells, l2, seed):
    d = PC.tensors(design, ds, tr_cells)
    m = M.fit_hard(d, "kan", 5, 3, l2, seed, steps=HARD_STEPS)
    de = PC.tensors(design, ds, ev_cells)
    dwe, fmask, _ = PC.window_forecast_split(de)
    delta = M.fit_delta_hard(m, dwe)
    with torch.no_grad():
        pred = m.predict(de, delta)
    return m, de, fmask, pred


def score(pred, de, fmask):
    return PC.cell_condition_rmse_pp(pred, de, fmask)["noisy"]["cell_cond_mean"]


def per_cell_rmse(pred, de, fmask):
    cell = de["obs_cell"][fmask]
    e = (pred[fmask] - de["obs_y"][fmask]) * 10
    C = de["cell_cond"].shape[0]
    se = torch.zeros(C).index_add_(0, cell, e ** 2)
    n = torch.zeros(C).index_add_(0, cell, torch.ones_like(e))
    return torch.sqrt(se / n.clamp_min(1)).tolist()


def run_draw(draw, out, variants):
    t_draw = time.perf_counter()
    design = SG.Design(ROOT)
    ds = SG.make_dataset("G1", draw, design)
    test_conds = SG.split_conditions(draw)
    train_conds = np.setdiff1d(np.arange(design.n_cond), test_conds)
    folds = PC.inner_folds(train_conds, draw)
    tr_cells = PC.cells_of(design, train_conds)
    ev_cells = PC.scoring_cells(design, PC.cells_of(design, test_conds))
    res = {"draw": draw, "params": ds.params, "level_c0": ds.truth.c0, "test_conditions": test_conds.tolist(), "n_train_cells": int(len(tr_cells)),
           "n_test_cells_scored": int(len(ev_cells)), "test_cells": [design.cell_names[c] for c in ev_cells], "arms": {}}

    # ---- hard ODE
    t0 = time.perf_counter()
    table = []
    for ti, l2 in enumerate(L2S):
        sc = []
        for j, f in enumerate(folds):
            ftr = PC.cells_of(design, np.setdiff1d(train_conds, f))
            fva = PC.scoring_cells(design, PC.cells_of(design, f))
            _, de, fm, pr = hard_fit_and_forecast(design, ds, ftr, fva, l2, seed=1000 * draw + 10 * ti + j)
            sc.append(score(pr, de, fm))
        table.append({"l2": l2, "inner_cv_rmse_pp": float(np.mean(sc)), "per_fold": sc})
    best = min(range(len(table)), key=lambda i: table[i]["inner_cv_rmse_pp"])
    m, de, fm, pr = hard_fit_and_forecast(design, ds, tr_cells, ev_cells, table[best]["l2"], seed=1000 * draw + 99)
    d_tr = PC.tensors(design, ds, tr_cells)
    with torch.no_grad():
        tr_rmse = float(torch.sqrt(((m.predict(d_tr, m.delta) - d_tr["obs_y"]) ** 2).mean()) * 10)
    fc = PC.cell_condition_rmse_pp(pr, de, fm)
    res["arms"]["hard"] = {"chosen": {"l2": table[best]["l2"]}, "inner_cv": table, "forecast_rmse_pp_cell_cond_mean": fc["noisy"]["cell_cond_mean"],
                           "forecast_rmse_pp_pooled": fc["noisy"]["pooled"], "forecast_rmse_pp_vs_noiseless_truth": fc["truth"]["cell_cond_mean"],
                           "train_rmse_pp": tr_rmse, "per_cell_rmse_pp": per_cell_rmse(pr, de, fm), "seconds": time.perf_counter() - t0,
                           "edge": table[best]["l2"] in (L2S[0], L2S[-1])}
    print(f"draw {draw} hard: forecast {fc['noisy']['cell_cond_mean']:.2f} pp  l2 {table[best]['l2']}  {res['arms']['hard']['seconds']:.0f} s", flush=True)

    # ---- PINN variants
    for variant in variants:
        t0 = time.perf_counter()
        table = []
        for li, lam in enumerate(LAMS):
            sc = []
            for j, f in enumerate(folds):
                ftr = PC.cells_of(design, np.setdiff1d(train_conds, f))
                fva = PC.scoring_cells(design, PC.cells_of(design, f))
                _, de, fm, pr = pinn_fit_and_forecast(design, ds, ftr, fva, lam, variant, seed=1000 * draw + 10 * li + j)
                sc.append(score(pr, de, fm))
            table.append({"lambda_res": lam, "inner_cv_rmse_pp": float(np.mean(sc)), "per_fold": sc})
        best = min(range(len(table)), key=lambda i: table[i]["inner_cv_rmse_pp"])
        lam = table[best]["lambda_res"]
        m, de, fm, pr = pinn_fit_and_forecast(design, ds, tr_cells, ev_cells, lam, variant, seed=1000 * draw + 99)
        fc = PC.cell_condition_rmse_pp(pr, de, fm)
        res["arms"]["pinn_" + variant] = {
            "chosen": {"lambda_res": lam}, "inner_cv": table, "forecast_rmse_pp_cell_cond_mean": fc["noisy"]["cell_cond_mean"],
            "forecast_rmse_pp_pooled": fc["noisy"]["pooled"], "forecast_rmse_pp_vs_noiseless_truth": fc["truth"]["cell_cond_mean"],
            "train_rmse_pp": float(np.sqrt(m.train_data_mse) * 10), "train_residual_msq_last_step": m.train_res_msq,
            "per_cell_rmse_pp": per_cell_rmse(pr, de, fm), "seconds": time.perf_counter() - t0, "edge": lam in (LAMS[0], LAMS[-1])}
        print(f"draw {draw} pinn_{variant}: forecast {fc['noisy']['cell_cond_mean']:.2f} pp  lambda {lam}  {res['arms']['pinn_' + variant]['seconds']:.0f} s", flush=True)
    res["seconds_total"] = time.perf_counter() - t_draw
    PC.save_json(res, os.path.join(out, f"draw_{draw}.json"))


def aggregate(out):
    R = [json.load(open(f, encoding="utf8")) for f in sorted(glob.glob(os.path.join(out, "draw_*.json")))]
    n = len(R)
    fc = lambda r, a: r["arms"][a]["forecast_rmse_pp_cell_cond_mean"]
    summ = {"n_draws": n, "draws": [r["draw"] for r in R]}
    for v in ("record_end", "whole_axis"):
        a = "pinn_" + v
        if all(a in r["arms"] for r in R):
            k = sum(fc(r, a) < fc(r, "hard") for r in R)
            summ[a] = {"pinn_lower_than_hard_draws": k, "go": bool(n == 5 and k >= 3), "median_forecast_pp": float(np.median([fc(r, a) for r in R])),
                       "median_ratio_pinn_over_hard": float(np.median([fc(r, a) / fc(r, "hard") for r in R])),
                       "chosen_lambda": [r["arms"][a]["chosen"]["lambda_res"] for r in R]}
    summ["hard_median_forecast_pp"] = float(np.median([fc(r, "hard") for r in R]))
    summ["per_draw"] = [{"draw": r["draw"], "params": r["params"], **{a: fc(r, a) for a in r["arms"]}} for r in R]
    summ["seconds_total_sum"] = float(sum(r["seconds_total"] for r in R))
    PC.save_json(summ, os.path.join(out, "summary.json"))
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", default="0,1,2,3,4")
    ap.add_argument("--variants", default="record_end,whole_axis")
    ap.add_argument("--out", default=os.path.join(ROOT, "runs", "pilot_P5"))
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    if a.aggregate:
        aggregate(a.out)
    else:
        PC.write_config(a.out, "P5 (synthetic G1: hard ODE vs soft PINN)", {
            "lambda_res_grid": LAMS, "hard_l2_grid": L2S, "pinn_l2": PINN_L2, "pinn_steps": PINN_STEPS, "hard_steps": HARD_STEPS,
            "pinn_arch": "F = t g(t,x,z), g = tanh MLP 32x3, z in R^2; KAN [3,3,1] grid 5 in the law (same as hard ODE); Adam lr 5e-3 cosine to 10 %",
            "collocation": "(a) 24 times per training cell from record end (primary) or from 0 (whole_axis) to t_max=1.8; (b) 256 hull LHS stress points x 16 times in [0,1.8]; "
                           "512 + 256 rows resampled per step; no calendar twins (ISU has no storage arm)",
            "window": "first 4 check-ups after the initial one", "draws_in_this_process": a.draws, "variants": a.variants,
            "go_rule": "PINN forecast RMSE beyond the window below the hard ODE in >= 3 of 5 draws (primary variant record_end)"})
        for dr in [int(x) for x in a.draws.split(",")]:
            run_draw(dr, a.out, a.variants.split(","))
