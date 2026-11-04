# Preregistration DRAFT: confirmatory experiments, PINN + KAN calendar-and-cycle ageing (JES)

Status: **DRAFT v0.1, not frozen** (2026-11-05). Author: experiment-designer. Freezes only after `statistician` and
`red-team` sign; afterwards any change is a new version with a change log (section 18), never an edit.
Basis (read in full): CONTRACT.md (3, 6, 6a); `debates/D010_topic/04_judge.md` (all; cited "J§n"); DECISIONS D005, D006;
`runs/pilot_P0,P1,P2,P4,P5/RESULT.md`; `notes/papers/samsung50e_dataset_paper.md`; `notes/exemplars/BLUEPRINT.md`.
Also read for this draft: `runs/splits/README.md`, `code/pilots/p3_make_splits.py`, `p3_headroom.py` (replicate_floor), the
"Known incidents" list of the Samsung paper (`refs/samsung50e_paper/paper.html`), `data/raw/samsung50e_meta/experiments_meta.csv`.
P3 outputs were **not** used (still running; slot in section 11). No test label of any dataset was read for this draft.

Markers. **[a]** depends on P3 (headroom). **[b]** depends on the full Samsung download/parse. **[c]** depends on reading
Zhang, JES 182, 125097 (unread; title says equivalent-circuit parameter evolution with a PINN, cites this dataset).
**[D]** draft value fixed at freeze. **[R]** rule whose value is computed from training-side data before confirmatory runs.
**[OPEN-n]** needs a ruling at sign-off (section 17). Numbers carry their source: judge (J), pilot file, or `experiments_meta.csv`
(counted by `code/prereg/make_samsung_splits.py`). No coverage, calibration or interval claim is made anywhere (retired topic).

---

## 1. Claim contract

- **Claim (J§1, unchanged).** On held-out Samsung 50E cycling conditions (Test B, primary window) the PINN-KAN has lower
  condition-level retention RMSE than (i) the same network without the physics residual (lambda = 0), (ii) the same PINN with the
  best alternative stress map, (iii) the best tuned data-only learner.
- **Mechanism.** (1) The soft residual holds a shared surface F to a time-driven plus throughput-driven law where there are no
  data (beyond the window, between conditions, 35 C storage twins). (2) A hidden-layer KAN stress map represents interactions of
  (T, SOC window, DoD, C_ch, C_dch) without prespecifying them.
- **Closest methods and exact distinction.** Stroebl et al. (dataset authors; parametric calendar + cycle superposition fitted to
  this data; no learned stress maps; arm A10) and their JES 142, 119552 (states the cycle part is inadequate). PiDDM
  (arXiv 2607.29095; fixed law, parameters from a small MLP of stress; arm A7; no KAN, no joint storage-cycling training, no
  held-out-condition protocol as far as the re-audit read). KA-CRNN (JES 158, 121853; KAN-valued Arrhenius parameters of SOC in a
  neural ODE on thermal-abuse data). PIKAN/PGKAN (SOH estimation, PINN4SOH sets, per-cell life-fraction scaling; not forecasting).
  Zhang JES 182, 125097 **[c]**: positioning unchecked.
- **Competing explanations of a PINN-KAN win** and the control for each:
  E1 gain comes from the per-cell latent z_c and window inversion, not from physics or KAN: data-only F has the same z_c, inputs
  and inversion (A9). E2 gain comes from capacity or tuning budget: equal trials per arm, grids extended at pilot edges, parameter
  counts and effective degrees of freedom reported. E3 gain comes from lab/stage/temperature aliasing (section 3.3): lab and stage
  sensitivity row. E4 gain comes from label-free design-hull information that the data-only learners never see: stated as part
  of the PINN's mechanism and as a limitation; Test B vs Test C shows how much depends on it. E5 gain is window- or horizon-specific:
  windows k-1, k+2 and horizon-wise error.

## 2. Hypotheses (mapped to the judge's claim)

| ID | Statement | Judge ref | Role |
|---|---|---|---|
| H1a | PINN-KAN better than data-only F (lambda = 0) on Test B | J§1 (i) | primary, Holm 3 |
| H1b | PINN-KAN better than the inner-CV-best alternative stress map | J§1 (ii), J§3 | primary, Holm 3 |
| H1c | PINN-KAN better than (or, if [a] says no headroom, non-inferior to) the inner-CV-best of GP-ARD, LightGBM | J§1 (iii), J§7 P3 | primary, Holm 3 |
| H2 | Soft PINN vs hard ODE with the same law: outcome A (PINN better), B (tie), C (hard better) | J§2 | decision contrast, not in Holm |
| H3 | KAN wording: wins / ties / worse than the best GAM (from H1b arms) plus G2 synthetic | J§3 | derived |
| H4 | 35 C held out (Test C): PINN-KAN not worse than best data-only and better than A10 | J§6 Test C | secondary, Holm 3 inside Test C |
| H5 | Storage transfer (S2): the jointly trained law predicts held-out storage conditions | J§5 Opp 6.2 | secondary |
| H6 | PINN-KAN better than the semi-empirical Stroebl-type model (A10), Test B | D006 | key secondary, 1 test |
| H7 | Reduced identifiability on synthetic G0-G2 meets the thresholds of section 13 | J§6 | supporting figure |
| X1 | Cycling-only training (A13) and storage-only training (A14) lose to joint training | ablation | exploratory, no claim |

