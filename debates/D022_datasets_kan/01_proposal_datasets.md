# D022 (datasets part), proposal: NASA and CALCE as a pre-specified secondary section

Author: proposer (datasets), 2026-11-05. Status: proposal for the opponent and the judge. Nothing in PREREG_v4, the code or the approved table (D017/D019) is edited by this file.
Question from the supervising professor: "apart from SAMSUNG DATASET, check NASA AND CALCE DATASET; if possible, include both datasets for experimental results".

**Reading depth (CONTRACT section 1).** `research/CONTRACT.md`: full text. `notes/data/NASA_CALCE_feasibility.md`: full text (its own reading depth: NASA READMEs full, repository and CALCE pages = page digests, CALCE papers not read; no capacity, SOH or fade value was read there). `runs/prereg/PREREG_v4.md`: sections 1-16 full text (lines 1-430); sections 17-22 not read. `runs/prereg/stats_sim_v4/RESULT.md`: section 0 and the interval table of section 3 only. `debates/D021_cap/01_architect.md`: sections 1-5 (cap = 2, which fixes what A15/G15 can be). Code: `grep` of `code/pinnkan/specs.py`, `data.py`, `semi.py` and the head of `code/README.md` (the `DatasetSpec` mechanism, `has_calendar=False` for ISU/SNL, the ISU/SNL cyclic-only A10). **No Samsung, NASA or CALCE capacity value was opened and no number in this file is computed from capacity.** Numbers are quoted from the files named beside them; the few arithmetic lines are marked "arithmetic".

---

## 0. Decision requested (one paragraph)

Add **one pre-specified, descriptive, ungated secondary section** ("two further ageing campaigns") that re-runs the Samsung *task* (forecast held-out cycling conditions from the first k check-ups) on **(1) the CALCE graphite/LiCoO2 pouch cells (SOC-window x discharge-rate design, 8 conditions x 2 cells)** and **(2) the NASA PCoE set 5 18650 cells (5 temperature x current groups, 23 cells)**, each analysed **on its own**: a model is fitted on the training conditions of that campaign and scored on held-out conditions of the same campaign; nothing is trained on one campaign and tested on another, and no error is compared across campaigns. Arms: the cycling-only members of the Samsung set (A1c, A9, A4c, A2, A10c, D\*, R1, R2); same endpoint, same tuning-budget rules, same ensemble rule. Statistics: counts, medians and exact range intervals of the per-condition log ratio; **no test, no tier word, no entry in the graph or the secondary family, no change to any title, abstract claim sentence, state or clause of the closed table.** NASA is labelled "previously analysed data" and ranked last in the compute-cut order; CALCE PL is labelled "not previously analysed by the authors". CS2/CX2 and the NASA randomized/HIRF sets are checked and recorded as "considered, not analysed", with reasons. The plan is a separate addendum card, frozen after the Samsung `FROZEN` and before any model touches these data.

---

## 1. Proposal and its evidence

### 1.1 What is added and what is not (summary table)

| Item | CALCE PL pouch (EXT-PL) | NASA set 5 (EXT-NA) | CALCE CS2/CX2, NASA set 11/15 |
|---|---|---|---|
| Role | secondary section, descriptive | appendix-level, descriptive, "previously analysed" | recorded as considered, not analysed |
| Units (held-out) | 8 conditions (2 cells each) | 5 (T, current) groups, 23 cells | - |
| Task | leave-one-condition-out, k check-ups | leave-one-group-out, k check-ups | - |
| Law | cycling-only (no calendar KAN, no storage arm) | same | - |
| Gate / alpha | none (isolated from gate G) | none | - |
| Abstract / title | unchanged | unchanged | - |
| Evidence for the row | feasibility note section 4 (two of 16 cells parsed; downloads incomplete) | feasibility note section 1 (complete, parsed) | feasibility note sections 2, 3 |

### 1.2 Claim contract for the add-on (experiment-designer step 1)

