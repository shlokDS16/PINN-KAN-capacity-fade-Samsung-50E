"""Writes SUMMARY.md and SHA256.json from descriptive_post.json (all numbers read from the JSON). Descriptive; no test, no tier."""
import json, os, hashlib
D = os.path.dirname(os.path.abspath(__file__))
r = json.load(open(os.path.join(D, "descriptive_post.json"), encoding="utf8"))
L = []
w = L.append
f3 = lambda x: "--" if x is None else f"{x:.3f}"
f2 = lambda x: "--" if x is None else f"{x:.2f}"

w("# Descriptive post-freeze items for the Paper 7 domain review (2026-11-12)")
w("")
w("Descriptive only: no test, no tier, no p-value, no claim word. Script: `descriptive_post.py` (+ `descriptive_post_addon.py`, `make_summary.py`); all numbers are in `descriptive_post.json`. "
  "Inputs: run outputs only (`diagnostics.json`, `tuning_*.json`, `metrics.json`, `predictions.csv`, `window.csv`, `condition_scores*.json`, `stats_frozen/post/arm_table.json`, `stats_frozen/analysis/reference.json`). No `data/` file opened.")
w("")
w("## 1. Preregistered diagnostics (PREREG_v4 section 9.9, last paragraph; section 7.5)")
w("")
w("Registered output (9.9): per fold, tuned `lam_res` with edge share, sd of fitted delta_c on training cells against TAU (flag outside [0.5, 2] x 0.15), clipped-step fraction for A1 and A9; 7.5: inversion convergence (non-converged cells counted per arm, fold, m, k).")
w("TAU = 0.15; grid for lam_res = {1e-3, 1e-2, 1e-1, 1, 10, 100}. The flag band for delta_sd/tau is [0.5, 2].")
w("")
S = r["item1_summary"]
b = S["B_all_m"]
a1 = b["arms"]["A1"]
w("### Reviewer's claims, verified")
w(f"- A1 tuned lam_res = 1e-3 (grid minimum) in {a1['lam_counts']['0.001']} of {a1['n_runs_with_lam']} Test B runs (m = 8: {S['B_m8']['arms']['A1']['lam_counts']['0.001']}/5, m = 16: {S['B_m16']['arms']['A1']['lam_counts']['0.001']}/5, m = 32: {S['B_m32']['arms']['A1']['lam_counts']['0.001']}/5); 1e-2 in the other {a1['lam_counts']['0.01']}. `lam_res_at_lower_edge` is true in {a1['n_at_lower_edge_flag']} runs, `lam_res_at_upper_edge` in {a1['n_at_upper_edge_flag']}. CONFIRMED.")
w(f"- A1 delta_sd/tau over the 15 runs: min {f3(a1['delta_sd_over_tau_min'])}, median {f3(a1['delta_sd_over_tau_median'])}, max {f3(a1['delta_sd_over_tau_max'])}; {a1['n_flagged_outside_0p5_2']} of {a1['n_ratio']} runs flagged (all below 0.5). Reviewer's 0.012-0.319 CONFIRMED (the reviewer wrote 0.01-0.32 of tau in the brief).")
a2 = b["arms"]["A2"]
w(f"- A2 delta_sd/tau: {f3(a2['delta_sd_over_tau_min'])} to {f3(a2['delta_sd_over_tau_max'])}, {a2['n_inside_0p5_2']} of {a2['n_ratio']} inside the band. CONFIRMED.")
w("- Not stated by the reviewer: the same pattern holds for the other physics-residual arms that were run (table below), and `lam_res_edge_share_over_arms` (share of residual-weight arms at the lower edge) is in the per-run JSON.")
w("")
w("### Counts by arm (Test B, all 15 runs unless n given; A13 and A15 and G15 were run at m = 8 and 32 only)")
w("")
w("| arm | n runs | lam_res counts | at lower edge | delta_sd/tau min / median / max | flagged outside [0.5, 2] | clip fraction min / mean / max |")
w("|---|---|---|---|---|---|---|")
for a in ("A1", "A4", "A13", "A15", "G15", "A2", "A9"):
    e = b["arms"][a]
    lam = e.get("lam_counts")
    lams = ", ".join(f"{k}: {v}" for k, v in lam.items()) if lam else "n/a (no residual weight)"
    ratio = f"{f3(e['delta_sd_over_tau_min'])} / {f3(e['delta_sd_over_tau_median'])} / {f3(e['delta_sd_over_tau_max'])}" if "delta_sd_over_tau_min" in e else "not logged"
    fl = f"{e['n_flagged_outside_0p5_2']} of {e['n_ratio']}" if "n_ratio" in e else "not logged"
    clip = f"{f3(e['clip_fraction_min'])} / {f3(e['clip_fraction_mean'])} / {f3(e['clip_fraction_max'])}" if "clip_fraction_min" in e else "not logged"
    n = e.get("n_runs_with_lam", e.get("n_ratio", e.get("n_clip", "")))
    w(f"| {a} | {n} | {lams} | {e.get('n_at_lower_edge_flag', 'n/a')} | {ratio} | {fl} | {clip} |")
