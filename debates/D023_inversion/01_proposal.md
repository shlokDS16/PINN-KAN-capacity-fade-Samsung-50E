# D023 proposal: a converged, start-independent test-time inversion for every arm that infers per-cell latents (2026-11-05)

Role: proposer (ml-expert). The opponent and the judge are other agents (CONTRACT 3).
Reading depth: full text of `runs/pilot_P6b/RESULT.md`, `run_meta.json` and `config_used.json`; `code/pinnkan/pinn.py`
(`PINNModel`, `fit_pinn`, `invert_pinn`, `predict_pinn`, `DataOnlyF`, `fit_data_only`, `predict_data_only`);
`code/pinnkan/hard.py` in full; `code/models/ageing_models.py` `SolutionNet`; `code/pinnkan/law.py` lines 28-40, 61-68 and
336-395; `code/pinnkan/semi.py` (grep of `cell_factor`); `code/pinnkan/arms.py` (grep of the predict calls); and
`code/pilots/p6b_inner_folds.py` lines 1-440, whose diagnostic replicates the production loops.
No production code was edited. No Samsung label and no ISU outer-test fold was read.

## 0. Summary
- **Cause (section 1).** The inversion is a fixed-budget, constant-learning-rate Adam run (A1 200, A9 150, A2 300 steps,
  float32, no convergence test). It is applied to a non-convex, poorly conditioned per-cell objective. The early window
  barely identifies z, because F = t g(t, s, z) makes the window's sensitivity to z scale with t. The long-horizon forecast,
  however, depends strongly on z. In A1, z and delta can also trade off along a ridge. So the answer depends on where
  Adam stops. A2 converges because its latent is one scalar per cell in a closed-form, monotone law.
- **Proposal (section 2).** Replace the three loops by one routine for every inverting arm:
  - float64;
  - a deterministic start at the prior mode;
  - a per-cell damped Newton (Levenberg-Marquardt) step, using the exact per-cell Hessian (the objective is a sum of
    per-cell terms, so the Hessian is block diagonal with blocks of size 1-4);
  - a convergence test, with an iteration cap and a logged non-converged share;
  - optionally, K fixed starts with per-cell selection by the arm's own causal inversion objective.
  The objective itself is unchanged.
- **The small check (section 7) was committed before running.** Its result is in section 8: the verdict is **NONE**. O2
  converges (99.4 % of A1 cells, 100 % of A9 cells) and is budget-independent, but converged starts land in different local
  minima (A1 start spread median 7.8 pp), so the start-spread criterion fails for every option. The proposer recommends R-a
  (O2 from the prior mode, with the multimodality disclosed) and a separate check of the z-prior weight (R-b). The adoption rule uses only
  convergence, budget stability, start spread and the objective, never an A1-vs-D\* gap.

## 1. Diagnosis from the code
1. **Fixed budget, no stopping test, and a budget that differs by arm.** `invert_pinn` uses Adam with lr 0.05 constant and
   200 steps (`pinn.py` 190-222). `predict_data_only` uses Adam with lr 0.05 and 150 steps (272-292). `fit_delta` uses Adam
   with lr 0.05 and 300 steps (`hard.py` 55-73). Adam with a constant learning rate does not settle at a stationary point.
   Its per-coordinate step stays of order lr, so the returned latent is "wherever step 150/200/300 lands". This acts as an
   implicit, untuned regulariser whose strength differs between A1 and A9. That matches P6b Table E: doubling the steps moves
   forecasts by up to 4.6 pp (A1) and 42 pp (A9).
2. **Scale and conditioning.**
   - The data and residual terms are divided by SIGMA^2 = 0.0025 (`law.py` 28), and the residual term is multiplied by
     lam x pts_per_cell x Ct. The initial gradient norms are therefore about 3e4 for A1 (P6b Table E).
   - The prior curvatures are only 2 for z and 2/TAU^2, about 89, for delta.
   - The per-cell objective therefore mixes stiff directions (window and residual) with flat ones (prior only). Adam's
     per-coordinate normalisation zig-zags across a stiff valley that is not aligned with the axes, and it crawls along the
     flat valley floor.
   - Float32 with a 400x scaled loss limits the precision that can be reached; this is a minor factor.
