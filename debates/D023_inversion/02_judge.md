# D023 judge: test-time latent inversion (2026-11-05)

Role: independent judge (CONTRACT 3). I wrote none of the inputs.
Reading depth: full text of `01_proposal.md`, `runs/check_D023_inversion/decision.json`, `runs/pilot_P6b/RESULT.md`,
`debates/codex_panel/turn08_response.md`, `research/CONTRACT.md`; `runs/prereg/PREREG_v4.md` sections 1-8, 11a (part) and 17 in full and
sections 9-10, 12-16, 18-22 by heading and grep (inversion, tuning, sensitivity rows); `code/pinnkan/pinn.py` lines 140-300
(`fit_pinn`, `invert_pinn`, `predict_pinn`, `predict_data_only`), `hard.py` lines 40-90 (`fit_delta`), `tuning.py` by grep (budget, spaces,
inner folds); `code/pilots/d023_inversion_check.py` by grep only (constants and function names: `TOL`, `CAPS`, `problem`, `newton`).
No Samsung label and no ISU outer-test fold was read. Every number below is quoted from `decision.json` or `RESULT.md`; none is new.
All of those numbers are ISU training-side development data, not evidence for Samsung.

## 0. Verdict

**REVISE-ACCEPT: accept the proposer's R-a as a computational convention; reject the proposer's R-b and the opponent's tuned weight.**

1. The fixed rule of proposal section 7 returned **NONE**, and that stands. Nothing is "adopted by the check". O2 fails criterion (c) (start
   spread) for A1 and A9. I adopt O2 on my own authority, as proposal section 7 allows ("the judge decides"), and the paper must say
   it is a convention chosen after the rule returned NONE, never that it passed the check.
2. **Rule:** every inverting arm uses one routine: per-cell Levenberg-Marquardt Newton, float64, started at the prior mode, stopped by
   ||g_c|| <= 1e-6 (1 + |f_c|) or at 100 iterations, accepted steps never raise the cell's objective, non-converged cells keep their last
   accepted iterate and are counted. Objective unchanged. No multi-start selection.
3. **z-prior weight: fixed at 1, not tuned.** It equals the weight of the training loss, so the test-time objective is the posterior of the
   model that was fitted. No candidate set {1, 4, 16}, no inner-CV choice, no extra tuning budget.
4. **Diagnostics are mandatory and carry no consequence:** convergence share, budget sensitivity, start spread, a basin statement; the
   rule in Methods, the table in the Supplement, two descriptive sensitivity rows. Forecasts are described as conditional on the minimum
   reached from the prior mode. The words "identified", "unique", "start-independent" and "global" are not used for the latent.
5. The approved outcome table (D017, D019) is unchanged. Two fixed sentences and a forbidden-word list are added outside section 11.

## 1. What the evidence supports, and what it does not

- **Non-convergence was real and the second-order method removes it.** O0 (production): doubling the steps moves A1 forecasts by up to
  4.58 pp (p99 2.35) and A9 forecasts by up to 42.3 pp (p99 11.98). O2: 0 pp for A1 and A9 at the doubled cap; convergence share 0.994
  (A1) and 1.000 (A9); the Hessian is positive definite at every solution (A1 median condition number 2237, A9 6.88). A2 does not move
  (largest change against O0 1.07e-05 pp), so one routine for all arms costs A2 nothing. The production budgets also differ (A1 200,
  A9 150, A2 300 steps), an unequal implicit regulariser; O2 removes it. O1 (Adam, 4000 steps) leaves 37 % of A1 cells
  unconverged (share 0.627), so it is not an alternative.
- **Non-uniqueness is a property of the model, not of the optimiser.** Converged runs from different starts reach different positive-definite
  minima. A1 start spread under O2: median 7.76 pp, p95 46.4, max 90.3. A9: median about 0 (7e-06), p95 50.0, max 111. So for A9 most cells
  are unimodal and more than 5 % are not; for A1 the typical cell is start-dependent.
