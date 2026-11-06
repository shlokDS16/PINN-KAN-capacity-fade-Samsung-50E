"""build_v1 section 7: H3 assembly, sensitivity rows computed from run outputs (lab, stage, bootstraps, margins), H7 batch pieces (Kendall tau, thresholds, P1, hard vs soft,
resumable shardable driver), physical-validation analyses 11a, run-level outputs (cell_scores.json, condition_meta.json), run-level sensitivity options.
Synthetic data only."""
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

torch.set_num_threads(1)

from pinnkan import h7, physval, run, semi, stats_ext, synth
from pinnkan import stats_step as st
from test_pk_emit_stats import make_fold, scores_for


# ------------------------------------------------------------------------------------------------ H3
def _h3_folds(tmp_path, name, ratios, n=40, inner=None):
    conds = [f"c{i:02d}" for i in range(n)]
    base = {"A9": 0.3, "A3": 0.2, "A4": 0.0, "A5": 0.0, "A7": 0.2, "A10": 0.2, "A11": 0.1, "A12": 0.1, "A2": 0.0, "A13": 0.0, "R1": 1.5, "R2": 1.2}
    base.update(ratios)
    sc = scores_for(conds, base)
    inn = {"A1": 2.0, "A3": 2.6, "A4": 2.3, "A5": 2.5, "A7": 2.8, "A9": 2.7, "A10": 2.7, "A11": 2.2, "A12": 2.3, "A2": 2.0, "A13": 2.1, "R1": 9.0, "R2": 8.0}
    inn.update(inner or {})
    return [make_fold(tmp_path, name, sc, inn)]


def test_h3_win_needs_tier_S_against_the_gam_and_the_g2_gate(tmp_path):
    folds = _h3_folds(tmp_path, "w", {"A4": 0.20, "A5": 0.35})                       # inner-CV best of {A4, A5} is A4 (2.3 < 2.5): the comparator follows the inner CV
    c = st.build_contrasts("B", folds, g2={"passes": True})["contrasts"]["H3"]
    assert c["comp"] == "A4" and c["outcome"] == "win" and c["tier_S_met"] and c["g2_passes"] is True and c["win_blocked_by_g2"] is False
    c = st.build_contrasts("B", folds, g2={"passes": False})["contrasts"]["H3"]
    assert c["outcome"] != "win" and c["tier_S_met"] and c["win_blocked_by_g2"]                        # tier S but G2 failed: no KAN wording
    c = st.build_contrasts("B", folds)["contrasts"]["H3"]
    assert c["outcome"] != "win" and c["g2_passes"] is None and c["win_blocked_by_g2"]               # no H7 batch: unavailable, not assumed


def test_h3_worse_tie_and_unresolved(tmp_path):
    c = st.build_contrasts("B", _h3_folds(tmp_path, "a", {"A4": -0.25, "A5": -0.1}), g2={"passes": True})["contrasts"]["H3"]
    assert c["outcome"] == "worse" and c["p_worse"] <= 0.025                                        # the GAM is clearly better than the KAN
    c = st.build_contrasts("B", _h3_folds(tmp_path, "b", {"A4": 0.0, "A5": 0.0}), g2={"passes": True})["contrasts"]["H3"]
    assert c["outcome"] == "tie" and c["tie_tost"]                                                  # equal within +-10 %
    c = st.build_contrasts("B", _h3_folds(tmp_path, "c", {"A4": 0.06, "A5": 0.06}, n=5), g2={"passes": True})["contrasts"]["H3"]
    assert c["outcome"] == "unresolved"                                                             # five conditions cannot reach 0.025 with an exact sign test (2^-5 = 0.031)


def test_h3_only_in_test_b(tmp_path):
    sc = scores_for([f"s{i}" for i in range(19)], {"A3": 0.0, "A9": 0.1, "A10": 0.2})
    c = st.build_contrasts("S2", [make_fold(tmp_path, "s", sc, {"A1": 2.0, "A3": 2.1, "A9": 2.4, "A10": 2.6})])["contrasts"]
    assert "H3" not in c


