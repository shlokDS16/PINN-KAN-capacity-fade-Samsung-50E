> **DRAFT, outcome-independent section. The claim is not frozen. Counts are design or metadata counts; every count that depends on quality control or on the complete download is a placeholder. No capacity or retention value appears.**

# 3. Data

## 3.1 Samsung INR21700-50E, the primary data set

The primary data are the multi-stage ageing study of Stroebl et al. [@stroebl2024]: 279 commercial cells of one type (rated 4.9 Ah) tested in two stages and three laboratories (HM, INT, SIE) with one protocol. Stage 2 used a new cell batch, so stage is a batch effect. <!-- src: notes/papers/samsung50e_dataset_paper.md; runs/prereg/PREREG_v2.md 3.1 -->

*Storage arm.* The arm has 132 cells at 19 conditions (10, 23 and 45 C; state of charge 5 to 100 %, limited to 80 % in stage 2 because stage 1 behaved non-monotonically above it). Only cells 01 to 03 of a test point (66 cells) have intermediate check-ups; cells 04 to 06 are excluded from training and scoring in the primary analysis. No storage condition exists at 35 C.

*Cycling arm.* The arm has 147 cells at 40 conditions, with three cells at 35 conditions and 6, 6, 9, 9 and 12 cells at the five repeated centre points. Cycling temperatures are 23 C (10 conditions, 33 cells), 35 C (13 conditions, 39 cells) and 45 C (17 conditions, 75 cells). The design varies upper state of charge, depth of discharge (DoD) and charge and discharge rates within a 20 to 80 % window.

*Capacity and time.* The study provides no capacity table. Capacity at a check-up is the mean of the charge and discharge capacity (charge at C/2 to 4.2 V, discharge at 1C to 2.5 V, ambient 23 C), integrated from the logged current as in the data paper. Retention is capacity divided by a per-cell reference $Q_{0,c}$: the initial-test capacity at 23 C if it exists for every analysed cell, otherwise the first check-up that passes quality control [RESULT: rule after the complete download]. Time is counted in calendar days since the reference. Throughput in equivalent full cycles (EFC) comes from the design rates and is checked against logged cycler throughput on a sample [RESULT: median and maximum relative difference].

*Quality control and exclusions.* A check-up, not its cell, is dropped when a prespecified flag fires (thresholds in Appendix A). The outlier rule compares a check-up only with the preceding ones [TO VERIFY: the current code also uses the following neighbour; the causal form is queued for the frozen version]. Files that the data paper lists as faulty are dropped; no cell is excluded for its capacity trajectory. A cell is keyed by serial and stage, and a cell whose stage checks disagree is excluded and listed [RESULT: cells excluded]. Capacities of 18 cycling cells (163 check-ups) were parsed and checked before the preregistration was frozen, without scoring any model.

*Confounds.* All 39 cells at 35 C were run by laboratory INT. Cycling at 45 C is HM (66 cells) and SIE (9 cells), and storage at 10 C is entirely SIE and at 45 C entirely HM. Temperature is therefore aliased with laboratory in the 35 C test of Section 5 and in part of the storage analysis. The capacity test is also not isothermal: the cell surface averages 31.6 C (stage 1) and 29.8 C (stage 2) during the 1C discharge in the 23 C chamber, and laboratories differ. The primary models do not correct for either effect; laboratory and stage are sensitivity rows. <!-- src: runs/samsung_pipeline/RESULT.md item 7; PREREG_v2 3.3(7) -->

## 3.2 Secondary data sets

ISU-ILCC [@li2024isu] has 251 NMC/graphite pouch cells at 63 cycling conditions (charge rate, discharge rate, DoD), weekly reference tests and no storage arm; time is in weeks. The Sandia set (SNL) [@preger2020] has 61 commercial 18650 cells (LFP 18, NCA 22, NMC 21) cycled at 15, 25 and 35 C and discharge rates of 0.5 to 3C in 23 conditions; time is in cycles. Neither set has a calendar arm, so only the cycling term is used. Both were explored in a scratch pilot before their splits were fixed, so their results are labelled secondary and not blind. Their forecast sets end at the first point below 70 % retention.

| Set | Role | Cells | Conditions | Held-out unit | Cells used after QC |
|---|---|---|---|---|---|
| Samsung storage | training; storage transfer (S2) | 132 | 19 | S2: 5 folds | [RESULT] |
| Samsung cycling, Test B | primary | 147 | 40 | 5 folds of 8 conditions | [RESULT] |
| Samsung cycling, Test C | secondary | 39 held out | 13 held out | 35 C, laboratory INT | [RESULT] |
| ISU-ILCC | secondary, not blind | 251 | 63 | cycling conditions | [RESULT] |
| SNL | secondary, not blind | 61 | 23 | cycling conditions | [RESULT] |

<!-- src: PREREG_v2 3.1, 4; data/processed/isu_capacity.csv (251 cells, 63 groups), snl_cells.csv (61 cells), counted without reading any retention value. Table 1 caption to write: QC = quality control -->
