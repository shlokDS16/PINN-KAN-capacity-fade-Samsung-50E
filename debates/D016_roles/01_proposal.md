# D016 proposal: give the PINN and the KAN each a testable role (2026-11-05)

Role: proposer (method-architect). Specification and predictions only; no result is claimed and no Samsung retention value was opened.
Reading (full text unless stated): CONTRACT.md; D015 red team; DECISIONS D001-D015; PREREG_v3 sections 1-11a, 12-14, 16 (sections 3-4 and 17-19 skimmed by heading); D011 judge section 3 and headings; P3, P4, P5 RESULT.md; STATS_RULING sections 0-7; TYPE1_SIGNFLIP; samsung50e_dataset_paper.md; PRIORART_SUMMARY.md; code/README.md.
One new measurement, from identifiers only (`data/raw/samsung50e_meta/experiments_meta.csv`, no capacity file): designed throughput of the 40 cycling conditions.
Ledger: `tools/ledger.py` does not exist in this project (D015 red team says the same); no ledger rows added. The orchestrator must write the D016 row by hand.

---

## 0. Verdict in six lines

1. F1 is correct for the design as frozen: the closed-form hard ODE is the same law as the PINN (D013 (a)), so the soft residual can only help where the law is wrong; the only pilot (P5) gives a 4 % median gain (16 % with whole-axis collocation) against an 80 %-power detectable gain of 9-22 % at n = 40. The KAN contrast (H1b) is unwinnable for the same reason (P4: forecast gap 0.0-0.1 pp).
2. The fault is the regime, not the models: at full training data and a 4-check-up window, tuned data-only learners already sit at the replicate spread (P3: ISU 0.90 [0.78, 1.08]; SNL 1.13 [0.81, 1.62]). A physics prior cannot show value where nothing is left to win. It can where data are scarce.
3. Recommended redesign ("Design R", section 5): keep the data, the code base and the exact sign test, and move the confirmatory question to **data efficiency**: how many ageing conditions (m) and how many early check-ups (k) are needed. The PINN's role is a **prior that pays when data are scarce** (physics-informed family vs best data-only learner, fixed-sequence over a pre-ordered grid of (m, k) cells). The KAN's role is a **readable, fold-stable stress law** obtained by symbolic extraction, with an accuracy tie accepted and pre-stated, and not a race against GAMs.
4. What stays honest: the soft residual versus the hard ODE remains a secondary qualifier with a pre-written sentence for every outcome, including "tie". Nothing in the redesign makes the soft residual necessary; section 3, option 4 says what it can and cannot do.
5. Closed outcome table (section 6): P role (win / none / reverse) x K role (readable / accurate-not-readable / not shown or worse) gives six titles and fixed wording; qualifiers (A10, hard ODE, storage transfer) change one sentence by tier, never the title; no row says "put to Shlok".
6. Cost: about 2-3 days of code (subset selector, k = 0 and k = 2 windows, symbolic extraction, fixed-sequence assembly) plus a training-side pilot on ISU; extra CPU is of the order of the Test B core run (arithmetic in section 5.7). Everything in the D015 freeze conditions (A10 verified, lab confound on Test B including A10, Holm ordering, README alignment) still applies.

---

## 1. Evidence that sizes every option (what the files say)

