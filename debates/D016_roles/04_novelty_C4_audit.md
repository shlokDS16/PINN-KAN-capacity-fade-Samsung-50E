# C4 novelty audit: Hallinger, Lucu A/B, Jia, and the FB-1 check (2026-11-06)

Auditor: novelty-auditor (checks only; no rescue suggestions). Inputs: `02_judge.md` sections 1 and 3, `03_novelty_recheck.md`, D018 judge section 6 and 7, PREREG_v4 17.1 (FB-1, FB-2) and 17.2 (C4, C8). Paper notes written in this pass: `notes/papers/hallinger_ssrn7417281.md`, `notes/papers/lucu2020_A_B_JES30.md`, `notes/papers/jia2024_TTE.md`. No Samsung data opened. No ledger name was given in the brief; no ledger rows added.

Reading tags: FT = full text of the article read from the PDF or clean capture (each note states which sections were read line by line and which were located and keyword-checked); the garbled `.md` conversions of Hallinger, Lucu B and Jia were not relied on, and the PDFs were re-extracted in reading order.

## 0. Claim under audit (falsifiable, restated)
With 8 of 40 cycling conditions and 2 check-ups per held-out cell, a PINN with a joint calendar-plus-cycle law (Arrhenius x KAN(SOC) storage term plus KAN stress map) forecasts held-out Samsung 50E cycling conditions with a lower median error than the best tuned data-driven learner; a matched ladder attributes the gain; learning curves over m and k are reported; a closed-form law extracted from the KAN predicts held-out conditions no worse than an equally simplified GAM law.
Four parts: (i) learning curves over cycling conditions m and check-ups k; (ii) matched ablation ladder; (iii) KAN-extracted closed-form law against GAM law on held-out conditions; (iv) the combination, physics-informed, on the Samsung 50E campaign.

## 1. Verdict

**Framing as a whole: INCREMENTAL, confidence 0.65.** Not TAKEN: no paper read has the conjunction, and no paper read has parts (ii) as a matched ladder, (iii), or (iv). But part (i) in its generic form (a nested learning curve of a learned forecaster over the number of ageing conditions, scored on held-out cells) was found in Lucu A and B, which the D016 recheck had not established.

| Part | Verdict | Conf. | Basis (this audit) |
|---|---|---|---|
| (i) learning curve over m (cycling conditions) and k (check-ups) | **INCREMENTAL, with the m-curve alone TAKEN in generic form** | 0.70 | Lucu B: 16 nested training cases over cycling conditions, held-out and "targeted validation" cells, GP; Lucu A the same for storage (7 cases). The k axis, physics-informed network, joint law, tuned data-driven comparators, repeated draws and intervals were not found in any of them |
| (ii) matched ablation ladder | **INCREMENTAL** | 0.65 | Jia: physics-guided against physics-free is across two datasets, not matched; Lucu: no ablation; Hallinger: no learned component. The matched ladder is not pre-empted |
| (iii) KAN closed-form law against equally simplified GAM law on held-out conditions | **NOVEL** | 0.60 | None of the four papers touches it (no KAN, no symbolic extraction, no GAM) |
| (iv) combination on Samsung 50E | **NOVEL (narrow)** | 0.60 | Hallinger does not use the 50E data; Lucu and Jia use other cells; Zhang (ECM-PINN) is a different task |

**Single paper a JES reviewer is most likely to cite against us: Lucu et al., J. Energy Storage 30, 101410 (2020), Part B, with Part A.** Same journal, same stated aim ("minimal number of laboratory tests"), nested condition-count learning curve with held-out cells, cycling. This is now stronger than the recheck recorded. For the model class the single paper remains PiDDM (D010).

## 2. Difference matrix (S same, P partial, D different, relative to our claim)

