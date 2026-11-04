"""P4 / P5 models (new module; P2 modules are imported, not edited).

Law (common to every structured arm):  dy/dt = A_c / (1 + y),  A_c = exp(c + S(x_c)) * nu_norm(x_c) * exp(delta_c),  y(0) = 0,
S = stress map (KAN [3,h,1] | additive spline GAM = KAN [3,1]).  With this state factor the ODE has the exact solution
y(t) = sqrt(1 + 2 A_c t) - 1, so the hard ODE is integrated exactly (tested against RK4).  The free-G arm integrates its network by RK4 on a
common grid (+ cubic Hermite interpolation to the check-up times).  The PINN arm is F(t,x,z) = t g(t,x,z) with the residual dF/dt - A/(1+F).
Loss weights use fixed nominal noise / offset scales (SIGMA, TAU), identical for every arm.
"""
import math
import torch
from torch import nn

from .kan_spline import KANLayer
from .ageing_models import SolutionNet

SIGMA = 0.05  # nominal observation noise sd in y_s units (same constant in every arm)
TAU = 0.15  # nominal sd of per-cell log-rate offsets (same constant in every arm)


def analytic_y(A, t):
    return torch.sqrt(1.0 + 2.0 * A * t) - 1.0


class KANStack(nn.Module):
    """KAN with the spline grid of hidden layers widened to [-hr, hr] (hidden activations leave [-1,1]); first layer on [-1,1]."""

    def __init__(self, widths, grid, hr=2.0):
        super().__init__()
        ls = []
        for i, (a, b) in enumerate(zip(widths[:-1], widths[1:])):
            r = 1.0 if i == 0 else hr
            ls.append(KANLayer(a, b, grid=grid, k=3, lo=-r, hi=r))
        self.layers = nn.ModuleList(ls)

    def forward(self, x):
        for l in self.layers:
            x = l(x)
        return x


class StressMap(nn.Module):
    def __init__(self, kind, grid, hidden=3):
        super().__init__()
        self.kind = kind
        self.net = KANStack([3, hidden, 1], grid) if kind == "kan" else KANStack([3, 1], grid)

    def forward(self, x):
        return self.net(x)[:, 0]

    def spline_l2(self):
        return sum((l.spline_w ** 2).sum() for l in self.net.layers)


def n_params(m):
    return sum(p.numel() for p in m.parameters())


# ---------------------------------------------------------------- hard ODE (closed form)
class HardFit(nn.Module):
    def __init__(self, kind, grid, hidden, n_cells, c_init):
        super().__init__()
        self.smap = StressMap(kind, grid, hidden)
        self.c = nn.Parameter(torch.tensor(float(c_init)))
        self.delta = nn.Parameter(torch.zeros(n_cells))

    def log_rate(self, x):  # per-nu log rate
        return self.c + self.smap(x)

    def amplitude(self, d, delta):
        A_cond = torch.exp(self.log_rate(d["x_cond"])) * d["nu_cond"]
        return A_cond[d["cell_cond"]] * torch.exp(delta)

    def predict(self, d, delta):
        A = self.amplitude(d, delta)
        return analytic_y(A[d["obs_cell"]], d["obs_t"])

    def loss(self, d, l2):
        r = self.predict(d, self.delta) - d["obs_y"]
        n = r.numel()
        return (r ** 2).mean() / SIGMA ** 2 + (self.delta ** 2).sum() / (TAU ** 2 * n) + l2 * self.smap.spline_l2()


def init_c(d_train):
    """data-based level start: median over cells of log(A_hat/nu), A_hat = (y + y^2/2)/t at the last point (training cells only)."""
    cell, t, y = d_train["obs_cell"], d_train["obs_t"], d_train["obs_y"]
    C = d_train["cell_cond"].shape[0]
    last_t = torch.zeros(C).scatter_reduce(0, cell, t, "amax")
    ymax = torch.zeros(C).scatter_reduce(0, cell, y, "amax")
    A = (ymax + ymax ** 2 / 2) / last_t.clamp_min(1e-3)
    lnu = torch.log(d_train["nu_cond"][d_train["cell_cond"]])
    return float(torch.median(torch.log(A.clamp_min(1e-3)) - lnu))


