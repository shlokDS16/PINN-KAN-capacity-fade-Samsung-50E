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
def pinnkan_graph(w_p: float = 0.5):
    """(nodes, weights, G) of the D016 primary graph. w_p = initial weight on P1N (default 1/2); K1 gets 1 - w_p (D018: 0.78 / 0.22 is the one
    pre-identified alternative)."""
    if not 0.0 < w_p < 1.0:
        raise ValueError("w_p must be in (0, 1)")
    idx = {k: i for i, k in enumerate(NODES)}
    w = np.zeros(len(NODES))
    w[idx["P1N"]] = w_p
    w[idx["K1"]] = 1.0 - w_p
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


# ------------------------------------------------------------------------------------------ D018: fixed design-effect sign test
RHO_S0 = 0.03          # D018 section 2.1: confirmatory value; the sensitivity grid is (0, 0.01, 0.02, 0.03, 0.05)
RHO_GRID = (0.0, 0.01, 0.02, 0.03, 0.05)
W_ALT = 0.78           # D018 section 3: the one pre-identified alternative weight on P1N


def betabin_tail_table(n: int, rho_s: float = RHO_S0) -> np.ndarray:
    """t[k] = P(X >= k), k = 0..n+1, X ~ Beta-binomial(n; a = b = (1/rho_s - 1)/2): exchangeable pairwise correlation rho_s of the sign
    indicators, mean 1/2 (design effect 1 + (n-1) rho_s). rho_s = 0 is the binomial. Pure Python (lgamma)."""
    from math import lgamma, exp
    if rho_s <= 0:
        return binom_tail_table(n)
    a = (1.0 / rho_s - 1.0) / 2.0
    lb = lambda x, y: lgamma(x) + lgamma(y) - lgamma(x + y)
    lg_ab = lb(a, a)
    pmf = np.array([exp(lgamma(n + 1) - lgamma(k + 1) - lgamma(n - k + 1) + lb(k + a, n - k + a) - lg_ab) for k in range(n + 1)])
    pmf = pmf / pmf.sum()
    t = np.zeros(n + 2)
    t[: n + 1] = np.cumsum(pmf[::-1])[::-1]
    t[0] = 1.0
    return t


def betabin_p(pos, n: int, rho_s: float = RHO_S0):
    """One-sided p-value P(BetaBin >= pos) of the fixed design-effect sign test."""
    return betabin_tail_table(n, rho_s)[np.asarray(pos, dtype=int)]


def betabin_crit(n: int, alpha: float, rho_s: float = RHO_S0) -> int:
    """Smallest number of positives k with P(BetaBin >= k) <= alpha (n + 1 if none: the level cannot be reached at this n)."""
    t = betabin_tail_table(n, rho_s)
    for k in range(n + 2):
        if t[k] <= alpha * (1 + TOL):
            return k
    return n + 1


def dep_sign_test_p(L, margin: float, rho_s: float = RHO_S0):
    """(positives, p) of the fixed design-effect sign test of median(L) > margin (D018 confirmatory test; assumption-based)."""
    L = np.asarray(L, dtype=float)
    pos = int((L > margin).sum())
    return pos, float(betabin_p(pos, L.size, rho_s))


