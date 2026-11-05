"""build_v2 item 4: D* feature and storage options for A11 / A12, the raw-feature descriptive row, the D* / AG selectors, h = 1 in the KAN grid, A5 at m = 32 only (PREREG_v4 7.1, 7.4).
    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_v2_dstar.py -q"""
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

from pinnkan import arms as A
from pinnkan import baselines as B
from pinnkan import data as D
from pinnkan import negcontrol, run, selectors, synth
from pinnkan.specs import SPECS

SPEC = SPECS["synthetic"]
P3 = B.P3


@pytest.fixture(scope="module")
def g0():
    S = synth.make_synthetic("G0", n_cyc_cond=14, n_sto_cond=6, reps=2, seed=4)
    return synth.split_conditions(S.cells, 0.25, 4)


# ------------------------------------------------------------------------------------------------ the arm table of 7.1
def test_arm_table_v4_dimensions_and_h_grid():
    dims = {a: A.ARMS[a].dims for a in A.ARMS}
    assert dims["A1"] == 6 and dims["A13"] == 6 and dims["A2"] == 4 and dims["A11"] == 5 and dims["A12"] == 7 and dims["A12R"] == 6
    assert dims["A15"] == 6 and dims["G15"] == 4 and dims["A4"] == 4 and dims["A5"] == 5 and dims["A9"] == 4 and dims["A10"] == 0
    for a in ("A1", "A2", "A13"):
        assert A.ARMS[a].space["h"] == ("cat", [1, 2, 3, 4, 6, 8])
    assert A.ARMS["A11"].space["feat"] == ("cat", ["raw", "pinn"]) and A.ARMS["A12"].space["storage"] == ("cat", ["in", "out"])
    assert "feat" not in A.ARMS["A12R"].space and A.ARMS["A12R"].fixed == {"feat": "raw"}
    assert {k: v for k, v in A.ARMS["A12"].space.items() if k != "feat"} == A.ARMS["A12R"].space


def test_h1_kan_fits_and_is_smaller_than_h2(g0):
    tr, te = g0
    ctx = {"backbone": "self_limiting", "steps_scale": 0.04}
    base = D.WindowRule.for_spec(SPEC, k_cycling=3, k_storage=2)
    a1 = A.make_arm("A1", SPEC, {**A.default_hp("A1"), "h": 1}, 0, ctx).fit(tr)
    a2 = A.make_arm("A1", SPEC, {**A.default_hp("A1"), "h": 2}, 0, ctx).fit(tr)
    assert 0 < a1.n_params < a2.n_params
    pr = D.prepare_many([c for c in te if c.kind == "cycling"], base)
    out = a1.predict([p.win for p in pr])
    assert all(np.isfinite(v).all() for v in out.values())


# ------------------------------------------------------------------------------------------------ feature set option
def _prep(g0, k=3):
    tr, te = g0
    rule = D.WindowRule.for_spec(SPEC, k_cycling=k, k_storage=2)
    return rule, D.prepare_many(tr, rule), D.prepare_many([c for c in te if c.kind == "cycling"], rule)


def test_raw_feature_path_is_untouched_bit_for_bit(g0):
    rule, ptr, pte = _prep(g0)
    hp = {"n_est": 60, "lr": 0.1, "leaves": 6, "mcs": 8, "l2": 1.0}
    learner = B.P3Learner("lgb", hp, "synthetic", 0, SPEC).fit(ptr)
    out = learner.predict([p.win for p in pte])
    cells = B.cells_from_prepared(ptr, "synthetic")
    assert all("extra" not in c for c in cells.values())
    p = dict(n_est=60, lr=0.1, leaves=6, mcs=8, sub=0.8, col=0.8, l2=1.0, mono=True, tau_log=False)
    fn = P3.fit_lgb(cells, sorted(cells), p, "synthetic", 0)
    ref = P3.predict_cells(B.cells_from_windows([q.win for q in pte], "synthetic"), sorted(q.cell.cell_id for q in pte), "synthetic", fn, False, "full")
    for k in ref:
        assert np.array_equal(out[k], ref[k])


