"""pinnkan: law, stress maps, hard ODE, PINN residual / collocation, data-only F, A10, baselines, synthetic recovery.
    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_models.py -q        (CPU, single thread; about a minute)"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest
import torch

torch.set_num_threads(1)

from pinnkan import arms, baselines, data, hard, law, pinn, semi, synth
from pinnkan.data import EFCCurve, WindowRule, prepare_many
from pinnkan.specs import SPECS

SPEC = SPECS["synthetic"]


@pytest.fixture(scope="module")
def g0():
    S = synth.make_synthetic("G0", seed=1)
    tr, te = synth.split_conditions(S.cells, 0.25, 1)
    return S, tr, te


# ------------------------------------------------------------------------------------------------ backbones and the closed form
@pytest.mark.parametrize("bb", law.BACKBONES)
def test_drive_state_roundtrip(bb):
    y = torch.linspace(0.0, 3.0, 25, dtype=torch.float64)
    phi = law.state_to_drive(y, bb)
    assert torch.allclose(law.drive_to_state(phi, bb), y, atol=1e-9)


@pytest.mark.parametrize("bb", law.BACKBONES)
def test_closed_form_equals_rk4_with_piecewise_constant_nu(bb):
    t = np.array([0, 20, 50, 90, 140, 200], float)
    e = np.array([0, 10, 12, 40, 41, 70], float)                       # piecewise-constant EFC rate (includes a near-rest interval)
    curve = EFCCurve(t, e)
    a_cal, a_cyc = 0.15, 0.9
    tq = t[1:] / SPEC.t_scale
    ref = law.rk4_reference(a_cal, a_cyc, curve, tq, SPEC, bb)
    phi = a_cal * torch.tensor(tq) + a_cyc * torch.tensor(curve.value(t[1:]) / SPEC.efc_scale)
    cf = law.drive_to_state(phi, bb).numpy()
    assert np.allclose(cf, ref, rtol=2e-5, atol=1e-7), (cf, ref)


# ------------------------------------------------------------------------------------------------ stress maps
def test_stress_maps_shapes_params_and_edges():
    s = torch.tensor(np.random.default_rng(0).uniform(-1, 1, (7, 5)), dtype=torch.float32)
    s[0] = 1.0                                                          # exactly on the upper spline edge: must not collapse to zero basis
    for kind, hp in [("kan", {"h": 4, "grid": 5}), ("gam", {"grid": 5}), ("igam", {"grid": 5, "igrid": 3}), ("param", {}), ("mlp", {"width": 8, "depth": 2})]:
        m = law.build_stress_map(kind, SPEC, hp)
        out = m(s)
        assert out.shape == (7,) and torch.isfinite(out).all()
        assert float(m.spline_l2()) >= 0.0
    gam, kan = law.build_stress_map("gam", SPEC, {"grid": 5}), law.build_stress_map("kan", SPEC, {"h": 4, "grid": 5})
    assert law.n_params(gam) < law.n_params(kan)
    assert hasattr(kan, "sparsity") and float(kan.sparsity()) > 0


def test_igam_is_gam_plus_tensor_terms_and_mlp_is_capped():
    m = law.build_stress_map("igam", SPEC, {"grid": 5, "igrid": 3})
    assert len(m.pairs) == 3 and m.W.shape == (3, 36)                  # (3 + 3)^2 tensor coefficients per pair
    cap = law.kan_param_count(5, 8, 12)
    mlp = law.build_stress_map("mlp", SPEC, {"width": 32, "depth": 3})
    assert law.n_params(mlp) <= cap


def test_parametric_map_is_log_linear_in_features():
    m = law.build_stress_map("param", SPEC, {})
    with torch.no_grad():
        m.w[:] = torch.arange(1, m.nfeat + 1, dtype=torch.float32)
    s = torch.tensor(SPEC.norm(np.array([[35.0, 0.5, 0.2, 0.5, 1.0], [45.0, 0.4, 0.3, 1.0, 0.5]])), dtype=torch.float32)
    f = m.feats(s)
    assert f.shape == (2, m.nfeat) and torch.allclose(m(s), f @ m.w)
    assert f[1, 0] > f[0, 0]                                            # Arrhenius abscissa increases with temperature


def test_law_storage_cells_have_no_cycling_term_and_offsets_gate_correctly(g0):
    S, tr, te = g0
    b = law.batch_from_cells(SPEC, tr)
    L = law.Law(SPEC, law.build_stress_map("kan", SPEC, {"h": 3, "grid": 3}), log_cal0=-3.0, log_cyc0=-1.0)
    delta = torch.full((b.C,), 0.5)
    a_cal, a_cyc = L.amplitudes(b.s, b.is_cyc, delta)
    sto = b.is_cyc < 0.5
    base_cal, base_cyc = L.r_cal(b.s), L.r_cyc(b.s)
    assert torch.allclose(a_cal[sto], base_cal[sto] * np.exp(0.5)) and torch.allclose(a_cal[~sto], base_cal[~sto])   # offset scales calendar of storage cells
    assert torch.allclose(a_cyc[~sto], base_cyc[~sto] * np.exp(0.5)) and torch.allclose(a_cyc[sto], base_cyc[sto])  # and the cycling term of cycling cells
    assert float(b.obs_E[b.is_cyc[b.obs_cell] < 0.5].abs().max()) == 0.0                                           # storage: no throughput
    cal0, cyc0 = law.init_levels(b, SPEC, "self_limiting")
    assert np.isfinite(cal0) and np.isfinite(cyc0)


def test_calendar_rate_increases_with_temperature_at_initialisation():
    L = law.Law(SPEC, law.build_stress_map("gam", SPEC, {"grid": 3}))
    soc = 0.8                                                           # silu(x) = 0 at x = 0, so SOC 0.5 would carry no E
    s = torch.tensor(SPEC.norm(np.array([[T, soc, 0, 0, 0] for T in (10.0, 23.0, 45.0)])), dtype=torch.float32)
    with torch.no_grad():
        L.cal.layers[0].spline_w.zero_(); L.cal.layers[0].base_w.zero_()
        L.cal.layers[0].base_w[1, 0] = 1.0                              # E(SOC) > 0 -> Arrhenius
        r = L.r_cal(s)
    assert r[0] < r[1] < r[2]


# ------------------------------------------------------------------------------------------------ PINN pieces
def test_residual_matches_analytic_derivative():
    torch.manual_seed(0)
    cyc = law.build_stress_map("gam", SPEC, {"grid": 3})
    L = law.Law(SPEC, cyc)
    m = pinn.PINNModel(SPEC, L, 3, "self_limiting")
    m.F = lambda t, s, z: 0.8 * t * t                                   # known F -> dF/dt = 1.6 t
    t = torch.tensor([0.1, 0.4, 0.7])
    a_cal, a_cyc, nu = torch.tensor([0.2, 0.2, 0.2]), torch.tensor([1.0, 0.5, 0.2]), torch.tensor([0.5, 1.0, 2.0])
    R = m.residual(t, torch.zeros(3, 5), torch.zeros(3, 2), a_cal, a_cyc, nu)
    F = 0.8 * t * t
    expect = 1.6 * t - (a_cal + a_cyc * nu) / (1.0 + F)
    assert torch.allclose(R, expect, atol=1e-6)


def test_solution_network_hard_initial_condition(g0):
    S, tr, te = g0
    m = pinn.PINNModel(SPEC, law.Law(SPEC, law.build_stress_map("gam", SPEC, {"grid": 3})), 4, "self_limiting")
    out = m.F(torch.zeros(4), torch.rand(4, 5), torch.rand(4, 2))
    assert torch.all(out == 0.0)


def test_collocation_sets_are_label_free_and_well_placed(g0):
    S, tr, te = g0
    b = law.batch_from_cells(SPEC, tr)
    col = pinn.make_collocation(SPEC, b, 0, placement="record_end")
    n = b.C
    assert col.a_t.shape[0] == n * 24 and col.a_t.min() >= 0 and col.a_t.max() <= col.t_max + 1e-6
    start = b.t_end[col.a_cell]
    assert torch.all(col.a_t >= start - 1e-6)                           # from the end of the record
    col2 = pinn.make_collocation(SPEC, b, 0, placement="whole_axis")
    assert float(col2.a_t.min()) < float(start.min())                   # whole time axis reaches earlier times
    sto_cells = torch.where(b.is_cyc < 0.5)[0]
    assert torch.all(col.a_nu[torch.isin(col.a_cell, sto_cells)] == 0)
    X = b.s.numpy()[(b.is_cyc > 0.5).numpy()]
    assert col.b_s.shape[0] == 64 * 16 and np.all(col.b_s.numpy() >= X.min(0) - 1e-6) and np.all(col.b_s.numpy() <= X.max(0) + 1e-6)
    assert torch.all(col.b_nu > 0)
    assert col.c_s.shape[0] > 0 and torch.all(col.c_s[:, 2:] == torch.tensor(SPEC.norm(np.zeros(5))[2:], dtype=torch.float32))   # twins: no cycling stress
    extra = pinn.make_collocation(SPEC, b, 0, extra_twin_raw=[(35.0, 0.45)])
    assert extra.c_s.shape[0] >= col.c_s.shape[0]


def test_hull_sampler_stays_inside_hull():
    rng = np.random.default_rng(1)
    X = rng.uniform(-1, 1, (30, 5))
    P = pinn._hull_sample(X, 50, 3)
    from scipy.spatial import Delaunay
    assert (Delaunay(X, qhull_options="QJ").find_simplex(P) >= 0).all()


# ------------------------------------------------------------------------------------------------ synthetic generator and recovery
def test_generator_levels_and_design(g0):
    S, tr, te = g0
    assert len(S.cells) == 20 * 2 + 8 and {c.kind for c in S.cells} == {"cycling", "storage"}
    finals = [10.0 * (1.0 - c.ret[-1]) for c in S.cells]
    assert 1.3 < np.median(finals) < 2.7                                # target median final y_s = 2.0 (noise only)
    assert all(c.t[0] == 0 and c.fc_ok[1:].all() for c in S.cells)
    S2 = synth.make_synthetic("G0", seed=1)
    assert np.allclose(S.cells[3].ret, S2.cells[3].ret)                 # reproducible
    assert len({c.cond for c in tr} & {c.cond for c in te}) == 0


def test_g1_misspecified_time_law_generates_and_differs_from_g0():
    g1, g0_ = synth.make_synthetic("G1", seed=2), synth.make_synthetic("G0", seed=2)
    f1 = np.median([10.0 * (1.0 - c.ret[-1]) for c in g1.cells])
    assert 1.3 < f1 < 2.7 and all(np.isfinite(c.ret).all() for c in g1.cells)
    # the exponent z(T) != 1 makes y non-proportional to the closed-form drive: ratio of mid to final y differs from G0 for the same design
    r1 = np.mean([(1 - c.ret[len(c.t) // 2]) / (1 - c.ret[-1]) for c in g1.cells if c.kind == "cycling"])
    r0 = np.mean([(1 - c.ret[len(c.t) // 2]) / (1 - c.ret[-1]) for c in g0_.cells if c.kind == "cycling"])
    assert abs(r1 - r0) > 0.005


def test_g2_surface_is_not_additive_and_g0_is_():
    rng = np.random.default_rng(0)
    raw = np.column_stack([rng.choice([23., 35., 45.], 800), rng.uniform(.3, .7, 800), rng.uniform(.05, .6, 800), rng.uniform(.2, 1, 800), rng.uniform(.2, 2, 800)])

    def additive_floor(f):
        y = f(raw)
        s = SPEC.norm(raw)
        cols = [np.ones(len(s))] + [s[:, j] ** p for j in range(5) for p in (1, 2, 3)]
        A = np.column_stack(cols)
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        return float(np.sqrt(np.mean((A @ coef - y) ** 2)) / (y.max() - y.min()))
    f0 = additive_floor(synth.make_synthetic("G0", seed=2).log_rate_cyc)
    f2 = additive_floor(synth.make_synthetic("G2", seed=2).log_rate_cyc)
    assert f0 < 0.03 and f2 > 3 * f0 and f2 > 0.02


def test_hard_ode_recovers_log_rate_surface_on_g0(g0):
    S, tr, te = g0
    b = law.batch_from_cells(SPEC, tr)
    m = hard.fit_hard(b, SPEC, {"map": "kan", "h": 4, "grid": 5, "l2": 1e-4}, "self_limiting", 0, steps=800)
    rng = np.random.default_rng(0)
    raw = np.column_stack([rng.choice([23., 35., 45.], 300), rng.uniform(.3, .7, 300), rng.uniform(.05, .6, 300), rng.uniform(.2, 1, 300), rng.uniform(.2, 2, 300)])
    with torch.no_grad():
        est = (m.law.log_cyc + m.law.cyc(torch.tensor(SPEC.norm(raw), dtype=torch.float32))).numpy()
    tru = S.log_rate_cyc(raw)
    nrmse = float(np.sqrt(np.mean((est - tru) ** 2)) / (tru.max() - tru.min()))
    assert nrmse <= 0.15, nrmse                                         # prereg P1 pass line for a well-specified generator
    prep = prepare_many(te, WindowRule.for_spec(SPEC))
    preds, delta = hard.predict_hard(m, SPEC, [p.win for p in prep])
    rm = np.mean([np.sqrt(np.mean((preds[p.cell.cell_id] - p.fc_true) ** 2)) * 100 for p in prep])
    pers = np.mean([np.sqrt(np.mean((p.win.y_last - p.fc_true) ** 2)) * 100 for p in prep])
    assert rm < 0.35 * pers and np.isfinite(delta).all()


def test_forecast_uses_window_only(g0):
    """changing a held-out cell's forecast labels must not change its prediction"""
    S, tr, te = g0
    b = law.batch_from_cells(SPEC, tr)
    m = hard.fit_hard(b, SPEC, {"map": "gam", "grid": 3, "l2": 1e-4}, "self_limiting", 0, steps=60)
    prep = prepare_many(te, WindowRule.for_spec(SPEC))
    a = hard.predict_hard(m, SPEC, [p.win for p in prep])[0]
    te2 = [data.Cell(**{**c.__dict__, "ret": np.concatenate([c.ret[:5], c.ret[5:] * 0.5])}) for c in te]
    prep2 = prepare_many(te2, WindowRule.for_spec(SPEC))
    b2 = hard.predict_hard(m, SPEC, [p.win for p in prep2])[0]
    for k in a:
        assert np.allclose(a[k], b2[k])


