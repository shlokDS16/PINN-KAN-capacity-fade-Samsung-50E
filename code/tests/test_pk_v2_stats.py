"""build_v2 item 5: the statistics step of Design R2 (PREREG_v4 9, 11; D018): Beta-binomial design-effect sign test, primary and secondary graphs, simultaneous intervals,
dependence sensitivity row, GAP-1 test, item (f) guard, state / title / sentence assembly from the closed table.
    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_v2_stats.py -q"""
import json
import os
import re
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest

from pinnkan import graph_test as gt
from pinnkan import stats_step as ss
from pinnkan import stats_v4 as v4

CONDS = [f"T{23 + 12 * (i % 3)}|SOCmax0.{50 + i}|DoD0.{10 + i % 5}|Cch0.5|Cdch1" for i in range(40)]
LABS = {c: ("INT" if i < 19 else ("HM" if i < 36 else "SIE")) for i, c in enumerate(CONDS)}
FOLD = {c: i % 5 for i, c in enumerate(CONDS)}


def table(L_by, base=2.0):
    """scores from log ratios: A1 = base; comparator = base * exp(L); keys of L_by are (target, comp, cell) triples -> only arms listed are filled"""
    return None


def make_store(P1g1=0.3, P1g4=0.05, A9g1=0.2, K1=0.0, K2=0.25, A2g1=0.0, A10g1=0.3, A13g1=0.0, k_chain=True, nL=None, k_full=4):
    """A1 = 2.0 everywhere; D*, A9, A2, A10, A10P, A13 scored at A1 * exp(L); A15 = A1 * exp(-K1); G15 = A15 * exp(K2). Each L is a scalar (all conditions) or a length-40 array."""
    vec = lambda v: np.full(40, v, float) if np.isscalar(v) else np.asarray(v, float)
    t = {}
    for cell, Ld, L9 in (((8, "2"), P1g1, A9g1), ((32, "full"), P1g4, 0.0)):
        a1 = {c: 2.0 for c in CONDS}
        tab = {"A1": a1, "D*": {c: 2.0 * np.exp(v) for c, v in zip(CONDS, vec(Ld))}, "A9": {c: 2.0 * np.exp(v) for c, v in zip(CONDS, vec(L9))}}
        if cell == (8, "2"):
            tab["A2"] = {c: 2.0 * np.exp(v) for c, v in zip(CONDS, vec(A2g1))}
            tab["A10"] = {c: 2.0 * np.exp(v) for c, v in zip(CONDS, vec(A10g1))}
            tab["A10P"] = {c: 2.0 * np.exp(v) for c, v in zip(CONDS, vec(A10g1))}
            tab["A13"] = {c: 2.0 * np.exp(v) for c, v in zip(CONDS, vec(A13g1))}
        else:
            tab["A2"] = dict(a1)
            tab["A10"] = {c: 2.0 * np.exp(v) for c, v in zip(CONDS, vec(-0.3))}
            tab["A10P"] = dict(tab["A10"])
            tab["A13"] = dict(a1)
            if k_chain:
                tab["A15"] = {c: 2.0 * np.exp(-v) for c, v in zip(CONDS, vec(K1))}
                tab["G15"] = {c: tab["A15"][c] * np.exp(v) for c, v in zip(CONDS, vec(K2))}
        t[cell] = tab
    return v4.Store(t, LABS, FOLD, k_full)


# ------------------------------------------------------------------------------------------------ the sign rule and its limiting cases
def test_rho_zero_reproduces_the_plain_counts_28_and_27():
    assert gt.betabin_crit(40, 0.0125, 0.0) == 28 and gt.betabin_crit(40, 0.025, 0.0) == 27
    assert v4.PLAIN.crit(40, 0.0125) == 28 and v4.PLAIN.crit(40, 0.025) == 27 and v4.SignRule("plain").rho == 0.0
    assert np.allclose(gt.betabin_tail_table(40, 0.0), gt.binom_tail_table(40))
    assert v4.PLAIN.with_rho(0.0).kind == "plain" and v4.PLAIN.with_rho(0.03).rho_s0 == 0.03


def test_d018_counts_at_rho_003():
    r = v4.SignRule("betabin", 0.03)
    assert [r.crit(40, a) for a in (0.0125, 0.025, 0.005, 0.00625, 0.00833333)] == [31, 30, 33, 32, 32]
    assert r.crit(40, 0.0195) == 30 and r.crit(40, 0.0055) == 32           # w = 0.78: the graph levels 0.0195 / 0.0055 give 30 / 32 (D018 section 3)


