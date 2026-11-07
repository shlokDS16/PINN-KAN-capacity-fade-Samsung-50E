# Blueprint v2: what JES rewards, where its strongest papers in our niche are weak, and the display-item plan (2026-11-06)

Author: senior synthesis author (exemplar study). Supersedes `BLUEPRINT.md` (2026-11-04, built from three arXiv texts and captions) for
framing, figures and gaps; v1 is kept unchanged. Nothing here is a result: our outcome is unknown, and every sentence below that
mentions our paper says what the design tests, never what it found.

**Sources and reading depth.** Eight deep notes in `notes/exemplars/deep/` (all full-text readings, figure images viewed except
where a note says otherwise): Stroebl et al. JES 142, 119552 (2026) [STR]; Lucu et al. JES 30, 101409 [LA] and 101410 [LB] (2020);
Richardson et al. JES 23, 320 (2019; arXiv v1 text, VoR figures) [RIC]; Guo et al. JES 56, 105992 (2022, review) [GUO]; PIKAN, Liu
et al. JES 153, 120860 (2026) [PIK]; PGKAN, Zhao et al. JES 182, 124768 (2026) [PGK]; KA-CRNN, Koenig and Deng JES 158, 121853 (2026)
[KAC]; the three batch summaries; `JES_TOP_LIST.md` (Crossref metadata, E1 only); `BLUEPRINT.md`, `FIGURE_FORMS.md` (older rows,
partly caption-judged). Design facts are from `runs/prereg/PREREG_v4.md` sections 1, 2 and 14 (and, by grep, 4, 5, 7, 9, 11, 11a),
`debates/D-figures.md`, `code/figures/README.md`, `paper/draft/01_introduction.md`. The JES author guide is
`notes/JES_guide_for_authors_2026-11-04.md`.

**Binding constraints this file respects.** The preregistration is about to be frozen: nothing here changes a test, arm, margin or
the closed outcome table (section 11). Proposals are figures, tables, wording and clearly labelled exploratory or descriptive
analyses. Anything that would need a preregistered analysis is tagged [DESIGN-ISSUE-FOR-LEAD] and described, not resolved.
Retired topics stay retired: no coverage or calibration claim, no comparison of accuracy across split types (no Test A vs Test B
ratio, no Test B vs Test C ratio), and leakage-free condition-level evaluation is described as the task, never as a contribution
(`research/CONTRACT.md` section 1; PREREG_v4 section 4).

**Pending exemplars.** Nine paywalled papers (end of `refs/PAYWALLED_FOR_SHLOK.md`: Schuster 2015, Naumann 2018, Keil 2016, Olmos
2021, Najera 2023, Zhang 2026 TS-PINN, Li 2024 ECM-EIS, Wang 2024 open benchmark, Liu 2025 TL-LSTM) are unread. Each place where one
of them could change a conclusion is marked **[PENDING: name]**.

---

## (a) What JES rewards, with evidence

### a1. Citation drivers (Crossref counts, 2026-11; inference marked)

| Paper | Crossref cites | What plausibly drives them | Evidence |
|---|---|---|---|
| Richardson 2019 | 220 | a named, reusable unit ("load pattern", "transition model"); public NASA data; one excellent held-out-trajectory figure (13 panels, failures visible) | [RIC] F1, F4, C Fig 6; the link from naming to citations is the note's inference |
| Guo 2022 (review) | 120 | a coined label ("grey box") and a two-level taxonomy with one flowchart per leaf | [GUO] F1-F2 |
| Lucu 2020 A / B | 41 / 44 | a data-efficiency headline ("trained on N cells, error X") and a learning-curve figure | [LA] B abstract; [LB] B abstract |
| Stroebl 2026, PIKAN, PGKAN, KA-CRNN | 0-3 | too new to say | `JES_TOP_LIST.md` L2/L3 |

The best-cited physics-informed ageing papers in JES are modest (largest about 40 Crossref citations; `JES_TOP_LIST.md` L2 note);
citation leaders are data-driven SOH papers and reviews. Reading for us (inference): a paper in this niche gains citations through
(i) a short name for the task or unit that later papers can reuse, (ii) public data and released code, (iii) one figure that other
authors reproduce in talks. Our candidates: the term "held-out cycling condition" used identically in the abstract, highlights,
captions and tables, and the (m, k) learning-curve figure. **[PENDING: Zhang 2026 TS-PINN, Wang 2024]** both are top of their lists
by citations per year; reading them may show other drivers (benchmark release, code library).

### a2. Structure and size

| Paper | Body words (approx.) | Main display items | Appendix items | References | Limitations section |
|---|---|---|---|---|---|
| Stroebl 2026 | 6,500 | 9 (8 fig + 1 tab) | 7 | at least 46 | no section; scope sentence in Sect. 1, failure subsection, contribution bullet 5 |
| Lucu A | 10,000 | 13 (8 + 5) | 3 | 53 | Sect. 8 "Discussion, limitations, further work" |
| Lucu B | 9,000 | 13 (10 + 3) | 5 | 38 | Sect. 8 (same title) |
| Richardson 2019 | 6,400 | 10 (6 + 4) | 0 | 34 (VoR) | in Conclusions |
| PIKAN | 10,000 | 18 (10 + 8) | supplement | 45 | none |
| PGKAN | 8,700 | 20 (11 + 9) | supplement | 50 | Sect. 6, about 180 words |
| KA-CRNN | 8,100 | 6 (4 + 2) | 7 | 48 | none (scattered) |

Sources: the (B) sections of each note. The 2026 guide asks "ideally" at most 6,000 words and 8-10 figures and/or tables for a
full-length article. Accepted papers exceed both (PIKAN, PGKAN, Lucu), so the guide is a target, not a filter; Stroebl is the length
model and sits close to it. **Plan for us:** body 6,000-7,000 words; 8 figures + 2 tables in the main text (PREREG_v4 section 14),
diagnostics, hyperparameters, sensitivity rows, subset compositions and the decision log in appendices (Stroebl appendices A-G hold
5 figures and 2 tables; KA-CRNN puts every activation and reconstruction in appendices); 45-55 references.

