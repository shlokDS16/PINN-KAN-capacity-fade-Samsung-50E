"""Hard-ODE arm (A2; also the backbone-tournament model): the law integrated exactly (closed form of law.drive_to_state), per-cell
offsets delta_c fitted on the training records, and MAP-inferred from the window of a held-out cell (causal)."""
import torch
from torch import nn

from .law import (GRAD_CLIP, SIGMA, TAU, clip_and_count, clip_fraction, new_clip_stats, Law, Batch, batch_forecast_query, batch_from_cells, batch_from_windows, build_stress_map, drive_to_state,
                  init_levels, retention_from_y)


class HardODE(nn.Module):
    def __init__(self, spec, law: Law, n_cells, backbone):
        super().__init__()
        self.spec, self.law, self.backbone = spec, law, backbone
        self.delta = nn.Parameter(torch.zeros(n_cells))

    def predict_y(self, b: Batch, delta):
        a_cal, a_cyc = self.law.amplitudes(b.s, b.is_cyc, delta)
        phi = a_cal[b.obs_cell] * b.obs_t + a_cyc[b.obs_cell] * b.obs_E
        return drive_to_state(phi, self.backbone)

    def loss(self, b: Batch, l2, sparsity):
        r = self.predict_y(b, self.delta) - b.obs_y
        n = r.numel()
        return (r ** 2).mean() / SIGMA ** 2 + (self.delta ** 2).sum() / (TAU ** 2 * n) + self.law.reg(l2, sparsity)


def make_law(spec, batch, hp, backbone):
    cal0, cyc0 = init_levels(batch, spec, backbone)
    return Law(spec, build_stress_map(hp.get("map", "kan"), spec, hp), grid_cal=int(hp.get("grid_cal", 5)), log_cal0=cal0, log_cyc0=cyc0)


def fit_hard(batch: Batch, spec, hp, backbone, seed, steps=1200, lr=0.02, clip=GRAD_CLIP):
    torch.manual_seed(seed)
    m = HardODE(spec, make_law(spec, batch, hp, backbone), batch.C, backbone)
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


def fit_delta(m: HardODE, bw: Batch, steps=300, lr=0.05):
    """MAP of per-cell offsets from window points, model frozen (prior sd TAU, noise SIGMA)."""
    flags = [p.requires_grad for p in m.parameters()]
    for p in m.parameters():
        p.requires_grad_(False)
    delta = torch.zeros(bw.C, requires_grad=True)
    opt = torch.optim.Adam([delta], lr=lr)
    for _ in range(steps):
        opt.zero_grad()
        r = m.predict_y(bw, delta) - bw.obs_y
        ((r ** 2).sum() / SIGMA ** 2 + (delta ** 2).sum() / TAU ** 2).backward()
        opt.step()
    for p, f in zip(m.parameters(), flags):
        p.requires_grad_(f)
    return delta.detach()


def split_by_cell(b: Batch, values):
    out = {}
    v = values.detach().numpy()
    cells = b.obs_cell.numpy()
    for c, cid in enumerate(b.ids):
        out[cid] = v[cells == c]
    return out


def predict_hard(m: HardODE, spec, wcells, steps=300):
    bw = batch_from_windows(spec, wcells)
    delta = fit_delta(m, bw, steps=steps)
    bq = batch_forecast_query(spec, wcells)
    with torch.no_grad():
        y = m.predict_y(bq, delta)
    return {k: retention_from_y(spec, v) for k, v in split_by_cell(bq, y).items()}, delta
