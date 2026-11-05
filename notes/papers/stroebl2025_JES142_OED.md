# Stroebl et al. 2025/2026: model-based optimal experimental design on the Samsung 50E ageing data (JES 142, 119552)

Written 2026-11-05 for freeze blocker FB-2 (A10 equations). Template: CONTRACT section 4. Locations: "Sec." = section of the JES article, "Eq." = its equation number,
"SI" = Supplement S.1.1 of the Scientific Data paper (refs/samsung50e_paper/si.md; the local conversion garbles the Greek symbols but keeps the structure).

## Citation
- Florian Stroebl, Florian Schaeufl, Oliver Bohlen, Herbert Palm. "Model-based optimal experimental design for lithium-ion battery aging: Insights from a comprehensive
  multi-stage study with real-world data". Journal of Energy Storage 142, article 119552 (issue date 2026; online 2025). DOI 10.1016/j.est.2025.119552
  (Crossref-verified earlier in the project, see notes/papers/samsung50e_dataset_paper.md). Institute for Sustainable Energy Systems (ISES), Munich University of Applied Sciences, Germany.
  Funding: German Federal Ministry for Economic Affairs and Climate Action, grant 03EI4023A.
- The data come from Stroebl et al., Sci. Data 11, 1020 (2024), doi 10.1038/s41597-024-03859-z (the JES reference [27]); the model and the multi-stage framework from the authors' earlier
  work (refs [26], [41] = Muehlbauer et al., J. Energy Storage 48, 103803).

## Reading depth
reading: **full text** of the article body (Sec. 1 to 5, Appendices A to G, Tables 1, D.2, D.3, figure captions) from `refs/fulltext/ft_stroebl2025_OED_JES142_119552.txt` (publisher HTML saved
2026-11-05 through the institutional access). **Not read:** the figures as images (Fig. 1 to 8, B.9, B.10, C.11, E.12, F.13), so no panel layout or colour statements below; Eq. (23) is
missing from the text conversion (an empty line follows the sentence that introduces it); the reference list is empty in the saved file. SI S.1.1 read in full (local conversion).

## Problem and stated contribution
The paper tests whether parameter-individual optimal experimental design (pi-OED, Fisher-information based) lowers the uncertainty of fitted ageing-model parameters more than a
non-model-based design (full factorial for calendar ageing, conditioned Latin hypercube for cycle ageing) at equal experimental effort, using the real multi-stage campaign (Sec. 1, Sec. 2.4).
Result: a 28 % lower bootstrap standard deviation of the calendar temperature parameter (63.78 against 89.01, Sec. 3.1, Table D.2); for cycle ageing pi-OED increased the uncertainty of the
current-rate parameters (Sec. 3.2, Fig. 7, Table D.3), explained by an inadequate model (R2_adj below 0.95, MAE above the measurement noise, Table 1, Sec. 4.2), insignificant current-rate
terms (leave-one-covariate-out with Mann-Whitney U, Table 1) and non-normal residuals (Fig. F.13). No machine-learning model, no held-out forecast anywhere in the paper.

