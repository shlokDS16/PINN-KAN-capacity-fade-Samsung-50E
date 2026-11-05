"""Diagnostics of the test-time inversion (D023 judge section 4). Descriptive, no consequence for any state, tier or sentence.

    convergence share      logged by `inversion.solve` for every call (inner-CV calls included: a count only)
    budget sensitivity     the same inversion with the cap doubled (200): the largest absolute forecast change per cell, p99 and max (pp)
    start spread           prior mode + three seeded diagnostic starts (z ~ N(0, 0.5^2), delta ~ N(0, TAU^2)), each run to convergence: range of the forecast across the four per cell
                           (median, p95, max pp); seed stream SeedSequence([20261105, crc32("inv|<fold>|<arm>|<m>|<k>|<j>")]) (the seed rule of PREREG section 8; no second root)
    basin statement        share of cells where a diagnostic start reached a minimum with objective lower than the prior-mode minimum by more than 1e-6 (1 + |f|), and the share of cells
                           whose forecast differs by more than 1 pp between the prior-mode minimum and the lowest-objective diagnostic minimum
    rows (v) and (vi)      forecasts from each diagnostic start j = 1..3 and with the z-prior weights 4 and 16 (inference only, no refit); the run writer scores them (descriptive rows,
                           outside the closed list (i)-(iv) of 9.8)

Rules that keep this from becoming an analysis choice: it takes WINDOW cells only (no label, no forecast truth enters any function here); it is called after the primary scores are written;
nothing is selected, re-run, dropped or re-weighted because of it."""
import zlib

import numpy as np
import torch

from . import inversion
from .law import batch_forecast_query, batch_from_windows

DIAG_STARTS = 3
SPREAD_SD_Z = 0.5
BASIN_PP = 1.0


def diag_rng(fold, arm, m, k, j):
    return np.random.default_rng(np.random.SeedSequence([20261105, zlib.crc32(f"inv|{fold}|{arm}|{m}|{k}|{j}".encode())]))


def problem_for(arm, wcells, z_weight=None):
    """the arm's inversion problem on window cells (window labels only) and the label-free forecast query"""
    from .hard import HardODE
    from .pinn import DataOnlyF, PINNModel
    mdl = arm.model
    spec = arm.spec
    if isinstance(mdl, PINNModel):
        bw = batch_from_windows(spec, wcells, indicator=mdl.beta is not None)
        return inversion.pinn_problem(mdl, bw, batch_forecast_query(spec, wcells), float(arm.hp.get("lam_res", 1.0)), arm.seed, z_weight=z_weight), "pinn"
    if isinstance(mdl, DataOnlyF):
        bw = batch_from_windows(spec, wcells, indicator=mdl.B is not None)
        return inversion.data_problem(mdl, bw, batch_forecast_query(spec, wcells), z_weight), "data"
    if isinstance(mdl, HardODE):
        bw = batch_from_windows(spec, wcells, indicator=mdl.beta is not None)
        return inversion.hard_problem(mdl, bw, batch_forecast_query(spec, wcells)), "hard"
    raise TypeError(f"no inversion for {type(mdl)}")


def inverts(arm):
    from .hard import HardODE
    from .pinn import DataOnlyF, PINNModel
    return isinstance(getattr(arm, "model", None), (PINNModel, DataOnlyF, HardODE))


def _pp(a, b, ids):
    return np.array([100.0 * float(np.max(np.abs(np.asarray(a[c]) - np.asarray(b[c])))) for c in ids])


def _range_pp(preds, ids):
    return np.array([100.0 * float(np.max(np.ptp(np.stack([np.asarray(q[c]) for q in preds]), axis=0))) for c in ids])


def _q(x, qs=(50, 95, 99)):
    return {f"p{q}": float(np.percentile(x, q)) for q in qs} | {"max": float(np.max(x))} if len(x) else {}


def diagnose(arm, wcells, arm_label, fold, m, k, full=False, rows=False):
    """-> dict. Always: convergence at the cap, cap-doubling change (p99, max pp). full (A1, A9, AG): start spread, basin shares. rows: forecasts of rows (v)/(vi) under 'forecasts'."""
    prob, kind = problem_for(arm, wcells)
    keep = ~prob["ref_only"]
    ids = [c for c, kp in zip(prob["ids"], keep) if kp]
    base = inversion.solve(prob, kind, log=False)
    out = {"arm": arm_label, "fold": fold, "m": m, "k": k, "kind": kind, "n_cells": int(len(prob["ids"])), "n_inverted": int(keep.sum()),
           "convergence_share": float(base.converged[torch.as_tensor(keep)].float().mean()) if keep.any() else 1.0, "gnorm_max": float(base.gnorm[torch.as_tensor(keep)].max()) if keep.any() else 0.0}
    if not keep.any():
        return out
    p0 = prob["predict"](base.P)
    dbl = inversion.solve(prob, kind, cap=2 * inversion.CAP, log=False)
    out["cap_doubling_change_pp"] = _q(_pp(p0, prob["predict"](dbl.P), ids), (99,))
    forecasts = {}
    if full or rows:
        res = [base]
        preds = [p0]
        starts = []
        for j in range(1, DIAG_STARTS + 1):
            r = diag_rng(fold, arm_label, m, k, j)
            sd = np.where(prob["sd"] == 1.0, SPREAD_SD_Z, prob["sd"])
            S = prob["P0"] + torch.tensor(r.normal(0.0, 1.0, size=(prob["C"], prob["p"])) * sd, dtype=prob["P0"].dtype)
            rj = inversion.solve(prob, kind, P0=S, log=False)
            res.append(rj)
            preds.append(prob["predict"](rj.P))
            starts.append(j)
        sp = _range_pp(preds, ids)
        out["start_spread_pp"] = _q(sp, (50, 95))
        f = torch.stack([r.f for r in res])                                      # (4, C)
        keep_t = torch.as_tensor(keep)
        tol = 1e-6 * (1.0 + f[0].abs())
        lower = ((f[1:] < f[0][None] - tol[None]).any(0) & keep_t)
        best = f[1:].argmin(0)
        diff = np.zeros(prob["C"])
        for c, cid in enumerate(prob["ids"]):
            if keep[c]:
                diff[c] = 100.0 * float(np.max(np.abs(np.asarray(preds[1 + int(best[c])][cid]) - np.asarray(p0[cid]))))
        out["basin"] = {"share_lower_objective": float(lower.float().sum() / keep.sum()), "share_forecast_differs_gt_1pp": float(((torch.tensor(diff) > BASIN_PP) & keep_t).float().sum() / keep.sum()), "threshold_pp": BASIN_PP}
        if rows:
            forecasts["v"] = {j: preds[j] for j in starts}
    if rows and kind in ("pinn", "data"):
        for w in (4.0, 16.0):
            pw, _ = problem_for(arm, wcells, z_weight=w)
            forecasts.setdefault("vi", {})[int(w)] = pw["predict"](inversion.solve(pw, kind, log=False).P)
    if forecasts:
        out["forecasts"] = forecasts
    return out


def summarise(records):
    """pool the logged inversion calls by (arm, k): convergence share and counts (the table of the Supplement)"""
    by = {}
    for r in records:
        by.setdefault((r.get("arm"), r.get("k")), []).append(r)
    return {f"{a}|{k}": inversion.pooled_convergence(v) for (a, k), v in sorted(by.items(), key=lambda x: str(x[0]))}
