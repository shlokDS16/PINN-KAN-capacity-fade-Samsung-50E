"""Unit tests of pinnkan.graph_test: sign test thresholds of PREREG_v3 9.3, the Holm special case of the graphical procedure,
the pass-through rules of the D016 graph, batch/single agreement and a small null simulation. Synthetic data only."""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))

import numpy as np
import pytest

from pinnkan import graph_test as gt

A = 0.025


def P(**kw):
    base = {k: 1.0 for k in gt.NODES}
    base.update(kw)
    return base


def test_sign_thresholds_match_prereg_v3_9_3():
    # PREREG_v3 9.3 / TYPE1_SIGNFLIP: positives needed (actual size) at n = 40, 19, 13
    assert gt.sign_crit(40, A / 3) == 28 and gt.sign_crit(40, A / 2) == 28 and gt.sign_crit(40, A) == 27
    assert gt.sign_crit(40, A / 4) == 29
    assert gt.sign_crit(19, A / 3) == 16 and gt.sign_crit(19, A / 2) == 15 and gt.sign_crit(19, A) == 15
    assert gt.sign_crit(13, A / 3) == 12 and gt.sign_crit(13, A / 2) == 11 and gt.sign_crit(13, A) == 11
    t = gt.binom_tail_table(40)
    assert t[28] == pytest.approx(0.0083, abs=5e-5) and t[27] == pytest.approx(0.0192, abs=5e-5)
    assert t[0] == pytest.approx(1.0) and t[41] == 0.0


def test_sign_test_p_counts_strictly_above_margin():
    L = np.array([0.1] * 30 + [-0.2] * 10)
    pos, p = gt.sign_test_p(L, 0.0)
    assert pos == 30 and p == pytest.approx(gt.binom_tail_table(40)[30])
    pos, _ = gt.sign_test_p(L, 0.1)          # ties with the margin are not positive
    assert pos == 0


def test_order_statistic_interval_coverage_and_rank():
    rng = np.random.default_rng(1)
    x = rng.standard_normal(40)
    lo, hi, r, cov = gt.order_stat_interval(x, 0.05)
    xs = np.sort(x)
    assert (lo, hi) == (xs[r - 1], xs[40 - r]) and cov >= 0.95 and r == 14
    lo, hi, r, cov = gt.order_stat_interval(x, 0.05 / 9)
    assert r >= 1 and cov >= 1 - 0.05 / 9
    # no interval exists for n = 5 at that coverage
    assert gt.order_stat_interval(rng.standard_normal(5), 0.05 / 9)[2] == 0


def test_graph_reduces_to_holm():
    # three hypotheses, equal weights, full Holm graph (each passes half of its weight to each of the others)
    w = np.ones(3) / 3
    G = (np.ones((3, 3)) - np.eye(3)) / 2
    for p in ([0.001, 0.02, 0.9], [0.009, 0.012, 0.0125], [0.02, 0.02, 0.02], [0.2, 0.001, 0.0124], [0.0001, 0.013, 0.2]):
        r = gt.graph_test(p, w, G, A).rejected
        order = np.argsort(p)
        holm = np.zeros(3, bool)
        for step, i in enumerate(order):
            if p[i] <= A / (3 - step):
                holm[i] = True
            else:
                break
        assert (r == holm).all(), (p, r, holm)


def test_chain_p_alone_runs_at_half_alpha():
    # P chain passes at 0.0125 each; K1 fails, so nothing is handed over
    r = gt.run_pinnkan_graph(P(P1N=0.0125, P1S=0.0125, P2=0.0125, P3=0.0125))
    assert r.names() == ["P1N", "P1S", "P2", "P3"] or set(r.names()) == {"P1N", "P1S", "P2", "P3"}
    assert np.allclose(r.level_at_rejection[:4], A / 2)
    # a p-value of 0.02 at P1N is not rejected while K1 is open
    r = gt.run_pinnkan_graph(P(P1N=0.02))
    assert not r.rejected.any() and r.final_level[0] == pytest.approx(A / 2)


def test_chain_gating_is_sequential():
    r = gt.run_pinnkan_graph(P(P1N=1e-6, P1S=0.5, P2=1e-9, P3=1e-9))     # P1S fails: P2 and P3 are never reached
    assert r.names() == ["P1N"]
    r = gt.run_pinnkan_graph(P(P1N=1e-6, P1S=1e-6, P2=0.5, P3=1e-9))
    assert set(r.names()) == {"P1N", "P1S"}
    r = gt.run_pinnkan_graph(P(K1=1e-6, K2N=0.5, K2S=1e-9))
    assert r.names() == ["K1"]


