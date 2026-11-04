# Preregistration v2 (pre-freeze): confirmatory experiments, PINN + KAN calendar-and-cycle ageing (JES)

Status: **v2, NOT FROZEN** (2026-11-05). Author: experiment-designer. Supersedes `PREREG_DRAFT.md` (v0.1, kept unchanged).
Applies the 19 edits of `debates/D011_prereg/01_judge.md` section 8 (cited "J11§n"); the change log (section 19) maps each edit to its source.
Other sources cited: "SR§n" = `runs/prereg/STATS_RULING.md`; "GA Cn" = `runs/GATE_pilots_audit.md`; "Cx§n" = `debates/codex_panel/turn03_response.md`;
"J§n" = D005 judge file `debates/D010_topic/04_judge.md`; "PD§n" = `PREREG_DRAFT.md`; DECISIONS D005-D011.
Basis (read in full): CONTRACT.md; D005 judge file; STATS_RULING; GATE_pilots_audit; D011 judge file; PREREG_DRAFT; `runs/samsung_pipeline/RESULT.md`
and `folder_mapping.csv`/`issues.csv`; P0-P5 RESULT files. **P3 used (descriptive only)**; no gate. No Samsung retention value appears in this file.

Markers. **[FB-n]** a freeze blocker of section 17 (n = precondition number). **[R]** rule whose value is computed from training-side data
before confirmatory runs. **[D]** draft value fixed at freeze. The old markers [a], [b], [c] and OPEN-n are closed (section 17.3) or replaced
by [FB-n]; the frozen file must contain none of [FB-n], [D], "pending".
No coverage, calibration or interval-calibration claim is made anywhere (retired topic).

**Freeze blockers (judge's list, section 17):** [FB-1] Zhang JES 182, 125097 read in full, and [FB-2] Stroebl JES 142, 119552 read (A10 equations
fixed; Hallinger SSRN 7417281 model/data sections read); [FB-3] full Samsung download with manifest and [FB-4] stage assignment of all 279 cells;
[FB-5] ZYK throughput check; [FB-6] window counts; [FB-7] type-I simulation of the sign-flip test (and power re-report); [FB-8] Samsung training-fold
timing run. Second gate audit (C9) and statistician/red-team signatures follow.

---

## 1. Claim contract

- **Claim (amends J§1 (iii); J11§1.1).** On held-out Samsung 50E cycling conditions (Test B, primary window) the PINN-KAN has lower condition-level
  retention RMSE than **(i)** the same network without the physics residual (lambda = 0), **(ii)** the same PINN with the best alternative stress map,
  and **(iii) the dataset authors' semi-empirical calendar + cycle model (A10)**. The comparison with data-only learners (GP-ARD, LightGBM) is a
  **key secondary**, tested only through a serial gate (section 9.6). "Beats data-driven models" appears nowhere unless that gate is open and the
  contrast reaches tier S (D007/D009/D011 consequence).
- **Mechanism.** (1) The soft residual holds a shared surface F to a time-driven plus throughput-driven law where there are no data (beyond the window,
  between conditions, at 35 C storage twins). (2) A hidden-layer KAN stress map represents interactions of (T, SOC window, DoD, C_ch, C_dch) without
  prespecifying them.
- **Closest methods and exact distinction.** Stroebl et al. (dataset authors; parametric calendar + cycle superposition fitted to this data; no
  learned stress maps; arm A10) and their JES 142, 119552 (states the cycle part is inadequate) **[FB-2]**. PiDDM (arXiv 2607.29095; fixed law,
  parameters from a small MLP of stress; arm A7; no KAN, no joint storage-cycling training, no held-out-condition protocol as far as the re-audit
  read). KA-CRNN (JES 158, 121853; KAN-valued Arrhenius parameters of SOC in a neural ODE on thermal-abuse data). PIKAN/PGKAN (SOH estimation, PINN4SOH
  sets, per-cell life-fraction scaling; not forecasting). Zhang JES 182, 125097 (title: equivalent-circuit parameter evolution with a PINN; cites this
  dataset) **[FB-1]**: positioning unchecked until read.
- **Competing explanations of a PINN-KAN win** and the control for each: E1 gain from the per-cell latent z_c and window inversion, not physics or KAN:
  data-only F has the same z_c, inputs, inversion (A9). E2 gain from capacity or tuning budget: equal trials per arm, grids extended at pilot edges,
  parameter counts and effective degrees of freedom reported. E3 gain from lab/stage/temperature aliasing and non-isothermal check-ups (section 3.3(7)):
  lab/stage sensitivity rows. E4 gain from label-free design-hull information the data-only learners never see: part of the PINN's mechanism and a stated
  limitation. E5 gain specific to the window or horizon: windows k-1, k+2 and horizon-wise error.
