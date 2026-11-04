# Pilot P0: Samsung INR21700-50E per-cell file schema (2026-11-04, 22:20-22:40)

Commands: `tools/zip_range_fetch.py list` on 4 per-cell zips (TP_k03_01 storage 10 C; TP_k10_05 storage
45 C; TP_z10_03 cycling 35 C; TP_z18_01 cycling 45 C centre point); member lists in `*_members.tsv` here.
Probe: `code/data/samsung_cu_probe.py` on `TP_k03_01_02_CU.csv` and `TP_z18_01_03_CU.csv`
(output reproduced below). Data: `data/raw/samsung50e_members/`.

## Findings
- Each per-cell zip holds CSV time series (run_time, c_vol, c_cur, c_surf_temp, amb_temp, step_type) for
  entry tests (ET, at 10/23/45 C), check-ups (CU), extended check-ups (exCU), cycling segments (ZYK,
  cycling cells only) and final tests (AT), each with a small `_meta.txt` (lab, device, chamber set
  point, measurement start date).
- CU files: about 0.12-0.35 MB compressed, about 1.9-3.7 MB as CSV, about 15.4 h of test each.
- In both probed CU files, step_type 22 is a constant-current discharge of about 4.5 A from about 4.2 V
  to 2.5 V lasting about 1.05 h: integrated charge 4.878 Ah (TP_k03_01, CU 02) and 4.822 Ah
  (TP_z18_01, CU 03). step_type 21 is the preceding charge (about 4.85 Ah). So **check-up capacity is
  computable from the CU member alone** (go criterion met on schema).
- Calendar time: CU meta files carry a measurement start date (day resolution).
- Throughput for cycling cells is not in the CU files; it is in the ZYK segments (0.8-6.4 MB
  compressed each). Plan: compute equivalent full cycles from the ZYK files of a few cells and check an
  analytic estimate from the designed DoD and C-rates against them; if the analytic estimate fails, ZYK
  files are needed for all cycling cells (part of the full download).
- Number of CUs per cell (from listings): storage TP_k03_01 has 4 CU and 3 exCU; TP_k10_05 has none
  (only entry and final tests, i.e. no intermediate check-up in this cell); cycling TP_z10_03 has 7 CU
  and 2 exCU, TP_z18_01 11 CU and 5 exCU.

## Verdict against the judge's rule (04_judge.md section 7)
- Schema: **GO** (capacity per check-up from a small separable member).
- All-cell size of the CU members: estimated from these 4 listings at roughly 0.5 GB, above the 400 MB
  overnight threshold, and the link ran at 2-50 KB/s tonight. So the judge's overnight queue cannot be
  completed tonight. Action taken: a resumable range-request job (`tools/samsung_cu_batch.py`, detached
  restart loop `tools/run_samsung_cu_forever.ps1`) fetches CU members for all 279 cells in an order that
  covers every condition first (download order only; analysis uses all cells). Whatever is missing by
  morning goes to Shlok as a full download on a faster network (10.29 GB).
- Open: TP_k10_05 has no intermediate CU; check how many storage cells lack check-ups (some storage
  test points may be end-point only), which affects the storage arm's forecasting window.