def test_pinn_features_are_the_a3_abscissae_plus_t_and_efc(g0):
    rule, ptr, pte = _prep(g0)
    q = pte[0]
    sf = B.pinn_stress_features(SPEC, q.cell.raw)[0]
    assert sf.shape == (6,)                                               # T abscissa, SOC_mid, SOC_mid^2, log DoD, log C_ch, log C_dch (order of the stress vector)
    T, soc = q.cell.raw[0], q.cell.raw[1]
    assert sf[0] == pytest.approx((1 / 298.15 - 1 / (273.15 + T)) / (1 / 298.15 - 1 / 308.15), rel=1e-5) and sf[1] == pytest.approx(soc, rel=1e-5) and sf[2] == pytest.approx(soc * soc, rel=1e-4)
    assert sf[3] == pytest.approx(np.log(q.cell.raw[2]), rel=1e-4) and sf[5] == pytest.approx(np.log(q.cell.raw[4]), rel=1e-4)
    cells = B.cells_from_windows([q.win], "synthetic", SPEC, "pinn")
    c = cells[q.cell.cell_id]
    tn = q.win.t_fc / SPEC.t_scale
    en = q.win.efc_curve.value(q.win.t_fc) / SPEC.efc_scale
    assert np.allclose(c["extra"], np.column_stack([tn, en, np.log(tn + 1e-3), np.log(en + 1e-3)]))
    X = P3.feat_rows(c, "synthetic", False, "full")
    assert X.shape == (len(q.win.t_fc), 6 + 5 + 4 + 1) and np.allclose(X[:, -1], (q.win.t_fc - q.win.t_win[-1]) / P3.TAU_UNIT["synthetic"])      # horizon stays the last column
    Xm = P3.feat_rows(c, "synthetic", False, "min")
    assert Xm.shape[1] == 6 + 2 + 4 + 1                                   # the 'min' window-summary set keeps the extras
    raw = B.cells_from_windows([q.win], "synthetic")[q.cell.cell_id]
    assert P3.feat_rows(raw, "synthetic", False, "full").shape[1] == 5 + 5 + 1


@pytest.mark.parametrize("arm_id,kw", [("A11", {"nu": 2.5, "noise_lo": 1e-4, "fs": "min"}), ("A12", {"n_est": 60, "lr": 0.1, "leaves": 6, "mcs": 8, "l2": 1.0})])
@pytest.mark.parametrize("k", [0, 2])
def test_pinn_feature_learners_are_causal_and_work_at_k0_and_k2(g0, arm_id, kw, k):
    tr, te = g0
    base = D.WindowRule.for_spec(SPEC, k_cycling=4, k_storage=2)
    rk = D.WindowRule.for_grid(SPEC, k, base)
    arm = A.make_arm(arm_id, SPEC, {**kw, "feat": "pinn", "storage": "in"}, 0, {"rule": rk, "backbone": "self_limiting"}).fit(tr)
    cyc = [c for c in te if c.kind == "cycling"]
    res = negcontrol.check_invariance(arm.predict, cyc, rk, SPEC)
    assert res["passed"] and res["max_abs_diff"] == 0.0 and res["n_rows"] > 0


def test_storage_rows_option_changes_the_training_cells(g0):
    tr, te = g0
    rule = D.WindowRule.for_spec(SPEC, k_cycling=3, k_storage=2)
    hp = {"n_est": 40, "lr": 0.1, "leaves": 6, "mcs": 8, "l2": 1.0}
    a_in = A.make_arm("A12", SPEC, {**hp, "feat": "raw", "storage": "in"}, 0, {"rule": rule}).fit(tr)
    a_out = A.make_arm("A12", SPEC, {**hp, "feat": "raw", "storage": "out"}, 0, {"rule": rule}).fit(tr)
    n_sto = sum(c.kind == "storage" for c in tr)
    n_cyc = sum(c.kind == "cycling" for c in tr)
    assert a_out.n_train_used == n_cyc and a_in.n_train_used == len(D.prepare_many(tr, rule)) > n_cyc and n_sto > 0
    with pytest.raises(ValueError):
        B.P3Learner("lgb", {"feat": "bogus"}, "synthetic", 0, SPEC)


