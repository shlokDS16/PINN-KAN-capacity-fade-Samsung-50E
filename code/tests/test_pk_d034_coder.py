"""D034 coder batch (author decisions AD1, AD2, AD4, AD5 of D033; debates/D033_signoff/01_judge.md, AUTHOR DECISIONS; DECISIONS D034):
    AD1  P3 tests D_c = L_c(g1) - L_c(32, 2) (primary analysis, downgrade rows (ii)-(iv), lab-stratified row (i))
    AD2  modifier M3 = P+ and A1 not shown better than R1 (persistence) at g1 (margin 0, 30 of 40 at one-sided 0.025, outside the graph): T1-T3 and T9a/T9b become the K column's T4/T5/T6 with the added clause
    AD4  "when cycling tests are few" (T9a/T9b) only if P3 is S, otherwise "with few cycling tests";  AD5  "readable" -> "closed-form"
    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_d034_coder.py -q"""
import itertools
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest

from pinnkan import graph_test as gt
from pinnkan import stats_rows as R
from pinnkan import stats_v4 as v4
from test_pk_v2_stats import CONDS, FOLD, LABS, make_store

RULE = v4.resolve_config()[0]
CFG = v4.resolve_config()[1]


# ================================================================================================ AD1: P3 = L(g1) - L(32, 2)
def test_p3_is_the_g1_minus_32_2_contrast_and_g4_does_not_enter():
    s = make_store(P1g1=0.3, P1g32k2=0.3, P1g4=0.0)                            # same gain at g1 and (32, 2); a large "gain" at g4 would have passed the old contrast
    pr = v4.run_v4(s)["primary"]
    assert pr["nodes"]["P3"]["positives"] == 0 and not pr["rejected"]["P3"] and pr["tiers"]["P3"] is False
    s2 = make_store(P1g1=0.3, P1g32k2=0.0, P1g4=0.3)                           # the old contrast would give 0; the new one 0.3 for every condition
    pr2 = v4.run_v4(s2)["primary"]
    assert pr2["nodes"]["P3"]["positives"] == 40 and pr2["rejected"]["P3"] and pr2["tiers"]["P3"] is True
    L1 = np.linspace(0.1, 0.5, 40)
    s3 = make_store(P1g1=L1, P1g32k2=0.05, P1g4=0.2)
    conds, D = v4.p3_contrast(s3)
    assert conds == sorted(CONDS) and np.allclose(D, np.array([L1[CONDS.index(c)] for c in conds]) - 0.05)
    nodes, Ls = v4.primary_nodes(s3, RULE)
    assert np.allclose(Ls["P3"], D) and nodes["P3"]["label"] == "P3" and nodes["P3"]["margin"] == 0.0


def test_p3_needs_the_32_2_cell_and_g1_cell_only_and_follows_k_full_equal_two():
    s = make_store()
    del s.tables[(32, "2")]
    nodes, Ls = v4.primary_nodes(s, RULE)
    assert "P3" not in nodes and "P3" not in Ls and "P1N" in nodes                              # a store without (32, 2) has no P3 node (p = 1, never rejected)
    assert v4.run_v4(s)["primary"]["tiers"]["P3"] is False
    t = {(8, "full"): {"A1": {c: 2.0 for c in CONDS}, "D*": {c: 2.6 for c in CONDS}, "A9": {c: 2.4 for c in CONDS}, "R1": {c: 5.0 for c in CONDS}},
         (32, "full"): {"A1": {c: 2.0 for c in CONDS}, "D*": {c: 2.1 for c in CONDS}}}
    sk = v4.Store(t, LABS, FOLD, k_full=2)                                                     # k_full = 2: the (32, 2) cell IS the (32, full) cell
    conds, D = v4.p3_contrast(sk)
    assert np.allclose(D, np.log(1.3) - np.log(1.05))


def test_p3_contrast_in_the_downgrade_rows_uses_the_32_2_cell():
    first = v4.run_v4(make_store())
    row_bad = make_store(P1g1=0.3, P1g32k2=0.3, P1g4=0.0)                                      # (32, 2) as good as g1: P3 fails in this row
    assert R.row_tiers(first, row_bad, RULE)["P3"] is False
    row_good = make_store(P1g1=0.3, P1g32k2=0.0, P1g4=0.3)
    assert R.row_tiers(first, row_good, RULE)["P3"] is True
    no_cell = make_store()
    del no_cell.tables[(32, "2")]
    t = R.row_tiers(first, no_cell, RULE)
    assert "P3" not in t and "P1" in t                                                         # a row run without the (32, 2) cell does not cover P3 (it is not silently passed)
    assert "P3" not in R.row_tiers(first, row_bad, RULE, cells="g1")                           # row (iv) is g1 only