- **Expected endpoint (judge's reading of the files, not a result; J11§3.1).** H1b forecasting gap was 0.0-0.1 pp on synthetic G2 (P4) against a minimum
  detectable gain near 10 % (SR§7); H2 synthetic median ratio 0.96 with one reversal (P5); H1c needs about 19 % (SR§7) against learners already at the
  replicate reference (P3). H6 is the contrast most likely to reach tier S. **Most likely: H6 S; H1a S or N; H1b N or none (KAN tie wording); H1c gate
  closed or unresolved; H2 unresolved, i.e. title 3.** Title 1 needs tier S on all three family members and H2 = A and is rated unlikely. The paper's
  strength would then rest on the calendar-cycle law, the comparison with the dataset authors' model, the physical checks (section 11a) and the
  evaluation design. The lead tells Shlok before the freeze; his answer changes no rule.
- **Power (SR§7; assumptions, not Samsung numbers; to be re-reported for the adopted log-scale rule, [FB-7]).** n = 40 conditions detect at 80 % power
  (Holm step 1, superiority margin 2 %) a relative improvement of about 9.8 % / 13.7 % / 19.4 % when the two arms' condition errors correlate 0.95 / 0.90 /
  0.75 (same-model contrasts H1a, H1b at 0.95; different families at 0.75). n = 13 (Test C) cannot resolve below about 17 %. A tie with a different-family
  learner is resolved as non-inferior (10 % margin) only about 24-40 % of the time at n = 40. The error correlation for PINN-KAN pairs is an assumption.
- **Abstract rules (SR§6).** Per primary contrast: n, mean paired difference in pp with 95 % BCa interval, relative reduction with interval, tier (S/N/none),
  and PINN-KAN's own score with seed SD. No p-values, no "significant", "outperforms/beats" only at tier S, "matches" never, "comparable/equivalent"
  only after a two-sided TOST at +-delta_N. Scope words: "held-out cycling conditions of one cell type in three laboratories".

## 2. Hypotheses (J11§1.1-1.2)

| ID | Statement | Status |
|---|---|---|
| H1a | A1 (PINN-KAN) vs A9 (data-only F, lambda = 0): residual does work | **primary family**, tiers N then S |
| H1b | A1 vs the inner-CV-best of the stress-map pool {A3, A4, A5, A7}: KAN does work | **primary family** |
| H6 | A1 vs A10 (dataset authors' semi-empirical model, with per-cell factor, section 7.1) | **primary family** |
| H1c | A1 vs inner-CV-best of {A11 GP-ARD, A12 LightGBM} | **key secondary, serially gatekept**: tested (tiers N then S, level 0.025) only if H1a, H1b, H6 all reach tier S; otherwise reported with interval and the label "secondary, not tested" |
| H2 | A1 (soft PINN) vs A2 (hard ODE, same law): outcome A / C / B | decision contrast, not in the family (9.6) |
| H3 | KAN wording against the inner-CV-best of {A4, A5} (GAMs only): win / tie / worse | derived; "win" also needs the strengthened, validity-checked G2 (section 13) |
| H4 | Test C (35 C, INT; section 4): A1 vs best of A11/A12 (tier N) and A1 vs A10 (tier S) | secondary, Holm-2 inside Test C at 0.025; n = 13, descriptive in strength |
| H5 | S2: A1 non-inferior to the inner-CV-best of {A3, A9, A10} at -ln(1.10) | secondary, one test at 0.025 |
| X1 | Joint training vs cycling-only (A1 vs A13) | **secondary, descriptive**: interval and unadjusted tier; claim word only "joint training lowered / did not lower the error" |
| H7 | Reduced identifiability on synthetic G0-G2 (section 13) | supporting figure |
| ISU, SNL | same rules per dataset: H1a, H1b (pool A4, A5, A7), H6-analogue (cyclic semi-empirical form), H1c (not gatekept, labelled secondary) | secondary, **not blind** (section 3.4); unadjusted across datasets, never pooled with Samsung |

The family-wise level is 0.025 one-sided (0.05 two-sided for a directional claim). Test A, S3, A14: exploratory (section 7).

## 3. Datasets, inclusion and exclusion

### 3.1 Samsung INR21700-50E (primary; figshare 25975315)
Counted from `experiments_meta.csv`: 279 cells = 132 storage (19 conditions: 10/23/45 C x SOC; the 23 C/0.8 centre point has 4 test points = 24 cells) +
147 cycling (40 conditions; 23 C: 10 conditions / 33 cells; 35 C: 13 / 39; 45 C: 17 / 75; 35 conditions with 3 cells, five centre points with 6, 6, 9, 9,
12). Storage at 35 C does not exist; cycling at 35 C does.

### 3.2 Cell identity and stage assignment (J11 C5; closes OPEN-1)
138 of 141 zip names occur in both stages, so a cell is keyed **`cell_id = <serial>_s<stage>`** (e.g. `TP_z01_01_s2`); the fetcher is stage-aware (folders
`<serial>__f<figshare id>`). **One stage rule, the pipeline's** (`runs/samsung_pipeline/folder_mapping.csv`): (1) internal cell serial in the meta text
equals `serial_internal` of the design; else (2) laboratory; else (3) first test date (stage 1: tests from Sep-Oct 2021 to Aug 2022; stage 2: from
Jan-Feb 2023); cross-checked with `m_0`/`U_0` of the metadata where present. Disagreement between checks: the cell is **excluded and listed**.
Open cases carried from the pipeline snapshot (17 by internal serial, 1 by laboratory, 1 by date, 1 unassignable of 20 folders): TP_z10_01 and
TP_z15_01 (meta internal serial contradicts the design table: INT028 vs INT037/INT149; INT043 vs INT052) are resolved against the dataset paper's
tables; if the condition stays ambiguous the cell is excluded from training and scoring and listed. The empty folder `TP_z02_01__f47631268` is re-fetched;
excluded if still empty. Any cell unassignable on the complete download is excluded and listed before the freeze **[FB-4]**.

### 3.3 Inclusion and exclusion (rules; J11 C6, C8)
1. Capacity per check-up = mean of charge (step 21) and discharge (step 22) capacity by trapezoid integration of the current (dataset paper definition;
   pipeline `q_mean`). A check-up that fails the flags below is dropped, not its cell.
2. Reference Q0,c: ET_T23 capacity if ET members exist for every analysed cell, otherwise the first quality-passed CU for every analysed cell (one
   reference for all; by availability) **[FB-3]**. The current pipeline output is anchored on the first CU: fade before it is not measured (first CU is
   1 week (cycling) or 5 weeks (storage) into ageing). Retention = Q / Q0,c.
3. **Pipeline QC flags (critical; set qc_pass false), now rules at check-up level:** step 21 or 22 missing; step durations out of range (22: 0.45-1.35 h;
   21: 0.9-2.8 h); median current off nominal; sampling gap > 60 s inside the step; NaN current; capacity outside 2.0-5.2 Ah; discharge not from >= 4.0 V to
   <= 2.55 V; charge not to 4.2 V; |q_ch - q_dch| / q_dch > 3 %; cell surface temperature at the start of the discharge more than 5 C from 23 C; setpoint
   not 23 C; start date missing; start dates decreasing with file number; **isolated outlier** (interior point outside the range of its two neighbours
   by > 1 %). Info flags only: file > 30 h, voltage below 2 V somewhere, capacity rise > 0.5 %, stub runs.
   **Disclosure:** these thresholds were fixed after 163 check-ups of 18 cycling cells (19 cells in total) had been parsed and QC-checked; no critical
   flag fired and the outlier rule fired zero times. The outlier rule depends on capacity; a **sensitivity row retains every check-up** regardless of flags.
4. **Incident handling** from the paper's "Known incidents" list (names as printed there). Dropped at file level: TP_z25_01_01_ET_T45 (undefined load),
   TP_z01_03_11_CU (concatenated files), TP_z17_03_13_exCU and TP_z17_03_17_CU (incorrect SOC_max), TP_z17_02_19_exCU and TP_k11_02_03_exCU (manual
   charge), TP_z12_*_31_AT_T45 (aborted; AT is excluded anyway). Retained: TP_k[08-11] ET files (the failed capacity cycle was replaced by a repeated
   measurement; only the charge OCV may be affected). Because the paper asks to drop "potentially consecutive files", every later check-up of a cell
   whose cycling segment shows undefined load or a wrong SOC_max (TP_z24_01_02, TP_z25_01_04, TP_z07_03_16, TP_z20_03_16, TP_z17 from segment 18) is
   dropped from that point. Segments with only missing log data ("cycling itself was performed correctly") keep their check-ups and use the designed
   throughput for that interval. Each pattern is mapped to `<serial>_s<stage>` cells under 3.2.
5. Pauses (chamber downtime 15 and 20 days, lab downtime 4 days; stage 2) stay on the real calendar axis.
6. Storage cells 01-03 of a test point (66 cells) form the storage trajectories. Cells 04-06 have entry and final tests only: excluded from training and
   scoring in the primary; a sensitivity row adds their two-point records. The final test (AT) is excluded from the forecast set (AT capacity at 23 C may
   deviate because of preceding 10 C and 45 C tests); AT-included is a sensitivity.
7. **Confound and non-isothermal check-ups.** All 39 cells at 35 C were run by lab INT; 45 C is HM (66 cells) and SIE (9); storage 10 C is all SIE and
   storage 45 C all HM; at 23 C cycling INT runs 6 of the 10 conditions (SIE 3, HM+INT 1). Temperature is therefore aliased with laboratory (and partly with
   stage) in Test C and S2. In addition the capacity test is **not isothermal**: the cell surface temperature during the 1C discharge averages 31.6 C
   (stage 1) and 29.8 C (stage 2) in a 23 C chamber, with lab differences (pipeline item 7), so a lab/stage offset can enter the capacity. Handling: Fig. 2,
   the lab/stage rows of section 9.8, the CU surface-temperature offsets by lab tabulated beside Test C. No adjustment in the primary models.
8. No cell is excluded because of its capacity trajectory. Cells whose record ends inside the window are scored in a sensitivity row as forecast failures
   (retention carried forward from the last observation, same rule for every arm).
9. **Retention blinding until the freeze (J11 C8).** Samsung retention values stay in `data/processed/` (gitignored); nothing under `runs/` or any note
   shows retention by cell or condition; the window rule uses check-up counts only; no plot of Samsung trajectories is made. The full parse after the
   download is a data step, not a look.
10. **Disclosure sentences (printed in the paper's methods).** "Capacities of 18 cycling cells (163 check-ups) were parsed and quality-checked before the
    preregistration was frozen, without scoring any model. ISU and SNL were explored in a scratch pilot before their splits were fixed; their results
    are therefore secondary and not blind."

### 3.4 ISU-ILCC and SNL (secondary; cyclic term only; "not blind", J11 C6, C8)
Splits already fixed in `runs/splits/` (hash checked by every run). Test B analogue only; arms of section 7 without calendar term; A10 replaced by the
cyclic power-law form. ISU uses weeks and an analytic cycles-per-week forcing, calibrated on the 6 fetched `Cycling_json` members; the ISU authors' EOL MAPE
is reported beside ours. SNL: 61 cells, the 90-row exclusion of P1. **Forecast set** ends at the first point below 70 % retention for every arm (as in P3);
cells whose life ends inside the window are scored as forecast failures in a sensitivity row (same rule as 3.3(8)). The scratch pilot of the proposer
(`debates/D010_topic/pilot_scratch`) looked at all ISU cells before the splits (replicate scatter, per-cell power-law errors at W = 2, 4, 6, where W = 4 and
6 came from): ISU and SNL results are labelled **not blind**, claims "also holds / does not hold", with their own n. **Fallback (J§4, J§8-1):** if Samsung
check-ups are not parsed by **07 Nov 09:00**, ISU becomes primary with the same hierarchical rule for every contrast (H1c on ISU is **not** pre-decided as
non-inferiority; D007 is superseded by D009), SNL secondary, no calendar arm, fallback title TF, and the "not blind" disclosure on the primary.

## 4. Outer splits (Samsung; generated from identifiers only)

Script `code/prereg/make_samsung_splits.py` (reads only `experiments_meta.csv`; dealing routine of P3), output **`runs/prereg/samsung_splits_v2.json`**,
keyed by `cell_id = <serial>_s<stage>`. Regenerated because the cell key changed; the condition-to-fold assignments are identical to
`samsung_splits_DRAFT.json` (checked), only cell strings and hashes differ. Copied to `runs/splits/` and hashed at freeze (J11 C7). Seeds **[D]**:
B 20261107, A 20261108, S2 20261109.

- **Test B (primary): held-out cycling conditions, 5 folds of 8**, stratified over temperature x stress: the five conditions with more than 3 cells are
  dealt first, one per fold; then per temperature (23, 35, 45 C) conditions are clustered in standardised (SOC_max, DoD, C_ch, C_dch) into ceil(n_T/5)
  neighbourhoods whose members go to different folds (fewest-so-far, random ties; counts shared across temperatures). Conditions per fold at 23/35/45 C and
  test cells: f0 2/3/3, 33; f1 3/3/2, 27; f2 1/3/4, 30; f3 2/2/4, 27; f4 2/2/4, 30. All storage cells (per 3.3(6)) are always in training. Stage and lab are
  not strata (reported per fold). Hash prefix of the fold block `5cde4d3eeeed`.
- **Test C (secondary): held-out temperature-laboratory domain (35 C, laboratory INT).** All 13 conditions (39 cells; stage composition from identifiers:
  9 conditions stage 1, 4 conditions stage 2) are held out; training = 23 and 45 C cycling (27 conditions, 108 cells) + all storage. **Never called
  "temperature extrapolation", "temperature generalisation" or "untested temperature" alone, and not interpolation in temperature either**: the lab is new
  to that temperature (J11 §2). INT cells at 23 C are in the training set, which partly separates lab from temperature; the identification of an INT
  offset holds only under "no lab x temperature interaction", printed with the result. Calendar twins at 35 C stay label-free collocation (mechanism); no
  sentence presents them as evidence for a temperature response. Hash prefix `a70f9dbef540`. No Test B vs Test C ratio anywhere (retired topic).
- **Test A (exploratory, appendix): held-out replicates.** 3 folds, 49 cells each, every condition keeps >= 2 cells in training per fold; own tuning per
  fold. Not the paper's question; `R_LOO` (replicate spread) is its yardstick (SR§1.1). Hash prefix `d78537346d43`.
- **S2 storage transfer (secondary).** 19 storage conditions, 5 folds (3, 4, 4, 4, 4) by blocks of consecutive SOC inside each temperature; all cycling cells
  and the other storage conditions in training; only cells 01-03 of a held-out point are scored. SOC 1.0 and 0.05 are edges; the table also reports SOC
  <= 0.8 (stage 1 shows non-monotonic behaviour above 80 % SOC); a reporting split, not an exclusion. Hash prefix `a8078f030393`.
- **S3 (exploratory): leave-23-C-storage-out** (7 conditions; train on 10 and 45 C storage + all cycling). No claim, no Holm.

## 5. Task, window rule, forecast set

- **Task (identical for every arm).** Inputs: stress vector s (cycling: T, SOC_mid, DoD, C_ch, C_dch; storage: T, SOC), Q0,c, window check-ups, throughput rate
  nu. Output: retention at every later check-up time. Time t_tilde = days since the reference check-up, global scaling only (never per-cell life fraction).
- **Throughput.** Inside the window: logged equivalent full cycles per interval. After the window: the cell's own mean rate over the window (causal).
  **Validation rule (fixed now; J11 §7.5) [FB-5]:** analytic EFC (pipeline `efc_est`) versus ZYK-logged EFC for at least 2 cycling cells per DoD class and
  per laboratory, at every check-up. Accept analytic throughput iff the median absolute relative difference is <= 5 % and no sampled cell exceeds 10 % at
  its last check-up. Otherwise ZYK-logged throughput is used for every cycling cell (ZYK of all cycling cells parsed before the freeze). An oracle-throughput
  row (logged, all arms) is a sensitivity either way.
- **Window rule in check-up counts, from the schedule alone [R] [FB-6].** Count intermediate check-ups (CU + exCU; ET and AT excluded) per cell from the zip
  member listings (identifiers only). n_med = median over cycling cells; **k_cyc = round(n_med / 3)**; likewise k_sto from storage cells 01-03. Primary
  window = first k check-ups after the reference; secondary k-1 and k+2. Corrected expectation (GA N1): the two listed P0 cycling cells have **8 and 15**
  intermediate check-ups (6 CU + 2 exCU; 10 CU + 5 exCU) and the storage cell 7 (4 CU + 3 exCU); the pipeline reports 8, 10 or 11 CU per cell plus exCU;
  k_cyc is expected in 3 to 5, k_sto near 2 (expectation, not a computation). Count-based because paused intervals make weeks unreliable.
- **Schedule go/no-go (J§8-3).** If fewer than 3 post-window check-ups exist for most cycling cells at the primary window, Samsung becomes secondary
  (storage transfer only) and the fallback of 3.4 applies.
- **Forecast set.** For each scored cell: all CU and exCU after the window surviving 3.3, in time order. A cell is scored with at least one such check-up;
  the number of points per cell is reported; a sensitivity row restricts to cells with >= 3 forecast points.

## 6. Endpoints

- **Primary endpoint (one; judge's endpoint, in pp):** cell-level retention RMSE (percentage points) over the forecast set, averaged within condition (mean
  over the condition's scored cells) then over conditions; Test B, primary window k_cyc, 5 seeds (per-condition value = mean over seeds of that condition's
  RMSE), frozen configuration. **The primary contrast is tested on the log ratio of condition scores** (section 9.3); the pp difference is reported with every tier.
- **Secondary:** windows k-1, k+2; error at fixed horizons after the window (first post-window check-up and later ones, in check-up counts); RUL error in days
  for cells crossing 80 % (n reported); MAE, MAPE, R^2 (correct argument order); Test C, S2, X1; ISU EOL MAPE and SNL analogue; wall clock and parameter
  count; share of non-finite or diverging forecasts per arm (a non-finite forecast is scored with the persistence error and counted); `E/R_LOO` and
  `E/R_WARP` (descriptive, section 9.9).
- **Metrics where a regression is expected** (so that they are not read as failure): wall clock and parameter count; error at the first post-window
  check-up (a data-only learner can be locally better); RUL error (few cells reach 80 %).

## 7. Arms, tuning, budget (J11 §1.3, §1.4)

Common: tanh MLP solution network F (width 32, depth 3, per-cell latent z_c of dimension 2, hard initial condition) as in the P5 configuration, fixed in
every F-based arm and not tuned (conservative for the claim; A9 gets a larger space). Cyclic KAN over (T, SOC_mid, DoD, C_ch, C_dch); calendar KAN [1,2]
from storage SOC to (a, E); own compact B-spline KAN (`code/models/kan_spline.py`), cubic. **Collocation placement (record end vs whole time axis, P5 item 4)
is a tuned categorical in every PINN arm.** State factor (backbone) chosen once per outer fold by a tournament on training conditions with the hard-ODE-KAN
at default settings among {constant, self-limiting 1/(y+y0), accelerating exp(gamma y)}: the simplest backbone within one standard error of the best,
shared by all law-based arms of that fold. Loss normalisation and optimiser frozen by code commit at freeze.

**Budget rule.** Every tuned arm gets the same N trials (TPE, sampler seed = outer-fold index) x 3 inner folds grouped by condition and stratified by
temperature, inside outer-training conditions only, plus 5 final refits (seeds 0-4). N = 20; N = 40 if the median fit on a Samsung training fold is under
20 s for every neural arm (J§6). **Timing run before the freeze (D008(a), J11 C3) [FB-8]:** if the median hard-ODE fit exceeds 30 s or the PINN fit exceeds
90 s, the J§7 Partial plan applies to **every arm equally** (trials 20 -> 10, inner folds 3 -> 2, seeds stay 5). Edge-optimum rule: a value at a grid edge
extends the grid in the next version (extensions below already include the P4/P5 edges).

### 7.1 Arms and spaces

| Arm | What it is | Tuned space (extended at pilot edges) | Dims |
|---|---|---|---|
| A1 PINN-KAN | F + residual; cyclic KAN [5,h,1]; calendar KAN | h {2,3,4,6,8} (P4: 4 in 4/5 = old top); grid {2,3,5,8,12} (P4: 3 and 8, both ends); spline L2 {1e-5..1e-2} (P4: 1e-4 low edge); sparsity L1+entropy {0,1e-4,1e-3,1e-2} (no pilot); lambda_res {1e-2,1e-1,1,10,100} (P5: 1.0 = old top in 2 of 5; 10 worse post hoc); collocation placement {record end, whole axis} | 6 |
| A2 hard-ODE-KAN | same law, exact or RK4 integration, delta_c MAP from the window, no F; **decision contrast H2** | A1 without lambda_res and F; <= 60 nodes per cell (P2: 30 s met to about 60 nodes by interpolation) | 4 |
| A3 PINN, parametric stress factors ("parametric") | log-linear Arrhenius/power-law factors in 1/T, C_ch, C_dch, DoD, SOC terms | ridge L2 {1e-5..1e-1}, lambda_res, placement | 3 |
| A4 PINN, additive GAM (= KAN [5,1]) | additive cubic splines | grid {3,5,10,20,30} (P4: 5 chosen 3/5 = old bottom), L2 {1e-5..1e-1} (P4: both edges), lambda_res, placement | 4 |
| A5 PINN, interaction GAM | A4 + tensor products T x C_ch, T x SOC_mid, DoD x SOC_mid | A4 space + interaction grid {3,5} | 5 |
| A7 PINN, MLP stress map (**PiDDM-style**) | fixed law, parameters from a small MLP of s | width {4,8,16,32}, depth {1,2,3}, wd {1e-5..1e-2}, lambda_res, placement; parameter count capped at the largest in the A1 space | 5 |
| A9 data-only F (lambda = 0) | F, same z_c, inputs, window inversion, **no residual, no law**; **H1a** | width {16,32,64,128}, depth {2,3,4}, wd {1e-5..1e-2}, z dim {1,2,3} | 4 |
| A10 Stroebl semi-empirical (**H6**) | see 7.2 | multi-start least squares, no hyperparameters | 0 |
| A11 GP-ARD, A12 LightGBM (**H1c**) | on (s, window summary, t) | A11: kernel {RBF, Matern 3/2, 5/2}, noise floor, window-summary set; A12: ranges as in `p3_headroom.py`, frozen by commit | 3 / 5 |
| A13 PINN-KAN, cycling cells only (**X1**) | joint-training ablation | as A1 | 6 |
| R1, R2 (no tuning) | persistence of the last window retention; linear extrapolation of the window | - | - |
| *A6 degree-2 log-polynomial* | **dropped** (21 cross terms on 40 conditions; information covered by A5 and A7); discussed in text, no numbers; amends J§1 (ii)'s list (D011) | | |
| *A8 free G* | **synthetic H7 only** (identifiability is synthetic by design) | | |
| *A14 PINN-KAN, storage cells only* | **exploratory** (S2 only; first to be cut) | as A1 (calendar part) | 4 |

**Arms by test.** Test B: A1, A2, A3, A4, A5, A7, A9, A10, A11, A12, A13, R1, R2. Test C: A1, A9, A10, A11, A12 (n = 13 cannot resolve the stress-map
contrasts). S2: A1, A3, A9, A10 (+ A14 exploratory). Negative control: A1, A9, R2. Test A (exploratory, appendix): A1, A2, A9. Synthetic: A1, A2, A4, A8.
LSTM, Transformer, PiDDM reimplementation, BatLiNet/FlowBatt: out (discussed, no numbers). Label note (GA §7): "PiDDM-style" belongs to A7 only; A3 is "parametric".

**Comparator selection (no test information).** For H1b the comparator in each outer fold is the pool arm {A3, A4, A5, A7} with the lowest mean inner-CV
score on that fold's training conditions; for H1c the lower of A11/A12; for H3 the lower of A4/A5. Its outer-fold predictions are compared. All pool arms are
also reported against A1 (Table 2, descriptive, Holm over the four). Selecting by outer test error is not allowed.

### 7.2 A10 fairness (J11 §1.4; closes the Stroebl form once [FB-2] is met)
A10 primary = the published form (Stroebl data paper SI S.1.1, after Muehlbauer et al., J. Energy Storage 48, 103803, doi 10.1016/j.est.2021.103803,
Crossref-verified in the re-audit), population parameters by multi-start least squares on the training conditions, **plus one per-cell multiplicative factor on
the predicted loss fitted to the cell's window points by MAP with the same prior family as A1's delta_c**, and the same throughput input as every arm.
Sensitivity row: **A10 as published** (no per-cell factor). Equations are taken from the SI and the JES 142, 119552 full text with equation numbers recorded
(the local conversion of the SI is garbled: not freezable until fixed). A10 gets a **parameter-recovery unit test** on data generated from its own form.

## 8. Seeds

Final refits seeds 0, 1, 2, 3, 4 (initialisation and collocation sampling); tuning seed 1000 + outer fold, TPE sampler seed = outer fold. Condition score =
mean over seeds of the per-seed condition RMSE, then mean over the condition's scored cells; seed SD of the cross-condition mean shown beside every score
(reproducibility statement, not a CI). Seeds are never units; no best-seed or best-fold reporting; no post-hoc seed addition. Limitation stated: the tuned
configuration comes from one TPE search per outer fold, so search-to-search variation is not in the standard errors; a second search seed on the primary
contrasts is an appendix row if compute allows, not a decision input (SR§5).

## 9. Statistical analysis (J11 §4; SR§2-4)

1. **Unit = held-out condition** (Test B 40, Test C 13, S2 19, ISU 63, SNL 23); equal weight per condition (the five centre conditions are not
   up-weighted). Paired by condition (both arms scored on the same cells and windows). Neighbour dependence and fold-shared fits are not modelled
   (stated); per-fold means and the number of folds with sign agreement are reported.
2. **Margins.** *Log scale (primary):* L_c = ln(S_comp,c / S_PINN,c); superiority margin ln(1.02), non-inferiority margin -ln(1.10) (exact relative margins,
   no E estimate needed). *pp scale (reported beside every tier):* delta_S = 0.02 E, delta_N = 0.10 E, where E = the comparator's training-side inner-CV
   condition-mean score, per outer fold, pooled by test-condition count (SR§2.1-2.2); `runs/prereg/margins.json` (E, delta_S, delta_N per contrast, hash) is
   written **after tuning ends and before any final refit is applied to a test condition**. If the pp tier differs from the log tier, the abstract states both.
   Sensitivity rows: delta_S in {0, 0.05}, delta_N in {0.05, 0.15} (relative). The replicate spread is not in any margin or gate.
3. **Test (J11 §4.2).** One-sided **studentized sign-flip permutation test** of mean(L - m), statistic t = mean / (sd / sqrt n), 100,000 random sign vectors
   plus the identity, p = (1 + #{t* >= t}) / (1 + B), fixed RNG seed **[D]**, **AND** the one-sided BCa lower bound of mean(L) at confidence 1 - a (10,000
   condition resamples) exceeding m. Tier S passes ln(1.02); tier N passes -ln(1.10) but not S; "none" otherwise. The Wilcoxon is reported in the appendix
   only (it targets the pseudo-median, not the mean).
4. **Type-I verification before the freeze [FB-7] (statistician; no Samsung data).** Re-run the null-boundary simulation for exactly this rule at n = 40
   and n = 13, at levels 0.025/3, 0.025/2, 0.025 and the gatekept 0.025, >= 10,000 simulations per cell. Shapes: two arms' condition scores as positive
   correlated variables (CV 0.45; rho 0.95, 0.90, 0.75) with (a) the ISU-derived shape, (b) normal, (c) failure contamination (PINN errors inflated on a
   fraction of conditions, set so the pp difference has the skewness of the mirrored ISU shape, -1.06). **Acceptance:** simulated rejection <= 1.2 x nominal in
   every cell. **Fallback fixed now (used if this fails in any cell at n = 40):** exact one-sided **sign test** on L - m (estimand: median condition
   log-ratio) with the order-statistic interval of the median; abstract words become "on the typical held-out condition ... (median)". Test C uses the
   fallback if the check fails at n = 13 only. Power is re-reported for the adopted rule; no rule changes after that. `code/prereg/stats_rule.py` is
   updated to the log scale and the sign-flip test as part of this step.
5. **Primary family and Holm.** Family {H1a, H1b, H6}, one-sided, family-wise 0.025. Holm step levels 0.025/3, 0.025/2, 0.025 are assigned by ordering the
   three N-tier p-values; each contrast's S-tier is tested at its own step level (nested nulls, N then S at the same level needs no extra correction;
   SR§2.3). Implementation in `stats_rule.py`.
6. **Gatekeeping and H2 (J11 §1.1, §1.2; SR§3).** *H1c:* tested at the full 0.025 (tiers N then S) only if H1a, H1b, H6 all reach tier S; else reported
   with its interval and the label "secondary, not tested", and the abstract may only use the "none" wording for it. *H2* (d = S_hard - S_PINN; hard ODE's own
   margins): order **A** (tier S for the soft PINN; tested only if the family passes, i.e. all three tier S), then **C** (reverse tier S; tested regardless,
   a safety finding), then **B** (TOST at +-ln(1.10)); anything else "unresolved", worded as B. Separate level 0.025, not in the Holm family.
7. **H3.** Against the inner-CV-best of {A4, A5}: win = H1b tier S against that arm and G2 passes (section 13); tie = two-sided TOST at +-ln(1.10); worse
   = reverse tier S; otherwise unresolved.
8. **Sensitivity rows (appendix, mandatory):** (a) lab-stratified bootstrap (resample conditions within lab strata, stratum = majority lab) and the
   post-stratified mean; (b) mean paired difference per lab and per stage, with n; (c) leave-one-lab-out mean; (d) two-stage bootstrap (conditions, then
   cells); weights by scored cells; (e) pp-scale row; (f) **Test C lab-indicator row**: A1, A9, A12 with a lab indicator in the per-cell prior/inputs (INT offset
   learned from INT at 23 C; identified only under "no lab x temperature interaction"); and the same lab-and-stage indicator row for Test B; (g)
   **A10 as published**; (h) retain-every-check-up (outlier rule off); (i) AT included; storage cells 04-06 included; cells with >= 3 forecast points;
   forecast-failure rule 3.3(8); oracle throughput; backbone fixed to self-limiting; windows k-1, k+2; (j) margin sensitivities of 9.2. If the lab-stratified tier is
   lower than the primary tier the abstract says so (disclosure, not automatic downgrade).
9. **Reference quantities (descriptive, never margins or gates).** `R_LOO` (replicate spread; renamed from "replicate floor") and `R_WARP` (window-aware
   replicate predictor, SR§1.2, the form with the lower training-side median per fold, ties to additive) are computed on training sides after parsing; Table 1
   reports `E/R_LOO` and `E/R_WARP`. Samsung values are computed only after the download and decide nothing.
10. **Effect sizes (always shown):** geometric-mean ratio (relative reduction exp(mean L) - 1), mean difference in pp with BCa interval, share of conditions
    won, per-fold means. Other families: Test C Holm-2 at 0.025 (H4); H5 one test at 0.025; X1 unadjusted; exploratory results labelled.

## 10. Controls

- **Negative control (effect must vanish).** In each Test B outer fold the stress vectors (with design throughput) are permuted among conditions, separately
  in training and test sets, window data untouched; **A1, A9 and R2** re-run at the same budget. Required: the A9 - A1 contrast has mean L < ln(1.02) and the
  unshifted two-sided sign-flip p > 0.05; A1 does not beat R2 (window-linear extrapolation) by more than the superiority margin. A violation means leakage
  through something other than stress: stop and audit (section 12).
- **Positive controls.** (P1) Synthetic G0 (well specified): structured arms recover the log-rate surface with nRMSE <= 0.15 and beat A11/A12 on G0 forecast
  RMSE (paired Wilcoxon p < 0.05, 20 draws). (P2) Real storage cells: the fitted calendar rate increases monotonically with temperature at every SOC inside the
  storage hull (also section 11a item 3). (P3) A1 beats R1 (persistence) on Test B with margin 0.

## 11. Outcomes and consequences (replaces PD§11; J11 §3.2, §2)

Titles: **T1** "Physics-informed neural networks with Kolmogorov-Arnold stress functions forecast calendar and cycle ageing of lithium-ion cells at untested
conditions"; **T2** "Coupling calendar and cycle ageing in a physics-informed Kolmogorov-Arnold network to forecast lithium-ion capacity fade under unseen
stress conditions"; **T3** "Learning stress-dependent calendar and cycle ageing laws of lithium-ion cells with physics-informed neural networks and
Kolmogorov-Arnold networks"; **TF** fallback "Physics-informed neural networks with Kolmogorov-Arnold stress functions forecast capacity fade of lithium-ion
cells under unseen cycling conditions" (ISU primary). "Identifiable" never appears in a title. Evaluate gate G first, then the first matching row.

| # | Condition | Title | Abstract / highlights wording |
|---|---|---|---|
| G | negative or positive control fails, or a test-fold read is found | none | no claim; audit; new version |
| 1 | H1b reverse tier S (KAN worse than the best alternative map) | KAN leaves the title; retitle put to Shlok | "a [winning map] stress model was more accurate than the KAN" |
| 2 | H1a not S (residual no better than lambda = 0) | T3 at most; framing put to Shlok | "the physics residual did not lower the forecast error" plus its interval |
| 3 | H6 not S | T3 at most; lead tells Shlok before writing | "could not be distinguished from" / tier-N wording against "the dataset authors' semi-empirical model"; no "outperforms physics-based models" |
| 4 | H1a S, H6 S, H1b N or none | **T3** | KAN tie wording (J§3): "reached the accuracy of the best prespecified-interaction model without specifying the interactions", with interval; never "outperforms" for the KAN |
| 5 | family all S, H2 = C | framing to Shlok: C1 (judge's recommendation) T2 with "physics-informed Kolmogorov-Arnold network", or C2 T1 wording kept with the hard ODE reported stronger | as J§2 |
| 6 | family all S, H2 = B or unresolved | **T3** | "lower error than the same network without the residual, the best alternative stress map and the dataset authors' model by X % (CI)"; "the soft residual and exact integration of the same law were [equivalent / not distinguished]" |
| 7 | family all S, H2 = A | **T1** (T2 allowed) | as 6, plus "the soft residual lowered the error relative to exact integration"; KAN "superiority" only if H3 "win" holds |
| H1c add-on (rows 6-7 only; gate open) | S | no title change | "and lower than the best tuned data-driven learner by X % (CI)"; highlights may say "outperformed" |
| | N | no title change | "no more than 10 % worse than the best tuned data-driven learner (one-sided bound ...)"; "comparable" only after TOST |
| | none / gate closed | no title change | "accuracy could not be distinguished from tuned data-driven learners" with interval |
| T, S, X1 | Test C (below), S2 (H5 non-inferior: storage sentence allowed, else removed), X1 (descriptive) | no title change | as below / SR§6 |

**Test C wording (H4, Holm-2 inside Test C).**

| Outcome | Title | Abstract |
|---|---|---|
| A1 vs A10 tier S and A1 vs best data-only tier N or S | never mentions 35 C or temperature | may add: "and on a held-out combination of temperature and laboratory (35 C cells from one laboratory, n = 13 conditions), [tier wording]", followed in the same sentence by "temperature and laboratory cannot be separated in this design" |
| one of the two reached | same | the reached contrast with the same clause; the other "could not be distinguished" |
| neither reached | same | no Test C sentence in the abstract; Table 1 column, Results paragraph and a Limitations sentence report it with intervals (no selective omission from the paper) |

All tier words follow SR§6. Every abstract number is a relative reduction (geometric-mean ratio) with its 95 % interval and n, plus the pp difference with its
interval.

**P3 entry (descriptive only; J11 C1).** P3 used (descriptive only); D007 superseded by D009; **no gate**. Ratios of the best flexible learner's inner-CV error to
`R_LOO` on training folds: ISU W4 0.90, SNL W100 1.13 (`runs/pilot_P3/RESULT.md`). Samsung: `E/R_LOO` and `E/R_WARP` computed on training sides after parsing,
descriptive, in Table 1.

## 11a. Physical validation analyses (secondary, descriptive; no test, no Holm, no claim word beyond "consistent / not consistent"; J11 §6)

1. **Calendar temperature dependence.** Effective activation energy E(SOC) from the calendar KAN with fold x seed envelope, compared with (a) the Arrhenius
   parameter of the dataset authors' own calendar fit on the same data (labelled "consistency with the semi-empirical fit", not independent validation) and
   (b) published calendar-ageing activation energies **only** for cells of the chemistry stated in the dataset paper, each with a Crossref-verified DOI and
   page/table location (citation-validator) and comparable SOC, temperature range and check-up protocol; if none is verified, (b) is omitted and the text says
   so. Printed caveat: storage at 10 C is all SIE and at 45 C all HM, so E(SOC) is lab-confounded; the storage lab composition at 23 C is tabulated.
2. **SOC dependence above 80 %.** The learned storage rate versus SOC at each storage temperature with envelope, and whether it changes slope sign above 0.8;
   caveat: SOC > 0.8 exists in stage 1 only. The S2 table already splits SOC <= 0.8.
3. **Arrhenius monotonicity** (positive control P2): calendar rate increases with temperature at every SOC inside the storage hull.
4. **Superposition check.** Per cycling cell, the share of predicted fade attributed to the calendar term, and the number of cells where the calendar term alone
   exceeds the observed total fade at the last check-up (a physically impossible split), for A1 and A2.
5. **Direction of cyclic stress effects.** Signs of the cyclic partial dependences versus the signs of the exponents in the dataset authors' cycle model
   (consistency only), with envelopes. Items 1-5 go to Fig. 5 / Fig. 6 and one appendix table; none enters the outcome table.

## 12. Stop rules

1. Samsung not parsed by 07 Nov 09:00: fallback of 3.4. 2. Schedule go/no-go (section 5). 3. Gate G of section 11. 4. A test fold read by any tuning,
selection, margin or comparator step: run void (test-fold guard line in every run script). 5. Compute: if the projection of section 16 exceeds the agreed cap, cut
in this order: **A14, Test A, S3, sensitivity rows, A13 last**; trials and seeds are never reduced (except the equal-for-all Partial plan of section 7). 6. No
interim look at outer-test results; each frozen configuration is scored once, after all folds finish. 7. Any rule changed after a Samsung test fold is scored
is not allowed (new version, disclosed).

## 13. Identifiability protocol (one figure + appendix; synthetic only; J§6)

- **Design:** real Samsung design (40 + 19 conditions, replicates, cadence and window from section 5) **[FB-6]**; ISU design as in P4/P5.
- **Generators** written before any real fit; truth never from model fits. G0 well specified (positive control); G1 misspecified time law (t^z with z depending
  on T, plus a logistic knee in throughput with stress-shifted onset); G2 non-additive stress law (charge-rate hinge with temperature-shifted threshold, plus DoD x
  SOC product); optional G3 storage and cycle terms not additive. Pilot grids: `runs/pilot_P4/config.json`. **G2 strengthened:** P4's additive-GAM class floor on
  the true surface (0.05-0.07) is below the 0.15 pass line, so the pilot G2 could not discriminate; the confirmatory G2 uses the upper pilot-grid values H = 1.2 and
  P = 0.8 (no new numbers; chosen after seeing P4, disclosed); the pilot-strength G2 is a sensitivity. **Validity rule:** computed before fitting any model, a G2
  draw is discriminating only if its additive-GAM class floor exceeds 0.15; if the median floor stays below, KAN superiority cannot be claimed from G2 and H3
  "win" is unavailable.
- **Constants:** round numbers as in the pilots (median final fade 20 pp, noise 0.5 pp, offset sd 0.15), not matched to Samsung summary statistics as J§6 asked,
  because matching needs label-derived scalars before the freeze, which J11 C8 forbids (departure recorded in D011).
- **Metrics:** nRMSE of the recovered log-rate surface on the fixed 500-point hull Latin hypercube divided by the true range (level included; centred reported
  alongside because P4 showed the free-G level offset: KAN/free 0.61 absolute, 0.76 centred); Kendall tau of variance-based stress importance; forecast RMSE on
  held-out conditions.
- **Thresholds (J§6):** pass nRMSE <= 0.15 on G1 and G2, fail > 0.30; structured median <= 0.67 x free-G median and paired Wilcoxon p < 0.05 over 20 draws; KAN
  lower than additive GAM on strengthened G2, paired p < 0.05; on G0 KAN not above GAM by more than 10 %. The structure claim is stated for the KAN-structured model
  and extends to "structured" generically only if the GAM also meets 0.67 (P4). Interval widths: diagnostic, no claim.
- **Hard vs soft on G1:** the H2 contrast on synthetic data (20 draws, paired); P5: PINN below hard in 4 of 5 draws, median ratio 0.96, one reversal. A residual-map
  claim needs a rank-correlation threshold with the true violation surface set by the statistician before optional G3 runs; without it Fig. 7 carries no claim.
- **Size:** 3 generators x 20 draws x 4 models (A1, A2, A4, A8) = 240 fits at the pilot tuning effort (8 trials x 2 inner folds, equal across arms), plus G1 hard vs
  soft 20 draws.

## 14. Figures and tables (10 items; JES limit 8-10; forms per BLUEPRINT.md and D-figures)

| Item | Content | Hypotheses |
|---|---|---|
| Fig. 1 | Method schematic (data strip, F/G, KAN stress functions, collocation sets) | mechanism |
| Fig. 2 | Design map: storage and cycling conditions, replicate fade, **lab and stage colouring (confound)** | 3.3(7), H4, E3 |
| Fig. 3 | Forecast overlays at held-out conditions, window shaded, **35 C row boxed and labelled "held-out temperature-laboratory domain"** | H1, H4 |
| Fig. 4 | Forest plot of paired condition-level differences on the **log-ratio scale, pp on a secondary axis**, all arms vs A1, with tier marks | H1a, H1b, H6, H1c, H2 |
| Fig. 5 | Learned stress functions a(SOC), E(SOC), cyclic partial dependences with envelopes, GAM dashed; carries 11a items 1, 2, 5 | H3 |
| Fig. 6 | Storage transfer parity and storage share of cycled-cell fade; carries 11a items 3, 4 | H5, X1, S3 |
| Fig. 7 | Residual map |R| over (T, SOC) and (C-rate, T) | H2 mechanism |
| Fig. 8 | Synthetic recovery G1, G2 (G0 control) with thresholds 0.15/0.30 | H7, H3 |
| Table 1 | Arms x {Test B, C, S2, ISU, SNL}, mean +- seed SD, tiers, time, parameters, **`E/R_LOO`, `E/R_WARP` (descriptive)**; "replicate spread" wording everywhere | H1, H4-H6 |
| Table 2 | Ablations and controls: what changes, parameters, delta primary endpoint, pool arms vs A1, negative/positive control results, X1; one appendix table for 11a | H1b, X1, section 10 |

Appendix: hyperparameter tables, sensitivity rows, windows, KAN/GAM symbolic rounding, chosen settings per fold, decision log.

## 15. Order of runs, by information per CPU-hour (CPU only; 3 single-thread processes)

1. Analytic and data checks (minutes): stage-aware identity, listings, n_med and k, split hashes, incident handling, Q0 rule, throughput validation. 2. Synthetic
G0-G2 and G1 hard vs soft (about 6 CPU-h): positive control and identifiability before any real fit. 3. Training-side measurements (no outer test): `E`,
margins.json, backbone tournament, `R_LOO`/`R_WARP`, Samsung timing run (fixes N), type-I simulation. 4. Core of Test B: A1, A9, A10, A3, A4, A5, A7 (H1a, H1b, H6),
then A2 (H2), A11/A12 (H1c if gate opens). 5. Negative control, Test C, A13. 6. S2, sensitivity rows, then ISU and SNL; exploratory Test A, A14, S3 last.

## 16. Compute budget (CPU only, from P2 timings; arithmetic, not a Samsung measurement; J11 edit 16)

Fits per arm and outer fold = 3N + 5 (N = 20: 65; N = 40: 125). P2 (1 thread, 61 cells; 2,000 Adam steps): PINN 13.3 s at 20 points per cell to 18.9 s at 80, 50.6 s
for 279 cells (tiled) at 80 points; hard ODE 11.4 s at 20 nodes, 18.5 s at 40, 38.4 s at 80, 42.0 s for 279 cells at 80 nodes. Expected column uses the low values (Samsung
about 20 nodes or fewer per cell), ceiling the 279-cell, 80-point values. Hard ODE gains nothing from threads: 3 single-thread processes in parallel, 0.7-0.8 GB RAM each
(P2 peaks 691-840 MB), about 2.5 GB total (3.6 GB free at night, D002); no GPU.

| Block (essential set) | Outer folds x neural arms | N = 20 expected / ceiling, CPU-h | N = 40 expected / ceiling, CPU-h |
|---|---|---|---|
| Test B | 5 x (7 PINN-type: A1, A3, A4, A5, A7, A9, A13 + 1 hard A2) | 9.4 / 35.8 | 18.1 / 68.8 |
| Test C | 1 x 2 (A1, A9) | 0.5 / 1.8 | 0.9 / 3.5 |
| S2 | 5 x 3 (A1, A3, A9) | 3.6 / 13.7 | 6.9 / 26.4 |
| Negative control | 5 x 2 (A1, A9) | 2.4 / 9.1 | 4.6 / 17.6 |
| Synthetic (scaled from P4 266 s and P5 232 s per draw; pilot tuning effort) | 60 + 20 draws | about 6 | about 6 |
| GP-ARD (ISU W4 log 339-539 s per outer fold; timing only), 6 folds (Test B, C) | | about 0.9 | about 0.9 |
| LightGBM, A10, R1, R2, bootstraps, sign-flip tests | | negligible | negligible |
| **Core total** | | **about 23 / 67** | **about 37 / 123** |
| Exploratory: Test A (3 x 2 + 1 hard), A14 (5 x 1) | | 3.3 / 12.3 | 6.3 / 23.7 |

Wall clock on 3 processes (core): N = 20 about 7.6 h expected, 22 h ceiling; N = 40 about 12.5 h expected, 41 h ceiling; with exploratory arms about 8.7 / 27 h and 14.6 /
49 h. Not included: sensitivity rows (the lab-indicator rows for A1, A9, A12 on Test B and Test C cost about one negative control each, 2-9 CPU-h at N = 20; A10-as-published
is cheap). Previous draft (9 PINN-type + 1 hard in Test B, 14-arm list) is superseded. PINN cost falls with data, so inner folds are cheaper than the ceiling.

## 17. Freeze preconditions, checklist, rulings recorded

### 17.1 Hard preconditions (J11 §7; only Shlok can waive one, in a ledger row)
1. **[FB-1] Zhang et al., JES 182, 125097 read in full** (Shlok saves the PDF; paper-reader note per CONTRACT §4; novelty-auditor verdict). If it contains a neural calendar +
   cycle model with learned stress functions forecasting held-out conditions of this dataset: D005 re-opens, no freeze. If it supplies a comparator or metric on this dataset:
   added in v3 before the freeze.
2. **[FB-2] Stroebl et al., JES 142, 119552 full text** read and A10's equations fixed (7.2); Hallinger et al. SSRN 7417281 read at least in its model and data sections.
3. **[FB-3] Full Samsung data on disk** (Shlok's download), every zip size- and checksum-verified, manifest written; pipeline re-run; ET/exCU members parsed so the Q0 rule
   (3.3(2)) and window counts can be fixed.
4. **[FB-4] Stage assignment complete for all 279 cells** under 3.2; exclusion list written.
5. **[FB-5] Throughput validated on a sample** (rule in section 5).
6. **[FB-6]** Window rule (k_cyc, k_sto) and schedule go/no-go evaluated from counts.
7. **[FB-7]** Type-I simulation of section 9.4 passed or the sign-test fallback adopted; power re-reported.
8. **[FB-8]** Samsung training-fold timing run done; N fixed (D008(a), section 7).
D005's date stands: Samsung not parsed by **07 Nov 09:00** means the ISU fallback (with the "not blind" disclosure).

### 17.2 Freeze checklist (gate auditor ticks each with a file pointer)
- [ ] Preconditions 1-8 met, each with its file.
- [ ] This file contains every edit of J11 §8; no [FB-n], [D], "pending" or OPEN marker left.
- [ ] Samsung splits copied to `runs/splits/`, hashes recorded; ISU/SNL split hashes unchanged.
- [ ] Grid files, code commit (clean tree), seeds, RNG seed of the permutation test recorded.
- [ ] A10 parameter-recovery test and the 19 pipeline tests pass on the frozen commit.
- [ ] `margins.json` procedure (pp row) and log-scale margins written; test-fold guard line in every run script.
- [ ] Disclosure sentences (3.3(10)) in the paper text.
- [ ] Statistician signs sections 6-9 and 16; red team signs sections 1, 10, 11; gate auditor second audit (C9) of this filled file against this checklist.
- [ ] DECISIONS rows complete; Shlok told the likely outcome (section 1) and the told-on date recorded.

### 17.3 Draft OPEN items, rulings recorded (J11 §5)
OPEN-1 closed (3.2; fetcher stage-aware). OPEN-2 A7 in. OPEN-3 F fixed in PINN arms while A9 gets a larger space (accepted as conservative); collocation placement a tuned
categorical. OPEN-4 closed (D009; floor is not a margin). OPEN-5 H6 in the family, H1c out (gatekept key secondary). OPEN-6 round synthetic constants accepted.

## 18. Run-record specification (J11 C7)

Every run writes: `config.json`, `metrics.json`, per-cell predictions, git commit **and dirty-file list**, split hash, raw-file manifest (path, size, sha256), seeds, RNG seed of
the permutation test. The Samsung pipeline is re-run on the complete download with a manifest; Samsung splits are copied to `runs/splits/` and hashed at freeze. Provenance
corrections (P3 commit statement: SNL runs 992b5b4, ISU W6 86fca6f, ISU W4 61bb730, code identical apart from audit lines; P0 run record written retroactively and labelled so) are
errata in the RESULT files, not here.

## 19. Change log

| Version | Date | Change |
|---|---|---|
| v0.1 DRAFT | 2026-11-05 | first draft; splits from identifiers only |
| **v2** | 2026-11-05 | D011 rulings; edits below. Not frozen. |

| J11 §8 edit | Where applied | Source |
|---|---|---|
| 1 Header: v2, basis, "P3 used (descriptive only)", markers as they close | header, markers | J11 §8-1; C1 |
| 2 Claim contract (iii) = A10; data-only key secondary; power paragraph; abstract rules; likely-outcome sentence | §1 | J11 §1.1, §3.1; SR§6, §7 |
| 3 Hypothesis table: family {H1a, H1b, H6}; H1c gatekept; H4 Holm-2; X1 secondary; ISU/SNL rows | §2 | J11 §1.1-1.2; SR§3 |
| 4 Stage rule = pipeline's; OPEN-1 closed; TP_z10_01, TP_z15_01, empty folder, unassignable cells | §3.2 | J11 C5; GA C5; pipeline RESULT item 1, 3 |
| 5 Pipeline QC flags as rules with post-parse disclosure; outlier sensitivity; non-isothermal CU under item 7; retention blinding | §3.3(3), (7), (9), (10), §9.8h | J11 C6, C8; GA C6, C8; pipeline item 7 |
| 6 ISU/SNL 70 % truncation and forecast-failure row; fallback uses hierarchical rule; "not blind" | §3.4 | J11 C6, C8; GA §6; D009 |
| 7 Test C renamed; stage composition of its 13 conditions; Test A exploratory | §4 | J11 §2; Cx§4; SR§4 |
| 8 "9 and 16" corrected to "8 and 15"; throughput validation rule | §5 | J11 C4, §7.5; GA N1 |
| 9 Arm table per 1.3 (A6 dropped, A8 synthetic, A14 and Test A exploratory, A13 secondary, pool {A3, A4, A5, A7}, naming); A10 per 1.4 with sensitivity; placement tuned; arms-by-test; Partial rule | §7 | J11 §1.3, §1.4, C3; D008; GA §7; P5 item 4 |
| 10 Margins (pp row, margins.json), log scale, sign-flip AND BCa, verification, fallback; H2 order A, C, B; families; added sensitivity rows | §9 | J11 §4; SR§2, §3, §4, §9 edits 1-8 |
| 11 Negative control arms A1, A9 (+R2) | §10 | J11 §1.3 |
| 12 Outcome table of 3.2, Test C table, descriptive P3 entry replacing the slot | §11 | J11 §3.2, §2, C1, C2 |
| 13 Physical validation analyses | §11a | J11 §6 |
| 14 Stop-rule cut order | §12 | J11 §8-14 |
| 15 Figures: Fig. 3 label, Fig. 4 log scale, Figs. 5-6 carry 11a, Table 1 columns, "replicate spread" | §14 | J11 §8-15; SR§9 edit 9 |
| 16 Compute table recomputed for the essential set | §16 | J11 §1.3, §8-16 |
| 17 Preconditions and checklist; OPEN-2..6 rulings | §17 | J11 §7, §5 |
| 18 Run-record spec; change log row | §18, §19 | J11 C7, §8-18 |
| 19 Errata appended to RESULT.md files | not in this file (errata task) | J11 C4 |
| Splits regenerated, keyed `<serial>_s<stage>`; assignments unchanged, hashes changed (B 5cde4d3eeeed, C a70f9dbef540, A d78537346d43, S2 a8078f030393) | §4, `samsung_splits_v2.json` | lead instruction; J11 C5 |
