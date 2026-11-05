# Samsung 50E check-up pipeline (2026-11-05, code version 2026-11-05.5)

Code: `code/data/samsung_checkups.py` (tests: `code/tests/test_samsung_checkups.py`, 19 pass, including the two
probed files: step 22 of TP_k03_01 CU 02 and TP_z18_01 CU 03 reproduce about 4.878 and 4.822 Ah within 0.01 Ah;
the trapezoid rule gives 4.884 and the probe's backward rectangle 4.878, a 0.12 % method difference that cancels
in retention). Outputs: `data/processed/samsung_checkups.csv`, `samsung_cells.csv` (gitignored) and, in this
folder, `metrics.json`, `config.json`, `issues.csv`, `cells_summary.csv`, `conditions_summary.csv`,
`folder_mapping.csv`. All numbers below are a snapshot of the download at 00:09 (re-run the script for the current
state; it is idempotent and caches per-file results). Run: `.venv/Scripts/python.exe -P code/data/samsung_checkups.py`.

## Definitions
- Step 22 = CC-CV discharge (median 4.9 A = 1C, CV tail to C/20, 4.2 to 2.5 V); step 21 = CC-CV charge (2.45 A =
  C/2). Capacity = trapezoid integral of current over all samples of the step. `q_mean = (q_ch + q_dch)/2`, the
  dataset paper's definition (mean of charge and discharge capacity of the RPT at 23 C; note
  `notes/papers/samsung50e_dataset_paper.md`). Charge is on average 0.32 % below discharge (range -0.90 to +0.47 %).
- `retention = q_mean / reference`; reference = ET_T23 capacity if that file exists (none downloaded yet), else the
  first quality-passed check-up of the cell (`ref_kind` column). **Retention is therefore relative to the first CU,
  not to the fresh cell** (first CU is 1 week (cycling) or 5 weeks (storage) into ageing), so fade before it is lost.
  The ET_T23 csv (about 1-2.7 MB compressed per cell) is needed for the true Q0.
- Cell key = `cell_id = <serial>_s<stage>`. See data issue 1.
- Cycling cells: `exposure_days_est` = 7 d at the first check-up (design schedule, Fig. 4 of the dataset paper, read
  from the image) + calendar days since the first check-up - durations of the check-up files in between (CU: measured
  file length; exCU: 30 h from the paper, csv not downloaded; number and kind of events from the file numbering and the
  zip member list). `efc_est_*` = exposure x 24 x C_ch C_dch/(C_ch + C_dch) (CC only, zero rest, FEC = discharged
  Ah / 4.9 Ah; DoD cancels). The column `*_rest300s` repeats it with 5 min rest after each half cycle, as a
  sensitivity only. **These are analytic estimates and must be validated against ZYK segment files** (for example
  the first ZYK of 2-3 cells per DoD class; low-DoD cells such as z05 are the most sensitive to rests: 1021 vs 650
  EFC at the last check-up). Storage cells get exposure days but no EFC.
- Flags (critical, set `qc_pass` False): step 21 or 22 missing, durations out of range (22: 0.45-1.35 h; 21: 0.9-2.8 h),
  median current off nominal, sampling gap > 60 s inside the step, NaN current, capacity outside 2.0-5.2 Ah, discharge
  not from >= 4.0 V to <= 2.55 V, charge not to 4.2 V, |q_ch - q_dch|/q_dch > 3 %, surface temperature at the start of
  the discharge more than 5 C from 23 C, setpoint not 23 C, start date missing, start dates decreasing with file
  number, isolated outlier (interior point outside the range of its two neighbours by > 1 %). Info flags: long file
  (> 30 h), voltage below 2 V somewhere in the file, capacity rise > 0.5 %, stub runs.