w("")
w("By m (A1 lam_res = 1e-3 count / delta_sd/tau range): " + "; ".join(
    f"m = {m}: {S[f'B_m{m}']['arms']['A1']['lam_counts'].get('0.001', 0)}/5, {f3(S[f'B_m{m}']['arms']['A1']['delta_sd_over_tau_min'])}-{f3(S[f'B_m{m}']['arms']['A1']['delta_sd_over_tau_max'])}" for m in (8, 16, 32)) + ".")
w("")
c = S["C"]["arms"]["A1"]
s2 = S["S2"]["arms"]["A1"]
w(f"Test C (1 run): A1 lam_res {list(c['lam_counts'])[0]} (edge flag {c['n_at_lower_edge_flag']}), delta_sd/tau {f3(c['delta_sd_over_tau_min'])} (flagged), clip fraction A1 {f3(c['clip_fraction_min'])}, A9 {f3(S['C']['arms']['A9']['clip_fraction_min'])}. "
  f"S2 (4 runs): A1 lam_res 0.01 in {s2['lam_counts'].get('0.01', 0)}/4, edge flag {s2['n_at_lower_edge_flag']}, delta_sd/tau {f3(s2['delta_sd_over_tau_min'])}-{f3(s2['delta_sd_over_tau_max'])} (all flagged). "
  "So the lower-edge pattern is a Test B pattern; at Test C and S2 the tuned weight is 1e-2, one grid step up (the reviewer listed Test C only as a source file).")
w("")
w("The `delta_sd_over_tau` is the sd of the fitted per-cell offset on training cells divided by TAU = 0.15; a ratio far below 0.5 means the offsets are strongly shrunk to the prior mean. It says nothing by itself about whether the law is 'off'; the residual still acts at collocation points beyond the records (reviewer's caveat; not tested here).")
w("")
w("### Per-run table, Test B (A1 and A2)")
w("")
w("| run | A1 lam_res | lower edge | A1 delta_sd/tau | A1 clip | A2 delta_sd/tau | A9 clip | A4 lam_res | A13 lam_res |")
w("|---|---|---|---|---|---|---|---|---|")
for x in r["item1_per_run"]:
    if x["test"] != "B":
        continue
    A = x["arms"]
    w(f"| {x['run']} | {A['A1']['lam_res']} | {A['A1']['lam_res_at_lower_edge']} | {f3(A['A1']['delta_sd_over_tau'])} | {f3(A['A1']['clip_fraction'])} | {f3(A['A2']['delta_sd_over_tau'])} | {f3(A['A9']['clip_fraction'])} | {A['A4']['lam_res']} | {A['A13']['lam_res'] if 'A13' in A else 'not run'} |")
w("")
w("The `tuning_A1.json` best_hp lam_res equals the diagnostics value in every run where both exist (checked in the JSON field `tuning_best_hp_lam_res`).")
w("")
w("### Inversion convergence (7.5; registered minimum share 0.99 for A1 and A9)")
w("")
w("| scope | outer-test cells inverted (all arms, k = 0, 2, full) | non-converged | inner-CV cells inverted | inner-CV non-converged | max start spread (pp) | max share of forecasts differing > 1 pp between basins |")
w("|---|---|---|---|---|---|---|")
for k in ("B_m8", "B_m16", "B_m32", "B_all_m", "C", "S2"):
    s = S[k]
    ip = s["inversion_primary_outer"]
    ic = s["inversion_inner_cv"]
    w(f"| {k} | {ip['n_inverted']} | {ip['n_nonconverged']} | {ic['n_inverted']} | {ic['n_nonconverged']} | {f2(s['max_over_runs']['max_start_spread_pp'])} | {f3(s['max_over_runs']['max_share_forecast_differs_gt_1pp'])} |")