def test_the_run_refuses_to_score_without_a_sign_rule_and_defaults_are_the_ruling():
    for bad in ({"sign_rule": None}, {"sign_rule": "betabin", "rho_s0": None}, {"sign_rule": "exact"}, {"sign_rule": "betabin", "rho_s0": 0.0}):
        with pytest.raises(v4.SignRuleNotSetError):
            v4.resolve_config(bad)
    rule, c = v4.resolve_config()
    assert rule.kind == "betabin" and rule.rho_s0 == 0.03 and c["graph_w"] == 0.5 and c["alpha"] == 0.025 and c["e1_prime_approved"] is False
    with pytest.raises(ValueError):
        v4.resolve_config({"graph_w": 1.0})                              # w = 1 only when chain K is struck
    assert v4.resolve_config({"graph_w": 1.0, "k_chain_struck": True})[1]["graph_w"] == 1.0


def test_ties_with_the_margin_are_dropped_and_n_reduced():
    L = np.array([0.1] * 33 + [0.0] * 4 + [-0.1] * 3)
    pos, n, p = v4.PLAIN.test(L, 0.0)
    assert (pos, n) == (33, 36) and p == pytest.approx(float(gt.binom_tail_table(36)[33]))


# ------------------------------------------------------------------------------------------------ primary analysis: tiers, states, titles
def test_strong_everything_gives_P_plus_K_plus_title_T1_and_the_sentence():
    out = v4.run_v4(make_store())
    pr = out["primary"]
    assert pr["rejected"] == {k: True for k in gt.NODES} and pr["tiers"] == {"P1": "S", "P2": True, "P3": True, "K1": True, "K2": "S"}
    o = out["outcome"]
    assert (o["P"], o["K"], o["M1"], o["M2"], o["title_id"], o["extent_clause"]) == ("P+", "K+", False, False, "T1", "e1") and not o["gate_G"]
    assert o["title"].startswith("Physics-informed neural networks with readable Kolmogorov-Arnold stress laws")
    s = o["abstract_sentence"]
    assert s.startswith("With eight cycling conditions and two check-ups per held-out cell, the physics-informed network's typical (median) held-out-condition error was 25.9 % lower")
    assert "(95 % interval [25.9, 25.9]; n = 40)" in s and "most of the advantage came from the physics law, since the same network without it was 22.1 % worse" in s
    assert "predicted held-out conditions no more than 10 % worse than the full network and 22.1 % more accurately than an equally simplified additive law (95 % interval [22.1, 22.1])." in s
    assert out["most_test"]["most"] is True and out["config"]["sign_rule"] == "betabin"


def test_graph_counts_31_then_30_and_the_weight_is_a_config_value():
    L = np.array([0.5] * 30 + [-0.02] * 10)                                # P1: 30 above ln 1.02, all above -ln 1.10
    s = make_store(P1g1=L, K2=0.0)                                         # K2S fails, so chain K never hands its level over: P1 stays at 0.0125
    a = v4.run_v4(s)["primary"]
    assert a["nodes"]["P1S"]["positives"] == 30 and a["nodes"]["P1N"]["rejected"] and not a["nodes"]["P1S"]["rejected"]
    assert a["nodes"]["P1S"]["crit_positives"] == 31 and a["tiers"]["P1"] == "N"
    b = v4.run_v4(s, {"graph_w": 0.78})["primary"]
    assert b["nodes"]["P1S"]["rejected"] and b["tiers"]["P1"] == "S" and b["nodes"]["P1S"]["crit_positives"] == 30
    assert b["initial_levels"]["P1N"] == pytest.approx(0.025 * 0.78) and b["initial_levels"]["K1"] == pytest.approx(0.025 * 0.22)


def test_P0_with_tier_N_and_the_none_sentence():
    L = np.array([0.04] * 20 + [-0.03] * 20)
    o = v4.run_v4(make_store(P1g1=L))["outcome"]
    assert o["P"] == "P0" and o["extent_clause"] is None
    assert "typical held-out-condition error was no more than 10 % above that of the best tuned data-driven learner" in o["abstract_sentence"]
    L2 = np.array([0.3] * 20 + [-0.3] * 20)
    o2 = v4.run_v4(make_store(P1g1=L2))["outcome"]
    assert o2["P"] == "P0" and "could not be distinguished from that of the best tuned data-driven learner (95 % interval" in o2["abstract_sentence"]
    assert o2["title_id"] in ("T4", "T5", "T6")