## 3. Datasets, inclusion and exclusion

### 3.1 Samsung INR21700-50E (primary; figshare 25975315)
Counted from `experiments_meta.csv`: 279 cells = 132 storage (19 conditions: 10/23/45 C x SOC, one 23 C/0.8 centre point of
4 test points = 24 cells) + 147 cycling (40 conditions; 23 C: 10 conditions/33 cells; 35 C: 13/39; 45 C: 17/75; 35 conditions
with 3 cells, five centre points with 6 to 12). Storage at 35 C does not exist; cycling at 35 C does.

### 3.2 Identity of cells (new finding, must be resolved before any parsing) **[b]**
138 of 141 zip names occur twice on figshare (`TP_k01_01.zip` and `TP_z01_01.zip` exist once in stage 1 and once in stage 2, with
different file ids and sizes; `data/DEFERRED_URLS.tsv`, `experiments_meta.csv` `serial` column repeats the same way). A cell is
therefore keyed **(stage, serial)**, as in `st1_TP_z01_01`. The mapping of the two same-name files to stages is decided from the
zip contents, not from file-id order: measurement start dates in `*_meta.txt` (stage 1 is earlier), cross-checked against `m_0`
and `U_0` in the metadata row. A pair where the two checks disagree is excluded and listed. `tools/samsung_cu_batch.py` builds
`urls` as `{name: url}` and stores by serial, so it keeps one file per name; it must be made stage-aware before the cell count of
279 means anything (OPEN-1).

### 3.3 Inclusion and exclusion (rules, none depends on a capacity outcome)
1. Capacity per check-up = mean of charge (step 21) and discharge (step 22) capacity from Coulomb counting of the CU, exCU or ET
   file (dataset paper). A check-up without a complete step 21/22 pair is dropped, not its cell.
2. Reference capacity Q0,c: the ET capacity if ET members exist for every analysed cell, otherwise the first CU for every analysed
   cell (one reference for all cells; chosen once, by availability) **[b]**. Retention = Q / Q0,c.
3. Incident handling, from the paper's "Known incidents" list (file names as printed there). Dropped at file level: TP_z25_01_01_ET_T45
   (undefined load), TP_z01_03_11_CU (concatenated files), TP_z17_03_13_exCU and TP_z17_03_17_CU (incorrect SOC_max),
   TP_z17_02_19_exCU and TP_k11_02_03_exCU (manual charge), TP_z12_*_31_AT_T45 (aborted; AT is excluded anyway). Retained: TP_k[08-11]
   ET files (the failed capacity cycle was replaced by a repeated measurement; only the charge OCV may be affected). Because the paper
   asks to drop "potentially consecutive files", every later check-up of a cell whose cycling segment shows undefined load or a wrong
   SOC_max (TP_z24_01_02, TP_z25_01_04, TP_z07_03_16, TP_z20_03_16, TP_z17 from segment 18) is dropped from that point. Segments with
   only missing log data ("cycling itself was performed correctly") keep their check-ups and use the designed throughput for that
   interval **[b]**. Mapping of each pattern to (stage, serial) cells follows 3.2.
4. Pauses (chamber downtime 15 and 20 days, lab downtime 4 days, stage 2) are kept on the real calendar axis.
5. Storage cells 01-03 of a test point (66 cells) have intermediate check-ups and form the storage trajectories. Cells 04-06 have
   entry and final tests only: **excluded** from training and scoring in the primary analysis; a sensitivity row adds their
   two-point records. The final test (AT) is excluded from the forecast set (dataset paper: AT capacity at 23 C may deviate because
   of preceding 10 C and 45 C tests); an AT-included row is a sensitivity.
6. No cell is excluded because of its capacity trajectory. Cells whose record ends inside the window are scored in a sensitivity
   row as forecast failures (retention carried forward from the last observation, the same rule for every arm).
7. Stage (batch) and lab are recorded covariates. **Confound found in the metadata:** all 39 cells at 35 C were run by lab INT;
   all 75 cells at 45 C by HM except 9 (SIE); storage 10 C is all SIE and storage 45 C all HM. Temperature is therefore aliased
   with lab (and partly with stage) in Test C and S2. Handling: reported in Fig. 2, a lab-and-stage sensitivity row (section 9.5),
   and the Test C wording of section 11. No adjustment in the primary models.

### 3.4 ISU-ILCC and SNL (secondary; cyclic term only)
Splits already fixed in `runs/splits/` (hash checked by every run). Test B analogue only; arms of section 7 without calendar term;
A10 replaced by the cyclic power-law form. ISU uses weeks and an analytic cycles-per-week forcing, calibrated on the 6 fetched
`Cycling_json` members; the ISU authors' EOL MAPE is reported next to ours (J§4). SNL: 61 cells, cell 90-row exclusion from P1.
Claims from these sets are "also holds / does not hold on another chemistry and format", never pooled with Samsung into one test.
**Fallback (J§4, J§8-1):** if Samsung check-ups are not parsed by **07 Nov 09:00**, ISU becomes primary with the same three
contrasts, SNL secondary, no calendar arm, fallback title (section 11).