| # | Fact | Pointer |
|---|---|---|
| E1 | Best tuned data-only learner / replicate spread = 0.90 [0.78, 1.08] (ISU, W = 4 wk), 1.13 [0.81, 1.62] (SNL, W = 100 cycles); LightGBM best in 3 of 5 (ISU) and 5 of 5 (SNL) folds. At full data and a full window there is little headroom over data-only learners. Samsung is blinded; no Samsung number exists. | P3 RESULT, verdict table |
| E2 | KAN [3,h,1] vs additive GAM on synthetic G2: nRMSE 0.081 vs 0.103 (median), forecast RMSE gap 0.0-0.1 pp, GAM class floor 0.05-0.07; hidden width at the grid edge in 5 of 5 draws. | P4 RESULT |
| E3 | Soft PINN vs hard ODE on synthetic G1 (strong misspecification): judge-spec collocation median ratio 0.96 (4 of 5 draws, one reversal +0.40 pp); whole-axis collocation 0.84 (5 of 5). Lambda_res = 10 was worse than hard in every draw. Attribution not clean (F and z_c are extra capacity). | P5 RESULT, items 1-4 |
| E4 | Exact sign test, n = 40, Holm step 1: 80 %-power gain about 9-12 % (rho 0.95), 12-16 % (0.90), 17-22 % (0.75); non-inferiority at true equality (margin 10 %) 0.71-0.95 / 0.40-0.72 / 0.16-0.32; n = 13 cannot support anything below about 20 %; n = 27 (design effect 1.5) 12.5 % / 15.5 % / above 20 % (Wilcoxon-based). rho for PINN-KAN pairs is an assumption. | TYPE1_SIGNFLIP "Power"; STATS_RULING 7 |
| E5 | Design: 279 cells; 147 cycling cells in 40 conditions; 132 storage cells in 19 conditions, only cells 01-03 (66) have intermediate check-ups; Test B = 5 folds of 8 held-out conditions, so 32 training conditions per fold; all 35 C cells are lab INT, 45 C is mostly HM. | PREREG 3.1, 4; dataset note |
| E6 | Check-up cadence: cycling CU at weeks 1, 2, 3 then 5, 7, 9, 13, ...; storage CU at about weeks 5, 9, 17, 25 then every 8 weeks. Window k_cyc = round(n_med / 3), expected 3-5. | dataset note Fig. 4; PREREG 5 |
| E7 | **Designed throughput (new, identifiers only; assumes charge time DoD/C_ch plus discharge time DoD/C_dch, no rest, no CV phase, no pauses):** the 40 cycling conditions span 23 to 112 equivalent full cycles per week, a factor of about 5; none is a low-rate, calendar-dominated condition. The calendar term therefore enters every cycling cell, but the cycling term is large in all of them; no stratum exists where storage knowledge dominates. | `experiments_meta.csv`, arithmetic in section 7 |
| E8 | In a cycling cell calendar and cyclic terms are collinear (E_n proportional to t_n at constant rate); only storage cells identify the split. | D015 F9 |

Consequence: wherever the full training set and a full window are used, the expected differences are inside the minimum detectable gain. Every option below is judged by whether it moves to a regime where a gain above the MDE is plausible, or accepts a tie and says so in advance.

---

## 2. Why the current design produces F1 (diagnosis, for the judge)

- PINN role "integrate the law": removed by the closed form (D013 (a)); A2 is the exact solution of the PINN's own law.
- PINN role "regularise F where data are absent" (collocation, twins): F is a surrogate of the law; with the law fixed, collocation adds no information about the cell, only consistency with the law's own stress map. It cannot beat the law-integrator unless the law is wrong.
- KAN role "accuracy": a hidden-layer KAN [5,h,1] with h up to 8 on 32 training conditions is a tuned spline MLP; accuracy over GAM/MLP is E2-sized.
- KAN role "interpretability": the KAN literature's selling point; the frozen design uses it only as partial-dependence plots of a non-additive map (D015 F1).
- Comparators: H1a (A9) is a low bar (F5), H6 is a win over a model its authors call inadequate (F6), H1c is gated and probably unwinnable (E1).

So the redesign changes the regime (scarce data) and the KAN claim (readable law, tie accepted), and demotes everything that cannot be won to a qualifier with fixed wording.

---

## 3. Options

Common conventions: unit = held-out condition; primary test = exact one-sided sign test on L_c = ln(S_comp,c / S_A,c) with margins ln 1.02 (tier S) and -ln 1.10 (tier N), as D012. "Chance" is a qualitative judgement from E1-E8, not a probability; no pilot on Samsung exists.

### Option 1. Knowledge transfer across arms (storage <-> cycling)

- **Hypothesis H-T1.** Training jointly on 132 storage cells lowers the forecast error of held-out cycling conditions relative to cycling-only training (A1 vs A13), because the shared calendar term r_cal(T, SOC) is identified by storage cells. Dose-response sub-hypothesis: the gain grows as cycling conditions become scarce (m = 8 vs 32) and with the calendar share. Converse H-T2: cycling cells lower the forecast error of held-out storage conditions (A1 vs A14, S2, n = 19).
- **Endpoint.** Condition-level retention RMSE (pp), log ratio. Dose-response: Spearman correlation between L_c and a **label-free** design covariate (designed EFC per week, E7), n = 40.
- **Test.** Exact sign test A13 vs A1, tier S/N, n = 40, level 0.025. Dose-response: Fisher-z approximation, 80 % power for |rho_s| about 0.43 at n = 40 (textbook value, not simulated). H-T2: n = 19, sign test (15 positives needed at 0.025); no tabulated MDE below about 17 % at n = 13 and above 12.5 % at n = 27 suggests above 15 %.
- **Power.** Same-model contrast (rho about 0.95): MDE about 9-12 % at n = 40. Any stratified subset (for example the 20 lowest-throughput conditions) has n = 20, not tabulated; interpolating the n = 13 and n = 27 columns puts the 80 % MDE above 13 % even at rho 0.95 (to be simulated by the statistician).
- **Risk.** (i) The calendar share of fade is probably modest in every cycling condition (E7: throughput 23-112 EFC/week, factor 5 only), so the transfer gain is probably below 9-12 %. (ii) Storage cells also feed the backbone tournament; the gain may be a backbone effect, not a calendar-term effect. (iii) The carrier is the shared law, which A2 has too; the soft residual is not the carrier. (iv) Temperature is lab-aliased (35 C INT, 45 C HM); storage cells at 10 C are all SIE. (v) H-T2 is expected null: storage conditions are measured directly.
- **Chance of a demonstrable effect.** Low to moderate for the main effect at n = 40; moderate for the scarcity version (m = 8), where the cycling-only model has too few conditions to separate the calendar part.
- **Title and claim if it carries the paper.** "Calendar-ageing tests as informative priors for cycling forecasts: ..." Claim: "joint training lowered the typical held-out cycling error by X % (interval) and the gain was larger where cycling conditions were scarce."
- **Verdict.** Keep as a **qualifier** (Q-T) at two grid cells and as a figure panel; not strong enough alone.