# ------------------------------------------------------------------------------------------------ sensitivity rows from run outputs
def _fold_with_meta(tmp_path, n=24, shift=0.2, seed=3):
    conds = [f"c{i:02d}" for i in range(n)]
    sc = scores_for(conds, {"A9": shift, "A10": shift / 2, "A4": 0.05, "A5": 0.05, "A3": 0.05, "A7": 0.05}, seed=seed)
    inner = {a: 2.0 for a in sc}
    d = make_fold(tmp_path, "f0", sc, inner)
    labs = ["HM"] * 12 + ["INT"] * 8 + ["SIE"] * 4
    meta = {c: dict(n_cells=3, lab={labs[i]: 3}, stage={"1": 2, "2": 1}) for i, c in enumerate(conds)}
    json.dump(meta, open(os.path.join(d, "condition_meta.json"), "w"))
    rng = np.random.default_rng(seed)
    cells = {a: {} for a in ("A1", "A9", "A10", "A4", "A5", "A3", "A7")}
    for c in conds:
        for k in range(3):
            base = sc["A1"][c] * np.exp(rng.normal(0, 0.1))
            for a in cells:
                cells[a][f"{c}_{k}"] = dict(cond=c, rmse_pp=float(base * (1.0 if a == "A1" else float(sc[a][c] / sc["A1"][c]) * np.exp(rng.normal(0, 0.05)))), n_fc=4)
    json.dump(cells, open(os.path.join(d, "cell_scores.json"), "w"))
    return d, conds


def test_sensitivity_rows_have_lab_stage_bootstrap_and_margin_content(tmp_path, monkeypatch):
    monkeypatch.setattr(stats_ext, "B_BOOT", 400)
    d, conds = _fold_with_meta(tmp_path)
    folds = [st.load_fold(d)]
    c = st.Builder(folds, "B").build()
    s = stats_ext.sensitivity_for_test(c, folds, "B")
    assert s["availability"] == {"condition_meta": True, "cell_scores": True}
    h1a = s["entries"]["H1a"]
    assert set(h1a["per_lab"]) == {"HM", "INT", "SIE"} and sum(v["n"] for v in h1a["per_lab"].values()) == 24 and set(h1a["per_stage"]) == {"1"}
    assert set(h1a["leave_one_lab_out"]) == {"HM", "INT", "SIE"} and h1a["leave_one_lab_out"]["HM"]["n"] == 12
    lb = h1a["lab_stratified_bootstrap"]
    assert lb["strata_sizes"] == {"HM": 12, "INT": 8, "SIE": 4} and lb["median_L_ci95"][0] < lb["median_L"] < lb["median_L_ci95"][1]
    assert lb["post_stratified_mean_L"] != lb["plain_mean_L"]                                       # equal weight per laboratory differs from equal weight per condition
    ts = h1a["two_stage_bootstrap"]
    assert ts["n_conditions"] == 24 and ts["median_L_ci95"][0] < ts["median_L"] < ts["median_L_ci95"][1] and "weighted_log_ratio_ci95" in ts
    rows = {(r["delta_S"], r["delta_N"]): r for r in h1a["margins"]["rows"]}
    assert set(rows) == {(0.0, 0.05), (0.0, 0.15), (0.05, 0.05), (0.05, 0.15)}
    assert rows[(0.0, 0.05)]["p_S"] <= rows[(0.05, 0.05)]["p_S"] + 1e-12                              # a lower superiority margin cannot raise the p-value
    assert set(s["mc_labels"]) >= {"B|H1a|A9|SENS_lab_strat_boot", "B|H1a|A9|SENS_two_stage_boot"}
    # reproducible: the Monte Carlo streams are the registered ones
    s2 = stats_ext.sensitivity_for_test(c, folds, "B")
    assert s2["entries"]["H1a"]["lab_stratified_bootstrap"]["median_L_ci95"] == lb["median_L_ci95"]


def test_sensitivity_rows_are_marked_unavailable_without_run_files(tmp_path):
    conds = [f"c{i}" for i in range(14)]
    sc = scores_for(conds, {"A9": 0.2, "A10": 0.0, "A4": 0.1})
    f = st.load_fold(make_fold(tmp_path, "f", sc, {a: 2.0 for a in sc}))
    c = st.Builder([f], "B").build()
    s = stats_ext.sensitivity_for_test(c, [f], "B")
    assert s["availability"] == {"condition_meta": False, "cell_scores": False}
    assert "not available" in s["entries"]["H1a"]["lab_rows"] and "margins" in s["entries"]["H1a"]


