"""Inputs of the display items that the Design R2 statistics step did not produce (code/figures/ALIGN_V4_REPORT.md section 3, gaps G1-G8; code/pinnkan/STATS_GAPS_REPORT.md).

Everything here is DESCRIPTIVE or INTERPRETIVE and additive: nothing in this module sets a tier, a state, a title, a count, a margin or a gate input, and `run_stats_v4` calls it
after every confirmatory quantity is formed (the pre-existing keys of contrasts_v4_B.json and the gate fields of controls.json are unchanged: `strip_new_keys_*` is the registry of the
new keys, and the test of the no-regression rule removes exactly those).

    G1  arm_table            analysis/arm_table.json   Table 1: per arm x grid cell / Test C / S2, pooled mean pp, seed SD, n_conditions, n_params, n_train_used, fit seconds
    G2  reference_record     analysis/reference.json   R_LOO, R_WARP (training sides, 9.10; descriptive, decides nothing)
    G3  nc2_v4, pc2_v4, pc3_v4     controls.json       NC-2 (fixed design-effect sign test of 9.3, 0.025, interpretive), PC-2, PC-3 (reported checks, never gate inputs)
    G4  law_summary          analysis/law_summary.json  closed forms, coefficient counts, training-side BIC, stability metric, partial dependences of A15 / G15 (11a items 6-7)
    G6  merge_residual_cells analysis/residual_map.npz  pooled |R| map over the five outer folds from the raw cell-level values
    G7  qt_interval          contrasts_v4_B.json secondary.tests.QT_g1.median_interval
    G8  candidates_vs_a1     contrasts_v4_B.json candidates_vs_a1 (A11, A12, A4, A5 against A1 at g4; outside every family and the graph)
(G5, the curves of Figs. 5 and 6, is `physval.figure_inputs`.)

Integrity errors (unequal condition sets, a negative run that is not a permute_stress run of Test B, runs of different folds) raise; a missing optional input gives a record whose `status`
says `not available: ...` and never a verdict. The sign test is the one of the P chain: `stats_v4.SignRule.test` (ties and L = margin are not positive, n is not reduced), Beta-binomial
design effect rho_s0 from the pinned configuration (30 of 40 at 0.025).
"""
import copy
import json
import os

import numpy as np

from . import graph_test as gt
from . import stats_v4 as v4

G1_, G4_ = v4.G1, v4.G4
CANDIDATES = ("A11", "A12", "A4", "A5")
class NeedsRescoreError(ValueError):
    """an input-integrity error of a registered control whose cure needs a scored configuration to be run again (stop rule 6): the control is recorded as failed with its fixed sentence and the step
    continues (PREREG_v4 10: "NC-2 never stops the study"). Any other exception is a code / compute error and stops a strict run."""


FAIL_SENTENCES = {"NC-2": "stress dependence was not shown necessary for the accuracy",
                  "PC-3": "At g4 the network's median condition error was not shown lower than carrying the last check-up forward (a reported check outside the family-wise count)"}


def rescore_record(name, reason):
    """the record of a registered control that failed because its inputs cannot be repaired without re-running a scored configuration"""
    return {"status": "failed: the inputs cannot be repaired without re-running a scored configuration (stop rule 6)", "passed": False, "failed_needs_rescore": True, "reason": reason,
            "fail_sentence": FAIL_SENTENCES[name], "gating": False}


NC2_ALPHA = 0.025            # section 10 / 9.3: NC-2 and PC-3 are tested at 0.025 whatever the graph alpha is
NC2_WORDING = "the accuracy of the learned law depends on the stress dependence it learns"


def _load(p):
    with open(p, encoding="utf8") as fh:
        return json.load(fh)


def _cfg(d):
    return _load(os.path.join(d, "config.json"))


def _m_of(d):
    c = _cfg(d)
    return 32 if c.get("m") is None else int(c["m"])


def _g4_dirs(run_dirs, name=None):
    """the m = 32 grid runs (g4 is m = 32 at k = full), optionally only those holding the file `name`"""
    return [d for d in run_dirs if _m_of(d) == 32 and (name is None or os.path.exists(os.path.join(d, name)))]


