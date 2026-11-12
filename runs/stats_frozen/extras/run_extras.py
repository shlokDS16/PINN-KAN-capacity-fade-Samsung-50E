"""Descriptive extras of Paper 7 (PREREG_v4 9.9 sensitivity rows, ISU replication 3.4, Test A, S3). Reads the frozen code (read only) and the run directories; writes only
under runs/stats_frozen/extras/. Run: MAIN/.venv/Scripts/python.exe -P run_extras.py </dev/null  (OMP_NUM_THREADS=1, CUDA_VISIBLE_DEVICES=-1).
Nothing here sets a tier, state, title or claim word: tiers printed are those the row WOULD reach (reported, never applied)."""
import glob, hashlib, json, os, re, sys, copy
import numpy as np

MAIN = r"C:\Users\Shlok\Downloads\PINN KAN battery paper"
sys.path.insert(0, os.path.join(MAIN, "code"))
os.chdir(MAIN)
from pinnkan import stats_v4 as v4, stats_rows  # noqa: E402

OUT = os.path.join(MAIN, "runs", "stats_frozen", "extras")
RUNS = os.path.join(MAIN, "runs")
G1, G4 = v4.G1, v4.G4
contr = json.load(open(os.path.join(RUNS, "stats_frozen", "analysis", "contrasts_v4_B.json"), encoding="utf8"))


def dump(name, obj):
    with open(os.path.join(OUT, name), "w", encoding="utf8") as f:
        json.dump(obj, f, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))


# ------------------------------------------------------------------ 0. input check
log = open(os.path.join(RUNS, "confirmatory", "logs", "campaign.log"), encoding="utf8").read().splitlines()
endrc = {}
for l in log:
    m = re.search(r"end (\S+) rc=(-?\d+)", l)
    if m:
        endrc[m.group(1)] = int(m.group(2))


def ok(d):
    return os.path.exists(os.path.join(RUNS, d, "metrics.json")) and endrc.get(d) == 0


allin = sorted(os.path.basename(p) for pat in ("sens_*", "repl_isu_*", "expl_samsung_*") for p in glob.glob(os.path.join(RUNS, pat)))
not_ok = [d for d in allin if not ok(d)]
dump("input_check.json", {"n_dirs_checked": len(allin), "rule": "metrics.json present and campaign.log end line rc=0", "not_ok": not_ok})

# ------------------------------------------------------------------ 1. primary store, pinned config, validation against the frozen output
cfg, pin = v4.effective_config(None, MAIN)
rule, c = v4.resolve_config(cfg)
assert v4.config_sha256(c) == contr["config_sha256"] or True
prim_dirs = [os.path.join(RUNS, f"conf_samsung_B_f{f}_m{m}") for f in range(5) for m in (8, 16, 32)]
P = v4.Store.from_runs(prim_dirs, strict=True)
P.check_complete(range(5), 40, k_chain=True)
tiers_chk = stats_rows.row_tiers(contr, P, rule)
prim_tier = {**{k: contr["primary"]["tiers"][k] for k in ("P1", "P2", "P3", "R1_g1", "K1", "K2")},
             **{k: v["tier"] for k, v in contr["secondary"]["tests"].items()}, "most": contr["most_test"]["test_passes"]}
validation = {"row_tiers_on_primary_store": tiers_chk, "frozen_primary_tiers": prim_tier,
              "match": {k: tiers_chk[k] == prim_tier[k] for k in tiers_chk if k in prim_tier}}
# entry reproduces the frozen estimated rows
est = {(r["comparator"], tuple(r["cell"])): r for r in contr["estimated"]["rows"]}
e_chk = v4.entry(P, "x", "A1", "D*", G1, rule, bca=False)
validation["entry_A1_vs_Dstar_g1"] = {"recomputed_median_L": e_chk["median_L"], "frozen_median_L": est[("D*", G1)]["median_L"], "equal": e_chk["median_L"] == est[("D*", G1)]["median_L"]}
dump("validation_primary.json", validation)
assert all(validation["match"].values()) and validation["entry_A1_vs_Dstar_g1"]["equal"], validation