3. **Weak identification of z by the window.**
   - `SolutionNet` has F(t, s, z) = t * g(t, s, z) (`ageing_models.py` 56-69), so the derivative of F with respect to z at
     a window point is t times the derivative of g.
   - With an early window (ISU W = 2 weeks, so t_n = t / 50 is at most 0.04) the window says little about z.
   - The forecast at t_n of order 1 depends on z through the tanh network, which is non-convex in z.
   - A9 has only the window and the N(0, I) prior, so its z posterior is flat and possibly multimodal.
   - A1 adds the residual over (window end, t_max], which ties F's shape to the law. But delta moves the law amplitude and z
     moves F, and both can reduce the residual, which creates a ridge in (z, delta).
4. **Why A2 converges.** Its latent is one delta per cell. The forward model is the closed-form law (`hard.py` 21-24), which
   is monotone in delta. The 1-D objective is smooth and well scaled, and 300 Adam steps reach a gradient norm of about 1e-5
   (P6b Table E).
5. **A10** fits its per-cell factor with bounded Brent on [-2, 2] (`semi.py` 177-185), which is 1-D and converged. It is
   unchanged, but boundary hits should be logged (a delta at plus or minus 2 means the bound, not the data, set the value).
6. **Related risk (not the test-time issue).** The training cells' z_c and delta_c are fitted jointly with the network in
   the same 2000-step Adam loop (`fit_pinn` 154-187). A fully converged test-time MAP can land in a region of z that the
   network never saw in training, where the forecast extrapolates wildly. Section 8 reports the forecast scores of each
   option (descriptive only) so that the judge can see whether this occurs.

## 2. Proposal
One routine `invert_latents(objective_per_cell, P0)`, used by `invert_pinn` (A1, A4/AG, A5, A13, A15, G15),
`predict_data_only` (A9) and `fit_delta` (A2 and the backbone tournament):
- **Objective: unchanged.** It is each arm's production loss written per cell: window points, A1's residual over the
  horizon, and the priors. It uses only causal information, with no label after the window. The per-cell form sums exactly
  to the production loss (checked by the replica column in section 8).
- **Start:** the prior mode (z = 0, delta = mu), deterministic.
- **Step:** per-cell Levenberg-Marquardt on the exact block Hessian (autograd: one gradient plus p Hessian-column passes,
  with p = dim z + dim delta, at most 4).
  - The damping is shifted so that H plus the shift is positive definite.
  - A step is accepted only if that cell's objective does not rise.
  - Float64 for the inversion only; the network stays as trained.
- **Stopping:** ||g_c|| <= 1e-6 (1 + |f_c|) for every cell, or an iteration cap. The non-converged share and the final
  gradient norms go to `diagnostics.json`.
- **k = 0 rule:** unchanged (latents at the prior mode when the window has only the reference point).
- **Multi-start (only if the check shows multimodality after convergence; option O3):** K fixed starts (the prior mode, and
  the prior mode plus or minus 1 prior sd along each latent axis), each run to convergence, with per-cell selection by the
  same causal objective. Selection never uses a later label, a forecast score or a comparator.
- **Same for every inverting arm:** the same tolerance, cap and start rule. The confirmatory arms that do not invert (A11,
  A12, R1, R2) are unaffected.

**Expected effect.**
- Forecasts become a deterministic function of the trained network and the window: start-independent if the per-cell
  minimum is unique, and budget-independent once converged.
- This removes a source of noise that the seed ensemble only partly averages, which helps P1's effective rho (D020 01, section 1).
- The direction of the change in accuracy is not known in advance: the early-stopped iterate may have been regularising.
  Section 8 shows it on development data, descriptively.

**Cost (arithmetic from the timing check in section 7, fold 0, 131 pseudo-test cells).**
- A1: about 0.031 s per Newton iteration (float64), against about 0.004 s per Adam step. Typically tens of iterations, cap
  100, so about 1-3 s per prediction call against about 0.5-1 s now.
- Inner-CV prediction calls (about 100 per tuned PINN arm per (fold, m), on smaller validation sets) give roughly +1-3 CPU-h
  over the grid. O3 with 5 starts would be roughly x5 on the inversion part (about +5-15 CPU-h).
