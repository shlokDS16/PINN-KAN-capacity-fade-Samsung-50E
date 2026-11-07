# JES style guide for the PINN-KAN capacity-fade paper (for the research-writer agent)

Version 2026-11-06. Distilled from the eight deep exemplar notes in `notes/exemplars/deep/` (cited as [STR] Stroebl 2026, [LA]/[LB]
Lucu 2020 A/B, [RIC] Richardson 2019, [GUO] Guo 2022, [PIK] PIKAN, [PGK] PGKAN, [KAC] KA-CRNN), the JES guide for authors
(`notes/JES_guide_for_authors_2026-11-04.md`), the preregistration's wording rules (`runs/prereg/PREREG_v4.md` sections 1, 7.3, 9.3,
11, 11a) and the `research-humanizer` skill. Companion: `notes/exemplars/BLUEPRINT_v2.md` (what to show and why).
Spelling: British English (en-GB), -ise forms, no Oxford comma, as in the current draft. Nine paywalled exemplars are unread; where
one could change a rule it is marked **[PENDING: name]**.

## 0. Rules that override everything below

1. **No number without a file.** Every number in prose comes from a file in `runs/<run-id>/` (statistics-step outputs listed in
   `code/figures/README.md`) or from a cited paper with page, table or figure location. Put the source in an HTML comment after the
   sentence: `<!-- src: runs/<id>/analysis/contrasts_v4_B.json estimated.rows[D*|8|2].rel_reduction_pct -->`. A number that is not yet
   available is written `[RESULT: what, file, field]`. Never round differently from the table that shows the same number.
2. **Claim sentences are fixed.** Title, abstract claim sentence, extent clause and qualifier sentences are the strings of the closed
   outcome table (PREREG_v4 section 11), filled only with bracketed values from the statistics step. Do not paraphrase them.
3. **Tier words carry the claim strength.** S: "had a median condition error X % lower than"; N: "was no more than 10 % worse than
   (one-sided bound); not shown better"; none: "could not be distinguished (interval)"; reverse S: the comparator's error was lower.
   No other claim verb is allowed for a gated or secondary contrast. Estimated contrasts get numbers and intervals, never tier words.
4. **Retired topics stay out**: no coverage, calibration or interval-calibration claim; no accuracy comparison across split types
   (Test A against Test B, Test B against Test C); held-out evaluation is the task, never a contribution.
5. **AI use appears only in the Declaration of generative AI use**, never in Methods, captions, Acknowledgments or the cover letter
   (project `CLAUDE.md`; see BLUEPRINT_v2 gap 11 for the caption question the lead must settle).
6. **No citation without a verified entry** in `paper/draft/refs_verified.md`; otherwise `[AUTHOR: add verified reference]`.

## 1. Section-by-section moves

### Abstract (at most 250 words; one paragraph; abbreviations defined again inside it)
JES asks for purpose, procedure, main findings and conclusions. Exemplars put one or two numbers in the abstract and the
data-efficiency number last ([LA] B; [LB] B; [RIC] A). Our abstract has six moves, in this order:
1. Context, one sentence, concrete: what calendar-plus-cycle laws are used for and what limits them. Do not present "how many tests are
   needed" as an open question (Lucu asked it in 2020; D029).
2. What was done, one or two sentences: the model (physics-informed network, Kolmogorov-Arnold stress functions, joint storage and
   cycling training), the data (Samsung INR21700-50E, three laboratories), the task (held-out cycling conditions), the grid (m, k).
