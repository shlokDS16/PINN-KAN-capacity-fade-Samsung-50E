# KA-CRNN (Koenig and Deng, J. Energy Storage 158, 121853, 2026): exemplar dissection

Reading depth: full text of the JES version (saved extract `refs/fulltext/ft_koenig2026_KACRNN_JES158_121853.txt`: Sec 1-4, Appendices A-D, Tables 1-2, references) + figures 1, 2, 3, 4 and B.1 viewed as images (`refs/figs/kacrnn/gr1..gr4, gr6`; gr5 = Fig A.1, gr7-gr8 = B.2-B.3, gr9-gr11 = C.1-C.3 downloaded but NOT opened: judged from captions). The abstract text is not in the saved extract (it repeats the Highlights). Supplementary CSV files (S1-S6) not read. Extends `notes/exemplars/kacrnn_2026.md` and `notes/papers/priorart_kacrnn.md` (which used the arXiv v2 text); numbers and figure numbering here are those of the JES version. Setting reminder: thermal-abuse kinetics from DSC, not ageing. "Paper reports" = E2 for the report only.

## (A) Contribution as stated; list pattern
- Gap (Sec 1, para 2): CRNN kinetic models treat Arrhenius parameters as fixed scalars, so they cannot represent dependence on SOC; most kinetic studies are at 100 % SOC (para 3); Kissinger-type fits at a few SOCs give no continuous model (para 4); a "critical SOC" jump in heat release is known from DSC (para 5).
- Construction: reaction network from literature review (layered -> spinel -> rock salt with O2 release, plus O2-limited electrolyte oxidation), Arrhenius plus mass action, and 11 of the parameters per cathode (reaction orders n1, n2; ln A1, ln A2; Ea1, Ea2; temperature exponents b1, b2; enthalpies Delta H1, Delta H2; oxygen stoichiometry nu) replaced by univariate Chebyshev KAN activations of SOC (N = 10); 5 electrolyte-oxidation parameters are scalars shared by the three cathodes (Tab 1).
- NO numbered contribution list. The novelty is stated in running prose at the end of Sec 1 and in Sec 4 (continuous response of kinetic parameters to SOC, plus a shared SOC-invariant electrolyte reaction). A numbered list is a pattern we should keep (PIKAN, PGKAN, PINEAPPLE use one); KA-CRNN's strength is the opposite: a long mechanistic motivation that makes the model form look inevitable.
- Highlights: 5 bullets, no numbers (learn continuous SOC-dependent kinetics; physics-encoded pathway gives interpretable parameters; fits DSC across SOCs for several cathodes; reveals SOC-linked oxygen release and phase transitions; extensible to runaway prediction).
- Claim strength: "fit well" and "interpretable" are asserted without a metric; the only test is one withheld SOC per cathode.

## (B) Structure
| Section | Content | Approx. words |
|---|---|---|
| 1 Introduction | thermal runaway, DSC, Kissinger vs CRNN, SOC problem, critical SOC, KA-CRNN gap | 860 |
| 2.1 Mechanism review | cathode oxygen evolution vs lithiation; electrolyte oxidation; four numbered literature conclusions; proposed model form (Eq 5-7, three reactions) | 1,700 |
| 2.2 Model | Arrhenius/mass action (Eq 8-12), KAN encoding (Eq 13-15), Chebyshev N = 10, 121 weights per cathode | 1,140 |
| 2.3 Training | data (3 cathodes x 9 SOC), held-out SOC, loss with penalties (Eq 16-19), Tab 1, optimiser | 1,190 |
| 3 Results | 3.1 DSC predictions (Fig 3, Tab 2), 3.2 parameter visualisations (Fig 4), 3.3 outlook and limitations | 2,150 |
| 4 Conclusions | two paragraphs | 330 |
| Appendices A-D | O2 rates, all activations, all reconstructions, supplementary CSVs | 680 |
About 8,100 words in total (section splits counted from line ranges of the saved extract); 4 main figures + 7 appendix figures (A.1, B.1-B.3, C.1-C.3); 2 tables; equations numbered to (19); 48 references. Observations: a mechanism-first article (about 60 % of the words, Sec 1-2, come before the first result); only 2 main tables, no results table; the appendices carry completeness (all activations, all reconstructions). Supplement: three pairs of CSV files (continuous parameter forms and discretised lookup tables), 2 KB and 53 KB each. No code link in the saved text (Julia packages DifferentialEquations and ForwardDiff are named).