Results order that reviewers have accepted: accuracy against baselines, then ablation by component, then small-sample or transfer,
then interpretation of the learned functions, then limits ([PIK] B; [PGK] B, "the clearest accuracy then interpretation then
limitations template"). Mechanism-first openings are also accepted (KA-CRNN: about 60 % of words before the first result, [KAC] B).
Stroebl reuses the box names of its method flowchart as run-in headings in every case study ([STR] C Fig 2, J2).

### a3. Abstract and highlights

- **Abstracts carry one or two numbers and put the data-efficiency number last.** Lucu A: one number, last sentence, "18 cells,
  0.53 %" ([LA] B); Lucu B: "26 cells, 1.04 %" ([LB] B); Richardson: one number (4.3 %) ([RIC] A); Guo: one number (78 %) ([GUO] A);
  PGKAN: a range 8.5-19.7 % that a reader cannot reproduce for one dataset ([PGK] A). Stroebl's abstract was not in the capture
  ([STR] B), so no pattern is taken from it.
- **Highlights: 4-5 bullets, 0-2 numbers.** Stroebl: 5 bullets with function sequence contribution, headline number, boundary of
  validity, cause of failure, transferable rule; two of five are negative or conditional ([STR] B). Lucu A: 5 bullets, one number.
  PIKAN and KA-CRNN: no numbers. PGKAN: numbers only in the last bullet. The guide caps bullets at 85 characters including spaces.
- **Our constraint is tighter than any exemplar's.** The abstract claim sentence, qualifier sentences and title are fixed by the
  closed outcome table (PREREG_v4 section 11); no p-values, no "significant"; no novelty sentence until condition (d) holds
  (`paper/draft/01_introduction.md` 1.3). The Stroebl highlight pattern fits this well: one highlight per tested claim, one boundary
  highlight (scope words), one transferable-rule highlight.

### a4. How contributions and novelty are stated

| Pattern | Who | Assessment for us |
|---|---|---|
| 5 bold-label bullets, one of them a limits bullet ("critical assessment") | Stroebl ([STR] A) | adopt the labelled form and a limits item; drop "for the first time" (banned here) |
| two tiers, main and secondary contributions | Lucu A/B ([LA] A) | not needed: D029 fixes the order (A15 vs G15 test, matched ladder, learning curves) |
| 4 numbered items, 3 of them architectural labels that cannot be falsified | PIKAN ([PIK] A) | avoid |
| 4 numbered items, each with a checkable statement | PGKAN ([PGK] A) | adopt: every item names its test |
| no list; mechanism prose makes the model form look inevitable | KA-CRNN ([KAC] A) | borrow the mechanism subsection (Methods), not the missing list |
| one framing sentence, no list | Richardson ([RIC] A) | avoid |

Novelty moves that JES accepted: a gap statement lifted from the authors' own earlier review (Lucu, [LA] F1); naming a quantity
"nobody reported" (minimal number of tests, [LA] F4); "first" claims (Stroebl three, PIKAN one). For us "first" is banned in every
form and how many tests a forecaster needs may not be presented as an open question, because Lucu asked it in 2020 (D029;
`01_introduction.md` 1.2-1.3). Our novelty is therefore stated as design commitments plus a gated conjunction sentence.

### a5. How limitations and negative results are handled

- **Negative results are publishable when diagnosed.** Stroebl puts the failure in the highlights, gives it its own subsection, the
  same figure size as the positive result (Fig. 7 vs Fig. 5), three testable explanations, and a two-part recommendation ([STR] G).
  Lucu shows a missed dynamic cell and poor interval calibration and explains each in one paragraph ([LA] G; [LB] G). Richardson's
  best figure shows failing cells on purpose ([RIC] C Fig 6).
- **Unremarked failures are what reviewers quote.** PIKAN's non-physical constants and three formulas for one dataset, PGKAN's
  closed form worse than every baseline, KA-CRNN's under-predicted peaks mentioned only in text ([PIK] F; [PGK] F; [KAC] C Fig 3).
- **Limitations sections are optional in practice but cheap insurance:** PGKAN's 180-word Sect. 6 and Lucu's Sect. 8 are the forms;
  Guo and PIKAN have none and the notes list that as an attack ([GUO] J7; [PIK] J9).
- **For us:** every outcome row of section 11, including P0, P- and K-, has its own title and sentence; a tie or reverse result gets
  the same figure and the same space as a win. The Limitations subsection is planned (`05_evaluation.md` 5.7).

**[PENDING: Najera 2023, Olmos 2021, Naumann 2018]** these are the semi-empirical-law papers JES cites most in our niche; how they
validate (held-out conditions or in-sample fits) could change a4 and the W2 framing below.

---

## (b) Recurring weaknesses of the strongest JES papers in our niche, and how our paper is positioned

Rule for this section: the paper never criticises a named paper for what our design does; it describes the difference in the task
or in the evidence, once, with a citation. "Positioned to" means the design can show it; whether it does is the outcome.

### W1. Statistics: no test across units; seed variance read as unit variance

Evidence. Stroebl: one realisation per design arm, the 28 % reduction has no interval, Case distributions differ by more than 4
sigma ([STR] E, I1). Lucu A/B: means only, no seeds, no repeated orderings, no interval, no test ([LA] E; [LB] E). Richardson: one
split, one run, no spread ([RIC] E). PIKAN and PGKAN: 10-seed violins that measure run-to-run variance on one split, no paired test,
no SD in tables, ablation differences of 0.0001 MAPE presented as effects ([PIK] E; [PGK] E). KA-CRNN: no seeds, no metric ([KAC] E).

Our position. Unit = held-out cycling condition (n = 40 in Test B), equal weight; every contrast paired by condition; the confirmatory
test is a sign test with a fixed design effect, nodes in a graph with family-wise error 0.025 one-sided, simultaneous 95 %
order-statistic intervals over the nine grid cells; seeds enter only through the five-seed ensemble forecast (PREREG_v4 6, 9.1-9.7).

Framing to use (Methods, once; not a contribution bullet):
- "The unit of analysis is the held-out cycling condition (n = 40); every comparison is paired by condition and tested with a sign
  test with a fixed design effect (assumed average pairwise sign correlation at most 0.03). Seeds are averaged into a five-seed
  ensemble forecast and are not treated as replicates."
- In Discussion, if needed: "Reported gains for physics-informed and Kolmogorov-Arnold estimators are usually seed averages on one
  split [refs]; the intervals given here are over held-out conditions." (Neutral, no "unlike", no adjectives.)
Never write: "the first rigorous", "statistically significant", "exact test" (the rule is assumption-based), or any p-value in the
abstract.

### W2. What "held out" means

Evidence. Richardson: test cells are odd-numbered cells, every one of seven load profiles is in training, and the authors say a
block split would extrapolate and do worse ([RIC] E). Lucu A: validation cells at held-out SOC levels sit at temperatures already
seen, one hand-chosen order ([LA] E, I1-I2); Lucu B's "targeted validation cells" are the cleanest held-out-level definition found
([LB] E) but rest on one fixed ladder. PIKAN/PGKAN: same-cycle charging features plus time, a cell split, estimation not forecasting
([PIK] E; [PGK] E). KA-CRNN: one interpolated SOC per cathode ([KAC] E).

Our position. Test B: 40 cycling conditions dealt into 5 folds of 8, none of their cells in training or tuning; the m axis thins
only the training side, so the same 40 conditions are scored at every grid cell (PREREG_v4 4, 4.1). Test C (35 °C, one laboratory)
is descriptive and never called temperature extrapolation.

Guard (retired topic). The paper describes the held-out unit as the task. It does not argue that condition-level splits change
accuracy, does not compare Test A with Test B, and does not make the split a contribution.

Framing to use:
- "Each forecast is for a cycling condition none of whose cells entered training or tuning." (Methods 4.1, Data, captions.)
- Related work, one sentence: "Richardson et al. assigned alternate cells to training and test, so every load profile was present in
  training [ref]; Lucu et al. added ageing conditions in a fixed order and validated on the remaining cells [refs]. The held-out unit
  here is the cycling condition."
- Missing piece: a reader cannot see how far each held-out condition is from its training set at m = 8, 16 and 32. See gap G2.

### W3. Evidence for extracted or "discovered" laws

Evidence. PIKAN: the restricted library forces the Verhulst form; recovered constants are non-physical (C = -2.2171, K = 7.6789);
three different formulas for one dataset; manual pruning; R2 of the symbolic fit to the model, split unstated ([PIK] F). PGKAN: the
closed form (HUST RMSE 0.0109) is worse than every baseline in its own Table 3 (0.0083-0.0090); a printed PDE term is significant in
0 of 10 repeats; abstract says "reveals" while Sect. 4.3 says "library-constrained surrogate" ([PGK] F). KA-CRNN: prefactor and
activation-energy functions co-vary (one heating rate), a monotone penalty imposes part of the story, no stability ([KAC] F). Lucu:
kernel length-scales read as sensitivity ([LA] C Fig 6).

Our position. Chain K: K1 tests whether the extracted closed-form law A15 is non-inferior to its parent A1 on held-out conditions,
K2 whether it beats an equally simplified additive law G15 built by the same frozen library, cap 2, BIC rule and end-to-end refit
(PREREG_v4 7.3); coefficient counts and training-side BIC printed beside K2 (E8); a descriptive stability table over 25 fold-by-seed
laws for A15 and G15 side by side (11a item 6); synthetic recovery as the PC-1 gate; the permanent rule that no form or direction of an
individual effect is named and no temperature direction is read from any cyclic law, because laboratory is aliased with temperature
(7.3 item 6). This is stronger evidence than any exemplar offers and also a narrower claim; the paper must not let the reader infer
more than K1 and K2 test.

Framing to use:
- "Readable means that the extracted law is a short closed form that can be written out and evaluated; we name no form or direction
  for its individual effects." (fixed sentence, 11a item 10)
- "The laws are scored on the 40 held-out conditions that the extraction never saw."
- Caption of the stability table: "descriptive; not evidence that the training design identifies these forms".
Never write: recovered, discovered, identified, governing equation, power law, Arrhenius (for the cyclic law), hinge, threshold,
"no effect", "interpretable physics discovered" (7.3 item 6(c); section 11).

### W4. Baselines and tuning parity

Evidence. Lucu A/B: no baseline at all ([LA] E; [LB] E). Richardson: no semi-empirical or trivial baseline although the Introduction
motivates from Schimpe's law; six configurations scored on the test set, best reported; learner confounded with the time input
([RIC] E). PGKAN: no KAN-only row, no no-physics row, baselines with 5x fewer parameters than claimed comparable ([PGK] E). PIKAN:
baseline tuning undocumented, tuning split not in the main text ([PIK] E). KA-CRNN: none ([KAC] E).

Our position. Persistence R1, window line R2 and the k = 0 population forecast; the dataset authors' semi-empirical model A10 in both
forms; the same network without the law A9; the law with an additive map AG; the hard-integrated law A2; GP-ARD A11 and LightGBM A12;
D* chosen by inner CV per (fold, m) among A9, A11 and A12; 40 TPE trials for every tuned arm; parameter counts, `n_train_used` and fit
time in Table 1; modifier M3 removes T1-T3 if A1 does not beat persistence at g1 (PREREG_v4 7.1-7.4, 11).

Framing to use: "Every tuned arm received the same 40 trials of the same search inside the training conditions of each outer fold;
the data-driven bar D* is the inner-cross-validation winner among three learners, not the learner that scores best on held-out
conditions." (Methods; D033 M6 definition.)

### W5. Attribution: which part of the model buys the gain

Evidence. PGKAN cannot separate KAN, physics and sensing weights ([PGK] E, I3); PIKAN has a KAN-only baseline but no test ([PIK] E);
Richardson's GP-versus-boosting gap mixes learner and inputs ([RIC] E).

Our position. P2 (A1 vs A9) tests the law within the same network; the ladder ln(S_A9/S_A1) = ln(S_A9/S_AG) + ln(S_AG/S_A1) is
estimated at every cell with simultaneous intervals and reported as medians of the terms, never as a decomposition of the median
(9.6); Q-H isolates the soft residual against exact integration; Q-T isolates the storage cells.

Framing: "Medians do not add, so the two shares are reported separately and are not read as a decomposition of the median gain."

### W6. Internal consistency of numbers and text

Evidence. PGKAN HUST MAPE 0.0057 in Tables 3/5 and 0.0064 in Table 9 for the same architecture; loss in Fig. 2 differs from Eq. 12
([PGK] E, C Fig 2). Lucu A 0.31 vs 0.30; Lucu B cell counts 124/122 ([LA] E; [LB] B). Stroebl "17-fold" for 18.1, duplicated
conclusion paragraphs, unused legend entry ([STR] I6). KA-CRNN MSE in text, absolute error in Eq. 16 ([KAC] E). Guo unresolved
cross-reference in the VoR ([GUO] B).

Our position. Figure and table scripts read only statistics-step outputs and compute nothing inferential (`code/figures/README.md`
binding rule); every number in prose carries a source comment; the gate auditor reconciles manuscript numbers against `runs/`.
Text action: one term per concept (C4 elegant-variation rule in the style guide); equations in figures typeset from the same source
as Methods.

### W7. Post hoc data handling

Evidence. Stroebl removed SoC 100 % after seeing non-monotone behaviour ([STR] G, I3); Lucu discards about 35 % of data using
whole-trajectory knowledge ([LA] I5). Both report the counts, which is the part to copy.

Our position. Inclusion and exclusion rules fixed before scoring (PREREG_v4 3.3), capped windows disclosed in Methods (5, D033 M4).
Missing: one table of cells and check-ups kept and dropped per laboratory and stage with the rule that dropped each (gap G5).

### W8. Interval calibration (do not import)

Lucu reports calibration scores and Richardson a CS_2sigma column ([LA] E; [RIC] D). Batch R2 suggested a calibration column. **Not
for this paper:** PREREG_v4 header ("No coverage, calibration or interval-calibration claim is made anywhere (retired topic)").
The only intervals are inferential intervals on median log ratios.

### W9. Claim language

Evidence. "excellent cross-dataset generalisation" for 2.5-20 % SOH error ([PIK] E); "reveals the dominant degradation PDEs" against
the paper's own disclaimer ([PGK] F); "one of the most accurate long range predictions" with no comparison ([RIC] A).
Our position: banned-word lists of PREREG_v4 1, 7.3 and 11; claim words tied to tiers (S, N, none, reverse S); the style guide lists
the replacements.

---

## (c) Display-item plan v2

### c1. Global specification (applies to every item)

- **Widths (Elsevier artwork sizes, from the guide's pixel minima at 300 dpi: 1063 px = 90 mm, 2244 px = 190 mm).** Double column
  190 mm; single column 90 mm; graphical abstract 130 mm wide (guide: readable at 13 cm, at least 1328 px wide). Heights at most
  230 mm. This replaces the 16 cm (`pk_style.W_FULL`) and 13 cm widths of D-figures (change C1).
- **Type.** Sans serif (Arial/Helvetica), 8 pt for labels and ticks at final size, 7 pt minimum anywhere including the schematic and
  graphical abstract, panel letters 9 pt bold, lower case in parentheses, top left outside the axes ([KAC] C Fig 4: letters collided
  with ticks). Math symbols in a serif math font so that the throughput symbol does not read as a Latin v (lead render note).
- **Lines and markers.** Data lines 1.0-1.2 pt, reference lines 0.6 pt dashed grey, markers 3.5-4.5 pt; no line thinner than 0.5 pt.
- **Palette (colour-blind safe).** Okabe-Ito for arms; identity always by colour + marker + line style, so greyscale still separates
  arms. Fix the collisions in `pk_style.ARMS` (change C9): D* and A12 share teal #44AA99, A15 and A11 share indigo #332288 and
  marker "h"; give D* its own identity (for example vermilion #D55E00 with a square marker; A5 can move to the Tol wine #AA3377,
  since A5 runs only at m = 32) and A15 a distinct marker. Never draw an arm and a laboratory in the same panel, because LAB_COL reuses
  orange, green and purple. Do not use Okabe-Ito yellow #F0E442 for lines on white. R1 persistence in mid grey #7A7A7A dotted, not
  #B0B0B0. Temperature: three discrete cividis levels (23, 35, 45 °C; 10 °C for storage only), never a rainbow ([LB] C Fig 2; [PIK] C
  Fig 1 failures).
- **Uncertainty.** The only intervals drawn are those the statistics step supplies: simultaneous 95 % order-statistic intervals of
  the median log ratio (ranks 8 and 33 of 40), BCa intervals of the mean pp difference, and min-max envelopes of run-writer bands. Every
  panel that shows a summary also shows its units (the 40 conditions as small grey dots) ([PIK]/[PGK] violins hid n). No KDE, no
  violin, no bar without its units. Tier letters (S, N, -, rS) only at gated cells and only from `effective_tiers`.
- **Held-out marking.** Held-out conditions in every design and forecast figure are marked the same way: open marker with a thick
  outline and the label "held out" in the arm-neutral accent colour (black), never red only ([KAC] Fig 2 used red italics).
- **Axes.** One quantity per axis, no dual axes ([LA]/[LB] learning curves mixed MAE and CS on two axes); stress axes restricted to the
  data range, with the extrapolated range hatched where a curve continues beyond it ([KAC] Fig 4 ran past the data; [LB] Fig 6 shaded
  honestly).
- **Captions.** Brief title (not on the figure), then what is drawn, n, what the interval is, and which numbers are descriptive. Synthetic
  inputs keep the watermark until real runs exist.

### c2. Item by item

**Fig. 1 Method schematic (190 x 110 mm).**
Emulate: Pugalenthi 2026 Fig 2 (real data strip into the diagram; FF row rated 8) and KA-CRNN Fig 1 (green = learned vs grey = fixed
colour code, cross-referenced panels) ([KAC] C Fig 1, J2); Guo Fig 9b is the conceptual slot (ML replaces part of a semi-empirical model
under a physics constraint) ([GUO] C Fig 9).
Improve: every number in the figure is real or labelled "illustrative" ([KAC] Fig 1B carried unlabelled placeholder values); the (m, k)
grid appears as a 3 x 3 inset with g1, (32, 2) and g4 named, because the learning curve is the paper's axis ([STR] J1: "ours is a
ladder, so draw the ladder").
Specs: (a) top strip, three real data panels after the freeze (one storage cell, one cycling training cell, one held-out cycling cell
with the window shaded and the forecast region marked); (b) inputs s, Q0, window, throughput; (c) solution network F with latent z_c;
(d) law dy/dt = [r_cal(T, SOC) + r_cyc(s) nu] h(y) typeset once, with the two KAN maps as blue boxes holding small spline glyphs
(learned) and h(y), the superposition and the integral in grey (fixed); (e) soft residual with the three collocation-set glyphs
(record end or whole axis, training-hull LHS points, calendar twins); (f) the (m, k) grid inset and the extraction path A1 -> A15
with the matched G15 path from A4. Learned = Okabe-Ito blue tints; fixed physics = grey; data = black markers. No arm comparison here.

**Fig. 2 Design map and training subsets (190 x 140 mm).**
Emulate: Stroebl Fig. B.10 (5 x 5 scatter matrix with physical-constraint region; the best design-map idea in that paper, but hidden
in an appendix) ([STR] C B.10, J1); KA-CRNN Fig 2 (whole design in one grid, held-out marked) ([KAC] C Fig 2); Lucu B Fig 2 factor
banners ([LB] C Fig 2).
Improve: put it in the body; show laboratory and stage (the confound) and the nested subsets, which no exemplar has.
Specs: (a) storage T x SOC, 19 conditions, colour = laboratory, marker = stage, size = number of cells; (b)-(d) cycling pairs T x DoD,
SOC_mid x DoD, C_ch x C_dch with the impossible region (DoD above SOC_max) shaded light grey, colour = laboratory, marker = stage, Test B
fold printed as a small digit beside each point; (e) stacked counts of cycling conditions by temperature, laboratory and stage
(metadata only, allowed before the freeze); (f) nested subsets: for each of the 5 folds a row of the 32 training conditions in
max-min order with the m = 8 and m = 16 cut lines and temperature colour, so a reader sees that each m = 8 subset holds at least two
conditions per temperature (PREREG_v4 4.1); (g) [ANALYSIS-EXPLORATORY, identifiers only] distance of each held-out condition to its
nearest training condition in the standardised five-stress space at m = 8, 16 and 32 (strip plot, 40 points per m), answering "how
much of the test is interpolation" ([LA] I1; [RIC] E); (h)-(i) after the freeze, replicate fade of two conditions with all
replicates drawn (Lucu B Fig 2 form). Laboratory colours appear only in this figure.

**Fig. 3 Forecast overlays at held-out conditions (190 x 160 mm).**
Emulate: Richardson Fig 6 (one panel per held-out unit, bands, failures shown; the best figure of that paper) ([RIC] C Fig 6); Lucu A
Fig 4 / B Fig 5 (the same held-out condition at rising training information) ([LA] C Fig 4; [LB] C Fig 5); KA-CRNN Fig 3 (markers =
data, bold line = model, held-out label) ([KAC] C Fig 3).
Improve: conditions chosen by a rule, not by eye; the worst condition shown as well ([KAC] and [PGK] showed only the best-looking unit);
the same condition drawn at g1 and g4 so the reader sees what eight versus 32 conditions and two versus four check-ups change.
Specs: columns = the held-out conditions at the 25th, 50th and 75th percentile and the worst of A1's g1 condition score (`rank_pick`,
no quantile computed); row 1 = g1, row 2 = g4 (same conditions); row 3 = three Test C conditions picked by the same rule, boxed and
labelled "held-out temperature-laboratory domain (descriptive)". In each panel: observed check-ups as markers (window filled, forecast
set open), window shaded light grey, A1 (blue, five-seed min-max band), D* (its own colour), A10 (orange), R1 thin dotted grey (the M3
comparator at g1); at most three coloured lines. Printed in the panel: condition label (T, SOC_mid, DoD, C_ch/C_dch) and the cell RMSE in
pp of A1 and D*. Shared y-axis within a row. One replicate per condition (the median-RMSE cell, as in D-figures).

