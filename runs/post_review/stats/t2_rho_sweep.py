"""T2: sweep of the assumed average pairwise sign correlation rho over stored positive counts, with the frozen test function (read-only import).
No refit. POST-HOC, EXPLORATORY; the frozen decisions are not changed. Validation first: at rho = 0.03 every stored p-value, critical count and graph decision must be reproduced."""
import sys
sys.path.insert(0, r"C:\Users\Shlok\Downloads\PINN KAN battery paper\runs\post_review\stats")
import numpy as np
from common import *

gt, gt_sha = load_frozen_graph_test()
c = jload(os.path.join(FROZEN, "contrasts_v4_B.json"))
ct = jload(os.path.join(FROZEN, "controls.json"))
RHO0 = gt.RHO_S0
W = c["config_full"]["graph_w"]
ALPHA = c["config_full"]["alpha"]
n = 40
prim = c["primary"]["nodes"]
sec = c["secondary"]["tests"]
SEC_ORDER = ["QA10_g1", "QA10_g4", "QH_g1", "QH_g4", "QT_g1"]
PNODES = ["P1N", "P1S", "P2", "P3", "K1", "K2N", "K2S"]

# ---- stored positive counts -------------------------------------------------------------------------------------------------------------
pos = {k: prim[k]["positives"] for k in PNODES}
extra = {   # tests outside the two graphs, with their frozen level
    "P1_rev (outside graph, level 0.025)": (prim["P1rev"]["positives"], prim["P1rev"]["level"], "unfavourable direction"),
    "K2_rev (outside graph, level 0.025)": (prim["K2rev"]["positives"], prim["K2rev"]["level"], "unfavourable direction"),
    "R1 at g1: PINN-KAN vs persistence (outside graph, level 0.025)": (prim["R1g1"]["positives"], prim["R1g1"]["level"], "reported, feeds modifier M3"),
    "K1 tier S, unadjusted (level 0.025, descriptive)": (prim["K1_S_unadjusted"]["positives"], prim["K1_S_unadjusted"]["level"], "descriptive"),
    "NC-2 permuted stress (level 0.025, interpretive)": (ct["negative"]["nc2"]["k_positive"], ct["negative"]["nc2"]["alpha"], "reported check"),
    "PC-3 PINN-KAN vs persistence at g4 (level 0.025, reported check)": (ct["positive"]["PC3_detail"]["positives"], ct["positive"]["PC3_detail"]["alpha"], "reported check"),
}
sec_pos = {}      # node positives: a node p-value is the larger p of the forms, i.e. the smaller positive count
sec_rev = {}
for s in SEC_ORDER:
    pf = sec[s]["per_form"]
    sec_pos[s] = {"N": min(pf[f]["N"]["positives"] for f in pf), "S": min(pf[f]["S"]["positives"] for f in pf)}
    sec_rev[s] = {f: sec[s]["reverse_S"][f]["positives"] for f in sec[s]["reverse_S"]}

nodes_p, w_p, G_p = gt.pinnkan_graph(W)
nodes_s, w_s, G_s = gt.secondary_graph(5)


def tail(rho):
    return gt.betabin_tail_table(n, rho)


def run_all(rho):
    """decisions at one rho from the stored counts, with the frozen graph and the frozen beta-binomial tail"""
    t = tail(rho)
    pP = np.array([t[pos[k]] for k in PNODES])
    rp = gt.graph_test(pP, w_p, G_p, ALPHA)
    pN = [t[sec_pos[s]["N"]] for s in SEC_ORDER]
    pS = [t[sec_pos[s]["S"]] for s in SEC_ORDER]
    rs = gt.graph_test(np.array(pN + pS), w_s, G_s, ALPHA)
    out = {"p_nodes": dict(zip(PNODES, pP.tolist())), "graph_rejected": rp.names(nodes_p),
           "graph_final_levels": dict(zip(PNODES, rp.final_level.tolist())),
           "sec_rejected": rs.names(nodes_s), "sec_p": dict(zip([f"N{i+1}" for i in range(5)] + [f"S{i+1}" for i in range(5)], (pN + pS)))}
    tests = {}
    for k, (kk, lvl, why) in extra.items():
        p = float(t[kk])
        tests[k] = {"positives": kk, "level": lvl, "p": p, "rejected": bool(p <= lvl * (1 + gt.TOL)), "role": why}
    # reverse-S safety tests of the secondary slots, at the slot's final level
    names = list(nodes_s)
    rev = {}
    for i, s in enumerate(SEC_ORDER, start=1):
        lv = 0.0
        for nm in (f"N{i}", f"S{i}"):
            k = names.index(nm)
            lv = max(lv, float(rs.level_at_rejection[k]) if rs.rejected[k] else float(rs.final_level[k]))
        for f, pc in sec_rev[s].items():
            p = float(t[pc])
            rev[f"{s}:{f}:revS"] = {"positives": pc, "level": lv, "p": p, "rejected": bool(lv > 0 and p <= lv * (1 + gt.TOL))}
    out["tests"] = tests
    out["secondary_reverse"] = rev
    out["crit_levels"] = {str(l): gt.betabin_crit(n, l, rho) for l in (0.0195, 0.025, 0.0055, 0.005)}
    return out