def test_p3_in_the_lab_stratified_row_uses_the_32_2_cell():
    primary = make_store()
    first = v4.run_v4(primary)
    t_ok, det = R.lab_stratified_tiers(first, primary, B=300)
    assert t_ok["P3"] is True and "P3" in det
    t_bad, _ = R.lab_stratified_tiers(first, make_store(P1g1=0.3, P1g32k2=0.3, P1g4=0.0), B=300)
    assert t_bad["P3"] is False
    t_g4, _ = R.lab_stratified_tiers(first, make_store(P1g1=0.3, P1g32k2=0.0, P1g4=0.3), B=300)
    assert t_g4["P3"] is True


# ================================================================================================ AD2: modifier M3
def _r1_store(n_pos, extra=0.0):
    """R1 worse than A1 by exp(0.5) in n_pos conditions and better than A1 by exp(0.2) in the others"""
    return make_store(R1g1=np.array([0.5] * n_pos + [-0.2] * (40 - n_pos)) + extra)


def test_m3_is_a_30_of_40_sign_test_at_one_sided_0025_outside_the_graph():
    for n_pos, expect in ((29, False), (30, True), (40, True), (0, False)):
        out = v4.run_v4(_r1_store(n_pos))
        node = out["primary"]["nodes"]["R1g1"]
        assert node["positives"] == n_pos and node["n"] == 40 and node["margin"] == 0.0 and node["level"] == 0.025 and node["crit_positives"] == 30
        assert node["rejected"] is expect and out["primary"]["tiers"]["R1_g1"] is expect
        assert out["outcome"]["M3"] is (not expect)                                             # P+ in every case here: M3 = the test is not rejected
        assert all(out["primary"]["rejected"][k] for k in gt.NODES)                             # the graph is untouched: P1S etc. are rejected whatever R1 does
        assert "R1g1" not in gt.NODES and out["primary"]["initial_levels"].keys() == set(gt.NODES)
    ties = make_store(R1g1=np.array([0.5] * 30 + [0.0] * 10))                                    # ties are not positive and n is not reduced (D033 D2)
    nd = v4.run_v4(ties)["primary"]["nodes"]["R1g1"]
    assert (nd["positives"], nd["n"]) == (30, 40) and nd["rejected"]


def test_m3_swaps_the_title_for_the_K_column_and_adds_the_clause():
    expect = {"K+": "T4", "K=": "T5", "K-": "T6"}
    stores = {"K+": dict(K2=0.25), "K=": dict(K2=0.0), "K-": dict(K1=-0.5, K2=-0.3)}
    for K, kw in stores.items():
        ok = v4.run_v4(make_store(**kw))["outcome"]
        m3 = v4.run_v4(make_store(R1g1=-0.2, **kw))["outcome"]
        assert ok["K"] == m3["K"] == K and ok["P"] == m3["P"] == "P+" and not ok["M3"] and m3["M3"]
        assert ok["title_id"] == {"K+": "T1", "K=": "T2", "K-": "T3"}[K]
        assert m3["title_id"] == expect[K] and m3["title"] == v4.TITLES[("P0", K)][1]
        assert m3["abstract_sentence"].endswith("; the physics-informed network was not shown more accurate than carrying the last check-up forward (95 % interval [-22.1, -22.1]).")
        assert m3["abstract_sentence"].startswith(ok["abstract_sentence"][:-1])               # the P+ sentence is kept; the clause is appended before the full stop
    assert "closed-form" in v4.run_v4(make_store(R1g1=-0.2))["outcome"]["title"].lower()          # T4 (K column), AD5


def test_m3_clause_interval_is_the_95_percent_interval_of_a1_against_r1_at_g1():
    L = np.array([0.4] * 25 + [-0.1] * 15)
    out = v4.run_v4(make_store(R1g1=L))
    o = out["outcome"]
    lo, hi, _, _ = RULE.interval(L, 0.05)
    iv = f"95 % interval [{v4.fmt1(v4.pct_reduction(lo))}, {v4.fmt1(v4.pct_reduction(hi))}]"
    assert o["M3"] and o["abstract_sentence"].endswith(f"carrying the last check-up forward ({iv}).") and o["number_sources"]["R1_g1"] == "primary"
    assert v4.pct_reduction(lo) < 0                                                              # "not shown more accurate": the interval does not lie above zero