**Fig. 4 Learning curves over the 3 x 3 grid (190 x 200 mm; the paper's primary figure).**
Emulate: Lucu A Fig 3 / B Fig 4 (ordered ladder on x, banner naming what each step adds, held-out-only error) ([LA] C Fig 3; [LB] C
Fig 4); PIKAN Fig 7 (error against the number of training units) as the idea to do properly ([PIK] C Fig 7, J3); Nakano 2024 Fig 11
(error against labelled fraction with CI bands over seeds; FF rating 8).
Improve: units visible, simultaneous intervals, absolute and relative scales separated, one axis per quantity, no dual axes, tiers
only where a test exists ([LB] C Fig 4 used dual axes and different y-ranges; no exemplar has an interval on a learning curve).
Specs, three blocks:
- (a) Absolute scale, one panel per k (0, 2, 4): mean condition RMSE in pp of A1, D*, A9, AG, A2, A10 and R1/R2 (k >= 1) against m =
  8, 16, 32 (log-spaced positions), points with seed-SD bars from `arm_table.json`, lines joining them; horizontal grey band for the
  training-side replicate spread R_LOO (`reference.json`, m = 32), labelled "replicate spread (training side)". This is the panel Lucu
  readers expect (gap G3).
- (b) Relative scale, rows = comparator (D*, A9, AG, A2, A10), columns = k (0, 2, 4), x = m: median relative error reduction of A1
  against the comparator, X = 100 (1 - exp(-median L)) %, with the simultaneous 95 % interval, 40 grey condition dots behind each
  estimate with deterministic jitter, zero line, and the margin lines +2 % (S) and -10 % (N) drawn only in the panels that hold a gated
  cell. Tier letters at g1 (D* row: P1; A9 row: P2) and the P3 contrast shown as a bracket between g1 and (32, 2) in the D* row,
  labelled with its tier. Every other cell is "estimated" and carries no letter.
- (c) Ladder: at each of the 9 cells, the law share ln(S_A9/S_AG) and the KAN share ln(S_AG/S_A1) as two offset points with
  simultaneous intervals (medians of the terms), with the caption sentence that medians do not add.
Right-hand margin column (as in D-figures): mean paired pp difference with BCa interval for the gated cells only. The random-subset
downgrade row at g1 is drawn as an open diamond in the D* row (9.8). Pool arms (A11, A12) are not drawn separately here; they are in
Table 1.

**Fig. 5 Extracted laws, learned stress dependences and their stability (190 x 170 mm).**
Emulate: KA-CRNN Fig 4 / B.1 (learned functions drawn large; the dashed rug of training conditions) ([KAC] C Fig 4, B.1, J5); PGKAN
Table 7 term frequencies over repeats and PIKAN Fig 10 stage layout (train, prune, symbolise, formula) ([PGK] D Tab 7; [PIK] C Fig 10).
Improve: fold-by-seed envelopes ([KAC] none; [PIK] one fit per dataset), A15 and G15 side by side with the same treatment, coefficients
counted, curves inside the data range, and the temperature carve-out visible rather than hidden.
Specs: row 1 calendar: (a) a(SOC) and (b) effective E(SOC) from the calendar KAN with fold x seed envelopes, the dataset authors'
calendar fit as a dotted reference labelled "consistency with the semi-empirical fit", caption caveat that 10 °C storage is all SIE and
45 °C all HM (11a items 1, 9); (c) storage rate against SOC per storage temperature, SOC > 0.8 region hatched with "stage 1 only"
(11a item 2). Row 2 cyclic partial dependences for SOC_mid, DoD, C_ch, C_dch: A1 envelope (blue band), A4 mean (dashed), A10 direction
(dotted), A15 and G15 representative laws (thin lines, their own identities); rug of the training conditions on each x-axis; outside the
training hull hatched. A fifth panel for temperature shows only the fixed label "temperature (aliased with laboratory; no form or sign
reported)" and no curve (7.3 item 6(b)). Row 3: (h) the A15 and G15 closed forms typeset as printed by `law_summary.json`
(representative fold), with coefficient counts and training-side BIC; (i) the descriptive stability panel: family votes, tie share,
additivity share and sign votes over the 25 fold-by-seed laws per input except temperature, A15 and G15 in adjacent columns, caption
"descriptive; not evidence that the training design identifies these forms". If (h)-(i) do not fit legibly at 190 mm, move (i) to an
appendix table and keep a pointer.

