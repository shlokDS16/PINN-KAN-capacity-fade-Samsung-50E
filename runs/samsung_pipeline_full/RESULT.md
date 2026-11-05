# Samsung 50E full release: pipeline re-pointing, FB-3/4/5/6 evidence, Test B cell table (2026-11-05)

Role: data steward. Blinding: no capacity value, curve or capacity statistic was printed, logged or written to a committed file by this work.
All comparisons are by hash or equality; every number below is a count, an identifier, a schedule, a file check or a pass/fail flag.
The throughput columns of the ZYK files (Ah, EFC) stay in the git-ignored `data/processed/samsung_zyk_efc.csv`; the committed per-file table keeps
presence and parse flags only. No new exposure to add to `runs/prereg/BLINDING_LOG.md`.

Code: `code/data/samsung_checkups.py` (re-pointed; `configure`, `--raw/--lists/--out-dir/--run-dir/--cu-only`), `code/data/samsung_extract.py` (new),
`code/data/samsung_full_audit.py` (new), `code/tests/test_samsung_full_release.py` (new, 8 tests). Numbers: `fb_status.json` (this folder).

## D024 update (C1 to C5 of `debates/D024_data_rules/01_judge.md`, same day, later): supersedes sections 4 (incident files), 6 and 7 (lab-map caution) and concern 1 to 5

Same blinding rule: counts, identifiers, throughput (current-derived) and flags only; the check-up table was read with `usecols` that exclude every capacity column wherever it was only needed for throughput.
Code: `pinnkan/zyk.py` (rule, variants, validation), `pinnkan/data.py` (incidents, reference), `pinnkan/labmap.py` (new), `metrics.py`, `stats_ext.py`, `prereg/extraction_calibration.py` (read the map),
`data/samsung_checkups.py` (`meta_serial_conflict`), `data/samsung_full_audit.py`. Tests: `test_labmap.py` (6, new), `test_samsung_full_release.py` (15), `test_pk_build2_data.py` (extended), full suite (`code/tests`): 605 passed in 7 min 6 s after all D024 changes.

