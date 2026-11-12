"""Builds SUMMARY.md and SHA256.json. Every number in SUMMARY.md is formatted from a JSON in this folder (or from the frozen JSON via the JSONs here)."""
import sys
sys.path.insert(0, r"C:\Users\Shlok\Downloads\PINN KAN battery paper\runs\post_review\stats")
from common import *

t2 = jload(os.path.join(OUT, "t2_rho_sweep.json"))
e4 = jload(os.path.join(OUT, "e4_final_target.json"))
e3 = jload(os.path.join(OUT, "e3_descriptive.json"))
c1 = jload(os.path.join(OUT, "c1_flow.json"))
L = []
w = L.append


def f2(x, d=2):
    return ("%." + str(d) + "f") % x


def ci(a, d=2):
    return "[%s, %s]" % (f2(a[0], d), f2(a[1], d))


def yn(b):
    return "yes" if b else "no"


w("# Post-hoc statistics for the teacher's review (no refit), 2026-11-12")
w("")
w("Status: POST-HOC and EXPLORATORY (decision D048). Nothing here changes a frozen decision (P0, K=, M1 to M3, NC-2, T5). Computed from stored files only; `code/`, `runs/prereg/` and `runs/stats_frozen/` were read, never written. "
  "Every number below is formatted by `make_summary.py` from `t2_rho_sweep.json`, `e4_final_target.json`, `e3_descriptive.json` or `c1_flow.json` in this folder. Hashes: `SHA256.json`.")
w("")
w("Validation before use. T2: at rho = %s every stored p-value, critical count and graph decision was reproduced with the frozen test function (graph_test.py sha256 `%s`, imported read-only): all reproduced = %s; primary graph decision matches = %s; secondary graph decision matches = %s. "
  "E4: the condition mean of the recomputed cell RMSE matches the stored `condition_scores` json for every arm and fold, largest absolute difference %.1e pp at g1 and %.1e pp at g4 (validation ok: g1 %s, g4 %s). "
  "E4 reconciliation with the frozen endpoint: median log ratio of A1 against D* over all forecast check-ups is %s at g1 and %s at g4 (%d and %d of 40 positive). "
  "Table D.1 check: pooled A1 RMSE at forecast index 1 recomputes as %s (g1) and %s (g4), n = %d cells; the plan quotes 0.34 and 1.90, so the second decimal of the printed Table D.1 is not reproduced by this recomputation (condition scores are)."
  % (f2(t2["validation_at_rho_0p03"]["rho"], 2), t2["frozen_graph_test_sha256"], yn(t2["validation_at_rho_0p03"]["all_reproduced"]), yn(t2["validation_at_rho_0p03"]["graph_decision_matches_stored"]),
     yn(t2["validation_at_rho_0p03"]["secondary_decision_matches_stored"]),
     max(e4["cells"]["g1"]["validation_max_abs_diff_condition_score_pp"].values()), max(e4["cells"]["g4"]["validation_max_abs_diff_condition_score_pp"].values()),
     yn(e4["cells"]["g1"]["validation_ok"]), yn(e4["cells"]["g4"]["validation_ok"]),
     f2(e4["cells"]["g1"]["reconcile_frozen_endpoint_A1_vs_Dstar"]["median_L"], 4), f2(e4["cells"]["g4"]["reconcile_frozen_endpoint_A1_vs_Dstar"]["median_L"], 4),
     e4["cells"]["g1"]["reconcile_frozen_endpoint_A1_vs_Dstar"]["n_positive"], e4["cells"]["g4"]["reconcile_frozen_endpoint_A1_vs_Dstar"]["n_positive"],
     f2(e4["cells"]["g1"]["table_D1_check_A1_pooled_rmse_by_forecast_index"]["1"]["rmse_pp"], 3), f2(e4["cells"]["g4"]["table_D1_check_A1_pooled_rmse_by_forecast_index"]["1"]["rmse_pp"], 3),
     e4["cells"]["g1"]["table_D1_check_A1_pooled_rmse_by_forecast_index"]["1"]["n"]))
w("")

