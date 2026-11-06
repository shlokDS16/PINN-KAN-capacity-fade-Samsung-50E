"""The four automatic-downgrade sensitivity rows of PREREG_v4 9.8 rule 2 / 9.9 (D016 judge 2 rule 2; D018 GAP-4) and the Test C / S2 descriptive tables.

    (i)   lab-stratified          post-stratified weighted median of L (stratum = majority laboratory, weight 1/3 per laboratory, equal inside a laboratory) with the
                                  one-sided lower bound of a within-stratum bootstrap at the contrast's level (MC seed rule); can only lower a tier
    (ii)  lab-and-stage indicator  a re-run of the grid cells g1 and g4 with `lab_indicator: true` (indicators enter the per-cell prior mean of delta_c for A1, A9 (z_c prior), A2, A13,
                                  A15, G15, the per-cell factor prior of A10 and the feature set of D*): a Store built from those runs
    (iii) retain-every-check-up    a re-run with `retain_all: true` (outlier rule off)
    (iv)  random subset at g1      three seeded random nested subsets in place of max-min, for A1 and the D* candidates; condition scores averaged over the three
Rows (ii)-(iv) are recomputed by `row_tiers`: every gated and secondary contrast the row covers is tested at the final local level it had in the primary analysis (no re-run of the
graph), on the scale reverse S < none < N < S (binary for P2, P3, K1, the 'most' test). The lowest tier over the primary analysis and the rows is the tier used in the abstract and in
the state definitions (`stats_v4.run_v4(row_tiers=...)`). A missing row is recorded as not run and the outcome is flagged provisional.
"""
import numpy as np

from . import graph_test as gt
from . import stats_v4 as v4
from .negcontrol import mc_rng

B_BOOT = 10000
LAB_STRATUM_WEIGHT = "1/3 per laboratory (equal weight per condition inside a laboratory)"
ROWS = ("lab_stratified", "lab_indicator", "retain_all", "random_subset")


# ------------------------------------------------------------------------------------------------ levels of the primary analysis
def primary_levels(out):
    """final local levels of the gated nodes and the secondary slots of a `run_v4` result"""
    nodes = out["primary"]["nodes"]
    lv = {k: float(v["level"]) for k, v in nodes.items() if "level" in v}
    sec = {k: {"N": float(t["N_level"]), "S": float(t["S_level"]), "slot": float(t["slot_level"])} for k, t in out["secondary"]["tests"].items()}
    return lv, sec


def _positives_reach(rule, L, margin, level):
    """does the sign test of median(L) > margin reach its critical count at `level`?"""
    if level is None or level <= 0:
        return False
    pos, n, p = rule.test(L, margin)
    return bool(n > 0 and p <= level * (1 + gt.TOL))


def _tier3(rule, L, level_N, level_S, level_rev):
    if _positives_reach(rule, -L, v4.LOG_S, level_rev):
        return "reverse S"
    if _positives_reach(rule, L, v4.LOG_S, level_S):
        return "S"
    if _positives_reach(rule, L, v4.LOG_N, level_N):
        return "N"
    return "none"


