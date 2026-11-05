"""build_v2 item 3: A15 / G15 symbolic extraction (PREREG_v4 7.3; D016 judge 3 and 5.5). Limiting cases:
noiseless law recovered; untruncated library reproduces A1 to float tolerance; G15 == A15 when h = 1 and the outer edge is linear; one code path for both arms.
    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_v2_symbolic.py -q"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest
import torch

torch.set_num_threads(1)

from models.kan_spline import KANLayer, bspline_basis  # noqa: E402
from pinnkan import arms as A
from pinnkan import data as D
from pinnkan import law, pinn, symbolic as S, synth
from pinnkan.hard import fit_hard
from pinnkan.specs import SPECS

SPEC = SPECS["synthetic"]


# ------------------------------------------------------------------------------------------------ frozen library, hash, cap
PINNED_CAP = 2          # D021 (debates/D021_cap/01_architect.md): the cap pinned in symbolic_library.json before the freeze


def test_library_file_matches_the_code_and_the_cap_is_the_pinned_value():
    rec = json.load(open(S.LIB_FILE, encoding="utf8"))
    assert rec["library_sha256"] == S.library_hash() and rec["library"] == json.loads(json.dumps(S.library_description()))
    assert rec["max_coeffs_per_edge"] == PINNED_CAP and S.library_file_cap() == PINNED_CAP and S.resolve_cap(None) == PINNED_CAP
    assert set(rec["library"]["families"]) == {"zero", "linear", "quadratic", "power", "log", "exponential", "arrhenius", "hinge"}
    assert len(S.library_hash()) == 64
    # D021: at the pinned cap the eligible families are exactly the two-coefficient ones (and zero); the other five stay in the hashed library but are never selected
    assert {f for f, n in S.N_COEFS.items() if n <= PINNED_CAP} == {"zero", "linear", "log"}


def test_extraction_refuses_to_run_while_the_cap_is_unset(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "library_file_cap", lambda path=S.LIB_FILE: None)            # the situation before D021: neither a config value nor a file value
    with pytest.raises(S.CapNotSetError):
        S.resolve_cap(None)
    assert S.resolve_cap(3) == 3
    kan = law.KANMap(5, None, 4)
    s = np.random.default_rng(0).uniform(-0.8, 0.8, (20, 5))
    with pytest.raises(S.CapNotSetError):
        S.extract_stack(kan, S.stress_geos(SPEC, s), s)


def test_the_cap_is_a_three_way_switch_and_caps_above_the_largest_family_change_nothing():
    """D021 reading of the code: N_COEFS tops out at 3, so cap 0/1 prune every edge, cap 2 leaves {zero, linear, log}, cap >= 3 is the whole library"""
    geo = _geo("T")
    x = np.linspace(geo.lo, geo.hi, S.G_GRID)
    for fam, (kind, theta) in TRUTH.items():
        g = _geo(kind)
        xx = np.linspace(g.lo, g.hi, S.G_GRID)
        y = S.eval_family(fam, g, theta, xx)
        f3, f4, f9 = (S.choose_family(g, xx, y, c, 1e-6) for c in (3, 4, 9))
        assert f3.family == f4.family == f9.family and np.array_equal(f3.theta, f4.theta) and np.array_equal(f3.theta, f9.theta) and set(f3.table) == set(f4.table) == set(f9.table)
        assert S.choose_family(g, xx, y, 1, 1e-6).family == "zero" and S.choose_family(g, xx, y, 0, 1e-6).family == "zero"
        assert S.choose_family(g, xx, y, 2, 1e-6).family in ("zero", "linear", "log")
    assert S.choose_family(geo, x, S.eval_family("linear", geo, [0.5, 0.1], x), 1, 1e-6).n_coefs == 0


def test_library_hash_changes_with_the_rule(monkeypatch):
    h = S.library_hash()
    monkeypatch.setattr(S, "RMS_TOL_REL", 0.02)
    assert S.library_hash() != h


# ------------------------------------------------------------------------------------------------ one edge: every family is recovered from noiseless data
def _geo(kind="phys"):
    if kind == "T":
        return S.EdgeGeo(-0.8, 0.6, "T", p0=273.15 + 5 + 22.5, p1=22.5, name="T_C")
    return S.EdgeGeo(-0.6, 0.8, "phys", p0=1.0, p1=1.0, name="x")


TRUTH = {
    "linear": ("phys", [0.7, 0.2]), "quadratic": ("phys", [0.5, 0.3, -0.1]), "power": ("phys", [1.2, 0.5, -0.3]), "log": ("phys", [0.8, 0.1]),
    "exponential": ("phys", [0.4, 1.5, -0.2]), "arrhenius": ("T", [0.5, 2.5, 0.1]), "hinge": ("phys", [0.9, 0.2, 0.1]),
}


@pytest.mark.parametrize("family", list(TRUTH))
def test_each_library_family_is_recovered_from_noiseless_data(family):
    kind, theta = TRUTH[family]
    geo = _geo(kind)
    x = np.linspace(geo.lo, geo.hi, S.G_GRID)
    y = S.eval_family(family, geo, theta, x)
    fit = S.choose_family(geo, x, y, cap=3, tol=1e-6)
    assert fit.family == family, (family, fit.family, fit.table)
    assert np.allclose(fit.theta, theta, atol=2e-3)
    assert np.max(np.abs(S.eval_family(fit.family, geo, fit.theta, x) - y)) < 1e-4


def test_zero_wins_on_a_vanishing_edge_and_arrhenius_only_on_temperature():
    geo = _geo()
    x = np.linspace(geo.lo, geo.hi, S.G_GRID)
    assert S.choose_family(geo, x, np.zeros_like(x), 3, 1e-3).family == "zero"
    y = S.eval_family("arrhenius", _geo("T"), TRUTH["arrhenius"][1], x)
    assert "arrhenius" not in S.choose_family(geo, x, y, 3, 1e-6).table             # not eligible on a non-temperature edge
    assert "arrhenius" in S.choose_family(_geo("T"), x, y, 3, 1e-6).table


def test_the_cap_removes_families_and_bic_prefers_fewer_coefficients_at_equal_fit():
    geo = _geo()
    x = np.linspace(geo.lo, geo.hi, S.G_GRID)
    y = S.eval_family("quadratic", geo, TRUTH["quadratic"][1], x)
    assert S.choose_family(geo, x, y, 3, 1e-6).family == "quadratic"
    assert S.choose_family(geo, x, y, 2, 1e-6).n_coefs <= 2 and "quadratic" not in S.choose_family(geo, x, y, 2, 1e-6).table
    assert S.choose_family(geo, x, y, 0, 1e-6).family == "zero"
    lin = 0.5 * geo.u(x) + 0.1
    f = S.choose_family(geo, x, lin, 3, 1e-6)
    assert f.family == "linear" and f.table["quadratic"][1] < 1e-18               # quadratic fits equally well, linear wins on the penalty


def test_extraction_without_an_explicit_cap_uses_the_pinned_cap_and_only_two_coefficient_families():
    funcs = [lambda z: 0.8 * z, lambda z: 0.5 * z * z - 0.1 * z, lambda z: 0.3 * z, lambda z: -0.6 * z, lambda z: 0.0 * z]
    a15, _ = _kan_pair(funcs)
    s = _train_stress()
    stack, rep = S.extract_stack(a15, S.stress_geos(SPEC, s), s)                 # no cap argument: the file value
    assert rep["cap"] == PINNED_CAP
    assert all(e["family"] in ("zero", "linear", "log") for L in rep["layers"] for row in L["edges"] for e in row)
    assert all(e["n_coefs"] <= PINNED_CAP for L in rep["layers"] for row in L["edges"] for e in row)


def test_torch_edge_equals_the_numpy_family():
    for fam, (kind, theta) in TRUTH.items():
        geo = _geo(kind)
        x = np.linspace(geo.lo, geo.hi, 41)
        e = S.SymEdge(fam, theta, geo)
        got = e(torch.tensor(x, dtype=torch.float32)).detach().numpy()
        assert np.allclose(got, S.eval_family(fam, geo, theta, x), atol=2e-5), fam
        assert e.n_coefs() == S.N_COEFS[fam]


# ------------------------------------------------------------------------------------------------ a KAN built from known pieces
def _set_edge(layer, j, i, fn, lo, hi):
    """spline coefficients of edge (j <- i) = least-squares projection of fn on the layer's B-spline basis over [lo, hi] (exact for polynomials of degree <= 3); base term off"""
    g = torch.linspace(lo + 1e-4, hi - 1e-4, 400)
    B = bspline_basis(g.unsqueeze(1), layer.knots, layer.k)[:, 0, :]
    c = torch.linalg.lstsq(B, fn(g).unsqueeze(1)).solution[:, 0]
    with torch.no_grad():
        layer.base_w[j, i] = 0.0
        layer.spline_w[j, i] = c


