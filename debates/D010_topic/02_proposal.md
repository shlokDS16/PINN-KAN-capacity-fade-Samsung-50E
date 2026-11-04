# D010 proposal (proposer, 2026-11-04)

Role: proposer. I do not validate this; the opponent and judge do. Decision to be taken: topic, title, method, datasets, experiments of the JES paper.

**Reading depth (CONTRACT section 1).** I read in full: CONTRACT, 00_candidates, 01_novelty_audit, GAPS, PIKAN.md, PINN4SOH.md, Codex turn 01, the JES guide, INVENTORY.md, and the ISU-ILCC `README_V2.0.pdf` (converted, full text). I looked at the ISU `capacity_fade.zip` CSV text (251 cells) and the Oxford readme. I read **no paper** (PiDDM, PIKAN, PGKAN, JECS addd4e, arXiv 2607.16864, Gasper, ISU authors' arXiv 2307.08382 are all unread by me); every statement about them is the novelty auditor's or the lead's, and is marked as such. Numbers marked **[scratch]** come from `debates/D010_topic/pilot_scratch/` (scripts plus `output.txt`); they are not results and must be reproduced under `runs/` by scripts in `code/` before any use. The group-stress table of ISU (Table A1) was transcribed by hand from the README into the scratch script and must be re-checked against the PDF.

## 1. Research question and claim

**Question.** If battery capacity fade is written as a stress-conditioned rate law on a physics backbone, with the dependence of the rate on charge rate, discharge rate, depth of discharge (and temperature where measured) carried by a Kolmogorov-Arnold network, are the stress laws the network learns determined by the data (identifiable), and does the same model forecast the capacity trajectory and end of life of an unseen cell from its first few weeks of cycling?

**Single claim (falsifiable).** At the size and cadence of public ageing matrices (63 conditions, 4 replicate cells, weekly reference tests), a physics-backbone model whose stress dependence is a KAN (a) recovers the exponents and shapes of known stress laws on synthetic cells with the same design, (b) returns stable, rounding-robust stress laws across seeds, bootstrap resamples of cells and condition-held-out folds on the real cells, and (c) forecasts held-out cells at least as accurately as the best flexible data-driven baseline and more accurately than the semi-empirical, PiDDM-style and PIKAN-style baselines, whereas a PIKAN-style free-G model of identical capacity fails (a) and (b).

**What refutes it (stated now, fixed in the preregistration before confirmatory runs).**
- R1: synthetic recovery error of the three principal stress slopes at the ISU design is above the threshold (proposal: median relative error above 25 percent with the well-specified generator; the "pass" threshold of 10 percent is fixed after pilot P3 and before any real-data confirmatory run).
- R2: the free-G model recovers the stress laws as well as the structured model (paired difference not above the preregistered 2-fold margin).
- R3: the primary endpoint (section 6) of the proposed model is not better than the best of {semi-empirical, PiDDM-style, PIKAN-style, Wang-style} by a paired test, or is worse than the best flexible baseline (LightGBM / GP on stress plus early-window summary) by more than the preregistered non-inferiority margin.
- R4: a log-polynomial (GAM) stress map matches the KAN on every endpoint and is equally identifiable. Then the KAN is decoration; the paper's claim is rewritten without KAN superiority (the title would change; see section 2).
If R1 or R2 occurs the novelty-bearing part (C2) is dead and the topic must be re-opened; the remainder is the incremental C1 slice that the audit rates INCREMENTAL.

## 2. Titles

1. **Identifiable stress laws of lithium-ion battery capacity fade from physics-informed Kolmogorov-Arnold networks** (preferred: it names the only part the audit judged novel and the model class).
2. Forecasting capacity fade of unseen lithium-ion cells with learnable, identifiable stress-dependent rate laws
3. Learning degradation laws from designed ageing matrices: a physics-informed Kolmogorov-Arnold approach with identifiability tests

Preferred: 1. Fallback if R4 occurs: option 2 (no KAN in the title). The JES guide discourages naming optimisation techniques in the title; "Kolmogorov-Arnold" here is the model class, not a tuner.

## 3. Method

### 3.1 State, coordinate, data per cell
- Cell c, rated stress vector s_c = (ln C_chg, ln C_dis, DoD), standardised with training-fold means and standard deviations only. For temperature datasets add u = 1/T (K^-1). ISU stress values per group are in the README (Table A1); the realised mean DoD is a measured property of each group.
- Capacity retention x(Θ) = Q_RPT(Θ)/Q_0,c where Q_0,c is the cell's own week-0 reference capacity (known at time zero). State y = 1 - x.
- **Time coordinate: equivalent full cycles Θ = cumulative discharged Ah / Q_0,c** (throughput). Rationale: groups differ by up to a factor of several in cycles per week, so a law in calendar weeks mixes cycle count and per-cycle damage. ISU gives weeks on test in `capacity_fade`; cycle counts need `Cycling_json` (10.2 GB, README section 4.1; per-cell file with per-cycle `capacity_discharge`). **Dependency D1** (needs the lead's yes; pilot P0 below fetches about 12 cells first). Fallback F1 if D1 is refused: weeks on test plus an analytic cycles-per-week from rates and DoD, with the error of that approximation checked on the 12 pilot cells; claims restricted to "per week of continuous cycling".
- Constant 30 C in ISU (README 3.2): the primary dataset has no Arrhenius test; temperature is treated in the secondary dataset (section 5).

### 3.2 Rate law (physics backbone)
Two loss mechanisms, y = y_1 + y_2, integrated in Θ from y(0) = 0:

- dy_1/dΘ = A_1 / (y_1 + y_0)  (self-limiting, SEI-type growth; sqrt(Θ) law as y_0 → 0)
- dy_2/dΘ = A_2 · exp(γ y)  (throughput-driven loss that accelerates with accumulated damage: knee / plating / active-material-loss surrogate)
- ln A_i = f_i(s) + δ_{c,i} [+ Arrhenius term −(E_i/R)(1/T − 1/T_ref) where T is measured]

Global parameters (shared by all cells): y_0 > 0 (softplus), γ ≥ 0 (softplus), E_1, E_2 ≥ 0 (secondary dataset), observation noise σ (retention units), prior scales σ_δ,1 and σ_δ,2. Per-cell parameters: δ_c = (δ_c1, δ_c2), two log-rate offsets (cell-to-cell variability). The stress dependence f_i(s) is the KAN (3.3). Only the offsets δ_c are per cell; nothing else is cell-specific, which is what makes the stress law global and testable.

Why this form. (i) It is a state-dependent rate law, not a curve fit: r(y, Θ, s). (ii) Positivity and monotonicity hold **by architecture**: A_i = exp(·) > 0, y_1 + y_0 > 0, so dy/dΘ > 0; no monotonicity penalty. (iii) of the 232 ISU cells with at least 10 reference points, 84 percent show a later-third mean fade rate above the first-third rate **[scratch, per week, not per Θ]**, so an accelerating term is needed; a pure power law cannot represent it. (iv) Each term has a physical reading that reviewers recognise (diffusion-limited SEI growth; plating/knee feedback) without claiming mechanism identification, which is exactly what C2 tests.

**Backbone tournament, decided on training cells only (inner CV, tie goes to the simpler):** B1 power law y = A Θ^z (state form); B2 sqrt + linear (γ = 0); B3 the form above; B4 B3 with a free third term. The preregistered main model is the winner of the tournament on the training folds of the first confirmatory fold; the other backbones are reported in the ablation table. This guards against "chosen after seeing the test cells".

### 3.3 Where the KAN sits
Primary: **the KAN is the stress-to-log-rate map**, f: R^3 → R^2 (R^4 with 1/T), small: width [3, 2] (additive, a log-additive generalised additive model with learned univariate edges) or [3, h, 2] with h ∈ {2, 3} (interactions). Width chosen by inner CV. This is the natural KAN use case (low-dimensional scientific map, edges inspectable, symbolic fitting feasible; Liu et al., arXiv 2404.19756 and the KAN 2.0 paper arXiv 2408.10205, both to verify), in contrast to PIKAN/PGKAN which feed 16 summary features and a free G.
Secondary (ablation row, not the headline): a bounded KAN correction κ(y, Θ, s) multiplying the total rate, ln R_total = ln R_backbone + κ, with L1 and a hard bound |κ| ≤ κ_max, to answer "does a correction help accuracy and what does it cost in identifiability?" (this gives an accuracy-identifiability frontier, one figure panel).

**KAN variant.** B-spline KAN (pykan `MultKAN`, cubic splines, grid 4 to 8 with grid extension, SiLU base off or on by inner CV), for three reasons: PIKAN and PGKAN use B-spline KANs, so the contrast isolates how the KAN is used; pykan provides pruning and symbolic fitting with a user-defined library; B-splines allow local non-linearities such as a plating onset hinge. Ablation at matched parameters: Chebyshev KAN, Gaussian-RBF KAN, MLP, log-polynomial GAM (degree 2) and an additive-spline GAM (the R4 control). Implementation uses PyPI `pykan` (MIT upstream); pin the version after reading its README and API. The PIKAN repository has no licence, so no code is copied; I reimplement (PIKAN.md section 8).

### 3.4 Positivity, monotonicity
Architecture only (3.2 ii). The soft PINN-form (3.5) adds a collocation residual but still uses the same positive R, so it inherits positivity. Capacity regeneration and RPT noise are handled by the observation model N(0, σ²) on retention, not by a constraint. (ISU is a set of reference-test capacities at C/5, so regeneration is minor; NASA-type regeneration is out of scope and said so.)

### 3.5 The PINN element, stated plainly
The primary model is **hard-physics**: the ODE is integrated, so the "residual" is identically zero and there is no loss weight to tune. That is physics-informed in structure (ODE-constrained learning), not in the strict PINN collocation sense. To meet the project brief and to answer "does the PINN residual add anything" (candidate C3, reduced to a control), I include the strict form as variant M_P:
- Solution network y_ψ(Θ; s, δ_c) (small KAN or MLP) with hard initial condition y_ψ(0) = 0 by construction.
- Loss = data term at reference-test points + λ_ic term + λ_res · mean over collocation points of [dy_ψ/dΘ − R(y_ψ, Θ, s, δ̂_c)]².
- **Collocation points:** 256 per training cell, log-uniform on (Θ_K, Θ_hor] where Θ_K is the end of the early window and Θ_hor is where the current model's own forecast crosses y = 0.4 (self-referential, uses no test label), resampled every optimiser step. Unlabelled points beyond the observed window are where a PINN has its argument (physics enforced in the forecast region).
- λ_res chosen by inner CV on training cells (grid, 5 values on a log scale); the optimum at an edge triggers an extension of the grid.
Decision rule: both hard and soft forms are reported; the headline model is the one that wins on inner CV, with ties to the hard form. If the lead requires a strict PINN as the headline, the soft form is promoted; the identifiability programme runs on both.

### 3.6 Integrator and training
Vectorised RK4 over all cells in one batch on CPU, log-spaced Θ steps (400 steps; converge-check by halving, relative tolerance 1e-4; Dormand-Prince via torchdiffeq as a check if the package is available; **API and install status to verify**). Initial rate scales as A_1 / y_0, so y_0 is bounded below (initial prior from the first reference test). Optimiser: Adam for 2,000 steps then L-BFGS refine, learning rate and weight decay tuned (nuisance); sparsity regularisation of the KAN edges (pykan-style L1 plus entropy, weights tuned by inner CV) so that pruning and symbolic fitting are meaningful (PIKAN used none, PIKAN.md section 2). Loss, joint MAP over training cells:
L = Σ_c Σ_j (Q_obs,cj − Q̂_cj)² / (2σ²) + Σ_c ‖δ_c‖²_Σ^-1 / 2 + λ_1 · sparsity(f) + λ_s · smoothness(f).

### 3.7 Per-cell parameters for an unseen cell from its first K weeks (causal)
Test-time: the cell's stress s_c and its early-window points (week 0 to W) are the only inputs. Estimate δ̂_c = argmax of the Gaussian likelihood of the window points under the integrated ODE plus the learned prior N(0, Σ) (MAP, Gauss-Newton or L-BFGS, 2 unknowns, with 3 to 7 data points in the window [scratch: median number of points including t = 0 is 3, 5, 7 for W = 2, 4, 6 weeks]); then integrate forward. No quantity uses data after the window; Q_0 comes from week 0; scaling constants are global. The prior regularises the 2-dimensional problem; cells whose window has fewer than 2 points after t = 0 are excluded from that window's evaluation and counted. 
Train-test alignment: the first version fits δ_c on the full trajectory of training cells (a posteriori) and applies window-MAP at test; the **amortisation gap** is measured by an ablation in which training cells' δ_c are themselves obtained by window-MAP (unrolled five Gauss-Newton steps, differentiable). Whichever is better on inner CV is the main model.
Honest note: this is a nonlinear mixed-effects (hierarchical) formulation, standard outside batteries; the paper does not claim it as new, it claims the stress law and its identifiability.

### 3.8 Symbolic extraction
For the trained KAN (after sparsity-regularised training): (1) prune edges by attribution threshold chosen on training folds; (2) for each remaining univariate edge φ_ij(s_i) fit a symbolic form from a restricted library {a·s + b, a·s² + b·s + c, a·ln(s)+b, a·exp(b s)+c, power a·s^p+b with p fitted, softplus/hinge max(0, s − s0) (onset)} with affine wrappers, via least squares on the edge's input-output samples; (3) choose per edge by an information criterion (not top R² alone), with ties to the simpler form; (4) rounding: coefficients rounded to 2, 3 and 4 significant digits; the symbolic model is re-integrated and scored on training-fold validation cells. **Success criterion fixed in advance: forecast RMSE ratio (rounded symbolic / numeric KAN) ≤ 1.10 at 3 significant digits** (GAPS item 4), and formula length reported. Library is deliberately restricted; PIKAN's extended library (bessel, sinc, cosh) is not used because it produced fragile formulas (PIKAN.md section 6.6).

## 4. Identifiability programme

All of it is CPU-only and uses the real designs and noise, so it can run before anything is spent on real-data fits.

### 4.1 Synthetic cells from known laws
Generators (the ODE solved with a fine step, different from the training integrator, to avoid the inverse crime):
- **S1 well-specified:** the section-3.2 backbone with known log-additive stress laws (power-law exponents on C_chg, C_dis and DoD; with 1/T for the temperature design), per-cell offsets δ_c drawn from a Gaussian.
- **S2 hinge onset:** as S1 but ln A_2 has a threshold term max(0, ln C_chg − c0) (plating onset). Tests whether the KAN finds a shape that a quadratic GAM cannot (R4).
- **S3 misspecified:** generator with a different knee mechanism (logistic accelerating term, or a Bacon-Watts two-regime power law) so the fit model is wrong; measures how recovery degrades and whether the stress ordering survives.
- **S4 free-G generator:** dy/dΘ drawn from a smooth random positive function of (y, Θ, s) (Gaussian-process draw), to check that the free-G model can fit trajectories without having a unique law.
**Parameter ranges.** Principle: no literature numbers enter the headline. The ground-truth stress exponents, hinge location and noise are **anchored on the real data**: first fit the backbone to the ISU training cells, then use the fitted values (and fixed multiples of them) as truth; noise level and cadence are the observed ones (the replicate spread in `capacity_fade`; within-condition standard deviation of ln(time to 80 percent) median 0.19 over 63 conditions [scratch]). Literature cross-checks (only as "plausible range" statements, all **to verify** before use): Ah-throughput power-law exponent and Arrhenius energy for graphite/LFP in Wang et al., J. Power Sources 196 (2011) 3942 (doi 10.1016/j.jpowsour.2010.11.134, from memory); holistic NMC ageing model of Schmalstieg et al., J. Power Sources 257 (2014) 325 (doi 10.1016/j.jpowsour.2014.02.045, from memory); Gasper et al. (2021) doi 10.1149/1945-7111/abdde1 (Crossref per audit, abstract only). Activation-energy sweeps in the secondary design are design choices (grid), not literature claims.

### 4.2 Design-size sweeps (the result a reader can use)
Recovery error versus (number of conditions: 8, 16, 32, 63) × (replicates: 1, 2, 4) × (reference-test cadence: weekly, 2-weekly) × (noise multiplier: 0.5, 1, 2) × (window W). 20 draws of the synthetic experiment per cell of the grid. Output: the smallest design at which the exponents are recovered within the threshold, which doubles as guidance for designing ageing matrices (JES scope: "testing, test procedures").
Design property already measured: the 63 ISU conditions are close to orthogonal in (ln C_chg, ln C_dis, DoD): pairwise correlations 0.00, −0.10, −0.34; condition number of the standardised design with intercept 1.44 **[scratch]**. Main effects are therefore estimable by design; the open question is whether the nonlinear two-mechanism law keeps them separable.

### 4.3 Metrics
- **Recovery:** relative error of each true log-slope (S1), curve distance ‖φ_ij − φ_ij^true‖ after removing the per-edge constant (S1, S2, S3), rank agreement of stress importance, top-1 symbolic-form accuracy (S2).
- **Stability (synthetic and real):** coefficient of variation of each fitted slope across 5 initialisation seeds; across 200 cell-level bootstrap resamples of the training cells (cluster by condition on Test B); across the 7 condition-held-out folds; Kendall W of the importance ordering; Jaccard overlap of the selected symbolic forms; edge-curve envelope width.
- **Local identifiability:** Fisher information eigen-spectrum and profile likelihood of the global parameters (y_0, γ, E_i, σ_δ) for one synthetic design; condition number reported (Raue et al., Bioinformatics 2009, **to verify**).
- **Rounding survival:** ratio defined in 3.8, on synthetic and real folds.

### 4.4 PIKAN-style free-G comparison
Free-G: dy/dΘ = G(y, Θ, s) with G an unconstrained B-spline KAN of the same parameter count (widths matched), no positivity beyond a softplus output option shown separately, trained with the same shooting loss (variant 1) and with the Wang-family PDE residual with u_t removed from G as in PIKAN (variant 2, PIKAN.md section 1). Evaluate: (i) trajectory fit (should be as good or better); (ii) recovery of the stress dependence by partial dependence of G on s versus truth; (iii) seed/bootstrap/fold stability of that partial dependence; (iv) rounding survival of its symbolic extraction using the same restricted library and, as a replication of the PIKAN notebooks, an extended library; (v) a direct non-uniqueness test: distinct G with indistinguishable trajectories (Hausdorff distance of trajectories ≤ noise vs distance between laws). This is the tested hypothesis, not an assumption: the expected outcome is "fits equally, identifies worse"; if it is not, R2 applies.

## 5. Datasets

**Primary: ISU-ILCC (Iowa State; figshare 22582234; CC BY 4.0; arXiv 2307.08382 per the README).** 251 NMC/graphite 250 mAh pouch cells, 63 unique conditions, three stress factors varied: charge C-rate (0.5 to 3.0), discharge C-rate (0.5 to 2.475) and mean DoD (4 to 98 percent); 62 conditions with 4 cells and 1 with 3; constant 30 C; reference performance test (C/5 and C/2) about weekly (half-weekly early for groups 20 to 64); README Table A1 lists all 63 conditions. The `capacity_fade` curves and `Q_interpolated` Q-V curves are on disk; all 251 cells fall below 80 percent retention; median time to 80 percent is 12.0 weeks (quartiles 8.6 and 16.9), median number of reference points 19 (quartiles 15 and 28) [scratch]. Why this dataset: it is a designed stress matrix with replicates (replicates give a direct noise floor and a clean split for the "unseen cell"), it is not a PINN4SOH set, it is public (CC BY 4.0), and the arrival of 63 conditions is the thing a stress law needs; PiDDM used XJTU (6 protocols). Limits (to be said in the paper): one temperature, small pouch cells, weekly sampling, no calendar-cycle separation.
**Held out.**
- **Test A (unseen cells, seen conditions):** replicate-wise 4-fold with fixed random assignment (seed in `runs/splits/`, not the C-index, which may track the cycler site); each condition keeps 3 of 4 replicates in training. Expected: a strong "condition median of the other replicates" baseline: leave-one-replicate-out median absolute error of ln(time to 80 percent) is 0.151 [scratch], so ties and defeats are possible and will be reported.
- **Test B (unseen conditions; primary):** 7 folds of 9 conditions, each fold stratified over the standardised stress space, test conditions inside the training range except in Test C; no cell of a test condition enters training or tuning.
- **Test C (stress extrapolation):** train on conditions with charge rate ≤ 2.0 C, test on charge rate > 2.0 C (19 conditions, about 76 cells; condition count from Table A1 [scratch]); report separately; hinge-law recovery (S2) predicts the hardest extrapolation here.
Test B and C are tests of the law's behaviour in stress space, not a study of how evaluation protocol changes accuracy (retired topic); no "inflation ratio between protocols" is reported or claimed.

**Secondary: Sandia (SNL) cycling data, Preger et al., J. Electrochem. Soc. 2020, doi 10.1149/1945-7111/abae37 (Crossref per audit), via the BatteryLife processed release (`SNL.zip`, Zenodo 19688272).** Why: temperature (several levels, per INVENTORY: 15 to 35 C; **to verify**), DoD and discharge-rate variation on LFP, NCA, NMC 18650 cells, cycled to 80 percent by design, throughput known per cycle. Needed for the Arrhenius part of the backbone and for generality across chemistries. **Status: the local `SNL.zip` is truncated (111,586,886 of 115,187,861 bytes, central directory missing, download gave up on DNS failure); resume with `curl -C -` (expected MD5 900a5bb283ffb0b3255da618118510b7 from DEFERRED_URLS.tsv).** Cells per condition, replicates, cycle-level capacity noise and file schema are **unverified**; the processed release is pickle: parse only with the allowlist loader (`code/data_audit/verify_raw.py`), never `pickle.load`. Held out: same two tests if the replicate structure allows it, otherwise cell-wise only with held-out temperature levels as the stress-extrapolation test. Each chemistry is analysed separately (no pooled-chemistry claim).
**Stretch / reserve (not in the plan, named for the rebuttal): Samsung INR21700-50E (figshare 25975315; 279 cells, 71 conditions over temperature, DoD, C-rate; 10.3 GB)**: the strongest design for the Arrhenius and temperature interaction test; use if SNL fails pilot P5 or if the opponent shows ISU+SNL insufficient. SNU (60 cells, four temperatures) is the second reserve.
**Not used:** XJTU, TJU, HUST, MIT. They are the PINN4SOH sets (no stress columns in the author's feature tables; INVENTORY), and the audit says PIKAN and PGKAN own estimation on them. If a reviewer demands comparability with PIKAN on its own task, a reproduction note on XJTU is a possible appendix, not a claim. TJU (25/35/45 C) is the only one of these with a real temperature factor; it stays out unless SNL and Samsung both fail.

## 6. Experiments and endpoints (preregistrable)

**Common forecasting task, identical for every model.** Input: s_c, Q_0,c, the reference points in the first W weeks (the "window"); output: retention at every reference test after the window. Every model, physical or not, gets the same inputs and the same permission to adapt to the cell from its window (a per-cell scale for the semi-empirical model, the δ_c MAP for ours, the window summary as static input for learned baselines).
- **Windows:** W ∈ {2, 4, 6} weeks; **primary W = 4** (5 points including t = 0 at the median; about a third of the median life). Cells whose life ends inside the window are excluded and counted (5.2 percent of cells have time to 80 percent ≤ 4 weeks, 2.4 percent ≤ 2 weeks [scratch]).
- **Forecast set F_c:** reference tests after the window up to the first test below 70 percent retention (so the 80 percent end of life and the knee are inside).
- **Primary endpoint (one):** cell-level RMSE of retention (percentage points) over F_c, macro-averaged over test conditions, **Test B, W = 4**, final frozen configuration, 5 seeds.
- **Secondary:** (S1) the same on Test A and Test C; (S2) end-of-life error |ln(Θ̂_80/Θ_80)| and the share within ±20 percent (and weeks if F1); (S3) remaining-useful-life error at +2, +4, +8 weeks after the window; (S4) MAE, MAPE (retention in percent) and R² for completeness, with the correct metric argument order (PIKAN.md section 6.7); (S5) forecast error versus W ∈ {2, 4, 6}; (S6) identifiability endpoints I1 to I3 below; (S7) SNL equivalents; (S8) wall-clock and parameter count.
- **Identifiability endpoints.** I1: median relative error of the three principal stress slopes on S1 at the ISU design (pass threshold fixed after P3); I2: seed, bootstrap and fold CV of the slopes on real cells and their ranking agreement (Kendall W); I3: rounding ratio ≤ 1.10 at 3 significant digits on real validation cells; each compared with the free-G model by a paired test over synthetic draws.
- **Tuning (all models, same rules).** Inner grouped CV on training cells only: by condition for Test B and C, by cell for Test A. TPE (Optuna) with 60 trials per model family for all families with more than 3 hyperparameters (30 to 300 trials, mixed space); closed-form or multi-start least squares for the semi-empirical models; same trial budget and search spaces reported; top-5 configurations reported; optimum at a search-space edge triggers an extension. No test cell is used for tuning, early stopping, backbone choice or threshold choice. Test folds are evaluated once per frozen configuration.
- **Seeds and statistics.** 5 initialisation seeds for the final runs; search seeds distinct. Unit of analysis: condition (Test B and C) or condition-averaged cells (Test A; 63 units, to avoid pseudo-replication across replicates). Paired Wilcoxon signed-rank on the per-condition difference, paired mean difference and ratio with 10,000-resample cluster bootstrap 95 percent CI, Holm correction over the five preregistered primary contrasts (ours versus semi-empirical, PiDDM-style, PIKAN-style free-G, Wang-style PINN, best flexible baseline). Non-inferiority versus the best flexible baseline with a margin set after P1 (headroom pilot) and before confirmatory runs. Effect sizes always reported next to p-values.
- **Preregistration.** Frozen files in `runs/prereg/` before the first confirmatory run: splits, windows, forecast set, primary endpoint, tournament rule, thresholds, contrasts.

## 7. Baselines (each named; implementations in `code/baselines/`)
| ID | Baseline | Role | Source / status |
|---|---|---|---|
| B0a | Condition median (other replicates), nearest-condition trajectory | trivial, Test A / B | defined here |
| B0b | Per-cell power law on the window, extrapolated | "no stress information" | defined here; median |ln error| of EOL 0.43 at W = 4, 0.34 at W = 6 [scratch] |
| B1 | Semi-empirical stress-life, Gasper-style: algebraic stress-factor law Q_loss = F(s)·Θ^z, ≥ 3 published forms, best by inner CV, with per-cell scale from the window | physics-free-of-ML rival | Gasper et al. doi 10.1149/1945-7111/abdde1 and 10.1149/1945-7111/ac86a8, **abstract only read by the auditor; exact functional forms to be taken from the full texts** |
| B2 | PiDDM-style: Eq. 1 (SEI Arrhenius·t^α plus LLI DoD^b1·Ah^b2), 3×60 MLP mapping inputs to the five kinetic parameters, forward Euler | closest prior model | arXiv 2607.29095; **re-implemented from the paper, code "upon request"**; inputs adapted to the ISU data (stress plus window summaries instead of 16 charge-segment features; E_SEI, E_LLI fixed or dropped at constant 30 C); adaptation disclosed |
| B3 | PIKAN-style free-G: KAN G(y, Θ, s) unconstrained, shooting and PDE-residual variants | identifiability contrast | JES 153, 120860 (doi 10.1016/j.est.2026.120860); **full text unread**; reimplemented from code reading, no code copied |
| B4 | Wang-2024 PINN (sine-MLP F and G with PDE residual and monotone term), inputs (s, Θ, window summary), no future features | task-adapted classic PINN | doi 10.1038/s41467-024-48779-z; code read, not run |
| B5 | Data-only KAN and MLP, parameter-matched, plain and monotone-by-construction (integral of softplus) | separate "monotone prior" from "physics" | defined here |
| B6 | LightGBM, GP regression (ARD kernel), ridge on (s, window summary, Θ) | strong flexible tabular | tuned, same budget |
| B7 | LSTM and Transformer trajectory forecaster conditioned on s and the window (CPU, tiny) | sequence-model rival | tuned, same budget |
| B8 | Early-life lifetime: Severson-type elastic net on ΔQ(V) features between early reference Q-V curves (from `Q_interpolated`) plus stress, target ln(EOL) | EOL endpoint only | doi 10.1038/s41560-019-0356-8; plus the ISU authors' own method (arXiv 2307.08382, unread) |
| B9 | Recent trajectory-from-early-cycles models (FlowBatt arXiv 2611.03150, per audit; BatLiNet doi 10.1038/s42256-024-00972-x) | accuracy context only | run if code is public; otherwise discuss, no numbers quoted |
| Ablations (table) | KAN → GAM / Chebyshev / RBF / MLP; backbone B1 to B4; hierarchy off; window-MAP vs full-trajectory δ; hard vs soft (PINN-form); correction κ on/off; sparsity off; Arrhenius form vs T-in-KAN | attribution and R4 | defined here |
Every learned baseline receives the same window information and the same tuning budget; a baseline whose tuned optimum sits at the edge of its space is re-tuned.

## 8. Figure plan (8 to 10 items, forms to be debated in D-figures)
1. **Method schematic** (stress → KAN → log-rates → two-mechanism ODE with per-cell offsets and early-window MAP; equation inset). Claim: structure, causal inference, no future data.
2. **Data and design** (63 conditions in stress space with replicates; fade curves for three contrasting conditions; replicate spread). Claim: designed, near-orthogonal stress variation and a measurable noise floor.
3. **Forecast overlays** on held-out cells from low, middle and high stress with the window shaded, for the proposed model and 3 to 4 baselines. Claim: the knee is anticipated from the window and the stress.
4. **Primary result:** per-model dot-and-whisker with cluster-bootstrap CIs (primary endpoint, Test A / B / C), or a ranked forest plot of paired differences. Claim: superiority, ties and losses shown.
5. **End-of-life parity** (predicted versus true, log axes, ±20 percent band) for the proposed model and the two strongest baselines. Claim: EOL accuracy and where it fails.
6. **Window and horizon efficiency:** error versus W and versus horizon, with CI. Claim: how much early information is needed.
7. **Learned stress laws:** KAN edge functions φ_ij with seed, bootstrap and fold envelopes, symbolic fit overlaid (and synthetic truth in an adjacent panel). Claim: stable, compact laws.
8. **Identifiability sweep (synthetic):** recovery error versus number of conditions × replicates × cadence, structured versus free-G, with the real ISU design marked. Claim: identifiable at the public design size; free-G is not.
9. **Rounding survival and the accuracy-identifiability frontier:** forecast RMSE ratio versus significant digits for symbolic structured versus free-G; frontier from the optional correction κ. Claim: law survives rounding, flexibility costs identifiability.
10. **Tables:** (a) main results with Test A / B / C and secondary dataset, (b) ablation and control table (R4, hard versus soft, backbone). If the limit binds, merge (b) into an appendix; detailed procedures and sensitivity analyses go to an Appendix per the JES supplementary policy.
Secondary dataset (SNL) results and the Arrhenius panel are added as panels in 3, 4 and 7, not as new figures.

## 9. The four debate questions

### 9.1 Why this, and why not each alternative
- **A1. C1 alone (forecasting with a stress-conditioned PI-KAN, no identifiability programme).** Loses: each ingredient is public (PiDDM, JECS addd4e, Kuzhiyil, Gasper); the audit rates it INCREMENTAL at 0.70 confidence. It would be won or lost on decimals of RMSE.
- **A2. C3, audit of the Wang-family residual on the PINN4SOH sets.** Loses: audit rates it incremental leaning taken; every follow-up already has a component ablation; the strongest remaining point (total versus partial derivative, u_t inside G) is a short note, not a paper; and it uses the datasets the author prefers to avoid. Its useful part survives here as the hard-versus-soft and free-G control rows.
- **A3. SOH estimation with a better PINN+KAN on XJTU/TJU/HUST/MIT.** Loses: crowded (PIKAN JES 153, PGKAN JES 182, PI-EKAN, KLSTM, Verhulst KAN-PINN), reported gains are within seed spread on HUST and MIT per the PINN4SOH authors' own text, and the task cannot forecast.
- **A4. C2 alone as an audit of PIKAN/PGKAN.** Loses as a standalone: it targets two papers of one group and rests on an unread paper and a repo the lead found to be a mid-experiment snapshot; as an audit it lacks a constructive method and a forecasting result that a JES reviewer expects. Kept as the evidence inside this proposal (the free-G contrast on our synthetic and real data, not on their pipeline).
- **A5. Path-dependent (history-dependent) laws on dynamic-sequence data (A5 dataset) or neural-ODE/UDE with latent state.** Loses for a one-week budget: data not downloaded, UDE/NeuralODE forecasting is occupied (arXiv 2410.14347, Kuzhiyil), and a static stress law is the necessary first step. Named as the follow-up.
- **A6. Data-driven early-life models (BatLiNet-type, flow matching).** Loses: no physics, no JES novelty, and they set the accuracy baseline rather than offering a claim.
Why this: it is the only candidate in which the audit found a NOVEL slice (identifiability of the learned stress law), it joins C1 and C2 through named parameters that can be recovered, and ISU supplies the one thing the question needs, a designed multi-stress matrix with replicates.

### 9.2 Is it the best possible, or is there room?
Not the best possible. Room: (i) a second temperature-bearing dataset with larger cells (Samsung 50E) to make the Arrhenius claim non-trivial; (ii) calendar-cycle separation (the ISU weekly cycle includes continuous cycling plus reference tests; no storage control); (iii) a strict PINN headline instead of a hard-physics one; (iv) predictive intervals (retired topic; excluded by design); (v) path-dependent protocols. The weakest link is that the identifiability claim is conditional on the model class even with S3 misspecification. I would state that in the paper rather than hide it.

### 9.3 What we lack that a JES reviewer will hit
- Single temperature in the primary data; Arrhenius demonstrated only on SNL (3 levels cannot test curvature of the Arrhenius law).
- Small 250 mAh pouch cells at weekly resolution (about 19 points per cell); reviewers want EV-format cells and cycle-level data.
- PiDDM code unavailable (re-implementation fidelity attack); PIKAN, PGKAN, JECS addd4e, arXiv 2607.16864, ISU authors' paper and Gasper full texts unread by anyone on the team; ISU authors' arXiv 2307.08382 was not in the audit's closest-work table and is the nearest prior art on this dataset: **the novelty auditor should read it first**.
- `FIGURE_FORMS.md` (exemplar dissection of JES figure forms) is empty; the figure plan above is untested against the catalogue.
- Cycle counts (D1) and SNL (truncated download) are not yet in hand.
- No experiment in this proposal has been run on the models; the only measurements are the [scratch] profile numbers.

### 9.4 What would make a reviewer reject it
1. "Another PINN/KAN battery paper": mitigated only if identifiability results are crisp and the free-G contrast is clear.
2. "KAN adds nothing over a polynomial or GAM" (R4): the most serious technical risk; the hinge-law synthetic S2 and the Test C extrapolation are the only places a KAN could win clearly; if they do not, say so.
3. "Synthetic recovery is circular": answered by the misspecified generators S3 and S4 and anchoring of truth on real fits, only partly.
4. "Hard ODE is not a PINN": answered by the soft variant and the explicit decision rule; the title says physics-informed, not PINN.
5. "Single dataset, single temperature, small cells."
6. "Unfair baselines": answered by the common task, common window information, common tuning budget and the disclosure of adaptation of PiDDM and Wang-style models.
7. Hostile reading of the hierarchical window-MAP as "per-cell curve fitting with a prior": the answer is the held-out-condition test (Test B), where condition median is unavailable.

## 10. One-week plan with go/no-go pilots

All CPU. No GPU job is requested. Peak memory under 4 GB expected.

| Day | Work | Gate (kills or reshapes) |
|---|---|---|
| 0-1 | **P0 data readiness.** Range-fetch `Cycling_json` for about 12 cells spanning the stress space (needs the lead's yes; whole set 10.2 GB for the confirmatory runs); compute cycles and throughput per week; check Θ versus calendar-week coordinates and the F1 approximation error. Resume `SNL.zip`. Re-check Table A1 against the PDF. | If cycle counts unobtainable → F1 and restate the claims in weeks. If SNL cannot be parsed → Samsung 50E subset or SNU as secondary. |
| 1 | **P1 headroom (no physics).** Tuned LightGBM, GP, ridge on (s, window) for Test A / B at W = 2, 4, 6; B0a, B0b; replicate noise floor in retention units. | If the best flexible baseline already sits at the replicate noise floor on Test B (headroom ratio below about 1.3), the accuracy claim R3 cannot be won; reframe to identifiability-first (the claim still stands, the title changes to option 3) and tell the lead. |
| 1-2 | **P3 synthetic identifiability (first modelling pilot, because it is cheap and kills the novel part).** Implement the backbone, KAN stress map, integrator, δ MAP; run S1 at the ISU design with real noise; recovery of the slopes, seed and bootstrap CV. | If median slope error > 25 percent (R1) → identifiability does not hold at ISU's design; stop, re-open topic. Otherwise fix the pass threshold and write it into `runs/prereg/`. |
| 2 | **P4 free-G contrast on synthetic** (shooting and PDE-residual variants), same design. | If free-G is as well identified (R2) → the contrast claim is dead; the paper becomes a design-sufficiency study (title 3) or is stopped. |
| 2-3 | **P2 backbone adequacy on real training cells** (tournament B1 to B4, folds of Test B): residual RMSE versus replicate noise floor; check D1-aligned Θ. | If the best backbone misfits systematically (median training RMSE above about 1.5 times the noise floor) → reconsider the backbone before adding KAN capacity (otherwise identifiability is lost). |
| 3 | Baselines B1 to B8 implemented and tuned (equal budget, nested), preregistration frozen (splits, thresholds, contrasts). | Gate-auditor check of leakage and equal-budget before any test fold is touched. |
| 4 | Confirmatory runs ISU: Test A, B, C; 5 seeds; symbolic extraction; ablations (R4, hard/soft, hierarchy, backbone). | Report ties and losses as they are. |
| 5 | SNL runs (Arrhenius backbone, T-in-KAN contrast), identifiability sweep (4.2) and rounding runs on real folds. | If SNL gives no usable replicate structure → cell-wise only; Arrhenius claim reduced to a point estimate. |
| 6 | Figures from `runs/` only (`code/figures/`), tables, statistician pass, novelty re-audit (adds arXiv 2307.08382 and any new arXiv from the last week). | Figure form compared with the exemplar catalogue (CONTRACT 6a) once it exists. |
| 7 | Buffer, gate audit, writing outline. Writing a 6,000-word JES manuscript is not inside this week. | |

**Dependencies for the lead:** (D1) yes to the ISU `Cycling_json` fetch (pilot subset, then whole set 10.2 GB); (D2) resume of `SNL.zip`; (D3) e-gateway access to PIKAN and PGKAN full texts, JECS addd4e, Gasper 2021 and 2022, Preger 2020, and a task for the novelty auditor to read arXiv 2307.08382 and PiDDM Sections 3 and 4; (D4) confirmation of the PINN question in 3.5 (hard-physics headline with a soft control, or strict PINN headline).

## Citation status (all must pass the citation validator before use)
Verified by others per the audit or notes: PiDDM arXiv 2607.29095 (arXiv API); Wang et al. 2024, doi 10.1038/s41467-024-48779-z (Crossref); PIKAN, doi 10.1016/j.est.2026.120860 (Crossref); Kuzhiyil 2025 Applied Energy 382, 125221 (Crossref); Severson 2019, doi 10.1038/s41560-019-0356-8; Preger 2020, doi 10.1149/1945-7111/abae37; Gasper 2021, doi 10.1149/1945-7111/abdde1 and 2022, doi 10.1149/1945-7111/ac86a8 (abstract level). From the dataset README that I read: ISU associated preprint doi 10.48550/arXiv.2307.08382. **Not verified by anyone (from memory, to verify):** KAN arXiv 2404.19756 and 2408.10205; Wang 2011 doi 10.1016/j.jpowsour.2010.11.134; Schmalstieg 2014 doi 10.1016/j.jpowsour.2014.02.045; Raue 2009 (Bioinformatics); PGKAN DOI (JES 182, 124768, article known from Crossref, DOI not recorded).
