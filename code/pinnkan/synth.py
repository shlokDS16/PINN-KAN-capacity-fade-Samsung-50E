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

from .data import Cell, samsung_cond_key
from .law import SIGMA, TAU, drive_to_state, state_factor  # noqa: F401
from .specs import SPECS

CYC_WEEKS = [1, 2, 3, 5, 7, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49]
STO_WEEKS = [5, 9, 17, 25, 33, 41, 49]
FADE_TARGET = 2.0   # median final y_s
# G2 strength (H, P) = (hinge weight, DoD x SOC product weight). G2: the upper values of the pilot grid (H 0.8/1.2, P 0.5/0.8), chosen after seeing P4 and disclosed (PREREG 13);
# G2p: the lower pilot-grid values, the "pilot-strength" sensitivity of PREREG 13 (the pilot drew H and P at random from those grids; the lower corner is this builder's reading of
# "pilot strength" and is to be confirmed by the lead).
G2_STRENGTH = {"G2": (1.2, 0.8), "G2p": (0.8, 0.5)}


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
    seen = set()
    for i, c in enumerate(cyc):          # two LHS rows can round to the same condition (seen at 40 conditions, seed 18): nudge the later one by 0.01 in C_dch; designs without a collision are unchanged
        while c in seen:
            c = (c[0], c[1], c[2], c[3], round(c[4] + 0.01, 2))
        seen.add(c)
        cyc[i] = c
    us = qmc.LatinHypercube(d=1, seed=int(rng.integers(1 << 30))).random(n_sto_cond)[:, 0]
    st_t = np.resize(np.array([10.0, 23.0, 45.0]), n_sto_cond)
    sto = [(float(st_t[i]), float(round(0.05 + 0.95 * us[i], 2))) for i in range(n_sto_cond)]
    seen_s = set()
    for i, c in enumerate(sto):          # same rule for storage points that round to the same (T, SOC) (seed 18 at 19 conditions); designs without a collision are unchanged
        while c in seen_s:
            c = (c[0], round(c[1] - 0.01 if c[1] >= 0.99 else c[1] + 0.01, 2))
        seen_s.add(c)
        sto[i] = c
    return cyc, sto, reps


def truth_effect(family, sign, x, lo, hi, amp=0.5):
    """log-rate contribution of one input for the extraction-audit calibration (rule: debates/D022_datasets_kan/calibration_rule_v2.md): zero | linear | log (sign * amp * (2 g - 1) with g in
    [0, 1] over the training-hull range [lo, hi]) and the report-only curved shapes quadratic | hinge. x is the physical positive stress value (temperature in kelvin)."""
    x = np.asarray(x, float)
    if family == "zero":
        return np.zeros_like(x)
    u = 2.0 * (x - lo) / max(hi - lo, 1e-12) - 1.0
    if family == "linear":
        return sign * amp * u
    if family == "log":
        return sign * amp * (2.0 * np.log(np.maximum(x, 1e-9) / lo) / max(np.log(hi / lo), 1e-12) - 1.0)
    if family == "quadratic":
        return sign * amp * (2.0 * u ** 2 - 1.0)
    if family == "hinge":
        return sign * amp * (2.0 * np.maximum(0.0, u - 0.2) / 0.8 - 1.0)
    raise ValueError(family)


def truth_sign(family, sign):
    """sign of the hull-averaged slope of a truth effect (D022a rule v2 section 4.1): 0 for the zero and the symmetric quadratic, the stratum sign for linear, log and hinge"""
    return 0 if family in ("zero", "quadratic") else int(sign)


def design_from_keys(cyc_keys, sto_keys, reps=2):
    """design tuples of make_synthetic from Samsung condition identifiers: cycling 'T35|SOCmax0.55|DoD0.25|Cch0.5|Cdch1' -> (T, SOC_max, DoD, C_ch, C_dch); storage 'T10|SOC0.5' -> (T, SOC)"""
    cyc = []
    for k in cyc_keys:
        p = k.split("|")
        cyc.append((float(p[0][1:]), float(p[1][6:]), float(p[2][3:]), float(p[3][3:]), float(p[4][4:])))
    sto = []
    for k in sto_keys:
        p = k.split("|")
        sto.append((float(p[0][1:]), float(p[1][3:])))
    return cyc, sto, reps


