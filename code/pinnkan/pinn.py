"""Soft-residual PINN arms (A1, A3, A4, A5, A7, A13, A14) and the data-only solution network (A9).

Solution network F(t_n, s, z_c) = t_n * g(t_n, s, z_c)  (hard initial condition F(0)=0, tanh MLP width 32 depth 3, z_c of dim 2, as P5).
Residual (D010 section 2):  R = dF/dt_n - [ a_cal + a_cyc * nu(t) ] * h(F)  by autograd, collocation (all label-free):
  (a) along every training cell's time axis, from the end of its record (or from 0: tuned categorical `placement`) to t_max,
  (b) at unobserved stress points: a fixed Latin-hypercube sample inside the convex hull of the training design (nu from the design),
  (c) at the calendar twins (T, SOC_mid) of cycling conditions with nu = 0 (+ any extra design points passed in, e.g. 35 C in Test C).
Loss = (data + lam_res * mean R^2) / SIGMA^2 + prior(delta_c) + prior(z_c) + map regularisation.
Test time: z_c and delta_c are fitted to the window plus the residual over the forecast horizon (causal; network and law frozen)."""
import zlib
from dataclasses import dataclass

import numpy as np
import torch
from scipy.spatial import Delaunay
from scipy.stats import qmc
from torch import nn

from models.ageing_models import SolutionNet  # noqa: E402  (pilot module, imported not edited)

from .hard import make_law, split_by_cell
from .law import (GRAD_CLIP, SIGMA, TAU, WARMUP, Batch, Law, batch_forecast_query, batch_from_windows, clip_and_count, clip_fraction, new_clip_stats, retention_from_y,
                  state_factor)


@dataclass
class Collocation:
    a_t: torch.Tensor
    a_cell: torch.Tensor
    a_nu: torch.Tensor
    b_s: torch.Tensor
    b_t: torch.Tensor
    b_nu: torch.Tensor
    c_s: torch.Tensor
    c_t: torch.Tensor
    t_max: float


def _hull_sample(X, n, seed):
    """n points of a Latin-hypercube sample of the bounding box of X that lie inside the convex hull of X (fallback: the box).
    A constant column of X (span <= 1e-9, e.g. a neutralised stress input, PREREG_v4 9.9 (u)) is not sampled: the hull and the sample are formed on the non-constant columns and the constant
    columns are set to their value exactly (the points of the neutralised collocation set carry the neutral value, not a joggled or random one). Without a constant column the original code runs."""
    lo, hi = X.min(0), X.max(0)
    const = (hi - lo) <= 1e-9
    if const.any():
        free = ~const
        P = np.tile(lo, (n, 1))
        if free.any():
            P[:, free] = _hull_sample(X[:, free], n, seed) if free.sum() >= 2 else lo[free] + qmc.LatinHypercube(d=int(free.sum()), seed=seed + 99).random(n) * (hi - lo)[free]
        return P
    span = np.where(hi - lo > 1e-9, hi - lo, 1.0)
    pts = []
    try:
        tri = Delaunay(X, qhull_options="QJ")
        for rep in range(8):
            u = qmc.LatinHypercube(d=X.shape[1], seed=seed + rep).random(4 * n)
            p = lo + u * span
            pts.append(p[tri.find_simplex(p) >= 0])
            if sum(len(q) for q in pts) >= n:
                break
        P = np.concatenate(pts)
    except Exception:
        P = np.empty((0, X.shape[1]))
    if len(P) < n:
        P = np.concatenate([P, lo + qmc.LatinHypercube(d=X.shape[1], seed=seed + 99).random(n - len(P)) * span])
    return P[:n]


