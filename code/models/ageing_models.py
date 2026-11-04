"""P2 minimal models: stress-conditioned ageing law with KAN stress functions, hard-ODE fit (vectorised RK4) and PINN fit.

State y_s = 10 * (1 - Q/Q0,c)  (scaled retention loss), time t_n = days / 500.
Law (judge D010 section 2, minimal version):  dy/dt = [ r_cal(s) + r_cyc(s, delta_c) * nu_c ] * h(y),  h(y) = 1 / (1 + y / Y0)
  r_cal(s)  = exp(log_cal + a(SOC) + E(SOC) * x_arr(T))     KAN [1, 2] on storage SOC -> (a, E);  x_arr = Arrhenius abscissa
  r_cyc(s)  = exp(log_cyc + f(s) + delta_c)                 KAN [5, 3, 1] on (T, SOC mid, DoD, C_ch, C_dch)
  nu_c      = equivalent full cycles per day / median over cells (0 for storage cells)
Only ONE state factor is used (no backbone tournament) and nu_c is constant per cell: this is a TIMING pilot.
"""
import torch
from torch import nn

from .kan_spline import KAN

Y0 = 1.0  # state-factor scale in y_s units (= 0.1 of retention loss)


def state_factor(y):
    return 1.0 / (1.0 + y / Y0)


def rk4_step(f, y, h):
    k1 = f(y)
    k2 = f(y + 0.5 * h * k1)
    k3 = f(y + 0.5 * h * k2)
    k4 = f(y + h * k3)
    return y + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


class AgeingLaw(nn.Module):
    def __init__(self, n_cells, grid=5, hidden=3):
        super().__init__()
        self.kan_cal = KAN([1, 2], grid=grid)
        self.kan_cyc = KAN([5, hidden, 1], grid=grid)
        self.log_cal = nn.Parameter(torch.tensor(-4.0))
        self.log_cyc = nn.Parameter(torch.tensor(-2.0))
        self.delta = nn.Parameter(torch.zeros(n_cells))

    @staticmethod
    def x_arr(s):
        # s[:, 0] in [-1, 1] maps T in [10, 40] C; Arrhenius abscissa: 0 at 25 C, ~ +1 at 35 C
        T = 298.15 + 15.0 * s[:, 0]
        return (1.0 / 298.15 - 1.0 / T) / (1.0 / 298.15 - 1.0 / 308.15)

    def r_cal(self, s):
        aE = self.kan_cal(s[:, 1:2])
        return torch.exp(self.log_cal + aE[:, 0] + aE[:, 1] * self.x_arr(s))

    def r_cyc(self, s, delta):
        return torch.exp(self.log_cyc + self.kan_cyc(s)[:, 0] + delta)

    def amplitude(self, s, nu, delta):
        return self.r_cal(s) + self.r_cyc(s, delta) * nu


class SolutionNet(nn.Module):
    """F(t, s, z) = t * g(t, s, z): hard initial condition F(0) = 0 by construction."""

    def __init__(self, n_stress=5, n_latent=2, width=64, depth=3):
        super().__init__()
        layers, d = [], 1 + n_stress + n_latent
        for _ in range(depth):
            layers += [nn.Linear(d, width), nn.Tanh()]
            d = width
        layers.append(nn.Linear(d, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, t, s, z):
        return t * self.net(torch.cat([t, s, z], dim=1))


class HardODE(nn.Module):
    def __init__(self, n_cells, grid=5, hidden=3):
        super().__init__()
        self.law = AgeingLaw(n_cells, grid, hidden)

    def forward(self, stress, nu, t_nodes):
        """stress (C,5), nu (C,), t_nodes (C,M) sorted with t_nodes[:,0] = 0; one RK4 step per node interval.
        Returns y (C,M) with y[:,0] = 0 (hard initial condition)."""
        A = self.law.amplitude(stress, nu, self.law.delta)
        f = lambda y: A * state_factor(y)
        y = torch.zeros_like(A)
        out = [y]
        dts = t_nodes[:, 1:] - t_nodes[:, :-1]
        for m in range(dts.shape[1]):
            y = rk4_step(f, y, dts[:, m])
            out.append(y)
        return torch.stack(out, dim=1)

    def loss(self, d):
        y = self.forward(d["stress"], d["nu"], d["t_nodes"])
        m = d["mask"]
        data = (((y - d["y_nodes"]) ** 2) * m).sum() / m.sum()
        return data + 1e-3 * (self.law.delta ** 2).mean(), data


class PINN(nn.Module):
    def __init__(self, n_cells, n_latent=2, width=64, depth=3, grid=5, hidden=3, lam_res=1.0):
        super().__init__()
        self.law = AgeingLaw(n_cells, grid, hidden)
        self.net = SolutionNet(5, n_latent, width, depth)
        self.z = nn.Parameter(torch.zeros(n_cells, n_latent))
        self.lam = lam_res

    def _residual(self, t, s, z, A):
        t = t.requires_grad_(True)
        F = self.net(t, s, z)
        dF = torch.autograd.grad(F.sum(), t, create_graph=True)[0]
        return dF - A.unsqueeze(1) * state_factor(F)

    def loss(self, d, gen, n_a=768, n_bc=256):
        # data term at all observed points
        ci = d["obs_cell"]
        F = self.net(d["obs_t"], d["stress"][ci], self.z[ci])
        data = ((F - d["obs_y"]) ** 2).mean()
        # collocation (a): every cell's time axis up to the fixed horizon (KAN amplitude once per cell, gathered)
        A_cell = self.law.amplitude(d["stress"], d["nu"], self.law.delta)
        ia = torch.randint(0, d["coll_a_t"].shape[0], (n_a,), generator=gen)
        ca = d["coll_a_cell"][ia]
        Ra = self._residual(d["coll_a_t"][ia].clone(), d["stress"][ca], self.z[ca], A_cell[ca])
        # collocation (b) unobserved stress points and (c) calendar twins (nu = 0): KAN evaluated on those rows
        ib = torch.randint(0, d["coll_b_t"].shape[0], (n_bc,), generator=gen)
        sb, nb = d["coll_b_s"][ib], d["coll_b_nu"][ib]
        Ab = self.law.amplitude(sb, nb, torch.zeros_like(nb))
        Rb = self._residual(d["coll_b_t"][ib].clone(), sb, torch.zeros(n_bc, self.z.shape[1]), Ab)
        res = torch.cat([Ra, Rb]).pow(2).mean()
        return data + self.lam * res + 1e-3 * (self.law.delta ** 2).mean(), data, res
