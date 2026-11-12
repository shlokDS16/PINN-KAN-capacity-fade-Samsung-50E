# Post-hoc statistics for the teacher's review (no refit), 2026-11-12

Status: POST-HOC and EXPLORATORY (decision D048). Nothing here changes a frozen decision (P0, K=, M1 to M3, NC-2, T5). Computed from stored files only; `code/`, `runs/prereg/` and `runs/stats_frozen/` were read, never written. Every number below is formatted by `make_summary.py` from `t2_rho_sweep.json`, `e4_final_target.json`, `e3_descriptive.json` or `c1_flow.json` in this folder. Hashes: `SHA256.json`.

Validation before use. T2: at rho = 0.03 every stored p-value, critical count and graph decision was reproduced with the frozen test function (graph_test.py sha256 `6285f7d1b7c5dfddf8f10d80d6c2512c3b8a37aa796eac99a755f407d4cc6c23`, imported read-only): all reproduced = yes; primary graph decision matches = yes; secondary graph decision matches = yes. E4: the condition mean of the recomputed cell RMSE matches the stored `condition_scores` json for every arm and fold, largest absolute difference 1.2e-14 pp at g1 and 1.4e-14 pp at g4 (validation ok: g1 yes, g4 yes). E4 reconciliation with the frozen endpoint: median log ratio of A1 against D* over all forecast check-ups is -0.0233 at g1 and 0.0224 at g4 (20 and 21 of 40 positive). Table D.1 check: pooled A1 RMSE at forecast index 1 recomputes as 0.333 (g1) and 1.892 (g4), n = 140 cells; the plan quotes 0.34 and 1.90, so the second decimal of the printed Table D.1 is not reproduced by this recomputation (condition scores are).

## 1. E4 / Q4: error at the final forecast check-up of each held-out cell (exploratory)

Construction. Ensemble forecasts (five-seed mean for A1 and A9). Final target = the last forecast check-up of each held-out cell; condition value = mean over the condition's cells of the absolute error in percentage points; unit = the held-out condition (n = 40). Paired difference d = A1 error minus comparator error: NEGATIVE means A1 has the lower error. Median interval = frozen exact order-statistic interval (independent conditions, unadjusted for dependence); mean interval = BCa, 10000 condition-bootstrap resamples (seed rule `SeedSequence([20261105, crc32(label)])`). D* is the inner-CV-selected data-driven learner per fold: g1 A9, A12, A12, A12, A12; g4 A12, A11, A11, A12, A11 (fold 0 to 4). Comparators printed with equal prominence: D*, A9, A10 and its second form A10P, R1. No tier words, no p-values.

### g1 = (m 8, k 2)

Final-check-up horizon per condition (days after the window end): median 267.5, range 52.7 to 326.0. Window end = last k = 0 forecast row before the cell's first forecast row (k0_forecast_row: 140 cells).

Final-check-up error by arm (condition median and mean over 40 conditions, pp), all arms:

| arm | median | mean |
|---|---|---|
| A1 | 0.94 | 1.24 |
| A9 | 0.99 | 1.55 |
| A10 | 1.60 | 1.94 |
| A10P | 1.42 | 2.01 |
| A11 | 1.22 | 1.53 |
| A12 | 0.98 | 1.38 |
| A2 | 0.93 | 1.57 |
| A4 | 1.04 | 1.34 |
| A13 | 1.61 | 1.89 |
| A15 | 0.97 | 1.33 |
| G15 | 0.97 | 1.31 |
| R1 | 5.01 | 5.61 |
| R2 | 4.65 | 7.11 |
| D* | 0.87 | 1.34 |

Paired difference d = A1 minus comparator (pp; negative = A1 lower):

| comparator | median d [order-statistic 95 %] | median d, BCa 95 % | mean d [BCa 95 %] | conditions with A1 lower / higher |
|---|---|---|---|---|
| D* | 0.02 [-0.12, 0.31] | [-0.12, 0.29] | -0.10 [-0.53, 0.15] | 20 / 20 (of 40) |
| A9 | -0.00 [-0.11, 0.26] | [-0.10, 0.24] | -0.32 [-0.87, 0.03] | 21 / 19 (of 40) |
| A10 | -0.30 [-0.74, 0.03] | [-0.66, -0.05] | -0.70 [-1.20, -0.31] | 26 / 14 (of 40) |
| A10P | -0.31 [-0.92, 0.12] | [-0.89, 0.08] | -0.77 [-1.39, -0.34] | 25 / 15 (of 40) |
| R1 | -3.56 [-4.96, -2.95] | [-4.96, -3.18] | -4.37 [-5.30, -3.62] | 40 / 0 (of 40) |

388-day sensitivity: not applicable at g1 (no cell has a first forecast check-up 380 days or more after the window end).

Stability row: condition RMSE over the last three forecast check-ups, log ratio L = ln(S_comparator / S_A1) (positive = A1 lower error), median with the frozen order-statistic interval:

| comparator | median L [order-statistic 95 %] | conditions with L > 0 |
|---|---|---|
| D* | -0.028 [-0.290, 0.179] | 19 of 40 |
| A9 | -0.015 [-0.332, 0.123] | 19 of 40 |
| A10 | 0.261 [-0.048, 0.533] | 26 of 40 |
| A10P | 0.333 [-0.139, 0.496] | 25 of 40 |
| R1 | 1.560 [1.327, 1.767] | 40 of 40 |

Horizon tertiles (cut points at 267.0 and 288.0 days, tertile sizes 20/12/8; description only). Median d per tertile [order-statistic 95 %] and conditions with A1 lower; Spearman correlation of d with the final horizon in days, with a condition-bootstrap percentile interval:

