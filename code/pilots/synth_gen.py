"""Synthetic generators G1 / G2 on the ISU-ILCC design (P4, P5). Truth is written here, never fitted to a model.

Design (conditions, replicates, weekly cadence) is the real ISU design: the 63 condition rows of
data/processed/isu_conditions.csv and, for every one of the 251 cells, its own check-up weeks (columns `cell`, `group`,
`week` of data/processed/isu_capacity.csv ONLY; the capacity columns are never read here). No capacity value is used.

State  y_s = 10 * (1 - Q/Q0,c)  (retention loss in units of 10 percentage points);  time t_n = weeks / 50.
Stress x = (C_ch, C_dch, DoD) scaled to [-1, 1] by the design range.
Forcing nu(s): cycles per week from a nominal cycle duration  (DoD/100)/C_ch + (DoD/100)/C_dch + 0.5 h  (rest);
               nu_norm = nu / median over the 63 conditions.
ISU has one temperature (30 C) and no storage arm or SOC window, so the judge's temperature/SOC/storage terms are mapped
onto the stresses ISU has (documented in RESULT.md of P4 and P5):
  G2: charge-rate hinge whose threshold shifts with DoD (instead of with T) + product term DoD x C_dch (instead of DoD x SOC).
  G1: power-law time law y ~ t^z with exponent z depending on DoD (instead of T) + logistic knee in throughput whose onset shifts with
      charge rate and DoD.
Nominal constants (round numbers, not taken from any ISU label): noise sd 0.05 in y_s (0.5 pp), per-cell log-rate offset sd 0.15,
overall fade level: median over cells of y_s at the last check-up = 2.0 (20 pp).
"""
import os
import numpy as np
import pandas as pd
from scipy.spatial import Delaunay
from scipy.stats import qmc

SIGMA_Y = 0.05
TAU_DELTA = 0.15
FADE_TARGET = 2.0
T_SCALE = 50.0
REST_H = 0.5
T_MAX_N = 1.8  # fixed horizon in t_n (90 weeks > longest design record 88.2 weeks)

# parameter grids (normalised units), fixed before any run; a draw picks one value per key with a seeded RNG
G2_GRID = {
    "b1": [0.3, 0.5], "b2": [-0.15, 0.15], "b3": [0.3, 0.5], "q": [0.3],
    "H": [0.8, 1.2], "c0h": [-0.2, 0.2], "c1h": [-0.6, -0.3], "P": [0.5, 0.8],
}
G1_GRID = {
    "b1": [0.3, 0.5], "b2": [-0.15, 0.15], "b3": [0.3, 0.5],
    "z0": [0.9, 1.0, 1.1], "z1": [0.15, 0.25], "K": [0.8, 1.2, 1.6],
}
G1_KNEE_W = 0.08
G1_T_REF = 0.4


def draw_params(kind, draw):
    grid = G2_GRID if kind == "G2" else G1_GRID
    rng = np.random.default_rng([20261104, 2 if kind == "G2" else 1, draw])
    return {k: float(v[rng.integers(len(v))]) for k, v in grid.items()}


def cycles_per_week(raw):
    c_ch, c_dch, dod = raw[..., 0], raw[..., 1], raw[..., 2]
    dur = (dod / 100.0) / c_ch + (dod / 100.0) / c_dch + REST_H
    return 168.0 / dur


class Design:
    def __init__(self, root):
        cond = pd.read_csv(os.path.join(root, "data", "processed", "isu_conditions.csv")).sort_values("group").reset_index(drop=True)
        cap = pd.read_csv(os.path.join(root, "data", "processed", "isu_capacity.csv"), usecols=["cell", "group", "week"])
        self.groups = cond["group"].to_numpy()
        self.raw = cond[["charge_c", "discharge_c", "dod_pct"]].to_numpy(float)
        self.lo, self.hi = self.raw.min(0), self.raw.max(0)
        self.x = self.norm(self.raw)
        nu = cycles_per_week(self.raw)
        self.nu_med = float(np.median(nu))
        self.nu_norm = nu / self.nu_med
        self.efc_week = nu * self.raw[:, 2] / 100.0
        gi = {g: i for i, g in enumerate(self.groups)}
        cells = []
        for name, df in cap.groupby("cell", sort=True):
            w = np.sort(df["week"].to_numpy(float))
            cells.append((name, gi[int(df["group"].iloc[0])], w))
        self.cell_names = [c[0] for c in cells]
        self.cell_cond = np.array([c[1] for c in cells])
        self.cell_weeks = [c[2] for c in cells]
        self.n_cells = len(cells)
        self.n_cond = len(self.groups)
        self.efc_ref = float(np.median([self.efc_week[c] * w[-1] for c, w in zip(self.cell_cond, self.cell_weeks)]))
        self._hull = Delaunay(self.x)

    def norm(self, raw):
        return 2.0 * (np.asarray(raw) - self.lo) / (self.hi - self.lo) - 1.0

    def denorm(self, x):
        return self.lo + (np.asarray(x) + 1.0) / 2.0 * (self.hi - self.lo)

    def nu_norm_of_x(self, x):
        return cycles_per_week(self.denorm(x)) / self.nu_med

    def hull_lhs(self, n=500, seed=12345):
        """n Latin-hypercube-sampled stress points (normalised) inside the convex hull of the 63-condition design."""
        out = np.zeros((0, 3))
        s = seed
        while len(out) < n:
            cand = 2 * qmc.LatinHypercube(d=3, seed=s).random(4 * n) - 1
            cand = self.lo * 0 + cand  # bounding box is [-1, 1] after normalisation
            out = np.vstack([out, cand[self._hull.find_simplex(cand) >= 0]])
            s += 1
        return out[:n]