# ------------------------------------------------------------------------------------------------ G1 arm table
def _pool_blocks(blocks):
    """blocks: list of {arm: run-writer metrics block} (one per outer-fold run) -> {arm: pooled record}. Pooled mean = mean over all scored conditions (the per-fold means weighted by their
    condition counts); `seed_sd_pp` = SD over the seeds of the SINGLE-SEED pooled mean (`mean_pp_per_seed`), folds' seed noise taken as independent (sqrt(sum (w_f sd_f)^2); each sd_f is the SD over
    seeds of the single-seed cross-condition mean of fold f); the ensemble endpoint `mean_pp` has no seed replicate of its own. `seed_sd_pp_upper_bound` = sum w_f sd_f (perfectly correlated
    seeds). n_params, n_train_used, fit seconds: mean over the fold runs (with the range)."""
    res = {}
    for a in sorted({a for b in blocks for a in b}):
        bb = [b[a] for b in blocks if a in b]
        n = np.array([x["n_conditions"] for x in bb], float)
        if not n.sum():
            continue
        w = n / n.sum()
        sd = np.array([np.nan if x.get("seed_sd_of_mean") is None else float(x["seed_sd_of_mean"]) for x in bb])
        per_seed = [x.get("primary_pp_per_seed") for x in bb]
        res[a] = dict(mean_pp=float(np.sum(w * [x["primary_pp"] for x in bb])),
                      mean_pp_per_seed=(float(np.sum(w * per_seed)) if all(v is not None for v in per_seed) else None),
                      seed_sd_pp=float(np.sqrt(np.sum((w * sd) ** 2))) if not np.isnan(sd).any() else None,
                      seed_sd_pp_upper_bound=float(np.sum(w * sd)) if not np.isnan(sd).any() else None,
                      n_conditions=int(n.sum()), n_folds=len(bb),
                      n_params=float(np.mean([x["n_params"] for x in bb])), n_params_range=[min(x["n_params"] for x in bb), max(x["n_params"] for x in bb)],
                      n_train_used=float(np.mean([x["n_train_used"] for x in bb])), n_train_used_range=[min(x["n_train_used"] for x in bb), max(x["n_train_used"] for x in bb)],
                      fit_seconds=float(np.mean([x["fit_seconds_one_fit"] for x in bb])),
                      fit_seconds_ensemble=(float(np.mean([x["fit_seconds_ensemble"] for x in bb])) if all("fit_seconds_ensemble" in x for x in bb) else None))
    return res


def _blocks_by_cell(run_dirs):
    out = {}
    for d in run_dirs:
        p = os.path.join(d, "metrics.json")
        if not os.path.exists(p):
            continue
        met, m = _load(p), _m_of(d)
        if met.get("outer_test_by_k"):
            for kl, blk in met["outer_test_by_k"].items():
                out.setdefault((m, str(kl)), []).append(blk)
        elif met.get("outer_test"):
            out.setdefault((m, str(met.get("k_primary", "full"))), []).append(met["outer_test"])
    return out


def _single_blocks(run_dirs):
    """Test C / S2 runs: the k_full cell (the `outer_test` block, or the primary k of `outer_test_by_k`)"""
    out = []
    for d in run_dirs or []:
        p = os.path.join(d, "metrics.json")
        if not os.path.exists(p):
            continue
        met = _load(p)
        blk = met.get("outer_test") or (met.get("outer_test_by_k") or {}).get(str(met.get("k_primary", "full")))
        if blk:
            out.append(blk)
    return out


def arm_table(run_dirs, test_c_runs=None, s2_runs=None):
    """G1: Table 1 inputs (PREREG_v4 14) from the run files. Format: {"cells": {"m|k": {arm: {mean_pp, seed_sd_pp, n_conditions, n_params, n_train_used, fit_seconds, ...}}}, "test_c": {arm: ...}, "s2": {arm: ...}}"""
    cells = {f"{m}|{k}": _pool_blocks(b) for (m, k), b in sorted(_blocks_by_cell(run_dirs).items(), key=lambda kv: (kv[0][0], {"0": 0, "2": 1, "full": 2}.get(kv[0][1], 9)))}
    return {"producer": "stats_step.run_stats_v4 (stats_gaps.arm_table); descriptive, read from metrics.json of the runs",
            "definition": ("mean_pp = mean over all scored conditions of the primary endpoint (fold means weighted by their condition counts); seed_sd_pp = SD over the seeds of the single-seed pooled mean "
                           "(mean_pp_per_seed; folds independent; the ensemble endpoint mean_pp has no seed replicate of its own; upper bound without independence: seed_sd_pp_upper_bound); n_params, n_train_used and fit_seconds (one fit) = mean over the fold runs"),
            "cells": cells, "test_c": _pool_blocks(_single_blocks(test_c_runs)), "s2": _pool_blocks(_single_blocks(s2_runs))}


