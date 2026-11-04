# Prior art: Guo et al., arXiv 2607.16864 (virtual sensing + physics-informed learning, 2 % early data)

Extraction by paper-reader, 2026-11-05. Template: CONTRACT section 4. "Paper reports" statements are E2 for the report only.

## Citation
Guo W, Vilsen SB, Stroe DI, Li Y, Huang Y, Verma A, Brandell D. "Bridging battery design and health assessment through virtual sensing and physics-informed learning". arXiv:2607.16864, submitted 2026-07-18 (id, title, date, authors verified on the arXiv API on 2026-11-05; no journal reference or DOI listed; no Crossref record found by title search). Groups: Uppsala University (Guo, Huang, Brandell), Aalborg University (Vilsen, Stroe, Li), Alstom Rail Sweden (Verma); Sweden and Denmark. Preprint, not peer reviewed as far as can be seen.

## Reading depth
Full text of the PDF (abstract, Introduction, Results, Discussion, Methods, references) read from `ROOT/refs/md/arxiv_2607.16864_c.md`. Table 1 and Figure 6 and 3 pages viewed as images. The Supplementary Notes 1 to 7, Tables S1 to S3 and Figures S1 to S32 are cited in the text but are not in the PDF; they were not read. Several equation symbols in Methods are garbled by the converter (Greek letters lost).

## Problem and stated contribution
Predict capacity-loss trajectory and end of life (EOL) of unseen cells from only 2 to 20 % of early life under heterogeneous fast-charging, driving and temperature profiles. Two parts: (i) "virtual sensing": a random forest trained on digital-twin (COMSOL P2D) synthetic data maps short charging segments to four latent design parameters (D_neg, L_neg, R_neg, C_s,pos); (ii) a PINN with a particle-cracking plus SEI law (from the same digital twin) as a soft constraint, trained in two phases (source cells, then target-cell adaptation with the physical coefficients unfrozen). Claims in the abstract: trajectory and lifetime errors "6 to 8 times" lower than ML baselines with 2 % early data; capacity-loss error down by up to 39 %, EOL error by 17 %, variability by up to 54 % with virtual sensing; "accurate degradation extrapolation does not require fully resolved governing equations".

## Data
- Two fast-charging datasets of 18650 graphite/NMC532 cells, 2 Ah nominal: the public set of Guo et al. (Energy Environ. Sci. 18, 8462, 2025; doi 10.1039/d5ee03268g, Crossref verified, ref 4 of the preprint) plus an additional multistep-charging set (Sec. "Virtual sensing", refs 44, 48, 49).
- Conditions: charging 1C to 2C (Methods: 0.6C to 2C or multistep), four multistep protocols, dynamic discharge 70 to 100 % DoD, ambient 0, 15, 25, 35 C. Each cell has a unique combination except two cells at 1.3C at 15 C.
- Number of cells: not in the main text (in Supplementary Table S2). Figure 6(a-1) and (c) label "unit01" to "unit10", which suggests about ten unseen test cells, unconfirmed.
- Label: capacity loss Q_loss in % against equivalent full cycles (EFC = cumulative discharged capacity / nominal capacity). EOL definition not given in the main text.
- Inputs: 16 health indicators from randomly sampled charging segments (IC and DV based; Table S1, not read) plus virtually sensed design parameters; EFC as time coordinate normalised by M_phys = 1200.
- Storage or calendar cells: none. SOC enters only as the voltage window of the charging segment.

## Model
- FNN-type PINN. Loss: data term, PDE residual on collocation points over the full EFC domain, derivative consistency, initial-condition anchor, monotonicity (Methods Eq. 5 to 10; symbols garbled). Law: particle-crack growth plus SEI coverage of freshly exposed surface with parameters A, B and two more constitutive coefficients (four in total, Methods "Adaptive physics-informed transfer scheduler"); positivity by softplus-type reparameterisation with a floor of 1e-12.
- Phase I (source cells with about 50 % or more observable capacity loss): physical parameters fixed. Phase II (target cell, first 2 to 20 % of its trajectory): physical parameters unfrozen, "decoupled learning rates", early stopping on validation loss, plus a "physics-integrity sentinel" rejecting reversals or implausible futures.
- KAN: none. Calendar term: none. Arrhenius temperature law: none stated; temperature enters through the digital twin and the data.
- Baselines: FNN, CNN, LSTM (no PINN without the cracking law is reported in the main text; "PINN only" in Table 1 means PINN without virtual sensing).