# ------------------------------------------------------------------------------------------------ rows (ii)-(iv): tiers from a re-computed store
def row_tiers(out, store, rule, cells="g1g4"):
    """tiers of every gated / secondary contrast the row covers, at the primary final levels. cells 'g1' restricts to the g1 contrasts (row (iv): P1, P2 only)."""
    lv, sec = primary_levels(out)
    G1, G4 = v4.G1, v4.G4
    t = {}
    has = lambda a, c: store.has(a, *c)
    rev = out["config"]["alpha"]
    if has("A1", G1) and has("D*", G1) and "P1N" in lv:
        _, L, _ = store.L("A1", "D*", G1)
        t["P1"] = _tier3(rule, L, lv["P1N"], lv["P1S"], rev)
    if has("A1", G1) and has("A9", G1) and "P2" in lv:
        _, L, _ = store.L("A1", "A9", G1)
        t["P2"] = _positives_reach(rule, L, v4.LOG_S, lv["P2"])
    md = v4.most_d(store)
    if md is not None and "P2" in lv:                    # review I2: the GAP-1 'most' test is recomputed under every row (binary pass/fail at 0.025)
        t["most"] = _positives_reach(rule, md[3], 0.0, rev)
    if cells == "g1":
        return t
    if "P3" in lv and has("A1", G1) and has("A1", G4) and has("D*", G1) and has("D*", G4):
        c1, L1, _ = store.L("A1", "D*", G1)
        c4, L4, _ = store.L("A1", "D*", G4)
        common = sorted(set(c1) & set(c4))
        D = np.array([L1[c1.index(c)] - L4[c4.index(c)] for c in common])
        t["P3"] = _positives_reach(rule, D, 0.0, lv["P3"])
    kv = store.seed_view()                                                     # K chain: per-seed scores (D020 C1 item 4)
    if "K1" in lv and kv.has("A15", *G4) and kv.has("A1", *G4):
        _, L, _ = kv.L("A15", "A1", G4)
        t["K1"] = _positives_reach(rule, L, v4.LOG_N, lv["K1"])
    if "K2N" in lv and kv.has("A15", *G4) and kv.has("G15", *G4):
        _, L, _ = kv.L("A15", "G15", G4)
        t["K2"] = _tier3(rule, L, lv["K2N"], lv["K2S"], rev)
    for name, arm, cell in v4.SECONDARY:
        forms = [f for f in (v4.A10_FORMS if arm == "A10" else (arm,)) if has(f, cell) and has("A1", cell)]
        if not forms or name not in sec:
            continue
        tiers = []
        for f in forms:
            _, L, _ = store.L("A1", f, cell)
            tiers.append(_tier3(rule, L, sec[name]["N"], sec[name]["S"], sec[name]["slot"]))
        t[name] = v4.tier_min(*tiers)
    return t


# ------------------------------------------------------------------------------------------------ row (iv): average the draws
def average_stores(stores):
    """condition scores averaged over the random-subset draws (arms and conditions present in every draw)"""
    cells = set.intersection(*[set(s.tables) for s in stores])
    tables = {}
    for cell in cells:
        arms = set.intersection(*[set(s.tables[cell]) for s in stores])
        tables[cell] = {}
        for a in arms:
            conds = set.intersection(*[set(s.tables[cell][a]) for s in stores])
            tables[cell][a] = {c: float(np.mean([s.tables[cell][a][c] for s in stores])) for c in conds}
    first = stores[0]
    seed = None
    if all(x.seed_tables is not None for x in stores):
        seed = average_stores([v4.Store(x.seed_tables, x.lab, x.fold, x.k_full) for x in stores]).tables
    return v4.Store(tables, first.lab, first.fold, first.k_full, None, seed)


# ------------------------------------------------------------------------------------------------ row (i): lab-stratified
def weighted_median(x, w):
    """lower weighted median: smallest value whose cumulative weight reaches 1/2"""
    o = np.argsort(x, axis=-1, kind="stable")
    xs, ws = np.take_along_axis(x, o, -1), np.take_along_axis(w, o, -1)
    cw = np.cumsum(ws, -1)
    k = (cw >= 0.5 - 1e-12).argmax(-1)
    return np.take_along_axis(xs, k[..., None], -1)[..., 0]


