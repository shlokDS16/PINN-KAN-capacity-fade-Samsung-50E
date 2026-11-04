"""P4: synthetic G2 (non-additive stress law) on the ISU design, 5 draws.
Hard ODE (exact integration) with KAN [3,h,1] stress map vs the same hard ODE with an additive spline GAM stress map (= KAN [3,1]) vs a free-G model.
Per draw: 12 of the 63 conditions held out; hyperparameters by inner grouped CV (2 folds by condition) on the 51 training conditions only, equal number
of random trials per arm, then one refit on all training conditions.  Endpoints: nRMSE of the recovered log-rate surface against the known truth on a fixed
500-point Latin-hypercube sample inside the design hull (primary); forecast RMSE on the held-out conditions beyond a 4-check-up window (secondary).

python -P code/pilots/p4_kan_vs_gam.py --draws 0,1 --out runs/pilot_P4 [--trials 5] ;  python -P code/pilots/p4_kan_vs_gam.py --aggregate --out runs/pilot_P4
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

SPACES = {
    "kan": {"hidden": [2, 3, 4], "grid": [3, 5, 8], "l2": [1e-4, 1e-3, 1e-2]},
    "gam": {"grid": [5, 10, 20, 30], "l2": [1e-4, 1e-3, 1e-2]},
    "free": {"width": [8, 16, 32], "wd": [1e-5, 1e-4, 1e-3]},
}
STEPS = {"kan": 1200, "gam": 1200, "free": 1000}


def fit_arm(kind, hp, d, seed):
    if kind == "free":
        return M.fit_free(d, hp["width"], hp["wd"], seed, steps=STEPS[kind])
    return M.fit_hard(d, kind, hp["grid"], hp.get("hidden", 1), hp["l2"], seed, steps=STEPS[kind])


def forecast_arm(kind, m, d_eval, dw):
    if kind == "free":
        z = M.fit_z_free(m, dw)
        with torch.no_grad():
            return M.free_predict(m, d_eval, z)
    delta = M.fit_delta_hard(m, dw)
    with torch.no_grad():
        return m.predict(d_eval, delta)


def eval_cells(design, ds, cells):
    d = PC.tensors(design, ds, cells)
    dw, fmask, tw = PC.window_forecast_split(d)
    return d, dw, fmask


def fold_score(design, ds, kind, hp, tr_conds, va_conds, seed):
    m = fit_arm(kind, hp, PC.tensors(design, ds, PC.cells_of(design, tr_conds)), seed)
    d, dw, fmask = eval_cells(design, ds, PC.scoring_cells(design, PC.cells_of(design, va_conds)))
    pred = forecast_arm(kind, m, d, dw)
    return PC.cell_condition_rmse_pp(pred, d, fmask)["noisy"]["cell_cond_mean"]


def recovered_log_rate(kind, m, design, lhs):
    x = torch.tensor(lhs, dtype=torch.float32)
    with torch.no_grad():
        if kind == "free":
            lnu = torch.log(torch.tensor(design.nu_norm_of_x(lhs), dtype=torch.float32)).unsqueeze(1)
            feat = torch.cat([x, lnu], 1)
            return (m.logG(torch.zeros(x.shape[0]), feat, torch.zeros(x.shape[0], m.z.shape[1])) - lnu[:, 0]).numpy()
        return m.log_rate(x).numpy()


def nrmse(fh, ft, center=False):
    if center:
        fh, ft = fh - fh.mean(), ft - ft.mean()
    return float(np.sqrt(np.mean((fh - ft) ** 2)) / (ft.max() - ft.min()))


def additive_floor(design, truth, lhs):
    """nRMSE of the best additive spline fit (grid 10, least squares on the LHS) to the TRUE surface: the GAM class floor for this draw."""
    from models.kan_spline import bspline_basis
    lay = M.KANLayer(3, 1, grid=10, k=3, lo=-1.0, hi=1.0)
    B = bspline_basis(torch.tensor(lhs, dtype=torch.float32), lay.knots, 3).reshape(lhs.shape[0], -1).numpy()
    B = np.hstack([B, np.ones((lhs.shape[0], 1))])
    f = truth.shape(lhs)
    coef, *_ = np.linalg.lstsq(B, f, rcond=None)
    return float(np.sqrt(np.mean((B @ coef - f) ** 2)) / (f.max() - f.min()))


def run_draw(draw, n_trials, out):
    t_draw = time.perf_counter()
    design = SG.Design(ROOT)
    ds = SG.make_dataset("G2", draw, design)
    test_conds = SG.split_conditions(draw)
    train_conds = np.setdiff1d(np.arange(design.n_cond), test_conds)
    lhs = design.hull_lhs(500)
    ft = ds.truth.log_rate(lhs)
    folds = PC.inner_folds(train_conds, draw)
    d_train = PC.tensors(design, ds, PC.cells_of(design, train_conds))
    test_cells = PC.scoring_cells(design, PC.cells_of(design, test_conds))
    d_test, dw_test, fmask = eval_cells(design, ds, test_cells)
    res = {"draw": draw, "params": ds.params, "level_c0": ds.truth.c0, "test_conditions": test_conds.tolist(), "n_train_cells": int(d_train["cell_cond"].shape[0]),
           "n_test_cells_scored": int(len(test_cells)), "additive_floor_nrmse_true_surface": additive_floor(design, ds.truth, lhs),
           "log_rate_range_true": float(ft.max() - ft.min()), "arms": {}}
    surf = {"lhs": lhs, "f_true": ft}
    for ki, kind in enumerate(["kan", "gam", "free"]):
        t0 = time.perf_counter()
        trials = PC.sample_trials(SPACES[kind], n_trials, seed=draw * 10 + ki)
        table = []
        for ti, hp in enumerate(trials):
            sc = [fold_score(design, ds, kind, hp, np.setdiff1d(train_conds, f), f, seed=1000 * draw + 10 * ti + j) for j, f in enumerate(folds)]
            table.append({"hp": hp, "inner_cv_rmse_pp": float(np.mean(sc)), "per_fold": sc})
        best = min(range(len(table)), key=lambda i: table[i]["inner_cv_rmse_pp"])
        hp = table[best]["hp"]
        m = fit_arm(kind, hp, d_train, seed=1000 * draw + 99)
        fh = recovered_log_rate(kind, m, design, lhs)
        pred = forecast_arm(kind, m, d_test, dw_test)
        fc = PC.cell_condition_rmse_pp(pred, d_test, fmask)
        with torch.no_grad():
            if kind == "free":
                tr_pred = M.free_predict(m, d_train, m.z)
            else:
                tr_pred = m.predict(d_train, m.delta)
        train_rmse_pp = float(torch.sqrt(((tr_pred - d_train["obs_y"]) ** 2).mean()) * 10)
        res["arms"][kind] = {
            "chosen_hp": hp, "n_params": M.n_params(m) - (m.delta.numel() if kind != "free" else m.z.numel()), "inner_cv": table,
            "nrmse_recovery": nrmse(fh, ft), "nrmse_recovery_centered": nrmse(fh, ft, center=True),
            "forecast_rmse_pp_cell_cond_mean": fc["noisy"]["cell_cond_mean"], "forecast_rmse_pp_pooled": fc["noisy"]["pooled"],
            "forecast_rmse_pp_vs_noiseless_truth": fc["truth"]["cell_cond_mean"], "train_rmse_pp": train_rmse_pp,
            "seconds": time.perf_counter() - t0, "edge_hp": {k: (hp[k] in (SPACES[kind][k][0], SPACES[kind][k][-1])) for k in hp},
        }
        surf["f_" + kind] = fh
        print(f"draw {draw} {kind}: nRMSE {res['arms'][kind]['nrmse_recovery']:.3f}  forecast {fc['noisy']['cell_cond_mean']:.2f} pp  hp {hp}  {res['arms'][kind]['seconds']:.0f} s", flush=True)
    res["seconds_total"] = time.perf_counter() - t_draw
    PC.save_json(res, os.path.join(out, f"draw_{draw}.json"))
    np.savez(os.path.join(out, f"surfaces_draw_{draw}.npz"), **surf)
    return res


def aggregate(out):
    files = sorted(glob.glob(os.path.join(out, "draw_*.json")))
    R = [json.load(open(f, encoding="utf8")) for f in files]
    n = len(R)
    g = lambda r, k, key: r["arms"][k][key]
    kan_lt_gam = sum(g(r, "kan", "nrmse_recovery") < g(r, "gam", "nrmse_recovery") for r in R)
    kan_lt_free = sum(g(r, "kan", "nrmse_recovery") < g(r, "free", "nrmse_recovery") for r in R)
    gam_lt_free = sum(g(r, "gam", "nrmse_recovery") < g(r, "free", "nrmse_recovery") for r in R)
    struct_lt_free = sum(min(g(r, "kan", "nrmse_recovery"), g(r, "gam", "nrmse_recovery")) < g(r, "free", "nrmse_recovery") for r in R)
    med = lambda k, key: float(np.median([g(r, k, key) for r in R]))
    summ = {
        "n_draws": n, "draws": [r["draw"] for r in R],
        "kan_lower_nrmse_than_gam_draws": kan_lt_gam, "kan_lower_nrmse_than_free_draws": kan_lt_free,
        "gam_lower_nrmse_than_free_draws": gam_lt_free, "best_structured_lower_than_free_draws": struct_lt_free,
        "rule_kan_vs_gam": f"KAN lower nRMSE than additive GAM in >= 4 of 5 draws: {kan_lt_gam} of {n}",
        "rule_structured_vs_free": f"KAN-structured below free G in >= 4 of 5 draws: {kan_lt_free} of {n}",
        "go_kan_vs_gam": bool(n == 5 and kan_lt_gam >= 4), "go_structured_vs_free": bool(n == 5 and kan_lt_free >= 4),
        "median_nrmse": {k: med(k, "nrmse_recovery") for k in ("kan", "gam", "free")},
        "median_nrmse_centered": {k: med(k, "nrmse_recovery_centered") for k in ("kan", "gam", "free")},
        "median_forecast_rmse_pp": {k: med(k, "forecast_rmse_pp_cell_cond_mean") for k in ("kan", "gam", "free")},
        "median_ratio_kan_over_free": float(np.median([g(r, "kan", "nrmse_recovery") / g(r, "free", "nrmse_recovery") for r in R])),
        "median_ratio_gam_over_free": float(np.median([g(r, "gam", "nrmse_recovery") / g(r, "free", "nrmse_recovery") for r in R])),
        "median_ratio_kan_over_gam": float(np.median([g(r, "kan", "nrmse_recovery") / g(r, "gam", "nrmse_recovery") for r in R])),
        "kan_forecast_lower_than_gam_draws": sum(g(r, "kan", "forecast_rmse_pp_cell_cond_mean") < g(r, "gam", "forecast_rmse_pp_cell_cond_mean") for r in R),
        "kan_forecast_lower_than_free_draws": sum(g(r, "kan", "forecast_rmse_pp_cell_cond_mean") < g(r, "free", "forecast_rmse_pp_cell_cond_mean") for r in R),
        "per_draw": [
            {"draw": r["draw"], "additive_floor": r["additive_floor_nrmse_true_surface"],
             **{f"{k}_nrmse": g(r, k, "nrmse_recovery") for k in ("kan", "gam", "free")},
             **{f"{k}_forecast_pp": g(r, k, "forecast_rmse_pp_cell_cond_mean") for k in ("kan", "gam", "free")},
             **{f"{k}_params": g(r, k, "n_params") for k in ("kan", "gam", "free")},
             **{f"{k}_hp": g(r, k, "chosen_hp") for k in ("kan", "gam", "free")}, "params": r["params"]} for r in R],
        "seconds_total_sum": float(sum(r["seconds_total"] for r in R)),
    }
    PC.save_json(summ, os.path.join(out, "summary.json"))
    print(json.dumps({k: v for k, v in summ.items() if k != "per_draw"}, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", default="0,1,2,3,4")
    ap.add_argument("--trials", type=int, default=8)
    ap.add_argument("--out", default=os.path.join(ROOT, "runs", "pilot_P4"))
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    if a.aggregate:
        aggregate(a.out)
    else:
        PC.write_config(a.out, "P4 (synthetic G2: KAN vs additive GAM vs free G)", {
            "spaces": SPACES, "fit_steps": STEPS, "optimiser": "Adam lr 0.02 (free G 0.01), cosine to 5 %", "n_trials_per_arm": a.trials, "inner_folds": 2, "draws_in_this_process": a.draws,
            "window": "first 4 check-ups after the initial one; delta_c / z_c fitted on the window with the model frozen",
            "endpoint": "nRMSE of recovered log-rate surface vs truth on lhs500 (primary); forecast RMSE pp on held-out conditions (secondary)",
            "go_rule": "KAN lower nRMSE than additive GAM in >= 4 of 5 draws AND KAN-structured below free G in >= 4 of 5 draws"})
        for dr in [int(x) for x in a.draws.split(",")]:
            run_draw(dr, a.trials, a.out)