def test_a12r_is_a12_with_the_raw_features(g0):
    tr, te = g0
    rule = D.WindowRule.for_spec(SPEC, k_cycling=3, k_storage=2)
    hp = {"n_est": 40, "lr": 0.1, "leaves": 6, "mcs": 8, "l2": 1.0, "storage": "in"}
    r = A.make_arm("A12R", SPEC, hp, 0, {"rule": rule})
    assert r.hp["feat"] == "raw"
    pw = [p.win for p in D.prepare_many([c for c in te if c.kind == "cycling"], rule)]
    o1 = r.fit(tr).predict(pw)
    o2 = A.make_arm("A12", SPEC, {**hp, "feat": "raw"}, 0, {"rule": rule}).fit(tr).predict(pw)
    assert all(np.array_equal(o1[k], o2[k]) for k in o1)


# ------------------------------------------------------------------------------------------------ selectors
def test_dstar_is_the_inner_cv_best_of_a9_a11_a12_with_a_fixed_tie_order():
    s = {"A9": 1.2, "A11": 0.9, "A12": 1.0, "A12R": 0.1, "A1": 0.01}
    assert selectors.select_comparators(s, 8)["D*"]["arm"] == "A11"                      # A12R (descriptive) and A1 are never candidates
    assert selectors.select_comparators({"A9": 1.0, "A11": 1.0, "A12": 1.0}, 8)["D*"]["arm"] == "A9"        # ties: candidate order
    assert selectors.select_comparators({"A9": float("nan"), "A12": 2.0}, 8)["D*"]["arm"] == "A12"
    d = selectors.select_comparators({"A9": 1.0}, 8)["D*"]
    assert d["arm"] == "A9" and d["complete"] is False
    assert "D*" not in selectors.select_comparators({"A1": 1.0}, 8)


def test_ag_is_a4_below_m32_and_the_better_of_a4_a5_at_m32():
    s = {"A4": 1.1, "A5": 0.9}
    assert selectors.select_comparators(s, 8)["AG"]["arm"] == "A4" and selectors.select_comparators(s, 16)["AG"]["arm"] == "A4"
    assert selectors.select_comparators(s, 32)["AG"]["arm"] == "A5" and selectors.select_comparators(s, None)["AG"]["arm"] == "A5"
    assert selectors.select_comparators({"A4": 0.8, "A5": 0.9}, 32)["AG"]["arm"] == "A4"


def test_selectors_take_nothing_but_inner_scores():
    import inspect
    assert list(inspect.signature(selectors.select_comparators).parameters) == ["inner_scores", "m"]
    src = open(selectors.__file__, encoding="utf8").read()
    assert "condition_scores" not in src.replace("lowest inner-CV condition-mean", "") and "outer" not in src.replace("outer fold", "").replace("outer test error", "")


CFG = {"dataset": "synthetic", "n_trials": 1, "inner_k": 2, "steps_scale": 0.05, "seeds": [0], "mode": "inner", "diagnostics": False,
       "synthetic": {"kind": "G0", "n_cyc_cond": 16, "n_sto_cond": 6, "reps": 2, "seed": 3}}


def test_run_writes_comparators_from_inner_scores_and_refuses_a5_below_m32(tmp_path):
    d = run.run({**CFG, "run_id": "cmp", "arms": ["A9", "A11", "A12", "A4"], "window": {"k_cycling": 3}}, runs_dir=str(tmp_path))
    c = json.load(open(os.path.join(d, "comparators.json")))
    inner = json.load(open(os.path.join(d, "metrics.json")))["inner_cv_pp"]
    best = min(("A9", "A11", "A12"), key=lambda a: inner[a])
    assert c["D*"]["arm"] == best and c["AG"]["arm"] == "A4" and c["D*"]["table"]["A9"] == pytest.approx(inner["A9"])
    with pytest.raises(run.ConfigError):
        run.run({**CFG, "run_id": "a5", "arms": ["A5"], "m": 16}, runs_dir=str(tmp_path))