def lab_stratified_bounds(L, labs, levels, label, B=B_BOOT):
    """post-stratified weighted median of L (weight 1/(n_labs n_lab) per condition) and, for each level, the one-sided lower bound (quantile `level`) and the one-sided upper bound
    (quantile 1 - level) of the within-stratum bootstrap distribution. Strata are never resampled across; seed rule SeedSequence([20261105, crc32(label)])."""
    L = np.asarray(L, float)
    labs = np.asarray(labs)
    strata = sorted(set(labs.tolist()))
    idx = [np.nonzero(labs == s)[0] for s in strata]
    w = np.concatenate([np.full(len(i), 1.0 / (len(strata) * len(i))) for i in idx])
    xs = np.concatenate([L[i] for i in idx])
    point = float(weighted_median(xs[None, :], w[None, :])[0])
    rng = mc_rng(label)
    draws = np.concatenate([L[i][rng.integers(0, len(i), (B, len(i)))] for i in idx], axis=1)
    boot = weighted_median(draws, np.tile(w, (B, 1)))
    return {"point": point, "n_strata": len(strata), "strata_sizes": {s: int(len(i)) for s, i in zip(strata, idx)},
            "lower": {str(l): float(np.quantile(boot, l)) for l in levels}, "upper": {str(l): float(np.quantile(boot, 1 - l)) for l in levels}, "B": B}


def lab_stratified_tiers(out, store, B=B_BOOT):
    """row (i): tier of each contrast from the lab-post-stratified weighted median against the margins, lower bound at the contrast's final primary level"""
    lv, sec = primary_levels(out)
    G1, G4 = v4.G1, v4.G4
    has = lambda a, c: store.has(a, *c)
    rev = out["config"]["alpha"]
    labs_of = lambda conds: [store.lab.get(c, "") for c in conds]
    res, t = {}, {}

    def forward(name, L, conds, lvl_N, lvl_S):
        b = lab_stratified_bounds(L, labs_of(conds), sorted({lvl_N, lvl_S, rev}), f"B|lab-stratified|{name}", B)
        res[name] = b
        if b["upper"][str(rev)] < -v4.LOG_S:
            return "reverse S"
        if lvl_S and b["lower"][str(lvl_S)] > v4.LOG_S:
            return "S"
        if lvl_N and b["lower"][str(lvl_N)] > v4.LOG_N:
            return "N"
        return "none"

    def binary(name, L, conds, lvl, margin):
        b = lab_stratified_bounds(L, labs_of(conds), [lvl], f"B|lab-stratified|{name}", B)
        res[name] = b
        return bool(b["lower"][str(lvl)] > margin)

    if has("A1", G1) and has("D*", G1) and "P1N" in lv:
        c, L, _ = store.L("A1", "D*", G1)
        t["P1"] = forward("P1", L, c, lv["P1N"], lv["P1S"])
    if has("A1", G1) and has("A9", G1) and "P2" in lv:
        c, L, _ = store.L("A1", "A9", G1)
        t["P2"] = binary("P2", L, c, lv["P2"], v4.LOG_S)
    md = v4.most_d(store)
    if md is not None and "P2" in lv:
        t["most"] = binary("most", md[3], md[0], rev, 0.0)
    if "P3" in lv and all(has(a, g) for a in ("A1", "D*") for g in (G1, G4)):
        c1, L1, _ = store.L("A1", "D*", G1)
        c4, L4, _ = store.L("A1", "D*", G4)
        common = sorted(set(c1) & set(c4))
        D = np.array([L1[c1.index(c)] - L4[c4.index(c)] for c in common])
        t["P3"] = binary("P3", D, common, lv["P3"], 0.0)
    kv = store.seed_view()                                                     # K chain: per-seed scores
    if "K1" in lv and kv.has("A15", *G4) and kv.has("A1", *G4):
        c, L, _ = kv.L("A15", "A1", G4)
        t["K1"] = binary("K1", L, c, lv["K1"], v4.LOG_N)
    if "K2N" in lv and kv.has("A15", *G4) and kv.has("G15", *G4):
        c, L, _ = kv.L("A15", "G15", G4)
        t["K2"] = forward("K2", L, c, lv["K2N"], lv["K2S"])
    for name, arm, cell in v4.SECONDARY:
        forms = [f for f in (v4.A10_FORMS if arm == "A10" else (arm,)) if has(f, cell) and has("A1", cell)]
        if not forms or name not in sec:
            continue
        tiers = []
        for f in forms:
            c, L, _ = store.L("A1", f, cell)
            tiers.append(forward(f"{name}:{f}", L, c, sec[name]["N"], sec[name]["S"]))
        t[name] = v4.tier_min(*tiers)
    return t, res


