# 11 Jarraya 2025 - SOH-KLSTM (KAN inside the LSTM candidate cell state)

## Citation
Jarraya I, Ben Atitallah S, Alahmed F, Abdelkader M, Driss M, Abdelhedi F, Koubaa A. "SOH-KLSTM: A hybrid Kolmogorov-Arnold Network and LSTM model for enhanced lithium-ion battery health monitoring". Journal of Energy Storage, vol. 122, article 116541, 2025, DOI 10.1016/j.est.2025.116541 (Crossref lookup, 2026-11-04). A Corrigendum exists: J. Energy Storage 124, 116868, DOI 10.1016/j.est.2025.116868 (Crossref; its content NOT read). Group: Robotics and IoT Lab, College of CIS, Riyadh (Saudi Arabia), with RIADI Lab Manouba (Tunisia) and King Abdulaziz University; acknowledgement to Prince Sultan University (p.20).
Document read here is the arXiv preprint arXiv:2509.10496v1 (31 Aug 2025), 22 pages, "Preprint submitted to Elsevier". Numbers and tables below are the preprint's; the published version and the corrigendum may differ.

## Reading depth
reading: full text of the preprint (all 22 pages incl. all 5 figures and Tables 1-2; references not checked one by one). Source: `refs/pdf/11_jarraya2025.pdf`, `refs/md/11_jarraya2025.md`, `refs/txt/11_jarraya2025.txt`. Figures 1-5 viewed as rendered pages (Fig 3, 4, 5; Table 2 image verified because the text extraction scrambles it). Published JES version and corrigendum not read. No code released (no code or data availability statement in the preprint).

## Problem and stated contribution
Capacity/SOH estimation on NASA PCoE cells. Claim: replace the linear-plus-tanh transform of the LSTM candidate cell state by a KAN-style term (SiLU branch plus B-spline branch), so that the network "learns activation functions" and captures non-smooth degradation (p.3). Headline claim: RMSE 0.001682 on B0005 against 0.058334 for an LSTM, "97.12% reduction", "about 35 times" (abstract p.1; Table 2 p.19). Also claims real-time suitability from 1.26-3.42 s execution time (Table 1 p.17; Section 5.3.2).

## Data
- NASA PCoE Li-ion 18650, 2 Ah (p.15). Eight cells used: B0005, B0007, B0018 (Group A: 2 A discharge, 24 C), B0033, B0034 (Group B: 4 A), B0046, B0047, B0048 (Group C: 4 deg C) (p.15, Section 5.1). Number of cycles per cell not stated; Fig 5 x-axes run to about 170 (B05, B07), 130 (B18), 200 (B33, B34) and about 75 (B46-48).
- Inputs: previous-cycle capacity C_(k-1), terminal voltage V_k, current I_k, temperature T_k (Eq. 4, p.7). How a per-cycle scalar is obtained from V, I, T is not described (mean? sequence?). Sequence length / window of the LSTM is not given.
- Label: SOH_k = C_k / C_nominal (Eq. 1, p.6); an alternative charge-throughput form is written (Eq. 2). Outputs are SOH and capacity jointly (Eq. 10, p.9). The plotted SOH in Fig 5 starts around 0.8-0.9 (B05 about 0.82), not 1.0, and the normalisation actually used is not stated (MinMaxScaler is applied, p.15).
- Preprocessing: MinMaxScaler; no outlier handling described. Fig 5d-h (B33, B34, B46, B47, B48) contain excursions of the plotted "actual SOH" to about 0 at isolated cycles, which look like unremoved measurement artefacts; the model is drawn tracking them.

## Model
- Standard LSTM gates (Eq. 5-9) with the candidate cell state replaced (Eq. 14, p.12): c~_KAN = SiLU(W_c [h_(t-1), x_t] + b_c) + sum over unspecified index ranges of w_j B_(j,k)(Psi_(q,p)(x_t)). In Fig 4 (p.11) the B-spline branch is fed by x_t only (not by h_(t-1)). The index ranges, the number of spline terms and the meaning of Psi_(q,p) are not defined in the text.
- B-spline: degree and knots written generally (Eq. 16-18); grid size, spline order, knot placement, hidden size, number of layers, parameter count are NOT reported. The generic KAN form phi(x) = w_b b(x) + w_s spline(x) (Eq. 12-13) is quoted from Liu et al. (ref 29); the implemented model is not a KAN network (no spline matrix between layers); it is one KAN-like additive term in one gate.
- Physics prior: none. Eq. 3 is described as "differential equation-based" but is only the generic recurrent mapping (y_SOH, y_cap) = F(x_t, h_(t-1), c_(t-1); theta). No loss term, constraint or feature encodes a degradation law.
- Training: Adam lr 0.001, batch 32, up to 100 epochs "per fold", early stopping patience 10, plateau LR reduction (p.15-16); TensorFlow 2 / Keras, RTX 3080; the loss is not stated (only that RMSE is the metric).