# ------------------------------------------------------------------------------------------------ G2 reference quantities
def reference_record(run_dirs, test_c_runs=None, s2_runs=None):
    """G2: {"B": {R_LOO, R_WARP, n_folds}, "C": ..., "S2": ...} (the median over outer folds of the training-side reference quantities of the runs that wrote reference_values.json).
    B is read from the m = 32 runs (full-data training sides); entries without any reference_values.json are omitted. Descriptive: decides nothing (9.10)."""
    from . import stats_step as ss
    per = {}
    for name, dirs in (("B", _g4_dirs(run_dirs)), ("C", test_c_runs), ("S2", s2_runs)):
        r = ss.reference_from_runs(list(dirs)) if dirs else None
        if r:
            per[name] = r
    return per


# ------------------------------------------------------------------------------------------------ G3 controls
def _ok(p, alpha):
    return bool(p <= alpha * (1 + gt.TOL))


def nc2_v4(real_store, neg_store, rule, alpha=NC2_ALPHA):
    """NC-2 (interpretive, never a gate; PREREG_v4 10): L_c = ln(S_A1,permuted,c / S_A1,real,c) paired by condition at g4; one-sided fixed design-effect sign test of median(L) > 0 at `alpha`
    (the rule of the P chain: ties and L = 0 not positive, n not reduced; 30 of 40 at 0.025). Descriptive rows: L(A9/A1) under real and permuted stress and the scores of A1, A9, R1, R2 under
    permutation (an arm that the permuted runs did not fit is None)."""
    if not (real_store.has("A1", *G4_) and neg_store.has("A1", *G4_)):
        raise NeedsRescoreError("NC-2 needs A1 at g4 in the real and in the permuted runs")
    R, P = real_store.scores("A1", *G4_), neg_store.scores("A1", *G4_)
    if set(R) != set(P):
        raise NeedsRescoreError("NC-2 pairs the same held-out conditions: the real and the permuted run score different condition sets")
    fr, fn = real_store.notes.get("cell_folds", {}).get(real_store.key(*G4_)), neg_store.notes.get("cell_folds", {}).get(neg_store.key(*G4_))
    if fr is not None and fn is not None and set(fr) != set(fn):
        raise NeedsRescoreError(f"NC-2: the permuted runs cover the outer folds {sorted(fn)}, the real g4 runs {sorted(fr)}")
    conds = sorted(R)
    L = np.array([np.log(P[c] / R[c]) for c in conds])
    pos, n, p = rule.test(L, 0.0)
    pl, nl, pp_ = v4.PLAIN.test(L, 0.0)
    lo, hi, r, cov = rule.interval(L, 0.05)
    desc = {"scores_mean_pp": {"real": {}, "permuted": {}}}
    for a in ("A1", "A9", "R1", "R2"):
        desc["scores_mean_pp"]["real"][a] = float(np.mean(list(real_store.scores(a, *G4_).values()))) if real_store.has(a, *G4_) else None
        desc["scores_mean_pp"]["permuted"][a] = float(np.mean(list(neg_store.scores(a, *G4_).values()))) if neg_store.has(a, *G4_) else None
    for tag, st in (("real", real_store), ("permuted", neg_store)):
        if st.has("A9", *G4_) and st.has("A1", *G4_):
            c9, a9, a1 = st.pair("A9", "A1", G4_)          # the V3 descriptive row: ln(S_A9 / S_A1)
            l = np.log(a9 / a1)
            desc[f"L_A9_over_A1_{tag}"] = {"n": int(l.size), "median": float(np.median(l)), "mean": float(l.mean())}
        else:
            desc[f"L_A9_over_A1_{tag}"] = None
    return dict(test="B", cell=list(G4_), n=int(n), k_positive=int(pos), median_L=float(np.median(L)), rel_increase_median=float(np.exp(np.median(L)) - 1.0), median_ci95=[lo, hi], interval_rank=r,
                p_one_sided=float(p), crit_positives=int(rule.crit(n, alpha)), alpha=alpha, passed=_ok(p, alpha), sign_rule=rule.describe(),
                plain_exact_descriptive={"positives": int(pl), "n": int(nl), "p": float(pp_), "label": "independent-conditions row (descriptive)"},
                wording=NC2_WORDING, wording_rule="a pass permits the Discussion sentence (section 10), a fail removes it; no tier, no state and no title depends on NC-2",
                L_by_cond={c: float(v) for c, v in zip(conds, L)}, descriptive=desc, gating=False, interpretive=True)


