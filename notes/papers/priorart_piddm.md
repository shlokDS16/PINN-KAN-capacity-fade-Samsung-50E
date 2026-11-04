# Prior art: PiDDM (Chen et al., arXiv 2607.29095)

Extraction by paper-reader, 2026-11-05. Template: CONTRACT section 4. "Paper reports" statements are E2 for the report only, never for truth.

## Citation
Chen Z, Jian R, Sigdel S, Xiong G, Wang J-X, Luo T. "PiDDM: Physics-Informed Differentiable Degradation Modeling for Lithium-Ion Battery State-of-Health Prediction". arXiv:2607.29095v1 [cs.LG], submitted 2026-07-31 (id, title, date and author list verified on the arXiv API on 2026-11-05; the API shows no journal reference and no DOI). A second preprint copy exists on SSRN, doi 10.2139/ssrn.7213804 (Crossref verified: same title, same six authors, issued 2026). Groups: Univ. of Notre Dame (Luo, Wang, Chen), UT Dallas (Jian, Sigdel, Xiong), Cornell (Wang), USA. Corresponding author: Luo.

## Reading depth
Full text, all 28 pages of the PDF (abstract, Sections 1 to 4, references), read end to end from `ROOT/refs/md/arxiv_2607.29095_c.md` (blank-line-stripped markitdown). Eq. (1), Table 3 and Table 4 checked as rendered page images (PDF pages 5, 16, 17, 20) because markitdown garbled them. Figures 1 to 5: captions read, images not viewed. There is no supplement in the PDF and no appendix. Dataset facts for XJTU taken from our own full-text note `notes/papers/33_wang2024.md`.

## Problem and stated contribution
Purely data-driven SOH models extrapolate badly and show non-physical capacity regeneration. The authors put an Arrhenius SEI term plus a throughput/DoD LLI term (Eq. 1) inside the forward model; a network supplies five cycle-dependent kinetic parameters and the capacity is obtained by Euler integration over cycles. Claims: lowest average error against an MLP and the Wang et al. PINN across six protocols (abstract, Table 3), and better extrapolation of the last 10 % of life (Table 4), "avoiding non-physical capacity regeneration".

## Data
- Public XJTU set of Wang et al. (Nat. Commun. 15, 4332, 2024; ref [27] of PiDDM): 55 NCM cells, six protocols (2C, 3C, R2.5, R3, random walk RW, satellite "Sim"). 3C has 15 cells, the other five protocols 8 cells each (Sec. 2.4.6).
- Per our note 33: room temperature, nominal 2000 mAh. PiDDM itself never states the value of T_n it feeds into Eq. (1); Sec. 2.3 says only that T_n and DoD_n "are obtained from the operating protocol". Future work (Sec. 4) lists "time-varying temperature" as an extension, which suggests T was one constant per cell. This is an inference, not a stated fact.
- Inputs: 16 statistical features of the CC and CV charging segment of every cycle (mean, std, kurtosis, skewness, charge time, accumulated charge, slope, entropy descriptors; Sec. 2.3). Known operating variables z_n = (T_n, t_n, DoD_n, Ah_n), none predicted by the network. Initial condition Q_i,0 = first measured capacity of the cell.
- Label: SOH (definition not restated in PiDDM; Wang et al. use Q_k / nominal Q).
- Cycles: all cycles of each cell, one Euler step per cycle.
- No storage or calendar-ageing cells anywhere.

## Model
- Rate law, Eq. (1) (PDF p. 5): dQ/dt = - k_SEI exp(-E_SEI/RT) t^alpha - k_LLI exp(-E_LLI/RT) DoD^b1 Ah^b2. Two summed negative terms: a time-driven Arrhenius term (SEI) and a throughput-driven Arrhenius term (LLI).
- Parameters: k_SEI, k_LLI are global trainable scalars (Sec. 2.3). E_SEI, alpha, E_LLI, b1, b2 are produced per cycle by the network from the 16 features (Sec. 2.3, Fig. 2b). R fixed. No constraint (positivity, range) on the five outputs is stated.
- Network: MLP [16, 60, 60, 60, 5] (Table 1). Integration: forward Euler on the cycle coordinate, Eq. (2) and (3). Capacity is not re-initialised at the 90 % boundary in the extrapolation test (Sec. 2.3).
- How the physics enters: as the structure of the forward model (the network is only a parameter generator), not as a PDE residual. The abstract and conclusion nevertheless say the law is embedded "into the training objective" and "loss function"; the Methods describe no physics loss term for PiDDM, only the supervised capacity discrepancy ("minimizes the discrepancy", end of Sec. 2.3). Treat the loss-function wording as a loose description of the same thing.
- KAN: none. SOC: absent (no SOC variable anywhere in Eq. 1).
- Baselines: MLP [16, 60, 60, 60, 1], and the Wang et al. PINN (solution net [17, 60, 60, 32, 32, 1], dynamics net [35, 60, 60, 1], sine activations, loss weights 0.7 and 20) (Table 1, Sec. 2.4.2).
- Training: Adam, 500 epochs, batch 10000, lr 1e-3 to 2e-4 cosine, 30 warm-up epochs at 2e-3, min-max normalisation from training statistics (Table 2, Sec. 2.4.5). PINN baseline 200 epochs, batch 256, lr 0.01 (Table 2).

