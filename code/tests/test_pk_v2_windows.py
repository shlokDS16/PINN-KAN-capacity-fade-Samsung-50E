"""build_v2 item 2: the k = 0 and k = 2 early check-up paths, k_full, the grid scoring in the run writer (PREREG_v4 4.1, 5).
    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_v2_windows.py -q"""
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

from pinnkan import data as D
from pinnkan import negcontrol, run, synth
from pinnkan.arms import ARMS, default_hp, make_arm
from pinnkan.specs import SPECS

SPEC = SPECS["synthetic"]


@pytest.fixture(scope="module")
def g0():
    S = synth.make_synthetic("G0", n_cyc_cond=14, n_sto_cond=6, reps=2, seed=4)
    return synth.split_conditions(S.cells, 0.25, 4)


# ------------------------------------------------------------------------------------------------ the k axis
def test_grid_ks_and_the_k_full_rules():
    assert D.grid_ks(4) == (0, 2, "full") and D.grid_ks(5) == (0, 2, "full")
    assert D.grid_ks(2) == (0, "full")                      # cells (m, 2) and (m, k_full) are one cell
    for bad in (1, 0):
        with pytest.raises(D.DesignReopenError):
            D.grid_ks(bad)
    assert D.window_rule_from_counts([8, 15, 9, 11], [7, 7]) == (round(10.0 / 3), round(7 / 3))      # k_full = round(n_med / 3), Python rounding (halves to even)
    assert D.window_rule_from_counts([10.5], None)[0] == 4 and D.window_rule_from_counts([7.5], None)[0] == 2


def test_window_rules_of_the_grid_cells():
    base = D.WindowRule.for_spec(SPEC, k_cycling=5, k_storage=3)
    r0, r2, rf = (D.WindowRule.for_grid(SPEC, k, base) for k in (0, 2, "full"))
    assert (r0.k_cycling, r0.k_storage, r0.min_window_points, r0.design_spec is SPEC) == (0, 0, 1, True)
    assert (r2.k_cycling, r2.k_storage, r2.min_window_points) == (2, 2, 3) and r2.design_spec is None
    assert (rf.k_cycling, rf.k_storage) == (5, 3) and rf == base
    assert D.WindowRule.for_grid(SPEC, 2, D.WindowRule.for_spec(SPEC, k_cycling=5, k_storage=1)).k_storage == 1       # storage window = min(k, k_sto)
    with pytest.raises(D.DesignReopenError):
        D.WindowRule.for_grid(SPEC, 7, base)
    isu = D.WindowRule.for_spec(SPECS["isu"])
    w0, w2 = D.WindowRule.for_grid(SPECS["isu"], 0, isu), D.WindowRule.for_grid(SPECS["isu"], 2, isu)
    assert (w0.W, w0.min_window_points, w2.W) == (0.0, 1, 2.0) and D.WindowRule.for_grid(SPECS["isu"], "full", isu).W == 4.0


def test_prepare_at_k0_holds_the_reference_only_and_uses_the_design_throughput(g0):
    tr, te = g0
    base = D.WindowRule.for_spec(SPEC, k_cycling=4, k_storage=2)
    r0 = D.WindowRule.for_grid(SPEC, 0, base)
    cyc = next(c for c in te if c.kind == "cycling")
    p0 = D.prepare(cyc, r0)
    assert len(p0.win.t_win) == 1 and p0.win.t_win[0] == 0.0 and p0.win.y_win[0] == pytest.approx(1.0) and p0.w_idx == 0
    assert len(p0.win.t_fc) == int(cyc.fc_ok[1:].sum())                                    # every later CU / exCU check-up is forecast
    rate = float(SPEC.efc_rate(cyc.raw))
    assert p0.win.efc_curve.rate(np.array([10.0, 100.0]))[0] == pytest.approx(rate) and p0.win.efc_curve.value(100.0) == pytest.approx(rate * 100.0)
    sto = next(c for c in tr if c.kind == "storage")
    ps = D.prepare(sto, r0)
    assert len(ps.win.t_win) == 1 and ps.win.efc_curve.value(50.0) == pytest.approx(0.0)
    p2 = D.prepare(cyc, D.WindowRule.for_grid(SPEC, 2, base))
    assert len(p2.win.t_win) == 3 and len(p2.win.t_fc) == len(p0.win.t_fc) - 2
    assert p2.win.efc_curve.tail == pytest.approx((cyc.efc[2] - cyc.efc[0]) / (cyc.t[2] - cyc.t[0]))       # k = 2: the window's own mean rate, not the design rate
    assert D.prepare(cyc, D.WindowRule.for_grid(SPEC, "full", base)).w_idx == 4


