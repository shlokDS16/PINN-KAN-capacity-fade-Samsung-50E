# Preregistration v3 (freeze candidate): confirmatory experiments, PINN + KAN calendar-and-cycle ageing (JES)

Status: **v3, NOT YET FROZEN.** Freeze-ready in text; it freezes only when the blockers FB-1 to FB-10 of section 17 are closed, the signatures of section 17.2 are given
and the lead has written `runs/prereg/FROZEN` by the procedure of section 18. Author: experiment-designer (2026-11-05). `PREREG_DRAFT.md` (v0.1) and `PREREG_v2.md` are kept unchanged.
Sources, cited as: "J11" = `debates/D011_prereg/01_judge.md`; "SR" = `runs/prereg/STATS_RULING.md`; "T1" = `runs/prereg/TYPE1_SIGNFLIP.md`; "NC" = `runs/prereg/NEGCONTROL_RULING.md`;
"V3E" = `runs/prereg/V3_EDITS.md` (items 1-10); "J" = D005 judge file; "GA" = `runs/GATE_pilots_audit.md`; "RES" = `runs/build_v1/RESULT.md`; "README" = `code/README.md`; DECISIONS D005-D014.
Read in full for this version: CONTRACT.md, PREREG_v2, V3_EDITS, NEGCONTROL_RULING, TYPE1_SIGNFLIP, STATS_RULING, D011 judge, D013 ruling section 5-7, `code/README.md`, `runs/build_v1/RESULT.md` sections 3-6,
`code/pinnkan/guard.py` (`verify_freeze`, `build_freeze_payload`), `code/data/samsung_checkups.py` (QC functions), DECISIONS D007-D014. No Samsung retention value appears in this file.

Markers. **[FB-n]** a freeze blocker of section 17. **[D]** value fixed at freeze. They must not appear in the frozen text; the freeze procedure strikes them (section 18, step 3).
No coverage, calibration or interval-calibration claim is made anywhere (retired topic).

**What the code is.** The confirmatory code is `code/pinnkan/` (README); every analysis named here is either implemented in it or struck at the freeze (section 17.4). Ids of arms, files and constants below are those of the code.

---

## 1. Claim contract

- **Claim (J§1 as amended by J11 §1.1).** On held-out Samsung 50E cycling conditions (Test B, primary window) the PINN-KAN has lower condition-level retention RMSE than **(i)** the same network without the physics residual (lambda = 0; A9), **(ii)** the same PINN
  with the best alternative stress map (pool A3, A4, A5, A7), and **(iii)** the dataset authors' semi-empirical calendar + cycle model (A10). The comparison with the data-only learners GP-ARD and LightGBM (A11, A12) is a **key secondary**, tested only through a serial gate (9.6).
  "Beats data-driven models" appears nowhere unless that gate is open and the contrast reaches tier S (D007/D009/D011).
- **Estimand (D012).** The primary contrast per held-out condition is L_c = ln(S_comp,c / S_PINN,c); the primary test is the **exact one-sided sign test** on L_c - m; the estimand is the **median condition**. Abstract wording: "on the typical held-out condition (median)"; the relative reduction is 1 - exp(median L_c).
  The mean-based pp difference and mean log ratio with BCa intervals are descriptive (they are not the estimate of the median).
- **Mechanism.** (1) The soft residual holds a shared surface F to a **single state-dependent modulation** of the sum of a time-driven and a throughput-driven rate where there are no data (beyond the window, between conditions, at 35 C storage twins). (2) A hidden-layer KAN
  stress map represents interactions of (T, SOC window, DoD, C_ch, C_dch) without prespecifying them. The law is never called "independent superposition" (D013 (a)).
- **Closest methods and exact distinction.** Stroebl et al. (dataset authors; parametric calendar + cycle superposition fitted to this data; no learned stress maps; A10) and their JES 142, 119552 (states the cycle part is inadequate) **[FB-2]**. PiDDM (arXiv 2607.29095; fixed law, parameters from a small MLP of
  stress; A7; no KAN, no joint storage-cycling training, no held-out-condition protocol as far as the re-audit read). KA-CRNN (JES 158, 121853; KAN-valued Arrhenius parameters of SOC in a neural ODE on thermal-abuse data). PIKAN/PGKAN (SOH estimation, PINN4SOH sets, per-cell life-fraction scaling; not forecasting).
  Zhang JES 182, 125097 (equivalent-circuit parameter evolution with a PINN; cites this dataset) **[FB-1]**: positioning unchecked until read.
- **Competing explanations of a PINN-KAN win** and the control for each: E1 gain from the per-cell latent z_c and window inversion, not physics or KAN: A9 has the same z_c, inputs and inversion; NC-2 (section 10) tests whether stress dependence is needed. E2 gain from capacity or tuning budget: equal trials per arm, grids extended at pilot edges,
  parameter counts reported, `n_train_used` per arm reported. E3 gain from lab/stage/temperature aliasing and non-isothermal check-ups (3.3(7)): the lab/stage rows of 9.8. E4 gain from label-free design-hull information the data-only learners never see: part of the PINN's mechanism and a stated limitation. E5 gain specific to the window, horizon or the training set an arm
  can use: windows k-1, k+2, horizon-wise error, the `n_train_used` row (m6, 3.3(10)).