## Tuning
Not described. No validation split is mentioned for PiDDM or the MLP; no hyperparameter search; no early stopping criterion. The PINN weights are copied from Wang et al. Whether test cells influenced any choice cannot be ruled out from the text.

## Evaluation
- Split: cell level, fixed. Per protocol, cells 4 and 8 are test, the rest train (3C: cells 4 and 8 test, 13 train; others 1,2,3,5,6,7 train). 43 train and 12 test cells (Sec. 2.4.6). All six protocols appear in training, so the test cells are new cells of seen conditions, not held-out conditions.
- Two settings (Sec. 2.4.6): standard (train on full trajectories of the training cells, test on the 12 test cells) and temporal extrapolation (train on the first 90 % of each training trajectory, evaluate on "the remaining unseen 10 %", Table 4 caption). Sec. 3.2 also says test cells are "complete trajectories spanning" the early and final regions, so it is not stated whether Table 4 scores the last 10 % of test cells only or whole test trajectories integrated from Q_0; the caption says last 10 %.
- Test-time inputs: the 16 charging features of the test cell at every cycle, including every cycle of the extrapolated region (the Euler recursion needs g(theta_n, z_n) at each n), plus Q_0 of the test cell and the true t_n, Ah_n, DoD_n of the whole horizon. So this is not a forecast from early check-ups: future usage data of the test cell are required. The paper does not discuss this.
- Metrics: MAPE, RMSE, MAE, MSE on SOH (Eq. 15 to 18). No naive baseline (e.g. Q_0 carried forward, linear fade), no uncertainty, no seeds, no statistical test; one run per cell as far as the text shows.
- Headline numbers (re-read from the rendered tables):
  - Table 3 (standard), averages over six protocols, PiDDM / PINN / MLP: MAPE 6.6566e-3 / 9.1800e-3 / 1.2434e-2; RMSE 7.7017e-3 / 1.1776e-2 / 1.4508e-2; MAE 6.0917e-3 / 8.4564e-3 / 1.1354e-2; MSE 6.6271e-5 / 1.7702e-4 / 2.4187e-4. Derived by me: PiDDM MSE is 2.7 times lower than PINN and 3.6 times lower than MLP.
  - Exception in Table 3: R2.5, where the PINN has lower MAPE (7.9637e-3 vs 8.0314e-3) and MAE (7.3411e-3 vs 7.4570e-3); the text says so (Sec. 3.1).
  - Table 4 (extrapolation), averages, PiDDM / PINN / MLP: MAPE 8.1930e-3 / 1.0742e-2 / 1.6483e-2; RMSE 9.4475e-3 / 1.4856e-2 / 2.2592e-2; MAE 7.4376e-3 / 9.7129e-3 / 1.4609e-2; MSE 1.1067e-4 / 2.4381e-4 / 8.2631e-4. Derived: 2.2 times lower than PINN, 7.5 times lower than MLP in MSE.
  - Exception in Table 4: R3, where the MLP is best on all four metrics (MSE 1.5786e-4 vs PiDDM 3.4648e-4). The text admits this (Sec. 3.2).
- Claim check, abstract vs tables: "lowest average prediction error" holds for the averages of both tables (mixed per protocol, see exceptions). "Avoiding non-physical capacity regeneration" rests on Fig. 3 and 5 only; the authors state that trajectory instability is "not introduced as an additional quantitative metric" (Sec. 3.2). Status: unquantified.

## Figures
Fig. 1 schematic of the framework; Fig. 2 (a) the rate law, (b) network to five parameters plus global k and known z_n into the differentiable module; Fig. 3 SOH trajectories of MLP, PINN and PiDDM on six protocols (standard test); Fig. 4 schematic of the 90/10 extrapolation protocol; Fig. 5 extrapolated trajectories on six protocols. Visual style not inspected (captions only).