| comparator | tertile 1 | tertile 2 | tertile 3 | Spearman rho [95 %] |
|---|---|---|---|---|
| D* | 0.13 [-0.11, 0.36], 9 of 20 | 0.13 [-1.16, 1.01], 5 of 12 | -0.11 [-1.63, 0.43], 6 of 8 | -0.28 [-0.55, 0.03] |
| A9 | -0.01 [-0.25, 0.24], 12 of 20 | 0.13 [-1.99, 0.58], 5 of 12 | 0.14 [-5.13, 0.77], 4 of 8 | 0.08 [-0.25, 0.40] |
| A10 | -0.25 [-0.51, 0.14], 13 of 20 | -0.70 [-2.89, 0.83], 7 of 12 | -1.03 [-5.61, 0.60], 6 of 8 | -0.22 [-0.51, 0.12] |
| A10P | -0.21 [-0.55, 0.19], 12 of 20 | -0.83 [-1.66, 0.96], 7 of 12 | -1.61 [-6.18, 1.00], 6 of 8 | -0.33 [-0.59, 0.01] |
| R1 | -2.38 [-3.28, -1.62], 20 of 20 | -6.14 [-8.19, -3.27], 12 of 12 | -5.36 [-9.72, -3.69], 8 of 8 | -0.61 [-0.80, -0.35] |

### g4 = (m 32, k full)

Final-check-up horizon per condition (days after the window end): median 236.0, range 28.7 to 303.0. Window end = last k = 0 forecast row before the cell's first forecast row (k0_forecast_row: 140 cells).

Final-check-up error by arm (condition median and mean over 40 conditions, pp), all arms:

| arm | median | mean |
|---|---|---|
| A1 | 0.54 | 0.95 |
| A9 | 0.66 | 1.31 |
| A10 | 0.69 | 1.11 |
| A10P | 0.83 | 1.24 |
| A11 | 0.48 | 0.85 |
| A12 | 0.56 | 0.92 |
| A2 | 0.75 | 1.23 |
| A4 | 0.51 | 0.95 |
| A5 | 0.48 | 0.96 |
| A13 | 0.54 | 1.18 |
| A15 | 0.65 | 1.06 |
| G15 | 0.69 | 0.99 |
| R1 | 4.02 | 4.64 |
| R2 | 3.68 | 5.46 |
| D* | 0.49 | 0.98 |

Paired difference d = A1 minus comparator (pp; negative = A1 lower):

| comparator | median d [order-statistic 95 %] | median d, BCa 95 % | mean d [BCa 95 %] | conditions with A1 lower / higher |
|---|---|---|---|---|
| D* | 0.04 [-0.24, 0.18] | [-0.22, 0.18] | -0.03 [-0.36, 0.31] | 20 / 20 (of 40) |
| A9 | -0.23 [-0.40, -0.08] | [-0.37, -0.09] | -0.36 [-0.66, -0.14] | 28 / 12 (of 40) |
| A10 | -0.19 [-0.49, 0.15] | [-0.49, 0.11] | -0.16 [-0.44, 0.17] | 23 / 17 (of 40) |
| A10P | -0.21 [-0.70, 0.04] | [-0.70, 0.01] | -0.29 [-0.62, 0.05] | 26 / 14 (of 40) |
| R1 | -3.34 [-4.56, -2.37] | [-4.56, -2.40] | -3.69 [-4.49, -2.87] | 39 / 1 (of 40) |

388-day sensitivity (shown BESIDE the unaltered rows above, never in place of them). The cell with a first forecast check-up 388 days after the window end is `TP_z02_03_s2` (condition `T45|SOCmax0.8|DoD0.6|Cch1|Cdch2`, fold 2; its only forecast point is also its final one). Row 1 drops that whole condition (n = 39); row 2 drops only that cell from its condition mean (n = 40):

| comparator | unaltered: median d, mean d [BCa] (n = 40) | drop condition: median d, mean d [BCa] (n = 39) | drop cell: median d, mean d [BCa] (n = 40) |
|---|---|---|---|
| D* | 0.04, -0.03 [-0.36, 0.31] | -0.01, -0.12 [-0.43, 0.15] | 0.04, -0.09 [-0.41, 0.18] |
| A9 | -0.23, -0.36 [-0.66, -0.14] | -0.20, -0.35 [-0.67, -0.14] | -0.23, -0.35 [-0.66, -0.14] |
| A10 | -0.19, -0.16 [-0.44, 0.17] | -0.20, -0.22 [-0.50, 0.07] | -0.19, -0.19 [-0.48, 0.11] |
| A10P | -0.21, -0.29 [-0.62, 0.05] | -0.24, -0.36 [-0.68, -0.04] | -0.21, -0.32 [-0.64, -0.01] |
| R1 | -3.34, -3.69 [-4.49, -2.87] | -3.36, -3.88 [-4.66, -3.21] | -3.34, -3.78 [-4.57, -3.11] |

Stability row: condition RMSE over the last three forecast check-ups, log ratio L = ln(S_comparator / S_A1) (positive = A1 lower error), median with the frozen order-statistic interval:

| comparator | median L [order-statistic 95 %] | conditions with L > 0 |
|---|---|---|
| D* | -0.010 [-0.345, 0.425] | 19 of 40 |
| A9 | 0.382 [0.063, 0.664] | 27 of 40 |
| A10 | 0.294 [-0.159, 0.664] | 25 of 40 |
| A10P | 0.492 [0.097, 0.880] | 27 of 40 |
| R1 | 1.959 [1.622, 2.186] | 39 of 40 |

