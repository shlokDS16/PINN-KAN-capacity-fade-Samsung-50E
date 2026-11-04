"""A8: free-G arm (synthetic identifiability study H7 only; PREREG_v2 7.1, 13).  dy/dt = exp(b0 + MLP([y/2, s, log1p(nu_n), z_c])), y(0) = 0,
integrated by RK4 on a common grid with cubic Hermite interpolation to the check-up times; nu_n is the piecewise-constant EFC rate (causal after the window).
No stress-map structure, no calendar / cycling split: it is the unstructured comparator of the structured models. Per-cell latent z_c, window MAP at test time."""
import math

import numpy as np
import torch
from torch import nn

from .hard import split_by_cell
from .law import SIGMA, Batch, batch_forecast_query, batch_from_windows, retention_from_y

DT, ZDIM = 0.025, 1


class FreeG(nn.Module):
    def __init__(self, spec, n_cells, width=32, b0=-1.0):
        super().__init__()
        self.spec = spec
        self.net = nn.Sequential(nn.Linear(1 + spec.d + 1 + ZDIM, width), nn.Tanh(), nn.Linear(width, width), nn.Tanh(), nn.Linear(width, 1))
        nn.init.normal_(self.net[-1].weight, std=0.05)
        nn.init.zeros_(self.net[-1].bias)
        self.b0 = nn.Parameter(torch.tensor(float(b0)))
        self.z = nn.Parameter(torch.zeros(n_cells, ZDIM))

    def G(self, y, s, nu, z):
        return torch.exp(self.b0 + self.net(torch.cat([y.unsqueeze(1) / 2.0, s, torch.log1p(nu).unsqueeze(1), z], 1))[:, 0])

    def weight_l2(self):
        return sum((p ** 2).sum() for n, p in self.net.named_parameters() if n.endswith("weight"))


def _grid(spec, b: Batch, t_end):
    J = int(math.ceil(t_end / DT)) + 1
    mid = (np.arange(J) + 0.5) * DT * spec.t_scale
    to_n = spec.t_scale / spec.efc_scale
    nu = np.stack([b.curves[c].rate(mid) * to_n for c in range(b.C)])
    return J, torch.tensor(nu, dtype=torch.float32)


def _integrate(m: FreeG, b: Batch, z, J, nu):
    y = torch.zeros(b.C)
    ys, fl, fr = [y], [], []
    for j in range(J):
        n = nu[:, j]
        k1 = m.G(y, b.s, n, z)
        k2 = m.G(y + 0.5 * DT * k1, b.s, n, z)
        k3 = m.G(y + 0.5 * DT * k2, b.s, n, z)
        k4 = m.G(y + DT * k3, b.s, n, z)
        y = y + DT / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
        fl.append(k1)
        fr.append(m.G(y, b.s, n, z))
        ys.append(y)
    return torch.stack(ys, 1), torch.stack(fl, 1), torch.stack(fr, 1)


def _hermite(ys, fl, fr, cell, t):
    J = fl.shape[1]
    j = torch.clamp((t / DT).floor().long(), max=J - 1)
    th = (t - j * DT) / DT
    y0, y1, f0, f1 = ys[cell, j], ys[cell, j + 1], fl[cell, j], fr[cell, j]
    th2, th3 = th ** 2, th ** 3
    return (2 * th3 - 3 * th2 + 1) * y0 + (th3 - 2 * th2 + th) * DT * f0 + (-2 * th3 + 3 * th2) * y1 + (th3 - th2) * DT * f1


def predict_y(m, b, z, J, nu):
    ys, fl, fr = _integrate(m, b, z, J, nu)
    return _hermite(ys, fl, fr, b.obs_cell, b.obs_t)


def fit_free(b: Batch, spec, hp, seed, steps=1000, lr=0.01):
    torch.manual_seed(seed)
    J, nu = _grid(spec, b, float(b.obs_t.max()) + 1e-6)
    m = FreeG(spec, b.C, int(hp.get("width", 32)))
    opt = torch.optim.Adam(m.parameters(), lr=lr)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=lr * 0.05)
    wd = float(hp.get("wd", 1e-4))
    for _ in range(steps):
        opt.zero_grad(set_to_none=True)
        r = predict_y(m, b, m.z, J, nu) - b.obs_y
        n = r.numel()
        ((r ** 2).mean() / SIGMA ** 2 + (m.z ** 2).sum() / n + wd * m.weight_l2()).backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 20.0)
        opt.step()
        sch.step()
    return m


def predict_free(m: FreeG, spec, wcells, steps=150, lr=0.05):
    bw = batch_from_windows(spec, wcells)
    bq = batch_forecast_query(spec, wcells)
    t_end = float(max(bw.obs_t.max(), bq.obs_t.max())) + 1e-6
    Jw, nuw = _grid(spec, bw, t_end)
    flags = [p.requires_grad for p in m.parameters()]
    for p in m.parameters():
        p.requires_grad_(False)
    z = torch.zeros(bw.C, ZDIM, requires_grad=True)
    opt = torch.optim.Adam([z], lr=lr)
    for _ in range(steps):
        opt.zero_grad()
        r = predict_y(m, bw, z, Jw, nuw) - bw.obs_y
        ((r ** 2).sum() / SIGMA ** 2 + (z ** 2).sum()).backward()
        opt.step()
    for p, f in zip(m.parameters(), flags):
        p.requires_grad_(f)
    with torch.no_grad():
        Jq, nuq = _grid(spec, bq, t_end)
        y = predict_y(m, bq, z.detach(), Jq, nuq)
    return {k: retention_from_y(spec, v) for k, v in split_by_cell(bq, y).items()}


def log_rate_surface(m: FreeG, spec, raw):
    """log G at y = 0, z = 0 minus log nu_n(design) for cycling rows: log(r_cyc + r_cal / nu), the free-G counterpart of the structured log-rate (approximate)"""
    s = torch.tensor(spec.norm(raw), dtype=torch.float32)
    nu = torch.tensor(spec.efc_rate(raw) * spec.t_scale / spec.efc_scale, dtype=torch.float32)
    with torch.no_grad():
        g = m.G(torch.zeros(s.shape[0]), s, nu, torch.zeros(s.shape[0], ZDIM))
    return (torch.log(g) - torch.log(nu.clamp_min(1e-9))).numpy()