### Option 2. Data-poor regimes (learning curves)

Two axes, both available from the data and the code base.

**2a. Early check-ups k (window length).** k in {0, 2, k_full}, k_full = k_cyc by the frozen rule. k = 0 is the window-information reference demanded by D015 F7 (condition-only forecast, no cell information); k = 1 descriptive.
**2b. Ageing tests m (number of training cycling conditions per fold).** m in {8, 16, 32}; the 8 held-out conditions of each fold are identical for all m, so contrasts are paired across the grid. Training subsets are a deterministic max-min (space-filling) selection among the fold's 32 training conditions in standardised stress space (identifier-only, label-free, reproducible; the logic of the dataset's own conditioned-Latin-hypercube and pi-OED designs); random subsets are a sensitivity row. All storage cells stay in training in the base grid.

- **Hypothesis H-P (the PINN as a prior).** In the most data-poor cell the physics-informed family (law + F + residual, stress map chosen per fold by inner CV among A1 KAN, A3 parametric, A4 additive GAM) has a lower median condition error than the best data-only learner (inner-CV best of A9, A11, A12 with physics-motivated features, see fairness below). Prediction: the advantage is largest at (m = 8, k = 2) and shrinks as m and k grow (E1 says it is about nil at (32, k_full)).
- **Endpoint.** Condition retention RMSE (pp) at each cell; primary quantity L_c per cell.
- **Test.** Fixed-sequence testing at 0.025 per step (no multiplicity cost): g1 = (8, 2), g2 = (16, 2), g3 = (32, 2), g4 = (32, k_full); stop at the first step that fails. Tier S one-sided; reverse tier S evaluated at g1 regardless (safety finding). Result = number of consecutive passes J (0 to 4) and the sign at g1.
- **Power.** Different model families, rho about 0.75: 80 %-power gain 17-22 % at n = 40 (E4). That is large for E1's regime but small for a regime where a learner with 8 training conditions in a 5-D stress space must extrapolate; whether the true gain at g1 reaches it is **not measured** (Samsung blinded). The pre-freeze pilot P6 (section 5.6) measures the direction on ISU training sides.
- **Risk.** (i) At m = 8 every model may collapse to the same near-constant forecast (ratios near 1). (ii) Inner CV with 8 conditions is noisy (2 inner folds; equal for all arms). (iii) Straw-man risk: a reviewer will call a data-only learner without Arrhenius-type features a weak baseline; fairness condition: A11/A12 get a tuned choice between raw stresses and physics-motivated features (1/T, log C-rate, log DoD, SOC and SOC squared, the A3 abscissae) and the data-only family includes A9. (iv) Subsampling conditions changes the hull; report lab and temperature composition per cell. (v) "Physics beats data-only at small n" is a known pattern; the novelty is the quantified crossover on a designed dataset with a semi-empirical reference, not the pattern.
- **Chance.** Moderate for g1 (textbook regime, unmeasured here); low for g4 (E1).
- **Title and claim.** P+: "Physics-informed neural networks ... forecast lithium-ion capacity fade from few ageing tests and early check-ups"; claim: "with m = 8 training conditions and two check-ups the typical held-out condition error was X % lower than the best data-driven learner (interval), and the advantage extended down to cell g_J."
- **Verdict.** Adopt as the PINN's primary role.

### Option 3. KAN as readable, physically checkable stress laws