| # | Work | Question | Mechanism | Method | Evidence | Scale | Result |
|---|---|---|---|---|---|---|---|
| 1 | Lucu B, JES 30, 101410 (FT, targeted) | **S** (learning curve over cycling conditions, minimal tests) | P (five stress factors, no law, cycling only) | D (GP, nonparametric) | **S** (held-out cells at unobserved levels; designed static campaign) | P (124 cells, 1 cell type) | 26 cells at 9 conditions: 1.04 % MAE_Q on 122 cells |
| 2 | Lucu A, JES 30, 101409 (FT, targeted) | **S** (same, storage) | P (T, SOC; calendar only) | D (GP) | **S** | P (32 cells) | 18 cells at 6 conditions: 0.53 % MAE_Q on 30 cells |
| 3 | Jia et al., IEEE TTE 10(1) (FT, targeted) | P (cells needed, physics against none, but across datasets) | P (OCV-derived degradation-mode features, early-cycle lifetime, cycling only) | P (physics-guided decision trees) | D (random cell splits, accelerated aging, 14 NCM cells; LFP for the no-physics arm) | D | KP MAPE 4.18 % (NCM, 11 training cells per fold); LFP 100 cells: trajectory 2.68 % |
| 4 | Hallinger et al., SSRN 7417281 (FT, main body) | P (4 of 26 conditions with withheld-condition RMSE; one comparison, not a curve) | P (mechanistic calendar law, no cycling) | D (parametric least squares, FIM-based OED) | D (retrospective; NCA 18650 and LFP 18650; **not** the 50E data) | D | 0.59 % against 0.43 % RMSE (SOH_LI, MUR); LIW 1.60 % against 1.27 % |
| 5 | Stroebl et al., JES 142, 119552 (FT-partial per D018 6) | P (experiments against parameter variance) | S (calendar+cycle semi-empirical, same data) | D | S (same 279 cells) | S | calendar 28 % lower parameter SD; cycle model inadequate |
| 6 | Zhang et al., JES 182, 125097 (FT, `zhang2026` note and re-check below) | D | D (1RC ECM) | P (PINN) | P (same data, cell split) | P | SOH MAE 0.451 % test |
| 7 | Guo et al., arXiv 2607.16864 | P | D | P | P | D | as in the recheck (not re-read here) |
| 8 | Navidi 2024, Cui 2025, de Oliveira 2021 | as in the recheck | | | | | not re-read here; abstract level |

## 3. Conditions (a) to (d)

| Condition | Status | Evidence |
|---|---|---|
| (a) Hallinger full text read; shown not to contain a learning curve of a learned forecaster; Stroebl half | **CLOSED** (Hallinger now; Stroebl at FT-partial by D018 6) | Hallinger: no learned model, calendar only, one partition, "four of 26" is a single contrast, data are MUR and LIW, not the 50E. Not the stop-rule-12 case |
| (b) Lucu A/B full text read; no physics-informed arm | **CLOSED as worded, and it opens something else** | No physics-informed, semi-empirical or neural arm in either part. **But** both papers contain a learning curve of a learned forecaster over the number of ageing conditions on held-out cells. That is the D018 section 7 fifth bullet ("learning curve of a learned or physics-informed forecaster over the number of ageing conditions on held-out conditions ... re-opens the novelty scope of section 6"): **triggered for Lucu A/B** (the same-dataset stop rule 12 is not). The judge must rule on the re-opened scope; section 5 below gives the auditor's reading of what the scope can still contain |
| (c) Jia full text read; 14-against-100 is lifetime-from-early-cycles, not condition extrapolation | **CLOSED** | Task: knee point and EOL from the first 50 cycles; NCM four-fold by cell (11 training, 3 test per fold, Table II) with random cell choice; the 100-cell figure is a different dataset (LFP, 123 cells, no physics). In the passages read the body gives 2.68 % at 100 LFP cells, not 2.02 % |
| (d) arXiv/OpenReview repeat within 7 days of submission, ICLR 2027 enumeration | **OPEN** (by design) | A preliminary search on 2026-11-06 (section 6) found nothing new; it does not close (d) |

C4 therefore stays **partly**: (a), (c) closed, (b) closed as worded with a triggered re-open bullet, (d) open.

## 4. FB-1 (Zhang JES 182, 125097) and FB-2 (Hallinger part)