def _kan_pair(h1_funcs, outer_slope=0.7):
    """KAN [5,1,1] (A15 shape) whose first-layer edges are `h1_funcs` and whose outer edge is exactly linear, and the additive GAM KAN [5,1] with the composed edges"""
    a15 = law.KANMap(5, 1, 5)
    l1, l2 = a15.net.layers
    for i, fn in enumerate(h1_funcs):
        _set_edge(l1, 0, i, fn, -1.0, 1.0)
    _set_edge(l2, 0, 0, lambda z: outer_slope * z, -2.0, 2.0)
    g15 = law.KANMap(5, None, 5)
    for i, fn in enumerate(h1_funcs):
        _set_edge(g15.net.layers[0], 0, i, lambda z, fn=fn: outer_slope * fn(z), -1.0, 1.0)
    return a15, g15


def _train_stress(n=60, seed=1):
    return np.random.default_rng(seed).uniform(-0.9, 0.9, (n, 5))


def test_g15_equals_a15_when_h_is_one_and_the_outer_edge_is_linear():
    funcs = [lambda z: 0.8 * z, lambda z: 0.5 * z * z - 0.1 * z, lambda z: 0.3 * z, lambda z: -0.6 * z, lambda z: 0.0 * z]
    a15, g15 = _kan_pair(funcs)
    s = _train_stress()
    geos = S.stress_geos(SPEC, s)
    sa, ra = S.extract_stack(a15, geos, s, cap=3)
    sg, rg = S.extract_stack(g15, geos, s, cap=3)
    fa = [ra["layers"][0]["edges"][0][i]["family"] for i in range(5)]
    fg = [rg["layers"][0]["edges"][0][i]["family"] for i in range(5)]
    assert fa == fg == ["linear", "quadratic", "linear", "linear", "zero"]
    assert ra["layers"][1]["edges"][0][0]["family"] == "linear"
    t = torch.tensor(_train_stress(80, 9), dtype=torch.float32)
    with torch.no_grad():
        va, vg = sa(t)[:, 0], sg(t)[:, 0]
        ka, kg = a15(t), g15(t)
    assert torch.allclose(va, vg, atol=2e-4) and torch.allclose(ka, kg, atol=2e-4)       # the KANs themselves agree, and so do the two extractions