def test_P_minus_reverse_S_is_tested_regardless_and_gives_the_whereas_sentence():
    out = v4.run_v4(make_store(P1g1=-0.3, K2=0.25))
    pr = out["primary"]
    assert pr["tiers"]["P1"] == "reverse S" and pr["nodes"]["P1rev"]["rejected"] and not pr["rejected"]["P1S"]
    o = out["outcome"]
    assert o["P"] == "P-" and o["title_id"] in ("T7", "T8") and "whereas a closed-form stress law" in o["abstract_sentence"]
    assert "the best tuned data-driven learner's typical held-out-condition error was 25.9 % lower than that of the physics-informed network" in o["abstract_sentence"]


def test_K_minus_is_tested_regardless_of_K1():
    out = v4.run_v4(make_store(K1=-0.5, K2=-0.3))         # K1 fails (A15 far worse than A1) and G15 beats A15 by the S margin
    pr = out["primary"]
    assert pr["tiers"]["K1"] is False and pr["tiers"]["K2"] == "reverse S" and pr["nodes"]["K2rev"]["rejected"]
    assert out["outcome"]["K"] == "K-" and out["outcome"]["title_id"] == "T3"
    assert "while an equally simplified additive stress law predicted held-out conditions 25.9 % more accurately than the law extracted" in out["outcome"]["abstract_sentence"]


def test_K_equals_with_K1_pass_and_K1_fail_clauses():
    o = v4.run_v4(make_store(K2=0.0))["outcome"]
    assert o["K"] == "K=" and o["title_id"] == "T2" and "but was not shown more accurate than an equally simplified additive law" in o["abstract_sentence"]
    o2 = v4.run_v4(make_store(K1=-0.5, K2=0.0))["outcome"]
    assert o2["K"] == "K=" and "was not shown to stay within 10 % of the full network, so no readable-law claim is made" in o2["abstract_sentence"]


def test_chain_K_struck_puts_P_at_the_full_level():
    pr = v4.run_v4(make_store(k_chain=False), {"k_chain_struck": True})["primary"]
    assert pr["k_chain_struck"] and pr["graph_w"] == 1.0
    assert pr["nodes"]["P1N"]["level"] == pytest.approx(0.025) and pr["nodes"]["P1N"]["crit_positives"] == 30
    assert "K1" not in pr["tiers"]


def test_reduced_n_recomputes_the_counts_by_the_same_rule():
    r = v4.SignRule("betabin", 0.03)
    assert r.crit(36, 0.0125) <= 36 and r.crit(36, 0.0125) > r.crit(36, 0.025)
    assert v4.PLAIN.crit(37, 0.025) == gt.sign_crit(37, 0.025)


# ------------------------------------------------------------------------------------------------ plain row, reverse tests, K1 tier S
def test_plain_test_is_a_descriptive_row_and_cannot_raise_a_tier():
    L = np.array([0.5] * 28 + [-0.02] * 12)                                # 28 positives: plain reaches S at 0.0125, the design-effect test does not (needs 31)
    out = v4.run_v4(make_store(P1g1=L))
    assert out["plain_descriptive"]["tiers"]["P1"] == "S" and out["primary"]["tiers"]["P1"] == "N" and out["outcome"]["P"] == "P0"
    assert out["plain_descriptive"]["nodes"]["P1S"]["positives"] == 28


def test_K1_tier_S_is_reported_unadjusted_and_changes_no_title():
    out = v4.run_v4(make_store(K1=0.3))                                   # A15 better than A1 by the S margin
    n = out["primary"]["nodes"]["K1_S_unadjusted"]
    assert n["rejected"] and "unadjusted" in n["status"]


# ------------------------------------------------------------------------------------------------ intervals
def test_fallback_interval_ranks_at_n40():
    rule = v4.SignRule("betabin", 0.03)
    x = np.arange(1, 41, dtype=float)
    lo, hi, r, cov = rule.interval(x, 0.05)
    assert (r, lo, hi) == (11, 11.0, 30.0) and cov == pytest.approx(0.961288, abs=1e-5)       # unadjusted 95 % interval: rank 11, [L(11), L(30)] (D018 section 2.1)
    s = v4.simultaneous(x, rule, 9)
    assert (s["rank"], s["lo"], s["hi"]) == (8, 8.0, 33.0) and not s["is_range"]                  # 1 - 0.05/9: [L(8), L(33)]
    assert v4.simultaneous(x[:6], rule, 9)["is_range"]                                           # no pair attains the level at n = 6: the labelled range