Horizon tertiles (cut points at 230.3 and 264.0 days, tertile sizes 14/18/8; description only). Median d per tertile [order-statistic 95 %] and conditions with A1 lower; Spearman correlation of d with the final horizon in days, with a condition-bootstrap percentile interval:

| comparator | tertile 1 | tertile 2 | tertile 3 | Spearman rho [95 %] |
|---|---|---|---|---|
| D* | -0.07 [-0.64, 0.52], 8 of 14 | 0.09 [-0.58, 0.42], 8 of 18 | 0.02 [-1.85, 1.43], 4 of 8 | -0.08 [-0.41, 0.28] |
| A9 | -0.21 [-0.73, 0.16], 10 of 14 | -0.18 [-0.61, 0.17], 12 of 18 | -0.35 [-2.58, 0.79], 6 of 8 | -0.07 [-0.39, 0.28] |
| A10 | -0.18 [-0.69, 0.37], 8 of 14 | 0.01 [-0.82, 0.52], 9 of 18 | -0.84 [-2.68, 2.73], 6 of 8 | -0.17 [-0.50, 0.19] |
| A10P | -0.06 [-0.71, 0.29], 9 of 14 | -0.24 [-0.70, 0.13], 11 of 18 | -1.14 [-2.97, 2.61], 6 of 8 | -0.20 [-0.57, 0.18] |
| R1 | -2.07 [-4.17, -0.77], 13 of 14 | -3.76 [-5.62, -2.03], 18 of 18 | -4.70 [-7.90, -3.25], 8 of 8 | -0.58 [-0.78, -0.28] |

Reading rule (fixed in the plan, applied without interpretation): a late-horizon statement is made only if the tertile medians and the Spearman interval point the same way at both cells; the tables above are the evidence, no direction is asserted here.

## 2. E3 (descriptive): five-seed spread, optimisation spread only

All quantities describe the spread of five training seeds. This is OPTIMISATION spread, not predictive uncertainty: no calibration, no coverage guarantee for new conditions, no conformal method. Intervals: condition cluster bootstrap (10000 resamples; 2000 for the point-level Spearman). The ensemble mean equals the stored `ens` rows (largest absolute difference 4.4e-16 in retention).

Coverage: share of forecast points whose observed retention lies inside the band (pooled over folds; condition-cluster 95 % interval):

| cell | arm | n points | min-max envelope | mean +/- 1 SD | mean +/- 2 SD | mean +/- 3 SD |
|---|---|---|---|---|---|---|
| g1 | A1 | 1401 | 0.301 [0.204, 0.399] | 0.238 [0.153, 0.322] | 0.445 [0.322, 0.568] | 0.595 [0.473, 0.700] |
| g1 | A9 | 1401 | 0.233 [0.165, 0.314] | 0.208 [0.147, 0.277] | 0.398 [0.305, 0.488] | 0.550 [0.433, 0.655] |
| g4 | A1 | 1126 | 0.250 [0.175, 0.336] | 0.201 [0.138, 0.274] | 0.395 [0.287, 0.507] | 0.552 [0.419, 0.682] |
| g4 | A9 | 1126 | 0.194 [0.124, 0.273] | 0.180 [0.110, 0.261] | 0.312 [0.210, 0.418] | 0.453 [0.315, 0.584] |

Envelope coverage by forecast-index tertile (cut points on the pooled forecast index):

| cell | arm | tertile 1 | tertile 2 | tertile 3 |
|---|---|---|---|---|
| g1 | A1 | 0.260 [0.184, 0.332] (n 547) | 0.285 [0.185, 0.385] (n 506) | 0.391 [0.189, 0.589] (n 348) |
| g1 | A9 | 0.207 [0.129, 0.302] (n 547) | 0.314 [0.222, 0.409] (n 506) | 0.155 [0.068, 0.294] (n 348) |
| g4 | A1 | 0.201 [0.139, 0.270] (n 403) | 0.291 [0.192, 0.400] (n 375) | 0.261 [0.156, 0.405] (n 348) |
| g4 | A9 | 0.164 [0.109, 0.220] (n 403) | 0.229 [0.138, 0.328] (n 375) | 0.190 [0.073, 0.354] (n 348) |

Size of the spread against the observed error (pooled over points):

| cell | arm | mean seed SD (pp) | mean abs error of ensemble (pp) | mean SD / mean abs error | mean envelope full width (pp) |
|---|---|---|---|---|---|
| g1 | A1 | 0.279 [0.222, 0.331] | 0.643 [0.530, 0.761] | 0.434 [0.327, 0.565] | 0.703 |
| g1 | A9 | 0.437 [0.243, 0.677] | 0.914 [0.589, 1.274] | 0.478 [0.324, 0.702] | 1.067 |
| g4 | A1 | 0.167 [0.133, 0.211] | 0.593 [0.358, 0.864] | 0.282 [0.194, 0.425] | 0.406 |
| g4 | A9 | 0.312 [0.179, 0.487] | 0.796 [0.511, 1.089] | 0.392 [0.227, 0.689] | 0.736 |

Rank histogram (number of the five seed forecasts below the observation, bins 0 to 5; shares; a uniform histogram would be 0.167 per bin; not tested):

