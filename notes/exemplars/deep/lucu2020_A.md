# Deep dissection: Lucu et al. 2020, Part A (storage), JES 30, 101409

Role for us: a JES learning-curve paper on calendar ageing of an NMC pouch cell. Extends `notes/papers/lucu2020_A_B_JES30.md` (which read Sections 3-5 only by keyword and saw no figures). Part B is in `lucu2020_B.md`.

reading: full text (`refs/fulltext/lucu2020_A_JES30_101409.txt`, clean ScienceDirect capture, read end to end including appendices and all 53 references). Figures: downloaded `refs/figs/lucu2020A/gr1..gr9.jpg` from the Elsevier CDN (PII S2352152X19314215) and viewed gr1 (Fig. 1), gr2 (Fig. 2), gr3 (Fig. 3), gr4 (Fig. 4), gr5 (Fig. 5), gr6 (Fig. 6), gr7 (Fig. 7), gr8 (Fig. 8); gr9 (Fig. A1, raw curves) not viewed, judged from its caption. Numbers read from images are marked "image".

## (A) Contribution as the authors state it
A calendar-ageing capacity-loss model under the Gaussian-process framework with a composed (tensor-product) covariance function, built to show that the model learns from new data: accuracy rises and predictive uncertainty falls as ageing conditions are added, and the minimal number of laboratory ageing tests needed for a broad storage window is quantified (Abstract; Sect. 1 contributions).
Wording pattern, Sect. 1: "the present study aims to extend existing research by integrating the following main contributions" followed by two roman-numeral main contributions (learning from new data and extending the operating window; compositional covariance functions tailored to ageing), then "Additionally ... secondary contributions" in three roman-numeral items (minimal number of laboratory tests; validation on an extensive dataset of 30 static + 2 dynamic cells; sensitivity of capacity loss to each stress factor from the kernel length-scales, flagged as not previously done in this field). Two tiers (main, secondary) with the data-efficiency claim placed in the secondary tier but promoted to the headline number of the abstract. Quote (once): the title-level promise "learning from real operation data" (title, Part A).