# ------------------------------------------------------------------------------------------------------------------------------- E4
w("## 1. E4 / Q4: error at the final forecast check-up of each held-out cell (exploratory)")
w("")
w("Construction. Ensemble forecasts (five-seed mean for A1 and A9). Final target = the last forecast check-up of each held-out cell; condition value = mean over the condition's cells of the absolute error in percentage points; unit = the held-out condition (n = 40). "
  "Paired difference d = A1 error minus comparator error: NEGATIVE means A1 has the lower error. Median interval = frozen exact order-statistic interval (independent conditions, unadjusted for dependence); mean interval = BCa, %d condition-bootstrap resamples (seed rule `SeedSequence([20261105, crc32(label)])`). "
  "D* is the inner-CV-selected data-driven learner per fold: g1 %s; g4 %s (fold 0 to 4). Comparators printed with equal prominence: D*, A9, A10 and its second form A10P, R1. No tier words, no p-values." % (
      e4["bootstrap_B"], ", ".join("%s" % v for k, v in sorted(e4["cells"]["g1"]["D_star_arm_by_fold"].items())), ", ".join("%s" % v for k, v in sorted(e4["cells"]["g4"]["D_star_arm_by_fold"].items()))))
w("")
for g, nm in (("g1", "g1 = (m 8, k 2)"), ("g4", "g4 = (m 32, k full)")):
    r = e4["cells"][g]
    w("### %s" % nm)
    w("")
    w("Final-check-up horizon per condition (days after the window end): median %s, range %s to %s. Window end = last k = 0 forecast row before the cell's first forecast row (%s)." % (
        f2(r["condition_final_horizon_days"]["median"], 1), f2(r["condition_final_horizon_days"]["min"], 1), f2(r["condition_final_horizon_days"]["max"], 1), ", ".join("%s: %d cells" % kv for kv in r["window_end_source_counts"].items())))
    w("")
    w("Final-check-up error by arm (condition median and mean over 40 conditions, pp), all arms:")
    w("")
    w("| arm | median | mean |")
    w("|---|---|---|")
    for a, v in r["by_arm_final_error_pp"].items():
        w("| %s | %s | %s |" % (a, f2(v["median"]), f2(v["mean"])))
    w("")
    w("Paired difference d = A1 minus comparator (pp; negative = A1 lower):")
    w("")
    w("| comparator | median d [order-statistic 95 %] | median d, BCa 95 % | mean d [BCa 95 %] | conditions with A1 lower / higher |")
    w("|---|---|---|---|---|")
    for cmp_, v in r["comparators"].items():
        u = v["unaltered_final_target"]
        w("| %s | %s %s | %s | %s %s | %d / %d (of %d) |" % (cmp_, f2(u["median"]), ci(u["median_order_stat_ci95"]), ci(u["median_bca_ci95"]), f2(u["mean"]), ci(u["mean_bca_ci95"]), u["n_A1_lower"], u["n_A1_higher"], u["n"]))
    w("")
    gp = r["first_check_up_gap_ge_380_days"]
    if gp:
        w("388-day sensitivity (shown BESIDE the unaltered rows above, never in place of them). The cell with a first forecast check-up %s days after the window end is `%s` (condition `%s`, fold %d; its only forecast point is also its final one). Row 1 drops that whole condition (n = 39); row 2 drops only that cell from its condition mean (n = 40):" % (
            f2(gp[0]["h_first_days"], 0), gp[0]["cell"], gp[0]["cond"], gp[0]["fold"]))
        w("")
        w("| comparator | unaltered: median d, mean d [BCa] (n = 40) | drop condition: median d, mean d [BCa] (n = 39) | drop cell: median d, mean d [BCa] (n = 40) |")
        w("|---|---|---|---|")
        for cmp_, v in r["comparators"].items():
            u, a1, a2 = v["unaltered_final_target"], v["sensitivity_drop_condition_388d"], v["sensitivity_drop_cell_388d"]
            w("| %s | %s, %s %s | %s, %s %s | %s, %s %s |" % (cmp_, f2(u["median"]), f2(u["mean"]), ci(u["mean_bca_ci95"]), f2(a1["median"]), f2(a1["mean"]), ci(a1["mean_bca_ci95"]), f2(a2["median"]), f2(a2["mean"]), ci(a2["mean_bca_ci95"])))
        w("")
    else:
        w("388-day sensitivity: not applicable at %s (no cell has a first forecast check-up 380 days or more after the window end)." % g)
        w("")
    w("Stability row: condition RMSE over the last three forecast check-ups, log ratio L = ln(S_comparator / S_A1) (positive = A1 lower error), median with the frozen order-statistic interval:")
    w("")
    w("| comparator | median L [order-statistic 95 %] | conditions with L > 0 |")
    w("|---|---|---|")
    for cmp_, v in r["comparators"].items():
        s = v["last3_rmse_log_ratio"]
        w("| %s | %s %s | %d of %d |" % (cmp_, f2(s["median_L"], 3), ci(s["median_order_stat_ci95"], 3), s["n_positive"], s["n"]))
    w("")
    w("Horizon tertiles (cut points at %s and %s days, tertile sizes %s; description only). Median d per tertile [order-statistic 95 %%] and conditions with A1 lower; Spearman correlation of d with the final horizon in days, with a condition-bootstrap percentile interval:" % (
        f2(r["tertile_cut_points_days"][0], 1), f2(r["tertile_cut_points_days"][1], 1), "/".join(str(x) for x in r["tertile_sizes"])))
    w("")
    w("| comparator | tertile 1 | tertile 2 | tertile 3 | Spearman rho [95 %] |")
    w("|---|---|---|---|---|")
    for cmp_, v in r["comparators"].items():
        cells = []
        for t in v["horizon_tertiles"]:
            cells.append("%s %s, %d of %d" % (f2(t["median"]), ci(t["median_order_stat_ci95"]), t["n_A1_lower"], t["n"]))
        while len(cells) < 3:
            cells.append("n/a")
        sp = v["spearman_d_vs_final_horizon_days"]
        w("| %s | %s | %s | %s | %s %s |" % (cmp_, cells[0], cells[1], cells[2], f2(sp["rho"]), ci(sp["ci95_percentile_condition_bootstrap"])))
    w("")