def test_pinn_fit_reduces_loss_and_forecasts_beat_persistence(g0):
    S, tr, te = g0
    b = law.batch_from_cells(SPEC, tr)
    m = pinn.fit_pinn(b, SPEC, {"map": "kan", "h": 3, "grid": 3, "l2": 1e-4, "lam_res": 1.0}, "self_limiting", 0, steps=250)
    assert np.isfinite(m.train_data_mse) and m.train_data_mse < 0.5 and m.train_res_msq < 0.5
    prep = prepare_many(te, WindowRule.for_spec(SPEC))
    preds, (z, delta) = pinn.predict_pinn(m, SPEC, [p.win for p in prep], 1.0, 0)
    rm = np.mean([np.sqrt(np.mean((preds[p.cell.cell_id] - p.fc_true) ** 2)) for p in prep])
    pers = np.mean([np.sqrt(np.mean((p.win.y_last - p.fc_true) ** 2)) for p in prep])
    assert np.isfinite(rm) and rm < pers


def test_data_only_f_fits_and_predicts(g0):
    S, tr, te = g0
    m = pinn.fit_data_only(law.batch_from_cells(SPEC, tr), SPEC, {"width": 16, "depth": 2, "wd": 1e-4, "zdim": 2}, 0, steps=200)
    prep = prepare_many(te, WindowRule.for_spec(SPEC))
    out = pinn.predict_data_only(m, SPEC, [p.win for p in prep])
    assert all(np.isfinite(v).all() and len(v) == len(p.win.t_fc) for p, v in zip(prep, out.values()))


