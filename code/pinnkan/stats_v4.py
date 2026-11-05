"""Statistics step of Design R2 (PREREG_v4 sections 1, 9, 11; D016 judge 2 and 4; D018 ruling A4).

    Store          condition scores of every arm at every grid cell (m, k) from the grid runs (D* and AG resolved per outer fold from `comparators.json`)
    SignRule       the confirmatory sign test: Beta-binomial design-effect test (rho_s0 = 0.03, D018) or plain exact; plain is the descriptive row
    primary_analysis    nodes P1N, P1S, P2, P3, K1, K2N, K2S on the sequentially rejective graph (graph weight a config value), reverse-S safety tests, K1 tier S unadjusted
    secondary_analysis  Q-A10 (both forms; lowest tier), Q-H, Q-T on the nested N_i / S_i graph; reverse S at the slot's final level
    estimated_tables    A1 against D*, A9, AG, A2, A10 at every cell with simultaneous intervals, ladder, window-information gain, mean pp (BCa) and worst condition
    lab_rows, dependence_sensitivity, most_test (GAP-1), item (f) guard
    assemble_outcome    states P/K/M1/M2, extent clause, title and abstract sentences of the closed table (section 11), from effective tiers (downgrade rows lower them)

L_c = ln(S_comparator / S_target): L > 0 favours the target. Relative reductions X = 100 (1 - exp(-median L)); an excess Y = 100 (exp(median L) - 1) (PREREG_v4 section 1).
No p-value, coverage or calibration statement is made anywhere; the abstract sentences carry intervals and counts only.
"""
import hashlib
import json
import math
import os
from types import SimpleNamespace

import numpy as np

from . import graph_test as gt
from .negcontrol import MC_SEED_ROOT
from .stats_step import bca_mean_ci

LOG_S, LOG_N = float(np.log(1.02)), float(-np.log(1.10))
TIER_ORDER = ["reverse S", "none", "N", "S"]            # lowest first (PREREG_v4 9.5 scale)
G1, G4 = (8, "2"), (32, "full")
DEFAULT_CONFIG = {"sign_rule": "betabin", "rho_s0": gt.RHO_S0, "graph_w": 0.5, "alpha": 0.025, "e1_prime_approved": False, "sensitivity_rhos": list(gt.RHO_GRID),
                  "k_chain_struck": False}


class SignRuleNotSetError(RuntimeError):
    """the confirmatory sign-test rule (plain exact or Beta-binomial with rho_s0) is not set in the config: the run refuses to score (PREREG_v4 9.3, D018)"""


class ChainKMissingError(RuntimeError):
    """the K-chain arms (A15, G15, A1 at g4) are missing but the config does not say that chain K is struck: P would silently be tested at the full level (review I3)"""


class ItemFError(RuntimeError):
    """the item (f) dependence file is missing, altered, or was written after an outer score (D018 2.3 (ii)): the statistics step is blocked"""


# ------------------------------------------------------------------------------------------------ the sign rule
class SignRule:
    def __init__(self, kind, rho_s0=None):
        if kind not in ("betabin", "plain"):
            raise SignRuleNotSetError(f"sign_rule must be 'betabin' or 'plain', not {kind!r}")
        if kind == "betabin" and (rho_s0 is None or not 0.0 < float(rho_s0) < 1.0):
            raise SignRuleNotSetError("sign_rule 'betabin' needs rho_s0 in (0, 1)")
        self.kind, self.rho_s0 = kind, (None if kind == "plain" else float(rho_s0))

    @property
    def rho(self):
        return 0.0 if self.kind == "plain" else self.rho_s0

    def with_rho(self, rho):
        return SignRule("plain") if rho <= 0 else SignRule("betabin", rho)

    def crit(self, n, alpha):
        return gt.betabin_crit(n, alpha, self.rho)

    def p(self, pos, n):
        return float(gt.betabin_p(pos, n, self.rho))

    def test(self, L, margin):
        """(positives, n, p): conditions with L exactly equal to the margin are dropped and n reduced (PREREG_v4 9.3)"""
        L = np.asarray(L, float)
        L = L[L != margin]
        pos = int((L > margin).sum())
        return pos, int(L.size), (self.p(pos, L.size) if L.size else 1.0)

    def interval(self, L, alpha_two_sided):
        return gt.dep_order_stat_interval(L, alpha_two_sided, self.rho)

    def describe(self):
        if self.kind == "plain":
            return "plain exact sign test (independent conditions; descriptive row)"
        return f"sign test with a fixed design effect (assumed average pairwise sign correlation at most {self.rho_s0:g}); assumption-based, not exact and not distribution-free"


PLAIN = SignRule("plain")


def resolve_config(cfg=None):
    c = {**DEFAULT_CONFIG, **(cfg or {})}
    rule = SignRule(c["sign_rule"], c.get("rho_s0"))        # raises SignRuleNotSetError when unset
    w = float(c["graph_w"])
    if not (0.0 < w < 1.0 or (w == 1.0 and c["k_chain_struck"])):
        raise ValueError("graph_w must be in (0, 1) (1 only when chain K is struck)")
    return rule, c


