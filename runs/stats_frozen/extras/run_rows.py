"""Rows (b) per stage, (c), (d), (e), (v), (vi) of PREREG_v4 9.9 from the existing run outputs, with the frozen code's own functions (read-only import).
Writes only runs/stats_frozen/extras/row_*.json. Descriptive: no tier, state or claim word is set; tiers printed are what a row would reach at the primary final levels.
Run: MAIN/.venv/Scripts/python.exe -P run_rows.py </dev/null  (one thread, CPU)."""
import json, os, sys
import numpy as np

MAIN = r"C:\Users\Shlok\Downloads\PINN KAN battery paper"
sys.path.insert(0, os.path.join(MAIN, "code"))
os.chdir(MAIN)
from pinnkan import stats_v4 as v4, stats_rows, stats_ext  # noqa: E402

RUNS = os.path.join(MAIN, "runs")
OUT = os.path.join(RUNS, "stats_frozen", "extras")
G1, G4 = v4.G1, v4.G4
contr = json.load(open(os.path.join(RUNS, "stats_frozen", "analysis", "contrasts_v4_B.json"), encoding="utf8"))
cfg, _ = v4.effective_config(None, MAIN)
rule, c = v4.resolve_config(cfg)
dirs = {m: [os.path.join(RUNS, f"conf_samsung_B_f{f}_m{m}") for f in range(5)] for m in (8, 16, 32)}
P = v4.Store.from_runs([d for m in dirs for d in dirs[m]], strict=True)
lv, sec = stats_rows.primary_levels(contr)
strata = stats_ext.condition_strata([{"dir": d} for d in dirs[32]])        # frozen lab map (labmap) and stage, from condition_meta.json
lab_disagree = {k: [strata[k]["lab"], P.lab.get(k)] for k in strata if strata[k]["lab"] != P.lab.get(k)}


def dump(name, obj):
    with open(os.path.join(OUT, name), "w", encoding="utf8") as f:
        json.dump(obj, f, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))


# contrast catalogue: (key, tier key, target, comparator, cell, seed_view, level)
Q = lambda k, cell: sec[k]["slot"]
CONTRASTS = [("P1: A1 vs D* g1", "P1", "A1", "D*", G1, False, lv["P1N"]), ("P2: A1 vs A9 g1", "P2", "A1", "A9", G1, False, lv["P2"]),
             ("R1_g1: A1 vs R1 g1", "R1_g1", "A1", "R1", G1, False, lv["R1g1"]),
             ("QA10_g1: A1 vs A10", "QA10_g1", "A1", "A10", G1, False, Q("QA10_g1", 0)), ("QA10_g1: A1 vs A10P", "QA10_g1", "A1", "A10P", G1, False, Q("QA10_g1", 0)),
             ("QA10_g4: A1 vs A10", "QA10_g4", "A1", "A10", G4, False, Q("QA10_g4", 0)), ("QA10_g4: A1 vs A10P", "QA10_g4", "A1", "A10P", G4, False, Q("QA10_g4", 0)),
             ("QH_g1: A1 vs A2", "QH_g1", "A1", "A2", G1, False, Q("QH_g1", 0)), ("QH_g4: A1 vs A2", "QH_g4", "A1", "A2", G4, False, Q("QH_g4", 0)),
             ("QT_g1: A1 vs A13", "QT_g1", "A1", "A13", G1, False, Q("QT_g1", 0)),
             ("K1: A15 vs A1 g4 (per-seed)", "K1", "A15", "A1", G4, True, lv["K1"]), ("K2: A15 vs G15 g4 (per-seed)", "K2", "A15", "G15", G4, True, lv["K2N"])]
PRIM_TIER = {**{k: contr["primary"]["tiers"][k] for k in ("P1", "P2", "P3", "R1_g1", "K1", "K2")}, **{k: v["tier"] for k, v in contr["secondary"]["tests"].items()}}


def pr(x):
    return None if x is None else 100.0 * (1.0 - float(np.exp(-x)))


# ------------------------------------------------------------------ (b) per stage (per lab is in the frozen lab_rows; recomputed here beside it with mean pp) and (c) leave-one-lab-out by the frozen functions
rows_b = {"definition": "PREREG 9.9 (b): mean paired pp difference (comparator - target) and median log ratio per laboratory and per stage, with n; stats_ext.lab_stage_rows (frozen code) on the primary store's L and pp differences; strata from the frozen lab_map.json and condition_meta.json stage; descriptive",
          "lab_map_vs_store_majority_disagreements": lab_disagree, "contrasts": {}}