| cell | arm | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|---|
| g1 | A1 | 0.488 [0.377, 0.621] | 0.093 [0.059, 0.134] | 0.054 [0.034, 0.080] | 0.054 [0.032, 0.079] | 0.100 [0.037, 0.179] | 0.211 [0.125, 0.303] |
| g1 | A9 | 0.490 [0.378, 0.603] | 0.055 [0.029, 0.089] | 0.054 [0.027, 0.084] | 0.056 [0.026, 0.100] | 0.068 [0.037, 0.113] | 0.278 [0.172, 0.386] |
| g4 | A1 | 0.321 [0.215, 0.430] | 0.091 [0.056, 0.132] | 0.052 [0.033, 0.076] | 0.052 [0.028, 0.081] | 0.054 [0.029, 0.089] | 0.429 [0.288, 0.582] |
| g4 | A9 | 0.380 [0.264, 0.509] | 0.048 [0.023, 0.084] | 0.059 [0.023, 0.112] | 0.042 [0.016, 0.076] | 0.045 [0.023, 0.074] | 0.426 [0.279, 0.577] |

Spread-skill (Spearman correlation of seed SD with absolute error; ranks the errors, no coverage claim):

| cell | arm | point level rho [95 %] | condition level rho [95 %] (n = 40) |
|---|---|---|---|
| g1 | A1 | 0.472 [0.324, 0.618] | 0.337 [0.030, 0.598] |
| g1 | A9 | 0.609 [0.472, 0.720] | 0.556 [0.271, 0.752] |
| g4 | A1 | 0.493 [0.367, 0.606] | 0.335 [-0.004, 0.606] |
| g4 | A9 | 0.522 [0.337, 0.662] | 0.421 [0.118, 0.652] |

Mean absolute error of the ensemble (pp) within quintiles of seed SD (quintile 1 = smallest spread):

| cell | arm | Q1 | Q2 | Q3 | Q4 | Q5 |
|---|---|---|---|---|---|---|
| g1 | A1 | 0.294 | 0.404 | 0.572 | 0.801 | 1.143 |
| g1 | A9 | 0.229 | 0.397 | 0.538 | 0.883 | 2.516 |
| g4 | A1 | 0.209 | 0.285 | 0.341 | 0.777 | 1.349 |
| g4 | A9 | 0.223 | 0.384 | 0.618 | 0.917 | 1.836 |

One training-side band (the five-seed min-max envelope, label: optimisation spread, not predictive uncertainty): mean full width and share of observations inside.

| cell | arm | mean full width (pp) | median full width (pp) | share inside [95 %] |
|---|---|---|---|---|
| g1 | A1 | 0.703 | 0.449 | 0.301 [0.204, 0.399] |
| g1 | A9 | 1.067 | 0.377 | 0.233 [0.165, 0.314] |
| g4 | A1 | 0.406 | 0.296 | 0.250 [0.175, 0.336] |
| g4 | A9 | 0.736 | 0.303 | 0.194 [0.124, 0.273] |

Observed absolute-error quantiles of the ensemble forecast (pp; observed on these 40 conditions; not a predictive interval; no coverage guarantee for new conditions):

| cell | arm | point 50 % | 80 % | 90 % | 95 % | condition RMSE 50 % | 80 % | 90 % | 95 % |
|---|---|---|---|---|---|---|---|---|---|
| g1 | A1 | 0.442 | 1.066 | 1.500 | 1.860 | 0.703 | 1.212 | 1.384 | 1.513 |
| g1 | A9 | 0.413 | 1.211 | 2.575 | 4.217 | 0.660 | 1.356 | 2.566 | 3.123 |
| g4 | A1 | 0.278 | 0.783 | 1.509 | 2.561 | 0.331 | 0.811 | 1.358 | 2.103 |
| g4 | A9 | 0.373 | 1.096 | 2.164 | 3.095 | 0.444 | 1.083 | 2.216 | 2.865 |

## 3. T2: sweep of the assumed correlation rho, recomputed from the stored counts (exploratory)

Range swept: 0.00 to 0.50 (fine grid step 0.001 for every decision change). Decisions are recomputed with the frozen beta-binomial tail and the frozen graph procedure (primary graph weight on P1N 0.78, family-wise level 0.025; secondary graph, five qualifiers). Frozen decisions are those at rho = 0.03 and stay as they are.

Stored positive counts out of 40: primary nodes P1N 22, P1S 19, P2 18, P3 20, K1 20, K2N 29, K2S 19; outside the graphs P1_rev 20, K2_rev 16, R1 at g1: PINN-KAN vs persistence 40, K1 tier S, unadjusted 14, NC-2 permuted stress 28, PC-3 PINN-KAN vs persistence at g4 39.

Table A. Every gated test at each printed rho (rejections in the graph; `none` = no node rejected). Critical counts are the smallest positive counts out of 40 rejecting at the stated level.