def test_leave_one_lab_out_removes_exactly_that_labs_conditions(tmp_path):
    d, conds = _fold_with_meta(tmp_path, n=24, shift=0.3)
    f = st.load_fold(d)
    c = st.Builder([f], "B").build()
    strata = stats_ext.condition_strata([f])
    row = stats_ext.lab_stage_rows(c["contrasts"]["H1a"], strata, 0.025)
    L = np.array([c["contrasts"]["H1a"]["L_by_cond"][x] for x in conds])
    lab = np.array([strata[x]["lab"] for x in conds])
    assert row["leave_one_lab_out"]["SIE"]["median_L"] == pytest.approx(float(np.median(L[lab != "SIE"])))
    assert row["per_lab"]["INT"]["median_L"] == pytest.approx(float(np.median(L[lab == "INT"])))


# ------------------------------------------------------------------------------------------------ H7 pieces
def test_variance_importance_recovers_a_known_function():
    rng = np.random.default_rng(0)
    raw = rng.uniform(0, 1, (2000, 5))
    f = 3.0 * raw[:, 0] + 1.0 * raw[:, 2]
    imp = h7.variance_importance(f, raw)
    assert imp[0] > imp[2] > max(imp[1], imp[3], imp[4]) and imp[0] == pytest.approx(0.9, abs=0.05) and imp[1] < 0.01
    tau, a, b = h7.kendall_importance(f, f, raw)
    assert tau == pytest.approx(1.0)
    tau_rev, _, _ = h7.kendall_importance(-f + 5.0 * raw[:, 4], f, raw)
    assert tau_rev < 1.0
    assert np.isnan(h7.kendall_importance(np.zeros(2000), f, raw)[0])                                 # constant importance vector: undefined, not 0


def _rec(gen, i, nrmse, forecast=None, floor=0.3, tau=None):
    return dict(gen=gen, draw=i, additive_floor=floor, additive_floor_discriminates=floor > 0.15, nrmse=nrmse, nrmse_centred=nrmse, kendall_tau=tau or {a: 0.5 for a in nrmse},
                importance={}, forecast_pp=forecast or {}, best_hp={})


def _summary(good=True):
    rng = np.random.default_rng(1)
    dr = []
    for i in range(20):
        e = lambda s: float(s * (1 + 0.1 * rng.normal()))
        dr.append(_rec("G0", i, {"A1": e(0.08), "A2": e(0.06), "A4": e(0.08), "A8": e(0.2)}, {"A1": e(1.0), "A2": e(0.9), "A4": e(1.0), "A8": e(2.0), "A11": e(2.5 if good else 0.5), "A12": e(2.0 if good else 0.5)}))
        dr.append(_rec("G1", i, {"A1": e(0.10), "A2": e(0.12), "A4": e(0.10), "A8": e(0.30)}, {"A1": e(1.0), "A2": e(1.3), "A4": e(1.0), "A8": e(2.0)}))
        dr.append(_rec("G2", i, {"A1": e(0.10), "A2": e(0.14), "A4": e(0.27), "A8": e(0.34)}, {"A1": e(1.0), "A2": e(1.2), "A4": e(1.1), "A8": e(2.0)}, floor=0.3))
    return {"draws": dr}


def test_verdicts_follow_the_thresholds_of_section_13():
    v = h7.verdicts(_summary())
    assert v["recovery"]["G2"]["A1"]["status"] == "pass" and v["recovery"]["G2"]["A4"]["status"] == "between"
    assert v["structured_vs_free"]["G1"]["A1"]["meets"] and v["structured_vs_free"]["G1"]["structured_generic"]               # 0.10 / 0.30 = 0.33 <= 0.67, p << 0.05
    assert v["structured_vs_free"]["G2"]["A4"]["meets"] is False and v["structured_vs_free"]["G2"]["structured_generic"] is False   # GAM 0.27 / 0.34 = 0.79 > 0.67: generic "structured" needs the GAM too
    g2 = v["G2"]
    assert g2["valid"] and g2["kan_lower_than_gam"] and g2["kan_meets_pass_line"] and g2["passes"] and g2["p_kan_lower_than_gam"] < 0.05
    assert v["G0_kan_vs_gam"]["ok"] and v["P1"]["passed"] is True
    assert "not available" in v["residual_map_claim"]


