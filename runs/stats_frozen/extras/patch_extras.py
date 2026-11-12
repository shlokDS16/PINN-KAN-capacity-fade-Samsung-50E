p = r"C:\Users\Shlok\Downloads\PINN KAN battery paper\runs\stats_frozen\extras\run_extras.py"
s = open(p, encoding="utf8").read()


def rep(old, new, cnt=1):
    global s
    assert s.count(old) == cnt, (old[:60], s.count(old))
    s = s.replace(old, new)


rep('"positives": e["n_wins"], "mean_pp_diff": e["mean_pp"], "interval_rank": e["interval_rank"], "interval_is_range": e["interval_is_range"]}',
    '"positives": e["n_wins"], "mean_pp_diff": e["mean_pp"], "interval_rank": e["interval_rank"], "interval_is_range": e["interval_is_range"], "interval_coverage": e["interval_coverage"]}')
# identical-to-primary check per family
rep('    store = var if spec["mode"] == "within" else merged(P, var, [spec["mode"].split(":")[1]])\n',
    '    ident = {}\n    for key_, t_ in var.tables.items():\n        for a_, sc_ in t_.items():\n            if a_ in ("D*", "AG"):\n                continue\n            ident[f"{key_[0]}|{key_[1]}|{a_}"] = bool(a_ in P.tables.get(key_, {}) and P.tables[key_][a_] == sc_)\n'
    '    res["scores_bit_identical_to_primary"] = ident\n'
    '    res["no_op_row"] = bool(ident) and all(ident[k_] for k_ in ident if k_.endswith("|A2")) if spec["mode"] == "replace:A2" else None\n'
    '    store = var if spec["mode"] == "within" else merged(P, var, [spec["mode"].split(":")[1]])\n')
# Test A per condition
rep('    dstar = {i: json.load(open(os.path.join(dirs[i], "comparators.json")',
    '    if name == "TestA":\n        byc = {}\n        for a_, v_ in pool.tables[cell].items():\n            for k_, x_ in v_.items():\n                byc.setdefault(a_, {}).setdefault(k_.split("|", 1)[1], []).append(x_)\n'
    '        avg = v4.Store({cell: {a_: {c_: float(np.mean(xs)) for c_, xs in d_.items()} for a_, d_ in byc.items()}}, k_full=4)\n'
    '        res["per_condition_mean_over_folds"] = desc_block(avg, cell, arms, comps, "scores averaged over the folds in which a condition is tested; unit = condition")\n'
    '    dstar = {i: json.load(open(os.path.join(dirs[i], "comparators.json")')
# section B table
rep('"| Block | Arm means pp (n, mean, median) | A1 vs | n | Median L as % reduction | 95 % plain interval (%) | Positives | Mean pp diff |", "|---|---|---|---|---|---|---|---|"]',
    '"| Block | Arm means pp (n, mean, median) | A1 vs | n | Median L as % reduction | 95 % plain interval (%) or range | Coverage | Positives | Mean pp diff |", "|---|---|---|---|---|---|---|---|---|"]')
rep('for blk_name, blk in [("pooled", r["pooled"])] + list(r["per_fold"].items()):',
    'for blk_name, blk in [("pooled" + (" (n = fold x condition, NOT independent)" if name == "TestA" else ""), r["pooled"])] + ([("per condition, mean over folds (n = 40 conditions)", r["per_condition_mean_over_folds"])] if "per_condition_mean_over_folds" in r else []) + list(r["per_fold"].items()):')
rep("""lines.append(f"| {blk_name} | {am} | {cmp_} | {e} | | | | |")""", """lines.append(f"| {blk_name} | {am} | {cmp_} | {e} | | | | | |")""")
rep("""[{f(e['pct_reduction_ci95'][0])}, {f(e['pct_reduction_ci95'][1])}] | {e['positives']}/{e['n']} | {e['mean_pp_diff']:.3f} |")""",
    """{'range ' if e['interval_is_range'] else ''}[{f(e['pct_reduction_ci95'][0])}, {f(e['pct_reduction_ci95'][1])}] | {e['interval_coverage']:.3f} | {e['positives']}/{e['n']} | {e['mean_pp_diff']:.3f} |")""")