| rho | label | design effect | critical count at 0.0195 / 0.0055 / 0.005 | primary graph rejections | secondary graph rejections |
|---|---|---|---|---|---|
| 0.0000 | independence (binomial) | 1.00 | 27 / 29 / 29 | none | N3, N5, S3 |
| 0.0074 | frozen-code conversion of the within-fold estimate (60/780); NOT validated as a like-for-like estimate | 1.29 | 28 / 30 / 30 | none | N3, N5 |
| 0.0100 |  | 1.39 | 29 / 30 / 30 | none | N3, N5 |
| 0.0200 |  | 1.78 | 30 / 31 / 32 | none | N5 |
| 0.0300 | frozen assumption (reproduction check) | 2.17 | 30 / 32 / 33 | none | none |
| 0.0400 |  | 2.56 | 31 / 33 / 33 | none | none |
| 0.0500 | top of the frozen grid | 2.95 | 32 / 34 / 34 | none | none |
| 0.0600 |  | 3.34 | 33 / 35 / 35 | none | none |
| 0.0700 |  | 3.73 | 33 / 35 / 36 | none | none |
| 0.0800 |  | 4.12 | 34 / 36 / 36 | none | none |
| 0.0900 |  | 4.51 | 34 / 37 / 37 | none | none |
| 0.0968 | within-fold intra-group estimate applied to ALL pairs (over-states; labelled so) | 4.77 | 35 / 37 / 37 | none | none |
| 0.1000 |  | 4.90 | 35 / 37 / 37 | none | none |
| 0.1100 |  | 5.29 | 35 / 38 / 38 | none | none |
| 0.1200 |  | 5.68 | 36 / 38 / 38 | none | none |
| 0.1300 |  | 6.07 | 36 / 38 / 38 | none | none |
| 0.1400 |  | 6.46 | 37 / 39 / 39 | none | none |
| 0.1500 | grid point | 6.85 | 37 / 39 / 39 | none | none |
| 0.1600 |  | 7.24 | 37 / 39 / 39 | none | none |
| 0.1700 |  | 7.63 | 38 / 39 / 40 | none | none |
| 0.1800 |  | 8.02 | 38 / 40 / 40 | none | none |
| 0.1900 |  | 8.41 | 38 / 40 / 40 | none | none |
| 0.2000 | grid point | 8.80 | 38 / 40 / 40 | none | none |
| 0.2100 |  | 9.19 | 39 / 40 / 40 | none | none |
| 0.2200 |  | 9.58 | 39 / 40 / 40 | none | none |
| 0.2300 |  | 9.97 | 39 / 41 / 41 | none | none |
| 0.2400 |  | 10.36 | 39 / 41 / 41 | none | none |
| 0.2500 |  | 10.75 | 40 / 41 / 41 | none | none |
| 0.2600 |  | 11.14 | 40 / 41 / 41 | none | none |
| 0.2668 | frozen-code conversion of the within-fold upper limit; rests mainly on a 3-laboratory term | 11.40 | 40 / 41 / 41 | none | none |
| 0.2700 |  | 11.53 | 40 / 41 / 41 | none | none |
| 0.2800 |  | 11.92 | 40 / 41 / 41 | none | none |
| 0.2900 |  | 12.31 | 40 / 41 / 41 | none | none |
| 0.3000 | grid point | 12.70 | 40 / 41 / 41 | none | none |
| 0.4359 | within-fold upper limit applied to ALL pairs (over-states; labelled so) | 18.00 | 41 / 41 / 41 | none | none |
| 0.5000 | end of swept range | 20.50 | 41 / 41 / 41 | none | none |

Table B. Tests outside the graphs and the reverse-direction checks at each printed rho: positives out of 40, p-value, decision at the stated level (R = rejected).

