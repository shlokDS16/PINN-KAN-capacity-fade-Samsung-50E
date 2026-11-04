"""Synthetic generators G0 / G1 / G2 on a Samsung-like calendar + cycle design (PREREG_v2 section 13). Truth is written here, never fitted.

G0  well specified: the law of law.py with additive smooth stress functions (positive control).
G1  misspecified time law: y = Phi^z with z depending on temperature (the closed form of the law is applied, then a power).
G2  non-additive stress law: charge-rate hinge with temperature-shifted threshold + DoD x SOC product (additive GAMs cannot represent it).
Constants are round numbers, as in the pilots: median final fade 20 pp (y_s = 2.0), noise 0.5 pp (sigma 0.05 in y_s), offset sd 0.15.
The design is built here from stress ranges only (no capacity, no Samsung number). Check-up cadence follows the dataset paper's Fig. 4 reading
(weeks): cycling 1,2,3,5,7,9,13,17,...,49; storage 5,9,17,25,...,49.
"""
from dataclasses import dataclass

import numpy as np
import torch
from scipy.stats import qmc

from .data import Cell
from .law import SIGMA, TAU, drive_to_state, state_factor  # noqa: F401
from .specs import SPECS

CYC_WEEKS = [1, 2, 3, 5, 7, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49]
STO_WEEKS = [5, 9, 17, 25, 33, 41, 49]
FADE_TARGET = 2.0   # median final y_s


@dataclass
class SynthSet:
    kind: str
    cells: list
    log_rate_cyc: object      # callable: raw stress rows -> true log r_cyc (level included)
    log_rate_cal: object      # callable: raw (T, SOC) rows -> true log r_cal
    params: dict
    backbone: str
    cond_of: dict


def make_design(n_cyc_cond, n_sto_cond, reps, seed):
    rng = np.random.default_rng([20261106, seed])
    lo = np.array([0.3, 0.05, 0.2, 0.2])
    hi = np.array([0.8, 0.6, 1.0, 2.0])
    u = qmc.LatinHypercube(d=4, seed=int(rng.integers(1 << 30))).random(n_cyc_cond)
    p = lo + u * (hi - lo)
    temps = np.resize(np.array([23.0, 35.0, 45.0]), n_cyc_cond)
    rng.shuffle(temps)
    cyc = [(float(temps[i]), float(round(p[i, 0], 2)), float(round(p[i, 1], 2)), float(round(p[i, 2], 2)), float(round(p[i, 3], 2))) for i in range(n_cyc_cond)]
    us = qmc.LatinHypercube(d=1, seed=int(rng.integers(1 << 30))).random(n_sto_cond)[:, 0]
    st_t = np.resize(np.array([10.0, 23.0, 45.0]), n_sto_cond)
    sto = [(float(st_t[i]), float(round(0.05 + 0.95 * us[i], 2))) for i in range(n_sto_cond)]
    return cyc, sto, reps


def _truth(kind, spec):
    """true log-rate functions of raw stress"""
    def f_cyc(raw):
        raw = np.atleast_2d(raw)
        s = spec.norm(raw)
        sT, ssoc, sdod, scch, scdch = (s[:, i] for i in range(5))
        f = 0.5 * sT + 0.4 * scch + 0.3 * scdch + 0.4 * sdod + 0.2 * np.sin(2.0 * ssoc)
        if kind == "G2":
            thr = 0.1 - 0.5 * sT                                   # temperature-shifted threshold
            f = f + 1.2 * np.log1p(np.exp(6.0 * (scch - thr))) / 6.0 + 0.8 * sdod * ssoc
        return f

    def f_cal(raw):
        raw = np.atleast_2d(raw)
        s = spec.norm(np.column_stack([raw[:, 0], raw[:, 1], np.zeros(len(raw)), np.zeros(len(raw)), np.zeros(len(raw))]))
        a = 0.6 * s[:, 1]
        E = 0.8 + 0.4 * s[:, 1] ** 2
        xarr = (1.0 / 298.15 - 1.0 / (273.15 + raw[:, 0])) / (1.0 / 298.15 - 1.0 / 308.15)
        return a + E * xarr
    return f_cyc, f_cal