- **Expected endpoint (J11 §3.1; judge's reading of the files, not a result).** H1b forecasting gap was 0.0-0.1 pp on synthetic G2 (P4) against a minimum detectable gain near 10 % (SR§7, T1); H2 synthetic median ratio 0.96 with one reversal (P5); H1c needs about 17-22 % against learners already at the replicate reference (P3). H6 is the contrast most likely to reach tier S.
  **Most likely: H6 S; H1a S or N; H1b N or none (KAN tie wording); H1c gate closed or unresolved; H2 unresolved, i.e. title 3.** Title 1 needs tier S on all three family members and H2 = A and is rated unlikely. The paper's strength would then rest on the calendar-cycle law, the comparison with the dataset authors' model, the physical checks (11a)
  and the evaluation design. The lead tells Shlok before the freeze (checklist 17.2); his answer changes no rule.
- **Power (T1; assumptions, not Samsung numbers).** Exact sign test, tier S, Holm step 1: n = 40 detects (80 % power) a median relative improvement of about 9-12 % / 12-16 % / 17-22 % when the two arms' condition errors correlate 0.95 / 0.90 / 0.75 (same-model contrasts H1a, H1b at 0.95; different families at 0.75); this replaces the Wilcoxon-based 9.8 / 13.7 / 19.4 %.
  Non-inferiority at true equality (margin 10 %): 0.71-0.95 / 0.40-0.72 / 0.16-0.32 at n = 40. n = 13 (Test C) cannot reach 80 % below 20 % and cannot support a non-inferiority claim: Test C is descriptive. The error correlation for PINN-KAN pairs is an assumption.
- **Abstract rules (SR§6 with D012).** Per primary contrast: n, median condition log ratio expressed as relative reduction with its exact order-statistic 95 % interval, tier (S/N/none), the mean paired pp difference with its BCa interval as a descriptive companion, and PINN-KAN's own score with seed SD. No p-values, no "significant", "outperforms/beats" only at tier S,
  "matches" never, "comparable/equivalent" only after the TOST of 9.6. If the pp-scale tier (D009 margins) differs from the log tier, the abstract states both. Scope words: "held-out cycling conditions of one cell type in three laboratories".

## 2. Hypotheses and the map from hypothesis to test, arms, endpoint, margin, decision row and figure

| ID | Statement | Test (exact one-sided sign test unless stated) | Arms | Scale and margin | Decision row (section 11) | Figure / table |
|---|---|---|---|---|---|---|
| **H1a** primary | residual does work | on L_c = ln(S_A9/S_A1), Holm step level, tiers N then S | A1, A9 | log ratio; S: ln 1.02, N: -ln 1.10 (pp row: 0.02E, 0.10E) | 2, 4, 6, 7 | Fig. 4, Table 1, Table 2 |
| **H1b** primary | KAN does work | A1 vs inner-CV-best of the pool, same rule | A1; pool A3, A4, A5, A7 | same | 1, 4, 6, 7 | Fig. 4, Fig. 5, Table 2 |
| **H6** primary | beats the dataset authors' model | A1 vs A10 (with per-cell factor), same rule | A1, A10 | same | 3, 4, 6, 7 | Fig. 4, Table 1, Fig. 5 (11a) |
| **H1c** key secondary, gatekept | beats the best data-only learner | tested at 0.025 (N then S) only if H1a, H1b, H6 all reach S; else "secondary, not tested" | A1; inner-CV-best of A11, A12 | same | H1c add-on rows | Fig. 4, Table 1 |
| **H2** decision contrast | soft PINN vs hard ODE, same law | order A (reverse of C; gated on the family), C (regardless), B (TOST = two one-sided sign tests at +-ln 1.10), else "unresolved" | A1, A2 | same | 5, 6, 7 | Fig. 4, Fig. 7 |
| **H3** derived | KAN wording against the GAMs | win: H1b tier S against the best of A4, A5 and G2 passes; tie: TOST; worse: reverse tier S | A1; A4, A5 (inner-CV-best) | same | 1, 4, 7 | Fig. 5, Fig. 8 |
| **H4** secondary, **descriptive (D012)** | Test C: held-out temperature-laboratory domain (35 C, INT) | sign tests computed and labelled descriptive; median, interval, positives of 13 | A1, A9, A10, A11, A12 (A1 vs A10; A1 vs best of A11, A12) | same | Test C table | Fig. 3, Table 1 |
| **H5** secondary | storage transfer S2 | one tier-N test at 0.025 (n = 19; 15 positives needed) | A1 vs inner-CV-best of A3, A9, A10 | log ratio, -ln 1.10 | S | Fig. 6, Table 1 |
| **X1** secondary, descriptive | joint vs cycling-only training | interval and unadjusted tier; claim word only "lowered / did not lower" | A1, A13 | same | X1 | Fig. 6, Table 2 |
| **H7** supporting | reduced identifiability on synthetic G0-G2 | thresholds of section 13 | A1, A2, A4, A8 | nRMSE, forecast RMSE | G (positive control), 7 (KAN "win") | Fig. 8 |
| **NC-1** gate | label invariance | bit identity | every arm | max abs difference = 0 | G | Table 2 |
| **NC-2** interpretive | stress dependence needed | one sign test at 0.025 (27 of 40) | A1 (A9 optional) | ln(S_perm/S_real) | wording consequence | Table 2 |
| ISU, SNL | secondary, **not blind** | same rule per dataset: H1a, H1b (pool A4, A5, A7), H6-analogue (cyclic semi-empirical form), H1c unadjusted | per 7.1 | same | none (also holds / does not hold) | Table 1 |

Family-wise level 0.025 one-sided for {H1a, H1b, H6}. Test A, S3, A14 are exploratory (4, 7). Every row above has a test, arms, an endpoint (section 6), a margin (9.2), a decision row and a display item; this map is part of the checklist of 17.2.

## 3. Datasets, inclusion and exclusion

### 3.1 Samsung INR21700-50E (primary; figshare 25975315)
Counted from `experiments_meta.csv`: 279 cells = 132 storage (19 conditions: 10/23/45 C x SOC; the 23 C/0.8 centre point has 4 test points = 24 cells) + 147 cycling (40 conditions; 23 C: 10 conditions / 33 cells; 35 C: 13 / 39; 45 C: 17 / 75; 35 conditions with 3 cells, five centre points
with 6, 6, 9, 9, 12). Storage at 35 C does not exist; cycling at 35 C does.

### 3.2 Cell identity and stage assignment (J11 C5; OPEN-1 closed)
138 of 141 zip names occur in both stages, so a cell is keyed **`cell_id = <serial>_s<stage>`**; the fetcher is stage-aware (folders `<serial>__f<figshare id>`). **One stage rule, the pipeline's** (`runs/samsung_pipeline/folder_mapping.csv`): (1) internal cell serial in the meta text equals `serial_internal` of the design; else (2) laboratory;
else (3) first test date (stage 1: tests from Sep-Oct 2021 to Aug 2022; stage 2: from Jan-Feb 2023); cross-checked with `m_0`/`U_0` of the metadata where present. Disagreement: the cell is **excluded and listed**. Open cases from the pipeline snapshot: TP_z10_01 and TP_z15_01 (meta internal serial contradicts the design table) are resolved
against the dataset paper's tables, else excluded and listed; the empty folder `TP_z02_01__f47631268` is re-fetched, excluded if still empty; any cell unassignable on the complete download is excluded and listed **[FB-4]**.

### 3.3 Inclusion and exclusion (rules; J11 C6, C8)
1. Capacity per check-up = mean of charge (step 21) and discharge (step 22) capacity by trapezoid integration of the current (pipeline `q_mean`). A check-up failing a critical flag below is dropped, not its cell.
2. Reference Q0,c: ET_T23 capacity if ET members exist for every analysed cell, otherwise the first quality-passed CU for every analysed cell (one reference for all; by availability) **[FB-3]**. The current pipeline output is anchored on the first CU (fade before it is unmeasured). Retention = Q / Q0,c.
3. **Pipeline QC flags (critical; set qc_pass false) as implemented in commit 3415db2:** step 21 or 22 missing; step durations out of range (22: 0.45-1.35 h; 21: 0.9-2.8 h); median current off nominal; sampling gap > 60 s inside the step; NaN current; capacity outside 2.0-5.2 Ah; discharge not from >= 4.0 V to <= 2.55 V; charge not to 4.2 V;
   |q_ch - q_dch| / q_dch > 3 %; cell surface temperature at the start of the discharge more than 5 C from 23 C; setpoint not 23 C; start date missing; start dates decreasing with file number; and the **causal isolated-outlier rule** (V3E 5; review m1): with a, b the two preceding valid check-ups, r = max(q_a - q_b, 0) / (days between them) the latest fall rate
   and dt the days since b, check-up i is flagged when **q_i exceeds max(q_a, q_b) by more than 1 % of q_i (rise)**, or when **q_i is below min(q_a, q_b) - 3 x r x dt - 1 % of q_i (fall beyond a time-scaled allowance of three times the latest fall rate)**. The first check-up is never tested, the second for a rise only, and no later check-up enters, so window
   membership never depends on a post-window label and accelerating fade (knees) is not removed. Information flags only: file > 30 h, voltage below 2 V somewhere, capacity rise > 0.5 %, stub runs.
   **Disclosure:** the thresholds were fixed after 163 check-ups of 18 cycling cells (19 cells in total) had been parsed; the outlier rule was revised twice (neighbour range -> causal preceding range -> time-scaled allowance) after the lead inspected which of those check-ups the earlier forms flagged (a per-check-up allowance had flagged a point that matched its
   replicate). No model was scored. The rule depends on capacity; a **sensitivity row retains every check-up**.
4. **Incident handling** from the paper's "Known incidents" list. Dropped at file level: TP_z25_01_01_ET_T45 (undefined load), TP_z01_03_11_CU (concatenated files), TP_z17_03_13_exCU and TP_z17_03_17_CU (incorrect SOC_max), TP_z17_02_19_exCU and TP_k11_02_03_exCU (manual charge), TP_z12_*_31_AT_T45 (aborted; AT is excluded anyway). Retained: TP_k[08-11] ET files
   (the failed capacity cycle was replaced by a repeated measurement). The code drops these by `(serial, file number, kind)` for both stages because the paper does not name the stage (over-drop possible). The second sentence of the paper's advice ("potentially consecutive files": every later check-up of a cell whose cycling segment shows undefined load or a wrong SOC_max, i.e. TP_z24_01_02,
   TP_z25_01_04, TP_z07_03_16, TP_z20_03_16, TP_z17 from segment 18) is **not yet implemented** (`INCIDENT_CONSECUTIVE_DROPS_IMPLEMENTED = False`) **[FB-4]**; it is implemented before the freeze or struck with a change-log row (17.4). Segments with only missing log data keep their check-ups and use the designed throughput for that interval.
5. Pauses (chamber downtime 15 and 20 days, lab downtime 4 days; stage 2) stay on the real calendar axis.
6. Storage cells 01-03 of a test point (66 cells) form the storage trajectories. Cells 04-06 (entry and final tests only) are excluded from training and scoring in the primary; a sensitivity row adds their two-point records. The final test (AT) is excluded from the forecast set (AT capacity at 23 C may deviate because of preceding 10 C and 45 C tests); AT-included is a sensitivity.
7. **Confound and non-isothermal check-ups.** All 39 cells at 35 C were run by lab INT; 45 C is HM (66 cells) and SIE (9); storage 10 C is all SIE and storage 45 C all HM; at 23 C cycling INT runs 6 of the 10 conditions (SIE 3, HM+INT 1). Temperature is aliased with laboratory (and partly with stage) in Test C and S2. The capacity test is also
   **not isothermal**: the cell surface temperature during the 1C discharge averages 31.6 C (stage 1) and 29.8 C (stage 2) in a 23 C chamber, with lab differences (stage 2: SIE 28.3, INT 29.4, HM 32.9 C), so a lab/stage offset can enter the capacity (pipeline item 7). Handling: Fig. 2, the lab/stage rows of 9.8, the CU surface-temperature offsets by lab tabulated beside Test C. No adjustment in the primary models.
8. No cell is excluded because of its capacity trajectory. Cells whose record ends inside the window are scored in a sensitivity row as forecast failures (retention carried forward from the last observation, same rule for every arm).
9. **Retention blinding until the freeze (J11 C8).** Samsung retention values stay in `data/processed/` (gitignored); nothing under `runs/` or any note shows retention by cell or condition; the window rule uses check-up counts only; no plot of Samsung trajectories is made. The code enforces it: any non-confirmatory Samsung request is forced to `timing` (fit seconds and parameter counts only).
   The full parse after the download is a data step, not a look.
10. **Disclosure sentences (printed in the paper; D013 C9, J11 C8, review m6).** (a) "Capacities of 18 cycling cells (163 check-ups) were parsed and quality-checked before the preregistration was frozen, without scoring any model. ISU and SNL were explored in a scratch pilot before their splits were fixed; their results are therefore secondary and not blind."
    (b) "The optimiser recipe (gradient clip, residual warm-up) was fixed after a divergence on a synthetic design; the SNL interaction pairs were fixed from the training-design structure; neither used Samsung data." (c) "The data-only learners (A11, A12) are trained on the cells that have enough window and forecast points (storage cells with fewer than 2 window points at k-1 are dropped); the other
    arms use every cell; the number of training cells used per arm is reported (n_train_used) and the learners' inputs are not claimed identical to those of the neural arms." (d) "All computations ran on CPU, float32, one thread, torch 2.11.0+cu130 (CUDA build executed on CPU), numpy 2.4.2, Python 3.14.3; bitwise reproducibility is claimed on the same machine and library versions only."