| rho | P1_rev (outside graph, level 0.025) | K2_rev (outside graph, level 0.025) | R1 at g1: PINN-KAN vs persistence (outside graph, level 0.025) | K1 tier S, unadjusted (level 0.025, descriptive) | NC-2 permuted stress (level 0.025, interpretive) | PC-3 PINN-KAN vs persistence at g4 (level 0.025, reported check) |
|---|---|---|---|---|---|---|
| 0.0000 | 20: p = 0.563, - | 16: p = 0.923, - | 40: p = 9.09e-13, R | 14: p = 0.981, - | 28: p = 0.00829, R | 39: p = 3.73e-11, R |
| 0.0074 | 20: p = 0.555, - | 16: p = 0.894, - | 40: p = 8.63e-11, R | 14: p = 0.965, - | 28: p = 0.0176, R | 39: p = 2.27e-09, R |
| 0.0100 | 20: p = 0.553, - | 16: p = 0.886, - | 40: p = 2.75e-10, R | 14: p = 0.96, - | 28: p = 0.0213, R | 39: p = 6.42e-09, R |
| 0.0200 | 20: p = 0.546, - | 16: p = 0.855, - | 40: p = 8.41e-09, R | 14: p = 0.938, - | 28: p = 0.0372, - | 39: p = 1.38e-07, R |
| 0.0300 | 20: p = 0.542, - | 16: p = 0.829, - | 40: p = 8.84e-08, R | 14: p = 0.917, - | 28: p = 0.0539, - | 39: p = 1.12e-06, R |
| 0.0400 | 20: p = 0.538, - | 16: p = 0.808, - | 40: p = 5.07e-07, R | 14: p = 0.898, - | 28: p = 0.0705, - | 39: p = 5.28e-06, R |
| 0.0500 | 20: p = 0.535, - | 16: p = 0.789, - | 40: p = 1.98e-06, R | 14: p = 0.88, - | 28: p = 0.0865, - | 39: p = 1.75e-05, R |
| 0.0600 | 20: p = 0.533, - | 16: p = 0.773, - | 40: p = 5.95e-06, R | 14: p = 0.863, - | 28: p = 0.102, - | 39: p = 4.58e-05, R |
| 0.0700 | 20: p = 0.531, - | 16: p = 0.759, - | 40: p = 1.48e-05, R | 14: p = 0.848, - | 28: p = 0.116, - | 39: p = 0.000101, R |
| 0.0800 | 20: p = 0.529, - | 16: p = 0.747, - | 40: p = 3.21e-05, R | 14: p = 0.834, - | 28: p = 0.129, - | 39: p = 0.000197, R |
| 0.0900 | 20: p = 0.528, - | 16: p = 0.736, - | 40: p = 6.25e-05, R | 14: p = 0.821, - | 28: p = 0.142, - | 39: p = 0.000349, R |
| 0.0968 | 20: p = 0.527, - | 16: p = 0.729, - | 40: p = 9.33e-05, R | 14: p = 0.813, - | 28: p = 0.15, - | 39: p = 0.000492, R |
| 0.1000 | 20: p = 0.526, - | 16: p = 0.726, - | 40: p = 0.000112, R | 14: p = 0.81, - | 28: p = 0.154, - | 39: p = 0.000573, R |
| 0.1100 | 20: p = 0.525, - | 16: p = 0.716, - | 40: p = 0.000186, R | 14: p = 0.799, - | 28: p = 0.165, - | 39: p = 0.000886, R |
| 0.1200 | 20: p = 0.524, - | 16: p = 0.708, - | 40: p = 0.000293, R | 14: p = 0.788, - | 28: p = 0.176, - | 39: p = 0.0013, R |
| 0.1300 | 20: p = 0.523, - | 16: p = 0.7, - | 40: p = 0.000441, R | 14: p = 0.779, - | 28: p = 0.186, - | 39: p = 0.00184, R |
| 0.1400 | 20: p = 0.522, - | 16: p = 0.693, - | 40: p = 0.000638, R | 14: p = 0.77, - | 28: p = 0.195, - | 39: p = 0.0025, R |
| 0.1500 | 20: p = 0.521, - | 16: p = 0.686, - | 40: p = 0.000893, R | 14: p = 0.761, - | 28: p = 0.204, - | 39: p = 0.00331, R |
| 0.1600 | 20: p = 0.52, - | 16: p = 0.68, - | 40: p = 0.00121, R | 14: p = 0.753, - | 28: p = 0.213, - | 39: p = 0.00427, R |
| 0.1700 | 20: p = 0.52, - | 16: p = 0.674, - | 40: p = 0.00161, R | 14: p = 0.745, - | 28: p = 0.221, - | 39: p = 0.0054, R |
| 0.1800 | 20: p = 0.519, - | 16: p = 0.669, - | 40: p = 0.00209, R | 14: p = 0.738, - | 28: p = 0.229, - | 39: p = 0.00669, R |
| 0.1900 | 20: p = 0.518, - | 16: p = 0.663, - | 40: p = 0.00266, R | 14: p = 0.731, - | 28: p = 0.236, - | 39: p = 0.00816, R |
| 0.2000 | 20: p = 0.518, - | 16: p = 0.658, - | 40: p = 0.00332, R | 14: p = 0.725, - | 28: p = 0.243, - | 39: p = 0.0098, R |
| 0.2100 | 20: p = 0.517, - | 16: p = 0.654, - | 40: p = 0.00409, R | 14: p = 0.719, - | 28: p = 0.25, - | 39: p = 0.0116, R |
| 0.2200 | 20: p = 0.517, - | 16: p = 0.649, - | 40: p = 0.00498, R | 14: p = 0.713, - | 28: p = 0.257, - | 39: p = 0.0136, R |
| 0.2300 | 20: p = 0.516, - | 16: p = 0.645, - | 40: p = 0.00598, R | 14: p = 0.707, - | 28: p = 0.263, - | 39: p = 0.0158, R |
| 0.2400 | 20: p = 0.516, - | 16: p = 0.641, - | 40: p = 0.00711, R | 14: p = 0.701, - | 28: p = 0.269, - | 39: p = 0.0182, R |
| 0.2500 | 20: p = 0.515, - | 16: p = 0.637, - | 40: p = 0.00837, R | 14: p = 0.696, - | 28: p = 0.275, - | 39: p = 0.0208, R |
| 0.2600 | 20: p = 0.515, - | 16: p = 0.633, - | 40: p = 0.00976, R | 14: p = 0.691, - | 28: p = 0.281, - | 39: p = 0.0235, R |
| 0.2668 | 20: p = 0.515, - | 16: p = 0.631, - | 40: p = 0.0108, R | 14: p = 0.688, - | 28: p = 0.284, - | 39: p = 0.0255, - |
| 0.2700 | 20: p = 0.514, - | 16: p = 0.63, - | 40: p = 0.0113, R | 14: p = 0.686, - | 28: p = 0.286, - | 39: p = 0.0264, - |
| 0.2800 | 20: p = 0.514, - | 16: p = 0.626, - | 40: p = 0.013, R | 14: p = 0.681, - | 28: p = 0.291, - | 39: p = 0.0295, - |
| 0.2900 | 20: p = 0.514, - | 16: p = 0.623, - | 40: p = 0.0148, R | 14: p = 0.677, - | 28: p = 0.296, - | 39: p = 0.0328, - |
| 0.3000 | 20: p = 0.513, - | 16: p = 0.62, - | 40: p = 0.0167, R | 14: p = 0.672, - | 28: p = 0.301, - | 39: p = 0.0362, - |
| 0.4359 | 20: p = 0.509, - | 16: p = 0.584, - | 40: p = 0.0589, - | 14: p = 0.623, - | 28: p = 0.358, - | 39: p = 0.0974, - |
| 0.5000 | 20: p = 0.508, - | 16: p = 0.571, - | 40: p = 0.0889, - | 14: p = 0.604, - | 28: p = 0.379, - | 39: p = 0.134, - |

Table C. p-values of the seven primary graph nodes (stored positives) at each printed rho; node levels start at 0.0195 for P1N and 0.0055 for K1, all others 0 until a rejection.