- **Hypotheses.** H-K1 accuracy tie: the closed-form law extracted from the trained KAN (A15) is non-inferior to the unsimplified KAN (A1) within 10 %. H-K2 stability: the selected function family per stress input is the same across outer folds. H-K3 consistency: the direction of each extracted stress effect agrees with the sign of the corresponding exponent in the dataset authors' (verified) model A10, and the effective activation energy of the calendar term is reported with its fold spread against the authors' own fit and against **verified** literature only. Optional H-K4: the extracted law is more accurate than A10 (superiority), as a qualifier.
- **Procedure (A15, to be specified in full by method-architect after the opponent round).** Per outer fold, on training conditions only: tuned KAN with hidden width limited to {1, 2}; sparsify (existing L1 plus entropy penalty, sparsity level from the tuned grid); prune edges below a pre-set importance; fit each surviving first-layer edge by a **pre-registered library** (zero, linear, power, log, exponential/Arrhenius in 1/T, quadratic, hinge) with a fixed BIC rule and a complexity cap; refit the free coefficients end to end under the same loss. The extraction rule is frozen before any outer prediction.
- **Endpoints.** (K-acc) sign tests of A15 vs A1 at +-ln 1.10 (TOST) at g4. (K-stab) number of the 5 stress inputs whose family label (pruned counts as a label) is identical in at least 4 of 5 folds; context: the same count on the NC-2 permuted-stress fits. (K-con) number of inputs whose extracted direction matches the sign of A10's exponent; needs FB-2 closed. (Q-A10) A15 vs A10 tier. Thresholds "4 of 5 inputs" are the proposer's design choices, flagged for the statistician; they are not derived.
- **Power.** TOST at n = 40 with same-model rho about 0.95: 0.71-0.95 at Holm step 1 (E4), higher at 0.025. K-stab and K-con are counts over 5 inputs and 5 folds: no formal power; they are pass/fail descriptors with pre-stated rules. This is the honest limit of interpretability claims.
- **Risk.** (i) A15 loses accuracy through the width cap or the library (then the KAN role is "not shown"). (ii) With 3 storage temperatures (10 C all SIE, 45 C all HM) E_a is lab-confounded; the comparison is only to A10's fit on the same data, and a lab-indicator row is mandatory. (iii) The 35 C level exists in cycling only. (iv) The BIC library can pick different families fold to fold when the edge is nearly linear (stability fails for a benign reason; report "equivalent over the hull" as a second label, pre-defined as max difference below 5 % of the edge range, a proposer's choice). (v) Reviewers may call 5 inputs a thin test of "interpretability"; the claim is worded as "stable and consistent", not "discovered physics".
- **Chance.** Accuracy tie: moderate to high. Stability: moderate, unknown. Consistency with A10's signs: moderate (monotone effects expected, but non-monotone SOC-window effects may appear). Superiority over A10 (K-D): unknown.
- **Title and claim.** K+: "... with readable Kolmogorov-Arnold stress laws ..."; claim: "a closed-form law extracted from the KAN reached the accuracy of the full KAN within 10 % (interval), the same functional family was selected in k of 5 folds for n of 5 inputs, and the directions agreed with the dataset authors' model for n of 5 inputs."
- **Verdict.** Adopt as the KAN's primary role. It converts "KAN = spline MLP" into a deliverable (a formula plus its stability), with the tie pre-stated.

### Option 4. What the soft residual can do that the closed-form ODE cannot (and an honest statement if nothing)

Honest statement first. With a fixed law and a closed-form (or RK4) integral, the hard ODE uses every piece of information the law carries. The soft residual adds **no** information about the system; it can only (a) relax the law where the law is wrong (F can bend, lambda_res tunes how much), (b) interpolate between the law-driven limit (lambda_res large, A2-like) and the data-driven limit (lambda_res small, A9-like), (c) expose where the law is violated (residual map), and (d) accommodate laws without a closed form, which RK4 also handles. Anything beyond (a)-(c) would be a claim without a mechanism. If the data show a tie with the better of A2 and A9 everywhere, the PINN's contribution is robustness (not having to choose), and the paper must say so.

