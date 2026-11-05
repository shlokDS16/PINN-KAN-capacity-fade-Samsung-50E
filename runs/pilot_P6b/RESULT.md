# P6b result: four against two inner folds at m = 8 (D020 judge section 4, rule R2')

**All numbers below: development data (ISU), not evidence for Samsung.** Non-confirmatory. ISU is not blind (PREREG 3.4); if ISU later becomes primary, this pilot is part of the ISU development exposure (judge section 4).

## Verdict
**KEEP 2 inner folds for m in {8, 16}** (`decision.json`: `"adopt": false`). Four of six arms have q > 0 (A4, A9, A11, A12); the rule needs at least five. The floor condition (min q > -ln(1.02) = -0.0198) is met (min q = -0.0088, A1), so the first condition alone decides. All 60 units finished; no failed unit, no failed tuning trial, no non-finite seed forecast.

## What was run
- ISU Test B (`runs/splits/isu_testB.json`, sha256 identical before and after). Five outer folds; the outer-test conditions (12-13 per fold) and cells were never loaded (`fold_audit.json`: intersection 0 with conditions and cells, `test_fold_scored: false`, fold hash ok).
- Pseudo-train: the nested max-min subset of 8 of the fold's 51 training conditions. Pseudo-test: the other 42-43 conditions (171 cells in fold 0). Window W = 2 weeks, as `run.py` does at m < 32. 63 conditions in total, 43 pooled over folds for the median.
- Arms A1, A2, A4 (= AG at m < 32), A9, A11, A12; N = 20 TPE trials (sampler seed = fold, tuning seed 1000 + fold); final refits seeds 0-4; inner_k in {2, 4}; the backbone tournament was run per (fold, inner_k) on the pseudo-train (it chose self_limiting in every cell I looked at in the log).
- Endpoint: ensemble score (mean of the five refit forecasts, non-finite values replaced seed-wise by persistence before averaging). The per-seed score is the descriptive row. Every cell had RMSE(ensemble) <= mean per-seed RMSE (checked per unit).
- Rule R2' was applied by `aggregate` of the committed script; nobody chose the verdict. Script commit `93e478403a862c3e73465857a3a53c739f131425`, committed (10:59:43) before the first fit (10:59:58 start; first jobs began after). Script sha256 unchanged at the end.
- Mechanics smoke test before the commit: 1 fold, 2 trials, 2 seeds, steps_scale 0.02, in a scratch directory outside `runs/` (only to find bugs; its numbers were not used). It exposed one table-formatting bug, fixed before the commit.
- The lead's file contract asked for a boolean `adopt` key in `decision.json`. The script was not changed (a change after the first fit is a D020 re-open condition). `code/pilots/p6b_add_adopt_key.py` (commit 88e91eb) derives the key mechanically from `verdict` and `complete`; nothing was edited by hand.

### Table A. Rule R2' (development data, ISU: not evidence for Samsung)

| arm | q_a (ensemble endpoint) | bootstrap 95 % (descriptive) | q_a (per-seed endpoint, descriptive) | q_a > 0 |
|---|---|---|---|---|
| A1 | -0.00882 | [-0.0189, 0.0146] | -0.00651 | no |
| A2 | -0.00604 | [-0.0100, -0.0006] | -0.00412 | no |
| A4 | 0.06351 | [-0.0041, 0.0919] | 0.06092 | yes |
| A9 | 0.06438 | [0.0393, 0.1164] | 0.05198 | yes |
| A11 | 0.00322 | [-0.0608, 0.0421] | 0.00322 | yes |
| A12 | 0.02681 | [0.0098, 0.0545] | 0.02888 | yes |

Verdict: **KEEP_2_INNER_FOLDS**. 4 of 6 arms with q > 0 (need >= 5); min q = -0.00882 against floor -0.01980 -> KEEP two inner folds.

Floor -ln(1.02) = -0.01980; arms with q > 0: 4 of 6; min q = -0.00882.

### Table B. Per-fold median ln(S_2fold / S_4fold) over the fold's pseudo-test conditions (ensemble endpoint)

| arm | fold 0 | fold 1 | fold 2 | fold 3 | fold 4 |
|---|---|---|---|---|---|
| A1 | -0.1087 | 0.0098 | 0.0319 | 0.1248 | -0.0956 |
| A2 | -0.0003 | -0.0035 | -0.0226 | -0.0008 | 0.0022 |
| A4 | 0.3277 | -0.0405 | 0.0042 | 0.0000 | 0.0031 |
| A9 | -0.1915 | 0.0954 | 0.4944 | 0.0000 | -0.1372 |
| A11 | -0.3178 | 0.2211 | 0.0000 | 0.0687 | -0.1817 |
| A12 | -0.0173 | 0.0032 | 0.1449 | -0.0033 | 0.0286 |

