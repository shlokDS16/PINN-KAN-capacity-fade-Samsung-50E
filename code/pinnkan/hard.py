"""Hard-ODE arm (A2; also the backbone-tournament model): the law integrated exactly (closed form of law.drive_to_state), per-cell
offsets delta_c fitted on the training records, and MAP-inferred from the window of a held-out cell (causal)."""
import torch
from torch import nn

from . import law as _law   # TAU is read at call time here (sensitivity row (m): A2-only)
from .law import (GRAD_CLIP, SIGMA, clip_and_count, clip_fraction, new_clip_stats, Law, Batch, batch_forecast_query, batch_from_cells, batch_from_windows, build_stress_map, drive_to_state,
                  init_levels, retention_from_y)


class HardODE(nn.Module):
    def __init__(self, spec, law: Law, n_cells, backbone, n_ind=0):
        super().__init__()
        self.spec, self.law, self.backbone = spec, law, backbone
        self.delta = nn.Parameter(torch.zeros(n_cells))
        self.beta = nn.Parameter(torch.zeros(n_ind)) if n_ind else None      # lab-and-stage indicators: prior mean of delta_c = ind . beta (rows 9.8(ii))

    def prior_mean(self, ind):
        return 0.0 if (self.beta is None or ind is None) else ind @ self.beta

    def predict_y(self, b: Batch, delta):
        a_cal, a_cyc = self.law.amplitudes(b.s, b.is_cyc, delta)
        phi = a_cal[b.obs_cell] * b.obs_t + a_cyc[b.obs_cell] * b.obs_E
        return drive_to_state(phi, self.backbone)

    def loss(self, b: Batch, l2, sparsity):
        r = self.predict_y(b, self.delta) - b.obs_y
        n = r.numel()
        return (r ** 2).mean() / SIGMA ** 2 + ((self.delta - self.prior_mean(b.ind)) ** 2).sum() / (_law.TAU ** 2 * n) + self.law.reg(l2, sparsity)


def make_law(spec, batch, hp, backbone):
    cal0, cyc0 = init_levels(batch, spec, backbone)
    return Law(spec, build_stress_map(hp.get("map", "kan"), spec, hp), grid_cal=int(hp.get("grid_cal", 5)), log_cal0=cal0, log_cyc0=cyc0)


def fit_hard(batch: Batch, spec, hp, backbone, seed, steps=1200, lr=0.02, clip=GRAD_CLIP):
    torch.manual_seed(seed)
    m = HardODE(spec, make_law(spec, batch, hp, backbone), batch.C, backbone, n_ind=0 if batch.ind is None else int(batch.ind.shape[1]))
    opt = torch.optim.Adam(m.parameters(), lr=lr)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=lr * 0.05)
    l2, sp = float(hp.get("l2", 1e-4)), float(hp.get("sparsity", 0.0))
    stats = new_clip_stats()
    for _ in range(steps):
        opt.zero_grad(set_to_none=True)
        L = m.loss(batch, l2, sp)
        L.backward()
        clip_and_count(m.parameters(), clip, stats)       # D013 C1: one recipe for all gradient-trained arms (measured inert on A2)
        opt.step()
        sch.step()
    m.clip_fraction = clip_fraction(stats)
    return m


def fit_delta(m: HardODE, bw: Batch):
    """per-cell offsets of held-out cells from their window points, model frozen: the common inversion routine (damped Newton, float64, prior mode, D023); prior N(mu, TAU^2) with mu the
    indicator prior mean (0 in the primary analysis); a window with the reference point only keeps the prior mean (k = 0)."""
    from . import inversion
    prob = inversion.hard_problem(m, bw)
    res = inversion.solve(prob, "hard")
    return res.P[:, 0].float()


def split_by_cell(b: Batch, values):
    out = {}
    v = values.detach().numpy()
    cells = b.obs_cell.numpy()
    for c, cid in enumerate(b.ids):
        out[cid] = v[cells == c]
    return out


def predict_hard(m: HardODE, spec, wcells):
    bw = batch_from_windows(spec, wcells, indicator=m.beta is not None)
    delta = fit_delta(m, bw)
    bq = batch_forecast_query(spec, wcells)
    with torch.no_grad():
        y = m.predict_y(bq, delta)
    return {k: retention_from_y(spec, v) for k, v in split_by_cell(bq, y).items()}, delta