## 4. Outer splits (Samsung; generated from identifiers only)

Script `code/prereg/make_samsung_splits.py` (reads only `experiments_meta.csv`; same dealing routine as P3), output
`runs/prereg/samsung_splits_DRAFT.json` (copied to `runs/splits/` at freeze; hashes recorded then). Seeds **[D]**:
B 20261107, A 20261108, S2 20261109.

- **Test B (primary): held-out cycling conditions, 5 folds of 8 conditions**, stratified over temperature x stress.
  The five conditions with more than 3 cells (centre points) are dealt first, one per fold. Then, per temperature (23, 35, 45 C),
  conditions are clustered in standardised (SOC_max, DoD, C_ch, C_dch) into ceil(n_T/5) neighbourhoods and the members of a
  neighbourhood are dealt to different folds (fewest-so-far fold, random ties; counts shared across temperatures so fold sizes
  balance). Result (conditions per fold at 23/35/45 C, test cells): f0 2/3/3, 33; f1 3/3/2, 27; f2 1/3/4, 30; f3 2/2/4, 27; f4 2/2/4,
  30. All 132 storage cells (per 3.3) are always in training; no test cycling cell enters training or tuning.
  Hash prefix of the fold block: `9979767d1d27`. Stage and lab are not strata (reported per fold).
- **Test C (secondary): temperature hold-out.** All 13 conditions (39 cells) at 35 C held out; training = 23 and 45 C cycling
  (27 conditions, 108 cells) + all storage. 35 C lies inside the 23-45 C training range (no extrapolation) and has no storage twin,
  which is where the label-free calendar-twin collocation points act. Single split, n = 13 units. Hash prefix `dc53ce82e460`.
- **Test A (secondary): held-out replicates.** 3 folds, each cell of a seen condition in exactly one test fold (49 cells per fold);
  every condition keeps at least 2 cells in training per fold (conditions with 6-12 cells lose 2-4). Own tuning per fold (using
  Test B's tuned settings would let tuning see the held-out cell's replicates). Hash prefix `e1fbcd315fce`.
- **S2 storage transfer (secondary).** 19 storage conditions, 5 folds (3,4,4,4,4 test conditions)
  by blocks of consecutive storage SOC inside each temperature; all cycling cells and the other storage conditions in training; only
  cells 01-03 of a held-out point are scored (cells 04-06 are excluded with their condition). Conditions at SOC 1.0 and 0.05 are
  edges (extrapolation in SOC); the table also reports conditions with SOC <= 0.8, because stage 1 shows non-monotonic behaviour
  above 80 % SOC (dataset paper). A reporting split, not an exclusion. Hash prefix `35f3fbbb9e47`.
- **S3 (exploratory): leave-23-C-storage-out** (7 conditions; train on 10 and 45 C storage + all cycling): a test of the Arrhenius
  structure between two storage temperatures. No claim, no Holm.

## 5. Task, window rule, forecast set

- **Task (identical for every arm).** Inputs: stress vector s (cycling: T, SOC_mid, DoD, C_ch, C_dch, with SOC_max recoverable;
  storage: T, SOC), Q0,c, the window check-ups, throughput rate nu. Output: retention at every later check-up time.
  Time t_tilde = days since the reference check-up, global scaling only (never per-cell life fraction; J§2).
- **Throughput.** Inside the window: logged equivalent full cycles per interval. After the window: the cell's own mean rate over
  the window (causal; no log after the window is used). Oracle-throughput row (logged, all arms) is a sensitivity. **[b]**
  (needs ZYK segments; P0 plans an analytic estimate to be checked on a few cells; if it fails ZYK of all cycling cells is needed).
- **Window rule, in check-up counts, fixed from the schedule alone [R].** Count intermediate check-ups (CU + exCU; ET and AT
  excluded) per cell from the zip member listings (identifiers only, before any capacity is computed). n_med = median over the
  cycling cells; k_cyc = round(n_med / 3) (the first third of the median record); likewise k_sto from the storage cells 01-03.
  Primary window = first k check-ups after the reference; secondary windows k-1 and k+2 (J§6). **[b]** needs all 279 listings (a few
  KB each by range request). Expectation, not a computation: the Samsung figure gives cycling check-ups at weeks 1, 2, 3, 5, 7, 9,
  13, 17, 21, 25 then every 4 weeks, storage at about weeks 5, 9, 17, 25 then every 8; the two listed cycling cells in P0 have 9 and
  16 intermediate check-ups, the storage cell 7, so k_cyc is expected in 3 to 5 and k_sto near 2. Count-based because paused
  intervals make weeks unreliable.
- **Go/no-go from the schedule (J§8-3).** If fewer than 3 post-window check-ups exist for most cycling cells at the primary
  window, Samsung becomes secondary (storage transfer only) and the fallback of 3.4 applies.
- **Forecast set.** For each scored cell: all CU and exCU after the window that survive 3.3, in time order. A cell is scored if it
  has at least one such check-up; the number of forecast points per cell is reported; a sensitivity row restricts to cells with at
  least 3 forecast points.