3. How it was judged, one sentence: comparators named by role (best tuned data-driven learner, same network without the law, the
   dataset authors' semi-empirical model, an equally simplified additive law), unit n = 40 conditions, paired.
4. The claim sentence of the outcome-table cell, verbatim with its numbers and interval.
5. The required qualifier sentences (Q-H g1, Q-A10 g1 and g4, Q-T g1; M3 clause if it applies; mean-vs-median rule 9.8.1 if
   triggered).
6. Scope sentence with the fixed scope words: "held-out cycling conditions of one cell type in three laboratories". The novelty
   sentence ("we found no earlier study that ...") appears only if condition (d) of `01_introduction.md` 1.3 holds.
No p-values, no "significant", no "first", no citations.

### Highlights (3 to 5 bullets, at most 85 characters each including spaces; separate file)
Copy Stroebl's function sequence, not its words ([STR] B): one bullet per tested claim (P chain, K chain), one boundary bullet,
one transferable-rule bullet. Each bullet is a full statement with a verb, present tense, no abbreviation that is not defined
in the bullet, no interval (no room), no tier-free comparative ("better") without the tier's verb. Count characters with a script.

### Introduction (about 900-1,100 words; funnel then contributions then roadmap)
Moves ([STR] B; [PIK] A; [PGK] A; [GUO] A):
1. Problem in the field: semi-empirical calendar and cycle laws need large ageing matrices; the stress dependence is usually fixed by
   hand.
2. What exists, in families, with the nearest work named: parametric laws fitted to this dataset and the authors' statement that the
   cycle part is inadequate [stroebl2026]; learning curves over ageing conditions [Lucu A, B]; physics-informed and KAN estimators of
   SOH from same-cycle features [pikan2026, pgkan2026]; KAN-valued kinetic parameters [KA-CRNN]; Guo's taxonomy places our model as
   physics-based embedding.
3. What those studies leave untested, stated as a property of their designs, not as a void in the literature ("these studies estimate
   state of health from features of the same cycle" rather than "no study has forecast ...").
4. The question in three parts (PREREG_v4 1): how few cycling conditions and check-ups, how much from the law and how much from the KAN,
   and whether the extracted closed-form law predicts held-out conditions at least as well as an equally simplified additive law.
5. Contribution list, three numbered items in the D029 order, each naming its test; optionally the gated conjunction sentence.
6. Roadmap, one sentence ("Section 2 ... Section 6 ...").

### Methods (Data, Method, Evaluation protocol)
- Open the Method with a short mechanism paragraph that ends in the model form (KA-CRNN's pattern, [KAC] J1): calendar loss with time,
  temperature and SOC; cycling loss with throughput, DoD, SOC window and C-rate; why one shared state factor h(y).
- Then the task and causal window, the law, the KAN parametrisation, the comparators, tuning and seeds, the extraction of A15 and G15.
- State assumptions as numbered remarks with the diagnostic that checks each ([STR] J8; BLUEPRINT_v2 gap 5).
- Evaluation protocol: splits in one paragraph plus the split table; endpoint; contrast and test (name the rule exactly); claims and
  the outcome table; controls; downgrade and sensitivity rows. The split unit, the number of held-out units and the tuning split are
  in the main text, not a supplement ([PIK] J9).
- Every arm is defined once with its code and a plain name; after that use one or the other consistently (names in prose headlines,
  codes in tables and figure legends).

### Results (order fixed by the claims, not by what looks best)
1. Design and data (Fig. 2) in two or three sentences.
2. Primary: chain P at g1 (Fig. 4, Table 2), then the learning curves over the grid (estimated), then the ladder.
3. Chain K at g4 (Fig. 5, Table 2): K1, then K2, then the closed forms and stability table, descriptive.
4. Secondary family: Q-H, Q-A10, Q-T; then M3.
5. Descriptive: Test C, S2, storage axis (Fig. 6), residual map (Fig. 7), controls (Table 2, Fig. 8).
Every outcome, including ties and reverse results, gets the same structure: the sentence, the number, the interval, n, the figure.
A negative or tie result is never moved to an appendix or to the end of a paragraph ([STR] G: equal figure size for the failure).
Use run-in headings that mirror the method flowchart so each subsection reads the same way ([STR] C Fig 2).

### Discussion (about 800-1,000 words)
1. What the tested claims mean, one paragraph per chain, in the tier's strength.
2. Mechanism reading: what the soft residual does where there are no data (beyond the window, between conditions), stated as the
   hypothesis the design tests, with the qualifier when Q-H is none.
3. Relation to named prior work, factual and short: Lucu (learning curves), Stroebl (same data, inadequate cycle part, C-rate terms
   not supported; action A8 sentence), PIKAN/PGKAN/KA-CRNN (laws from KANs).
4. Practical reading for test planning, conditional on the outcome ("with this cell type and these laboratories, ...").

### Limitations (own subsection, 250-400 words; confounds first)
Laboratory aliased with temperature; one cell type; Test C cannot separate temperature from laboratory; window cap depends on record
length; the design-effect assumption; local posterior mode for the latent; path dependence and dynamic profiles outside the matrix;
design-hull information available only to the physics-informed arms (E4). One sentence each, each with its consequence. PGKAN Sect. 6
is the length model ([PGK] G).

### Conclusions (about 250-350 words)
Restate the question and the tested answers in the tiers' words, with the headline numbers already given in the abstract (no new
number), then two or three concrete next steps. No "In conclusion, this work demonstrates". Lucu's 220-word conclusion is the length
model ([LA] B).

### Back matter
CRediT statement; Declaration of competing interest; Declaration of generative AI use (Elsevier template sentence, every tool and use);
Data availability (dataset DOI, code and preregistration Zenodo DOI, licence); Acknowledgments without AI.

## 2. Sentence-level patterns

### Tense and voice
- Methods: past tense for what was done ("Each arm was tuned with 40 trials"), present tense for definitions and model structure ("The
  law has one state factor shared by the two rates"). Passive voice is normal in Methods; use "we" for decisions ("we fixed the window
  rule from the test schedule alone").
- Results: past tense for observations ("A1 had a median condition error ..."); present tense for what a display shows ("Fig. 4b shows
  the median relative reduction ...").
- Discussion: present tense for interpretation and for prior work's findings as reported ("Stroebl et al. report that ...").
- First person plural is acceptable and used by the exemplars; keep it to decisions and claims, not narration ("we then ...").

### Hedging (three tiers; one hedge per claim, matched to the evidence)
- Tested and passed: no hedge; the tier verb carries it ("had a median condition error X % lower than").
- Tested and not passed: state the absence plainly ("was not shown more accurate than"; "could not be distinguished").
- Not tested (mechanism, interpretation): one modal ("may", "is consistent with"), never stacked ("may possibly suggest").
- Boosters ("clearly", "strongly", "remarkably") are not used.

### Numbers, intervals, units
- Relative error reduction: X = 100 (1 - exp(-median L)) %, written "X % lower" with "(95 % interval [a, b]; n = 40)". An excess is
  "Y % worse", Y = 100 (exp(median L) - 1) %. Never the form "1 - exp(median L)" (sign slip noted in PREREG_v4 1).
- Simultaneous intervals over the nine grid cells are called "simultaneous 95 % intervals"; the interval of a gated contrast is the
  one the statistics step names. The confirmatory test is "a sign test with a fixed design effect (assumed average pairwise sign
  correlation at most 0.03)", never "exact". Counts as "30 of 40 conditions".
- Percentage points: "pp" defined once ("percentage points (pp)"); retention RMSE in pp to two decimals; relative reductions to whole
  per cent unless the interval needs one decimal. Space before %: "10 %" (the draft's form; be consistent).
- Temperature with a space and the degree sign: "35 °C" (the prose checker flags "35 C"). C-rates without a space: "0.5C", "C/3".
  Time in days (d), throughput in equivalent full cycles (EFC) defined once.
- Italic variables, upright units and labels; "exp" for powers of e; solidus for small fractions (guide, Math formulae).
- Report n with every summary, the unit with every n ("n = 40 held-out conditions").

### Terms (one term per concept; never vary for elegance)
held-out cycling condition (not "unseen condition", "test condition", "new protocol"); check-up (not "RPT", "checkup", "capacity
test"); window (the first k check-ups after the reference); closed-form law (hyphenated before a noun: "the closed-form law"; "in
closed form" otherwise); the dataset authors' semi-empirical model; the best tuned data-driven learner (D*); the same network without
the physics law (A9); equally simplified additive law (G15; defined once as in PREREG_v4 7.3 item 2); storage cells (not "calendar
cells" in prose, "calendar" is the rate); Kolmogorov-Arnold network (KAN) with a hyphen, consistent with the draft; dataset (one
word; the draft's majority form). Physics-informed means a phenomenological rate law; never imply an electrochemical mechanism.

### Abbreviations
Define at first use in the abstract and again at first use in the main text (Elsevier rule): "physics-informed neural network
(PINN)", "Kolmogorov-Arnold network (KAN)", "state of charge (SOC)", "depth of discharge (DoD)", "generalised additive model (GAM)".
Arm codes (A1, A9, A15, G15, D*) are labels, defined in a table of arms and in the first Methods sentence that uses them. Avoid
abbreviations in highlights unless defined there.

### Paragraphs and sentences
One point per paragraph, topic sentence first, evidence next to the claim. Sentences mostly 12-30 words with real variation; none over
40 words (prose-check limit). No bulleted lists in the body except the contribution list. Known-to-new order: start from the quantity
the reader has, end with the new one.

## 3. Phrases to avoid

### AI tells (from `research-humanizer` references/ai-patterns-academic.md sections B-F; the prose checker flags most)
delve, leverage, utilise, harness, foster, facilitate, bolster, underscore, showcase, elucidate, pivotal, crucial, vital, intricate,
multifaceted, nuanced, comprehensive, holistic, seamless, robust (undefined), notable/notably, noteworthy, landscape, realm, paradigm,
tapestry, interplay, myriad, plethora, cutting-edge, state-of-the-art (as praise), groundbreaking, meticulous, paramount, burgeoning;
"it is worth noting that", "it is important to note that", "plays a crucial role", "a wide range of", "serves as", "stands as",
"not only ... but also"; stacked connectives (Moreover, Furthermore, Additionally); rules of three; negative parallelism ("not merely X
but Y"); false ranges; trailing "-ing" clauses that add a vague consequence ("..., highlighting the potential of ..."); rhetorical
questions; "In short," "Put simply,"; closing aphorisms; chat residue of any kind.

### Overclaims and project bans (PREREG_v4 1, 7.3, 7.5, 11; `01_introduction.md` 1.3)
| Never write | Write instead |
|---|---|
| first, novel, for the first time, pioneering | the conjunction sentence, only when condition (d) holds; otherwise state the design |
| significant, statistically significant, p = ... (abstract) | the tier verb with the interval |
| outperforms, superior (below tier S) | the tier's sentence |
| matches, interpretable physics discovered, discovered, recovered, reveals the law | "a closed-form law extracted from the KAN" |
| identified, identifiable, unique, global optimum, robust to initialisation (latent) | "the local posterior mode reached from the prior mode by a converged per-cell Newton method" |
| power law, Arrhenius, hinge, threshold, "no effect" for an extracted cyclic law | the closed form as printed; no named form or direction |
| any temperature direction read from a cyclic law | "temperature (aliased with laboratory; no form or sign reported)" |
| temperature extrapolation, temperature generalisation, untested temperature (Test C) | "held-out temperature-laboratory domain" |
| independent superposition | "a single state-dependent modulation of the sum of a time-driven and a throughput-driven rate" |
| few ageing tests | few cycling tests |
| exact test (for the confirmatory rule) | sign test with a fixed design effect |
| how many tests are needed remains an open question | (do not write; Lucu et al. asked it) |
| excellent, outstanding, impressive accuracy | the number, its interval and n |
| calibration, coverage, well-calibrated intervals | (retired topic; do not write) |

## 4. Model passages for our paper (paraphrased patterns; placeholders only, no results)

These show structure, register and the placement of numbers. They are not text to paste: the abstract and claim sentences must be the
outcome-table strings. Every `[RESULT: ...]` names the field that fills it.

**P1. Abstract skeleton (moves 1-3 and 6; moves 4-5 are the outcome-table strings).**
> Semi-empirical laws of calendar and cycle ageing are fitted to large test matrices, and the stress dependence of their cycle term is
> usually chosen by hand. We trained a physics-informed neural network whose calendar and cycling rates are Kolmogorov-Arnold
> functions of the stress conditions on storage and cycling cells of the Samsung INR21700-50E ageing campaign, and forecast the
> capacity fade of cycling conditions that no training or tuning step saw. Training sets were thinned to 8, 16 and 32 cycling
> conditions and the forecast window to 0, 2 and 4 check-ups per held-out cell. Each forecast was compared, paired by condition (n =
> 40), with the best tuned data-driven learner, the same network without the physics law, the dataset authors' semi-empirical model and
> an equally simplified additive law. [RESULT: outcome-table claim sentence of the reached cell, PREREG_v4 11 4.2, values from
> analysis/contrasts_v4_B.json outcome]. [RESULT: required qualifier sentences, qualifier_sentences]. The results hold for held-out
> cycling conditions of one cell type in three laboratories.

**P2. Highlights (templates; each at most 85 characters once filled; outcome-dependent verbs in brackets).**
> - Physics-informed KAN model forecasts capacity fade of held-out cycling conditions
> - [RESULT: P-chain bullet in the reached tier's verb, with "8 cycling conditions"]
> - [RESULT: K-chain bullet: closed-form law against an equally simplified additive law]
> - Laboratory and temperature are aliased, so no temperature law is reported
> - Learning curves over cycling conditions and check-ups inform ageing test plans

**P3. Introduction, funnel paragraph.**
> Calendar and cycle ageing of lithium-ion cells is usually described by semi-empirical laws in which a time-driven and a
> throughput-driven loss are added and scaled by stress factors [AUTHOR: verified refs]. The stress factors are chosen before fitting,
> and the law is only as good as that choice: for the cell type studied here, the dataset authors report that the cycle part of their
> model is inadequate and that its C-rate terms are not supported by the data [stroebl2026]. A learned stress dependence avoids the
> choice but needs data, and ageing data are expensive: every cycling condition costs cells, channels and months. Lucu et al. measured
> how a Gaussian-process ageing model improves as conditions are added [AUTHOR: Lucu A, B]. Their curves were for a data-driven model
> without a physics law and were validated largely on cells at conditions inside the range of the training conditions.

**P4. Contribution list (D029 order; each item names its test).**
> The study makes three contributions, each tied to a preregistered test.
> 1. A held-out test of a closed-form law extracted from the KAN (A15) against an equally simplified additive law (G15), both obtained
>    with the same frozen library, coefficient cap, selection rule and refit, and both scored on the 40 held-out conditions that the
>    extraction never saw (chain K, Section 5.3).
> 2. A matched ablation ladder in which every tuned comparator receives the same search budget, so that the shares of the physics law
>    and of the KAN can be estimated separately (chain P, test P2, and the ladder of Section 5.2).
> 3. Learning curves over the number of cycling conditions and of check-ups per held-out cell for a joint calendar-plus-cycle law,
>    extending the curves of Lucu et al. [refs] to a physics-informed model and a second axis (chain P, tests P1 and P3).

**P5. Methods, comparator fairness.**
> Every tuned arm received the same 40 trials of a tree-structured Parzen estimator inside the training conditions of each outer fold,
> with inner folds grouped by condition and stratified by temperature ([RESULT: inner folds for m = 8 and 16, two or four as fixed by runs/pilot_P6b/decision.json]; three for m = 32). The
> data-driven bar D* is the arm with the lowest inner-cross-validation score among the same network without the law (A9), a Gaussian
> process with automatic relevance determination (A11) and gradient-boosted trees (A12); it is chosen per fold and per m and is not the
> learner that scores best on the held-out conditions. Parameter counts, the number of training rows used and fit times are listed in
> Table 1.

**P6. Methods, the test.**
> For a target arm T and a comparator C, the per-condition log ratio L_c = ln(S_C,c / S_T,c) is positive when T has the lower error. A
> claim at tier S requires the median of L_c to exceed ln 1.02, and at tier N to exceed -ln 1.10. Each node is tested with a sign test
> with a fixed design effect (assumed average pairwise sign correlation at most 0.03), because conditions in one outer fold share fitted
> models; the nodes form a sequentially rejective graph with a family-wise error rate of 0.025, one-sided. The plain sign test, which
> assumes independent conditions, is reported beside every contrast as a descriptive row and changes no tier.

**P7. Results, chain P at g1 (all values are placeholders).**
> With eight cycling conditions and two check-ups per held-out cell, [RESULT: claim sentence of the P state, outcome.p_sentence]
> (Fig. 4b, Table 2). [RESULT: positives of 40 and plain-test row, effective_tiers.P1]. The same network without the physics law
> [RESULT: P2 sentence in its tier, or extent clause e3] , and [RESULT: P3 sentence or "a dependence of the advantage on the number of
> cycling conditions was not shown"]. Across the other grid cells, which carry no test, the median reduction against D* ranged from
> [RESULT: min rel_reduction_pct] to [RESULT: max] % (simultaneous 95 % intervals in Fig. 4b). [RESULT: mean-vs-median sentence, only if
> rule 9.8.1 fires, with the mean pp difference, its BCa interval and the worst-condition error].

**P8. Results, chain K at g4.**
> At full data the closed-form law extracted from the KAN [RESULT: K1 sentence: "predicted held-out conditions no more than 10 % worse
> than the full network" or the K1-fail clause] and [RESULT: K2 sentence in its tier] (Fig. 5h, Table 2). The extracted law has
> [RESULT: law_summary.arms.A15.n_coefs] coefficients and the additive law [RESULT: law_summary.arms.G15.n_coefs]; their training-side
> BIC values are [RESULT: train_bic, both]. Readable means that the extracted law is a short closed form that can be written out and
> evaluated; we name no form or direction for its individual effects, because the training design aliases laboratory with temperature
> and the extraction has no laboratory term. The stability panel (Fig. 5i) is descriptive and is not evidence that the design
> identifies these forms.

**P9. Results, a tie reported at full weight (Q-H at "none").**
> The soft residual was not shown necessary relative to exact integration of the same law: at g1 the physics-informed network and the
> hard-integrated law could not be distinguished ([RESULT: QH_g1 interval]; n = 40), and at g4 [RESULT: QH_g4 sentence in its tier].
> Fig. 7 shows where the residual is large; it is descriptive and carries no claim.

**P10. Discussion and limitation, C-rate and confounding.**
> The learned cycling map [RESULT: describe only what Fig. 5 shows for C_ch and C_dch, inside the training hull, in the words "the
> partial dependence rises / falls / stays within its envelope"], which can be set beside the dataset authors' report that the C-rate
> terms of their parametric model were not supported on these cells [stroebl2026]. Neither result establishes a C-rate effect: our
> design tests the forecast of whole conditions, not the contribution of any one stress factor. A further limit applies to every
> temperature statement. At 35 °C all cycling conditions come from one laboratory and at 45 °C most do, so temperature and laboratory
> cannot be separated, and we report no temperature form or sign for the cycling law.

## 5. Final checks before a section is returned

1. Every number has a `src` comment or a `[RESULT: ...]` placeholder; no number appears in two places with different rounding.
2. Every claim verb matches its tier; every estimated contrast is free of tier words.
3. Grep for the banned words of section 3 (case-insensitive, word boundaries) returns nothing outside quotations.
4. Terms of section 2 used one way throughout; abbreviations defined in the abstract and again in the body.
5. `research-humanizer` pass, hidden-unicode scan and `tools/prose_check.py` as in `.claude/agents/jes-research-writer.md`.
6. Highlights counted at 85 characters or fewer; abstract at 250 words or fewer.

**[PENDING: Najera 2023, Naumann 2018, Olmos 2021]** may change how laws are reported in prose (parameter tables in physical units,
residual sentences). **[PENDING: Zhang 2026 TS-PINN]** may change the Results ordering norm for PINN papers.
