Turn 5 (you are the OPPONENT in debate D018: the confirmatory test after the size simulation failed). Read:
- C:\Users\Shlok\Downloads\PINN KAN battery paper\runs\prereg\stats_sim_v4\RESULT.md (sections 9 and 10: the plain exact
  sign test over n = 40 held-out conditions exceeds 1.2 x nominal size once intra-fold correlation of the latent log ratio
  reaches 0.03-0.05 or a random intra-lab correlation 0.015-0.023; proposed fallback = sign test with a fixed design effect,
  Beta-binomial null, rho_s0 = 0.03, 31 of 40 at 0.0125 and 30 of 40 at 0.025; P1S power 0.71 at a true 20 % reduction
  (rho 0.75) against 0.95 plain; P3 power 0.36 in the chain; a fold-blocked permutation cannot reject with 5 folds).
- C:\Users\Shlok\Downloads\PINN KAN battery paper\runs\prereg\PREREG_v4.md sections 9 and 22 (GAP-1 to GAP-11).
- C:\Users\Shlok\Downloads\PINN KAN battery paper\debates\D016_roles\02_judge.md section 2 (the plan the simulation tested).

Attack concretely:
1. Is lab a random effect or a fixed stratum for this estimand (3 labs: HM 17, INT 19, SIE 4 held-out conditions; temperature
   aliased with lab)? The statistician says with fixed labs rho_s0 = 0.02 suffices. Which target does a JES reader need?
2. Is a fixed design-effect sign test defensible to a reviewer, given that rho_s0 is assumed, not measured? Name better
   pre-specifiable options that keep validity under fold and lab clustering on CPU in a week, for example: repeated cross-fitting
   with more outer folds, a cluster bootstrap over folds, a lab-stratified sign test, a mixed model on log ratios with fold and
   lab random effects, or estimating rho from training-side inner-CV scores before the freeze (item f) and fixing the critical
   count from it. For each: validity, power at n = 40, and what must be frozen.
3. Is the power after the fallback (P1S 0.71 at 20 %, P3 about 0.3) acceptable for the approved outcome table, or should the
   headline cell, the margins or the graph weights change? Note the table itself is approved by the author (D017) and cannot be
   re-worded; rules that decide which row applies may be clarified before the freeze.
4. GAP-1: the approved clause (e1) says "most of the advantage came from the physics law". Propose a pre-specified numeric
   reading rule, or argue the wording needs the author's change.
5. Final: accept / revise / reject the fallback, with your 3 required changes.
Under 1000 words. No invented numbers or citations; mark anything unverified.