## 6. Endpoints

- **Primary (one):** cell-level retention RMSE (percentage points) over the forecast set, averaged within condition (mean over the
  condition's scored cells) and then over conditions; Test B, primary window k_cyc, 5 seeds (per-condition value = mean over seeds
  of that condition's RMSE), frozen configuration.
- **Secondary:** (1) the same under windows k-1 and k+2; (2) error at fixed horizons after the window (first post-window check-up
  and the later ones, horizons defined in check-up counts); (3) RUL error in days for cells whose record crosses 80 % retention
  (n reported; none otherwise); (4) MAE, MAPE, R^2 (correct argument order); (5) Test C, S2, Test A, A10 contrast; (6) ISU EOL MAPE
  and SNL analogue; (7) wall clock and parameter count; (8) share of non-finite or diverging forecasts per arm (a non-finite forecast
  is scored with the persistence error and counted).
- **Metrics where a regression is expected** (stated now so that they are not read as a failure): wall clock and parameter count
  (PINN-KAN is slower than LightGBM and A10); error at the first post-window check-up (a data-only learner can be locally better
  next to the window); RUL error (few cells reach 80 %).

## 7. Arms, tuning, budget

Common: tanh MLP solution network F (width 32, depth 3, per-cell latent z_c of dimension 2, hard initial condition), as in the P5
configuration, fixed in every F-based arm and **not tuned** [OPEN-3: conservative for the claim; the data-only F gets a larger
space, below]. Cyclic KAN over (T, SOC_mid, DoD, C_ch, C_dch); calendar KAN [1,2] from storage SOC to (a, E); own compact B-spline
KAN (`code/models/kan_spline.py`), cubic. State factor (backbone) chosen once per outer fold by a tournament on training
conditions with the hard-ODE-KAN at default settings, among {constant, self-limiting 1/(y+y0), accelerating exp(gamma y)}: the
simplest backbone whose inner-CV score is within one standard error of the best, shared by all law-based arms of that fold. Loss
normalisation and optimiser (Adam, steps) frozen by code commit at freeze.

**Budget rule.** Every tuned arm gets the same N trials (TPE, fixed sampler seed = outer-fold index) x 3 inner folds grouped by
condition and stratified by temperature, inside the outer-training conditions only, plus 5 final refits (seeds 0-4). N = 20; N = 40
if the median fit on a Samsung training fold is under 20 s for every neural arm (J§6) **[b]**; the same N for all arms (P2's
partial plan for the hard ODE alone is not used, because it would unbalance the budget). Inner score = window-forecast RMSE on the
held-out inner conditions, the same protocol as the outer endpoint. Edge optimum rule: a chosen value at a grid edge extends the
grid in the next version (P4/P5 show the pilots did this at several edges; extensions below already include them).

| Arm | What it is | Tuned space (extended at pilot edges) | Dims |
|---|---|---|---|
| A1 PINN-KAN | F + residual; cyclic KAN [5,h,1]; calendar KAN | h {2,3,4,6,8} (P4: 4 chosen in 4/5, the old top); grid {2,3,5,8,12} (P4: 3 and 8, both ends); spline L2 {1e-5..1e-2} (P4: 1e-4 at the low edge); sparsity L1+entropy weight {0,1e-4,1e-3,1e-2} (no pilot); lambda_res {1e-2,1e-1,1,10,100} (P5: 1.0 = old top in 2 of 5, 10 worse post hoc) | 5 |
| A2 hard-ODE-KAN | same law, RK4 or exact integration, delta_c MAP from the window, no F | as A1 without lambda_res; at most 60 nodes per cell (P2: 30 s met up to about 60 nodes by interpolation, not measured) | 4 |
| A3 PINN, parametric stress factors | log-linear Arrhenius/power-law factors in 1/T, C_ch, C_dch, DoD, SOC terms | ridge L2 {1e-5..1e-1}, lambda_res | 2 |
| A4 PINN, additive GAM (= KAN [5,1]) | additive cubic splines | grid {3,5,10,20,30} (P4: 5 chosen in 3/5, the old bottom), L2 {1e-5..1e-1} (P4: both edges), lambda_res | 3 |
| A5 PINN, interaction GAM | A4 + tensor-product terms T x C_ch, T x SOC_mid, DoD x SOC_mid | A4 space + interaction grid {3,5} | 4 |
| A6 PINN, polynomial | degree-2 log-polynomial, all cross terms (21 terms) | ridge L2 {1e-5..1e-1}, lambda_res | 2 |
| A7 PINN, MLP stress map (PiDDM-style) | fixed law, parameters from a small MLP of s | width {4,8,16,32}, depth {1,2,3}, wd {1e-5..1e-2}, lambda_res; parameter count capped at the largest count in the A1 space | 4 |
| A8 PINN, free G | dy/dt = exp(MLP(y, s, log nu, z_c)) | width {8,16,32,64} (P4: 32 chosen 4/5, the old top), wd {1e-5..1e-2} (P4: top in 2), lambda_res | 3 |
| A9 data-only F (lambda = 0) | F, same z_c, inputs, window inversion, **no residual, no law** | width {16,32,64,128}, depth {2,3,4}, wd {1e-5..1e-2}, z dim {1,2,3} | 4 |
| A10 semi-empirical (Stroebl) | calendar (3 parameters) + cycle (6 parameters) power-law superposition, least squares, multi-start; exact form from the SI **[b]** (equations garbled in the local conversion; GitHub processing code unread) | none (EOLC fixed as in the SI) | 0 |
| A11 GP-ARD | on (s, window summary, t) | kernel {RBF, Matern 3/2, 5/2}, noise floor, window-summary set | 3 |
| A12 LightGBM | same inputs | ranges as `p3_headroom.py`, frozen by commit | 5 |
| A13 PINN-KAN, cycling cells only | X1 ablation | as A1 | 5 |
| A14 PINN-KAN, storage cells only | X1, S2 only | as A1 (calendar part) | 3 |
| R1, R2 (no tuning) | persistence of the last window retention; linear extrapolation of the window | - | - |

Arms by test: Test B all of A1-A13, R1, R2; Test C same; Test A A1, A2, A9; S2 A1, A2, A3, A9, A10, A14; negative control A1, A9, A4.
LSTM/Transformer, PiDDM reimplementation, BatLiNet/FlowBatt: out (discussed, no numbers; J§6). The judge's arm list had no MLP
stress map although J§1 (ii) names one; A7 is added (OPEN-2).

**Comparator selection (no test information).** For H1b the comparator in each outer fold is the A3-A7 arm with the lowest mean
inner-CV score on that fold's training conditions; for H1c the lower of A11/A12 the same way. Its outer-fold predictions are the
ones compared. All individual alternatives are also reported against A1 (Table 2) as descriptive contrasts, Holm over the five.
Selecting the "best alternative" by outer test error is not allowed (J hard rule).

## 8. Seeds

Final refits: seeds 0, 1, 2, 3, 4 (initialisation and collocation sampling). Tuning seed 1000 + outer fold, TPE sampler seed = outer
fold. Per-condition value = mean over seeds; the seed SD per condition is reported next to every endpoint. Seeds are not units.

## 9. Statistical analysis

1. **Unit = condition** (Test B 40, Test C 13, S2 19, Test A 40; ISU 63; SNL 23). Condition score s_{a,c} per section 6.
2. **Contrast** d_c = s_comparator,c - s_PINN-KAN,c (positive favours PINN-KAN), paired on condition and on the same seeds.
3. **Margin delta [R].** Per outer fold f, delta_f = median over the fold's training conditions of the leave-one-replicate-out RMSE
   of the other replicates' mean trajectory (the judge's replicate floor; implementation = `replicate_floor` in `p3_headroom.py`,
   time-interpolated), computed by inner CV inside the training conditions only, with the same window and forecast rules. Pooled
   delta = weighted mean of delta_f by test conditions per fold. Test C, S2 use their own training side. No test label enters delta.