# ------------------------------------------------------------------------------------------------ the score store
class Store:
    """tables {(m, k): {arm: {cond: score_pp}}}; lab {cond: lab}; fold {cond: outer fold}; k_full (2 merges the k = 2 and k = full cells)"""

    def __init__(self, tables, lab=None, fold=None, k_full=4, notes=None, seed_tables=None):
        self.tables = {(int(m), str(k)): {a: dict(v) for a, v in t.items()} for (m, k), t in tables.items()}
        self.lab, self.fold, self.k_full, self.notes = dict(lab or {}), dict(fold or {}), k_full, notes or {}
        self.seed_tables = None if seed_tables is None else {(int(m), str(k)): {a: dict(v) for a, v in t.items()} for (m, k), t in seed_tables.items()}

    def seed_view(self):
        """the per-seed score tables (mean over seeds of the per-seed condition RMSE): K1 and K2 read them for A1, A15 and G15 alike (D020 C1 item 4); self when the store holds one
        kind of score only"""
        if self.seed_tables is None:
            return self
        return Store(self.seed_tables, self.lab, self.fold, self.k_full, self.notes)

    def key(self, m, k):
        k = str(k)
        if k == "2" and (int(m), "2") not in self.tables and self.k_full == 2:
            k = "full"
        return (int(m), k)

    def has(self, arm, m, k):
        return arm in self.tables.get(self.key(m, k), {})

    def scores(self, arm, m, k):
        return self.tables[self.key(m, k)][arm]

    def cells(self):
        return sorted(self.tables, key=lambda mk: (mk[0], {"0": 0, "2": 1, "full": 2}.get(mk[1], 9)))

    def arms(self):
        return sorted({a for t in self.tables.values() for a in t})

    def pair(self, target, comp, cell_t, cell_c=None):
        """(conds, s_target, s_comp) on the conditions scored for both arms (paired by condition)"""
        st, sc = self.scores(target, *cell_t), self.scores(comp, *(cell_c or cell_t))
        conds = sorted(set(st) & set(sc))
        return conds, np.array([st[c] for c in conds]), np.array([sc[c] for c in conds])

    def L(self, target, comp, cell_t, cell_c=None):
        conds, a, b = self.pair(target, comp, cell_t, cell_c)
        return conds, np.log(b / a), b - a

    @classmethod
    def from_runs(cls, run_dirs):
        """grid runs (config.m, one outer fold each, scored at every k; D* and AG resolved per fold from comparators.json)"""
        tables, lab, fold, k_full, notes = {}, {}, {}, None, {"runs": []}
        seed_tables, have_seed = {}, False
        for d in run_dirs:
            cfg = json.load(open(os.path.join(d, "config.json"), encoding="utf8"))
            met = json.load(open(os.path.join(d, "metrics.json"), encoding="utf8"))
            m = cfg.get("m")
            m = 32 if m is None else int(m)
            labels = met.get("k_labels") or ["full"]
            primary = met.get("k_primary", "full")
            comp = json.load(open(os.path.join(d, "comparators.json"), encoding="utf8")) if os.path.exists(os.path.join(d, "comparators.json")) else {}
            k_full = met.get("k_full") or k_full
            for kl in labels:
                suf = "" if kl == primary else f"_k{kl}"
                cs = json.load(open(os.path.join(d, f"condition_scores{suf}.json"), encoding="utf8"))
                t = tables.setdefault((m, str(kl)), {})
                for a, v in cs.items():
                    t.setdefault(a, {}).update(v)
                for alias in ("D*", "AG"):
                    if alias in comp and comp[alias]["arm"] in cs:
                        t.setdefault(alias, {}).update(cs[comp[alias]["arm"]])
                sp = os.path.join(d, f"condition_scores_seed{suf}.json")
                ss_ = json.load(open(sp, encoding="utf8")) if os.path.exists(sp) else cs
                have_seed = have_seed or os.path.exists(sp)
                ts = seed_tables.setdefault((m, str(kl)), {})
                for a, v in ss_.items():
                    ts.setdefault(a, {}).update(v)
                for alias in ("D*", "AG"):
                    if alias in comp and comp[alias]["arm"] in ss_:
                        ts.setdefault(alias, {}).update(ss_[comp[alias]["arm"]])
                mp = os.path.join(d, f"condition_meta{suf}.json")
                if os.path.exists(mp):
                    for c, e in json.load(open(mp, encoding="utf8")).items():
                        lab.setdefault(c, sorted(e["lab"].items(), key=lambda kv: (-kv[1], kv[0]))[0][0])
                for c in cs.get(next(iter(cs)), {}):
                    fold[c] = int(cfg["fold"])
            notes["runs"].append({"dir": d, "m": m, "fold": cfg["fold"], "k_labels": labels, "comparators": {k: v["arm"] for k, v in comp.items() if isinstance(v, dict) and "arm" in v}})
        return cls(tables, lab, fold, k_full or 4, notes, seed_tables if have_seed else None)


# ------------------------------------------------------------------------------------------------ helpers
def pct_reduction(median_L):
    return 100.0 * (1.0 - math.exp(-median_L))


def pct_excess(median_L):
    return 100.0 * (math.exp(median_L) - 1.0)


def tier_min(*tiers):
    return min(tiers, key=TIER_ORDER.index)


def entry(store, name, target, comp, cell, rule, cell_c=None, alpha_int=0.05, test="B", bca=True, bca_label=None):
    """descriptive record of one contrast at one grid cell: median log ratio with the unadjusted fallback 95 % interval, counts, mean pp (BCa), worst condition, per-fold medians"""
    conds, L, d = store.L(target, comp, cell, cell_c)
    st, sc = store.scores(target, *cell), store.scores(comp, *(cell_c or cell))
    lo, hi, r, cov = rule.interval(L, alpha_int)
    med = float(np.median(L))
    e = {"name": name, "target": target, "comparator": comp, "cell": list(cell), "n": int(L.size), "median_L": med, "median_ci": [lo, hi], "interval_rank": r, "interval_coverage": cov,
         "interval_is_range": bool(r == 0), "rel_reduction_pct": pct_reduction(med), "rel_reduction_ci_pct": [pct_reduction(lo), pct_reduction(hi)],
         "excess_pct": pct_excess(-med) if med < 0 else None, "n_wins": int((L > 0).sum()), "mean_pp": float(d.mean()),
         "worst_condition_pp": {"target": float(max(st[c] for c in conds)), "comparator": float(max(sc[c] for c in conds))}}
    if bca and L.size >= 3:
        lab_ = bca_label or f"{test}|{name}|g{cell[0]}-{cell[1]}|BCa_mean_pp"
        b = bca_mean_ci(d, label=lab_)
        e["mean_pp_ci"], e["mc_label"] = [b[0], b[1]], lab_
    if store.fold:
        folds = sorted({store.fold[c] for c in conds if c in store.fold})
        meds = {int(f): float(np.median([L[i] for i, c in enumerate(conds) if store.fold.get(c) == f])) for f in folds}
        e["fold_medians"] = meds
        e["folds_agreeing_with_sign"] = int(sum(1 for v in meds.values() if (v > 0) == (med > 0)))
    return e


def node(rule, L, margin, label):
    pos, n, p = rule.test(L, margin)
    return {"label": label, "margin": margin, "n": n, "positives": pos, "p": p, "p_plain": float(gt.betabin_p(pos, n, 0.0)) if n else 1.0}


def level_of(res, names, nm):
    """local level of one node: the level at its rejection, or its final level if it stayed open"""
    k = list(names).index(nm)
    return float(res.level_at_rejection[k]) if res.rejected[k] else float(res.final_level[k])


def slot_level(res, names, i):
    """largest level the slot of secondary test i reaches: max over its two nodes of the level at rejection (rejected) or the final level (open)"""
    out = 0.0
    for nm in (f"N{i}", f"S{i}"):
        k = names.index(nm)
        out = max(out, float(res.level_at_rejection[k]) if res.rejected[k] else float(res.final_level[k]))
    return out


