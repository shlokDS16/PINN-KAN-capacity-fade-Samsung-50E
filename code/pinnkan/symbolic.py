"""A15 / G15: closed-form (symbolic) laws extracted from a fitted KAN (A15) or from the additive GAM of A4 (G15). PREREG_v4 7.3; D016 judge section 3.

ONE code path for both arms: `extract_stack` reads any stack of `models.kan_spline.KANLayer` layers (A1: cyclic KAN [d,h,1]; A4: the additive GAM = KAN [d,1];
the calendar KAN [1,2] of every law-based arm) and returns a `SymbolicStack` whose edges are library functions. Only the stack differs between the arms.

FROZEN LIBRARY (hashed by `library_hash`, written to `symbolic_library.json`): per edge exactly one of
  zero (pruned) | linear | quadratic | power x^p on a positive physical abscissa | log | exponential | Arrhenius exp(-b/T) on temperature only | hinge max(0, x - c).
RULE (frozen with the library):
  1. Every first-layer edge i is evaluated on G = 101 equally spaced points over the fold's TRAINING HULL of its input (min to max of that input over the training
     cycling conditions; calendar edges: over the SOC of the training cells). Deeper edges: over the range of the (KAN's own) hidden activation at the training
     stress vectors. Labels never enter.
  2. Each family is fitted on that grid by least squares (variable projection: linear coefficients exact, the one non-linear parameter by a fixed grid then a bounded
     scalar polish). Families with more free coefficients than the per-edge CAP are not eligible (zero has none).
  3. The family is chosen by BIC = G ln(max(RSS/G, tol^2)) + k ln G, with tol = RMS_TOL_REL x (the largest range of any edge of the same layer): differences below
     1 % of the largest edge are not resolved, so approximation error of the spline is not mistaken for structure, and an edge that moves the output by less than that is
     pruned (zero has k = 0). Ties: fewer coefficients, then library order.
  4. The chosen coefficients are the starting point of an end-to-end refit under the loss of the parent arm (arms.SymbolicArm).
Per-edge cap on free coefficients: `cap` (config value `symbolic.cap`, or the `max_coeffs_per_edge` field of the library file). It is None until the method-architect
sets it; extraction raises `CapNotSetError` while it is None ([ARCH: cap]).
`untruncated=True` (tests only, not part of the frozen library) keeps every edge as its own spline: the symbolic stack then equals the KAN to float tolerance.
"""
import hashlib
import json
import os
from dataclasses import dataclass, field

import numpy as np
import torch
from scipy.optimize import minimize_scalar
from torch import nn

from . import ROOT  # noqa: F401
from models.kan_spline import bspline_basis  # noqa: E402

G_GRID = 101
RMS_TOL_REL = 0.01
FAMILIES = ("zero", "linear", "quadratic", "power", "log", "exponential", "arrhenius", "hinge")
N_COEFS = {"zero": 0, "linear": 2, "quadratic": 3, "power": 3, "log": 2, "exponential": 3, "arrhenius": 3, "hinge": 3}
# non-linear parameter grids (variable projection); values excluded where the family degenerates into a constant
_NL_GRID = {"power": np.round(np.linspace(-3.0, 3.0, 61), 10), "exponential": np.round(np.linspace(-6.0, 6.0, 61), 10),
            "arrhenius": np.round(np.linspace(-8.0, 8.0, 65), 10), "hinge": np.round(np.linspace(-0.9, 0.9, 37), 10)}
_NL_MIN_ABS = {"power": 0.05, "exponential": 0.1, "arrhenius": 0.1, "hinge": 0.0}
LIB_FILE = os.path.join(os.path.dirname(__file__), "symbolic_library.json")
T_REF, T_HI = 298.15, 308.15


class CapNotSetError(RuntimeError):
    """the per-edge coefficient cap ([ARCH: cap]) is set by the method-architect before the freeze; extraction refuses to run without it"""