def make_collocation(spec, b: Batch, seed, placement="record_end", n_a_per_cell=24, n_hull=64, n_tb=16, n_tc=16, extra_twin_raw=None, t_max=None):
    g = torch.Generator().manual_seed(seed)
    t_max = float(1.1 * b.t_end.max()) if t_max is None else t_max
    C = b.C
    start = b.t_end if placement == "record_end" else torch.zeros(C)
    u = torch.rand(C, n_a_per_cell, generator=g)
    a_t = start.unsqueeze(1) + u * (t_max - start).clamp_min(0.0).unsqueeze(1)
    a_nu = torch.zeros_like(a_t)
    to_n = spec.t_scale / spec.efc_scale
    for c in range(C):
        a_nu[c] = torch.tensor(b.curves[c].rate(a_t[c].numpy() * spec.t_scale) * to_n, dtype=torch.float32)
    a_cell = torch.arange(C).unsqueeze(1).expand(C, n_a_per_cell).reshape(-1)
    cyc = (b.is_cyc > 0.5).numpy()
    X = b.s.numpy()[cyc]
    if len(X) >= 2:
        H = _hull_sample(X, n_hull, seed)
        raw = spec.denorm(H)
        nu_h = torch.tensor(spec.efc_rate(raw) * to_n, dtype=torch.float32)
        Hs = torch.tensor(H, dtype=torch.float32)
    else:
        Hs, nu_h = torch.zeros(0, spec.d), torch.zeros(0)
    nb = Hs.shape[0]
    b_t = torch.rand(nb, n_tb, generator=g) * t_max
    b_s = Hs.unsqueeze(1).expand(nb, n_tb, spec.d).reshape(-1, spec.d)
    b_nu = nu_h.unsqueeze(1).expand(nb, n_tb).reshape(-1)
    # (c) calendar twins
    if spec.has_calendar:
        rows = {(round(float(r[spec.t_index]), 6), round(float(r[spec.soc_index]), 6)) for r in spec.denorm(b.s.numpy()[cyc])}
        for r in (extra_twin_raw if extra_twin_raw is not None else []):
            rows.add((round(float(r[0]), 6), round(float(r[1]), 6)))
        raw = np.zeros((len(rows), spec.d))
        for i, (T, soc) in enumerate(sorted(rows)):
            raw[i, spec.t_index], raw[i, spec.soc_index] = T, soc
        cs = torch.tensor(spec.norm(raw), dtype=torch.float32)
    else:
        cs = torch.zeros(0, spec.d)
    nc = cs.shape[0]
    c_t = torch.rand(nc, n_tc, generator=g) * t_max
    c_s = cs.unsqueeze(1).expand(nc, n_tc, spec.d).reshape(-1, spec.d)
    return Collocation(a_t.reshape(-1), a_cell, a_nu.reshape(-1), b_s, b_t.reshape(-1), b_nu, c_s, c_t.reshape(-1), t_max)


class PINNModel(nn.Module):
    def __init__(self, spec, law: Law, n_cells, backbone, width=32, depth=3, zdim=2, n_ind=0):
        super().__init__()
        self.spec, self.law, self.backbone = spec, law, backbone
        self.net = SolutionNet(spec.d, zdim, width, depth)
        self.z = nn.Parameter(torch.zeros(n_cells, zdim))
        self.delta = nn.Parameter(torch.zeros(n_cells))
        self.zdim = zdim
        self.beta = nn.Parameter(torch.zeros(n_ind)) if n_ind else None      # lab-and-stage indicators: prior mean of delta_c = ind . beta (rows 9.8(ii))

    def prior_mean(self, ind):
        """prior mean of the per-cell offset (zeros in the primary analysis)"""
        if self.beta is None or ind is None:
            return 0.0
        return ind @ self.beta

    def F(self, t, s, z):
        return self.net(t.unsqueeze(1), s, z)[:, 0]

    def residual(self, t, s, z, a_cal, a_cyc, nu):
        t = t.clone().requires_grad_(True)
        F = self.F(t, s, z)
        dF = torch.autograd.grad(F.sum(), t, create_graph=True)[0]
        return dF - (a_cal + a_cyc * nu) * state_factor(F, self.backbone)

    def residual_terms(self, b: Batch, col: Collocation, gen, delta, z, n_a, n_b, n_c):
        law = self.law
        A_cal, A_cyc = law.amplitudes(b.s, b.is_cyc, delta)
        ia = torch.randint(0, col.a_t.shape[0], (n_a,), generator=gen)
        ca = col.a_cell[ia]
        out = [self.residual(col.a_t[ia], b.s[ca], z[ca], A_cal[ca], A_cyc[ca], col.a_nu[ia])]
        if col.b_t.numel() and n_b:
            ib = torch.randint(0, col.b_t.shape[0], (n_b,), generator=gen)
            sb = col.b_s[ib]
            out.append(self.residual(col.b_t[ib], sb, torch.zeros(n_b, self.zdim), law.r_cal(sb), law.r_cyc(sb), col.b_nu[ib]))
        if col.c_t.numel() and n_c:
            ic = torch.randint(0, col.c_t.shape[0], (n_c,), generator=gen)
            sc = col.c_s[ic]
            out.append(self.residual(col.c_t[ic], sc, torch.zeros(n_c, self.zdim), law.r_cal(sc), torch.zeros(n_c), torch.zeros(n_c)))
        return torch.cat(out)

    def loss(self, b: Batch, col: Collocation, lam, l2, sparsity, gen, n_a=512, n_b=192, n_c=64):
        F = self.F(b.obs_t, b.s[b.obs_cell], self.z[b.obs_cell])
        r = F - b.obs_y
        n = r.numel()
        data = (r ** 2).mean()
        R = self.residual_terms(b, col, gen, self.delta, self.z, n_a, n_b, n_c)
        res = (R ** 2).mean()
        tot = (data + lam * res) / SIGMA ** 2 + ((self.delta - self.prior_mean(b.ind)) ** 2).sum() / (TAU ** 2 * n) + (self.z ** 2).sum() / n + self.law.reg(l2, sparsity)
        return tot, data, res