## Data
- The released Samsung INR21700-50E campaign [27], two stages. The paper does not give a cell or test-point total; it uses **three repeated cells per test point** (cal: "11 of the
  potential 15 combinations with 3 repetitions", 33 channels, Sec. 3.1; cycle: 25 test points x 3 = 75 channels, Sec. 3.2). Three repetitions per point match the calendar cells 01-03 that have
  intermediate check-ups (data paper note); cells 04-06 are not mentioned (inference, not stated).
- Chemistry of the cell is not stated. Labels: relative capacity Q_rel = Q_i/Q0 from the reference performance tests, Q0 from the initial RPT (SI Eq. S.4); the JES text calls the model output
  "relative capacity degradation" (Sec. 3.1) and uses Q_rel for the sum in Eq. (17) (a wording slip: SI S.1 calls it Q_loss,rel, the capacity loss).
- Calendar study: factors T and SOC; T in {10, 23, 45} C, SOC levels {5, 20, 50, 80, 100} % (full factorial grid of 15). **SOC = 100 % was dropped from the model fit** because the ageing
  there is not monotone in SOC (Sec. 3.1 "Experiments (S1)", Fig. C.11b); the fitted range is 5 % to 80 %. Time points are the RPT dates; the virtual experiment uses t = 0, 35, 63, 119, 175,
  231 days (Sec. 4.1), and the SI says "t days", so the time unit is days.
- Cycle study: factors T, SOC_max, C_ch, C_dch, DoD within 23-45 C, 0.2-0.8, 0.05-1.0, 0.05-2.0, 0.2-0.6 (Sec. 3.2). Total cycling data points 959 (S1) + 467 (S2a) + 450 (S2b) = 1876;
  outliers removed 44 + 1 + 3 = 48 (2.56 %), Sec. 3.2. **The sentence "48 of 1876 (2.56 %)" in Sec. 3 before the calendar subsection therefore counts the cycling data points only**; no calendar
  outlier count is given. Outlier rule: that of the data paper.
- Time or cumulative-throughput axis for the cycle model: FEC (fully equivalent cycles), reference value FEC_ref (SI S.3). EOLC, T_ref, SOC_ref, t_ref and every other reference value are **not
  given** in the JES text or the SI (checked: no numeric value anywhere).
- Anomaly screening and batch homogeneity (differential voltage analysis) are delegated to [27] (Sec. 3).

## Model (exact equations; this is the part A10 depends on)
Notation as printed. T in kelvin (inferred from the magnitude of theta_0, thousands, and the Arrhenius form), SOC and SOC_max as fractions or percent (only ratios to a reference enter),
t in days, C-rates in 1/h, FEC dimensionless.

| # | Equation | Location |
|---|---|---|
| 17 | Q_loss = Q_cal + Q_cyc (linear superposition of independent calendar and cycle losses; the paper calls this "simplified", path dependence ignored) | JES Eq. (17), Sec. 3; SI Eq. S.1 |
| 18 | Q_cal(T, SOC, t) = (1 - EOLC) * exp(-th0 * (1/T - 1/T_ref)) * (SOC/SOC_ref)^(1/th1) * (t/t_ref)^th2 ; theta_cal = (th0, th1, th2) | JES Eq. (18), Sec. 3.1; SI Eq. S.2 |
| 21 / S.3 | Q_cyc(T, SOC_max, C_ch, C_dch, DoD, FEC) = (1 - EOLC) * exp(-th0 * (1/T - 1/T_ref)) * (SOC_max/ref)^(1/th1) * (C_ch/ref)^(1/th2) * (C_dch/ref)^(1/th3) * (DoD/ref)^(1/th4) * (FEC/FEC_ref)^th5 ; theta_cyc = (th0 ... th5) | **SI Eq. S.3**. JES Eq. (21), Sec. 3.2, as extracted, prints the exponents of C_ch, C_dch, DoD as th2, th3, th4 (no reciprocal) and only SOC_max with 1/th1. **Source conflict, see M6.** |
| 23 | the cycle model without C_ch and C_dch (LOCO reduced model) | Sec. 4.2, text missing in the conversion; structure inferred only |

Parameter meaning (Sec. 3.1, 3.2): th0 temperature (Arrhenius-like activation term, units K); th1 SOC (or SOC_max) sensitivity, th1 = 1 linear in SOC; calendar th2 time exponent, 0.5 = square
root of time; cyc th2, th3 current-rate effects, th4 DoD, th5 charge-throughput exponent. "Q_cal describes the loss up to the defined end of life"; the factor (1 - EOLC) fixes the loss at the
reference conditions (it equals the allowed loss when all ratios are 1). The cycle model has no explicit time term: elapsed time enters only through FEC.

Published parameter values (Appendix D; bootstrap SD in parentheses; case 1 = S1, case 2 = S1 + S2a (non-OED), case 3 = S1 + S2b (pi-OED)):
- Table D.2 (calendar): th0 = 4894 (103.6), 3701 (89.01), 3941 (63.78); th1 = 0.840 (0.025), 0.800 (0.025), 0.820 (0.024); th2 = 0.580 (0.015), 0.610 (0.017), 0.580 (0.012).
- Table D.3 (cycle): th0 = 1318 (59.42), 1537 (62.54), 1115 (72.27); th1 = 0.940 (0.037), 1.230 (0.050), 0.870 (0.043); th2 = 19.05 (57.60), 9.550 (2.099), 14.10 (38.03);
  th3 = -12.81 (2.721), -21.63 (32.51), -284.6 (399.6); th4 = 2.07 (0.090), 2.500 (0.117), 1.500 (0.084); th5 = 0.600 (0.013), 0.520 (0.014), 0.510 (0.008).
- Units are not printed. Reading th0 as an activation temperature E_a/R in kelvin gives (arithmetic, not a statement of the paper) E_a about 40.7, 30.8, 32.8 kJ/mol for the calendar cases and
  about 11.0, 12.8, 9.3 kJ/mol for the cycle cases. The calendar th0 estimates of cases 1 and 2/3 differ by more than 4 sigma (Sec. 4.1, "Non-overlapping distributions"); the authors attribute
  this to non-converged estimators (assumption R3 violated) with a virtual experiment (true th = (5000, 0.87, 0.67), sigma 0.002, Fig. 8).
- Magnitude check for the exponent convention: with exponent th2 = 9.55 on C_ch/ref, a rate ratio of 0.05 gives 4e-13 and with th3 = -21.6 on C_dch ratio 0.05 gives 1e28; with 1/th the
  same values give 0.73 and 1.15, consistent with the paper's finding that the current rates do not matter (Sec. 4.2, Table 1: p_MWU 0.76 to 0.98, rho_s above 0.995). This supports the SI form.

## Fitting procedure
- Estimator: maximum likelihood, which for iid normal noise is least squares on the model-minus-measurement residuals of the relative capacity (Eq. 3, 4); calendar and cycle models are fitted
  **separately** on their own cells (Sec. 3.1, 3.2); the cycle model is fitted directly to the cycling cells' capacity loss, no calendar loss is subtracted (nothing of the kind is described).
- Uncertainty: Fisher information matrix and Cramer-Rao bound (Eq. 5-8, 13, 19) and **blockwise bootstrap with n_BS = 10,000** (Eq. 9, 10; Sec. 3.1). OED: Eq. 11, 12, 15 (pi-OED minimises
  the diagonal element of the inverse FIM), Eq. 20 (calendar, th0) and Eq. 22 (cycle, sum of variances of th2 and th3).
- Outliers excluded before fitting (see Data). Normality of measurement errors tested by Shapiro-Wilk (Fig. E.12 holds for calendar, Fig. F.13 fails for cycle). Assumptions R1-R3 (model
  correct and non-redundant; homoscedastic normal noise; stage-1 estimate near the truth) stated after Eq. 16.
- Not reported: optimiser, starting values, parameter bounds, number of restarts, software, code (the code link of the data paper is not in this article), the reference values and EOLC.

## Tuning
No hyperparameters. The only choices fixed beforehand: which parameters to optimise (largest relative FI standard deviation, Fig. 4 and Fig. 6; calendar th0 at 4.46 %, cycle th2 23.8 % and
th3 9.5 %), the SOC range of the calendar fit, outlier removal. No held-out data; every fit and metric is in-sample (Tables 1, D.2, D.3).

## Evaluation
- Criterion of the paper's main claim: Eq. (16), bootstrap SD of case 3 below case 2. Calendar th0: 63.78 against 89.01 (28 % lower), Fig. 5, Table D.2. Cycle th2: 2.099 (case 2) to 38.03
  (case 3); th3: 32.51 to 399.6, Fig. 7, Table D.3. Single realisation of the campaign; no repeated draws; the paper's own virtual experiment shows 4 sigma disagreements between designs
  under a correct model (Sec. 4.1, Fig. 8).
- Model validity (Sec. 4.2, Table 1, cycle model with all factors / without C_ch, C_dch): R2_adj 0.9255 / 0.9187 (case 1), 0.8731 / 0.8660 (case 2), 0.8271 / 0.8199 (case 3); RMSE
  0.0042 / 0.0044, 0.0051 / 0.0052, 0.0077 / 0.0079; MAE 0.0030 / 0.0032, 0.0036 / 0.0037, 0.0047 / 0.0045; Spearman rho_s of the two residual sets 0.9974, 0.9977, 0.9986; MWU p
  0.7645, 0.7969, 0.9796. Validity rule used: R2_adj above 0.95 and MAE at the size of the measurement error (sigma_exp = 0.00274), cited to [13]. The cycle model fails both; the calendar model's
  validity metrics are not tabulated. (Reading of the two column groups as full and reduced model follows the sentence below Table 1; the extracted header is ambiguous.)
- Seeds: none (deterministic fits); bootstrap n = 10,000. Statistical tests: Shapiro-Wilk (alpha 0.05), Mann-Whitney U (alpha 0.05), Spearman rho_s.
- No forecasting task, no split into training and test cells, no cross-validation.

## Figures
Figures were not viewed (text only); captions only. Fig. 1 schematic of the reference process (cases 1-3); Fig. 2 flowchart of the evaluation process; Fig. 3 (a-f) relative-capacity
trajectories of all cells per stage: calendar S1, S2a, S2b; cycle S1, S2a, S2b; Fig. 4 and Fig. 6 relative FI standard deviations per parameter (calendar, cycle); Fig. 5 and Fig. 7 bootstrap and
FI standard deviations for the targeted parameters over cases 1-3; Fig. 8 two bootstrap distributions separated by more than 4 sigma in a virtual experiment (iterations 141 and 333);
Fig. B.9, B.10 design-of-experiment scatter plots per stage (dots stage 1, crosses stage 2; axes normalised 0-1); Fig. C.11 relative capacity over T and over SOC, colour intensity with RPT
number; Fig. E.12, F.13 Shapiro-Wilk p-values per check-up and case. Table 1 validity metrics; Tables D.2 and D.3 parameter estimates with bootstrap SD. Visual style: not assessed.

## Ablations
Leave-one-covariate-out of C_ch and C_dch (Sec. 4.2, Table 1, Eq. 23). Virtual (simulated) experiment for estimator non-convergence (Sec. 4.1, Fig. 8). Case 1/2/3 comparison is the main
design contrast. No ablation of the superposition or of other factors.

## Hidden assumptions
- The joint model is a linear sum of independent terms (Eq. 17) while the two terms are fitted on different cells and the cycle term is fitted to total loss of cycling cells, so calendar loss of
  cycling cells sits inside Q_cyc in the published fits (inference from the absence of any subtraction).
- Unreported reference values and EOLC fix the scale; the published th values are meaningful only with those references (the scale is not identifiable from the paper alone).
- Homoscedastic normal noise (R2): rejected by the authors for the cycle data (Fig. F.13).
- Single cell batch per stage; stage 2 used a new batch (data paper note), so stage and batch are confounded.
- Calendar fit excludes 100 % SOC; the cycle design stays within 20-80 % SOC_max, 23-45 C.

## Weaknesses a reviewer would hit (for use of A10 as a baseline)
- The authors' cycle model does not meet their own validity criteria, in-sample (Table 1); an A10 baseline inherits that and is a deliberately modest baseline.
- Parameters are not converged even for the calendar model (4 sigma shifts between cases); published values are not stable targets for a "recovery" claim on real data.
- The C-rate parameters are poorly identified (SD larger than the value in cases 1 and 3, Table D.3); any comparison of effect signs for C_ch and C_dch against A10 is not informative.
- Exponent convention conflict between SI S.3 and JES Eq. (21) (M6).
- Reference values, EOLC, optimiser and bounds unreported; the code is not in this article.

## Conditions: "71" against 59
- The JES article never states a number of test points, cells or conditions (checked: no occurrence of 71, 59, 93 or 279 in the text). The figure 71 is the data paper's abstract (22 calendar
  + 49 cycle test points; notes/papers/samsung50e_dataset_paper.md), the figure 93 its Background text.