def library_description():
    """canonical description of the frozen library and rule (everything that decides an extraction except the cap)"""
    return {"version": "symbolic-v1", "families": {f: N_COEFS[f] for f in FAMILIES}, "grid_points": G_GRID, "rms_tol_rel": RMS_TOL_REL,
            "nonlinear_grids": {k: [float(x) for x in v] for k, v in _NL_GRID.items()}, "nonlinear_min_abs": _NL_MIN_ABS,
            "forms": {"linear": "a*u + b", "quadratic": "a*u^2 + b*u + c", "power": "a*(p/pref)^q + c", "log": "a*log(p/pref) + c", "exponential": "a*exp(b*u) + c",
                      "arrhenius": "a*exp(b*xarr) + c, xarr = (1/298.15 - 1/T_K)/(1/298.15 - 1/308.15); temperature edges only", "hinge": "a*max(0, u - k) + c"},
            "abscissae": "u = (x - mid)/half-range of the edge's training-hull interval; p = positive physical value of the stress (T in kelvin), pref = p at the hull maximum; "
                         "deeper edges: p = (x - lo)/(hi - lo) + 0.05",
            "criterion": "BIC = G ln(max(RSS/G, tol^2)) + k ln G, tol = rms_tol_rel x largest edge range in the layer; ties: fewer coefficients, then library order",
            "refit": "end to end under the loss of the parent arm, warm start from the extracted coefficients (arms.SymbolicArm)"}


def library_hash():
    return hashlib.sha256(json.dumps(library_description(), sort_keys=True).encode()).hexdigest()


def write_library_file(path=LIB_FILE, cap=None):
    rec = {"library": library_description(), "library_sha256": library_hash(), "max_coeffs_per_edge": cap,
           "note": "max_coeffs_per_edge is set by the method-architect before the freeze (PREREG_v4 7.3 item 1, [ARCH: cap]); None = extraction refuses to run"}
    with open(path, "w", encoding="utf8") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True)
    return rec


def library_file_cap(path=LIB_FILE):
    rec = json.load(open(path, encoding="utf8"))
    if rec["library_sha256"] != library_hash():
        raise RuntimeError("symbolic_library.json does not match the library in symbolic.py (regenerate with python -m pinnkan.symbolic --write)")
    return rec["max_coeffs_per_edge"]


def resolve_cap(cap=None):
    """the cap in force: the explicit config value, else the library file's value; None raises"""
    c = cap if cap is not None else library_file_cap()
    if c is None:
        raise CapNotSetError("symbolic extraction needs the per-edge coefficient cap ([ARCH: cap], set by the method-architect before the freeze): "
                             "pass symbolic.cap in the config or fill max_coeffs_per_edge in symbolic_library.json")
    c = int(c)
    if c < 0:
        raise ValueError("cap must be >= 0")
    return c


# ------------------------------------------------------------------------------------------------ geometry of one edge
@dataclass
class EdgeGeo:
    """how the edge's input x maps to the abscissae of the families"""
    lo: float
    hi: float
    kind: str                  # 'T' (temperature; Arrhenius allowed) | 'phys' | 'hidden'
    p0: float = 0.0            # positive abscissa p = max(p0 + p1 * x, P_MIN)
    p1: float = 1.0
    name: str = ""

    P_MIN = 1e-6

    @property
    def mid(self):
        return 0.5 * (self.lo + self.hi)

    @property
    def half(self):
        return max(0.5 * (self.hi - self.lo), 1e-12)

    def p(self, x):
        return np.maximum(self.p0 + self.p1 * np.asarray(x, float), self.P_MIN)

    @property
    def pref(self):
        return float(self.p(self.hi))

    def u(self, x):
        return (np.asarray(x, float) - self.mid) / self.half

    def xarr(self, x):
        return (1.0 / T_REF - 1.0 / self.p(x)) / (1.0 / T_REF - 1.0 / T_HI)

    def degenerate(self):
        return not (self.hi - self.lo > 1e-9)