- **One-sentence claim (descriptive, no test):** when the Samsung task is repeated on two other cycling campaigns, the report states, per campaign and per window length, in how many of the held-out conditions the cycling-only physics-informed KAN model (A1c) had a lower condition error than the best data-only learner (D\*), than the same network without the law (A9), than the hard ODE (A2) and than the semi-empirical cycle model (A10c), with the median log ratio and the exact range, whichever direction it takes.
- **Mechanism being looked at (same as Samsung P1/P2, restricted):** a rate law with a state-dependent modulation lets a few training conditions and a few early check-ups constrain a forecast that a data-only learner has to interpolate. Not examined here: the KAN-law extraction (K chain), the storage term (Q-T), the scarcity interaction (P3: no m axis exists on these sets), anything about temperature separated from laboratory.
- **Closest methods and exact distinction.** On NASA set 5 the usual protocol in the literature is within-cell or cell-split SOH regression on B0005/6/7/18; our task (held-out stress group, forecast from a window, retention curve) differs and **its numbers are not comparable with those papers; no such comparison is made** (stated limitation). On the CALCE pouch cells the dataset's own modelling is Saxena, Hendricks and Pecht, J. Power Sources 327 (2016) 394-400 (page digest only; paper not read; DOI to be verified on Crossref before any citation), a cycle-life model by SOC window; it is neither a PINN nor a held-out-condition forecast, and it is not a comparator in our arm list (limitation). These sets are not in the novelty claim of the paper.
- **Competing explanations of any direction seen, and the control for each.**
  - E-a *Batch/date confound on NASA:* each temperature group was a separate batch with its own current set (feasibility 1, "Confounding"); a held-out group is a batch. Control: none possible; stated, and NASA is descriptive.
  - E-b *Capacity measured at the stress condition on NASA:* capacity is read at the cycling current, temperature and cell-specific cut-off, so retention mixes ageing with rate/temperature capacity effects (feasibility 1, "Capacity measurement"). Control: per-cell reference (retention relative to the cell's own first discharge), plus the statement; no claim about intrinsic ageing.
  - E-c *Prior exposure of NASA labels to the author:* design choices could be shaped by remembered results. Control: every rule is written from schedule counts and identifiers, hashed before any model is fitted; NASA ranked last; labelled previously analysed.
  - E-d *Loss of the Samsung information advantages:* on Samsung A1 profits from the 132 storage cells and label-free collocation in the training hull (PREREG E4/E6); neither exists here. A direction on these sets therefore says nothing about the Samsung mechanism and the section does not argue from it.
  - E-e *Window drift and missing blocks on PL:* windows are held by Coulomb counting, so the realised SOC window shifts with fade; some blocks are "Data Missing" (feasibility 4). Control: nominal window used as the stress coordinate, disclosed; a sensitivity row with designed throughput for missing blocks.
  - E-f *Replicates and few units:* two cells per PL condition, 2 to 8 per NASA group; the unit is the condition/group, n = 8 and 5. Control: unit-level reporting only; per-unit values are all printed.

### 1.3 Framing guard (retired topic)

The retired paper asked how the evaluation split, cross-dataset or laboratory-to-field shift changes SOH accuracy and uncertainty (CONTRACT section 1). The add-on is built so that it cannot be read that way:
1. **One model per campaign**, trained and tested inside the campaign. No Samsung-trained model is applied to NASA or CALCE; no pooled training set; no transfer.
2. **No cross-campaign error comparison.** No table, figure or sentence puts the Samsung error beside the NASA or CALCE error or forms a ratio of them (the same rule as "No Test B vs Test C ratio anywhere", PREREG 4). The only cross-campaign statement permitted is a count of which arm had the lower error *inside* each campaign.
3. **Vocabulary.** Allowed: "further ageing campaigns", "re-run of the same task", "descriptive". Not used: "cross-dataset", "generalisation across datasets", "transfer", "domain shift", "protocol", "leakage" (as a theme), "validation on external data". The section's heading is not "Generalisation".
4. **Splits are by condition inside the campaign**, which is the paper's own held-out-condition design, not a new protocol contrast. No random-cycle, within-cell or cell-split variants are run.
5. No interval or coverage claim about forecasts (retired topic 2); only the paired log-ratio of condition scores.

### 1.4 Data, inclusion rules and stress coordinates (identifiers and schedule only)

**General rules copied from PREREG 3.3 unchanged:** retention = Q / Q0,c with the cell's own reference; the causal isolated-outlier rule and the information flags exactly as in 3.3(3) with the same thresholds (no refit to these sets); a failing check-up is dropped, not its cell; no cell is excluded because of its capacity trajectory (3.3(8)); a retain-every-check-up sensitivity row.

**EXT-PL (CALCE pouch; rated 1.5 Ah; all numbers from feasibility 4, page digest).**
- 16 cells, 8 conditions, 2 cells each. Windows are nominal; charge C/2 everywhere; temperature not stated on the page (constant, not an input; to be confirmed by reading Saxena et al. before the card is frozen).
- Condition table (SOC window; mid / depth; discharge rate): c1 0-60 (30/60, C/2); c2 40-60 (50/20, C/2); c3 40-60 (50/20, 2C); c4 0-100 (50/100, C/2); c5 0-100 (50/100, 2C); c6 20-80 (50/60, 2C); c7 40-100 (70/60, C/2); c8 20-80 (50/60, C/2).
- **Active inputs of the cyclic KAN: (SOC_mid, DoD, C_dch)**; the rule is general: *an input is active iff it takes at least two distinct values among the campaign's conditions* (the 3.4 precedent: the ISU "three-input cyclic KAN"). C_ch (constant C/2) and temperature (constant) are inactive.
- Reference check-up = the initial full characterisation. Check-up = a full C/2 characterisation cycle between partial-cycle blocks (every 50 or 100 partial cycles per the page digest; the operation table decides). Capacity by Coulomb counting of the discharge step.
- Clock: EFC = cumulative discharged Ah / 1.5 Ah (arithmetic on the rated value), counted from the data; for blocks labelled "Data Missing" the designed throughput of the block is used and a flag is set (row (v) below).
- Cells enter only if the member is complete and its CRC passes (feasibility 6). **Campaign go/no-go on completeness (decided from identifiers):** PL is analysed iff at least 6 of the 8 conditions have both cells readable when the addendum card is frozen; the set is not extended afterwards. Otherwise PL is reported in one sentence as "not analysed: incomplete download" and the freeze of the card lists the reason.

**EXT-NA (NASA set 5; feasibility 1).**
- Inclusion by README stress definition: a cell is a point in (T, C_dch) iff its protocol is one fixed temperature and one constant discharge current. Excluded and listed: B0025-B0028 (square wave, not a constant-current coordinate; B0028 README and data disagree), B0038-B0044 (temperature or current changes inside the cell). 34 - 4 - 7 = 23 cells (arithmetic).
- **Five groups (the held-out unit):** G1 24 C / 2 A (B0005, 06, 07, 18, 36; 5 cells); G2 24 C / 4 A (B0033, 34; 2); G3 43 C / 4 A (B0029-32; 4); G4 4 C / 1 A (B0045-48; 4); G5 4 C / 2 A (B0049-56; 8). The 21 nominal tuples of the feasibility note are *not* the unit: tuples inside a group differ only by cut-off voltage (2.0-2.7 V, "a weak depth-of-discharge lever"), so holding out one tuple leaves 3 near-replicates in training and turns the task into replicate prediction. Cut-off is a within-group factor, not an input.
- **Active inputs: (T, C_dch)** with C_dch = I / 2 Ah (0.5, 1, 2 C). Charge protocol, SOC window and DoD are constant and inactive.
- Reference = the cell's first quality-passed discharge; every discharge is a check-up (capacity every cycle).
- Record-level QC (drop the record, not the cell): non-positive or missing capacity; all-zero current; minimum voltage more than 0.3 V below the cell's cut-off or the discharge not reaching within 0.3 V above it (B0033, B0040, B0050, B0052 anomalies, feasibility 1 (v)); plus the 3.3(3) outlier rule. The 0.3 V band is a design choice made from the README cut-off list, not tuned on capacity.
- Clock: EFC = cumulative discharged Ah / 2.0 Ah (rated, README).
- Duplicates (B0025-28 in two inner zips) are counted once; the original `.mat` files are used, not the Drive CSV copy.

### 1.5 Task, splits, window, grid

- **Splits (deterministic, from identifiers, written to `runs/splits/` with a hash before any model sees data; CONTRACT 6).** PL: 8 folds, each holding out one condition (both cells); training = the other 7 conditions (14 cells). NASA: 5 folds, each holding out one group; training = the other 4 groups. No random element, hence no seed.
- **Hull status declared in advance** (not exclusions): PL folds c1 (only SOC_mid 30) and c7 (only SOC_mid 70) extrapolate in SOC_mid; the other six interpolate in every active input. NASA folds G3 (only 43 C) and G4 (only 1 A) extrapolate; G1, G2, G5 interpolate. A "interpolating folds only" row is reported beside the all-fold row.
- **No m axis.** The training side is the whole campaign minus the held-out unit (7 PL conditions; 4 NASA groups). A learning curve over the number of conditions is not specified (7 and 4 are the largest m; m of 2-6 on PL is "too few points for a trend claim", feasibility 4(b)); P3 has no analogue.
- **Window rule: the Samsung rule, applied per campaign from the schedule alone (PREREG 5, FB-6).** k_full = round(n_med / 3) with n_med the median number of intermediate check-ups per included cell, **counted from the operation tables / discharge records before any capacity is read**. Grid: PL k in {0, 2, k_full}; NASA k in {0, round(k_full/2), k_full} (check-ups come every cycle, so "2" has no meaning there; the half-window keeps the ratio of the scarce to the full window roughly as on Samsung; a design choice). Arithmetic from the feasibility counts for NASA: the 23 included cells have discharge-record counts with median 72, so k_full = 24 cycles and the half window 12 (the script recounts). For PL the count is unknown (only 2 of 16 cells parsed). If k_full = 2 on PL the grid is {0, 2}; if k_full < 2 PL is no-go (as PREREG J16 section 8).
- **Forecast set:** all later quality-passed check-ups of the cell, to the end of its record (no life-level cut: the sets do not all reach a common retention level); a cell is scored with at least one forecast point; the number of points per cell is reported; a sensitivity row restricts to cells with at least 3 (PREREG 5).
- **Headline row per campaign:** A1c against D\* at the scarce window (PL k = 2, which with 7 training conditions is the nearest analogue of g1 = (8, 2); NASA half window). All other rows are reported without ranking.

### 1.6 Arms, tuning, endpoint (same rules, nothing new to tune)

| Arm | On the extra campaigns | Change from PREREG 7.1 |
|---|---|---|
| A1c | PINN-KAN, cyclic KAN on the active inputs only, **no calendar KAN** (`has_calendar=False`, as ISU/SNL) | input mask; same tuned space, same `h` set, same F net (width 32, depth 3, z dim 2) |
| A9 | same network, physics off | none |
| A4c (= AG here) | PINN with additive GAM law | A5 (interaction GAM) not run: 7 or 4 conditions cannot support tensor terms |
| A2 | hard ODE, same law, closed form | none |
| A10c | cycle term only of the dataset authors' model (the ISU/SNL analogue already in `semi.py`: same power-law structure on the stresses, no calendar term) and both forms (with and without the per-cell factor) | **defined only if** the coder's unit test shows the cycle term separable; otherwise omitted with a change-log row, no substitute |
| D\* | inner-CV best of {A9, A11, A12}; feature sets as in 7.4 restricted to the active inputs (PL: SOC_mid, DoD, log C_dch; NASA: 1/T, log C_dch) plus t and EFC; **storage-rows option removed** (no storage cells) | none else |
| R1, R2, k = 0 reference | as defined | none |
| Not run | A13 (no storage), A15/G15 (extraction from 7 conditions at cap 2 is not a K1/K2 test), A5, A7, GRU | struck; K chain stays Samsung-only |

- **Tuning budget:** the same N, the same sampler rule, and the same inner-fold rule that the frozen Samsung `budget_rule.json` fixes for a training side with fewer than 32 conditions (2 inner folds, or 4 if pilot P6b adopted four); grouped by condition inside the training side. **No timing run of its own and no Partial-plan re-decision**: if the Samsung rule says N = 40 or 20, the extras use that. Tuned once per fold, scored in inner CV at the scarce window, applied at every k (7.1 rule for m < 32). Hard-ODE backbone tournament once per fold on that fold's training units, as in PREREG 7 / D20 6.
- **Endpoint:** cell RMSE (pp) of the five-seed ensemble forecast over the forecast set, mean over the unit's scored cells, then the paired log ratio L_u = ln(S_comparator,u / S_target,u) per held-out unit; positive favours A1c. Mean paired pp difference and the worst-unit error are printed beside every median (the 9.8 rule 1 reading: if the sign of the mean disagrees with the median, the Results sentence adds both).
- **Seeds:** final refits 0-4; tuning seed 1000 + fold index (NASA: fold index 0-4; PL: 0-7); TPE sampler seed = fold index; no Monte Carlo step is needed (counts and order statistics only), so the 20261105 root is unused.

### 1.7 Statistics: descriptive, with exact intervals (and why no gated family)

Machinery: the sign-test and order-statistic helpers of `graph_test.py` (RES section 1), used only in their *interval* form.

| Quantity | Rule | Numbers (arithmetic, n fixed by the design) |
|---|---|---|
| Per unit | condition score, log ratio | PL n = 8; NASA n = 5 |
| Count | positives = units with L_u > 0 (L_u = 0 is not positive) | reported as "k of n" |
| Interval for the median | the full range [L(1), L(n)] of the sorted unit log ratios | coverage at independent units 1 - 2^(1-n): **0.9922 (n = 8)**, 0.9688 (n = 6), **0.9375 (n = 5)**; the next inner interval has only 0.9297 (n = 8) and 0.625 (n = 5) |
| Smallest exact one-sided p of a unanimous result | 2^-n | 0.0039 (n = 8), 0.0313 (n = 5); 7 of 8 gives 0.0352 (above 0.025) |
| Plain exact p | **not reported as a result**; it exists in the files for audit | no tier is derived |

Why no test and no tier: (i) with n = 5 even 5 of 5 gives 0.031 > 0.025 and with n = 8 only 8 of 8 passes 0.025, before any allowance for dependence; (ii) the PREREG confirmatory rule (fixed design effect, rho_s0 = 0.03) was simulated for n = 40 only (RES 4.4; PREREG 9.3 "the simulation covered n = 40 only") and its counts do not exist for n = 5 or 8; (iii) units are not independent: the 8 PL (or 5 NASA) training sets overlap in 6 of 7 (3 of 4) conditions, so the independence coverage above is an optimistic upper figure and is printed as such; (iv) adding nodes to the graph or the secondary family would change the Holm levels (0.005, ...) and the critical counts of the approved analysis (PREREG 9.4, 9.5, 9.11), which is a change to the closed design. **Alpha accounting row (to be added to 9.11 by the designer): "EXT-PL, EXT-NA: none; counts and ranges only".**

**Direction labels (selection of a Results sentence, not inference).** For each contrast: "A1c lower" iff positives >= 6 of 8 (PL) or >= 4 of 5 (NASA); "comparator lower" iff negatives >= 6 of 8 or >= 4 of 5; otherwise "mixed". Under a fair coin per unit these have probability 0.1445 each way for n = 8 (37/256) and 0.1875 each way for n = 5 (6/32), so "mixed" has probability 0.711 and 0.625 (arithmetic). The labels exist to remove discretion in wording, are printed with the null probabilities, carry no error control, and are never called significant or a tier. A fixed sentence template per label (section 1.13) is the only text permitted.

**Always printed, in the Appendix:** the full per-unit table (all 8 or 5 log ratios and condition scores, per arm, per k), the per-unit hull status, the number of forecast points per cell, and the interpolating-folds-only row.

### 1.8 Fade go/no-go and schedule go/no-go (the lead's request; computed only after the addendum card is frozen)

Order of events: the card (splits, stress coordinates, active inputs, QC rules, window rule, this go/no-go, templates) is committed and hashed; **then** `fade_gate.py` (written and committed before it is run) reads capacities once and writes `fade_gate.json`; then models. The script uses capacity values only, no model, and its verdict is a printed rule, not a choice.

- **Definitions.** F_c = 100 x (1 - retention at the cell's last quality-passed check-up) in pp; F_u = median of F_c over the unit's cells. A cell is *scheduled* if it has at least 3 post-window check-ups at k_full.
- **S-gate (schedule), per campaign:** go iff at least 75 % of included cells are scheduled (PREREG J§8-3 analogue, "fewer than 3 post-window check-ups for most cells").
- **F-gate (fade), per campaign:** go iff at least 75 % of the units have F_u >= 5 pp (PL: >= 6 of 8; NASA: >= 4 of 5). 5 pp is a design choice, ten times the 0.5 pp noise constant of the synthetic design (PREREG 13) and the order of the replicate spread, not a measured quantity.
- **No unit and no cell is dropped by the gate** (3.3(8)). A unit with small fade stays in and persistence will usually win there; that is reported.
- **No-go consequence:** the campaign is reported in one sentence plus its fade table (F_c per cell, which is not a model result), and no forecast table. The no-go cannot change any Samsung item.
- Expected, from the README stop rules only (not from data): NASA cells in G3 (10 days, 40 cycles) and part of G5 (B0049-52: 25 cycles, software crash) may fail the F-gate or the S-gate; whether NASA survives is unknown and is allowed to fail.

### 1.9 Controls and gates (experiment-designer step 3)

| Control | Setting | Rule | Role |
|---|---|---|---|
| NC-1 label invariance | every run on each campaign, same code path (`invariance.json`) | bit identity of predictions and of `tuning_done.json` between the real run and the run with scrambled held-out post-window labels (PREREG 10) | **gate for that campaign**: a difference voids the campaign's section; if the failing code is shared with the Samsung path the lead and the gate auditor treat it under stop rule 3 exactly as written, otherwise no Samsung item changes |
| PC-1 positive control | synthetic G0 generated on the *campaign's own design* (its conditions, check-up cadence, window, active inputs, cycling-only law) before any real fit | nRMSE of the recovered log-rate surface <= 0.15 for A1c, A2, A4c (PREREG 13) | gate for that campaign (void if failed); same circularity sentence |
| PC-3 analogue (reported, not a gate) | A1c against persistence R1 at k_full | counts as in 1.7 | printed; a failure is a Limitations sentence |
| NC-2 analogue (negative control; interpretive; PL only; optional by CPU) | A1c at k_full with stress vectors permuted among training units, separately for training and test (`permute_stress`) | L_u = ln(S_perm/S_real); counts only | "stress dependence needed" sentence in the Discussion only if >= 6 of 8 positive; otherwise "not shown necessary"; not on NASA (batch confound, n = 5) |
| Fade null | the F-gate itself | 1.8 | stops forecasting claims on non-aged data |

**Isolation from the approved table.** The approved gate G is defined by NC-1, PC-1, a test-fold read and an unmet freeze condition (PREREG 11, 4.1) on the Samsung design. The extra campaigns' controls void *their own section only*. No extra-campaign outcome enters the evaluation order of section 11 (gate G, P state, K state, M1, M2, qualifier sentences). This keeps D017/D019 untouched.

### 1.10 Outcomes stated in advance (experiment-designer step 4)

| Outcome | Numeric condition | Consequence |
|---|---|---|
| Positive direction | headline contrast labelled "A1c lower" | Results sentence form (a); Conclusions sentence unchanged; no change to title, abstract or state |
| Negative direction | headline contrast labelled "comparator lower" | sentence form (c) is printed with the same prominence; Limitations notes that the Samsung mechanism (storage cells, hull collocation) is absent; **no suppression, no re-tuning, no added arm** |
| Inconclusive | "mixed" | sentence form (b) |
| Campaign void | NC-1 or PC-1 failure | one sentence; the section is not reported |
| Campaign no-go | S-gate or F-gate fails, or fewer than 6 PL conditions complete | one sentence plus fade table |
| Stop rule | no interim look at held-out scores; each frozen configuration is scored once after all folds; a test-fold read by tuning or selection voids that campaign's run (stop rule 4 analogue); a rule changed after any held-out unit of that campaign is scored is not allowed (new version, disclosed) | as stated |

### 1.11 Run order by information per CPU-hour (step 5)

1. Minutes: identifiers, schedule counts, k_full, group/condition tables, splits and hash, hull flags, the A10c separability test, adding of the dataset specs by the new files. 2. Synthetic PC-1 on each design and NC-1 full pipeline on one fold per campaign. 3. `fade_gate.py` (capacity values, once). 4. Inner-CV tuning and final refits, PL first (higher value, higher probability of a go), then NASA. 5. NC-2 analogue (PL). 6. Sensitivity rows: retain-every-check-up and the designed-throughput row for "Data Missing" blocks (PL), cells with >= 3 forecast points, interpolating folds only.

### 1.12 CPU cost (arithmetic, not a measurement; CPU only, three single-thread processes)

Basis (PREREG 16, from V3/J16): one neural arm over 5 outer folds at full Samsung data, N = 20, costs about 1.2 CPU-h expected and 4.5 at the ceiling, with 3N + 5 = 65 fits per fold, i.e. 325 fits: **13.3 s expected, 49.8 s ceiling per full-data fit**; the m = 8 and m = 16 refits are about half of that (6.6 s, 24.9 s). I take the extra-campaign fit at **0.25 of the Samsung m = 8 expected cost (1.7 s)** and at **1.0 of the m = 8 ceiling (24.9 s)**; the extra campaigns have 14 or about 19 training cells and no storage cells, but step counts and collocation do not shrink with cell count, hence the generous factors. Fits per arm and fold with 2 inner folds: 2N + 5 = 45 (N = 20) or 85 (N = 40). Arm-units per campaign: A1c, A9, A4c = 3, A2 about 0.3, A11/A12 retrained per k about 0.5; total 3.8.

| | PL (8 folds) | NASA (5 folds) | both |
|---|---|---|---|
| N = 20, expected / ceiling (CPU-h) | 0.63 / 9.5 | 0.39 / 5.9 | 1.0 / 15.4 |
| N = 40, expected / ceiling (CPU-h) | 1.19 / 17.9 | 0.75 / 11.2 | 1.9 / 29.1 |

Add: NC-1 about +10 %; PC-1 on both designs about 0.4 CPU-h expected; the NC-2 analogue one arm-unit on PL (0.17 or 0.31 CPU-h expected); two PL sensitivity re-fits (2 x the PL main run). **Total: about 3 CPU-h expected at N = 20 and about 5 at N = 40, about 12 to 20 % of the Samsung core (25 expected); wall clock about 1 to 2 h on three single-thread processes.** The ceilings (about 35 to 70 CPU-h) are pessimistic bounds, not a plan. **Cut order if the Samsung timing run projects more than 8 CPU-h expected for the extras:** NC-2 analogue, sensitivity rows, A10c on NASA, NASA, then PL; they never displace the "never dropped" Samsung list (PREREG 12 rule 5). Human cost (estimate): about 2 days for the PL (`.mat` operation tables) and NASA (`.mat` nested structs) loaders, two `DatasetSpec` entries, the splits, the gate scripts and tests; parsing untrusted raw files with `python -I` in their own directory (CONTRACT section 1).

### 1.13 Where it is reported, and the wording for "previously analysed data"

**Placement.** No change to title, abstract, highlights, or any sentence of the closed table. Main text: one short subsection after the Samsung results, "Two further ageing campaigns (descriptive)", about 300-400 words, with a pointer. JES allows 8-10 display items and the plan has 10 (PREREG 14): the display slot is **Fig. 8** (G0 recovery, already marked "appendix if space is short"), which moves to the appendix, and becomes a per-unit dot plot of the log ratios for the headline contrasts on EXT-PL (8 dots) and EXT-NA (5 dots, labelled previously analysed). Full tables (arms x k, per-unit values, hull status, gates, fade table, "datasets considered" table) go to an appendix; a figure and table plan row for D-figures is needed. Conclusions carry exactly one sentence, built from the templates below, in whichever direction it falls.

**Methods text (data subsection), proposed:**
"Two further cycling campaigns were re-analysed with the same task as a descriptive check. The CALCE graphite/LiCoO2 pouch cells were cycled over eight combinations of state-of-charge window and discharge rate, two cells per combination [Saxena et al., ref]. The NASA Prognostics Center of Excellence 18650 cells of set 5 were cycled at three ambient temperatures and three discharge currents [Saha and Goebel, ref]. The NASA cells were analysed by the first author in an earlier study of battery state-of-health estimation [ref]; their identifiers and capacity values had therefore been seen before this analysis was specified, and we treat them as previously analysed data. The CALCE pouch cells were not analysed by the authors before; their data are public and have been used by others [Saxena et al., ref]. We use no other cell from the NASA or CALCE repositories. The plan for these two campaigns (inclusion rules, stress coordinates, splits, window rule, quality rules, a check that the cells aged enough to make a forecast informative, and the reporting templates) was fixed and hashed [hash] after the plan for the Samsung cells was frozen and before any model was fitted to these data. Each campaign is analysed on its own: models are fitted on its training conditions and scored on its held-out conditions, no model is transferred between campaigns, and errors are not compared across campaigns. No test, tier or claim of the main analysis depends on them."

**Results caption / table note:** "Descriptive; no test. CALCE pouch cells: not previously analysed by the authors (n = 8 held-out conditions). NASA cells: previously analysed data (n = 5 held-out temperature-current groups; temperature is confounded with test batch). Positives = held-out units in which [A] had the lower error; the range is the exact range of the unit-level log ratios, whose coverage of the median is 1 - 2^(1-n) only if units were independent, which they are not."

**Result sentence templates (selection by the direction label of 1.7):** (a) "On [campaign] (n = [n] held-out [conditions/groups]), [A1c] had a lower condition error than [B] in [k] of [n] units (median ratio [r], range [lo, hi]; descriptive)." (b) "... lower in [k] of [n] and higher in [j] of [n] units (median ratio [r], range [lo, hi]; descriptive)." (c) "On [campaign] ..., [B] had a lower condition error than [A1c] in [k] of [n] units ...". The Conclusions sentence: "On two further campaigns the same comparison was repeated without a test: [sentence a/b/c for CALCE pouch], and [sentence for NASA]." If a campaign is void or no-go, its half is replaced by "was not analysed ([reason])".

**Limitations text:** "The NASA cells had been analysed by the first author before; although every rule for them was written from schedule counts and identifiers and hashed before any model was fitted, remembered results cannot be excluded as an influence on the choice of the task. In both campaigns the number of held-out units (8 and 5) is too small for a test, temperature and batch are confounded in the NASA set, the temperature of the CALCE pouch tests is not stated by the provider, the NASA capacity is measured at the cycling condition, and the storage cells and label-free collocation that the Samsung analysis uses are absent. The results do not bear on the main claims."

**Data availability:** "The NASA and CALCE data are available from the repositories cited; they carry no redistribution licence and are not republished with the code." (Feasibility 6.) References to Crossref-verified DOIs only (citation validator before use); the earlier study is cited by its Zenodo DOI if the lead confirms it may be cited, otherwise as "first author, unpublished".

### 1.14 Freeze order and what is touched

1. The Samsung `FROZEN` is written first (unchanged procedure). 2. The extra-campaign plan is a **separate addendum card** (name proposed: `runs/prereg/PREREG_v4_ADD_EXT.md`, ids EXT-PL, EXT-NA) with its own change log, signed by statistician and red-team, hashed into `runs/splits/`. It is not a new section of PREREG_v4, so PREREG v4 needs no edit and none of its signatures or checklist items (17.2) is reopened. 3. The extra code lives in **new files only** (loaders, extra specs registered without editing `specs.py`, gate scripts), committed after `FROZEN`; the gate auditor checks that the diff touches no pinned file and that a Samsung timing/smoke run is bit-identical before and after. (If the lead prefers that the dataset specs sit in `specs.py`, they must be in the commit that `FROZEN` pins, as inert code, which costs about two days of coder time before the freeze; not proposed because the Samsung parse deadline is 07 Nov 09:00.) 4. No extra-campaign result may change any Samsung plan item; any such change is a new version.

---

## 2. Why this, and why not each serious alternative

| # | Alternative | Why it loses |
|---|---|---|
| A | **Decline: Samsung only, with ISU/SNL as the planned fallback/replication.** | The supervising professor asked; reviewers of a battery paper in JES routinely ask for more than one campaign; the cost is about 3 CPU-h and 2 days. Loses unless the lead judges the professor's request optional. |
| B | **Full parity: NASA and CALCE enter the graph or the secondary family as confirmatory tests.** | n = 8 and 5 cannot pass any level of 0.025 below 8 of 8 and 5 of 5; the design-effect rule exists only for n = 40; adding nodes re-allocates Holm levels and critical counts (PREREG 9.4, 9.5) and so changes the closed design; NASA is previously analysed, so it can never be confirmatory. |
| C | **Pool Samsung, NASA and CALCE in one training set, or train on Samsung and test on NASA/CALCE.** | This *is* the retired cross-dataset topic; chemistry, format, charge protocol and capacity-check conditions differ; the claim "held-out cycling conditions of one cell type" would be broken. Excluded by CONTRACT section 1. |
| D | **Include CALCE CS2/CX2 (prismatic LiCoO2) as the "CALCE" dataset.** | Static types give two discharge rates (0.5C against 1C, 4 cells each; CX2 3C is one cell), no SOC window, no temperature; the cyclic law has nothing to be tested on; 13 of those cells were analysed in the retired paper (feasibility 3). A within-condition early-life forecast would be a leave-cell-out protocol, the retired theme. Recorded as "considered, not analysed". If the professor insists on a CS2 row, the only clean option is one descriptive within-condition row, flagged previously analysed; not recommended. |
| E | **NASA randomized usage (set 11) or HIRF (set 15).** | A "condition" is a load distribution, not a point in a stress space (set 11); HIRF is not ageing and is offline (feasibility 2). Not downloaded; not usable. |
| F | **NASA at the level of the 21 nominal tuples (leave-one-tuple-out).** | More units, but tuples in a group differ only by cut-off; training would hold near-replicates of the held-out tuple, so the score would measure replicate prediction and flatter every arm. Group-level holds out a genuinely different (T, current). |
| G | **NASA mixed-condition and square-wave cells kept, mapped to mean current.** | Their stress is not a point in the law's inputs; B0028's README and data disagree; mapping would be a post-hoc choice. Excluded by rule and listed. |
| H | **Leave-two-conditions-out on PL (28 pairs) to get more folds.** | Pairs are not independent (each condition occurs in 7 pairs) and training sides shrink to 6; it manufactures n, not information. |
| I | **A learning curve over m (number of training conditions) on PL/NASA.** | m of 2-6 gives too few points for a trend claim (feasibility 4(b)); P3 is not testable; inflates CPU. Left out; may be added by a new version if wanted. |
| J | **Put the sections in the abstract.** | Closed table (D017/D019); no tier word is possible; a prespecified symmetric Conclusions sentence is enough. If an abstract mention is demanded, the only compatible form is a single clause after the closed sentences, using the Conclusions template, whose direction is whatever it is. I recommend not doing it. |
| K | **Run the extras with their own tuned budgets, longer N, or extra arms where they underperform.** | That is the garden of forking paths; the same N and rules are what makes a direction informative. |

Why the chosen design is the best of these: it answers the request with the only requested data that can exercise the law's SOC-window, depth and rate terms (PL) plus the one that exercises temperature and current (NASA), at about 12-20 % of the Samsung core cost, without touching the approved claims, and without becoming a cross-dataset story.

## 3. Is this the best result possible, or is there room for improvement?

- The best *realistic* outcome is modest: an internally consistent descriptive subsection, and, if PL goes, a direction (a or c) on 8 units. It cannot become a confirmatory replication; the honest label is "does not contradict / is consistent with", only in the descriptive sense.
- **PL is the strongest asset** (not seen by the author; design varies SOC mid-point, depth and rate; check-ups at a fixed reference cycle, like Samsung). It is also the weakest on size: n = 8 and two folds are extrapolations.
- **NASA adds the name, little evidence.** It is the first item cut under any CPU pressure. A reasonable alternative for the lead to weigh: keep NASA only as the "datasets considered" row plus the fade table (zero CPU) if the professor accepts CALCE PL as the second dataset. I propose to run it if the F-gate and S-gate pass, because the professor named NASA.
- **Room for improvement:** (i) read Saxena et al. (temperature, check-up cadence, window control) before the card freezes, which could add a fourth active input or a temperature note; (ii) if a designed, temperature-controlled campaign with fixed reference check-ups were available it would be a better second set than NASA (ISU and SNL, already in PREREG 3.4, are not blind; the Oxford, SNU and TBSI folders in `data/raw` were not examined and are not proposed here); (iii) a pooled test across ISU, SNL, PL and NASA would be a meta-analysis of tiny n and is not proposed.
- Where this extension could lift the paper: showing that the same pipeline runs, unchanged, on a SOC-window design is the sort of robustness material a JES reviewer expects; it does not lift the title.

## 4. What are we lacking that a JES reviewer would hit?

1. **CALCE PL is not on disk.** One of 8 zips is almost complete (SOC_20-80_2C, 73.4 of 74.6 MB), one is at 40 of 67.5 MB, six have not started; only 2 of 16 cells have been parsed (feasibility 4, 6). Cycle counts, check-up counts and the characterisation capacity position are unverified. The 6-of-8 completeness rule exists for this.
2. **Provider facts unverified:** PL temperature, check-up cadence and rest handling (page digest only); NASA chemistry and format ("Li-ion", 2 Ah per README; 18650 LiCoO2 is secondary knowledge, not to be printed as a provider fact).
3. **Citations not yet verified:** Saxena et al. 2016 (J. Power Sources 327, 394-400), Saha and Goebel 2007 (repository entry), the earlier study. Each needs a Crossref-verified DOI and a page/table location via the citation validator before use; the paper was not read.
4. **Code that does not exist:** the two loaders, two dataset specs (input masks), the splits, `fade_gate.py`, the A10c separability test, PC-1 on the new designs. The pinned-file rule (below) must be respected.
5. **Selection of the datasets** is by the professor's request and by what could carry the law; a reviewer may ask "why these two"; the "datasets considered" table with reasons is the answer.
6. **No comparison with the PL authors' model or with published NASA numbers**; a reviewer may want one. Stated limitation; the tasks differ.
7. **No temperature/batch separation on NASA** and **no calendar term** (rest-heavy PL: calendar time is a large share of elapsed time; D\* may use t, A1c cannot; this favours D\*, conservative for A1c).
8. **SOC-window drift** (Coulomb-counted windows) means the stress coordinate is nominal.

## 5. What would make a reviewer reject it

- A tier word, "significant", "validated", "generalises" or "robust across datasets" attached to n = 8 or n = 5. Prevented by the vocabulary rule, the templates, and the absence of a test.
- Selective reporting: showing the extra campaigns only where A1c wins. Prevented by the fixed Conclusions sentence in every direction, the per-unit tables and the "campaign void / no-go" sentence.
- Hidden analyst freedom on NASA (labels seen before). Prevented by hashing every rule before fitting, by deriving the rules from schedule counts, and by the previously-analysed label; not removable, so disclosed.
- Reading the section as a cross-dataset study (the retired topic), or as an evaluation-protocol comparison: prevented by section 1.3.
- Changing a gated item after the fact: prevented by isolation (1.9) and by the freeze order (1.14).
- Different treatment of A1c and the comparators on these sets (e.g. a longer budget for A1c): prevented by identical budget rules, equal trials, the same ensemble rule and `n_train_used` reporting.
- Mixing in the Samsung-only mechanism claims (K chain, storage): not run, not mentioned as supported.

## 6. Edits other documents would need (none are made here)

- PREREG 3.4 (ii) "optional descriptive replication" should name EXT-PL and EXT-NA as taking that slot ahead of ISU/SNL replication (ISU stays the D005 fallback); PREREG 9.11 gets the row "EXT-PL, EXT-NA: none"; PREREG 12 rule 5 (cut order) gets the extras first; PREREG 14 and `debates/D-figures.md`: Fig. 8 slot and appendix tables; PREREG 15 gets the extras after step 5.
- `research/DECISIONS.md`: a D022 row after the judge; a `hypotheses` row for EXT-PL/EXT-NA when the designer files the card.
- `notes/data/`: a short note recording the CS2/CX2, set 11 and 15 "considered, not analysed" reasons for the datasets-considered table.

## 7. Questions for the lead (cheap to answer, affect the plan)

1. May the earlier study be cited by its Zenodo record (10.5281/zenodo.22754072 per the project notes), or is it "first author, unpublished"? 2. Run NASA at all, or give it only the datasets-considered row and the fade table? (Proposed: run it, cut first.) 3. Is the Fig. 8 swap acceptable, or should the extras be appendix only? 4. Does the professor mean CALCE CS2 specifically by "CALCE"? If so a one-line explanation of why PL replaces it (section 2, D) should go to the professor before the freeze.

## 8. Opponent's attack and judge's verdict

*(left empty: to be written by separate agents, CONTRACT section 3 items 6 and 7.)*