rows_c = {"definition": ("PREREG 9.9 (c): leave-one-laboratory-out. (1) stats_ext.lab_stage_rows leave_one_lab_out as written (plain exact sign test at the primary final level, v3 convention); "
                         "(2) every gated and secondary contrast recomputed with stats_rows.row_tiers on a copy of the primary store without the conditions of one laboratory (frozen sign rule, primary final levels, reduced n); descriptive, no consequence"),
          "plain_exact_stats_ext": {}, "frozen_rule_row_tiers": {}}
for key, tk, tgt, comp, cell, seed, level in CONTRASTS:
    st = P.seed_view() if seed else P
    conds, L, d = st.L(tgt, comp, cell)
    entry = {"L_by_cond": dict(zip(conds, L.tolist())), "d_by_cond": dict(zip(conds, d.tolist()))}
    r = stats_ext.lab_stage_rows(entry, strata, level)
    rows_b["contrasts"][key] = {"n": len(conds), "level_used": level, "per_lab": r["per_lab"], "per_stage": r["per_stage"]}
    rows_c["plain_exact_stats_ext"][key] = r["leave_one_lab_out"]


def without(store, lab):
    drop = {k for k in strata if strata[k]["lab"] == lab}
    f = lambda T: {kk: {a: {cd: s for cd, s in v.items() if cd not in drop} for a, v in t.items()} for kk, t in T.items()}
    return v4.Store(f(store.tables), store.lab, store.fold, store.k_full, store.notes, f(store.seed_tables) if store.seed_tables else None), len(drop)


for lab in sorted({s["lab"] for s in strata.values()}):
    S, nd = without(P, lab)
    tiers = stats_rows.row_tiers(contr, S, rule)
    ent = {}
    for key, tk, tgt, comp, cell, seed, level in CONTRASTS:
        sv = S.seed_view() if seed else S
        if sv.has(tgt, *cell) and sv.has(comp, *cell):
            e = v4.entry(sv, key, tgt, comp, cell, rule, bca=False)
            ent[key] = {"n": e["n"], "median_L": e["median_L"], "pct_reduction": e["rel_reduction_pct"], "pct_reduction_ci95": e["rel_reduction_ci_pct"], "positives": e["n_wins"],
                        "tier_it_would_reach": tiers.get(tk), "primary_tier": PRIM_TIER.get(tk)}
    rows_c["frozen_rule_row_tiers"][lab] = {"conditions_removed": nd, "tiers_all_keys": tiers, "contrasts": ent}
dump("row_b_stage.json", rows_b)
dump("row_c_leave_one_lab_out.json", rows_c)
print("b, c done", flush=True)


# ------------------------------------------------------------------ (d) two-stage bootstrap (stats_ext.two_stage_bootstrap; the cell pairing is stats_ext.cell_pairs with the cell file of the cell)
def pairs_for(mdirs, fname, comp_alias):
    out = {}
    for d in mdirs:
        cs = json.load(open(os.path.join(d, fname), encoding="utf8"))
        arm = comp_alias if comp_alias in cs else json.load(open(os.path.join(d, "comparators.json"), encoding="utf8"))[comp_alias]["arm"]
        by = {}
        for cid, r in cs["A1"].items():
            if cid in cs[arm]:
                by.setdefault(r["cond"], []).append((r["rmse_pp"], cs[arm][cid]["rmse_pp"]))
        for cd, v in by.items():
            a = np.array(v, float)
            out[cd] = (a[:, 0], a[:, 1])
    return out


rows_d = {"definition": ("PREREG 9.9 (d): two-stage bootstrap (conditions, then scored cells inside each sampled condition; weights = scored cells), stats_ext.two_stage_bootstrap, B = 10000, "
                         "percentile 95 %. The point value uses cell_scores (mean-over-seeds cell RMSE), not the ensemble-endpoint condition scores of the primary, so median_L can differ from the primary median. "
                         "K1/K2 (per-seed endpoints) are not computed: cell_scores holds no per-seed cell scores. Descriptive."), "contrasts": {}}
for key, tk, tgt, comp, cell, seed, level in CONTRASTS:
    if seed:
        rows_d["contrasts"][key] = "not computed: the K contrasts use per-seed endpoints and cell_scores files hold mean-over-seeds cell scores only"
        continue
    md = dirs[cell[0]]
    fname = "cell_scores.json" if cell[1] == "full" else f"cell_scores_k{cell[1]}.json"
    try:
        pairs = pairs_for(md, fname, comp)
    except (KeyError, FileNotFoundError) as e:
        rows_d["contrasts"][key] = f"not computed: {e!r}"
        continue
    conds, L, dd = P.L(tgt, comp, cell)
    entry = {"L_by_cond": dict(zip(conds, L.tolist()))}
    r = stats_ext.two_stage_bootstrap(entry, pairs, strata, f"extras|{key}|two_stage")
    r["median_L_primary_store"] = float(np.median(L))
    r["pct_reduction_point_cell_scores"] = pr(r.get("median_L"))
    r["pct_reduction_ci95"] = [pr(r["median_L_ci95"][0]), pr(r["median_L_ci95"][1])] if "median_L_ci95" in r else None   # pr is increasing in L: no swap (fixed after re-check 2)
    rows_d["contrasts"][key] = r
    print("d", key, flush=True)