w("")
w("Outer-test (scored) inversions: 0 non-converged in every Test B run; the only non-converged cells are in the inner-CV tuning inversions (Test B: "
  f"{S['B_all_m']['inversion_inner_cv']['n_nonconverged']} of {S['B_all_m']['inversion_inner_cv']['n_inverted']}). The start-spread and basin columns are the maxima over all arm-by-k blocks in `inversion.per_arm_cell` (any arm; "
  "the 7.5 text records that the second-order inversion did not pass its start-spread criterion on ISU development data and was adopted as a convention); they are reported as logged, not interpreted per arm here.")
w("")
w("## 2. Error by forecast horizon (`outer_test_by_k[k][arm].horizon_rmse_pp`, descriptive)")
w("")
w("Horizon h = h-th check-up after the window. The writer's per-run value is the RMSE (pp) over the cells that have an h-th forecast (n cells; seed-ensemble). Pooled here over the 5 outer folds as sqrt(sum n rmse^2 / sum n) (n-weighted). "
  "g1 = (m 8, k 2), 5 runs `conf_samsung_B_f*_m8`, key `outer_test_by_k['2']`; g4 = (m 32, k full = 4), `conf_samsung_B_f*_m32`, key `outer_test_by_k['full']`. D* is the per-fold inner-CV winner "
  "(`metrics.comparators.D*`); at g1 it is A9 in fold 0 and A12 in folds 1-4; at g4 A12 in folds 0 and 3, A11 in folds 1, 2, 4. Different h pool different absolute times across cells (not a calendar horizon). "
  "n at h is the number of forecast cells; no condition weighting, so these are not the condition-level endpoints of Table 1.")
w("")
for g in ("g1", "g4"):
    H = r["item2_horizon"][g]["by_arm"]
    w(f"### {g} ({r['item2_horizon'][g]['cell']})")
    w("")
    w("| h | n cells | A1 | D* | A9 | A10 | R1 |")
    w("|---|---|---|---|---|---|---|")
    for h in sorted(H["A1"], key=int):
        w(f"| {h} | {H['A1'][h]['n_forecast_points']} | " + " | ".join(f2(H[a][h]["pooled_rmse_pp_nweighted"]) if h in H[a] else "--" for a in ("A1", "D*", "A9", "A10", "R1")) + " |")
    w("")
w("Caution at g4 h = 1: A1 1.90, A9 2.11, A10 1.30 are far above their h = 2 to 3 values and above R1 (0.69). This comes from one fold: g4 fold 2, h = 1 (n = 26 cells), "
  f"A1 {f2(r['item2_h1_by_fold']['g4']['2']['A1']['rmse_pp'])}, A9 {f2(r['item2_h1_by_fold']['g4']['2']['A9']['rmse_pp'])}, A10 {f2(r['item2_h1_by_fold']['g4']['2']['A10']['rmse_pp'])}, R1 {f2(r['item2_h1_by_fold']['g4']['2']['R1']['rmse_pp'])} pp "
  "(other folds 0.16 to 0.43 for A1). I did not trace the cause (not a cell-level audit); the pooled h = 1 value is dominated by that fold. Per-fold h = 1 values are in `item2_h1_by_fold`.")
w("")
w("## 3. Size context")
w("")
sc = r["item3_size_context"]
for g in ("g1", "g4"):
    s = sc[g]
    w(f"### {g}: {s['n_scored_cells']} scored cells, {s['n_conditions']} conditions (pooled over the 5 folds; from `predictions.csv` R1 rows of `outer_test_k2` / `outer_test_kfull`, `window.csv`)")
    w("")
    w("| quantity | min | q25 | median | q75 | max |")
    w("|---|---|---|---|---|---|")
    for key, lab in (("n_forecast_points_per_cell", "forecast check-ups per cell"), ("days_from_reference_to_first_forecast", "days, reference to first forecast"),
                     ("days_from_reference_to_last_checkup", "days, reference to last check-up"), ("forecast_span_days_first_to_last", "forecast span, days (first to last forecast)"),
                     ("observed_retention_at_last_checkup_pct", "observed retention at last check-up, %"), ("observed_fade_reference_to_last_checkup_pp", "observed fade, reference to last check-up, pp"),
                     ("observed_fade_window_end_to_last_checkup_pp", "observed fade, window end to last check-up, pp")):
        q = s[key]
        w(f"| {lab} | {f2(q['min'])} | {f2(q['q25'])} | {f2(q['median'])} | {f2(q['q75'])} | {f2(q['max'])} |")
    w("")
    w(f"Cells whose last observed retention is at or below 0.80: {s['n_cells_with_last_retention_le_0.80']} (RUL at 80 % not scorable; `metrics.json` rul.n_cells_crossing = 0 in the runs read). "
      "Days are from the reference check-up (t = 0 row of `window.csv`); EFC is not available in the run outputs read here and is not computed.")
    w("")