# ------------------------------------------------------------------------------------------------ primary analysis
def primary_nodes(store, rule):
    """-> (nodes dict keyed P1N..K2S plus the reverse tests, L arrays); a node whose arms are absent is None (p = 1: never rejected)"""
    out, Ls = {}, {}
    have = lambda *a: all(store.has(x, *c) for x, c in a)
    kv = store.seed_view()                                       # K1 / K2: per-seed scores for A1, A15 and G15 (D020 C1 item 4)
    have_k = lambda *a: all(kv.has(x, *c) for x, c in a)
    if have(("A1", G1), ("D*", G1)):
        _, L1, _ = store.L("A1", "D*", G1)
        Ls["P1"] = L1
        out["P1N"], out["P1S"] = node(rule, L1, LOG_N, "P1N"), node(rule, L1, LOG_S, "P1S")
        out["P1rev"] = node(rule, -L1, LOG_S, "P1-rev")
    if have(("A1", G1), ("A9", G1)):
        _, L2, _ = store.L("A1", "A9", G1)
        Ls["P2"] = L2
        out["P2"] = node(rule, L2, LOG_S, "P2")
    if "P1" in Ls and "P2" in Ls and have(("A1", G4), ("D*", G4)):
        c1, L1, _ = store.L("A1", "D*", G1)
        c4, L4, _ = store.L("A1", "D*", G4)
        common = sorted(set(c1) & set(c4))
        D = np.array([L1[c1.index(c)] - L4[c4.index(c)] for c in common])
        Ls["P3"] = D
        out["P3"] = node(rule, D, 0.0, "P3")
    if have_k(("A15", G4), ("A1", G4)):
        _, LK1, _ = kv.L("A15", "A1", G4)
        Ls["K1"] = LK1
        out["K1"] = node(rule, LK1, LOG_N, "K1")
        out["K1_S_unadjusted"] = node(rule, LK1, LOG_S, "K1 tier S (unadjusted)")
    if have_k(("A15", G4), ("G15", G4)):
        _, LK2, _ = kv.L("A15", "G15", G4)
        Ls["K2"] = LK2
        out["K2N"], out["K2S"] = node(rule, LK2, LOG_N, "K2N"), node(rule, LK2, LOG_S, "K2S")
        out["K2rev"] = node(rule, -LK2, LOG_S, "K2-rev")
    return out, Ls


def run_graph(nodes, w, alpha, k_struck=False):
    """sequentially rejective graph on the p-values of the nodes (missing nodes: p = 1)"""
    p = {k: (nodes[k]["p"] if k in nodes else 1.0) for k in gt.NODES}
    if k_struck:
        names, wv, G = gt.pinnkan_graph(0.5)
        wv = np.zeros(len(names))
        wv[names.index("P1N")] = 1.0
        return gt.graph_test(np.array([p[k] for k in names]), wv, G, alpha), names
    names, wv, G = gt.pinnkan_graph(w)
    return gt.graph_test(np.array([p[k] for k in names]), wv, G, alpha), names


def primary_analysis(store, rule, cfg):
    nodes, Ls = primary_nodes(store, rule)
    k_struck = bool(cfg["k_chain_struck"])
    if not k_struck and ("K1" not in nodes or "K2N" not in nodes):
        raise ChainKMissingError("K1 / K2 cannot be computed (A15, G15 or A1 at g4 missing) and k_chain_struck is not set: chain K is struck only by an explicit config value (D016 section 8), "
                                 "never silently, because P1 would then be tested at 0.025 instead of 0.0125")
    res, names = run_graph(nodes, cfg["graph_w"], cfg["alpha"], k_struck)
    rej = {nm: bool(res.rejected[i]) for i, nm in enumerate(names)}
    lvl = {nm: (float(res.level_at_rejection[i]) if res.rejected[i] else float(res.final_level[i])) for i, nm in enumerate(names)}
    for nm in names:
        if nm in nodes:
            nodes[nm].update(rejected=rej[nm], level=lvl[nm], crit_positives=rule.crit(nodes[nm]["n"], lvl[nm]) if lvl[nm] > 0 else None)
    a = cfg["alpha"]
    rev = {}
    for nm in ("P1rev", "K2rev"):                       # outside the graph, 0.025 one-sided each, tested regardless (safety findings)
        if nm in nodes:
            nodes[nm].update(rejected=bool(nodes[nm]["p"] <= a * (1 + gt.TOL)), level=a, crit_positives=rule.crit(nodes[nm]["n"], a))
            rev[nm] = nodes[nm]["rejected"]
    if "K1_S_unadjusted" in nodes:
        nodes["K1_S_unadjusted"].update(rejected=bool(nodes["K1_S_unadjusted"]["p"] <= a * (1 + gt.TOL)), level=a, status="unadjusted, descriptive (GAP-8)")
    tiers = {}
    if "P1N" in nodes:
        tiers["P1"] = "reverse S" if rev.get("P1rev") else ("S" if rej["P1S"] else ("N" if rej["P1N"] else "none"))
    tiers["P2"] = bool(rej.get("P2", False))
    tiers["P3"] = bool(rej.get("P3", False))
    if "K1" in nodes:
        tiers["K1"] = bool(rej["K1"])
    if "K2N" in nodes:
        tiers["K2"] = "reverse S" if rev.get("K2rev") else ("S" if rej["K2S"] else ("N" if rej["K2N"] else "none"))
    return {"rule": rule.describe(), "graph_w": (1.0 if k_struck else cfg["graph_w"]), "k_chain_struck": k_struck, "alpha": a,
            "initial_levels": {nm: float(a * wv) for nm, wv in zip(names, (np.where(np.array(names) == "P1N", 1.0, 0.0) if k_struck else gt.pinnkan_graph(cfg["graph_w"])[1]))},
            "nodes": nodes, "rejected": rej, "tiers": tiers, "rejection_order": [names[i] for i in res.order]}, Ls


def plain_rows(store, cfg):
    """the independent-conditions row beside every gated contrast: positives, plain exact p, plain tier (descriptive, never sets a state or a tier)"""
    pa, _ = primary_analysis(store, PLAIN, cfg)
    return {"rule": "plain exact sign test, independent conditions (descriptive)", "tiers": pa["tiers"],
            "nodes": {k: {"n": v["n"], "positives": v["positives"], "p_plain": v["p"], "rejected_plain": v.get("rejected")} for k, v in pa["nodes"].items()}}


# ------------------------------------------------------------------------------------------------ secondary family
SECONDARY = [("QA10_g1", "A10", G1), ("QA10_g4", "A10", G4), ("QH_g1", "A2", G1), ("QH_g4", "A2", G4), ("QT_g1", "A13", G1)]
A10_FORMS = ("A10", "A10P")