4. **Primary tests.** One-sided exact Wilcoxon signed-rank on d_c - delta (superiority by at least delta), Holm over H1a, H1b, H1c at
   family-wise 0.05; a contrast **passes** only if the Holm-adjusted p <= 0.05, the mean of d_c >= delta, and the 10,000-resample
   cluster bootstrap (by condition) 95 % interval of the mean of d_c excludes 0. For H1c under non-inferiority **[a]**: test
   median(d_c) > -delta (shift d_c + delta), same Holm family and same bootstrap check on the lower bound. Two-sided unshifted p
   values are given in the appendix.
5. **Feasibility check of the superiority margin [R] [OPEN-4].** J§6 fixes delta = replicate floor and J§7 P3 calls superiority
   winnable when the best flexible learner exceeds 1.2 x floor. A superiority margin of one floor cannot be reached unless the best
   comparator's inner-CV error exceeds about 2 x floor (the model cannot be below the floor). Before the freeze the ratio r_f =
   (inner-CV error of the best of A11/A12 and the per-cell power law) / floor_f is computed on every training side. If the weighted
   mean of r_f is below 2, the default replacement (chosen now, before any outcome) is: superiority tested at margin 0
   (Holm-adjusted p and bootstrap excluding 0) and non-inferiority kept at delta. The statistician may overrule at sign-off.
6. **H2 (hard vs soft).** d_c = s_hard - s_PINN. A: mean d >= delta with p <= 0.05 (one-sided, shifted) and bootstrap excluding 0.
   B: the 90 % bootstrap interval of mean d inside (-delta, +delta) and both shifted one-sided Wilcoxon tests at 0.05 (equivalence).
   C: mean d <= -delta with p <= 0.05 (reverse direction). Anything else: "unresolved", worded as B, direction reported. Separate
   alpha 0.05, not in the Holm family (J§1: it does not refute the claim).
7. **KAN wording (H3).** Against the best interaction-capable GAM (inner-CV-best of A4, A5): win = H1b passes and G2 passes (section
   13); tie = equivalence within +-delta as in 6; worse = mean d <= -delta, p <= 0.05 reverse direction; otherwise "unresolved".
8. **Effect sizes (always shown):** mean d in pp, relative reduction, matched-pairs rank-biserial r, share of conditions won, per-fold
   means (heterogeneity), the cluster-bootstrap interval. Neighbour correlation between conditions is not modelled (stated).