| action | result |
|---|---|
| C1 ZYK rule | constants `ACTIVE_I_A 0.05`, `GAP_FLAG_S 600`, `REST_GAP_MAX_S 86400`, `MIN_ROWS 10`, DoD edges (0.15, 0.35); `TABLE_COLS` gained `dt_max_active_s` and `i_dch_med_a`. Table rebuilt from the zips: 1899 rows (1893 read + 6 `missing_file`), sha256 `dfc379a6544f0fc5e6465be95e9f005f823f68ecba31d89ccad10270ce64295d` (git-ignored). **Incomplete read files 18 = 15 active gap + 2 non-monotonic time + 1 with fewer than 10 rows; rest-only gaps above 24 h: 0; 22 cells with an incomplete file; 125 of 147 cycling cells fully logged**; fully logged by DoD class (low/mid/high): HM 15/9/38, INT 25/13/13, SIE 3/6/3 (all as the judge predicted). All 10 documented data-loss files are incomplete (TP_z19_01_s1 file 4; TP_z21_01_s1, TP_z24_01_s1, TP_z25_02_s1 file 22; the 6 `missing_file` files TP_z01_01..03_s2, TP_z03_01..03_s2 file 24). The 6 documented incident metas take the designed (analytic) throughput for their interval (existing `attach_zyk_cumulative` fallback); their cells stay in |
| C2 incidents and reference | `INCIDENT_FILE_DROPS` is stage-aware and stage 1 only (5 files: TP_z01_03_s1 file 11 CU, TP_z17_03_s1 files 13 exCU and 17 CU, TP_z17_02_s1 file 19 exCU, TP_k11_02_s1 file 3 exCU); the ET entry is deleted (TP_z25_01_01_ET_T45 and TP_z12_*_31_AT_T45 are documented no-ops, `INCIDENT_NOOP_FILES`). Consecutive drops with the same scope: stage 1 for TP_z24_01 (after 2), TP_z25_01 (after 4), TP_z20_03 (after 16), TP_z17_03 (after 18); stage 2 for TP_z07_03 (after 16). The loader decides the reference once, on row existence before any incident or QC step, records it in `meta`, and raises if an ET row of an ET-anchored table is later removed. **On the real table: `n_incident_rows_dropped_dataset == 5` (was the over-drop of 10) and `reference == "ET"` for 279 of 279 cells (213 of 213 analysed)**, also on the `throughput="zyk"` path; 49 rows removed by the consecutive rule |
| C3 lab map | `runs/prereg/lab_map.json` (sha256 of the file `bf8e75b246a413b28d4f86860cd9a73742d86936630426f755bf0c73bc72476f`, conditions hash `629358d675771bc076180c158b626aee15ff6a2247cadf2e2bc81d702d03f687`, unchanged): rule most cells, exact tie to the laboratory with more cycling cells in the design (HM 69, INT 60, SIE 18), then alphabetical. HM 17 / INT 19 / SIE 4; the only exact tie (T23\|SOCmax0.8\|DoD0.25\|Cch0.2\|Cdch1.4, HM 3 / INT 3) is HM; mixed conditions listed in the file. `majority_labs` (required file), `train_condition_meta` and `condition_strata` read it; conditions not in the map (ISU, SNL, synthetic) keep the local majority. The audit checks the file against a rebuild from the cell table (equal). Test: a changed cell count does not change the map |
| C4 FB-5 validation | `python -P -m pinnkan.zyk --validate --variants --out-json runs/samsung_pipeline_full/fb5_validation.json` (sha256 of the file `d3d45fb5abbee5f86c716f2a19f4a22c00f9ecd84957571a32fe77893827630c`; ZYK table hash recorded inside). **Ruled rule: analytic throughput is not accepted.** 134 cells with fully logged intervals, 1472 pairs (3 pairs of 3 cells dropped because the analytic throughput is undefined), coverage condition met in every DoD class and laboratory; median absolute relative difference 20.3 % against 5 %; 86 of 134 cells above 10 % at their last check-up (worst 10.3, i.e. 1030 %). Information variants: active gap above 60 s: 116 cells, median 21.7 %, 84 cells over; any gap above 600 s (the old rule): 12 cells, median 24.2 %, 12 over. The prereg branch follows: ZYK-logged throughput for every cycling cell, with the designed throughput for the intervals of the 22 cells that have an incomplete file. (A probable cause, not tested here: the analytic estimate assumes CC-only cycling with zero rest, while the protocol has rests of 3 to 12 h) |
| C4 identity check | median logged discharge current of the complete ZYK files of each cycling cell against C_dch x 4.9 A of the zip-name condition: 147 of 147 cells computed, **0 cells deviate by more than 10 %** (largest deviation 0.02 %); no cell excluded under 3.2 (`identity_check.csv`). The sentence "Disagreements: none" can stand |
| C5 ET incident cells | TP_k08_01 to TP_k11_01 (stage 1) ET_T23 files each hold exactly one step-21 run followed by one step-22 run (`et_incident_structure.csv`), so the ET capacity comes from the repeated cycle only; rule fixed: last complete charge-discharge pair (no change of code needed for these files) |
| C5 outlier flags by kind | `capacity_outlier_vs_neighbours` rows: CU 4, exCU 1, ET 0, AT 0 (5 in all, as before); first CU after ET: 213 rows, 0 flagged (ET anchor creates no rise flag at the first window point) |
| C5 `meta_serial_conflict` | new boolean column in `samsung_cells.csv`: 49 cells (stage 1: 45, stage 2: 4), all INT. New `samsung_cells.csv` sha256 `2a10647833c54127b48a4d68bea037b354e054e0224a33f3106bfd736d20adab`; `samsung_checkups.csv` unchanged (`6fa9b85e...47c4f`) |

FB status after D024 (evidence above): **FB-3** met (Q0 = ET_T23, 279 of 279 at loader level). **FB-4** closes: stage assignment 0 conflicts, stage-aware incident drops implemented and tested, lab map frozen, identity check passed.
**FB-5**: files present and parseable (147/147 cells, 1893/1893 files), rule fixed, validation run once with the ruled definition: analytic throughput rejected, ZYK-logged throughput applies to every cycling cell. **FB-6** unchanged (k_cyc 4, k_sto 2).

## 1. Data on disk and pipeline inputs