def test_a_noiseless_composed_law_is_recovered_through_the_hidden_layer():
    funcs = [lambda z: 0.9 * z, lambda z: 0.4 * z * z, lambda z: 0.0 * z, lambda z: 0.5 * z, lambda z: -0.3 * z]
    a15, _ = _kan_pair(funcs, outer_slope=0.0)
    l2 = a15.net.layers[1]
    _set_edge(l2, 0, 0, lambda z: 0.5 * z * z + 0.8 * z, -2.0, 2.0)           # genuinely composed: quadratic outer edge of the hidden sum
    s = _train_stress(80, 3)
    stack, rep = S.extract_stack(a15, S.stress_geos(SPEC, s), s, cap=3)
    assert rep["layers"][1]["edges"][0][0]["family"] == "quadratic" and rep["layers"][0]["edges"][0][2]["family"] == "zero"
    t = torch.tensor(_train_stress(100, 5), dtype=torch.float32)
    with torch.no_grad():
        err = (SymbolicMapOf(stack)(t) - a15(t)).abs().max()
    assert float(err) < 5e-3


def SymbolicMapOf(stack):
    return S.SymbolicMap(stack)


# ------------------------------------------------------------------------------------------------ untruncated library reproduces A1
@pytest.fixture(scope="module")
def parent():
    S0 = synth.make_synthetic("G0", n_cyc_cond=14, n_sto_cond=6, reps=2, seed=4)
    tr, te = synth.split_conditions(S0.cells, 0.25, 4)
    b = law.batch_from_cells(SPEC, tr)
    m = pinn.fit_pinn(b, SPEC, {"map": "kan", "h": 2, "grid": 3, "l2": 1e-4, "sparsity": 0.0, "lam_res": 0.1}, "self_limiting", 0, steps=60)
    return tr, te, b, m