# ------------------------------------------------------------------------------------------------ combine
def lowest(*row_dicts):
    """per contrast the lowest tier over the rows (strings on the tier scale, booleans by AND); contrasts a row does not cover are ignored for that row"""
    out = {}
    for d in row_dicts:
        for k, v in (d or {}).items():
            if k not in out:
                out[k] = v
            elif isinstance(v, bool) or isinstance(out[k], bool):
                out[k] = bool(out[k] and v)
            else:
                out[k] = v4.tier_min(out[k], v)
    return out


def _rank(v):
    return int(v) if isinstance(v, bool) else v4.TIER_ORDER.index(v)


def number_sources(first, rows, row_stores, lab_detail, rule):
    """D033 F2: for every gated and secondary contrast, the analysis that set its effective tier = the primary analysis if it is the lowest (ties go to the primary), else the first row
    (i) lab_stratified, (ii) lab_indicator, (iii) retain_all, (iv) random_subset whose tier is the lowest. The brackets of the abstract sentence are filled from that analysis
    (`stats_v4.primary_numbers(..., sources)`). -> {contrast: {'kind': ..., 'store' | 'detail', 'alpha', 'reverse_forms' (secondary tests)}}"""
    prim = {**first["primary"]["tiers"], **{k: v["tier"] for k, v in first["secondary"]["tests"].items()}}
    alpha = first["config"]["alpha"]
    lv, sec = primary_levels(first)
    out = {}
    for k, pv in prim.items():
        have = [(n, rows[n][k]) for n in ROWS if rows.get(n) and k in rows[n]]
        low = min([_rank(pv)] + [_rank(v) for _, v in have])
        if _rank(pv) == low:
            out[k] = {"kind": "primary"}
            continue
        kind = next(n for n, v in have if _rank(v) == low)
        s_ = {"kind": kind, "alpha": alpha}
        if kind == "lab_stratified":
            s_["detail"] = lab_detail
        else:
            s_["store"] = row_stores[kind]
        if k in first["secondary"]["tests"]:                                    # the forms that are reverse S in the analysis that set the tier (Q-A10 prints one of them)
            t = first["secondary"]["tests"][k]
            rf = []
            for f in t["forms"]:
                if kind == "lab_stratified":
                    if lab_detail[f"{k}:{f}"]["upper"][str(alpha)] < -v4.LOG_S:
                        rf.append(f)
                else:
                    _, L, _ = row_stores[kind].L("A1", f, tuple(t["cell"]))
                    if _positives_reach(rule, -L, v4.LOG_S, sec[k]["slot"]):
                        rf.append(f)
            s_["reverse_forms"] = rf
        out[k] = s_
    return out


def run_v4_full(store, cfg=None, lab_indicator=None, retain_all=None, random_subset=None, gate=None, B=B_BOOT):
    """the confirmatory result with the four downgrade rows. lab_indicator / retain_all: Stores from the re-runs (cells g1 and g4); random_subset: list of the three draws' Stores
    (cell g1 only). A row that is not supplied is recorded as not run: the outcome is then `provisional`. The brackets of the abstract sentence come from the analysis that set each
    contrast's effective tier (`number_sources`, D033 F2)."""
    rule, c = v4.resolve_config(cfg)
    first = v4.run_v4(store, cfg, gate)
    rows = {"lab_stratified": None, "lab_indicator": None, "retain_all": None, "random_subset": None}
    row_stores = {}
    tiers_lab, lab_detail = lab_stratified_tiers(first, store, B)
    rows["lab_stratified"] = tiers_lab
    if lab_indicator is not None:
        rows["lab_indicator"] = row_tiers(first, lab_indicator, rule)
        row_stores["lab_indicator"] = lab_indicator
    if retain_all is not None:
        rows["retain_all"] = row_tiers(first, retain_all, rule)
        row_stores["retain_all"] = retain_all
    if random_subset:
        row_stores["random_subset"] = average_stores(random_subset)
        rows["random_subset"] = row_tiers(first, row_stores["random_subset"], rule, cells="g1")
    combined = lowest(*[r for r in rows.values() if r])
    sources = number_sources(first, rows, row_stores, lab_detail, rule)
    final = v4.run_v4(store, cfg, gate, combined, sources)
    final["downgrade"] = {"rows": rows, "lab_stratified_detail": lab_detail, "lowest_over_rows": combined,
                          "rows_run": [k for k, v in rows.items() if v is not None], "rows_not_run": [k for k, v in rows.items() if v is None],
                          "provisional": any(v is None for v in rows.values()), "stratum_weights": LAB_STRATUM_WEIGHT,
                          "number_sources": {k: v["kind"] for k, v in sources.items()},
                          "rule": "the lowest tier over the primary analysis and the rows is the tier of the abstract and of the states (PREREG_v4 9.8 rule 2); the brackets of the abstract sentence are filled from the analysis that set that tier"}
    if "outcome" in final:
        final["outcome"]["provisional_downgrade_rows_incomplete"] = final["downgrade"]["provisional"]
    return final