def _truth(kind, spec, truth=None, interaction=None):
    """true log-rate functions of raw stress. truth (kind 'GA'): {input index: (family, sign, lo, hi[, amp])} (amp default 0.5); inputs missing from it contribute 0.
    interaction (kind 'GA', D022a): (p, q, amp, lo_p, hi_p, lo_q, hi_q) adds amp * u_p * u_q, u the hull coordinate in [-1, 1] of the physical stress (T in kelvin)."""
    def f_cyc(raw):
        raw = np.atleast_2d(raw)
        if truth is not None:
            f = np.zeros(len(raw))
            for i, tup in truth.items():
                fam, sg, lo, hi = tup[:4]
                x = raw[:, i] + (273.15 if i == spec.t_index else 0.0)
                f = f + truth_effect(fam, sg, x, lo, hi, *(tup[4:5]))
            if interaction is not None:
                p_, q_, a_, lop, hip, loq, hiq = interaction
                xp = raw[:, p_] + (273.15 if p_ == spec.t_index else 0.0)
                xq = raw[:, q_] + (273.15 if q_ == spec.t_index else 0.0)
                f = f + a_ * (2.0 * (xp - lop) / max(hip - lop, 1e-12) - 1.0) * (2.0 * (xq - loq) / max(hiq - loq, 1e-12) - 1.0)
            return f
        s = spec.norm(raw)
        sT, ssoc, sdod, scch, scdch = (s[:, i] for i in range(5))
        f = 0.5 * sT + 0.4 * scch + 0.3 * scdch + 0.4 * sdod + 0.2 * np.sin(2.0 * ssoc)
        if kind in G2_STRENGTH:
            H, P = G2_STRENGTH[kind]
            thr = 0.1 - 0.5 * sT                                   # temperature-shifted threshold
            f = f + H * np.log1p(np.exp(6.0 * (scch - thr))) / 6.0 + P * sdod * ssoc
        return f

    def f_cal(raw):
        raw = np.atleast_2d(raw)
        s = spec.norm(np.column_stack([raw[:, 0], raw[:, 1], np.zeros(len(raw)), np.zeros(len(raw)), np.zeros(len(raw))]))
        a = 0.6 * s[:, 1]
        E = 0.8 + 0.4 * s[:, 1] ** 2
        xarr = (1.0 / 298.15 - 1.0 / (273.15 + raw[:, 0])) / (1.0 / 298.15 - 1.0 / 308.15)
        return a + E * xarr
    return f_cyc, f_cal