### Table C. Mean cross-condition ensemble score (pp), mean over folds; seed SD of the cross-condition mean (pp); median ln(per-seed / ensemble) score

| arm | S 2-fold | S 4-fold | seed SD 2 | seed SD 4 | median ln(per-seed/ens) 2 | 4 | grid-edge share 2 | 4 | failed trials 2/4 | non-finite seed values 2/4 |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 | 5.486 | 5.517 | 0.249 | 0.328 | 0.0280 | 0.0361 | 0.40 | 0.32 | 0/0 | 0/0 |
| A2 | 7.731 | 7.810 | 0.102 | 0.080 | 0.0016 | 0.0002 | 0.55 | 0.45 | 0/0 | 0/0 |
| A4 | 6.233 | 5.892 | 0.281 | 0.281 | 0.0222 | 0.0243 | 0.13 | 0.20 | 0/0 | 0/0 |
| A9 | 14.397 | 12.896 | 2.403 | 2.121 | 0.0645 | 0.0855 | 0.50 | 0.50 | 0/0 | 0/0 |
| A11 | 6.646 | 6.852 | 0.000 | 0.000 | 0.0000 | 0.0000 | 0.00 | 0.40 | 0/0 | 0/0 |
| A12 | 6.123 | 5.916 | 0.057 | 0.038 | 0.0019 | 0.0010 | 0.12 | 0.08 | 0/0 | 0/0 |

### Table D. A1 against D* (inner-CV choice of A9, A11, A12 per fold and variant), ensemble endpoint, descriptive, non-binding

| variant | D* by fold | median ln(S_D* / S_A1) | share of conditions where A1 is better | conditions |
|---|---|---|---|---|
| 2-fold | 0:A11, 1:A12, 2:A12, 3:A12, 4:A12 | 0.0472 | 0.535 | 43 |
| 4-fold | 0:A12, 1:A12, 2:A12, 3:A12, 4:A12 | 0.0538 | 0.605 | 43 |

### Table E. Inversion-convergence diagnostic (seed-0 refit, pseudo-test windows W = 2 weeks; no rule attached)

| arm, variant | folds | grad norm initial (median) | grad norm final (median) | grad norm final (max) | final/initial (median) | final/initial (max) | spread over 4 inits, pp (median) | spread pp (max cell, max fold) | change when steps are doubled, pp (max) | score range over inits, pp (max) | replica vs production, pp (max) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 k=2 | 5 | 3.07e+04 | 25.1 | 6.9e+03 | 0.000726 | 0.321 | 7.3381 | 129.8795 | 4.5790 | 4.3867 | 0.00e+00 |
| A1 k=4 | 5 | 3.13e+04 | 39.2 | 5.53e+03 | 0.000328 | 3.34 | 7.5868 | 113.1600 | 8.1174 | 1.7198 | 0.00e+00 |
| A2 k=2 | 5 | 128 | 1.48e-05 | 0.000473 | 1.13e-07 | 0.00044 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.00e+00 |
| A2 k=4 | 5 | 141 | 1.53e-05 | 0.000485 | 9.98e-08 | 3.13e-05 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.00e+00 |
| A9 k=2 | 5 | 15.4 | 0.015 | 34.2 | 0.00144 | 2.68 | 5.1740 | 127.8337 | 42.2590 | 2.9334 | 0.00e+00 |
| A9 k=4 | 5 | 15.6 | 0.0278 | 7.16 | 0.000425 | 4.11 | 0.8710 | 130.7075 | 20.8982 | 3.1717 | 0.00e+00 |

### Table F. Run facts

- CPU hours (sum over units, tournaments and error files): 5.647; wall hours: 2.889; units complete: True.
- split sha256 before = after: True (c1227642a067e61c4e5110d577e0b84b6ccb6da1cd8e4b48b16e03b2ba4419d8).
- script commit: 93e478403a862c3e73465857a3a53c739f131425 (committed 2026-11-05T10:59:43+05:45); script sha256 unchanged since the first fit: True.
- pinnkan files whose content changed between the start and the end of the run: ['arms.py', 'guard.py', 'metrics.py', 'negcontrol.py', 'pinn.py', 'run.py', 'semi.py', 'stats_rows.py', 'stats_step.py', 'stats_v4.py', 'tuning.py'].
- tuned per fold: pseudo-train conditions = 8; pseudo-test conditions per fold: f0: 43, f1: 42, f2: 43, f3: 42, f4: 42.