- Coder about 3 h: one routine, three call sites, and unit tests (an exact minimum on a quadratic objective; agreement with
  the production replica at a fixed budget; per-cell separability; the k = 0 rule).

**Fairness.** One routine and one rule for A1 and its physics-off twin A9 (P2), and for AG, A2, A13, A15 and G15. D\* members
A11 and A12 do not invert. A9 is a D\* candidate and gains or loses the same way. Nothing is tuned for any arm.

## 3. Why this, and why not each alternative
- **O1, more Adam steps with a decaying learning rate (tested as a reference).** This is the smallest change, but a first-order
  method on this conditioning needs thousands of steps. It has no reliable stopping test, and its result still depends on the
  budget.
- **L-BFGS on the whole batch.** It couples cells inside its low-rank curvature approximation, uses one global line search
  and one global stopping test, and ignores the exact block-diagonal structure. Per-cell Newton uses that structure for the
  cost of p extra backward passes.
- **Reparameterisation by whitening with the prior.** The prior is already unit-scale for z. Whitening by the Hessian is the
  Newton step.
- **Drop z at test time (infer delta only, z at the prior mode).** This is well posed (like A2), but it changes the model: A9
  would then have nothing to infer, and P2 would compare different window usage. It is kept only as a fallback if the check
  finds no converged start-independent option.
- **Laplace or posterior-mean forecast (average over the latent posterior).** This changes the estimator and needs sampling
  or Hessian-based integration per cell. It is more defensible statistically, but it is a larger change than a pre-freeze
  fix should be.
- **Warm start from the nearest training cell's latent.** It adds a data-dependent design choice (the distance metric and
  which cell is nearest), and it is still not converged.
- **Leave it and disclose.** This is unacceptable: the reported scores would depend on an arbitrary step count that differs
  between A1 and A9.

## 4. Is this the best possible, or is there room?
A converged MAP is the best defensible point estimate for this objective. Further gains would have to come from the
objective itself, which is a separate decision, not part of this fix:
- the prior scale of z and TAU (D020 C6);
- the window weighting;
- a posterior mean.
If section 8 shows that the converged MAP forecasts worse than the early-stopped iterate on development data, the honest
reading is that the prior is too weak for an early window. The judge should then consider an explicit change to the prior
scale, decided on training sides only and the same for every arm, rather than keeping an implicit step count.

## 5. What a JES reviewer would hit
- "Test-time latent inference is an optimisation; is it converged?" The paper must report the tolerance, the cap, the
  non-converged share, and the start-sensitivity check.
- Unequal step budgets between the model and its ablation (200 vs 150) would read as a hidden handicap of A9.
- The order of operations: this fix and its check came before the freeze and on development data only (P6b, D023).

## 6. What would make a reviewer reject it
- Forecasts that change with the random seed of the inversion, or with the number of steps (the current state).
- A fix tuned on the test outcome, or one applied to A1 only.
- Selection among starts by forecast error. Here the selection is by the causal objective only.

## 7. Test plan and adoption rule (fixed and committed BEFORE the main run)
**Data.**
- ISU training sides only, exactly as P6b: `runs/splits/isu_testB.json`, folds 0-4, with the outer-test conditions never
  loaded (`p6b_inner_folds.fold_data` asserts it).
- Pseudo-train = the m = 8 max-min subset; pseudo-test = the fold's other training conditions; window W = 2 weeks.
- No Samsung data.

**Models.** A1, A9 and A2, refit with seed 0 using the P6b 2-fold configuration and tournament backbone of each fold
(`runs/pilot_P6b/units/f<f>_k2_<arm>.json`, `tournament_f<f>_k2.json`).

**Options (each applied identically to A1, A9 and A2).**
- **O0:** the production replica (float32 Adam lr 0.05; 200 / 150 / 300 steps; budget doubled by continuing).
- **O1:** float64 Adam, lr 0.05 cosine-decayed to 5e-4, 4000 steps (doubled: a fresh 8000-step run).
- **O2:** per-cell damped Newton, float64, from the prior mode, cap 100 iterations (doubled: 200).
- **O3:** O2 from S_A (the prior mode plus or minus 1 prior sd along every axis) with per-cell selection by the objective,
  compared with the selection from S_B (the prior mode plus 4 seeded draws, z ~ N(0, 1), delta ~ N(0, TAU^2)).