def fit_pinn(b: Batch, spec, hp, backbone, seed, steps=2000, lr=5e-3, extra_twin_raw=None, warmup=WARMUP, clip=GRAD_CLIP, law=None, init_from=None):
    """law / init_from: the end-to-end refit of A15 / G15 (symbolic.py): a prebuilt law (symbolic stress map) and a fitted PINNModel whose solution network, latents and offsets
    are the warm start; the loss, recipe and collocation are those of every other PINN arm"""
    torch.manual_seed(seed)
    law = make_law(spec, b, hp, backbone) if law is None else law
    m = PINNModel(spec, law, b.C, backbone, width=32, depth=3, zdim=2, n_ind=0 if b.ind is None else int(b.ind.shape[1]))
    if init_from is not None:
        m.net.load_state_dict(init_from.net.state_dict())
        with torch.no_grad():
            m.z.copy_(init_from.z)
            m.delta.copy_(init_from.delta)
            if m.beta is not None and init_from.beta is not None:
                m.beta.copy_(init_from.beta)
    col = make_collocation(spec, b, seed, placement=hp.get("placement", "record_end"), extra_twin_raw=extra_twin_raw)
    m.col_t_max = col.t_max
    m.pts_per_cell = b.obs_t.numel() / b.C
    opt = torch.optim.Adam(m.parameters(), lr=lr)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=lr * 0.1)
    gen = torch.Generator().manual_seed(seed + 17)
    lam, l2, sp = float(hp.get("lam_res", 1.0)), float(hp.get("l2", 1e-4)), float(hp.get("sparsity", 0.0))
    last = (float("nan"), float("nan"))
    stats = new_clip_stats()
    for it in range(steps):
        opt.zero_grad(set_to_none=True)
        ramp = min(1.0, (it + 1) / max(warmup * steps, 1.0))     # residual weight ramps 0 -> lam_res over the first 40 % of steps (data-first warm-up)
        L, data, res = m.loss(b, col, lam * ramp, l2, sp, gen)
        L.backward()
        clip_and_count(m.parameters(), clip, stats)
        opt.step()
        sch.step()
        last = (float(data.detach()), float(res.detach()))
    m.train_data_mse, m.train_res_msq = last
    m.clip_fraction = clip_fraction(stats)
    return m