| rho | P1N (22) | P1S (19) | P2 (18) | P3 (20) | K1 (20) | K2N (29) | K2S (19) |
|---|---|---|---|---|---|---|---|
| 0.0000 | 0.3179 | 0.6821 | 0.7852 | 0.5627 | 0.5627 | 0.003213 | 0.6821 |
| 0.0074 | 0.3391 | 0.6609 | 0.7556 | 0.555 | 0.555 | 0.008254 | 0.6609 |
| 0.0100 | 0.345 | 0.655 | 0.7472 | 0.5529 | 0.5529 | 0.01048 | 0.655 |
| 0.0200 | 0.3632 | 0.6368 | 0.7204 | 0.5464 | 0.5464 | 0.02095 | 0.6368 |
| 0.0300 | 0.3765 | 0.6235 | 0.7003 | 0.5417 | 0.5417 | 0.03326 | 0.6235 |
| 0.0400 | 0.3869 | 0.6131 | 0.6844 | 0.5381 | 0.5381 | 0.0464 | 0.6131 |
| 0.0500 | 0.3952 | 0.6048 | 0.6714 | 0.5353 | 0.5353 | 0.05978 | 0.6048 |
| 0.0600 | 0.4022 | 0.5978 | 0.6604 | 0.5329 | 0.5329 | 0.07302 | 0.5978 |
| 0.0700 | 0.4081 | 0.5919 | 0.6511 | 0.5309 | 0.5309 | 0.08592 | 0.5919 |
| 0.0800 | 0.4132 | 0.5868 | 0.643 | 0.5291 | 0.5291 | 0.09838 | 0.5868 |
| 0.0900 | 0.4176 | 0.5824 | 0.6358 | 0.5276 | 0.5276 | 0.1104 | 0.5824 |
| 0.0968 | 0.4204 | 0.5796 | 0.6314 | 0.5267 | 0.5267 | 0.1182 | 0.5796 |
| 0.1000 | 0.4216 | 0.5784 | 0.6295 | 0.5263 | 0.5263 | 0.1218 | 0.5784 |
| 0.1100 | 0.4251 | 0.5749 | 0.6237 | 0.5251 | 0.5251 | 0.1328 | 0.5749 |
| 0.1200 | 0.4283 | 0.5717 | 0.6185 | 0.524 | 0.524 | 0.1433 | 0.5717 |
| 0.1300 | 0.4313 | 0.5687 | 0.6138 | 0.523 | 0.523 | 0.1533 | 0.5687 |
| 0.1400 | 0.4339 | 0.5661 | 0.6094 | 0.5221 | 0.5221 | 0.1629 | 0.5661 |
| 0.1500 | 0.4364 | 0.5636 | 0.6054 | 0.5212 | 0.5212 | 0.1721 | 0.5636 |
| 0.1600 | 0.4387 | 0.5613 | 0.6017 | 0.5205 | 0.5205 | 0.1809 | 0.5613 |
| 0.1700 | 0.4408 | 0.5592 | 0.5982 | 0.5198 | 0.5198 | 0.1894 | 0.5592 |
| 0.1800 | 0.4428 | 0.5572 | 0.5949 | 0.5191 | 0.5191 | 0.1975 | 0.5572 |
| 0.1900 | 0.4447 | 0.5553 | 0.5918 | 0.5185 | 0.5185 | 0.2053 | 0.5553 |
| 0.2000 | 0.4465 | 0.5535 | 0.5889 | 0.5179 | 0.5179 | 0.2128 | 0.5535 |
| 0.2100 | 0.4481 | 0.5519 | 0.5862 | 0.5173 | 0.5173 | 0.22 | 0.5519 |
| 0.2200 | 0.4497 | 0.5503 | 0.5836 | 0.5168 | 0.5168 | 0.227 | 0.5503 |
| 0.2300 | 0.4512 | 0.5488 | 0.5811 | 0.5163 | 0.5163 | 0.2338 | 0.5488 |
| 0.2400 | 0.4526 | 0.5474 | 0.5788 | 0.5158 | 0.5158 | 0.2403 | 0.5474 |
| 0.2500 | 0.454 | 0.546 | 0.5765 | 0.5153 | 0.5153 | 0.2466 | 0.546 |
| 0.2600 | 0.4553 | 0.5447 | 0.5744 | 0.5149 | 0.5149 | 0.2527 | 0.5447 |
| 0.2668 | 0.4562 | 0.5438 | 0.573 | 0.5146 | 0.5146 | 0.2568 | 0.5438 |
| 0.2700 | 0.4566 | 0.5434 | 0.5723 | 0.5145 | 0.5145 | 0.2587 | 0.5434 |
| 0.2800 | 0.4577 | 0.5423 | 0.5704 | 0.5141 | 0.5141 | 0.2645 | 0.5423 |
| 0.2900 | 0.4589 | 0.5411 | 0.5685 | 0.5137 | 0.5137 | 0.2701 | 0.5411 |
| 0.3000 | 0.46 | 0.54 | 0.5666 | 0.5133 | 0.5133 | 0.2755 | 0.54 |
| 0.4359 | 0.472 | 0.528 | 0.5467 | 0.5093 | 0.5093 | 0.338 | 0.528 |
| 0.5000 | 0.4764 | 0.5236 | 0.5394 | 0.5079 | 0.5079 | 0.3621 | 0.5236 |

Decision changes found on the fine grid (rho from 0 in steps of 0.001). Each line gives the first grid value at which the decision differs from the value one step before; decisions at rho = 0 listed after.

| decision | state at rho = 0 | first grid rho of the change | change |
|---|---|---|---|
| sec:S3 | rejected | 0.004 | rejected to not rejected |
| test:NC-2 permuted stress (level 0.025, interpretive) | rejected | 0.013 | rejected to not rejected |
| sec:N3 | rejected | 0.020 | rejected to not rejected |
| sec:N5 | rejected | 0.030 | rejected to not rejected |
| test:PC-3 PINN-KAN vs persistence at g4 (level 0.025, reported check) | rejected | 0.266 | rejected to not rejected |
| test:R1 at g1: PINN-KAN vs persistence (outside graph, level 0.025) | rejected | 0.336 | rejected to not rejected |