w("Reading rule (fixed in the plan, applied without interpretation): a late-horizon statement is made only if the tertile medians and the Spearman interval point the same way at both cells; the tables above are the evidence, no direction is asserted here.")
w("")

# ------------------------------------------------------------------------------------------------------------------------------- E3
w("## 2. E3 (descriptive): five-seed spread, optimisation spread only")
w("")
w("All quantities describe the spread of five training seeds. This is OPTIMISATION spread, not predictive uncertainty: no calibration, no coverage guarantee for new conditions, no conformal method. "
  "Intervals: condition cluster bootstrap (%d resamples; %d for the point-level Spearman). The ensemble mean equals the stored `ens` rows (largest absolute difference %.1e in retention)." % (
      e3["bootstrap_B"], e3["bootstrap_B_point_level_spearman"], max(e3["cells"][g][a]["ens_equals_seed_mean_max_abs_diff_retention"] for g in e3["cells"] for a in e3["cells"][g])))
w("")
w("Coverage: share of forecast points whose observed retention lies inside the band (pooled over folds; condition-cluster 95 % interval):")
w("")
w("| cell | arm | n points | min-max envelope | mean +/- 1 SD | mean +/- 2 SD | mean +/- 3 SD |")
w("|---|---|---|---|---|---|---|")
for g in e3["cells"]:
    for a, r in e3["cells"][g].items():
        cv = r["coverage_of_observed_retention"]
        w("| %s | %s | %d | %s | %s | %s | %s |" % (g, a, r["n_points"], *["%s %s" % (f2(cv[k]["share"], 3), ci(cv[k]["ci95"], 3)) for k in ("seed_min_max_envelope", "mean_pm_1_seed_sd", "mean_pm_2_seed_sd", "mean_pm_3_seed_sd")]))
w("")
w("Envelope coverage by forecast-index tertile (cut points on the pooled forecast index):")
w("")
w("| cell | arm | tertile 1 | tertile 2 | tertile 3 |")
w("|---|---|---|---|---|")
for g in e3["cells"]:
    for a, r in e3["cells"][g].items():
        tt = r["coverage_of_observed_retention"]["seed_min_max_envelope"]["by_horizon_index_tertile"]
        w("| %s | %s | %s |" % (g, a, " | ".join("%s %s (n %d)" % (f2(t["share"], 3), ci(t["ci95"], 3), t["n"]) for t in tt)))