def test_m3_never_applies_outside_P_plus_and_a_p_plus_without_r1_is_refused():
    base = dict(P1="N", P2=False, P3=False, K1=True, K2="none", QH_g1="none", QA10_g1="none")
    num = {"X": 20.0, "Y": 5.0, "Z": 10.0, "W": 3.0, "interval_P1": (10.0, 30.0), "interval_K2": (5.0, 15.0), "interval_R1": (-5.0, 8.0), "n": 40}
    for P1 in ("N", "none", "reverse S"):
        a = v4.assemble_outcome({**base, "P1": P1, "R1_g1": True}, num)
        b = v4.assemble_outcome({**base, "P1": P1, "R1_g1": False}, num)
        c = v4.assemble_outcome({**base, "P1": P1}, num)                                           # no R1 entry at all: fine, M3 does not exist outside P+
        assert a["title"] == b["title"] == c["title"] and a["abstract_sentence"] == b["abstract_sentence"] == c["abstract_sentence"]
        assert a["M3"] is False and b["M3"] is False and "carrying the last check-up forward" not in b["abstract_sentence"]
    with pytest.raises(v4.R1MissingError):
        v4.assemble_outcome({**base, "P1": "S", "P2": True}, num)
    s = make_store()
    for t in s.tables.values():
        t.pop("R1", None)
    with pytest.raises(v4.R1MissingError):
        v4.run_v4(s)
    out = v4.run_v4(make_store(P1g1=np.array([0.3] * 20 + [-0.3] * 20)))                           # P0: no R1 needed, and none in the P0 store here
    assert out["outcome"]["P"] == "P0" and not out["outcome"]["M3"]


def test_every_state_combination_maps_to_exactly_one_title_and_the_modifiers_act_as_ruled():
    num = {"X": 20.0, "Y": 5.0, "Z": 10.0, "W": 3.0, "interval_P1": (10.0, 30.0), "interval_K2": (5.0, 15.0), "interval_W": (1.0, 5.0), "interval_R1": (-5.0, 8.0), "n": 40}
    Ptier = {"P+": "S", "P0": "N", "P-": "reverse S"}
    Ktier = {"K+": (True, "S"), "K=": (True, "none"), "K-": (False, "reverse S")}
    seen = {}
    n_cases = 0
    for P, K, qh, qa, r1, p3, p2 in itertools.product(("P+", "P0", "P-"), ("K+", "K=", "K-"), ("none", "reverse S"), ("none", "reverse S"), (True, False), (True, False), (True, False)):
        k1, k2 = Ktier[K]
        tiers = dict(P1=Ptier[P], P2=p2, P3=p3, K1=k1, K2=k2, QH_g1=qh, QA10_g1=qa, R1_g1=r1)
        o = v4.assemble_outcome(tiers, num)
        n_cases += 1
        M1, M2, M3 = qh == "reverse S", P == "P+" and qa == "reverse S", P == "P+" and not r1
        assert (o["P"], o["K"], o["M1"], o["M2"], o["M3"]) == (P, K, M1, M2, M3)
        if M3:                                                                                       # P+ and R1 not rejected: the K column's T4 / T5 / T6, verbatim, with the clause
            assert o["title"] == v4.TITLES[("P0", K)][1] and o["title_id"] == {"K+": "T4", "K=": "T5", "K-": "T6"}[K]
            assert o["abstract_sentence"].count("carrying the last check-up forward") == 1
        else:
            assert "carrying the last check-up forward" not in o["abstract_sentence"]
            if M2:                                                                                   # T9a (K+, K=) / T9b (K-); AD4: "when ... few" only if P3 is S
                tid, title = (v4.T9B if K == "K-" else v4.T9A) if p3 else (v4.T9B_NOP3 if K == "K-" else v4.T9A_NOP3)
                assert (o["title_id"], o["title"]) == (tid, title) and ("when cycling tests are few" in title) == p3
            elif P == "P+":
                tid, title = v4.TITLES[("P+", K)]
                assert o["title_id"] == tid and o["title"] == (title.replace(v4.M1_OLD, v4.M1_NEW) if M1 else title)
            else:
                assert (o["title_id"], o["title"]) == v4.TITLES[(P, K)]
            assert "when" not in o["title"] or (M2 and p3)                                           # T8 "When a physics prior ..." is the one capital-W title
        seen.setdefault((P, K, M1, M2, M3, p3 if (M2 and not M3) else None), set()).add((o["title_id"], o["title"]))
        again = v4.assemble_outcome(tiers, num)
        assert again["title"] == o["title"] and again["abstract_sentence"] == o["abstract_sentence"]   # a function of the state
    assert n_cases == 3 * 3 * 2 * 2 * 2 * 2 * 2 and all(len(v) == 1 for v in seen.values())       # one title per state; p2 and the unused modifiers change no title