- Released metadata (`data/raw/samsung50e_meta/experiments_meta.csv`, metadata only, no capacity values read), counted by this note with test points identified by (type, tp, stage):
  calendar 22 test points but 19 distinct (T, SOC) conditions; cycle 49 test points but 40 distinct (T, SOC_max, DoD, C_ch, C_dch) conditions; 19 + 40 = 59 distinct, 71 - 59 = 12.
  The 12 duplicates are all stage 2: the calendar pi-OED has 4 test points on a single condition (3 duplicates), the cycle pi-OED 12 test points on 4 conditions (8 duplicates), and the
  stage-2 cLH sampling one pair of identical conditions (1 duplicate). Stage 1 and stage 2 share no condition.
- The JES text supports the calendar part ("the pi-OED design repeats one test point multiple times", Sec. 3.1 Experiments S2b); for the cycle part it only says the pi-OED chose more stressful
  conditions (Sec. 3.2 Experiments S2b), the repeats are an observation from the metadata. So: 71 counts test points (repeats counted), 59 counts distinct conditions. Not resolved by the text:
  the JES calendar sub-stage S2a is described as completing the 15-point factorial grid and as equal in size to the 4-point pi-OED, whereas the metadata labels stage-2 calendar points as
  3 "FF", 4 "manual" and 4 "pi" (the JES figure note says manual sampling was not used); which 4 test points form S2a cannot be told from the text.