def _absent(require, msg):
    """a registered input is absent: with `require` (strict run at the FROZEN commit, PREREG_v4 10 as amended: every absence except the data reason is a failure to compute) raise, else the record says so"""
    if require:
        raise ValueError(msg)
    return dict(status="not evaluated: " + msg, passed=None, gating=False)


def pc3_v4(store, rule, alpha=NC2_ALPHA, require=False):
    """PC-3 (reported, not a gate; PREREG_v4 10): A1 beats R1 (persistence) at g4 with margin 0 (the M3 machinery of g1 at g4: L = ln(S_R1 / S_A1), fixed design-effect sign test at `alpha`).
    R1 and A1 must score the same conditions (n is never reduced); with `require`, an absence raises ValueError (a failure to compute)."""
    if not (store.has("A1", *G4_) and store.has("R1", *G4_)):
        return _absent(require, "R1 or A1 is not scored at g4")
    a1, r1 = store.scores("A1", *G4_), store.scores("R1", *G4_)
    if set(a1) != set(r1):                                  # store.L would intersect the condition sets and reduce n silently (9.3: n is not reduced)
        if require:
            raise NeedsRescoreError(f"R1 scores {len(r1)} and A1 {len(a1)} conditions at g4 (n would be reduced)")
        return _absent(require, f"R1 scores {len(r1)} and A1 {len(a1)} conditions at g4 (n would be reduced)")
    _, L, _ = store.L("A1", "R1", G4_)
    pos, n, p = rule.test(L, 0.0)
    pl, nl, pp_ = v4.PLAIN.test(L, 0.0)
    lo, hi, r, cov = rule.interval(L, 0.05)
    return dict(status="evaluated", cell=list(G4_), n=int(n), positives=int(pos), p=float(p), crit_positives=int(rule.crit(n, alpha)), alpha=alpha, passed=_ok(p, alpha), median_L=float(np.median(L)),
                median_ci95=[lo, hi], plain_exact_descriptive={"positives": int(pl), "n": int(nl), "p": float(pp_)}, sign_rule=rule.describe(), gating=False,
                rule="A1 beats persistence at g4 with margin 0 (L = ln(S_R1 / S_A1) > 0); reported, never a gate input")


def _storage_points(dirs):
    pts = set()
    for d in dirs:
        p = os.path.join(d, "storage_hull.json")
        if os.path.exists(p):
            pts |= {(float(a), float(b)) for a, b in _load(p)["points_T_SOCpct"]}
    return sorted(pts)


def _inside_hull(points, q):
    """is the point q = (T, SOC) inside (or on) the convex hull of `points`? No substitute rule (T1): points that do not span the plane raise ValueError (a failure to compute)"""
    pts = np.asarray(points, float)
    try:
        from scipy.spatial import Delaunay
        return bool(Delaunay(pts).find_simplex(np.asarray(q, float), tol=1e-9) >= 0), "convex hull"
    except Exception as e:  # noqa: BLE001  (Qhull error for collinear or too few points)
        raise ValueError("storage points do not span (T, SOC): PC-2 hull undefined") from e


PC2_T_GRID, PC2_SOC_GRID = [10.0, 23.0, 45.0], [float(x) for x in np.arange(0, 101, 5.0)]          # PREREG_v4 10 (T1)