## (C) Every figure
| Fig | Form and panels | Encodings | Claim | Quality | What we would do better |
|---|---|---|---|---|---|
| 1 | 5 panels A-E in one schematic: (A) three example activations nu, Ea,1, Delta H1 as curves vs SOC; (B) scalar CRNN parameters with example values; (C) cartoon of heat-release curves for three SOCs (0.95, 0.9, 0.5) with intermediates in a green gradient; (D) hybrid KA-CRNN/CRNN network, reactions R1, R2 green (KAN) and R3 grey (scalar); (E) flowchart (current SOC -> sample activations -> scalar parameters -> network -> Neural ODE -> heat release -> loss/autodiff), with cross-references to A-D | green = SOC-dependent, grey = fixed; gradient = SOC order | what is new vs a CRNN, and how it trains | the colour code (green vs grey) is the clearest conceptual encoding of the three papers; the numbers in (B) (1.4e5 J/mol, 140 J/g) are placeholders: they do not match Tab 2 (5.37e5 J/mol, 1779.39 J/g) and are not labelled as such; (C) is a cartoon, not data | keep the colour code (ours: KAN stress functions vs fixed constants) and the cross-referenced caption; label every illustrative value as illustrative |
| 2 | 3 x 9 small multiples of the training data (HRR in W/g vs T in K), rows = NM, NMA, NCA, columns = SOC 58.3 to 87.4 %; italic mAh/g label; held-out column (200/204/203 mAh/g) in red italics; y-axis rescaled from column 7 (3 to 15 W/g); marker grey shade light to dark with SOC | grey scale + red | the whole experimental design in one figure | the design is readable at a glance; the axis break in y between columns 6 and 7 is stated only in the caption | our design map (storage T x SOC, cycling T x DoD x C-rate) in the same row/column grid, with held-out conditions in red |
| 3 | (A) 3 x 3 grid: rows cathodes, columns lowest / held-out / highest SOC; markers = data, bold coloured line = model total, grey solid/dashed/dotted = R1, R2, R3 components, white legend in each panel, held-out label in red; (B) overlay of all 9 SOCs per cathode, gradient light to dark; (C) nu vs mAh, one line style per cathode | colour = cathode (blue, orange, green), gradient arrow "Inc. SOC" | model reconstructs unseen SOC, produces critical-SOC jump in nu | good; but at the highest SOC for NMA and NCA the markers reach about 13-14 W/g while the model line peaks at about 9 W/g (visible in (A), third column), acknowledged only in the text of Sec 3.3; x label of (C) says "mAh" where the data are per gram | same forecast-overlay grammar plus a seed/fold band and a printed error per panel; show the worst held-out case |
| 4 | 2 x 2 line panels: ln A1, ln A2, Ea,1, Ea,2 vs SOC for the three cathodes | blue, orange, green lines; boxed legend | learned stress functions; second reaction shifts at the critical SOC | readable; panel letters collide with the top y-axis tick ("(A)300"); axis runs to 250 mAh though the data stop at 240; no envelope; panels B and D have the same shape (see F) | add fold/seed envelope, GAM overlay, a rug of training conditions, restrict axes to the data range |
| A.1 | oxygen production and consumption rates for all cathodes and SOCs (caption only) | solid = production (R2), dashed = consumption (R3) | R2 controls R3 timing | not viewed | |
| B.1-B.3 | per cathode, 11 panels (all KAN-parameterised quantities): black = summed activation, green = each scaled Chebyshev term, grey dashed verticals = training SOCs, blue dash-dot = test SOC | black/green/grey/blue | full set of learned functions; decomposition into basis terms | B.1 viewed: the basis terms are large and cancel (nu panel: individual terms reach about +/-2.8 around a summed curve that stays 0.3-1.5), i.e. poorly conditioned coefficients; Delta H1 has a hump (about 500 near 212 mAh) then drops to about 170 at 238 | the dashed rug of training conditions is worth copying; show basis terms in the appendix only |
| C.1-C.3 | all train/test DSC reconstructions per cathode (A), overlay (B), nu activation (C) (caption only) | | completeness | not viewed | |
Palette: colour-blind-unsafe orange/green/blue pastel set, but with line-style redundancy only in Fig 3C.