def secondary_analysis(store, rule, cfg):
    """five tests on the nested graph (N_i level 0.025/5, S_i level 0); Q-A10 uses both forms of A10: a node p-value is the larger of the two forms (the test holds iff both hold =
    the lowest tier of the two forms); reverse S of a test is reverse S in either form, tested at the slot's final level"""
    tests, pN, pS = [], [], []
    for name, arm, cell in SECONDARY:
        forms = [a for a in (A10_FORMS if arm == "A10" else (arm,)) if store.has(a, *cell) and store.has("A1", *cell)]
        t = {"name": name, "arm": arm, "cell": list(cell), "forms": forms}
        if forms:
            per = {}
            for f in forms:
                _, L, _ = store.L("A1", f, cell)
                per[f] = {"L": L, "N": node(rule, L, LOG_N, f"{name}:{f}:N"), "S": node(rule, L, LOG_S, f"{name}:{f}:S")}
            t["per_form"] = per
            t["pN"], t["pS"] = max(per[f]["N"]["p"] for f in forms), max(per[f]["S"]["p"] for f in forms)
        else:
            t["pN"] = t["pS"] = 1.0
        tests.append(t)
        pN.append(t["pN"])
        pS.append(t["pS"])
    names, w, G = gt.secondary_graph(len(SECONDARY))
    res = gt.graph_test(np.array(pN + pS), w, G, cfg["alpha"])
    out = {}
    for i, t in enumerate(tests, start=1):
        sN, sS = bool(res.rejected[names.index(f"N{i}")]), bool(res.rejected[names.index(f"S{i}")])
        lvl = slot_level(res, list(names), i)
        rev = {}
        for f in t.get("forms", []):
            n_ = t["per_form"][f]
            rv = node(rule, -n_["L"], LOG_S, f"{t['name']}:{f}:revS")
            rv["level"], rv["rejected"] = lvl, bool(lvl > 0 and rv["p"] <= lvl * (1 + gt.TOL))
            rev[f] = rv
        any_rev = any(r["rejected"] for r in rev.values())
        tier = "reverse S" if any_rev else ("S" if sS else ("N" if sN else "none"))
        out[t["name"]] = {"arm": t["arm"], "cell": t["cell"], "forms": t.get("forms", []), "pN": t["pN"], "pS": t["pS"], "N_rejected": sN, "S_rejected": sS, "slot_level": lvl, "N_level": level_of(res, names, f"N{i}"), "S_level": level_of(res, names, f"S{i}"), "reverse_S": rev,
                          "tier": tier, "crit_positives_slot": (rule.crit(next(iter(t["per_form"].values()))["N"]["n"], lvl) if t.get("forms") and lvl > 0 else None),
                          "per_form": {f: {"N": t["per_form"][f]["N"], "S": t["per_form"][f]["S"]} for f in t.get("forms", [])}}
    return {"rule": rule.describe(), "graph": "N_i / S_i nested graph (Holm with one node per test), initial level alpha/5 on each N_i", "tests": out,
            "multiplicity_note": "the reverse-S safety test of Q-A10 is run once per form at the slot's final level (disclosed)"}


# ------------------------------------------------------------------------------------------------ estimated tables
ESTIMATED_COMPARATORS = ("D*", "A9", "AG", "A2", "A10", "A10P")


def simultaneous(L, rule, n_cells):
    lo, hi, r, cov = rule.interval(L, 0.05 / n_cells)
    return {"lo": lo, "hi": hi, "rank": r, "coverage": cov, "is_range": bool(r == 0), "level": 1 - 0.05 / n_cells,
            "rel_reduction_ci_pct": [pct_reduction(lo), pct_reduction(hi)]}


def estimated_tables(store, rule, bca=True):
    """A1 against D*, A9, AG, A2, A10 (both forms) at every cell with simultaneous intervals (Bonferroni over the cells present); ladder; window-information gain"""
    cells = [c for c in store.cells() if store.has("A1", *c)]
    nc = len(cells)
    rows, ladder, win = [], [], []
    for comp in ESTIMATED_COMPARATORS:
        for c in cells:
            if not store.has(comp, *c):
                continue
            e = entry(store, f"A1 vs {comp}", "A1", comp, c, rule, bca=bca)
            conds, L, _ = store.L("A1", comp, c)
            e["simultaneous"] = simultaneous(L, rule, nc)
            rows.append(e)
    for c in cells:
        if all(store.has(a, *c) for a in ("A9", "AG", "A1")):
            conds = sorted(set(store.scores("A9", *c)) & set(store.scores("AG", *c)) & set(store.scores("A1", *c)))
            s9, sg, s1 = (np.array([store.scores(a, *c)[x] for x in conds]) for a in ("A9", "AG", "A1"))
            law_, kan_ = np.log(s9 / sg), np.log(sg / s1)
            row = {"cell": list(c), "n": len(conds), "law_share_with_non_KAN_map": {"median": float(np.median(law_)), "mean": float(law_.mean()), "simultaneous": simultaneous(law_, rule, nc)},
                   "KAN_share_inside_law": {"median": float(np.median(kan_)), "mean": float(kan_.mean()), "simultaneous": simultaneous(kan_, rule, nc)},
                   "note": "medians do not add: shares are medians of the terms and mean log terms, never a decomposition of the median"}
            if len(conds) >= 3:
                row["law_share_with_non_KAN_map"]["mean_bca"] = list(bca_mean_ci(law_, label=f"B|ladder-law|g{c[0]}-{c[1]}|BCa_mean_log"))
                row["KAN_share_inside_law"]["mean_bca"] = list(bca_mean_ci(kan_, label=f"B|ladder-kan|g{c[0]}-{c[1]}|BCa_mean_log"))
            ladder.append(row)
    for arm in store.arms():
        for m in sorted({c[0] for c in store.cells()}):
            if not store.has(arm, m, "0"):
                continue
            for k in ("2", "full"):
                if store.key(m, k) in store.tables and store.has(arm, m, k) and store.key(m, k) != store.key(m, "0"):
                    conds, L, d = store.L(arm, arm, (m, k), (m, "0"))          # T = arm with the window, C = arm without it: L > 0 = the window helps
                    win.append({"arm": arm, "m": m, "k": k, "n": int(L.size), "median_L": float(np.median(L)), "rel_reduction_pct": pct_reduction(float(np.median(L))), "mean_pp_gain": float(d.mean())})
    return {"rule": rule.describe(), "n_cells": nc, "rows": rows, "ladder": ladder, "window_information_gain": win}


# ------------------------------------------------------------------------------------------------ lab rows, dependence sensitivity, most
def lab_rows(store, rule, contrasts):
    """per-lab descriptive rows (fixed lab strata; majority lab of the condition): n, positives (L > 0), median L, fallback 95 % interval (labelled range where no pair attains it)"""
    out = {}
    for name, (target, comp, cell) in contrasts.items():
        if not (store.has(target, *cell) and store.has(comp, *cell)):
            continue
        conds, L, _ = store.L(target, comp, cell)
        rows = {}
        for lab in sorted({store.lab.get(c, "?") for c in conds}):
            idx = [i for i, c in enumerate(conds) if store.lab.get(c, "?") == lab]
            x = L[idx]
            lo, hi, r, cov = rule.interval(x, 0.05)
            rows[lab] = {"n": len(idx), "positives": int((x > 0).sum()), "median_L": float(np.median(x)), "interval": [lo, hi], "interval_is_range": bool(r == 0), "rank": r}
        out[name] = {"cell": list(cell), "labs": rows}
    return out


