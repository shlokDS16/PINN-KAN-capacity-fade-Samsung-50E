# Outer splits (fixed 2026-11-04 before any model sees data; P3)

Made by `code/pilots/p3_make_splits.py` from identifiers only (conditions and cell names; no capacity values read).
Files: `isu_testB.json`, `snl_testB.json` (held-out conditions, 5 folds), `isu_testA.json`, `snl_testA.json`
(held-out replicate cells, 4 folds). Each file stores the seed, the stratification rule, the per-fold test
conditions/cells and `sha256_of_folds` (hash of the fold block, checked by every run).
Seeds: ISU 20261104 (Test B) and 20261105 (Test A); SNL 20261105 (Test B) and 20261106 (Test A).

- ISU Test B: 63 conditions, folds of 12-13; k-means (13 clusters on standardised charge C, discharge C, DoD)
  gives stress-space neighbourhoods whose members are dealt to different folds. Five folds (judge, section 6),
  not the proposal's seven.
- SNL Test B: 23 conditions (chemistry x temperature x SOC window x charge C x discharge C), folds of 4-5; blocks
  of 5 stress-neighbours inside a chemistry dealt to different folds. Condition groups are the unique parameter
  tuples in `snl_cells.csv` (1-4 cells each; 3 conditions have a single cell). Chemistries are pooled in the
  split; temperature is not a stratum on its own because only 3 levels exist per chemistry.
- Test A: replicates permuted within each condition and dealt to folds 0-3 (ISU: each condition keeps 3 of 4 in
  training; SNL: single-cell conditions are never held out).
Test folds must not be read by any tuning or exploratory step. P3 uses only the training side of Test B.