def test_the_m3_clause_follows_the_m2_tail_when_both_apply_and_m1_does_not_edit_the_k_column_title():
    num = {"X": 20.0, "Y": 5.0, "Z": 10.0, "W": 3.0, "interval_P1": (10.0, 30.0), "interval_K2": (5.0, 15.0), "interval_W": (1.0, 5.0), "interval_R1": (-5.0, 8.0), "n": 40}
    tiers = dict(P1="S", P2=True, P3=True, K1=True, K2="S", QH_g1="reverse S", QA10_g1="reverse S", R1_g1=False)
    o = v4.assemble_outcome(tiers, num)
    assert o["M1"] and o["M2"] and o["M3"] and o["title_id"] == "T4" and o["title"] == v4.TITLES[("P0", "K+")][1] and o["q_h_required_in_abstract"]
    s = o["abstract_sentence"]
    assert s.index("more accurate still at this cell") < s.index("carrying the last check-up forward") and s.endswith("(95 % interval [-5.0, 8.0]).")


# ---------------------------------------------------------------- the downgrade rows lower R1_g1 (a boolean: AND over the primary analysis and the rows)
def test_row_tiers_and_lab_stratified_row_cover_r1_at_g1_and_lower_the_modifier():
    primary = make_store()
    first = v4.run_v4(primary)
    assert first["primary"]["tiers"]["R1_g1"] is True and not first["outcome"]["M3"]
    row = make_store(R1g1=np.array([0.5] * 29 + [-0.2] * 11))
    assert R.row_tiers(first, row, RULE)["R1_g1"] is False and R.row_tiers(first, row, RULE, cells="g1")["R1_g1"] is False
    assert R.row_tiers(first, make_store(), RULE)["R1_g1"] is True
    out = R.run_v4_full(primary, lab_indicator=row, B=300)                                       # the row's interval is the source of the bracket (D033 F2)
    assert out["effective_tiers"]["R1_g1"] is False and out["primary"]["tiers"]["R1_g1"] is True and out["outcome"]["M3"] and out["outcome"]["title_id"] == "T4"
    assert out["outcome"]["number_sources"]["R1_g1"] == "lab_indicator"
    assert v4.run_v4(primary, row_tiers={"R1_g1": True})["outcome"]["M3"] is False              # a row can only lower the modifier
    assert R.run_v4_full(row, lab_indicator=make_store(), B=300)["effective_tiers"]["R1_g1"] is False      # a primary False stays False under a row that passes
    t, det = R.lab_stratified_tiers(first, primary, B=300)
    assert t["R1_g1"] is True and "R1_g1" in det and det["R1_g1"]["lower"]["0.025"] > 0
    t2, det2 = R.lab_stratified_tiers(first, make_store(R1g1=np.array([0.5] * 20 + [-0.5] * 20)), B=300)
    assert t2["R1_g1"] is False and det2["R1_g1"]["lower"]["0.025"] <= 0


def test_the_m3_interval_comes_from_the_analysis_that_set_the_modifier_and_must_not_contradict_it():
    primary = make_store()
    row = make_store(R1g1=np.array([0.4] * 25 + [-0.1] * 15))                                    # the retain-every-check-up re-run: A1 not shown better than persistence
    out = R.run_v4_full(primary, retain_all=row, B=300)
    o = out["outcome"]
    assert out["primary"]["tiers"]["R1_g1"] is True and out["effective_tiers"]["R1_g1"] is False and o["M3"] and o["number_sources"]["R1_g1"] == "retain_all"
    lo, hi, _, _ = RULE.interval(np.array([0.4] * 25 + [-0.1] * 15), 0.05)
    assert f"({v4.ivs(v4.pct_reduction(lo), v4.pct_reduction(hi))})." in o["abstract_sentence"]
    assert out["downgrade"]["rows"]["retain_all"]["R1_g1"] is False and out["downgrade"]["lab_stratified_detail"]["R1_g1"]["B"] == 300
    with pytest.raises(v4.BracketSignError):                                                     # the primary interval would lie above zero: refused, never printed under "not shown"
        v4.run_v4(primary, row_tiers={"R1_g1": False})
    with pytest.raises(v4.BracketSignError):
        v4.primary_numbers(primary, RULE, {"P1": "S", "R1_g1": False}, None, None)
    num = v4.primary_numbers(primary, RULE, {"P1": "S", "R1_g1": True}, None, None)              # not in force: the number is computed, no sign claim
    assert num["interval_R1"][0] > 0 and num["sources"]["R1_g1"] == "primary"