| item | value |
|---|---|
| zips in `data/raw/samsung50e_full` | 279 cell zips + `experiments_meta__f47627029.csv` (byte-identical to `data/raw/samsung50e_meta/experiments_meta.csv`) |
| zip integrity | `zipfile.testzip` (CRC of every member) clean for all 279; no unsafe or unexpected member name (0 of 11 532 members) |
| names | 141 serial names; 138 occur twice (two stages), 3 once; folder key = zip stem `<serial>__f<figshare id>` |
| members by kind | CU 1532 csv / 1531 meta; exCU 682 csv / 683 meta; ET 837 csv + meta; AT 819 csv + meta; ZYK 1893 csv / 1899 meta |
| extracted (own directory `data/raw/samsung50e_full_x`, git-ignored) | every `*_meta.txt` and the csv the pipeline reads (CU, exCU, ET_T23, AT_T23): 8535 files, 40.05 GB, sha256 of each in `extract_manifest.csv` (sha256 of the manifest `88ea00c41cc0f988b8851debc06248276e10b5d8be04f1dcd2b3dc41fac72ead`), 0 problems |
| left in the zips | ET/AT at 10 and 45 C, all ZYK csv (streamed by the audit, not extracted) |
| disk | extraction wrote 40.05 GB; free space now 104 GB (141 GB before). The step was an extraction of already-downloaded data, not a download; it is reported because it exceeds 5 GB |
| member lists | `member_lists/<folder>.txt` for all 279 zips (name, size, crc32); for the 148 folders that had a list in `runs/pilot_P0/member_lists` the names are identical |

Pipeline run (`code_version 2026-11-05.7`, full file set): 2766 capacity rows = CU 1532, exCU 682, ET_T23 279, AT_T23 273; 279 of 279 cells have rows, 279 have a
member list, 279 have all expected CU files (`complete`), 0 cells with a CU meta but no csv. Analysis of 2766 files took 377 s on 3 CPU processes.

## 2. Regression (task 1)

Cell key `<serial>_s<stage>` and the stage-aware folder key were already in the pipeline; the change is only the input path and an explicit file-set switch.
Rows are compared as raw text lines of `samsung_checkups.csv` (sha256 of the lines of each cell; hashes pinned in `baseline_row_hashes.csv`).

| check | result |
|---|---|
| refactored code on the per-member inputs (`data/raw/samsung50e_members`, pilot lists) vs the output written 2026-11-05 03:17 (76 cells, 539 rows) | byte-identical for 75 of 76 cells. The 76th, TP_z08_03_s1 (2 rows), differs in 4 date-derived columns only: its entry-test meta files were fetched after that output, so `first_test_source` moved from `first_capacity_row` to `ET_meta` (input change, not a code change) |
| full release, `--cu-only` (CU csv only, the file set of the first pipeline), vs the per-member rerun | byte-identical rows for all 147 cells that had been processed (1176 rows) |
| full release, full file set, CU rows of the 76 baseline cells | `q_dch`, `q_ch`, `q_mean`, durations, start dates and exposure estimates identical in 539 of 539 rows. Columns that depend on the added rows change by design: reference (now ET_T23), retention, `gap_days_prev` (exCU rows now sit between CU rows), `cu_idx` formatting (float because the column now holds blanks). The 2 date-derived rows of TP_z08_03_s1 as above. **2 CU rows of the 75 stable cells change from pass to flagged by the causal outlier rule**, because exCU rows now enter its "two preceding valid check-ups". |

