# Deep dissection: Richardson, Osborne, Howey 2019, JES 23, 320-328
"Battery health prediction under generalized conditions using a Gaussian process transition model", doi 10.1016/j.est.2019.03.022. CC-BY (Crossref `vor` licence, start 2019-03-26). Crossref 2026-11: 220 citations, 34 references, pages 320-328 (9 pages).

## Source and reliability (read first)
- **Text used: arXiv:1807.06350v1 (17 Jul 2018, submitted version, 10 pp, `stat.AP`)**, saved as `refs/fulltext/ft_richardson2019_JES23_320_ARXIV_V1.txt` (PyMuPDF dump; PDF in `refs/pdf/jes_exemplars/richardson2019_arxiv.pdf`). It is the only version I could read. arXiv has no v2; the arXiv record carries the JES DOI.
- **Version of record text NOT obtained.** ScienceDirect returns Cloudflare 403 ("Just a moment") to curl and to the Playwright browser; Semantic Scholar/OpenAlex list only the publisher page and the arXiv copy. I did not attempt to bypass the challenge. If we need the VoR wording (abstract, highlights, any added experiments), Shlok can save the CC-BY PDF from the publisher page into `refs/pdf/`.
- **VoR figures were fetched from the public CDN** (`ars.els-cdn.com/content/image/1-s2.0-S2352152X18307734-gr{1..6}_lrg.jpg`, saved in `refs/figs/richardson2019/gr1..gr6.jpg`) and viewed. The VoR has the same six figures as arXiv v1 and Figures 1-6 match in content (schematic, raw/feature examples, input densities, capacity by group, parity, test-cell trajectories). So the experimental design in this note is very likely the VoR design, but section numbers, word counts, the reference count (28 in arXiv v1 vs 34 in Crossref) and any wording are from the preprint and may differ in the VoR. Every number below is from arXiv v1 Table 4 unless marked.
- Claims below are "the paper reports X" (E2), not "X is true".

## (A) Contribution as stated; contribution-list pattern
- Stated idea: learn a **transition model** that maps what happened to a cell between two capacity checks (a "load pattern": current, voltage and temperature time series reduced to a fixed-length feature vector) to the capacity change over that interval, using a Gaussian process (GP); integrate the predicted changes along an arbitrary future input sequence to get a capacity trajectory with credible intervals (Abstract; Sec. 1 last paragraph; Sec. 2.1).
- Second claimed innovation: the feature-selection step mapping arbitrary-length I, V, T vectors to fixed-size features (Abstract; Highlights bullet 3).
- Headline result: best case normalised RMSE 4.3 % on 26 NASA randomised-usage cells, half train / half validation (Abstract).
- Pattern: **no numbered contribution list.** One framing sentence in the last paragraph of the Introduction (the authors introduce a Bayesian non-parametric transition model for battery health), five Highlights bullets (method, outputs with uncertainty, feature mapping, dataset of 26 cells, 4.3 %), and an Abstract with one number. The Conclusions paraphrase the claim as one of the first quantified accuracy assessments and one of the most accurate long-range capacity predictions to date (Sec. 6). That comparison is asserted, not tested: no other method's number appears anywhere in the paper.
- One short quote (11 words) from Sec. 6, kept for the record: "one of the most accurate long range predictions of future capacity seen to date".

## (B) Structure (arXiv v1; words are approximate, from the PyMuPDF dump)
| Part | ~words | Content |
|---|---|---|
| Abstract + keywords + 5 highlights | 300 | one number (4.3 %) |
| 1 Introduction | 1,200 | parametric stress-factor models (Schimpe Eq. 1-2), first-principles models, data-driven GP/SVM, gap; ends with the single framing sentence |
| 2 Method (2.1 transition model, 2.2 input features, 2.3 example data, 2.4 evaluation, 2.5 GP, 2.6 gradient boosting) | 2,400 | Eqs. 3-14; Table 1 (input format) |
| 3 Dataset | 600 | NASA randomised battery usage; Tables 2-3 |
| 4 Results | 550 | six model configurations; Table 4; Figs 4-6 |
| 5 Discussion | 600 | feature choice, kernel, calibration, split caveat |
| 6 Conclusions | 630 | claims, next steps (3), acknowledgments |
- Whole main text about 6,400 words (arXiv); 6 figures, 4 tables, 14 numbered equations; 28 references in arXiv v1 (34 in Crossref for the VoR); 9 journal pages.
- Short paper, short Results (550 words): the weight is on method description (2,400 words), not on results.