def _cols(family, geo, x, nl):
    u = geo.u(x)
    one = np.ones_like(u)
    if family == "linear":
        return np.stack([u, one], 1)
    if family == "quadratic":
        return np.stack([u * u, u, one], 1)
    if family == "power":
        return np.stack([(geo.p(x) / geo.pref) ** nl, one], 1)
    if family == "log":
        return np.stack([np.log(geo.p(x) / geo.pref), one], 1)
    if family == "exponential":
        return np.stack([np.exp(nl * u), one], 1)
    if family == "arrhenius":
        return np.stack([np.exp(nl * geo.xarr(x)), one], 1)
    if family == "hinge":
        return np.stack([np.maximum(0.0, u - nl), one], 1)
    raise ValueError(family)


def _lsq(cols, y):
    coef, *_ = np.linalg.lstsq(cols, y, rcond=None)
    r = cols @ coef - y
    return coef, float(r @ r)


def _theta(family, coef, nl):
    """pack to the stored layout: linear [a,b]; quadratic [a2,a1,a0]; power [a,q,c]; log [a,c]; exponential [a,b,c]; arrhenius [a,b,c]; hinge [a,k,c]"""
    if family in ("linear", "quadratic", "log"):
        return np.asarray(coef, float)
    return np.array([coef[0], nl, coef[1]], float)


def fit_family(family, geo, x, y):
    """-> (theta, rss) of one family on (x, y)"""
    if family == "zero":
        return np.zeros(0), float(y @ y)
    if family in ("linear", "quadratic", "log"):
        coef, rss = _lsq(_cols(family, geo, x, None), y)
        return _theta(family, coef, None), rss
    grid = [g for g in _NL_GRID[family] if abs(g) >= _NL_MIN_ABS[family] - 1e-12]
    res = [_lsq(_cols(family, geo, x, g), y)[1] for g in grid]
    i = int(np.argmin(res))
    lo, hi = grid[max(i - 1, 0)], grid[min(i + 1, len(grid) - 1)]
    best = (res[i], grid[i])
    if hi > lo:
        r = minimize_scalar(lambda g: _lsq(_cols(family, geo, x, g), y)[1], bounds=(lo, hi), method="bounded", options={"xatol": 1e-8})
        if r.fun < best[0]:
            best = (float(r.fun), float(r.x))
    coef, rss = _lsq(_cols(family, geo, x, best[1]), y)
    return _theta(family, coef, best[1]), rss


def eval_family(family, geo, theta, x):
    """numpy evaluation (tests, reports)"""
    x = np.asarray(x, float)
    if family == "zero":
        return np.zeros_like(x)
    th = np.asarray(theta, float)
    if family in ("linear", "quadratic", "log"):
        return _cols(family, geo, x, None) @ th
    return _cols(family, geo, x, th[1]) @ np.array([th[0], th[2]])


@dataclass
class EdgeFit:
    family: str
    theta: np.ndarray
    rss: float
    bic: float
    n_coefs: int
    tol: float
    table: dict = field(default_factory=dict)      # family -> (bic, rss) for every eligible family


def choose_family(geo, x, y, cap, tol, allowed=None):
    """frozen rule 2-3: BIC over the eligible families on the grid (x, y)"""
    n = len(x)
    best, table = None, {}
    for order, f in enumerate(FAMILIES):
        if allowed is not None and f not in allowed:
            continue
        if N_COEFS[f] > cap or (f == "arrhenius" and geo.kind != "T"):
            continue
        theta, rss = fit_family(f, geo, x, y)
        bic = n * float(np.log(max(rss / n, tol * tol, 1e-300))) + N_COEFS[f] * float(np.log(n))
        table[f] = (bic, rss)
        key = (round(bic, 9), N_COEFS[f], order)
        if best is None or key < best[0]:
            best = (key, f, theta, rss, bic)
    _, f, theta, rss, bic = best
    return EdgeFit(f, theta, rss, bic, N_COEFS[f], tol, table)


