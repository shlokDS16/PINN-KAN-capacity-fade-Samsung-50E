## 1. Prior-mode start: reproducible, not identified

Starting Newton from the prior mode is a defensible **deterministic estimator** if it is frozen and applied identically wherever z is inferred. It is not evidence that the cell’s latent is identified, or that the optimizer found a unique MAP. The check found converged minima with materially different forecasts: A1’s start-spread median is 7.8 pp; A9’s p95 is 50 pp. Calling the result “the MAP” would invite a reviewer to ask which mode and why.

Report convergence and start sensitivity separately: fraction meeting the gradient rule, budget sensitivity, forecast spread across the pre-specified starts, and whether different minima have similar objective values. Show this by arm and window length, and state that forecasts are conditional on the prior-mode basin. Do not select a basin using later outcomes. The pre-ruled verdict was **NONE**; adopting O2 can be a documented computational convention, but must not be presented as having passed the original start-independence criterion.

## 2. Choosing the z-prior weight

A pre-ruled check on ISU training sides is not test leakage, but it is weak grounds for a Samsung choice: ISU lacks the storage arm and has different stress coverage. It also risks consuming ISU’s development status if that dataset later becomes a fallback primary.

Prefer selecting among `{1, 4, 16}` by **Samsung-fold inner CV, using training conditions only**, with the same candidate set, window, and tuning budget for A1 and A9. Freeze the procedure before outer scoring; report the selected weight by fold. This parameter does not apply to non-inverting D* comparators or A2’s scalar delta, so fairness means equal access to the same window and training labels—not inventing a z parameter for those methods. If Samsung inner tuning is not already permitted by the frozen protocol, do not quietly add it: retain the existing weight and disclose the sensitivity.

## 3. Better options in 1–2 days

- **Inner-CV prior-weight choice:** strongest practical option. It addresses regularization under the actual Samsung training conditions without touching outer outcomes. Risk: the small inner folds may choose unstable weights.
- **Shrink z more for shorter windows:** plausible because early windows weakly constrain z. But a new window-dependent schedule is another modeling choice; tune it in inner CV or justify it independently and apply it symmetrically. Otherwise it looks post hoc.
- **Set z to its prior mode at k=0:** already consistent with the proposal. For k=2, dropping z may stabilize forecasts, but changes the model and the comparison; only consider it as a pre-specified arm/window rule tested in inner CV.
- **Reparameterize around `F=t*g`:** may improve numerical scaling, but cannot create information absent from the early window. It risks changing the model without fixing structural non-identifiability. Speculative as a quick remedy.
- **Marginalize over z:** conceptually best when the posterior is genuinely multimodal, but averaging starts is not posterior integration. A defensible posterior forecast needs a specified distribution and integration method; that is a larger, riskier change for this timeline. Report a sensitivity envelope now; pursue marginalization later.

## Verdict: revise

1. Use prior-mode Newton only as a frozen, reproducible operating rule; disclose that it chooses a basin and publish the start-sensitivity diagnostics.
2. If tuning z’s prior weight, do it in Samsung inner folds for both A1 and A9, training conditions only. Otherwise keep the weight fixed.
3. Do not claim the inversion is identified or start-independent. If that property is essential to the paper’s claim, the current evidence does not support it.