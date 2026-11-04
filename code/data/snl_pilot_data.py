"""Tensors for the P2 timing pilot from data/processed/snl_cycles.csv + snl_cells.csv (written by snl_cycles.py).

Timing pilot only: builds the fit tensors; makes NO train/test split (none exist yet) and every cell is used.
"""
import os
import sys

sys.path.append(os.path.join(os.environ.get("APPDATA", ""), "Python", "Python314", "site-packages"))
import numpy as np
import pandas as pd
import torch

T_SCALE_DAYS = 500.0
Y_SCALE = 10.0
RANGES = {"T": (10.0, 40.0), "soc_mid": (0.0, 1.0), "dod": (0.0, 1.0), "c_ch": (0.0, 3.0), "c_dch": (0.0, 3.0)}


def _norm(x, lo, hi):
    return (x - lo) / (hi - lo) * 2.0 - 1.0


def load_cells(root, m_obs=80, per_cycle_all=False):
    cyc = pd.read_csv(os.path.join(root, "data", "processed", "snl_cycles.csv"))
    cells = pd.read_csv(os.path.join(root, "data", "processed", "snl_cells.csv"))
    out = []
    for _, c in cells.iterrows():
        g = cyc[cyc["cell"] == c["cell"]].sort_values("cycle")
        g = g[(g["q_dis_ah"] > 0) & np.isfinite(g["q_dis_ah"])]
        q0 = g["q_dis_ah"].iloc[0]
        t_days = (g["t_start_s"].to_numpy() - g["t_start_s"].iloc[0]) / 86400.0
        y = 1.0 - g["q_dis_ah"].to_numpy() / q0
        n = len(g)
        idx = np.arange(n) if per_cycle_all else np.unique(np.round(np.linspace(0, n - 1, min(m_obs, n))).astype(int))
        span = max(t_days[-1], 1e-6)
        efc = g["throughput_ah"].sum() / (2.0 * q0)
        lo, hi = [int(v) for v in c["soc_window"].split("-")]
        soc_mid, dod = (lo + hi) / 200.0, (hi - lo) / 100.0
        s = [_norm(c["temp_c"], *RANGES["T"]), _norm(soc_mid, *RANGES["soc_mid"]), _norm(dod, *RANGES["dod"]),
             _norm(c["charge_c"], *RANGES["c_ch"]), _norm(c["discharge_c"], *RANGES["c_dch"])]
        out.append({"cell": c["cell"], "stress": s, "nu": efc / span, "t": t_days[idx] / T_SCALE_DAYS,
                    "y": y[idx] * Y_SCALE, "span_tn": span / T_SCALE_DAYS})
    return out


def build_fit_data(root, m_obs=80, tile_to=None, per_cycle_all=False, seed=0, n_coll_per_cell=32, n_lhs=256, n_twin=128):
    cells = load_cells(root, m_obs, per_cycle_all)
    if tile_to:
        cells = [dict(cells[i % len(cells)], cell=f"{cells[i % len(cells)]['cell']}#{i}") for i in range(tile_to)]
    C = len(cells)
    nu = np.array([c["nu"] for c in cells])
    nu = nu / np.median(nu)
    stress = np.array([c["stress"] for c in cells], dtype=np.float32)
    M = max(len(c["t"]) for c in cells)
    t_nodes = np.zeros((C, M), dtype=np.float32)
    y_nodes = np.zeros((C, M), dtype=np.float32)
    mask = np.zeros((C, M), dtype=np.float32)
    for i, c in enumerate(cells):
        k = len(c["t"])
        t_nodes[i, :k] = c["t"]
        t_nodes[i, k:] = c["t"][-1]
        y_nodes[i, :k] = c["y"]
        mask[i, :k] = 1.0
    mask[:, 0] = 0.0  # y(0) = 0 is exact (hard initial condition), not a data point
    rng = np.random.default_rng(seed)
    horizon = max(c["span_tn"] for c in cells)  # fixed from the design (longest record), label-free
    oc, ot, oy = [], [], []
    for i, c in enumerate(cells):
        oc.append(np.full(len(c["t"]) - 1, i))
        ot.append(c["t"][1:])
        oy.append(c["y"][1:])
    obs_cell = np.concatenate(oc)
    obs_t = np.concatenate(ot)[:, None]
    obs_y = np.concatenate(oy)[:, None]
    # collocation (a): every cell's time axis up to the fixed horizon (beyond its observed record)
    ca_cell = np.repeat(np.arange(C), n_coll_per_cell)
    ca_t = np.concatenate([rng.uniform(0.0, horizon, n_coll_per_cell) for _ in range(C)])[:, None]
    # collocation (b): Latin-hypercube stress points inside the design box, nu uniform in the design range
    lo, hi = stress.min(0), stress.max(0)
    u = (np.stack([rng.permutation(n_lhs) for _ in range(5)], 1) + rng.random((n_lhs, 5))) / n_lhs
    sb = (lo + u * (hi - lo)).astype(np.float32)
    nub = rng.uniform(nu.min(), nu.max(), n_lhs)
    tb = rng.uniform(0.0, horizon, n_lhs)
    # collocation (c): calendar twins (nu = 0) of randomly chosen cells' (T, SOC)
    pick = rng.integers(0, C, n_twin)
    sc = stress[pick].copy()
    nuc = np.zeros(n_twin)
    tc = rng.uniform(0.0, horizon, n_twin)

    def f(a):
        return torch.tensor(np.asarray(a), dtype=torch.float32)

    d = {"stress": f(stress), "nu": f(nu),
         "t_nodes": f(t_nodes), "y_nodes": f(y_nodes), "mask": f(mask),
         "obs_cell": torch.tensor(obs_cell, dtype=torch.long), "obs_t": f(obs_t), "obs_y": f(obs_y),
         "coll_a_cell": torch.tensor(ca_cell, dtype=torch.long), "coll_a_t": f(ca_t),
         "coll_b_s": f(np.concatenate([sb, sc])), "coll_b_nu": f(np.concatenate([nub, nuc])),
         "coll_b_t": f(np.concatenate([tb, tc])[:, None])}
    info = {"n_cells": C, "n_obs": int(len(obs_y)), "n_nodes_M": int(M), "horizon_tn": float(horizon),
            "n_coll_a_fixed": int(len(ca_t)), "n_coll_b_fixed": int(n_lhs), "n_coll_c_fixed": int(n_twin),
            "per_cycle_all": per_cycle_all, "tile_to": tile_to}
    return d, info
