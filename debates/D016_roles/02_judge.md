# D016 judge: roles of the PINN and the KAN, and the closed outcome table (2026-11-05)

Role: judge (proposed nothing in D016). Reading, full text: CONTRACT.md; DECISIONS.md D001-D015; D015 red team
(`debates/D015_redteam_v3/01_redteam.md`); D016 proposal (`01_proposal.md`); Codex opponent (`codex_panel/turn04_response.md`);
P3, P4, P5 RESULT.md; `notes/papers/PRIORART_SUMMARY.md`; `notes/papers/samsung50e_dataset_paper.md`. Partial: PREREG_v3
sections 1-2, 4-11a, 16-17 (sections 3 and 12-15 by heading and skim); STATS_RULING sections 0 and 7. No Samsung retention value
was opened. Every number below is quoted from those files or is labelled as my arithmetic on them. No new citation is introduced.

---

## 0. Verdict

**REVISE.** Design R's move to data efficiency is the right answer to F1 and is kept. Three of its parts are replaced, on the
opponent's grounds, which I find correct:

1. **Learning-curve inference replaces the four-step fixed sequence.** One gated threshold claim at the scarcest cell, one gated
   trend claim, and the whole 3 x 3 grid estimated with simultaneous intervals and no tier words.
2. **Attribution through a matched ladder** at every grid cell: the same network without the law (A9), then the law with the best
   GAM stress map, then the law with the KAN (A1), plus the hard ODE (A2) for the residual. A full 2 x 2 factorial is rejected,
   because a "KAN stress map without a law" does not exist in this model class (section 1.4).
3. **The KAN is judged on held-out prediction against a matched, equally simplified GAM law.** The arbitrary pass thresholds
   ("4 of 5 inputs stable / agreeing with A10") are removed. Stability and agreement with the dataset authors' model become reported
   numbers and never decide a title.

The outcome table (section 4) is closed. Every combination maps to one title and one abstract claim sentence through
deterministic rules, with no row left to the lead or to Shlok. Shlok approves or changes the table once, before the freeze.

---

## 1. Final confirmatory design ("Design R2")

### 1.1 Question
How few cycling ageing tests and early check-ups does a physics-informed neural network with Kolmogorov-Arnold stress functions
need to forecast held-out cycling conditions of the Samsung 50E campaign? How much of any advantage comes from the physics law and
how much from the KAN? Does the KAN yield a closed-form stress law that predicts held-out conditions at least as well as an equally
simplified additive law?

The word "few" applies to **cycling** conditions only. The full storage campaign stays in training in every grid cell, so the titles
say "few cycling tests", never "few ageing tests". The proposal's wording overstated what is being saved: 132 storage cells stay in.

### 1.2 Grid (fixed now)
- **m** (training cycling conditions per outer fold) in {8, 16, 32}. Subsets are **nested**, built from identifiers and labels never
  enter: a greedy max-min order in standardised (T, SOC_mid, DoD, C_ch, C_dch) over the fold's 32 training conditions. The order
  starts at the condition nearest the training centroid and breaks ties by condition id. Constraint: every cycling temperature
  (23, 35, 45 C) has at least 2 conditions at m = 8. The subset at m is the first m of that order. The lab and temperature
  composition of every subset is tabulated.
- **k** (check-ups per held-out cell) in {0, 2, k_full}, where k_full = round(n_med / 3), counted from member listings before any
  label is read (PREREG_v3 section 5, FB-6). If k_full = 2, the k grid is {0, 2} and cells (32, 2) and (32, k_full) are one cell.
  If the schedule go/no-go fails, the D005 fallback applies.
- **Named cells:** g1 = (8, 2) is the scarce headline cell; g4 = (32, k_full) is the full-data cell and equals PREREG_v3 Test B.
- **Held-out conditions:** the unchanged Test B (5 folds of 8, n = 40, `samsung_splits_v2.json`). Only the training side is
  thinned, so every contrast is paired by condition across the grid.
