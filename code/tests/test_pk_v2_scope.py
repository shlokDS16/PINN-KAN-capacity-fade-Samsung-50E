"""build_v2 item 7: struck pieces are out of the Design R2 confirmatory path (H3, G2 'KAN win', A3 / A7 off the grid, the V3 analysis) but stay in the code for history."""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import pytest

from pinnkan import arms, run
from pinnkan import stats_step as st

CFG = {"dataset": "synthetic", "n_trials": 1, "inner_k": 2, "steps_scale": 0.04, "seeds": [0], "diagnostics": False, "synthetic": {"kind": "G0", "n_cyc_cond": 12, "n_sto_cond": 5, "reps": 2, "seed": 3}}


def test_arm_scopes():
    assert set(arms.OUT_OF_SCOPE_ARMS) == {"A3", "A6", "A7", "A8", "A14"} and arms.ARMS["A5"].scope == "m32_only" and arms.ARMS["A1"].scope == "grid"
    assert all(a in arms.ARMS for a in arms.OUT_OF_SCOPE_ARMS)                    # history is kept: the classes and spaces are still there


@pytest.mark.parametrize("extra", [{"mode": "confirmatory"}, {"mode": "inner", "m": 8}, {"mode": "inner", "k": "grid"}])
def test_design_r2_refuses_out_of_scope_arms_on_the_grid_and_confirmatory_path(tmp_path, extra):
    for a in ("A3", "A7"):
        with pytest.raises(run.ConfigError, match="out of scope"):
            run.run({**CFG, "run_id": "x", "arms": [a, "R2"], **extra}, runs_dir=str(tmp_path))


def test_development_runs_and_v3_legacy_runs_may_still_use_them(tmp_path):
    d = run.run({**CFG, "run_id": "dev", "mode": "inner", "arms": ["A3", "R2"]}, runs_dir=str(tmp_path))                        # development run, no grid, no scoring
    assert not os.path.exists(os.path.join(d, "OUT_OF_SCOPE_V3_LEGACY"))
    d2 = run.run({**CFG, "run_id": "leg", "mode": "confirmatory", "design": "V3_legacy", "arms": ["A3", "A7", "R2"]}, runs_dir=str(tmp_path))
    assert os.path.exists(os.path.join(d2, "OUT_OF_SCOPE_V3_LEGACY"))
    with pytest.raises(run.ConfigError):
        run.run({**CFG, "run_id": "bad", "design": "R3", "arms": ["R2"]}, runs_dir=str(tmp_path))


def test_h7_is_g0_only_under_design_r2(tmp_path):
    for gens in (["G0", "G2"], ["G1"], None):
        h7 = {"n_draws": 1, "arms": ["A2"], "n_trials": 1, "inner_k": 2, "steps_scale": 0.04}
        if gens:
            h7["gens"] = gens
        with pytest.raises(run.ConfigError, match="G0 only"):
            run.run({"run_id": "h", "dataset": "synthetic", "mode": "h7", "h7": h7}, runs_dir=str(tmp_path))


def test_the_v3_statistics_refuse_design_r2_runs_and_mark_h3_out_of_scope(tmp_path):
    d = run.run({**CFG, "run_id": "r2", "mode": "inner", "arms": ["A1", "A2", "R2"], "diagnostics": False}, runs_dir=str(tmp_path))
    with pytest.raises(st.OutOfScopeError):
        st.run_stats(str(tmp_path / "an"), {"B": [d]})
    with pytest.raises(st.OutOfScopeError):
        st.Builder([st.load_fold(d)], "B")
    dg = run.run({**CFG, "run_id": "g", "mode": "inner", "arms": ["A1", "A2", "R2"], "m": 8}, runs_dir=str(tmp_path))
    with pytest.raises(st.OutOfScopeError):
        st.build_contrasts("B", [dg])
    assert "H3" in " ".join(st.V3_OUT_OF_SCOPE) and "KAN win" in " ".join(st.V3_OUT_OF_SCOPE)


def test_gate_g_is_nc1_and_pc1():
    g = st.gate_g({"negative": {"nc1": {"passed": True}}, "positive": {"P1_G0_nrmse_leq_0p15": True, "P3_passed": False}})
    assert not g["tripped"] and g["reported_checks"]["PC-3_A1_beats_persistence"] is False