def test_g2_validity_rule_blocks_the_gate_when_the_floor_is_low():
    s = _summary()
    for d in s["draws"]:
        if d["gen"] == "G2":
            d["additive_floor"] = 0.07                                   # the pilot-strength G2: additive GAM already fits (P4)
    g2 = h7.verdicts(s)["G2"]
    assert g2["valid"] is False and g2["passes"] is False


def test_p1_fails_when_a_learner_is_better_and_is_not_evaluated_without_learners():
    assert h7.verdicts(_summary(good=False))["P1"]["passed"] is False
    s = _summary()
    for d in s["draws"]:
        d["forecast_pp"].pop("A11", None)
        d["forecast_pp"].pop("A12", None)
    assert h7.p1_positive_control(s["draws"])["passed"] is None


def test_hard_vs_soft_on_g1_is_a_paired_exact_sign_test():
    hs = h7.verdicts(_summary())["hard_vs_soft_G1"]
    assert hs["n"] == 20 and hs["outcome"] == "A" and hs["n_soft_better"] >= 18 and hs["descriptive"]          # forecast RMSE of A2 is 30 % above A1 in the constructed draws
    assert h7.hard_vs_soft([], "G1")["outcome"] == "not evaluated"


def test_g2p_is_the_weaker_generator_and_g2_stays_the_strengthened_one():
    assert synth.G2_STRENGTH["G2"] == (1.2, 0.8)                                                      # the upper pilot-grid values of PREREG 13
    spec = h7.SPEC
    floors = {}
    for kind in ("G2", "G2p"):
        S = synth.make_synthetic(kind, n_cyc_cond=16, n_sto_cond=4, reps=1, seed=2)
        X = np.stack([spec.norm(c.raw) for c in S.cells if c.kind == "cycling"])
        raw = spec.denorm(h7._hull_sample(X, 500, 12345))
        floors[kind] = h7.additive_floor(S.log_rate_cyc(raw), raw)
    assert floors["G2"] > floors["G2p"] > 0.0


def test_h7_driver_is_resumable_shardable_and_aggregates(tmp_path):
    kw = dict(gens=("G0",), n_draws=2, arms=("A2",), n_trials=1, inner_k=2, steps_scale=0.04, design=dict(n_cyc_cond=10, n_sto_cond=4, reps=2))
    out = str(tmp_path / "h7")
    r0 = h7.run_h7(out, shard=(0, 2), **kw)
    assert r0["complete"] is False and r0["n_missing"] == 1 and sorted(os.listdir(os.path.join(out, "draws"))) == ["G0_00.json", "G0_00.npz"]
    t0 = os.path.getmtime(os.path.join(out, "draws", "G0_00.json"))
    r1 = h7.run_h7(out, shard=(1, 2), arms_by_gen={"G0": ("A2", "A12")}, **kw)                       # shard 1 adds the draw with the learner; shard 0's unit is not redone
    assert r1["complete"] and os.path.getmtime(os.path.join(out, "draws", "G0_00.json")) == t0
    d = r1["draws"]
    assert [x["draw"] for x in d] == [0, 1] and "A12" not in d[0]["forecast_pp"] and "A12" in d[1]["forecast_pp"] and "A12" not in d[1]["nrmse"]
    assert set(d[0]) >= {"kendall_tau", "importance", "nrmse", "additive_floor", "forecast_pp"} and d[0]["importance"]["true"] and len(d[0]["importance"]["A2"]) == 5
    z = np.load(os.path.join(out, "surfaces_G0.npz"))
    assert z["f_true"].shape == (2, 500) and z["f_A2"].shape == (2, 500)
    assert json.load(open(os.path.join(out, "summary.json")))["verdicts"]["P1"]["passed"] is None     # learners only in one draw -> mixed; P1 reports not evaluated or by draws present
    assert h7.g2_status(os.path.join(out, "summary.json"))["passes"] is False                         # no G2 draws: the gate is closed


