"""Shared helpers for P4 / P5: tensors, windows, inner grouped CV tuning, forecast metrics. CPU only."""
import json
import os
import subprocess
import sys

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
import numpy as np
import torch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.join(ROOT, "code", "pilots"))

from models import ageing_p45 as M  # noqa: E402
import synth_gen as SG  # noqa: E402

K_WINDOW = 4  # check-ups after the initial one that form the window
MIN_PTS = K_WINDOW + 1 + 3  # a cell is scored when it has >= 3 check-ups after the window


def git_info():
    def run(*a):
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()

    mine = ["code/pilots/synth_gen.py", "code/pilots/p45_common.py", "code/pilots/p4_kan_vs_gam.py", "code/pilots/p5_hard_vs_soft.py",
            "code/models/ageing_p45.py", "code/tests/test_p45_units.py"]
    return {"commit": run("rev-parse", "HEAD"), "dirty_code_files": run("status", "--porcelain", "--", *mine)}


def tensors(design, ds, cells, use="obs"):
    """Fit tensors for the listed cell indices. Conditions are always the full 63 (the stress map is evaluated on all of them)."""
    cells = np.asarray(cells, int)
    obs_cell, obs_t, obs_y, obs_yt, obs_w = [], [], [], [], []
    for li, c in enumerate(cells):
        w = design.cell_weeks[c]
        obs_cell += [li] * len(w)
        obs_t += list(w / SG.T_SCALE)
        obs_y += list(ds.y_obs[c])
        obs_yt += list(ds.y_true[c])
        obs_w += list(range(len(w)))
    d = {
        "x_cond": torch.tensor(design.x, dtype=torch.float32),
        "nu_cond": torch.tensor(design.nu_norm, dtype=torch.float32),
        "cell_cond": torch.tensor(design.cell_cond[cells], dtype=torch.long),
        "obs_cell": torch.tensor(obs_cell, dtype=torch.long),
        "obs_t": torch.tensor(obs_t, dtype=torch.float32),
        "obs_y": torch.tensor(obs_y, dtype=torch.float32),
        "obs_ytrue": torch.tensor(obs_yt, dtype=torch.float32),
        "obs_idx": torch.tensor(obs_w, dtype=torch.long),
    }
    return d


def window_forecast_split(d):
    """window = first K_WINDOW+1 check-ups of each cell (incl. t=0); forecast = the rest. Returns (window tensors, forecast mask)."""
    win = d["obs_idx"] <= K_WINDOW
    dw = {k: (v[win] if k.startswith("obs_") else v) for k, v in d.items()}
    t_win_end = torch.zeros(d["cell_cond"].shape[0]).scatter_reduce(0, dw["obs_cell"], dw["obs_t"], "amax")
    return dw, ~win, t_win_end


def scoring_cells(design, cells):
    return np.array([c for c in cells if len(design.cell_weeks[c]) >= MIN_PTS], int)


def cell_condition_rmse_pp(pred, d, fmask):
    """forecast RMSE in percentage points (y_s * 10): per cell, mean within condition, then over conditions; also pooled RMSE and RMSE vs noiseless truth."""
    cell = d["obs_cell"][fmask]
    err = (pred[fmask] - d["obs_y"][fmask]) * 10.0
    errt = (pred[fmask] - d["obs_ytrue"][fmask]) * 10.0
    C = d["cell_cond"].shape[0]
    out = {}
    for name, e in (("noisy", err), ("truth", errt)):
        se = torch.zeros(C).index_add_(0, cell, e ** 2)
        n = torch.zeros(C).index_add_(0, cell, torch.ones_like(e))
        rm = torch.sqrt(se / n.clamp_min(1))
        cc = d["cell_cond"]
        per_cond = [float(rm[cc == k].mean()) for k in torch.unique(cc).tolist()]
        out[name] = {"cell_cond_mean": float(np.mean(per_cond)), "pooled": float(torch.sqrt((e ** 2).mean())), "n_cells": int((n > 0).sum()), "n_points": int(e.numel())}
    return out


def inner_folds(train_conds, seed, k=2):
    rng = np.random.default_rng([20261104, 9, seed])
    p = rng.permutation(np.asarray(train_conds))
    return [np.sort(p[i::k]) for i in range(k)]


def cells_of(design, conds):
    return np.where(np.isin(design.cell_cond, conds))[0]


def sample_trials(space, n, seed):
    rng = np.random.default_rng([20261104, 11, seed])
    keys = list(space)
    seen, out = set(), []
    total = int(np.prod([len(space[k]) for k in keys]))
    while len(out) < min(n, total):
        t = tuple(space[k][rng.integers(len(space[k]))] for k in keys)
        if t not in seen:
            seen.add(t)
            out.append(dict(zip(keys, t)))
    return out


def save_json(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf8") as fh:
        json.dump(obj, fh, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))


def write_config(out, pilot, extra):
    cfg = {
        "pilot": pilot, "device": "CPU only (CUDA_VISIBLE_DEVICES empty, torch.set_num_threads(1), at most 3 processes)",
        "python": sys.version.split()[0], "torch": torch.__version__, "numpy": np.__version__,
        "git": git_info(), "interpreter": ".venv/Scripts/python.exe -P",
        "constants": {"SIGMA_Y": SG.SIGMA_Y, "TAU_DELTA": SG.TAU_DELTA, "FADE_TARGET_median_final_y_s": SG.FADE_TARGET, "T_SCALE_weeks": SG.T_SCALE, "REST_H": SG.REST_H,
                      "T_MAX_N": SG.T_MAX_N, "K_WINDOW": K_WINDOW, "MIN_PTS_scored_cell": MIN_PTS, "model_SIGMA": M.SIGMA, "model_TAU": M.TAU,
                      "G2_GRID": SG.G2_GRID, "G1_GRID": SG.G1_GRID, "G1_KNEE_W": SG.G1_KNEE_W, "G1_T_REF": SG.G1_T_REF},
        "seeds": {"draw_params": "default_rng([20261104, kind(1=G1,2=G2), draw])", "offsets_and_noise": "default_rng([20261104, 100+kind, draw])",
                  "split": "default_rng([20261104, 7, draw]) -> 12 of 63 conditions held out", "inner_folds": "default_rng([20261104, 9, draw])",
                  "trials": "default_rng([20261104, 11, seed])", "lhs500": "scipy LatinHypercube seed 12345 (rejection to the hull)", "lhs256_collocation": 777},
        "design": "63 ISU conditions x 251 cells, per-cell check-up weeks of data/processed/isu_capacity.csv (columns cell, group, week only)",
    }
    cfg.update(extra)
    save_json(cfg, os.path.join(out, "config.json"))