# ------------------------------------------------------------------------------------------------ Test C and S2: descriptive
def descriptive_entries(store, arms=("A9", "A10", "A10P", "D*"), cell=v4.G4, test="C"):
    """sign counts and order-statistic intervals labelled descriptive (plain exact, no tier word) for Test C (n = 13) and S2: A1 against each comparator"""
    rows = {}
    for a in arms:
        if not (store.has(a, *cell) and store.has("A1", *cell)):
            continue
        conds, L, d = store.L("A1", a, cell)
        n = int(L.size)
        lo, hi, r, cov = v4.PLAIN.interval(L, 0.05)
        lo9, hi9, r9, cov9 = v4.PLAIN.interval(L, 0.05 / 9)          # D033 D3 / PREREG_v4 9.7: the tables also print the plain interval at 1 - 0.05/9 ([L(2), L(12)] at n = 13, [L(4), L(16)] at n = 19)
        ratio = np.exp(-L)                                   # S_A1 / S_comparator
        rows[a] = {"n": n, "positives": int((L > 0).sum()), "k_ratio_below_1": int((ratio < 1).sum()), "p_plain": float(gt.betabin_p(int((L > 0).sum()), n, 0.0)),
                   "median_ratio": float(np.median(ratio)), "ratio_ci": [float(np.exp(-hi)), float(np.exp(-lo))], "interval_is_range": bool(r == 0), "mean_pp": float(d.mean()),
                   "ratio_ci_95": [float(np.exp(-hi)), float(np.exp(-lo))], "ratio_ci_95_rank": int(r), "ratio_ci_95_coverage": float(cov),
                   "ratio_ci_simultaneous": [float(np.exp(-hi9)), float(np.exp(-lo9))], "ratio_ci_simultaneous_rank": int(r9), "ratio_ci_simultaneous_coverage": float(cov9),
                   "interval_simultaneous_is_range": bool(r9 == 0),
                   "label": f"Test {test}: descriptive, plain exact, no tier word; the abstract sentence prints ratio_ci (the plain 95 % interval), the tables print both"}
    return rows


def test_c_in_abstract(median_L_primary, median_L_lab_indicator):
    """PREREG_v4 9.8 rule 3: the Test C sentence goes into the abstract only if the lab-indicator row leaves the sign of its median ratio unchanged"""
    if median_L_lab_indicator is None or median_L_primary is None:
        return False
    return bool(np.sign(median_L_primary) == np.sign(median_L_lab_indicator) and median_L_primary != 0)


def test_c_sentences(rows, comparators=(("A10", "the dataset authors' semi-empirical model"), ("D*", "the best data-driven learner"))):
    out = {}
    for a, name in comparators:
        if a in rows:
            r = rows[a]
            out[a] = v4.test_c_sentence(name, r["median_ratio"], r["ratio_ci"], r["k_ratio_below_1"], r["n"])
    return out