## Gaps and hooks for our paper (concrete, testable)
- A10 is a weak cycle baseline by its authors' own validity rule (R2_adj 0.83-0.93, RMSE 0.42-0.77 pp of Q0 in-sample, Table 1); report A10 with the two forms already preregistered (7.2) and
  quote this as context, not as our result.
- Prereg physical-validation item 5 (sign of the cyclic effects against A10): compare signs only for T, SOC_max and DoD; the authors find C_ch and C_dch statistically insignificant
  (Sec. 4.2), so a sign agreement or disagreement on those two carries no information. Item 1(a) (activation energy): the published calendar th0 corresponds to about 31 to 41 kJ/mol
  (arithmetic above), a reference range from the authors' own fit that the A1 envelope can be set beside, labelled as such.
- The authors drop SOC = 100 % from the calendar fit because their form is monotone in SOC; our arms keep it (non-monotone calendar SOC law). A10 trained with and without SOC = 100 %
  storage is a cheap sensitivity row that states what the authors did (M5).
- Time-dependent calendar exponent 0.58 to 0.61 (Table D.2) and FEC exponent 0.51 to 0.60 (Table D.3): both sub-linear, consistent with a self-limiting law; the cycle model has no time term.

## Code/data availability
Data: figshare doi 10.6084/m9.figshare.25975315 (CC BY 4.0, per the data paper). No code for this article is mentioned in the text read (the repository of the data paper is separate and its
contents were not read).

