"""D018 additions to pinnkan.graph_test: the fixed design-effect (Beta-binomial, rho_s0 = 0.03) sign test, the w = 0.78 weight alternative
(initial levels 0.0195 / 0.0055, counts 30 / 32), the fallback interval ranks, the secondary graph (PREREG_v4 9.5, GAP-2) with
hand-worked examples, and the item (f) dependence estimator. Synthetic data only; all expected values are worked by hand in the comments."""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))

import numpy as np
import pytest
from scipy import stats

from pinnkan import graph_test as gt

A = 0.025


def P(**kw):
    base = {k: 1.0 for k in gt.NODES}
    base.update(kw)
    return base


# ------------------------------------------------------------------------------------------------ fixed design-effect test
def test_betabin_matches_scipy_and_limits():
    n = 40
    for rho in (0.01, 0.03, 0.05):
        a = (1 / rho - 1) / 2
        ref = stats.betabinom.sf(np.arange(n + 1) - 1, n, a, a)
        ref[0] = 1.0
        assert np.allclose(gt.betabin_tail_table(n, rho)[: n + 1], ref, atol=1e-12)
    # limiting case: rho_s0 = 0 is the plain binomial, counts 28 / 27 (PREREG_v3 9.3)
    assert np.allclose(gt.betabin_tail_table(n, 0.0), gt.binom_tail_table(n))
    assert gt.betabin_crit(40, 0.0125, 0.0) == 28 and gt.betabin_crit(40, 0.025, 0.0) == 27


def test_counts_at_n40_match_the_judge_table():
    # D018 2.1: 33 / 32 / 32 / 31 / 30 at 0.005, 0.00625, 0.00833, 0.0125, 0.025
    got = [gt.betabin_crit(40, a, 0.03) for a in (0.005, 0.00625, 0.025 / 3, 0.0125, 0.025)]
    assert got == [33, 32, 32, 31, 30]
    t = gt.betabin_tail_table(40, 0.03)
    assert t[31] == pytest.approx(0.0106, abs=5e-5) and t[30] == pytest.approx(0.0194, abs=5e-5)
    # sensitivity grid at 0.0125 / 0.025 (RESULT 4.4)
    assert [gt.betabin_crit(40, 0.0125, r) for r in gt.RHO_GRID] == [28, 29, 30, 31, 33]
    assert [gt.betabin_crit(40, 0.025, r) for r in gt.RHO_GRID] == [27, 28, 29, 30, 31]


def test_unreachable_level_at_small_n_returns_n_plus_1():
    assert gt.betabin_crit(5, 0.005, 0.03) == 6
    assert gt.betabin_crit(13, 0.025, 0.03) <= 13


def test_dep_sign_test_counts_strictly_above_margin():
    L = np.array([0.1] * 31 + [-0.2] * 9)
    pos, p = gt.dep_sign_test_p(L, 0.0)
    assert pos == 31 and p == pytest.approx(gt.betabin_tail_table(40, 0.03)[31])
    assert p <= 0.0125 and gt.dep_sign_test_p(np.array([0.1] * 30 + [-0.2] * 10), 0.0)[1] > 0.0125


def test_fallback_interval_ranks_n40():
    # D018 2.1: 1 - 0.05/9 interval rank 8 = [L(8), L(33)]; the 95 % interval rank 11 = [L(11), L(30)], coverage 1 - 2 * P(BB >= 30)
    r9, c9 = gt.dep_interval_rank(40, 0.05 / 9, 0.03)
    r95, c95 = gt.dep_interval_rank(40, 0.05, 0.03)
    assert (r9, r95) == (8, 11)
    assert c95 == pytest.approx(1 - 2 * gt.betabin_tail_table(40, 0.03)[30]) and c9 >= 1 - 0.05 / 9
    x = np.arange(1.0, 41.0)
    lo, hi, r, cov = gt.dep_order_stat_interval(x, 0.05 / 9, 0.03)
    assert (lo, hi, r) == (8.0, 33.0, 8)
    # no pair attains the level at tiny n: the labelled range is used
    lo, hi, r, cov = gt.dep_order_stat_interval(np.array([3.0, 1.0, 2.0, 5.0]), 0.05 / 9, 0.03)
    assert (lo, hi, r) == (1.0, 5.0, 0) and np.isnan(cov)
    # rho = 0 reproduces the plain exact interval ranks 11 and 14
    assert gt.dep_interval_rank(40, 0.05 / 9, 0.0)[0] == 11 and gt.dep_interval_rank(40, 0.05, 0.0)[0] == 14