## Tuning
Main text: loss weights lambda_i "to balance competing loss terms"; early stopping on a validation split of the early target data; details in Supplementary Notes 2, 3, 7 (not read). No nested scheme described. Because Phase II uses the target cell's own first 2 to 20 % of labelled capacity for both fitting and early stopping, the visible part is not a held-out calibration set.

## Evaluation
- Split: cell level. Source cells split chronologically into train and validation; target cells (unseen) give 2 to 20 % of their trajectory for adaptation and the rest is hidden (Sec. "Physics-informed learning framework", Fig. 3). Source ratio 50 to 80 % of cells ("despite using only 44 % of the cells and 50 % of the observable trajectory", Sec. "Sparse data").
- Whether target-cell features of the hidden future (charging segments) are used at forecast time is not stated in the main text (it matters for comparison with us; SI note not read).
- Metrics: trajectory MAE in % capacity loss, EOL relative error, EOL MAE in EFC, R2; 10 random seeds for the 2 % case (Fig. 5c); no statistical test.
- Reported numbers (text):
  - 2 % early data, 80 % source: trajectory MAE about 5 % (PINN) vs about 9.5, 8.8, 10.2 % (FNN, CNN, LSTM) (Fig. 5b-1, text).
  - EOL error at 2 %: PINN 15 to 22 % vs ML baselines that "collapse" (Fig. 5b-2, Fig. S15 not read); in the source-ratio sweep the ML baselines stay above 110 to 160 % relative EOL error (Fig. 5a-2, text).
  - Table 1 (main text; PINN only / +D_neg / +L_neg / +R_neg / +C_pos): capacity-loss MAE 1.87 / 1.26 / 1.22 / 1.24 / 1.25 %; EOL MAE 74.14 / 61.41 / 59.39 / 59.15 / 61.28 EFC; capacity-loss R2 0.68 / 0.85 / 0.87 / 0.89 / 0.86; EOL R2 0.60 / 0.75 / 0.78 / 0.77 / 0.76.
  - Narrow V2G window [3.80, 3.85] V, 2 %: MAE/RMSE 2.20 %/2.84 % with virtual sensing vs 3.07 %/3.95 % without.