**Fig. 6 Storage axis (190 x 120 mm).**
Emulate: Nakano 2024 Figs 7, 9 (colour by the nuisance factor; FF rating 8); Lucu A Fig 2 (storage curves by SOC) ([LA] C Fig 2).
Improve: the condition is the unit in every panel, not pooled points; the outside-hull SOC levels are visibly separated (caption rule
of D-figures, 2026-11-06).
Specs: (a) Q-T at g1: per-condition paired log ratio of A13 against A1 (40 dots) with the median and the interval from
`secondary.tests.QT_g1.median_interval`, tier letter from the secondary family; (b) S2 storage transfer, descriptive: predicted against
observed retention at the last check-up per held-out storage cell, colour = temperature, SOC > 0.8 open markers, no tier word;
(c) model-defined calendar share of fade of cycled cells (A1 filled, A2 open) with the 100 % line and the count of physically
impossible splits printed (11a item 4); (d) ln calendar rate against 1000/T at the selected SOC levels with envelopes, outside-hull
levels dashed and labelled "outside hull", with the PC-2 fixed sentence including the temperature-laboratory clause.

**Fig. 7 Residual map (190 x 70 mm).**
Emulate: Yuan 2025 Fig 15 (compact annotated heat maps with per-panel scales; FF rating 8). Improve: training points overlaid, counts
per bin (`n_cells_T_SOC`, `n_cells_cch_T`) printed small, empty bins blank not zero. Specs: (a) |R| over (T, SOC), (b) |R| over (C_ch,
T), sequential cividis, one colour bar per panel, values printed where n >= 1; caption: descriptive, no claim (PREREG_v4 14, Fig. 7).

