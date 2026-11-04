# D011 judge's verdict: what the frozen preregistration must contain (2026-11-05)

Role: judge (did not write the draft, the ruling or the audit). Reading: **full text** of CONTRACT.md,
`debates/D010_topic/04_judge.md` (D005), `research/DECISIONS.md` (D001-D009), `runs/prereg/PREREG_DRAFT.md` (v0.1),
`runs/prereg/STATS_RULING.md`, `runs/GATE_pilots_audit.md`, `debates/codex_panel/turn03_response.md`,
`runs/pilot_P3/RESULT.md`, `runs/pilot_P4/RESULT.md`, `runs/pilot_P5/RESULT.md`, `runs/samsung_pipeline/RESULT.md`,
`debates/D010_topic/05_novelty_reaudit.md`, `notes/exemplars/BLUEPRINT.md`. No paper read by me; no code run; no data
opened. Every number below is quoted from those files (pointer given) or is a decision rule fixed now. Cited as
"SR§n" (statistics ruling), "GA" (gate audit), "Cx§n" (Codex turn 3), "J§n" (D005 judge file), "PD§n" (draft).

---

## 0. Verdict

**REVISE.** The draft is sound in structure (splits from identifiers, test-fold guard, outcome table before data,
controls) and the statistician's ruling fixes its margin problem. Four changes are needed before it can freeze:
(1) the primary family is narrowed to the three contrasts that carry the paper's claim, with the dataset authors'
model in and the data-only learners moved to a gatekept key secondary (section 1); (2) the 35 C hold-out is a
joint temperature-laboratory transfer test, never a temperature test (section 2); (3) the primary contrast is
tested on the log-ratio scale with a test that targets the mean and whose level is verified by simulation before
the freeze, with a pre-set fallback that holds level by construction (section 4); (4) the arm list is cut to the
essential set (section 1.3). The likely outcome is title 3 and Shlok must be told now (section 3).

---

## 1. Hypotheses and the primary Holm family

### 1.1 Ruling on the statistician's family {H1a, H1b, H1c, H6}

| ID | Statistician | Ruling | Reason |
|---|---|---|---|
| H1a residual (A1 vs A9, lambda = 0) | primary, S | **Accept, primary** | Tests that the physics part does work (J§1 (i)). Same-model pair, SR§7 power about 10% relative at n = 40. |
| H1b stress map (A1 vs inner-CV-best of the alternative pool) | primary, S | **Accept, primary; pool amended** (1.3) | Tests that the KAN does work (J§1 (ii)). P4 shows a small forecasting gap (0.0-0.1 pp, P4 RESULT item 1), so tier N or "none" is the likely result; the test must still be run as primary because the title names the KAN. |
| H6 dataset authors' semi-empirical model (A1 vs A10) | primary, S | **Accept, primary** | Closest prior art on the same data (D006; re-audit §0, §3 row 2). Any contrast named in title/abstract must be in the family (SR§3). Fairness amendment in 1.4. |
| H1c best tuned data-only learner (A1 vs best of A11/A12) | primary, N then S | **Amend: key secondary, serially gatekept** | SR§7: superiority needs about a 19% true gain (rho 0.75), and the non-inferiority tier is reached only 24-40% of the time even at true equality. P3 puts the best learner at the replicate reference on ISU (ratio 0.90) and near it on SNL (1.13). In the family it would mostly cost alpha and add an outcome branch; Codex (Cx§5.3) asks for exactly this cut. Gatekeeping keeps it confirmatory at no cost to the family. |

**Final primary Holm family: {H1a, H1b, H6}**, one-sided, family-wise 0.025 (SR§3), hierarchical tiers N then S per
contrast (SR§2.3), on the log-ratio scale with the test of section 4.
**H1c rule:** tested at the full 0.025 (tiers N then S) **only if all three family members reach tier S**
(serial gatekeeping; FWER preserved). If the gate is closed, H1c is reported with its interval and the label
"secondary, not tested", and the abstract may only use the "none" wording for it.
**Claim contract (amends J§1 (iii)):** "On held-out Samsung 50E cycling conditions (Test B, primary window) the
PINN-KAN has lower condition-level retention RMSE than (i) the same network without the physics residual,
(ii) the same PINN with the best alternative stress map, and (iii) the dataset authors' semi-empirical calendar +
cycle model." The data-only comparison is a key secondary. D007/D009's consequence stands: "beats data-driven
models" appears nowhere unless H1c is tested and reaches tier S.