def make_synthetic(kind="G0", n_cyc_cond=20, n_sto_cond=8, reps=2, seed=0, backbone="self_limiting", fade_target=FADE_TARGET, noise=SIGMA, tau=TAU):
    """-> SynthSet. Cells are `Cell` objects (dataset 'synthetic', days, EFC); retention = 1 - y_s / 10 (+ noise)."""
    spec = SPECS["synthetic"]
    cyc, sto, reps = make_design(n_cyc_cond, n_sto_cond, reps, seed)
    f_cyc, f_cal = _truth(kind, spec)
    rng = np.random.default_rng([20261106, 1000 + seed])
    series = []
    for ci, (T, smax, dod, cch, cdch) in enumerate(cyc):
        raw = np.array([T, smax - dod / 2.0, dod, cch, cdch])
        for r in range(reps):
            series.append(("cycling", f"C{ci:02d}", raw, r))
    for si, (T, soc) in enumerate(sto):
        series.append(("storage", f"S{si:02d}", np.array([T, soc, 0.0, 0.0, 0.0]), 0))
    prepared = []
    for kind_c, cond, raw, r in series:
        days = np.array((CYC_WEEKS if kind_c == "cycling" else STO_WEEKS), float) * 7.0
        t = days - days[0]
        efc = spec.efc_rate(raw) * t if kind_c == "cycling" else np.zeros_like(t)
        delta = rng.normal(0.0, tau)
        prepared.append((kind_c, cond, raw, t, efc, delta))

    def y_true(c_cyc, c_cal, kind_c, cond, raw, t, efc, delta):
        tn, En = t / spec.t_scale, efc / spec.efc_scale
        a_cyc = np.exp(c_cyc + float(f_cyc(raw)[0]) + (delta if kind_c == "cycling" else 0.0))
        a_cal = np.exp(c_cal + float(f_cal(raw[:2][None])[0]) + (delta if kind_c == "storage" else 0.0))
        phi = torch.tensor(a_cal * tn + a_cyc * En, dtype=torch.float64)
        y = drive_to_state(phi, backbone).numpy()
        if kind == "G1":
            z = 1.0 + 0.25 * float(spec.norm(np.concatenate([raw[:1], np.zeros(4)]))[0])
            y = np.maximum(y, 1e-12) ** z * (t > 0)
        return y

    def median_final(c):
        return float(np.median([y_true(c, c - 2.0, *p)[-1] for p in prepared]))
    lo_c, hi_c = -8.0, 4.0
    for _ in range(50):     # bisection of the level so that median final y_s = fade_target
        mid = 0.5 * (lo_c + hi_c)
        lo_c, hi_c = (mid, hi_c) if median_final(mid) < fade_target else (lo_c, mid)
    c_cyc = 0.5 * (lo_c + hi_c)
    c_cal = c_cyc - 2.0
    cells, cond_of = [], {}
    cnt = {}
    for kind_c, cond, raw, t, efc, delta in prepared:
        y = y_true(c_cyc, c_cal, kind_c, cond, raw, t, efc, delta)
        y_obs = y + rng.normal(0.0, noise, len(y)) * (t > 0)
        n = cnt.get(cond, 0) + 1
        cnt[cond] = n
        cid = f"SYN_{kind}_{seed}_{cond}_{n}"
        ret = 1.0 - y_obs / spec.y_scale
        fc = np.ones(len(t), bool)
        fc[0] = False
        cells.append(Cell(cid, "synthetic", kind_c, f"{kind}{seed}_{cond}", raw.copy(), t, ret, efc, fc, meta={"delta_true": delta}))
        cond_of[cid] = cond
    return SynthSet(kind, cells, lambda raw: c_cyc + f_cyc(raw), lambda raw: c_cal + f_cal(raw), {"c_cyc": c_cyc, "c_cal": c_cal}, backbone, cond_of)


def split_conditions(cells, test_frac=0.25, seed=0):
    """held-out cycling conditions (storage cells stay in training); returns (train_cells, test_cells)"""
    rng = np.random.default_rng([20261106, 7, seed])
    conds = sorted({c.cond for c in cells if c.kind == "cycling"})
    k = max(1, int(round(test_frac * len(conds))))
    test = set(rng.choice(conds, size=k, replace=False))
    return [c for c in cells if c.cond not in test], [c for c in cells if c.cond in test]