# ------------------------------------------------------------------------------------------------ weights 0.78 / 0.22
def test_weight_alternative_initial_levels_and_counts():
    nodes, w, G = gt.pinnkan_graph(gt.W_ALT)
    r = gt.graph_test(np.ones(7), w, G, A)               # nothing rejected: final levels are the initial levels
    assert r.final_level[0] == pytest.approx(0.0195) and r.final_level[4] == pytest.approx(0.0055)
    assert w.sum() == pytest.approx(1.0)
    # counts under rho_s0 = 0.03: P1N needs 30 at 0.0195 (31 at 1/2 weight), K1 needs 32 at 0.0055 (33 at 0.00625... 32 holds down to 0.00535)
    assert gt.betabin_crit(40, r.final_level[0], 0.03) == 30 and gt.betabin_crit(40, r.final_level[4], 0.03) == 32
    nodes, w5, G5 = gt.pinnkan_graph()
    r5 = gt.graph_test(np.ones(7), w5, G5, A)
    assert r5.final_level[0] == pytest.approx(0.0125) and gt.betabin_crit(40, r5.final_level[0], 0.03) == 31
    assert gt.betabin_tail_table(40, 0.03)[32] == pytest.approx(0.005352, abs=1e-6)       # D018 3, section "discreteness"
    with pytest.raises(ValueError):
        gt.pinnkan_graph(1.0)


def test_default_graph_unchanged():
    nodes, w, G = gt.pinnkan_graph()
    assert w[0] == 0.5 and w[4] == 0.5 and G[3, 4] == 1.0 and G[6, 0] == 1.0


def test_hand_worked_p_chain_at_30_positives_under_the_alternative_weights():
    t = gt.betabin_tail_table(40, 0.03)
    pN = t[30]                                              # 0.019356 <= 0.0195
    pv = P(P1N=pN, P1S=pN, P2=pN, P3=pN)
    r = gt.graph_test(np.array([pv[k] for k in gt.NODES]), *gt.pinnkan_graph(gt.W_ALT)[1:], A)
    assert set(r.names()) == {"P1N", "P1S", "P2", "P3"}
    # K1 then receives the whole level 0.025 (32 positives needed at 0.0055, but only 30 at 0.025): hand-over by P3
    assert r.final_level[4] == pytest.approx(A)
    r = gt.graph_test(np.array([pv[k] for k in gt.NODES]), *gt.pinnkan_graph(0.5)[1:], A)
    assert r.names() == []                                  # at weight 1/2, 30 positives are not enough (need 31)


def test_k_chain_needs_32_at_the_alternative_weights():
    t = gt.betabin_tail_table(40, 0.03)
    for pos, expect in ((32, True), (31, False)):
        pv = P(K1=t[pos])
        r = gt.graph_test(np.array([pv[k] for k in gt.NODES]), *gt.pinnkan_graph(gt.W_ALT)[1:], A)
        assert ("K1" in r.names()) == expect


# ------------------------------------------------------------------------------------------------ secondary graph (GAP-2)
def sec(pN, pS):
    nodes, w, G = gt.secondary_graph(5)
    return nodes, gt.graph_test(np.array(list(pN) + list(pS), float), w, G, A)