Testable forms:
- **4a. Regime adaptivity ("no regret").** Using the same (m, k) grid: A1 is non-inferior (tier N) to the inner-CV best of {A2 hard law, A9 data-only} at each cell, and strictly better (tier S) at any cell where the two limits cross. Test: sign tests per cell, N then S; no extra data. Power: A1 vs A2 and A1 vs A9 are near-same-model contrasts (rho 0.90-0.95): NI at equality 0.40-0.95 (E4); the S tier at a crossing cell needs 9-16 %. Chance: NI moderate; S at a crossing cell low (E3: 4-16 %). Wording: "tracked the better of ... within 10 %" or "was not shown necessary".
- **4b. Controlled misspecification (backbone dose-response).** Fix the state factor h to each of {constant, self-limiting, accelerating} for A1 and A2 (existing `backbone` config), order the three by the hard ODE's training-side inner-CV error (training data only, computed before any outer scoring), and test A1_b vs A2_b in descending dose, fixed sequence. Chance: low to moderate (E3 is the only evidence). Risk: reviewers read a deliberately wrong law as a straw man; mitigated because the three backbones are the tournament's own candidates, but the result is a robustness statement, not an accuracy claim. Adopt only as an appendix row.
- **4c. Residual map as a law-violation detector.** Does |R| from A1 (training points) rank-correlate (n = 40) with the hard ODE's held-out error by condition, and does it beat the hard ODE's own training misfit mapped over stress as a predictor? Expected: equal to training misfit, i.e. no PINN-specific value. Chance: low. Descriptive figure only.
- **4d. Collocation where data are absent / calendar twins.** No mechanism beyond (a); keep as a mechanism description, not a test.
- **Verdict.** Adopt 4a as the qualifier Q-H (H2 restated on the grid, fixed wording), keep 4b-4c as appendix rows, state in the Discussion that the soft residual is not shown necessary unless Q-H says otherwise. This is the honest answer to F1 for the residual itself.

### Option 5. Other ideas

- **5a. k = 0 window-information reference (adopted).** Answers D015 F7: if the window adds nothing at k_full, "forecast from first check-ups" is empty. It is free for the law-based arms (no window inversion).
- **5b. Design-stage reading of k = 0 and m (adopted as the framing).** "Predict a planned ageing condition from the tests already run" is what an ageing-test planner does; it ties the study to the dataset's own subject (optimal experimental design).
- **5c. KAN-discovered term added to A10 (A10+).** Test A10+ vs A10 (same family, rho high, MDE about 10 %). Not adopted: it needs a second model-building step and A10 is still unverified (FB-2); possible follow-up.
- **5d. More condition-level units from further cycling datasets (for example BatteryLife).** Would lower the MDE (n = 126 pooled units from Samsung, ISU, SNL is already available but ISU/SNL are "not blind"). Not adopted: data volume (31 GB), CONTRACT preference and one-week limit; ISU and SNL are used as "also holds" replications of the same grid.
- **5e. Pooled units, cycling plus storage.** One sign test over 40 + 19 = 59 conditions of "held-out ageing condition". Heterogeneous estimand; secondary only.
- **5f. Hierarchical prior for the per-cell offset from replicate structure.** Would help law-based arms at k <= 2 but adds a tuned dimension. Not adopted.

### Comparison

| Option | Role it gives | Realistic chance at n = 40 | Meaning for engineers | Closes F1? |
|---|---|---|---|---|
| 1 transfer | shared law as carrier | low-moderate | fewer cycling tests via storage tests | partly (carrier is the law, not the residual) |
| 2 data-poor | PINN as prior | moderate at g1, low at g4 | how many tests/check-ups are needed | yes for "physics-informed", not for "soft residual" |
| 3 readable KAN | KAN as symbolic law, tie accepted | tie: moderate-high; stability: moderate | a formula to check and reuse | yes for the KAN, if worded as readable/stable |
| 4 residual | relaxation, adaptivity | low-moderate | robustness to a wrong law | honest "not shown" if null |
| 5a/5b | window information, design-stage framing | n/a (reference) | meaning of "early forecast" | supports 2 |

---

## 4. Contract questions (CONTRACT section 3, items 2-5)

