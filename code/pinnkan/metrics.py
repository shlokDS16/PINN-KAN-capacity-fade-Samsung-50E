"""Metrics (PREREG_v2 section 6). Retention is a fraction; errors are reported in percentage points (pp).

Primary: cell-level RMSE over the forecast set, averaged within condition (mean over the condition's scored cells), then over conditions.
A non-finite forecast is scored with the persistence error (last window retention) and counted."""
import numpy as np


def clean_forecast(pred, y_last):
    """-> (pred with non-finite replaced by persistence, number replaced)"""
    pred = np.asarray(pred, float).copy()
    bad = ~np.isfinite(pred)
    pred[bad] = y_last
    return pred, int(bad.sum())


def score_prepared(preds, prepared):
    """per-cell rows: cell, cond, rmse_pp, mae_pp, mape_pct, n_fc, n_nonfinite (+ arrays _t, _pred, _true). `preds`: cell_id -> retention at the forecast times."""
    rows = []
    for p in prepared:
        pr, nbad = clean_forecast(preds[p.cell.cell_id], p.win.y_last)
        e = (pr - p.fc_true) * 100.0
        rows.append(dict(cell=p.cell.cell_id, cond=p.cell.cond, rmse_pp=float(np.sqrt(np.mean(e ** 2))), mae_pp=float(np.mean(np.abs(e))),
                         mape_pct=float(100.0 * np.mean(np.abs(pr - p.fc_true) / np.maximum(np.abs(p.fc_true), 1e-9))), n_fc=len(e), n_nonfinite=nbad,
                         _t=p.win.t_fc, _pred=pr, _true=p.fc_true))   # underscore keys: arrays for predictions.csv, stripped from json
    return rows


def ensemble_rows(per_seed_preds, prepared):
    """D020 C1: rows of the five-seed prediction ensemble. Per cell and check-up the forecast is the mean over the seeds of the seed's forecast in retention space; a non-finite
    forecast of a seed is replaced by the persistence forecast BEFORE averaging (the per-seed rule of `clean_forecast`, applied seed-wise) and counted per seed.
    `per_seed_preds`: list over seeds of {cell_id: forecast}. One seed, or seeds that agree, give exactly the per-seed rows."""
    mean = {}
    by_seed = {}
    for p in prepared:
        cid = p.cell.cell_id
        cleaned = []
        for preds in per_seed_preds:
            pr, nb = clean_forecast(preds[cid], p.win.y_last)
            cleaned.append(pr)
            by_seed.setdefault(cid, []).append(nb)
        mean[cid] = cleaned[0] if all(np.array_equal(cleaned[0], x) for x in cleaned[1:]) else np.mean(np.stack(cleaned), axis=0)      # agreeing seeds (one fit, a deterministic arm): exactly that forecast
    rows = score_prepared(mean, prepared)
    for r in rows:
        r["n_nonfinite_by_seed"] = by_seed[r["cell"]]
        r["n_nonfinite"] = int(sum(by_seed[r["cell"]]))
    return rows


def ensemble_condition_scores(per_seed_preds, prepared):
    """-> (condition -> mean over its scored cells of the cell RMSE of the ensemble forecast (pp), rows)"""
    rows = ensemble_rows(per_seed_preds, prepared)
    return condition_scores(rows), rows


def cell_scores_from_rows(rows):
    """cell -> {cond, rmse_pp, n_fc} for one set of rows (the ensemble's cell-level scores behind its condition scores)"""
    return {r["cell"]: dict(cond=r["cond"], rmse_pp=float(r["rmse_pp"]), n_fc=int(r["n_fc"])) for r in rows}


def condition_scores(rows):
    """condition -> mean over its scored cells of the cell RMSE (pp)"""
    by = {}
    for r in rows:
        by.setdefault(r["cond"], []).append(r["rmse_pp"])
    return {c: float(np.mean(v)) for c, v in by.items()}


def primary_score(rows):
    cs = condition_scores(rows)
    return float(np.mean(list(cs.values()))) if cs else float("nan")


def seed_condition_scores(per_seed_rows):
    """per-condition score = mean over seeds of that condition's RMSE (prereg 6/8); also the seed SD of the cross-condition mean."""
    per_seed = [condition_scores(r) for r in per_seed_rows]
    conds = sorted(set.intersection(*[set(d) for d in per_seed]))
    mat = np.array([[d[c] for c in conds] for d in per_seed])
    sd = float(mat.mean(1).std(ddof=1)) if len(per_seed) > 1 else 0.0
    return dict(zip(conds, mat.mean(0).tolist())), sd


def seed_cell_scores(per_seed_rows):
    """cell -> {cond, rmse_pp (mean over seeds), n_fc}: the cell-level scores behind the condition scores (second stage of the two-stage bootstrap, 9.8(d))"""
    cells = sorted(set.intersection(*[{r["cell"] for r in rows} for rows in per_seed_rows]))
    out = {}
    for c in cells:
        rs = [next(r for r in rows if r["cell"] == c) for rows in per_seed_rows]
        out[c] = dict(cond=rs[0]["cond"], rmse_pp=float(np.mean([r["rmse_pp"] for r in rs])), n_fc=int(rs[0]["n_fc"]))
    return out