def dependence_sensitivity(store, rule, cfg):
    """the tier of each gated contrast at rho_s0 in the grid, and the fixed sentence of D018 2.3 (i)"""
    base, _ = primary_analysis(store, rule, cfg)
    per = {}
    for rho in cfg["sensitivity_rhos"]:
        pa, _ = primary_analysis(store, rule.with_rho(rho), cfg)
        per[str(rho)] = pa["tiers"]
    sentences = {}
    for name, t in base["tiers"].items():
        if t in ("S", "N") or t is True:
            ok = [rho for rho in cfg["sensitivity_rhos"] if _tier_ge(per[str(rho)].get(name), t)]
            holds = max(ok) if ok else None
            word = {"S": "tier S", "N": "tier N", True: "result"}[t]
            sentences[name] = (f"The {word} holds for an assumed average sign correlation up to {holds:g}." if holds is not None else None)
    return {"grid": list(cfg["sensitivity_rhos"]), "tiers_by_rho": per, "sentences": sentences, "no_consequence_for_any_tier": True}


def _tier_ge(a, b):
    if isinstance(b, bool) or isinstance(a, bool):
        return bool(a) >= bool(b)
    return a is not None and TIER_ORDER.index(a) >= TIER_ORDER.index(b)


def most_d(store):
    """per-condition d_c = L_law,c - 0.5 L_total,c at g1 (D018 section 4); None when A1, A9 or D* is missing at g1"""
    if not (store.has("A1", *G1) and store.has("A9", *G1) and store.has("D*", *G1)):
        return None
    c9, L9, _ = store.L("A1", "A9", G1)
    cD, LD, _ = store.L("A1", "D*", G1)
    common = sorted(set(c9) & set(cD))
    law_ = np.array([L9[c9.index(c)] for c in common])
    tot = np.array([LD[cD.index(c)] for c in common])
    return common, law_, tot, law_ - 0.5 * tot


def most_test(store, rule, cfg, e1_reached):
    """GAP-1 (D018 section 4): d_c = L_law,c - 0.5 L_total,c at g1; 'most' holds iff e1 is reached and the sign test of median(d_c) > 0 at 0.025 reaches its count"""
    md = most_d(store)
    if md is None:
        return None
    common, law_, tot, d = md
    pos, n, p = rule.test(d, 0.0)
    crit = rule.crit(n, cfg["alpha"])
    lo, hi, r, cov = rule.interval(d, 0.05)
    reached = bool(pos >= crit)
    return {"n": n, "positives": pos, "p": p, "crit_positives": crit, "test_passes": reached, "e1_reached": bool(e1_reached), "most": bool(e1_reached and reached),
            "median_d": float(np.median(d)), "median_d_ci": [lo, hi], "median_L_law": float(np.median(law_)), "median_L_total": float(np.median(tot)),
            "ratio_median_law_to_total": (float(np.median(law_) / np.median(tot)) if np.median(tot) != 0 else None),
            "note": "median(d_c) > 0 is not the same statement as median L_law >= 0.5 median L_total; both medians are printed. Outside the graph, labelled like the safety findings; downgrade rows apply as pass/fail."}


# ------------------------------------------------------------------------------------------------ item (f) guard
ITEM_F_FILE, ITEM_F_HASH = "item_f_dependence.json", "item_f_dependence.sha256.json"


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def write_item_f(directory, report):
    """write the item (f) dependence report and its hash record; call BEFORE any outer score is computed"""
    os.makedirs(directory, exist_ok=True)
    p = os.path.join(directory, ITEM_F_FILE)
    with open(p, "w", encoding="utf8") as fh:
        json.dump(report, fh, indent=1, sort_keys=True)
    import time
    rec = {"file": ITEM_F_FILE, "sha256": _sha(p), "written_unix": time.time(), "estimator": "graph_test.dependence_report", "rule": "hashed before any outer score; the statistics step refuses to run otherwise"}
    with open(os.path.join(directory, ITEM_F_HASH), "w", encoding="utf8") as fh:
        json.dump(rec, fh, indent=1)
    return rec


def outer_score_mtimes(run_dirs):
    out = []
    for d in run_dirs:
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.startswith("condition_scores") and f.endswith(".json"):
                    out.append(os.path.getmtime(os.path.join(d, f)))
    return out


def require_item_f(directory, run_dirs):
    """block the statistics step unless the item (f) file exists, matches its recorded hash, and was written before every outer score file of `run_dirs`"""
    p, h = os.path.join(directory, ITEM_F_FILE), os.path.join(directory, ITEM_F_HASH)
    if not (os.path.exists(p) and os.path.exists(h)):
        raise ItemFError(f"item (f) dependence file or its hash record missing in {directory}: write it (stats_v4.write_item_f) before any outer score; the statistics step is blocked")
    rec = json.load(open(h, encoding="utf8"))
    if rec["sha256"] != _sha(p):
        raise ItemFError("item (f) dependence file differs from its recorded hash (altered after hashing)")
    scores = outer_score_mtimes(run_dirs)
    if scores and not (os.path.getmtime(p) < min(scores) and rec["written_unix"] < min(scores)):
        raise ItemFError("item (f) dependence file was written after an outer score file existed: the pre-score rule of D018 2.3 (ii) is broken")
    return json.load(open(p, encoding="utf8"))