def invert_pinn(m: PINNModel, bw: Batch, lam, seed, n_col=16, z_weight=None):
    """z_c, delta_c of held-out cells: ONE routine for every inverting arm (inversion.invert_latents: per-cell damped Newton, float64, from the prior mode z = 0, delta = prior mean,
    stop at ||g|| <= 1e-6 (1 + |f|) or 100 iterations, non-converged cells kept and counted; D023). Objective: window points + A1's residual over (window end, t_max] with per-cell seeded
    collocation draws + priors; the z prior has weight 1, the weight of the training loss (fit_pinn: (z**2).sum() / n against the mean data term). Causal: no label after the window.
    A cell whose window holds the reference point only keeps the prior mode (k = 0). Returns float32 latents for the (float32) trained network."""
    from . import inversion
    prob = inversion.pinn_problem(m, bw, None, lam, seed, n_col, z_weight)
    res = inversion.solve(prob, "pinn")
    z, delta = prob["split"](res.P)
    return z.float(), delta.float()


def predict_pinn(m: PINNModel, spec, wcells, lam, seed, z_weight=None):
    bw = batch_from_windows(spec, wcells, indicator=m.beta is not None)
    z, delta = invert_pinn(m, bw, lam, seed, z_weight=z_weight)
    bq = batch_forecast_query(spec, wcells)
    with torch.no_grad():
        F = m.F(bq.obs_t, bq.s[bq.obs_cell], z[bq.obs_cell])
    return {k: retention_from_y(spec, v) for k, v in split_by_cell(bq, F).items()}, (z, delta)


# ------------------------------------------------------------------------------------------------ A9: data-only solution network
class DataOnlyF(nn.Module):
    def __init__(self, spec, n_cells, width, depth, zdim, n_ind=0):
        super().__init__()
        self.spec, self.zdim = spec, zdim
        self.net = SolutionNet(spec.d, zdim, width, depth)
        self.z = nn.Parameter(torch.zeros(n_cells, zdim))
        self.B = nn.Parameter(torch.zeros(n_ind, zdim)) if n_ind else None      # lab-and-stage indicators: prior mean of z_c = ind . B (rows 9.8(ii))

    def z_prior(self, ind):
        return 0.0 if (self.B is None or ind is None) else ind @ self.B

    def F(self, t, s, z):
        return self.net(t.unsqueeze(1), s, z)[:, 0]

    def weight_l2(self):
        return sum((p ** 2).sum() for n, p in self.net.named_parameters() if n.endswith("weight"))


def fit_data_only(b: Batch, spec, hp, seed, steps=1500, lr=5e-3, clip=GRAD_CLIP):
    torch.manual_seed(seed)
    m = DataOnlyF(spec, b.C, int(hp.get("width", 32)), int(hp.get("depth", 3)), int(hp.get("zdim", 2)), n_ind=0 if b.ind is None else int(b.ind.shape[1]))
    opt = torch.optim.Adam(m.parameters(), lr=lr)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=lr * 0.1)
    wd = float(hp.get("wd", 1e-4))
    stats = new_clip_stats()
    for _ in range(steps):
        opt.zero_grad(set_to_none=True)
        r = m.F(b.obs_t, b.s[b.obs_cell], m.z[b.obs_cell]) - b.obs_y
        n = r.numel()
        ((r ** 2).mean() / SIGMA ** 2 + ((m.z - m.z_prior(b.ind)) ** 2).sum() / n + wd * m.weight_l2()).backward()
        clip_and_count(m.parameters(), clip, stats)       # same clip as the PINN arms (D013 C1): no optimiser-recipe confound in H1a
        opt.step()
        sch.step()
    m.clip_fraction = clip_fraction(stats)
    return m


def predict_data_only(m: DataOnlyF, spec, wcells, z_weight=None):
    """A9 forecast: z_c by the same routine as every inverting arm (prior mode z = prior mean, damped Newton in float64; D023); z prior weight 1 = the training loss weight."""
    from . import inversion
    bw = batch_from_windows(spec, wcells, indicator=m.B is not None)
    prob = inversion.data_problem(m, bw, None, z_weight)
    res = inversion.solve(prob, "data")
    z = res.P.float()
    bq = batch_forecast_query(spec, wcells)
    with torch.no_grad():
        F = m.F(bq.obs_t, bq.s[bq.obs_cell], z[bq.obs_cell])
    return {k: retention_from_y(spec, v) for k, v in split_by_cell(bq, F).items()}