### 1.2 The other hypotheses

| ID | Status | Rule |
|---|---|---|
| H2 hard ODE vs soft PINN | decision contrast (not in family) | As SR§3: outcome A tested only if the family passes (gatekept); C tested regardless (safety); then B by TOST at +-ln(1.10); else "unresolved", worded as B. |
| H3 KAN wording | derived | Against the inner-CV-best of A4, A5 (GAMs only), as PD§9.7; "win" also needs the strengthened, validity-checked G2 (PD§13). |
| H4 Test C (section 2) | secondary | Two contrasts, Holm-2 inside Test C at 0.025: A1 vs best of A11/A12 (tier N), A1 vs A10 (tier S). n = 13: SR§7 MDE above 17%; descriptive in strength. |
| H5 storage transfer S2 | secondary | A1 non-inferior to the inner-CV-best of A3, A9, A10 at -ln(1.10), one test at 0.025. |
| X1 joint vs cycling-only training (A1 vs A13) | **secondary, descriptive** (raised from exploratory) | Joint storage-plus-cycling training is part of the novelty statement (D006); a reviewer will ask whether storage cells help. Interval and unadjusted tier reported; no claim word beyond "joint training lowered / did not lower the error". |
| H7 synthetic identifiability | supporting figure | PD§13 unchanged, plus the G2 validity rule. |
| ISU, SNL | secondary, **not blind** (GA C8) | Same rule per dataset, unadjusted across datasets, never pooled with Samsung; contrasts H1a, H1b (pool A4, A5, A7), H6-analogue (cyclic semi-empirical form), H1c (not gatekept there, labelled secondary). |

### 1.3 Arms: the essential set and where every removed arm goes

Test B (primary) arms: **A1, A2, A3, A4, A5, A7, A9, A10, A11, A12, A13, R1, R2.** H1b pool = **{A3, A4, A5, A7}**.

| Arm | Fate | Reason |
|---|---|---|
| A1 PINN-KAN | primary | the model |
| A9 data-only F | primary (H1a) | isolates the residual; same z_c, inputs, inversion (E1) |
| A3 parametric stress factors in the same PINN | primary pool (H1b) | the only arm that isolates "learned vs Arrhenius/power-law" inside the same machinery; A10 differs in more than the stress map |
| A4 additive GAM (= KAN [5,1]) | primary pool (H1b), H3 | the opponent's identity point (J§5 Opp 2.1) |
| A5 interaction GAM | primary pool (H1b), H3 | strongest prespecified-interaction contrast |
| A7 MLP stress map (PiDDM-style, parameter-capped) | primary pool (H1b) | OPEN-2 accepted; J§1 (ii) names a parameter-matched MLP. GA notes the J§6 arm list called the parametric arm "PiDDM-style": that label now belongs to A7 only, A3 is "parametric". |
| A10 Stroebl semi-empirical | primary (H6) | closest prior art |
| A2 hard-ODE-KAN | decision contrast (H2) | decides the PINN framing |
| A11 GP-ARD, A12 LightGBM | key secondary (H1c) | best of the two by inner CV (P3: LightGBM won 3/5 ISU, 5/5 SNL folds) |
| A13 cycling-only PINN-KAN | secondary (X1) | see 1.2 |
| R1 persistence, R2 window-linear | references (positive and negative control) | no tuning, negligible cost |
| A6 degree-2 log-polynomial | **dropped** | 21 cross terms on 40 conditions; its information is covered by A5 (prespecified interactions) and A7 (flexible map); compute. Discussed in text, no numbers. This amends J§1 (ii)'s list; the change is recorded in D011. |
| A8 free G on real data | **dropped on real data; kept in the synthetic H7 only** | its role is identifiability (structured vs free), which is synthetic by design (J§6); on real data it adds an arm without a hypothesis |
| A14 storage-only | **exploratory** (S2 only, first to be cut) | no claim depends on it |
| Test A arms (A1, A2, A9) | **exploratory**, appendix | held-out replicates of seen conditions is not the paper's question; SR§1.1 keeps R_LOO as its yardstick |

