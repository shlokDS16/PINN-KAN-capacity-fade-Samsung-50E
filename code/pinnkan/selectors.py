"""Comparator selection (PREREG_v4 7.1, 'Comparator selection (no test information)'):

    D*  = the arm of {A9, A11, A12} with the lowest inner-CV condition-mean score on the fold's training conditions at that m
    AG  = the lower of A4 and A5 the same way; at m < 32 AG = A4 (A5 does not run there)

Selection is per (outer fold, m) and uses ONLY the inner-CV scores of the tuned arms (the argument is a dict arm -> inner score; no test score can enter).
Ties go to the candidate listed first (A9 < A11 < A12; A4 < A5). A non-finite score is never chosen. A12R (the raw-feature descriptive row) is not a candidate.
All candidates stay reported against A1 (Table 2); the selected arm's condition scores are what the statistics step uses for D* / AG.
"""
import math

DSTAR_CANDIDATES = ("A9", "A11", "A12")
AG_CANDIDATES = ("A4", "A5")


def choose(inner_scores, candidates):
    """-> {'arm', 'score', 'table', 'candidates_present', 'complete'} or None when no candidate was run"""
    table = {a: float(inner_scores[a]) for a in candidates if a in inner_scores}
    ok = {a: v for a, v in table.items() if math.isfinite(v)}
    if not ok:
        return None
    best = min(candidates, key=lambda a: (ok[a] if a in ok else math.inf, candidates.index(a)))
    return {"arm": best, "score": ok[best], "table": table, "complete": set(table) == set(candidates)}


def select_comparators(inner_scores, m=None):
    """{'D*': ..., 'AG': ...} (keys only for the selectors that have at least one candidate). `inner_scores`: {arm_id: inner-CV condition-mean score (pp)}."""
    out = {"rule": "lowest inner-CV condition-mean score on the training conditions at this (outer fold, m); ties by candidate order; test scores never enter", "m": m}
    d = choose(inner_scores, DSTAR_CANDIDATES)
    if d is not None:
        out["D*"] = d
    ag_c = AG_CANDIDATES if (m is None or int(m) >= 32) else ("A4",)
    g = choose(inner_scores, ag_c)
    if g is not None:
        out["AG"] = g
    return out