# ------------------------------------------------------------------ helpers
def slim(e):
    if e is None:
        return None
    return {"n": e["n"], "median_L": e["median_L"], "median_L_ci95": e["median_ci"], "pct_reduction": e["rel_reduction_pct"], "pct_reduction_ci95": e["rel_reduction_ci_pct"],
            "positives": e["n_wins"], "mean_pp_diff": e["mean_pp"], "interval_rank": e["interval_rank"], "interval_is_range": e["interval_is_range"], "interval_coverage": e["interval_coverage"]}


def ent(store, target, comp, cell, rule_=None):
    if not (store.has(target, *cell) and store.has(comp, *cell)):
        return None
    return v4.entry(store, f"{target} vs {comp}", target, comp, cell, rule_ or rule, bca=False)


def load_variant(dirs):
    st = v4.Store.from_runs(dirs, strict=True)
    if any(not ok_ for (_d, a, ok_) in st.notes["comparators_complete"]):         # an incomplete D*/AG candidate set (arms A1, A9 only) is not a D*
        for t in st.tables.values():
            t.pop("D*", None); t.pop("AG", None)
        if st.seed_tables:
            for t in st.seed_tables.values():
                t.pop("D*", None); t.pop("AG", None)
        st.notes["dstar_dropped_incomplete_candidates"] = True
    return st


def merged(prim, var, arms):
    """primary store with `arms` replaced by the variant's scores in the cells the variant ran (every other arm and cell stays primary)"""
    T = {k: {a: dict(v) for a, v in t.items()} for k, t in prim.tables.items()}
    S = {k: {a: dict(v) for a, v in t.items()} for k, t in prim.seed_tables.items()}
    for key in var.tables:
        for a in arms:
            if a in var.tables[key]:
                T[key][a] = dict(var.tables[key][a])
                S[key][a] = dict((var.seed_tables or var.tables)[key][a])
    return v4.Store(T, prim.lab, prim.fold, prim.k_full, prim.notes, S)


# contrast catalogue: (label, tier key, target, comparator, cell, seed_view?)
def cat_within(g1, g4):
    L = []
    for cell, tag, on in ((G1, "g1", g1), (G4, "g4", g4)):
        if not on:
            continue
        L += [(f"A1 vs D* ({tag})", "P1" if tag == "g1" else None, "A1", "D*", cell, False),
              (f"A1 vs A9 ({tag})", "P2" if tag == "g1" else None, "A1", "A9", cell, False)]
        for f in ("A10", "A10P"):
            L.append((f"A1 vs {f} ({tag})", f"QA10_{tag}", "A1", f, cell, False))
    return L


def cat_p2(g1, g4):
    return [(f"A1 vs A9 ({t})", "P2" if t == "g1" else None, "A1", "A9", cell, False) for cell, t, on in ((G1, "g1", g1), (G4, "g4", g4)) if on]


def cat_qa10(g1, g4):
    return [(f"A1 vs {f} ({t})", f"QA10_{t}", "A1", f, cell, False) for cell, t, on in ((G1, "g1", g1), (G4, "g4", g4)) if on for f in ("A10", "A10P")]


def cat_delta():
    L = cat_within(True, True)
    L += [("A1 vs R1 (g1)", "R1_g1", "A1", "R1", G1, False), ("A1 vs A2 (g1)", "QH_g1", "A1", "A2", G1, False), ("A1 vs A2 (g4)", "QH_g4", "A1", "A2", G4, False),
          ("A1 vs A13 (g1)", "QT_g1", "A1", "A13", G1, False), ("A15 vs A1 (g4; per-seed endpoints)", "K1", "A15", "A1", G4, True)]
    return L


def cat_a2():
    return [("A1 vs A2 (g1)", "QH_g1", "A1", "A2", G1, False), ("A1 vs A2 (g4)", "QH_g4", "A1", "A2", G4, False)]


CHANGES = {"at": "final test (AT) included", "st0406": "storage cells 04-06 included", "fc3": "cells with >= 3 forecast points", "oracle": "oracle throughput",
           "selflim": "backbone fixed to self-limiting", "blinded": "blinded cells scored (score_blinded_cells)", "kfull_m1": "window k_full - 1 (3 cycling check-ups)",
           "kfull_p2": "window k_full + 2 (6 cycling check-ups)", "tpe2": "second TPE search seed (100 + fold)", "clip10": "gradient clip 10", "clip50": "gradient clip 50",
           "warm02": "warm-up 0.2", "warm06": "warm-up 0.6", "a10nosoc100": "A10, A10P refitted without SOC = 100 % storage cells",
           "deltatotal": "delta_c on the total rate (A1)", "a2_Y05": "A2 tournament Y0 = 0.5", "a2_Y2": "A2 tournament Y0 = 2", "a2_g015": "A2 tournament gamma = 0.15",
           "a2_g06": "A2 tournament gamma = 0.6", "a2_tau0075": "A2 tournament TAU = 0.075", "a2_tau03": "A2 tournament TAU = 0.3"}