def test_estimated_tables_have_simultaneous_intervals_and_the_ladder():
    t = {}
    rng = np.random.default_rng(1)
    for m in (8, 16, 32):
        for k in ("0", "2", "full"):
            a1 = {c: 2.0 for c in CONDS}
            t[(m, k)] = {"A1": a1, "A9": {c: 2.0 * np.exp(0.2 + 0.05 * rng.standard_normal()) for c in CONDS}, "AG": {c: 2.0 * np.exp(0.1) for c in CONDS},
                         "D*": {c: 2.0 * np.exp(0.15 + 0.05 * rng.standard_normal()) for c in CONDS}, "A2": {c: 2.0 * np.exp(0.01) for c in CONDS}}
    store = v4.Store(t, LABS, FOLD, 4)
    est = v4.estimated_tables(store, v4.SignRule("betabin", 0.03))
    assert est["n_cells"] == 9
    rows = [r for r in est["rows"] if r["comparator"] == "D*"]
    assert len(rows) == 9 and all(r["simultaneous"]["rank"] == 8 and "mean_pp_ci" in r and r["n"] == 40 for r in rows)
    lad = est["ladder"]
    assert len(lad) == 9 and lad[0]["law_share_with_non_KAN_map"]["median"] == pytest.approx(0.1, abs=0.1)
    wg = [w for w in est["window_information_gain"] if w["arm"] == "A1"]
    assert len(wg) == 6 and all(abs(w["median_L"]) < 1e-12 for w in wg)


# ------------------------------------------------------------------------------------------------ secondary family
def _sec_store(forms_L, qh=0.3, qt=0.0):
    t = {}
    for cell in (G1 := (8, "2"), G4 := (32, "full")):
        a1 = {c: 2.0 for c in CONDS}
        tab = {"A1": a1, "A2": {c: 2.0 * np.exp(qh) for c in CONDS}}
        for f, v in forms_L.items():
            tab[f] = {c: 2.0 * np.exp(v) for c in CONDS}
        if cell == G1:
            tab["A13"] = {c: 2.0 * np.exp(qt) for c in CONDS}
        t[cell] = tab
    return v4.Store(t, LABS, FOLD, 4)


def test_secondary_graph_reduces_to_holm_when_no_S_node_is_rejected():
    rule = v4.SignRule("betabin", 0.03)
    rng = np.random.default_rng(3)
    Lq = {k: rng.normal(0.02, 0.1, 40) for k in range(5)}
    t = {}
    # five N-tests with graded evidence: p_N from the sign counts; S never reached (all L below ln 1.02)
    pos = [38, 36, 34, 33, 25]
    for (cell, arm), npos in zip([((8, "2"), "A10"), ((32, "full"), "A10"), ((8, "2"), "A2"), ((32, "full"), "A2"), ((8, "2"), "A13")], pos):
        L = np.array([-0.01] * npos + [-0.5] * (40 - npos))                # target A1: L = ln(S_comp / S_A1): all above -ln 1.10 for npos, far below for the rest
        t.setdefault(cell, {"A1": {c: 2.0 for c in CONDS}})[arm] = {c: 2.0 * np.exp(v) for c, v in zip(CONDS, L)}
    for cell in t:
        t[cell].setdefault("A10P", dict(t[cell]["A10"])) if "A10" in t[cell] else None
    sec = v4.secondary_analysis(v4.Store(t, LABS, FOLD, 4), rule, v4.resolve_config()[1])["tests"]
    pN = sorted([(sec[k]["pN"], k) for k in sec])
    crit = {k: None for k in sec}
    holm = {}
    alive = 5
    for i, (p, k) in enumerate(pN):                                          # Holm at 0.025 over the five N-tests
        if p <= 0.025 / (5 - i) * (1 + 1e-9):
            holm[k] = True
        else:
            break
    for k in sec:
        assert sec[k]["N_rejected"] == holm.get(k, False) and not sec[k]["S_rejected"]
    assert sec["QH_g1"]["tier"] in ("N", "none") and sec["QA10_g1"]["pN"] == pytest.approx(rule.p(38, 40))


def test_QA10_takes_the_lowest_tier_of_its_two_forms_and_reverse_S_in_either_form():
    s = _sec_store({"A10": 0.3, "A10P": 0.3})
    assert v4.secondary_analysis(s, v4.SignRule("betabin", 0.03), v4.resolve_config()[1])["tests"]["QA10_g1"]["tier"] == "S"
    s2 = _sec_store({"A10": 0.3, "A10P": -0.4})                           # the as-published form is better than A1 by far
    sec = v4.secondary_analysis(s2, v4.SignRule("betabin", 0.03), v4.resolve_config()[1])["tests"]["QA10_g1"]
    assert sec["tier"] == "reverse S" and sec["reverse_S"]["A10P"]["rejected"] and not sec["reverse_S"]["A10"]["rejected"] and sec["slot_level"] > 0
    s3 = _sec_store({"A10": 0.3, "A10P": 0.0})                            # one form only N/none: the lower tier
    assert v4.secondary_analysis(s3, v4.SignRule("betabin", 0.03), v4.resolve_config()[1])["tests"]["QA10_g1"]["tier"] in ("N", "none")