w("")
w("Size of the spread against the observed error (pooled over points):")
w("")
w("| cell | arm | mean seed SD (pp) | mean abs error of ensemble (pp) | mean SD / mean abs error | mean envelope full width (pp) |")
w("|---|---|---|---|---|---|")
for g in e3["cells"]:
    for a, r in e3["cells"][g].items():
        w("| %s | %s | %s %s | %s %s | %s %s | %s |" % (g, a, f2(r["mean_seed_sd_pp"]["value"], 3), ci(r["mean_seed_sd_pp"]["ci95"], 3), f2(r["mean_abs_error_of_ensemble_pp"]["value"], 3), ci(r["mean_abs_error_of_ensemble_pp"]["ci95"], 3),
                                          f2(r["mean_seed_sd_over_mean_abs_error"]["value"], 3), ci(r["mean_seed_sd_over_mean_abs_error"]["ci95"], 3), f2(r["training_side_band"]["mean_full_width_pp"], 3)))
w("")
w("Rank histogram (number of the five seed forecasts below the observation, bins 0 to 5; shares; a uniform histogram would be %s per bin; not tested):" % f2(e3["cells"]["g1"]["A1"]["rank_histogram"]["uniform_reference_share"], 3))
w("")
w("| cell | arm | 0 | 1 | 2 | 3 | 4 | 5 |")
w("|---|---|---|---|---|---|---|---|")
for g in e3["cells"]:
    for a, r in e3["cells"][g].items():
        w("| %s | %s | %s |" % (g, a, " | ".join("%s %s" % (f2(b["share"], 3), ci(b["ci95"], 3)) for b in r["rank_histogram"]["bins"])))
w("")
w("Spread-skill (Spearman correlation of seed SD with absolute error; ranks the errors, no coverage claim):")
w("")
w("| cell | arm | point level rho [95 %] | condition level rho [95 %] (n = 40) |")
w("|---|---|---|---|")
for g in e3["cells"]:
    for a, r in e3["cells"][g].items():
        s = r["spread_skill"]
        w("| %s | %s | %s %s | %s %s |" % (g, a, f2(s["spearman_point_level"]["rho"], 3), ci(s["spearman_point_level"]["ci95"], 3), f2(s["spearman_condition_level"]["rho"], 3), ci(s["spearman_condition_level"]["ci95"], 3)))
w("")
w("Mean absolute error of the ensemble (pp) within quintiles of seed SD (quintile 1 = smallest spread):")
w("")
w("| cell | arm | Q1 | Q2 | Q3 | Q4 | Q5 |")
w("|---|---|---|---|---|---|---|")
for g in e3["cells"]:
    for a, r in e3["cells"][g].items():
        w("| %s | %s | %s |" % (g, a, " | ".join(f2(q["mean_abs_error_pp"], 3) for q in r["spread_skill"]["mean_abs_error_by_seed_sd_quintile"])))
w("")
w("One training-side band (the five-seed min-max envelope, label: optimisation spread, not predictive uncertainty): mean full width and share of observations inside.")
w("")
w("| cell | arm | mean full width (pp) | median full width (pp) | share inside [95 %] |")
w("|---|---|---|---|---|")
for g in e3["cells"]:
    for a, r in e3["cells"][g].items():
        b = r["training_side_band"]
        w("| %s | %s | %s | %s | %s %s |" % (g, a, f2(b["mean_full_width_pp"], 3), f2(b["median_full_width_pp"], 3), f2(b["share_of_points_with_observation_inside"], 3), ci(b["share_ci95"], 3)))
w("")
w("Observed absolute-error quantiles of the ensemble forecast (pp; %s):" % e3["cells"]["g1"]["A1"]["observed_abs_error_quantiles_pp"]["label"])
w("")
w("| cell | arm | point 50 % | 80 % | 90 % | 95 % | condition RMSE 50 % | 80 % | 90 % | 95 % |")
w("|---|---|---|---|---|---|---|---|---|---|")
for g in e3["cells"]:
    for a, r in e3["cells"][g].items():
        o = r["observed_abs_error_quantiles_pp"]
        w("| %s | %s | %s | %s |" % (g, a, " | ".join(f2(o["overall"][q], 3) for q in ("0.5", "0.8", "0.9", "0.95")), " | ".join(f2(o["condition_rmse"][q], 3) for q in ("0.5", "0.8", "0.9", "0.95"))))
w("")