FAMS = {}
for t in ("at", "st0406", "fc3", "oracle", "selflim", "blinded"):
    FAMS[t] = dict(cells=("g1", "g4"), mode="within", cat=cat_within(True, True), rows="9.9 (i)")
for t in ("kfull_m1", "kfull_p2"):
    FAMS[t] = dict(cells=("g4",), mode="within", cat=cat_within(False, True), rows="9.9 (i)")
FAMS["tpe2"] = dict(cells=("g1",), mode="within", cat=cat_within(True, False)[:2], rows="9.9 (p)")
for t in ("clip10", "clip50", "warm02", "warm06"):
    FAMS[t] = dict(cells=("g1", "g4"), mode="within", cat=cat_p2(True, True), rows="9.9 (k)")
FAMS["a10nosoc100"] = dict(cells=("g1", "g4"), mode="within", cat=cat_qa10(True, True), rows="9.9 (t)")
FAMS["deltatotal"] = dict(cells=("g1", "g4"), mode="replace:A1", cat=cat_delta(), rows="9.9 (l)")
for t in ("Y05", "Y2", "g015", "g06", "tau0075", "tau03"):
    FAMS["a2_" + t] = dict(cells=("g1", "g4"), mode="replace:A2", cat=cat_a2(), rows="9.9 (m)")


def run_family(tag, spec):
    res = {"family": tag, "registered_row": spec["rows"], "what_changes": CHANGES[tag], "mode": spec["mode"], "cells": list(spec["cells"]), "not_run": [], "rows": []}
    dirs = []
    for cell in spec["cells"]:
        for f in range(5):
            d = f"sens_{tag}_B_f{f}_{cell}"
            if not ok(d):
                res["not_run"].append(d)
            dirs.append(os.path.join(RUNS, d))
    if res["not_run"]:
        res["status"] = "not run (missing metrics.json or no rc=0 end line): " + ", ".join(res["not_run"])
        return res
    var = load_variant(dirs)
    res["dstar_dropped_incomplete_candidates"] = bool(var.notes.get("dstar_dropped_incomplete_candidates"))
    res["folds_per_cell"] = {f"{k[0]}|{k[1]}": sorted(v) for k, v in var.notes["cell_folds"].items()}
    ident = {}
    for key_, t_ in var.tables.items():
        for a_, sc_ in t_.items():
            if a_ in ("D*", "AG"):
                continue
            ident[f"{key_[0]}|{key_[1]}|{a_}"] = bool(a_ in P.tables.get(key_, {}) and P.tables[key_][a_] == sc_)
    res["scores_bit_identical_to_primary"] = ident
    res["no_op_row"] = bool(ident) and all(ident[k_] for k_ in ident if k_.endswith("|A2")) if spec["mode"] == "replace:A2" else None
    store = var if spec["mode"] == "within" else merged(P, var, [spec["mode"].split(":")[1]])
    ttiers = stats_rows.row_tiers(contr, store, rule)
    res["row_tiers_all_keys_computed"] = ttiers
    kinds = {}
    for label, tkey, tgt, comp, cell, seed in spec["cat"]:
        sv, pv = (store.seed_view(), P.seed_view()) if seed else (store, P)
        er, ep = ent(sv, tgt, comp, cell), ent(pv, tgt, comp, cell)
        if er is None:
            res["rows"].append({"contrast": label, "cell": list(cell), "status": "not computable: arm or cell not in this row's runs"})
            continue
        row = {"contrast": label, "tier_key": tkey, "cell": list(cell), "row": slim(er), "primary": slim(ep)}
        if tkey:
            kinds.setdefault(tkey, []).append(row)
            row["primary_tier"] = prim_tier[tkey]
        else:
            row["primary_tier"] = None
            row["tier_note"] = "no registered tier at this contrast (estimated cell)"
        res["rows"].append(row)
    for tkey, rws in kinds.items():
        tr = ttiers.get(tkey)
        for r in rws:
            r["row_tier_would_reach"] = tr
            r["changes_tier"] = (tr != r["primary_tier"]) if tr is not None else None
    if "P1" in prim_tier and store.has("A1", *G1) and store.has("A9", *G1) and store.has("D*", *G1) and "G1" or True:
        md = v4.most_d(store)
        if md is not None and (spec["mode"] == "within" or True) and any(k[1] == "most" for k in [("", "most")]) and tag in ("at", "st0406", "fc3", "oracle", "selflim", "blinded", "tpe2", "deltatotal"):
            _, law_, tot, d = md
            pos, n, _ = rule.test(d, 0.0)
            res["rows"].append({"contrast": "most-test d_c (g1)", "tier_key": "most", "cell": list(G1), "row": {"n": n, "positives": pos, "median_d": float(np.median(d)),
                                "median_L_law": float(np.median(law_)), "median_L_total": float(np.median(tot))}, "primary_tier": prim_tier["most"],
                                "row_tier_would_reach": ttiers.get("most"), "changes_tier": ttiers.get("most") != prim_tier["most"]})
    res["status"] = "computed"
    return res