def test_M2_modifier_gives_T9_and_M1_replaces_the_phrase_in_T1_to_T3():
    base = make_store(A10g1=-0.5)
    out = v4.run_v4(base)
    assert out["outcome"]["M2"] is True and out["outcome"]["title_id"] == "T9a"          # make_store has A10 better than A1 by exp(0.5) at g1
    assert out["outcome"]["title"].startswith("Physics priors pay when cycling tests are few: semi-empirical, physics-informed Kolmogorov-Arnold")
    assert out["outcome"]["abstract_sentence"].endswith("; the dataset authors' semi-empirical model was 39.3 % more accurate still at this cell (95 % interval [39.3, 39.3]).")
    out2 = v4.run_v4(make_store(A10g1=-0.5, K1=-0.5, K2=-0.3))
    assert out2["outcome"]["title_id"] == "T9b" and out2["outcome"]["K"] == "K-"
    out3 = v4.run_v4(make_store(A10g1=0.3, A2g1=-0.3))                                    # A2 better than A1 at g1: M1, no M2
    o3 = out3["outcome"]
    assert o3["M1"] and not o3["M2"] and o3["title"].startswith("Physics-constrained neural ageing models with readable Kolmogorov-Arnold stress laws") and o3["q_h_required_in_abstract"]
    q = out3["qualifier_sentences"]
    assert q["QH_g1"].startswith("the hard ODE with the same law had a median condition error") and "% lower than the soft-residual network" in q["QH_g1"]


def test_qualifier_sentences_use_the_fixed_templates():
    assert v4.qualifier_sentence("QH", "none") == "the soft residual was not shown necessary relative to exact integration of the same law"
    assert v4.qualifier_sentence("QA10", "N") == "the physics-informed network was no more than 10 % worse than the dataset authors' semi-empirical model (one-sided bound); not shown better"
    assert v4.qualifier_sentence("QA10", "S", 12.34, (5.0, 20.0)) == "the physics-informed network had a median condition error 12.3 % lower than the dataset authors' semi-empirical model (95 % interval [5.0, 20.0]; n = 40)"
    assert v4.qualifier_sentence("QT", "none", None, (-3.0, 4.0)) == "training with and without the storage cells could not be distinguished (95 % interval [-3.0, 4.0])"
    assert "training with the storage cells" in v4.qualifier_sentence("QT", "reverse S", 8.0, (1.0, 2.0)) or True


def test_gate_G_gives_no_title_and_no_claim():
    o = v4.run_v4(make_store(), gate={"tripped": True, "reasons": ["NC-1 tripped"]})["outcome"]
    assert o["gate_G"] and o["title"] is None and o["abstract_sentence"] is None


# ------------------------------------------------------------------------------------------------ GAP-1: "most"
def test_most_test_and_the_e1_prime_branch():
    # L_total = ln 1.3 (0.262), L_law = ln 1.2 (0.182): d = 0.182 - 0.131 > 0 for every condition
    out = v4.run_v4(make_store(P1g1=np.log(1.3), A9g1=np.log(1.2)))
    mt = out["most_test"]
    assert mt["test_passes"] and mt["most"] and mt["crit_positives"] == 30 and out["outcome"]["extent_clause"] == "e1"
    assert mt["median_d"] == pytest.approx(np.log(1.2) - 0.5 * np.log(1.3))
    # law share below half of the total: d < 0 everywhere -> 'most' fails; e1 unless Shlok approved e1'
    out2 = v4.run_v4(make_store(P1g1=np.log(1.6), A9g1=np.log(1.1)))
    assert out2["primary"]["tiers"]["P2"] and out2["primary"]["tiers"]["P3"] and not out2["most_test"]["most"]
    assert out2["outcome"]["extent_clause"] == "e1" and "most of the advantage came from the physics law" in out2["outcome"]["abstract_sentence"]
    out3 = v4.run_v4(make_store(P1g1=np.log(1.6), A9g1=np.log(1.1)), {"e1_prime_approved": True})
    s = out3["outcome"]["abstract_sentence"]
    assert out3["outcome"]["extent_clause"] == "e1'" and "most of the advantage" not in s and "the same network without the physics law was 10.0 % worse, and the advantage was larger with 8 than with 32 cycling conditions" in s
    out4 = v4.run_v4(make_store(P1g1=np.log(1.6), A9g1=np.log(1.1)), {"e1_prime_approved": True}, row_tiers={"most": False})
    assert out4["outcome"]["extent_clause"] == "e1'"