# ------------------------------------------------------------------------------------------------------------------------------- T2
w("## 3. T2: sweep of the assumed correlation rho, recomputed from the stored counts (exploratory)")
w("")
sw = t2["sweep"]
keys = sorted(sw, key=float)
w("Range swept: %s to %s (fine grid step %s for every decision change). Decisions are recomputed with the frozen beta-binomial tail and the frozen graph procedure (primary graph weight on P1N %s, family-wise level %s; secondary graph, five qualifiers). "
  "Frozen decisions are those at rho = %s and stay as they are." % (f2(t2["swept_range"][0], 2), f2(t2["swept_range"][1], 2), t2["fine_grid"]["step"], f2(t2["graph_w"], 2), f2(t2["alpha"], 3), f2(t2["validation_at_rho_0p03"]["rho"], 2)))
w("")
w("Stored positive counts out of %d: primary nodes %s; outside the graphs %s." % (t2["n_conditions"], ", ".join("%s %d" % kv for kv in t2["stored_positive_counts"]["primary_nodes"].items()),
                                                                                  ", ".join("%s %d" % (k.split(" (")[0], v) for k, v in t2["stored_positive_counts"]["outside_graph"].items())))
w("")
w("Table A. Every gated test at each printed rho (rejections in the graph; `none` = no node rejected). Critical counts are the smallest positive counts out of 40 rejecting at the stated level.")
w("")
w("| rho | label | design effect | critical count at 0.0195 / 0.0055 / 0.005 | primary graph rejections | secondary graph rejections |")
w("|---|---|---|---|---|---|")
for k in keys:
    s = sw[k]
    cl = s["crit_levels"]
    w("| %s | %s | %s | %d / %d / %d | %s | %s |" % (f2(float(k), 4), s["label"], f2(s["design_effect"], 2), cl["0.0195"], cl["0.0055"], cl["0.005"], ", ".join(s["graph_rejected"]) or "none", ", ".join(s["sec_rejected"]) or "none"))
w("")
w("Table B. Tests outside the graphs and the reverse-direction checks at each printed rho: positives out of 40, p-value, decision at the stated level (R = rejected).")
w("")
tnames = list(sw[keys[0]]["tests"].keys())
w("| rho | " + " | ".join(tnames) + " |")
w("|---|" + "---|" * len(tnames))
for k in keys:
    s = sw[k]
    w("| %s | " % f2(float(k), 4) + " | ".join("%d: p = %s, %s" % (s["tests"][t]["positives"], ("%.3g" % s["tests"][t]["p"]), "R" if s["tests"][t]["rejected"] else "-") for t in tnames) + " |")
w("")
w("Table C. p-values of the seven primary graph nodes (stored positives) at each printed rho; node levels start at %s for P1N and %s for K1, all others 0 until a rejection." % (
    f2(t2["sweep"]["0.03"]["graph_final_levels"]["P1N"], 4), f2(t2["sweep"]["0.03"]["graph_final_levels"]["K1"], 4)))
w("")
pn = list(sw[keys[0]]["p_nodes"].keys())
w("| rho | " + " | ".join("%s (%d)" % (n_, t2["stored_positive_counts"]["primary_nodes"][n_]) for n_ in pn) + " |")
w("|---|" + "---|" * len(pn))
for k in keys:
    w("| %s | " % f2(float(k), 4) + " | ".join("%.4g" % sw[k]["p_nodes"][n_] for n_ in pn) + " |")
w("")
w("Decision changes found on the fine grid (rho from 0 in steps of %s). Each line gives the first grid value at which the decision differs from the value one step before; decisions at rho = 0 listed after." % t2["fine_grid"]["step"])
w("")
ch = t2["fine_grid"]["decision_changes_along_increasing_rho"]
w("| decision | state at rho = 0 | first grid rho of the change | change |")
w("|---|---|---|---|")
for k, v in ch.items():
    for x in v:
        w("| %s | %s | %s | %s to %s |" % (k, "rejected" if t2["fine_grid"]["decisions_at_rho_0"][k] else "not rejected", f2(x["rho_step_to"], 3), "rejected" if x["from"] else "not rejected", "rejected" if x["to"] else "not rejected"))
unch = [k for k in t2["fine_grid"]["decisions_at_rho_0"] if k not in ch]
w("")
w("Decisions with no change anywhere on the grid %s to %s: %s. Of these, rejected at rho = 0: %s." % (f2(t2["fine_grid"]["range"][0], 3), f2(t2["fine_grid"]["range"][1], 3), str(len(unch)) + " decisions",
                                                                                                 ", ".join(k for k in unch if t2["fine_grid"]["decisions_at_rho_0"][k]) or "none"))