def test_secondary_graph_structure():
    nodes, w, G = gt.secondary_graph(5)
    assert nodes[:5] == ("N1", "N2", "N3", "N4", "N5") and nodes[5:] == ("S1", "S2", "S3", "S4", "S5")
    assert w[:5].tolist() == [0.2] * 5 and w[5:].sum() == 0.0 and w.sum() == pytest.approx(1.0)
    assert G[0, 5] == 1.0 and G[5, 1] == pytest.approx(0.25) and G[5, 0] == 0.0 and G.sum(1).max() <= 1.0 + 1e-12
    # initial levels: alpha / 5 = 0.005 for each N_i
    r = gt.graph_test(np.ones(10), w, G, A)
    assert np.allclose(r.final_level[:5], 0.005)


def test_secondary_reduces_to_holm_when_every_S_is_rejected():
    # Hand-worked. p_N = (0.001, 0.0055, 0.008, 0.02, 0.5), p_S = 0 (S_i passes whatever level it receives).
    # N1: 0.001 <= 0.005 -> reject, weight 0.2 goes to S1 (p 0, rejected), 0.05 to each of N2..N5: levels 0.00625 (= 0.025/4).
    # N2: 0.0055 <= 0.00625 -> reject; remaining N3..N5 at 0.025/3 = 0.008333. N3: 0.008 <= 0.008333 -> reject.
    # N4, N5 at 0.0125: 0.02 > 0.0125, 0.5 > 0.0125 -> stop. Holm over (0.001, 0.0055, 0.008, 0.02, 0.5) rejects exactly the first three.
    nodes, r = sec([0.001, 0.0055, 0.008, 0.02, 0.5], [0.0] * 5)
    assert set(r.names(nodes)) == {"N1", "N2", "N3", "S1", "S2", "S3"}
    assert r.level_at_rejection[0] == pytest.approx(0.005)
    assert r.level_at_rejection[1] == pytest.approx(0.025 / 4) and r.level_at_rejection[2] == pytest.approx(0.025 / 3)
    assert r.final_level[3] == pytest.approx(0.0125) and r.final_level[4] == pytest.approx(0.0125)
    # p_N4 = 0.012 <= 0.0125 -> rejected (p_N = 0.001, 0.0055, 0.008, 0.012, 0.02), then N5 at 0.025: 0.02 <= 0.025 -> rejected: Holm rejects all five
    nodes, r = sec([0.001, 0.0055, 0.008, 0.012, 0.02], [0.0] * 5)
    assert set(r.names(nodes)) == set(nodes)
    assert r.level_at_rejection[4] == pytest.approx(0.025)


def test_secondary_equals_holm_on_random_p_values_when_S_always_rejects():
    rng = np.random.default_rng(11)
    for _ in range(200):
        pN = rng.random(5) ** 3 * 0.05
        nodes, r = sec(pN, np.zeros(5))
        order = np.argsort(pN)
        holm = np.zeros(5, bool)
        for step, i in enumerate(order):
            if pN[i] <= A / (5 - step):
                holm[i] = True
            else:
                break
        assert (r.rejected[:5] == holm).all()


def test_secondary_tier_N_holds_its_level():
    # Hand-worked consequence of 9.5 as written: if S_i is NOT rejected its weight stays at S_i. p_N = (0.001, 0.006, 1, 1, 1), p_S = 1.
    # N1 rejected at 0.005; its 0.005 goes to S1 and stays there; N2 stays at 0.005, so 0.006 is not rejected.
    # (Holm over the N p-values alone would reject 0.006 <= 0.00625.) Only a rejected S_i releases the level.
    nodes, r = sec([0.001, 0.006, 1, 1, 1], [1.0] * 5)
    assert r.names(nodes) == ["N1"] and r.final_level[5] == pytest.approx(0.005) and r.final_level[1] == pytest.approx(0.005)
    # with S1 rejected (p_S1 = 0) the level is released: N2 at 0.00625 is rejected, S2 (p 1) holds its level
    nodes, r = sec([0.001, 0.006, 1, 1, 1], [0.0, 1.0, 1.0, 1.0, 1.0])
    assert set(r.names(nodes)) == {"N1", "S1", "N2"}
    assert r.level_at_rejection[1] == pytest.approx(0.00625)


