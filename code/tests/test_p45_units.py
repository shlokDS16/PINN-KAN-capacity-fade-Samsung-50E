"""Unit tests for the P4 / P5 generators and building blocks (run before any pilot run).
Run:  .venv/Scripts/python.exe -P -m pytest code/tests/test_p45_units.py -q   (from ROOT)
"""
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.join(ROOT, "code", "pilots"))

import numpy as np
import pytest
import torch

import synth_gen as SG
import p45_common as PC
from models import ageing_p45 as M
from models.ageing_models import rk4_step

torch.set_num_threads(1)


@pytest.fixture(scope="module")
def design():
    return SG.Design(ROOT)


def test_design_counts_and_forcing(design):
    assert design.n_cond == 63 and design.n_cells == 251
    assert design.x.min() == -1.0 and design.x.max() == 1.0
    # 100 % DoD at 0.5 C both ways: 2 h + 2 h + 0.5 h rest = 4.5 h -> 168/4.5 cycles per week
    assert SG.cycles_per_week(np.array([0.5, 0.5, 100.0])) == pytest.approx(168.0 / 4.5)
    assert np.isclose(np.median(design.nu_norm), 1.0)
    for w in design.cell_weeks:
        assert w[0] == 0.0 and np.all(np.diff(w) > 0)


def test_hull_lhs_inside_hull(design):
    pts = design.hull_lhs(500)
    assert pts.shape == (500, 3) and np.all(design._hull.find_simplex(pts) >= 0)
    assert np.allclose(pts, design.hull_lhs(500))  # fixed seed -> same points


def test_g2_known_parameters_reproduce_known_values():
    p = dict(b1=0.5, b2=0.0, b3=0.0, q=0.0, H=1.0, c0h=0.0, c1h=-0.5, P=0.0)
    tr = SG.G2Truth(p)
    # hinge active: x1 = 0.8, x3 = 0.4 -> relu(0.8 - (0 - 0.2)) = 1.0 ; shape = 0.5*0.8 + 1.0
    assert tr.shape(np.array([0.8, 0.3, 0.4])) == pytest.approx(1.4)
    # hinge inactive: x1 = -0.5, x3 = 0.4 -> relu(-0.5 + 0.2) = 0 ; shape = -0.25
    assert tr.shape(np.array([-0.5, 0.3, 0.4])) == pytest.approx(-0.25)
    # threshold shifts with DoD: same x1 = 0.1 is above threshold at x3 = 0.5 (thr = -0.25) and below at x3 = -0.5 (thr = 0.25)
    assert tr.shape(np.array([0.1, 0, 0.5])) - 0.05 == pytest.approx(0.35)
    assert tr.shape(np.array([0.1, 0, -0.5])) == pytest.approx(0.05)
    tr2 = SG.G2Truth(dict(b1=0, b2=0, b3=0, q=0, H=0, c0h=0, c1h=0, P=1.0))
    assert tr2.shape(np.array([0.2, 0.5, -0.6])) == pytest.approx(-0.3)
    tr3 = SG.G2Truth(dict(b1=0, b2=0, b3=0, q=0.3, H=0, c0h=0, c1h=0, P=0))
    assert tr3.shape(np.array([0.0, 0.0, 0.5])) == pytest.approx(0.075)


def test_g2_curve_is_the_exact_solution_of_the_ode(design):
    ds = SG.make_dataset("G2", 0, design, noise=False)
    tr = ds.truth
    for c in (0, 100, 250):
        k = design.cell_cond[c]
        A = math.exp(tr.log_rate(design.x[k])) * design.nu_norm[k] * math.exp(ds.delta[c])
        t = torch.tensor(design.cell_weeks[c] / SG.T_SCALE)
        y = torch.zeros(1)
        f = lambda y: A / (1.0 + y)
        ys = [0.0]
        for i in range(len(t) - 1):
            # many RK4 substeps per interval
            h = (t[i + 1] - t[i]) / 200
            for _ in range(200):
                y = rk4_step(f, y, h)
            ys.append(float(y))
        assert np.max(np.abs(np.array(ys) - ds.y_true[c])) < 1e-4


@pytest.mark.parametrize("kind", ["G1", "G2"])
def test_level_match_and_first_point_and_monotone(design, kind):
    for draw in range(3):
        ds = SG.make_dataset(kind, draw, design, noise=True)
        fin = np.array([y[-1] for y in ds.y_true])
        assert np.median(fin) == pytest.approx(SG.FADE_TARGET, abs=1e-6)
        assert all(y[0] == 0.0 for y in ds.y_obs) and all(y[0] == 0.0 for y in ds.y_true)
        assert all(np.all(np.diff(y) > 0) for y in ds.y_true)