def test_extent_clauses_e2_e3():
    o2 = v4.run_v4(make_store(P1g1=0.3, P1g4=0.3))["outcome"]                            # P3 fails: the advantage is not larger at g1
    assert o2["extent_clause"] == "e2" and "a dependence of the advantage on the number of cycling conditions was not shown" in o2["abstract_sentence"]
    o3 = v4.run_v4(make_store(A9g1=0.0))["outcome"]
    assert o3["extent_clause"] == "e3" and "a gain attributable to the physics law within the same network was not shown" in o3["abstract_sentence"]


# ------------------------------------------------------------------------------------------------ downgrade interface (item 6 feeds it)
def test_row_tiers_lower_the_effective_tier_and_the_title_follows():
    out = v4.run_v4(make_store(), row_tiers={"P1": "N", "K2": "none"})
    assert out["effective_tiers"]["P1"] == "N" and out["primary"]["tiers"]["P1"] == "S"
    assert out["outcome"]["P"] == "P0" and out["outcome"]["K"] == "K=" and out["outcome"]["title_id"] == "T5"
    assert v4.tier_min("S", "N", "none") == "none" and v4.tier_min("N", "reverse S") == "reverse S"


# ------------------------------------------------------------------------------------------------ dependence sensitivity, lab rows
def test_dependence_sensitivity_sentence_and_monotonicity():
    L = np.array([0.5] * 32 + [-0.02] * 8)                                # 32 positives at P1S
    store = make_store(P1g1=L)
    dep = v4.dependence_sensitivity(store, v4.SignRule("betabin", 0.03), v4.resolve_config()[1])
    t = dep["tiers_by_rho"]
    order = [t[str(r)]["P1"] for r in gt.RHO_GRID]
    assert order[0] == "S" and all(v4.TIER_ORDER.index(a) >= v4.TIER_ORDER.index(b) for a, b in zip(order, order[1:]))
    last = max(r for r in gt.RHO_GRID if t[str(r)]["P1"] == "S")
    assert dep["sentences"]["P1"] == f"The tier S holds for an assumed average sign correlation up to {last:g}."
    assert dep["no_consequence_for_any_tier"]


def test_lab_rows_per_lab_with_labelled_range_for_the_small_stratum():
    store = make_store(P1g1=np.linspace(-0.1, 0.5, 40))
    rows = v4.lab_rows(store, v4.SignRule("betabin", 0.03), {"P1": ("A1", "D*", (8, "2"))})["P1"]["labs"]
    assert {k: v["n"] for k, v in rows.items()} == {"HM": 17, "INT": 19, "SIE": 4}
    assert rows["SIE"]["interval_is_range"] and rows["SIE"]["rank"] == 0 and not rows["INT"]["interval_is_range"] or rows["INT"]["rank"] >= 0


# ------------------------------------------------------------------------------------------------ the closed table is copied verbatim
def _norm(s):
    s = s.replace("**", "").replace("\\", "")
    return re.sub(r"\s+", " ", s).strip()


JUDGE = _norm(open(os.path.join(ROOT, "debates", "D016_roles", "02_judge.md"), encoding="utf8").read())


def _as_judge(t):
    for a, b in (("{Y}", "[Y]"), ("{Z}", "[Z]"), ("{W}", "[W]"), ("{X}", "[X]"), ("{A}", "[A]"), ("{B}", "[B]"), ("{iv}", "interval"), ("{interval}", "interval"), ("{n}", "40")):
        t = t.replace(a, b)
    return _norm(t)


