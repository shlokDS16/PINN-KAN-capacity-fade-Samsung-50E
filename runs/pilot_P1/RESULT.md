# P1 result: local data readiness (2026-11-04)

Judge rule (D010 section 7, P1): **Go** if Table A1 matches the scratch transcription and SNL gives per-cycle
capacity and throughput. **No-go**: fix transcription; drop duplicated SNL cells.

## Verdict: GO (both parts)

### (a) ISU-ILCC Table A1 against README_V2.0.pdf
- Reading depth: README_V2.0.pdf full text converted with markitdown (`runs/pilot_P1/README_V2.0.md`); Table A1 (appendix,
  two blocks: groups 1-41 and 42-64; there is no group 15) parsed by `code/data/isu_conditions.py`.
- Proposer's hand transcription (`debates/D010_topic/pilot_scratch/isu_profile.py`, parsed as text, never run):
  **0 mismatches** over 63 groups x 3 fields (charge C-rate, discharge C-rate, mean DoD). Report: `isu_table_check.json`.
- One extraction artefact, handled and logged: the page number "10" sits inside the discharging C-rate column at the page
  break (index 40) and is dropped; the column then has 63 entries like the others.
- The 63 groups in the table equal the 63 groups present in `capacity_fade.zip` (251 cells, no group missing either way).
- README facts worth keeping: constant 30 C chamber; the 0.5-week RPT exists only for groups 20-64; groups 20-29 lost the
  4th-week RPT; cells G25C1 and G26C1-C4 lost weeks 23-24 (A2 notes). `capacity_fade` column 1 is "time on test"
  (weeks, from the README and the 0-88 range), column 2 remaining C/5 capacity (Ah).
- Written: `data/processed/isu_conditions.csv` (63 rows: group, charge_c, discharge_c, dod_pct) and
  `data/processed/isu_capacity.csv` (5,455 rows, 251 cells: cell, group, week, retention = Q/Q at week 0, capacity_ah;
  2 to 80 points per cell; no non-finite values; every cell starts at week 0).

### (b) SNL per-cycle schema and duplicates (allowlist loader only)
- 61 of 61 pickles loaded through `verify_raw.safe_pickle_load` (static scan, allowlist unpickler); plain pickle never called.
  Peak RSS 222 MB.
- Per cell and cycle: capacity (max of cumulative discharge and charge Ah), time (start and end, seconds since the cell's first
  sample), charge throughput (integral of |I| dt), mean temperature, mean |I|. `data/processed/snl_cycles.csv`
  (96,492 rows; cycles per cell 389 to 4,569) and `snl_cells.csv` (conditions parsed from the file name, 61 rows).
- Quality: no missing cycle numbers in any cell; one cell with 90 invalid capacity records (LFP 25 C 0.5-1C replicate b,
  cycles 2622-2711, capacity zero or empty: exclude those rows); mean temperature missing in 4,639 rows (the temperature
  column is empty in those cycles); 30 of 61 cells fall below 80 % of their first-cycle capacity within the record.
- **Duplicates: none.** All 1,830 cell pairs tested three ways: (1) SHA-1 of rounded voltage and current at 5 cycle positions
  (cycles 1, 2, 100, middle, last): 0 matches; (2) per-cycle capacity vectors identical over common cycles: 0 pairs;
  (3) median absolute difference below 1e-4 Ah: 0 pairs. The 31 cells that share a cycle count in 11 groups (for example
  LFP 25 C 0.5-1C c and d, both 3038) have different time stamps and different capacity values (c vs d: equal in 34 % of
  cycles only because capacity is quoted to 1 mAh; maximum difference 2 mAh, time axes differ), so the shared count is a
  common stopping step, as INVENTORY suspected possible. Replicate trajectories are close, as replicates should be; do not
  count replicate agreement as duplication. No SNL cell needs dropping for duplication.
- Caveats for later use (not blockers): capacity is measured at the cell's own cycling rate (0.5 to 3C discharge), not at a
  fixed reference rate; cycle 1 is not always a clean reference (median ratio of cycle 1 to cycles 2-10 is 1.003, range
  0.994 to 1.060); the mirror holds 0-100 % and 20-80 % windows only (INVENTORY).

Files: `config.json`, `isu_table_check.json`, `snl_duplicates.json`, `README_V2.0.md`; code in `code/data/`.
Scratch numbers in the proposer's folder are not used.