## Reading (descriptive)
- Effect sizes are small. A1 and A2 do slightly worse with four folds (q = -0.009, -0.006; for A2 the descriptive bootstrap interval excludes 0); A4 and A9 gain about 6 %; A12 gains 2.7 %; A11 is flat (+0.3 %). Per-fold signs flip for A1, A9 and A11 (Table B), so folds disagree, as expected with validation folds of 2 conditions.
- The bootstrap intervals (resampling the pooled conditions, 5000 draws) are descriptive and ignore the dependence between conditions of the same fold.
- Table D: with either variant, A1 is not clearly better than D*: the median ln(S_D*/S_A1) is +0.047 (2-fold) and +0.054 (4-fold), A1 better in 54 % and 61 % of conditions. Non-binding signal for Shlok (the P6 reading of J16 5.6); D* was chosen by inner CV only.
- The per-seed against ensemble gap (median ln ratio 0.028 to 0.086 for A1, A4, A9) is where C1 helps; A11 has no seed variance, A2 and A12 almost none.
- Grid-edge share (Table C) is 0.3 to 0.55 for A1, A2, A9: selected configurations often sit on the end of an ordered grid in both variants.

## Inversion-convergence diagnostic (Table E; no rule attached)
- A2 (delta only): converged. Final gradient norm about 1e-5, four starting points give identical forecasts, doubling the steps changes nothing.
- A1 and A9 (z, and delta for A1): **not converged by this measure.** The gradient norm falls by three to four orders of magnitude from its start, but the median spread of the forecast across the production start and three random starts (z ~ N(0, 0.5^2), delta ~ N(0, TAU^2); my design choice, not in the ruling) is 7.3 pp (A1, 2-fold), 7.6 pp (A1, 4-fold), 5.2 pp (A9, 2-fold), 0.9 pp (A9, 4-fold), with maxima near 113-131 pp for single cells. Doubling the steps changes some forecasts by up to 4.6 to 42 pp. The mean score moves by up to 4.4 pp (A1) and 3.2 pp (A9) across starts. The replica of the production loop reproduces the production forecasts exactly (difference 0).
- Per the ruling, any fix (more steps or starts, equal for every affected arm) needs its own decision row before the freeze; nothing was changed. Caveat: the inversion is non-convex, and random starts at this scale may land in basins the production start never reaches, so the spread is an upper-end indication; the doubled-step column is the cleaner sign that the 200- and 150-step budgets stop early.

## Runtime and budget
CPU 5.65 h (sum over units and tournaments), wall 2.89 h on 2 worker processes (one thread each), start 10:59:58, end 13:53:19. Judge's estimate was about 6 CPU-h; the 8 CPU-h abort guard was not reached. CPU only (`CUDA_VISIBLE_DEVICES=-1`, torch reports no CUDA).

## Limits
- ISU only: 3 stress inputs, no storage, no 5-D stress sparsity; says nothing about C1, C3, Samsung, or the size of A1's advantage there.
- m = 8 only; m = 16 is assumed to follow (disclosed in the ruling).
- Pseudo-test conditions are shared across folds; the median over 43 pooled conditions is not an independent sample.
- Code changed on disk during the run: a coder edited `code/pinnkan/` files (arms, guard, metrics, negcontrol, pinn, run, semi, stats_*, tuning; modification times 11:11 to 12:33) while the run was in progress. The two worker processes had imported all modules used in training and scoring at about 11:00-11:02 and Python does not reload them, so the run used the start-of-run code; the uncommitted state at start was only `arms.py`, `run.py`, `stats_step.py` (scope flags, no behaviour used here). The per-file hashes at start and end are in `run_meta.json`. A reviewer who wants to be certain can re-run the committed script on commit-pinned code.
- Selected configurations differ between variants and often sit on grid edges, so q partly reflects search noise at N = 20.

## Files
`decision.json`, `summary.json`, `tables.md`, `per_condition.csv`, `per_fold_condition.csv`, `fold_audit.json`, `run_meta.json`, `config_used.json`, `RUN.log`, `units/` (one JSON per fold, variant and arm; tournaments).
