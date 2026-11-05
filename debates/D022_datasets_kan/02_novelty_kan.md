# D022 (KAN part), novelty audit (2026-11-05)

Auditor: novelty-auditor (checks only; no rescue suggestions). Read first: `research/CONTRACT.md`, `debates/D022_datasets_kan/01_proposal_kan.md`, `debates/D016_roles/03_novelty_recheck.md` (not redone; its battery rows are relied on).

Tags. Reading: **FT-partial** = HTML version fetched through the fetch tool's summariser with targeted questions (it returns an answer to my prompt, not the raw text; for several papers only the first ~100k of ~110-165k characters were covered, stated per row); **AB** = abstract/landing page only. Citation status: **V** = DOI resolved on Crossref this session; **V-arXiv** = id, title and authors resolved on the arXiv abs page this session; **unverified** = not resolved. No paper was read in full by me, so every S/P/D cell below can move.

## 0. Candidates restated (falsifiable)

- (a) Monotone KAN stress edges: in a PINN ageing law whose stress map is a KAN, edges for inputs with a physical sign (T, DoD, C_ch) are monotone by construction, and this changes held-out error or what the edge can absorb (laboratory offset on temperature). Prior-art question: is a sign-constrained KAN, and its use in battery degradation, already published?
- (b) Physics-typed edge bases: edges use a basis tied to the physics (Arrhenius abscissa, power laws), so the extracted law is exact.
- (c) Library-aware training: a penalty on the distance of each edge from its best fit in a small symbolic library, so extraction loses little.
- (e) Identifiability-audited extraction: per extracted edge, a table of training levels, identifiable shape parameters, BIC margin, calibrated false-structure rate, and a "readable" label only where the design identifies the form; no change to any scored arm.

## 1. Verdicts