def test_pass_through_p_complete_gives_k_the_full_level():
    # P chain complete -> K1 is tested at 0.0125 + 0.0125 = 0.025
    r = gt.run_pinnkan_graph(P(P1N=1e-6, P1S=1e-6, P2=1e-6, P3=1e-6, K1=0.02))
    assert "K1" in r.names() and r.level_at_rejection[4] == pytest.approx(A)
    # but only 0.0125 if P3 does not pass
    r = gt.run_pinnkan_graph(P(P1N=1e-6, P1S=1e-6, P2=1e-6, P3=0.5, K1=0.02))
    assert "K1" not in r.names() and r.final_level[4] == pytest.approx(A / 2)
    # P3 rejected at its own level also frees K2N and K2S at 0.025 once K1 is rejected
    r = gt.run_pinnkan_graph(P(P1N=1e-6, P1S=1e-6, P2=1e-6, P3=1e-6, K1=1e-6, K2N=0.02, K2S=0.024))
    assert {"K1", "K2N", "K2S"} <= set(r.names())
    assert r.level_at_rejection[5] == pytest.approx(A) and r.level_at_rejection[6] == pytest.approx(A)


def test_pass_through_k_complete_gives_p1_the_full_level():
    # K chain complete -> P1N is tested at 0.025 (27 of 40 positives); P1S then P2 and P3 follow at 0.025
    pN = gt.binom_tail_table(40)[27]
    r = gt.run_pinnkan_graph(P(K1=1e-6, K2N=1e-6, K2S=1e-6, P1N=pN, P1S=pN, P2=pN, P3=pN))
    assert set(r.names()) == set(gt.NODES)
    assert r.level_at_rejection[0] == pytest.approx(A)
    # K chain incomplete (K2S fails): P1N stays at 0.0125 and 27 positives are not enough
    r = gt.run_pinnkan_graph(P(K1=1e-6, K2N=1e-6, K2S=0.5, P1N=pN))
    assert "P1N" not in r.names() and r.final_level[0] == pytest.approx(A / 2)
    # P chain partly done when K completes: P2 is reached at the full level
    r = gt.run_pinnkan_graph(P(P1N=1e-6, P1S=1e-6, P2=0.02, K1=1e-6, K2N=1e-6, K2S=1e-6))
    assert "P2" in r.names() and r.level_at_rejection[2] == pytest.approx(A)


def test_total_level_never_exceeds_alpha():
    nodes, w, G = gt.pinnkan_graph()
    rng = np.random.default_rng(3)
    Pm = rng.random((2000, 7)) ** 3
    r = gt.graph_test(Pm, w, G, A)
    # at every termination the levels of the still-open nodes plus the levels at which nodes were rejected cannot exceed alpha:
    # the weights of rejected nodes are zero, so alpha * sum(open w) <= alpha
    open_ = ~r.rejected
    assert (r.final_level[open_.nonzero()[0], open_.nonzero()[1]] <= A + 1e-12).all()
    assert ((r.final_level * open_).sum(1) <= A + 1e-12).all()


def test_batch_equals_single():
    nodes, w, G = gt.pinnkan_graph()
    rng = np.random.default_rng(4)
    Pm = rng.random((300, 7)) ** 4
    rb = gt.graph_test(Pm, w, G, A)
    for i in range(0, 300, 7):
        rs = gt.graph_test(Pm[i], w, G, A)
        assert (rs.rejected == rb.rejected[i]).all()
        assert np.allclose(rs.final_level, rb.final_level[i])


def test_fwer_under_independent_uniform_nulls_is_below_alpha():
    nodes, w, G = gt.pinnkan_graph()
    rng = np.random.default_rng(5)
    Pm = rng.random((200000, 7))
    fw = gt.graph_test(Pm, w, G, A).rejected.any(1).mean()
    assert fw <= A + 3 * np.sqrt(A * (1 - A) / 200000)
    # every hypothesis false except the last of each chain: still bounded
    Pm[:, :3] = 0.0
    Pm[:, 4:6] = 0.0
    fw = gt.graph_test(Pm, w, G, A).rejected[:, [3, 6]].any(1).mean()
    assert fw <= A + 3 * np.sqrt(A * (1 - A) / 200000)


def test_invalid_graphs_are_refused():
    with pytest.raises(ValueError):
        gt.graph_test([0.1, 0.1], [0.7, 0.7], np.zeros((2, 2)))
    with pytest.raises(ValueError):
        gt.graph_test([0.1, 0.1], [0.5, 0.5], np.array([[0, 1.2], [0, 0]]))
    with pytest.raises(KeyError):
        gt.run_pinnkan_graph({"P1N": 0.1})