# ---- validation at rho = 0.03 (stop if anything differs) ---------------------------------------------------------------------------------
val = {"rho": RHO0, "checks": []}
r03 = run_all(RHO0)
ok = True
for k in PNODES:
    d = abs(r03["p_nodes"][k] - prim[k]["p"])
    val["checks"].append({"what": "primary p " + k, "stored": prim[k]["p"], "recomputed": r03["p_nodes"][k], "abs_diff": d})
    ok &= d < 1e-12
for k, (kk, lvl, why) in extra.items():
    pass
stored_extra_p = {"P1_rev (outside graph, level 0.025)": prim["P1rev"]["p"], "K2_rev (outside graph, level 0.025)": prim["K2rev"]["p"],
                  "R1 at g1: PINN-KAN vs persistence (outside graph, level 0.025)": prim["R1g1"]["p"],
                  "K1 tier S, unadjusted (level 0.025, descriptive)": prim["K1_S_unadjusted"]["p"],
                  "NC-2 permuted stress (level 0.025, interpretive)": ct["negative"]["nc2"]["p_one_sided"],
                  "PC-3 PINN-KAN vs persistence at g4 (level 0.025, reported check)": ct["positive"]["PC3_detail"]["p"]}
for k, sp in stored_extra_p.items():
    d = abs(r03["tests"][k]["p"] - sp)
    val["checks"].append({"what": "p " + k, "stored": sp, "recomputed": r03["tests"][k]["p"], "abs_diff": d})
    ok &= d < 1e-12 * max(1.0, 1e6 * sp) if sp > 0 else d < 1e-15
for s in SEC_ORDER:
    for key, st in (("N", sec[s]["pN"]), ("S", sec[s]["pS"])):
        rc = r03["sec_p"][f"{key}{SEC_ORDER.index(s)+1}"]
        d = abs(rc - st)
        val["checks"].append({"what": f"secondary p{key} {s}", "stored": st, "recomputed": rc, "abs_diff": d})
        ok &= d < 1e-12
val["graph_decision_matches_stored"] = bool(r03["graph_rejected"] == [k for k in PNODES if c["primary"]["rejected"][k]])
val["secondary_decision_matches_stored"] = bool(all((f"N{i+1}" in r03["sec_rejected"]) == sec[s]["N_rejected"] and (f"S{i+1}" in r03["sec_rejected"]) == sec[s]["S_rejected"] for i, s in enumerate(SEC_ORDER)))
crit_frozen = {"P1N (level 0.0195)": prim["P1N"]["crit_positives"], "P1_rev (0.025)": prim["P1rev"]["crit_positives"], "K1 (0.0055)": prim["K1"]["crit_positives"], "secondary slot (0.005)": sec["QA10_g1"]["crit_positives_slot"]}
crit_re = {"P1N (level 0.0195)": r03["crit_levels"]["0.0195"], "P1_rev (0.025)": r03["crit_levels"]["0.025"], "K1 (0.0055)": r03["crit_levels"]["0.0055"], "secondary slot (0.005)": r03["crit_levels"]["0.005"]}
val["critical_counts"] = {k: {"stored": crit_frozen[k], "recomputed": crit_re[k]} for k in crit_frozen}
ok &= all(v["stored"] == v["recomputed"] for v in val["critical_counts"].values())
ok &= val["graph_decision_matches_stored"] and val["secondary_decision_matches_stored"]
val["all_reproduced"] = bool(ok)
if not ok:
    jdump({"validation": val}, "t2_rho_sweep.json")
    raise SystemExit("VALIDATION FAILED: frozen decisions not reproduced at rho = 0.03; see t2_rho_sweep.json")