**Fig. 8 Synthetic pipeline recovery, PC-1 (90 mm single column, 90 x 80 mm; appendix if space is short, as PREREG_v4 14 allows).**
Emulate: Pugalenthi 2026 Fig 6 (synthetic truth first, truth as reference; FF rating 8); Stroebl Fig 8 (truth as a dashed line) and
its lesson to report how often recovery fails, not only the extreme pair ([STR] J6). Specs: nRMSE of each structured arm on the G0
draws, box plus every draw, the 0.15 gate line; one inset of recovered against true log-rate surface for the median draw. No G1/G2
discrimination claim (struck from v4).

**Table 1 Accuracy of all arms (190 mm, booktabs, no vertical rules or shading, as the guide asks).**
Emulate: Stroebl Table 1 (model adequacy beside the measurement-noise yardstick) ([STR] D Tab 1, J4); PGKAN Table 4 (cost columns)
([PGK] D Tab 4); Wang 2024 Table 4 layout (FF rating 7). Improve: spread, n and cost beside accuracy; the replicate-spread yardstick in
the same table; no ranking typography.
Specs: Panel A, rows = arms (A1, A9, AG/A4, A5 at m = 32 only, A2, A11, A12, D*, A10 both forms, A13, A15, G15, R1, R2, k = 0 forecast,
raw-feature LightGBM); columns = Test B grid cells g1 ... g4 and the five other cells (mean condition RMSE in pp +- seed SD, with the
footnote that the seed SD is the SD of single-seed pooled means), Test C, S2. Panel B: parameters, `n_train_used`, fit time, E/R_LOO and
E/R_WARP per arm at m = 32. No bold "best" and no underline (change C8: a mean ranking can contradict a median-based tier, PREREG_v4
9.8 rule 1); tiers live in Fig. 4 and Table 2. If the 190 mm width is exceeded, split Panel B to the appendix first.