def fit_hard(d, kind, grid, hidden, l2, seed, steps=1200, lr=0.02):
    torch.manual_seed(seed)
    m = HardFit(kind, grid, hidden, d["cell_cond"].shape[0], init_c(d))
    opt = torch.optim.Adam(m.parameters(), lr=lr)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=lr * 0.05)
    for _ in range(steps):
        opt.zero_grad(set_to_none=True)
        L = m.loss(d, l2)
        L.backward()
        opt.step()
        sch.step()
    return m


def fit_delta_hard(m, dw, steps=300, lr=0.05):
    """MAP of per-cell offsets from window points with the model frozen"""
    for p in m.parameters():
        p.requires_grad_(False)
    delta = torch.zeros(dw["cell_cond"].shape[0], requires_grad=True)
    opt = torch.optim.Adam([delta], lr=lr)
    for _ in range(steps):
        opt.zero_grad()
        r = m.predict(dw, delta) - dw["obs_y"]
        L = (r ** 2).sum() / SIGMA ** 2 + (delta ** 2).sum() / TAU ** 2
        L.backward()
        opt.step()
    for p in m.parameters():
        p.requires_grad_(True)
    return delta.detach()


# ---------------------------------------------------------------- free G (unstructured dynamics with stress inputs), RK4 on a common grid
class FreeFit(nn.Module):
    def __init__(self, width, n_cells, c_init, zdim=1):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(1 + 3 + 1 + zdim, width), nn.Tanh(), nn.Linear(width, width), nn.Tanh(), nn.Linear(width, 1))
        nn.init.normal_(self.net[-1].weight, std=0.05)
        nn.init.zeros_(self.net[-1].bias)
        self.b0 = nn.Parameter(torch.tensor(float(c_init)))
        self.z = nn.Parameter(torch.zeros(n_cells, zdim))

    def logG(self, y, feat, z):
        return self.b0 + self.net(torch.cat([y.unsqueeze(1) / 2.0, feat, z], 1))[:, 0]

    def G(self, y, feat, z):
        return torch.exp(self.logG(y, feat, z))

    def weight_l2(self):
        return sum((p ** 2).sum() for n, p in self.net.named_parameters() if n.endswith("weight"))


def rk4_grid(G, C, dt, J):
    y = torch.zeros(C)
    ys, fs = [y], []
    for _ in range(J):
        k1 = G(y)
        k2 = G(y + 0.5 * dt * k1)
        k3 = G(y + 0.5 * dt * k2)
        k4 = G(y + dt * k3)
        fs.append(k1)
        y = y + dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
        ys.append(y)
    fs.append(G(y))
    return torch.stack(ys, 1), torch.stack(fs, 1)


def hermite_gather(ys, fs, dt, obs_cell, obs_t):
    J = ys.shape[1] - 1
    j = torch.clamp((obs_t / dt).floor().long(), max=J - 1)
    th = (obs_t - j * dt) / dt
    y0, y1 = ys[obs_cell, j], ys[obs_cell, j + 1]
    f0, f1 = fs[obs_cell, j], fs[obs_cell, j + 1]
    th2, th3 = th ** 2, th ** 3
    return (2 * th3 - 3 * th2 + 1) * y0 + (th3 - 2 * th2 + th) * dt * f0 + (-2 * th3 + 3 * th2) * y1 + (th3 - th2) * dt * f1


FREE_DT, FREE_J = 0.1, 18  # covers t_n up to 1.8


def free_feat(d):
    return torch.cat([d["x_cond"][d["cell_cond"]], torch.log(d["nu_cond"][d["cell_cond"]]).unsqueeze(1)], 1)