dump("row_d_two_stage_bootstrap.json", rows_d)

# ------------------------------------------------------------------ (e) pp-scale row: BCa lower bound of the mean paired pp difference against delta*E (stats_ext.margin_rows tier_pp rule), registered deltas 0.02 and 0.10 of 9.2
mg = json.load(open(os.path.join(RUNS, "stats_frozen", "analysis", "margins.json"), encoding="utf8"))["contrasts"]
est = {(r["comparator"], tuple(r["cell"])): r for r in contr["estimated"]["rows"]}
rows_e = {"definition": ("PREREG 9.9 (e) / 9.2: pp-scale row. mean paired pp difference (comparator - target) with the BCa 95 % interval of the frozen step (estimated rows) against the pp margins "
                         "delta_S = 0.02 E and delta_N = 0.10 E of margins.json (stats_ext 'tier_pp' rule: S if the BCa lower bound > delta_S, N if > -delta_N, else none); descriptive, sets no tier"), "rows": {}}
mapping = [("A1 vs D*", "D*", G1), ("A1 vs A9", "A9", G1), ("A1 vs A10", "A10", G1), ("A1 vs A10P", "A10P", G1), ("A1 vs A10", "A10", G4), ("A1 vs A10P", "A10P", G4), ("A1 vs A2", "A2", G1), ("A1 vs A2", "A2", G4),
           ("A1 vs A13", "A13", G1), ("A1 vs D*", "D*", G4), ("A1 vs A9", "A9", G4)]
for name, comp, cell in mapping:
    e = est.get((comp, cell))
    mk = f"m{cell[0]}_k{cell[1]}"
    if e is None and name == "A1 vs A13":              # not an estimated comparator of the frozen step: same entry() function, BCa label by the frozen convention
        e = v4.entry(P, name, "A1", comp, cell, rule, bca=True, bca_label=f"B|{name}|g{cell[0]}-{cell[1]}|BCa_mean_pp")
    m = mg.get(name, {}).get(mk)
    lab = f"{name} {mk}"
    if e is None or m is None:
        rows_e["rows"][lab] = "not computed: no estimated row or no margin entry"
        continue
    lo, hi = e["mean_pp_ci"]
    tier = "S" if lo > m["delta_S_pp"] else ("N" if lo > -m["delta_N_pp"] else "none")
    rows_e["rows"][lab] = {"n": e["n"], "mean_pp_diff": e["mean_pp"], "mean_pp_bca95": [lo, hi], "E_pp": m["E_pp"], "delta_S_pp": m["delta_S_pp"], "delta_N_pp": m["delta_N_pp"], "pp_scale_tier_it_would_reach": tier}
for name, tgt, comp, kk in (("A15 vs A1", "A15", "A1", "K1"), ("A15 vs G15", "A15", "G15", "K2")):      # K1, K2: per-seed endpoints (seed view), same entry() and BCa as the other rows
    mk = "m32_kfull"
    m = mg.get(name, {}).get(mk)
    lab = f"{name} {mk} ({kk}; per-seed endpoints)"
    sv = P.seed_view()
    if m is None or not (sv.has(tgt, *G4) and sv.has(comp, *G4)):
        rows_e["rows"][lab] = "not computed: no margin entry or arm missing in the per-seed tables"
        continue
    e = v4.entry(sv, name, tgt, comp, G4, rule, bca=True, bca_label=f"B|{name}|g32-full|BCa_mean_pp")
    lo, hi = e["mean_pp_ci"]
    tier = "S" if lo > m["delta_S_pp"] else ("N" if lo > -m["delta_N_pp"] else "none")
    rows_e["rows"][lab] = {"n": e["n"], "mean_pp_diff": e["mean_pp"], "mean_pp_bca95": [lo, hi], "E_pp": m["E_pp"], "delta_S_pp": m["delta_S_pp"], "delta_N_pp": m["delta_N_pp"], "pp_scale_tier_it_would_reach": tier}
dump("row_e_pp_scale.json", rows_e)
print("e done", flush=True)