- **Deeper is not better.** O3 (select the lowest objective among starts) disagrees with itself between two start sets (p95 5.49 pp A1, 1.63 A9), picks a
  start other than the prior mode in 72 to 84 % (A1) and 68 to 82 % (A9) of cells, and is descriptively worse for A9 in fold 3 (9.05 under O0, 16.34 under
  O3; the proposal's own reading: a window MAP that is searched harder over-fits z). O3 is rejected.
- **O2 does not change accuracy in a direction anyone could have tuned for.** Descriptive fold means (no rule, development data), O0 against O2:
  A1 5.48/5.84/4.98/5.76/5.56 against 5.27/5.73/4.97/5.97/5.74; A9 10.13/13.70/22.43/9.05/15.28 against 10.10/13.71/21.67/9.32/14.83.
  Three A1 folds go down and two up; no direction is claimed.
- **What the data do not show.** Nothing in the check says that the prior mode is a good basin, that the z prior weight is too weak, or
  that any other weight would reduce the spread. R-b was not run. I will not rule on an effect nobody measured.
- **A scale problem the paper must face.** A1's median per-cell start spread (7.76 pp) is of the same order as A1's mean pseudo-test error
  (4.97 to 5.97 pp, descriptive; units not identical: largest forecast change per cell against cell RMSE). Whatever the paper shows for P1
  is therefore a statement about the estimator with its prior-mode convention. This is why the diagnostics sit beside the scores (section 4), not only in the Supplement.

## 2. Ruling (1): the inversion rule

| Element | Ruling |
|---|---|
| Objective | Each arm's current per-cell loss, unchanged: window points, A1's residual over (window end, t_max] with the per-cell seeded collocation draws (`n_col` = 16, seed from the final-refit seed and the cell id), the priors. Causal: no label after the window. |
| Arithmetic | float64 for the inversion only; the trained network is cast to a float64 copy; the network itself is unchanged. |
| Start | Prior mode: z = 0, delta = prior mean. Deterministic. Single start in production. |
| Step | Per-cell Levenberg-Marquardt on the exact per-cell Hessian (block diagonal, blocks of size 1 to 4, by autograd). The damping shift makes H plus the shift positive definite. A step is accepted only if that cell's objective does not rise. Damping constants are fixed in code and in the config hash. No randomness. |
| Stop | Per cell: ||g_c|| <= 1e-6 (1 + |f_c|); else at 100 iterations. The same TOL and cap for A1, A4, A5, A9, A13, A15, G15 and A2. |
| Non-converged cell | Keep the last accepted iterate (the objective is non-increasing, so it is the best iterate). Count it per arm, fold, m, k and seed in `diagnostics.json`. It is not dropped, re-run or re-started. A non-finite forecast follows PREREG section 6(3) (persistence, seed-wise, counted). |
| k = 0 | Unchanged: a cell whose window holds only the reference point keeps the prior mode (z = 0, delta = mean). |
| A10 | Unchanged (bounded Brent on [-2, 2], one dimension). Log the cells at a bound; a value at plus or minus 2 means the bound set it. |
| Multi-start | None in production. Alternative starts exist only for the diagnostics of section 4. |
| Call sites | One routine `invert_latents`, used by `invert_pinn` (A1, A4/A5/AG, A13, A15, G15), `predict_data_only` (A9) and `fit_delta` (A2 and the backbone tournament). The `steps` and `lr` arguments of the three sites are removed (a call that passes them raises). |

**Why this and not the alternatives.**
- *O0, leave the production Adam loop and disclose.* The result depends on a step count that differs between A1 (200) and A9 (150); P6b Table E
  and the check both show it (A9 up to 42 pp when the steps are doubled). A reviewer reads this as a hidden handicap of the ablation. Rejected.
- *O1, Adam with a longer cosine schedule.* Fails (a) and (b) for A1 (share 0.627; budget change p99 1.23 pp, max 17.7). No stopping test. Rejected.
- *O3, multi-start with selection by the objective.* Less stable than a single start, no better forecast, several times the inversion cost, and
  it adds a data-dependent choice. Rejected.
- *Fix z at the prior mode (delta-only inversion).* Unimodal by construction, but A9 would become a population forecast with no window use, and A1 would
  lose the window's information on its latent. That changes P2 and the identity of A1. Kept only as the fallback if the Samsung dry run shows
  that O2 cannot be made to converge (section 8).
- *Posterior mean or Laplace forecast.* Statistically the better answer to a multimodal posterior, but it needs a specified distribution and
  an integration method per cell, changes the estimator of every arm, and the freeze is days away. Deferred to a later version; future work, not a result.
- *Warm start from a neighbouring training cell.* Adds a data-dependent design (distance, neighbour) and is still not converged. Rejected.
- *Change the prior scale now.* Untested; see section 3.

**Honest label.** The paper calls it: "the local posterior mode reached from the prior mode by a converged per-cell Newton method". It
does not call it "the MAP estimate" without that qualifier. The opponent's point holds: the check found converged minima with materially
different forecasts, so "the MAP" invites "which mode".

## 3. Ruling (2): the z-prior weight

**Fixed at 1. Not tuned.** The training losses already weight z against the data term in the same units as the test-time objectives
(`fit_pinn`: `(z**2).sum() / n` against a mean data term; `fit_data_only`: the same; `invert_pinn`: `(z**2).sum()` against a summed data term;
`predict_data_only`: `((z - zmu)**2).sum()` against a summed data term), so the test-time objective equals the training posterior of the same model.
Weight 1 is the model's own prior, not a new constant.

**Does the PREREG permit tuning it?**
- Inner tuning on Samsung training conditions is the standing protocol (section 7 budget rule; section 4.1), so tuning as such is permitted.
- The weight is not in any tuned space of 7.1. Adding it is an amendment of the unfrozen draft by change-log row, and it must reach every arm that
  inverts z: **A1, A4, A5 and A9** (A13, A15 and G15 inherit from A1 and A4). The opponent named A1 and A9 only. Giving it to A1 and A9 and not to A4/A5
  would break parity inside the PINN family (A1 against AG in the ladder, A15 against G15 in K2). A2 has no z; A11 and A12 have none. The dimension counts in 7.1
  (6, 4, 4, 5) and the test `test_arm_table_matches_prereg_dimensions` (C15) would change.
- Budget: N = 20 trials per tuned arm would not change; the extra dimension is absorbed inside the same N and thins the search of the
  arms that carry it. A post-hoc stage (choose among {1, 4, 16} after tuning) would add inner-CV evaluations for some arms only, which is a
  parity violation. The only form that keeps parity is the in-space categorical, and I do not adopt it, for these reasons:

1. **The weight would be chosen at one window and applied at others.** A configuration is tuned once per (outer fold, m), scored at k = 2 for m < 32, and
   then applied at every k of that m (section 4.1), including k_full. A weight chosen at k = 2 (where the window is weakest and shrinkage pays most)
   over-shrinks at k_full and harms A1 and A9 at (8, k_full) and (16, k_full) relative to arms with no such parameter. A k-dependent weight would be a new
   schedule, which the opponent himself flags as a post hoc risk.
2. **The inner folds are too small to choose it.** m = 8 with two inner folds holds two conditions per validation fold; P6b Table B shows per-fold signs
   flipping for A1, A9 and A11, and the grid-edge share of selected configurations is 0.3 to 0.55 for A1, A2 and A9 (Table C). A three-level choice from this signal is mostly noise.
3. **No measurement supports it.** The check measured convergence and start dependence; it did not vary the weight. Whether weights 4 or 16 reduce
   the spread, and at what cost to the forecast, is unknown. R-b would answer it on ISU training sides, but it changes the estimator, needs its own
   committed rule and about 0.5 CPU-h (the proposer's estimate), and it spends ISU development exposure on a Samsung choice (the opponent's point). With the freeze this close,
   that is not justified when a fixed, model-consistent weight is available.
4. **A9 could shrink itself into a population forecast** by choosing 16, which makes it a stronger D* candidate and blurs P2; the same choice for A1 moves A1 toward its k = 0 reference.
   Tuning would let the window-information gain (E7) depend on a tuning outcome.

**What the paper does instead.** A descriptive sensitivity row (section 4, row (vi)): the frozen fitted models re-inverted with weights 4 and 16, A1, A9 and AG at g1 and
g4, inference only, no refit, no consequence for any state or sentence, no change of the weight afterwards. It is the "sensitivity envelope" the opponent asked for, without a new hyperparameter.

## 4. Ruling (3): diagnostics, and where

**Fixed definitions (so that Samsung and the development numbers can be compared).**
- *Convergence fraction:* the share of cells with ||g_c|| <= 1e-6 (1 + |f_c|) at the cap, per arm, outer fold, m, k, seed. Logged for every inversion in the run, including inner-CV calls (a count only).
- *Budget sensitivity:* the same inversion with the cap doubled (200); the largest absolute forecast change per cell, reported as p99 and max (pp).
- *Start spread:* on seed 0 of the final refit, per arm and cell (m, k): the prior mode plus three seeded diagnostic starts (z ~ N(0, 0.5^2), delta ~ N(0, TAU^2)), each run to convergence; the range of the forecast across the four, as median, p95 and max (pp). Seed stream:
  `SeedSequence([20261105, crc32("inv|<fold>|<arm>|<m>|<k>|<j>")])` (the seed rule of PREREG section 8; no second root). The check used a different stream; that does not matter for the comparison.
- *Basin statement:* per arm and cell, the share of cells in which a diagnostic start reached a minimum with objective lower than the prior-mode minimum by more than 1e-6 (1 + |f_c|), and the share of cells whose forecast differs by more than 1 pp between the prior-mode minimum and the lowest-objective diagnostic minimum. (1e-6 is the convergence tolerance; 1 pp is a design choice for the share, not a result.)
- Arms: A1, A9, AG (A4 or A5 as selected) at all nine cells, window k in {2, k_full} (k = 0 is the prior mode by rule, nothing to report); all other inverting arms report the convergence fraction and the cap-doubling change only.

**Rules that keep the diagnostics from becoming analysis choices.**
- They use window labels only, as scoring does. Forecasts from alternative starts are never compared with outer-test labels in the diagnostics, no per-start score is computed there, and nothing is selected, re-run, dropped or re-weighted because of them.
- They are computed after the primary scores are written.
- The only scored versions of the alternative starts are the descriptive sensitivity rows below.

**Where.**
- *Methods (one paragraph):* the rule of section 2 (optimiser, arithmetic, start, tolerance, cap, handling of non-converged cells, same for every inverting arm), the pooled convergence fraction per arm, the basin sentence (section 5), a pointer to the Supplement.
- *Supplement (one table plus the two rows):* convergence fraction, cap-doubling change (p99, max), start spread (median, p95, max), basin shares, by arm x m x k; the D023/P6b development numbers only in a labelled appendix paragraph ("ISU training sides, development, not evidence for Samsung").
- *Limitations:* one sentence, fixed text in section 5.
- *Sensitivity rows (descriptive, no consequence; they come after the core set in the drop order):* (v) the A1, A9 and AG scores and the P1 and P2 plain-rule counts recomputed with each diagnostic start (j = 1 to 3) in place of the prior mode, the same start for every arm, at g1 and g4; D* is not reselected. (vi) the weight row of section 3. Rows (v) and (vi) are outside the closed list (i)-(iv) of 9.8, so neither can change a downgrade, a state or a sentence. A result of (v) or (vi) that disagrees with the primary is reported as such; it is not a reason to change the frozen rule.

## 5. Ruling (4): claim wording

- **Approved outcome table (section 11, D017, D019): no change.** Nothing here edits an abstract sentence, a title or a state.
- **Fixed Methods sentence:** "The per-cell latent is the local posterior mode reached from the prior mode by a converged damped Newton method (float64, gradient tolerance 1e-6, at most 100 iterations), identical for every arm that infers a latent."
- **Fixed Limitations sentence:** "The per-cell objective can have several local minima. Forecasts are conditional on the minimum reached from the prior mode; the share of cells for which other starting points reached a different minimum is given in the Supplement, and the latent is not claimed to be identified."
- **Words never used for the latent or the inversion** (listed outside section 11, which is not edited): identified, identifiable (the extraction audit of 7.3 item 6 is a different object and keeps its own use), unique, start-independent, global optimum, "the MAP" without the qualifier above, "robust to initialisation".
- **P2 and E1.** P2 compares two estimators that share one inversion rule; the contrast is stated as that. The paper does not say that the law identifies the latent or that A9's gap is "the physics". The Discussion states that A9's inference is multimodal on part of its cells, so the P2 gap is conditional on this estimator and a posterior-mean forecast for A9 might narrow it (future work, not a result). The competing-explanation line E1 gets one sentence on this.
- **Order of operations (a reviewer will ask).** The inversion check and this ruling came before the freeze, on ISU training sides, with the rule committed before the main run (`0ba9f92`, 14:04:51, per the proposal); the rule returned NONE; O2 was adopted by the judge. This is part of the ISU development exposure, disclosed with P6b.
- **P6b.** Its verdict (keep two inner folds) was computed with the production inversion. It stands as the default of 4.1. It is not re-run (the run took 5.65 CPU-h, and it would buy a default that is also the cheaper option); the paper states that P6b used the earlier fixed-budget inversion.

## 6. The opponent and the proposer

| Point | Disposition |
|---|---|
| Prior-mode Newton only as a frozen operating rule; do not call it the MAP or identified (opponent 1) | Accepted in full. Wording in section 5. |
| Report convergence and start sensitivity separately, and whether other minima have similar objective values (opponent 1) | Accepted: basin statement and objective comparison in section 4. |
| Tune the z-weight in Samsung inner CV for A1 and A9, else keep fixed (opponent 2) | The fixed branch is taken. Reasons in section 3. Correction: if tuned, the weight would have to reach A4/A5 as well. |
| "If Samsung inner tuning is not already permitted, do not quietly add it" (opponent 2) | Inner tuning is permitted; a new dimension is not in 7.1 and would need a change-log row. Not made. |
| Sensitivity envelope for the weight now (opponent 3) | Accepted as row (vi). |
| Shrink z by window length, reparameterise, marginalise (opponent 3) | Not adopted: each is a new modelling choice without a measurement; marginalisation is future work. |
| R-a (proposer): adopt O2 | Adopted as a convention, with the NONE verdict stated. |
| R-b (proposer): test the weight on ISU first | Not run. No decision depends on it. |
| R-c (proposer): reject O3 | Accepted. |

## 7. Actions

| # | Owner | File | Action |
|---|---|---|---|
| 1 | coder | `code/pinnkan/inversion.py` (new) | `invert_latents(objective_per_cell, P0)`: the per-cell LM Newton of the check (`code/pilots/d023_inversion_check.py`; `problem` and `newton` are the reference), float64, TOL 1e-6, cap 100, prior-mode start, monotone acceptance, non-converged counter, final gradient norms; constants read from one frozen config object. No randomness. |
| 2 | coder | `code/pinnkan/pinn.py` (`invert_pinn`, `predict_pinn`, `predict_data_only`), `code/pinnkan/hard.py` (`fit_delta`, `predict_hard`), `arms.py`, `run.py` | Replace the three Adam loops by the routine; remove `steps` and `lr`; keep the k = 0 override; keep the z weight at 1 in all four objectives (code comment pointing to the training loss); write `diagnostics.json` (convergence share, final gradient norms, A10 boundary hits). |
| 3 | coder | `code/pinnkan/inversion_diag.py` (new), `run.py` | Diagnostics of section 4: cap doubling, three seeded diagnostic starts on seed 0, basin shares, sensitivity rows (v) and (vi); computed after the primary scores are written; no outer label read in the diagnostics. |
| 4 | coder | `code/tests/test_inversion.py` (new) | **T1 known quadratic:** per-cell quadratics with different curvatures (condition numbers up to 1e4); the exact minimiser within the tolerance in a handful of iterations; a non-convex double well from an indefinite-Hessian start: the objective never rises and the result has a positive-definite Hessian; an under-capped hard cell is flagged non-converged and returns the last accepted iterate. **T2 deterministic reproducibility:** two calls bitwise identical; a cell's result independent of its position and of the other cells in the batch (separability); the same seed gives the same collocation draw. **T3 parity A1/A9:** the call sites of A1, A4, A5, A9, A13, A15, G15 and A2 import one routine and read the same TOL, cap, start rule and dtype from one config; a synthetic case in which A1's objective with lam_res = 0 and delta fixed and A9's give the same iterates through the routine. **T4** k = 0 rule. **T5** cap doubling leaves a converged cell unchanged. **T6** the test-time objective equals the training per-cell terms (z weight 1) on one cell. **T7 regression:** on one fold of the check (A1, A9, A2) the routine reproduces the check's O2 forecasts to the check's replica tolerance (largest difference reported there 1.9e-5 pp for A1). |
| 5 | coder | `code/tests/test_pk_tuning_run.py`, `test_pk_models.py` | Update the call sites that pass `steps`; `test_arm_table_matches_prereg_dimensions` must stay at 6/4/4/5 (no weight dimension). |
| 6 | experiment-designer | `runs/prereg/PREREG_v4.md` | New subsection 7.5 "Test-time inversion" with the table of section 2 and the fixed weight 1; edit the clause at line 145 and the pilot sentence in 4.1 (the inversion diagnostic "no rule attached, a fix needs its own decision row" now points to D023); 9.9 rows (v) and (vi), outside (i)-(iv); the two fixed sentences and the forbidden-word list of section 5 (in 7.5, **not** in section 11); change-log row (19.1/19.2) and an alignment item in section 20; a new checklist condition C27 "inversion routine, unit tests T1-T7, diagnostics file; constants pinned in the config hash"; section 17.4 build list; the disclosure that P6b ran under the earlier inversion and the order-of-operations sentence. Do not touch section 11. |
| 7 | experiment-designer | `runs/prereg/PREREG_v4.md` sections 15-16 | Compute line for the diagnostics on seed-0 outer windows for A1, A9, AG (proposal arithmetic, not a measurement: about 0.031 s per Newton iteration for A1; inner-CV cost +1 to 3 CPU-h; to be replaced by the timing run). Rows (v), (vi) sit last in the drop order. |
| 8 | coder | the FB-8 timing run at the freeze commit | Log the inversion convergence share on training-side windows (no outer fold). If the share is below 0.99 for A1 or A9 (the threshold of criterion (a)), tell the lead before the freeze; see section 8, item 1. |
| 9 | gate-auditor | `research/audits/` | Check C27 at the freeze: T1-T7 pass, constants in the config hash, no `steps`/`lr` argument left, diagnostics computed after scoring, no outer label read by `inversion_diag.py`. |
| 10 | paper writer | `paper/draft/` Methods, Supplement, Limitations | Fixed sentences of section 5; Supplement table; no forbidden words; the development numbers only in the labelled appendix. |

## 8. Re-open if

1. The Samsung dry run (the FB-8 timing or a synthetic PC-1 run) shows a convergence share below 0.99 for A1 or A9 at the cap, or a Newton failure
   (non-finite step) on any cell: stop and tell the lead; the fallbacks are a raised cap (same for every arm, new row) or the delta-only inversion.
2. A development rule (committed before running, ISU training sides only) shows that a fixed weight above 1 passes the start-spread criteria (c) with a
   non-inferior pseudo-test score for both A1 and A9: a decision row may change the *fixed* weight for all inverting arms before the freeze. It may not make the weight tuned.
3. ISU becomes the primary dataset (the D005 fallback): the diagnostics and rows (v), (vi) are repeated on ISU, and this check is disclosed as part of the ISU development exposure.
4. Shlok or the supervising professor requires an identified inversion: then the estimator must change (posterior mean, marginalisation), which is a new decision and a new version.
5. Test T7 shows that the ported routine disagrees with the check's O2 by more than the replica tolerance.
6. Any outer-test score exists before FROZEN (the run is void; D023 is unaffected).

## 9. What this ruling does not do

It does not show that the Samsung forecasts are right, only that they are reproducible and described correctly. It does not claim that A1 beats D*; the
descriptive pseudo-test scores carry no A1-against-D* contrast, and none is computed here. It does not change the weight of any chain in the graph, the margins, the
tiers, the grid or the number of trials. It does not replace the freeze checklist.