---

## A10 FORM vs PAPER: comparison, equation by equation (FB-2)
Code: `code/pinnkan/semi.py` (`SemiForm.loss`). Reference implementations of the paper's equations and the parameter map are in `code/tests/test_pk_a10_paper_form.py`.

| Piece | Paper | Code | Verdict |
|---|---|---|---|
| Superposition | Q = Q_cal + Q_cyc, Eq. (17), S.1 | `loss` returns `q + cyc term`; cycling cells get both terms | match |
| Calendar temperature | exp(-th0 (1/T - 1/T_ref)), T in K | exp(-p0 1e4 (1/T - 1/298.15))^(1/r); th0 = p0 1e4 / r | match under the map (T_ref shift absorbed in lc) |
| Calendar SOC | (SOC/SOC_ref)^(1/th1) | (SOC/0.5)^(p1/r); 1/th1 = p1/r | match under the map |
| Calendar time | (t/t_ref)^th2, th2 about 0.58 | t_n^(1/r), t in days, t_n = t/500; th2 = 1/r, r in [0.3, 5] so th2 in [0.2, 3.3] | match under the map |
| Calendar scale | (1 - EOLC), fixed | exp(lc_cal) free | **M1**: superset; published form nested |
| Cycle temperature | exp(-th0 (1/T - 1/T_ref)) | same construction with q0 | match under the map |
| Cycle factors | SOC_max, C_ch, C_dch, DoD, each a power of the ratio to a reference | features (SOC_mid + DoD/2 = SOC_max, C_ch, C_dch, DoD), refs (0.5, 0.5, 1.0, 0.3), free exponents q_j/r | match (feature order and SOC_max = SOC_mid + DoD/2 checked) |
| Cycle FEC | (FEC/FEC_ref)^th5, th5 about 0.5-0.6 | E_n^(1/r_cyc), E_n = EFC/500 | match under the map |
| Cycle scale | (1 - EOLC), fixed | exp(lc_cyc) free | **M1** |
| Exponent form | independent exponents per factor | common 1/r on the bracket | **M2**: same function class (re-parameterisation, bijective); bounds differ; no transcription error |
| Activation energy used in emit.py | E_a = th0 R | theta[1] 1e4 / theta[3] R (= p0 1e4 / r R) | correct |
| Fit | cal on storage, cyc on cycling, separately; LS/MLE | one joint least squares of both terms, multi-start TRF | **M3** |
| Calendar term of a cycling cell | not specified (only the superposition) | ambient T, SOC_mid, elapsed days | **M4**: unspecified in the paper |
| SOC = 100 % storage, outliers | excluded from the calendar fit (Sec. 3.1); outlier rule of [27] | no filter in semi.py | **M5**: data-layer matter |
| Exponent convention for C_ch, C_dch, DoD | SI S.3: 1/th_j; JES Eq. (21) as extracted: th_j | free q_j | **M6**: source conflict; function class unaffected |
| Eq. (17) wording | JES calls Q_rel relative capacity; SI calls it loss | retention loss | **M7**: JES wording slip |
| EOLC, T_ref, SOC_ref, t_ref, FEC_ref, bounds, starts | not published | absorbed in lc; bounds/starts are the code's | **M8** |