# ------------------------------------------------------------------ (v), (vi): single-seed (seed 0 of the final refit) inversion-diagnostic scores written by the runs; D* not reselected
def alias_arm(d, alias):
    return json.load(open(os.path.join(d, "comparators.json"), encoding="utf8"))[alias]["arm"]


def inv_tables(tag):
    """-> {cell: {'A1': {cond: s}, 'A9': ..., 'AG': ..., 'D*': ...}}; arms that are not inverted (GP, LightGBM D*) keep their base scores"""
    res = {}
    for cell, m, suf in ((G1, 8, "k2"), (G4, 32, "kfull")):
        t = {"A1": {}, "A9": {}, "AG": {}, "D*": {}}
        notes = set()
        for d in dirs[m]:
            sens = json.load(open(os.path.join(d, f"condition_scores_sens_{tag}_{suf}.json"), encoding="utf8"))
            base = json.load(open(os.path.join(d, "condition_scores.json" if cell[1] == "full" else f"condition_scores_k{cell[1]}.json"), encoding="utf8"))
            for a in ("A1", "A9"):
                t[a].update(sens[a])
            for al in ("AG", "D*"):
                arm = alias_arm(d, al)
                if arm in sens:
                    t[al].update(sens[arm])
                else:
                    t[al].update(base[arm]); notes.add(f"{al} = {arm} not inverted: base (ensemble) score")
        res[cell] = (t, sorted(notes))
    return res


def inv_row(tag, desc):
    out = {"row": tag, "description": desc, "cells": {}}
    for cell, (t, notes) in inv_tables(tag).items():
        s = v4.Store({(cell[0], cell[1]): t}, k_full=4)
        blk = {"notes": notes, "arm_means_pp": {a: float(np.mean(list(t[a].values()))) for a in t}}
        for lab_, comp, tkey, node_names in (("P1: A1 vs D*", "D*", "P1", (("P1N", v4.LOG_N), ("P1S", v4.LOG_S))), ("P2: A1 vs A9", "A9", "P2", (("P2", v4.LOG_S),)), ("A1 vs AG", "AG", None, ())):
            conds, L, _ = s.L("A1", comp, cell)
            e = v4.entry(s, lab_, "A1", comp, cell, v4.PLAIN, bca=False, test="B")
            b = {"n": e["n"], "median_L": e["median_L"], "pct_reduction": e["rel_reduction_pct"], "pct_reduction_ci95_plain": e["rel_reduction_ci_pct"], "positives_L_gt_0": e["n_wins"]}
            if cell == G1:
                for nm, mgn in node_names:
                    pos, n, p = v4.PLAIN.test(L, mgn)
                    b[f"plain_count_{nm}"] = {"margin": mgn, "positives": pos, "n": n, "reaches_plain_critical_count_at_primary_final_level": stats_rows._positives_reach(v4.PLAIN, L, mgn, lv[nm]),
                                              "primary_final_level": lv[nm]}
            blk[lab_] = b
        out["cells"][f"{cell[0]}|{cell[1]}"] = blk
    return out


rows_v = {"definition": ("PREREG 9.9 (v): A1, A9 and AG scores and the P1 and P2 plain-rule counts recomputed with each diagnostic start j = 1..3 (condition_scores_sens_v{j}_k2 at g1, _kfull at g4) in place of the "
                         "prior mode, the same start for every arm, D* not reselected. The files hold seed 0 of the final refit only (run.py _inversion_diagnostics), the primary uses the five-seed ensemble endpoint; "
                         "so the counts are single-seed and are not compared with the primary tiers. Plain-rule counts as registered; descriptive."),
          "primary_reference_counts_g1": {"P1": {k: contr["primary"]["nodes"][k]["positives"] for k in ("P1N", "P1S")}, "P2": contr["primary"]["nodes"]["P2"]["positives"], "note": "ensemble endpoint, rule of the frozen step (p, not plain)"},
          "starts": {f"v{j}": inv_row(f"v{j}", f"diagnostic start {j}") for j in (1, 2, 3)}}
rows_vi = {"definition": ("PREREG 9.9 (vi): frozen fitted models re-inverted with z-prior weight 4 and 16 (inference only), A1, A9, AG at g1 and g4, seed 0 of the final refit (files condition_scores_sens_vi{4,16}_*); "
                          "P1/P2 counts and plain-rule flags computed with the same function as (v); descriptive."), "weights": {f"vi{w}": inv_row(f"vi{w}", f"z-prior weight {w}") for w in (4, 16)}}
dump("row_v_inversion_starts.json", rows_v)
dump("row_vi_zprior_weight.json", rows_vi)
print("v, vi done", flush=True)
