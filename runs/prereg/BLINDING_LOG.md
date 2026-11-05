# Blinding log: every pre-freeze exposure to Samsung outcome data (append-only)

Rule: before runs/prereg/FROZEN exists, no person or agent may inspect Samsung retention or capacity values of
outer-test cells. Every exposure, intended or not, is recorded here and disclosed in the paper's methods.

| when | who | what was seen | cells | split membership | used for any decision? |
|---|---|---|---|---|---|
| 2026-11-04 22:40 | lead (P0 probe) | capacity of one check-up each (4.878 Ah, 4.822 Ah) | TP_k03_01 (stage 2), TP_z18_01 (stage 2) | to be looked up at the freeze | schema check only (GO on file layout) |
| 2026-11-05 00:09 | Samsung pipeline agent | capacities of 163 check-ups of 19 cells parsed and QC-checked (not scored) | 18 cycling + 1 storage (runs/samsung_pipeline) | to be looked up at the freeze | pipeline QC only; flagged by gate audit (item 3) |
| 2026-11-05 03:15 | lead | retention sequences of two cells while checking QC flags (5 check-ups each) | TP_z02_01_s2, TP_z02_02_s2 | to be looked up at the freeze | QC rule design (time-scaled drop allowance), no model decision |
| 2026-11-05 ~04:00 | builder agent (grep) | ten rows of samsung_checkups.csv printed to its terminal; nothing copied | TP_z24_01_s1 | split search output: /B/folds/1/test_cells
/A/folds/0/test_cells | none (agent's disclosure, RESULT.md 7.5) |

- 2026-11-05 (D024 judge, gate-auditor agent): printed the qc_pass bit (True/False) of the 6 incident check-up rows while ruling on the stage scope of the incident drop (one False). No capacity or retention value was shown. Logged by the lead for transparency; the freeze judge decides whether it matters (judged immaterial by the D024 judge: a QC flag, not an outcome, and the rows are dropped or kept by the dataset paper's incident list, not by the flag).