def test_run_v4_full_lab_stratified_row_can_lower_the_modifier_by_itself():
    """30 of 40 favour A1 (the primary test passes at 30), but A1 is not better than persistence in the 4 SIE conditions and in 6 of the 17 HM conditions: with the three laboratories weighted
    1/3 each the weighted median is not robustly above zero, so row (i) lowers the modifier although the primary analysis passes"""
    L = np.full(40, 0.5)
    hm = [i for i, c in enumerate(CONDS) if LABS[c] == "HM"]
    sie = [i for i, c in enumerate(CONDS) if LABS[c] == "SIE"]
    assert (len(hm), len(sie)) == (17, 4)
    for i in hm[11:] + sie:
        L[i] = -0.3
    primary = make_store(R1g1=L)
    out = R.run_v4_full(primary, B=1000)
    assert out["primary"]["tiers"]["R1_g1"] is True and out["primary"]["nodes"]["R1g1"]["positives"] == 30
    assert out["downgrade"]["rows"]["lab_stratified"]["R1_g1"] is False and out["effective_tiers"]["R1_g1"] is False
    o = out["outcome"]
    assert o["M3"] and o["title_id"] == "T4" and o["number_sources"]["R1_g1"] == "lab_stratified"
    b = out["downgrade"]["lab_stratified_detail"]["R1_g1"]
    assert f"({v4.ivs(v4.pct_reduction(b['lower']['0.025']), v4.pct_reduction(b['upper']['0.025']))})." in o["abstract_sentence"]


# ================================================================================================ AD4, AD5: title and phrase strings
def test_closed_form_replaces_readable_in_T1_T4_T7_and_the_no_claim_phrase():
    assert v4.TITLES[("P+", "K+")][1].startswith("Physics-informed neural networks with closed-form Kolmogorov-Arnold stress laws forecast")
    assert v4.TITLES[("P0", "K+")][1].startswith("Closed-form Kolmogorov-Arnold stress laws for lithium-ion capacity fade")
    assert v4.TITLES[("P-", "K+")][1].endswith("but yields closed-form Kolmogorov-Arnold stress laws")
    assert all("readable" not in t.lower() for _, t in v4.TITLES.values()) and "readable" not in v4.KCLAUSE_KEQ_FAIL.lower()
    assert v4.KCLAUSE_KEQ_FAIL.endswith("so no closed-form-law claim is made")
    num = {"X": 20.0, "Y": 5.0, "interval_P1": (10.0, 30.0), "interval_K2": (5.0, 15.0), "n": 40}
    s = v4.assemble_outcome(dict(P1="S", P2=True, P3=True, K1=False, K2="none", QH_g1="none", QA10_g1="none", R1_g1=True), num)["abstract_sentence"]
    assert s.endswith("was not shown to stay within 10 % of the full network, so no closed-form-law claim is made.")


def test_t9_says_when_few_only_if_P3_is_S():
    num = {"X": 20.0, "Y": 5.0, "Z": 10.0, "W": 3.0, "interval_P1": (10.0, 30.0), "interval_K2": (5.0, 15.0), "interval_W": (1.0, 5.0), "n": 40}
    for K, k1, k2, with_p3, without_p3 in (("K+", True, "S", "Physics priors pay when cycling tests are few: semi-empirical, physics-informed Kolmogorov-Arnold and data-driven forecasts",
                                            "Physics priors pay with few cycling tests: semi-empirical, physics-informed Kolmogorov-Arnold and data-driven forecasts"),
                                           ("K-", False, "reverse S", "Physics priors pay when cycling tests are few: semi-empirical, physics-informed and data-driven forecasts",
                                            "Physics priors pay with few cycling tests: semi-empirical, physics-informed and data-driven forecasts")):
        base = dict(P1="S", P2=True, K1=k1, K2=k2, QH_g1="none", QA10_g1="reverse S", R1_g1=True)
        a = v4.assemble_outcome({**base, "P3": True}, num)
        b = v4.assemble_outcome({**base, "P3": False}, num)
        assert a["title"].startswith(with_p3) and b["title"].startswith(without_p3) and a["title_id"] == b["title_id"] == ("T9a" if K == "K+" else "T9b")
        assert a["M2"] and b["M2"] and not a["M3"] and not b["M3"]
    for tid, title in (v4.T9A_NOP3, v4.T9B_NOP3):
        assert title.endswith("forecasts of lithium-ion capacity fade") and " when " not in title