## (C) Figures (VoR gr1-gr6 viewed; arXiv v1 vector versions used for caption text)
| Fig | Form | Panels / encodings | Claim supported | Quality | What we would do better |
|---|---|---|---|---|---|
| 1 | Schematic with real signal traces | Top: capacity staircase Q1..Q5 with y_i = dQ arrows; below V(t), I(t), T(t) traces; dashed verticals delimit load patterns u1..u4 | Defines the unit of prediction (interval between check-ups) | Very good: the definition is visible in one picture, data are real | Our Fig 1 should attach real storage, cycling and held-out panels to the network boxes (BLUEPRINT row 1); show check-up spacing explicitly because our learning curves vary it |
| 2 | 2 cells x 6 panels | Left: raw V, I, T for cells 9 (random) and 19 (skewed-current); right: extracted Q [%], throughput per interval, time with T > 35 C | Features differ by cell and encode usage | Good; shows a feature (time above 35 C) that **never appears in Table 4** | We would not show features the models do not use |
| 3 | 5 kernel-density panels | dt, charge throughput, I, V, T densities over all cells | Dataset covers a wide input range | Fine but a summary of marginals only, no joint coverage and no train/test overlay | Show the stress-condition design as a joint map (T x SOC; T x DoD x C-rate) with held-out conditions highlighted |
| 4 | 7 line panels, capacity vs day per group | 3-4 cells per group, coloured by cell | Within-group replicates are similar; groups differ | Good; reveals that replicate cells overlap closely (groups 2, 4, 5) | Same, plus mark which cells are train vs test (not done here) |
| 5 | 3x2 parity grid of predicted vs actual dQ | one panel per model, 7 group colours, grey +-2 sigma bars, red 45-degree line | Model 1 (GP-Matern, 6 lags) tracks dQ best | Honest: predicted dQ occupies a much narrower range than actual dQ (visible compression) and bars are wide; ideal for exposing weak interval skill | Add a per-unit error number and a baseline panel; show pooled R2 only with condition-level spread |
| 6 | 13 small multiples (one per test cell) | black true capacity, blue dashed predicted mean with markers, blue +-2 sigma band; panel titles coloured by group | Trajectory and calibration hold on each held-out cell | Best figure in the paper. Shows failures (cells 9, 11 mid-life, 13, 21 end-of-life) and wide bands (cell 25) | Our Fig 3 equivalent: rows = temperature with held-out condition boxed, one line per model (at most 3), seed band, training window shaded, per-panel error printed |

## (D) Tables
| Table | Content | Note |
|---|---|---|
| 1 | Example input vector for one load pattern (explicitly "arbitrary values for explanatory purposes") | Explanatory only |
| 2 | Dataset overview: LG Chem 18650, LCO vs graphite, 26 cells, 950 Q samples, Q range 2.10 to 0.80 Ah, 7 regimes | Good habit: one table that fixes the dataset |
| 3 | The 7 load profiles (groups of 3-4 cells; 5 at room temperature, 2 at 40 C) | Needed to understand the split |
| 4 | Six model configurations x metrics (RMSE dQ, CS 2-sigma on dQ; RMSE Q, RMSE-norm, CS on Q), best in bold | Model 1: RMSE dQ 0.0201 Ah, CS 0.959, RMSE Q 0.070 Ah, RMSE-norm 0.043, CS 0.967. Model 2 (1 lag + t): 0.0236 / 0.950 / 0.116 / 0.086 / 0.922. Linear-kernel GPs 3, 4: RMSE-norm 0.173, 0.593; CS 0.839, 0.241. Gradient boosting 5, 6: RMSE-norm 0.067, 0.106; CS 0.846, 0.757 |
- No table has a spread, a seed count or a per-cell breakdown.

## (E) Evaluation: what "generalized conditions" means and how it is held out
- **"Generalized" refers to arbitrary input sequences, not to held-out conditions.** The test cells are the odd-numbered cells (1, 3, 5, 7, 9, 11, 13, 15, 19, 21, 23, 25, 27; Fig 6); training uses the even-numbered cells (13 vs 13; cells 16, 17 dropped as spurious; Sec. 3). Both halves contain cells from **all seven groups**.
- Sec. 5 explains why: the even/odd split guarantees at least one training cell in every one of the 7 groups; the authors expect worse results if the first N cells were used for training because the model would then extrapolate outside the training input space; they say large coverage of input conditions is needed. So the paper itself reports that held-out condition performance was not tested and may be poorer.
- The test cell therefore has same-protocol replicate cells in training (Fig 4: groups 2, 4, 5 replicates nearly overlap). This is cell-level, not condition-level, holdout (my inference, E3).
- Prediction mode: roll the learned dQ forward from the measured initial capacity along the (known) future inputs (Sec. 2.1, Sec. 6: the model assumes the future inputs are known exactly).
- Baselines: GP with linear kernel (Bayesian linear regression), scikit-learn gradient boosting with quantile regression (SKGB); input variants (1 vs 6 lags, with or without absolute time). **No parametric semi-empirical baseline, although the Introduction builds its motivation on Schimpe's Eq. 1-2**, and no trivial baseline (per-time mean slope or persistence of last rate).
- Metrics: RMSE of dQ, RMSE of Q, normalised RMSE of Q (Eq. 5), calibration score CS_2sigma = fraction of test points inside +-2 sigma (Eq. 6, target 0.954).
- Uncertainty/statistics: **none beyond one split.** One train/test partition, one run per configuration, no confidence interval on RMSE, no per-cell or per-group error, no significance test. The six configurations were all scored on the test cells and the best was reported ("best case"); there is no validation split mentioned (E2: absence in the text I read).
- Comparisons confounded: Model 1 (GP, 6 lags, no t) vs Model 5 (SKGB, 6 lags, with t) differ in learner **and** in whether t is included, so the GP-vs-boosting gap (4.3 % vs 6.7 %) is not a clean contrast. The design is not a full factorial.