9. **Other families.** Test C: the three contrasts of H1 with Holm inside Test C (n = 13, low power, stated). H6: one test, A10
   vs A1, shifted at margin 0. S2: non-inferiority of A1 to the best of A3, A9, A10 at delta_S2. Everything else descriptive;
   exploratory results are labelled and unadjusted.
10. **Sensitivity rows (appendix):** lab-and-stage one-hot added to z_c prior for A1, A9, A12 (E3); AT included; cells 04-06 of
    storage included; cells with at least 3 forecast points; forecast-failure rule of 3.3(6); oracle throughput; backbone fixed to
    self-limiting; all window variants.

## 10. Controls

- **Negative control (effect must vanish).** In each Test B outer fold the stress vectors (with their design throughput) are permuted
  among conditions, separately in training and test sets, window data untouched; A1, A9, A4 are re-run with the same budget.
  Required: contrast A9 - A1 has mean d < delta and unshifted two-sided Wilcoxon p > 0.05; A1 does not beat R2 (window-linear
  extrapolation) by more than delta. A violation means leakage through something other than stress: stop and audit (section 12).
- **Positive controls (known effect the pipeline must recover).** (P1) Synthetic G0 (well specified): the structured arms recover the
  log-rate surface with nRMSE <= 0.15 (J pass line) and beat A11/A12 on G0 forecast RMSE (paired Wilcoxon p < 0.05, 20 draws).
  (P2) Real storage cells: the fitted calendar rate increases monotonically with temperature at every SOC inside the storage hull
  (a deterministic check of the learned law, computed from training fits). (P3) A1 beats R1 (persistence) with margin 0 in Test B;
  a physically trivial improvement the pipeline must show.

## 11. Outcomes and consequences (stated before any outcome)

Evaluate gates first, then rows in order; the first row that applies governs. Titles are those of J§1.

| # | Condition (Samsung, Test B unless stated) | Consequence: title and wording |
|---|---|---|
| G | Negative control or a positive control fails, or an audit finds a test fold read by tuning | No outcome row applies. Stop, audit, rerun under a new version. No claim. |
| 1 | H1b "KAN worse" (section 9.7) | KAN leaves the headline; lead puts the retitle to Shlok (J§3). |
| 2 | H1a not passed (residual no better than lambda = 0 by delta, or worse) | "Physics residual unnecessary" reported plainly; outcome-C logic: the lead puts the framing and retitle to Shlok (J§6). |
| 3 | H1c fails even non-inferiority (best data-only better by delta) | No forecast-accuracy claim. The paper can only offer physical consistency (H4, H5, residual map) or stop; lead tells Shlok before any writing. |
| 4 | H1c non-inferior only, or [a] preregisters non-inferiority for Samsung | Claim "parity in accuracy plus physical consistency" (J§6 tie plan). **Title 3.** Lead tells Shlok before writing. |
| 5 | H1b equivalence (KAN ties the best interaction GAM) or unresolved | Tie wording of J§3: KAN stress functions reach the accuracy of the best prespecified-interaction GAM without specifying the interactions, and their curves agree; no superiority wording. **Title 3.** |
| 6 | H1a, H1b, H1c all pass (superiority), H2 = A | Primary claim holds, PINN contribution shown. **Title 1** (title 2 allowed). KAN superiority wording only if G2 also passes (section 13). |
| 7 | As 6 but H2 = B or unresolved | Residual equals exact integration for forecasting at this design; PINN kept for the residual map and solver-free training; claim rests on the calendar-cycle KAN law and H1a. **Title 3** (J§2). |
| 8 | As 6 but H2 = C | Framing choice to Shlok: C1 (recommended by J) hard-constrained physics-informed KAN, title 2 with that wording; C2 PINN headline with the hard ODE reported stronger. |
| T | Test C (H4) | If H4 passes: the abstract may say "including a temperature absent from training" with the lab-confound sentence. If not: the sentence is removed, the title keeps "untested conditions" (Test B). Never a ratio B vs C (retired topic). |
| S | S2 (H5) | The sentence "the storage law learned jointly predicts held-out storage conditions" only if non-inferior; else removed. |
| K | H6 not passed (A1 not better than A10) | The abstract says so; no "outperforms physics-based baselines"; lead considers J§8-2 style re-check. |

Fallback title if Samsung is not parsed by 07 Nov 09:00 (J§1) and rows apply on ISU. "Identifiable" never appears in a title.
**P3 slot [a]** (the rule of J§7 P3: ratio of best flexible learner's inner-CV error to the median replicate floor, > 1.2 means
superiority, <= 1.2 means non-inferiority for H1c, per dataset; training folds only):
ISU: `[P3 ISU W=4/6: pending]`; SNL: `[P3 SNL W=100/200: pending, partial files exist and were not read]`; Samsung: `[must be rerun on the
Samsung training sides after cadence is known **[b]**; the ISU and SNL answers do not decide it]`. Superiority vs non-inferiority per
dataset is written here at freeze.

## 12. Stop rules