def _hull_rows(b, spec):
    cyc = (b.is_cyc > 0.5).numpy()
    return b.s.numpy()[cyc], b.s.numpy()[:, spec.soc_index]


def test_untruncated_extraction_reproduces_a1_to_float_tolerance(parent):
    tr, te, b, m = parent
    s_cyc, s_cal = _hull_rows(b, SPEC)
    sym_cyc, sym_cal, rep = S.extract_law(m.law, SPEC, s_cyc, s_cal, cap=None, untruncated=True)
    t = torch.tensor(np.random.default_rng(2).uniform(-1.0, 1.0, (200, 5)), dtype=torch.float32)
    with torch.no_grad():
        assert torch.allclose(sym_cyc(t), m.law.cyc(t), atol=1e-5, rtol=1e-5)
        x = torch.tensor(np.linspace(-1, 1, 50), dtype=torch.float32)[:, None]
        assert torch.allclose(sym_cal(x), m.law.cal(x), atol=1e-5, rtol=1e-5)
    # the whole model: swapping the laws gives the same predictions as A1 itself
    swapped = A.swap_law(m, sym_cyc, sym_cal)
    base = D.WindowRule.for_spec(SPEC, k_cycling=3, k_storage=2)
    pr = D.prepare_many([c for c in te if c.kind == "cycling"], base)
    p1, _ = pinn.predict_pinn(m, SPEC, [p.win for p in pr], 0.1, 0, steps=30)
    p2, _ = pinn.predict_pinn(swapped, SPEC, [p.win for p in pr], 0.1, 0, steps=30)
    for k in p1:
        assert np.allclose(p1[k], p2[k], atol=2e-5)
    assert rep["untruncated"] and rep["n_coefs"] > 0


def test_truncated_extraction_is_a_closed_form_with_fewer_coefficients(parent):
    tr, te, b, m = parent
    s_cyc, s_cal = _hull_rows(b, SPEC)
    sym_cyc, sym_cal, rep = S.extract_law(m.law, SPEC, s_cyc, s_cal, cap=3)
    full = S.extract_law(m.law, SPEC, s_cyc, s_cal, untruncated=True)[2]["n_coefs"]
    assert rep["n_coefs"] < full and rep["library_sha256"] == S.library_hash() and rep["cap"] == 3
    assert set(rep["input_family_labels"]) == set(SPEC.stress_names)
    assert all(l in S.FAMILIES for ls in rep["input_family_labels"].values() for l in ls)
    assert len(S.describe(rep)) > 0


# ------------------------------------------------------------------------------------------------ arms
CTX = {"backbone": "self_limiting", "steps_scale": 0.05, "symbolic": {"cap": 3}}