# ------------------------------------------------------------------------------------------------ 11a
def _sf(tmp_path, name, n_members=3, turning=True, a10=True):
    soc = list(np.arange(0, 101, 5.0))
    rng = np.random.default_rng(len(name))
    E = 60 + 5 * np.sin(np.array(soc) / 30.0) + rng.normal(0, 0.5, (n_members, len(soc)))
    r = np.array([[1.0 + 0.02 * np.array(soc) * (T / 23.0) + (-0.03 * np.maximum(np.array(soc) - 85.0, 0.0) * (T / 23.0) if turning else 0.0) for T in (10, 23, 45)] for _ in range(n_members)]) \
        + rng.normal(0, 0.01, (n_members, 3, len(soc)))
    x = np.linspace(0, 1.2, 49)
    pd_up = np.stack([x - x.mean() + rng.normal(0, 0.002, len(x)) for _ in range(n_members)])
    sf = dict(n_members=n_members, calendar=dict(soc=soc, E_kJmol=dict(mean=E.mean(0).tolist(), lo=E.min(0).tolist(), hi=E.max(0).tolist()),
                                                 a_pp500=dict(mean=[1.0] * len(soc), lo=[1.0] * len(soc), hi=[1.0] * len(soc)), **({"A10_E_kJmol": 62.0} if a10 else {})),
              storage_rate=dict(T_C=[10, 23, 45], soc=soc, mean=r.mean(0).tolist(), lo=r.min(0).tolist(), hi=r.max(0).tolist()),
              arrhenius={}, cyclic={"c_ch": dict(x=x.tolist(), A1=dict(mean=pd_up.mean(0).tolist(), lo=pd_up.min(0).tolist(), hi=pd_up.max(0).tolist()), **({"A10": dict(mean=(x - x.mean()).tolist())} if a10 else {}))},
              members={"E_kJmol": E.tolist(), "a_pp500": [[1.0] * len(soc)] * n_members, "storage_rate": r.tolist(), "arrhenius_ln_rate": [], "cyclic.c_ch": pd_up.tolist()})
    d = tmp_path / name
    d.mkdir()
    json.dump(sf, open(d / "stress_functions.json", "w"))
    json.dump({"dataset": "synthetic"}, open(d / "config.json", "w"))
    pd.DataFrame(dict(cell_id=["a", "b", "c", "d"], cond=["x", "x", "y", "y"], arm=["A1"] * 4, share_cal=[0.2, 0.4, 0.9, 1.3], cal_exceeds_total=[False, False, False, True])).to_csv(d / "superposition.csv", index=False)
    return str(d)


def test_soc_turning_detects_a_peak_above_80_and_nothing_below():
    soc = np.arange(0, 101, 5.0)
    r = np.minimum(soc, 90.0) - 0.5 * np.maximum(soc - 90.0, 0.0)                                      # rises to 90 %, falls after
    assert h7 is not None and physval.soc_turning(soc, r) == [(90.0, "peak")]
    r2 = np.minimum(soc, 60.0) - 0.5 * np.maximum(soc - 60.0, 0.0)                                       # the peak is at 60 %: below the 80 % start, not reported
    assert physval.soc_turning(soc, r2) == []
    assert physval.soc_turning(soc, soc.astype(float)) == []


def test_physval_items_on_constructed_stress_function_files(tmp_path, monkeypatch):
    monkeypatch.setitem(semi.A10_FORM, "verified", False)               # the blocked-comparison mechanism (A10_FORM is True since FB-2 closed)
    a, b = _sf(tmp_path, "fold0"), _sf(tmp_path, "fold1")
    out = physval.physval_11a([a, b])
    assert out["n_members"] == 6 and out["item1"]["activation_energy"]["n_members"] == 6
    ae = out["item1"]["activation_energy"]
    assert all(lo <= hi for lo, hi in zip(ae["E_kJmol"]["lo"], ae["E_kJmol"]["hi"])) and set(ae["at_selected_soc"]) == {"5", "50", "80", "100"}
    assert out["item1"]["published"]["status"].startswith("omitted")                                    # nothing is invented
    pt = out["item2"]["per_temperature"]
    assert set(pt) == {"10", "23", "45"} and pt["45"]["share_members_with_peak"] == 1.0 and pt["45"]["slope_sign_changes_above_80"] is True
    assert out["item4"]["arms"]["A1"]["n_cells"] == 8 and out["item4"]["arms"]["A1"]["n_calendar_exceeds_observed_total"] == 2
    di = out["item5"]["directions"]["c_ch"]
    assert di["share_increasing"] == 1.0 and di["share_monotone"] == 1.0 and di["n_members"] == 6
    # the A10 comparisons are blocked while the A10 form is unverified (FB-2): recorded, not guessed
    assert set(out["blocked"]) == {"item1a_vs_A10", "item5_vs_A10"} and "FB-2" in out["blocked"]["item5_vs_A10"]
    with pytest.raises(semi.UnverifiedArmError):
        physval.compare_with_a10_activation(physval.merge_stress_functions([a]))
    with pytest.raises(semi.UnverifiedArmError):
        physval.physval_11a([a], strict=True)