# ------------------------------------------------------------------------------------------------ torch modules
class SymEdge(nn.Module):
    def __init__(self, family, theta, geo: EdgeGeo, spline=None):
        super().__init__()
        self.family, self.geo_name = family, geo.name
        self.kind = geo.kind
        for k, v in (("mid_", geo.mid), ("half_", geo.half), ("p0", geo.p0), ("p1", geo.p1), ("pref", geo.pref)):
            self.register_buffer(k, torch.tensor(float(v)))
        if family == "spline":                                  # untruncated mode: the edge as the KAN has it
            self.base_w = nn.Parameter(spline["base_w"].clone())
            self.spline_w = nn.Parameter(spline["spline_w"].clone())
            self.register_buffer("knots", spline["knots"].clone())
            self.k = int(spline["k"])
            self.theta = None
        elif family == "zero":
            self.theta = None
        else:
            self.theta = nn.Parameter(torch.tensor(np.asarray(theta, float), dtype=torch.float32))

    def n_coefs(self):
        if self.family == "spline":
            return int(self.base_w.numel() + self.spline_w.numel())
        return 0 if self.theta is None else int(self.theta.numel())

    def p(self, x):
        return (self.p0 + self.p1 * x).clamp_min(EdgeGeo.P_MIN)

    def forward(self, x):
        f, th = self.family, self.theta
        if f == "zero":
            return torch.zeros_like(x)
        if f == "spline":
            b = bspline_basis(x.unsqueeze(1), self.knots, self.k)[:, 0, :]
            return self.base_w * nn.functional.silu(x) + b @ self.spline_w
        u = (x - self.mid_) / self.half_
        if f == "linear":
            return th[0] * u + th[1]
        if f == "quadratic":
            return th[0] * u * u + th[1] * u + th[2]
        if f == "power":
            return th[0] * (self.p(x) / self.pref) ** th[1].clamp(-6.0, 6.0) + th[2]
        if f == "log":
            return th[0] * torch.log(self.p(x) / self.pref) + th[1]
        if f == "exponential":
            return th[0] * torch.exp((th[1] * u).clamp(max=20.0)) + th[2]
        if f == "arrhenius":
            xa = (1.0 / T_REF - 1.0 / self.p(x)) / (1.0 / T_REF - 1.0 / T_HI)
            return th[0] * torch.exp((th[1] * xa).clamp(max=20.0)) + th[2]
        if f == "hinge":
            return th[0] * torch.relu(u - th[1]) + th[2]
        raise ValueError(f)

    def spline_l2(self):
        if self.family == "spline":
            return (self.spline_w ** 2).sum()
        return torch.zeros(()) if self.theta is None else (self.theta ** 2).sum()


class SymLayer(nn.Module):
    def __init__(self, edges):
        super().__init__()
        self.edges = nn.ModuleList(nn.ModuleList(row) for row in edges)     # edges[j][i]: input i -> output j
        self.n_out, self.n_in = len(edges), len(edges[0])

    def forward(self, x):
        return torch.stack([sum(e(x[:, i]) for i, e in enumerate(row)) for row in self.edges], 1)


class SymbolicStack(nn.Module):
    """drop-in for `KANStack` in the calendar slot of `law.Law` (call signature (N, n_in) -> (N, n_out))"""

    def __init__(self, layers, report=None):
        super().__init__()
        self.sym_layers = nn.ModuleList(layers)
        self.layers = []                       # law.Law.reg iterates `cal.layers` for spline coefficients: none here
        self.report = report or {}

    def forward(self, x):
        for l in self.sym_layers:
            x = l(x)
        return x

    def edges(self):
        return [e for l in self.sym_layers for row in l.edges for e in row]

    def n_coefs(self):
        return sum(e.n_coefs() for e in self.edges())

    def spline_l2(self):
        return sum(e.spline_l2() for e in self.edges())


class SymbolicMap(nn.Module):
    """drop-in for `law.KANMap`: cyclic log-rate map f(s) of the law; same interface (forward, spline_l2, sparsity)"""

    def __init__(self, stack: SymbolicStack):
        super().__init__()
        self.net = stack

    def forward(self, s):
        return self.net(s.clamp(-1.0, 1.0 - 1e-6))[:, 0]

    def spline_l2(self):
        return self.net.spline_l2()

    def sparsity(self):
        return torch.zeros(())

    def n_coefs(self):
        return self.net.n_coefs()