**Table 2 Ablations, controls and the outcome reached (190 mm).**
Emulate: Deng 2025 Table 4 control-variable table (FF rating 7) and KA-CRNN Table 1 (which quantity is a learned function of which
input and which is a constant) ([KAC] D Tab 1, J6). Improve: each row names what changes, the hypothesis, the test and the tier, and the
controls carry their required outcome.
Specs: Part A, one row per contrast (P1, P1-rev, P2, P3, most-test, K1, K2, K2-rev, Q-H g1/g4, Q-A10 g1/g4, Q-T g1, M3): what changes,
parameters of each side, cell, median relative reduction with interval, mean pp difference with BCa interval, positives of 40, tier
(design-effect rule) and, in a smaller column, the plain-test descriptive row. Part B, controls: NC-1 (bit identity), NC-2 (stress
permutation, wording consequence), PC-1 (gate), PC-2 and PC-3 labelled "reported check outside the family-wise count". Last row: the
outcome-table state (P, K, modifiers) and the title reached.

**Graphical abstract (130 x 52 mm; at least 1328 px wide; text >= 8 pt at final size).**
Emulate: PIKAN Fig 4 (a workflow figure that carries real results) ([PIK] C Fig 4, J2); Nakano 2024 Fig 1 (problem and model at a
glance). Specs: three framed blocks left to right: the design (mini Fig. 2a-b, held-out conditions marked), the model (F + law with the
blue KAN boxes), the result (mini Fig. 4b, D* row, k = 2: median relative reduction against m with intervals and the g1 tier letter).
Text at least 8 pt (D-figures measured 7.0-7.6 pt; change C10). No number that is not in the abstract.

