## Datasets proposal — revise

A separate descriptive section can satisfy the professor’s request to include both datasets, but it will be **supporting evidence, not a JES advance**. With eight CALCE conditions and five NASA groups, the results will be fragile; NASA’s conditions are also confounded with batch, and its measured capacity mixes ageing with cycling-condition effects. Keep these results out of the paper’s main evidence for the method.

The proposed within-campaign training and testing avoids directly testing cross-dataset transfer, and the “previously analysed” disclosure is necessary. It does not make the NASA analysis independent: prior exposure could still shape choices. The retired-topic risk is reduced, not erased, by prohibiting pooled training and cross-campaign error comparisons. Keep the language strictly descriptive, avoid “external validation” or transfer claims, and disclose the prior NASA analysis prominently.

A separate sign rule would imply more than these small, overlapping holdout designs can reliably establish. In particular, five NASA groups cannot reach a one-sided \(p<0.025\) sign-test threshold even if all five favor the model. For CALCE, finish the download, resolve missing blocks, and confirm the check-up and fade criteria before committing to results. If either dataset fails its identifier-based go/no-go, report that fact rather than substitute another set.

**Required changes:**

1. Freeze an addendum after Samsung’s freeze, with all splits, windows, exclusions, and go/no-go criteria fixed before fitting either dataset.
2. Report per-condition/group outcomes and uncertainty descriptively, separately by campaign; no inferential tier or cross-campaign comparison.
3. Disclose prior NASA label exposure and its batch/capacity-measurement confounds; describe CALCE’s small condition count and incomplete-download risk.

## KAN proposal — revise

An “identifiability-audited extraction protocol” could help reviewers interpret the KAN outputs, but calling it a novel methodological contribution is a stretch. D021’s synthetic study shows why audits matter; it does not establish that the proposed audit is distinct from existing model-selection or identifiability practice. Relevant prior work is **unverified**.

The synthetic rejection of monotone KAN (M) is not conclusive evidence that the architecture is inferior: the proposal reports strong sensitivity to initialization, only six seeds, no end-to-end refit, and no held-out RMSE decision metric. That is a fair reason to avoid a last-minute architectural change, not to claim M has been fairly ruled out. Do not add M to the primary analysis without a new, prespecified test that addresses those issues and applies sign constraints fairly to all relevant comparators.

Cap 2 permits only zero, linear, or log edge forms. It is compatible with “readable Kolmogorov-Arnold stress laws” if that phrase means compact extracted expressions that retain predictive accuracy; it does **not** support claims that the method identifies Arrhenius, power-law, or hinge physics. Cap 2 also cannot represent the proposed non-monotonic SOC behavior. The title may remain, but any physical interpretation must be narrower than the model’s label.

**Strongest legitimate KAN contribution within three days:** present **selective, design-aware extraction**. For each edge, report the number of distinct training stress levels, the number of shape parameters the design can identify, the eligible families under cap 2, and the fold/seed stability of the extracted form. Where the data cannot distinguish expressions, report that ambiguity rather than naming a discovered law. Test it by applying the same extraction and reporting rules to A15 and G15, the existing design-matched synthetic cases, and held-out Samsung conditions. The risk is that a reviewer sees this as careful reporting rather than a new KAN method; frame it as an audit protocol unless a targeted novelty check finds otherwise.

**Required changes:**

1. Use cap 2 as a complexity safeguard, but remove claims of recovered Arrhenius, power-law, hinge, or non-monotonic SOC mechanisms.
2. Add the design-level identifiability and fold/seed stability audit for both A15 and G15, with abstention when the form is not identifiable.
3. Treat the M result as inconclusive under the tested optimization setup; do not claim it was fairly rejected or introduce it into the confirmatory model.