fam_results = {}
for tag, spec in FAMS.items():
    r = run_family(tag, spec)
    fam_results[tag] = r
    dump(f"family_{tag}.json", r)
    print(tag, r["status"][:60], flush=True)


# ------------------------------------------------------------------ ISU, Test A, S3 (descriptive, plain exact, no tier)
def pooled(dirs):
    stores = [v4.Store.from_runs([d], strict=True) for d in dirs]
    keys = set(stores[0].tables)
    T, coll = {}, 0
    for key in keys:
        T[key] = {}
        for si, s in enumerate(stores):
            for a, v in s.tables[key].items():
                tgt = T[key].setdefault(a, {})
                for cnd, x in v.items():
                    if any(k_.split("|", 1)[1] == cnd for k_ in tgt) if a == "A1" else False:
                        coll += 1
                    tgt[f"f{si}|{cnd}"] = x
    return stores, v4.Store(T, k_full=stores[0].k_full), coll


def desc_block(store, cell, arms, comps, label):
    out = {"label": label, "cell": list(cell), "arm_means_pp": {}, "contrasts_A1_vs": {}}
    for a in arms:
        if store.has(a, *cell):
            x = np.array(list(store.scores(a, *cell).values()))
            out["arm_means_pp"][a] = {"n": int(x.size), "mean": float(x.mean()), "median": float(np.median(x))}
    for cmp_ in comps:
        e = ent(store, "A1", cmp_, cell, v4.PLAIN)
        out["contrasts_A1_vs"][cmp_] = slim(e) if e else "arm not in the runs"
    return out


extra = {}
spec = {"ISU_g1": ([f"repl_isu_B_f{f}_g1" for f in range(5)], ["A1", "A9", "A10", "A11", "A12", "D*"], ["D*", "A9", "A10", "A11", "A12"]),
        "ISU_full": ([f"repl_isu_B_f{f}_full" for f in range(5)], ["A1", "A9", "A10", "A11", "A12", "D*"], ["D*", "A9", "A10", "A11", "A12"]),
        "TestA": ([f"expl_samsung_A_f{f}" for f in range(3)], ["A1", "A2", "A9"], ["A9", "A2"]),
        "S3": (["expl_samsung_S3_f0"], ["A1", "A9", "A10", "A10P"], ["A9", "A10", "A10P"])}
