# Gate audit: pilots P0-P5 complete and preregistration draft fit to be frozen once its open items close

Date: 2026-11-05. Auditor: gate-auditor (check only; nothing was fixed, `progress.md` not ticked by me).
Basis: CONTRACT.md; `debates/D010_topic/04_judge.md` (sections 1-8); DECISIONS D005-D007; every file named below, opened on disk.
Reading depth: RESULT.md of P0-P5 and samsung_pipeline full; PREREG_DRAFT.md full; `p3_headroom.py` main() and `p3_make_splits.py`
full, `make_samsung_splits.py` header and ID logic, P4/P5 and P2 config/summary/draw files by key; the rest of the code by grep.
Recomputation: `.venv/Scripts/python.exe -P`, CPU only, a few seconds each. Scratch only in the session scratchpad; no repo file touched.

## Overall verdict: PASS WITH CONDITIONS

No criterion is wholly `missing`, so the gate does not fail, but 9 conditions (C1-C9 below) must be closed, and the filled
prereg re-checked, before the freeze. The gate does not certify the freeze itself. I cannot waive anything; only the user can,
in the decision ledger.

| # | Check | Verdict |
|---|---|---|
| 1 | Numbers in RESULT.md reproducible from run files | PASS WITH CONDITIONS |
| 2 | Go/no-go verdicts follow the judge's rule as written | PASS WITH CONDITIONS |
| 3 | No test fold read or scored before preregistration | PASS WITH CONDITIONS (disclosure) |
| 4 | Splits are the ones the code used, committed before modelling | PASS |
| 5 | Seeds, configs, commits recorded | PASS WITH CONDITIONS |
| 6 | Data issues handled or carried as open items | PASS WITH CONDITIONS |
| 7 | Prereg consistent with judge and D007; lists every open item | PASS WITH CONDITIONS |

---

## 1. Number audit

Recomputed from run-directory files:

- **P2** (summary.json vs table): all 16 rows match (38.4 / 38.3 / 18.5 / 11.4 / 42.0 for hard ODE; 18.9 / 15.6 / 13.3 / 50.6 / 219.4 / 102.0
  for the PINN; peak RAM 691-710 and 735, 840 MB). config.json lists seeds [0,1,2] and both commits.
- **P3** (results.json and condition_level.csv): ISU W4 ratio 0.897 (folds 0.85/0.82/0.84/0.93/1.04), floor median 5.753 (range 5.10-6.09),
  48-50 multi-replicate conditions; SNL W100 1.128 (folds 1.04/1.29/1.34/0.96/1.01), floor 2.620 (2.39-2.76), 15-17 conditions; W6 0.792; W200 0.925;
  pooled-condition ratios (0.901, 0.782, 1.108, 0.922) recomputed from condition_level.csv; 7 and 13 excluded ISU cells; CPU seconds 2,369 / 1,795 / 201 / 215;
  best learner per fold (LightGBM 3 of 5 on ISU W4, 5 of 5 on SNL). All reproduce. D007's numbers (0.90, CI [0.78, 1.08]; 1.13) match.
- **P4** (summary.json): 4 of 5 KAN < GAM, 5 of 5 KAN < free G, medians 0.081 / 0.103 / 0.141, ratios 0.81 / 0.61 / 0.76, free G passes 3 of 5. Match.
- **P5** (summary.json, draw_0.json): 4 of 5 (record-end), 5 of 5 (whole axis), medians 4.72 vs 5.37 (0.96), 4.65 (0.84); chosen lambda_res lists; hard inner-CV 5.83 in draw 0. Match.
- **P1**: 63 groups, 5,455 rows, 251 cells, 2-80 points, 96,492 SNL rows, 389-4,569 cycles, 90 invalid rows (one cell, cycles 2622-2711), 4,639 missing
  temperatures, median cycle-1 ratio 1.003 (0.994-1.060), no duplicate pairs (1,830 tested), 0 Table A1 mismatches (three groups spot-checked against the README text). Match.