# ------------------------------------------------------------------------------------------------ extraction
def kan_layers(stack):
    """the `KANLayer`s of a KANStack / KAN (or of a law.KANMap via .net)"""
    st = getattr(stack, "net", stack)
    return list(st.layers)


def _edge_function(layer, j, i, g):
    """the learned univariate function of edge (j <- i) on the points g (numpy), exactly as KANLayer.forward uses it"""
    gt = torch.tensor(g, dtype=torch.float32)
    b = bspline_basis(gt.unsqueeze(1), layer.knots, layer.k)[:, 0, :]
    with torch.no_grad():
        v = layer.base_w[j, i] * nn.functional.silu(gt) + b @ layer.spline_w[j, i]
    return v.numpy().astype(float)


def _spline_payload(layer, j, i):
    return {"base_w": layer.base_w[j, i].detach(), "spline_w": layer.spline_w[j, i].detach(), "knots": layer.knots, "k": layer.k}


def extract_stack(stack, geos0, hidden_sample, cap=None, untruncated=False, allowed=None):
    """Extract a stack of KANLayers into a SymbolicStack.
    geos0: EdgeGeo of every input of the first layer (training hull of that input; kind/p0/p1 per the input's physical meaning).
    hidden_sample: (N, n_in) clamped inputs at which the first-layer activations define the hull of the deeper edges (training stress vectors).
    -> (SymbolicStack, report)"""
    if not untruncated:
        cap = resolve_cap(cap)
    layers = kan_layers(stack)
    x = torch.tensor(np.asarray(hidden_sample), dtype=torch.float32)
    geos = list(geos0)
    sym_layers, rep_layers = [], []
    for li, layer in enumerate(layers):
        n_out, n_in = layer.base_w.shape
        assert len(geos) == n_in
        grids = [np.linspace(g.lo, g.hi, G_GRID) if not g.degenerate() else np.array([g.lo]) for g in geos]
        vals = [[_edge_function(layer, j, i, grids[i]) for i in range(n_in)] for j in range(n_out)]
        ranges = [float(np.ptp(v)) if len(v) > 1 else 0.0 for row in vals for v in row]
        tol = RMS_TOL_REL * max(ranges + [1e-12])
        rows, rep_rows = [], []
        for j in range(n_out):
            row, rep_row = [], []
            for i in range(n_in):
                g, geo, y = grids[i], geos[i], vals[j][i]
                if untruncated:
                    row.append(SymEdge("spline", None, geo, _spline_payload(layer, j, i)))
                    rep_row.append({"family": "spline", "n_coefs": row[-1].n_coefs()})
                    continue
                if geo.degenerate() or len(g) < 5:
                    fit = EdgeFit("zero", np.zeros(0), float(y @ y), float("nan"), 0, tol)
                else:
                    fit = choose_family(geo, g, y, cap, tol, allowed)
                row.append(SymEdge(fit.family, fit.theta, geo))
                rep_row.append({"family": fit.family, "theta": [float(t) for t in fit.theta], "rss": fit.rss, "bic": fit.bic, "n_coefs": fit.n_coefs, "name": geo.name,
                                "lo": geo.lo, "hi": geo.hi, "range": float(np.ptp(y)) if len(y) > 1 else 0.0,
                                "bic_table": {k: [float(v[0]), float(v[1])] for k, v in fit.table.items()}})
            rows.append(row)
            rep_rows.append(rep_row)
        sym_layers.append(SymLayer(rows))
        rep_layers.append({"layer": li, "tol": tol, "edges": rep_rows})
        with torch.no_grad():                                       # hull of the next layer's inputs: the KAN's own activations on the training stress vectors
            x = layer(x)
        z = x.numpy().astype(float)
        geos = []
        for j in range(n_out):
            lo, hi = float(z[:, j].min()), float(z[:, j].max())
            geos.append(EdgeGeo(lo, hi, "hidden", p0=0.05 - lo / max(hi - lo, 1e-12), p1=1.0 / max(hi - lo, 1e-12), name=f"h{li}_{j}"))
    rep = {"layers": rep_layers, "n_coefs": int(sum(e.n_coefs() for l in sym_layers for row in l.edges for e in row)), "cap": cap, "untruncated": bool(untruncated),
           "library_sha256": library_hash()}
    return SymbolicStack(sym_layers, rep), rep