def pc2_v4(run_dirs, require=False):
    """PC-2 (reported, not a gate; PREREG_v4 10 and 11a item 3): the fitted calendar rate of A1 increases strictly with temperature at every SOC inside the storage hull. Evaluated on every
    fold x seed member of the g4 (m = 32) runs and on the mean curve; `passed` = every member at every evaluated SOC (the most conservative reading). The hull is the convex hull of the
    training storage cells pooled over the folds (storage_hull.json). No substitute rule: if any g4 run lacks stress_functions.json or storage_hull.json, PC-2 is not evaluated (None), or with
    `require` (strict run at the FROZEN commit) ValueError: a failure to compute. Only "no SOC level with two storage temperatures inside the hull" stays `not evaluated` (the data reason).
    The grid is asserted: T = 10, 23, 45 C and SOC = 0, 5, ..., 100 % (T1)."""
    from . import physval
    all32 = _g4_dirs(run_dirs)
    dirs = _g4_dirs(run_dirs, "stress_functions.json")
    if not dirs or len(dirs) != len(all32):
        return _absent(require, f"stress_functions.json in {len(dirs)} of {len(all32)} g4 runs")
    if not all(os.path.exists(os.path.join(d, "storage_hull.json")) for d in dirs):
        return _absent(require, "storage_hull.json missing in a g4 run (no substitute rule)")
    M = physval.merge_stress_functions(dirs)
    T = np.array(M["T_C"], float)
    order = np.argsort(T)
    T, rate, soc = T[order], np.asarray(M["rate"], float)[:, order, :], np.asarray(M["soc"], float)
    if T.tolist() != PC2_T_GRID or soc.tolist() != PC2_SOC_GRID:
        raise ValueError("PC-2 grid differs from PREREG_v4 10 (T1)")
    pts = _storage_points(dirs)
    if not pts:
        return _absent(require, "storage_hull.json holds no storage point")
    method = None
    evaluated, excluded, bad = [], [], []
    mean_curve = rate.mean(0)
    mean_ok = True
    for j, s in enumerate(soc):
        ins = []
        for i, t in enumerate(T):
            ok, method = _inside_hull(pts, (t, s))
            if ok:
                ins.append(i)
        if len(ins) < 2:
            excluded.append(float(s))
            continue
        evaluated.append(float(s))
        mean_ok = mean_ok and bool(np.all(np.diff(mean_curve[ins, j]) > 0))
        for m_ in range(rate.shape[0]):
            if not np.all(np.diff(rate[m_, ins, j]) > 0):
                bad.append((int(m_), float(s)))
    if not evaluated:
        return dict(status="not evaluated: no SOC level has two temperatures inside the storage hull", passed=None, gating=False, hull=method)
    return dict(status="evaluated", passed=bool(not bad), mean_curve_increasing=bool(mean_ok), n_members=int(rate.shape[0]), n_folds=len(dirs), soc_evaluated=evaluated, soc_excluded_outside_hull=excluded,
                members_failing=len(set(m_ for m_, _ in bad)), first_violations=[{"member": m_, "soc": s} for m_, s in bad[:5]], T_C=T.tolist(), hull=method,
                rule="strictly increasing in T between neighbouring storage temperatures at every SOC with at least two temperatures inside the training storage hull; every fold x seed member must pass",
                gating=False)


def extend_controls(controls, nc2=None, pc2=None, pc3=None):
    """-> a COPY of `controls` with negative.nc2 (when given), positive.P2_monotone_in_T / P3_passed (+ details) and gate_G.reported_checks filled from them. gate_G.tripped, .reasons,
    .not_evaluated and .rule are asserted unchanged (PC-2, PC-3 and NC-2 are not gate inputs)."""
    from . import stats_step as ss
    out = copy.deepcopy(controls)
    if nc2 is not None:
        out["negative"] = dict(out.get("negative") or {})
        out["negative"]["nc2"] = nc2
    pos = out.setdefault("positive", {})
    if pc2 is not None:
        pos["P2_monotone_in_T"] = pc2.get("passed")
        pos["PC2_detail"] = pc2
    if pc3 is not None:
        pos["P3_passed"] = pc3.get("passed")
        if pc3.get("median_L") is not None:
            pos["P3_A1_beats_R1_median_L"] = pc3["median_L"]
        pos["PC3_detail"] = pc3
    new_gate = ss.gate_g(out)
    for k in ("tripped", "reasons", "not_evaluated", "rule"):
        if new_gate[k] != controls["gate_G"][k]:
            raise AssertionError(f"gate_G.{k} changed by the reported checks: {controls['gate_G'][k]!r} -> {new_gate[k]!r}")
    out["gate_G"] = new_gate
    return out