def test_physval_a10_comparisons_when_the_form_is_declared_verified(tmp_path, monkeypatch):
    a = _sf(tmp_path, "fold0")
    monkeypatch.setitem(semi.A10_FORM, "verified", True)
    out = physval.physval_11a([a])
    assert out["blocked"] == {} and out["item1"]["vs_A10"]["verdict"] in ("consistent", "not consistent") and out["item1"]["vs_A10"]["label"].startswith("consistency with the semi-empirical")
    assert out["item5"]["vs_A10"]["c_ch"]["verdict"] == "consistent"
    pub = [{"doi": "10.0000/placeholder", "location": "Table 1", "E_kJmol_range": [100.0, 120.0]}, {"doi": "", "location": "x", "E_kJmol_range": [1, 2]}]
    r = physval.compare_with_published(physval.merge_stress_functions([a]), pub)
    assert len(r["sources"]) == 1 and r["sources"][0]["overlaps"] is False                              # an item without a DOI is ignored


def test_storage_lab_composition_from_design_metadata(tmp_path):
    p = tmp_path / "meta.csv"
    pd.DataFrame(dict(type=["k", "k", "k", "k", "z"], cell=[1, 2, 3, 4, 1], amb_temp_tp=[10, 10, 45, 45, 23], lab=["SIE", "SIE", "HM", "HM", "INT"])).to_csv(p, index=False)
    assert physval.storage_lab_composition(str(p)) == {"10.0": {"SIE": 2}, "45.0": {"HM": 1}}          # cells 04-06 and cycling cells excluded


# ------------------------------------------------------------------------------------------------ run-level outputs and options
CFG = {"design": "V3_legacy", "dataset": "synthetic", "mode": "confirmatory", "test": "B", "n_trials": 1, "inner_k": 2, "steps_scale": 0.04, "seeds": [0, 1], "backbone": "self_limiting",
       "arms": ["A1", "A2", "A4", "A9", "A10", "R1", "R2"], "synthetic": {"kind": "G0", "n_cyc_cond": 12, "n_sto_cond": 4, "reps": 2, "seed": 4}}


@pytest.fixture(scope="module")
def build2_runs(tmp_path_factory):
    d = tmp_path_factory.mktemp("b2")
    run.run({**CFG, "run_id": "base"}, runs_dir=str(d))
    run.run({**CFG, "run_id": "min3", "min_fc_points": 3}, runs_dir=str(d))
    run.run({**CFG, "run_id": "tau", "arms": ["A2"], "law_overrides": {"tau": 0.3, "Y0": 2.0}}, runs_dir=str(d))
    return d


def test_confirmatory_run_writes_cell_scores_and_condition_meta(build2_runs):
    d = build2_runs / "base"
    cs = json.load(open(d / "cell_scores.json"))
    cm = json.load(open(d / "condition_meta.json"))
    scores = json.load(open(d / "condition_scores.json"))
    assert set(cs) == set(CFG["arms"]) and set(cm) == set(scores["A2"])
    for cond, e in cm.items():
        cells = [r for r in cs["A2"].values() if r["cond"] == cond]
        assert e["n_cells"] == len(cells) and sum(e["lab"].values()) == e["n_cells"]
        assert scores["A2"][cond] == pytest.approx(np.mean([r["rmse_pp"] for r in cells]))             # the condition score is the mean of its cell scores