def make_synthetic(kind="G0", n_cyc_cond=20, n_sto_cond=8, reps=2, seed=0, backbone="self_limiting", fade_target=FADE_TARGET, noise=SIGMA, tau=TAU, design=None, truth=None, interaction=None, cond_offsets=None):
    """-> SynthSet. Cells are `Cell` objects (dataset 'synthetic', days, EFC); retention = 1 - y_s / 10 (+ noise). cond_offsets (D022a): {cycling condition index: offset} added to the
    cyclic log-rate of every cell of that condition (laboratory aliasing); the random draws are unchanged by it."""
    spec = SPECS["synthetic"]
    cyc, sto, reps = design if design is not None else make_design(n_cyc_cond, n_sto_cond, reps, seed)       # design: given condition lists (the real folds' training identifiers) instead of a Latin hypercube
    f_cyc, f_cal = _truth(kind, spec, truth, interaction)
    rng = np.random.default_rng([20261106, 1000 + seed])
    series = []
    for ci, (T, smax, dod, cch, cdch) in enumerate(cyc):
        raw = np.array([T, smax - dod / 2.0, dod, cch, cdch])
        for r in range(reps):
            series.append(("cycling", f"C{ci:02d}", raw, r))
    offs = {f"C{int(k):02d}": float(v) for k, v in (cond_offsets or {}).items()}
    for si, (T, soc) in enumerate(sto):
        series.append(("storage", f"S{si:02d}", np.array([T, soc, 0.0, 0.0, 0.0]), 0))
    prepared = []
    for kind_c, cond, raw, r in series:
        days = np.array((CYC_WEEKS if kind_c == "cycling" else STO_WEEKS), float) * 7.0
        t = days - days[0]
        efc = spec.efc_rate(raw) * t if kind_c == "cycling" else np.zeros_like(t)
        delta = rng.normal(0.0, tau) + offs.get(cond, 0.0)
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
        ckey = (samsung_cond_key("cycling", raw[0], raw[1] + raw[2] / 2.0, raw[2], raw[3], raw[4]) if kind_c == "cycling" else samsung_cond_key("storage", raw[0], raw[1], 0, 0, 0))   # Samsung key format: the figure scripts parse it
        cells.append(Cell(cid, "synthetic", kind_c, ckey, raw.copy(), t, ret, efc, fc, meta={"delta_true": delta}))
        cond_of[cid] = cond
    assert len({c.cond for c in cells}) == len(cyc) + len(sto), "condition keys collide: change the seed or the rounding"
    return SynthSet(kind, cells, lambda raw: c_cyc + f_cyc(raw), lambda raw: c_cal + f_cal(raw), {"c_cyc": c_cyc, "c_cal": c_cal}, backbone, cond_of)


def split_conditions(cells, test_frac=0.25, seed=0):
    """held-out cycling conditions (storage cells stay in training); returns (train_cells, test_cells)"""
    rng = np.random.default_rng([20261106, 7, seed])
    conds = sorted({c.cond for c in cells if c.kind == "cycling"})
    k = max(1, int(round(test_frac * len(conds))))
    test = set(rng.choice(conds, size=k, replace=False))
    return [c for c in cells if c.cond not in test], [c for c in cells if c.cond in test]


def split_synthetic(cells, test, frac=0.25, seed=0):
    """held-out part per test name: B and A random cycling conditions; C the 35 C cycling conditions (a temperature domain); S2 and S3 random storage conditions"""
    if test == "C":
        te = {c.cond for c in cells if c.kind == "cycling" and abs(c.raw[0] - 35.0) < 1e-9}
        if te:
            return [c for c in cells if c.cond not in te], [c for c in cells if c.cond in te]
    if test in ("S2", "S3"):
        rng = np.random.default_rng([20261106, 8, seed])
        conds = sorted({c.cond for c in cells if c.kind == "storage"})
        te = set(rng.choice(conds, size=max(1, int(round(frac * len(conds)))), replace=False))
        return [c for c in cells if c.cond not in te], [c for c in cells if c.cond in te]
    return split_conditions(cells, frac, seed)


def shorten_cells(cells, n_points_list):
    """D033 F7: copies of `cells` in which the first len(n_points_list) CYCLING cells (in list order) are cut to the given number of check-ups (reference included), so that the record is shorter
    than the window (the D025 cap binds) or has no forecast point left (unscored). None / empty = unchanged. The cut keeps the leading points, so labels before the cut are untouched."""
    if not n_points_list:
        return cells
    import copy
    todo = list(n_points_list)
    out = []
    for c in cells:
        if c.kind == "cycling" and todo:
            n = int(todo.pop(0))
            if not 2 <= n <= c.n:
                raise ValueError(f"short record of {n} points for a cell of {c.n} points")
            c = copy.copy(c)
            c.t, c.ret, c.efc, c.fc_ok = c.t[:n].copy(), c.ret[:n].copy(), c.efc[:n].copy(), c.fc_ok[:n].copy()
        out.append(c)
    return out
