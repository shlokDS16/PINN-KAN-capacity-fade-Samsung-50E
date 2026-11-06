# Lucu et al. 2020 - Data-driven nonparametric Li-ion ageing model, Part A (storage) and Part B (cycling), J. Energy Storage 30

Paper note per research/CONTRACT.md section 4, written for novelty condition (b). Auditor: novelty-auditor, 2026-11-06.

## Citation
M. Lucu, E. Martinez-Laserna, I. Gandiaga, K. Liu, H. Camblong, W. D. Widanage, J. Marco. "Data-driven nonparametric Li-ion battery ageing model aiming at learning from real operation data - Part A: Storage operation", J. Energy Storage 30 (2020) 101409, DOI 10.1016/j.est.2020.101409; "... - Part B: Cycling operation", J. Energy Storage 30 (2020) 101410, DOI 10.1016/j.est.2020.101410 (both Crossref-verified in `debates/D016_roles/03_novelty_recheck.md`). Ikerlan (Spain), University of the Basque Country, Warwick WMG (UK).

## Reading depth
- Part A: full text from `refs/fulltext/lucu2020_A_JES30_101409.txt` (ScienceDirect capture, clean text): abstract, introduction, Sections 2, 6 (6.2, 6.3.1, 6.3.2), 8, 9 read line by line; Sections 3-5 (preprocessing, GP theory, kernel construction) located and keyword-checked, not read line by line; figures not seen.
- Part B: full text from `refs/pdf/lucu2020_B.pdf`, re-extracted with pdftotext in reading order (the `.md` conversion is garbled): abstract, introduction contributions, Sections 6.2, 6.3.1, 8, 9 and appendix header read; Sections 2-5 and 7 located and keyword-checked, Section 7 read by targeted lines only; figures not seen. Part B was not read line by line.
- Keyword checks over both files (physic, semi-empirical, Arrhenius, ablation, neural, held, benchmark): no physics-informed, semi-empirical-law or neural arm in either paper; the only "Arrhenius" hit is an input transformation (reciprocal temperature "for alignment to the Arrhenius law", Part A Section 5 and Part B Section 5 input list).

## Problem and stated contribution
Gaussian-process (GP) ageing models that "learn from new data observations": a composed covariance function tailored to ageing, learning from progressively observed operating conditions, the "minimal number of laboratory tests required for the design of an accurate ageing model" (secondary contribution (i) in both papers), validation on a broad condition window, sensitivity of capacity loss to stress factors by the kernel length-scales. Part A is calendar ageing, Part B cycling; the two are **not** combined ("the integration ... is the subject of ongoing research").

## Data
- Part A: 20 Ah NMC (4:4:2)/graphite pouch cell (Batteries2020 project); 30 cells at 10 static storage conditions (T 25/35/45 C, SOC 20-100 %, 3 cells per condition, Table 2) plus 2 cells at dynamic conditions; checks about every 28 days. Label: capacity loss (MAE of Delta-Q and of Q).
- Part B: 122 cells at static cycling conditions plus 2 at dynamic conditions (124 cells in the abstract); factors temperature, DoD, middle-SOC, charge C-rate, discharge C-rate; range 25-45 C, 20-100 % DoD, 20-80 % middle-SOC, C/3-2C. Not the Samsung 50E data.

## Model
GP regression with a composed kernel on the stress inputs and the throughput/time input (reciprocal temperature, DoD, middle-SOC, C-rates, Ah-throughput). Non-parametric; no ageing law, no neural network, no physics-informed loss, no KAN, no closed form.

## Tuning
Kernel hyperparameters by marginal-likelihood optimisation on the training cells of each case (standard GP); the 2 % MAE threshold used to read off "adequate" is set by the authors, not derived. Training-case order is chosen by design, not randomised.