def item_f_from_runs(run_dirs, contrast=("D*", "A1")):
    """item (f) estimate from the INNER-CV training-side condition scores of the outer-fold runs (tuning_done.json): sign of ln(S_comp / S_target) > its median per condition;
    groups: the inner fold of the condition (the model that scored it) and the majority laboratory. Reported evidence only (D018 2.3 (ii))."""
    from . import tuning
    from .specs import SPECS
    signs, fold, lab = [], [], []
    for d in run_dirs:
        cfg = json.load(open(os.path.join(d, "config.json"), encoding="utf8"))
        td = json.load(open(os.path.join(d, "tuning_done.json"), encoding="utf8"))
        comp = json.load(open(os.path.join(d, "comparators.json"), encoding="utf8"))
        meta = json.load(open(os.path.join(d, "train_condition_meta.json"), encoding="utf8"))
        tgt, cmp_ = contrast[1], (comp[contrast[0]]["arm"] if contrast[0] in comp else contrast[0])
        sa, sb = td["arms"][tgt]["cond_scores"], td["arms"][cmp_]["cond_scores"]
        conds = sorted(set(sa) & set(sb))
        L = np.array([math.log(sb[c] / sa[c]) for c in conds])
        cells = [SimpleNamespace(kind="cycling", cond=c, raw=np.array([float(c.split("|")[0][1:])])) for c in conds]
        fo = tuning.inner_folds(cells, int(cfg["inner_k"]), 1000 + int(cfg["fold"]), SimpleNamespace(strat_index=0))
        med = float(np.median(L))
        for i, c in enumerate(conds):
            signs.append(1.0 if L[i] > med else 0.0)
            fold.append(f"{cfg['fold']}:{fo[c]}")
            lab.append(meta.get(c, {}).get("lab", "?"))
    if len(set(fold)) < 2 or len(set(lab)) < 2:
        return {"note": "fewer than two groups: no estimate", "n": len(signs)}
    rep = gt.dependence_report(np.array(signs), np.array(fold), np.array(lab))
    rep.update(n_observations=len(signs), contrast=list(contrast), groups="inner fold within outer fold; majority laboratory",
               disclosure=("The training-side estimate of the sign correlation exceeded the value assumed by the test; the confirmatory tiers rest on that assumption." if rep["exceeds_rho_s0"] else None))
    return rep


# ------------------------------------------------------------------------------------------------ the closed table (PREREG_v4 section 11 = D016 judge 4.2/4.3)
LEAD_IN = "With eight cycling conditions and two check-ups per held-out cell,"
E1 = "most of the advantage came from the physics law, since the same network without it was {Y} % worse, and the advantage was larger with 8 than with 32 cycling conditions"
E1P = "the same network without the physics law was {Y} % worse, and the advantage was larger with 8 than with 32 cycling conditions"      # D018 section 4 (needs Shlok's approval; off by default)
E2 = "the same network without the physics law was {Y} % worse; a dependence of the advantage on the number of cycling conditions was not shown"
E3 = "a gain attributable to the physics law within the same network was not shown"
TITLES = {
    ("P+", "K+"): ("T1", "Physics-informed neural networks with readable Kolmogorov-Arnold stress laws forecast lithium-ion capacity fade from few cycling tests and early check-ups"),
    ("P+", "K="): ("T2", "Physics-informed neural networks with Kolmogorov-Arnold stress functions forecast lithium-ion capacity fade from few cycling tests and early check-ups"),
    ("P+", "K-"): ("T3", "Physics-informed neural networks forecast lithium-ion capacity fade from few cycling tests and early check-ups"),
    ("P0", "K+"): ("T4", "Readable Kolmogorov-Arnold stress laws for lithium-ion capacity fade, with learning curves of physics-informed and data-driven forecasts from few cycling tests"),
    ("P0", "K="): ("T5", "How many cycling tests and check-ups do physics-informed and data-driven forecasts of lithium-ion capacity fade need? Learning curves with Kolmogorov-Arnold stress functions"),
    ("P0", "K-"): ("T6", "How many cycling tests and check-ups do physics-informed and data-driven forecasts of lithium-ion capacity fade need? Learning curves on a designed ageing dataset"),
    ("P-", "K+"): ("T7", "A physics prior does not help lithium-ion fade forecasts from few cycling tests but yields readable Kolmogorov-Arnold stress laws"),
    ("P-", "K="): ("T8", "When a physics prior does not help: learning curves of physics-informed and data-driven forecasts of lithium-ion capacity fade from few cycling tests"),
    ("P-", "K-"): ("T8", "When a physics prior does not help: learning curves of physics-informed and data-driven forecasts of lithium-ion capacity fade from few cycling tests"),
}
T9A = ("T9a", "Physics priors pay when cycling tests are few: semi-empirical, physics-informed Kolmogorov-Arnold and data-driven forecasts of lithium-ion capacity fade")
T9B = ("T9b", "Physics priors pay when cycling tests are few: semi-empirical, physics-informed and data-driven forecasts of lithium-ion capacity fade")
M1_OLD, M1_NEW = "Physics-informed neural networks", "Physics-constrained neural ageing models"
Q_TEMPLATES = {
    "S": "{A} had a median condition error {X} % lower than {B} ({interval}; n = {n})",
    "N": "{A} was no more than 10 % worse than {B} (one-sided bound); not shown better",
    "none": "{A} and {B} could not be distinguished ({interval})",
    "reverse S": "{B} had a median condition error {X} % lower than {A} ({interval})",
}
Q_H_NONE = "the soft residual was not shown necessary relative to exact integration of the same law"
A10_NAME = "the dataset authors' semi-empirical model"
QT_NAME = "training with and without the storage cells"
TEST_C_TAIL = "temperature and laboratory cannot be separated in this design"
KCLAUSE_KPLUS = ("and a closed-form stress law extracted from its Kolmogorov-Arnold network predicted held-out conditions no more than 10 % worse than the full network and {Z} % more accurately "
                 "than an equally simplified additive law ({iv})")
KCLAUSE_KEQ_PASS = ("and a closed-form stress law extracted from its Kolmogorov-Arnold network predicted held-out conditions no more than 10 % worse than the full network, but was not shown more "
                    "accurate than an equally simplified additive law ({iv})")
KCLAUSE_KEQ_FAIL = ("and a closed-form stress law extracted from its Kolmogorov-Arnold network was not shown to stay within 10 % of the full network, so no readable-law claim is made")
KCLAUSE_KMINUS = "while an equally simplified additive stress law predicted held-out conditions {Z} % more accurately than the law extracted from its Kolmogorov-Arnold network ({iv})"
T9_TAIL = "; the dataset authors' semi-empirical model was {W} % more accurate still at this cell ({iv})"


def fmt1(x):
    return f"{x:.1f}"


def ivs(lo, hi):
    return f"95 % interval [{fmt1(lo)}, {fmt1(hi)}]"


def state_P(tiers):
    t = tiers["P1"]
    return "P+" if t == "S" else ("P-" if t == "reverse S" else "P0")


def state_K(tiers):
    if tiers.get("K2") == "reverse S":
        return "K-"
    if tiers.get("K1") and tiers.get("K2") == "S":
        return "K+"
    return "K="


def extent_clause(tiers, most=None, e1_prime_approved=False):
    if tiers["P1"] != "S":
        return None
    if not tiers["P2"]:
        return "e3"
    if not tiers["P3"]:
        return "e2"
    if most is not None and not most and e1_prime_approved:
        return "e1'"
    return "e1"