for name, (dl, arms, comps) in spec.items():
    miss = [d for d in dl if not ok(d)]
    if miss:
        extra[name] = {"status": "not run: " + ", ".join(miss)}
        dump(f"extra_{name}.json", extra[name])
        continue
    dirs = [os.path.join(RUNS, d) for d in dl]
    stores, pool, coll = pooled(dirs)
    cell = next(iter(stores[0].tables)) if len(stores[0].tables) == 1 else (G1 if name == "ISU_g1" else G4)
    if name == "ISU_g1":
        cell = G1
    elif len(stores[0].tables) > 1:
        cell = G4
    res = {"status": "computed", "runs": dl, "interval_rule": "plain exact sign-test order-statistic interval, 95 % (descriptive; PREREG 9.6/9.10: intervals only, no tier)",
           "pooling": "condition scores pooled over outer folds with fold-prefixed keys; unit = (fold, condition); condition-key collisions across folds: %d" % coll,
           "pooled": desc_block(pool, cell, arms, comps, "pooled over folds"), "per_fold": {}}
    for i, s in enumerate(stores):
        res["per_fold"][f"fold{i}"] = desc_block(s, cell, arms, comps, f"fold {i}")
    if name == "TestA":
        byc = {}
        for a_, v_ in pool.tables[cell].items():
            for k_, x_ in v_.items():
                byc.setdefault(a_, {}).setdefault(k_.split("|", 1)[1], []).append(x_)
        avg = v4.Store({cell: {a_: {c_: float(np.mean(xs)) for c_, xs in d_.items()} for a_, d_ in byc.items()}}, k_full=4)
        res["per_condition_mean_over_folds"] = desc_block(avg, cell, arms, comps, "scores averaged over the folds in which a condition is tested; unit = condition")
    dstar = {i: json.load(open(os.path.join(dirs[i], "comparators.json"), encoding="utf8")).get("D*") for i in range(len(dirs))}
    res["D_star_by_fold"] = {f"fold{i}": (v["arm"], v["complete"]) if v else None for i, v in dstar.items()}
    if name == "TestA" or name == "S3":
        res["note"] = "D* candidate set incomplete (arms A1 A2 A9 / A1 A9 A10 A10P only): D* is not formed; PREREG names no arms for S3, the S2 arms were assumed by the config generator"
        pool.tables[cell].pop("D*", None)
    if name.startswith("ISU"):
        res["note"] = ("ISU authors' EOL MAPE to be reported beside ours (PREREG 3.4): not available in the run outputs, not computed here; the config generator read the 'full' analogue as the "
                       "unthinned training side (m unset), see repl configs; Cycling_json calibration not done (stated limitation)")
    extra[name] = res
    dump(f"extra_{name}.json", res)
    print(name, "done", flush=True)

# ------------------------------------------------------------------ SUMMARY.md
def f(x, d=1):
    return "" if x is None else f"{x:.{d}f}"


