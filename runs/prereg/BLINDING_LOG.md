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


## Split look-up of the kind (b) cells (2026-11-06, coder C13; identifiers only, no capacity or retention value read)

Looked up in `runs/prereg/samsung_splits_v2.json` (byte-identical copy in `runs/splits/`) by `code/prereg/make_blinding_exclusions.py`; result in `runs/prereg/blinding_exclusions.json` (pinned at the freeze).

| cell | outer-test cell of | excluded from scoring (3.3(11)) |
|---|---|---|
| TP_k03_01_s2 | S2 fold 4 | yes (S2 fold 4, condition T23\|SOC0.2: 5 of 6 test cells remain) |
| TP_z18_01_s2 | Test B fold 0; Test A fold 1 | Test B fold 0 (condition T45\|SOCmax0.8\|DoD0.6\|Cch0.2\|Cdch0.44: 11 of 12 remain); Test A is not a confirmatory test (informational) |
| TP_z02_01_s2 | Test B fold 2; Test A fold 0 | Test B fold 2 (with TP_z02_02_s2: condition T45\|SOCmax0.8\|DoD0.6\|Cch1\|Cdch2, 7 of 9 remain); Test A informational |
| TP_z02_02_s2 | Test B fold 2; Test A fold 1 | as above |
| TP_z24_01_s1 | Test B fold 1; Test A fold 0 | Test B fold 1 (condition T45\|SOCmax0.45\|DoD0.05\|Cch1\|Cdch1.8: 2 of 3 remain); Test A informational |

No cell is an outer-test cell of Test C. No condition is left without a scored cell by the exclusion alone, so n stays 40 (Test B) and 19 (S2) before QC and forecast rules. Four z-type cells of Test B are excluded, as 3.3(11) states (minimum n = 36 holds).