def test_noise_statistics_and_noise_off(design):
    ds = SG.make_dataset("G2", 1, design, noise=True)
    e = np.concatenate([(o - t)[1:] for o, t in zip(ds.y_obs, ds.y_true)])
    assert abs(e.mean()) < 0.005 and e.std() == pytest.approx(SG.SIGMA_Y, rel=0.05)
    d0 = SG.make_dataset("G2", 1, design, noise=False)
    assert all(np.array_equal(o, t) for o, t in zip(d0.y_obs, d0.y_true))
    # the noiseless curves of the same draw are identical with and without noise
    assert all(np.allclose(a, b) for a, b in zip(ds.y_true, d0.y_true))
    # draw offsets have the nominal sd
    assert ds.delta.std() == pytest.approx(SG.TAU_DELTA, rel=0.2)


def test_draws_reproducible_and_different():
    assert SG.draw_params("G2", 3) == SG.draw_params("G2", 3)
    assert len({tuple(SG.draw_params("G2", d).items()) for d in range(5)}) >= 4
    assert len(set(SG.split_conditions(0))) == 12 and not np.array_equal(SG.split_conditions(0), SG.split_conditions(1))


def test_g1_known_parameters_and_misspecification(design):
    p = dict(b1=0, b2=0, b3=0, z0=1.0, z1=0.0, K=0.0)
    tr = SG.G1Truth(p)
    tr.c0 = math.log(2.0)
    w = np.array([0.0, 10.0, 20.0, 40.0])
    # z = 1, K = 0 : y = 2 * (t_n / 0.4) exactly linear in t
    tr.efc_ref = 1.0
    y = tr.y_of(np.zeros(3), 10.0, 0.0, w)
    assert np.allclose(y, 2.0 * (w / SG.T_SCALE / SG.G1_T_REF))
    # knee only: power term off by c0 -> -inf; K sigmoid: at tau = tau0 the knee equals K (0.5 - sig(-tau0/w))
    p2 = dict(b1=0, b2=0, b3=0, z0=1.0, z1=0.0, K=1.0)
    t2 = SG.G1Truth(p2)
    t2.c0 = -50.0
    t2.efc_ref = 100.0
    x = np.zeros(3)  # tau0 = 0.65
    wk = np.array([0.0, 65.0 / 5.0])  # efc_week 5 -> tau = 0.65 at week 13
    val = t2.y_of(x, 5.0, 0.0, wk)
    sig = lambda u: 1 / (1 + math.exp(-u))
    assert val[0] == pytest.approx(0.0, abs=1e-12)
    assert val[1] == pytest.approx(0.5 - sig(-0.65 / SG.G1_KNEE_W), abs=1e-9)
    # onset shifts with stress: higher charge rate -> earlier knee
    a = t2.y_of(np.array([1.0, 0, 0]), 5.0, 0.0, np.array([0.0, 8.0]))[1]
    b = t2.y_of(np.array([-1.0, 0, 0]), 5.0, 0.0, np.array([0.0, 8.0]))[1]
    assert a > b
    # not of the model form A/(1+y): implied exponent differs from 0.5 (sqrt law) for z = 1
    # (a hard-ODE closed form gives y ~ sqrt(t) at long times, this truth ~ t)


def test_additive_gam_cannot_represent_g2_but_can_represent_additive_truth(design):
    pts = design.hull_lhs(500)
    layer = M.KANLayer(3, 1, grid=10, k=3, lo=-1.0, hi=1.0)
    from models.kan_spline import bspline_basis
    Bm = bspline_basis(torch.tensor(pts, dtype=torch.float32), layer.knots, 3).reshape(500, -1).numpy()
    Bm = np.hstack([Bm, np.ones((500, 1))])
    full = SG.G2Truth(dict(b1=0.4, b2=0.15, b3=0.4, q=0.3, H=1.2, c0h=0.0, c1h=-0.6, P=0.8))
    onlyadd = SG.G2Truth(dict(b1=0.4, b2=0.15, b3=0.4, q=0.3, H=0.0, c0h=0.0, c1h=-0.6, P=0.0))
    res = {}
    for name, tr in (("full", full), ("add", onlyadd)):
        f = tr.shape(pts)
        coef, *_ = np.linalg.lstsq(Bm, f, rcond=None)
        res[name] = np.sqrt(np.mean((Bm @ coef - f) ** 2)) / (f.max() - f.min())
    assert res["add"] < 0.01
    assert res["full"] > 0.04  # the interaction part is outside the additive class (floor of the GAM)