1. Samsung check-ups not parsed by 07 Nov 09:00: fallback of 3.4. 2. Schedule go/no-go (section 5). 3. Any gate G of section 11.
4. A test fold read by any tuning, selection or delta step: the run is void. 5. Compute: if the projection of section 16 exceeds the
agreed cap, cut arms in this order: A14, S3, A13, Test A arms, sensitivity rows; trials and seeds are never reduced. 6. No interim
look at outer-test results: each frozen configuration is scored once, after all folds are finished.

## 13. Identifiability protocol (one figure + appendix; synthetic only; J§6)

- **Design:** the real Samsung design (40 + 19 conditions, replicates, cadence and window from section 5) **[b]**; ISU design as in P4/P5.
- **Generators** written before any real fit, truth never from model fits: G0 well specified (positive control); G1 misspecified time law
  (t^z with z depending on T, plus a logistic knee in throughput whose onset shifts with stress); G2 non-additive stress law (charge-rate
  hinge with a temperature-shifted threshold, plus DoD x SOC product); optional G3 storage and cycle terms not additive. Pilot grids
  are in `runs/pilot_P4/config.json`. **G2 strengthened:** P4 found the additive-GAM class floor on the true surface at 0.05-0.07,
  below the 0.15 pass line, so G2 could not discriminate. The confirmatory G2 uses the upper values of the pilot grid for the hinge
  H = 1.2 and the product P = 0.8 (no new numbers); the pilot-strength G2 is a sensitivity. **Validity rule:** computed before fitting
  any model, a G2 draw is discriminating only if its additive-GAM class floor exceeds 0.15; if the median floor stays below, KAN
  superiority cannot be claimed from G2 and H3 "win" is unavailable.
- **Constants:** fade level, noise and offset spread follow the pilots (round numbers: median final fade 20 pp, noise 0.5 pp, offset
  sd 0.15), not matched to Samsung summary statistics as J§6 asked, because matching needs label-derived scalars (OPEN-6).
- **Metrics:** nRMSE of the recovered log-rate surface on the fixed 500-point hull Latin hypercube divided by the true range
  (absolute level included, as defined in J, centred reported alongside because P4 showed free-G carries a level offset: KAN/free 0.61
  absolute but 0.76 centred); Kendall tau of variance-based stress importance with truth; forecast RMSE on held-out conditions.
- **Thresholds (J§6):** pass nRMSE <= 0.15 on G1 and G2, fail > 0.30, between = partial. Structured median <= 0.67 x free-G median and
  paired Wilcoxon p < 0.05 over 20 draws. KAN lower than additive GAM on (strengthened) G2, paired p < 0.05; on G0 KAN not above GAM by
  more than 10 %. Because P4 passed "any structured" only on the absolute metric (GAM/free 0.76), the claim is stated for the
  KAN-structured model; it extends to "structured" generically only if the GAM also meets 0.67. Interval widths: diagnostic, no claim.
- **Hard vs soft on G1:** the H2 contrast on synthetic data (20 draws, paired); P5 saw PINN below hard in 4 of 5 draws with a small
  median ratio (0.96 primary, 0.84 whole-axis collocation) and one reversal. Collocation placement (record end vs whole time axis) is
  decided on training-condition inner CV, not on P5. Residual map: optional G3; a residual-map claim needs a rank-correlation threshold
  with the true violation surface that the statistician sets before G3 runs; without it Fig. 7 carries no claim.
- **Size:** 3 generators x 20 draws x 4 models (A1, A2, A4, A8) = 240 fits at the pilot tuning effort (8 trials x 2 inner folds, equal
  across arms), plus G1 hard vs soft 20 draws.

## 14. Figures and tables (10 items; JES limit 8-10; forms per BLUEPRINT.md and D-figures)

| Item | Content | Hypotheses |
|---|---|---|
| Fig. 1 | Method schematic (data strip, F/G, KAN stress functions, collocation sets) | mechanism |
| Fig. 2 | Design map: storage and cycling conditions, replicate fade, **lab and stage colouring (confound)** | 3.3(7), H4, E3 |
| Fig. 3 | Forecast overlays at held-out conditions, 35 C row boxed, window shaded | H1, H4 |
| Fig. 4 | Forest plot of paired condition-level differences, all arms vs A1, Holm intervals | H1a-c, H2, H6 |
| Fig. 5 | Learned stress functions a(SOC), E(SOC), cyclic partial dependences, seed/fold envelopes, GAM dashed | H3 |
| Fig. 6 | Storage transfer parity and storage share of cycled-cell fade | H5, S3 |
| Fig. 7 | Residual map |R| over (T, SOC) and (C-rate, T) | H2 mechanism, G3 |
| Fig. 8 | Synthetic recovery G1, G2 (G0 as control) with thresholds 0.15/0.30 | H7, H3 |
| Table 1 | Arms x {Test B, C, S2, ISU, SNL}, mean +- seed SD, Holm p, time, parameters | H1, H4, H5, H6 |
| Table 2 | Ablations and controls: what changes, parameters, delta primary endpoint, negative/positive control results, X1 | H1, X1, section 10 |

Appendix (supplementary, JES policy): hyperparameter tables, sensitivity rows, windows, symbolic rounding of KAN, GAM and polynomial,
chosen settings per fold, decision log of section 11.