w("")
assert not any(v for k, v in t2["fine_grid"]["decisions_at_rho_0"].items() if k.startswith("graph:")) and not any(k.startswith("graph:") for k in ch)
w("Within the primary graph no node is rejected at any rho on the grid (including rho = 0). At rho below the frozen value the secondary graph and the NC-2 check change as listed; they do not enter any tier, state or title.")
w("")
_fz = jload(os.path.join(FROZEN, "contrasts_v4_B.json"))["dependence_sensitivity"]["tiers_by_rho"]
w("Note on scope: the frozen dependence table (`dependence_sensitivity.tiers_by_rho`, grid %s) lists %s only; it does not contain the qualifier nodes or NC-2, whose decisions at rho below 0.03 are listed above." % (
    ", ".join(sorted(_fz.keys(), key=float)), ", ".join(next(iter(_fz.values())).keys())))
w("")
w("### What the two numbers measure")
w("")
fi = t2["item_f_from_frozen_json"]
w("The test assumes an average pairwise correlation of the sign indicators over all C(40, 2) = 780 pairs of conditions (exchangeable beta-binomial; design effect 1 + 39 x rho). "
  "The estimate %s is an intra-group correlation: the correlation between two conditions that share an inner fold (within an outer fold), from a one-way ANOVA of %d sign indicators on the training side (one-sided 95 %% limit %s). It describes same-group pairs only and says nothing directly about pairs that share no group. "
  "The two are therefore not on the same scale, and the sentence that the estimate 'exceeds' the assumption compares a within-group figure with an all-pairs average." % (f2(fi["rho_fold"], 4), fi["n_observations"], f2(fi["rho_fold_upper"], 4)))
w("")
w("The frozen code converts the intra-group estimates to an all-pairs average as (same-fold pairs x rho_fold + same-laboratory pairs x rho_lab) / 780, with negative terms set to zero. The stored result %s equals %s x %s; that ratio (%s) equals 60/780 (%s), i.e. the laboratory term contributed zero because its estimate is negative (%s, upper limit %s). "
  "This conversion is NOT validated here and is not offered as a like-for-like value: it assumes pairs in different groups are uncorrelated, adds fold and laboratory pair terms although the pairings overlap, sets a negative laboratory estimate to zero instead of carrying it, and uses inner-CV training-side signs rather than the held-out signs. "
  "The upper limit %s rests mainly on the laboratory term (few laboratories, so a wide limit). The sweep therefore prints %s only as `frozen-code conversion` and makes no claim that it, or any single value, is the correct counterpart of 0.03; the data neither establish nor exclude 0.03." % (
      f2(fi["avg_pairwise_frozen_code"], 5), f2(fi["rho_fold"], 4), f2(fi["ratio_avg_pairwise_to_rho_fold"], 5), f2(fi["ratio_avg_pairwise_to_rho_fold"], 6), f2(fi["ratio_if_60_over_780"], 6), f2(fi["rho_lab"], 4), f2(fi["rho_lab_upper"], 4), f2(fi["avg_pairwise_upper_frozen_code"], 4), f2(fi["avg_pairwise_frozen_code"], 5)))
w("")

# ------------------------------------------------------------------------------------------------------------------------------- C1
w("## 4. C1: flow-diagram content and practitioner paragraph")
w("")
w("Node list (kind: design / gating / reported / result / terminal; use one colour for gating, one for reported-only):")
w("")
w("| id | label | kind | content lines |")
w("|---|---|---|---|")
for n_ in c1["nodes"]:
    w("| %s | %s | %s | %s |" % (n_["id"], n_["label"], n_["kind"], " ; ".join(n_["lines"])))
w("")
w("Edge list:")
w("")
w("| from | to | label | style |")
w("|---|---|---|---|")
for e in c1["edges"]:
    w("| %s | %s | %s | %s |" % (e["src"], e["dst"], e["label"], e["style"]))
w("")
w("Practitioner paragraph (%d words):" % c1["practitioner_paragraph_word_count"])
w("")
w("> " + c1["practitioner_paragraph"])
w("")
open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf8").write("\n".join(L) + "\n")

sh = {}
for fn in sorted(os.listdir(OUT)):
    p = os.path.join(OUT, fn)
    if os.path.isfile(p) and fn != "SHA256.json":
        sh[fn] = sha256_file(p)
jdump(sh, "SHA256.json")
print("summary lines", len(L), "files hashed", len(sh))