### c3. Changes against `debates/D-figures.md` (2026-11-05, written against PREREG_v2)

| # | Item | D-figures | v2 | Reason |
|---|---|---|---|---|
| C1 | all | 16 cm full width, 13 cm medium | 190 mm double, 90 mm single, 130 mm graphical abstract | Elsevier artwork sizes (guide pixel minima); `pk_style.W_FULL` must change |
| C2 | Fig. 4 | forest plot at one cell | three-block learning-curve figure over the 3 x 3 grid (absolute, relative with tiers, ladder) | PREREG_v4 14 redefines Fig. 4; Lucu form improved |
| C3 | Fig. 3 | 3 x 3, rows = temperature, lines A1, A10, A12 | rows = g1, g4, Test C; columns = 25/50/75th percentile + worst condition; lines A1, D*, A10 + thin R1 | v4 asks for g1 and g4; A12 is not necessarily D*; M3 makes R1 relevant; worst case answers the cherry-picking attack |
| C4 | Fig. 5 | "Arrhenius ordering by temperature", direction of five cyclic effects against A10 | no temperature curve or verdict for any cyclic law (fixed label panel); A15/G15 closed forms, counts, BIC; stability panel; rug and hull hatching | PREREG_v4 7.3 item 6(b), 11a items 5-7, 9 |
| C5 | Fig. 6 | 2 x 2 without Q-T | panel (a) is Q-T (A13 vs A1 at g1) | PREREG_v4 14 Fig. 6 |
| C6 | Fig. 8 | G1/G2 discrimination, 0.30 fail line, additive-GAM floor | G0 (PC-1) only, 0.15 line; single column or appendix | H7 beyond PC-1 struck in v4 |
| C7 | Fig. 2 | 2 x 3, metadata panels a-d, two replicate panels | adds nested-subset panel (v4 panel g) and the exploratory distance-to-training strip | PREREG_v4 14; gap G2 |
| C8 | Table 1 | best bold, second underlined; tier column in panel B | no ranking typography; tiers only in Fig. 4 and Table 2 | rule 9.8.1 (mean against median) |
| C9 | palette | D* = A12 teal; A15 = A11 indigo, same marker | distinct identities for D*, A15; arm and lab colours never in one panel; R1 darker | collisions in `pk_style.ARMS` |
| C10 | graphical abstract | 7.0-7.6 pt; mini forest | >= 8 pt; mini learning curve with the g1 tier | readable at 13 cm; v4 headline is the learning curve |
| C11 | wording | "Holm CIs", "paired Wilcoxon" (BLUEPRINT v1) | simultaneous order-statistic intervals; design-effect sign test in a graph; Wilcoxon appendix-only | PREREG_v4 9.3-9.7 |
| C12 | Fig. 1 | throughput as Greek nu in Arial | serif math symbol | lead render note |
| C13 | Table 2 | Part B a plain block | Part A per contrast with the plain-test descriptive column; M3 row; outcome state row | PREREG_v4 2, 9.3, 11 |

Kept from D-figures: the percentile selection rule, the pp column beside the log ratio, the ban on hand-typed numbers, tiers read only
from the statistics step, watermarking of synthetic renders, the Fig. 6 and Table 2 caption rules of 2026-11-06.

**[PENDING: Schuster 2015, Keil 2016, Naumann 2018]** these are the most-cited JES experimental-campaign and calendar-law papers; their
design-map and residual-plot forms could replace the exemplar chosen for Fig. 2 or Fig. 5. **[PENDING: Liu 2025 TL-LSTM]** the nearest
data-scarce trajectory paper; its learning-curve figure, if any, could change the Fig. 4 exemplar.

---

## (d) Ranked gap list: what top JES papers have, or reviewers will demand, that our plan lacks

Ranking = likelihood that a JES reviewer raises it x cost of not having it. Tags as requested.

1. **[DESIGN-ISSUE-FOR-LEAD] C-rate and the other stress factors: is each one needed?** Stroebl et al. report on this cell type that
   dropping C_ch and C_dch from their cycle model leaves residuals unchanged (Table 1: p 0.76-0.98, Spearman above 0.995) and that
   the model is inadequate ([STR] D Tab 1, J5; batch R1 item 14). A reviewer will ask what our learned C-rate dependence adds. The
   preregistration has NC-2 (all stress inputs permuted together, g4, wording consequence) and the 11a item 5 partial dependences
   (descriptive), but no leave-one-stress-factor-out arm and no test of a single factor. Options the lead may weigh (not resolved here):
   (i) leave it as is and answer in Discussion with the action-A8 sentence (report any C-rate dependence of the learned map against
   Stroebl's finding; never call a C-rate effect established); (ii) a post-freeze leave-one-factor-out row at g4, labelled
   exploratory, no tier word, no consequence, run only if CPU remains; (iii) anything with a test or consequence would need a decision
   row before the freeze. Note for the lead: option (ii) re-tunes arms and costs CPU; the order of runs (section 15) would have to
   place it last. **[PENDING: Olmos 2021]** chemistry-influenced stress factors; it may show whether C-rate terms are routinely
   supported, which changes how hard reviewers push.
2. **[ANALYSIS-EXPLORATORY] [FIG] How far is each held-out condition from its training set?** Lucu's validation was mostly
   interpolation and Richardson kept every regime in training ([LA] I1; [RIC] E); reviewers now ask. Compute, from identifiers only,
   the standardised five-stress distance of each held-out condition to its nearest training condition at m = 8, 16, 32 (Fig. 2g), and
   colour the 40 condition dots of Fig. 4b by that distance. Descriptive, no test, no tier word, no claim that error grows with
   distance. It is not a split comparison (the split is fixed); it describes the test set.
3. **[FIG] Absolute-error learning curve with the replicate-spread yardstick, and the worst condition.** Fig. 4 as specified in
   PREREG_v4 14 is relative only; JES readers of Lucu expect error in pp against the number of conditions ([LA] C Fig 3; [LB] C Fig 4)
   and Stroebl's adequacy table sets error beside the noise floor ([STR] J4). Add block (a) of Fig. 4 (mean pp with seed SD from
   `arm_table.json`, R_LOO band) and the worst-condition column of Fig. 3 (rank pick). Both read supplied numbers only.