**No unambiguous transcription error was found, so no production code was changed except the status flag and comments.** The one place where a different reading would matter in practice is M6;
it changes how published parameter values map to the code (tested for both conventions) but not what the code can fit.

### Recovery test (no Samsung labels)
`code/tests/test_pk_a10_paper_form.py` (8 tests) and `code/pilots/fb2_a10_recovery.py` (writes `runs/fb2_a10/metrics.json`): data generated from the paper's Eq. (18) and S.3 with the
published Table D.2 case 3 and Table D.3 case 2 values (reference values and EOLC = 0.8 are test conventions because the paper does not give them), on the synthetic stress design (stress
ranges only). Hand-worked inputs reproduce Eq. (18) (0.258326) and S.3 (0.151008) from first principles. Noise-free: maximum relative parameter error 1.4e-14, cost 1.6e-30.
With sigma = 0.00274 (the paper's sigma_exp): maximum relative error in code parameters 0.030, RMSE of loss against the true loss 3.0e-4 (about 0.11 sigma). See `runs/fb2_a10/metrics.json`.

---

## Note for the novelty auditor: does Stroebl JES 142 contain a learning curve of a learned forecaster?
1. **No.** The article contains no learned model and no held-out forecast (reading: full text of the body).
2. The only model is the parametric semi-empirical calendar and cycle model of Eq. (18) and Eq. (21), fitted by least squares; its figures of merit are in-sample (Table 1, Tables D.2, D.3).
3. The nearest thing to a "more data" curve: Fig. 5 and Fig. 7 (bootstrap and Fisher standard deviations of selected parameters over cases 1, 2, 3 = S1, S1 + S2a, S1 + S2b).
   That is estimator uncertainty against experimental design, not forecast error against training size.
4. Table 1 gives R2_adj, RMSE, MAE of the cycle model over the same three cases (in-sample fit; the fit gets worse with more data: RMSE 0.0042, 0.0051, 0.0077).
5. Fig. 3 (a-f) shows the capacity trajectories only; Fig. 8 is a simulated-estimator experiment (Sec. 4.1).
6. No neural network, PINN or KAN; the outlook (Sec. 5) names mechanistic ageing models as future work, not machine learning.
7. No data-efficiency or few-condition forecast result, no held-out-condition protocol, no early-life prediction from a short window.
8. Not checked: the figures as images and Eq. (23); neither can change the answer (no learned model is mentioned in the text).
9. Consequence for our novelty statement: the closest data-efficiency content is OED of the experiment design for a fixed parametric model (28 % lower calendar th0 SD), a different object.
10. Companion paper to check separately if wanted: the IEEE Access 2024 paper (doi 10.1109/ACCESS.2024.3446234) was not read.