## (D) Every table
| Tab | Content | What it proves |
|---|---|---|
| 1 | two-row classification: "cathode-specific KAN activation, function of SOC" = n1, n2, A1, A2, Ea,1, Ea,2, b1, b2, Delta H1, Delta H2, nu (11); "universal scalars, SOC- and cathode-invariant" = n3, A3, Ea,3, b3, Delta H3 (5) | which quantities are functions and which are constants; the cleanest parameter-roles table of the three papers |
| 2 | learned electrolyte-oxidation scalars: ln A3 = 132.45, Ea,3 = 5.37e5 J/mol, b3 = -0.069, Delta H3 = 1779.39 J/g, n3 = 3.250 | the shared law; authors call the large A and Ea "in accordance with expectations" for stiff data |
No accuracy table, no baseline table, no table of errors. Layout is minimal (text-like tables).

## (E) Evaluation
- Data: DSC curves reproduced from the authors' ref [18] (cathode powder + LP57 electrolyte, 2 C/min, Netzsch STA 449): 3 cathodes x 9 SOCs (lithium removal 87.4 % down to 58.3 %, steps of about 3.6 %), one curve per condition.
- Split: the 5th of 9 SOCs withheld per cathode as "testing data" (Sec 2.3): one interpolation point per cathode, 3 test curves in total, 8 training curves per cathode.
- Baselines: none (no scalar CRNN, no Kissinger, no interpolation of per-SOC fits, no MLP). Metrics: none numerical; fit judged by overlay (Fig 3A, C.1-C.3). Text verdicts: test fit "strong" for NM and NMA; for NCA "not quite as accurate" (Sec 3.1); highest-SOC peaks not fully reconstructed (Sec 3.3).
- Statistics: none (no seeds, no repeats, no CI, no test).
- Tuning: N = 10 "found to be a high-performing choice" and "experimentally selected"; penalty weights fixed by hand (Eq 17-19); whether the held-out SOC influenced these choices is not said (Sec 2.2, 2.3).
- Loss: described as an augmented MSE (Sec 2.2, 2.3) but Eq 16 is written with absolute values (MAE); the symbol L_max uses 0.05 n^4 + b^3 etc., and the form is justified only as "knowledge-based guardrails".
- Capacity of the model vs data: 121 KAN weights per cathode for 11 functions, from 8 curves (each with tens of points per Fig 2); the authors say N = 10 is "similar to the nine SOC samples".

## (F) The "interpretable law" claim and its evidence
- It is not symbolic regression. Each parameter is a Chebyshev series; "interpretability" = the learned curve is read off directly "with zero postprocessing" (Sec 3.1). The "law" is a set of curves (Fig 3C, 4, B.1-B.3) and numbers in lookup tables (supplement).
- Evidence offered: critical-SOC jump in nu at 210-230 mAh/g for all three cathodes (Fig 3C), shifts of ln A2 and Ea,2 before each cathode's critical SOC (Fig 4), NMA critical SOC higher than NM and NCA, matching the DSC peaks and literature on oxygen release.
- Weaknesses of that evidence:
  1. Shape imposed by a penalty: nu and Delta H2 are "slightly underconstrained" (Sec 2.3), so a monotone-increasing penalty (Eq 17, weight 100 on nu) is applied. The jump location is data-driven, but that nu rises with SOC is partly built in; no ablation without the penalty.
  2. Non-identifiability: lnA2 and Ea,2 have almost the same shape (Fig 4B, 4D) and reach about 270 (ln A) and about 1.0e6 J/mol (Ea,2) for NCA, values far above what a bulk reaction normally shows (values read from the figure; my domain-knowledge judgement, not tested here). Both come from a single heating rate (2 C/min), and a prefactor and an activation energy cannot be separated from one heating rate (kinetic compensation; standard in DSC kinetics, flagged here as a reviewer argument, not a result of this audit). The paper reads the joint rise as chemistry.
  3. Oscillation between data points: the degree-10 series produces humps in ln A1, n1 and Delta H1 (Fig 4A, C, B.1) that are not discussed; Appendix B admits Delta H1 falls toward the critical SOC, "counterintuitive", and attributes it to the data (R1 peaks are 33 % higher at 210 than at 220 mAh/g for NM, 21 % for NCA at 213 vs 224).
  4. No stability: no seeds, no refit with another SOC held out, no comparison with a spline or polynomial parameterisation of the same 11 functions (a univariate Chebyshev series per parameter is an additive/GAM-type component by construction).
  5. Single-input functions: SOC is the only "stress"; the authors themselves note voltage or dq/dV could be the better variable (Sec 2.1.2).
  6. "Assumption-free" (Sec 2.2) coexists with a literature-fixed three-reaction network, a shared R3 across cathodes, penalties L_mono, L_min, L_max.