- **samsung_pipeline**: 163 CU rows, 19 cells, 18 cycling with at least 3 points; cadence median 29 d, quartiles 17/45.5, range 7-78, first check-up 7-77 d (median 26);
  per-CU medians (11.5, 27, 16.5, 55, 40, 69, 30 d); capacities recomputed independently from raw CSV by trapezoid on steps 21/22:
  TP_z18_01 CU03 4.8247/4.8284 Ah, CU09 4.7295/4.7373, TP_z01_01 CU03 4.811/4.8428 equal the table to 4 decimals; retention 0.9807 at CU09. 19 unit tests pass.
- **Metadata counts** (experiments_meta.csv, recounted): 279 = 132 storage in 19 conditions + 147 cycling in 40; cycling cells at 23/35/45 C = 33/39/75
  (10/13/17 conditions); 35 conditions with 3 cells and five (not four) centre points with 6, 6, 9, 9, 12; lab confound exactly as stated in prereg 3.3(7)
  (35 C all INT; 45 C 66 HM + 9 SIE; storage 10 C all SIE, storage 45 C all HM).
- **Prereg compute table** (section 16): reproduced arithmetically from P2 timings (11.8 / 44.9 CPU-h for Test B, 11 h and 35 h wall clock).

Not reproduced:

- **N1 (P0).** RESULT says TP_z10_03 has 7 CU + 2 exCU and TP_z18_01 has 11 CU + 5 exCU. The listings in the same directory give
  6 CU + 2 exCU and 10 CU + 5 exCU (TP_k03_01: 4 CU + 3 exCU agrees). The prereg section 5 repeats "9 and 16 intermediate check-ups"
  (should be 8 and 15 by the listings). The pipeline RESULT independently reports "8, 10 or 11 CU per cell".
- **N2 (P0).** The all-cell CU size "roughly 0.5 GB, above 400 MB" has no calculation on disk. From the four listings I get about 0.37 GB for CU only
  (cycling about 2.1-2.5 MB per cell x 147, storage about 0.5 MB x 66), 0.4-0.57 GB if every cycling cell has 8-11 CU at 0.35 MB. The estimate is
  borderline, not demonstrated either way, and excludes exCU/ET.
- **N3 (P1).** "30 of 61 cells fall below 80 % of first-cycle capacity": I get 35 (36 if the 90 invalid rows are kept). Descriptive only; no verdict depends on it.
- **N4 (pipeline).** "Stage 2 median first check-up 62.5 d" sits under the cycling bullet; for cycling cells alone it is 76 d (62.5 includes the one storage cell).
  Stage-1 median 22 d is right.
- **N5 (P3).** "ISU W6 0.79 [0.68, 0.98]" and "SNL W200 0.93 [0.65, 1.35]" pair the fold-mean ratio with the CI of the pooled-condition ratio
  (0.78 [0.67, 0.97], 0.92 [0.64, 1.35]). The table header says which is which; the second ratio is not shown. Cosmetic.
- **N6 (prereg 16).** "GP-ARD 526-539 s per outer fold" is the maximum of three folds; the five ISU W4 folds took 339-539 s. Harmless (upper end).

## 2. Verdicts against the judge's rules

- **P0: PASS WITH CONDITIONS.** The judge's Go needs (time, cumulative Ah or cycle count, check-up capacity) in one member and an all-cell total below 400 MB.
  P0 found capacity in the CU member but no cumulative Ah (throughput is in ZYK), and put the total at about 0.5 GB (N2). So the rule's letter gives
  neither Go nor No-go; the RESULT calls the schema GO and starts the fetch anyway, and says so openly. Outcome-equivalent, but the departure is not in the decision ledger.
- **P1: PASS.** Both Go conditions met (0 mismatches; per-cycle capacity, time, throughput; no duplicates, so nothing to drop; the 90 invalid rows are excluded in code,
  `p3_headroom.py` line 48).
- **P2: PASS as a verdict, with a deviation downstream.** Hard ODE 38.4 s > 30 s, PINN 18.9 s < 90 s: "Partial" is the rule's reading for the specified setting. The judge's
  Partial action is trials 20 -> 10 and inner folds 3 -> 2. The lead's note (progress.md 23:05) rules the hard-ODE arm GO "for Samsung" on node count, and prereg 7 keeps 20 x 3 for all arms
  (N = 40 if the fit is under 20 s). Rationale is written down, but there is no DECISIONS row; it is an unlogged override of a judge rule. The Samsung timing is still an inference
  (nodes per cell), not a measurement.
