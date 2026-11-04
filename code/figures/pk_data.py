"""Loaders for run-directory files (formats: code/README.md run record + code/figures/README.md additions)."""
from pathlib import Path

import numpy as np
import pandas as pd

import pk_style as ps


def run_files(run: Path, *names):
    run = Path(run)
    return [ps.need(run / n, f"(run directory {run.name}; see code/figures/README.md)") for n in names]


def load_predictions(run, phase="outer_test"):
    (p,) = run_files(run, "predictions.csv")
    df = pd.read_csv(p)
    return df[df.phase == phase].copy()


def load_window(run):
    (p,) = run_files(run, "window.csv")
    return pd.read_csv(p)


def load_scores(run):
    (p,) = run_files(run, "condition_scores.json")
    return ps.load_json(p)


def load_metrics(run):
    (p,) = run_files(run, "metrics.json")
    return ps.load_json(p)


def load_contrasts(path):
    return ps.load_json(ps.need(Path(path), "(analysis step output contrasts_<test>.json)"))


def cell_curve(pred: pd.DataFrame, win: pd.DataFrame, cell_id: str, arm: str):
    """(window t, window y), (forecast t, observed y), per-seed predicted y [n_seed x n_t] for one cell and arm (retention %)."""
    w = win[win.cell_id == cell_id].sort_values("t")
    p = pred[(pred.cell_id == cell_id) & (pred.arm == arm)]
    seeds = sorted(p.seed.unique())
    tt = np.sort(p.t.unique())
    yobs = p[p.seed == seeds[0]].sort_values("t").true_retention.values * 100
    Y = np.stack([p[p.seed == s].sort_values("t").pred_retention.values * 100 for s in seeds])
    return (w.t.values, w.retention.values * 100), (tt, yobs), Y


def median_cell(pred, cond, arm="A1"):
    """Deterministic, non-cherry-picked cell of a condition: the replicate with the median cell RMSE of `arm`."""
    p = pred[(pred.cond == cond) & (pred.arm == arm)]
    r = (100 * (p.pred_retention - p.true_retention)).pow(2).groupby(p.cell_id).mean().pow(0.5).sort_values()
    return r.index[len(r) // 2], r
