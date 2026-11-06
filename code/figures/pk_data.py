"""Loaders for run-directory files and statistics-step outputs (formats: code/README.md run record + code/figures/README.md).

READ-ONLY by rule (PREREG_v4 section 20, GATE_freeze_audit re-check rev. 19): nothing in this module computes an interval, test, p-value, tier, count of positive
conditions, effect size or bootstrap. The only transformations are plot-only: selecting rows, sorting by a supplied value, rank picks, unit conversion of a supplied
log ratio, and the min / max envelope merge of bands that the run writer already defines as min / max over members.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

import pk_style as ps

GRID_M = (8, 16, 32)
G1, G4 = (8, "2"), (32, "full")
CELL_NAME = {G1: "g1", G4: "g4"}


# ------------------------------------------------------------------------------------------------ run directories
def run_files(run: Path, *names):
    run = Path(run)
    return [ps.need(run / n, f"(run directory {run.name}; see code/figures/README.md)") for n in names]


def expand_runs(arg):
    """`arg`: a run directory, a directory whose sub-directories are run directories (config.json inside), or a comma-separated list of those -> sorted list of run dirs"""
    out = []
    for part in str(arg).split(","):
        p = Path(part.strip())
        if (p / "config.json").exists():
            out.append(p)
        elif p.is_dir():
            out += sorted(q for q in p.iterdir() if q.is_dir() and (q / "config.json").exists())
        else:
            raise SystemExit(f"MISSING INPUT: {p}  (run directory or directory of run directories)")
    if not out:
        raise SystemExit(f"MISSING INPUT: no run directory under {arg}")
    return out


def run_config(run):
    return ps.load_json(run_files(run, "config.json")[0])


def run_m(run):
    m = run_config(run).get("m")
    return 32 if m is None else int(m)


def runs_by_m(runs):
    out = {}
    for r in runs:
        out.setdefault(run_m(r), []).append(Path(r))
    return out


def k_suffix(run, k):
    """file-name suffix and predictions phase of the grid cell k ('0', '2', 'full') of a run: the primary k keeps the plain names (run.py)"""
    met = load_metrics(run)
    primary = met.get("k_primary", "full")
    if "k_labels" not in met:                                  # grid-free run (Test C, S2): one cell, plain names
        return "", "outer_test"
    if str(k) not in [str(x) for x in met["k_labels"]]:
        raise SystemExit(f"MISSING INPUT: cell k={k} is not in {Path(run).name}/metrics.json k_labels {met['k_labels']}")
    return ("", "outer_test") if str(k) == str(primary) else (f"_k{k}", f"outer_test_k{k}")


# ------------------------------------------------------------------------------------------------ run-writer files
def load_predictions(run, phase="outer_test"):
    (p,) = run_files(run, "predictions.csv")
    df = pd.read_csv(p, dtype={"seed": str})
    return df[df.phase == phase].copy()


def load_cell_predictions(runs, k):
    """predictions of the grid cell k of every run in `runs` (one outer fold each), concatenated"""
    parts = []
    for r in runs:
        _, phase = k_suffix(r, k)
        parts.append(load_predictions(r, phase))
    return pd.concat(parts, ignore_index=True)


def load_window(run):
    (p,) = run_files(run, "window.csv")
    return pd.read_csv(p)


def load_windows(runs):
    return pd.concat([load_window(r) for r in runs], ignore_index=True).drop_duplicates(["cell_id", "t"])


def load_scores(run, k=None):
    suf = k_suffix(run, k)[0] if k is not None else ""
    (p,) = run_files(run, f"condition_scores{suf}.json")
    return ps.load_json(p)


def load_scores_runs(runs, k=None):
    """arm -> condition -> score over the runs (one outer fold each: disjoint condition sets)"""
    out = {}
    for r in runs:
        for arm, d in load_scores(r, k).items():
            out.setdefault(arm, {}).update(d)
    return out


def load_cell_scores(run, k=None):
    suf = k_suffix(run, k)[0] if k is not None else ""
    (p,) = run_files(run, f"cell_scores{suf}.json")
    return ps.load_json(p)


def load_cell_scores_runs(runs, k=None):
    out = {}
    for r in runs:
        for arm, d in load_cell_scores(r, k).items():
            out.setdefault(arm, {}).update(d)
    return out


def load_comparators(runs):
    """alias (D*, AG) -> actual arm of the first run that names it (selection is per outer fold; the plotted arm of a condition is its fold's arm)"""
    out = {}
    for r in runs:
        p = Path(r) / "comparators.json"
        if p.exists():
            out[r.name] = {a: v["arm"] for a, v in ps.load_json(p).items() if isinstance(v, dict) and "arm" in v}
    return out


def load_metrics(run):
    (p,) = run_files(run, "metrics.json")
    return ps.load_json(p)


def cond_run(runs):
    """condition -> run directory that scored it (from the condition_scores.json of each run)"""
    out = {}
    for r in runs:
        for c in load_scores(r)["A1"]:
            out[c] = Path(r)
    return out


def forecast_curves(pred, win, cell_id, arm):
    """(window t, window y), (forecast t, observed y), ensemble y (seed 'ens', retention %), per-seed y [n_seed x n_t] for one cell and arm.
    The window of a grid cell = the window.csv rows of the cell before its first forecast point (window.csv is written for the primary k only)."""
    p = pred[(pred.cell_id == cell_id) & (pred.arm == arm)]
    tt = np.sort(p.t.unique())
    w = win[(win.cell_id == cell_id) & (win.t < tt.min())].sort_values("t")
    ens = p[p.seed == "ens"].sort_values("t")
    seeds = sorted(s for s in p.seed.unique() if s != "ens")
    Y = np.stack([p[p.seed == s].sort_values("t").pred_retention.values * 100 for s in seeds]) if seeds else np.empty((0, len(tt)))
    return (w.t.values, w.retention.values * 100), (ens.t.values, ens.true_retention.values * 100), ens.pred_retention.values * 100, Y


def rank_pick(items, key, q):
    """item at relative rank q (0 = lowest key, 1 = highest) of `items` sorted by the supplied `key` (a rule, not a choice; no quantile is computed)"""
    s = sorted(items, key=key)
    return s[int(round(q * (len(s) - 1)))]


def pick_cell(cell_scores_arm, cond):
    """the replicate cell of `cond` at the middle rank of the supplied cell scores of one arm"""
    cells = [c for c, v in cell_scores_arm.items() if v["cond"] == cond]
    return rank_pick(cells, lambda c: cell_scores_arm[c]["rmse_pp"], 0.5)


# ------------------------------------------------------------------------------------------------ statistics-step outputs
def load_stats(path):
    """analysis/contrasts_v4_B.json (stats_step.run_stats_v4)"""
    d = ps.load_json(ps.need(Path(path), "(statistics step output contrasts_v4_B.json)"))
    for k in ("estimated", "effective_tiers", "secondary", "primary"):
        if k not in d:
            raise SystemExit(f"MISSING INPUT: {path} has no key {k!r} (not a stats_v4 output)")
    return d


def load_analysis_json(analysis_dir, name, required=True):
    p = Path(analysis_dir) / name
    if not p.exists():
        if required:
            raise SystemExit(f"MISSING INPUT: {p}  (statistics step output)")
        return None
    return ps.load_json(p)


def est_rows(stats, comp, cell=None):
    """rows of stats['estimated'] for a comparator (all cells, ordered m then k) or one cell"""
    rows = [r for r in stats["estimated"]["rows"] if r["comparator"] == comp and (cell is None or tuple(r["cell"]) == (cell[0], str(cell[1])))]
    order = {"0": 0, "2": 1, "full": 2}
    rows.sort(key=lambda r: (r["cell"][0], order.get(str(r["cell"][1]), 9)))
    return rows


# gated / secondary contrast of each (comparator, cell): the key under which the statistics step stores its tier
TIER_KEY = {("D*", G1): "P1", ("A9", G1): "P2", ("A2", G1): "QH_g1", ("A2", G4): "QH_g4",
            ("A10", G1): "QA10_g1", ("A10", G4): "QA10_g4", ("A10P", G1): "QA10_g1", ("A10P", G4): "QA10_g4"}


def tier_read(stats, comp, cell):
    """the tier the statistics step assigned to the contrast of `comp` at `cell` (str tier, bool for P2, or None for a cell that is not gated); nothing is computed"""
    key = TIER_KEY.get((comp, (cell[0], str(cell[1]))))
    if key is None:
        return None
    if key in stats["effective_tiers"]:
        return stats["effective_tiers"][key]
    return stats["secondary"]["tests"][key]["tier"]


def tier_text(v):
    """display text of a supplied tier value"""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "met" if v else "not met"
    return {"S": "S", "N": "N", "none": "–", "reverse S": "rev. S", "-": "–"}.get(v, str(v))


def pct_from_log(x):
    """relative reduction of the error, % (unit conversion of a supplied median log ratio L = ln(S_comparator / S_A1); same formula as stats_v4.pct_reduction)"""
    return 100.0 * (1.0 - float(np.exp(-x)))


def merge_bands(bands):
    """envelope merge of run-writer bands {mean, lo, hi} (lo / hi are min / max over members, so the merge min of lo, max of hi is exact; mean = average of the run means,
    equal weights because every run has the same member count). Plot-only; the statistics step's physval_11a.json is preferred wherever it carries the quantity."""
    lo = np.min([np.asarray(b["lo"], float) for b in bands], axis=0)
    hi = np.max([np.asarray(b["hi"], float) for b in bands], axis=0)
    mean = np.mean([np.asarray(b["mean"], float) for b in bands], axis=0)
    return dict(lo=lo, hi=hi, mean=mean)
