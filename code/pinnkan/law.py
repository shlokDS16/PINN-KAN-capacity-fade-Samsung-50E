"""The ageing law and its building blocks (PREREG_v2 section 7; D010 judge section 2).

    dy/dt = [ r_cal(T, SOC) + r_cyc(s) * nu(t) ] * h(y),        y(0) = 0
    r_cal = exp(log_cal + a(SOC) + E(SOC) * x_arr(T))      (a, E) = calendar KAN [1,2] of storage SOC; x_arr = Arrhenius abscissa
    r_cyc = exp(log_cyc + f(s))                            f = stress map: KAN [d,h,1] | additive GAM (= KAN [d,1]) | interaction GAM |
                                                            parametric log-linear | MLP
    nu    = dE_n/dt_n  (piecewise-constant equivalent-full-cycle rate), E_n = EFC / efc_scale; storage cells have nu = 0
Per-cell offset delta_c scales the cycling term of a cycling cell and the calendar term of a storage cell. One backbone h is
shared by both terms of a fold (consequence of "shared by all law-based arms of that fold"), which gives the closed form
    y = drive_to_state(Phi),   Phi(t) = a_cal * t_n + a_cyc * E_n(t)        (exact integration of the law for piecewise-constant nu).
Units: y is y_s = y_scale * (1 - retention); t_n = t / t_scale.
"""
import math
from dataclasses import dataclass

import numpy as np
import torch
from torch import nn

from . import ROOT  # noqa: F401  (puts code/ on sys.path)
from models.ageing_p45 import KANStack  # noqa: E402  (pilot module, imported not edited)
from models.kan_spline import bspline_basis  # noqa: E402

from .data import EFCCurve
from .specs import DatasetSpec

SIGMA = 0.05   # nominal observation noise in y_s units (0.5 pp); same constant in every arm (as P4/P5)
TAU = 0.15     # nominal sd of per-cell log-rate offsets (as P4/P5)
Y0 = 1.0       # self-limiting scale, y_s units
GAMMA = 0.3    # accelerating exponent, 1 / y_s units
GRAD_CLIP = 20.0   # recipe constant (D013 C1): global gradient-norm clip of EVERY gradient-trained arm (A1, A2, A3-A7, A9, A13, A14); loss is scaled by 1/SIGMA^2 = 400
WARMUP = 0.4       # residual-weight ramp 0 -> lam_res over this fraction of the steps (arms with a residual only)
BACKBONES = ("constant", "self_limiting", "accelerating")   # order = simplicity order for the tournament
_EPS = 1e-4


def state_factor(y, kind):
    if kind == "constant":
        return torch.ones_like(y)
    if kind == "self_limiting":
        return 1.0 / (1.0 + y / Y0)
    if kind == "accelerating":
        return torch.exp(GAMMA * y.clamp(max=30.0))
    raise ValueError(kind)


def state_to_drive(y, kind):
    """Phi(y) = integral_0^y dy' / h(y')"""
    if kind == "constant":
        return y
    if kind == "self_limiting":
        return y + y * y / (2.0 * Y0)
    if kind == "accelerating":
        return (1.0 - torch.exp(-GAMMA * y)) / GAMMA
    raise ValueError(kind)


def drive_to_state(phi, kind):
    """exact solution of dy/dt = A(t) h(y), y(0)=0, with Phi = integral A dt  (inverse of state_to_drive)"""
    phi = phi.clamp_min(0.0)
    if kind == "constant":
        return phi
    if kind == "self_limiting":
        return Y0 * (torch.sqrt(1.0 + 2.0 * phi / Y0) - 1.0)
    if kind == "accelerating":
        return -torch.log((1.0 - GAMMA * phi).clamp_min(_EPS)) / GAMMA
    raise ValueError(kind)


def clip_and_count(params, clip, stats):
    """clip the global gradient norm (if clip) and count the steps where the norm exceeded it (D013 C7: clipped fraction)"""
    stats["steps"] += 1
    if clip:
        gn = torch.nn.utils.clip_grad_norm_(params, clip)
        stats["clipped"] += int(float(gn) > clip)


def new_clip_stats():
    return {"steps": 0, "clipped": 0}


def clip_fraction(stats):
    return stats["clipped"] / max(stats["steps"], 1)