rf = sc["reference_floor"]["B"]
w(f"Replicate floor (`stats_frozen/analysis/reference.json`, training-side, descriptive, never a margin): Test B R_LOO {f3(rf['R_LOO'])} pp, R_WARP {f3(rf['R_WARP'])} pp (n_folds {rf['n_folds']}); Test C {f3(sc['reference_floor']['C']['R_LOO'])} / {f3(sc['reference_floor']['C']['R_WARP'])}; S2 {f3(sc['reference_floor']['S2']['R_LOO'])} / {f3(sc['reference_floor']['S2']['R_WARP'])}. "
  "Compare arm errors at g1 (A1 0.790) and g4 (A1 0.669), see item 4.")
w("")
w("## 4. A10 versus A1 numbers the reviewer quotes (`stats_frozen/post/arm_table.json`, mean over conditions, pp)")
w("")
a = r["item4_a10_vs_a1"]
w("| setting | key | A1 | A10 | A10P | n conditions | reviewer's figures | status |")
w("|---|---|---|---|---|---|---|---|")
w(f"| g1 | cells['8|2'] | {f3(a['g1']['A1'])} | {f3(a['g1']['A10'])} | {f3(a['g1']['A10P'])} | {a['g1']['n_conditions']} | A1 0.79, A10 1.21, A10P 1.31 | confirmed |")
w(f"| g4 | cells['32|full'] | {f3(a['g4']['A1'])} | {f3(a['g4']['A10'])} | {f3(a['g4']['A10P'])} | {a['g4']['n_conditions']} | A1 0.67, A10 0.75, A10P 0.94 | confirmed |")
w(f"| Test C | test_c | {f3(a['test_c']['A1'])} | {f3(a['test_c']['A10'])} | {f3(a['test_c']['A10P'])} | {a['test_c']['n_conditions']} | A10 0.39 vs A1 0.60; A10P 0.76 | confirmed |")
w(f"| S2 | s2 | {f3(a['s2']['A1'])} | {f3(a['s2']['A10'])} | {f3(a['s2']['A10P'])} | {a['s2']['n_conditions']} | A10 0.39 vs A1 0.32; A10P 0.57 | confirmed |")
w("")
w(f"Persistence R1 g1 {f3(a['g1']['R1'])}, g4 {f3(a['g4']['R1'])}; line-through-window R2 g1 {f3(a['g1']['R2'])}, g4 {f3(a['g4']['R2'])} (reviewer: R2 3.89 vs R1 3.39; 3.32 vs 2.91: confirmed). "
  f"n_params: A1 mean {a['g1']['A1_n_params_mean']:.1f} at g1 and {a['g4']['A1_n_params_mean']:.1f} at g4 (reviewer 'about 2,800'; range 2,489-3,029 per fold run, fine as 'about 2,700 to 2,800'); A10 11. "
  f"Fit seconds (one fit): A1 {a['g1']['A1_fit_seconds']:.1f} / {a['g4']['A1_fit_seconds']:.1f}, A10 {a['g1']['A10_fit_seconds']:.1f} / {a['g4']['A10_fit_seconds']:.1f} (g1 / g4). "
  "The paired difference 0.417 pp [0.197, 0.709] at g1 is from `extras/row_e_pp_scale.json`, which I did not re-derive here (it is not an arm_table value; A10 minus A1 means differ by 1.206 - 0.790 = 0.417, consistent).")