## Ablations done
None in the usual sense. The MLP shares the PiDDM backbone and so acts as a "remove the rate law" comparison (Sec. 2.4.4 says this is the intent), but it also drops the Euler integration, Q_0 anchoring and the t_n, Ah_n inputs, so the contrasts are confounded. No ablation of the SEI term vs the LLI term, no test of the Arrhenius factor, no per-cycle vs global parameters, no feature ablation. No identifiability or parameter-recovery test. The learned E_SEI, alpha, E_LLI, b1, b2 are never shown or interpreted ("effective" parameters, Sec. 2.3).

## Hidden assumptions
- The 16 charging features of every future cycle of the test cell are available (needed for every Euler step).
- Q_0 of the test cell is known and the true t_n, Ah_n, DoD_n are known for the whole horizon.
- A cell-and-cycle-specific E_SEI and E_LLI are meaningful. With T constant per cell, exp(-E/RT) multiplied by the global k is a free per-cycle rate, so k, E and alpha are degenerate (reader's inference; the paper does not test it). This means the "Arrhenius" structure cannot be shown to be doing physical work on this dataset.
- Monotonic fade is the right prior; the authors concede measurement regeneration in R2.5 and lose on MAE there.

## Weaknesses a reviewer would hit
1. Test cells share protocols with training cells; no held-out operating condition, so the "generalise across protocols" motivation is not tested.
2. Test-time need of per-cycle features and future usage: not an early forecast. 12 test cells, one split, no seeds, no uncertainty, no naive baseline.
3. Euler integration anchored on Q_0 plus monotone decay can give small MAPE (about 0.7 %) trivially; no baseline shows the margin is not an artefact of the anchoring.
4. Temperature and SOC are not varied (room temperature XJTU), so the Arrhenius factor is untested; no storage cells; no SOC.
5. Wording inconsistency between "loss function / regularisation" and a forward-model structure.
6. Ambiguity on what Table 4 scores. Code and data "available upon request" only.

## Gaps and hooks for our paper
- Hook 1: PiDDM never varies T or SOC and has no calendar arm; our storage and cycling cells at several T and SOC windows can test whether the learned activation energy is recoverable (a parameter-recovery or profile-likelihood test that PiDDM omits).
- Hook 2: an apples-to-apples comparator is possible: re-implement the Eq. (1) form (Arrhenius t^alpha term plus Arrhenius DoD^b1 Ah^b2 term, per-cycle MLP parameters) on the Stroebl data under our held-out-condition protocol. Hypothesis: it will not forecast unseen conditions from first check-ups because it needs future charging features. Test: report error with future features removed.
- Hook 3: the "MLP vs PiDDM" contrast shows how not to ablate; ours should remove the physics residual and the KAN separately, with the same inputs and integration.
- Hook 4: add a trivial baseline (constant, linear, power-law refit) to every table.

## Code/data availability
"Data and code are available upon request" (Data and code availability statement). XJTU data are public via Wang et al. No repository.

## Exact overlap with our design
Our design: joint calendar (Arrhenius x KAN of storage SOC) plus cycling (throughput term with KAN over T, SOC window, DoD, C_ch, C_dch) law, PINN trained jointly on storage and cycling cells, forecasting held-out conditions from the first check-ups, ablations of residual and KAN.
- Arrhenius temperature factor in a rate law: same in form (Eq. 1, two terms with exp(-E/RT)); partial in function, because PiDDM predicts E per cycle from features.
- Time-driven (calendar-like) term: partial (SEI term k exp(-E/RT) t^alpha, Eq. 1; time-only, no SOC, applied to cycling cells, not fitted to storage cells).
- Calendar arm with SOC dependence: different (no SOC; no storage cells).
- Throughput-driven cycling term: partial (DoD^b1 Ah^b2 with Arrhenius, Eq. 1; no C_ch, C_dch, SOC window or temperature variation).
- Learned stress functions: different in kind (MLP maps 16 charge-curve features to five parameters per cycle, Fig. 2b, Table 1; our functions are of the stress variables).
- KAN: different (none).
- Physics residual / PINN: different (differentiable forward model with Euler integration; no residual loss for PiDDM; the PINN is only the baseline from Wang et al.).
- Joint storage plus cycling training: different.
- Forecast at held-out conditions: different (test cells from seen protocols; Table 3 and Sec. 2.4.6).
- Forecast from early check-ups: different (needs per-cycle features and usage over the whole horizon; extrapolation is the last 10 % of life, Table 4).
- Dataset: different (XJTU 55 NCM, room temperature) from Samsung INR21700-50E storage and cycling cells.
- Identifiability test: different (absent).
- Ablation of physics component: partial (MLP comparison only, confounded).
- Monotone-fade prior: same idea (negative sign in Eq. 1; PINN baseline has a monotonicity penalty).