def test_min_fc_points_restricts_only_the_scored_cells(build2_runs):
    base = json.load(open(build2_runs / "base" / "cell_scores.json"))["A2"]
    m3 = json.load(open(build2_runs / "min3" / "cell_scores.json"))["A2"]
    assert set(m3) <= set(base) and all(r["n_fc"] >= 3 for r in m3.values())
    assert json.load(open(build2_runs / "min3" / "config.json"))["min_fc_points"] == 3


def test_law_overrides_run_a2_only_and_restore_the_constants(build2_runs):
    from pinnkan import law
    assert (law.Y0, law.TAU, law.DELTA_SCOPE) == (1.0, 0.15, "term")
    assert json.load(open(build2_runs / "tau" / "config.json"))["law_overrides"] == {"tau": 0.3, "Y0": 2.0}
    s0 = json.load(open(build2_runs / "base" / "condition_scores.json"))["A2"]
    s1 = json.load(open(build2_runs / "tau" / "condition_scores.json"))["A2"]
    assert s0 != s1                                                                                      # the override reached the fit


def test_run_stats_writes_sensitivity_and_physval_files(build2_runs, tmp_path, monkeypatch):
    monkeypatch.setitem(semi.A10_FORM, "verified", False)               # these runs have no A10 arm; the blocked record is the unverified-form mechanism
    out = tmp_path / "an"
    st.run_stats(str(out), {"B": [str(build2_runs / "base")]}, physval_runs=[str(build2_runs / "base")])
    s = json.load(open(out / "sensitivity_B.json"))
    assert s["availability"]["condition_meta"] and s["availability"]["cell_scores"]
    c = json.load(open(out / "contrasts_B.json"))["contrasts"]
    assert c["H3"]["comp"] == "A4" and c["H3"]["g2_passes"] is None and c["H3"]["outcome"] != "win"       # only A4 ran; no H7 batch given: the KAN 'win' is unavailable
    pv = json.load(open(out / "physval_11a.json"))                                                       # end to end: the run writer's `members` block feeds 11a
    assert pv["n_members"] == 2 and pv["item2"]["per_temperature"]["23"]["n_members"] == 2 and pv["item4"]["arms"]["A1"]["n_cells"] > 0
    assert set(pv["blocked"]) == {"item1a_vs_A10", "item5_vs_A10"}


def test_h7_mode_shards_share_one_run_directory_and_resume(tmp_path):
    base = {"run_id": "h7b", "dataset": "synthetic", "mode": "h7", "h7": {"gens": ["G0"], "n_draws": 2, "arms": ["A2"], "n_trials": 1, "inner_k": 2, "steps_scale": 0.04,
                                                                       "design": {"n_cyc_cond": 10, "n_sto_cond": 4, "reps": 2}, "resume": True}}
    d = run.run({**base, "h7": {**base["h7"], "shard": [0, 2]}}, runs_dir=str(tmp_path))
    assert not os.path.exists(os.path.join(d, "summary.json"))
    run.run({**base, "h7": {**base["h7"], "shard": [1, 2]}}, runs_dir=str(tmp_path))                 # a second process on the same directory: allowed with resume
    assert json.load(open(os.path.join(d, "summary.json")))["complete"] is True
    assert os.path.exists(os.path.join(d, "config.json")) and os.path.exists(os.path.join(d, "config_shard1of2.json"))
    with pytest.raises(FileExistsError):
        run.run({**base, "h7": {k: v for k, v in base["h7"].items() if k != "resume"}}, runs_dir=str(tmp_path))     # without resume the directory is still protected


def test_synthetic_design_of_the_h7_batch_has_unique_conditions_for_all_60_draws():
    for seed in (0, 7, 18, 19):                                                    # seed 18 produced a duplicate storage point at 40 + 19 conditions before the de-duplication
        cyc, sto, reps = synth.make_design(40, 19, 3, seed)
        assert len(set(cyc)) == 40 and len(set(sto)) == 19 and reps == 3
        assert all(0.0 < soc <= 1.0 for _, soc in sto)
    S = synth.make_synthetic("G2", seed=18, n_cyc_cond=40, n_sto_cond=19, reps=3)
    assert len({c.cond for c in S.cells}) == 59