## Evaluation (the part that matters for novelty)
- **Learning curve over the number of ageing conditions, scored on held-out cells.** Part A: 7 nested training cases (Table 5: temperature extrema at 80 % SOC, then 35 C, then SOC levels one by one; training share of data 24.86 % to 100 %), error computed separately for training cells and for validation cells not involved in the case (Fig. 3). Case 3 (6 storage conditions, 18 cells) reaches 0.64 % MAE_Q on validation cells and the paper reports 0.31 % MAE_dQ and 0.53 % MAE_Q for 30 cells (Conclusions); the paper calls case 3 an adequate trade-off.
- Part B: **16 nested training cases** (temperature levels, then DoD, middle-SOC, charge C-rate, discharge C-rate levels, highest and lowest first), training cells, validation cells, and "targeted validation cells" at unobserved levels of the factor being learned (Fig. 4b, 4c); the 2 % threshold is reached at case 4 (26 cells at 9 cycling conditions); 0.58 % MAE_dQ and 1.04 % MAE_Q for 122 cells (Conclusions).
- The kernel length-scales rank the factors: temperature, DoD, charge C-rate, middle-SOC, discharge C-rate (Part B Section 6.3.3, Fig. 7).
- Dynamic cells: the GP is updated with the cells' own observed data (Section 7). I found no curve over the number of check-ups per held-out cell, and no matched comparison with other learner families. No seeds or repeated draws of the training conditions (one fixed sequence); no interval on the error difference between cases; no statistical test.

## Figures
Capacity curves (Fig. 2, A1), error against training case for training/validation/all cells (Part A Fig. 3, Part B Fig. 4), prediction curves with confidence bands for chosen cases (Fig. 4-5), standard-deviation maps over the stress space by case (Part A Fig. 5, Part B Fig. 6), length-scale relevance by case (Part B Fig. 7), dynamic-profile updates (Fig. 8). Forms not inspected.

## Ablations
Training cases are the nearest thing (information-content ladder of conditions). No ablation of a physics law, a map, or of the kernel against a neural alternative.

## Hidden assumptions
GP isotropic kernel components suit temperature and SOC inside the manufacturer window; cells at one condition are replicates (3 per condition in Part A); the 2 % threshold is meaningful; preprocessing (removal of initial capacity rise, Part A Section 3) does not bias the trend.

## Weaknesses a reviewer would hit
One cell type, one fixed order of conditions, no repeats, no baselines, over-confident intervals (calibration score 86.55 % against 95.4 % in Part A; about 75 % in Part B), no cycling-plus-storage joint model.

## Overlap with our four-part claim (condition (b))
- **Physics-informed arm: none in either paper (condition (b) as worded, closed).**
- **Correction to the D016 recheck (`03_novelty_recheck.md` sections 2.2 and 2.5):** it described Lucu B as a learning curve "by number of cells" and found a curve over the number of cycling conditions "not found". Read in full, Lucu A and B **are** learning curves of a learned (nonparametric) forecaster over the number of ageing conditions (storage and cycling), nested, scored on held-out cells at unobserved stress levels. This is the element (i) of our claim in its generic form. The differences that remain: GP not physics-informed; no joint calendar-plus-cycle law (two papers); no check-ups per held-out cell axis (k); no matched ladder; no comparison with tuned data-driven learner families; one fixed condition order, no repeated draws, no simultaneous intervals; not the Samsung 50E designed campaign; no closed-form law.
- Consequence: D018 section 7, fifth bullet ("Hallinger, Lucu A/B or Jia (full text) contain a learning curve of a learned or physics-informed forecaster over the number of ageing conditions on held-out conditions, which re-opens the novelty scope of section 6") **is triggered for Lucu A/B**. The stop rule 12 part (same dataset) is not.

## Gaps and hooks for our paper
Cite both as the JES precedent for the minimal-number-of-tests question; name the differences above; do not describe our m-curve as a new type of study. The "adequate at 9 cycling conditions of 26 cells" statement is a published reference point for how many cycling conditions a GP needed on a different cell.

## Code/data availability
Not stated in the passages read (Part A funding and CRediT only).