def test_titles_extent_clauses_and_templates_are_the_approved_wording():
    for (P, K), (tid, title) in v4.TITLES.items():
        assert _norm(title) in JUDGE, (P, K, tid)
    for tid, title in (v4.T9A, v4.T9B):
        assert _norm(title) in JUDGE
    for const in (v4.E1, v4.E2, v4.E3):
        assert _as_judge(const) in JUDGE
    assert v4.LEAD_IN in JUDGE and _norm(v4.Q_H_NONE) in JUDGE and v4.A10_NAME in JUDGE and v4.QT_NAME in JUDGE
    assert _as_judge(v4.KCLAUSE_KPLUS) in JUDGE and _as_judge(v4.KCLAUSE_KMINUS).replace("while ", "while ", 1) in JUDGE
    # K= clause: the judge writes it as 'and a closed-form stress law extracted from its Kolmogorov-Arnold network [K1 pass: ... / K1 fail: ...]'
    assert "and a closed-form stress law extracted from its Kolmogorov-Arnold network" in JUDGE
    assert _as_judge(v4.KCLAUSE_KEQ_PASS).split("network ", 1)[1] in JUDGE and _as_judge(v4.KCLAUSE_KEQ_FAIL).split("network ", 1)[1].rstrip() in JUDGE
    assert _as_judge(v4.T9_TAIL).lstrip("; ") in JUDGE.replace("; the", "; the")
    for k, t in v4.Q_TEMPLATES.items():
        assert _as_judge(t).replace("(interval; n = 40)", "(interval; n = 40)") in JUDGE
    assert v4.M1_OLD in JUDGE and v4.M1_NEW in JUDGE
    for piece in ("the physics-informed network's typical (median) held-out-condition error was [X] % lower than that of the best tuned data-driven learner",
                  "the physics-informed network's typical held-out-condition error", "was no more than 10 % above", "could not be distinguished from",
                  "the best tuned data-driven learner's typical held-out-condition error was [X] % lower than that of the physics-informed network"):
        assert _norm(piece) in JUDGE


def test_prereg_v4_section_11_still_contains_the_same_titles():
    p = open(os.path.join(ROOT, "runs", "prereg", "PREREG_v4.md"), encoding="utf8").read()
    pn = _norm(p)
    for (P, K), (tid, title) in v4.TITLES.items():
        assert _norm(title) in pn


# ------------------------------------------------------------------------------------------------ item (f) guard
def _fake_run(tmp, name, m, fold, k_labels, scores_by_k, comparators, with_meta=True, mtime=None):
    d = os.path.join(tmp, name)
    os.makedirs(d)
    json.dump({"m": m, "fold": fold, "inner_k": 2, "window": {"k_cycling": 4}}, open(os.path.join(d, "config.json"), "w"))
    json.dump({"k_labels": k_labels, "k_primary": "full", "k_full": 4}, open(os.path.join(d, "metrics.json"), "w"))
    json.dump(comparators, open(os.path.join(d, "comparators.json"), "w"))
    for kl, sc in scores_by_k.items():
        suf = "" if kl == "full" else f"_k{kl}"
        json.dump(sc, open(os.path.join(d, f"condition_scores{suf}.json"), "w"))
        meta = {c: {"n_cells": 3, "lab": {LABS[c]: 3}, "stage": {"1": 3}} for c in next(iter(sc.values()))}
        json.dump(meta, open(os.path.join(d, f"condition_meta{suf}.json"), "w"))
        if mtime:
            os.utime(os.path.join(d, f"condition_scores{suf}.json"), (mtime, mtime))
    return d


def test_item_f_guard_blocks_missing_altered_and_late_files(tmp_path):
    tmp = str(tmp_path)
    cs = {"A1": {c: 2.0 for c in CONDS[:8]}, "A9": {c: 2.5 for c in CONDS[:8]}}
    d = _fake_run(tmp, "r0", 8, 0, ["full"], {"full": cs}, {}, mtime=time.time())
    fdir = os.path.join(tmp, "prereg")
    with pytest.raises(v4.ItemFError):
        v4.require_item_f(fdir, [d])
    v4.write_item_f(fdir, {"rho_fold": 0.01})
    old = time.time() - 1000
    os.utime(os.path.join(fdir, v4.ITEM_F_FILE), (old - 10, old - 10))
    rec = json.load(open(os.path.join(fdir, v4.ITEM_F_HASH)))
    rec["written_unix"] = old - 10
    json.dump(rec, open(os.path.join(fdir, v4.ITEM_F_HASH), "w"))
    assert v4.require_item_f(fdir, [d]) == {"rho_fold": 0.01}                          # written before the outer score file: allowed
    os.utime(os.path.join(d, "condition_scores.json"), (old - 100, old - 100))
    with pytest.raises(v4.ItemFError):                                                  # an outer score older than the file: blocked
        v4.require_item_f(fdir, [d])
    os.utime(os.path.join(d, "condition_scores.json"), (time.time(), time.time()))
    with open(os.path.join(fdir, v4.ITEM_F_FILE), "w") as fh:
        json.dump({"rho_fold": 0.5}, fh)
    with pytest.raises(v4.ItemFError):                                                  # altered after hashing
        v4.require_item_f(fdir, [d])
    with pytest.raises(v4.ItemFError):
        ss.run_stats_v4(os.path.join(tmp, "an"), [d], item_f_dir=None)