def test_analytic_vs_rk4_and_free_grid_hermite():
    A = torch.tensor([0.5, 3.0, 12.0])
    t = torch.tensor([[0.0, 0.3, 1.0, 1.77]] * 3)
    ana = M.analytic_y(A.unsqueeze(1), t)
    f = lambda y: A / (1 + y)
    ys, fs = M.rk4_grid(f, 3, M.FREE_DT, M.FREE_J)
    obs_cell = torch.arange(3).repeat_interleave(4)
    inter = M.hermite_gather(ys, fs, M.FREE_DT, obs_cell, t.reshape(-1)).reshape(3, 4)
    assert (inter - ana).abs().max() < 5e-3  # <= 10 % of the noise sd (0.05) for rates up to A = 12
    # exact RK4 reference with fine steps
    y = torch.zeros(3)
    for _ in range(2000):
        y = rk4_step(f, y, 1.77 / 2000)
    assert (y - ana[:, -1]).abs().max() < 1e-5


def test_kan_param_counts_and_hidden_range():
    gam = M.StressMap("gam", grid=5)
    kan = M.StressMap("kan", grid=5, hidden=3)
    assert M.n_params(gam) == 3 * (5 + 3) + 3  # spline coefs + base weights
    assert M.n_params(kan) == (3 * 3 * 8 + 3 * 3) + (3 * 1 * 8 + 3 * 1)
    assert kan.net.layers[0].knots[3].item() == pytest.approx(-1.0) and kan.net.layers[1].knots[3].item() == pytest.approx(-2.0)
    x = torch.tensor([[1.0, 1.0, 1.0], [-1.0, -1.0, -1.0]])
    layer = M.KANLayer(1, 1, grid=5, k=3, lo=-1.0, hi=1.0)
    from models.kan_spline import bspline_basis
    assert torch.allclose(bspline_basis(torch.tensor([[1.0]]), layer.knots, 3).sum(-1), torch.ones(1, 1), atol=1e-5)


def test_pinn_residual_zero_for_exact_solution():
    m = M.PINNFit(4, c_init=math.log(3.0))
    for p in m.smap.parameters():
        torch.nn.init.zeros_(p)
    with torch.no_grad():
        m.c.copy_(torch.tensor(math.log(3.0)))
    class Exact(torch.nn.Module):
        def forward(self, t, x, z):
            return M.analytic_y(torch.tensor(3.0), t)

    m.net = Exact()
    t = torch.linspace(0.05, 1.7, 9)
    R = m.residual(t, torch.zeros(9, 3), torch.zeros(9, 2), torch.zeros(9), torch.zeros(9))
    assert R.abs().max() < 1e-5
    # wrong rate -> nonzero residual
    R2 = m.residual(t, torch.zeros(9, 3), torch.zeros(9, 2), torch.zeros(9), torch.full((9,), 0.5))
    assert R2.abs().max() > 0.1


def test_hard_fit_recovers_additive_truth_without_noise(design):
    """machinery check: noiseless additive truth (H = P = 0, no cell offsets) is recovered by the additive spline GAM and by the KAN"""
    ds = SG.make_dataset("G2", 0, design, noise=False)
    # overwrite the draw with an additive truth and no offsets, level matched
    ds.truth = SG.G2Truth(dict(b1=0.4, b2=0.15, b3=0.4, q=0.3, H=0.0, c0h=0.0, c1h=-0.6, P=0.0))
    ds.delta = np.zeros(design.n_cells)
    SG._solve_level(ds.truth, design, ds.delta)
    ds.y_true = ds.truth.y_cells(design, ds.delta)
    ds.y_obs = [y.copy() for y in ds.y_true]
    cells = np.arange(design.n_cells)
    d = PC.tensors(design, ds, cells)
    pts = torch.tensor(design.hull_lhs(500), dtype=torch.float32)
    ft = ds.truth.log_rate(pts.numpy())
    for kind, kw in (("gam", dict(grid=8, hidden=1)), ("kan", dict(grid=5, hidden=3))):
        m = M.fit_hard(d, kind, kw["grid"], kw["hidden"], l2=1e-4, seed=0, steps=1500)
        fh = m.log_rate(pts).detach().numpy()
        nr = np.sqrt(np.mean((fh - ft) ** 2)) / (ft.max() - ft.min())
        assert nr < 0.10, (kind, nr)