# ---- sweep -------------------------------------------------------------------------------------------------------------------------------
avg_pw = c["item_f"]["avg_pairwise"]
avg_pw_up = c["item_f"]["avg_pairwise_upper"]
rho_fold = c["item_f"]["rho_fold"]
rho_fold_up = c["item_f"]["rho_fold_upper"]
printed = {   # named points, each with its provenance label
    0.0: "independence (binomial)",
    float(avg_pw): "frozen-code conversion of the within-fold estimate (60/780); NOT validated as a like-for-like estimate",
    0.03: "frozen assumption (reproduction check)",
    0.05: "top of the frozen grid",
    float(rho_fold): "within-fold intra-group estimate applied to ALL pairs (over-states; labelled so)",
    0.15: "grid point",
    0.2: "grid point",
    0.3: "grid point",
    float(avg_pw_up): "frozen-code conversion of the within-fold upper limit; rests mainly on a 3-laboratory term",
    float(rho_fold_up): "within-fold upper limit applied to ALL pairs (over-states; labelled so)",
    0.5: "end of swept range",
}
grid = sorted(set([round(x * 0.01, 4) for x in range(0, 31)] + list(printed.keys())))
sweep = {}
for r in grid:
    o = run_all(r)
    o["label"] = printed.get(r, "")
    o["design_effect"] = 1 + (n - 1) * r
    sweep[repr(r)] = o

# fine grid: every rho at which any decision changes (0 to 0.5 in steps of 0.001)
fine = [round(i * 0.001, 3) for i in range(0, 501)]


def decision_vector(o):
    v = {"graph:" + k: (k in o["graph_rejected"]) for k in PNODES}
    v.update({"sec:" + k: (k in o["sec_rejected"]) for k in [f"N{i}" for i in range(1, 6)] + [f"S{i}" for i in range(1, 6)]})
    v.update({"test:" + k: x["rejected"] for k, x in o["tests"].items()})
    v.update({"rev:" + k: x["rejected"] for k, x in o["secondary_reverse"].items()})
    return v


changes = {}
prev = None
for r in fine:
    v = decision_vector(run_all(r))
    if prev is None:
        first = dict(v)
    else:
        for k in v:
            if v[k] != prev[k]:
                changes.setdefault(k, []).append({"rho_step_to": r, "from": prev[k], "to": v[k]})
    prev = v
dec0 = first
out = {
    "note": "POST-HOC, EXPLORATORY. Decisions recomputed from stored positive counts with the frozen beta-binomial tail and frozen graph test (graph_test.py sha256 below, imported read-only). The frozen decisions (rho = 0.03) are unchanged.",
    "frozen_graph_test_sha256": gt_sha, "graph_w": W, "alpha": ALPHA, "n_conditions": n,
    "stored_positive_counts": {"primary_nodes": pos, "secondary_node_positives": sec_pos, "secondary_reverse_positives": sec_rev,
                               "outside_graph": {k: v[0] for k, v in extra.items()}},
    "validation_at_rho_0p03": val,
    "item_f_from_frozen_json": {"rho_fold": rho_fold, "rho_fold_upper": rho_fold_up, "rho_lab": c["item_f"]["rho_lab"], "rho_lab_upper": c["item_f"]["rho_lab_upper"],
                                "avg_pairwise_frozen_code": avg_pw, "avg_pairwise_upper_frozen_code": avg_pw_up,
                                "ratio_avg_pairwise_to_rho_fold": avg_pw / rho_fold, "ratio_if_60_over_780": 60 / 780,
                                "n_observations": c["item_f"]["n_observations"], "groups": c["item_f"]["groups"]},
    "swept_range": [grid[0], grid[-1]],
    "sweep": sweep,
    "fine_grid": {"step": 0.001, "range": [fine[0], fine[-1]], "decisions_at_rho_0": dec0,
                  "decision_changes_along_increasing_rho": changes},
}
jdump(out, "t2_rho_sweep.json")
print("ok; reproduced:", ok, "| graph rejections at 0.03:", r03["graph_rejected"], "| changes:", {k: [x['rho_step_to'] for x in v] for k, v in changes.items()})