## Counts (snapshot)
- Design: 279 cells, 59 distinct conditions (19 storage + 40 cycling; matches the judge's count).
- Folders present: 20 (one is empty so far: TP_z02_01__f47631268, not assignable yet). Cells with check-ups: 19
  (1 storage, 18 cycling). Check-up rows: 163, all CU (no exCU, ET, AT csv are fetched), all 163 pass the quality
  flags (no critical flag fired; the outlier rule fired 0 times; interior excess over neighbours at most 0.024 %).
- Cells with a trajectory (>= 3 passed check-ups): 18, all cycling, 17 distinct conditions (of 40 cycling);
  >= 5 points: 17 cells. Storage: 0 (only TP_k03_01 stage 2, 1 CU of 4 expected). Per-condition table:
  `conditions_summary.csv`; per-cell: `cells_summary.csv`.
- Complete cells (all expected CU present): 17 of 20 folders; incomplete: TP_k03_01 (1 of 4), TP_z18_01 (4 of 10, fetch
  in progress, 2 CU metas without csv), the empty folder.
- Stage assignment (`folder_mapping.csv`): 17 by internal serial, 1 by lab (TP_z15_01 s1), 1 by date (TP_z10_01 s1),
  1 unassignable (empty folder). Independent check where possible: ZYK-file chamber set point equals the design
  temperature (TP_z18_01 s2: 45 C, ok); the CU set point is 23 C by protocol and cannot discriminate.

## Cadence (calendar days between consecutive downloaded check-ups; exCU not downloaded, so most gaps contain a hidden exCU)
- Cycling, 18 cells: first check-up 7-77 d after the first test (median 26; stage 1 median 22 d, stage 2 median 62.5 d,
  INT stage 2 cells 76-77 d); gaps overall median 29 d (quartiles 17-45.5, min 7, max 78). By check-up number: CU2 11.5 d
  (7-15), CU3 27 d, CU4 16.5 d, CU5 55 d (14-61), CU6 40 d, CU7 69 d (28-77), CU8 30 d (28-78). 105 of 163 gaps have no
  hidden event, 58 have one hidden exCU.
- Cells have 8 (stage 1 and most stage 2), 10 or 11 CU; the design gives about 15-17 intermediate points in total with
  exCU. Storage: only one cell, first CU 49 d after first test (design: 5 weeks after the end of the entry tests).
- Storage cells 04-06 of every storage test point have no intermediate check-up by design (66 of 132 storage cells have
  CU; 66 do not): `endpoint_only_cell` in `cells_summary.csv`.

## Data issues found
1. **Serial names are not unique.** 138 of the 141 names (TP_k01_01, TP_z01_01 ...) exist in stage 1 and stage 2 as
   different cells with different conditions (279 rows, 141 distinct `serial` values in `experiments_meta.csv`; the
   zips share the names). Joining the design by `serial` alone is wrong for half of the cells. The original fetch
   kept one zip per name; the lead has since changed folders to `<serial>__f<id>`. Resolution used here: internal
   cell serial in the meta text = `serial_internal` of the design (17 of 20 folders), else laboratory, else first
   test date. **The date rule is not "stage 1 early 2023": stage 1 tests (S-prefixed or INT/HM001-series serials)
   started Sep-Oct 2021 and ran to Aug 2022; stage 2 started Jan-Feb 2023.** Example: TP_z01_01__f47632513 is stage 1
   (S019, 2021-09-21), TP_z01_01__f47632462 is stage 2 (021, 2023-01-30).
2. The P0 pilot labelled TP_k03_01 as "storage 10 C"; the downloaded zip is stage 2: 23 C, SOC_max 0.20 (internal serial
   055). P0 labels for k10_05, z10_03 and z18_01 were assigned by name and may be wrong in the same way (z18_01 here is
   stage 2: 45 C, SOC 0.8, DoD 0.6, C_ch 0.2, C_dch 0.44).
3. Internal serial in the meta files contradicts the design table for two folders: TP_z10_01 (meta INT028, table
   INT037/INT149) and TP_z15_01 (meta INT043, table INT052). They are stage 1 by date (2021) and, for z15_01, by lab; if
   the INT serial lists of `experiments_meta.csv` are shifted for stage 1 the conditions of these two cells need a check
   against the paper (low risk: both are INT, 35 C test points, but DoD and C-rates differ between stages).
4. Capacity comes only from the CU files. No exCU, ET or AT csv is downloaded, so roughly a third of the intermediate check-ups (storage:
   3 of 7 intermediate) and the entry/final capacity are missing; retention is anchored on the first CU.
5. CU files end in a rest tail at about 3.9 V: median file length 23.1 h, but active (|I| > 0.05 A) only 12.6 h (8.8-17.6);
   25 files exceed 30 h (up to 176 h). The whole file length is subtracted from the exposure time. 40 files contain
   an end-of-file voltage glitch (as low as 1.1 V) in the rest tail, outside the capacity steps.
6. The gap between ET and the first CU of the INT stage 2 cells is 76-77 d (design: about 2 weeks plus entry tests), so
   time since the first test overstates ageing time for them; the schedule anchor (7 d) is used for exposure, the
   ET-based figure stays in `exposure_days_est_et_route` (for TP_z04_01 s2: 66.8 d vs 7 d). Pauses listed in the dataset
   paper's Technical Validation are not modelled; the exposure estimate is an upper bound if a pause occurred, and dates
   have day resolution (+-1 d).
7. Cell surface temperature during the 1C discharge averages 31.6 C (stage 1), 29.8 C (stage 2) with lab differences (stage
   2 SIE 28.3, INT 29.4, HM 32.9 C; maximum 37.9 C) while the chamber is 23 C, so the capacity test is not isothermal
   and the lab/stage offset can enter the capacity; columns `t_surf_dch_start_c`, `t_surf_dch_mean_c`.
8. Meta date formats differ (dd.mm.yyyy and dd.mm.yy; TP_z04_01 reports "TP_z04_01_MKII", HM stage 2 cells use the
   test-point name as internal serial); the parser handles all three. Two CU metas (TP_z17_01 at the first run) arrived
   after their csv, a transient state of the running download.
9. Paper vs data: dataset paper says 15 h per CU; measured active time is 12.6 h and file length 23 h (median).

## Not done / next
- EFC validation against ZYK files (needs the ZYK csv of a few cells and all ZYK `_meta.txt` for pause detection).
- ET_T23 / exCU / AT_T23 csv for true Q0 and double the intermediate points (code path exists for ET_T23, exCU and AT_T23
  but is untested on real files, none present).
- Re-run after the download completes; empty/in-progress folders are reported, not guessed.


---
Update 2026-11-05: the pipeline now reads the full release (all 279 zips, CU + exCU + ET_T23 + AT_T23); the counts above describe the earlier per-member snapshot. Current numbers and the freeze-blocker evidence: runs/samsung_pipeline_full/RESULT.md.
