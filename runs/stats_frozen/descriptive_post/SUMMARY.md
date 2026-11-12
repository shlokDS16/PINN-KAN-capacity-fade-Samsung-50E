# Descriptive post-freeze items for the Paper 7 domain review (2026-11-12)

Descriptive only: no test, no tier, no p-value, no claim word. Script: `descriptive_post.py` (+ `descriptive_post_addon.py`, `make_summary.py`); all numbers are in `descriptive_post.json`. Inputs: run outputs only (`diagnostics.json`, `tuning_*.json`, `metrics.json`, `predictions.csv`, `window.csv`, `condition_scores*.json`, `stats_frozen/post/arm_table.json`, `stats_frozen/analysis/reference.json`). No `data/` file opened.

## 1. Preregistered diagnostics (PREREG_v4 section 9.9, last paragraph; section 7.5)

Registered output (9.9): per fold, tuned `lam_res` with edge share, sd of fitted delta_c on training cells against TAU (flag outside [0.5, 2] x 0.15), clipped-step fraction for A1 and A9; 7.5: inversion convergence (non-converged cells counted per arm, fold, m, k).
TAU = 0.15; grid for lam_res = {1e-3, 1e-2, 1e-1, 1, 10, 100}. The flag band for delta_sd/tau is [0.5, 2].

### Reviewer's claims, verified
- A1 tuned lam_res = 1e-3 (grid minimum) in 12 of 15 Test B runs (m = 8: 5/5, m = 16: 4/5, m = 32: 3/5); 1e-2 in the other 3. `lam_res_at_lower_edge` is true in 12 runs, `lam_res_at_upper_edge` in 0. CONFIRMED.
- A1 delta_sd/tau over the 15 runs: min 0.012, median 0.113, max 0.319; 15 of 15 runs flagged (all below 0.5). Reviewer's 0.012-0.319 CONFIRMED (the reviewer wrote 0.01-0.32 of tau in the brief).
- A2 delta_sd/tau: 0.546 to 0.846, 15 of 15 inside the band. CONFIRMED.
- Not stated by the reviewer: the same pattern holds for the other physics-residual arms that were run (table below), and `lam_res_edge_share_over_arms` (share of residual-weight arms at the lower edge) is in the per-run JSON.

### Counts by arm (Test B, all 15 runs unless n given; A13 and A15 and G15 were run at m = 8 and 32 only)

| arm | n runs | lam_res counts | at lower edge | delta_sd/tau min / median / max | flagged outside [0.5, 2] | clip fraction min / mean / max |
|---|---|---|---|---|---|---|
| A1 | 15 | 0.001: 12, 0.01: 3 | 12 | 0.012 / 0.113 / 0.319 | 15 of 15 | 0.017 / 0.072 / 0.172 |
| A4 | 15 | 0.001: 11, 0.01: 4 | 11 | 0.019 / 0.086 / 0.401 | 15 of 15 | 0.013 / 0.062 / 0.169 |
| A13 | 10 | 0.001: 9, 0.01: 1 | 9 | 0.019 / 0.114 / 0.382 | 10 of 10 | 0.015 / 0.051 / 0.115 |
| A15 | 10 | 0.001: 9, 0.1: 1 | 9 | not logged | not logged | not logged |
| G15 | 10 | 0.001: 10 | 10 | not logged | not logged | not logged |
| A2 | 15 | n/a (no residual weight) | n/a | 0.546 / 0.652 / 0.846 | 0 of 15 | 0.000 / 0.003 / 0.007 |
| A9 | 15 | n/a (no residual weight) | n/a | not logged | not logged | 0.014 / 0.191 / 0.587 |

By m (A1 lam_res = 1e-3 count / delta_sd/tau range): m = 8: 5/5, 0.012-0.129; m = 16: 4/5, 0.047-0.171; m = 32: 3/5, 0.057-0.319.

Test C (1 run): A1 lam_res 0.01 (edge flag 0), delta_sd/tau 0.287 (flagged), clip fraction A1 0.146, A9 0.321. S2 (4 runs): A1 lam_res 0.01 in 4/4, edge flag 0, delta_sd/tau 0.215-0.260 (all flagged). So the lower-edge pattern is a Test B pattern; at Test C and S2 the tuned weight is 1e-2, one grid step up (the reviewer listed Test C only as a source file).