rep('"## B. ISU replication, Test A, S3 (descriptive; plain exact intervals; no tier, no claim word)", ""]',
    '"## B. ISU replication, Test A, S3 (descriptive; plain exact intervals; no tier, no claim word)", "",\n'
    '          "Where the interval is marked \'range\', no pair of order statistics reaches 95 % and the printed interval is the full range [L(1), L(n)] with the coverage shown (S3, n = 7: coverage 0.984); it is not a 95 % interval. S3 carries no claim and no test (PREREG section 4): read the counts (2/7, 6/7) only. ISU g1 and full differ in n (45 and 62) because different conditions survive the 2-week and 4-week windows; ISU is not blind, not pooled with Samsung, has no error control; claims are \'also holds / does not hold\' with their own n. Test A: the pooled n = 118 is 40 unique conditions tested on different replicate cells in up to three folds, so it is not 118 independent conditions and its interval is too narrow; use the per-condition n = 40 row or the three folds.", ""]')
# notes after section A
rep('"- \'Changes tier?\' compares with the primary-analysis tier (not the effective, downgrade-lowered tier).", "",',
    '"- \'Changes tier?\' compares with the primary-analysis tier (not the effective, downgrade-lowered tier). The ~100 contrasts are unadjusted and no multiplicity control applies; the single would-be tier rise (a2_Y2, Q-H g1) is a descriptive observation that sets nothing.",\n'
    '          "- NO-OP ROWS, not robustness evidence: " + "; ".join(f"{t_}" for t_, r_ in fam_results.items() if r_.get("no_op_row")) + " (A2 condition scores are bit-identical to the primary in every run of the row: the tournament still picks the \'constant\' backbone, so the changed parameter has no effect). selflim at g4 equals the primary (the tournament already chose self_limiting in all five m = 32 folds; only g1 differs): " + str(all(v_ for k_, v_ in fam_results["selflim"]["scores_bit_identical_to_primary"].items() if k_.startswith("32|"))) + " (bit-identical flags in family_selflim.json).", "",')
# section C text
rep('"- Rows (a)-(e), (j), (q), (s), (v), (vi), (u) of 9.9 are outputs of the frozen statistics step (or the C-rate ablation in contrasts_v4_B.json), not recomputed here; (f), (h), (o) are downgrade rows already in the frozen step.",',
    '"- Rows (a), (j), (q), (s), (u) are outputs of the frozen statistics step (contrasts_v4_B.json: lab_rows, downgrade, dependence_sensitivity, plain_descriptive, crate_ablation; margins.json); (f), (h), (o) are the downgrade rows already in the frozen step. Rows (b) per stage, (c), (d), (e), (v), (vi) are NOT in the frozen analysis directory; they are computed in section D by run_rows.py.",')
rep('"- Test A: 3 folds x 39-40 conditions (118 in all; condition keys recur across folds, so the pooled unit is fold x condition), pooled with fold-prefixed keys (unit = fold x condition, not independent of replicate structure); R_LOO yardstick not computed here.",',
    '"- Test A: 3 folds x 39-40 conditions (118 fold x condition units = 40 unique conditions); the per-condition n = 40 view is printed beside the pooled one; R_LOO yardstick not computed here.",')
# section D appended before writing
rep('with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf8") as fh:',
    '''def J(n):
    return json.load(open(os.path.join(OUT, n), encoding="utf8"))


D = ["", "## D. Rows (b) per stage, (c), (d), (e), (v), (vi): computed after the frozen step from the existing run outputs (run_rows.py; frozen functions, read-only; descriptive, no consequence)", ""]
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
            ex = "; ".join(f"{k_[11:]} {v_['positives']}/{v_['n']} {'yes' if v_['reaches_plain_critical_count_at_primary_final_level'] else 'no'}" for k_, v_ in b_.items() if k_.startswith("plain_count_"))
            D.append(f"| {blk['row']} | {cell_} | {lab_} | {f(b_['pct_reduction'])} | {b_['positives_L_gt_0']}/{b_['n']} | {ex} | {'; '.join(cb['notes']) if lab_.startswith('P1') else ''} |")
lines += D
with open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf8") as fh:''')
open(p, "w", encoding="utf8").write(s)
print("patched")