# ------------------------------------------------------------------------------------------------ A10
def _a10_theta(form):
    th = np.array([-3.0, 0.4, 0.8, 1.4, -2.5, 0.7, 0.6, 0.5, 0.4, 0.3, 1.6])
    assert len(th) == form.n_params
    return th


def test_a10_parameter_recovery_on_data_from_its_own_form():
    form = semi.SemiForm(SPEC)
    th = _a10_theta(form)
    S = synth.make_synthetic("G0", n_cyc_cond=30, n_sto_cond=12, reps=1, seed=4)
    cells = []
    for c in S.cells:
        loss = form.loss(th, c.raw, c.t, c.efc)
        cells.append(data.Cell(**{**c.__dict__, "ret": 1.0 - loss}))          # noise-free data generated from the form
    hat, cost = semi.fit_semi(form, cells, n_starts=10, seed=0)
    assert cost < 1e-7, cost
    lo, hi = form.bounds()
    rel = np.abs(hat - th) / np.maximum(np.abs(th), 0.3)
    assert rel.max() < 0.05, (hat, th)
    # predictions of held-out windows
    prep = prepare_many(cells[:10], WindowRule.for_spec(SPEC))
    preds = semi.predict_semi(form, hat, [p.win for p in prep], per_cell_factor=True)
    assert max(np.max(np.abs(preds[p.cell.cell_id] - p.fc_true)) for p in prep) < 5e-3


