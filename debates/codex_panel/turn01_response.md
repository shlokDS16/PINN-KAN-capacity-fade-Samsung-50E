## Panel verdict

The obvious “PINN + KAN improves SOH accuracy” paper is a weak bet. The space is already crowded: a PIKAN paper in *Journal of Energy Storage* (2026) reports SOH estimation and symbolic analysis on four datasets, and PGKAN (article 124768) also reports joint SOH estimation and degradation discovery. A 2026 PIKAN paper further adds RUL prediction on the MIT–Stanford–Toyota fast-charging dataset. These are reported abstracts; I have not independently checked their full methods or results. ([PIKAN, JES](https://www.sciencedirect.com/science/article/pii/S2352152X26005244), [PGKAN, JES](https://www.sciencedirect.com/science/article/pii/S2352152X26044324), [PIKAN RUL paper](https://www.mdpi.com/1996-1073/19/16/3742))

### 1. Early-life lifetime forecasting with stress-aware degradation dynamics

**Working title:** *Early-Cycle Lifetime Forecasting Under Variable Battery Use: A Physics-Regularized KAN Study*

**Question:** Can a model forecast a held-out cell’s capacity trajectory or cycle life from early-life measurements and known cycling conditions, rather than estimate SOH from features of the same cycle?

**Physics prior and method:** Enforce non-increasing capacity with accumulated cycling and nonnegative degradation rate. Treat the chosen exposure variables—such as charge/discharge rate and depth of discharge—as inputs to the rate law. This is a modest empirical prior; do not claim it is an electrochemical mechanism. Use a KAN to represent the rate law, then integrate it forward from the early-life state.

**Dataset:** Oxford’s public aging dataset is a candidate: its catalog describes 238 cells tested across 63 conditions involving charge rate, discharge rate, and depth of discharge. Availability, schema, and suitability for a clean early-life forecast split are **unverified**. ([dataset catalog](https://datasetcatalog.nlm.nih.gov/dataset?q=0002815342))

**Main experiment:** Train using only a fixed early-life window per training cell; forecast the remaining capacity trajectory and threshold life for entirely held-out cells. Compare forecast errors over the full trajectory and at the end-of-life threshold. Pick the early-life window and threshold before looking at test results.

**Baselines a JES reviewer will demand:** Per-condition empirical curve fit; linear or regularized regression; MLP and KAN without physics; MLP with the identical physics loss; and established trajectory-fit models such as exponential or power-law degradation, if compatible with the data. Include ablations for monotonicity and exposure inputs.

**Biggest risk:** Early-life capacity may not identify later-life behavior well enough. A flexible KAN could fit the observed trajectories while adding no useful forecast skill.

**Why it beats the others:** It targets the clearest gap in the supplied prior-art summary: future trajectory prediction for an unseen cell from early data and operating conditions. **Why it might fail:** Available data may not provide sufficiently frequent early-life measurements or consistent life endpoints; the stated dataset metadata alone does not establish that.

### 2. Test whether KAN-discovered stress laws are stable and predictive

**Working title:** *Are Battery Degradation Laws Discovered by KANs Identifiable? A Multi-Stress Reproducibility Study*

**Question:** Do learned symbolic degradation laws recover stable, predictive stress dependencies across random seeds and training-cell subsets?

**Physics prior and method:** Require capacity loss to be nonnegative and capacity retention to be non-increasing. Encode temperature through a physically motivated temperature dependence only if the dataset has measured temperature and the needed metadata; otherwise do not claim an Arrhenius test. Use KAN for the rate function, then apply symbolic regression to its learned functions.

**Dataset:** Sandia’s repository lists temperature-dependent degradation data for commercial NMC and NCA cells; Battery Data Commons describes an LG HE4 dataset with temperature, depth-of-discharge, and other cycling stresses. Which has the accessible per-cell metadata and sufficient repeated conditions for this exact analysis is **unverified**. ([Sandia repository](https://www.sandia.gov/ess/tools-resources/rd-data-repository), [Battery Data Commons](https://batterydatacommons.org/find-data/))

**Main experiment:** Repeat fitting across seeds and resampled training cells. Measure symbolic-formula stability and out-of-sample prediction on held-out conditions, against fitted conventional stress-life models. Report cases where formulas differ despite similar predictions; a good fit alone does not establish an identifiable physical law.

**Baselines a JES reviewer will demand:** Conventional parametric stress-life model; MLP with the same monotonicity prior; KAN without symbolic extraction; and symbolic regression fitted directly to data. Compare predictive performance and formula stability, not just interpretability examples.

**Biggest risk:** Too few cells per stress condition may make the proposed identifiability analysis inconclusive—or the dataset may already have been used for closely related stress-law discovery.

**Why it beats the others:** It directly probes whether KAN “discovery” survives perturbations, rather than repeating a best-seed symbolic expression. **Why it might fail:** KAN and symbolic regression can yield different expressions with equivalent predictions; formula agreement is not the same as physical identifiability.

### 3. Audit whether a learned PDE residual constrains SOH at all

**Working title:** *When Does a Learned Degradation Residual Constrain Battery SOH? A Controlled PINN–KAN Ablation*

**Question:** Does a jointly learned free-form dynamics network add predictive or physical value, or can it simply fit the estimator’s derivatives?

**Physics prior and method:** Reproduce the cited Wang-family residual structure and compare it with explicit monotonicity and a prespecified degradation ODE. A free network \(G\) in \(u_t=G(t,x,u,u_t,u_x)\) is not automatically informative: unless its inputs, capacity, and training setup prevent it from matching the left side trivially, the residual may impose little restriction. That is a hypothesis to test, not a conclusion about the paper’s implementation. Use matched KAN/MLP estimators and residual modules.

**Dataset:** PINN4SOH’s XJTU, TJU, MIT, and HUST feature tables are directly relevant, but the author prefers another dataset. Wang et al.’s paper and data repository are linked from the reproduction materials. ([Wang et al., Nature Communications](https://www.nature.com/articles/s41467-024-48779-z), [data download notes](https://github.com/WinchellZhang/wang2024-pinn4soh-reproduction/blob/main/DATA_DOWNLOADS.md))

**Main experiment:** Hold the estimator and data fixed; compare no residual, free-\(G\) residual, explicit ODE residual, and monotonicity-only constraint. Test residual magnitude, sensitivity to loss weight, and held-out-cell prediction. This is a focused audit, not a new broad benchmark.

**Baselines a JES reviewer will demand:** The original PINN architecture; data-only MLP/KAN; same backbone with explicit monotonicity; and a conventional explicit degradation law.

**Biggest risk:** It may read as a narrow critique or replication rather than a sufficiently novel battery contribution, especially if the central residual is not in fact unconstraining.

**Why it beats the others:** It is the most direct test of the lead’s open question and can be a compact controlled study. **Why it might fail:** The result may depend on implementation details, and the PINN4SOH features do not themselves establish a future-cell forecasting contribution.

## Ranking and one-week bet

1. **Candidate 1**, if the Oxford data pass a rapid schema and split-feasibility check. It has the clearest distinct prediction task and avoids making symbolic interpretability the main claim.
2. **Candidate 2**, if one stress dataset supports repeated-condition holdouts and enough cells for meaningful resampling.
3. **Candidate 3**, the most feasible controlled audit, but the weakest standalone novelty case.

**One-week bet:** Candidate 1, with a narrow scope: one dataset, one prespecified early-life window, held-out cells, and trajectory forecasting. Do not add RUL as a second headline unless the pilot confirms reliable end-of-life labels and forecasting.

## Verify before committing

- Read the full PIKAN and PGKAN papers and supplements; inspect their splits, feature definitions, symbolic-regression protocol, and whether their “discovered” equations are tested across seeds or training subsets. Read the full PI-EKAN and Verhulst-based papers too. The search results establish titles and abstracts, not detailed methods.
- Inspect the Oxford dataset files and license; verify cell IDs, condition metadata, measurement cadence, capacity definitions, and whether a held-out-cell early-life experiment is possible without using future information.
- For Candidate 2, inspect Sandia and Battery Data Commons metadata and original papers; verify per-cell condition coverage and repeated cells before choosing a dataset.
- Run a small pilot: compare data-only KAN, matched MLP, and monotone rate model on cell-held-out splits. Check whether early-life data beat a simple per-condition curve fit. If they do not, stop Candidate 1.
- For Candidate 3, inspect Wang et al.’s equations and code before asserting the learned residual is vacuous. The claimed tautology is **unverified** until that audit.