# ------------------------------------------------------------------------------------------------ G7, G8
def qt_interval(store, rule):
    """G7: Q-T (A13) beside the existing secondary test: the median log ratio L = ln(S_A13 / S_A1) at g1 with the unadjusted fallback 95 % order-statistic interval of the rule (the interval type of
    `stats_v4._stat`, i.e. of the qualifier-sentence numbers of the secondary family), the relative reduction with its interval, counts, mean pp (BCa) and the worst condition. None without A13."""
    if not (store.has("A1", *G1_) and store.has("A13", *G1_)):
        return None
    e = v4.entry(store, "A1 vs A13 (Q-T)", "A1", "A13", G1_, rule)
    e["interval_type"] = "unadjusted fallback 95 % order-statistic interval of the median (design-effect rank), as the qualifier sentences of the secondary family"
    e["label"] = "structured interval beside the secondary test QT_g1; the tier of Q-T is set by the secondary graph only"
    return e


def candidates_vs_a1(store, rule, cands=CANDIDATES, cell=G4_):
    """G8 (Table 2, 'candidates against A1'): each of A11, A12, A4, A5 against A1 individually at g4, `stats_v4.entry` records (median L, unadjusted 95 % interval, counts, mean pp with BCa,
    worst condition, per-fold medians). Descriptive: outside every family and the graph, no tier word, no error control."""
    rows, missing = {}, []
    for a in cands:
        if store.has("A1", *cell) and store.has(a, *cell):
            rows[a] = v4.entry(store, f"A1 vs {a}", "A1", a, cell, rule)
        else:
            missing.append(a)
    return {"label": "descriptive (Table 2, candidates against A1): outside every family and the graph; no tier word, no error control; changes no count, tier or title",
            "cell": list(cell), "rows": rows, "not_scored_at_this_cell": missing}


# ------------------------------------------------------------------------------------------------ G4 extracted laws
def _arm_family(key):
    return "G15" if key == "G15" else "A15"


def _hull_mask(points, X):
    """boolean mask of the rows of X inside the convex hull of `points` (Delaunay), else inside their bounding box; -> (mask, method)"""
    pts = np.asarray(points, float)
    try:
        from scipy.spatial import Delaunay
        return Delaunay(pts).find_simplex(X, tol=1e-9) >= 0, "convex hull"
    except Exception:  # noqa: BLE001
        return np.all((X >= pts.min(0) - 1e-9) & (X <= pts.max(0) + 1e-9), axis=1), "bounding box"


def stability_metric(laws, hulls, lhs):
    """11a item 6: the median, over the points of the fixed Latin hypercube that lie inside the intersection of the training hulls of all folds present, of the fold-to-fold SD of the predicted
    log-rate divided by its range. laws: [{fold, seed, log_rate (n points)}]; hulls: {fold: training stress rows}. SD at a point: sqrt of the mean over seeds of the variance across folds
    (ddof = 1; seeds present in every fold); range: max - min over those points of the mean log-rate over folds and seeds (the smaller of the two readings, so the larger metric)."""
    folds = sorted({l["fold"] for l in laws})
    if len(folds) < 2:
        return dict(status="not available: fewer than two outer folds")
    X = np.asarray(lhs, float)
    inside, methods = np.ones(len(X), bool), {}
    for f in folds:
        mk, how = _hull_mask(hulls[f], X)
        inside &= mk
        methods[str(f)] = how
    seeds = sorted(set.intersection(*[{l["seed"] for l in laws if l["fold"] == f} for f in folds]))
    if not inside.any() or not seeds:
        return dict(status="not available: no Latin-hypercube point inside the intersection of the training hulls" if not inside.any() else "not available: no seed present in every fold",
                    n_points_inside=int(inside.sum()), hull_method=methods)
    V = np.array([[next(np.asarray(l["log_rate"], float)[inside] for l in laws if l["fold"] == f and l["seed"] == s) for s in seeds] for f in folds])       # folds x seeds x points
    sd = np.sqrt(np.mean(np.var(V, axis=0, ddof=1), axis=0))
    rng = float(np.ptp(V.mean(axis=(0, 1))))
    per_seed = [float(np.median(np.std(V[:, i, :], axis=0, ddof=1) / max(float(np.ptp(V[:, i, :].mean(0))), 1e-300))) for i in range(len(seeds))]
    return dict(status="evaluated", n_points=int(len(X)), n_points_inside=int(inside.sum()), n_folds=len(folds), n_seeds=len(seeds), hull_method=methods,
                median_sd_over_range=float(np.median(sd) / rng) if rng > 0 else None, range_log_rate=rng, median_sd=float(np.median(sd)), per_seed_median_sd_over_range=per_seed,
                definition="median over the Latin-hypercube points inside the intersection of the training hulls of the fold-to-fold SD of the predicted log-rate (pooled over seeds) divided by the range "
                           "of the fold-and-seed mean log-rate over those points")