def stress_geos(spec, s_train):
    """EdgeGeo of every stress input of the cyclic map from the normalised training stress rows (N, d)"""
    s = np.asarray(s_train, float)
    out = []
    for i, name in enumerate(spec.stress_names):
        lo_s, hi_s = float(spec.stress_lo[i]), float(spec.stress_hi[i])
        p1 = 0.5 * (hi_s - lo_s)                        # raw = lo + (x + 1)/2 (hi - lo)
        p0 = lo_s + 0.5 * (hi_s - lo_s) + (273.15 if i == spec.t_index else 0.0)
        out.append(EdgeGeo(float(s[:, i].min()), float(s[:, i].max()), "T" if i == spec.t_index else "phys", p0=p0, p1=p1, name=name))
    return out


def calendar_geo(spec, s_cal):
    """EdgeGeo of the SOC input of the calendar KAN from the normalised SOC column of the training cells (storage SOC and cycling SOC_mid)"""
    k = spec.soc_index
    lo_s, hi_s = float(spec.stress_lo[k]), float(spec.stress_hi[k])
    s = np.asarray(s_cal, float)
    return EdgeGeo(float(s.min()), float(s.max()), "phys", p0=lo_s + 0.5 * (hi_s - lo_s), p1=0.5 * (hi_s - lo_s), name=spec.stress_names[k])


def extract_law(law, spec, s_cyc_train, s_cal_train, cap=None, untruncated=False):
    """law: a fitted law.Law (cyclic map KANMap with .net, calendar KANStack or None). -> (SymbolicMap, SymbolicStack|None, report)"""
    cyc, rep_c = extract_stack(law.cyc, stress_geos(spec, s_cyc_train), np.clip(s_cyc_train, -1.0, 1.0 - 1e-6), cap, untruncated)
    cal, rep_k = (None, None)
    if law.cal is not None:
        g = calendar_geo(spec, s_cal_train)
        cal, rep_k = extract_stack(law.cal, [g], np.clip(np.asarray(s_cal_train)[:, None], -1.0, 1.0 - 1e-6), cap, untruncated)
    first = rep_c["layers"][0]["edges"]
    labels = {}
    for i, name in enumerate(spec.stress_names):
        labels[name] = sorted({first[j][i]["family"] for j in range(len(first))})
    report = {"cyclic": rep_c, "calendar": rep_k, "input_family_labels": labels, "n_coefs": rep_c["n_coefs"] + (rep_k["n_coefs"] if rep_k else 0),
              "library_sha256": library_hash(), "cap": rep_c["cap"], "untruncated": bool(untruncated)}
    return SymbolicMap(cyc), cal, report


def describe(report):
    """one line per edge (the closed form as text), for the appendix"""
    out = []
    for part in ("cyclic", "calendar"):
        r = report.get(part)
        if not r:
            continue
        for L in r["layers"]:
            for j, row in enumerate(L["edges"]):
                for i, e in enumerate(row):
                    out.append(f"{part} layer {L['layer']} edge {j}<-{i}: {e['family']} {np.round(e.get('theta', []), 4).tolist()}")
    return out


if __name__ == "__main__":
    import sys
    if "--write" in sys.argv:
        rec = write_library_file(LIB_FILE, cap=library_file_cap() if os.path.isfile(LIB_FILE) else None)
        print(LIB_FILE, rec["library_sha256"])
    else:
        print(library_hash())
