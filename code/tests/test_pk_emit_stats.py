"""pinnkan: figure-input emitters (window.csv, stress_functions.json, residual_map.npz, superposition.csv, reference_values.json, H7 summary) and the statistics step
(contrasts_<test>.json, reference.json, controls.json).   .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_emit_stats.py -q"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.join(ROOT, "code", "tests"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pandas as pd
import pytest
import torch
from scipy import stats

torch.set_num_threads(1)

from pinnkan import guard, run, stats_step as st, synth
from pinnkan.data import WindowRule, prepare_many
from pinnkan.specs import SPECS

SPEC = SPECS["synthetic"]


# ------------------------------------------------------------------------------------------------ statistics primitives
def test_sign_test_and_order_statistic_interval():
    L = np.array([0.1] * 29 + [-0.1] * 11)                        # n = 40, 29 positives: the first k at level a/4 of TYPE1_SIGNFLIP.md
    assert np.isclose(st.sign_p(L, 0.0), stats.binom.sf(28, 40, 0.5)) and st.sign_p(L, 0.0) <= 0.025 / 4
    assert st.sign_p(np.array([0.1] * 28 + [-0.1] * 12), 0.0) > 0.025 / 4
    x = np.arange(1.0, 41.0)
    lo, hi, l = st.median_order_ci(x)
    assert (lo, hi, l) == (14.0, 27.0, 14)                         # coverage >= 95 %: 14th smallest .. 14th largest at n = 40


def test_bca_interval_brackets_the_mean_and_is_seeded():
    x = np.random.default_rng(0).normal(0.3, 1.0, 40)
    lo, hi = st.bca_mean_ci(x, B=4000)
    assert lo < x.mean() < hi and (lo, hi) == st.bca_mean_ci(x, B=4000)
    assert hi - lo < 1.0


# ------------------------------------------------------------------------------------------------ contrasts on constructed folds
def make_fold(tmp_path, name, scores, inner, dataset="samsung"):
    d = tmp_path / name
    os.makedirs(d)
    json.dump(scores, open(d / "condition_scores.json", "w"))
    json.dump({"inner_cv_pp": inner, "outer_test": {}}, open(d / "metrics.json", "w"))
    json.dump({"dataset": dataset, "test": "B"}, open(d / "config.json", "w"))
    return str(d)


def scores_for(conds, ratios, base=2.0, seed=0):
    rng = np.random.default_rng(seed)
    s1 = base * np.exp(rng.normal(0, 0.15, len(conds)))
    out = {"A1": dict(zip(conds, s1))}
    for a, r in ratios.items():
        out[a] = dict(zip(conds, s1 * np.exp(r + rng.normal(0, 0.03, len(conds)))))
    return out


def test_test_b_family_holm_gate_and_comparators_from_inner_cv(tmp_path):
    conds = [f"c{i:02d}" for i in range(40)]
    ratios = {"A9": 0.30, "A3": 0.02, "A4": 0.12, "A5": 0.16, "A7": 0.25, "A10": 0.0, "A11": 0.05, "A12": 0.10, "A2": 0.0, "A13": 0.08, "R1": 1.5, "R2": 1.2}
    sc = scores_for(conds, ratios)
    # the TEST-best pool arm is A3 (smallest ratio) but the INNER-CV best is A5: the comparator must follow the inner CV
    inner = {"A1": 2.0, "A3": 2.6, "A4": 2.4, "A5": 2.1, "A7": 2.8, "A9": 2.7, "A10": 2.7, "A11": 2.2, "A12": 2.3, "A2": 2.0, "A13": 2.1, "R1": 9.0, "R2": 8.0}
    c = st.build_contrasts("B", [make_fold(tmp_path, "f0", sc, inner)])["contrasts"]
    assert c["H1b"]["comp"] == "A5" and c["H1b"]["comp_by_fold"] == ["A5"]
    assert c["H1a"]["tier"] == "S" and c["H1b"]["tier"] == "S" and c["H6"]["tier"] != "S"       # ratios 0.30 and 0.16 clear ln 1.02 on 40 conditions; A10 is equal
    levels = sorted(c[k]["holm_level"] for k in ("H1a", "H1b", "H6"))
    assert np.allclose(levels, [0.025 / 3, 0.025 / 2, 0.025])
    assert c["H1c_A11"]["tier"] is None and c["H1c_A11"]["status"].startswith("secondary, not tested")
    for k in ("H1a", "H1b"):
        e = c[k]
        assert e["n"] == 40 and e["n_wins"] >= 38 and e["mean_pp"] > 0 and e["median_ci95"][0] < e["median_L"] < e["median_ci95"][1]
        assert set(e) >= {"L_by_cond", "mean_pp_ci95", "p_S", "p_N", "E_pp", "delta_S_pp", "delta_N_pp", "tier_pp", "rel_reduction_median"}
    assert np.isclose(c["H1b"]["E_pp"], inner["A5"]) and np.isclose(c["H1b"]["delta_S_pp"], 0.02 * inner["A5"]) and np.isclose(c["H1b"]["delta_N_pp"], 0.10 * inner["A5"])
    assert c["H2"]["outcome"] in ("B", "unresolved") and c["H2"]["tier"] is None
    assert {"ref_R1", "ref_R2", "pool_A3", "pool_A7", "X1"} <= set(c)


def test_gate_opens_h1c_only_when_the_family_is_all_tier_s(tmp_path):
    conds = [f"c{i:02d}" for i in range(40)]
    sc = scores_for(conds, {"A9": 0.3, "A3": 0.2, "A4": 0.2, "A5": 0.2, "A7": 0.2, "A10": 0.3, "A11": 0.25, "A12": 0.01, "A2": -0.2})
    inner = {a: 2.0 + 0.01 * i for i, a in enumerate(sc)}
    inner["A11"] = 1.9                                                               # A11 is the inner-CV-best data-only learner
    c = st.build_contrasts("B", [make_fold(tmp_path, "g", sc, inner)])
    cc = c["contrasts"]
    assert all(cc[k]["tier"] == "S" for k in ("H1a", "H1b", "H6"))
    assert cc["H1c_A11"]["tier"] == "S" and cc["H1c_A11"]["status"] == "key secondary, gate open"
    assert cc["H1c_A12"]["tier"] is None                                             # not the selected comparator: reported only
    assert cc["H2"]["outcome"] == "C"                                                # the hard ODE is better by far: reverse tier S
    assert c["margins"] == {"S": np.log(1.02), "N": -np.log(1.10)}


def test_h2_outcome_a_requires_the_gate_and_tost_gives_b(tmp_path):
    conds = [f"c{i:02d}" for i in range(40)]
    inner = {"A1": 2.0, "A2": 2.0, "A9": 2.0, "A10": 2.0, "A3": 2.0, "A4": 2.0, "A5": 2.0, "A7": 2.0}
    sc = scores_for(conds, {"A9": 0.3, "A3": 0.3, "A4": 0.3, "A5": 0.3, "A7": 0.3, "A10": 0.3, "A2": 0.2})
    assert st.build_contrasts("B", [make_fold(tmp_path, "a", sc, inner)])["contrasts"]["H2"]["outcome"] == "A"
    sc = scores_for(conds, {"A9": 0.3, "A3": 0.3, "A4": 0.3, "A5": 0.3, "A7": 0.3, "A10": 0.3, "A2": 0.0})
    assert st.build_contrasts("B", [make_fold(tmp_path, "b", sc, inner)])["contrasts"]["H2"]["outcome"] == "B"
    sc = scores_for(conds, {"A9": 0.0, "A3": 0.3, "A4": 0.3, "A5": 0.3, "A7": 0.3, "A10": 0.3, "A2": 0.2})
    assert st.build_contrasts("B", [make_fold(tmp_path, "c", sc, inner)])["contrasts"]["H2"]["outcome"] != "A"       # family not all S: A is not tested


def test_comparator_is_chosen_per_fold_and_conditions_are_merged(tmp_path):
    c1, c2 = [f"a{i}" for i in range(20)], [f"b{i}" for i in range(20)]
    s1 = scores_for(c1, {"A4": 0.1, "A5": 0.3, "A9": 0.2, "A10": 0.2}, seed=1)
    s2 = scores_for(c2, {"A4": 0.3, "A5": 0.1, "A9": 0.2, "A10": 0.2}, seed=2)
    i1 = {"A1": 2.0, "A4": 2.1, "A5": 2.5, "A9": 2.5, "A10": 2.5}
    i2 = {"A1": 2.0, "A4": 2.5, "A5": 2.1, "A9": 2.5, "A10": 2.5}
    c = st.build_contrasts("B", [make_fold(tmp_path, "f1", s1, i1), make_fold(tmp_path, "f2", s2, i2)])["contrasts"]["H1b"]
    assert c["comp_by_fold"] == ["A4", "A5"] and c["n"] == 40
    assert np.isclose(c["E_pp"], 0.5 * 2.1 + 0.5 * 2.1)
    assert np.isclose(c["L_by_cond"]["a3"], np.log(s1["A4"]["a3"] / s1["A1"]["a3"])) and np.isclose(c["L_by_cond"]["b3"], np.log(s2["A5"]["b3"] / s2["A1"]["b3"]))


def test_test_c_s2_and_isu_rules(tmp_path):
    conds = [f"c{i}" for i in range(13)]
    sc = scores_for(conds, {"A10": 0.4, "A11": 0.05, "A12": 0.1, "A9": 0.2, "R1": 1.0})
    inner = {"A1": 2.0, "A10": 2.5, "A11": 2.2, "A12": 2.4, "A9": 2.5, "R1": 9.0}
    c = st.build_contrasts("C", [make_fold(tmp_path, "c", sc, inner)])["contrasts"]
    assert {"H4a", "H4b"} <= set(c) and c["H4a"]["comp"] == "A11" and sorted([c["H4a"]["holm_level"], c["H4b"]["holm_level"]]) == [0.0125, 0.025]
    assert c["H4b"]["tier"] in ("S", "N", "-")
    sc = scores_for([f"s{i}" for i in range(19)], {"A3": 0.0, "A9": 0.1, "A10": 0.2})
    c = st.build_contrasts("S2", [make_fold(tmp_path, "s", sc, {"A1": 2.0, "A3": 2.1, "A9": 2.4, "A10": 2.6})])["contrasts"]
    assert c["H5"]["comp"] == "A3" and c["H5"]["holm_level"] == 0.025 and c["H5"]["tier"] in ("N", "-")
    sc = scores_for([f"i{i}" for i in range(40)], {"A4": 0.1, "A5": 0.2, "A7": 0.3, "A9": 0.4, "A10": 0.4, "A11": 0.0})
    c = st.build_contrasts("ISU", [make_fold(tmp_path, "i", sc, {a: 2.0 for a in sc}, "isu")])["contrasts"]
    assert "pool_A3" not in c and c["H1b"]["comp"] in ("A4", "A5", "A7") and c["H1c_A11"]["status"].startswith("secondary (not gatekept")


# ------------------------------------------------------------------------------------------------ reference quantities
def test_reference_values_zero_for_identical_replicates_and_positive_otherwise():
    S = synth.make_synthetic("G0", n_cyc_cond=6, n_sto_cond=2, reps=3, seed=5, noise=0.0, tau=0.0)
    rule = WindowRule.for_spec(SPEC)
    ref = st.reference_values(prepare_many([c for c in S.cells if c.kind == "cycling"], rule))
    assert ref["R_LOO"] < 1e-6 and ref["R_WARP"] < 1e-6 and ref["n_conditions"] == 6                    # no noise, no offsets: replicates coincide
    S = synth.make_synthetic("G0", n_cyc_cond=6, n_sto_cond=2, reps=3, seed=5)
    ref = st.reference_values(prepare_many([c for c in S.cells if c.kind == "cycling"], rule))
    assert ref["R_LOO"] > 0.1 and ref["R_WARP_form"] in ("additive", "multiplicative") and ref["R_WARP"] <= min(ref["R_WARP_add"], ref["R_WARP_mult"]) + 1e-12


# ------------------------------------------------------------------------------------------------ end-to-end on synthetic runs
CFG = {"dataset": "synthetic", "mode": "confirmatory", "n_trials": 1, "inner_k": 2, "steps_scale": 0.04, "seeds": [0, 1], "backbone": "self_limiting",
       "arms": ["A1", "A2", "A4", "A9", "A10", "R1", "R2"], "synthetic": {"kind": "G2", "n_cyc_cond": 16, "n_sto_cond": 8, "reps": 2, "seed": 7}}


@pytest.fixture(scope="module")
def runs_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("emit")
    run.run({**CFG, "run_id": "B", "test": "B"}, runs_dir=str(d))
    run.run({**CFG, "run_id": "NEG", "test": "B", "arms": ["A1", "A9", "R2"], "permute_stress": True}, runs_dir=str(d))
    return d


def test_run_record_has_all_figure_inputs(runs_dir):
    d = runs_dir / "B"
    assert (d / "SYNTHETIC").exists()
    w = pd.read_csv(d / "window.csv")
    assert list(w.columns) == ["cell_id", "cond", "t", "retention"] and w.groupby("cell_id").size().min() >= 3
    pred = pd.read_csv(d / "predictions.csv")
    assert set(w.cell_id) == set(pred[pred.phase == "outer_test"].cell_id)                                       # a window for every scored cell
    sf = json.load(open(d / "stress_functions.json"))
    assert sf["n_members"] == 2 and len(sf["soc"] if "soc" in sf else sf["calendar"]["soc"]) == 21
    cal = sf["calendar"]
    assert set(cal) == {"soc", "E_kJmol", "a_pp500", "A10_E_kJmol"} and set(cal["E_kJmol"]) == {"mean", "lo", "hi"} and len(cal["E_kJmol"]["mean"]) == 21
    assert np.all(np.array(cal["E_kJmol"]["lo"]) <= np.array(cal["E_kJmol"]["hi"]))
    sr = sf["storage_rate"]
    assert sr["T_C"] == [10, 23, 45] and np.array(sr["mean"]).shape == (3, 21)
    ar = sf["arrhenius"]
    assert ar["soc"] == [5, 50, 80, 100] and np.array(ar["ln_rate"]["mean"]).shape == (4, 3)
    assert set(sf["cyclic"]) == {"T", "soc_mid", "dod", "c_ch", "c_dch"}
    for v in sf["cyclic"].values():
        n = len(v["x"])
        assert len(v["A1"]["mean"]) == n and abs(np.mean(v["A1"]["mean"])) < 1e-6 and len(v["A4"]["mean"]) == n and len(v["A10"]["mean"]) == n
        assert np.isfinite(v["A10"]["mean"]).all()
    z = np.load(d / "residual_map.npz")
    assert z["absR_T_SOC"].shape == (len(z["T_edges"]) - 1, len(z["soc_edges"]) - 1) and z["absR_cch_T"].shape == (len(z["T_edges"]) - 1, len(z["cch_edges"]) - 1)
    assert np.all(z["absR_T_SOC"] >= 0) and z["train_T_SOC"].shape[1] == 2 and z["train_cch_T"].shape[1] == 2
    sp = pd.read_csv(d / "superposition.csv")
    assert list(sp.columns) == ["cell_id", "cond", "arm", "share_cal", "cal_exceeds_total"] and set(sp.arm) == {"A1", "A2"} and (sp.share_cal >= 0).all()
    assert json.load(open(d / "reference_values.json"))["R_LOO"] > 0


def test_stats_step_end_to_end_with_controls(runs_dir, tmp_path):
    an = tmp_path / "analysis"
    out = st.run_stats(str(an), {"B": [str(runs_dir / "B")]}, negative_run=str(runs_dir / "NEG"), stress_run=str(runs_dir / "B"))
    c = json.load(open(an / "contrasts_B.json"))
    assert c["test"] == "B" and c["source"] == ["outer_test"] and c["synthetic"] is True and (an / "SYNTHETIC").exists()
    demo = json.load(open(os.path.join(ROOT, "runs", "figdemo_SYNTHETIC", "analysis", "contrasts_B.json")))
    assert set(demo) - {"synthetic"} <= set(c)                                                                  # same top-level keys as the figure demo
    assert {"H1a", "H1b", "H6", "ref_R1", "ref_R2"} <= set(c["contrasts"]) and set(demo["contrasts"]["H1a"]) - {"label", "hyp"} <= set(c["contrasts"]["H1a"])
    ctl = json.load(open(an / "controls.json"))
    assert set(ctl["negative"]) == {"permutation", "A9_minus_A1_mean_L", "p_two_sided", "passed", "A1_vs_R2_median_L", "A1_not_beating_R2"}
    assert isinstance(ctl["positive"]["P2_monotone_in_T"], bool)
    ref = json.load(open(an / "reference.json"))["values"]["B"]
    assert ref["R_LOO"] > 0 and ref["R_WARP"] > 0
    m = json.load(open(runs_dir / "NEG" / "metrics.json"))
    assert m["negative_control"]["complete"] and "median_L_R2_over_A1" in m["negative_control"]


def test_stats_step_on_real_training_folds_uses_inner_cv_only(tmp_path):
    """ISU training fold 0, mode inner: no outer cell is built, the contrast is computed from out-of-fold inner-CV scores and labelled so"""
    assert not guard.is_frozen()
    cfg = {"run_id": "isu0", "dataset": "isu", "test": "B", "fold": 0, "mode": "inner", "arms": ["A1", "A2", "A4", "A5", "A7", "A9", "A10", "A12", "R1", "R2"], "n_trials": 1,
           "inner_k": 2, "steps_scale": 0.03, "backbone": "self_limiting"}
    d = run.run(cfg, runs_dir=str(tmp_path))
    assert (tmp_path / "isu0" / "window.csv").exists() and not (tmp_path / "isu0" / "condition_scores.json").exists()
    assert not (tmp_path / "isu0" / "stress_functions.json").exists()                                           # no calendar term on ISU
    test_cells = set(json.load(open(os.path.join(ROOT, "runs", "splits", "isu_testB.json")))["folds"]["0"]["test_cells"])
    assert not (set(pd.read_csv(tmp_path / "isu0" / "window.csv").cell_id) & test_cells)
    st.run_stats(str(tmp_path / "an"), {"ISU": [d]})
    c = json.load(open(tmp_path / "an" / "contrasts_ISU.json"))
    assert c["source"] == ["inner_cv_training_conditions"] and "H1a" in c["contrasts"] and c["contrasts"]["H1b"]["comp"] in ("A4", "A5", "A7")
    with pytest.raises(guard.TestFoldAccessError):
        run.run({**cfg, "run_id": "isu_conf", "mode": "confirmatory", "steps_scale": 1.0}, runs_dir=str(tmp_path))                  # the guard still blocks the outer test


def test_stats_step_on_snl_training_fold(tmp_path):
    cfg = {"run_id": "snl0", "dataset": "snl", "test": "B", "fold": 0, "mode": "inner", "arms": ["A1", "A4", "A5", "A9", "A10", "R1"], "n_trials": 1, "inner_k": 2,
           "steps_scale": 0.03, "backbone": "self_limiting"}
    d = run.run(cfg, runs_dir=str(tmp_path))
    st.run_stats(str(tmp_path / "an"), {"SNL": [d]})
    c = json.load(open(tmp_path / "an" / "contrasts_SNL.json"))
    assert c["source"] == ["inner_cv_training_conditions"] and c["contrasts"]["H6"]["n"] == c["n"]
    assert json.load(open(tmp_path / "an" / "reference.json"))["values"]["SNL"]["R_LOO"] > 0


# ------------------------------------------------------------------------------------------------ H7 driver
def test_h7_driver_summary_and_surfaces(tmp_path):
    d = run.run({"run_id": "h7", "dataset": "synthetic", "mode": "h7", "backbone": "self_limiting",
                 "h7": {"gens": ["G0", "G2"], "n_draws": 2, "arms": ["A2", "A4"], "n_trials": 1, "inner_k": 2, "steps_scale": 0.05, "design": {"n_cyc_cond": 14, "n_sto_cond": 6, "reps": 2}}},
                runs_dir=str(tmp_path))
    S = json.load(open(os.path.join(d, "summary.json")))
    assert len(S["draws"]) == 4 and S["thresholds"] == {"pass_": 0.15, "fail": 0.30} and S["arms"] == ["A2", "A4"]
    for r in S["draws"]:
        assert set(r["nrmse"]) == {"A2", "A4"} and 0 <= r["additive_floor"] and set(r["forecast_pp"]) == {"A2", "A4"}
    for g in ("G0", "G2"):
        z = np.load(os.path.join(d, f"surfaces_{g}.npz"))
        assert z["f_true"].shape == (2, 500) and z["f_A4"].shape == (2, 500) and z["lhs"].shape == (500, 5) and abs(z["f_true"].mean()) < 1e-9
    fl = {g: np.mean([r["additive_floor"] for r in S["draws"] if r["gen"] == g]) for g in ("G0", "G2")}
    assert fl["G2"] > fl["G0"]
    assert (tmp_path / "h7" / "SYNTHETIC").exists()
    with pytest.raises(run.ConfigError):
        run.run({"run_id": "h7x", "dataset": "isu", "mode": "h7"}, runs_dir=str(tmp_path))