def dep_interval_rank(n: int, alpha_two_sided: float, rho_s: float = RHO_S0):
    """Largest rank r such that [L_(r), L_(n+1-r)] has coverage 1 - 2 P(BetaBin <= r-1) >= 1 - alpha_two_sided (by symmetry
    P(BetaBin <= r-1) = P(BetaBin >= n-r+1)). Returns (r, coverage); (0, nan) if no pair attains the level (then the range (min, max) is used)."""
    t = betabin_tail_table(n, rho_s)
    r, cov = 0, float("nan")
    for rr in range(1, n // 2 + 1):
        c = 1.0 - 2.0 * t[n - rr + 1]
        if c >= 1.0 - alpha_two_sided - 1e-12:
            r, cov = rr, float(c)
    return r, cov


def dep_order_stat_interval(L, alpha_two_sided: float, rho_s: float = RHO_S0):
    """Fallback-rank order-statistic interval (lo, hi, r, coverage); the labelled range (min, max) with r = 0 if no pair attains the level."""
    x = np.sort(np.asarray(L, dtype=float))
    r, cov = dep_interval_rank(x.size, alpha_two_sided, rho_s)
    if r == 0:
        return float(x[0]), float(x[-1]), 0, float("nan")
    return float(x[r - 1]), float(x[x.size - r]), r, cov


# ---------------------------------------------------------------------------------- D018 secondary graph (PREREG_v4 9.5, GAP-2)
def secondary_graph(m: int = 5):
    """(nodes, weights, G) of the secondary family: for each test i a node N_i (initial weight 1/m) and a node S_i (initial weight 0);
    edges N_i -> S_i (1) and S_i -> N_j (1/(m-1)) for j != i. With alpha = 0.025 the initial level of N_i is 0.025/m = 0.005 for m = 5."""
    nodes = tuple(["N%d" % i for i in range(1, m + 1)] + ["S%d" % i for i in range(1, m + 1)])
    w = np.zeros(2 * m)
    w[:m] = 1.0 / m
    G = np.zeros((2 * m, 2 * m))
    for i in range(m):
        G[i, m + i] = 1.0
        for j in range(m):
            if j != i:
                G[m + i, j] = 1.0 / (m - 1)
    return nodes, w, G


# ---------------------------------------------------------------------------------------- D018 item (f): dependence estimate
def sign_icc_anova(signs, groups, conf: float = 0.95):
    """One-way ANOVA intraclass correlation of 0/1 sign indicators (= the pairwise sign correlation inside a group) with a one-sided upper
    confidence limit (Searle's F-based limit for the one-way random model, unbalanced via n0):
        F = MSB / MSW ;  F_U = F * F_{conf; N-k, k-1} ;  rho_U = (F_U - 1) / (F_U + n0 - 1).
    Few groups make the limit wide (5 folds, 3 labs); it is REPORTED evidence, never a rule input (D018 2.3). Returns a dict."""
    from scipy import stats
    x = np.asarray(signs, dtype=float)
    g = np.asarray(groups)
    labs = np.unique(g)
    k, N = labs.size, x.size
    gs = [x[g == u] for u in labs]
    n0 = (N - sum(len(v) ** 2 for v in gs) / N) / (k - 1)
    msb = sum(len(v) * (v.mean() - x.mean()) ** 2 for v in gs) / (k - 1)
    msw = sum(((v - v.mean()) ** 2).sum() for v in gs) / (N - k)
    if msw <= 0:
        return dict(icc=1.0, upper=1.0, k=k, n0=n0, msb=msb, msw=msw)
    icc = (msb - msw) / (msb + (n0 - 1) * msw)
    f_u = (msb / msw) * stats.f.ppf(conf, N - k, k - 1)
    upper = (f_u - 1.0) / (f_u + n0 - 1.0)
    return dict(icc=float(icc), upper=float(min(upper, 1.0)), k=int(k), n0=float(n0), msb=float(msb), msw=float(msw))


def avg_pairwise_sign_corr(fold, lab, rho_fold: float, rho_lab: float) -> float:
    """Average pairwise sign correlation implied by intra-fold and intra-lab correlations (negative values set to 0; additive,
    pairs in the same fold and the same lab are counted in both): (pairs_same_fold * rho_F + pairs_same_lab * rho_L) / C(N, 2).
    This is the quantity the Beta-binomial rho_s0 bounds."""
    fold, lab = np.asarray(fold), np.asarray(lab)
    N = fold.size
    pf = sum(int(c) * (int(c) - 1) / 2 for c in np.unique(fold, return_counts=True)[1])
    pl = sum(int(c) * (int(c) - 1) / 2 for c in np.unique(lab, return_counts=True)[1])
    return float((pf * max(rho_fold, 0.0) + pl * max(rho_lab, 0.0)) / (N * (N - 1) / 2))


def dependence_report(signs, fold, lab, conf: float = 0.95) -> dict:
    """Item (f) estimator, defined before the freeze. signs = indicator (score difference > its median) per condition from the INNER-CV
    training sides. Returns intra-fold and intra-lab sign ICC (point and one-sided upper limit) and the implied average pairwise sign
    correlation (point and upper), to be compared with rho_s0 = 0.03. Disclosure rule D018 2.3 (ii): if rho_fold point > 0.03 the
    Limitations sentence is added; nothing changes a critical count."""
    f = sign_icc_anova(signs, fold, conf)
    l = sign_icc_anova(signs, lab, conf)
    return dict(rho_fold=f["icc"], rho_fold_upper=f["upper"], rho_lab=l["icc"], rho_lab_upper=l["upper"],
                avg_pairwise=avg_pairwise_sign_corr(fold, lab, f["icc"], l["icc"]),
                avg_pairwise_upper=avg_pairwise_sign_corr(fold, lab, f["upper"], l["upper"]),
                exceeds_rho_s0=bool(f["icc"] > RHO_S0), rho_s0=RHO_S0, conf=conf)