4. **[TAB] Data accounting and replicate spread (appendix).** Every exemplar that survived scrutiny reports retention per condition
   (Lucu A Table 3, Lucu B Table 1/B1 with a footnote cause per large variance, Stroebl's outlier counts per stage) ([LA] D; [LB] D;
   [STR] J10). We have the rules (3.3) and the cap disclosure (5) but no table: cells and check-ups kept and dropped per laboratory and
   stage with the rule that dropped each, and replicate spread per held-out condition with a footnote for each large value.
5. **[TEXT] Mechanism subsection and numbered assumptions.** KA-CRNN's mechanism review ending in numbered conclusions makes its
   model form look inevitable ([KAC] J1); Stroebl states assumptions R1-R3 and tests each ([STR] J8). Our Methods (`04_methods.md`)
   has the law but no mechanism paragraph and no numbered assumptions. Write (about 1 page): calendar loss and SEI growth with time
   and SOC, cycling loss with throughput, DoD and C-rate, why one shared state factor h(y) (PREREG_v4 1 mechanism (1)), placed in
   Guo's taxonomy as physics-based embedding B3(b) with residual learning B2 as the neighbour and the extraction as an A2 symbolic
   reduction ([GUO] taxonomy; cite Guo, not a claim that nothing else exists). Then assumptions as remarks with the diagnostic that
   checks each: (R1) one state factor for both terms (tournament, 7); (R2) average pairwise sign correlation at most 0.03 (dependence
   rows 9.9 (q), (r)); (R3) no laboratory x temperature interaction for Test C (printed with the result); (R4) causal throughput after
   the window (oracle-throughput sensitivity row).
6. **[TAB] Positioning table in Related work.** Guo's Table 5 compares hybrid families but has no column for the evaluation unit
   ([GUO] D Tab 5, J3). A compact table (method; physics form; what the learner replaces; held-out unit; baselines; statistics across
   units) for Richardson, Lucu A/B, Stroebl, PIKAN, PGKAN, KA-CRNN, Zhang JES 182 and ours, filled only from full-text notes. It is an
   eleventh display item: place it in the appendix, or move Fig. 8 to the appendix as PREREG_v4 14 allows and use the slot. Guard: the
   "held-out unit" column describes tasks; no row says that a split changed an accuracy.
7. **[TEXT] Limitations subsection with the confounds stated first.** Exemplars that lack one are attacked for it ([GUO] J7; [PIK]
   J9). Ours must lead with: laboratory aliased with temperature (35 °C all INT, 45 °C 12 of 15 HM, 10 °C storage all SIE); one cell
   type; Test C not a temperature test; window cap depends on record length; the design-effect assumption; the latent is a local mode
   from the prior; path dependence and dynamic profiles outside the matrix ([LB] E, J9); E4 design-hull information available to the
   PINN only. `05_evaluation.md` 5.7 has part of this; check it against this list.
8. **[FIG] Learned-function plots inside the data range, with a rug and hatched extrapolation.** Reviewers attacked KA-CRNN for curves
   past the data and humps between points ([KAC] F3); covered by the Fig. 5 spec above, listed so that the figure-smith does not drop it.
9. **[DESIGN-ISSUE-FOR-LEAD] One ordering of the nested subsets.** Lucu's "N cells is enough" rests on one hand-chosen order and is
   the attack the notes list first ([LA] I2; [LB] I1). We have a rule-based max-min order and a random-subset downgrade row at g1 only
   (three seeded random subsets; 9.8). The curves at m = 16 and the P3 contrast at (32, 2) rest on the single max-min order. A band over
   random orderings at every m would need new runs and is not preregistered; the lead decides whether to leave it (and say so in
   Limitations), or add a post-freeze exploratory row. Text action either way: Methods states that subsets come from one rule-based
   order and the g1 random-subset row is the only check of order dependence.
10. **[TEXT] Data and code availability with persistent identifiers.** Richardson, PIKAN and KA-CRNN give no code link in the texts
    read ([RIC] H; [PIK] H; [KAC] H); Stroebl's data are CC BY 4.0 ([STR] H). State the dataset DOI (figshare 25975315), a Zenodo DOI for
    code, frozen preregistration and per-condition predictions, and the licence. **[PENDING: Wang 2024]** open benchmark and code
    library; may set the bar for what JES expects in a release.
11. **[TEXT] Figure-caption AI rule, decision for the lead.** The Elsevier artwork policy asks that use of generative AI tools to create
    an image be disclosed in each caption as well as in the declaration; the project rule puts AI use only in the Declaration
    (`CLAUDE.md`). Data plots made by scripts from run files fall under the "data visualisation" allowance; a schematic (Fig. 1, graphical
    abstract) drawn with a generative tool would need a caption note. The lead should confirm how Figs 1 and the graphical abstract are
    produced before the captions are written.
12. **[TEXT] One results ledger and one term per concept.** Exemplar mismatches (W6) are what referees quote. Before submission the gate
    auditor's reconciliation covers numbers; the writer covers terms (held-out cycling condition, check-up, closed-form law, the
    dataset authors' semi-empirical model) and equation identity between figures and Methods.

Items a reviewer might ask for that we deliberately do not add: interval calibration or coverage of forecasts (retired topic, W8); a
Test A vs Test B accuracy comparison (retired topic); a GP baseline (already A11); a KAN edge-glyph diagram of the trained network
(the Fig. 1 glyphs stand in; [PIK] C Fig 8 shows that such glyphs are unreadable at print size).