## (F) Novelty framing moves
1. Name the unit ("load pattern") and the idea ("transition model"): a reusable noun that later papers cite (220 citations is, in my reading, mostly this).
2. Position against two families only: "parametric/empirical stress-factor models" (fixed form, decoupled inputs, no regime change) and "first-principles" (parametrisation hard), then the data-driven GP as the third way.
3. Use Bayesian uncertainty as a differentiator and give it a metric (CS) next to RMSE.
4. Public data (NASA randomised usage) so anyone can re-run.
5. Honest limitation about feature use, inputs and dataset size stated up front in Conclusions.

## (G) Limitations (stated and unstated)
- Stated (Sec. 6): need a much larger dataset; no parametric prior mean yet; future inputs assumed known; automated feature selection left to future work; training set must cover the input range.
- Unstated: (i) feature innovation untested: Table 4 uses only dt, throughput and absolute time; the temperature/current-range histogram features of Sec. 2.2 and Table 1 are never evaluated; (ii) test-set model selection; (iii) one split, no spread; (iv) replicate leakage across train/test; (v) the Q-RMSE is dominated by the monotone trend, so a trivial baseline may score well (not tested, my hypothesis); (vi) no cross-chemistry or cross-temperature holdout although groups 6-7 are the only 40 C regimes (and both appear in training).

## (H) Data / code
- Data: NASA Ames PCoE randomised battery usage repository (public; cited as ref [27]); cells 16, 17 excluded.
- Code: GPy and scikit-learn named; **no code or repository link** in the arXiv v1 text (grep for github/zenodo/code availability found nothing). VoR statement unknown.

## (I) Hostile-reviewer attacks (what a JES reviewer could say about this paper; use them to pre-empt ours)
1. "Generalized conditions" is not tested: every operating regime is in training; this is cell-level interpolation.
2. The advertised feature-selection innovation has no ablation and is absent from Table 4.
3. Best configuration chosen on the test set; no spread; single split.
4. No semi-empirical or trivial baseline; the 4.3 % has no reference point.
5. Calibration claim: how variance of Q is propagated through the summed dQ predictions is not specified in the text I read; gradient-boosting intervals are a moment-fitted Gaussian around the mean, which is not comparable.
6. "One of the most accurate long-range predictions" has no comparison table.

## (J) Lessons for our paper
1. **[TEXT]** Put the split in one sentence plus a table: which conditions are held out, how many cells each, which conditions are in training. Richardson's own Discussion shows the field's flagship "generalized" paper did not hold out conditions; our condition-disjoint claim is the differentiator and must be stated early, with their sentence on the odd/even split cited as the contrast.
2. **[TAB]** Table 1 must contain a trivial baseline and a semi-empirical baseline before any hybrid; Richardson's 4.3 % floats without one. Report mean +- seed SD and paired condition-level contrasts, not a single split.
3. **[TAB]** Borrow the paired-metric idea (error on the increment and error on the integrated state) and the calibration score next to accuracy; add the Eq. 6 CS (or condition-level coverage) as a column.
4. **[FIG]** Reproduce the Fig 6 pattern (one panel per held-out unit, titles coloured by condition class, uncertainty band) but with held-out status marked and per-panel error printed; show failures on purpose (they did: cells 9, 11, 13, 21).
5. **[FIG]** Add a joint coverage map of the condition design with held-out cells highlighted; their Fig 3 (marginal densities) cannot show this.
6. **[ANALYSIS-EXPLORATORY]** Add a GP (Matern-5/2) transition-style baseline on the same inputs; it is the closest JES precedent, so a reviewer will ask. Label as exploratory if not in the preregistration.
7. **[TEXT]** Ablate every feature or stress input we claim matters; Richardson claims a feature innovation and never tests it.
8. **[TEXT]** Give the idea a short noun ("condition-held-out forecast", "condition learning curve") and use it in the Abstract, Highlights and every caption; naming plausibly drove their citation count (inference).
9. **[TEXT]** State future-input knowledge: calendar and cycle conditions are constant-stress and known, so the known-future-inputs caveat is mild for us; say so in one sentence.
10. **[TEXT]** Release code and data with a persistent DOI; the preprint has no code link, so this is a place we can exceed it.
