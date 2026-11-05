"""Fixes of the independent review of build_v2 (runs/build_v2/CODE_REVIEW.md): one test per finding.
    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_v2_review.py -q"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest

from pinnkan import stats_rows as R
from pinnkan import stats_v4 as v4
from test_pk_v2_stats import CONDS, FOLD, LABS, make_store


# ------------------------------------------------------------------------------------------------ I1
def test_I1_the_T9_clause_takes_W_only_from_forms_that_are_reverse_S():
    store = make_store(A10g1=-0.5)                                  # both forms better than A1 by exp(0.5)
    store.tables[(8, "2")]["A10P"] = {c: 2.0 * np.exp(0.1) for c in CONDS}        # the as-published form is WORSE than A1: not reverse S, its effect is negative
    out = v4.run_v4(store)
    o = out["outcome"]
    assert o["M2"] and out["secondary"]["tests"]["QA10_g1"]["reverse_S"]["A10"]["rejected"] and not out["secondary"]["tests"]["QA10_g1"]["reverse_S"]["A10P"]["rejected"]
    assert o["abstract_sentence"].endswith("was 39.3 % more accurate still at this cell (95 % interval [39.3, 39.3]).")
    assert "-" not in o["abstract_sentence"].split("semi-empirical model was")[1]            # no negative effect printed


# ------------------------------------------------------------------------------------------------ I2
def test_I2_most_is_recomputed_under_the_downgrade_rows():
    good = make_store(P1g1=np.log(1.3), A9g1=np.log(1.2))            # d_c > 0 for every condition
    bad = make_store(P1g1=np.log(1.6), A9g1=np.log(1.1))             # same P1 / P2 / P3 outcomes, but the law share is below half of the total: d_c < 0
    rule = v4.resolve_config()[0]
    out = v4.run_v4(good)
    assert out["most_test"]["most"]
    assert R.row_tiers(out, good, rule)["most"] is True and R.row_tiers(out, bad, rule)["most"] is False
    assert R.row_tiers(out, bad, rule, cells="g1")["most"] is False              # row (iv) covers it too
    full = R.run_v4_full(good, {"e1_prime_approved": True}, retain_all=bad, B=500)
    assert full["downgrade"]["lowest_over_rows"]["most"] is False and full["most_test"]["most"] is False
    assert full["outcome"]["extent_clause"] == "e1'" and "most of the advantage" not in full["outcome"]["abstract_sentence"]
    lab = R.lab_stratified_tiers(out, good, B=500)[0]
    assert lab["most"] is True
    labs = {c: ("A" if i < 32 else "B") for i, c in enumerate(CONDS)}
    store = make_store(P1g1=np.log(1.3), A9g1=np.array([np.log(1.2)] * 32 + [np.log(1.01)] * 8))
    store.lab = labs
    assert R.lab_stratified_tiers(v4.run_v4(store), store, B=500)[0]["most"] is not None


# ------------------------------------------------------------------------------------------------ I3
def test_I3_missing_k_arms_raise_unless_chain_k_is_struck_by_config():
    store = make_store(k_chain=False)
    with pytest.raises(v4.ChainKMissingError):
        v4.run_v4(store)
    out = v4.run_v4(store, {"k_chain_struck": True})["primary"]
    assert out["k_chain_struck"] and out["initial_levels"]["P1N"] == pytest.approx(0.025) and out["initial_levels"]["K1"] == 0.0
    ok = v4.run_v4(make_store())["primary"]
    assert not ok["k_chain_struck"] and ok["initial_levels"]["P1N"] == pytest.approx(0.0125) and ok["initial_levels"]["K1"] == pytest.approx(0.0125)
    partial = make_store()
    del partial.tables[(32, "full")]["G15"]
    with pytest.raises(v4.ChainKMissingError):
        v4.run_v4(partial)


# ------------------------------------------------------------------------------------------------ I4 and the matched budget of A15 / G15
def test_I4_config_symbolic_reaches_the_arm_and_a_cap_that_disagrees_with_the_library_file_refuses_to_start(tmp_path, monkeypatch):
    from pinnkan import arms as A, run, symbolic as S
    base = {"dataset": "synthetic", "arms": ["A15"], "n_trials": 1, "inner_k": 2, "steps_scale": 0.04, "seeds": [0], "mode": "inner", "diagnostics": False,
            "synthetic": {"kind": "G0", "n_cyc_cond": 12, "n_sto_cond": 5, "reps": 2, "seed": 3}}
    monkeypatch.setattr(S, "library_file_cap", lambda path=S.LIB_FILE: 3)
    with pytest.raises(run.ConfigError, match="disagrees"):
        run.run({**base, "run_id": "bad", "symbolic": {"cap": 2}}, runs_dir=str(tmp_path))
    with pytest.raises(run.ConfigError, match="unknown symbolic"):
        run.run({**base, "run_id": "bad2", "symbolic": {"capp": 3}}, runs_dir=str(tmp_path))
    seen = []
    orig = S.resolve_cap
    monkeypatch.setattr(S, "resolve_cap", lambda cap=None: (seen.append(cap), orig(cap))[1])
    run.run({**base, "run_id": "ok", "symbolic": {"cap": 3, "refit_frac": 0.25}}, runs_dir=str(tmp_path))
    assert seen and all(c == 3 for c in seen)                            # the config value is what the arm resolved
    assert json.load(open(os.path.join(tmp_path, "ok", "config.json")))["symbolic"] == {"cap": 3, "refit_frac": 0.25}      # and it is part of the hashed config


def test_matched_budget_a15_g15_use_no_more_optimisation_steps_than_one_a1_fit(monkeypatch):
    from pinnkan import arms as A, data as D, pinn, symbolic as S, synth
    from pinnkan.specs import SPECS
    SPEC = SPECS["synthetic"]
    S0 = synth.make_synthetic("G0", n_cyc_cond=10, n_sto_cond=4, reps=2, seed=4)
    tr, _ = synth.split_conditions(S0.cells, 0.25, 4)
    calls = []
    orig = A.fit_pinn
    monkeypatch.setattr(A, "fit_pinn", lambda *a, **k: (calls.append(k.get("steps")), orig(*a, **k))[1])
    ctx = {"backbone": "self_limiting", "steps_scale": 0.05, "symbolic": {"cap": 3}}
    a1 = A.make_arm("A1", SPEC, A.default_hp("A1"), 0, ctx).fit(tr)
    n_a1 = calls[-1]
    for aid in ("A15", "G15"):
        calls.clear()
        arm = A.make_arm(aid, SPEC, A.default_hp(aid), 0, ctx).fit(tr)
        assert len(calls) == 2 and sum(calls) == n_a1 == arm.total_steps
    calls.clear()
    A.make_arm("A15", SPEC, A.default_hp("A15"), 0, {**ctx, "symbolic": {"cap": 3, "refit_frac": 0.25}}).fit(tr)
    assert sum(calls) == n_a1 and calls[1] < calls[0]