Test C arms: A1, A9, A10, A11, A12 (n = 13 cannot resolve the stress-map contrasts). S2 arms: A1, A3, A9, A10
(+A14 exploratory). Negative control: A1, A9 (A4 dropped from it; the control's two conditions use A1, A9, R2 only).
Synthetic: A1, A2, A4, A8 (PD§13). Neural Test B arms fall from 9 PINN-type + 1 hard to 7 + 1 (PD§16 table to be
recomputed; same per-arm budget, no trial or seed cut).

### 1.4 Fairness of A10 (H6)

Codex (Cx§2.1) warns an unfair Stroebl baseline could sink the paper. Ruling: **A10 primary** = the published form
(Stroebl data paper SI S.1.1, after Muehlbauer et al., J. Energy Storage 48, 103803, doi 10.1016/j.est.2021.103803,
Crossref-verified per the re-audit §1), population parameters fitted by multi-start least squares on the training
conditions, **plus one per-cell multiplicative factor on the predicted loss fitted to the cell's window points by MAP
with the same prior family as A1's delta_c**, and the same throughput input as every arm. Sensitivity: A10 as
published (no per-cell factor). The equations are taken from the SI and the JES 142, 119552 full text with equation
numbers recorded (PD§7 says the local conversion is garbled: not freezable until fixed). A10 gets a parameter-recovery
unit test on data generated from its own form.

---

## 2. Test C (35 C): framing and wording

**Fact (SR§4, GA §1, PD§3.3(7)):** all 13 conditions / 39 cells at 35 C were run by lab INT; INT also runs 6 of the
10 conditions at 23 C (plus 1 mixed); 45 C is HM and SIE. Temperature is aliased with laboratory at 35 C, and storage
does not exist at 35 C. Accepting Cx§4 in full:

- **Name:** "held-out temperature-laboratory domain (35 C, laboratory INT)". Never "temperature extrapolation",
  "untested temperature" alone, or "temperature generalisation". It is not called interpolation in temperature either,
  because the lab is new to that temperature.
- **What partly separates the two:** INT cells at 23 C are in Test C's training set. Sensitivity row (mandatory):
  A1, A9, A12 with a lab indicator in the per-cell prior/inputs, so an INT offset is learned from INT at 23 C; the
  result is identified only under "no lab x temperature interaction", stated as that assumption. Report the stage
  composition of the 13 conditions (from identifiers) and the CU surface-temperature offsets by lab (pipeline item 7)
  beside Test C, because capacity measurement is not isothermal and differs by lab.
- **Calendar twins at 35 C** remain label-free collocation (mechanism); no sentence may present them as evidence
  for the temperature response (Cx§3, §4).

| Test C outcome (H4, Holm-2 inside Test C) | Title | Abstract |
|---|---|---|
| A1 vs A10 tier S and A1 vs best data-only tier N or S | never mentions 35 C or temperature | may add: "and on a held-out combination of temperature and laboratory (35 C cells from one laboratory, n = 13 conditions), [tier wording]", followed in the same sentence by "temperature and laboratory cannot be separated in this design" |
| one of the two reached, the other not | same | the reached contrast with the same clause, and the other one with "could not be distinguished" |
| neither reached | same | no Test C sentence in the abstract; Table 1 column, Results paragraph and a Limitations sentence report it with intervals (no selective omission from the paper) |

No Test B vs Test C ratio anywhere (retired topic, J§6).

---

## 3. Titles and abstract wording by outcome, and the likely outcome

### 3.1 What is likely (stated plainly)

From the files, not hoped: H1b forecasting gap on synthetic G2 was 0.0-0.1 pp (P4 item 1) against an MDE near 10%
(SR§7); H2 synthetic median ratio 0.96 with one reversal (P5); H1c needs about 19% (SR§7) against learners already at
the replicate reference (P3). H6 is the contrast most likely to reach S (the authors call their cycle part inadequate;
JES 142, 119552 abstract per the re-audit), but with the per-cell factor of 1.4 that is not guaranteed. **Most likely
outcome: H6 S; H1a S or N; H1b N or none (KAN tie wording); H1c gate closed or unresolved; H2 unresolved.
That is title 3.** Title 1 needs S on all three family members and H2 = A; I rate that unlikely.
**The lead must tell Shlok now, before the freeze**, that title 3 is the expected endpoint, that "outperforms
data-driven models" is improbable, and that the strength of the paper will rest on the calendar-cycle law, the
comparison with the dataset authors' model, the physical checks (section 6) and the evaluation design. His answer
does not change any rule; it tells him what kind of paper the week produces.

### 3.2 Outcome table (replaces PD§11; evaluate gate first, then the first matching row)

Titles: **T1** "Physics-informed neural networks with Kolmogorov-Arnold stress functions forecast calendar and cycle
ageing of lithium-ion cells at untested conditions"; **T2** "Coupling calendar and cycle ageing in a physics-informed
Kolmogorov-Arnold network to forecast lithium-ion capacity fade under unseen stress conditions"; **T3** "Learning
stress-dependent calendar and cycle ageing laws of lithium-ion cells with physics-informed neural networks and
Kolmogorov-Arnold networks"; **TF** fallback (J§1, ISU primary).

| # | Condition | Title | Abstract / highlights wording |
|---|---|---|---|
| G | negative or positive control fails, or a test-fold read is found | none | no claim; audit; new version |
| 1 | H1b reverse tier S (KAN worse than the best alternative map) | KAN leaves the title; retitle put to Shlok | "a [winning map] stress model was more accurate than the KAN" |
| 2 | H1a not S (residual no better than lambda = 0) | T3 at most; framing put to Shlok | "the physics residual did not lower the forecast error" plus its interval |
| 3 | H6 not S | T3 at most; lead tells Shlok before writing | "could not be distinguished from" / tier-N wording against "the dataset authors' semi-empirical model"; no "outperforms physics-based models" |
| 4 | H1a S, H6 S, H1b N or none | **T3** | KAN tie wording (J§3): "reached the accuracy of the best prespecified-interaction model without specifying the interactions", with interval; never "outperforms" for the KAN |
| 5 | family all S, H2 = C | framing to Shlok: C1 (J's recommendation) T2 with "physics-informed Kolmogorov-Arnold network", or C2 T1 wording kept with the hard ODE reported stronger | as J§2 |
| 6 | family all S, H2 = B or unresolved | **T3** (J§2: PINN contribution not shown) | "lower error than the same network without the residual, the best alternative stress map and the dataset authors' model by X% (CI)"; "the soft residual and exact integration of the same law were [equivalent / not distinguished]" |
| 7 | family all S, H2 = A | **T1** (T2 allowed) | as 6, plus "the soft residual lowered the error relative to exact integration"; KAN "superiority" only if H3 "win" holds |
| H1c add-on (rows 6-7 only; gate open) | S | no title change | "and lower than the best tuned data-driven learner by X% (CI)"; highlights may say "outperformed" |
| | N | no title change | "no more than 10% worse than the best tuned data-driven learner (one-sided bound ...)"; "comparable" only after TOST |
| | none / gate closed | no title change | "accuracy could not be distinguished from tuned data-driven learners" with interval |
| T, S, X1 | Test C (section 2), S2 (H5 non-inferior: storage sentence allowed, else removed), X1 (descriptive) | no title change | as section 2 / SR§6 |

All tier words follow SR§6 (no p-values, no "significant", "outperforms" only at tier S, "matches" never). Every
abstract number is a relative reduction (geometric-mean ratio, section 4) with its 95% interval and n, plus the pp
difference with its interval. Scope words: "held-out cycling conditions of one cell type in three laboratories".

---

## 4. Type-I inflation under skew: the test

**Problem (SR§2.3, §7):** the Wilcoxon-AND-BCa rule is liberal at the null boundary under strong left skew of d
(a few conditions where PINN-KAN fails badly): 1.6-2.3 times nominal. The Wilcoxon cannot be justified here: it tests
the pseudo-median, which under left skew lies above the mean, so at "mean = margin" it rejects too often. The
estimand in the claim and the abstract is a mean over conditions.

**Ruling.**
1. **Scale.** The primary contrast per condition is L_c = ln(S_comp,c / S_PINN,c); margins ln(1.02) (S) and
   -ln(1.10) (N) — the statistician's own robustness margins (SR§2.2), so the relative margins become exact and need
   no E estimate. Reasons: the margins are already relative; condition errors are heteroscedastic (CV 0.45 on both
   pilots, SR§2.2), so a pp mean is dominated by the hardest conditions; the log compresses exactly the failure tail
   that causes the left skew; the abstract's main number (relative reduction) becomes the estimand itself
   (exp(mean L) - 1). The pp mean difference with its BCa interval is reported beside every tier; if the pp tier
   (SR's rule, margins 0.02E/0.10E from `margins.json`) differs, the abstract states both (SR§2.2 rule kept, roles swapped).
2. **Test.** One-sided **studentized sign-flip permutation test** of mean(L - m) (statistic t = mean/(sd/sqrt n);
   100,000 random sign vectors plus the identity; p = (1 + #{t* >= t})/(1 + B); fixed RNG seed), **AND** the one-sided
   BCa lower bound of mean(L) at 1 - a exceeding m (10,000 condition resamples). The sign-flip test targets the mean
   (exact under symmetry, asymptotically valid without it); the AND can only lower the level, never raise it, and
   keeps decision and interval in agreement. The Wilcoxon is reported in the appendix only.
3. **Verification before the freeze (statistician, no Samsung data).** Re-run the null-boundary simulation for this
   exact rule at n = 40 and n = 13, at the Holm levels 0.025/3, 0.025/2, 0.025 and the gatekept 0.025, with at least
   10,000 simulations per cell. Shapes: generate the two arms' condition scores as positive, correlated variables
   (CV 0.45; rho 0.95, 0.90, 0.75), then (a) the ISU-derived shape, (b) normal, (c) **failure contamination**: PINN
   errors inflated on a fraction of conditions, with fraction and size set so that the pp difference has the skewness
   of the mirrored ISU shape (-1.06, SR§7 A3). **Acceptance:** simulated rejection <= 1.2 x nominal in every cell.
4. **Fallback, fixed now (used if 3 fails in any cell at n = 40):** exact one-sided **sign test** on L - m (estimand:
   median condition log-ratio; holds level for any continuous distribution) with the order-statistic interval of the
   median; abstract words become "on the typical held-out condition ... (median)". Test C uses the fallback if 3 fails
   at n = 13 only.
5. Power is re-reported for the adopted rule (SR§7 table re-run on the log scale); no rule changes after that.

---

## 5. Gate-audit conditions C1-C9

| C | Ruling | Fix |
|---|---|---|
| C1 P3 slot | **Accepted, amended by D009** | The slot becomes descriptive: ISU W4 0.90, SNL W100 1.13 (P3 RESULT), with "D007 superseded by D009; no gate". Header: "P3 used (descriptive only)". PD§3.4 fallback: H1c on ISU uses the hierarchical rule, not a pre-decided non-inferiority. Samsung: E/R_LOO and E/R_WARP computed on training sides after parsing, descriptive. |
| C2 NI margin, unresolved row | **Closed** by D009 and section 4 here (-ln(1.10); the floor is not a margin) | Unresolved-H1c row added (3.2 "none"). |
| C3 ledger rows | **Closed by D008 + D011.** D008(a) confirmed with a condition: a Samsung training-fold timing run before the freeze; if the median hard-ODE fit > 30 s or PINN fit > 90 s, the J§7 Partial plan (trials 20 -> 10, inner folds 3 -> 2, seeds 5) applies **to every arm equally**. D008(b) confirmed (no test label scored; outcome-equivalent). Arm list: section 1.3. | |
| C4 number errors | **Accepted** | P0: 6 CU + 2 exCU and 10 CU + 5 exCU; PD§5 "8 and 15"; the 0.5 GB estimate is withdrawn as unsupported (GA computed about 0.37 GB CU-only; moot once the full download exists); P0 stage/temperature labels annotated (TP_k03_01 is stage 2, 23 C). P1 N3 (35 not 30 of 61 cells), pipeline N4 (cycling stage-2 median 76 d), P3 N5 (pair ratio with its own CI). Corrections as dated errata appended to each RESULT.md, original text kept. |
| C5 stage rule | **Accepted** | One rule = the pipeline's: internal serial, else laboratory, else first test date (stage 1: tests from Sep-Oct 2021 to Aug 2022; stage 2: from Jan-Feb 2023; pipeline item 1), cross-checked with m_0/U_0 of the metadata where present; disagreement -> excluded and listed. TP_z10_01, TP_z15_01: resolved against the dataset paper's tables; if the condition stays ambiguous the cell is excluded from training and scoring and listed. Empty folder TP_z02_01__f47631268: re-fetched; excluded if still empty. OPEN-1 closed (fetcher is stage-aware). |
| C6 inclusion rules | **Accepted** | The pipeline QC flags and thresholds go into PD§3.3 as check-up-level rules, with the disclosure that they were fixed after 163 check-ups were parsed and fired zero times. The isolated-outlier rule depends on capacity: kept, with a sensitivity row that retains every check-up. Non-isothermal CU (pipeline item 7) added to E3. ISU/SNL: forecast set ends at the first point below 70 % for every arm; cells whose life ends inside the window are scored as forecast failures in a sensitivity row (same rule as Samsung PD§3.3(6)). |
| C7 provenance | **Accepted** | Run-record spec in the prereg: config.json, metrics.json, per-cell predictions, git commit, dirty-file list, split hash, raw-file manifest (path, size, sha256). P3 commit statement corrected (SNL 992b5b4, W6 86fca6f, W4 61bb730; code identical apart from audit lines). P0 run record written retroactively and labelled so. Samsung pipeline re-run on the complete download with manifest; Samsung splits copied to `runs/splits/` and hashed at freeze. |
| C8 disclosure | **Accepted, extended** | Disclosure sentence as GA wrote it. Extension: until the freeze, Samsung retention values stay in `data/processed/` (gitignored); nothing under `runs/` or any note shows retention by cell or condition; the window rule uses counts only; no plot of Samsung trajectories is made. The full parse after the download is a data step, not a look. |
| C9 second audit | **Accepted** | Gate auditor audits PREREG_v2 filled, against the checklist of section 7, before the freeze. |

Draft OPEN items: OPEN-1 closed (C5). OPEN-2 A7 in (1.3). OPEN-3 F fixed in PINN arms while A9 gets a larger space:
accepted as conservative for the claim; collocation placement (record end vs whole axis, P5 item 4) becomes a tuned
categorical in every PINN arm. OPEN-4 closed (D009, section 4). OPEN-5: H6 in, H1c out (1.1). OPEN-6: round synthetic
constants accepted (matching to Samsung needs label-derived scalars before the freeze, which C8 forbids); the J§6
departure is recorded here.

---

## 6. Physical validation analyses (secondary, descriptive; no test, no Holm, no claim word beyond "consistent / not consistent")

1. **Calendar temperature dependence.** Effective activation energy E(SOC) from the calendar KAN, with fold x seed
   envelope, compared with (a) the Arrhenius parameter of the dataset authors' own calendar fit on the same data
   (labelled "consistency with the semi-empirical fit", not independent validation), and (b) published calendar-ageing
   activation energies **only** for cells of the chemistry stated in the dataset paper, each with a Crossref-verified
   DOI and page/table location (citation-validator), and only where SOC, temperature range and check-up protocol are
   comparable. If no such value is verified, (b) is omitted and the text says so. Caveat that must be printed: storage
   at 10 C is all SIE and at 45 C all HM (PD§3.3(7)), so E(SOC) is lab-confounded; the storage lab composition at
   23 C is tabulated.
2. **SOC dependence above 80 % SOC.** The dataset paper reports non-monotonic stage-1 capacity behaviour in storage
   above 80 % SOC that its model does not capture (re-audit §1). Pre-stated descriptive check: the learned storage
   rate vs SOC at each storage temperature, with envelope, and whether it changes slope sign above 0.8; reported with
   the caveat that SOC > 0.8 exists in stage 1 only (stage and batch confounded). The S2 table already splits SOC <= 0.8.
3. **Arrhenius monotonicity** (PD§10 positive control P2, kept): calendar rate increases with temperature at every SOC
   inside the storage hull.
4. **Superposition check.** For each cycling cell, the share of its predicted fade attributed to the calendar term,
   and the number of cells where the calendar term alone exceeds the observed total fade at the last check-up (a
   physically impossible split), per arm A1, A2.
5. **Direction of cyclic stress effects.** Signs of the cyclic partial dependences compared with the signs of the
   exponents in the dataset authors' cycle model (consistency only), with envelopes.
Items 1-5 go to Fig. 5 / Fig. 6 and one appendix table; none enters the outcome table.

---

## 7. What must be true before the freeze, and the checklist

Hard preconditions (no freeze without them; only Shlok can waive one, in a ledger row):
1. **Zhang et al., JES 182, 125097 read in full** (Shlok saves the PDF; paper-reader note per CONTRACT §4; novelty
   auditor verdict). If it contains a neural calendar + cycle model with learned stress functions forecasting held-out
   conditions of this dataset: D005 re-opens, no freeze. If it supplies a comparator or a metric on this dataset: added
   in v2 before the freeze.
2. **Stroebl et al., JES 142, 119552 full text** read and A10's equations fixed (1.4); Hallinger et al. SSRN 7417281 read
   at least in its model and data sections (Cx§2.1).
3. **Full Samsung data on disk** (Shlok's download), all zips size- and checksum-verified, manifest written; pipeline
   re-run; ET/exCU members parsed so the Q0 rule (PD§3.3(2)) and the window counts can be fixed.
4. **Stage assignment complete for all 279 cells** under the C5 rule; exclusion list written.
5. **Throughput validated on a sample:** analytic EFC vs ZYK-logged EFC for at least 2 cycling cells per DoD class and
   per laboratory, at every check-up. Acceptance rule (fixed now): median absolute relative difference <= 5 % and no
   sampled cell above 10 % at its last check-up. Else logged ZYK throughput is used for every cycling cell (ZYK of all
   cycling cells parsed before the freeze).
6. Window rule (k_cyc, k_sto) and the schedule go/no-go (PD§5) evaluated from counts.
7. Section 4 verification passed or the fallback adopted; power re-reported.
8. Samsung training-fold timing run (C3) done; N fixed.
D005's date stands: if Samsung check-ups are not parsed by **07 Nov 09:00**, the ISU fallback applies (with the C8
"not blind" disclosure on the primary).

**Freeze checklist (gate auditor ticks each with a file pointer):**
- [ ] Preconditions 1-8 met, each with its file.
- [ ] PREREG_v2.md contains every edit of section 8; no "[a]", "[b]", "[c]", "pending" or OPEN marker left.
- [ ] Samsung splits copied to `runs/splits/`, hashes recorded; ISU/SNL split hashes unchanged.
- [ ] Grid files, code commit (clean tree), seeds, RNG seeds of the permutation test recorded.
- [ ] A10 parameter-recovery test and the 19 pipeline tests pass on the frozen commit.
- [ ] `margins.json` procedure (pp row) and log-scale margins written; test-fold guard line in every run script.
- [ ] Disclosure sentences (C8) in the prereg.
- [ ] Statistician signs sections 6-9 and 16; red team signs sections 1, 10, 11; gate auditor C9 pass.
- [ ] D011 row and any later rows in DECISIONS.md; Shlok told the likely outcome (3.1) and the told-on date recorded.

---

## 8. Edits for the experiment designer (PREREG_DRAFT.md v0.1 -> PREREG_v2.md)

1. Header: "v2", basis adds STATS_RULING.md, GA, Cx turn 3, D007-D011; "P3 used (descriptive only)"; remove markers as
   they close.
2. §1 claim: replace with the claim contract of 1.1; contrast (iii) = A10; data-only = key secondary; add SR§7 power
   paragraph and SR§6 abstract rules; add 3.1 "likely outcome" sentence.
3. §2 hypothesis table: rewrite per 1.1-1.2 (family {H1a, H1b, H6}; H1c gatekept; H4 Holm-2; X1 secondary; ISU/SNL rows).
4. §3.2: replace the stage rule by C5; close OPEN-1; list TP_z10_01, TP_z15_01, the empty folder and unassignable cells
   with the exclusion rule.
5. §3.3: add the pipeline QC flags and thresholds as rules with the post-parse disclosure; outlier-rule sensitivity row;
   non-isothermal CU note under item 7; C8 retention-blinding rule.
6. §3.4: ISU/SNL 70 % truncation and forecast-failure rows; fallback uses the hierarchical rule; "not blind" label.
7. §4: Test C renamed "held-out temperature-laboratory domain (35 C, INT)"; add the stage composition of its 13
   conditions; Test A marked exploratory.
8. §5: correct "9 and 16" to "8 and 15"; throughput validation rule of 7.5.
9. §7: arm table per 1.3 (A6 dropped, A8 synthetic only, A14 and Test A exploratory, A13 secondary, H1b pool {A3, A4,
   A5, A7}, A3 renamed "parametric", A7 "PiDDM-style"); A10 per 1.4 with sensitivity; collocation placement as a tuned
   categorical in every PINN arm; arms-by-test line per 1.3; P2 Partial rule of C3.
10. §9: replace 9.3-9.5 by SR§2 margins (pp row) and section 4 here (log scale, sign-flip AND BCa, verification,
    fallback); 9.6 H2 per SR§3 order A, C, B; 9.9 families per 1.1-1.2; 9.10 add lab-stratified bootstrap, by-lab/stage
    means, leave-one-lab-out, two-stage bootstrap, pp-scale row, Test C lab-indicator row, A10-as-published row.
11. §10: negative control arms A1, A9 (+R2).
12. §11: replace by the outcome table of 3.2 and the Test C table of section 2; delete the P3 slot text and replace with
    the descriptive P3 entry of C1.
13. New §11a: physical validation analyses of section 6 (secondary, descriptive).
14. §12 stop rule 5 cut order: A14, Test A, S3, sensitivity rows, A13 last; trials and seeds never cut.
15. §14: Fig. 3 box label "held-out temperature-laboratory domain"; Fig. 4 forest plot on the log-ratio scale with pp
    on a secondary axis; Fig. 5/6 carry section 6 items; Table 1 adds E/R_LOO, E/R_WARP (descriptive) and "replicate
    spread" wording everywhere (SR§9 edit 9).
16. §16: recompute the compute table for the essential arm set (7 PINN-type + 1 hard in Test B; Test C 5 arms; S2 4).
17. §17: replace by the preconditions and checklist of section 7; record OPEN-2..6 rulings of section 5.
18. §18: run-record spec of C7; change log row "v2 2026-11-05: D011 rulings".
19. Errata (C4) are appended to the RESULT.md files, not to the prereg.

---

## 9. What would re-open this decision

1. Zhang (JES 182, 125097) or Hallinger contains the combination (re-opens D005 itself).
2. The section 4 simulation fails both the adopted rule and the sign-test fallback (not expected: the sign test holds
   level by construction) -> statistician proposes, judge rules, before the freeze.
3. The Samsung timing run makes even the Partial plan exceed the CPU week -> re-cut arms in the stop-rule order.
4. Shlok rejects title 3 as an acceptable endpoint or asks to restore the data-only learners to the family (his call;
   the power cost of SR§7 is then stated in the ledger).
5. Any rule above changed after a Samsung test fold is scored: not allowed (new version, disclosed).