def test_gate_g_v4_is_nc1_and_pc1_only_and_pc2_pc3_are_reported():
    ok = {"negative": {"nc1": {"passed": True}}, "positive": {"P1_G0_nrmse_leq_0p15": True, "P2_monotone_in_T": False, "P3_passed": False}}
    g = st.gate_g(ok)
    assert g["tripped"] is False and g["reasons"] == [] and g["not_evaluated"] == [] and g["reported_checks"]["PC-2_calendar_rate_monotone_in_T"] is False        # PC-2 / PC-3 failing is not a gate input
    assert st.gate_g({"negative": {"nc1": {"passed": True}}, "positive": {"P1_G0_nrmse_leq_0p15": False}})["reasons"] == ["PC-1 failed (G0 pipeline check: nRMSE > 0.15)"]
    assert st.gate_g({"negative": {"nc1": {"passed": False}}, "positive": {"P1_G0_nrmse_leq_0p15": True}})["reasons"] == ["NC-1 tripped"]
    g2 = st.gate_g({"negative": {"nc1": {"passed": True}}, "positive": {}})
    assert not g2["tripped"] and g2["not_evaluated"] == ["PC-1"]


def test_gate_g_collects_nc1_and_the_positive_controls():
    ok = {"negative": {"nc1": {"passed": True}}, "positive": {"P1_passed": True, "P2_monotone_in_T": True, "P3_passed": True}}
    assert st.gate_g_v3(ok)["tripped"] is False and st.gate_g_v3(ok)["not_evaluated"] == [] and st.gate_g_v3(ok)["reasons"] == []
    bad = {"negative": {"nc1": {"passed": True}}, "positive": {"P1_passed": False, "P2_monotone_in_T": True, "P3_passed": True}}
    assert st.gate_g_v3(bad)["tripped"] and st.gate_g_v3(bad)["reasons"] == ["positive control P1 failed"]
    trip = {"negative": {"nc1": {"passed": False}}, "positive": {"P1_passed": True, "P2_monotone_in_T": True, "P3_passed": True}}
    assert st.gate_g_v3(trip)["tripped"] and "NC-1 tripped" in st.gate_g_v3(trip)["reasons"]
    pend = {"negative": {"nc1": {"passed": True}}, "positive": {"P1_passed": None, "P2_monotone_in_T": True}}
    g = st.gate_g_v3(pend)
    assert g["tripped"] is False and g["not_evaluated"] == ["P1", "P3"]                                       # unevaluated is neither tripped nor cleared


def test_p3_and_gate_are_written_to_controls_json(build2_runs, tmp_path):
    out = tmp_path / "an2"
    st.run_stats(str(out), {"B": [str(build2_runs / "base")]})
    ctl = json.load(open(out / "controls.json"))
    assert isinstance(ctl["positive"]["P3_passed"], bool) and ctl["gate_G"]["not_evaluated"] == ["PC-1"]
    assert ctl["gate_G"]["rule"].startswith("PREREG_v4 gate G")


# build_v2 item 6: the lab-and-stage-indicator row is built (it was a hard error here); tests in test_pk_v2_rows.py


def test_cells_with_two_points_do_not_break_a_fit(tmp_path):
    # storage cells 04-06 enter as two-point records in the sensitivity row: a fit must tolerate a cell with a single post-reference point
    from pinnkan import tuning
    from pinnkan.arms import make_arm
    from pinnkan.data import WindowRule
    S = synth.make_synthetic("G0", n_cyc_cond=8, n_sto_cond=4, reps=2, seed=3)
    cells = []
    for c in S.cells:
        if c.kind == "storage" and not cells:
            import dataclasses
            c = dataclasses.replace(c, t=c.t[:2], ret=c.ret[:2], efc=c.efc[:2], fc_ok=c.fc_ok[:2])
            cells.append(c)
        else:
            cells.append(c)
    spec = h7.SPEC
    ctx = {"backbone": "self_limiting", "steps_scale": 0.04, "rule": WindowRule.for_spec(spec)}
    for a in ("A1", "A2"):
        arm = make_arm(a, spec, tuning.ARM_DEFAULTS[a] if hasattr(tuning, "ARM_DEFAULTS") else __import__("pinnkan.arms", fromlist=["default_hp"]).default_hp(a), 0, ctx).fit(cells)
        assert arm.n_params > 0