- Claim checks (abstract and Results against Table 1 and the text; ratios derived by me from the paper's own numbers):
  1. "Capacity loss error by up to 39 % (R_neg)": Table 1 gives 33.7 % for R_neg (1.87 to 1.24); largest reduction in the table is L_neg at 34.8 %. Status: contradicted by Table 1 (a different run or metric may exist in the SI).
  2. "EOL error by 17 %": Table 1 gives 17.2 % (D_neg) to 20.2 % (R_neg). Status: consistent only with the smallest value.
  3. "Variability by up to 54 % (L_neg), 28 % (C_pos)": Table 1 capacity-loss STD rises from 0.14 to 0.18 to 0.21; EOL STD falls by 48 % (D_neg), 35 % (L_neg), 19 % (C_pos), 19 % (R_neg). Status: contradicted by Table 1.
  4. "6 to 8 times lower trajectory and lifetime errors": EOL ratio supported (about 6 to 8 times against collapsing baselines); trajectory MAE ratio is about 1.8 to 2.0 (5 % vs 8.8 to 10.2 %), and the text itself says 40 to 50 % and 5 to 7 times. Status: mixed (abstract overstates the trajectory part).
  5. Three versions of the EOL gain from virtual sensing: text 71.27 +/- 16.07 to 60.55 +/- 9.73 EFC and R2 0.63 to 0.75; Table 1 74.14 +/- 15.20 to 61.41 +/- 7.89 and 0.60 to 0.75; Fig. 6(d-1,-2) 74.14 +/- 14.42 to 61.41 +/- 7.49 and 0.61 to 0.74. Status: inconsistent across text, table and figure.
  6. "Does not require fully resolved governing equations": no run removes or alters the cracking law in the main text (the comparison is PINN vs FNN, CNN, LSTM, and PINN with vs without virtual sensing). Status: not tested in the main text.

## Figures
Fig. 1 virtual sensing from partial charging segments, feature importance; Fig. 2 health indicators and inferred design variables vs Q_loss; Fig. 3 two-phase PINN pipeline schematic; Fig. 4 co-evolution of loss terms, parameter adaptation, loss landscapes, mechanism consistency; Fig. 5 data efficiency (source ratio, target ratio, 10 seeds); Fig. 6 diffusion-coefficient SHAP, loss landscapes, EOL parity; Fig. 7 V2G voltage-window robustness (the text calls it "Figure 6" a second time). Style: many panels and 3-D loss landscapes; two pages viewed, not assessed in detail.

## Ablations done
Source ratio 50 to 80 %; target ratio 2 to 20 %; virtual-sensing parameters added one by one (Table 1); voltage windows (Fig. 7d, e). Not done in the main text: removing the particle-cracking law, freezing the physical parameters in Phase II, swapping the law.

## Hidden assumptions
- The digital-twin cracking law is valid for NMC532 under all these profiles; the model learns four coefficients while the form is fixed.
- The random forest virtual sensor trained on synthetic data with 1 % parameter spread transfers to real cells; no ground truth of D_neg or R_neg exists for the test cells, so "virtual sensing" is validated only through downstream error.
- The first 2 % of target labelled data are available (cells have a measured early capacity series).
- The loss-landscape curvature argument (Fig. 4c) is read as "improved identifiability"; that is a qualitative picture, not an identifiability test.

## Weaknesses a reviewer would hit
1. Cell count and train/test lists are in the SI; about ten unseen cells; heterogeneous unique conditions, so one cell per condition and no replicates.
2. Internal numeric inconsistencies (claim checks 1, 3, 5).
3. No "same PINN without the law" ablation, so the headline claim about partial mechanisms is untested.
4. Early-stopping and adaptation on the same early target data.
5. Fast-charging EV cycling only; no storage; physics is a mechanical-cracking law of a digital twin, with no Arrhenius stress functions.
6. Code and data "after publication"; preprint.

## Gaps and hooks for our paper
- Hook 1: this is the closest in the task statement (forecast the rest of the life of an unseen cell from its first 2 to 20 %). Our protocol uses the first check-ups of storage and cycling cells at held-out conditions; our added value must be the held-out stress combination plus calendar coverage, not the early-data idea.
- Hook 2: they use the target cell's early labels for both adaptation and early stopping; we can report a protocol where the early check-ups are used only for conditioning, and show the effect of the early-window length (2, 5, 10 %).
- Hook 3: the claim "partial mechanisms are sufficient" is untested there; our ablation (physics residual removed, KAN removed, law component dropped) tests exactly that for a calendar plus cycle law.
- Hook 4: they offer loss-landscape pictures as "identifiability"; a formal test (parameter recovery on synthetic data from our own law, profile likelihood over the KAN coefficients) would differ and be checkable.

## Code/data availability
"Data and code used in this work will be available after publication." Public dataset (Guo et al. 2025) exists; the additional multistep dataset is not stated as public.

## Exact overlap with our design
- Physics-informed neural network with PDE-style residual and monotonicity penalty: same in kind (Methods Eq. 5 to 10, loss with residual, anchor and monotonic terms).
- Forecast of an unseen cell from early-life labelled data: partial (2 to 20 % of the target cell's trajectory, Fig. 3, Fig. 5; our first check-ups of storage and cycling cells).
- Held-out operating conditions: partial (each cell has a unique condition, so every test cell is a new condition; SI not read for the exact split).
- Calendar or storage ageing term: different (none; no storage cells).
- Arrhenius temperature stress function: different (not stated; temperature handled implicitly via the digital twin).
- KAN stress functions: different (none; FNN).
- Learned stress dependence in the law: different (four fixed-form constitutive coefficients re-fitted in Phase II).
- Cycling stress variables T, DoD, C_ch, C_dch: partial (data cover temperature, charge rate, DoD; the law does not take them as functions).
- Ablation of physics residual: different (not in the main text).
- Identifiability test: different (qualitative loss-landscape view only, Fig. 4c).
- Dataset: different (NMC532 18650 fast-charging; not Samsung 50E).
- Joint training on storage and cycling cells: different.
- Latent design parameter inference (virtual sensing): different (no counterpart in our design).