- **P3: PASS.** Ratio 0.90 (ISU W4) and 1.13 (SNL W100), both <= 1.2, hence non-inferiority for contrast (iii): exactly the rule. D007 applies it correctly and says Samsung
  is decided separately. Caveats the RESULT states honestly: SNL folds 1 and 2 are above 1.2 and the CI straddles 1.2; selection of the best trial on the same inner folds is optimistic
  (the repartition check moves the ratio by -0.01 to +0.06); the floor is not a lower bound.
- **P4: PASS.** 4 of 5 and 5 of 5 against the >= 4 / >= 4 rule. The RESULT correctly adds that the margin is small, the GAM floor (0.05-0.07) sits under the 0.15 pass line,
  and the structured-vs-free claim holds only on the absolute metric for the KAN.
- **P5: PASS.** 4 of 5 (>= 3 needed) on the judge-spec collocation. Post hoc lambda = 10 run is labelled and not used for selection; draw 1 reverses.
  Attribution caveat (no lambda = 0 arm in P5) is stated and handled in the prereg (A9).

## 3. Test-fold guard

- **P3:** `main()` drops each outer fold's test cells from the frame before `build_cells`, `replicate_floor` and `tune`; per-fold asserts; split hash re-checked after the loop.
  The cross-fold assert in the first version would have fired spuriously; the final per-fold check is correct. Verified in code; `audit.intersection_within_fold = 0`,
  `test_fold_scored = false` in all four results.json. I found no code path that scores a test fold.
- **P4/P5:** synthetic; the ISU design is read with `usecols=["cell","group","week"]` (`p45_common.py` line 60), so no capacity value is read. Hyperparameters chosen by inner CV on the
  training conditions. Post hoc sensitivity (lambda = 10, whole-axis collocation) was looked at on the synthetic held-out conditions and is declared.
- **P2:** ran on all 61 SNL cells, before the splits existed, as a timing run (finite-loss check only). No scoring.
- **Samsung:** the splits draft is built from `experiments_meta.csv` only (no capacity column) with seeds that are dates. The parser (`samsung_checkups.py`) has however read capacities of
  163 check-ups of 18 cycling cells, all of which sit in some draft Test B fold, and applies capacity-dependent QC (range 2.0-5.2 Ah, charge/discharge mismatch > 3 %, isolated-outlier 1 %). No
  flag fired. Nothing under `runs/` exposes retention values (cadence and counts only). Nothing was scored.
- **Earlier exposure of ISU/SNL:** the proposer's scratch pilot (`debates/D010_topic/pilot_scratch/output.txt`) analysed all ISU cells before the splits (t80, replicate scatter, per-cell power-law errors at
  W = 2, 4, 6, which is also where W = 4 and 6 came from). These are descriptive numbers, not model scoring, but ISU is not blind for later confirmatory use.

## 4. Splits

- `runs/splits/*.json` were added in one commit, 16a9da4 (2026-11-04 23:14:03 +0545), and never modified since. `p3_headroom.py` first appears at 23:21 (175327f); the
  earliest P3 result file is 23:28 (SNL W100).
- Run configs record `split_sha256` = SHA-256 of the file: ISU c1227642a067..., SNL d5018c6bf008...; both equal the current files.
- I regenerated all four split files in a scratch directory with `p3_make_splits.py` (reads only identifier columns): all four `sha256_of_folds` equal the committed ones (763eb6daed96, f9dba72d6373, 3811be897663, a678191e5341).
- Samsung draft: regenerated bit-identical with `make_samsung_splits.py`; fold counts (2/3/3 ... , 33/27/30/27/30 cells), Test C 13 conditions / 39 cells, Test A 49 cells per fold, S2 sizes and the four hash prefixes
  (9979767d1d27, dc53ce82e460, e1fbcd315fce, 35f3fbbb9e47) equal prereg section 4. They are draft (copied to `runs/splits/` only at freeze); committed in 99d0da4 before any Samsung model exists.

## 5. Seeds, configs, commits