def assemble_outcome(tiers, numbers, cfg=None, gate=None, most=None):
    """states, modifiers, title and abstract claim sentence from the EFFECTIVE tiers (primary tier lowered by the downgrade rows, PREREG_v4 9.8 rule 2).
    tiers: {'P1': S|N|none|reverse S, 'P2': bool, 'P3': bool, 'K1': bool, 'K2': S|N|none|reverse S, 'QH_g1': tier, 'QA10_g1': tier}
    numbers: from the primary analysis entries: {'X': rel. reduction pct + CI (P1), 'Y': excess of A9, 'Z': K2 pct + CI, 'W': A10 pct + CI, 'interval_P1': (a, b)}"""
    c = {**DEFAULT_CONFIG, **(cfg or {})}
    if gate and gate.get("tripped"):
        return {"gate_G": True, "title": None, "abstract_sentence": None, "reasons": gate.get("reasons"), "note": "no title and no claim: audit, then a new version (outcome table, gate G)"}
    P, K = state_P(tiers), state_K(tiers)
    M1 = tiers.get("QH_g1") == "reverse S"
    M2 = P == "P+" and tiers.get("QA10_g1") == "reverse S"
    tid, title = TITLES[(P, K)]
    if M2 and P == "P+":
        tid, title = T9B if K == "K-" else T9A
    elif M1 and tid in ("T1", "T2", "T3"):
        title = title.replace(M1_OLD, M1_NEW)
    ext = extent_clause(tiers, most, c["e1_prime_approved"])
    sent = _sentence(P, K, tiers, numbers, ext, M2)
    return {"gate_G": False, "P": P, "K": K, "M1": M1, "M2": M2, "extent_clause": ext, "title_id": tid, "title": title, "abstract_sentence": sent,
            "q_h_required_in_abstract": bool(M1), "tiers_used": tiers}


def _sentence(P, K, tiers, num, ext, M2):
    X, Y, Z, W = num.get("X"), num.get("Y"), num.get("Z"), num.get("W")
    ivP = ivs(*num["interval_P1"]) if num.get("interval_P1") else "95 % interval"
    ivK = ivs(*num["interval_K2"]) if num.get("interval_K2") else "95 % interval"
    ivW = ivs(*num["interval_W"]) if num.get("interval_W") else "95 % interval"
    nn = num.get("n", 40)
    if P == "P+":
        head = f"the physics-informed network's typical (median) held-out-condition error was {fmt1(X)} % lower than that of the best tuned data-driven learner ({ivP}; n = {nn})"
        e = {"e1": E1, "e1'": E1P, "e2": E2, "e3": E3}[ext].format(Y=fmt1(Y) if Y is not None else "?")
        head = f"{head}, {e}"
    elif P == "P0":
        word = "was no more than 10 % above" if tiers["P1"] == "N" else "could not be distinguished from"
        head = f"the physics-informed network's typical held-out-condition error {word} that of the best tuned data-driven learner ({'95 % interval' if not num.get('interval_P1') else ivP}; n = {nn})"
    else:
        head = (f"the best tuned data-driven learner's typical held-out-condition error was {fmt1(X)} % lower than that of the physics-informed network ({ivP}; n = {nn})")
    if K == "K+":
        kc = KCLAUSE_KPLUS.format(Z=fmt1(Z) if Z is not None else "?", iv=ivK)
    elif K == "K=":
        kc = KCLAUSE_KEQ_PASS.format(iv=ivK) if tiers.get("K1") else KCLAUSE_KEQ_FAIL
    else:
        kc = KCLAUSE_KMINUS.format(Z=fmt1(Z) if Z is not None else "?", iv=ivK)
    if P == "P-" and kc.startswith("and "):
        kc = "whereas " + kc[4:]               # P-/K+ is written with 'whereas'; the same connector is used for P-/K= (the table fixes the K= clause but not the joiner)
    sentence = f"{LEAD_IN} {head}, {kc}"
    if M2:
        sentence += T9_TAIL.format(W=fmt1(W) if W is not None else "?", iv=ivW)
    return sentence + "."


def qualifier_sentence(kind, tier, X=None, interval=None, n=40):
    """section 4.3 templates with the fixed names; interval is (lo, hi) of the relative reduction in percent (or None)"""
    iv = ivs(*interval) if interval else "95 % interval"
    if kind == "QH":
        A, B = "the soft-residual network", "the hard ODE with the same law"
        if tier == "none":
            return Q_H_NONE
    elif kind == "QA10":
        A, B = "the physics-informed network", A10_NAME
    elif kind == "QT":
        A, B = "training with the storage cells", "training without them"
        if tier == "none":
            return f"{QT_NAME} could not be distinguished ({iv})"
    else:
        raise ValueError(kind)
    return Q_TEMPLATES[tier].format(A=A, B=B, X=fmt1(X) if X is not None else "?", interval=iv, n=n)


def test_c_sentence(comparator_name, ratio, ci, k_below, n=13):
    """the fixed D011 Test C sentence (no tier word, whatever the direction); ratio = median over conditions of S_A1 / S_comparator, ci its order-statistic interval, k_below =
    number of conditions with ratio < 1"""
    return (f"on a held-out combination of temperature and laboratory (35 C cells from one laboratory, n = {n} conditions) the median condition error ratio against {comparator_name} was "
            f"{ratio:.2f} (95 % interval [{ci[0]:.2f}, {ci[1]:.2f}]; {k_below} of {n} below); {TEST_C_TAIL}")


# ------------------------------------------------------------------------------------------------ the whole step
CONTRASTS_FOR_LABS = {"P1": ("A1", "D*", G1), "P2": ("A1", "A9", G1), "K1": ("A15", "A1", G4), "K2": ("A15", "G15", G4), "QA10_g1": ("A1", "A10", G1), "QA10_g4": ("A1", "A10", G4),
                      "QH_g1": ("A1", "A2", G1), "QH_g4": ("A1", "A2", G4), "QT_g1": ("A1", "A13", G1)}


