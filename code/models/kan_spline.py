"""Compact B-spline KAN in plain torch (own implementation, NOT pykan; pykan 0.2.8 MultKAN carries grid-update and
symbolic bookkeeping that a timing-critical inner loop does not need).

Layer: y_j = sum_i [ w_b[j,i] * silu(x_i) + sum_m c[j,i,m] * B_m(x_i) ]   (Liu et al. 2024 form, without the
per-edge learnable scale), cubic B-splines (k=3) on a uniform grid with G intervals on [lo, hi]. Inputs are
expected in [lo, hi] (normalised stress); outside the grid the spline part is 0 and the silu base term carries.
"""
import torch
from torch import nn


def bspline_basis(x, knots, k):
    """x: (N, I); knots: (G + 2k + 1,) uniform. Returns (N, I, G + k). Cox-de Boor, vectorised."""
    x = x.unsqueeze(-1)
    b = ((x >= knots[:-1]) & (x < knots[1:])).to(x.dtype)  # degree 0: (N, I, G+2k)
    for p in range(1, k + 1):
        left = (x - knots[: -(p + 1)]) / (knots[p:-1] - knots[: -(p + 1)])
        right = (knots[p + 1:] - x) / (knots[p + 1:] - knots[1:-p])
        b = left * b[..., :-1] + right * b[..., 1:]
    return b


class KANLayer(nn.Module):
    def __init__(self, n_in, n_out, grid=5, k=3, lo=-1.0, hi=1.0, init_scale=0.1):
        super().__init__()
        self.n_in, self.n_out, self.k, self.grid = n_in, n_out, k, grid
        h = (hi - lo) / grid
        self.register_buffer("knots", lo + h * torch.arange(-k, grid + k + 1, dtype=torch.float32))
        self.base_w = nn.Parameter(torch.randn(n_out, n_in) * init_scale)
        self.spline_w = nn.Parameter(torch.randn(n_out, n_in, grid + k) * init_scale * 0.5)

    def forward(self, x):
        b = bspline_basis(x, self.knots, self.k)  # (N, I, G+k)
        return nn.functional.silu(x) @ self.base_w.T + b.reshape(x.shape[0], -1) @ self.spline_w.reshape(self.n_out, -1).T


class KAN(nn.Module):
    def __init__(self, widths, grid=5, k=3, lo=-1.0, hi=1.0):
        super().__init__()
        self.layers = nn.ModuleList(KANLayer(a, b, grid, k, lo, hi) for a, b in zip(widths[:-1], widths[1:]))

    def forward(self, x):
        for l in self.layers:
            x = l(x)
        return x

    def n_params(self):
        return sum(p.numel() for p in self.parameters())