# ------------------------------------------------------------------------------------------------ k = 0: nothing but the reference and the stress enters
CTX = {"backbone": "self_limiting", "steps_scale": 0.05}


@pytest.mark.parametrize("arm_id", ["A2", "A9", "A10", "A4", "A11", "A12"])
def test_k0_predictions_do_not_depend_on_any_post_reference_label(g0, arm_id):
    tr, te = g0
    base = D.WindowRule.for_spec(SPEC, k_cycling=4, k_storage=2)
    r0 = D.WindowRule.for_grid(SPEC, 0, base)
    hp = default_hp(arm_id) if ARMS[arm_id].tuned else {}
    arm = make_arm(arm_id, SPEC, hp, 0, dict(CTX, rule=r0)).fit(tr)
    cyc_te = [c for c in te if c.kind == "cycling"]
    res = negcontrol.check_invariance(arm.predict, cyc_te, r0, SPEC)
    assert res["passed"] and res["n_rows"] > 0 and res["max_abs_diff"] == 0.0
    # at k = 2 the window labels are used: scrambling beyond k = 2 is invisible, scrambling beyond k = 0 is not (a different window)
    p0 = D.prepare_many(cyc_te, r0)
    out0 = arm.predict([p.win for p in p0])
    assert all(np.all(np.isfinite(v)) for v in out0.values())


def test_k0_latents_and_offsets_are_the_prior_means(g0):
    tr, te = g0
    from pinnkan.pinn import predict_pinn
    base = D.WindowRule.for_spec(SPEC, k_cycling=4, k_storage=2)
    arm = make_arm("A4", SPEC, default_hp("A4"), 0, dict(CTX, rule=base)).fit(tr)
    for k, zero in ((0, True), (2, False)):
        pr = D.prepare_many([c for c in te if c.kind == "cycling"], D.WindowRule.for_grid(SPEC, k, base))
        _, (z, delta) = predict_pinn(arm.model, SPEC, [p.win for p in pr], 1.0, 0, steps=20)
        assert bool((z == 0).all() and (delta == 0).all()) == zero


def test_k0_semi_empirical_uses_the_population_parameters(g0):
    tr, te = g0
    base = D.WindowRule.for_spec(SPEC, k_cycling=4, k_storage=2)
    arm = make_arm("A10", SPEC, {}, 0, dict(CTX, rule=base)).fit(tr)
    from pinnkan import semi
    pr0 = D.prepare_many([c for c in te if c.kind == "cycling"], D.WindowRule.for_grid(SPEC, 0, base))
    a = semi.predict_semi(arm.form, arm.theta, [p.win for p in pr0], per_cell_factor=True)
    b = semi.predict_semi(arm.form, arm.theta, [p.win for p in pr0], per_cell_factor=False)
    for k in a:
        assert np.array_equal(a[k], b[k])                      # factor exactly 1 with or without the per-cell factor


def test_the_window_gains_information_between_k0_and_k2(g0):
    tr, te = g0
    base = D.WindowRule.for_spec(SPEC, k_cycling=4, k_storage=2)
    arm = make_arm("A2", SPEC, default_hp("A2"), 0, dict(CTX, rule=base)).fit(tr)
    cyc_te = [c for c in te if c.kind == "cycling"]
    pr = {k: D.prepare_many(cyc_te, D.WindowRule.for_grid(SPEC, k, base)) for k in (0, 2)}
    o0 = arm.predict([p.win for p in pr[0]])
    o2 = arm.predict([p.win for p in pr[2]])
    cid = pr[2][0].cell.cell_id
    assert not np.allclose(o0[cid][-len(o2[cid]):], o2[cid])


# ------------------------------------------------------------------------------------------------ run writer
CFG = {"dataset": "synthetic", "arms": ["A2", "A9", "A10", "A11", "R1", "R2"], "n_trials": 1, "inner_k": 2, "steps_scale": 0.05, "seeds": [0], "mode": "confirmatory",
       "diagnostics": False, "synthetic": {"kind": "G0", "n_cyc_cond": 16, "n_sto_cond": 6, "reps": 2, "seed": 3}}