- Strength: the mechanistic story is internally consistent (Fig A.1 shows R2 production shaping R3 consumption); honest admission of ill-conditioning where data do not constrain parameters (Sec 2.3, Appendix B).

## (G) Limitations and negative results
No Limitations section; they appear in Sec 2.1.2 (SOC vs voltage), Sec 3.3 (highest-SOC peaks not fully reconstructed; R3 cannot be split per cathode without breaking the mechanism; DSC plus TGA/mass spectrometry would help), Sec 3.1 (NCA test less accurate), Appendix B (Delta H1 anomaly). The outlook proposes a Bayesian KA-CRNN for uncertainty (Sec 3.3) i.e. they know there is none.

## (H) Data and code availability
Data: DSC curves are reproduced from the authors' ref [18], not newly deposited; model parameters in supplementary CSVs (continuous and lookup forms); no repository link in the saved text; solver stack named (Julia, DifferentialEquations, ForwardDiff, Adam, lr 5e-4). A preprint exists (arXiv 2512.15628; per earlier note).

## (I) What a hostile reviewer would attack
1. One interpolated test point per cathode, no number, no baseline: "good fit" is not evidence of predictive value; a per-SOC scalar fit with linear interpolation of parameters would probably match.
2. 121 weights per cathode vs 8 curves; the penalties define the answer; no ablation of the penalties.
3. Compensation between ln A and Ea; physically extreme values; single heating rate.
4. Loss definition inconsistent (MSE vs absolute); degree N chosen "experimentally" possibly with the test point.
5. Unexplained oscillations and the Delta H1 anomaly; higher-SOC peak heights underestimated.
6. Interpretability is asserted by plotting activations; no stability, no uncertainty.
7. Scope: abuse kinetics, not ageing; units (mAh vs mAh/g).

## (J) Lessons for our paper
1. [TEXT] Open the method with a mechanism-literature subsection that ends in numbered conclusions leading to the model form (their Sec 2.1.2); ours: calendar (SEI growth, T and SOC) and cycling (C-rate, DoD) mechanisms leading to the form of a(SOC), E(T) and cycle terms; keep it to about 1.5 pages.
2. [FIG] Reuse the green (stress-dependent, learned) vs grey (fixed) colour code in the schematic, panel cross-references in the caption, and label every illustrative number as illustrative (their Fig 1B values are unlabelled placeholders).
3. [FIG] Use their Fig 2 grid for our design: rows by temperature (held-out row marked), columns by SOC or C-rate, held-out cells in red italics.
4. [FIG] Fig 3 grammar for forecasts (markers = data, bold line = model, grey components, red label for held-out, gradient arrow for the ordered stress) but add a seed or fold band and a printed per-condition error; show the worst held-out condition too (their highest-SOC underestimation is only in the text).
5. [FIG] Fig 4 grammar for stress functions, with seed/fold envelope, GAM overlay and a rug of training conditions (their dashed verticals in B.1); keep axes inside the data range.
6. [TAB] Their Tab 1 (which parameter is a function of which stress, which is a shared constant) is worth copying as our Table of model terms; add the number of parameters per term.
7. [ANALYSIS-EXPLORATORY] Test identifiability before interpreting: recover a known law from simulated data, report the correlation between the fitted prefactor and activation-energy functions, and show profile likelihood; this addresses their unacknowledged compensation problem.
8. [ANALYSIS-EXPLORATORY] Ablate every soft physics penalty (monotone, bounds): show the learned stress function with and without; if the interpretation depends on the penalty, state it.
9. [TAB] Provide the numbers they omit: held-out RMSE per condition with CIs, paired comparison against a no-KAN scalar-parameter baseline and a spline/GAM parameterisation, and the number of held-out units.
10. [TEXT] Release parameter lookup tables (as they do) AND code and per-condition predictions; write an explicit Limitations subsection; keep loss definitions identical across text and equations.