def rk4_reference(a_cal, a_cyc, curve: EFCCurve, t_query_n, spec: DatasetSpec, backbone, sub=40):
    """Numpy RK4 of the law for ONE cell (tests only): nu piecewise constant from `curve`, substeps split at the curve knots."""
    hfun = {"constant": lambda y: 1.0, "self_limiting": lambda y: 1.0 / (1.0 + y / Y0), "accelerating": lambda y: math.exp(GAMMA * min(y, 30.0))}[backbone]
    to_n = spec.t_scale / spec.efc_scale
    knots = np.unique(np.concatenate([curve.t / spec.t_scale, np.asarray(t_query_n, float), [0.0]]))
    y, out, tq = 0.0, {}, 0.0
    for t0, t1 in zip(knots[:-1], knots[1:]):
        nu = float(curve.rate(0.5 * (t0 + t1) * spec.t_scale)) * to_n
        A = a_cal + a_cyc * nu
        h = (t1 - t0) / sub
        for _ in range(sub):
            k1 = A * hfun(y); k2 = A * hfun(y + 0.5 * h * k1); k3 = A * hfun(y + 0.5 * h * k2); k4 = A * hfun(y + h * k3)
            y += h / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
        out[round(t1, 12)] = y
    return np.array([out.get(round(float(t), 12), 0.0) for t in t_query_n])


# ------------------------------------------------------------------------------------------------ stress maps (cyclic log-rate f(s))
def _clamp(s):
    return s.clamp(-1.0, 1.0 - 1e-6)


def n_params(m):
    return sum(p.numel() for p in m.parameters())


class KANMap(nn.Module):
    """KAN [d,h,1] (h given) or the additive GAM = KAN [d,1] (h None)."""

    def __init__(self, d, hidden, grid):
        super().__init__()
        self.net = KANStack([d, hidden, 1] if hidden else [d, 1], grid)

    def forward(self, s):
        return self.net(_clamp(s))[:, 0]

    def spline_l2(self):
        return sum((l.spline_w ** 2).sum() for l in self.net.layers)

    def sparsity(self):
        """L1 + entropy of edge magnitudes (parameter-based proxy of Liu et al.'s activation-based penalty; TODO if the activation form is required)."""
        tot = 0.0
        for l in self.net.layers:
            m = l.spline_w.abs().mean(-1) + l.base_w.abs()
            p = m / (m.sum() + 1e-12)
            tot = tot + m.sum() + (-(p * torch.log(p + 1e-12)).sum())
        return tot


class IGAMMap(nn.Module):
    """A4 plus tensor-product spline terms for prespecified pairs."""

    def __init__(self, d, grid, pairs, igrid):
        super().__init__()
        self.gam = KANMap(d, None, grid)
        self.pairs = list(pairs)
        h = 2.0 / igrid
        self.register_buffer("knots", -1.0 + h * torch.arange(-3, igrid + 4, dtype=torch.float32))
        self.nb = igrid + 3
        self.W = nn.Parameter(torch.randn(max(len(self.pairs), 1), self.nb * self.nb) * 0.02)

    def forward(self, s):
        s = _clamp(s)
        out = self.gam(s)
        for p, (i, j) in enumerate(self.pairs):
            bi = bspline_basis(s[:, i:i + 1], self.knots, 3)[:, 0, :]
            bj = bspline_basis(s[:, j:j + 1], self.knots, 3)[:, 0, :]
            out = out + (bi.unsqueeze(2) * bj.unsqueeze(1)).reshape(s.shape[0], -1) @ self.W[p]
        return out

    def spline_l2(self):
        return self.gam.spline_l2() + (self.W ** 2).sum()


class ParamMap(nn.Module):
    """A3: log-linear Arrhenius / power-law factors, f = w . phi(s); phi per stress by spec.param_kinds (arr | log | quad | lin)."""

    def __init__(self, spec: DatasetSpec):
        super().__init__()
        self.kinds = [spec.param_kinds[n] for n in spec.stress_names]
        self.register_buffer("lo", torch.tensor(spec.stress_lo, dtype=torch.float32))
        self.register_buffer("hi", torch.tensor(spec.stress_hi, dtype=torch.float32))
        self.nfeat = sum(2 if k == "quad" else 1 for k in self.kinds)
        self.w = nn.Parameter(torch.zeros(self.nfeat))

    def feats(self, s):
        raw = self.lo + (s + 1.0) / 2.0 * (self.hi - self.lo)
        cols = []
        for k, kind in enumerate(self.kinds):
            x = raw[:, k]
            if kind == "arr":
                cols.append((1.0 / 298.15 - 1.0 / (273.15 + x)) / (1.0 / 298.15 - 1.0 / 308.15))
            elif kind == "log":
                cols.append(torch.log(x.clamp_min(0.01 * float(self.hi[k]))))
            elif kind == "quad":
                cols += [x, x * x]
            else:
                cols.append(x)
        return torch.stack(cols, 1)

    def forward(self, s):
        return self.feats(s) @ self.w

    def spline_l2(self):
        return (self.w ** 2).sum()