**Spread starts for O0-O2:** the prior mode plus 3 seeded draws, z ~ N(0, 0.5^2), delta ~ N(0, TAU^2) (as P6b). Seeds:
`[20261106, 23, fold, arm index, j]`.

**Measures, per pseudo-test cell, pooled over the 5 folds.** Cells with a single window point are excluded, because
production sets them to the prior.
- Convergence share (||g|| <= 1e-6 (1 + |f|)).
- Budget change: the largest absolute forecast change in pp between the cap and the doubled cap.
- Start spread: the largest range in pp across starts. For O3 it is the largest |selection(S_A) - selection(S_B)|.
- Objective difference f(option) - f(O0).
- For A2, the largest change against O0.

**Adoption rule (`RULE` in `code/pilots/d023_inversion_check.py`, applied by `aggregate`; nobody chooses).** Go through the
options in the order **O2, O1, O3** and adopt the first one for which all of the following hold:
- (a) for A1 and for A9, the convergence share (of the base run, i.e. O2 for O3) is at least 0.99;
- (b) for A1 and A9, the budget change has p99 <= 0.1 pp and max <= 1 pp;
- (c) for A1 and A9, the start spread has median <= 0.1 pp and p95 <= 1 pp;
- (d) for A1 and A9, the median objective difference against O0 is <= 0;
- (e) for A2, the p99 change against O0 is <= 0.05 pp (A2 is already converged; the fix must not move it);
- and all 15 units are complete.

If no option passes, the verdict is **NONE**: nothing is adopted from this check, and the judge decides on the fallbacks of
section 3 (z fixed at the prior mode, or a prior-scale change), with the descriptive table.
The pseudo-test forecast scores per arm and option are reported as **descriptive only, with no rule**. No A1-vs-D\* contrast
is computed.

**Budget.** CPU only, 2 processes (folds {0, 1, 2} and {3, 4}), with a guard of 0.70 CPU-h per process (an incomplete run
gives NONE). Expected cost about 0.3 CPU-h (timing check on fold 0: A1 fit 12.5 s, Adam step 0.004 s, Newton iteration
0.031 s; A9 2.5 s, 0.0008 s and 0.005 s).

**Mechanics smoke test** (before the commit, in the scratchpad outside `runs/`, 1 fold, 5 % training steps, tiny caps): it
ran end to end. Its numbers are not used.

## 8. Result (appended after the run; development data, ISU training sides, not evidence for Samsung)
**Run facts.**
- Rule and script committed in `0ba9f92` (14:04:51) before the main run.
- All 15 units complete, no errors, 0.30 CPU-h on 2 processes.
- The replica matches the production path: largest difference 1.9e-5 pp for A1 and 0 for A9 and A2.
- Files: `runs/check_D023_inversion/decision.json`, `units/`, `log_a.txt`, `log_b.txt`.

**Verdict of the fixed rule: NONE.**
- O2, O1 and O3 all fail criterion (c), start spread, for A1 and for A9.
- O1 also fails (a) and (b) for A1.
- Criteria (a), (b), (d) and (e) pass for O2.
- Nothing is adopted from this check (section 7). The judge decides.

| arm, option | conv. share | budget change p99 / max (pp) | start spread median / p95 / max (pp) | median f - f(O0) | Hessian at solution |
|---|---|---|---|---|---|
| A1 O0 (production) | - | 2.35 / 4.58 | 7.83 / 65.6 / 119 | 0 | - |
| A1 O1 (Adam 4000, cosine) | 0.627 | 1.23 / 17.7 | 5.71 / 52.0 / 139 | -0.78 | - |
| A1 O2 (Newton-LM) | 0.994 | 0 / 0 | 7.76 / 46.4 / 90.3 | -1.00 | min eig > 0 in all cells; median condition number 2237 |
| A1 O3 (S_A vs S_B selection) | (O2) | (O2) | 0 / 5.49 / 24.9 | -1.92 | best start is not the prior mode in 72-84 % of cells |
| A9 O0 (production) | - | 12.0 / 42.3 | 1.13 / 50.4 / 128 | 0 | - |
| A9 O1 | 1.000 | 0 / 0 | 0 / 46.0 / 111 | 0 | - |
| A9 O2 | 1.000 | 0 / 0 | 0 / 50.0 / 111 | 0 | min eig > 0 in all cells; median condition number 6.9 |
| A9 O3 | (O2) | (O2) | 0 / 1.63 / 65.8 | -0.0002 | best start is not the prior mode in 68-82 % of cells |
| A2 O0, O1, O2, O3 | 1.000 | 0 / 0 | 0 / 0 / 0 | 0 | median condition number 1 |