- P1: config.json + commit.txt (78d1731). P2: config.json with seeds and two commits. P4/P5: config.json with commit 992b5b4, empty dirty-file list, seed scheme. P3: config.json per run with seed and split hash.
- **Gaps:** (a) P0 has no config.json, commit or run record, only RESULT.md and listings (commands are in the text). (b) P3 `commit` fields do not identify the executed code: SNL runs record 992b5b4, ISU W6 86fca6f, ISU W4 61bb730; the RESULT
  says "config.json records 61bb730". `p3_headroom.py` carried an uncommitted edit when the SNL runs started (the edit, 7 lines, only changes the audit fields: `git diff 175327f 61bb730`), so numbers are unaffected, but the provenance
  statement is wrong. No dirty-file field in P3. (c) samsung_pipeline `config.json` records 86fca6f but the code changed in 9907449 (the commit that carries the RESULT); outputs are explicitly a snapshot of a running download, so they cannot be rebuilt
  from a fixed raw state. (d) CONTRACT 6 asks for `metrics.json` and per-cell predictions per run; pilots use `summary.json` / per-cell RMSE. Acceptable for pilots, but write it into the prereg's run-record spec.

## 6. Data issues

| Issue | Where handled | State |
|---|---|---|
| Samsung two-stage naming (138 of 141 names twice) | pipeline `cell_id = serial_s<stage>`, fetcher keys by file id (`<serial>__f<id>`), prereg 3.2 | handled; two remaining problems below |
| Stage assignment | pipeline: internal serial, then lab, then date; 17 + 1 + 1 + 1 unassignable | **prereg 3.2 states a different rule** (dates from `_meta.txt`, cross-check m_0/U_0, exclude disagreements) and calls the fetcher fix OPEN-1, which is already done |
| Two folders whose meta serial contradicts the design table (TP_z10_01, TP_z15_01) and one empty folder (TP_z02_01 f47631268) | pipeline RESULT item 3, issues.csv | carried in the RESULT only; **not in prereg 17** |
| P0 labels wrong (TP_k03_01 is stage 2, 23 C, not 10 C) | pipeline RESULT item 2 | P0 RESULT.md not annotated; D006 evidence still cites it |
| Lab-temperature confound | prereg 3.3(7), E3, Fig. 2, sensitivity row | handled; verified against metadata |
| Storage cells 04-06 without intermediate check-ups | prereg 3.3(5), S2 rule, D006 | handled |
| SNL invalid rows | P1, P3 loader (> 0.05 Ah), prereg 3.4 | handled |
| Non-isothermal CU (cell surface 28-33 C in a 23 C chamber, lab-dependent) | pipeline item 7 only | not in prereg; relevant to E3 |
| exCU/ET/AT not downloaded; retention anchored on the first CU; analytic EFC not validated against ZYK | pipeline "Not done"; prereg 3.3(2), 5, 17(b) | carried (covered) |
| Outcome-dependent forecast truncation in ISU/SNL (forecast up to first point below 70 %; 7 and 13 ISU cells with no forecast point excluded in P3) | P3 RESULT "pilot choices" | not in prereg 3.4; Judge Opp 3.5 asks for a preregistered forecast-failure row (prereg 3.3(6) does this for Samsung only) |

## 7. Prereg consistency

Consistent with the judge: claim and contrasts (J1), Holm 3, Wilcoxon + 10,000 cluster bootstrap, margin = median leave-one-replicate-out floor (computed on training conditions), Test B/C/S2 layout, 5 seeds,
inner grouped CV, outcome A/B/C and tie plan (rows 1-8 of section 11), titles, fallback date, synthetic thresholds (0.15 / 0.30 / 0.67 / 10 %), and the retired-topic guard (no coverage or ratio B/C). Departures from the
judge are mostly flagged (OPEN-2, OPEN-3, OPEN-4, OPEN-6, the G2 strengthening).

Gaps and inconsistencies:

- Section 11 "P3 slot [a]" and section 17(a) still read "pending"; the header says P3 outputs were not used. P3 finished and D007 fixes non-inferiority for (iii) on ISU and SNL. Section 3.4's fallback ("same three
  contrasts") does not say that (iii) is non-inferiority on ISU in the fallback; Samsung stays open until its own P3.