class PolyMap(nn.Module):
    """A6 (dropped from the essential set by the prereg; kept as an optional arm): degree-2 polynomial of the normalised stress,
    d linear + d(d+1)/2 quadratic and cross terms, ridge via spline_l2."""

    def __init__(self, d):
        super().__init__()
        self.idx = [(i, j) for i in range(d) for j in range(i, d)]
        self.w = nn.Parameter(torch.zeros(d + len(self.idx)))

    def forward(self, s):
        cols = [s[:, i] for i in range(s.shape[1])] + [s[:, i] * s[:, j] for i, j in self.idx]
        return torch.stack(cols, 1) @ self.w

    def spline_l2(self):
        return (self.w ** 2).sum()


class MLPMap(nn.Module):
    """A7 (PiDDM-style): small tanh MLP of the stress vector."""

    def __init__(self, d, width, depth):
        super().__init__()
        layers, a = [], d
        for _ in range(depth):
            layers += [nn.Linear(a, width), nn.Tanh()]
            a = width
        layers.append(nn.Linear(a, 1))
        self.net = nn.Sequential(*layers)
        nn.init.normal_(self.net[-1].weight, std=0.05)
        nn.init.zeros_(self.net[-1].bias)

    def forward(self, s):
        return self.net(s)[:, 0]

    def spline_l2(self):
        return sum((m.weight ** 2).sum() for m in self.net if isinstance(m, nn.Linear))


def kan_param_count(d, hidden, grid):
    """number of parameters of KAN [d,hidden,1] (edges x (1 base + grid + 3 spline)); used to cap the A7 MLP at the largest A1 map"""
    edges = d * hidden + hidden if hidden else d
    return edges * (1 + grid + 3)