def law_summary(run_dirs, m=32):
    """G4: A15 and G15 side by side from the `extracted_law_forms.json` of the g4 runs (written by the run writer): the closed forms (final coefficients, temperature masked), the coefficient
    counts and training-side BIC, the stability metric, and the partial-dependence envelopes of the non-temperature inputs. Descriptive (11a items 6 and 7); no licence word, no comparative
    wording, no form or sign for temperature. The `representative` law of an arm is the one with the median training-side BIC (ties: lowest fold, seed)."""
    from .extraction_audit import load_thresholds
    thr = load_thresholds()
    files = [(d, _load(os.path.join(d, "extracted_law_forms.json"))) for d in _g4_dirs(run_dirs, "extracted_law_forms.json")]
    if not files:
        return dict(status="not available: no extracted_law_forms.json in the m = 32 runs (the run writer writes it for runs with A15 / G15)")
    lhs = np.asarray(files[0][1]["lhs"]["points"], float)
    for _, f in files[1:]:
        if not np.allclose(np.asarray(f["lhs"]["points"], float), lhs):
            raise ValueError("extracted_law_forms.json files with different Latin hypercubes cannot be merged")
    hulls = {int(f["fold"]): np.asarray(f["train_hull_points"], float) for _, f in files}
    if len(hulls) != len(files):
        raise ValueError("two runs of the same outer fold among the extracted_law_forms.json files")
    grid = files[0][1]["pd_grid"]
    laws = {"A15": [], "G15": []}
    for _, f in files:
        for l in f["laws"]:
            laws[_arm_family(l["arm"])].append(l)
    out = {"label": thr["wording"]["stability_table_caption"], "m": m, "n_runs": len(files), "contribution": False, "arms": {}, "temperature": {"display": thr["wording"]["temperature_label"], "note": thr["wording"]["temperature_note"]}}
    for arm, ls in laws.items():
        if not ls:
            continue
        nc, bic = np.array([l["n_coefs"] for l in ls], float), np.array([l["train_bic"] for l in ls], float)
        stab = stability_metric([dict(fold=l["fold"], seed=l["seed"], log_rate=l["log_rate_on_lhs"]) for l in ls], hulls, lhs)
        order = sorted(range(len(ls)), key=lambda i: (bic[i], ls[i]["fold"], ls[i]["seed"]))
        rep = ls[order[(len(ls) - 1) // 2]]
        pdc = {}
        for var in sorted(grid):
            Y = np.array([l["pd"][var] for l in ls], float)
            pdc[var] = dict(x=grid[var], median=np.median(Y, 0).tolist(), lo=Y.min(0).tolist(), hi=Y.max(0).tolist(), n_laws=int(len(ls)))
        out["arms"][arm] = dict(
            n_laws=len(ls), complete=bool(len(ls) == 25), n_coefs=dict(median=float(np.median(nc)), min=float(nc.min()), max=float(nc.max())),
            n_params=dict(median=float(np.median([l["n_params"] for l in ls]))), train_bic=dict(median=float(np.median(bic)), min=float(bic.min()), max=float(bic.max()), note="training-side BIC of the law (printed beside K2)"),
            stability=stab, partial_dependence=pdc,
            representative=dict(fold=rep["fold"], seed=rep["seed"], arm=rep["arm"], n_coefs=rep["n_coefs"], train_bic=rep["train_bic"], closed_form=rep["closed_form"], cyclic=rep["cyclic"], calendar=rep["calendar"],
                                rule="the law with the median training-side BIC of the arm (the lower median for an even count; ties: lowest fold, seed)"),
            closed_forms=[dict(fold=l["fold"], seed=l["seed"], arm=l["arm"], n_coefs=l["n_coefs"], train_bic=l["train_bic"], closed_form=l["closed_form"]) for l in sorted(ls, key=lambda l: (l["fold"], l["seed"]))])
    return out


# ------------------------------------------------------------------------------------------------ G6 merged residual map
def merge_residual_cells(run_dirs, T_edges=None, soc_edges=None, cch_edges=None):
    """G6: the residual map pooled over the outer folds from the raw cell-level values of residual_cells.npz (n_cells x members x n_t per run). Each scored cell belongs to exactly one outer
    fold (a repeated cell id raises); a bin's value is the median of ALL |R| values of the cells in that bin (no median of fold or cell medians). Bin edges as residual_map.npz of the run
    writer. -> dict of arrays (the keys of residual_map.npz plus counts) or None when no run has the file."""
    T_edges = np.linspace(5, 50, 5) if T_edges is None else np.asarray(T_edges, float)
    soc_edges = np.linspace(0, 100, 6) if soc_edges is None else np.asarray(soc_edges, float)
    cch_edges = np.linspace(0, 1.2, 5) if cch_edges is None else np.asarray(cch_edges, float)
    dirs = _g4_dirs(run_dirs, "residual_cells.npz")
    if not dirs:
        return None
    parts = [dict(np.load(os.path.join(d, "residual_cells.npz"))) for d in dirs]
    ids = np.concatenate([p["cell_id"] for p in parts])
    if len(set(ids.tolist())) != len(ids):
        raise ValueError("a scored cell appears in more than one outer-fold run: the merged residual map needs each test cell exactly once")
    T, soc, cch = (np.concatenate([p[k] for p in parts]) for k in ("T", "soc_mid", "c_ch"))
    A = [np.asarray(p["absR"][i], float).reshape(-1) for p in parts for i in range(len(p["T"]))]          # the raw |R| values of every cell (members x times)
    train_ts, train_ct = [], []
    for d in _g4_dirs(run_dirs, "residual_map.npz"):
        z = np.load(os.path.join(d, "residual_map.npz"))
        train_ts.append(z["train_T_SOC"])
        train_ct.append(z["train_cch_T"])

    def binned(xv, xe, yv, ye):
        ix = np.digitize(xv, xe) - 1
        iy = np.digitize(yv, ye) - 1
        ix = np.where(xv == xe[-1], len(xe) - 2, ix)
        iy = np.where(yv == ye[-1], len(ye) - 2, iy)
        Z = np.full((len(ye) - 1, len(xe) - 1), np.nan)
        N = np.zeros((len(ye) - 1, len(xe) - 1), int)
        for a in range(len(ye) - 1):
            for b in range(len(xe) - 1):
                sel = (iy == a) & (ix == b)
                N[a, b] = int(sel.sum())
                if sel.any():
                    Z[a, b] = float(np.median(np.concatenate([A[i] for i in np.flatnonzero(sel)])))
        return Z, N, int(((ix < 0) | (ix >= len(xe) - 1) | (iy < 0) | (iy >= len(ye) - 1)).sum())
    Z1, N1, out1 = binned(soc, soc_edges, T, T_edges)
    Z2, N2, out2 = binned(cch, cch_edges, T, T_edges)
    uniq = lambda arrs: np.unique(np.round(np.concatenate(arrs), 6), axis=0) if arrs else np.zeros((0, 2))
    return dict(T_edges=T_edges, soc_edges=soc_edges, cch_edges=cch_edges, absR_T_SOC=Z1, absR_cch_T=Z2, n_cells_T_SOC=N1, n_cells_cch_T=N2, n_cells=np.array(len(ids)), n_outside_T_SOC=np.array(out1),
                n_outside_cch_T=np.array(out2), train_T_SOC=uniq(train_ts), train_cch_T=uniq(train_ct))