- **Tuning:** inside training conditions only. The same N TPE trials for every tuned arm. Inner folds: 2 for m in {8, 16}, 3 for
  m = 32, the same for every arm. Arms are tuned once per (fold, m), using inner-CV scoring at k = 2 for m < 32 and at k_full for
  m = 32. The k axis costs inference only for the law-based arms and A9. A11 and A12 retrain per k.

### 1.3 Arms (at every grid cell unless stated)
| Role | Arm | Change from PREREG_v3 |
|---|---|---|
| Paper's model | **A1** PINN-KAN | Hidden width **h = 1 added** to the grid (KAN [5,1,1]), so at m = 8 the KAN can collapse towards a near-additive map instead of being forced to overfit |
| Physics off, same network | **A9** | Same training cells as A1, storage included (stated in code and checked) |
| Law with a non-KAN map | **AG** = inner-CV best of A4 (additive GAM) and A5 (interaction GAM) | A5 at m = 32 only (its tensor terms cannot be supported by 8 conditions); at m < 32 AG = A4 |
| Residual axis | **A2** hard ODE, same law | unchanged |
| External data-only bar | **D\*** = inner-CV best of {A9, A11 GP-ARD, A12 LightGBM} | A11/A12 gain two tuned options: feature set {raw stresses, the PINN's transformed inputs (A3 abscissae: 1/T, log C-rates, log DoD, SOC_mid, SOC_mid^2) plus t and EFC raw and log}, and storage rows {in, out}. A raw-feature-only LightGBM is reported beside it as a descriptive row (what the features buy) |
| External physics bar | **A10** Stroebl semi-empirical | both "as published" and "with per-cell factor"; the weaker of the two comparisons sets the wording (D015 demand 2) |
| Storage axis | **A13** cycling-only PINN-KAN | g1 and g4 only |
| KAN law | **A15** = closed-form law extracted from a KAN (h in {1, 2}) tuned like A1 | g4 confirmatory; g1 descriptive |
| Matched GAM law | **G15** = the same extraction applied to A4's additive terms | g4 confirmatory; g1 descriptive |
| References | R1, R2, and k = 0 as the window-information reference (F7) | descriptive |

Cut from the confirmatory set: A3 (its abscissae now serve as D\*'s features), A7 (moved to the drop list, g4 descriptive at most),
H3 and the G2 "KAN win" (D015 F11: the generator was strengthened after P4), and H7 except the G0 pipeline check. Positive
control P1 is reduced to the G0 recovery check (nRMSE <= 0.15). The "beat A11/A12 on G0" part goes: the model is being tested on
its own law, so the result is uninformative (F11).

### 1.4 Hypotheses and roles
**PINN role, chain P (primary).**
- **P1, usefulness at scarcity:** at g1, A1 has a lower median condition error than D\*. Tiers N, then S; reverse S is tested
  regardless and reported as a safety finding.
- **P2, attribution to the physics law within the same network:** at g1, A1 against A9, tier S. Tested only if P1 reaches S.
- **P3, data-dependence (the "pays when scarce" signature):** D_c = L_c(g1) - L_c(g4), with L = ln(S_D\*/S_A1), is positive,
  tested by a sign test with margin 0. Tested only if P2 passes.

**KAN role, chain K (primary).**
- **K1, readability at no cost:** at g4, A15 is non-inferior to A1 (tier N at -ln 1.10; S reported if reached).
- **K2, what the KAN adds over an additive law (attributable to the KAN's composition layer):** at g4, A15 against G15, tiers N
  then S. Tested only if K1 passes. Reverse S (G15 better) is tested regardless.

**Qualifiers (secondary family, section 2).** Q-H (A1 against A2) at g1 and g4; Q-A10 (A1 against A10) at g1 and g4; Q-T (A1
against A13) at g1.

**Why this attribution, and why not the alternatives.**
- *Proposal's "physics-informed family, map chosen by inner CV" against data-only learners:* rejected. A gain could come from
  whichever map won, and the paper could not name the component that worked (the opponent's point 1). A1 is now fixed and the
  ladder decomposes the gain. Per condition, ln(S_A9/S_A1) = ln(S_A9/S_AG) + ln(S_AG/S_A1): the first term is the law's share
  with a non-KAN map, the second is the KAN's share inside the law. Both are estimated at every cell with simultaneous intervals.
- *Full 2 x 2 factorial (physics x stress map):* rejected. Without the law there is no stress map, so "data-only with KAN" would be
  a new, made-up model, and it would cost one more neural arm per cell. The nested ladder answers the same attribution question.
- *P1 against A9 only (higher correlation, smaller detectable gain):* rejected as the headline. D015 F5 is right that A9 is a low
  bar. A JES reader asks whether this beats what a practitioner would use, and that is D\*. A9 enters as P2, where it answers the
  attribution question.
- *P1 against A10:* rejected as the PINN's role, because A10 is physics, not data. It is a qualifier (Q-A10), and if A10 wins at
  g1 a title modifier applies (section 4, M2).
- *KAN accuracy race against GAMs (old H1b):* rejected as a primary. P4 found a forecast gap of 0.0-0.1 pp, so it cannot be won.
  It survives as the ladder term ln(S_AG/S_A1), estimated only.
- *KAN pass rules "4 of 5 stable / agreeing":* rejected. The thresholds are not derived, and agreement with a model fitted to the
  same data is not independent (the opponent's point 2). K2 is a held-out prediction test against a matched competitor, which is
  checkable.
- *Misspecification dose-response for the residual (proposal 4b):* rejected. It reads as a straw man and rests on P5 alone. The
  residual's role is Q-H, worded honestly.

### 1.5 Realistic expectation (my reading of the files, not a result)
- K1 is likely to pass: the contrast is between two forms of the same model, with non-inferiority power near 0.96 at
  rho = 0.95 (STATS_RULING 7).
- K2 is likely to come out N or none: P4 found the KAN-GAM gap small.
- Q-H is likely to be none (P5: a 4 % gain).
- Q-A10 at g4 is likely S (D011). At g1 it is unknown and could be reversed, since 9 parameters are what scarce data support.
- P1 is the open risk. No measurement exists for g1. The 80 %-power detectable gain is 17-22 % at rho = 0.75 (STATS_RULING 7;
  different model families).

---

## 2. Statistical plan (outline; the statistician formalises it before the freeze)

**Unit, test and estimand are unchanged (D012):** held-out condition, n = 40; exact one-sided sign test on L_c - m; median
estimand; margins ln 1.02 (S) and -ln 1.10 (N); exact order-statistic intervals.

**Gated: primary graph, family-wise error rate (FWER) 0.025 one-sided.** This is a Bonferroni-based graphical procedure, valid under
any dependence, and it replaces "Holm ordered by the N-tier statistic", which the D015 F4 attack correctly faulted.
- Nodes: P1N -> P1S -> P2 -> P3 and K1 -> K2N -> K2S. Initial weights: 1/2 on P1N and 1/2 on K1. A chain passes its level along
  its own path, and passes it to the other chain only when its last node is rejected.
- At the initial local level 0.0125, P1 needs 28 of 40 positive conditions (exact size 0.0083, PREREG_v3 9.3). If chain K
  completes first, P1 is tested at 0.025 and needs 27 (size 0.0192).
- Reverse-S findings (P1 reverse, K2 reverse) are tested regardless at 0.025 one-sided each, labelled safety findings. Their alpha
  is disclosed as outside the graph: together with the forward test this is a directional two-sided test at 0.05.

**Gated: secondary family, Holm at 0.025 over {Q-A10 g1, Q-A10 g4, Q-H g1, Q-H g4, Q-T g1}.** Tier words follow the template of
section 4.3. Reverse S is evaluated at each test's assigned Holm level.

**Estimated, no tier words:**
- A1 against D\*, A9, AG, A2 and A10 at all 9 grid cells, with simultaneous 95 % exact intervals (Bonferroni over the 9 cells per
  contrast);
- the ladder decomposition per cell;
- the window-information gain (k = 2 against k = 0) per arm;
- the mean paired pp difference with a BCa interval, and the worst-condition error, for every arm and cell;
- per-fold medians; Test C (descriptive, as in D012); NC-2; KAN-law stability and agreement metrics (section 3).

**Fixed rules adopted from the proposal (section 5.3), as amended:**
1. Mean against median: whenever the sign of the mean paired pp difference disagrees with the median log ratio at g1 or g4, the
   abstract adds the mean difference with its BCa interval and the worst-condition error (D015 F3).
2. Automatic downgrade: if any of the following rows lowers the tier of a gated or secondary contrast, the abstract's tier word is
   lowered to that row's tier, with no discretion (closes D015 F2.4):
   - the lab-stratified row;
   - the lab-and-stage-indicator row on Test B, which includes A10 and D\* (closes the A10 gap of D015 F8);
   - the retain-every-check-up row;
   - the random-subset row at g1 (3 seeded random nested subsets in place of max-min, for A1 and the D\* candidates; condition
     scores averaged over the 3).

   Every other sensitivity row is reported and has no consequence.
3. Test C appears in the abstract in its fixed D011 sentence only if the lab-indicator row leaves the sign of its median ratio
   unchanged. Otherwise it goes to Limitations. It is always reported in the Results. This is a rule, not a choice.

**Must be simulated or computed by the statistician before the freeze:**
- (a) Size of the exact sign test when condition errors share fold-level and lab-level random effects with the ISU-like skew,
  including the nested-subset correlation across grid cells (D015 F4). If the size exceeds 1.2 x nominal, the statistician files
  a pre-set fallback (for example a fold-blocked permutation version), approved by the gate auditor before any Samsung score.
- (b) Power for P1 at g1 for rho in {0.6, 0.75, 0.9} at local level 0.0125, and the chain probabilities for P2 and P3. The trend
  test P3 is a contrast of two log ratios, so its power is unknown and must be simulated.
- (c) Power for K1 and K2 (rho for A15/A1 and A15/G15 assumed at 0.9-0.95, then estimated).
- (d) FWER of the graph under the dependence between P1, P2 and P3 (same conditions, nested fits). The graph is valid by
  construction; the check guards against implementation errors.
- (e) Existence and coverage of exact order-statistic intervals at 1 - 0.05/9 with n = 40.
- (f) rho estimated from inner-CV condition scores (ISU in P6, Samsung training sides), for the power report only. No rule changes
  with it.

---

## 3. KAN validation (what is external, and its limits)

1. **Frozen symbolic library and extraction rule.** Committed with a hash before any outer prediction, and identical for A15 and
   G15.
   - Library per edge: zero (pruned); linear; quadratic; power x^p on a positive physical abscissa; log; exponential; Arrhenius
     exp(-b/T) on temperature only; hinge max(0, x - c).
   - Each surviving edge is fitted on a fixed grid over the fold's training hull and chosen by BIC. A per-edge cap on free
     coefficients is set by the method-architect before the freeze and is the same for both arms.
   - The free coefficients are then refitted end to end under the same loss.
   - Unit tests: a noiseless synthetic law is recovered; with an untruncated library A15 reproduces A1 to float tolerance; G15 and
     A15 coincide when h = 1 and the outer edge is linear.
2. **Matched GAM simplification (G15).** Same library, BIC rule, cap and refit, applied to A4's additive terms. The calendar KAN
   [1,2] is the same in both arms and is extracted identically, so K2 isolates the cyclic map, which is where the KAN's composition
   layer (the part an additive GAM lacks) can matter. Coefficient counts and training-side BIC of both laws are printed beside K2.
3. **External test = prediction of held-out conditions.** K1 and K2 are scored on Test B outer conditions that the extraction never
   saw. This is the independent check the opponent asked for: a formula that predicts unseen conditions, not a formula that looks
   plausible.
4. **Stability over the supported region (descriptive, no threshold).** Per law: the median, over a fixed 500-point Latin
   hypercube restricted to the intersection of the five training hulls, of the fold-to-fold SD of the predicted log-rate, divided by
   its range. Reported for A15 and G15 side by side, together with the per-input family labels across folds (pruned counts as a
   label).
5. **Comparison with A10 and with the dataset authors' observations (descriptive, labelled "consistency with same-data models").**
   Direction of each extracted cyclic effect against the sign of A10's exponent (needs FB-2). Calendar SOC law: whether the slope
   changes sign above SOC 0.8, against the non-monotonic behaviour above 80 % SOC that the dataset authors report (data paper, full
   text). This uses storage cells only, and SOC > 0.8 exists in stage 1 only.
6. **Independent literature only where verified.** Before any activation energy is compared with literature, the cell chemistry
   must be verified from a primary source with a Crossref-verified DOI or the manufacturer's datasheet; the data paper read so far
   does not state it. Each literature value then needs a DOI, a page or table location, and a comparable SOC, temperature range and
   protocol, checked by the citation validator. If any of these is missing, the comparison is omitted and the text says so.
7. **Confound limits, printed:**
   - E(SOC) is lab-confounded (10 C storage all SIE, 45 C all HM) and is reported only as an "effective" value with a lab-indicator
     row.
   - The temperature dependence of the cycling law cannot be separated from lab (35 C all INT), so no Arrhenius statement is made
     for the cycling term.
   - The calendar share of cycled-cell fade is model-defined (D015 F9).
   - "Physics-informed" means a phenomenological rate law; no electrochemical mechanism is claimed.

---

## 4. Closed outcome table (for Shlok's approval)

Evaluation order: gate G, then the P state, then the K state, then modifiers M1 and M2, then the fixed qualifier sentences. No row
requires a choice after the data. Bracketed values are filled from `runs/` by the statistics step. Bracketed alternatives inside a
sentence are chosen by the rule stated next to them.

### 4.1 States
- **Gate G:** NC-1 trips, the G0 pipeline check fails, a test-fold read is found, or a freeze condition of section 5 is unmet at the
  freeze. Then there is no title and no claim: audit, then a new version.
- **P+:** P1 reaches tier S at g1. **P0:** P1 reaches tier N or none, and not reverse S. **P-:** P1 reverse tier S.
- **K+:** K1 passes and K2 reaches tier S. **K-:** K2 reverse tier S (tested regardless of K1). **K=:** every other case (K1 passes
  and K2 is N or none; or K1 fails without K2 reverse).
- **M1:** Q-H reverse S at g1 (the hard ODE lower than A1 at the headline cell). In titles T1-T3 and T9a/T9b, the phrase
  "Physics-informed neural networks" is replaced by "Physics-constrained neural ageing models"; the abstract sentence of Q-H is
  required.
- **M2:** P+ and Q-A10 reverse S at g1 (the dataset authors' model lower than A1 at the headline cell). Titles T1-T3 are replaced by
  T9a (K+ or K=) or T9b (K-).
- **ISU fallback (D005, Samsung not parsed by 07 Nov 09:00):** the same table on ISU, with "cycle ageing" scope words and the clause
  "(the analysis was specified after exploratory use of this dataset)" added to the abstract scope sentence. Titles are unchanged.

### 4.2 Titles and abstract claim sentences (one each)
P-part extent clause, fixed by P2 and P3:
- (e1) P2 S and P3 S: "most of the advantage came from the physics law, since the same network without it was [Y] % worse, and the
  advantage was larger with 8 than with 32 cycling conditions"
- (e2) P2 S and P3 not: "the same network without the physics law was [Y] % worse; a dependence of the advantage on the number of
  cycling conditions was not shown"
- (e3) P2 not S: "a gain attributable to the physics law within the same network was not shown"

| P \ K | K+ | K= | K- |
|---|---|---|---|
| **P+** | **T1** "Physics-informed neural networks with readable Kolmogorov-Arnold stress laws forecast lithium-ion capacity fade from few cycling tests and early check-ups" | **T2** "Physics-informed neural networks with Kolmogorov-Arnold stress functions forecast lithium-ion capacity fade from few cycling tests and early check-ups" | **T3** "Physics-informed neural networks forecast lithium-ion capacity fade from few cycling tests and early check-ups" |
| **P0** | **T4** "Readable Kolmogorov-Arnold stress laws for lithium-ion capacity fade, with learning curves of physics-informed and data-driven forecasts from few cycling tests" | **T5** "How many cycling tests and check-ups do physics-informed and data-driven forecasts of lithium-ion capacity fade need? Learning curves with Kolmogorov-Arnold stress functions" | **T6** "How many cycling tests and check-ups do physics-informed and data-driven forecasts of lithium-ion capacity fade need? Learning curves on a designed ageing dataset" |
| **P-** | **T7** "A physics prior does not help lithium-ion fade forecasts from few cycling tests but yields readable Kolmogorov-Arnold stress laws" | **T8** "When a physics prior does not help: learning curves of physics-informed and data-driven forecasts of lithium-ion capacity fade from few cycling tests" | **T8** |

- **T9a** (P+ with M2; K+ or K=): "Physics priors pay when cycling tests are few: semi-empirical, physics-informed Kolmogorov-Arnold and data-driven forecasts of lithium-ion capacity fade"
- **T9b** (P+ with M2; K-): "Physics priors pay when cycling tests are few: semi-empirical, physics-informed and data-driven forecasts of lithium-ion capacity fade"

**Abstract claim sentence per cell.** The common lead-in is "With eight cycling conditions and two check-ups per held-out cell,".

- **P+/K+:** "...the physics-informed network's typical (median) held-out-condition error was [X] % lower than that of the best tuned
  data-driven learner (95 % interval [a, b]; n = 40), (e1/e2/e3), and a closed-form stress law extracted from its Kolmogorov-Arnold
  network predicted held-out conditions no more than 10 % worse than the full network and [Z] % more accurately than an equally
  simplified additive law (interval)."
- **P+/K=:** as P+/K+ up to (e·), then "and a closed-form stress law extracted from its Kolmogorov-Arnold network [K1 pass: 'predicted
  held-out conditions no more than 10 % worse than the full network, but was not shown more accurate than an equally simplified
  additive law (interval)' / K1 fail: 'was not shown to stay within 10 % of the full network, so no readable-law claim is made']."
- **P+/K-:** as P+/K+ up to (e·), then "while an equally simplified additive stress law predicted held-out conditions [Z] % more
  accurately than the law extracted from its Kolmogorov-Arnold network (interval)."
- **P0/K+:** "...the physics-informed network's typical held-out-condition error [N: 'was no more than 10 % above' / none: 'could not
  be distinguished from'] that of the best tuned data-driven learner (interval; n = 40), and a closed-form stress law extracted from
  its Kolmogorov-Arnold network predicted held-out conditions no more than 10 % worse than the full network and [Z] % more
  accurately than an equally simplified additive law (interval)."
- **P0/K=:** P0 part as in P0/K+, then the K= clause of P+/K=.
- **P0/K-:** P0 part, then the K- clause of P+/K-.
- **P-/K+:** "...the best tuned data-driven learner's typical held-out-condition error was [X] % lower than that of the
  physics-informed network (interval; n = 40), whereas a closed-form stress law extracted from its Kolmogorov-Arnold network
  predicted held-out conditions no more than 10 % worse than the full network and [Z] % more accurately than an equally simplified
  additive law (interval)."
- **P-/K= and P-/K-:** P- part, then the K= or K- clause.
- **T9a/T9b (M2):** the P+ sentence of its K column, followed by the required clause "; the dataset authors' semi-empirical model was
  [W] % more accurate still at this cell (interval)."

### 4.3 Qualifier sentences (always present in Results; in the abstract for Q-H g1, Q-A10 g1 and g4, and Q-T g1)
| Tier | Template |
|---|---|
| S | "[A] had a median condition error [X] % lower than [B] (interval; n = 40)" |
| N | "[A] was no more than 10 % worse than [B] (one-sided bound); not shown better" |
| none | "[A] and [B] could not be distinguished (interval)" |
| reverse S | "[B] had a median condition error [X] % lower than [A] (interval)" |

- Q-H at "none" must read: "the soft residual was not shown necessary relative to exact integration of the same law".
- Q-A10 names "the dataset authors' semi-empirical model", and the weaker of its two forms sets the tier.
- Q-T names "training with and without the storage cells".
- Words never used: "matches", "interpretable physics discovered", "outperforms" below tier S, and "first" unless the novelty
  auditor clears the new framing (section 5).

---

## 5. Red-team findings: resolved here, and still freeze conditions

**Resolved by this design:**
- **F1:** each named component has a gated, attributable test (P chain, K chain), and the residual has an honest qualifier with
  fixed "not shown necessary" wording. Note: this resolves F1 as a design fault. It does not promise a win; section 7 says so.
- **F2:** the table is closed. Reverse tiers are covered everywhere, the automatic-downgrade rule applies, Test C follows a rule, and
  no "put to Shlok" row remains.
- **F3:** the mean/worst-case rule.
- **F4, in part:** alpha accounting is a graph plus a Holm secondary family; ordering by the tested statistic is moot.
- **F5:** the headline bar is D\*; A9 is attribution only.
- **F7, in part:** D\* has physics features and the storage rows; the k = 0 window reference is added.
- **F8, in part:** the lab-indicator row on Test B includes A10 and D\* and lowers tiers automatically.
- **F11:** H3, the G2 win and the synthetic "beat A11/A12" part are struck.
- **F12, for the outcome table:** superseded by this file.

**Still freeze conditions (all must be met before `runs/prereg/FROZEN`):**
1. FB-1 to FB-6 and FB-8 to FB-10 of PREREG_v3, unchanged. This includes Zhang JES 182, 125097, Stroebl JES 142, 119552 and Hallinger
   read in full, and A10 verified with its recovery test (F6, F13).
2. Statistician's items (a)-(f) of section 2 (F4).
3. **PREREG_v4** written from this file. The code, `stats_step.py`, the README and draft 5.5 are aligned with it, and the F12 items
   are fixed. The gate auditor ticks it.
4. Novelty auditor re-checks the **data-efficiency framing** (physics-prior learning curves for battery fade, including Guo et al.
   arXiv 2607.16864, already on file) before any "to our knowledge" sentence (F13).
5. All new code exists with the limiting-case unit tests of proposal 5.5, plus: the nested selector reproduces the subsets for the
   same identifiers; m = 32 reproduces Test B bit for bit; G15 equals A15 in the h = 1, linear-outer case.
6. P6 (ISU, training sides) has been run and its pre-set reading reported to Shlok (proposal 5.6). The result does not change the
   design.
7. Shlok's approval row for this outcome table in DECISIONS.md.

**Remaining as stated limitations, not fixable this week:** F9 (collinearity of the calendar and cycling terms; phenomenological
law); F14 (one cell type, constant stress, capacity only; no LSTM or Transformer unless the optional GRU of section 6 is built);
F10 timetable risk; F15.6 (the preregistration is only local). On F15.6 I recommend Shlok publicly timestamp the frozen file's hash
(OSF or Zenodo); that is his decision because it publishes something.

---

## 6. Code and time cost, and what to drop

**Code (one implementer).** The proposal's estimate of 2-3 days stands, plus about half a day for my additions. The items are:
- the nested, temperature-constrained subset selector;
- the k = 0 and k = 2 paths;
- the A15/G15 extraction with its frozen library and tests (the largest item);
- the D\* feature and storage options;
- h = 1 in the KAN grid;
- the graphical procedure, simultaneous intervals and sentence templates in `stats_step.py`;
- the random-subset rows.

Total about 3-3.5 days, plus P6 (half a day, run in parallel). Removed work: H3, H7 beyond G0 (the Kendall-tau and 20-draw pieces
were not built), A3/A5/A7 on the grid.

**CPU.** This is my arithmetic from PREREG_v3 section 16, not a measurement. One neural arm over 5 folds at full data is about
1.2 CPU-h expected and 4.5 at the ceiling (9.4 / 35.8 for 8 arms, N = 20). The m = 16 and m = 8 refits cost about 0.5 of that each
(fewer cycling cells, 2 inner folds; the storage cells stay). With A1, A9, AG and A2 on all m, A5, A13, A15/G15 and the g1
random-subset rows, the grid comes to about 13 arm-units: about 16 CPU-h expected, about 60 at the ceiling. With NC-1, NC-2, Test C,
the GP refits and G0, the core is about 25 expected and 85 ceiling, which is similar to PREREG_v3's core (25 / 77). On 3
single-thread processes that is about 8-9 h wall-clock expected and about 28 h at the ceiling. The timing run at the freeze commit
fixes N.

**Drop order if the week is short:**
1. A14, Test A, S3 (already last).
2. S2/H5.
3. A7 and the optional GRU member of D\*.
4. H7 synthetic beyond G0.
5. Random-subset rows cut to 1 draw and made descriptive (they leave the downgrade rule).
6. The m = 16 level. P3 uses only g1 and g4, so this costs only the middle of the curve.

**Never dropped:** g1, g4, A1, A9, AG (A4), A2, D\*, A10, A15, G15, NC-1, the lab-indicator row.

---

## 7. Message to Shlok (one paragraph)

This paper can now show, in tests fixed before any Samsung score, whether the physics prior earns its place and whether the KAN
does. The PINN's test: with only 8 cycling conditions and 2 check-ups, does it forecast held-out conditions better than the best
tuned data-driven model, and does the gain come from the physics law (the same network without it), shrinking as data grow? The
KAN's test: does it give a closed-form stress law that predicts unseen conditions about as well as the full network, and better
than an equally simplified additive law? It cannot claim that the soft residual is necessary (the closed-form ODE uses the same
law, and the pilot gain was 4 %), any temperature mechanism or validated activation energy (temperature and lab are aliased), more
than one cell type under constant stress, or a "first". At full data the best data-driven learners already sit near the replicate
spread (P3), so no full-data win over them is expected. Nothing has been measured for the scarce cell, and its 80 %-power detectable
gain is 17-22 %. The realistic best case is T2: the PINN beats data-driven learners at the scarce cell, the gain is traced to the
physics law, the KAN law is readable at no accuracy cost but no better than an additive law, the residual is "not shown necessary",
and the semi-empirical model is beaten at full data. An equally plausible case is T5, an honest learning-curve paper that is weaker
for JES. The ISU pilot P6 gives the first signal before the freeze. Please approve or change the nine-cell table and modifiers M1
and M2 as written; after the freeze no sentence will be chosen by anyone.

---

## 8. Re-open if
- P6 shows the data-only learners ahead at the smallest m on most ISU training sides. This does not change the design, but Shlok
  may then choose to stop before spending compute.
- The statistician's item (a) fails and no pre-set fallback is accepted.
- Zhang, Hallinger or Stroebl JES 142 contains a data-efficiency study of learned ageing laws on this dataset.
- The A15/G15 extraction cannot pass its unit tests by the freeze. Chain K is then struck before the freeze and its weight of 1/2
  goes to chain P (P1 tested at 0.025). The K state is fixed at K= with the K1-fail clause ("no readable-law claim is made"), and
  the table is otherwise unchanged.
- k_full < 2.
- Shlok changes the table.