def test_k_full_reproduces_the_single_window_run_bit_for_bit(tmp_path):
    cfg = {**CFG, "arms": ["A2", "A9", "R1", "R2"]}
    d1 = run.run({**cfg, "run_id": "legacy"}, runs_dir=str(tmp_path))
    d2 = run.run({**cfg, "run_id": "kfull", "k": ["full"]}, runs_dir=str(tmp_path))
    assert json.load(open(os.path.join(d1, "condition_scores.json"))) == json.load(open(os.path.join(d2, "condition_scores.json")))
    assert json.load(open(os.path.join(d1, "cell_scores.json"))) == json.load(open(os.path.join(d2, "cell_scores.json")))


def test_grid_run_scores_every_k_cell_and_checks_invariance_at_each(tmp_path):
    d = run.run({**CFG, "run_id": "grid", "k": "grid", "window": {"k_cycling": 4}}, runs_dir=str(tmp_path))
    f = lambda n: os.path.join(d, n)
    cs = {k: json.load(open(f(n))) for k, n in (("0", "condition_scores_k0.json"), ("2", "condition_scores_k2.json"), ("full", "condition_scores.json"))}
    assert set(cs["0"]) == {"A2", "A9", "A10", "A11"}                       # R1 and R2 need a window check-up: not scored at k = 0
    assert set(cs["2"]) == set(cs["full"]) == set(CFG["arms"])
    for k in cs:
        assert all(len(v) == len(cs["full"]["A2"]) for v in cs[k].values())          # same held-out conditions at every cell (paired by condition)
    m = json.load(open(f("metrics.json")))
    assert m["k_labels"] == ["0", "2", "full"] and m["k_primary"] == "full" and set(m["outer_test_by_k"]) == {"0", "2", "full"}
    inv = json.load(open(f("invariance.json")))
    assert inv["passed"] and inv["max_abs_diff"] == 0.0 and any(key.endswith("|k0") for key in inv["per_arm_seed"]) and any(key.endswith("|kfull") for key in inv["per_arm_seed"])
    ph = open(f("predictions.csv")).read()
    assert "outer_test_k0" in ph and "outer_test_k2" in ph and "outer_test_kfull" in ph
    assert os.path.isfile(f("condition_meta_k0.json")) and os.path.isfile(f("cell_scores_k2.json"))


def test_k_full_equal_two_merges_cells_and_k_full_below_two_reopens_the_design(tmp_path):
    d = run.run({**CFG, "arms": ["A2", "R2"], "run_id": "kf2", "k": "grid", "window": {"k_cycling": 2}}, runs_dir=str(tmp_path))
    assert json.load(open(os.path.join(d, "metrics.json")))["k_labels"] == ["0", "full"]
    with pytest.raises(D.DesignReopenError):
        run.run({**CFG, "arms": ["R2"], "run_id": "kf1", "k": "grid", "window": {"k_cycling": 1}}, runs_dir=str(tmp_path))


def test_tuning_window_follows_m(tmp_path):
    cfg = {**CFG, "mode": "inner", "arms": ["R2"], "window": {"k_cycling": 5}}
    d8 = run.run({**cfg, "run_id": "w8", "m": 8}, runs_dir=str(tmp_path))
    d32 = run.run({**cfg, "run_id": "w32", "m": 32}, runs_dir=str(tmp_path))
    d0 = run.run({**cfg, "run_id": "w0"}, runs_dir=str(tmp_path))
    tw = lambda d: json.load(open(os.path.join(d, "metrics.json")))["tuning_window"]
    assert tw(d8)["k_cycling"] == 2 and tw(d32)["k_cycling"] == 5 and tw(d0)["k_cycling"] == 5


def test_bad_k_is_rejected(tmp_path):
    for bad in (["x"], [-1], [0, 0]):
        with pytest.raises(run.ConfigError):
            run.run({**CFG, "arms": ["R2"], "run_id": "badk", "k": bad}, runs_dir=str(tmp_path / str(len(str(bad)))))


def test_nc1_full_pipeline_passes_on_the_grid_paths(tmp_path):
    cfg = {**CFG, "arms": ["A2", "A9"], "run_id": "nc1", "mode": "nc1_full", "k": "grid", "m": 8, "window": {"k_cycling": 3}}
    d = run.run(cfg, runs_dir=str(tmp_path))
    r = json.load(open(os.path.join(d, "nc1_full.json")))
    assert r["passed"] and r["n_outer_rows"] > 0