def test_secondary_total_level_never_exceeds_alpha_under_null():
    nodes, w, G = gt.secondary_graph(5)
    rng = np.random.default_rng(12)
    Pm = rng.random((100000, 10))
    fw = gt.graph_test(Pm, w, G, A).rejected.any(1).mean()
    assert fw <= A + 3 * np.sqrt(A * (1 - A) / 100000)


# ------------------------------------------------------------------------------------------------ item (f) estimator
def test_sign_icc_hand_worked():
    fold = np.repeat(np.arange(5), 8)
    # alternating signs inside every fold: four ones and four zeros per fold -> MSB = 0, MSW = 8 * 4 * 4 / 8 ... computed by hand:
    # within-fold SS = 8 * 0.25 * ... = 2 per fold -> MSW = 10 / 35 = 2/7; MSB = 0; ICC = (0 - 2/7) / (0 + 7 * 2/7) = -1/7
    s = np.tile([1, 0], 20)
    out = gt.sign_icc_anova(s, fold)
    assert out["icc"] == pytest.approx(-1 / 7) and out["msb"] == pytest.approx(0.0)
    # whole folds all ones / all zeros: MSW = 0 -> ICC = 1
    s = np.repeat([1, 1, 0, 0, 0], 8)
    assert gt.sign_icc_anova(s, fold)["icc"] == 1.0
    # two ones in every fold at the same positions... a balanced example with ICC 0: fold means all equal -> MSB = 0 -> ICC = -1/7 (as above)
    # one fold of ones, the rest half: fold means (1, .5, .5, .5, .5), grand mean .6; MSB = 8 * (0.16 + 4 * 0.01) / 4 = 0.4;
    # SS_within = 4 folds * 8 * 0.25 = 8 -> MSW = 8 / 35; ICC = (0.4 - 8/35) / (0.4 + 7 * 8/35)
    s = np.concatenate([np.ones(8), np.tile([1, 0], 16)])
    out = gt.sign_icc_anova(s, fold)
    msw = 8 / 35
    assert out["msb"] == pytest.approx(0.4) and out["msw"] == pytest.approx(msw)
    assert out["icc"] == pytest.approx((0.4 - msw) / (0.4 + 7 * msw))
    assert out["upper"] >= out["icc"]


def test_avg_pairwise_sign_corr_hand_worked():
    fold = np.repeat(np.arange(5), 8)
    lab = np.array([0] * 17 + [1] * 19 + [2] * 4)
    # same-fold pairs 5 * C(8,2) = 140 ; same-lab pairs C(17,2) + C(19,2) + C(4,2) = 136 + 171 + 6 = 313 ; all pairs C(40,2) = 780
    assert gt.avg_pairwise_sign_corr(fold, lab, 0.10, 0.0) == pytest.approx(0.10 * 140 / 780)
    assert gt.avg_pairwise_sign_corr(fold, lab, 0.10, 0.05) == pytest.approx((0.10 * 140 + 0.05 * 313) / 780)
    assert gt.avg_pairwise_sign_corr(fold, lab, -0.2, -0.1) == 0.0                     # negative estimates are floored at 0


def test_dependence_report_flags_rho_above_the_assumed_value():
    rng = np.random.default_rng(5)
    fold = np.repeat(np.arange(5), 8)
    lab = np.array([0] * 17 + [1] * 19 + [2] * 4)
    z = np.sqrt(0.6) * rng.standard_normal(5)[fold] + np.sqrt(0.4) * rng.standard_normal(40)    # strong fold effect
    rep = gt.dependence_report((z > np.median(z)).astype(float), fold, lab)
    assert set(rep) >= {"rho_fold", "rho_fold_upper", "rho_lab", "avg_pairwise", "avg_pairwise_upper", "exceeds_rho_s0", "rho_s0"}
    assert rep["rho_fold_upper"] >= rep["rho_fold"] and rep["avg_pairwise_upper"] >= rep["avg_pairwise"] and rep["rho_s0"] == 0.03
    # independent signs: the point estimate is near zero on average
    est = [gt.dependence_report((rng.random(40) > 0.5).astype(float), fold, lab)["rho_fold"] for _ in range(400)]
    assert abs(np.mean(est)) < 0.02
