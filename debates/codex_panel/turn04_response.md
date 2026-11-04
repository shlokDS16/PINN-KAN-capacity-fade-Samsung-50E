## Opponent’s verdict: revise, not accept as written

Design R addresses F1 by moving the experiment into data-poor regimes and giving the KAN a deliverable beyond raw accuracy. But it does **not yet show that PINN or KAN is the reason for any gain**. The data-efficiency question is valuable to battery-test planners; “physics helps when data are scarce” by itself is a familiar result, and the proposal itself cites small-sample PINN/PIKAN work. The exact prior results and their comparability to this task are **unverified** here. A JES paper must show *where* the prior helps, against a fair comparator, and what the learned law adds.

### 1. PINN claim and baseline fairness

The proposed P+ comparison is a **physics-informed family**—law, solution network, residual, and whichever stress map wins inner CV—against a data-only family. That can establish a useful system-level result, but it cannot attribute the gain to the residual, KAN, or rate-law structure. A win over that family comparator should not be described as “the PINN helps” without matched component ablations.

The fairness clause allowing data-only models to use Arrhenius-type features is necessary but underspecified. Every learner needs the same condition data, time/exposure coordinates, early-window summaries, and access to per-cell adaptation. Give the data-only side the same transformed inputs—such as \(1/T\), log C-rate and DoD, SOC terms, calendar time, and throughput—and tune them inside training folds. Otherwise the PINN receives physically engineered features and the comparator is accused of being deliberately uninformed. Conversely, a raw-feature model should remain as a separate baseline to show what feature engineering buys.

The P3 headroom on ISU/Sandia warns that full-data gains over flexible learners may be absent. It does not establish Samsung’s small-\(m\), small-\(k\) effect. The proposed ISU P6 is useful for rejecting a hopeless idea, but it cannot validate Samsung behavior or its storage arm.

### 2. KAN role: promising, but current endpoints risk decoration

Readable and fold-stable equations could be a real contribution if an electrochemist can check them and they predict a held-out condition. The current criteria—same selected function family in four of five folds, agreement in direction with A10, and extracted-law error within 10% of the numeric KAN—are mostly **internal consistency checks**. The 4/5 threshold is arbitrary, and agreement with a comparator fitted to the same dataset is not independent physical validation.

The electrochemical case needs more. Check whether calendar temperature dependence implies plausible activation energies, but use literature matched to the cell chemistry, SOC, and protocol; do not assume NCA/graphite unless verified. Check SOC dependence against the dataset authors’ reported non-monotonic behavior above 80% SOC, but only where there are measurements and sufficient replication. That behavior concerns calendar cells; it does not automatically validate cycling SOC-window effects. The storage temperature/lab confound further limits any activation-energy claim. **Literature ranges and the cell chemistry are unverified here.**

KAN versus a prespecified GAM/polynomial need not be a race if the claim is readability, but compare them anyway. At minimum, show equally sparse, rounded functions for both, out-of-fold prediction from each, and stability of *predicted response curves over the supported stress region*. If only the KAN can be simplified under the chosen extraction library, the comparison is unfair.

### 3. Statistics: useful grid, fragile gate

At \(n=40\), the ruling estimates an 80%-power detectable improvement of roughly **17–22%** for a different-family comparison at \(\rho=0.75\). Smaller effects are likely to be unresolved. Those are simulation assumptions, not Samsung power measurements; correlation and effect size at \(m=8\) remain unknown. The fixed-sequence rule also means that if \((m=8,k=2)\) fails, confirmatory claims at \(m=16\) or \(m=32\) stop—even if the advantage appears there. That is a poor fit for the stated question, “how many tests are needed?” Report the entire learning curve with simultaneous intervals or a preregistered trend/interaction test; reserve the gated claim for “benefit holds down to \(m=8,k=2\).”

Also make the \(k_{\text{full}}\) rule fixed from cadence before outcome inspection. The four grid points are not four independent replications: they reuse the same outer conditions and fitted folds. The proposed sign tests need a type-I simulation that includes fold-shared and lab-shared effects, as the proposal itself acknowledges. Do not describe the power as established until that is done.

### 4. Better use of the same data

Keep the data-efficiency experiment, but make it a **matched factorial ablation**:

- **Physics axis:** structured rate-law prior active versus removed/relaxed, with the same solution model, latent dimension, inputs, and tuning budget.
- **Stress-map axis:** KAN versus the strongest tuned GAM/interaction-GAM, using the same prior and training subsets.
- **Data axes:** \(m=8,16,32\) and \(k=0,2,k_{\text{full}}\), with identical outer held-out conditions and label-free condition subsets.

The primary PINN question becomes whether the physics prior changes the learning curve—especially at low \(m\)—relative to a data-only model given the same physics-motivated features. The KAN question becomes whether its extracted, rounded response law is stable and predicts held-out conditions as well as the full KAN and the matched GAM. Treat the soft-residual versus hard-integration comparison as secondary: when both encode the same rate law, the residual may add little beyond the prior. If soft PINN wins only under controlled law misspecification, say that is the demonstrated regime.

### Required changes before freeze

1. **Replace the single fixed-sequence result with an inferential learning-curve analysis.** Keep \(g_1\) as the threshold claim, but don’t let its failure erase evidence about \(g_2\)–\(g_4\).
2. **Match the comparison and attribution.** Same information and adaptation for data-only models; separate physics-prior and KAN effects with the factorial ablations. Do not call a family-level win a residual-specific win.
3. **Make the KAN result externally checkable.** Freeze the symbolic library and simplification rules; report held-out curve accuracy and stability against GAM/polynomial simplifications; restrict electrochemical validation to supported, independently sourced expectations, with chemistry and lab-confounding limits stated.

Without these revisions, Design R is more defensible than the original full-data comparison, but it still risks reading as a learning-curve study with a PINN/KAN label attached.