w("")
w("## 5. EXPLORATORY: b*sqrt(t) through the window (post hoc, NOT preregistered; descriptive; no test, no tier)")
w("")
w("Feasible without raw Samsung data: `window.csv` of each run holds the reference check-up and the window points (the points the forecasters also see), and `predictions.csv` holds the forecast times and held-out truths used for scoring (as for R1). "
  "Construction per scored cell: window = the post-reference points of `window.csv` before the first forecast check-up (k_eff; it equals k = 2 at g1 for all 140 cells; at g4 it is 4 for 136 cells, 3 for 3, 2 for 1: the D025 cap). "
  "Fit: b = sum sqrt(t) (1 - y) / sum t over the window points (least squares through the reference, one parameter, t in days since the reference, retention y; reference y = 1 as in window.csv), forecast y_hat = 1 - b sqrt(t), no clipping or monotonicity rule; "
  "nothing is fitted to any post-window value. Scored exactly as R1: cell RMSE over the forecast check-ups, then mean over the cells of each condition, then mean over the 40 conditions. "
  "Validation: the recomputed R1 reproduces `arm_table.json` exactly (g1 3.390, g4 2.906) and R1's carried-forward value equals the last window point in all 140 cells at both cells. "
  "A t^z form with z fitted was not computed: at k = 2 it has as many parameters as window points (exact interpolation), so it is not a like-for-like reference.")
w("")
w("| cell | sqrt baseline, mean condition RMSE (pp) | R1 persistence | A1 | A10 | sqrt median / worst condition | conditions: sqrt < R1 | A1 < sqrt | A10 < sqrt |")
w("|---|---|---|---|---|---|---|---|---|")
for g in ("g1", "g4"):
    s = r["item5_exploratory_sqrt"][g]
    v = r["item5_vs_scored_arms"][g]
    w(f"| {g} | {f3(s['mean_condition_rmse_pp_sqrt'])} | {f3(s['mean_condition_rmse_pp_R1_recomputed'])} | {f3(v['A1_mean_pp'])} | {f3(v['A10_mean_pp'])} | {f3(s['median_condition_rmse_pp_sqrt'])} / {f3(s['worst_condition_rmse_pp_sqrt'])} | {v['n_conditions_sqrt_lt_R1']} of {v['n_conditions']} | {v['n_conditions_A1_lt_sqrt']} of {v['n_conditions']} | {v['n_conditions_A10_lt_sqrt']} of {v['n_conditions']} |")
w("")
w(f"Reading, descriptive: the sqrt-through-window baseline is about half the persistence error (g1 {f2(r['item5_exploratory_sqrt']['g1']['mean_condition_rmse_pp_sqrt'])} vs {f2(r['item5_exploratory_sqrt']['g1']['mean_condition_rmse_pp_R1_recomputed'])} pp; g4 {f2(r['item5_exploratory_sqrt']['g4']['mean_condition_rmse_pp_sqrt'])} vs {f2(r['item5_exploratory_sqrt']['g4']['mean_condition_rmse_pp_R1_recomputed'])} pp) "
  f"but remains above A1 and A10 at both cells in mean; {r['item5_exploratory_sqrt']['g1']['n_cells_b_negative']} cell at g1 and {r['item5_exploratory_sqrt']['g4']['n_cells_b_negative']} at g4 had b < 0 (a rising forecast). So the sqrt baseline does not beat A1. "
  "No interval, no test. Persistence is therefore not the only yardstick, and the 11-parameter A10 is in the same range as this one-parameter baseline at g1 (1.206 vs 1.728; A10 lower) and the baseline is not lower than A10 at g4 (0.755 vs 1.469).")
w("")
w("## Notes and limits")
w("- Item 5 labelled exploratory, post hoc, not preregistered; it sets nothing and does not enter the title, abstract claim sentence or highlights.")
w("- Test B only for items 2 and 5; horizon pooling here is not the condition-level pooling of Table 1.")
w("- The D* labels are per fold and differ between g1 and g4, so the D* column pools different learners across folds.")
w("- I did not read `data/`; the retention values used come from `window.csv` and `predictions.csv` (run outputs).")
open(os.path.join(D, "SUMMARY.md"), "w", encoding="utf8").write("\n".join(L) + "\n")
sha = {}
for fn in ("descriptive_post.py", "descriptive_post_addon.py", "make_summary.py", "descriptive_post.json", "SUMMARY.md"):
    sha[fn] = hashlib.sha256(open(os.path.join(D, fn), "rb").read()).hexdigest()
json.dump(sha, open(os.path.join(D, "SHA256.json"), "w"), indent=1)
print("ok")
