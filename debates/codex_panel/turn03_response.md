## 1. Still viable for JES?

**Yes, but as a narrow, conditional advance—not a claim that PINN-KAN beats data-driven models.** P3 says tuned learners are already near the replicate floor on ISU and Sandia. There, the honest result is parity in accuracy plus any demonstrated physical consistency. Samsung remains the decisive primary test; its corresponding headroom result is still pending.

The strongest honest headline is: **a joint calendar-and-cycle model uses storage and cycling experiments to predict held-out ageing conditions, while controlled ablations test whether its residual and learned stress maps add value.** Novelty remains “as a combination” with only moderate confidence in the re-audit; Zhang et al. and Hallinger et al. are still unresolved, so don’t overstate priority.

A JES reviewer is most likely to call this a real advance if the model **predicts held-out conditions and a held-out storage condition from early check-ups**, and the result survives comparison with Stroebl’s semi-empirical model and matched data-only, hard-ODE, and GAM/MLP controls. A tiny RMSE gain alone will not do it. If the soft PINN ties or loses to exact integration, report that plainly and drop the claim that the residual improves forecasting.

## 2. What to improve first, by impact per day

1. **Resolve the closest-prior-art and comparator question.** Read Zhang et al. (*JES* 182, 125097), Hallinger et al., and Stroebl et al. (*JES* 142, 119552) in full. Zhang is specifically flagged as a PINN on Samsung 50E; its dataset and task must be checked, not inferred from its title. Stroebl is the mandatory same-data calendar-plus-cycle comparator. A novelty overlap or an unfair baseline could sink the paper outright.
2. **Make the temperature claim statistically defensible.** The 35 °C cells all come from one lab; that is not identifiable as a temperature effect. See section 4.
3. **Simplify the confirmatory question and analysis.** The draft has many arms, tests, gates, and figures. Preserve the primary held-out-condition forecast and a small set of diagnostic ablations; treat the rest as supporting or exploratory.
4. **Add a restrained physical plausibility check.** Compare the fitted calendar temperature dependence with activation-energy ranges from relevant literature only after matching chemistry, SOC, and test protocol. Report differences and limits. **Unverified:** the relevant literature values have not been checked here; a numerical “agreement” claim is premature.
5. **Only then add cross-dataset panels.** ISU and Sandia are useful evidence of transportability, but P3 supports non-inferiority there, not superiority. Keep those claims separate from the Samsung result.

A well-resourced group would likely have more independent cells, replicated temperature-by-lab combinations, and validation on another cell design. The immediate deficit is not model scale; it is the lack of independent evidence that separates temperature from lab and validates the learned law.

## 3. Is there a better use for the PINN residual?

The strongest use is the draft’s proposed **soft coupling of a flexible solution surface to a calendar-plus-throughput rate law**, with collocation in the unobserved forecast interval. This tests whether a soft residual helps under model mismatch. It should be judged against exact integration of the same law, not presented as inherently better.

Collocation at untested temperatures or “calendar twins” can make a forecast obey the assumed law there, but it **cannot validate** that temperature response. It is a model-imposed extrapolation. Coupling storage and cycling arms is scientifically useful because storage informs time-driven fade and cycling informs throughput-driven fade; however, if both arms are already encoded in the ODE, the residual adds no independent constraint beyond that law. Likewise, a residual enforcing consistency between check-up capacity and measured throughput can be valuable as a diagnostic, but exact integration enforces the same consistency more directly.

So keep these as diagnostics or ablations. A residual map is informative only if its error can be compared with observed departures or an independent validation set; otherwise it visualizes model disagreement without establishing which model is right.

## 4. Temperature–lab confounding

Do **not** call the 35 °C result temperature extrapolation or attribute its error or success to temperature alone. All 35 °C cells being from lab INT means temperature is aliased with lab; stage is also partly entangled. Adding lab and stage covariates cannot identify separate effects where the design has no overlap.

Frame the 35 °C holdout as **transfer to a combined temperature–laboratory condition**, and state the confound beside the result. Show the design map colored by both lab and stage. Run a sensitivity analysis on the overlapping temperature/lab combinations where such overlap exists, and report whether the learned temperature response is stable there. If the overlap cannot support that analysis, present the 35 °C result as a bundled domain holdout and remove temperature-specific language from the abstract and title. Collocation at 35 °C storage does not cure the confound; storage at 35 °C was not experimentally observed.

## 5. Three biggest preregistration weaknesses

1. **The primary claim still overreaches the observed headroom.** H1c switches between superiority and non-inferiority based on a training-side floor rule; Samsung’s P3 result is pending. Freeze that decision using Samsung training folds before scoring outer test folds. Given ISU/Sandia P3, parity with flexible learners is plausible, not a fallback failure.
2. **The temperature claim and residual mechanism are underidentified by the design.** The draft acknowledges the 35 °C/lab alias but leaves Test C as a conditional temperature claim. Reword it as joint domain transfer now; specify which overlapping strata can support a temperature-specific sensitivity analysis. Treat unsupported “calendar twins” as extrapolative constraints, not evidence.
3. **Too many confirmatory contrasts and decision branches for the available condition counts and compute budget.** The draft has a three-test Holm family, secondary families, multiple gates, synthetic generators, and 10–14 arms, while the condition is the statistical unit. This risks low power and makes the conclusion hinge on a complicated outcome tree. Choose one primary endpoint and the smallest set of essential contrasts: PINN vs same model without residual, KAN vs strongest GAM/MLP stress map, and the Stroebl comparator. Predefine all other analyses as secondary or exploratory.

Finally, the draft should resolve its open items before freeze: stage-aware cell identity, the Stroebl implementation details, MLP stress-map arm, model-capacity matching, Samsung-specific headroom rule, and whether Stroebl belongs in the primary multiplicity family.