### 3.4 ISU-ILCC and SNL (secondary; cyclic term only; "not blind")
Splits already fixed in `runs/splits/` (hash checked by every run). Test B analogue only; the arms of 7.1 without calendar term; A10 replaced by the cyclic power-law form. ISU uses weeks and an analytic cycles-per-week forcing with a 0.5 h rest; the calibration on the 6 fetched `Cycling_json` members is **not done** (stated limitation). The ISU authors' EOL MAPE is reported beside ours. SNL: 61 cells,
the 90-row exclusion of P1. **Forecast set** ends at the first point below 70 % retention for every arm; no arm reads the extent of its own forecast set (tested). Cells whose life ends inside the window are scored as forecast failures in a sensitivity row (same rule as 3.3(8)). The proposer's scratch pilot (`debates/D010_topic/pilot_scratch`) looked at all ISU cells before the splits:
ISU and SNL are labelled **not blind**; claims are "also holds / does not hold", with their own n. **Fallback (J§4, J§8-1):** if Samsung check-ups are not parsed by **07 Nov 09:00**, ISU becomes primary with the same hierarchical sign-test rule for every contrast (H1c is **not** pre-decided as non-inferiority; D007 is superseded by D009), SNL secondary, no calendar arm, fallback title TF and the "not blind" disclosure on the primary.

## 4. Outer splits (Samsung; generated from identifiers only)

Script `code/prereg/make_samsung_splits.py` (reads only `experiments_meta.csv`; dealing routine of P3), output `runs/prereg/samsung_splits_v2.json`, keyed by `cell_id = <serial>_s<stage>` (pinned at freeze under the name `samsung_splits_v2.json`; the loader looks in `runs/splits/` first). Seeds **[D]**: B 20261107, A 20261108, S2 20261109. ISU and SNL split hashes unchanged.

- **Test B (primary): held-out cycling conditions, 5 folds of 8**, stratified over temperature x stress: the five conditions with more than 3 cells are dealt first, one per fold; then per temperature (23, 35, 45 C) conditions are clustered in standardised (SOC_max, DoD, C_ch, C_dch) into ceil(n_T/5) neighbourhoods whose members go to different folds (fewest-so-far, random ties; counts shared across temperatures).
  Conditions per fold at 23/35/45 C and test cells: f0 2/3/3, 33; f1 3/3/2, 27; f2 1/3/4, 30; f3 2/2/4, 27; f4 2/2/4, 30. All storage cells (per 3.3(6)) are in training. Stage and lab are not strata (reported per fold). Fold-block hash prefix `5cde4d3eeeed`.
- **Test C (secondary, descriptive): held-out temperature-laboratory domain (35 C, laboratory INT).** All 13 conditions (39 cells; stage composition from identifiers: 9 conditions stage 1, 4 conditions stage 2) are held out; training = 23 and 45 C cycling (27 conditions, 108 cells) + all storage. **Never called "temperature extrapolation",
  "temperature generalisation", "untested temperature" alone, or interpolation in temperature**: the lab is new to that temperature. INT cells at 23 C are in the training set, which partly separates lab from temperature; the identification of an INT offset holds only under "no lab x temperature interaction", printed with the result. Calendar twins at 35 C are label-free collocation
  (mechanism, `twins: auto`); no sentence presents them as evidence for a temperature response. Hash prefix `a70f9dbef540`. No Test B vs Test C ratio anywhere (retired topic).
- **Test A (exploratory, appendix): held-out replicates.** 3 folds, 49 cells each, every condition keeps >= 2 cells in training per fold; own tuning per fold. Not the paper's question; `R_LOO` (replicate spread) is its yardstick (SR§1.1). Hash prefix `d78537346d43`.
- **S2 storage transfer (secondary).** 19 storage conditions, 5 folds (3, 4, 4, 4, 4) by blocks of consecutive SOC inside each temperature; all cycling cells and the other storage conditions in training; only cells 01-03 of a held-out point are scored. SOC 1.0 and 0.05 are edges; the table also reports SOC <= 0.8 (stage 1 shows non-monotonic behaviour above 80 % SOC); a reporting split, not an exclusion. Hash prefix `a8078f030393`.
- **S3 (exploratory): leave-23-C-storage-out** (7 conditions; train on 10 and 45 C storage + all cycling). No claim, no test.

## 5. Task, window rule, forecast set

- **Task (identical for every arm).** Inputs: stress vector s (cycling: T, SOC_mid, DoD, C_ch, C_dch; storage: T, SOC), Q0,c, window check-ups, throughput rate nu. Output: retention at every later check-up time. Time t_tilde = days since the reference check-up (t_n = days / 500), global scaling only.
- **Throughput.** Inside the window: logged (analytic `efc_est_cum` of the pipeline) equivalent full cycles; after the window: the cell's own mean rate over the window (causal). **Validation rule (fixed now) [FB-5]:** analytic EFC versus ZYK-logged EFC for at least 2 cycling cells per DoD class and per laboratory, at every check-up. Accept analytic throughput iff the median absolute relative
  difference is <= 5 % and no sampled cell exceeds 10 % at its last check-up; otherwise ZYK-logged throughput is used for every cycling cell (`throughput: zyk` is a stub that raises until implemented, so this branch needs code before the freeze, 17.4). An oracle-throughput row is a sensitivity either way.
- **Window rule in check-up counts, from the schedule alone [FB-6].** Count intermediate check-ups (CU + exCU; ET and AT excluded) per cell from the zip member listings (identifiers only). n_med = median over cycling cells; **k_cyc = round(n_med / 3)**, where `round` is Python's (halves go to the even integer; 3.5 gives 4), as implemented in `window_rule_from_counts`; likewise k_sto from storage cells 01-03.
  Primary window = first k check-ups after the reference; secondary k-1 and k+2. Expectation (GA N1): the two listed P0 cycling cells have 8 and 15 intermediate check-ups and the storage cell 7; k_cyc is expected in 3 to 5, k_sto near 2; the code defaults k = 4 and 2 are placeholders until counted.
- **Schedule go/no-go (J§8-3).** If fewer than 3 post-window check-ups exist for most cycling cells at the primary window, Samsung becomes secondary (storage transfer only) and the fallback of 3.4 applies.
- **Forecast set.** For each scored cell: all CU and exCU after the window surviving 3.3, in time order. A cell is scored with at least one such check-up; the number of points per cell is reported; a sensitivity row restricts to cells with >= 3 forecast points.

## 6. Endpoints

