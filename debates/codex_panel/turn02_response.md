## 1. Verdict: revise; do not commit to the proposal as written

The identifiable-law question is the strongest novelty slice, but the proposal bundles too many hard problems for one week: a new two-mechanism ODE, hierarchical estimation, forecasting, KAN symbolic extraction, free-\(G\) and strict-PINN controls, synthetic recovery studies, several splits, and multiple datasets. That is a project plan, not a one-week paper plan.

There is also a modeling risk before the ML begins. The proposed \(y_2\) term accelerates exponentially with accumulated damage; the author must show that it stays well behaved over the forecast horizon and does not simply create a fitted knee. The two-mechanism interpretation is a modeling assumption, not evidence that those mechanisms were separately measured or identified. The proposal’s own concern that only about three post-baseline points are available in the median four-week window makes per-cell estimation of two offsets questionable. **Unverified:** the stated point counts and preliminary recovery thresholds depend on scratch analyses, not reproduced confirmatory runs.

A JES editor could say: “This is close to recent PINN/KAN degradation papers; what is the distinct contribution?” Reviewer 1 could say: “You call the laws identifiable, but the result is conditional on your chosen ODE and KAN class. Why do stable coefficients establish physical identifiability?” Reviewer 2 could say: “The model has many choices and baselines; show me a leakage-proof, held-out-condition experiment and a fair GAM comparison. Also, why use this two-term law?” The full text and methods of several cited papers remain unread per the proposal, so novelty is not yet secure.

**Revision:** make the paper a focused test of *when a stress law is recoverable from a designed ageing matrix*. Keep forecast performance as a validation endpoint. Drop the claim that the KAN has discovered mechanisms. Start with one fixed, defensible rate-law family and one dataset; only add the second dataset after the pilot works.

## 2. Must a genuine PINN be central?

A hard-constrained ODE with a KAN stress map is a reasonable **physics-informed model**, but it is not a strict PINN. If “PINN + KAN” must be the headline, a solution-network PINN can be built:

- **Solution network:** \(y_\theta(\tilde I,s,\eta_c)\), with \(y_\theta(0)=0\) imposed by construction. The KAN maps stress to positive rate parameters; \(\eta_c\) are cell offsets estimated from the early window.
- **Residual:** at collocation points, penalize \(dy_\theta/d\tilde I-R(y_\theta,\tilde I,s;\eta_c)\). Place points along training-cell trajectories, including beyond the observed early window into the forecast interval. Fit data only at observed reference-test points; never collocate on or tune against held-out future labels.
- **What it adds:** it can regularize a smooth solution between sparse observations and constrain the forecast region using a specified ODE. It cannot create evidence for the ODE beyond the window. If the same rate law is already integrated exactly, the hard ODE model enforces that constraint more directly and with fewer optimization choices.

So I would **not** make the PINN central by default. Run it as a controlled comparison against the integrated ODE model. A soft residual does real work only if the learned solution differs meaningfully from numerical integration and the difference improves a preregistered held-out forecast without sacrificing law recovery. Otherwise, call the method physics-informed KAN, not PINN. CPU feasibility is plausible for a small network, but the proposal’s training plan and compute time are **unverified**; pilot that before promising a PINN result.

## 3. Dataset choice

For identifiability, designed variation and replication matter more than cell count alone. ISU-ILCC’s stated 63 conditions with replicates is attractive, but weekly sampling and small pouch cells limit the resolution of a continuous-time rate law. The author also says cycle counts require a large `Cycling_json` download; if equivalent full cycles cannot be computed promptly and reliably, the proposed throughput coordinate is a blocker.

Samsung INR21700-50E appears more compelling for JES appeal if its stated 279 cells and 71 temperature/DoD/C-rate conditions are confirmed. Its 10.3 GB size and parse/runtime costs make it a risky one-week choice. **Unverified:** the available files, condition replication, and actual completeness of the release. Sandia is appealing for chemistry and stress breadth, but its usable replication structure and processed data status are also **unverified**.

**My choice:** ISU primary only if the overnight data pilot confirms usable cycling exposure, per-condition replication, and enough post-window observations. Otherwise use Samsung only if it is already accessible and a small, nonselective data audit shows a viable design. Do not quietly substitute a convenient subset. Add Sandia as secondary only if it can be processed without consuming the core analysis time; do not make an Arrhenius claim from a dataset whose temperature metadata and coverage have not been checked.

## 4. Can KAN beat a GAM or polynomial?

Potentially, if the stress-to-rate relationship has a localized onset or interaction—for example, a charge-rate threshold whose effect changes with DoD. That is a hypothesis, not an established advantage here. With only three or four stress inputs and a designed condition matrix, an additive spline GAM may be more stable, simpler, and easier to interpret.

Use identical splits and inputs, training-only scaling, comparable effective degrees of freedom, and equal tuning effort. Compare KAN against a degree-2 log-polynomial, additive spline GAM, and a GAM with prespecified interactions. Evaluate held-out conditions, not only held-out replicate cells; plot the learned map and uncertainty across stress-space coverage. If KAN does not improve held-out prediction or law recovery, report that plainly and remove KAN superiority from the claim.

## 5. Title, claim, and figures

**Title I would bet on:** *When Are Stress-Dependent Battery Degradation Laws Identifiable from Ageing Data?*

It avoids promising that KAN is superior or that learned expressions are electrochemical mechanisms. The claim should be conditional: under specified model classes and tested stress designs, quantify whether law parameters and predictive stress-response shapes can be recovered and remain stable under resampling.

A compelling paper needs four main figures:

1. Dataset condition map, replicate fade curves, and observed noise/resolution.
2. Synthetic recovery plot across the actual design and degraded designs, with structured and free-\(G\) models.
3. Held-out-condition forecast curves with the observed fitting window marked, alongside the strongest simple and flexible baselines.
4. Law stability: seed/fold/bootstrap envelopes and rounded symbolic law predictions against the numerical KAN, including regions where the design provides little support.

Those figures matter more than a long architecture schematic or a leaderboard table.

## 6. Biggest risk and tonight’s cheapest pilot

**Biggest risk:** the identifiability headline may be circular or untestable in the real data. A structured model can recover parameters from synthetic data generated by the same structure, while real-data coefficient instability may reflect model misspecification and sparse sampling rather than a meaningful failure of identifiability. Stable predictions can also coexist with unstable equations.

**Kill/confirm pilot tonight:** take a small, spread of conditions from the primary dataset; verify the per-cell time coordinate and observation cadence; fit the simplest proposed rate model and a log-polynomial/GAM using grouped condition holdouts. In parallel, generate synthetic data at that exact design with known stress slopes and realistic replicate noise, then recover the slopes across resamples. If the simpler model fits at the measurement-noise level, or slopes are not recoverable under the real design, stop the KAN-identifiability claim before building the larger model.