## Tuning
No hyperparameter search is described. No statement about how hidden size, spline grid or order were selected. "Per fold" is used once but no fold scheme is defined. Whether the test portion influenced any choice cannot be assessed; with a validation portion of 20 % of the same cell (below) the early-stopping signal is in-cell.

## Evaluation
- Split: "training (70%), validation (20%) and tests (10%)" of the dataset (p.15). Not stated whether this is per cell, over cycles, random or chronological. Because each reported result is per cell (Table 1) and each cell is a separate model/dataset, the split is within cell. Fig 5 plots the predicted and actual curve over the whole cycle range as dense points (red and blue overlapping on the full trajectory), consistent with predictions drawn over all cycles of the cell. I could not tell from the text which points are test points.
- Leakage channel in the input: C_(k-1) is the previous-cycle capacity, which is almost the label (SOH_k = C_k/C_nom). The task is therefore one-step-ahead autoregression on capacity, not estimation from V, I, T. This explains tracking of isolated artefacts (Fig 5) and the very low RMSE. The paper presents it as SOH "estimation" and "prediction" interchangeably.
- Metrics: RMSE (Table 1) and MAPE (only in Table 2 for B05, B07); no MAE, R2, or interval. Table 1 RMSE per cell (p.17): B05 0.001682, B07 0.002112, B18 0.001816, B33 0.003976, B34 0.002342, B46 0.006440, B47 0.006888, B48 0.007114. Execution time 1.260 to 3.422 s.
- Baselines: no baseline was run by the authors. Table 2 (p.19, verified on the image) copies literature numbers: LSTM [14] 0.058334 / 0.041061 RMSE, CNN-LSTM [29] 0.02 / 0.03, SVR-LSTM [30] 0.003, DEGWO-LSTM [20] 0.325 / 0.377, SBL 3.5656 / 2.6153, GPR 0.0114, CMMOG 0.6490, DGL-STFA 0.876. These come from different papers with different splits, inputs and units.
- Seeds / repeats / statistical test: none stated. Single run per cell implied.
- Headline numbers: B05 RMSE 0.001682, MAPE 0.17 %, "error reduction" 97.12 % vs LSTM; B07 0.002112, 0.21 %, 94.85 % (Table 2 p.19). 97.12 % = (0.058334 - 0.001682)/0.058334 is arithmetically correct; "about 35 times" = 0.058334/0.001682 = 34.7 is correct.

## Figures
- Fig 1 (p.2): taxonomy tree of SOH estimation methods (experimental / model-based / data-driven / fusion). Form: block diagram. Message: context. Not viewed in detail. Rating 3/10: textbook taxonomy, no data; a JES reader skips it.
- Fig 2 (p.7): cartoon of cell with indicators V, I, T, C_(k-1) feeding SOH estimation (caption). Rating 2/10: conceptual clip-art; and it announces the leakage-prone input C_(k-1).
- Fig 3 (p.10): two-layer KAN schematic with B-spline basis inset (basis functions B_1..B_7 plotted bottom-left, summation inset), learnable activation icons on edges, inputs X_1, X_2, output f(X). Form: re-drawn from Liu et al.'s Fig 0.1 style, blue-grey icons, dotted callout. Message: how a KAN edge is a spline sum. Rating 4/10: clear but borrowed; not about the battery model.
- Fig 4 (p.11): architecture of SOH-KLSTM, three stages down the left (data preprocessing, model learning, performance validation), LSTM cell in green with forget/input/output gates, the KAN module in a purple box with W_c, SiLU, Psi_(q,p), B_(j,k), w_j and summation nodes; NASA logo, train/val/test folders at the top. Message: where the KAN term enters the gate. Rating 6/10: readable data flow and the only figure that shows the actual novelty; but symbols are small and the stage-1 folders do not say per-cell or per-cycle.
- Fig 5 (p.17): 8-panel (a-h, 2 columns x 4 rows) per-cell SOH vs cycle, red dots = actual, blue dots = predicted, grid lines, legend per panel. Message: tracking is nearly perfect, including spikes. Rating 3/10 for a JES reader: no zoom on the error, no residual plot, no train/test marking, no uncertainty; the near-perfect overlay on artefact dips to 0 invites the leakage suspicion (input C_(k-1)) instead of confidence.
- Tables: Table 1 (p.17) three columns (dataset, RMSE, execution time), plain; Table 2 (p.19) literature comparison with up/down arrows, best row in bold; rating 4/10: the comparison mixes protocols and possibly units (see weaknesses).