Test suite (full, `code/tests`): 587 passed in 6 min 54 s (before the last edit of the audit script's output columns; `test_samsung_full_release.py` and `test_samsung_checkups.py` re-run afterwards, passed).

## 3. QC (task 3): causal rule, `OUTLIER_DROP_MULT = 3.0`, `OUTLIER_REL = 1 %`, thresholds unchanged

| | rows | qc pass | qc fail |
|---|---|---|---|
| CU | 1532 | 1501 | 31 |
| exCU | 682 | 669 | 13 |
| ET_T23 | 279 | 279 | 0 |
| AT_T23 | 273 | 268 | 5 |
| all | 2766 | 2717 | 49 (29 cells have at least one failed row) |

Flag counts (rows; a row can carry several): charge_discharge_mismatch 24, surface_temp_at_discharge_start_far_from_23C 20, duration21_out_of_range 12,
current21_off_nominal 10, capacity_outlier_vs_neighbours 5, negative_exposure_time 5, duration22_out_of_range 3, step22_missing 3, no_start_date 3, date_out_of_order 3,
current22_off_nominal 2, charge_not_to_4p2V 2, multiple_runs_21 1, setpoint_not_23C 1. Information flags: long_file 1322, voltage_glitch_below_2V 669, AT_after_10C_45C_tests 273,
capacity_rise_gt_0p5pct 7, stub_run_21 1, stub_run_22 1. The 3 capacity-derived flags (outlier, implausible capacity, charge-discharge mismatch) are counted only; the 38 rows with a
structural flag are listed by identifier in `structural_problem_rows.csv`.

Files with problems (`runs/samsung_pipeline/issues.csv`, 56 rows, plus the listing check): meta internal serial differs from the design table 49 cells (section 4); start date decreases with file index 3
(TP_z02_03 idx 12, TP_z09_02 idx 21, TP_z25_01 idx 9); start date unparsable 2 (TP_z12_03_07_exCU_meta, TP_z19_01_31_CU_meta, raw text `22.10.222`); CU csv without meta 1 (TP_z02_02_09_CU);
chamber set point not 23 C 1 (TP_z08_02_19_exCU, 35 C); exCU meta without csv 1 (TP_z01_02_s1). Two ZYK meta files carry an impossible date (TP_z02_02 file 16: 19.01.2021; TP_z04_03 file 13:
21.01.2021, about 8 months before every other test); they do not enter the pipeline (the first-test date is taken from the ET meta).

## 4. FB-3 / FB-4: stage assignment of all 279 cells (metadata and file dates only)

| result | value |
|---|---|
| folders / design cells / distinct `cell_id` | 279 / 279 / 279; the set of `cell_id` equals the design set exactly; no duplicate, none unassigned, none `_s?` |
| cells per stage | stage 1: 141 (75 cycling, 66 storage); stage 2: 138 (72 cycling, 66 storage) |
| decided by (pipeline rule order) | internal serial 227, laboratory 13, first test date 36, unique name 3 |
| independent re-derivation (`stage_assignment.csv`) | four rules, each applied where it can decide: internal serial (230 folders), laboratory (39), first meta date (279), testpoint tag `<serial>_MKII` (96 folders = 48 serials; present in exactly one zip of each, it marks the second-stage zip). **Disagreements between rules: 0. Cells to exclude under 3.2: 0.** Tag rule agrees 96 of 96 |
| date ranges of the meta files | stage 1: up to 2022-10-12 (earliest regular start 2021-09-08); stage 2: from 2022-12-01 to 2024-04-12. The ranges do not overlap, so the pipeline's 2022-07-01 cut on the first date is unambiguous (no folder has its first date inside the 2022-07-01 to 2022-11-30 gap) |
| stage by figshare id order (lower id = stage 1) | agrees in 222 of 276: not a rule, recorded only |
| contradiction between meta internal serial and design table | 49 cells (stage 1: 45, stage 2: 4), all resolved by laboratory, date and, where present, the tag; they include **TP_z10_01_s1 and TP_z15_01_s1**, the two open cases of PREREG 3.2. The stage-2 zip of each of the two has a meta serial equal to the design table, so the other zip is stage 1 by elimination, and date and laboratory agree. The labels follow a permutation among INT-laboratory cells (e.g. the meta of TP_z04_01_s1 carries the design serial of TP_k04_04_s1), so the design table's `serial_internal` column is unreliable for these 49 cells; it is not used for anything but the stage vote, and the condition of a cell comes from its zip name. 38 folders share a meta internal serial with another folder |
| other label oddities | `Testpoint` field of TP_k03_04, _05, _06 reads `k02noCU` (zip name k03; stage not affected) |
| splits | all 147 cycling `cell_id` in `samsung_splits_v2.json` (test cells of the 5 folds) exist in the cell table with the same stage |

Incident files (PREREG 3.3(4)), stage in which the named file exists: TP_z25_01_01_ET: stage 1 only; TP_z17_02_19_exCU: stage 1 only; TP_z01_03_11_CU, TP_z17_03_13_exCU,
TP_z17_03_17_CU and TP_k11_02_03_exCU exist in **both** stages (listing alone cannot decide which one the paper means). The drop stays by (serial, file, kind) for both stages: at most 4 files
over-dropped. Consecutive-file drops: `INCIDENT_CONSECUTIVE_DROPS_IMPLEMENTED = True` in `data.py` (not re-examined here).

**FB-3: met on the evidence, lead to confirm.** Full data on disk, 279 zips CRC-tested, manifest written, pipeline re-run, ET and exCU parsed. ET_T23 exists and passes QC for all 213
analysed cells (147 cycling + 66 storage cells 01-03) and for all 279 cells, so the Q0 rule 3.3(2) (ET_T23 capacity if ET members exist for every analysed cell) is available without fallback to the first CU.
**FB-4: stage assignment closed (0 conflicts, 0 exclusions).** Open inside FB-4: stage of 4 incident files (both-stage files, over-drop kept) and the 49-cell label anomaly to be disclosed.

## 5. FB-6: window counts from the zip listings (identifiers only)

Count = intermediate check-ups = CU + exCU csv members per cell (ET and AT excluded), computed with `pinnkan.data.window_rule_from_counts`.

| | cells | min | q25 | median | q75 | max | count by value |
|---|---|---|---|---|---|---|---|
| cycling | 147 | 3 | 11 | **11** | 15 | 15 | 3:2, 4:1, 5:2, 6:3, 7:5, 8:2, 10:1, 11:59, 13:1, 14:29, 15:42 |
| storage cells 01-03 | 66 | 5 | 5 | **6** | 7 | 8 | 5:21, 6:15, 7:18, 8:12 |

**k_cyc = round(11 / 3) = 4; k_sto = round(6 / 3) = 2** (unchanged, 4 and 2, after the file-level incident drops). Both are inside the expectation of PREREG 5 (3 to 5; near 2); k_full >= 2, the design is not re-opened.
Median by stage (cycling): stage 1: 14 (7 to 15), stage 2: 11 (3 to 15); by temperature: 23 C 11, 35 C 11, 45 C 14. Storage cells 01-03: median 6 (stage 1), 7 (stage 2).
Schedule go/no-go: cycling cells with at least 3 check-ups after the window of k = 4: 139 of 147 by listing, 136 of 147 after QC (141 with at least 1). Fewer than 3 (8 cells, all stage 2):
TP_z02_03_s2, TP_z10_01_s2, TP_z20_01_s2, TP_z20_02_s2, TP_z20_03_s2, TP_z23_01_s2, TP_z23_02_s2, TP_z23_03_s2; two of them (TP_z20_02_s2, TP_z23_01_s2) have only 3 intermediate check-ups,
so cannot carry a window of 4. The go/no-go ("fewer than 3 for most cycling cells") is not triggered. **FB-6: counts fixed from listings; values for the lead to adopt.**

## 6. FB-5: ZYK files (presence and parseability per cycling cell)

| result | value |
|---|---|
| cycling cells with at least one ZYK csv | 147 of 147; storage cells with a ZYK csv: 0 |
| ZYK csv in the listing / read from the zips / schema ok (run_time, c_vol, c_cur, step_type) / read errors | 1893 / 1893 / 1893 / 0 |
| ZYK meta without csv | 6 files, cells TP_z01_01_s2, TP_z01_02_s2, TP_z01_03_s2, TP_z03_01_s2, TP_z03_02_s2, TP_z03_03_s2 (recorded as `missing_file` segments) |
| other parse flags | time not monotonic 2 files, fewer than 10 rows 1 file; charge-discharge imbalance above 5 % (information) 4 files |
| `zyk.py` completeness (`GAP_FLAG_S = 600 s`, any sampling gap) | 523 files complete, 1370 flagged `sampling_gap`; only 9 cells have every ZYK file complete |
| the same gap counted only while current flows (|I| > 0.05 A) | 15 files exceed 600 s (46 exceed 60 s); 1875 files complete, 129 cells fully complete. Of the 1370 flagged files, 1355 have their long gap in a rest period only; 15 have a gap above 600 s while current flows (identifiers in `zyk_files.csv`, column `dt_max_active_s`) |
| table | `data/processed/samsung_zyk_efc.csv` (1899 rows: 1893 read + 6 missing; sha256 `546e03b0aa451b0ccee1efbaa4e263fbf676a5d5825997b711ccc331b22fac4d`, git-ignored) |

The existing `pinnkan.zyk` validation run informationally with the assumed constants on the only cells it can use (12 INT stage-2 cells whose every interval is complete under the any-gap rule, 120 pairs):
median relative difference between analytic and logged throughput 24 %, worst at the last check-up 25 %; accept-analytic = false. This is **not** the FB-5 verdict: the sample has one laboratory
and `GAP_FLAG_S` and the gap definition are assumptions in `zyk.py` that were to be fixed once ZYK files were read. **FB-5: files present and parseable; the verdict needs the lead's gap-rule decision,
then `python -P -m pinnkan.zyk --validate`** (after the decision the sample can be 129 cells covering all laboratories and DoD classes).

## 7. Test B cell table (lab map)

`data/processed/samsung_cells.csv` (279 rows; sha256 `e48c216611d50f0d39504253067ecb5a49a99e2e7c4f5ff52cd9b597c0a1a86e`): all 40 cycling conditions present (design 40, table 40, `samsung_splits_v2.json` 40,
none missing either way); 147 of 147 cycling cells in the table, 0 null in lab, stage, tp, cell, T, SOC_max, DoD, C_ch, C_dch, type; every condition has as many cells as in the design; 147 of 147 split test cells found.
`majority_labs` returns 40 conditions (sha256 of the map `629358d675771bc076180c158b626aee15ff6a2247cadf2e2bc81d702d03f687`). Storage: 19 of 19 conditions, 132 cells. Per condition: `test_b_conditions.csv`.
**Caution for the lab map:** 3 conditions have cells from two laboratories: T23|SOCmax0.8|DoD0.25|Cch0.2|Cdch1.4 is **a tie, HM 3 and INT 3** (`majority_labs` breaks ties alphabetically, so it returns HM);
T45|SOCmax0.8|DoD0.6|Cch0.24|Cdch2 and T45|SOCmax0.8|DoD0.6|Cch1|Cdch2 are HM 6 / SIE 3 (clear majority).

## 8. Counts per stage, arm, temperature, laboratory (cells; all downloaded)

| arm | stage 1 | stage 2 | 10 C | 23 C | 35 C | 45 C | HM | INT | SIE |
|---|---|---|---|---|---|---|---|---|---|
| cycling (40 conditions, 3 to 12 cells each) | 75 | 72 | 0 | 33 | 39 | 75 | 69 | 60 | 18 |
| storage (19 conditions, 6 to 24 cells each) | 66 | 66 | 30 | 60 | 0 | 42 | 54 | 42 | 36 |

By stage and laboratory, cycling: stage 1 HM 30, INT 36, SIE 9; stage 2 HM 39, INT 24, SIE 9. Storage: stage 1 HM 30, INT 18, SIE 18; stage 2 HM 24, INT 24, SIE 18.
Conditions with at least 3 quality-passed trajectory points: 59 of 59 (cycling 40, storage 19); cells with at least 3 / 5 passed rows: cycling 147 / 145, storage 66 / 66 (counts include ET and AT rows).
Check-up rows: cycling cells 2085, storage cells 681. Per condition: `runs/samsung_pipeline/conditions_summary.csv`; per cell: `cells_summary.csv`, `folder_mapping.csv`.

## 9. Pins

| file | sha256 |
|---|---|
| `data/processed/samsung_checkups.csv` | `6fa9b85e30ca816e8cfcb476792f544fc7437de2aaa6d06976b301c44ae47c4f` |
| `data/processed/samsung_cells.csv` | `e48c216611d50f0d39504253067ecb5a49a99e2e7c4f5ff52cd9b597c0a1a86e` |
| `data/processed/samsung_zyk_efc.csv` | `546e03b0aa451b0ccee1efbaa4e263fbf676a5d5825997b711ccc331b22fac4d` |
| previous `samsung_checkups.csv` (76 cells, kept in `data/processed/_baseline_pre_full/`) | `e37c5294f12015234038f7802336705568c647aeb6abca32c0723f96858de0e3` |
| previous `samsung_cells.csv` | `c50620ad8b148b2e78c216ae8a74746b08e0891a3c071be7aa26e61c1340eb0f` |

## 10. Concerns for the lead

1. Retention in the new table is anchored on ET_T23 for every cell (ET passes QC everywhere); the first pipeline anchored on the first CU. `retention_vs_first_cu` is kept as a column. Freeze decision (Q0).
2. The causal outlier rule now sees exCU rows as preceding points: 2 CU rows that passed in the CU-only series are flagged. The rule is unchanged; the denser series is the reason. Decide whether exCU belongs in the rule's series.
3. The `serial_internal` column of the design table disagrees with the files for 49 INT-laboratory cells; stage is safe, the column is not an identifier here.
4. Lab-map tie (HM 3 / INT 3) in one Test B condition.
5. ZYK `GAP_FLAG_S` and the gap definition decide whether analytic throughput can even be validated on a full sample; strict reading leaves 9 cells.