def build_stress_map(kind, spec: DatasetSpec, hp):
    d = spec.d
    if kind == "kan":
        return KANMap(d, int(hp.get("h", 4)), int(hp.get("grid", 5)))
    if kind == "gam":
        return KANMap(d, None, int(hp.get("grid", 5)))
    if kind == "igam":
        names = list(spec.stress_names)
        pairs = [(names.index(a), names.index(b)) for a, b in spec.interaction_pairs]
        return IGAMMap(d, int(hp.get("grid", 5)), pairs, int(hp.get("igrid", 3)))
    if kind == "param":
        return ParamMap(spec)
    if kind == "poly":
        return PolyMap(d)
    if kind == "mlp":
        width, depth = int(hp.get("width", 8)), int(hp.get("depth", 2))
        cap = max(kan_param_count(d, 8, 12), 1)
        while True:           # parameter count capped at the largest A1 map (prereg 7.1); deterministic shrink
            m = MLPMap(d, width, depth)
            if n_params(m) <= cap or width <= 2:
                return m
            width = max(2, width // 2)
    raise ValueError(kind)


# ------------------------------------------------------------------------------------------------ the law
class Law(nn.Module):
    def __init__(self, spec: DatasetSpec, cyc_map, grid_cal=5, log_cal0=-3.0, log_cyc0=-1.0):
        super().__init__()
        self.spec = spec
        self.cyc = cyc_map
        self.cal = KANStack([1, 2], grid_cal) if spec.has_calendar else None
        self.log_cal = nn.Parameter(torch.tensor(float(log_cal0)))
        self.log_cyc = nn.Parameter(torch.tensor(float(log_cyc0)))
        self.register_buffer("lo", torch.tensor(spec.stress_lo, dtype=torch.float32))
        self.register_buffer("hi", torch.tensor(spec.stress_hi, dtype=torch.float32))

    def x_arr(self, s):
        k = self.spec.t_index
        T = 273.15 + self.lo[k] + (s[:, k] + 1.0) / 2.0 * (self.hi[k] - self.lo[k])
        return (1.0 / 298.15 - 1.0 / T) / (1.0 / 298.15 - 1.0 / 308.15)

    def calendar_ae(self, s):
        """(a(SOC), E(SOC)) of the calendar KAN at the SOC column of s"""
        k = self.spec.soc_index
        return self.cal(_clamp(s[:, k:k + 1]))

    def r_cal(self, s):
        if self.cal is None:
            return torch.zeros(s.shape[0])
        ae = self.calendar_ae(s)
        return torch.exp(self.log_cal + ae[:, 0] + ae[:, 1] * self.x_arr(s))

    def r_cyc(self, s):
        return torch.exp(self.log_cyc + self.cyc(s))

    def amplitudes(self, s, is_cyc, delta):
        ed = torch.exp(delta)
        a_cal = self.r_cal(s) * torch.where(is_cyc > 0.5, torch.ones_like(ed), ed)
        a_cyc = self.r_cyc(s) * torch.where(is_cyc > 0.5, ed, torch.ones_like(ed))
        return a_cal, a_cyc

    def reg(self, l2, sparsity):
        r = l2 * self.cyc.spline_l2()
        if self.cal is not None:
            r = r + l2 * sum((l.spline_w ** 2).sum() for l in self.cal.layers)
        if sparsity > 0 and hasattr(self.cyc, "sparsity"):
            r = r + sparsity * self.cyc.sparsity()
        return r


# ------------------------------------------------------------------------------------------------ batches
@dataclass
class Batch:
    ids: list
    conds: list
    kinds: list
    s: torch.Tensor           # (C, d) normalised stress (storage cells: (T, SOC, 0, 0, 0) normalised)
    is_cyc: torch.Tensor      # (C,)
    obs_cell: torch.Tensor    # (M,)
    obs_t: torch.Tensor       # (M,) t_n
    obs_y: torch.Tensor       # (M,) y_s (NaN when unknown)
    obs_E: torch.Tensor       # (M,) E_n at obs_t
    t_end: torch.Tensor       # (C,) last observed t_n
    curves: list              # EFCCurve per series (rate beyond the data: mean rate)

    @property
    def C(self):
        return len(self.ids)


def _series_batch(spec, ids, conds, kinds, raws, ts, rets, curves):
    s = torch.tensor(np.stack([spec.norm(r) for r in raws]), dtype=torch.float32)
    is_cyc = torch.tensor([1.0 if k == "cycling" else 0.0 for k in kinds])
    oc, ot, oy, oe, te = [], [], [], [], []
    for c, (t, ret, cur) in enumerate(zip(ts, rets, curves)):
        t = np.asarray(t, float)
        oc += [c] * len(t)
        ot += list(t / spec.t_scale)
        oy += list(spec.y_scale * (1.0 - np.asarray(ret, float))) if ret is not None else [float("nan")] * len(t)
        oe += list(cur.value(t) / spec.efc_scale)
        te.append(t.max() / spec.t_scale)
    f = lambda a: torch.tensor(np.asarray(a), dtype=torch.float32)
    return Batch(list(ids), list(conds), list(kinds), s, is_cyc, torch.tensor(oc, dtype=torch.long), f(ot), f(oy), f(oe), f(te), list(curves))


def batch_from_cells(spec, cells):
    """full records of training cells"""
    return _series_batch(spec, [c.cell_id for c in cells], [c.cond for c in cells], [c.kind for c in cells], [c.raw for c in cells],
                         [c.t for c in cells], [c.ret for c in cells], [EFCCurve(c.t, c.efc) for c in cells])


def batch_from_windows(spec, wcells):
    """window observations of held-out cells (the only labels a model may use for them)"""
    return _series_batch(spec, [w.cell_id for w in wcells], [w.cond for w in wcells], [w.kind for w in wcells], [w.raw for w in wcells],
                         [w.t_win for w in wcells], [w.y_win for w in wcells], [w.efc_curve for w in wcells])


def batch_forecast_query(spec, wcells):
    """forecast times of held-out cells, no labels; throughput after the window from the causal curve"""
    return _series_batch(spec, [w.cell_id for w in wcells], [w.cond for w in wcells], [w.kind for w in wcells], [w.raw for w in wcells],
                         [w.t_fc for w in wcells], [None] * len(wcells), [w.efc_curve for w in wcells])


def retention_from_y(spec, y):
    return 1.0 - np.asarray(y, float) / spec.y_scale


def init_levels(batch: Batch, spec, backbone):
    """data-based starting levels of log_cal and log_cyc (training series only; median over series of log(Phi_last / driver))."""
    last_t, last_y, last_E = {}, {}, {}
    for c, t, y, e in zip(batch.obs_cell.tolist(), batch.obs_t.tolist(), batch.obs_y.tolist(), batch.obs_E.tolist()):
        if c not in last_t or t >= last_t[c]:
            last_t[c], last_y[c], last_E[c] = t, y, e
    phi = lambda y: float(state_to_drive(torch.tensor(max(y, 0.0)), backbone))
    cyc = [math.log(max(phi(last_y[c]), 1e-4) / max(last_E[c], 1e-4)) for c in last_t if batch.is_cyc[c] > 0.5 and last_E[c] > 1e-6]
    sto = [math.log(max(phi(last_y[c]), 1e-4) / max(last_t[c], 1e-4)) for c in last_t if batch.is_cyc[c] < 0.5 and last_t[c] > 1e-6]
    log_cyc = float(np.median(cyc)) if cyc else -1.0
    log_cal = float(np.median(sto)) if sto else (log_cyc - 2.0 if spec.has_calendar else -3.0)
    return log_cal, log_cyc
