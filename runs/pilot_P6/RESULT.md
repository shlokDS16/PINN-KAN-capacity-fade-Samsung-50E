# P6 result: PINN-KAN (A1) against data-only learners at m = 8 on ISU training sides (PREREG_v4 17.2 C6, stop rule 10)

**All numbers below: development data (ISU), not evidence for Samsung.** Non-confirmatory. ISU is not blind (PREREG 3.4). No outer-test condition or cell was loaded (`fold_audit.json`: intersection with outer-test conditions 0, with outer-test cells 0, `test_fold_scored: false`, fold hash ok on all five folds; split sha256 identical before and after).

## Reading by the rule (`RULE.md`, committed 6299c24 before the first fit)
**Stop rule 10 is not triggered** (`decision.json`: `"stop_rule_10_triggered": false`, verdict `NOT_TRIGGERED`). At m = 8, W = 2 weeks (g1 analogue), A1 is lower than D* (side median of the ensemble condition score) on 4 of the 5 outer ISU training sides (folds 0, 1, 2, 4); D* is ahead on 1 of 5 (fold 3). The rule triggers at 3 or more sides with the data-only learner ahead, no margin. The design is not changed on the pilot in either case; nothing is reported to Shlok as a stop signal.

The verdict was produced by `aggregate` of the committed driver. All 30 units finished (6 arms x 5 folds), no failed unit, no failed tuning trial, no non-finite seed forecast; ensemble RMSE <= mean per-seed RMSE in every cell of every unit.

## What was run
- ISU Test B, pseudo-train = nested max-min subset of 8 of each side's 51 training conditions; pseudo-test = the side's other 42-43 conditions (30-33 of them are scored at W = 2, because a cell needs a check-up inside the two-week window; see the conditions column of the paired table). Inner CV: 2 folds, grouped by condition, stratified by temperature, on the 8 pseudo-train conditions only.
- Arms: A1, A2, A4 (physics-informed family); A9, A11, A12 (data-only, the D* candidates). N = 20 TPE trials (sampler seed = fold, tuning seed 1000 + fold), final refits seeds 0-4, `steps_scale` 1.0, ensemble endpoint, backbone tournament per fold (chose self_limiting in all five folds). Tuning and inner CV at W = 2 weeks as `run.py` does at m < 32; the refits were scored at W = 0, 2 and full (4 weeks), the ISU analogues of k = 0, 2, k_full.
- Not run: the A10-analogue of proposal 5.6 (no ISU form in the code base) and the m = 16, 32, all points of the learning curve (the reading is at the smallest m). Deviations from RULE.md: none (the budget rule did not bind: 2.02 CPU-h, no reduction of `n_trials`).
- Script and config commit 6299c24 (committed 2026-11-05 23:19:36 +05:45, run start 23:19:42); script sha256 unchanged. No `code/pinnkan` file changed content between the start and the end of the run (`run_meta.json`) (`pinnkan_dirty` empty at the start of the run).

## Table A. Primary reading: side median of the ensemble condition score (pp), W = 2 weeks, m = 8 (D* marked *)

| arm | fold 0 | fold 1 | fold 2 | fold 3 | fold 4 |
|---|---|---|---|---|---|
| A1 | 4.222 | 4.872 | 4.899 | 4.645 | 5.384 |
| A2 | 6.698 | 6.144 | 6.317 | 5.773 | 6.659 |
| A4 | 7.077 | 4.685 | 5.658 | 4.766 | 5.214 |
| A9 | 14.681 | 10.308 | 19.019 | 8.183 | 11.162 |
| A11 | 5.858* | 7.857 | 6.232 | 5.054 | 6.694 |
| A12 | 5.975 | 5.038* | 6.142* | 4.259* | 6.183* |
| data-only ahead of A1? (D* <= A1) | no | no | no | yes | no |

D* by fold (inner-CV choice on the pseudo-train): A11, A12, A12, A12, A12. Inner-CV condition-mean scores (pp): A9 10.6 / 9.2 / 9.2 / 15.0 / 10.9; A11 6.1 / 6.1 / 5.6 / 6.6 / 6.5; A12 6.9 / 5.1 / 4.4 / 5.8 / 4.6 (folds 0-4).

Paired conditions, A1 against D*, W = 2 (ln(S_D*/S_A1) > 0 means A1 lower on that condition):

| fold | D* | conditions | median ln(D*/A1) | share of conditions with A1 lower |
|---|---|---|---|---|
| 0 | A11 | 33 | 0.180 | 0.636 |
| 1 | A12 | 31 | -0.059 | 0.419 |
| 2 | A12 | 30 | 0.237 | 0.700 |
| 3 | A12 | 30 | -0.093 | 0.300 |
| 4 | A12 | 31 | 0.085 | 0.645 |

Mean over the five sides of the mean condition score (pp), W = 2: A1 5.431, A2 7.731, A4 5.925, A9 14.442, A11 6.646, A12 6.123 (P6b, two inner folds, m = 8: A1 5.486, A2 7.731, A4 6.233, A9 14.397, A11 6.646, A12 6.123).

## Table B. Descriptive readings (attached to no decision): sides with the data-only learner ahead of A1, out of 5

| comparison | W = 0 | W = 2 (primary cell) | W = full (4 weeks) |
|---|---|---|---|
| A1 against D*, median (primary reading) | 1 | 1 | 1 |
| A1 against D*, mean | 3 | 2 | 2 |
| best data-only learner by the side's own median (oracle) | 1 | 1 | 1 |
| A1 against A9 | 0 | 0 | 0 |
| A1 against A11 | 0 | 0 | 0 |
| A1 against A12 | 1 | 1 | 1 |
| best of A1, A2, A4 against D*, median | 1 | 1 | 0 |

One descriptive variant reaches the count of 3: the mean statistic at W = 0 (reference check-up only), where the data-only learner is ahead on 3 of 5 sides. The rule's statistic is the median at W = 2, so this row does not bear on the decision; it is listed because it differs from the primary reading.

## Reading (descriptive)
- At the g1 analogue the five-side count under the pre-set rule is 4 sides with A1 lower and 1 with D* ahead. The other two windows, the oracle comparator and the larger physics family give the same count or a count more favourable to the physics-informed arms, except the W = 0 mean row above.
- At the condition level on a side the comparison is not uniform: the share of conditions with A1 lower runs from 0.30 to 0.70 across sides at W = 2, and the sign of the side median of ln(D*/A1) is negative on folds 1 and 3.
- A9 (data-only network with the same latent) is the weakest arm at every side and window; A12 is the D* on four of five sides.
- The weight of this pilot is limited: five sides that share training conditions, one dataset that is not blind, a pseudo-test frame inside the training side, and no margin in the rule. It is not evidence about Samsung.

## Run facts
- Units complete: True (30 of 30). CPU hours (sum over units and tournaments): 2.021. Wall clock: 9.5 h from first start to last end as logged; the machine was asleep for most of this span (the three workers had used about 11 CPU-minutes each after 9 h of wall time); active wall about 0.8 h (2.02 CPU-h on 3 single-thread processes).
- split sha256 before = after: True (c1227642a067e61c4e5110d577e0b84b6ccb6da1cd8e4b48b16e03b2ba4419d8).
- Files: `RULE.md`, `decision.json`, `summary.json`, `tables.md` (all windows, selected hyperparameters), `per_side_arm.csv`, `fold_audit.json`, `config_used.json`, `run_meta.json`, `RUN.log`, `aggregate.log`, `units/`.
