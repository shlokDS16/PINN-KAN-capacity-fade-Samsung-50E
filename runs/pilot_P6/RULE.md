# Pilot P6: reading rule (written and committed before the first fit)

Development data (ISU), non-confirmatory. ISU is not blind (PREREG 3.4). Nothing here is evidence for Samsung. CPU only. No outer-test condition or cell is loaded.

## Sources of the rule (nothing below is chosen after a result)
- `runs/prereg/PREREG_v4.md` 17.2 C6: "Pilot P6 (ISU, training sides) has been run and its pre-set reading reported to Shlok (J16 5.6; stop rule 10)".
- `runs/prereg/PREREG_v4.md` section 12 rule 10 (stop rule 10), quoted: "if the physics-informed family is not lower than the best data-only learner at the smallest m on a majority of the five outer ISU training sides, the lead tells Shlok before the freeze that the state P0 is the likely outcome; the design is not changed on the pilot's size, and Shlok may stop before compute is spent (J16 section 8, P16 5.6)".
- `debates/D016_roles/01_proposal.md` 5.6: learning curves on ISU for m in {8, 16, 32, all} and the weeks-window analogue of k, inner CV on training conditions only; "Pre-set reading, fixed now: if on ISU the physics-informed family is not lower than the best data-only learner at the smallest m in a majority of the five outer training sides, the lead tells Shlok before the freeze that P0 is the likely outcome; the design is not changed on the basis of the pilot's size."
- `debates/D016_roles/02_judge.md` section 8 (Re-open if): "P6 shows the data-only learners ahead at the smallest m on most ISU training sides. This does not change the design, but Shlok may then choose to stop before spending compute." Also lines 173, 320, 342, 384, and PREREG section 15 step 3.
- No numerical threshold, margin or tolerance appears in any of these sources. None is introduced here.

## What is run (the part of the sources that this pilot covers)
- ISU Test B, `runs/splits/isu_testB.json`. For each of the five outer folds only the fold's training side is loaded (`data.load_split role='train'`); the identifier audit of P6b is repeated and the split sha256 is checked before and after.
- Smallest m = 8: the nested max-min subset of 8 of the side's 51 training conditions is the pseudo-train (PREREG 4.1 selector). The side's other training conditions (42 or 43) are the pseudo-test. This is the same frame as P6b. Inner CV (grouped by condition, stratified by temperature, 2 folds as for m in {8, 16}, P6b decision keep 2) runs on the 8 pseudo-train conditions only.
- Available k on ISU = window length W in weeks (`data.WindowRule.for_grid`): W = 0 (reference check-up only, k = 0 analogue), W = 2 (scarce analogue, g1 analogue, PREREG 1 and 4.1), W = full = 4 weeks (k_full analogue). Tuning, the backbone tournament and the inner-CV window use W = 2 as `run.py` does at m < 32 (`rule_tune`); the five final refits are scored at all three windows, the way `run.py` scores a k list (one fit per seed, A11 and A12 refit per window because their window features differ).
- Arms: A1 (PINN-KAN), A2 (hard-ODE-KAN), A4 (PINN, additive GAM = AG at m < 32) as the physics-informed family; A9 (data-only F), A11 (GP-ARD), A12 (LightGBM) as the data-only learners (the D* candidates, `code/pinnkan/selectors.py`). Settings as P6b: N = 20 TPE trials per arm and fold (sampler seed = fold, tuning seed 1000 + fold), final refits seeds 0-4, `steps_scale` 1.0, ensemble endpoint (mean of the five seed forecasts, non-finite replaced seed-wise by persistence before averaging).
- Not run: the A10-analogue named in proposal 5.6 (the dataset-authors' semi-empirical form has no ISU analogue in the code base; PREREG 2 allows only a "cyclic power-law form" in the fallback) and the other m values of the learning-curve list (the reading is at the smallest m). Both omissions are recorded in RESULT.md.

## The reading by the rule (decision quantity)
Cell of the reading: m = 8, W = 2 weeks (the g1 analogue; the P1 claim is stated at g1).

For each outer training side s (five sides):
1. Side statistic of an arm a: S_s(a) = median over the side's pseudo-test conditions of the ensemble condition score (pp; condition score = mean over the condition's cells of the cell RMSE of the ensemble forecast). Median because P1 is a "lower median held-out-condition error" claim. Conditions are those scored by both arms of the comparison.
2. Physics-informed arm for the reading: A1 (the arm P1 names). Best data-only learner for the reading: D*(s) = the arm of {A9, A11, A12} with the lowest inner-CV condition-mean score on the side's pseudo-train (`selectors.select_comparators`; ties by candidate order; no pseudo-test score enters the choice). This is the comparator of P1.
3. The data-only learner leads on side s iff S_s(D*) <= S_s(A1), that is, iff A1 is "not lower" than the best data-only learner. No margin.
4. Stop rule 10 is triggered iff the data-only learner leads on at least 3 of the 5 sides (a majority of five). Then the lead tells Shlok that the state P0 is the likely outcome; the design is not changed; Shlok may stop before compute is spent.
5. Not triggered iff A1 is lower than D* on at least 3 of the 5 sides. If fewer than five sides are evaluable (a unit failed), the reading is evaluated on the sides that exist: triggered if the count of sides with the data-only learner ahead is at least 3; cleared if the count of sides with A1 lower is at least 3; otherwise "undetermined" and reported as such.

The decision file `decision.json` is written by `aggregate` of the committed driver from these four steps; nobody edits it.

## Descriptive rows (reported, attached to no decision)
- The same count at W = 0 and W = full (4 weeks).
- Oracle variant: best data-only learner chosen by the side's own pseudo-test statistic (min over A9, A11, A12), stricter for A1 than D*; A1 against each of A9, A11, A12 separately; the larger physics-informed family (min over A1, A2, A4 of S_s) against D*; mean in place of median.
- Per-side medians and means, the paired condition-level log ratio ln(S(D*) / S(A1)) and the share of pseudo-test conditions where A1 is lower, selected D* per side, selected hyperparameters, grid-edge hits, seed SD, failed trials.
- If a descriptive variant disagrees with the primary reading, RESULT.md says so; the primary reading above is the one that carries stop rule 10.

## Budget and deviations
Planned: 6 arms x 5 folds x one tuning (N = 20) plus tournaments; arithmetic from P6b (5.65 CPU-h for twice this tuning work) puts the expected cost at about 3 CPU-h, 1 to 1.5 h wall on 3 single-thread processes. Abort at 6 CPU-h (then the reading is evaluated on what exists, step 5). If the estimate from the first fits exceeds 6 h wall, `n_trials` is reduced equally for every arm and recorded here as a deviation before continuing. Deviations: none yet.