**What this shows (reading of the table).**
1. **Non-convergence was real, and the second-order method removes it.**
   - With O2, 99.4 % (A1) and 100 % (A9) of cells meet the gradient test.
   - Doubling the cap changes no forecast (0 pp).
   - This also holds for A2, whose forecasts do not move at all (criterion e).
   - Adam needs thousands of steps for A1 and still leaves 37 % of cells unconverged (O1).
2. **The dominant problem is non-uniqueness, not only non-convergence.**
   - Converged runs from different starts end at different local minima: the Hessian is positive definite at each one.
   - Those minima carry forecasts that differ by up to about 90 pp for A1 and 111 pp for A9.
   - A9's per-cell problem is well conditioned (median condition number 6.9) but multimodal. A1's is both ill-conditioned
     (2237) and multimodal.
   - This supports diagnosis item 3: the early window does not pin z, and the tanh network gives several basins.
3. **Selecting the lowest objective among starts (O3) does not give a stable answer.**
   - Its p95 disagreement between two start sets is 5.5 pp (A1) and 1.6 pp (A9).
   - Its best start is mostly not the prior mode.
   - Descriptive only, no rule: the forecast scores move the wrong way. The A1 fold means are 4.98-5.84 pp for O0, 4.97-5.98
     for O2 and 5.03-5.97 for O3. A9 fold 3 goes from 9.05 (O0) to 16.34 (O3).
   - So a deeper minimum of the window MAP objective is not a better forecast. The window over-fits z when the search goes
     looking for it.
4. **O2 from the prior mode is a well-defined, deterministic and budget-independent estimator.** It is the local MAP in the
   basin of the prior mode. Its descriptive forecast scores are close to production for both arms: A1 fold means 4.97-5.98
   vs 4.98-5.84 pp; A9 9.32-21.67 vs 9.05-22.43 pp. Its dependence on the start is a property of the model, not of the
   optimiser.

**Recommendation to the judge (the proposer's, not a rule outcome).**
- **(R-a) Adopt O2 from the prior mode for every inverting arm.** Name it in the paper for exactly what it is: "the local
  posterior mode reached from the prior mode by a converged per-cell Newton method". Report the convergence share, and the
  start-spread diagnostic as a stated limitation.
  - It meets every criterion except (c), and (c) measures the model's multimodality, which no optimiser can remove.
  - It removes the budget dependence and the unequal step counts between A1 and A9 (200 vs 150).
  - Its cost is small (section 2).
- **(R-b) Before the freeze, test whether the multimodality comes from the z prior being too weak for an early window.**
  - This is a separate decision row, because it changes the objective.
  - The check would compare a z prior weight of {1, 4, 16} (the same for A1 and A9; A2 has no z), on the same ISU training
    sides, with O2 from the prior mode.
  - Its criterion would be start spread (median <= 0.1 pp, p95 <= 1 pp) plus a non-inferiority guard on each arm's own
    pseudo-test score. The guard is needed because the weight changes the estimator.
  - Cost about 0.5 CPU-h. It is not run here, because it changes the model and needs its own committed rule.
- **(R-c) Do not adopt O3 (multi-start selection by objective).** It is less stable and, descriptively, worse.
- **Fallback if the judge rejects R-a:** fix z at the prior mode at test time (delta-only inversion, as A2). This is
  unimodal by construction, but it changes A9 into a population forecast with no window use, so P2 would then compare unequal
  window use. That is why it is not preferred.

## 9. Opponent's attack and the proposer's answer
(separate agent)

## 10. Judge's verdict
(separate agent)