def primary_numbers(store, rule, tiers, sec=None):
    """numbers of the abstract sentence from the primary entries (unadjusted fallback 95 % intervals)"""
    num = {}
    if store.has("D*", *G1) and store.has("A1", *G1):
        _, L, _ = store.L("A1", "D*", G1)
        num["n"] = int(L.size)
        med = float(np.median(L))
        lo, hi, _, _ = rule.interval(L, 0.05)
        if tiers.get("P1") == "reverse S":
            num["X"] = pct_reduction(-med)
            num["interval_P1"] = (pct_reduction(-hi), pct_reduction(-lo))
        else:
            num["X"] = pct_reduction(med)
            num["interval_P1"] = (pct_reduction(lo), pct_reduction(hi))
    if store.has("A9", *G1):
        _, L, _ = store.L("A1", "A9", G1)
        num["Y"] = pct_excess(float(np.median(L)))
    kv = store.seed_view()
    if kv.has("A15", *G4) and kv.has("G15", *G4):
        _, L, _ = kv.L("A15", "G15", G4)
        L = -L if tiers.get("K2") == "reverse S" else L
        lo, hi, _, _ = rule.interval(L, 0.05)
        num["Z"] = pct_reduction(float(np.median(L)))
        num["interval_K2"] = (pct_reduction(lo), pct_reduction(hi))
    forms = [f for f in A10_FORMS if store.has(f, *G1)]
    if sec is not None:                          # review I1: [W] only from the forms that are reverse S (the clause is printed iff M2); a form that is not reverse S can have a negative effect
        rs = sec["tests"].get("QA10_g1", {}).get("reverse_S", {})
        forms = [f for f in forms if rs.get(f, {}).get("rejected")]
    if forms:
        best = None
        for f in forms:                           # M2: the weaker (smaller) reverse effect among the forms that are reverse S
            _, L, _ = store.L(f, "A1", G1)                           # L > 0 = this form of A10 is better than A1
            lo, hi, _, _ = rule.interval(L, 0.05)
            cand = (pct_reduction(float(np.median(L))), (pct_reduction(lo), pct_reduction(hi)))
            best = cand if best is None or cand[0] < best[0] else best
        num["W"], num["interval_W"] = best
    return num


def _qual_form(store, t, kind):
    """the arm whose numbers a qualifier sentence prints: Q-A10 has two forms; the one that is WEAKER for A1 sets the tier, so the sentence uses the form with the smallest median L
    (largest reverse effect is not used: for a reverse-S tier the form with the smallest reverse effect among the reverse-S forms, the conservative statement)"""
    if kind != "QA10":
        return t["arm"]
    forms = t["forms"]
    med = {f: float(np.median(store.L("A1", f, tuple(t["cell"]))[1])) for f in forms}
    if t["tier"] == "reverse S":
        rs = [f for f in forms if t["reverse_S"][f]["rejected"]]
        return max(rs, key=lambda f: med[f])
    return min(forms, key=lambda f: med[f])


ENDPOINT_NOTE = ("P-chain, secondary family, ladder, downgrade rows, Test C, S2 and NC-2 score the five-seed prediction ensemble; K1 and K2 score the per-seed rule for A1, A15 and G15 alike "
                 "(an average of five laws is not one law). A1 therefore has an ensemble score in the P chain and a per-seed score in the K chain; both are printed (D020 C1).")


def per_seed_descriptive(store):
    """per-seed P1 and P2 counts with the plain rule, labelled descriptive (not a downgrade row), and A1's two scores side by side"""
    sv = store.seed_view()
    out = {"label": "descriptive: per-seed condition scores, plain exact rule, not a downgrade row (D020 C1 item 5)", "available": sv is not store}
    for name, comp in (("P1", "D*"), ("P2", "A9")):
        if sv.has("A1", *G1) and sv.has(comp, *G1):
            _, L, _ = sv.L("A1", comp, G1)
            margins = (LOG_N, LOG_S) if name == "P1" else (LOG_S,)
            out[name] = {"n": int(L.size), "median_L": float(np.median(L)), "positives": {("N" if m_ == LOG_N else "S"): int((L > m_).sum()) for m_ in margins},
                         "p_plain": {("N" if m_ == LOG_N else "S"): float(gt.betabin_p(int((L > m_).sum()), int(L.size), 0.0)) for m_ in margins}}
    a1 = {}
    for cell, key in ((G1, "g1"), (G4, "g4")):
        if store.has("A1", *cell):
            a1[key] = {"ensemble_mean_pp": float(np.mean(list(store.scores("A1", *cell).values()))),
                       "per_seed_mean_pp": float(np.mean(list(sv.scores("A1", *cell).values()))) if sv.has("A1", *cell) else None}
    out["A1_scores_both_chains"] = a1
    return out


def run_v4(store, cfg=None, gate=None, row_tiers=None):
    """the whole confirmatory statistics of Design R2 from a Store. row_tiers (item 6): {contrast: lowest tier of the downgrade rows}; effective tier = min(primary, rows)."""
    rule, c = resolve_config(cfg)
    prim, Ls = primary_analysis(store, rule, c)
    sec = secondary_analysis(store, rule, c)
    tiers = dict(prim["tiers"])
    for k, v in (row_tiers or {}).items():
        if k in tiers:
            tiers[k] = (tier_min(tiers[k], v) if isinstance(tiers[k], str) else bool(tiers[k] and v))
        elif k in sec["tests"]:
            sec["tests"][k]["tier"] = tier_min(sec["tests"][k]["tier"], v)
    tiers["QH_g1"] = sec["tests"]["QH_g1"]["tier"]
    tiers["QA10_g1"] = sec["tests"]["QA10_g1"]["tier"]
    ext0 = extent_clause(tiers) if "P1" in tiers else None
    most = most_test(store, rule, c, ext0 == "e1")
    if most is not None and row_tiers and "most" in row_tiers:
        most["most"] = bool(most["most"] and row_tiers["most"])           # downgrade rows apply to the 'most' test as a binary pass/fail
    out = {
        "rule": rule.describe(), "config": {k: c[k] for k in ("sign_rule", "rho_s0", "graph_w", "alpha", "e1_prime_approved", "k_chain_struck")}, "seed_root": MC_SEED_ROOT,
        "primary": prim, "secondary": sec, "plain_descriptive": plain_rows(store, c), "most_test": most, "dependence_sensitivity": dependence_sensitivity(store, rule, c),
        "estimated": estimated_tables(store, rule), "lab_rows": lab_rows(store, rule, CONTRASTS_FOR_LABS), "effective_tiers": tiers,
        "per_seed_descriptive": per_seed_descriptive(store), "endpoint_note": ENDPOINT_NOTE,
    }
    if "P1" in tiers:
        out["outcome"] = assemble_outcome(tiers, primary_numbers(store, rule, tiers, sec), c, gate, None if most is None else most["most"])
        q = {}
        for key, kind in (("QH_g1", "QH"), ("QH_g4", "QH"), ("QA10_g1", "QA10"), ("QA10_g4", "QA10"), ("QT_g1", "QT")):
            t = sec["tests"][key]
            if not t["forms"]:
                continue
            f = _qual_form(store, t, kind)
            _, L, _ = store.L("A1", f, tuple(t["cell"]))
            lo, hi, _, _ = rule.interval(L, 0.05)
            med = float(np.median(L))
            X = pct_reduction(-med) if t["tier"] == "reverse S" else pct_reduction(med)
            iv = (pct_reduction(-hi), pct_reduction(-lo)) if t["tier"] == "reverse S" else (pct_reduction(lo), pct_reduction(hi))
            q[key] = qualifier_sentence(kind, t["tier"], X, iv, int(L.size))
        out["qualifier_sentences"] = q
    return out