**Why this and not each alternative.**
- Keep PREREG_v3 and add an expected-outcome clause: loses, because F1 is the expected outcome itself and the supervisor's test ("does each named component earn its place") fails by design.
- Option 1 alone: loses on E7 (no calendar-dominated stratum) and because the carrier is the law, which A2 shares.
- Option 3 alone (KAN-only paper): loses the PINN, which the author wants, and the tie has no accuracy headline.
- Option 4b alone (misspecification): loses as a straw man and rests on E3 only.
- Drop PINN/KAN from the title (Codex's earlier identifiability-first idea, D005): already rejected by the author's brief.
- Option 5d (more datasets): loses on volume and time.

**Is this the best possible, or is there room?** Design R is the best option I can find inside "same data, CPU, one week". Room: a measured effect at g1 on Samsung is unknown; the training-side ISU pilot (P6) is the only cheap evidence before the freeze, and it is cyclic-only.

**What a JES reviewer would still hit.** One cell type (NCA-type chemistry is not stated in the data paper note, so no chemistry claim); constant-stress protocols, no dynamic loads; capacity only (no EIS/DVA); lab/temperature aliasing; learning curves on random/space-filling subsets are a standard device; "interpretable" claims rest on 5 inputs; the 4-8-dataset breadth of the strongest JES PINN/KAN papers is not matched (ISU, SNL as replications).

**What would make a reviewer reject.** (1) A data-only baseline without physics-motivated features (fixed by the fairness condition); (2) a learning curve whose small-m cells are chosen after seeing results (fixed: grid and order frozen); (3) a symbolic-law claim without a stability rule (fixed: K-stab); (4) a PINN claim where only the hard ODE matters (fixed: wording "physics-informed", soft residual only per Q-H); (5) preprint-heavy novelty (unchanged; D015 F13 remains open).

---

## 5. Recommended design ("Design R")

### 5.1 Question and claim
"How few ageing tests and early check-ups does a physics-informed neural network with learned stress laws need to forecast the capacity fade of unseen cycling conditions, and are the learned stress laws readable and consistent with the dataset authors' model?" The claim contract is the outcome table of section 6; no sentence of the paper is chosen after the data.

### 5.2 Grid, arms, tuning
- Grid cells (m, k): m in {8, 16, 32}, k in {0, 2, k_full}; k = 1 descriptive. Primary path (fixed sequence): g1 = (8, 2), g2 = (16, 2), g3 = (32, 2), g4 = (32, k_full). If k_full = 2 then g3 = g4 and the sequence has three steps; if k_full = 3, g4 = (32, 3).
- Held-out set: the unchanged Test B (5 folds of 8, 40 conditions, `samsung_splits_v2.json`, hash pinned); only the training side is thinned.
- Arms: physics-informed family A1, A3, A4 (stress map by inner CV); A2 hard ODE; A9 data-only F; A10 semi-empirical (with per-cell factor, and "as published" row); A11, A12 data-only learners with physics-motivated feature option; A13 cycling-only (Q-T); A15 symbolic (K role; g4 only, plus g1 descriptive); R1, R2 and the k = 0 population forecast (reference). Dropped from Test B: A5, A7 (their only contrast, H1b, is replaced; A7 may stay at g4 as the "PiDDM-style" comparator), H3, G2-based KAN "win".
- Tuning: equal for every arm; same N of TPE trials, inner folds 2 for m < 32 and 3 for m = 32 (a stated rule, equal across arms); training-side only; comparators chosen per fold and per cell by inner-CV score, never by test error. The k axis costs inference only for A1-A4, A9, A10 (window inversion at test time); A11/A12 retrain per k (cheap).

### 5.3 Statistics
- Primary tests: exact one-sided sign tests (D012), tiers S (ln 1.02) and N (-ln 1.10), median estimand, exact order-statistic interval.
- P role: fixed-sequence over g1-g4 at 0.025 each (tier S); reverse S at g1 tested regardless.
- K role: TOST at g4 (two sign tests at +-ln 1.10, 0.025 each); K-stab and K-con as pass rules; Q-A10 tier.
- Qualifiers (Q-A10, Q-H, Q-T) at g1 and g4, each labelled secondary, interval reported, tier word by the shared template of section 6; none changes a title.
- Holm is not needed inside the primary roles (fixed-sequence for P; K's two components are a conjunction of independently stated pass rules). The two roles are tested at their own 0.025 and are not combined into a family claim; the abstract says so. This replaces the unclear alpha accounting of D015 F4.
- Rules from D015 adopted here: (i) whenever the sign of the mean paired pp difference differs from the median log ratio at a primary cell, the abstract adds the mean difference with its BCa interval and the worst-condition error; (ii) a lab-stratified, lab-indicator (including A10) or retain-all sensitivity row that lowers a primary tier lowers the tier word in the abstract automatically (other sensitivity rows carry no consequence); (iii) Holm ordering is by the statistic actually tested (moot here); (iv) a type-I simulation with fold-level and lab-level shared effects is still required before the freeze.

### 5.4 Fairness conditions (to be checked by red team)
1. Data-only family sees the same training cells, equal tuning budget, and may use Arrhenius-type features.
2. A10 uses the verified form (FB-2) both as published and with the per-cell factor; the weaker of the two sets the wording.
3. Subset selection is label-free and deterministic; random subsets are a sensitivity row.
4. All storage cells stay in the base grid; storage-off is Q-T.
5. Lab and temperature composition of every thinned training set is tabulated; the lab-indicator row exists for Test B including A10.

### 5.5 What the retained freeze conditions still require
FB-1 to FB-6 and FB-8 to FB-10 are unchanged; the new code items are: the subset selector, the k = 0 population forecast and k = 2 window path, the symbolic extraction (A15), data-only learner feature option, the fixed-sequence assembly in `stats_step.py`, the sentence templates, and a unit test for each limiting case (m = 32 reproduces the unthinned run bit for bit; k = full reproduces Test B; A15 with an untruncated library reproduces A1 to float tolerance on a noiseless synthetic law; subsets are identical for identical identifiers). README, stats step and draft 5.5 must be aligned with the new document (D015 F12).

### 5.6 Pre-freeze pilot P6 (training sides only, ISU, non-binding)
Learning curves on ISU (63 conditions, cyclic term only): m in {8, 16, 32, all} and the weeks-window analogue of k, for A1, A2, A9, A11, A12, A10-analogue, inner CV on training conditions only (the P3 enforcement). Purpose: show whether the ordering "law-based better than data-only at small m" exists at all on a dataset that is already "not blind". Pre-set reading, fixed now: if on ISU the physics-informed family is not lower than the best data-only learner at the smallest m in a majority of the five outer training sides, the lead tells Shlok before the freeze that P0 is the likely outcome; the design is not changed on the basis of the pilot's size. The pilot uses no Samsung number.

### 5.7 Compute (arithmetic from PREREG section 16, not measured)
Baseline Test B core at N = 20 is about 9.4 CPU-h expected (35.8 ceiling) for 8 neural arms over 5 folds. Design R drops two arms (A5, A7) from Test B and adds m = 8 and m = 16 refits for A1, A2, A3, A4, A9 with smaller training sets and 2 inner folds; the k axis adds inference only. Order of magnitude: the extra work is comparable to the dropped work, so the core total stays near 10-20 CPU-h expected with a ceiling near 40-70 (three single-thread processes: about one day wall clock expected). A15 adds a few refits per fold. The timing run at the freeze commit fixes N; the Partial plan of D008 (a) applies to every arm equally if triggered.

### 5.8 Power summary for the recommended design
- P role per step: a gain of about 17-22 % (assumed rho 0.75, n = 40) is detectable at 80 %; smaller gains would end as "none" at that step. Whether the gain at g1 reaches it is the open risk.
- K-acc: TOST detectable at equality with power 0.71-0.95 or higher (rho 0.95).
- Qualifiers: Q-A10 and Q-H are same-model-like contrasts (MDE 9-16 %); Q-T as in option 1.
- No simulation was run for fixed sequences, for the thinned-training correlation structure, or for n = 20 strata; the statistician must supply them (a freeze condition).

---

## 6. Closed outcome table (Design R)

Evaluate gate G first, then the P role (three states), then the K role (three states); the title is the single cell of the matrix. Qualifier sentences are added by tier from the shared template. No row requires a choice by the lead or by Shlok.

**Gate G.** NC-1 trips, or a positive control fails, or a test-fold read is found, or A10's form is unverified at the freeze, or the freeze conditions of section 5.5 are unmet: no claim, audit, new version.

**P role states.**
- P+ : tier S at g1 (physics-informed family lower than the best data-only learner by more than 2 %, exact one-sided sign test at 0.025). Extent J = number of consecutive tier-S passes along g1-g4.
- P0 : no tier S at g1 and no reverse tier S at g1 ("none").
- P- : reverse tier S at g1 (the best data-only learner is lower than the physics-informed family by more than 2 %).

**K role states.**
- K+ : K-acc (TOST pass: A15 within 10 % of A1 in both directions) AND K-stab (at least 4 of 5 inputs stable) AND K-con (at least 4 of 5 directions agree with A10).
- K1 : K-acc passes but K-stab or K-con fails.
- K0 : K-acc does not pass (A15 not shown within 10 % of A1; includes reverse tier S for A15).

**Titles (one per cell).**

| P \ K | K+ | K1 | K0 |
|---|---|---|---|
| P+ | **T1** "Physics-informed neural networks with readable Kolmogorov-Arnold stress laws forecast lithium-ion capacity fade from few ageing tests and early check-ups" | **T2** "Physics-informed neural networks with Kolmogorov-Arnold stress functions forecast lithium-ion capacity fade from few ageing tests and early check-ups" | **T3** "Physics-informed neural networks forecast lithium-ion capacity fade from few ageing tests and early check-ups: learning curves against data-driven and semi-empirical models" |
| P0 | **T4** "Readable Kolmogorov-Arnold stress laws for calendar and cycle ageing of lithium-ion cells: accuracy, stability and data requirements" | **T5** "Learning curves of learned calendar and cycle ageing laws for lithium-ion cells: how many ageing tests and check-ups are needed" | **T5** |
| P- | **T6** "When a physics prior does not help: learning curves of physics-informed and data-driven forecasts of lithium-ion capacity fade from few ageing tests" | **T6** | **T6** |

**Abstract wording per state (fixed).**
- P+ : "With m = [8] training conditions and k = [2] check-ups, the physics-informed network's typical (median) held-out condition error was X % lower than the best data-driven learner (95 % interval; n = 40). The advantage held down to [cell g_J] and was not shown beyond it." (J = 4: "at every tested cell".)
- P0 : "The physics-informed network's typical held-out condition error could not be distinguished from the best data-driven learner at the most data-poor cell (interval; n = 40)."
- P- : "The best data-driven learner had a lower typical held-out condition error than the physics-informed network at the most data-poor cell by X % (interval)."
- K+ : "A closed-form law extracted from the KAN was within 10 % of the full KAN (interval), selected the same function family in at least 4 of 5 folds for n of 5 inputs, and agreed in direction with the dataset authors' model for n of 5 inputs."
- K1 : "A closed-form law extracted from the KAN was within 10 % of the full KAN (interval); its function families were stable for n of 5 inputs and consistent with the dataset authors' model for n of 5 inputs, which is below the stated criterion."
- K0 : "A closed-form law extracted from the KAN was not shown to be within 10 % of the full KAN (interval); the readable-law claim is not made."
- Never: "outperforms", "matches", "interpretable physics discovered", "first" (unless D015 F13 is cleared by the novelty auditor).

**Qualifier sentences (appended in the Results and Abstract slot; the same template for every qualifier, by tier of the exact sign test, cells g1 and g4).**

| Tier | Template |
|---|---|
| S (comparator worse) | "[A] had a median condition error X % lower than [B] (interval; n = 40)" |
| N | "[A] was no more than 10 % worse than [B] (one-sided bound); not shown better" |
| none | "[A] and [B] could not be distinguished (interval)" |
| reverse S | "[B] had a median condition error X % lower than [A] (interval)" |

Qualifiers: Q-A10 = physics-informed family (and A15) vs A10 ("the dataset authors' semi-empirical model"); Q-H = A1 vs A2 ("exact integration of the same law"), both cells; Q-T = A1 vs A13 ("with vs without storage cells"), both cells. The sentence for Q-H "none" must read "the soft residual was not shown necessary". Crossover with A10 (smallest m at which the physics-informed family is lower than A10 at tier S, or "not within the tested range") is reported as a descriptive sentence.

**Rules that close the remaining forks.** (1) Mean-vs-median disagreement: add the mean pp difference and worst-condition error (section 5.3). (2) A sensitivity row that lowers a primary tier lowers the abstract's tier word (section 5.3). (3) Test C stays descriptive with the D011 wording and may not be omitted from the Results; the abstract carries it in a fixed form only if the lab-indicator row leaves the median ratio's sign unchanged, otherwise it is omitted from the abstract and stated in Limitations (a rule, not a choice). (4) A tier-S result on ISU or SNL is worded "also holds / does not hold" with its own n (not blind).
Reverse tiers for A10, A2, A13: covered by the qualifier template.

---

## 7. Notes on facts and snippets used

- E7 arithmetic: for each of the 40 unique cycling conditions in `experiments_meta.csv` (type z; key = temperature, SOC_max, DoD, C_ch, C_dch, stage): hours per cycle = DoD/C_ch + DoD/C_dch, cycles per week = 168 / hours, EFC per week = cycles per week x DoD. Minimum 23.1 (45 C, DoD 0.6, C_ch 0.2, C_dch 0.44), maximum 112.0 (45 C, DoD 0.6, C_ch 1, C_dch 2). It ignores rest, CV phases, check-up time and pauses, so absolute values are upper bounds; the ratio (about 5) is the point.
- No literature value (activation energy, exponent) is quoted anywhere in this file. Any such comparison in the paper needs the citation validator (Crossref-verified DOI, page/table) and A10's verified equations (FB-2).
- The chemistry of the cell is not stated in the dataset note; no chemistry-specific claim is made.

## 8. Decision sheet for Shlok (approve before the freeze)

1. The headline becomes a data-efficiency study with two named roles (PINN as prior when data are scarce; KAN as a readable, stable stress law with an accuracy tie accepted), not "PINN-KAN beats everything".
2. You approve in advance all six titles T1-T6 of section 6, including T5 and T6 (the "none" and reverse results), and the rule that no sentence is chosen after the data.
3. The soft residual is not claimed to be necessary; if Q-H says "none", the paper says "not shown necessary".
4. You accept 2-3 extra days for code and the P6 pilot; the 07 Nov 09:00 Samsung fallback of D005 is not moved by this proposal.

## 9. Hand-offs
Next in the debate: Codex opponent (attack the grid, the fixed sequence, the fairness of the data-only family, the A15 rules), then judge. Before any code: red-team on the derivation of the stat rules (hard rule of this agent). The statistician must supply: fixed-sequence power, n = 20 strata, correlated-condition type-I with fold and lab effects, and the thresholds marked "proposer's choice" in option 3.