def free_predict(m, d, z):
    feat = free_feat(d)
    ys, fs = rk4_grid(lambda y: m.G(y, feat, z), feat.shape[0], FREE_DT, FREE_J)
    return hermite_gather(ys, fs, FREE_DT, d["obs_cell"], d["obs_t"])


def fit_free(d, width, wd, seed, steps=1200, lr=0.01):
    torch.manual_seed(seed)
    m = FreeFit(width, d["cell_cond"].shape[0], init_c(d))
    opt = torch.optim.Adam(m.parameters(), lr=lr)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=lr * 0.05)
    for _ in range(steps):
        opt.zero_grad(set_to_none=True)
        r = free_predict(m, d, m.z) - d["obs_y"]
        n = r.numel()
        L = (r ** 2).mean() / SIGMA ** 2 + (m.z ** 2).sum() / n + wd * m.weight_l2()
        L.backward()
        opt.step()
        sch.step()
    return m


def fit_z_free(m, dw, steps=150, lr=0.05):
    for p in m.parameters():
        p.requires_grad_(False)
    z = torch.zeros(dw["cell_cond"].shape[0], m.z.shape[1], requires_grad=True)
    opt = torch.optim.Adam([z], lr=lr)
    for _ in range(steps):
        opt.zero_grad()
        r = free_predict(m, dw, z) - dw["obs_y"]
        L = (r ** 2).sum() / SIGMA ** 2 + (z ** 2).sum()
        L.backward()
        opt.step()
    for p in m.parameters():
        p.requires_grad_(True)
    return z.detach()


# ---------------------------------------------------------------- PINN (soft constraint)
class PINNFit(nn.Module):
    def __init__(self, n_cells, c_init, width=32, depth=3, grid=5, hidden=3, zdim=2):
        super().__init__()
        self.smap = StressMap("kan", grid, hidden)
        self.c = nn.Parameter(torch.tensor(float(c_init)))
        self.delta = nn.Parameter(torch.zeros(n_cells))
        self.z = nn.Parameter(torch.zeros(n_cells, zdim))
        self.net = SolutionNet(3, zdim, width, depth)

    def log_rate(self, x):
        return self.c + self.smap(x)

    def residual(self, t, x, z, lognu, delta):
        """dF/dt - A/(1+F), A = exp(c + S(x) + delta) nu_norm  (rows are independent)"""
        t = t.clone().requires_grad_(True)
        F = self.net(t.unsqueeze(1), x, z)[:, 0]
        dF = torch.autograd.grad(F.sum(), t, create_graph=True)[0]
        A = torch.exp(self.log_rate(x) + lognu + delta)
        return dF - A / (1.0 + F)

    def loss(self, d, col, lam, l2, gen, n_a=512, n_b=256):
        ci = d["obs_cell"]
        xo = d["x_cond"][d["cell_cond"]][ci]
        F = self.net(d["obs_t"].unsqueeze(1), xo, self.z[ci])[:, 0]
        r = F - d["obs_y"]
        n = r.numel()
        data = (r ** 2).mean()
        ia = torch.randint(0, col["a_t"].shape[0], (n_a,), generator=gen)
        ca = col["a_cell"][ia]
        xa = d["x_cond"][d["cell_cond"][ca]]
        lna = torch.log(d["nu_cond"][d["cell_cond"][ca]])
        Ra = self.residual(col["a_t"][ia], xa, self.z[ca], lna, self.delta[ca])
        ib = torch.randint(0, col["b_t"].shape[0], (n_b,), generator=gen)
        Rb = self.residual(col["b_t"][ib], col["b_x"][ib], torch.zeros(n_b, self.z.shape[1]), col["b_lognu"][ib], torch.zeros(n_b))
        res = torch.cat([Ra, Rb]).pow(2).mean()
        tot = (data + lam * res) / SIGMA ** 2 + (self.delta ** 2).sum() / (TAU ** 2 * n) + (self.z ** 2).sum() / n + l2 * self.smap.spline_l2()
        return tot, data, res