def test_a15_and_g15_share_one_code_path_and_differ_only_in_the_parent_map():
    assert type(A.make_arm("A15", SPEC, A.default_hp("A15"), 0, CTX)) is type(A.make_arm("G15", SPEC, A.default_hp("G15"), 0, CTX)) is A.SymbolicArm
    assert A.ARMS["A15"].dims == 6 and A.ARMS["A15"].space["h"] == ("cat", [1, 2]) and A.ARMS["G15"].dims == A.ARMS["A4"].dims == 4
    assert A.ARMS["G15"].space == A.ARMS["A4"].space and A.ARMS["A15"].map_kind == "kan" and A.ARMS["G15"].map_kind == "gam"
    assert {k: v for k, v in A.ARMS["A15"].space.items() if k != "h"} == {k: v for k, v in A.ARMS["A1"].space.items() if k != "h"}


@pytest.mark.parametrize("arm_id", ["A15", "G15"])
def test_symbolic_arm_fits_refits_and_predicts(parent, arm_id):
    tr, te, b, m = parent
    arm = A.make_arm(arm_id, SPEC, A.default_hp(arm_id), 0, CTX).fit(tr)
    assert arm.report["cap"] == 3 and arm.report["library_sha256"] == S.library_hash() and arm.n_coefs == arm.report["n_coefs"]
    assert np.isfinite(arm.train_bic) and arm.n_params >= arm.n_coefs
    assert isinstance(arm.model.law.cyc, S.SymbolicMap) and isinstance(arm.model.law.cal, S.SymbolicStack)
    pr = D.prepare_many([c for c in te if c.kind == "cycling"], D.WindowRule.for_spec(SPEC, k_cycling=3, k_storage=2))
    out = arm.predict([p.win for p in pr])
    assert set(out) == {p.cell.cell_id for p in pr} and all(np.all(np.isfinite(v)) for v in out.values())
    assert arm.model.train_data_mse <= arm.parent_train_data_mse * 3 + 1e-3             # the refit does not wreck the parent's fit


def test_symbolic_arm_without_a_cap_raises(parent, monkeypatch):
    tr, te, b, m = parent
    monkeypatch.setattr(S, "library_file_cap", lambda path=S.LIB_FILE: None)
    with pytest.raises(S.CapNotSetError):
        A.make_arm("A15", SPEC, A.default_hp("A15"), 0, {**CTX, "symbolic": {}}).fit(tr)


def test_a15_recovers_a_noiseless_law_end_to_end():
    """noiseless G0 (additive smooth truth): the hard-ODE KAN fit, its extraction and the refit recover the cyclic log-rate surface"""
    S0 = synth.make_synthetic("G0", n_cyc_cond=16, n_sto_cond=6, reps=1, seed=2, noise=0.0, tau=0.0)
    tr, te = synth.split_conditions(S0.cells, 0.25, 2)
    b = law.batch_from_cells(SPEC, tr)
    hard = fit_hard(b, SPEC, {"map": "kan", "h": 1, "grid": 5, "l2": 1e-5, "sparsity": 0.0}, "self_limiting", 0, steps=1500)
    s_cyc, s_cal = _hull_rows(b, SPEC)
    sym_cyc, sym_cal, rep = S.extract_law(hard.law, SPEC, s_cyc, s_cal, cap=3)
    truth = lambda raw: S0.log_rate_cyc(raw)
    rows = np.unique(s_cyc, axis=0)
    raw = SPEC.denorm(rows)
    t_true = np.asarray(truth(raw)).ravel()
    with torch.no_grad():
        f_sym = sym_cyc(torch.tensor(rows, dtype=torch.float32)).numpy()
        f_kan = hard.law.cyc(torch.tensor(rows, dtype=torch.float32)).numpy()
    c = lambda v: v - v.mean()
    rng_ = np.ptp(t_true)
    assert np.sqrt(np.mean((c(f_kan) - c(t_true)) ** 2)) / rng_ < 0.15            # the KAN itself recovers the law (identifiability of the level aside)
    assert np.sqrt(np.mean((c(f_sym) - c(f_kan)) ** 2)) / np.ptp(f_kan) < 0.08       # and the closed form stays within 8 % of the range of the KAN it was read from
    assert rep["n_coefs"] < S.extract_law(hard.law, SPEC, s_cyc, s_cal, untruncated=True)[2]["n_coefs"]