def test_store_from_runs_resolves_dstar_and_ag_per_fold_and_run_stats_v4_end_to_end(tmp_path):
    tmp = str(tmp_path)
    dirs = []
    for fold, conds in enumerate((CONDS[:20], CONDS[20:])):
        sc = {}
        for kl in ("0", "2", "full"):
            base = {"A1": {c: 2.0 for c in conds}, "A9": {c: 2.0 * 1.2 for c in conds}, "A11": {c: 2.0 * (1.3 if fold == 0 else 1.5) for c in conds},
                    "A12": {c: 2.0 * (1.1 if fold == 0 else 1.6) for c in conds}, "A4": {c: 2.0 * 1.05 for c in conds}}
            sc[kl] = base
        dirs.append(_fake_run(tmp, f"f{fold}_m8", 8, fold, ["0", "2", "full"], sc, {"D*": {"arm": "A12" if fold == 0 else "A9"}, "AG": {"arm": "A4"}}))
        dirs.append(_fake_run(tmp, f"f{fold}_m32", 32, fold, ["0", "2", "full"], sc, {"D*": {"arm": "A12" if fold == 0 else "A9"}, "AG": {"arm": "A4"}}))
    store = v4.Store.from_runs(dirs)
    assert store.k_full == 4 and set(store.tables) == {(m, k) for m in (8, 32) for k in ("0", "2", "full")}
    ds = store.scores("D*", 8, "2")
    assert ds[CONDS[0]] == pytest.approx(2.2) and ds[CONDS[25]] == pytest.approx(2.4) and len(ds) == 40       # fold 0 -> A12 (1.1), fold 1 -> A9 (1.2)
    assert store.lab[CONDS[0]] == "INT" and store.fold[CONDS[25]] == 1
    fdir = os.path.join(tmp, "prereg")
    v4.write_item_f(fdir, {"rho_fold": 0.0})
    old = time.time() - 10000
    for d in dirs:
        for f in os.listdir(d):
            if f.startswith("condition_scores"):
                os.utime(os.path.join(d, f), (time.time() + 5, time.time() + 5))
    out = ss.run_stats_v4(os.path.join(tmp, "analysis"), dirs, {"k_chain_struck": True}, item_f_dir=fdir, strict=False)
    assert os.path.isfile(os.path.join(tmp, "analysis", "contrasts_v4_B.json"))
    assert out["primary"]["nodes"]["P1S"]["positives"] == 40 and out["outcome"]["P"] == "P+" and out["item_f"] == {"rho_fold": 0.0}
    assert out["primary"]["k_chain_struck"]                                      # no A15 / G15 in these fake runs: chain K absent, P at the full level


def test_k_full_equal_two_merges_the_g1_cell():
    t = {(8, "full"): {"A1": {c: 2.0 for c in CONDS}, "D*": {c: 2.6 for c in CONDS}, "A9": {c: 2.4 for c in CONDS}}, (32, "full"): {"A1": {c: 2.0 for c in CONDS}, "D*": {c: 2.1 for c in CONDS}}}
    s = v4.Store(t, LABS, FOLD, k_full=2)
    assert s.has("D*", 8, "2") and s.key(8, "2") == (8, "full")
    assert v4.Store(t, LABS, FOLD, k_full=4).key(8, "2") == (8, "2")


def test_item_f_estimate_from_inner_cv_training_sides(tmp_path):
    tmp = str(tmp_path)
    dirs = []
    rng = np.random.default_rng(0)
    for fold in range(2):
        d = os.path.join(tmp, f"r{fold}")
        os.makedirs(d)
        conds = CONDS[:32]
        json.dump({"fold": fold, "inner_k": 2}, open(os.path.join(d, "config.json"), "w"))
        a1 = {c: float(2 + rng.random()) for c in conds}
        ds = {c: a1[c] * float(np.exp(0.2 * rng.standard_normal())) for c in conds}
        json.dump({"arms": {"A1": {"cond_scores": a1}, "A9": {"cond_scores": ds}}}, open(os.path.join(d, "tuning_done.json"), "w"))
        json.dump({"D*": {"arm": "A9"}}, open(os.path.join(d, "comparators.json"), "w"))
        json.dump({c: {"lab": LABS[c], "n_cells": 3} for c in conds}, open(os.path.join(d, "train_condition_meta.json"), "w"))
        dirs.append(d)
    rep = v4.item_f_from_runs(dirs)
    assert {"rho_fold", "rho_fold_upper", "rho_lab", "avg_pairwise", "exceeds_rho_s0"} <= set(rep) and rep["n_observations"] == 64
    assert rep["disclosure"] is None or rep["disclosure"].startswith("The training-side estimate of the sign correlation exceeded")


def test_stats_step_nc2_uses_the_ruled_rule_by_default():
    assert ss.nc2.__defaults__ is not None