Decisions with no change anywhere on the grid 0.000 to 0.500: 24 decisions. Of these, rejected at rho = 0: none.

Within the primary graph no node is rejected at any rho on the grid (including rho = 0). At rho below the frozen value the secondary graph and the NC-2 check change as listed; they do not enter any tier, state or title.

Note on scope: the frozen dependence table (`dependence_sensitivity.tiers_by_rho`, grid 0.0, 0.01, 0.02, 0.03, 0.05) lists P1, P2, P3, R1_g1, K1, K2 only; it does not contain the qualifier nodes or NC-2, whose decisions at rho below 0.03 are listed above.

### What the two numbers measure

The test assumes an average pairwise correlation of the sign indicators over all C(40, 2) = 780 pairs of conditions (exchangeable beta-binomial; design effect 1 + 39 x rho). The estimate 0.0968 is an intra-group correlation: the correlation between two conditions that share an inner fold (within an outer fold), from a one-way ANOVA of 40 sign indicators on the training side (one-sided 95 % limit 0.4359). It describes same-group pairs only and says nothing directly about pairs that share no group. The two are therefore not on the same scale, and the sentence that the estimate 'exceeds' the assumption compares a within-group figure with an all-pairs average.

The frozen code converts the intra-group estimates to an all-pairs average as (same-fold pairs x rho_fold + same-laboratory pairs x rho_lab) / 780, with negative terms set to zero. The stored result 0.00744 equals 0.0968 x 0.07692; that ratio (0.076923) equals 60/780 (0.076923), i.e. the laboratory term contributed zero because its estimate is negative (-0.0399, upper limit 0.5040). This conversion is NOT validated here and is not offered as a like-for-like value: it assumes pairs in different groups are uncorrelated, adds fold and laboratory pair terms although the pairings overlap, sets a negative laboratory estimate to zero instead of carrying it, and uses inner-CV training-side signs rather than the held-out signs. The upper limit 0.2668 rests mainly on the laboratory term (few laboratories, so a wide limit). The sweep therefore prints 0.00744 only as `frozen-code conversion` and makes no claim that it, or any single value, is the correct counterpart of 0.03; the data neither establish nor exclude 0.03.

## 4. C1: flow-diagram content and practitioner paragraph

Node list (kind: design / gating / reported / result / terminal; use one colour for gating, one for reported-only):

| id | label | kind | content lines |
|---|---|---|---|
| N1 | Data and splits | design | 40 cycling conditions; five outer folds of 8 held-out conditions; contrasts paired by condition ; history m = 8, 16, 32 conditions; check-ups used k = 0, 2, full ; confirmatory cells g1 = (m 8, k 2) and g4 = (m 32, k full) ; endpoint: median over held-out conditions of the condition RMSE ; contrast L_c = ln(S_comparator / S_target) |
| N2 | Gate G | gating | NC-1 label invariance (15 runs checked, maximum difference 0.0) ; PC-1 synthetic recovery ; fail: no title, no claim; pass: continue ; result: gate tripped = False |
| N3 | Controls reported beside the tests (never change a tier) | reported | NC-2 permuted stress: 28 of 40, p = 0.0539, needed 30, not passed (interpretive) ; PC-2 calendar rate monotone in temperature: True ; PC-3 PINN-KAN against persistence at g4: 39 of 40, passed = True |
| N4 | Test | gating | sign test with a fixed design effect (assumed average pairwise sign correlation 0.03; design effect 2.17) ; margins on the log-ratio scale: tier N -0.0953 (10.0 %), tier S +0.0198 (2.0 %) ; 30 of 40 conditions needed at level 0.025 |
| N5 | Graph, one-sided family-wise level 0.025 | gating | chain P: P1 (tier N, then S) -> P2 -> P3; chain K: K1 (tier N) -> K2 (tier N, then S) ; joined by P3 -> K1 and K2S -> P1N; a level passes on only after a rejection ; initial local levels: P1N 0.0195, K1 0.0055 (weight on P1N 0.78) ; second graph for five qualifiers: initial level 0.005 each, family-wise 0.025 |
| N6 | Outputs | gating | states P and K; modifiers M1 to M3; title from one closed table fixed before scoring ; reverse-direction tests and persistence comparisons sit outside the graph (reported) |
| N7 | Reading | reported | tier none = not shown, not equal ; descriptive numbers carry no tier |
| N8 | Outcome reached | result | gate passed ; P1: 22 of 40 positive, 30 needed ; K1: 20 of 40 positive, 32 needed ; states P0 and K=; M1, M2, M3 all false; title T5 |
| N_stop | Stop: no title, no claim | terminal | reached only if the gate fails |

Edge list:

| from | to | label | style |
|---|---|---|---|
| N1 | N2 |  | solid |
| N2 | N4 | pass | solid |
| N2 | N_stop | fail | dashed |
| N1 | N3 | same cells | dashed |
| N4 | N5 | p-values | solid |
| N5 | N6 | rejections | solid |
| N3 | N6 | reported only | dashed |
| N6 | N7 |  | solid |
| N6 | N8 |  | solid |

Practitioner paragraph (93 words):

> How to read the results. Three questions are answered in order. First, the checks for leaked labels and for failed synthetic recovery did not trip. Second, P1 asks whether PINN-KAN is no more than 10 % worse than the best tuned learner at g1: 22 of 40 held-out conditions agreed, 30 were needed, so the comparison is undecided, which is not a finding of equality. Third, K1 asks the same of the extracted law against PINN-KAN at g4: 20 of 40, 32 needed. Persistence was beaten in 40 of 40 conditions at g1.