| Candidate | Verdict (method / battery ageing) | Conf. | Closest 3 verified papers | Reads as a methodological contribution in JES? |
|---|---|---|---|---|
| (a) monotone KAN edges | method **TAKEN**; as application to battery stress law **INCREMENTAL** | 0.75 | MonoKAN (Polo-Molina et al., Neural Netw. 196, 2026); Krasnov et al., arXiv 2606.17886 (MKAN); Tan et al. (TIDE), arXiv 2607.14640 (battery, monotone residual, KAN) | No. A reviewer reads it as applying a known constraint (MonoKAN supports partial monotonicity in chosen inputs). Only the lab-confound argument is new, and it is an argument, not a method. |
| (b) physics-typed edge bases | **TAKEN** (idea), **TAKEN** (Arrhenius abscissa in battery KAN laws) | 0.80 | Bagrow and Bongard, S2KAN, arXiv 2512.07875 (symbolic/Chebyshev/Fourier dictionary inside the activation); Koenig and Deng, JES 158, 121853 (KAN in Arrhenius law; D016); Chen et al., PiDDM, arXiv 2607.29095 (Arrhenius kinetics in the objective) | No. The proposal already says "not a contribution"; the audit agrees. |
| (c) library-aware training | concept **TAKEN**; the specific "distance to best library fit on the extraction grid" penalty **INCREMENTAL**; in battery ageing no prior found | 0.65 | S2KAN (differentiable gated library in training, MDL/BIC regulariser, fidelity metric); Faroughi et al., Symbolic-KAN, arXiv 2603.23854 (library of primitives, hierarchical gating, symbolic regulariser); Sovrano et al., arXiv 2603.15250 (GSR/GMP, end-to-end selection instead of per-edge snapping) | Weakly. The idea is the core of two 2025-2026 KAN papers; only a battery application with a matched GAM, plus a small accuracy gain (0.0055 of range, synthetic), remains. |
| (e) identifiability-audited extraction protocol | **NOVEL (narrow)**; built from known ingredients | 0.55 | Sovrano et al. 2603.15250 (per-edge extraction instability, equivalent operators on a bounded domain discussed qualitatively, Sec. 3 and 8); Raue et al., Bioinformatics 2009 (structural/practical identifiability by profile likelihood; ODE parameters, not KAN edges); Gasper et al., J. Electrochem. Soc. 2021 (statistical validation of algebraic battery life models) | Yes, conditionally. It is a validation/reporting protocol, not an architecture. It reads as methodological if the calibrated false-structure table is shown and the label discipline changes what the paper claims; otherwise as bookkeeping (the proposal's own warning). |

**Single paper most likely cited against us.** For (a), (b), (c) together and for the KAN part as a whole: Sovrano, Losavio, Vilone, Langheinrich, *In-Context Symbolic Regression for Robustness-Improved Kolmogorov-Arnold Networks*, arXiv 2603.15250 (V-arXiv; XAI'2026). It states that per-edge symbolic snapping is sensitive to initialisation and that equivalent operators cannot be told apart on a bounded domain, and it replaces snapping by end-to-end selection. A reviewer will say the post hoc weakness is known and that training toward a library (S2KAN) already addresses it. For (e) alone: the same paper plus Raue et al. For the battery side of (a): TIDE (arXiv 2607.14640).

## 2. Evidence

### 2.1 Query log (WebSearch unless stated; 2026-11-05; US-only search engine, no date filter available)
1. MonoKAN certified monotonic Kolmogorov-Arnold network cubic Hermite splines
2. monotonic Kolmogorov-Arnold network shape-constrained convex KAN arXiv
3. Kolmogorov-Arnold network battery degradation monotonic constraint physics-informed SOH
4. KAN symbolic regression extraction stability identifiability audit symbolic library fidelity
5. Kolmogorov-Arnold network lithium-ion battery capacity fade degradation law interpretable stress factors temperature C-rate KAN
6. physics-informed KAN battery aging calendar cycle Arrhenius learnable functions arXiv 2026
7. identifiability symbolic regression battery degradation model structural identifiability neural network extracted equation
8. monotone neural network battery degradation temperature C-rate monotonic lattice constrained capacity fade prediction
9. Hallinger identifiability reduced experimental effort mechanistic calendar aging models a priori identifiability (title not found)
10. monotone constrained neural additive model Kolmogorov-Arnold physical sign constraints scientific application interpretable 2025 2026
11. KAN symbolic regression versus generalized additive model GAM held-out comparison interpretable equations
12. KAN physics-informed neural network lithium-ion battery PIKAN state of health Kolmogorov-Arnold PINN
13. KAN activation physics-based basis functions instead of B-splines domain-specific basis Kolmogorov-Arnold physical law priors
14. equation learner SINDy identifiability library collinearity audit which terms identifiable from design of data stability selection
15. Kolmogorov-Arnold network false positive symbolic formula recovery edge identifiability limited levels input design KAN interpretability reliability
16. "Kolmogorov-Arnold" battery calendar ageing OR "capacity fade" Arrhenius KAN physics-informed 2026 Journal of Energy Storage
17. monotonicity-constrained neural network battery aging model temperature DoD sign constraint physically consistent degradation rate
18. KAN library-aware training symbolic regularization quantization-aware snapping penalty distance to symbolic function end-to-end
19. ICLR 2027 OR NeurIPS 2026 submission Kolmogorov-Arnold network monotone symbolic extraction identifiability OpenReview
20. Gasper Smith bilevel optimization symbolic regression battery life model identification stress factors penalized regression
21. Samsung INR21700-50E Stroebl calendar cycle ageing dataset neural network KAN physics-informed 2026
Fetches: arXiv abs pages 2409.11078, 2606.17886, 2512.07875, 2603.15250, 2603.23854, 2503.05617, 2607.14640, 2604.13873, 2604.00400, 2604.01229, 2607.29095, 2605.09696, 2504.03913, 1610.02995, 0809.2932, 1006.3316 (unrelated, discarded); HTML full-page fetches of 2512.07875v2, 2409.11078v2, 2603.15250v2, 2606.17886v3, 2607.14640v2; Crossref for 10.1016/j.neunet.2025.108278, 10.1016/j.cma.2025.118089, 10.1093/bioinformatics/btp358, 10.1007/s11222-013-9448-7, 10.1149/1945-7111/abdde1, 10.1073/pnas.1517384113. Crossref returned HTTP 429 for 10.1111/j.1467-9868.2010.00740.x (Meinshausen and Buhlmann) once; resolved instead by arXiv id.

About 70 distinct hits screened by title/snippet; 20 abstracts read; 5 papers read through targeted HTML questions (FT-partial). OpenReview and arXiv listing pages were not browsed.

### 2.2 Verified identifiers

| Work | Identifier | Status |
|---|---|---|
| Polo-Molina, Alfaya, Portela, MonoKAN, Neural Networks 196 (2026) | 10.1016/j.neunet.2025.108278; arXiv 2409.11078 (v1 17 Sep 2024, v2 21 Nov 2025) | V; V-arXiv |
| Krasnov, Bertalanic, Fortuna, Monotonic KANs (MKAN) | arXiv 2606.17886 (v1 16 Jun 2026, v3 5 Sep 2026) | V-arXiv |
| Thakolkaran et al., Input-convex KANs, CMAME 443 (2025) 118089 | 10.1016/j.cma.2025.118089; arXiv 2503.05617 | V |
| Bagrow and Bongard, Softly Symbolifying KANs (S2KAN) | arXiv 2512.07875 (v1 27 Nov 2025, v2 22 Oct 2026) | V-arXiv |
| Faroughi, Mostajeran, Arzani, Faroughi, Symbolic-KAN | arXiv 2603.23854 (25 Mar 2026) | V-arXiv |
| Sovrano, Losavio, Vilone, Langheinrich, In-Context Symbolic Regression for KANs | arXiv 2603.15250 (v1 16 Mar 2026, v2 18 Apr 2026; accepted XAI'2026 per abs page) | V-arXiv |
| Tan et al., TIDE, WI-IAT 2026 | arXiv 2607.14640 (16 Jul 2026, v2 9 Sep 2026) | V-arXiv |
| Ghosh and Roy, Explainable functional relation discovery for SoH using KAN | arXiv 2604.00400 (1 Apr 2026, v2 16 Aug 2026) | V-arXiv (already in D016) |
| Chen et al., PiDDM | arXiv 2607.29095 (31 Jul 2026) | V-arXiv (already in D010/D016) |
| Panczyk, Erdem, Radaideh, Opening the Black-Box (KAN symbolic, energy) | arXiv 2504.03913 | V-arXiv |
| Basiri and Nicholson, AutoSINDy | arXiv 2605.09696 (10 May 2026, v2 30 Oct 2026) | V-arXiv |
| Raue et al., Bioinformatics 2009 (profile-likelihood identifiability) | 10.1093/bioinformatics/btp358 | V |
| Pya and Wood, Shape constrained additive models, Stat. Comput. (2014 online, 2015 print) | 10.1007/s11222-013-9448-7 | V |
| Gasper, Gering, Dufek, Smith, J. Electrochem. Soc. (2021) | 10.1149/1945-7111/abdde1 | V |
| Brunton, Proctor, Kutz, SINDy, PNAS (2016) | 10.1073/pnas.1517384113 | V |
| Martius and Lampert, Extrapolation and learning equations | arXiv 1610.02995 | V-arXiv |
| Meinshausen and Buhlmann, Stability selection | arXiv 0809.2932 | V-arXiv (Crossref DOI not resolved: HTTP 429) |
| Koenig and Deng JES 158, 121853; Zhao et al. JES 182, 124768 (PGKAN); Stroebl et al. Sci. Data 11, 1020; Gasper et al. J. Electrochem. Soc. 169, 080518 | per D016 section 4 | V in D016, not re-resolved here |

**Not verified, do not cite:** Sill 1997 (monotonic networks) and Gupta et al., JMLR 2016 (lattice regression), named in the proposal from memory; the E-SINDy paper (Fasel et al.) and arXiv 2507.11739 / 2410.18268, which came only from a search summary; the 2022 and 2020 NREL/INL conference items; Hallinger et al. (SSRN 7417281) title not found again. "SOH-KPINN", "PIKAN", "KA-CRNN" are on file from earlier work and were not re-checked here.

### 2.3 Difference matrix (S same, P partial, D different, against the candidate named in the row header)

**(a) Monotone KAN stress edges for battery ageing** (Q = sign-constrained KAN edges; Mech = per-input sign constraint inside a physics-structured law; Meth = architecture; Ev = held-out battery conditions; Scale; Res)

| # | Work (depth) | Q | Mech | Meth | Ev | Scale | Res |
|---|---|---|---|---|---|---|---|
| 1 | MonoKAN, 2409.11078 (FT-partial: Sec. 3.1-3.4, first 100k of 124k chars) | S | P (generic monotone inputs; partial monotonicity defined in Sec. 3.1; no physics law) | S (cubic Hermite, positive weights, clamping/projection after each step) | D (tabular: ESL, COMPAS, Blog Feedback, Loan, Auto MPG, Heart) | D | P (beats monotone MLPs on most tabular benchmarks) |
| 2 | MKAN, 2606.17886 (FT-partial, first 100k of 118k) | S | D (every edge monotone; partial monotonicity per-edge masks listed as future work, Sec. 6) | S (exp reparametrisation of B-spline coefficients, positive weights; hard guarantee for all parameter values) | D (SMM/ICML-2024 benchmark, Dry Bean, MAGIC, MNIST, synthetic) | D | D |
| 3 | ICKAN, 2503.05617 / CMAME 443 (AB) | S (monotone and convex spline activations) | S (physical admissibility imposed by sign/convexity on KAN edges; physics-typed use) | S | D (hyperelasticity) | D | D |
| 4 | TIDE, 2607.14640 (FT-partial: Sec. II-C, III-A, III-B5) | P (monotone component beside a KAN residual) | P (monotone w.r.t. cycle index and internal resistance, not operating stresses; contextual MultKAN branch is unconstrained) | P (softplus non-negative-weight monotone block, not a KAN edge) | P (MIT-Stanford fast charge, 140 cells, battery-disjoint split) | P | D (SOH estimation) |
| 5 | Pya and Wood, SCAM (AB; title/authors V) | S (shape-constrained additive terms) | S (additive terms with monotone/convex splines) | D (GAM, not KAN) | D | D | D |

Not found: any battery ageing paper that imposes a sign on dependence on T, DoD or C-rate in a learned rate map (query 8, 17 returned only monotone-in-cycle penalties: arXiv 2607.16864, 2603.10527, 2604.01229, PiDDM, PID-Net, plus an input-convex network for V2G fade, arXiv 2505.11047, snippet only). Absence is weak evidence.

**(b)/(c) Physics-typed bases and library-aware training**

| # | Work (depth) | Q | Mech | Meth | Ev | Scale | Res |
|---|---|---|---|---|---|---|---|
| 1 | S2KAN, 2512.07875 (FT-partial: Sec. 3-5, first 100k of 165k) | S (symbolic dictionary inside training; "symbolic fidelity" SF metric) | S for (c) (gates over symbolic library S, sparse bases F, dense spline R; Hard Concrete gates; MDL/BIC-style penalty, Eq. 16-17); P for (b) (primitives chosen by the user, not typed by physics) | S | D (airfoil, concrete, power plant, superconductor, Nguyen, dynamics; no battery) | D | P (higher fidelity, smaller models, competitive error; no GAM comparison found; no false-structure study found; no monotone constraint) |
| 2 | Symbolic-KAN, 2603.23854 (AB) | S | S for (c) (library of analytic primitives, hierarchical gating, symbolic regulariser to one-hot) | S | D (regression, inverse dynamics, PDEs) | D | D (recovery claimed empirically) |
| 3 | Sovrano et al., 2603.15250 (FT-partial: Sec. 3, 5, 6, 8, first 100k of 108k) | P (extraction stability and robustness of KANs; end-to-end operator choice) | P (greedy end-to-end replacement; gated matching pursuit) | S/P | D (benchmark functions; OFAT sweeps of width, lambda, pruning; seeds in Table 1) | D | P (up to 99.8 % lower median OFAT test MSE; no precision/recall or false-positive rate; no analysis of input levels or range) |
| 4 | Koenig and Deng, JES 158, 121853 (per D016, AB) | D | P (KAN of SOC inside Arrhenius kinetics; Arrhenius coefficients already in the architecture) | S | D (thermal abuse DSC) | D | D |
| 5 | PiDDM, 2607.29095 (AB) | D | P (Arrhenius SEI/inventory-loss kinetics in the loss) | D | P (55 cells, 6 protocols) | P | D |
| 6 | Ghosh and Roy, 2604.00400 (AB) | P (KAN closed form for SoH) | P (physics-guided loss, cycle number and temperature) | S | P (one cell family) | D | D |

Not found: a KAN-edge penalty that measures distance to the best library fit on the extraction grid and is applied to a matched GAM parent (query 18 returned only QuantKAN/KANHard quantisation papers, not symbolic). Weak evidence. The "library projection residual" is a variant of S2KAN's idea; the audit cannot say whether the variant is better.

**(e) Identifiability-audited extraction**

| # | Work (depth) | Q | Mech | Meth | Ev | Scale | Res |
|---|---|---|---|---|---|---|---|
| 1 | Sovrano et al. 2603.15250 (FT-partial) | P (extraction reliability) | P (notes equivalent operators under affine reparametrisation on a shared domain, Sec. 3; says correct recovery is not uniquely defined without an equivalence protocol, Sec. 8; offers no protocol) | D (stability by seeds/OFAT; no per-edge audit table) | D | D | D (no false-structure rate; no analysis of the number of input levels) |
| 2 | Raue et al., Bioinformatics 2009 (V; AB) | P (identifiability of what the data can determine) | S in spirit (structural vs practical identifiability) | D (profile likelihood on ODE parameters) | D (systems biology) | D | D |
| 3 | S2KAN 2512.07875 (FT-partial) | P (SF metric = expressibility in a declared language, not identifiability) | D | D | D | D | D (no identifiability or false-positive study found in the 100k characters read) |
| 4 | Gasper et al., J. Electrochem. Soc. 2021, 10.1149/1945-7111/abdde1 (AB via search summary; D016 row for the 2022 companion) | P (statistical validation of identified algebraic battery life models; bootstrap uncertainty) | P | D (penalized regression/bilevel, no KAN) | S (battery life models) | P | D |
| 5 | TIDE (FT-partial) | D | D (no identifiability or stability check, single values without spread, Sec. III-B5) | D | P | P | D |
| 6 | AutoSINDy 2605.09696 (AB) | P (library curation by collinearity analysis) | P (collinearity of candidate terms, structural side of identifiability) | D (PySR + weak-form SINDy, no KAN) | D | D | D |
| 7 | Stability selection, Meinshausen and Buhlmann, arXiv 0809.2932 (AB) | P (selection frequency as reliability) | P | D | D | D | D |

Not found: a per-edge table of the form (training levels, identifiable parameters, BIC margin, calibrated false-structure rate) for KAN edges or any symbolic extraction, in battery work or in SINDy/EQL work. Searches 4, 7, 14, 15 each returned only pieces (instability, collinearity pruning, stability selection, symbolic fidelity). One concrete risk: the proposal's key quantities (137 of 400 random 3-level data sets exactly fitted by at least three different 3-coefficient forms; false structure 92-94 % at cap 3) are, to my search, not stated in any of the above, but "number of levels bounds identifiable parameters" is a textbook statement (counting argument), so the novelty of (e) lies in the calibrated table and the label discipline, not in the principle.

### 2.4 Related items judged not to change a verdict
- Ghosh and Roy 2604.00400: closed form SoH vs cycle number with temperature data; no monotone sign inputs, no audit (AB).
- Panczyk et al. 2504.03913: KAN symbolic equations for nuclear data; no GAM, no audit (AB).
- arXiv 2604.13873 (EML operator for RC models): withdrawn, irrelevant.
- GAM comparator: no paper found that compares a KAN-extracted closed form with a GAM on held-out data (queries 11, 10); D016 already holds this as NOVEL (0.60). Not re-weighed.

### 2.5 Last 90 days (about 2026-08-07 to 2026-11-05)
Papers with a revision date in the window: S2KAN v2 (22 Oct 2026), AutoSINDy v2 (30 Oct 2026), MKAN v3 (5 Sep 2026), TIDE v2 (9 Sep 2026). First submissions in the window relevant to the claim: none found. S2KAN v2 was not compared with v1: if the revision added a monotone constraint, a battery example or an identifiability analysis, this audit would not know (only 100k of 165k characters of v2 were read, and App. A was truncated). OpenReview and the arXiv listing pages were not browsed; ICLR 2027 and NeurIPS 2026 submissions could not be enumerated (query 19 returned no matching submission, which is weak evidence).

## 3. Residual risk
- Reading depth: no paper was read by me directly in full; the fetch tool answers my prompts from the page text and I cannot audit the answers. Statements like "no identifiability analysis in S2KAN" cover only the characters fetched.
- Searches ran on a US-only engine with no date filter; battery-specific Chinese-language and Elsevier-paywalled JES 2026 papers (the likely home of a competing "KAN + monotone + battery" paper) are poorly indexed. A JES paper with a monotone or sign-constrained KAN in an ageing law cannot be excluded.
- The 2026 KAN literature is moving quickly: three relevant preprints (S2KAN, Symbolic-KAN, MKAN) appeared in the last 12 months, and MKAN names partial monotonicity and identifiability under monotone data as future work, so a follow-up may appear before submission. A repeat check within 7 days of submission is needed.
- Verdicts for (e) rest on absence of results (weak evidence) plus the observation that every ingredient is known.
- Unverified names listed in section 2.2 must not be cited.

## 4. Ledger
No ledger name was given in the brief; no rows added. Nothing committed.