def condition_meta(prepared):
    """condition -> {n_cells (scored), lab: {lab: n cells}, stage: {stage: n cells}}; identifiers of the scored cells only, no label"""
    out = {}
    for p in prepared:
        e = out.setdefault(p.cell.cond, dict(n_cells=0, lab={}, stage={}))
        e["n_cells"] += 1
        e["lab"][p.cell.lab or ""] = e["lab"].get(p.cell.lab or "", 0) + 1
        e["stage"][p.cell.stage or ""] = e["stage"].get(p.cell.stage or "", 0) + 1
    return out


def train_condition_meta(cells):
    """cycling training condition -> {n_cells, lab, labs}; identifiers only. `lab` is the frozen map of runs/prereg/lab_map.json (D024 section 4) for Samsung conditions,
    the local majority (ties alphabetical) for conditions not in the map; `labs` counts the training cells."""
    out = {}
    for c in cells:
        if c.kind != "cycling":
            continue
        e = out.setdefault(c.cond, {"n_cells": 0, "labs": {}})
        e["n_cells"] += 1
        e["labs"][c.lab or ""] = e["labs"].get(c.lab or "", 0) + 1
    from . import labmap
    for cond, e in out.items():
        e["lab"] = labmap.lab_of(cond, e["labs"])
    return out


def r2_pooled(preds, prepared):
    """R^2 = 1 - SSE / SST with (y_true, y_pred) in the correct argument order"""
    yt, yp = [], []
    for p in prepared:
        pr, _ = clean_forecast(preds[p.cell.cell_id], p.win.y_last)
        yt.append(p.fc_true)
        yp.append(pr)
    yt, yp = np.concatenate(yt), np.concatenate(yp)
    sst = float(np.sum((yt - yt.mean()) ** 2))
    return 1.0 - float(np.sum((yt - yp) ** 2)) / sst if sst > 0 else float("nan")


def _cross_time(t, y, level):
    """first time the series falls to `level` (linear interpolation), None when it does not"""
    for i in range(1, len(t)):
        if y[i - 1] > level >= y[i]:
            return float(t[i - 1] + (level - y[i - 1]) * (t[i] - t[i - 1]) / (y[i] - y[i - 1]))
    return None


def rul_error(prepared_item, pred, level=0.8):
    """RUL error (time units) for a cell whose TRUE series crosses `level` after the window; None otherwise. Time since the window end.
    A forecast that never crosses is scored at the last forecast time (lower bound)."""
    p = prepared_item
    t = np.concatenate([[p.win.t_last], p.win.t_fc])
    yt = np.concatenate([[p.win.y_last], p.fc_true])
    yp = np.concatenate([[p.win.y_last], pred])
    tt, tp = _cross_time(t, yt, level), _cross_time(t, yp, level)
    if tt is None:
        return None
    return float((tp if tp is not None else t[-1]) - tt)


def horizon_errors(pairs):
    """RMSE (pp) by forecast index after the window (1 = first post-window check-up); input: list of (pred, truth) arrays"""
    mx = max(len(a) for a, _ in pairs)
    out = {}
    for h in range(mx):
        e = [(a[h] - b[h]) * 100.0 for a, b in pairs if len(a) > h]
        out[h + 1] = {"rmse_pp": float(np.sqrt(np.mean(np.square(e)))), "n": len(e)}
    return out


def log_ratio(s_comp, s_pinn):
    """L_c = ln(S_comp,c / S_PINN,c) per condition (primary contrast scale, prereg 9.2)"""
    if set(s_comp) != set(s_pinn):
        raise ValueError(f"paired contrast needs identical condition sets; differ in {sorted(set(s_comp) ^ set(s_pinn))[:3]}")
    conds = sorted(s_comp)
    return {c: float(np.log(s_comp[c] / s_pinn[c])) for c in conds}


def permute_stress(cells, spec, seed):
    """Negative control (prereg 10): stress vectors (with the design throughput that goes with them) are permuted among the CYCLING conditions
    of this set; condition labels, window and forecast data stay. Called separately for the training and the test set."""
    import copy
    rng = np.random.default_rng([20261107, 31, int(seed)])
    conds = sorted({c.cond for c in cells if c.kind == "cycling"})
    donor = dict(zip(conds, [conds[i] for i in rng.permutation(len(conds))]))
    if len(conds) > 1:                      # a permutation without fixed points, so that the control really moves every stress vector
        for _ in range(100):
            if all(donor[c] != c for c in conds):
                break
            donor = dict(zip(conds, [conds[i] for i in rng.permutation(len(conds))]))
    raw_of = {c.cond: c.raw for c in cells if c.kind == "cycling"}
    out = []
    for c in cells:
        if c.kind != "cycling":
            out.append(c)
            continue
        n = copy.copy(c)
        n.raw = raw_of[donor[c.cond]].copy()
        n.efc = spec.efc_rate(n.raw) * c.t
        n.meta = {**c.meta, "stress_permuted_from": donor[c.cond]}
        out.append(n)
    return out