## Ablations
None. No KAN-term-removed LSTM under the same input and split, no KAN vs MLP-with-equal-parameters, no spline grid study, no input ablation (with and without C_(k-1)). The "LSTM-only" comparator is a number from another paper.

## Hidden assumptions
1. The previous-cycle capacity is available at inference time (it is the quantity to be estimated one cycle earlier). Then the model solves one-step capacity forecasting from the immediate past.
2. Cycle-to-cycle correlation of capacity makes a random or in-cell split nearly interpolation.
3. The three NASA groups (Group A/B/C) are used as independent per-cell experiments; no transfer between cells is tested although the text says the model "generalises across operating conditions" (p.17, Section 5.5).
4. Units of RMSE are comparable across Table 2 rows.

## Weaknesses a reviewer would hit
- Input leakage through C_(k-1) (Eq. 4) and an in-cell, undefined split (p.15): the headline accuracy is not evidence that V, I, T carry the signal or that the KAN term helps.
- No ablation of the KAN term. The claimed 97.12 % is measured against a number from another paper (Yao et al., ref 14), not an LSTM run under the same pipeline (Table 2).
- Table 2 internal inconsistency: the "Error reduction" column for SVR-LSTM (94.86 %) and CNN-LSTM (65.74 %, 26.83 %) cannot be reproduced from RMSE or MAPE in the same rows (0.003 vs 0.001682 gives 43.9 %; 0.02 vs 0.001682 gives 91.6 %; MAPE 2.00 vs 0.17 gives 91.5 %). Column header says RMSE (%), while the proposed RMSE 0.001682 is a fraction (0.17 percentage points, matching MAPE 0.17 %) and other rows (0.325, 3.5656, 0.876) look like percent; if so the proposed model is compared across a factor of 100 in units. I cannot confirm the units from the text.
- Group/condition description contradicts itself: Section 5.3.1 (p.16) says B33 and B34 "were tested at a low temperature of 4 deg C" while Group B is described as the 4 A cells (no temperature given) and Group C as the 4 deg C cells.
- Fig 5 shows SOH going to about 0 at isolated cycles; no cleaning is described; accuracy on those points is presented as robustness.
- No seeds, no spread, no test of significance; no architecture sizes or spline settings; no code: not reproducible.
- No physics prior despite "differential equation-based" wording at Eq. 3; no interpretability claim is demonstrated (no learned spline shown, although Fig 3 suggests it).
- Execution time of 1-3 s is for training/inference on a workstation GPU with unspecified scope; not evidence of BMS real-time suitability.
- A published corrigendum exists (J. Energy Storage 124, 116868); a reviewer will expect us to cite the corrected version if we cite the numbers.

## Gaps and hooks for our paper
- It is the in-journal precedent for "KAN + battery SOH" in JES (vol. 122) but it contains no stress-dependent law, no physics loss, no cross-cell test, no learned-spline interpretation. A KAN whose splines are shown and tested for identifiability across cells is clearly outside it.
- Test to include: our model with and without the previous-cycle capacity input, to show that we do not rely on the channel identified here. (This is a control, not a contribution.)
- Reuse as a comparator only through our own re-implementation with identical inputs and cell-level splits; do not quote its Table 2 numbers.
- Use its limitation statement as motivation: "KAN activation functions are not examined" (the splines are never plotted).

## Code/data availability
No code, no data statement in the preprint. Data: NASA PCoE public set (cells B0005, B0007, B0018, B0033, B0034, B0046-B0048). Published JES version may carry a data statement (not checked).
