# P3 result: headroom on training folds only (2026-11-04/05)

Judge rule (D010 section 7, P3): inner-CV error of the best flexible learner (tuned GP-ARD or LightGBM) divided by the
replicate floor. **> 1.2: superiority winnable. <= 1.2: the primary contrast (iii) on that dataset is preregistered as
non-inferiority.**

## Verdict
| Dataset (primary window) | ratio, judge-literal (fold mean) | pooled-condition 95 % CI (cluster bootstrap, 10,000) | like-for-like (mean/mean) | verdict |
|---|---|---|---|---|
| ISU-ILCC, W = 4 weeks | **0.90** (folds 0.82-1.04) | 0.90 [0.78, 1.08] | 0.83 | **non-inferiority** |
| SNL, W = 100 cycles | **1.13** (folds 0.96-1.34; two folds above 1.2) | 1.11 [0.81, 1.62] | 1.04 | **non-inferiority** (weak: CI straddles 1.2) |

Sensitivity (same code, other window): ISU W = 6 weeks 0.79 [0.68, 0.98]; SNL W = 200 cycles 0.93 [0.65, 1.35].
Both datasets give non-inferiority under every window run. The data cannot support a superiority claim over the best
data-only learner on ISU; on SNL the primary-window point estimate (1.13) is close enough to 1.2, and the interval wide
enough, that superiority is not excluded by this pilot, but the preregistered rule says non-inferiority.
**Preregister contrast (iii) as non-inferiority on both, with the margin of the next section.**

## Numbers (pp = percentage points of retention; condition-averaged cell RMSE; mean over 5 outer training folds)
| | ISU W4 | ISU W6 | SNL W100 | SNL W200 |
|---|---|---|---|---|
| persistence (r at window end) | 13.22 | 12.54 | 10.83 | 7.71 |
| per-cell power law, tuned exponent bounds | 6.67 | 6.30 | 4.67 | 3.72 |
| GP-ARD, tuned | 5.24 | 5.04 | 3.33 | 2.93 |
| LightGBM, tuned | 5.21 | 4.87 | 2.97 | 2.54 |
| best flexible (per fold min of GP, LGBM) | 5.13 | 4.86 | 2.97 | 2.54 |
| replicate floor, median over conditions (judge margin) | 5.75 | 6.17 | 2.62 | 2.74 |
| replicate floor, mean over conditions | 6.19 | 6.69 | 2.85 | 2.99 |

Ratios to the median floor: power law 1.17 / 1.03 / 1.78 / 1.36; GP 0.92 / 0.82 / 1.27 / 1.07; LightGBM 0.91 / 0.79 / 1.13 / 0.93.
Best learner per fold: LightGBM in 3 of 5 folds (ISU W4), 5 of 5 (SNL). Re-scoring the selected configurations on a second
inner partition (selection-bias check) moves the ratio by 0.00 / +0.06 / -0.01 / +0.03 (ISU W4, ISU W6, SNL W100, SNL W200).

**Margin to carry forward (rule of section 6, computed on training conditions only):** replicate floor, median over
training conditions, mean of the five outer training folds: **ISU W4 5.75 pp** (folds 5.10-6.09; 48-50 multi-replicate
conditions per fold), **SNL W100 2.62 pp** (folds 2.39-2.76; 15-17 conditions per fold). These are pilot values; the
confirmatory margin must be recomputed with the frozen window and forecast set.

## Design as run (fixed in code before results; pilot choices marked P)
- **Splits** (committed first, `splits:` commit 16a9da4): `runs/splits/{isu,snl}_testB.json` (held-out conditions, 5 folds) and
  `{isu,snl}_testA.json` (held-out replicate cells, 4 folds); seeds ISU 20261104 (B) / 20261105 (A), SNL 20261105 (B) / 20261106 (A);
  README in that folder. ISU: 63 conditions (folds of 12-13); k-means (13 clusters on standardised charge C, discharge C, DoD)
  gives stress-space neighbourhoods whose members are dealt to different folds. SNL: 23 chemistry x temperature x SOC window
  x charge C x discharge C condition groups (unique tuples in `snl_cells.csv`, 1-4 cells each, 3 of them single-cell), folds
  of 4-5; blocks of 5 stress neighbours inside a chemistry dealt to different folds. Chemistries are pooled in the split and
  in the learners (chemistry one-hot) because 7-8 conditions per chemistry cannot support 5 outer x 3 inner folds.
  P: 5 outer folds for ISU (judge, section 6) instead of the proposal's 7.