## (B) Structure
Type: full-length article; seven authors (Ikerlan, UPV/EHU, Warwick WMG); EU-project data (Batteries2020).
Sections (word counts from a raw count of the capture, equation fragments inflate Sections 4 and 5 by about 20 %; total about 10,000 words, well above the JES "ideal" 6,000 limit of today's guide):
| Section | ~words | Content |
|---|---|---|
| Highlights | 90 | 5 bullets: GP calendar model; new covariance function; learning from new data; sensitivity and UQ analysis; validation with 32 cells. Only one number (32). |
| 1 Introduction | 1,650 | context, ageing-model families, test-effort problem, GP and why nonparametric, gaps, contributions, roadmap |
| 2 Experimental calendar data (2.1 static, 2.2 dynamic), Tables 1-2 | 770 | 20 Ah NMC (4:4:2)/graphite pouch cell; 30 cells at 10 conditions x 3 cells; 2 dynamic cells; check-up about every 28 days |
| 3 Data preprocessing | 1,180 | four-phase capacity curve (Fig. 1); only Phase 2 modelled; Table 3 data kept |
| 4 GP theory | 500 | Eq. 1-6 |
| 5 Model (5.1 inputs, 5.2 kernel) | 1,500 | inputs 1/T, SOC, delta-t; Matern 5/2 x Matern 5/2 x linear; Eq. 7 |
| 6 Learning from static conditions (6.1 metrics, 6.2 seven training cases, 6.3 accuracy, confidence, sensitivity) | 2,900 | the core |
| 7 Learning from dynamic conditions | 850 | cells #31, #32 |
| 8 Discussion, limitations, further work | 950 | |
| 9 Conclusions | 220 | |
| Appendix A (raw data, Table A1 variance), B (Table B1 results) | | |
Display items: 8 figures (Figs. 1-8) + 5 tables (Tables 1-5) in the body, plus Fig. A1, Table A1, Table B1 in the appendix: 16 items, nearly twice the current JES ideal of 8-10. Equations 13. References 53 (read from the capture; one is a "under review" companion paper, one entry is duplicated as [37] and [44]).
Abstract pattern (5 + 2 sentences): (1) conventional ageing models need much time and test effort; (2) telemetry data are coming; (3) therefore models that learn from in-field data are attractive; (4) this two-paper series develops a GP ageing model, emphasising learning from new data; (5) this paper = calendar ageing, a specific covariance function, quantification of the minimal number of laboratory tests; (6) headline: a model trained with 18 cells reaches 0.53 % mean absolute error on the capacity curve over a broad window of static and dynamic storage conditions. One number, placed last; the number is a data-efficiency number (cells needed), not an accuracy record.

## (C) Every figure
| No. | Form, panels | Encodings | Claim it supports | Quality | Do better |
|---|---|---|---|---|---|
| 1 | Single capacity-retention curve vs storage time, four phases coloured and separated by dotted lines (rise, linear loss, knee drop, slowdown) | colour = phase (green, black, blue, red); y 60-110 % | defines what is modelled (Phase 2 only) | very clear teaching figure; x ticks only 0, 300, 600 | keep this style for our "what the fade phases look like" inset, mark the part we forecast |
| 2 | 3 panels (25, 35, 45 C) of preprocessed normalised capacity vs days, 4th panel for dynamic cells | colour = SOC (7 levels), marker = replicate cell | all conditions retained after preprocessing; spread within replicate triples | colour set (black, green, red, blue, yellow, purple) mixes similar hues; lines thin; no replicate legend | one panel per factor with colour-blind-safe palette and replicate shading |
| 3 | The learning-curve figure: 3 stacked panels (training cells, validation cells, all cells), x = training case 1-7 with a top banner "Learning the influence of Temperature | SOC" and a dashed divider where the learned factor changes; left axis MAE (dQ dashed x, Q solid o, black), right axis calibration score CS (green); y-axes differ by panel (0-1.5 vs 0-3) | colour = metric family, line style = target (dQ vs Q) | the model improves and stabilises from Case 3 (validation MAE_Q 0.64 %, Table B1) | strong idea; dual axis and different y-ranges are hard to compare; no uncertainty over orderings; case 7 has no validation point because nothing is held out | one ordering only: ours should draw the band over random orderings and use one axis per quantity |
| 4 | 8 small multiples of predicted capacity vs days with confidence band; (a-d) training cells in blue, (e-h) a held-out 35 C / 65 % SOC cell predicted with training cases 1, 2, 3, 7 in green | band = +-2 sigma | the same held-out cell improves from "over-estimated fade" (Case 1, 3.15 % MAE_Q, Sect. 6.3.1) to 0.34 % (Case 3) | excellent narrative figure: one held-out cell, rising training information | we copy this: one held-out condition, panels over m, with the closed-form law overlay |
| 5 | 5 panels of predictive sigma vs T (at SOC 80 %) and vs SOC at 15, 25, 35, 45 C, one curve per case (red/grey for Cases 1-2, blue shades for Cases 3-7) | line style and shade = case | uncertainty is lowest at observed conditions and falls with each added case; cold range stays uncertain | informative; sigma is the GP's own sigma, not an empirical error | ours: empirical spread of the extracted stress law over resamples, plotted the same way |
| 6 | Stacked-area chart of normalised inverse length-scales, temperature (green) vs SOC (hatched), Cases 1-7 | fill = factor | temperature outweighs SOC in the learned kernel, SOC share rises at Case 4 (adds 100 % SOC) | hatching survives greyscale; shares are interpolated between discrete cases as if continuous; no uncertainty; the authors warn it "does not imply causality" (Sect. 6.3.3, paraphrase) | compute relevance by ablation on held-out error with seed bands |
| 7 | (a) Dynamic cells #31, #32: data, initial prediction (Case 3, grey band), updated prediction (blue band) after training on days 0-368; (b) T and SOC step profiles below on a shared x axis | colour = model version | the model can be updated from in-field-like profiles and the band narrows | good stacking of response and drivers; two cells only; cell #32 shows 92 % at about 1,030 days well below prediction (image), a miss that is not hidden | keep the stacked drivers beneath the response |
| 8 | Same as Fig. 5 for model Case 3 (solid) vs updated model (dashed) | | uncertainty at cold T and low SOC falls after the update | fine | |
| A1 | 5 raw-curve panels | | raw variability | not viewed | |
Quality summary: consistent MATLAB-style formatting, serif fonts large enough at column width, panel letters bold in a corner, and a colour pair (blue = training, green = new/validation) used consistently across Figs. 4, 5, 7.

## (D) Tables
| No. | Content | What it proves |
|---|---|---|
| 1 | nominal cell data and manufacturer limits | context, and justifies the temperature limits for the kernel |
| 2 | test matrix: 25/35/45 C x six SOC levels, 3 cells per cell of the matrix, 10 filled conditions (25 C and 45 C at 50 % and 80 %, 35 C at all six) | the design is unbalanced: only 35 C has the full SOC sweep |
| 3 | percent of data kept per condition after preprocessing (ranges, e.g. 94.4-100 % to 10-15 %) and the mean 64.64 % in the text | transparent data-loss accounting; low-SOC cells lose most data (rise phase discarded) |
| 4 | structure of the training rows (cell, input vector, target) | shows that training rows are increments from different starting points, which also gives the noise term |
| 5 | seven training cases: which T and SOC levels are in, and "# training data / # total data" (24.86, 42.40, 70.13, 79.70, 80.44, 95.43, 100 %) | the ladder; the most reusable table for us |
| A1 | variance of replicate capacity curves per condition (e.g. 0.05 to 3.51 %^2) | replicate noise level by condition; shows the hot, high-SOC cells are noisiest |
| B1 | MAE, RMSE, CS for dQ and Q, training/validation/all, Cases 1-7 (Case 3 validation MAE_Q 0.64, RMSE 0.76, CS 89.04) | full numbers behind Fig. 3 |

## (E) Evaluation protocol
- Task: predict capacity loss of a storage cell given T, SOC and time, iteratively (accumulating dQ gives Q). Units: cells. Static: 30 cells, 10 conditions; dynamic: 2 cells.
- Splits: seven nested training sets built by hand in a fixed order (temperature extremes at SOC 80 %, then 35 C, then SOC 50 %, 100 %, 20 %, 65 %, 35 %; Sect. 6.2, Table 5). Training cells vs validation cells (cells whose condition is absent from the case). Validation cells at the held-out SOC levels are at temperatures already seen (35 C), so the held-out task is mostly interpolation inside the convex hull of the training conditions. Case 3 uses 18 cells at 6 conditions; its validation set is the 12 remaining cells.
- Metrics: MAE and RMSE of dQ and of Q; a 2 % MAE_Q "acceptable" threshold set by the authors; calibration score CS_2sigma (share of points within +-2 sigma; 95.4 % is the target).
- Headline numbers: Case 3 overall MAE_Q 0.53 % (Sect. 6.3.1; Table B1 "All"); the Conclusions quote 0.31 % MAE_dQ whereas Table B1 prints 0.30 for Case 3, a small mismatch; CS_Q converges to about 86.55 % and CS_dQ to about 96.19 % (Sect. 6.3.2, 8): over-confident on the accumulated capacity, close to nominal on the increments. Dynamic cells: MAE_Q 1.78 % and 0.62 % for #31 and #32 with the Case 3 model (Sect. 7).
- Baselines: none. No other model class, no semi-empirical law, no persistence.
- Statistics: none beyond means. No seeds, no repeated orderings, no confidence interval on any error, no test. Replicate variance only in Table A1.

## (F) Novelty framing
(1) "Most critical gaps" lifted from the authors' own earlier review [23]: underuse of stress-factor features and insufficient validation. (2) Positions against prior GP battery papers (nine citations in a single bracket [25]-[33]) as limited to conventional kernels chosen by trial and error for one dataset. (3) Argues a design principle (the covariance function encodes assumptions, so justify it beyond the dataset). (4) Claims a quantity nobody reported ("minimal number of laboratory tests"), and a quantity "not performed in the field" (kernel-based sensitivity of capacity loss). (5) Defers integration of calendar and cycle ageing to future work and says so twice. Notice that no head-to-head with a competing model class is offered: novelty is a framing (data-efficiency and updateability), not a benchmark win.

## (G) Limitations and negative results
Stated in Sect. 8: over-confidence of the accumulated-capacity intervals, attributed to error accumulation in iterative prediction; only 2 dynamic cells and no realistic daily-cycled temperature; Phase 1 (initial rise) discarded on an assumption "to be verified in further work"; preprocessing needs knowledge of the full trajectory to find phases, which a deployed model would not have; cycle-induced calendar ageing excluded; O(n^3) time and O(n^2) memory of the GP. Not stated: one fixed ordering of the ladder; validation is mostly interpolation in T; no baseline; Phase 3-4 (knee and slowdown) data dropped, so the method forecasts only the benign regime. Negative or weak results are shown (Fig. 7 miss on cell #32; CS_Q 86.55 %) and explained in one paragraph each rather than hidden.

## (H) Data and code availability
No data-availability or code statement (2020 article). Data from the Batteries2020 consortium are thanked, not deposited. No software named. (JES now requires such statements: check `notes/JES_guide_for_authors_2026-11-04.md`.)

## (I) What a hostile reviewer would attack
1. Held-out units are largely interpolation (all three temperatures already seen at Case 3); the "learning" is mostly the model finding a second SOC level, not extrapolating.
2. One hand-chosen ordering of the training ladder; the claim that "Case 3 is enough" depends on it.
3. The 2 % MAE_Q threshold is arbitrary and MAE_Q is an accumulated, normalised, monotone quantity that flatters any smooth model; no comparison with a trivial linear-in-time or Arrhenius baseline.
4. Over-confident intervals (86.55 %) contradict the headline claim of "more confident" predictions unless calibration is the goal.
5. 35 % of the raw data are discarded using knowledge of the whole curve; the retained percentages differ by condition (10 % to 100 %), biasing towards the hot, high-SOC cells.
6. Length-scale "relevance" read as sensitivity (and stacked as shares) is a property of the kernel and of what the training set contains, not of the cell.
7. Two dynamic cells; one update point chosen after looking at the profile.

## (J) Lessons for our paper
1. [FIG] Our learning curve over m (conditions) and k (check-ups) should reuse the Part A Fig. 3 grammar: x = ordered ladder, a banner above the axis naming what each stage adds (a new temperature, a new SOC window, a new DoD, a new C-rate), dashed dividers between factor blocks, held-out-only error. Improve it: median and interquartile band over random orderings of the ladder, a noise-floor line from the replicate cells, and one axis per quantity.
2. [FIG] Reproduce the Fig. 4 narrative: one held-out condition shown at four ladder positions (small multiples, same y-range, markers = data, line = forecast, band = interval, held-out label in colour). It is the cleanest way to show "more conditions, better extrapolation" in 4 panels.
3. [FIG] A "uncertainty collapses as m grows" figure (their Figs. 5 and 6 of Part B) for our extracted stress laws: spread of the learned law across resamples at each m, over the stress axis, with the training conditions marked on the axis as ticks. Replaces the GP sigma by an empirical envelope.
4. [TAB] A ladder table (their Table 5): per rung, the conditions added, the number of cells, the share of all data. Add the number of check-ups k per cell and the number of held-out conditions per rung.
5. [TAB] Data-retention table per condition (their Table 3) with the exclusion rule stated; plus the replicate-variance table (their Table A1). Both pre-empt cherry-picking attacks.
6. [TEXT] Put the data-efficiency number in the last sentence of the abstract ("trained with only N cells ... error X over Y held-out conditions"), and state a pre-declared adequacy threshold in the methods. Define the threshold relative to the replicate noise floor, not as a round percentage.
7. [TEXT] Mirror their "main versus secondary contribution" tiers, but keep one primary claim with the paired condition-level test; they offer no test, so ours is the differentiator.
8. [TEXT] Keep a Discussion section titled with "limitations": report calibration honestly (they show 86.55 % vs 95.4 % and diagnose it). Do the same for any interval we report.
9. [ANALYSIS-EXPLORATORY] Their relevance plot (Fig. 6) is a sensitivity read-out with no uncertainty. Ours: relative importance of each stress factor by held-out ablation, per ladder rung, with bootstrap bands, labelled exploratory and with their own caution that it implies no causality.
10. [ANALYSIS-EXPLORATORY] Include one extrapolation-in-time check beyond the last used check-up, shown as a dashed continuation, to answer the "interpolation only" objection; mark exploratory.
