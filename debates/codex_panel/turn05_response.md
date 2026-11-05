## Opponent’s verdict: revise the fallback

The simulation invalidates the plain exact sign test for the dependence levels tested. The Beta-binomial sign test is a defensible **assumption-based fallback**, but not a distribution-free repair: its validity depends on the average sign correlation staying below the prespecified bound. The simulation supports \(\rho_{s0}=0.03\) within its tested R4 envelope; it does not establish that Samsung’s dependence lies in that envelope.

### 1. Labs: fixed strata are the defensible target

There are only three observed labs, and temperature is partly aliased with lab. The supported estimand is therefore performance over **held-out conditions in these observed labs**, with fixed, disclosed lab weights. It is not performance for a random population of future labs. Treating lab as random would imply broader generalization the design cannot support; estimating a random-effect distribution from three labs is fragile. Temperature and lab effects also cannot be disentangled where the design has no overlap.

Report lab-specific results and define the aggregate weights before scoring. Keep the simulation’s conservative fold-dependence allowance: fixed lab strata do not remove dependence from fold-shared model fits. The statistician’s \(\rho_{s0}=0.02\) result is relevant only under its fixed-lab assumptions; it is not evidence that the observed sign dependence is that small.

### 2. Is the fixed design-effect test defensible?

It is defensible **only as a sensitivity-calibrated, model-based test**. The assumed \(\rho_{s0}=0.03\) requires 31/40 positives at 0.0125 and 30/40 at 0.025. Those cutoffs are conservative in the simulated R4 region, but the guarantee depends on the assumed exchangeable sign-correlation bound. The preregistration must say that explicitly; do not call it an exact test without qualification.

Other options have material limits:

- **Lab-stratified sign test:** targets fixed labs, and can be exact under independent signs within strata. It does not solve fold-shared dependence. The SIE stratum has only four conditions, so separate lab-level tests will be weak.
- **Cluster bootstrap over labs or folds:** not credible with only three labs and five folds; cluster count is too small for dependable coverage.
- **Mixed model with fold and lab random effects:** possible computationally, but its inference would be model-dependent and poorly supported with so few clusters. It does not rescue temperature attribution.
- **More outer folds or repeated cross-fitting:** useful to check split sensitivity, but the repeated predictions do not create new independent conditions. Do not treat repeats as a larger \(n\).
- **Estimate dependence from training-side inner-CV scores:** the cleanest calibration aid, if frozen before outer scoring. Predefine an upper-bound rule, for example \(\rho_{s0}=\max(0.03,\text{one-sided upper bound from training-side estimates})\), and compute the critical count from that value. This remains assumption-based: inner-CV dependence may not equal outer-test dependence.

There is no distribution-free method here that retains useful power under arbitrary fold and lab clustering. The paper should state that limitation and show results across prespecified dependence bounds.

### 3. Power and approved outcome table

P1S power of 0.71 at a true 20% reduction, and P3 chain power around 0.36, are weak for a paper whose approved outcome table can make the headline depend on those nodes. A failed node may reflect low power, not evidence of no benefit. Keep the approved wording and table, but qualify conclusions by intervals and the simulation’s assumptions.

Do **not** relax the practical margins after seeing the power results. Keep \(g1=(8,2)\): it is the scientific target, and changing it to obtain significance would change the question. Before freeze, test a graph that allocates more error budget to the P chain than the current half-and-half split, then report its simulated type-I error and power. That is a rule clarification, not a table rewrite; it trades power for the K chain, so disclose the tradeoff. If it does not materially improve chain power, freeze the current graph and accept that the confirmatory result may be inconclusive.

### 4. Define “most of the advantage”

GAP-1 needs a numeric rule before freeze. At \(g1\), define total gain as the median paired log error ratio \(L_{\text{total}}=\operatorname{median}\ln(S_{D*}/S_{A1})\), and law gain as \(L_{\text{law}}=\operatorname{median}\ln(S_{A9}/S_{A1})\). Only if \(L_{\text{total}}>0\), “most” means \(L_{\text{law}}\ge 0.5L_{\text{total}}\), with a prespecified interval for \(L_{\text{law}}-0.5L_{\text{total}}\) reported. If its interval includes zero, the paper must not say “most.” This clarifies the approved clause without changing its wording. Because medians do not generally decompose across the A9→AG→A1 ladder, do not attribute the remaining share to KAN by subtraction.

### Three required changes

1. Freeze the estimand as performance over the **observed labs**, with prespecified weights and lab-specific reporting; make no random-lab or isolated-temperature claim.
2. Retain \(\rho_{s0}=0.03\) only as an explicit assumption-based fallback; add a training-only upper-bound sensitivity rule, and report its dependence sensitivity.
3. Before freeze, define the “most” criterion and simulate the graph-weight alternative. Do not change the approved table or margins; if power remains low, report inconclusive evidence as such.