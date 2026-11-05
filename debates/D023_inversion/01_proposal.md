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
- **The small check (section 7) was committed before running.** Its result is in section 8. The adoption rule uses only
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

## 8. Result (appended after the run)
(pending)

## 9. Opponent's attack and the proposer's answer
(separate agent)

## 10. Judge's verdict
(separate agent)