def make_collocation(d, t_end_cell, hull_x, hull_lognu, seed, variant="record_end", n_a_per_cell=24, n_tb=16, t_max=1.8):
    """Fixed label-free collocation sets.  (a) per training cell: n_a_per_cell times from the end of its record (variant record_end, D010 section 2)
    or from 0 (variant whole_axis) to t_max;  (b) hull stress points x n_tb times in [0, t_max].  No (c) set: ISU has no storage arm."""
    g = torch.Generator().manual_seed(seed)
    C = t_end_cell.shape[0]
    start = t_end_cell if variant == "record_end" else torch.zeros(C)
    u = torch.rand(C, n_a_per_cell, generator=g)
    ta = start.unsqueeze(1) + u * (t_max - start).clamp_min(0.0).unsqueeze(1)
    a_cell = torch.arange(C).unsqueeze(1).expand(C, n_a_per_cell).reshape(-1)
    nb = hull_x.shape[0]
    tb = torch.rand(nb, n_tb, generator=g) * t_max
    b_x = hull_x.unsqueeze(1).expand(nb, n_tb, 3).reshape(-1, 3)
    b_ln = hull_lognu.unsqueeze(1).expand(nb, n_tb).reshape(-1)
    return {"a_t": ta.reshape(-1), "a_cell": a_cell, "b_t": tb.reshape(-1), "b_x": b_x, "b_lognu": b_ln}


def fit_pinn(d, col, lam, l2, seed, steps=2500, lr=5e-3):
    torch.manual_seed(seed)
    m = PINNFit(d["cell_cond"].shape[0], init_c(d))
    opt = torch.optim.Adam(m.parameters(), lr=lr)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=lr * 0.1)
    gen = torch.Generator().manual_seed(seed + 17)
    last = None
    for _ in range(steps):
        opt.zero_grad(set_to_none=True)
        L, data, res = m.loss(d, col, lam, l2, gen)
        L.backward()
        opt.step()
        sch.step()
        last = (float(data.detach()), float(res.detach()))
    m.train_data_mse, m.train_res_msq = last
    return m


def invert_pinn(m, dw, lam, t_win_end, seed, pts_per_cell, n_col=16, steps=200, lr=0.05, t_max=1.8):
    """Test-time inversion: z_c, delta_c from window points + residual over (window end, t_max]; network and law frozen. Causal: no label after the window.
    Same MAP weights as training (training objective x N: sum r^2 + lam * N * mean R^2, N/C = pts_per_cell points per training cell)."""
    for p in m.parameters():
        p.requires_grad_(False)
    Ct = dw["cell_cond"].shape[0]
    g = torch.Generator().manual_seed(seed)
    u = torch.rand(Ct, n_col, generator=g)
    tc = (t_win_end.unsqueeze(1) + u * (t_max - t_win_end).unsqueeze(1)).reshape(-1)
    cc = torch.arange(Ct).unsqueeze(1).expand(Ct, n_col).reshape(-1)
    xc = dw["x_cond"][dw["cell_cond"][cc]]
    lnc = torch.log(dw["nu_cond"][dw["cell_cond"][cc]])
    xo = dw["x_cond"][dw["cell_cond"]][dw["obs_cell"]]
    z = torch.zeros(Ct, m.z.shape[1], requires_grad=True)
    delta = torch.zeros(Ct, requires_grad=True)
    opt = torch.optim.Adam([z, delta], lr=lr)
    for _ in range(steps):
        opt.zero_grad()
        F = m.net(dw["obs_t"].unsqueeze(1), xo, z[dw["obs_cell"]])[:, 0]
        data = ((F - dw["obs_y"]) ** 2).sum()
        R = m.residual(tc, xc, z[cc], lnc, delta[cc])
        L = (data + lam * pts_per_cell * Ct * (R ** 2).mean()) / SIGMA ** 2 + (delta ** 2).sum() / TAU ** 2 + (z ** 2).sum()
        L.backward()
        opt.step()
    for p in m.parameters():
        p.requires_grad_(True)
    return z.detach(), delta.detach()