- Non-inferiority margin = replicate floor (the judge's rule, kept for H1c in 9.4/9.5). On ISU the floor (5.75 pp) exceeds the best learner's own error (5.13 pp), and on SNL (2.62 pp) it is about the learner's error (2.97 pp).
  A margin of this size lets a model about twice as bad pass non-inferiority. 9.5 handles the superiority margin only. Needs a statistician ruling before freeze; not in the open list.
- Section 11 has no row for H1c "neither superior, nor non-inferior, nor significantly worse" (unresolved).
- Arm count: judge cut to 9 arms for compute (Opp 5.3/7.1); prereg has 14 arms + R1, R2. Only A7 is flagged. The judge's third arm already is the PiDDM-style MLP-of-s stress map, so "the judge's list had no MLP stress map" (section 7)
  is not accurate; A7 may duplicate it. Compute table still gives 11-35 h wall clock.
- Samsung capacity-dependent QC rules (pipeline thresholds) are not in prereg 3.3, which says no inclusion rule depends on capacity.
- OPEN-1 is stale (fetcher is stage-aware); the stage-rule mismatch above is new.
- `progress.md` (00:25) says Codex turn 3 proposes different primary contrasts (Stroebl comparator primary, data-only as non-inferiority); OPEN-5 covers it. If adopted, the prereg is a new version and the hypothesis table changes.
- Not audited here: bibliographic facts (Stroebl JES 142, 119552; Zhang JES 182, 125097; KA-CRNN JES 158, 121853; PiDDM arXiv ID). They are for the citation validator.

---

## Conditions (all must close before the freeze; none can be waived by me)

- **C1** Fill the P3 slot (ISU W4: 0.90, SNL W100: 1.13 -> non-inferiority for H1c on both, citing `runs/pilot_P3/*`, D007), update the header ("P3 used") and the 3.4 fallback wording; leave Samsung open until a Samsung P3.
- **C2** Statistician ruling on the non-inferiority margin (floor >= learner error on ISU/SNL), and on the unresolved-H1c row; record it.
- **C3** Decision-ledger rows for: P0 departure from the 400 MB / cumulative-Ah wording; the lead's hard-ODE "GO for Samsung" and the 20 x 3 budget against the judge's P2 Partial action; arm list vs the judge's 9 arms (A7, A13, A14, R1, R2).
- **C4** Correct the numbers in P0 RESULT / prereg section 5 (CU/exCU counts 6+2 and 10+5; "8 and 15"), add the calculation behind the 0.5 GB estimate or drop it, annotate the P0 stage/temperature labels; fix N3-N5 in P1, pipeline, P3.
- **C5** Prereg 3.2: one stage-assignment rule that matches the pipeline (or change the pipeline), close OPEN-1, add the two serial conflicts, the empty folder and unassignable cells as open items with a rule (exclude and list).
- **C6** Prereg 3.3: add the capacity-dependent QC rules and thresholds as pre-specified inclusion rules; add the non-isothermal CU note to E3; add the ISU/SNL forecast-failure and 70 % truncation rule to 3.4.
- **C7** Provenance: add a dirty-file field and fix the commit statement for P3 (SNL 992b5b4, W6 86fca6f, code unchanged apart from audit lines); write a P0 run record; for samsung_pipeline state the raw-file snapshot (file list + sizes) and re-run after the download completes. At freeze record code commit, split hashes (move the Samsung draft to `runs/splits/`).
- **C8** Disclosure sentence in the prereg: capacities of 18 cycling cells (163 check-ups) were parsed and QC-checked before the freeze without scoring; ISU and SNL were explored in the proposer's scratch pilot before the splits; ISU/SNL results are therefore labelled "not blind" and are secondary.
- **C9** After C1-C8 and the existing open items (OPEN-2..6, [a], [b], [c], A10 equations, Zhang JES 182) are closed, a second audit of the filled version before the freeze (as prereg 18 already requires of the pilot numbers).

What would turn this into FAIL: a test-fold read found in a path I did not run (the Samsung pipeline's later versions, the P3 `load_*` functions were read only by grep for the filtering order), or a post-freeze change to margin or comparator rules after seeing an outcome.