- **Primary endpoint (one; judge's endpoint, pp):** cell-level retention RMSE (percentage points) over the forecast set, averaged within condition (mean over the condition's scored cells) then over conditions; Test B, primary window k_cyc, 5 seeds (per-condition value = mean over seeds of that condition's RMSE), frozen configuration. **The primary contrast is the sign test on the log ratio of
  condition scores** (9.3); the pp difference is reported with every tier.
- **Secondary:** windows k-1, k+2; error at fixed horizons after the window; RUL error in days for cells crossing 80 % (n reported); MAE, MAPE, R^2 (correct argument order); Test C, S2, X1; ISU EOL MAPE and SNL analogue; wall clock and parameter count; share of non-finite or diverging forecasts per arm (a non-finite forecast is scored with the persistence error and counted);
  `n_train_used` per arm; `E/R_LOO` and `E/R_WARP` (descriptive, 9.9). The code writes R^2, MAPE, error by horizon and RUL error into the outer-test `metrics.json`.
- **Metrics where a regression is expected:** wall clock and parameter count; error at the first post-window check-up (a data-only learner can be locally better); RUL error (few cells reach 80 %).

## 7. Arms, tuning, budget (J11 §1.3, §1.4; D013; code README)

**Common law and recipe (D013 (a), (b), (d); README "Decisions made while building").** Law: dy/dt = [r_cal(T, SOC) + r_cyc(s) nu(t)] h(y), y_s = 10 (1 - retention), t_n = days / 500, E_n = EFC / 500. **One state factor h per fold shared by the time-driven and the throughput-driven term** ("single state-dependent modulation"; this gives the closed-form integral
y = Psi^-1(a_cal t_n + a_cyc E_n(t)), checked against RK4); it is chosen once per outer fold by a tournament on training conditions with the hard-ODE-KAN at default settings among {constant, self-limiting 1/(1 + y/Y0), accelerating exp(gamma y)} (Y0 = 1, gamma = 0.3), the simplest within one standard error of the best, shared by all law-based arms of that fold.
The per-cell offset delta_c scales the term(s) the cell has (the cycling term for a cycling cell, the calendar term for a storage cell), prior sd TAU = 0.15 fixed. Calendar KAN [1,2] from storage SOC to (a, E) is identical in A3-A7; the calendar term of a cycling cell uses (T, SOC_mid); calendar twins are (T, SOC_mid) of the training cycling conditions (+ the 35 C twins in Test C). Cyclic KAN over
(T, SOC_mid, DoD, C_ch, C_dch); own compact cubic B-spline KAN (`code/models/kan_spline.py`); KAN sparsity (L1 + entropy) is computed on edge parameter magnitudes (a proxy for the activation-based penalty of the KAN literature). Stress inputs are scaled to [-1, 1] with fixed physical ranges (T 5-50 C, SOC 0-1, DoD 0-0.8, C_ch 0-1.2, C_dch 0-2.2) and clamped inside the spline grid.
Solution network F: tanh MLP width 32, depth 3, per-cell latent z_c of dimension 2, hard initial condition; fixed in every F-based arm and not tuned (conservative for the claim; A9 gets a larger space).
**Optimiser recipe (fixed constants of `law.py`, accepted as D013 (d)):** Adam, learning rate 5e-3 with cosine decay, **global gradient-norm clip 20 in every gradient-trained arm (A1, A2, A3-A7, A9, A13, A14)**, residual weight ramped from 0 to lam_res over the first 40 % of the steps in arms with a residual. The recipe was fixed after a divergence on a synthetic design (clip off: data MSE 1.7 and 34 at lam_res 0.1 and 1);
the clipped-step fraction is logged. Collocation sets: (a) record end or whole axis (tuned categorical, below), (b) Latin-hypercube points in the training hull, (c) calendar twins; causal test-time inversion (z_c, delta_c from the window plus the residual over the forecast horizon).
**Where the recipe is a choice, not a result:** the A9/A2 clip, the 40 % warm-up and the 1e-3 grid point were set before any Samsung score; sensitivity rows (k) vary clip {10, 50} and warm-up {0.2, 0.6} for H1a.

**Budget rule.** Every tuned arm gets the same N trials (TPE, sampler seed = outer-fold index) x 3 inner folds grouped by condition and stratified by temperature (SNL: by temperature), inside outer-training conditions only, plus 5 final refits (seeds 0-4); failed trials are redrawn until N valid ones exist (more than max(2, N/4) failures raise).
N = 20; N = 40 if the median fit on a Samsung training fold is under 20 s for every neural arm (J§6). The budget is fixed **before tuning** by one timing fit per neural arm (`auto_budget`, `budget_rule.json`). **Timing run at the freeze commit [FB-8] (D008(a), J11 C3):** if the median hard-ODE fit exceeds 30 s or the PINN fit exceeds 90 s, the J§7 Partial plan
applies to **every arm equally** (trials 20 -> 10, inner folds 3 -> 2, seeds stay 5). Edge-optimum rule: a value at a grid edge extends the grid in the next version.

### 7.1 Arms and spaces

| Arm | What it is | Tuned space (extended at pilot edges) | Dims |
|---|---|---|---|
| A1 PINN-KAN | F + residual; cyclic KAN [5,h,1]; calendar KAN | h {2,3,4,6,8} (P4: 4 in 4/5 = old top); grid {2,3,5,8,12} (P4: 3 and 8, both ends); spline L2 {1e-5..1e-2} (P4: 1e-4 low edge); sparsity {0,1e-4,1e-3,1e-2} (no pilot); **lam_res {1e-3,1e-2,1e-1,1,10,100}** (D013 C3, lead-confirmed: 1e-3 added because the synthetic optimum sat at the old edge 1e-2; P5: 1.0 = old top in 2 of 5); collocation placement {record end, whole axis} | 6 |
| A2 hard-ODE-KAN | same law, closed-form integration (RK4-checked), delta_c MAP from the window, no F; **decision contrast H2** | A1 without lam_res and F; <= 60 nodes per cell | 4 |
| A3 PINN, parametric stress factors ("parametric") | log-linear Arrhenius/power-law factors (Arrhenius abscissa, log C-rates, log DoD, SOC and SOC^2) | ridge L2 {1e-5..1e-1}, lam_res, placement | 3 |
| A4 PINN, additive GAM (= KAN [d,1]) | additive cubic splines | grid {3,5,10,20,30}, L2 {1e-5..1e-1}, lam_res, placement | 4 |
| A5 PINN, interaction GAM | A4 + tensor-product terms; **pair sets per dataset: Samsung the three prespecified pairs T x C_ch, T x SOC_mid, DoD x SOC_mid; ISU all three pairs; SNL (D013 C2) T x discharge plus each chemistry flag x T and x discharge = 7 pairs** (in every SNL Test B training fold the charge rate is constant (0.5 C) and DoD has two levels; fixed from the training-design structure) | A4 space + interaction grid {3,5} | 5 |
| A7 PINN, MLP stress map (**PiDDM-style**) | fixed law, parameters from a small MLP of s | width {4,8,16,32}, depth {1,2,3}, wd {1e-5..1e-2}, lam_res, placement; parameter count capped at the largest in the A1 space | 5 |
| A9 data-only F (lambda = 0) | F, same z_c, inputs, window inversion, **no residual, no law**; **H1a** | width {16,32,64,128}, depth {2,3,4}, wd {1e-5..1e-2}, z dim {1,2,3} | 4 |
| A10 Stroebl semi-empirical (**H6**) | see 7.2 | multi-start least squares, no hyperparameters | 0 |
| A11 GP-ARD, A12 LightGBM (**H1c**) | on (s, window summary, horizon), the P3 learners; A11 fixes m = 4, tau_log = True; A12 fixes subsample 0.8, column 0.8 and a monotone constraint on the horizon (predicted drop does not decrease with horizon) | A11: kernel {RBF, Matern 3/2, 5/2}, noise floor, window-summary set; A12: ranges of `p3_headroom.py`, frozen by commit | 3 / 5 |
| A13 PINN-KAN, cycling cells only (**X1**) | joint-training ablation | as A1 | 6 |
| R1, R2 (no tuning) | persistence of the last window retention; least-squares line through the window | - | - |
| *A6* | **dropped** (21 cross terms on 40 conditions; covered by A5 and A7); text only | | |
| *A8 free G* | **synthetic H7 only** (implemented, `pinnkan/free.py`) | | |
| *A14 PINN-KAN, storage cells only* | **exploratory** (S2 only; first to be cut) | as A1 (calendar part) | 4 |

**Arms by test.** Test B: A1, A2, A3, A4, A5, A7, A9, A10, A11, A12, A13, R1, R2. Test C: A1, A9, A10, A11, A12. S2: A1, A3, A9, A10 (+ A14 exploratory). NC-2: A1 (A9 optional). Test A (exploratory, appendix): A1, A2, A9. Synthetic: A1, A2, A4, A8. LSTM, Transformer, PiDDM reimplementation, BatLiNet/FlowBatt: out.
"PiDDM-style" belongs to A7 only; A3 is "parametric". The confirmatory run of A10 on real data is refused by the code until `semi.A10_FORM["verified"]` is set after [FB-2].
**Comparator selection (no test information).** For H1b the pool arm {A3, A4, A5, A7} with the lowest mean inner-CV score on that fold's training conditions; for H1c the lower of A11/A12; for H3 the lower of A4/A5; for H5 the lower of A3, A9, A10. Selection is per fold and never by outer test error. All pool arms are also reported against A1 (Table 2, descriptive).

### 7.2 A10 fairness (J11 §1.4; D013 (a), (b))
A10 primary = the published form (Stroebl data paper SI S.1.1, after Muehlbauer et al., J. Energy Storage 48, 103803, doi 10.1016/j.est.2021.103803), population parameters by multi-start least squares on the training conditions, **plus one per-cell multiplicative factor on the predicted total loss fitted to the cell's window points by MAP with the same prior family as A1's delta_c**, and the
same throughput input as every arm. **Scope sentence (printed):** A10's factor multiplies the cell's total loss and A10 has two free time exponents, whereas A1's delta_c scales only the term(s) the cell has and the law has one modulation; the difference favours A10. Sensitivity rows: A10 as published (no per-cell factor), and (l) A1 with delta_c on the total rate.
Equations are taken from the SI and the JES 142, 119552 full text with equation numbers recorded **[FB-2]** (the local conversion of the SI is garbled; the provisional form in `semi.py` is refused in confirmatory runs). A10 gets a parameter-recovery unit test on data generated from its own form.

## 8. Seeds

Final refits seeds 0-4 (initialisation and collocation sampling); tuning seed 1000 + outer fold, TPE sampler seed = outer fold. Condition score = mean over seeds of the per-seed condition RMSE, then mean over the condition's scored cells; the seed SD of the cross-condition mean is shown beside every score (reproducibility statement, not a CI). Seeds are never units; no best-seed or best-fold reporting;
no post-hoc seed addition. Limitation: the tuned configuration comes from one TPE search per outer fold, so search-to-search variation is not in the interval; a second search seed on the primary contrasts is an appendix row if compute allows, not a decision input (SR§5).
**Monte Carlo seed rule (D014; NC§5).** The root integer **20261105** is fixed (a date chosen before any scoring, never changed in response to a p-value). Every Monte Carlo step (BCa intervals, bootstraps of sensitivity rows) uses `np.random.default_rng(np.random.SeedSequence([20261105, zlib.crc32(label.encode())]))` with a fixed label such as `"B|H1a|<comparator>|BCa_mean_pp"`;
root, rule and labels are written to `seeds.json` and `contrasts_<test>.json` (`mc_labels`) and the root is part of the config hash (a different root raises `ConfigError`). The stress-permutation stream of NC-2 is `[20261107, 31, fold]` (+1000 for the test side). All pass/fail tests are exact binomial sign tests with no RNG. The earlier placeholder seed of the sign-flip p-value is gone with that test.

## 9. Statistical analysis (D012; J11 §4; SR§2-4; T1)

1. **Unit = held-out condition** (Test B 40, Test C 13, S2 19, ISU 63, SNL 23); equal weight per condition (the five centre conditions are not up-weighted). Paired by condition (both arms scored on the same cells and windows). Neighbour dependence and fold-shared fits are not modelled (stated); per-fold medians and the number of folds with sign agreement are reported.
2. **Margins.** *Log scale (primary):* L_c = ln(S_comp,c / S_PINN,c); superiority margin ln(1.02), non-inferiority margin -ln(1.10). *pp scale (descriptive beside every tier):* delta_S = 0.02 E, delta_N = 0.10 E, E = the comparator's training-side inner-CV condition-mean score, per outer fold, pooled by test-condition count; `runs/prereg/margins.json` (E, deltas, hash)
   is written **after tuning ends and before any final refit is applied to a test condition**. Sensitivity rows: delta_S in {0, 0.05}, delta_N in {0.05, 0.15} (relative). The replicate spread is in no margin or gate.
3. **Primary test (D012; the sign-flip rule is retired).** One-sided **exact sign test** of median(L - m) > 0, i.e. the number of conditions with L_c > m must reach k, binomial(n, 1/2), no RNG. Tier S passes m = ln 1.02; tier N passes m = -ln 1.10 but not S; "none" otherwise. Reported with the exact order-statistic 95 % interval of the median (coverage >= 0.95) and exp(median) - 1. The Wilcoxon and sign-flip rules are appendix-only (they target other estimands).
   Positives needed (T1): n = 40: 28 at 0.025/3, 28 at 0.025/2, 27 at 0.025 (actual size 0.0083 / 0.0083 / 0.0192); n = 19 (S2): 16 at 0.025/3, 15 at 0.025/2 and 0.025; n = 13: 12 at 0.025/3, 11 at 0.025/2 and 0.025.
4. **Type-I verification: DONE, rule changed (T1; FB-7 closed).** The studentized sign-flip permutation test AND BCa bound failed the D011 acceptance (worst ratio 1.86 at n = 40 and 2.14 at n = 13 under the left-skewed ISU mirror; 1.30 / 1.54 under failure contamination); the pre-set fallback (exact sign test) was adopted as D012. The sign test holds its size for any continuous distribution; discreteness costs power
   (size 0.019 at n = 40, level 0.025). Test C is descriptive (a non-inferiority claim has power 0.02-0.22 at n = 13).
5. **Primary family and Holm.** Family {H1a, H1b, H6}, one-sided, family-wise 0.025. Holm step levels 0.025/3, 0.025/2, 0.025 are assigned by ordering the three N-tier p-values; each contrast's S tier is tested at its own step level (nested nulls, N then S at the same level needs no extra correction). Implemented in `pinnkan/stats_step.py`.
6. **Gatekeeping and H2 (J11 §1.1-1.2).** *H1c:* tested at the full 0.025 (tiers N then S) only if H1a, H1b, H6 all reach tier S, and only for the inner-CV-best of A11/A12; else reported with its interval and the label "secondary, not tested", and the abstract may only use the "none" wording for it. *H2* (d = S_hard - S_PINN; same margins, sign tests): order **A** (tier S for the soft PINN; tested only if the family
   passes, i.e. all three tier S), then **C** (reverse tier S; tested regardless, a safety finding), then **B** (TOST: both one-sided sign tests at +-ln 1.10); anything else "unresolved", worded as B. Separate level 0.025, not in the Holm family.
7. **H3.** Against the inner-CV-best of {A4, A5}: win = H1b tier S against that arm and G2 passes (13); tie = TOST at +-ln 1.10; worse = reverse tier S; otherwise unresolved. (`stats_step` does not assemble H3 yet: 17.4.)
8. **Sensitivity rows (appendix).** (a) lab-stratified bootstrap (conditions resampled within lab strata, stratum = majority lab) and the post-stratified mean; (b) mean paired difference per lab and per stage, with n; (c) leave-one-lab-out; (d) two-stage bootstrap (conditions, then cells); weights by scored cells; (e) pp-scale row; (f) **Test C lab-indicator row** (A1, A9, A12 with a lab indicator in the per-cell prior/inputs;
   identified only under "no lab x temperature interaction") and the same lab-and-stage indicator row for Test B; (g) A10 as published; (h) retain-every-check-up (outlier rule off); (i) AT included; storage cells 04-06 included; cells with >= 3 forecast points; forecast-failure rule 3.3(8); oracle throughput; backbone fixed to self-limiting; windows k-1, k+2;
   (j) margin sensitivities of 9.2; **(k) optimiser recipe: clip {10, 50} and warm-up {0.2, 0.6} for H1a; (l) delta scope "total" (delta_c on the total rate, A1); (m) A2-only tournament sensitivity: Y0 {0.5, 2}, gamma {0.15, 0.6}, TAU {0.075, 0.3}; (n) optional appendix row "separate h_cal and h_cyc" for A2 (RK4), descriptive, only if CPU remains after the core set;** no decision uses (n).
   Per fold (D013 C7): tournament table, tuned lam_res with edge share, sd of fitted delta_c on training cells against TAU (flag outside [0.5, 2] x 0.15), clipped-step fraction for A1 and A9 (`diagnostics.json`). If the lab-stratified tier is lower than the primary tier the abstract says so (disclosure, not automatic downgrade).
   Re-open triggers recorded in D013: a non-simplest tournament winner in more than one fold; sd of delta_c outside [0.5, 2] x 0.15 in most folds; tuned lam_res at the lower edge in most folds; a sensitivity row changing a primary tier; the A9 clip moving A9's inner-CV score by more than 10 %.
9. **Reference quantities (descriptive, never margins or gates).** `R_LOO` (replicate spread) and `R_WARP` (window-aware replicate predictor, SR§1.2, the form with the lower training-side median per fold) are computed on training sides after parsing; Table 1 reports `E/R_LOO` and `E/R_WARP`. They decide nothing.
10. **Effect sizes (always shown):** median condition log ratio and relative reduction with the exact interval; mean paired difference in pp with BCa interval (descriptive); share of conditions won; per-fold medians. Other tests: Test C descriptive (computed, labelled); H5 one test at 0.025; X1 unadjusted; exploratory results labelled.

## 10. Controls (D014; NC§3, §6)

- **NC-1 (gate G): label invariance.** Purpose: detect any flow from held-out post-window labels into predictions, tuning or selection. Procedure: every held-out cell's post-window retention is replaced by garbage (`ret_new = ret[w] - k_c (ret[w] - ret) + eps`, k_c ~ U(0.3, 2.5) per cell, eps ~ N(0, 0.02^2), clipped to [0, 1.1]; with a life level L: `ret_new = L + k_c (ret - L) + eps`, so the forecast times are unchanged and asserted),
  applied to the underlying cell object so that any copy carries the same garbage; window points and training cells untouched. **Pass iff** (a) every prediction row of the two runs (all arms, all seeds, same cells and times) is identical, max |difference| = 0 (same machine, same commit, one thread; if a platform ever breaks bitwise reproducibility the tolerance is 1e-12 and a clean-vs-clean repeat must show the same), and (b) `tuning_done.json` and
  `margins_inputs.json` are identical. Any difference trips gate G. Run (1) **before the freeze, mandatory [FB-9]:** `mode: nc1_full` on the synthetic G2 design at Samsung size, the complete pipeline, at the candidate frozen commit, all confirmatory arms, one fold, `nc1_full.json` filed in the checklist; (2) **in every confirmatory run**, after the final predictions, each fitted arm and seed re-predicts from
  windows rebuilt out of scrambled cells and writes `invariance.json`; a difference writes `GATE_G_TRIPPED` and raises `InvarianceError`. The guard's train/test disjointness assertions (cell ids and condition keys) stay and are cited as the real-data analogue of the grouping-error leak. Evidence at demo budgets (NC§4): 0 of 9 clean datasets flagged, 9 of 9 flagged for each of two deliberate leaks.
  NC-1 is blind to what does not flow from labels through the code (human selection after looking, covariate use such as the design hull); stop rule 6 covers the former, E4 the latter. No arm reads the extent of its own forecast set (tested for all 15 arms).
- **NC-2 (interpretive, not gating): do the stress functions carry the gain?** Run A1 (A9 optional) on the Test B folds with the stress vectors (with design throughput) permuted among conditions, separately in training and test (`permute_stress`, Test B only), and compare with the real Test B run: L_c = ln(S_A1,permuted,c / S_A1,real,c), paired by condition. Criterion: exact one-sided sign test of median(L) > 0 at 0.025
  (27 of 40 positive). Consequence: pass licenses the Discussion sentence "the accuracy of the learned law depends on the stress dependence it learns"; fail removes it and the Discussion says stress dependence was not shown necessary for the accuracy (E1). It does not stop the study and changes no tier. Descriptive rows (no criterion): L(A9/A1) under real and permuted stress, scores of A1, A9, R1, R2 under permutation.
  Not run on Test C (power 0.39 at n = 13). The draft criteria (A9 - A1 two-sided p > 0.05; A1 must not beat R2) are withdrawn: a leak-free pipeline is expected to fail them and they do not react to leaks (NC§2, §4).
- **Positive controls.** (P1) Synthetic G0 (well specified): structured arms recover the log-rate surface with nRMSE <= 0.15 and beat A11/A12 on G0 forecast RMSE (paired Wilcoxon p < 0.05, 20 draws); G0 shares choices (a) and (b) with the fitted law, so recovery is a pipeline check and not evidence about real cells (printed). (P2) Real storage cells: the fitted calendar rate increases
  monotonically with temperature at every SOC inside the storage hull (also 11a item 3). (P3) A1 beats R1 (persistence) on Test B with margin 0. A failed positive control also trips gate G.

## 11. Outcomes and consequences (J11 §3.2, §2; D012; D014)

Titles: **T1** "Physics-informed neural networks with Kolmogorov-Arnold stress functions forecast calendar and cycle ageing of lithium-ion cells at untested conditions"; **T2** "Coupling calendar and cycle ageing in a physics-informed Kolmogorov-Arnold network to forecast lithium-ion capacity fade under unseen stress conditions"; **T3** "Learning stress-dependent calendar and cycle ageing laws
of lithium-ion cells with physics-informed neural networks and Kolmogorov-Arnold networks"; **TF** fallback "Physics-informed neural networks with Kolmogorov-Arnold stress functions forecast capacity fade of lithium-ion cells under unseen cycling conditions" (ISU primary). "Identifiable" never appears in a title. Evaluate gate G first, then the first matching row.

| # | Condition | Title | Abstract / highlights wording |
|---|---|---|---|
| G | **NC-1 trips (any prediction, tuning-record or margin-input difference), or a positive control fails, or a test-fold read is found.** NC-2 failing is not a gate. | none | no claim; audit; new version |
| 1 | H1b reverse tier S (KAN worse than the best alternative map) | KAN leaves the title; retitle put to Shlok | "a [winning map] stress model was more accurate than the KAN" |
| 2 | H1a not S (residual no better than lambda = 0) | T3 at most; framing put to Shlok | "the physics residual did not lower the forecast error" plus its interval |
| 3 | H6 not S | T3 at most; lead tells Shlok before writing | "could not be distinguished from" / tier-N wording against "the dataset authors' semi-empirical model"; no "outperforms physics-based models" |
| 4 | H1a S, H6 S, H1b N or none | **T3** | KAN tie wording (J§3): "reached the accuracy of the best prespecified-interaction model without specifying the interactions", with interval; never "outperforms" for the KAN |
| 5 | family all S, H2 = C | framing to Shlok: C1 (judge's recommendation) T2 with "physics-informed Kolmogorov-Arnold network", or C2 T1 wording kept with the hard ODE reported stronger | as J§2 |
| 6 | family all S, H2 = B or unresolved | **T3** | "on the typical held-out condition, lower error than the same network without the residual, the best alternative stress map and the dataset authors' model by X % (CI)"; "the soft residual and exact integration of the same law were [equivalent / not distinguished]" |
| 7 | family all S, H2 = A | **T1** (T2 allowed) | as 6, plus "the soft residual lowered the error relative to exact integration"; KAN "superiority" only if H3 "win" holds |
| H1c add-on (rows 6-7 only; gate open) | S | no title change | "and lower than the best tuned data-driven learner by X % (CI)"; highlights may say "outperformed" |
| | N | no title change | "no more than 10 % worse than the best tuned data-driven learner (one-sided bound ...)"; "comparable" only after TOST |
| | none / gate closed | no title change | "accuracy could not be distinguished from tuned data-driven learners" with interval |
| NC-2 | pass / fail | no title change | pass: the Discussion sentence of section 10; fail: the sentence is removed and the limitation stated |
| S, X1 | S2 (H5 non-inferior: storage sentence allowed, else removed); X1 (descriptive) | no title change | as SR§6 |

**Test C wording (H4, descriptive by D012).** Title: never mentions 35 C or temperature. Abstract: may carry at most one sentence, "on a held-out combination of temperature and laboratory (35 C cells from one laboratory, n = 13 conditions) the median condition error ratio against [A10 / the best data-driven learner] was X (interval; k of 13 below)", followed in the same sentence by "temperature and laboratory cannot be separated in this design";
no tier word, whatever the direction. If the sentence is omitted from the abstract for space, Table 1, the Results paragraph and a Limitations sentence report it with intervals (no selective omission from the paper).

All tier words follow SR§6. Every abstract number is a median-based relative reduction with its exact 95 % interval and n, plus the pp difference with its BCa interval as a descriptive companion.

**P3 entry (descriptive only; J11 C1).** P3 used (descriptive only); D007 superseded by D009; **no gate**. Ratios of the best flexible learner's inner-CV error to `R_LOO` on training folds: ISU W4 0.90, SNL W100 1.13 (`runs/pilot_P3/RESULT.md`). Samsung: `E/R_LOO` and `E/R_WARP` computed on training sides after parsing, descriptive, in Table 1.

## 11a. Physical validation analyses (secondary, descriptive; no test, no Holm, no claim word beyond "consistent / not consistent"; J11 §6)

1. **Calendar temperature dependence.** Effective activation energy E(SOC) from the calendar KAN with fold x seed envelope, compared with (a) the Arrhenius parameter of the dataset authors' own calendar fit on the same data (labelled "consistency with the semi-empirical fit", not independent validation) and (b) published calendar-ageing activation energies only for cells of the chemistry stated in the dataset paper,
   each with a Crossref-verified DOI and page/table location and comparable SOC, temperature range and protocol; if none is verified, (b) is omitted and the text says so. Printed caveat: storage at 10 C is all SIE and at 45 C all HM, so E(SOC) is lab-confounded; the storage lab composition at 23 C is tabulated.
2. **SOC dependence above 80 %.** The learned storage rate versus SOC at each storage temperature with envelope, and whether it changes slope sign above 0.8; caveat: SOC > 0.8 exists in stage 1 only. The S2 table already splits SOC <= 0.8.
3. **Arrhenius monotonicity** (positive control P2): calendar rate increases with temperature at every SOC inside the storage hull.
4. **Superposition check, counterfactual definition (D013).** For each scored cycling cell and for A1 and A2: the calendar share = y(a_cyc = 0) / y(full), the predicted loss at the last check-up with the throughput-driven coefficient set to zero divided by the full prediction; and the number of cells where the counterfactual calendar loss alone exceeds the observed total fade at the last check-up
   (a physically impossible split). Written to `superposition.csv` (confirmatory runs; computed after scoring).
5. **Direction of cyclic stress effects.** Signs of the cyclic partial dependences versus the signs of the exponents in the dataset authors' cycle model (consistency only), with envelopes. Items 1-5 go to Fig. 5 / Fig. 6 and one appendix table; none enters the outcome table.

## 12. Stop rules

1. Samsung not parsed by 07 Nov 09:00: fallback of 3.4. 2. Schedule go/no-go (section 5). 3. **Gate G of section 11 (NC-1 tripped, positive control failed): stop and audit.** The NC-1 synthetic invariance run at the candidate frozen commit (Samsung-size G2) must already have passed (FB-9) and `invariance.json` must be written in every confirmatory run. 4. A test fold read by any tuning, selection, margin or comparator step: run void (the guard line is in every run script; `SCORED.jsonl` is append-only).
5. Compute: if the projection of section 16 exceeds the agreed cap, cut in this order: **A14, Test A, S3, sensitivity rows, A13 last**; trials and seeds are never reduced (except the equal-for-all Partial plan of section 7). 6. No interim look at outer-test results; each frozen configuration is scored once, after all folds finish. 7. Any rule changed after a Samsung test fold is scored is not allowed (new version, disclosed).

## 13. Identifiability protocol (one figure + appendix; synthetic only; J§6)

- **Design:** real Samsung design (40 + 19 conditions, replicates, cadence and window from section 5) **[FB-6]**; ISU design as in P4/P5. Driver `mode: h7` (`pinnkan/h7.py`) with generators G0-G2 (`pinnkan/synth.py`).
- **Generators** written before any real fit; truth never from model fits. G0 well specified (positive control); G1 misspecified time law (t^z with z depending on T, plus a logistic knee in throughput with stress-shifted onset); G2 non-additive stress law (charge-rate hinge with temperature-shifted threshold, plus DoD x SOC product); optional G3. **G2 strengthened:** the confirmatory G2 uses the upper
  pilot-grid values H = 1.2 and P = 0.8 (P4's additive-GAM class floor 0.05-0.07 is below the 0.15 pass line); chosen after seeing P4 and disclosed; the pilot-strength G2 is a sensitivity. **Validity rule:** computed before fitting any model, a G2 draw is discriminating only if its additive-GAM class floor exceeds 0.15; if the median floor stays below, KAN superiority cannot be claimed from G2 and H3 "win" is unavailable.
- **Constants:** round numbers as in the pilots (median final fade 20 pp, noise 0.5 pp, offset sd 0.15), not matched to Samsung summary statistics (matching needs label-derived scalars before the freeze, forbidden by 3.3(9); departure from J§6 recorded in D011).
- **Metrics:** nRMSE of the recovered log-rate surface on the fixed 500-point hull Latin hypercube divided by the true range (level included; centred reported alongside); Kendall tau of variance-based stress importance; forecast RMSE on held-out conditions.
- **Thresholds (J§6):** pass nRMSE <= 0.15 on G1 and G2, fail > 0.30; structured median <= 0.67 x free-G median and paired Wilcoxon p < 0.05 over 20 draws; KAN lower than additive GAM on strengthened G2, paired p < 0.05; on G0 KAN not above GAM by more than 10 %. The structure claim is stated for the KAN-structured model and extends to "structured" generically only if the GAM also meets 0.67. Interval widths: diagnostic.
  The synthetic generator shares choices (a) (one state modulation) and (b) (per-cell offset on the cell's terms) with the fitted law (D013 C8): recovery on G0/G2 is a pipeline and identifiability check, not evidence about real cells (printed).
- **Hard vs soft on G1:** the H2 contrast on synthetic data (20 draws, paired). A residual-map claim needs a rank-correlation threshold with the true violation surface set by the statistician before optional G3 runs; without it Fig. 7 carries no claim.
- **Size:** 3 generators x 20 draws x 4 models (A1, A2, A4, A8) = 240 fits at the pilot tuning effort (8 trials x 2 inner folds, equal across arms), plus G1 hard vs soft 20 draws. The driver exists; the Kendall-tau metric, the paired thresholds and the 20-draw batch are not yet built (17.4).

## 14. Figures and tables (10 items; JES limit 8-10; forms per BLUEPRINT.md and D-figures)

Inputs produced by the run writer and the statistics step (formats in `code/figures/README.md`): `window.csv`, `reference_values.json`, `stress_functions.json`, `residual_map.npz`, `superposition.csv`, `contrasts_<test>.json`, `reference.json`, `controls.json` (NC-1, NC-2) and the H7 `summary.json` with `surfaces_<gen>.npz`. Synthetic runs carry a watermark.

| Item | Content | Hypotheses |
|---|---|---|
| Fig. 1 | Method schematic (data strip, F/G, KAN stress functions, collocation sets) | mechanism |
| Fig. 2 | Design map: storage and cycling conditions, replicate fade, **lab and stage colouring (confound)** | 3.3(7), H4, E3 |
| Fig. 3 | Forecast overlays at held-out conditions, window shaded, **35 C row boxed and labelled "held-out temperature-laboratory domain"** | H1, H4 |
| Fig. 4 | Forest plot of paired condition-level contrasts: **the median condition log ratio (as relative reduction) with the exact order-statistic interval is the plotted estimate; a column gives the mean paired pp difference with its BCa interval (descriptive); tiers are read from the statistics step** | H1a, H1b, H6, H1c, H2 |
| Fig. 5 | Learned stress functions a(SOC), E(SOC), cyclic partial dependences with envelopes, GAM dashed; carries 11a items 1, 2, 5 | H3, H6 |
| Fig. 6 | Storage transfer parity and storage share of cycled-cell fade; carries 11a items 3, 4 | H5, X1, S3 |
| Fig. 7 | Residual map |R| over (T, SOC) and (C-rate, T) | H2 mechanism |
| Fig. 8 | Synthetic recovery G1, G2 (G0 control) with thresholds 0.15/0.30 | H7, H3 |
| Table 1 | Arms x {Test B, C, S2, ISU, SNL}, mean +- seed SD, tiers (Test C descriptive), time, parameters, `E/R_LOO`, `E/R_WARP` (descriptive); "replicate spread" wording | H1, H4-H6 |
| Table 2 | Ablations and controls: what changes, parameters, delta primary endpoint, pool arms vs A1, **NC-1 and NC-2 rows**, positive controls, X1; one appendix table for 11a | H1b, X1, section 10 |

Appendix: hyperparameter tables, sensitivity rows (9.8), windows, KAN/GAM symbolic rounding, chosen settings per fold, `diagnostics.json` summary, decision log.

## 15. Order of runs, by information per CPU-hour (CPU only; 3 single-thread processes)

1. Analytic and data checks (minutes): stage-aware identity, listings, n_med and k, split hashes, incident handling, Q0 rule, throughput validation. 2. Synthetic G0-G2 and G1 hard vs soft (about 6 CPU-h) and the NC-1 full-pipeline run: positive control, invariance and identifiability before any real fit. 3. Training-side measurements (no outer test): `E`, margins.json, backbone tournament, `R_LOO`/`R_WARP`, Samsung timing at the freeze commit (fixes N).
4. Core of Test B: A1, A9, A10, A3, A4, A5, A7 (H1a, H1b, H6), then A2 (H2), A11/A12 (H1c if the gate opens). 5. NC-2, Test C, A13. 6. S2, sensitivity rows, then ISU and SNL; exploratory Test A, A14, S3 last.

## 16. Compute budget (CPU only, from P2 timings; arithmetic, not a Samsung measurement)

Fits per arm and outer fold = 3N + 5 (N = 20: 65; N = 40: 125). P2 (1 thread, 61 cells; 2,000 Adam steps): PINN 13.3 s at 20 points per cell to 18.9 s at 80, 50.6 s for 279 cells (tiled) at 80 points; hard ODE 11.4 s at 20 nodes, 18.5 s at 40, 38.4 s at 80, 42.0 s for 279 cells at 80 nodes. Expected column uses the low values, ceiling the 279-cell, 80-point values.
3 single-thread processes in parallel, 0.7-0.8 GB RAM each, about 2.5 GB total (3.6 GB free at night, D002); no GPU. The recomputation uses the arms of section 7.1 (7 PINN-type + 1 hard in Test B).

| Block | Outer folds x neural arms | N = 20 expected / ceiling, CPU-h | N = 40 expected / ceiling, CPU-h |
|---|---|---|---|
| Test B | 5 x (A1, A3, A4, A5, A7, A9, A13 + hard A2) | 9.4 / 35.8 | 18.1 / 68.8 |
| Test C | 1 x 2 (A1, A9) | 0.5 / 1.8 | 0.9 / 3.5 |
| S2 | 5 x 3 (A1, A3, A9) | 3.6 / 13.7 | 6.9 / 26.4 |
| NC-2 | 5 x 1 (A1; A9 optional adds the same again) | 1.2 / 4.6 | 2.3 / 8.8 |
| NC-1 full pipeline, synthetic Samsung-size, one fold, clean + scrambled runs (all confirmatory arms) | 2 x 1 fold of Test B | 3.8 / 14.3 | 7.2 / 27.5 |
| NC-1 in every confirmatory run | prediction time only | negligible | negligible |
| Synthetic H7 (scaled from P4 266 s and P5 232 s per draw; pilot tuning effort) | 60 + 20 draws | about 6 | about 6 |
| GP-ARD (ISU W4 log 339-539 s per outer fold), 6 folds | | about 0.9 | about 0.9 |
| LightGBM, A10, R1, R2, exact sign tests, BCa | | negligible | negligible |
| **Core total** | | **about 25 / 77** | **about 42 / 142** |
| Exploratory: Test A (3 x 2 + 1 hard), A14 (5 x 1) | | 3.3 / 12.3 | 6.3 / 23.7 |

Wall clock on 3 processes (core): N = 20 about 8.5 h expected, 26 h ceiling; N = 40 about 14 h expected, 47 h ceiling; with the exploratory arms about 9.6 / 30 h and 16 / 55 h. Not included: sensitivity rows (the lab-indicator rows for A1, A9, A12 on Test B and Test C cost about one NC-2 each, 1-9 CPU-h at N = 20), the smoke re-run at the freeze commit (minutes), ISU and SNL (cyclic only; smaller).
PINN cost falls with data, so inner folds are cheaper than the ceiling.

## 17. Freeze blockers, signatures, code status, rulings recorded

### 17.1 Freeze blockers (hard preconditions; only Shlok can waive one, in a ledger row). All open unless marked closed.
1. **[FB-1] Zhang et al., JES 182, 125097 read in full** (Shlok saves the PDF; paper-reader note per CONTRACT §4; novelty-auditor verdict). If it contains a neural calendar + cycle model with learned stress functions forecasting held-out conditions of this dataset: D005 re-opens, no freeze. If it supplies a comparator or metric on this dataset: added in a later version before the freeze.
2. **[FB-2] Stroebl et al., JES 142, 119552 full text** read and A10's equations fixed (7.2; `A10_FORM["verified"]` set; parameter-recovery test passes); Hallinger et al. SSRN 7417281 read at least in its model and data sections.
3. **[FB-3] Full Samsung data on disk** (Shlok's download), every zip size- and checksum-verified, manifest written; pipeline re-run; ET/exCU members parsed so the Q0 rule (3.3(2)) and window counts can be fixed.
4. **[FB-4] Stage assignment complete for all 279 cells** under 3.2, exclusion list written; incident-file stage mapping and the consecutive-file drops of 3.3(4) implemented or struck.
5. **[FB-5] Throughput validated on a sample** (rule in section 5); if it fails, ZYK-logged throughput for every cycling cell (stub to implement).
6. **[FB-6]** Window rule (k_cyc, k_sto) and the schedule go/no-go evaluated from counts.
7. **[FB-7] CLOSED.** Type-I verification of the primary test was run (T1), failed for the sign-flip rule, and the pre-set exact sign test was adopted (D012); power re-reported (section 1). Evidence: `TYPE1_SIGNFLIP.md`, `stats_ruling/signtest_fallback.json`.
8. **[FB-8]** Samsung training-fold timing run **at the freeze commit** done; N fixed or the Partial plan applied equally to every arm (section 7).
9. **[FB-9]** NC-1 full-pipeline run (`mode: nc1_full`, synthetic Samsung-size G2, all confirmatory arms, one fold) passed **at the candidate frozen commit**; `nc1_full.json` filed (a demo-budget run passed earlier, `build_v1_nc1_full_synth`; it does not count for the freeze commit).
10. **[FB-10]** Smoke re-run of `runs/build_v1` configs at the freeze commit (the code changed after the earlier smoke runs: lam_res grid, clip on A2/A9, QC rule, negative control). Results are not Samsung scores.
D005's date stands: Samsung not parsed by **07 Nov 09:00** means the ISU fallback (with the "not blind" disclosure).

### 17.2 Freeze checklist (the gate auditor ticks each with a file pointer)
- [ ] FB-1 to FB-10 met (FB-7 closed), each with its file; Shlok told the likely outcome (section 1) and the told-on date recorded.
- [ ] This file contains every item of V3_EDITS 1-10 and NC section 6; no [FB-n], [D], "pending" or OPEN marker remains in the frozen text (freeze procedure step 3).
- [ ] Hypothesis map (section 2): every row has test, arms, endpoint, margin, decision row and display item (checked in the consistency table of section 19).
- [ ] Samsung splits copied to `runs/splits/`, hashes recorded; ISU/SNL split hashes unchanged.
- [ ] Grid files, code commit (clean tree), seeds, MC seed root 20261105 and labels recorded; configs of every confirmatory run listed for the pins.
- [ ] A10 parameter-recovery test and the full test suite (205 passed at `f3e0b2f`; re-run at the freeze commit) pass; `test_arm_table_matches_prereg_dimensions` passes against section 7.1.
- [ ] `margins.json` procedure (pp row) and log-scale margins written; test-fold guard line in every run script.
- [ ] **NC-1 synthetic invariance run at the candidate frozen commit (Samsung-size G2) filed; `invariance.json` is produced by every confirmatory run; NC-2 (A1 on permuted stress, Test B) is in the run list.**
- [ ] Disclosure sentences (3.3(10) a-d, A10 scope sentence 7.2, synthetic-circularity sentence 13) in the paper text.
- [ ] Statistician signs sections 6-9 and 16; red team signs sections 1, 10, 11; gate auditor second audit (C9) of this filled file against this checklist.
- [ ] DECISIONS rows complete (D011-D014 and the freeze row).

### 17.3 Rulings recorded
OPEN-1 closed (3.2). OPEN-2 A7 in. OPEN-3 F fixed in PINN arms while A9 gets a larger space (conservative); collocation placement a tuned categorical. OPEN-4 closed (D009; floor is not a margin). OPEN-5 H6 in the family, H1c out (gatekept key secondary). OPEN-6 round synthetic constants accepted. D012 sign test; D013 C1-C9; D014 NC-1/NC-2.

### 17.4 Code status at this version (README, RES §3-6) and what must happen before the freeze
Analysis code that is not in the frozen commit cannot be added afterwards (`verify_freeze` requires HEAD = the frozen commit and a clean tree under `code/` and `runs/prereg/`). Each item below is therefore either **built before the freeze** or **struck from this file by a change-log row** (the lead decides; recommendation in brackets).
- *Built:* data interface with window and forecast rules, guard, run writer, all arms of 7.1, tuning, margins, emit of figure inputs, statistics step (sign test, tiers, Holm, gate, H2, H4 descriptive, H5, ISU/SNL), NC-1 (per run and full pipeline), NC-2, seed rule, H7 driver with A8, secondary metrics (R^2, MAPE, horizon, RUL), blinding.
- *Not built:* ZYK throughput branch [FB-5] (build if the validation fails); consecutive-file incident drops and stage mapping of incident files [FB-4] (build, needs the full download); H3 assembly in `stats_step` (build, small); H7 batch pieces: Kendall-tau importance, paired Wilcoxon thresholds, 20-draw G1 hard-vs-soft batch, positive control "A1 beats A11/A12 on G0" (build; P1 is a gate input);
  physical-validation analyses 11a items 1, 2, 4, 5 (build or strike; item 3 is in the stress-function output); sensitivity rows not implemented: lab-indicator rows, AT-included, forecast-failure rule, lab-stratified bootstraps, two-stage bootstrap (build the lab rows and the forecast-failure row; strike the rest if CPU/time is short); rows (k)-(m) need configs only (`pinn: {clip, warmup}` exists); (n) optional;
  ISU `Cycling_json` calibration (stated limitation, not built).

## 18. Freeze procedure

1. **Close the blockers** of 17.1 and collect the signatures of 17.2; confirm that the working tree is clean under `code/` and `runs/prereg/` (`git status --porcelain --untracked-files=no -- code runs/prereg` empty).
2. **Pins.** Copy `runs/prereg/samsung_splits_v2.json` to `runs/splits/samsung_splits_v2.json` (hashes unchanged); ISU/SNL split files are already in `runs/splits/`. Write `runs/prereg/margins.json` procedure inputs only after tuning (not at freeze). List the JSON config of every confirmatory run (one per outer fold and arm group, with `steps_scale` 1, no `overwrite`).
3. **Final text.** Produce the frozen prereg file: strike every [FB-n] and [D] marker, fill the values (k_cyc, k_sto, N or Partial plan, A10 equation numbers, seeds), set the status line to FROZEN, commit it. The freeze commit is the commit that contains the final prereg text, the splits, the configs and the code. (`PREREG_DEFAULT` in `guard.py` still names PREREG_v2.md; `build_freeze_payload` is therefore called
   with `prereg_file` set to the final file, e.g. `runs/prereg/PREREG_v3.md` or its frozen successor, and FROZEN stores that name.)
4. **Who writes FROZEN.** **The lead** (not the experiment designer, not the statistician, not any code): after the signatures. Nothing in the package writes the file. The lead calls `guard.build_freeze_payload(root, split_keys, config_paths, prereg_file)` with `split_keys = [("samsung","B"), ("samsung","C"), ("samsung","S2"), ("samsung","A"), ("isu","B"), ("snl","B")]` (plus A/S3 entries as run) and the list of confirmatory config paths, and writes the returned dict as JSON to `runs/prereg/FROZEN`.
5. **FROZEN fields** (from `build_freeze_payload`): `commit` (git rev-parse HEAD at the call), `prereg_file`, `prereg_sha256`, `splits` = {"<dataset>:<test>": {`file_sha256`, `fold_hash`}}, `config_sha256s` (canonical hashes of DEFAULTS merged with each config file). The file is committed in the same step only if the commit is the frozen commit itself; the simplest order is: commit everything, call the payload builder, write FROZEN as an untracked flag file (the guard checks tracked files only), run `verify_freeze`. HEAD must then not move until all confirmatory runs finish (a later commit invalidates the freeze, by design).
6. **What the guard then enforces.** `verify_freeze`: FROZEN present; prereg hash equals the pin; HEAD = commit; tracked files under `code/` and `runs/prereg/` clean. `load_split(role="test")` and the scorer call it; the split file and fold-hash pins are checked on every load (training role too); a confirmatory real-data run needs its canonical config hash in `config_sha256s`, `steps_scale = 1`, no `overwrite`, and is appended to
   `runs/prereg/SCORED.jsonl` (a second scoring of the same config is refused; a folder holding `condition_scores.json` is never replaced). Samsung un-blinds only on a valid freeze. At run start `DeviceError` is raised if CUDA is visible.
7. **After scoring.** Run the statistics step (`code/run_pinnkan_stats.py`) on the fold runs; the figure scripts read its outputs. Any rule change after a Samsung test fold is scored is a new version with a change-log row and a disclosure (stop rule 7).

## 19. Change log and consistency check

| Version | Date | Change |
|---|---|---|
| v0.1 DRAFT | 2026-11-05 | first draft |
| v2 | 2026-11-05 | D011 rulings (19 edits) |
| **v3** | 2026-11-05 | freeze candidate; edits below |

| v2 -> v3 edit | Where | Source |
|---|---|---|
| D013 C5 text: backbone sentence (one h, "single state-dependent modulation"), optimiser recipe paragraph (clip 20 on every gradient-trained arm, warm-up 0.4, Adam 5e-3 cosine), A5 pair sets per dataset incl. SNL 7 pairs, A10 scope sentence, 11a item 4 counterfactual share | 7, 7.1, 7.2, 11a | V3E 1; D013 C5; README decisions 1-9 |
| D013 C6 sensitivity rows (k), (l), (m), (n) | 9.8 | V3E 2; D013 C6 |
| lam_res grid includes 1e-3 (A1 stays 6 dimensions) | 7.1 | V3E 3; D013 C3 and lead note |
| D013 C8/C9 wording and disclosure sentences (single modulation, three prespecified pairs, SNL charge-rate sentence, A10 flexibility, synthetic circularity, recipe and pairs fixed without Samsung data), environment sentence | 1, 3.3(10), 7, 7.2, 13 | V3E 4; D013 C8, C9, (e) |
| QC outlier rule as implemented in 3415db2 (rise > 1 % above the max of the 2 preceding; drop beyond 3 x latest fall rate x days + 1 %; causal) with disclosure of the revisions | 3.3(3) | V3E 5; review m1; commit 3415db2 |
| m6 disclosure: A11/A12 drop storage cells with < 2 window points at k-1; `n_train_used` reported; no claim of identical inputs | 3.3(10)(c), 6, 1 (E5) | V3E 6; review m6; RES §4 |
| D012: primary test = exact one-sided sign test, median estimand; sign-flip rule and its seed removed; Test C descriptive; abstract wording "typical held-out condition (median)"; power table of T1; FB-7 closed | 1, 2, 9.3-9.5, 9.10, 11, 14 (Fig. 4), 17.1 | V3E 7; D012; T1 |
| Figure inputs emitted; Fig. 4 estimand (median log ratio + exact interval, mean pp BCa column, tiers from the statistics step) | 14 | V3E 8; figure-smith 1a8c95f; README |
| Smoke re-run at the freeze commit | 17.1 FB-10, 16, 17.2 | V3E 9; RES §4 |
| D014: NC-1 label-invariance gate (per run + full pipeline), NC-2 permuted-stress sign test on Test B, seed rule SeedSequence([20261105, crc32(label)]); section 10, stop rule 3, checklist 17.2, outcome row G | 8, 10, 11, 12, 17.2, 16 | V3E 10; NC §3, §5, §6; D014; RES §6 |
| Code as it stands: arm list, recipe constants, emitted files, code status table | 7, 7.1, 14, 17.4 | README; RES §3-6 |
| Freeze procedure, FROZEN fields, who writes it, pins, clean tree; PREREG_DEFAULT note | 18 | `guard.py` `verify_freeze`, `build_freeze_payload`; J11 §7 |
| Compute table recomputed (NC-2 5 x 1; NC-1 full pipeline added) | 16 | NC §3; RES §6 |
| Hypothesis map table | 2 | lead instruction (consistency) |
| Window rounding rule stated (Python half-to-even) | 5 | RES §3 item 7 |

**Consistency check (done for this version).** (1) Every hypothesis row of section 2 names a test, arms in 7.1, an endpoint (section 6), a margin (9.2), a decision row (section 11) and a display item (section 14): H1a-H6, H1c, H2, H3, H5, X1, H7, NC-1, NC-2 pass; H4 has no decision row beyond the Test C wording because D012 makes it descriptive (intended). (2) H1a-H1b-H6 tiers use the same
margins in 9.2, 9.3 and 11. (3) Arms used by each test in 7.1 equal the arms in the compute table of 16 (Test B 7 + 1, Test C 2 neural, S2 3, NC-2 1). (4) Test C: the v2 Holm-2 and tier wording is replaced by the descriptive rule (D012). (5) Gate G is tripped by NC-1 and the positive controls only (sections 10, 11, 12 agree). (6) Fixed: the v2 control "A1 must not beat R2" and the sign-flip p are removed everywhere. (7) Open mismatches
for the lead: `guard.PREREG_DEFAULT` names v2 (handled in 18.3); H3 is not assembled in `stats_step` and the H7 batch pieces are not built (17.4); positive control P1 and the physical-validation analyses depend on those builds; the ISU H1b pool (A4, A5, A7) differs from the Samsung pool (A3, A4, A5, A7) by the judge's rule (J11 §1.2).