class G2Truth:
    """Non-additive stress law:  f(x) = b.x + q x3^2 + H relu(x1 - (c0h + c1h x3)) + P x2 x3 ;  dy/dt = exp(f + c0 + delta_c) nu_norm / (1 + y)."""

    kind = "G2"

    def __init__(self, params):
        self.p = dict(params)
        self.c0 = 0.0

    def shape(self, x):
        p = self.p
        x = np.asarray(x, float)
        add = p["b1"] * x[..., 0] + p["b2"] * x[..., 1] + p["b3"] * x[..., 2] + p["q"] * x[..., 2] ** 2
        hinge = p["H"] * np.maximum(x[..., 0] - (p["c0h"] + p["c1h"] * x[..., 2]), 0.0)
        prod = p["P"] * x[..., 1] * x[..., 2]
        return add + hinge + prod

    def additive_part(self, x):
        p = self.p
        x = np.asarray(x, float)
        return p["b1"] * x[..., 0] + p["b2"] * x[..., 1] + p["b3"] * x[..., 2] + p["q"] * x[..., 2] ** 2

    def log_rate(self, x):
        """per-nu log rate at delta = 0, including the level constant c0 (what a recovered stress map is compared with)"""
        return self.shape(x) + self.c0

    def y_cells(self, design, delta):
        A = np.exp(self.log_rate(design.x))[design.cell_cond] * design.nu_norm[design.cell_cond] * np.exp(delta)
        return [np.sqrt(1.0 + 2.0 * A[c] * (w / T_SCALE)) - 1.0 for c, w in enumerate(design.cell_weeks)]


class G1Truth:
    """Misspecified time law:  y(t) = exp(g(x) + c0 + delta_c) (t_n/0.4)^z(x) + K [sig((tau - tau0(x))/w) - sig(-tau0(x)/w)],
    g = b.x, z = z0 + z1 x3, tau = EFC(t)/EFC_ref (throughput), tau0 = clip(0.65 - 0.2 x1 - 0.15 x3, 0.25, 1.1). Not of the form A/(1+y)."""

    kind = "G1"

    def __init__(self, params):
        self.p = dict(params)
        self.c0 = 0.0

    @staticmethod
    def _sig(u):
        return 1.0 / (1.0 + np.exp(-u))

    def y_of(self, x, efc_week, delta, weeks):
        p = self.p
        x = np.asarray(x, float)
        g = p["b1"] * x[0] + p["b2"] * x[1] + p["b3"] * x[2] + self.c0 + delta
        z = p["z0"] + p["z1"] * x[2]
        tau0 = float(np.clip(0.65 - 0.2 * x[0] - 0.15 * x[2], 0.25, 1.1))
        tau = efc_week * weeks / self.efc_ref
        pw = np.exp(g) * (weeks / T_SCALE / G1_T_REF) ** z
        knee = p["K"] * (self._sig((tau - tau0) / G1_KNEE_W) - self._sig(-tau0 / G1_KNEE_W))
        return pw + knee

    def y_cells(self, design, delta):
        self.efc_ref = design.efc_ref
        return [self.y_of(design.x[design.cell_cond[c]], design.efc_week[design.cell_cond[c]], delta[c], w) for c, w in enumerate(design.cell_weeks)]


def _solve_level(truth, design, delta):
    lo, hi = -12.0, 8.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        truth.c0 = mid
        fin = np.array([y[-1] for y in truth.y_cells(design, delta)])
        if np.median(fin) > FADE_TARGET:
            hi = mid
        else:
            lo = mid
    truth.c0 = 0.5 * (lo + hi)


def make_truth(kind, params):
    return G2Truth(params) if kind == "G2" else G1Truth(params)


class Dataset:
    pass


def make_dataset(kind, draw, design, noise=True):
    """One synthetic draw: truth parameters from the grid, per-cell offsets, level matched, noisy observations (first point exact 0)."""
    params = draw_params(kind, draw)
    truth = make_truth(kind, params)
    rng = np.random.default_rng([20261104, 100 + (2 if kind == "G2" else 1), draw])
    delta = rng.normal(0.0, TAU_DELTA, design.n_cells)
    _solve_level(truth, design, delta)
    ytrue = truth.y_cells(design, delta)
    ds = Dataset()
    ds.kind, ds.draw, ds.params, ds.truth, ds.delta = kind, draw, params, truth, delta
    ds.y_true = ytrue
    ds.y_obs = []
    for y in ytrue:
        e = rng.normal(0.0, SIGMA_Y, y.shape) if noise else np.zeros_like(y)
        e[0] = 0.0
        ds.y_obs.append(y + e)
    return ds


def split_conditions(draw, n_cond=63, n_test=12):
    rng = np.random.default_rng([20261104, 7, draw])
    test = np.sort(rng.choice(n_cond, n_test, replace=False))
    return test
