"""D023 (judge actions 1-5): one inversion routine for every inverting arm; tests T1-T7 and the diagnostics.
    .venv/Scripts/python.exe -P -m pytest code/tests/test_inversion.py -q"""
import inspect
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.join(ROOT, "code", "pilots"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest
import torch

torch.set_num_threads(1)

from pinnkan import arms as A
from pinnkan import data as D
from pinnkan import hard, inversion, inversion_diag, law, pinn, run, synth
from pinnkan.law import SIGMA, batch_forecast_query, batch_from_cells, batch_from_windows
from pinnkan.specs import SPECS

SPEC = SPECS["synthetic"]
DT = torch.float64


# ------------------------------------------------------------------------------------------------ T1 known problems
def _quad(C=6, p=3, cond_max=1e4, seed=0):
    g = torch.Generator().manual_seed(seed)
    Q = torch.linalg.qr(torch.randn(C, p, p, generator=g, dtype=DT))[0]
    ev = torch.stack([torch.logspace(0, np.log10(cond_max), p, dtype=DT) * (0.5 + torch.rand(1, generator=g, dtype=DT)) for _ in range(C)])
    Hm = Q @ torch.diag_embed(ev) @ Q.transpose(1, 2)
    mstar = torch.randn(C, p, generator=g, dtype=DT)
    return (lambda P: 0.5 * torch.einsum("ci,cij,cj->c", P - mstar, Hm, P - mstar)), mstar


def test_T1_a_quadratic_is_solved_exactly_in_a_handful_of_iterations_up_to_condition_number_1e4():
    fun, mstar = _quad()
    res = inversion.invert_latents(fun, torch.zeros(6, 3, dtype=DT))
    assert bool(res.converged.all()) and res.n_iter <= 10
    assert torch.allclose(res.P, mstar, atol=1e-5) and float((res.P - mstar).abs().max()) < 1e-5
    assert res.P.dtype == torch.float64 and bool((res.gnorm <= 1e-6 * (1 + res.f.abs())).all())


def test_T1_a_double_well_from_an_indefinite_hessian_start_never_raises_the_objective_and_ends_positive_definite():
    def fun(P):
        x, y = P[:, 0], P[:, 1]
        return (x ** 2 - 1.0) ** 2 + 0.5 * y ** 2 + 0.1 * x * y
    P0 = torch.tensor([[0.0, 0.5], [0.05, -1.0], [-0.02, 2.0]], dtype=DT)               # Hessian at x ~ 0 is indefinite (-4)
    f0 = fun(P0)
    prev = f0.clone()
    for cap in range(1, 8):
        r = inversion.invert_latents(fun, P0, cap=cap)
        assert bool((r.f <= prev + 1e-15).all())                                             # non-increasing in the number of iterations: accepted steps never raise a cell's objective
        prev = r.f
    r = inversion.invert_latents(fun, P0)
    assert bool(r.converged.all())
    Pv = r.P.clone().requires_grad_(True)
    g = torch.autograd.grad(fun(Pv).sum(), Pv, create_graph=True)[0]
    H = torch.stack([torch.autograd.grad(g[:, j].sum(), Pv, retain_graph=True)[0] for j in range(2)], dim=2)
    assert bool((torch.linalg.eigvalsh(0.5 * (H + H.transpose(1, 2))) > 0).all())          # a minimum, not a saddle


def test_T1_an_under_capped_hard_cell_is_flagged_and_returns_the_last_accepted_iterate():
    def fun(P):                                                                            # Rosenbrock: slow valley
        x, y = P[:, 0], P[:, 1]
        return (1 - x) ** 2 + 100.0 * (y - x ** 2) ** 2
    P0 = torch.tensor([[-1.2, 1.0], [0.9, 0.8]], dtype=DT)
    capped = inversion.invert_latents(fun, P0, cap=3)
    assert not bool(capped.converged[0]) and capped.n_iter == 3
    assert float(capped.f[0]) < float(fun(P0)[0]) and not torch.equal(capped.P[0], P0[0])           # the best accepted iterate, not the start
    full = inversion.invert_latents(fun, P0)
    assert bool(full.converged.all()) and torch.allclose(full.P, torch.ones(2, 2, dtype=DT), atol=1e-4)
    rec = inversion.log_result("hard", capped)
    assert rec["n_nonconverged"] >= 1 and rec["convergence_share"] < 1.0                   # counted, kept in the output (shape unchanged), not dropped
    assert capped.P.shape == P0.shape


# ------------------------------------------------------------------------------------------------ a small trained zoo
@pytest.fixture(scope="module")
def zoo():
    S0 = synth.make_synthetic("G0", n_cyc_cond=12, n_sto_cond=5, reps=2, seed=3)
    tr, te = synth.split_conditions(S0.cells, 0.25, 3)
    base = D.WindowRule.for_spec(SPEC, k_cycling=3, k_storage=2)
    ctx = {"backbone": "self_limiting", "steps_scale": 0.1, "rule": base}
    arms = {a: A.make_arm(a, SPEC, A.default_hp(a), 0, ctx).fit(tr) for a in ("A1", "A9", "A2", "A4")}
    prep = D.prepare_many([c for c in te if c.kind == "cycling"], base)
    return {"arms": arms, "wcells": [p.win for p in prep], "tr": tr, "te": te, "base": base}


def _prob(zoo, a, wcells=None, z_weight=None):
    return inversion_diag.problem_for(zoo["arms"][a], zoo["wcells"] if wcells is None else wcells, z_weight)


# ------------------------------------------------------------------------------------------------ T2 determinism, separability
@pytest.mark.parametrize("a", ["A1", "A9", "A2"])
def test_T2_two_calls_are_bitwise_identical_and_a_cell_does_not_depend_on_the_others(zoo, a):
    (p1, kind), (p2, _) = _prob(zoo, a), _prob(zoo, a)
    r1, r2 = inversion.solve(p1, kind, log=False), inversion.solve(p2, kind, log=False)
    assert torch.equal(r1.P, r2.P) and torch.equal(r1.f, r2.f)
    w = zoo["wcells"]
    ids = list(p1["ids"])
    rev = _prob(zoo, a, list(reversed(w)))[0]
    rr = inversion.solve(rev, kind, log=False)
    idx = {c: i for i, c in enumerate(rev["ids"])}
    for i, c in enumerate(ids):
        assert torch.allclose(r1.P[i], rr.P[idx[c]], atol=1e-9), (a, c)                      # separability: position in the batch is irrelevant
    sub = _prob(zoo, a, w[:2])[0]
    rs = inversion.solve(sub, kind, log=False)
    for j, c in enumerate(sub["ids"]):
        assert torch.allclose(rs.P[j], r1.P[ids.index(c)], atol=1e-9)                        # nor are the other cells


def test_T2_the_collocation_draw_of_a_cell_is_fixed_by_the_seed_and_the_cell_id(zoo):
    p_full, _ = _prob(zoo, "A1")
    p_rev, _ = _prob(zoo, "A1", list(reversed(zoo["wcells"])))
    ids = p_full["ids"]
    P = torch.cat([torch.zeros(len(ids), 2, dtype=DT), torch.full((len(ids), 1), 0.05, dtype=DT)], dim=1)
    f_full = p_full["fun"](P).detach()
    f_rev = p_rev["fun"](P[:len(ids)]).detach()
    order = [p_rev["ids"].index(c) for c in ids]
    assert torch.allclose(f_full, f_rev[order], rtol=1e-12, atol=1e-12)                      # same cell, same latents, same objective whatever the batch order


# ------------------------------------------------------------------------------------------------ T3 parity
def test_T3_every_inverting_arm_calls_the_one_routine_with_one_config(zoo, monkeypatch):
    for fn in (pinn.invert_pinn, pinn.predict_data_only, hard.fit_delta):
        src = inspect.getsource(fn)
        assert "inversion.solve" in src and "Adam" not in src and "steps" not in inspect.signature(fn).parameters and "lr" not in inspect.signature(fn).parameters
    for fn in (pinn.predict_pinn, hard.predict_hard):
        assert not {"steps", "lr"} & set(inspect.signature(fn).parameters)
    with pytest.raises(TypeError):
        pinn.predict_pinn(zoo["arms"]["A1"].model, SPEC, zoo["wcells"][:1], 1.0, 0, steps=10)
    with pytest.raises(TypeError):
        hard.fit_delta(zoo["arms"]["A2"].model, batch_from_windows(SPEC, zoo["wcells"][:1]), steps=5)
    seen = []
    orig = inversion.invert_latents
    monkeypatch.setattr(inversion, "invert_latents", lambda fun, P0, config=inversion.CONFIG, cap=None: (seen.append((config, cap)), orig(fun, P0, config, cap))[1])
    for a, arm in zoo["arms"].items():                                                      # A1, A9, A2, A4 (and thereby A5, A13, A15, G15: same model classes)
        arm.predict(zoo["wcells"][:3])
    assert len(seen) == 4 and all(c is inversion.CONFIG and cap is None for c, cap in seen)
    cfg = inversion.config_dict()
    assert cfg["tol"] == 1e-6 and cfg["cap"] == 100 and cfg["dtype"] == "float64" and cfg["z_prior_weight"] == 1.0 and inversion.Z_PRIOR_WEIGHT == 1.0
    assert len(inversion.config_sha256()) == 64


def test_T3_a1_with_zero_residual_weight_and_a9_give_the_same_iterates_through_the_routine(zoo):
    a9 = A.make_arm("A9", SPEC, {"width": 32, "depth": 3, "wd": 1e-4, "zdim": 2}, 0, {"rule": zoo["base"], "backbone": "self_limiting", "steps_scale": 0.05}).fit(zoo["tr"])
    a4 = zoo["arms"]["A4"]
    m1 = a4.model
    m1.net.load_state_dict(a9.model.net.state_dict())                                       # the same solution network in the A1-type model
    w = zoo["wcells"]
    bw9 = batch_from_windows(SPEC, w)
    p9 = inversion.data_problem(a9.model, bw9, None)
    p1 = inversion.pinn_problem(m1, bw9, None, 0.0, 0)                                      # lam_res = 0: no residual; delta then only meets its prior
    r9, r1 = inversion.solve(p9, "data", log=False), inversion.solve(p1, "pinn", log=False)
    assert torch.allclose(r9.P, r1.P[:, :2], atol=1e-9) and float(r1.P[:, 2].abs().max()) < 1e-12
    assert torch.equal(p9["P0"], torch.zeros_like(p9["P0"])) and torch.equal(p1["P0"], torch.zeros_like(p1["P0"]))      # same start rule: the prior mode


# ------------------------------------------------------------------------------------------------ T4, T5
def test_T4_k0_cells_keep_the_prior_mode_at_every_site(zoo):
    base = zoo["base"]
    r0 = D.WindowRule.for_grid(SPEC, 0, base)
    w0 = [p.win for p in D.prepare_many([c for c in zoo["te"] if c.kind == "cycling"], r0)]
    z, delta = pinn.invert_pinn(zoo["arms"]["A4"].model, batch_from_windows(SPEC, w0), 1.0, 0)
    assert bool((z == 0).all() and (delta == 0).all())
    prob = inversion_diag.problem_for(zoo["arms"]["A9"], w0)[0]
    assert prob["ref_only"].all() and bool((inversion.solve(prob, "data", log=False).P == 0).all())
    d = hard.fit_delta(zoo["arms"]["A2"].model, batch_from_windows(SPEC, w0))
    assert bool((d == 0).all())
    rec = [r for r in inversion.LOG if r["n_inverted"] == 0]
    assert rec == [] or all(r["convergence_share"] == 1.0 for r in rec)                  # nothing to invert, nothing non-converged


def test_T5_doubling_the_cap_leaves_a_converged_cell_unchanged(zoo):
    for a in ("A1", "A9", "A2"):
        prob, kind = _prob(zoo, a)
        r1 = inversion.solve(prob, kind, log=False)
        r2 = inversion.solve(prob, kind, cap=200, log=False)
        c = r1.converged
        assert bool(c.any()) and torch.equal(r1.P[c], r2.P[c])
        fc = prob["predict"](r1.P)
        fd = prob["predict"](r2.P)
        for i, cid in enumerate(prob["ids"]):
            if bool(c[i]):
                assert np.array_equal(fc[cid], fd[cid])


# ------------------------------------------------------------------------------------------------ T6 the test-time objective is the training posterior
def test_T6_with_z_weight_one_the_test_time_objective_equals_n_times_the_per_cell_training_loss(zoo):
    tr = zoo["tr"]
    cell = next(c for c in tr if c.kind == "cycling")
    b = batch_from_cells(SPEC, [cell])
    n = b.obs_t.numel()
    m = zoo["arms"]["A4"].model                                                              # A1-type PINN model
    col = pinn.make_collocation(SPEC, b, 0, placement="record_end")
    gen = torch.Generator().manual_seed(0)
    z0, d0 = torch.tensor([[0.3, -0.2]]), torch.tensor([0.07])
    with torch.no_grad():
        m.z.zero_()
        m.delta.zero_()
        m.z[0], m.delta[0] = z0[0], d0[0]                                                  # the model holds one row per training cell; only row 0 belongs to this batch
    tot, data, res = m.loss(b, col, 0.0, 0.0, 0.0, gen)
    prob = inversion.pinn_problem(m, b, None, 0.0, 0)
    P = torch.cat([z0, d0[:, None]], dim=1).double()
    assert float(prob["fun"](P)[0]) == pytest.approx(float(tot) * n, rel=1e-4)
    a9 = zoo["arms"]["A9"].model
    with torch.no_grad():
        a9.z.zero_()
        a9.z[0] = torch.tensor([0.4, 0.1])
    r = a9.F(b.obs_t, b.s[b.obs_cell], a9.z[b.obs_cell]) - b.obs_y
    train = (r ** 2).mean() / SIGMA ** 2 + (a9.z ** 2).sum() / n                          # fit_data_only without weight decay
    p9 = inversion.data_problem(a9, b, None)
    assert float(p9["fun"](torch.tensor([[0.4, 0.1]], dtype=DT))[0]) == pytest.approx(float(train) * n, rel=1e-4)
    p16 = inversion.data_problem(a9, b, None, z_weight=16.0)
    base = float(p9["fun"](torch.tensor([[0.4, 0.1]], dtype=DT))[0])
    assert float(p16["fun"](torch.tensor([[0.4, 0.1]], dtype=DT))[0]) == pytest.approx(base + 15.0 * 0.17, rel=1e-6)      # the sensitivity row changes only the z term


# ------------------------------------------------------------------------------------------------ T7 regression against the check's reference routine
@pytest.mark.parametrize("a", ["A1", "A9", "A2"])
def test_T7_the_routine_reproduces_the_checks_O2_forecasts(zoo, a):
    import d023_inversion_check as K
    arm, w = zoo["arms"][a], zoo["wcells"]
    hp = dict(arm.hp)
    pr = K.problem(a, arm.model, SPEC, w, hp, "f64", seed=arm.seed)
    P_ref, _ = K.newton(pr, torch.zeros(pr["C"], pr["p"], dtype=DT), 100)
    ref = pr["predict"](P_ref)
    prob, kind = _prob(zoo, a)
    mine = prob["predict"](inversion.solve(prob, kind, log=False).P)
    keep = ~prob["ref_only"]
    worst = max(100.0 * float(np.max(np.abs(np.asarray(ref[c]) - np.asarray(mine[c])))) for c, k in zip(prob["ids"], keep) if k)
    assert worst <= 1.9e-5                                                                  # the check's reported replica tolerance (pp); the algorithm is the same, so far below it


# ------------------------------------------------------------------------------------------------ diagnostics
def test_diagnostics_are_seeded_window_only_and_deterministic(zoo):
    import zlib
    r = inversion_diag.diag_rng(2, "A1", 8, "2", 3)
    ref = np.random.default_rng(np.random.SeedSequence([20261105, zlib.crc32(b"inv|2|A1|8|2|3")]))
    assert r.integers(0, 1 << 30) == ref.integers(0, 1 << 30)
    d1 = inversion_diag.diagnose(zoo["arms"]["A9"], zoo["wcells"], "A9", 0, 8, "2", full=True, rows=True)
    d2 = inversion_diag.diagnose(zoo["arms"]["A9"], zoo["wcells"], "A9", 0, 8, "2", full=True, rows=True)
    assert json.dumps({k: v for k, v in d1.items() if k != "forecasts"}, sort_keys=True) == json.dumps({k: v for k, v in d2.items() if k != "forecasts"}, sort_keys=True)
    assert {"convergence_share", "cap_doubling_change_pp", "start_spread_pp", "basin", "n_inverted"} <= set(d1) and d1["cap_doubling_change_pp"]["max"] >= 0.0
    assert set(d1["basin"]) == {"share_lower_objective", "share_forecast_differs_gt_1pp", "threshold_pp"} and d1["start_spread_pp"]["p95"] >= d1["start_spread_pp"]["p50"] >= 0.0
    assert set(d1["forecasts"]["v"]) == {1, 2, 3} and set(d1["forecasts"]["vi"]) == {4, 16}
    assert not hasattr(zoo["wcells"][0], "fc_true") and "labels" not in inspect.signature(inversion_diag.diagnose).parameters           # window cells carry no forecast truth
    d3 = inversion_diag.diagnose(zoo["arms"]["A2"], zoo["wcells"], "A2", 0, 8, "2")
    assert "start_spread_pp" not in d3 and d3["convergence_share"] >= 0.0                    # other arms: convergence and cap doubling only


def test_a_larger_z_prior_weight_shrinks_the_latent(zoo):
    p1, kind = _prob(zoo, "A9")
    p16, _ = _prob(zoo, "A9", z_weight=16.0)
    z1 = inversion.solve(p1, kind, log=False).P.norm(dim=1)
    z16 = inversion.solve(p16, kind, log=False).P.norm(dim=1)
    assert float(z16.mean()) < float(z1.mean())


# ------------------------------------------------------------------------------------------------ run writer
CFG = {"dataset": "synthetic", "arms": ["A9", "A2", "R2"], "n_trials": 1, "inner_k": 2, "steps_scale": 0.05, "seeds": [0, 1], "mode": "confirmatory",
       "synthetic": {"kind": "G0", "n_cyc_cond": 16, "n_sto_cond": 6, "reps": 2, "seed": 3}}


def test_the_run_pins_the_inversion_constants_logs_convergence_and_writes_the_diagnostics_and_rows(tmp_path):
    with pytest.raises(run.ConfigError, match="inversion_config_sha256"):
        run.run({**CFG, "run_id": "bad", "inversion_config_sha256": "0" * 64}, runs_dir=str(tmp_path))
    with pytest.raises(run.ConfigError, match="inversion_config_sha256"):
        run.run({"run_id": "c", "dataset": "isu", "test": "B", "fold": 0, "mode": "confirmatory", "arms": ["A1"]}, runs_dir=str(tmp_path))
    d = run.run({**CFG, "run_id": "ok", "inversion_config_sha256": inversion.config_sha256(), "inversion_diagnostics": True, "k": "grid", "window": {"k_cycling": 4}}, runs_dir=str(tmp_path))
    dg = json.load(open(os.path.join(d, "diagnostics.json")))["inversion"]
    assert dg["config_sha256"] == inversion.config_sha256() and dg["z_prior_weight"] == 1.0 and dg["inner_cv"]["n_inverted"] > 0 and dg["n_calls"] > 0
    assert any(k.startswith("A9|") for k in dg["primary"]) and all(v["convergence_share"] <= 1.0 for v in dg["primary"].values())
    cells = {(r["arm"], r["k"]) for r in dg["per_arm_cell"]}
    assert ("A9", "2") in cells and ("A9", "full") in cells and ("A2", "full") in cells and not any(k == "0" for _, k in cells)        # k = 0 is the prior mode by rule: nothing to report
    a9 = next(r for r in dg["per_arm_cell"] if r["arm"] == "A9" and r["k"] == "full")
    assert "start_spread_pp" in a9 and "start_spread_pp" not in next(r for r in dg["per_arm_cell"] if r["arm"] == "A2")
    assert json.load(open(os.path.join(d, "config.json")))["inversion_config_sha256"] == inversion.config_sha256()
    rows = [f for f in os.listdir(d) if f.startswith("condition_scores_sens_")]
    assert any("vi4" in f for f in rows) and any("vi16" in f for f in rows) and any("v1_" in f for f in rows)
    sens = json.load(open(os.path.join(d, [f for f in rows if "vi4" in f][0])))
    assert "A9" in sens and "A2" not in sens                                                  # rows (v) and (vi) cover A1, A9 and AG only
    sc = json.load(open(os.path.join(d, "condition_scores.json")))
    assert set(sc) == {"A9", "A2", "R2"}                                                      # the primary scores are untouched by the diagnostics
