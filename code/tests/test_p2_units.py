"""Unit tests for the P2 timing-pilot building blocks (run before any timing run).
Run:  python -m pytest code/tests/test_p2_units.py -q   (from ROOT)
"""
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.append(os.path.join(os.environ.get("APPDATA", ""), "Python", "Python314", "site-packages"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import torch

from models.kan_spline import KAN, bspline_basis, KANLayer
from models import ageing_models as am


def test_bspline_partition_of_unity():
    layer = KANLayer(1, 1, grid=5, k=3)
    x = torch.linspace(-0.999, 0.999, 200).unsqueeze(1)
    b = bspline_basis(x, layer.knots, 3)
    assert b.shape == (200, 1, 8)
    assert torch.allclose(b.sum(-1), torch.ones(200, 1), atol=1e-5)
    assert (b >= -1e-7).all()


def test_kan_shapes_and_grad():
    kan = KAN([5, 3, 1])
    x = torch.rand(7, 5) * 2 - 1
    y = kan(x)
    assert y.shape == (7, 1)
    y.sum().backward()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in kan.parameters())


def test_rk4_order_and_exactness():
    # dy/dt = -y, y(0)=1: global error of RK4 shrinks ~16x when the step is halved
    f = lambda y: -y
    def run(n):
        y = torch.ones(1, dtype=torch.float64); h = 1.0 / n
        for _ in range(n):
            y = am.rk4_step(f, y, torch.tensor(h, dtype=torch.float64))
        return abs(float(y) - math.exp(-1.0))
    e1, e2 = run(10), run(20)
    assert e2 < e1 / 12.0 and e1 < 1e-5


def test_rk4_constant_rate_exact():
    y = torch.zeros(3, dtype=torch.float64)
    rate = torch.tensor([0.1, 0.2, 0.3], dtype=torch.float64)
    y = am.rk4_step(lambda y: rate, y, torch.tensor(2.0, dtype=torch.float64))
    assert torch.allclose(y, 2.0 * rate)


def test_hard_initial_condition_pinn():
    torch.manual_seed(0)
    net = am.SolutionNet(n_stress=5, n_latent=2, width=16, depth=2)
    t0 = torch.zeros(4, 1)
    out = net(t0, torch.randn(4, 5), torch.randn(4, 2))
    assert torch.all(out == 0.0)


def test_residual_zero_for_exact_solution():
    # F = r * t  solves dF/dt = r exactly: the autograd residual must vanish for any stress/latent
    t = torch.rand(6, 1, requires_grad=True)
    r = 0.37
    F = r * t
    dF = torch.autograd.grad(F.sum(), t, create_graph=True)[0]
    assert torch.allclose(dF, torch.full_like(dF, r))


def test_residual_matches_finite_difference():
    torch.manual_seed(1)
    net = am.SolutionNet(n_stress=5, n_latent=2, width=16, depth=2).double()
    s = torch.randn(5, 5, dtype=torch.float64); z = torch.randn(5, 2, dtype=torch.float64)
    t = torch.rand(5, 1, dtype=torch.float64, requires_grad=True)
    dF = torch.autograd.grad(net(t, s, z).sum(), t)[0]
    eps = 1e-6
    fd = (net(t.detach() + eps, s, z) - net(t.detach() - eps, s, z)) / (2 * eps)
    assert torch.allclose(dF, fd, atol=1e-6)


def test_law_positive_rates_and_state_factor():
    torch.manual_seed(2)
    law = am.AgeingLaw(n_cells=3)
    s = torch.rand(3, 5) * 2 - 1
    nu = torch.tensor([0.0, 1.0, 2.0])
    A = law.amplitude(s, nu, delta=torch.zeros(3))
    assert (A >= 0).all()
    # storage cell (nu = 0): amplitude equals r_cal only
    rc = law.r_cal(s)
    assert torch.allclose(A[0], rc[0])
    # state factor decreases with y (self-limiting)
    assert am.state_factor(torch.tensor(0.0)) > am.state_factor(torch.tensor(0.2))
