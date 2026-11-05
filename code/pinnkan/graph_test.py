"""Bonferroni-based graphical multiple-testing procedure (Bretz et al. 2009 weight/graph update) and the exact sign-test
helpers used by the D016 primary graph (PREREG_v4).

Graph of D016 (judge file, section 2): nodes P1N -> P1S -> P2 -> P3 and K1 -> K2N -> K2S; initial weights 1/2 on P1N and
1/2 on K1; every edge has weight 1. A chain passes its level along its own path. The two chains are joined by the edges
P3 -> K1 and K2S -> P1N, so that a chain hands its level to the other chain only when its last node is rejected (a node that
has been rejected is removed from the graph and its outgoing edges are re-routed by the update rule, which makes the level of a
completed chain reach the first node of the other chain that is still open).

The procedure is valid for any dependence between the p-values as long as each p-value is valid (super-uniform) under its null:
the sum of the local levels alpha * w_i is at most alpha at every step.

All functions accept one vector of p-values (shape (m,)) or a batch (shape (B, m)); the batch form is used by the simulations.
Reverse-S safety tests of D016 are outside the graph and are not part of this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import comb

import numpy as np

NODES = ("P1N", "P1S", "P2", "P3", "K1", "K2N", "K2S")
TOL = 1e-9          # relative tolerance in the comparison p <= alpha * w (binomial tails are floats)


# ----------------------------------------------------------------------------------------------------------- sign test
def binom_tail_table(n: int) -> np.ndarray:
    """t[k] = P(X >= k), X ~ Binomial(n, 1/2), k = 0..n+1 (t[n+1] = 0)."""
    pmf = np.array([comb(n, j) for j in range(n + 1)], dtype=float) / 2.0 ** n
    t = np.zeros(n + 2)
    t[: n + 1] = np.cumsum(pmf[::-1])[::-1]
    return t


def sign_p(pos, n: int):
    """Exact one-sided p-value of observing >= pos positives out of n under H0: P(L > m) <= 1/2."""
    return binom_tail_table(n)[np.asarray(pos, dtype=int)]


def sign_crit(n: int, alpha: float) -> int:
    """Smallest number of positives k with P(X >= k) <= alpha (n + 1 if none)."""
    t = binom_tail_table(n)
    for k in range(n + 2):
        if t[k] <= alpha * (1 + TOL):
            return k
    return n + 1


def sign_test_p(L, margin: float):
    """(positives, exact one-sided p) of the sign test of median(L) > margin. Ties with the margin are not positive."""
    L = np.asarray(L, dtype=float)
    pos = int((L > margin).sum())
    return pos, float(sign_p(pos, L.size))


def order_stat_interval(L, alpha_two_sided: float):
    """Exact distribution-free interval for the median: [L_(r), L_(n+1-r)] with the largest r such that
    coverage 1 - 2 P(X <= r-1) >= 1 - alpha_two_sided. Returns (lo, hi, r, coverage) or (nan, nan, 0, nan) if none exists."""
    x = np.sort(np.asarray(L, dtype=float))
    n = x.size
    pmf = np.array([comb(n, j) for j in range(n + 1)], dtype=float) / 2.0 ** n
    cdf = np.cumsum(pmf)
    r = 0
    for rr in range(1, n // 2 + 1):
        if 1.0 - 2.0 * cdf[rr - 1] >= 1.0 - alpha_two_sided - 1e-12:
            r = rr
    if r == 0:
        return float("nan"), float("nan"), 0, float("nan")
    return float(x[r - 1]), float(x[n - r]), r, float(1.0 - 2.0 * cdf[r - 1])


# --------------------------------------------------------------------------------------------------------------- graph
def pinnkan_graph():
    """(nodes, weights, G) of the D016 primary graph."""
    idx = {k: i for i, k in enumerate(NODES)}
    w = np.zeros(len(NODES))
    w[idx["P1N"]] = 0.5
    w[idx["K1"]] = 0.5
    G = np.zeros((len(NODES), len(NODES)))
    for a, b in (("P1N", "P1S"), ("P1S", "P2"), ("P2", "P3"), ("P3", "K1"),
                 ("K1", "K2N"), ("K2N", "K2S"), ("K2S", "P1N")):
        G[idx[a], idx[b]] = 1.0
    return NODES, w, G


@dataclass
class GraphResult:
    rejected: np.ndarray        # bool, (m,) or (B, m)
    level_at_rejection: np.ndarray   # alpha * w_i at the moment i was rejected (nan if not rejected)
    final_level: np.ndarray     # alpha * w_i at termination (the last level a still-open node was compared with)
    order: list                 # single input only: node indices in order of rejection

    def names(self, nodes=NODES):
        return [nodes[i] for i in np.nonzero(np.atleast_1d(self.rejected))[0]]


def graph_test(p, weights, G, alpha: float = 0.025) -> GraphResult:
    """Sequentially rejective graphical procedure. A hypothesis i is rejected when p_i <= alpha * w_i (w_i > 0); then its weight
    is passed along the outgoing edges, and the edge weights are updated:
        w_l <- w_l + w_i g_il ;  g_lk <- (g_lk + g_li g_ik) / (1 - g_li g_il)  (l, k != i; 0 if the denominator is 0).
    Loops until no open hypothesis can be rejected."""
    P = np.atleast_2d(np.asarray(p, dtype=float))
    single = np.asarray(p).ndim == 1
    B, m = P.shape
    w0 = np.asarray(weights, dtype=float)
    G0 = np.asarray(G, dtype=float)
    if w0.shape != (m,) or G0.shape != (m, m):
        raise ValueError("weights/graph do not match the number of p-values")
    if (w0 < 0).any() or w0.sum() > 1 + 1e-12 or (G0 < 0).any() or (G0.sum(1) > 1 + 1e-12).any() or np.diag(G0).any():
        raise ValueError("invalid graph: weights >= 0 summing to <= 1; edge weights >= 0, row sums <= 1, no self-loops")
    w = np.tile(w0, (B, 1))
    Gm = np.tile(G0, (B, 1, 1))
    active = np.ones((B, m), bool)
    rej = np.zeros((B, m), bool)
    lev = np.full((B, m), np.nan)
    order_log = [[] for _ in range(B)] if single else None
    diag = np.arange(m)
    for _ in range(m):
        cand = active & (w > 0) & (P <= alpha * w * (1 + TOL))
        any_ = cand.any(1)
        if not any_.any():
            break
        rows = np.nonzero(any_)[0]
        jj = np.argmax(cand[rows], axis=1)
        R = rows.size
        wj = w[rows, jj]
        lev[rows, jj] = alpha * wj
        rej[rows, jj] = True
        active[rows, jj] = False
        if single:
            order_log[0].append(int(jj[0]))
        Gj_row = Gm[rows, jj, :]                       # g_jk
        Gj_col = Gm[rows, :, jj]                       # g_lj
        w[rows] += wj[:, None] * Gj_row
        w[rows, jj] = 0.0
        den = 1.0 - Gj_col * Gj_row                    # 1 - g_lj g_jl, indexed by l
        num = Gm[rows] + Gj_col[:, :, None] * Gj_row[:, None, :]
        newG = np.where(den[:, :, None] > 1e-12, num / np.maximum(den, 1e-12)[:, :, None], 0.0)
        newG[:, diag, diag] = 0.0
        newG[np.arange(R), jj, :] = 0.0
        newG[np.arange(R), :, jj] = 0.0
        Gm[rows] = newG
    final = alpha * w
    if single:
        return GraphResult(rej[0], lev[0], final[0], order_log[0])
    return GraphResult(rej, lev, final, [])


def run_pinnkan_graph(p_by_node: dict, alpha: float = 0.025) -> GraphResult:
    """Convenience: p-values keyed by node name (all seven required); returns the GraphResult on the D016 graph."""
    nodes, w, G = pinnkan_graph()
    missing = [k for k in nodes if k not in p_by_node]
    if missing:
        raise KeyError(f"missing p-values for {missing}")
    return graph_test(np.array([p_by_node[k] for k in nodes], dtype=float), w, G, alpha)