- **Task** (proposal section 6 wording; judge: ISU/SNL are the Test B analogue): inputs stress vector, Q0 (retention is
  relative to the cell's first check-up), check-ups inside window W; output retention at every later check-up up to and
  including the first one below 70 %; per-cell RMSE (pp), mean within condition, then over conditions. P: ISU W = 4 weeks
  (primary), 6 (sensitivity); SNL check-ups = every 25th cycle (1, 26, 51, ...), W = 100 cycles (primary), 200 (sensitivity).
  `runs/prereg/` did not exist, so these values are pilot choices, not preregistered. Cells with no forecast point (life ends
  inside the window) are excluded and counted: ISU 7 of 251 (W4), 13 of 251 (W6); SNL none. SNL rows with capacity <= 0.05 Ah
  dropped (P1 caveat).
- **Replicate floor:** for each cell, RMSE of the mean trajectory of the other replicates of its condition (linear
  interpolation in time; replicates not reaching that time skipped), evaluated at the cell's forecast times; mean over the
  condition's replicates; median over the training conditions with >= 2 replicates (judge, section 6). Inside each outer
  training set only.
- **Learners, inner grouped CV by condition (3 folds, one partition shared by all learners), equal tuning budget = 20 Optuna
  TPE trials per learner per outer fold** (search seed 7*seed+fold with seed 1; one search seed only). GP-ARD (scikit-learn; ARD
  Matern 1.5/2.5 or RBF + white noise; tuned: kernel family, rows per cell 3/4/6, linear or log time, full or minimal feature
  set, noise lower bound; L-BFGS-B capped at 60 iterations). LightGBM (n_estimators, learning rate, leaves, min child
  samples, subsample, colsample, L2, optional monotone constraint in time, linear or log time; rows weighted so every cell counts
  once). Per-cell power law r = 1 - a t^b fitted to the window (a closed form, b on a 41-point grid inside tuned bounds),
  extrapolated. Persistence as reference. Features: stress vector, window summary (r at window end, r at first check-up,
  window slope, curvature, window end time), time since window end. Target: drop since window end. CPU only, 1 thread per
  process; four runs took about 4,600 CPU-s (ISU W4 2,370 s, W6 1,800 s, SNL 200-215 s each); memory not measured (frames of
  at most 100k rows).
- **Selection:** best flexible learner per outer fold = lower inner-CV error of GP and LightGBM at its best trial; ratio per
  fold, then averaged. Pooled-condition CI: cluster bootstrap over training conditions (condition error = mean over the outer
  folds in which it was a training condition; the floor per condition does not depend on the training set). The bootstrap
  conditions on the fixed splits and one search seed; folds overlap in training conditions, so fold ratios are not independent.

## Cautions for the paper and the preregistration
1. **The replicate floor is not a lower bound.** The learners see the held-out cell's own window, the floor does not, so ratios
   below 1 occur (ISU 0.8-0.9). The 1.2 rule therefore gates "is there anything left to win over a tuned data-only learner";
   the answer is no on ISU and not clearly on SNL.
2. The judge's floor is a median over conditions; the learner error is a mean over conditions (primary endpoint). Judge-literal
   and like-for-like ratios are both shown; the verdict is the same on every row (1.13 vs 1.04 on SNL W100).
3. Mean errors are 5.1 pp (ISU) and 3.0 pp (SNL): this is forecasting, not estimation. ISU replicate spread alone is about 5.8 pp.
4. SNL W100 is the only row near the threshold: folds 1 and 2 give 1.29 and 1.34; pooled CI [0.81, 1.62]. A superiority claim
   there would need the confirmatory run, not this pilot. Tuned optima at search-space edges were not checked.
5. One search seed; seed spread of the ratio not estimated (5 seeds belong to the confirmatory runs).
6. ISU and SNL have no storage arm; this pilot says nothing about Samsung.

## Test-fold guard (required line)
**No outer test fold (the conditions and cells listed in `runs/splits/*_testB.json`, `folds[f].test_cells`) was read,
predicted or scored.** Enforcement in `code/pilots/p3_headroom.py`, `main()`: for each outer fold the frame is filtered with
`train = full[~full.cell.isin(test_cells)]` before any feature, floor or model code runs; assertions check that no train cell
or condition belongs to the fold's test cells/conditions; every later function (`build_cells`, `replicate_floor`, `tune`)
receives only objects derived from `train`; no model is refit or applied outside inner CV (the verdict is inner-CV only);
after the loop the split-file hash is recomputed and asserted unchanged. The per-run audit in `results.json` -> `audit`
records `intersection_within_fold: 0`, `test_fold_scored: false` and the split SHA-256. Limit of the enforcement: the processed
CSV is read whole into memory before the filter (the test rows are dropped, not inspected). Test A splits were fixed but not used.

## Files
`code/pilots/p3_headroom.py` (sha256 cda0bd3f...ca5966 at run time), `code/pilots/p3_make_splits.py`; per run
`runs/pilot_P3/<ds>_W<w>/{config.json,results.json,condition_level.csv}`; logs `log_*.txt`. Reproduce:
`CUDA_VISIBLE_DEVICES= .venv/Scripts/python.exe -P code/pilots/p3_headroom.py . isu 4 20 1` (then `snl 100`, `isu 6`, `snl 200`).
`config.json` records the HEAD commit at launch (61bb730); the code file was committed afterwards with unchanged content
(sha above); the commit of this result carries the prefix "P3:".
