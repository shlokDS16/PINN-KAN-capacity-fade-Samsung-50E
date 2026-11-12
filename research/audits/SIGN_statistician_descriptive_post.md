# Sign-off: statistician, descriptive_post (Paper 7), 2026-11-12

Verdict: PASS WITH CONDITIONS

Scope: `runs/stats_frozen/descriptive_post/`. Independent recomputation from run dirs (scratchpad scripts, CPU, one thread; no `data/` file opened). Descriptive items, no tier or test set; I checked arithmetic and provenance, not claim wording beyond the items below.

## Checks

1. SHA256: all 5 files (descriptive_post.py, _addon.py, make_summary.py, descriptive_post.json, SUMMARY.md) match SHA256.json. PASS.
2. Diagnostics (recomputed from `conf_samsung_B_f*_m*/diagnostics.json`): PASS.
   - Band confirmed: PREREG_v4 line 311 "flag outside [0.5, 2] x 0.15"; quantity is `delta_sd_over_tau` (sd of fitted delta_c on training cells / TAU 0.15).
   - A1 lam_res 1e-3 in 12/15 (1e-2 in 3); delta_sd/tau 0.012-0.319, 15/15 below 0.5. A2 0.546-0.846, 0/15 flagged. A4 11/15 at edge (15/15 flagged), A13 9/10 (10/10 flagged), A15 9/10 at edge, G15 10/10 at edge (delta_sd not logged for A15/G15).
   - Test C: A1 lam_res 0.01, edge False, 0.287. S2 (5 runs): 0.01 in all, edge False, 0.215-0.260. Note: SUMMARY says "S2 (4 runs)"; there are 5 S2 run dirs (f0-f4) and I read 5. Fix the count (the range 0.215-0.260 is what SUMMARY prints; I get 0.215-0.260 over 5 folds, so the range is for 5).
   - Inversion: 0 non-converged of 30,800 outer-test inversions; 35 of 286,681 inner-CV inversions non-converged. Match.
3. sqrt(t) baseline: PASS.
   - Fit uses only reference point plus post-reference window points strictly before the first forecast check-up; forecast truths are used only for scoring. No test-period value enters the fit.
   - Recomputed independently: g1 sqrt 1.728, R1 3.390 (reproduces arm_table); g4 sqrt 1.469, R1 2.906. k_eff: 2 for all 140 at g1; 4/3/2 for 136/3/1 at g4. Aggregation (cell RMSE, mean within condition, mean over 40 conditions) is identical to R1's.
   - A1 < sqrt in 35/40 (g1) and 37/40 (g4); A10 < sqrt 29/40 and 37/40; sqrt < R1 40/40 and 37/40; b<0 in 1 cell (g1), 0 (g4). All match. A1 means 0.790 / 0.669 reproduced from condition_scores.
   - Caveat: the baseline's sqrt form was chosen post hoc; it is a yardstick, not a registered comparator. SUMMARY labels it so.
4. Size context: PASS. Recomputed last-check-up retention median 93.22 %, min 83.97 %, fade median 6.78 pp, range 0.98-16.03 pp, 0 cells <= 80 %, forecast span medians 258 d (g1) / 219 d (g4). R_LOO 0.178, R_WARP 0.111 (B) as stated. Minor curiosity: S2 R_WARP equals B's to all digits (0.11076484942758215) while R_LOO differs; probably shared training cells, but not verified.
5. g4 h=1 anomaly (A1 1.90 vs R1 0.69): traced.
   - Fold 2 only (A1 h=1 RMSE 4.36; other folds 0.16-0.43). Within fold 2, one cell causes it: `TP_z02_03_s2` (condition T45|SOCmax0.8|DoD0.6|Cch1|Cdch2, 45 C, 1 C charge, high stress). Its window ends at t = 45 d (5 points, 6.5 pp lost); its first forecast check-up is at t = 433 d, a 388-day gap with no intermediate check-up in the record. Observed retention at 433 d is 90.1 % (fade stalled). A1 ensemble predicts 68.3 % (seeds 63-76 %), A10 75.4 %, R1 93.5 %. A1 error -21.8 pp, A10 -14.7, R1 +3.4. All other cells in fold 2 have |error| <= 3.3 pp.
   - Excluding that cell, pooled A1 h=1 over the other 139 cells is about 0.45 pp (SSE arithmetic from per-fold values), in line with h = 2-3.
   - Classification: a real forecast failure for that cell (consistent across seeds and A10: all trend-extrapolating arms overshoot a fade that plateaued) amplified by a pooling artefact (h = 1 mixes a 388-day horizon with 8-21-day ones; "h" is an index, not time) and by a sparse check-up schedule for this cell (a data-record property, not a data error I can see). It is not a run or code bug.
   - Consequence beyond the horizon table: at g4 this one cell makes condition T45|SOCmax0.8|DoD0.6|Cch1|Cdch2 score A1 5.84 pp (A10 3.44, R1 2.14), and lifts the g4 A1 mean from 0.536 (39 other conditions) to 0.669. At g1 the same condition scores A1 2.09 (A10 2.49, R1 2.59); excluding it moves g1 A1 from 0.790 to 0.756. The headline g4 error is therefore sensitive to one cell/condition. This is a leave-one-condition-out sensitivity I computed ad hoc; it is not in the JSON.

## Conditions for use in the manuscript

- C1. Replace the SUMMARY sentence "I did not trace the cause" with the traced cause above (cell id, 388-d gap, 68 % vs 90 %), or drop the h=1 g4 row/column from any figure. Do not present the h index as a calendar horizon.
- C2. If g4 headline errors (A1 0.669) are quoted, add a one-line sensitivity (condition excluded: 0.536 for A1) as descriptive, or state that one condition contributes 5.84 pp. It sets no tier.
- C3. Correct "S2 (4 runs)" to 5 runs. Note that delta_sd/tau is not logged for A15/G15, and that the lower-edge/shrinkage pattern is not by itself evidence the law is wrong.
- C4. Keep item 5 (sqrt baseline) labelled exploratory/post hoc, out of the title, abstract and highlights; no claim that A1 "beats" it (descriptive counts only, no interval).
- C5. The pooled horizon tables (item 2) were not fully recomputed by me beyond the h=1 per-fold values and fold-level pooling arithmetic; the script is the source for the other horizons.

Files: scripts in scratchpad (`v.py`, `h1.py`, `h2.py`); nothing in MAIN other than this report was written.