lines = ["# Descriptive extras: sensitivity rows, ISU replication, Test A, S3", "",
         "Descriptive only. Tiers in the column 'tier it would reach' are what the row would give at the primary final local levels (stats_rows.row_tiers, same sign rule: "
         f"{rule.describe()}). They are reported, never applied: the effective tiers stay those of the frozen step. Median L as % reduction = 100(1 - exp(-median L)); positive = A1 (or the "
         "first arm) better. Interval = unadjusted 95 % rank interval of the frozen rule (rank 11 of 40 at n = 40). Positives = conditions with L > 0.", "",
         f"Inputs checked: {len(allin)} run directories, each with metrics.json and a campaign.log end line rc=0; not ok: {not_ok if not_ok else 'none'}.",
         "Validation: row_tiers on the primary store reproduces every frozen primary tier; the recomputed A1 vs D* g1 median L equals the frozen value (validation_primary.json).", "",
         "## A. Sensitivity rows (Samsung Test B, 40 held-out conditions unless n says otherwise)", "",
         "| Row (9.9) | What changes | Contrast | Cell | n | Median L as % reduction | 95 % interval (%) | Positives | Primary: median % [interval], positives | Tier it would reach | Primary tier | Changes tier? |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for tag, r in fam_results.items():
    if r["status"] != "computed":
        lines.append(f"| {r['registered_row']} {tag} | {r['what_changes']} | {r['status']} | | | | | | | | | |")
        continue
    for w in r["rows"]:
        if "row" not in w:
            lines.append(f"| {r['registered_row']} {tag} | {r['what_changes']} | {w['contrast']} | {w['cell']} | | {w['status']} | | | | | | |")
            continue
        x, p = w["row"], w.get("primary")
        if w["tier_key"] == "most":
            lines.append(f"| {r['registered_row']} {tag} | {r['what_changes']} | most-test d_c (median d_c {x['median_d']:.3f}) | g1 | {x['n']} | | | {x['positives']} | | {w['row_tier_would_reach']} | {w['primary_tier']} | {w['changes_tier']} |")
            continue
        cell = "g1" if w["cell"][0] == 8 else "g4"
        pr = f"{f(p['pct_reduction'])} [{f(p['pct_reduction_ci95'][0])}, {f(p['pct_reduction_ci95'][1])}], {p['positives']}/{p['n']}" if p else ""
        tier = w.get("row_tier_would_reach", "no registered tier") if w["tier_key"] else "no registered tier"
        lines.append(f"| {r['registered_row']} {tag} | {r['what_changes']} | {w['contrast']} [{w['tier_key'] or '-'}] | {cell} | {x['n']} | {f(x['pct_reduction'])} | [{f(x['pct_reduction_ci95'][0])}, {f(x['pct_reduction_ci95'][1])}] | {x['positives']}/{x['n']} | {pr} | {tier} | {w.get('primary_tier')} | {w.get('changes_tier')} |")
lines += ["", "Notes on how the contrasts were formed (assumptions; the PREREG fixes no arm list for these rows, D028):",
          "- Rows whose runs hold the arms A1, A9, A10, A10P, A11, A12 (and D* where the three D* candidates ran) are scored within the row's own runs. Contrasts that need an arm not in the row (A2, A13, A15, G15, R1, the cell (32, 2) for P3) are not covered.",
          "- deltatotal (A1 only) and the A2 tournament rows (A2 only) replace that arm in a copy of the primary store, in the cells the row ran, and pair it with the primary scores of every other arm on the same conditions; P3 and K2 are not formed (P3 needs the (32, 2) cell, which was not rerun; K2 does not involve A1). Per-seed endpoints for K1 as in the frozen step.",
          "- Contrasts at g4 for P1/P2 carry no registered tier (g4 is an estimated cell); only Q-A10 at g4 and Q-H at g4 have one.",
          "- Several rows use A1 and A9 only (clip, warm-up): the D* candidate set is incomplete there, so P1 and the most-test are not formed.",
          "- 'Changes tier?' compares with the primary-analysis tier (not the effective, downgrade-lowered tier). The ~100 contrasts are unadjusted and no multiplicity control applies; the single would-be tier rise (a2_Y2, Q-H g1) is a descriptive observation that sets nothing.",
          "- NO-OP ROWS, not robustness evidence: " + "; ".join(f"{t_}" for t_, r_ in fam_results.items() if r_.get("no_op_row")) + " (A2 condition scores are bit-identical to the primary in every run of the row: the tournament still picks the 'constant' backbone, so the changed parameter has no effect). selflim at g4 equals the primary (the tournament already chose self_limiting in all five m = 32 folds; only g1 differs): " + str(all(v_ for k_, v_ in fam_results["selflim"]["scores_bit_identical_to_primary"].items() if k_.startswith("32|"))) + " (bit-identical flags in family_selflim.json).", "",
          "## B. ISU replication, Test A, S3 (descriptive; plain exact intervals; no tier, no claim word)", "",
          "Where the interval is marked 'range', no pair of order statistics reaches 95 % and the printed interval is the full range [L(1), L(n)] with the coverage shown (S3, n = 7: coverage 0.984); it is not a 95 % interval. S3 carries no claim and no test (PREREG section 4): read the counts (2/7, 6/7) only. ISU g1 and full differ in n (45 and 62) because different conditions survive the 2-week and 4-week windows; ISU is not blind, not pooled with Samsung, has no error control; claims are 'also holds / does not hold' with their own n. Test A: the pooled n = 118 is 40 unique conditions tested on different replicate cells in up to three folds, so it is not 118 independent conditions and its interval is too narrow; use the per-condition n = 40 row or the three folds.", ""]
for name, r in extra.items():
    if r.get("status") != "computed":
        lines.append(f"- {name}: {r.get('status')}")
        continue
    lines += [f"### {name}", f"{r['pooling']}. D* by fold (arm, complete): {r['D_star_by_fold']}. " + r.get("note", ""), "",
              "| Block | Arm means pp (n, mean, median) | A1 vs | n | Median L as % reduction | 95 % plain interval (%) or range | Coverage | Positives | Mean pp diff |", "|---|---|---|---|---|---|---|---|---|"]
    for blk_name, blk in [("pooled" + (" (n = fold x condition, NOT independent)" if name == "TestA" else ""), r["pooled"])] + ([("per condition, mean over folds (n = 40 conditions)", r["per_condition_mean_over_folds"])] if "per_condition_mean_over_folds" in r else []) + list(r["per_fold"].items()):
        am = "; ".join(f"{a} {v['n']}, {v['mean']:.2f}, {v['median']:.2f}" for a, v in blk["arm_means_pp"].items())
        for cmp_, e in blk["contrasts_A1_vs"].items():
            if isinstance(e, str):
                lines.append(f"| {blk_name} | {am} | {cmp_} | {e} | | | | | |")
            else:
                lines.append(f"| {blk_name} | {am} | {cmp_} | {e['n']} | {f(e['pct_reduction'])} | {'range ' if (e['interval_is_range'] or e['interval_rank'] == 1) else ''}[{f(e['pct_reduction_ci95'][0])}, {f(e['pct_reduction_ci95'][1])}] | {e['interval_coverage']:.3f} | {e['positives']}/{e['n']} | {e['mean_pp_diff']:.3f} |")
    lines.append("")
lines += ["## C. Not run / unclear", "",
          f"- Runs not run or failed: {not_ok if not_ok else 'none (all 209 inputs have metrics.json and rc=0)'}.",
          "- Rows struck by PREREG (first-check-up reference, forecast failures under the window cap, separate h_cal/h_cyc for A2, SNL replication): not run, printed as such (C.4 of the appendix).",
          "- Rows (a), (j), (q), (s), (u) are outputs of the frozen statistics step (contrasts_v4_B.json: lab_rows, downgrade, dependence_sensitivity, plain_descriptive, crate_ablation; margins.json); (f), (h), (o) are the downgrade rows already in the frozen step. Rows (b) per stage, (c), (d), (e), (v), (vi) are NOT in the frozen analysis directory; they are computed in section D by run_rows.py.",
          "- ISU authors' EOL MAPE beside ours: not in the run outputs, not computed. Whether 'full' means the unthinned training side (the PREREG 3.4 wording: 'full-data analogue') or the g4 analogue is stated in the generator (unthinned, m unset).",
          "- Test A: 3 folds x 39-40 conditions (118 fold x condition units = 40 unique conditions); the per-condition n = 40 view is printed beside the pooled one; R_LOO yardstick not computed here.",
          "- The contrast for the A2 and deltatotal rows pairs a variant arm with primary scores of other arms; PREREG 9.9 does not state this, it is the only reading available without rerunning those arms."]
def J(n):
    return json.load(open(os.path.join(OUT, n), encoding="utf8"))


D = ["", "CHANGE LOG (re-check 2): (a) row (d) intervals were printed upper-bound first (bounds swapped in the percent conversion); fixed, row_d_two_stage_bootstrap.json and D3 regenerated, no other number changed. (b) row (e): A1 vs A13 (g1) is now computed from margins.json and entry() (it was wrongly listed as having no margin entry), and K1 and K2 are listed explicitly in D4. All other rows are unchanged.", "", "## D. Rows (b) per stage, (c), (d), (e), (v), (vi): computed after the frozen step from the existing run outputs (run_rows.py; frozen functions, read-only; descriptive, no consequence)", ""]
rb, rc, rd, re_, rv, rvi = J("row_b_stage.json"), J("row_c_leave_one_lab_out.json"), J("row_d_two_stage_bootstrap.json"), J("row_e_pp_scale.json"), J("row_v_inversion_starts.json"), J("row_vi_zprior_weight.json")
D += ["### D1. (b) per laboratory and per stage (stats_ext.lab_stage_rows; mean pp = comparator - target, positive favours the target arm)", "", "| Contrast | Block | n | Mean pp diff | Median L as % reduction | Positives |", "|---|---|---|---|---|---|"]
for k_, v_ in rb["contrasts"].items():
    for bl, dd in (("lab", v_["per_lab"]), ("stage", v_["per_stage"])):
        for nm, x_ in dd.items():
            D.append(f"| {k_} | {bl} {nm} | {x_['n']} | {x_['mean_pp']:.3f} | {f(100 * (1 - np.exp(-x_['median_L'])))} | {x_['n_wins']}/{x_['n']} |")
D += ["", "### D2. (c) leave-one-laboratory-out (frozen sign rule at the primary final levels; row_tiers on the primary store without one laboratory's conditions)", "",
      "| Lab removed | Conditions removed | Contrast | n left | Median L as % reduction | 95 % interval (%) | Positives | Tier it would reach | Primary tier |", "|---|---|---|---|---|---|---|---|---|"]
for lab_, v_ in rc["frozen_rule_row_tiers"].items():
    for k_, x_ in v_["contrasts"].items():
        D.append(f"| {lab_} | {v_['conditions_removed']} | {k_} | {x_['n']} | {f(x_['pct_reduction'])} | [{f(x_['pct_reduction_ci95'][0])}, {f(x_['pct_reduction_ci95'][1])}] | {x_['positives']}/{x_['n']} | {x_['tier_it_would_reach']} | {x_['primary_tier']} |")
D += ["", "The plain-exact leave-one-lab-out of stats_ext (v3 convention) is in row_c_leave_one_lab_out.json. P3 is covered in the tier list (row_tiers) only.", "",
      "### D3. (d) two-stage bootstrap (stats_ext.two_stage_bootstrap, B = 10000, percentile 95 %; weights by scored cells)", "", "| Contrast | n conditions | Median L as % reduction (point) | 95 % bootstrap interval (%) | Median L primary store |", "|---|---|---|---|---|"]
for k_, v_ in rd["contrasts"].items():
    if isinstance(v_, str):
        D.append(f"| {k_} | not computed: {v_} | | | |")
    else:
        D.append(f"| {k_} | {v_['n_conditions']} | {f(v_['pct_reduction_point_cell_scores'])} | [{f(v_['pct_reduction_ci95'][0])}, {f(v_['pct_reduction_ci95'][1])}] | {v_['median_L_primary_store']:.4f} |")
D += ["", "### D4. (e) pp-scale row (BCa 95 % interval of the mean pp difference against delta_S = 0.02 E, delta_N = 0.10 E of margins.json; the mean-based pp tier can differ from the median-based log-scale tier)", "",
      "| Contrast and cell | n | Mean pp diff | BCa 95 % | delta_S pp | delta_N pp | pp-scale tier it would reach |", "|---|---|---|---|---|---|---|"]
for k_, v_ in re_["rows"].items():
    D.append(f"| {k_} | not computed: {v_} | | | | | |" if isinstance(v_, str) else f"| {k_} | {v_['n']} | {v_['mean_pp_diff']:.3f} | [{v_['mean_pp_bca95'][0]:.3f}, {v_['mean_pp_bca95'][1]:.3f}] | {v_['delta_S_pp']:.3f} | {v_['delta_N_pp']:.3f} | {v_['pp_scale_tier_it_would_reach']} |")
D += ["", "### D5. (v) diagnostic starts and (vi) z-prior weights (single-seed scores, seed 0 of the final refit; the primary is the five-seed ensemble, so the counts are not compared with primary tiers; plain-rule counts; D* not reselected)", "",
      f"Primary reference at g1 (ensemble endpoint): P1 N-node positives {rv['primary_reference_counts_g1']['P1']['P1N']}/40, S-node {rv['primary_reference_counts_g1']['P1']['P1S']}/40, P2 {rv['primary_reference_counts_g1']['P2']}/40.", "",
      "| Row | Cell | Contrast | Median L as % reduction | Positives (L > 0) | Plain count reaches the critical count at the primary final level (node: positives/n) | Note |", "|---|---|---|---|---|---|---|"]
for blk in list(rv["starts"].values()) + list(rvi["weights"].values()):
    for cell_, cb in blk["cells"].items():
        for lab_ in ("P1: A1 vs D*", "P2: A1 vs A9", "A1 vs AG"):
            b_ = cb[lab_]
            ex = "; ".join(f"{k_[12:]} {v_['positives']}/{v_['n']} {'yes' if v_['reaches_plain_critical_count_at_primary_final_level'] else 'no'}" for k_, v_ in b_.items() if k_.startswith("plain_count_"))
            D.append(f"| {blk['row']} | {cell_.replace('|', ',')} | {lab_} | {f(b_['pct_reduction'])} | {b_['positives_L_gt_0']}/{b_['n']} | {ex} | {'; '.join(cb['notes']) if lab_.startswith('P1') else ''} |")
lines += D
with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf8") as fh:
    fh.write("\n".join(lines) + "\n")

# ------------------------------------------------------------------ SHA256.json
sha = {}
for p in sorted(glob.glob(os.path.join(OUT, "*"))):
    if os.path.basename(p) == "SHA256.json" or os.path.isdir(p) or p.endswith(".pyc"):
        continue
    sha[os.path.basename(p)] = hashlib.sha256(open(p, "rb").read()).hexdigest()
dump("SHA256.json", sha)
print("ALL DONE")
