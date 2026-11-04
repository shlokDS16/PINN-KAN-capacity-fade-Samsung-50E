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
    conds = sorted(set(s_comp) & set(s_pinn))
    return {c: float(np.log(s_comp[c] / s_pinn[c])) for c in conds}