def test_a10_per_cell_factor_removes_a_cell_scale_error():
    form = semi.SemiForm(SPEC)
    th = _a10_theta(form)
    S = synth.make_synthetic("G0", seed=5)
    c = next(c for c in S.cells if c.kind == "cycling")
    scaled = 1.0 - 1.3 * form.loss(th, c.raw, c.t, c.efc)
    cell = data.Cell(**{**c.__dict__, "ret": scaled})
    p = prepare_many([cell], WindowRule.for_spec(SPEC))[0]
    with_f = semi.predict_semi(form, th, [p.win], True)[cell.cell_id]
    without = semi.predict_semi(form, th, [p.win], False)[cell.cell_id]
    assert np.abs(with_f - p.fc_true).max() < 0.5 * np.abs(without - p.fc_true).max()


def test_a10_is_provisional_and_confirmatory_use_is_refused():
    assert semi.A10_FORM["verified"] is False and semi.A10_FORM["todo"]
    with pytest.raises(semi.UnverifiedArmError):
        semi.require_verified()
    for ds in ("isu", "snl"):                                            # cyclic-only analogue fits too
        f = semi.SemiForm(SPECS[ds])
        assert not f.has_cal and f.n_params == f.n_cyc


# ------------------------------------------------------------------------------------------------ baselines and arm registry
def test_reference_arms(g0):
    S, tr, te = g0
    prep = prepare_many(te, WindowRule.for_spec(SPEC))
    wc = [p.win for p in prep]
    r1, r2 = baselines.persistence(wc), baselines.window_linear(wc)
    for p in prep:
        assert np.all(r1[p.cell.cell_id] == p.win.y_last)
        k, c0 = np.polyfit(p.win.t_win, p.win.y_win, 1)
        assert np.allclose(r2[p.cell.cell_id], np.clip(c0 + k * p.win.t_fc, 0.0, 1.1))