**FB-1: CONFIRMED NOT TRIGGERED** (the proposer's verdict stands; validated by the auditor, not copied). Checked on `refs/fulltext/ft_zhang2026_JES182_125097.txt` (848 lines): whole-file counts match the note: "calendar" 1 (line 61, a sentence saying the full dataset has calendar experiments; line 62 selects 104 cycle-aged cells), "stress" 0, "Arrhenius" 0, "DoD" 0, "C-rate" 0, "forecast" 0, "held-out" 0, "learning curve" 0, "data-efficien" 0, "seed" 0, "ablation" 0, "baseline" 0, "Kolmogorov" 1 (only inside the title of reference [16], SOH-KLSTM, line 684); "KAN" 2 case-insensitive (the surname "Kang" in two reference author lists, lines 665 and 763; no KAN model). Task and split re-read at lines 46-62, 147-149, 391 (89 train / 15 test cells, cell-level, "unseen cells"): joint SOH estimation and ECM parameter inversion from HPPC pulse sequences at the time being labelled, not a fade forecast; no learning curve; no ageing law. The three re-open elements (neural calendar+cycle model with learned stress functions forecasting held-out conditions; data-efficiency study of learned laws; KAN) are all absent. Two leads not needed for the verdict: the introduction (lines 32-33) cites [25]-[27], including Wen et al. on "semi-empirical aging models with physics-constrained SOH prediction", which were not read; they are not Samsung-data claims in the text, but a reviewer could ask about them. Status: **FB-1 can be marked met on this confirmation.**

**FB-2 Hallinger part: CLOSED.** Model and data sections read in full. The data are Murata/Sony US18650VTC5A (MUR) and LithiumWerks APR18650M1B (LIW); the 50E dataset is named once in the introduction as a large public campaign ([4], 279 cells) and not analysed. The model is the Karger et al. mechanistic LLI/LAM calendar law (electrode-potential terms), a different function from A10 (Stroebl JES 142 Eq. 17, 18, 21 and SI S.1-S.3; `code/pinnkan/semi.py`); nothing in the preprint concerns A10's calendar or cycle term, and the preprint cites Stroebl JES 142 only as an OED application. No claim of ours is pre-empted and no part of A10 changes. (The Stroebl half of FB-2 was already met: `semi.A10_FORM["verified"]` is True.) FB-2 as a whole: **met** on this audit, subject to the gate auditor's tick.

## 5. Framing sentences

Basis: D018 section 6 (abstract may say only "we found no earlier study that ..."; "to our knowledge" only in the introduction contribution list; "first" banned), amended by section 3 above. All allowed sentences remain subject to condition (d) and to the judge's ruling on the re-opened scope; no sentence below may be used before then.

### 5.1 Allowed
**Abstract** (only after (d) and the judge's ruling; no "first"):
- "We found no earlier study that combines a learning curve over cycling conditions and check-ups, a physics-informed network with a joint calendar-and-cycle law, a matched ablation of the physics law and of the Kolmogorov-Arnold map, and a held-out test of a closed-form law extracted from that network, on a designed storage-and-cycling campaign."
- The abstract's context sentence may say that earlier studies quantified how many ageing tests a data-driven or mechanistic model needs (Lucu et al. 2020 for Gaussian-process models; Hallinger et al. 2026 for a mechanistic calendar model); it must not present the question itself as open.

**Introduction contribution list** ("to our knowledge" allowed here, after (d)):
1. "Lucu et al. [A, B] traced held-out error against the number of storage and cycling conditions with Gaussian processes, calendar and cycling in separate models and without a physics-informed model; we extend this with check-ups per held-out cell, a joint calendar-plus-cycle physics-informed law, tuned data-driven comparators, repeated nested subsets and simultaneous intervals." (Each named difference is verified in the notes.)
2. "Jia et al. [..] reported that a physics-guided tree model needed 14 cells against about 100 for a physics-free model, comparing two datasets in an early-cycle lifetime task; our ladder removes the physics law from the same network on the same cells." (Use "about 100 without physics" only with the dataset difference stated.)
3. "To our knowledge, no earlier study tests a closed-form law extracted from a Kolmogorov-Arnold network against an equally simplified additive law on held-out ageing conditions." (Element rated NOVEL, 0.60; absence of search hits is weak evidence.)
4. The conjunction sentence of 5.1 (abstract) in "to our knowledge" form.

**Related work:** Hallinger et al. (2026 preprint) as the calendar-ageing OED study that reduces experiments for a mechanistic law, mark as preprint with SSRN id; Zhang et al. JES 182 as the same-dataset ECM-PINN use (sentence in `notes/papers/zhang2026_JES182_125097.md`).

### 5.2 Banned (each with a verified counterexample)
- "first learning curve over the number of ageing (or cycling) conditions", "first data-efficiency study of battery ageing", "first to quantify the minimal number of tests for a cycling ageing model" (Lucu B; Lucu A for storage; Hallinger for calendar; Stroebl 2026).
- "first study to test a model on held-out stress conditions with few training conditions" (Lucu A/B validation cells at unobserved levels).
- "first physics-informed (or physics-guided) model shown to need fewer cells" and "physics reduces the cells needed" as an established matched result (Jia states 14 against 100 across datasets).
- "first to reduce the experiments needed to parameterise a calendar-ageing law" (Hallinger, Stroebl).
- "first PINN on the Samsung 50E / Stroebl data" (Zhang JES 182); "no other study uses this dataset for a neural model" (same).
- "first physics-informed or learned-parameter ageing law", "first KAN with Arrhenius-type terms", "first symbolic or closed-form degradation law", "first early-data physics-constrained forecast" (D018/recheck list: PiDDM, Koenig and Deng, Gasper, Cui, Schofer, Guo).
- Any use of "first", "novel framework", "unprecedented", or "outperforms" below tier S in the abstract or introduction (D016 section 4.3).
- Calling Hallinger "the same data", or describing A10's calendar term as the Hallinger/Karger model.
- Describing the m-grid as "a new type of study" or "learning curves" as the contribution by themselves.

### 5.3 Wording consequences for D018 section 6 (record only)
D018 section 6's contribution item 1 ("extension of Lucu A/B (GP, number of cells, no law)") should read "number of conditions", because Lucu A/B vary the number of conditions; item 2 ("extension of Jia and Navidi") must name Jia's cross-dataset comparison. Both are corrections of fact, not of design.

## 6. Last-90-days check (preliminary, does not close (d))
Queries run 2026-11-06 (WebSearch, standard): (1) "physics-informed neural network battery capacity fade few ageing conditions learning curve held-out stress conditions Samsung INR21700-50E 2026"; (2) "Kolmogorov-Arnold network calendar and cycle ageing law symbolic extraction lithium-ion capacity fade arXiv 2026"; (3) "Hallinger Kirst Singer Bohlen calendar aging model optimal experimental design cyclic aging follow-up 2026". Results: arXiv 2601.00862 (foundation-model forecasting; already unverified in the recheck), Navidi et al. eTransportation 2025, Wang et al. Nat. Commun. 2024 (PINN4SOH), arXiv 2501.14573, arXiv 2604.00400 (KAN functional relation for SOH from temperature; already in the recheck), Cui 2025 JES-Soc. No Samsung 50E result, no KAN symbolic calendar-cycle law, no Hallinger follow-up. arXiv listing pages and OpenReview (ICLR 2027, NeurIPS 2026) were **not** enumerated.

## 7. Residual risk
- Depth: Lucu B, Jia and Hallinger were read in the passages relevant to the claim, not line by line; Lucu A/B kernel and GP-theory sections and Jia's mechanism sections were keyword-checked only. A learned-law or physics-informed arm hidden in a section not read line by line is unlikely (keyword checks negative) but not excluded.
- Figures and appendix tables were not inspected; the Lucu cases' exact train/validation membership (Table 3 of Part B, Table 5 of Part A) was read only through the text.
- Rows 7 and 8 of the matrix are carried from the recheck at abstract level.
- Searches are weak evidence of absence; ICLR 2027 and NeurIPS 2026 submissions cannot be enumerated, so a concurrent submission is not excluded; Hallinger's stated future work (combined calendar and cyclic models) and the Stroebl/Palm group's continued work on the same data make a same-dataset follow-up the most plausible scoop during the freeze window.
- The 0.60 to 0.70 confidences are my judgement of coverage, not measured quantities.

## 8. What changed relative to `03_novelty_recheck.md`
- Lucu A/B: from "number of cells, GP, S/P" to a nested condition-count learning curve with held-out cells (m-axis precedent confirmed); (i) stays INCREMENTAL, now with the m-curve alone TAKEN.
- Jia: "14 against at least 100" is cross-dataset and early-cycle; not condition extrapolation (condition (c) closed).
- Hallinger: not the 50E data, calendar only, no learned model (condition (a) and FB-2 Hallinger part closed).
- FB-1 confirmed.
- D018 section 7 fifth bullet triggered by Lucu A/B: judge ruling needed on the scope; the allowed sentence of the recheck is replaced by 5.1.