The `delta_sd_over_tau` is the sd of the fitted per-cell offset on training cells divided by TAU = 0.15; a ratio far below 0.5 means the offsets are strongly shrunk to the prior mean. It says nothing by itself about whether the law is 'off'; the residual still acts at collocation points beyond the records (reviewer's caveat; not tested here).

### Per-run table, Test B (A1 and A2)

| run | A1 lam_res | lower edge | A1 delta_sd/tau | A1 clip | A2 delta_sd/tau | A9 clip | A4 lam_res | A13 lam_res |
|---|---|---|---|---|---|---|---|---|
| conf_samsung_B_f0_m8 | 0.001 | True | 0.025 | 0.045 | 0.652 | 0.125 | 0.001 | 0.001 |
| conf_samsung_B_f1_m8 | 0.001 | True | 0.118 | 0.123 | 0.546 | 0.078 | 0.001 | 0.001 |
| conf_samsung_B_f2_m8 | 0.001 | True | 0.012 | 0.017 | 0.588 | 0.229 | 0.001 | 0.001 |
| conf_samsung_B_f3_m8 | 0.001 | True | 0.085 | 0.172 | 0.572 | 0.394 | 0.001 | 0.001 |
| conf_samsung_B_f4_m8 | 0.001 | True | 0.129 | 0.150 | 0.651 | 0.527 | 0.001 | 0.001 |
| conf_samsung_B_f0_m16 | 0.001 | True | 0.171 | 0.115 | 0.595 | 0.028 | 0.001 | not run |
| conf_samsung_B_f1_m16 | 0.001 | True | 0.131 | 0.076 | 0.681 | 0.587 | 0.01 | not run |
| conf_samsung_B_f2_m16 | 0.001 | True | 0.047 | 0.017 | 0.586 | 0.219 | 0.001 | not run |
| conf_samsung_B_f3_m16 | 0.01 | False | 0.130 | 0.084 | 0.653 | 0.159 | 0.001 | not run |
| conf_samsung_B_f4_m16 | 0.001 | True | 0.081 | 0.060 | 0.806 | 0.030 | 0.001 | not run |
| conf_samsung_B_f0_m32 | 0.01 | False | 0.273 | 0.067 | 0.846 | 0.022 | 0.01 | 0.01 |
| conf_samsung_B_f1_m32 | 0.001 | True | 0.112 | 0.035 | 0.627 | 0.014 | 0.001 | 0.001 |
| conf_samsung_B_f2_m32 | 0.01 | False | 0.319 | 0.018 | 0.684 | 0.185 | 0.01 | 0.001 |
| conf_samsung_B_f3_m32 | 0.001 | True | 0.057 | 0.049 | 0.782 | 0.020 | 0.001 | 0.001 |
| conf_samsung_B_f4_m32 | 0.001 | True | 0.113 | 0.055 | 0.657 | 0.253 | 0.01 | 0.001 |

The `tuning_A1.json` best_hp lam_res equals the diagnostics value in every run where both exist (checked in the JSON field `tuning_best_hp_lam_res`).

### Inversion convergence (7.5; registered minimum share 0.99 for A1 and A9)

| scope | outer-test cells inverted (all arms, k = 0, 2, full) | non-converged | inner-CV cells inverted | inner-CV non-converged | max start spread (pp) | max share of forecasts differing > 1 pp between basins |
|---|---|---|---|---|---|---|
| B_m8 | 11200 | 0 | 49456 | 11 | 35.63 | 0.103 |
| B_m16 | 7000 | 0 | 53613 | 1 | 42.36 | 0.308 |
| B_m32 | 12600 | 0 | 183612 | 23 | 49.63 | 0.038 |
| B_all_m | 30800 | 0 | 286681 | 35 | 49.63 | 0.308 |
| C | 585 | 0 | 8424 | 2 | 0.00 | 0.000 |
| S2 | 810 | 0 | 17010 | 3 | 0.00 | 0.000 |

Outer-test (scored) inversions: 0 non-converged in every Test B run; the only non-converged cells are in the inner-CV tuning inversions (Test B: 35 of 286681). The start-spread and basin columns are the maxima over all arm-by-k blocks in `inversion.per_arm_cell` (any arm; the 7.5 text records that the second-order inversion did not pass its start-spread criterion on ISU development data and was adopted as a convention); they are reported as logged, not interpreted per arm here.

## 2. Error by forecast horizon (`outer_test_by_k[k][arm].horizon_rmse_pp`, descriptive)

Horizon h = h-th check-up after the window. The writer's per-run value is the RMSE (pp) over the cells that have an h-th forecast (n cells; seed-ensemble). Pooled here over the 5 outer folds as sqrt(sum n rmse^2 / sum n) (n-weighted). g1 = (m 8, k 2), 5 runs `conf_samsung_B_f*_m8`, key `outer_test_by_k['2']`; g4 = (m 32, k full = 4), `conf_samsung_B_f*_m32`, key `outer_test_by_k['full']`. D* is the per-fold inner-CV winner (`metrics.comparators.D*`); at g1 it is A9 in fold 0 and A12 in folds 1-4; at g4 A12 in folds 0 and 3, A11 in folds 1, 2, 4. Different h pool different absolute times across cells (not a calendar horizon). n at h is the number of forecast cells; no condition weighting, so these are not the condition-level endpoints of Table 1.

### g1 (m=8, k=2)

| h | n cells | A1 | D* | A9 | A10 | R1 |
|---|---|---|---|---|---|---|
| 1 | 140 | 0.34 | 0.25 | 0.28 | 0.58 | 0.46 |
| 2 | 139 | 0.48 | 0.46 | 0.45 | 0.82 | 1.18 |
| 3 | 136 | 0.82 | 0.83 | 1.20 | 1.23 | 1.74 |
| 4 | 132 | 0.55 | 0.83 | 0.93 | 0.95 | 2.03 |
| 5 | 131 | 0.73 | 1.02 | 1.25 | 1.19 | 2.72 |
| 6 | 126 | 0.95 | 1.36 | 1.67 | 1.55 | 3.59 |
| 7 | 125 | 1.12 | 1.65 | 1.96 | 1.85 | 4.30 |
| 8 | 124 | 1.32 | 1.82 | 2.23 | 2.17 | 4.96 |
| 9 | 116 | 1.17 | 1.42 | 2.11 | 2.05 | 5.15 |
| 10 | 66 | 1.32 | 1.84 | 2.64 | 2.87 | 6.65 |
| 11 | 66 | 1.42 | 1.91 | 2.78 | 3.11 | 7.25 |
| 12 | 64 | 1.49 | 2.15 | 2.90 | 3.45 | 7.92 |
| 13 | 36 | 1.47 | 2.05 | 3.12 | 4.01 | 7.94 |

### g4 (m=32, k=full)

| h | n cells | A1 | D* | A9 | A10 | R1 |
|---|---|---|---|---|---|---|
| 1 | 140 | 1.90 | 0.76 | 2.11 | 1.30 | 0.69 |
| 2 | 132 | 0.32 | 0.29 | 0.37 | 0.35 | 0.96 |
| 3 | 131 | 0.46 | 0.47 | 0.54 | 0.44 | 1.66 |
| 4 | 126 | 0.77 | 0.90 | 1.06 | 0.88 | 2.56 |
| 5 | 125 | 0.94 | 1.69 | 1.37 | 1.10 | 3.28 |
| 6 | 124 | 1.19 | 2.02 | 1.72 | 1.37 | 3.94 |
| 7 | 116 | 1.00 | 1.20 | 1.52 | 0.92 | 4.13 |
| 8 | 66 | 1.32 | 1.45 | 1.93 | 1.28 | 5.43 |
| 9 | 66 | 1.47 | 1.64 | 2.18 | 1.40 | 6.03 |
| 10 | 64 | 1.59 | 1.79 | 2.45 | 1.60 | 6.71 |
| 11 | 36 | 1.88 | 1.70 | 2.81 | 1.68 | 6.83 |

Caution at g4 h = 1: A1 1.90, A9 2.11, A10 1.30 are far above their h = 2 to 3 values and above R1 (0.69). This comes from one fold: g4 fold 2, h = 1 (n = 26 cells), A1 4.37, A9 4.87, A10 2.95, R1 1.16 pp (other folds 0.16 to 0.43 for A1). I did not trace the cause (not a cell-level audit); the pooled h = 1 value is dominated by that fold. Per-fold h = 1 values are in `item2_h1_by_fold`.

## 3. Size context

### g1: 140 scored cells, 40 conditions (pooled over the 5 folds; from `predictions.csv` R1 rows of `outer_test_k2` / `outer_test_kfull`, `window.csv`)

| quantity | min | q25 | median | q75 | max |
|---|---|---|---|---|---|
| forecast check-ups per cell | 1.00 | 9.00 | 9.00 | 13.00 | 13.00 |
| days, reference to first forecast | 28.00 | 28.00 | 31.00 | 50.00 | 90.00 |
| days, reference to last check-up | 28.00 | 305.00 | 308.00 | 340.50 | 433.00 |
| forecast span, days (first to last forecast) | 0.00 | 237.00 | 258.00 | 307.00 | 402.00 |
| observed retention at last check-up, % | 83.97 | 90.45 | 93.22 | 95.55 | 99.02 |
| observed fade, reference to last check-up, pp | 0.98 | 4.45 | 6.78 | 9.55 | 16.03 |
| observed fade, window end to last check-up, pp | 0.70 | 3.31 | 5.50 | 7.91 | 13.86 |

Cells whose last observed retention is at or below 0.80: 0 (RUL at 80 % not scorable; `metrics.json` rul.n_cells_crossing = 0 in the runs read). Days are from the reference check-up (t = 0 row of `window.csv`); EFC is not available in the run outputs read here and is not computed.

### g4: 140 scored cells, 40 conditions (pooled over the 5 folds; from `predictions.csv` R1 rows of `outer_test_k2` / `outer_test_kfull`, `window.csv`)

| quantity | min | q25 | median | q75 | max |
|---|---|---|---|---|---|
| forecast check-ups per cell | 1.00 | 7.00 | 7.00 | 11.00 | 11.00 |
| days, reference to first forecast | 28.00 | 59.00 | 65.50 | 92.00 | 433.00 |
| days, reference to last check-up | 28.00 | 305.00 | 308.00 | 340.50 | 433.00 |
| forecast span, days (first to last forecast) | 0.00 | 202.00 | 219.00 | 273.00 | 287.00 |
| observed retention at last check-up, % | 83.97 | 90.45 | 93.22 | 95.55 | 99.02 |
| observed fade, reference to last check-up, pp | 0.98 | 4.45 | 6.78 | 9.55 | 16.03 |
| observed fade, window end to last check-up, pp | 0.17 | 2.67 | 4.54 | 6.70 | 12.24 |

Cells whose last observed retention is at or below 0.80: 0 (RUL at 80 % not scorable; `metrics.json` rul.n_cells_crossing = 0 in the runs read). Days are from the reference check-up (t = 0 row of `window.csv`); EFC is not available in the run outputs read here and is not computed.

Replicate floor (`stats_frozen/analysis/reference.json`, training-side, descriptive, never a margin): Test B R_LOO 0.178 pp, R_WARP 0.111 pp (n_folds 5); Test C 0.196 / 0.121; S2 0.192 / 0.111. Compare arm errors at g1 (A1 0.790) and g4 (A1 0.669), see item 4.

## 4. A10 versus A1 numbers the reviewer quotes (`stats_frozen/post/arm_table.json`, mean over conditions, pp)

| setting | key | A1 | A10 | A10P | n conditions | reviewer's figures | status |
|---|---|---|---|---|---|---|---|
| g1 | cells['8|2'] | 0.790 | 1.206 | 1.309 | 40 | A1 0.79, A10 1.21, A10P 1.31 | confirmed |
| g4 | cells['32|full'] | 0.669 | 0.755 | 0.936 | 40 | A1 0.67, A10 0.75, A10P 0.94 | confirmed |
| Test C | test_c | 0.598 | 0.386 | 0.759 | 13 | A10 0.39 vs A1 0.60; A10P 0.76 | confirmed |
| S2 | s2 | 0.321 | 0.392 | 0.566 | 19 | A10 0.39 vs A1 0.32; A10P 0.57 | confirmed |

Persistence R1 g1 3.390, g4 2.906; line-through-window R2 g1 3.886, g4 3.315 (reviewer: R2 3.89 vs R1 3.39; 3.32 vs 2.91: confirmed). n_params: A1 mean 2733.8 at g1 and 2792.6 at g4 (reviewer 'about 2,800'; range 2,489-3,029 per fold run, fine as 'about 2,700 to 2,800'); A10 11. Fit seconds (one fit): A1 20.4 / 21.2, A10 4.4 / 8.0 (g1 / g4). The paired difference 0.417 pp [0.197, 0.709] at g1 is from `extras/row_e_pp_scale.json`, which I did not re-derive here (it is not an arm_table value; A10 minus A1 means differ by 1.206 - 0.790 = 0.417, consistent).

## 5. EXPLORATORY: b*sqrt(t) through the window (post hoc, NOT preregistered; descriptive; no test, no tier)

Feasible without raw Samsung data: `window.csv` of each run holds the reference check-up and the window points (the points the forecasters also see), and `predictions.csv` holds the forecast times and held-out truths used for scoring (as for R1). Construction per scored cell: window = the post-reference points of `window.csv` before the first forecast check-up (k_eff; it equals k = 2 at g1 for all 140 cells; at g4 it is 4 for 136 cells, 3 for 3, 2 for 1: the D025 cap). Fit: b = sum sqrt(t) (1 - y) / sum t over the window points (least squares through the reference, one parameter, t in days since the reference, retention y; reference y = 1 as in window.csv), forecast y_hat = 1 - b sqrt(t), no clipping or monotonicity rule; nothing is fitted to any post-window value. Scored exactly as R1: cell RMSE over the forecast check-ups, then mean over the cells of each condition, then mean over the 40 conditions. Validation: the recomputed R1 reproduces `arm_table.json` exactly (g1 3.390, g4 2.906) and R1's carried-forward value equals the last window point in all 140 cells at both cells. A t^z form with z fitted was not computed: at k = 2 it has as many parameters as window points (exact interpolation), so it is not a like-for-like reference.

| cell | sqrt baseline, mean condition RMSE (pp) | R1 persistence | A1 | A10 | sqrt median / worst condition | conditions: sqrt < R1 | A1 < sqrt | A10 < sqrt |
|---|---|---|---|---|---|---|---|---|
| g1 | 1.728 | 3.390 | 0.790 | 1.206 | 1.557 / 3.927 | 40 of 40 | 35 of 40 | 29 of 40 |
| g4 | 1.469 | 2.906 | 0.669 | 0.755 | 1.303 / 3.801 | 37 of 40 | 37 of 40 | 37 of 40 |

Reading, descriptive: the sqrt-through-window baseline is about half the persistence error (g1 1.73 vs 3.39 pp; g4 1.47 vs 2.91 pp) but remains above A1 and A10 at both cells in mean; 1 cell at g1 and 0 at g4 had b < 0 (a rising forecast). So the sqrt baseline does not beat A1. No interval, no test. Persistence is therefore not the only yardstick, and the 11-parameter A10 is in the same range as this one-parameter baseline at g1 (1.206 vs 1.728; A10 lower) and the baseline is not lower than A10 at g4 (0.755 vs 1.469).

## Notes and limits
- Item 5 labelled exploratory, post hoc, not preregistered; it sets nothing and does not enter the title, abstract claim sentence or highlights.
- Test B only for items 2 and 5; horizon pooling here is not the condition-level pooling of Table 1.
- The D* labels are per fold and differ between g1 and g4, so the D* column pools different learners across folds.
- I did not read `data/`; the retention values used come from `window.csv` and `predictions.csv` (run outputs).

## 6. Fix 11 and fix 18 tables (descriptive_post_tables.py; descriptive, no test, no tier)

### 6.1 Median over the 40 held-out conditions of the condition score (pp), g1 = (m 8, k 2), g4 = (m 32, k full)

Mean reproduces arm_table.json mean_pp for every arm (max abs difference 4.4e-16 at both cells). D* = per-fold inner-CV winner from comparators.json, assembled as stats_v4.Store.from_runs does; it pools different learners across folds (g1 folds 0-4: A9, A12, A12, A12, A12; g4: A12, A11, A11, A12, A11). The D* mean condition RMSE pooled as arm_table does is the D* mean column here (arm_table.json has no D* row).

| arm | g1 mean | g1 median | g4 mean | g4 median |
|---|---|---|---|---|
| A1 | 0.790 | 0.703 | 0.669 | 0.331 |
| A10 | 1.206 | 1.072 | 0.755 | 0.470 |
| A10P | 1.309 | 0.960 | 0.936 | 0.698 |
| A11 | 1.154 | 0.919 | 0.627 | 0.330 |
| A12 | 0.918 | 0.747 | 0.660 | 0.318 |
| A12R | 0.908 | 0.693 | 0.701 | 0.367 |
| A13 | 1.139 | 0.930 | 0.796 | 0.395 |
| A15 | 0.820 | 0.676 | 0.736 | 0.450 |
| A2 | 1.273 | 0.945 | 0.977 | 0.637 |
| A4 | 0.836 | 0.642 | 0.679 | 0.347 |
| A5 | n/a | n/a | 0.684 | 0.321 |
| A9 | 1.020 | 0.660 | 0.891 | 0.444 |
| AG | 0.836 | 0.642 | 0.692 | 0.358 |
| D* | 0.925 | 0.663 | 0.721 | 0.330 |
| G15 | 0.819 | 0.598 | 0.685 | 0.482 |
| R1 | 3.390 | 3.060 | 2.906 | 2.501 |
| R2 | 3.886 | 2.772 | 3.315 | 2.143 |

### 6.2 Model-defined calendar share (PREREG_v4 11a item 4), confirmatory m32 runs, A1 and A2 (140 cells each)

Source: runs/conf_samsung_B_f{0..4}_m32/superposition.csv (the runs physval item 4 reads); lab from condition_meta.json (majority lab of the condition's cells); T from the condition key. share_cal > 1 means the counterfactual calendar loss exceeds the fitted total; the file's own cal_exceeds_total flag (observed total) is set in 8 of 280 rows (both arms), a different criterion.

| grouping | group | arm | cells | conditions | median | min | max | cells with share > 1 |
|---|---|---|---|---|---|---|---|---|
| temperature_C | 23 | A1 | 33 | 10 | 0.532 | 0.295 | 1.827 | 3 |
| temperature_C | 35 | A1 | 39 | 13 | 0.699 | 0.387 | 0.981 | 0 |
| temperature_C | 45 | A1 | 68 | 17 | 0.485 | 0.260 | 0.723 | 0 |
| temperature_C | 23 | A2 | 33 | 10 | 0.468 | 0.375 | 0.825 | 0 |
| temperature_C | 35 | A2 | 39 | 13 | 0.764 | 0.385 | 0.934 | 0 |
| temperature_C | 45 | A2 | 68 | 17 | 0.398 | 0.100 | 0.811 | 0 |
| laboratory | HM | A1 | 71 | 17 | 0.487 | 0.260 | 0.723 | 0 |
| laboratory | INT | A1 | 57 | 19 | 0.664 | 0.295 | 1.827 | 3 |
| laboratory | SIE | A1 | 12 | 4 | 0.398 | 0.346 | 0.681 | 0 |
| laboratory | HM | A2 | 71 | 17 | 0.399 | 0.100 | 0.825 | 0 |
| laboratory | INT | A2 | 57 | 19 | 0.642 | 0.375 | 0.934 | 0 |
| laboratory | SIE | A2 | 12 | 4 | 0.424 | 0.386 | 0.607 | 0 |
| all | all | A1 | 140 | 40 | 0.522 | 0.260 | 1.827 | 3 |
| all | all | A2 | 140 | 40 | 0.484 | 0.100 | 0.934 | 0 |

Plainly: there is no 35 C storage in these data, and 35 C is all laboratory INT (cells by laboratory: {"23": {"INT": 18, "SIE": 9, "HM": 6}, "35": {"INT": 39}, "45": {"HM": 65, "SIE": 3}}). Temperature and laboratory are confounded at 35 C; 23 C and 45 C each mix laboratories. Laboratory is the majority laboratory of the condition's cells (condition_meta.json). No test, no claim.