def test_data_only_learners_a11_a12_run(g0):
    S, tr, te = g0
    rule = WindowRule.for_spec(SPEC)
    ctx = {"rule": rule, "backbone": "self_limiting"}
    wc = [p.win for p in prepare_many(te, rule)]
    for aid in ("A11", "A12"):
        a = arms.make_arm(aid, SPEC, arms.default_hp(aid), 0, ctx).fit(tr)
        out = a.predict(wc)
        assert set(out) == {w.cell_id for w in wc} and all(np.isfinite(v).all() for v in out.values())


def test_arm_table_matches_prereg_dimensions():
    dims = {a: arms.ARMS[a].dims for a in arms.ARMS}
    assert dims["A1"] == 6 and dims["A2"] == 4 and dims["A3"] == 3 and dims["A4"] == 4 and dims["A5"] == 5 and dims["A7"] == 5
    assert dims["A9"] == 4 and dims["A10"] == 0 and dims["A11"] == 3 and dims["A12"] == 5 and dims["A13"] == 6 and dims["A14"] == 4
    assert arms.H1B_POOL == ("A3", "A4", "A5", "A7")
    assert set(arms.ARMS["A1"].space["lam_res"][1]) == {1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0} and arms.ARMS["A1"].space["placement"][1] == ["record_end", "whole_axis"]


@pytest.mark.parametrize("aid", ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "A13", "A14", "R1", "R2"])
def test_every_arm_fits_and_predicts_on_synthetic(aid, g0):
    S, tr, te = g0
    rule = WindowRule.for_spec(SPEC)
    ctx = {"rule": rule, "backbone": "self_limiting", "steps_scale": 0.04, "a10_starts": 2}
    hp = arms.default_hp(aid)
    a = arms.make_arm(aid, SPEC, hp, 0, ctx).fit(tr)
    prep = prepare_many([c for c in te if c.kind == "cycling"] if aid != "A14" else [c for c in tr if c.kind == "storage"][:2], rule)
    out = a.predict([p.win for p in prep])
    assert set(out) == {p.cell.cell_id for p in prep} and all(np.isfinite(v).all() for v in out.values())
    assert aid in ("R1", "R2") or a.n_params > 0