## 15. Order of runs, by information per CPU-hour (all CPU; 3 single-thread processes)

1. Analytic and data checks (minutes): stage-aware cell identity (3.2), listings, n_med and k, split hashes, incident handling, Q0
   reference rule. 2. Synthetic G0-G2 and G1 hard vs soft (about 6 CPU-h): positive control and identifiability before any real fit.
3. Training-side measurements (no outer test): replicate floor and delta_f, P3 headroom on Samsung **[a][b]**, feasibility check of
   9.5, backbone tournament, timing on a Samsung fold (fixes N). 4. Core of Test B: A1, A2, A9, A11, A12 (decides H1, H2). 5. Rest of
   Test B arms, negative control, Test C. 6. S2, Test A, sensitivity rows, then ISU and SNL.

## 16. Compute budget (CPU only, from P2 timings; arithmetic, not a Samsung measurement)

Fits per arm and outer fold = 3N + 5 (N = 20: 65; N = 40: 125). P2 (1 thread, 61 cells; 2,000 Adam steps): PINN 13.3 s at 20 points per
cell to 18.9 s at 80 points, 50.6 s for 279 cells (tiled) at 80 points; hard ODE 11.4 s at 20 nodes, 18.5 s at 40, 38.4 s at 80,
42.0 s for 279 cells at 80 nodes. Samsung has about 20 nodes or fewer per cell, so the expected column uses the low values, the ceiling
column the 279-cell, 80-point values. Threads: hard ODE gains nothing from threads; 3 single-thread processes in parallel, each
about 0.7-0.8 GB RAM (P2: 691-840 MB peak), about 2.5 GB in total, below the 3.6 GB free at night (D002); no GPU.

| Block | Outer folds x arms (neural) | N = 20 expected / ceiling, CPU-h | N = 40 expected / ceiling, CPU-h |
|---|---|---|---|
| Test B | 5 x (9 PINN-type + 1 hard) | 11.8 / 44.9 | 22.8 / 86.4 |
| Test C | 1 x (9 + 1) | 2.4 / 9.0 | 4.6 / 17.3 |
| Test A | 3 x (2 + 1) | 2.1 / 7.8 | 4.0 / 14.9 |
| S2 | 5 x (4 + 1) | 5.8 / 22.1 | 11.2 / 42.4 |
| Negative control | 5 x 3 | 3.6 / 13.7 | 6.9 / 26.4 |
| Subtotal neural | | 25.7 / 97.4 | 49.4 / 187.3 |
| Synthetic (pilot tuning effort, scaled from P4 266 s and P5 232 s per draw) | 60 + 20 draws | about 6 | about 6 |
| GP-ARD (ISU W=4 log: 526-539 s per outer fold; timing only) | 14 folds | about 2 | about 2 |
| LightGBM, A10, R1, R2, bootstraps | | negligible | negligible |

Wall clock on 3 processes: N = 20 about 11 h expected, about 35 h ceiling; N = 40 about 19 h expected, about 65 h ceiling. Not included:
sensitivity rows (about the cost of the negative control each, about 4-14 CPU-h), ISU and SNL (cyclic only; smaller). PINN cost
falls with data (P2), so inner folds on two thirds of the conditions are cheaper than the ceiling; the ceiling treats every fit
as full size. P2's rule stands: PINN GO; hard ODE inside the 30 s budget if nodes <= about 60 (tested at 80: 1.28x).

## 17. Open items and dependencies

**(a) P3:** the superiority vs non-inferiority entry for H1c per dataset (section 11 slot); the feasibility check of 9.5 uses the same
quantities. **(b) Full Samsung download/parse:** stage-aware identity 3.2 (and the batch fetcher, OPEN-1); n_med and k (section 5);
Q0 reference (ET vs first CU); throughput source; incident file resolution; A10 exact form; N from a Samsung timing run; G0-G2 design
from the real cadence; Samsung P3. **(c) Zhang JES 182, 125097:** novelty positioning (re-open trigger J§8-2 if it contains a neural
calendar + cycle model with learned stress functions evaluated on held-out conditions), whether it supplies a comparator or a metric
definition on this dataset (a new arm would be a new version). Nothing else in the numerical design depends on it.
**Rulings needed at sign-off:** OPEN-1 repair of the duplicate-name mapping in the fetcher; OPEN-2 add A7 (MLP stress map) to the arm
list; OPEN-3 F fixed rather than tuned in PINN arms; OPEN-4 superiority margin vs replicate floor (9.5); OPEN-5 whether H6 (A10) should
join the primary Holm family (reviewers see it as the closest prior art; family size 4); OPEN-6 synthetic constants matched or round.

## 18. Freeze protocol and change log

Freeze requires: `statistician` sign (sections 6-9, 16), `red-team` sign (sections 1, 10, 11), `gate-auditor` check of pilot
numbers quoted here (P4/P5 had a pending audit), code commit hash, split hashes, grid files, the resolved [OPEN] items and filled
slots. After freeze: new version file plus log row; no edit. Test-set results never choose hyperparameters, comparators or wording.

| Version | Date | Change |
|---|---|---|
| v0.1 DRAFT | 2026-11-05 | first draft; splits generated from identifiers only; nothing frozen |
