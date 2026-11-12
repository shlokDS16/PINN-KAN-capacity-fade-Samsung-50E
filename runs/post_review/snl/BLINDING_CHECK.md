# SNL Test B replication: blinding and preregistration check (D048 item 8)

Written by the lab-engineer before any SNL outer-test score. Result: **the SNL split is not outcome-blind; SNL was struck from the replication list; the SNL replication was NOT run.**
All statements below were read from the files named; nothing was inferred from memory.

## 1. Preregistration status of SNL (runs/prereg/PREREG_v4.md at c6a89b6)
- Line 52 (outcome table): "ISU, SNL | secondary, not blind".
- Line 85, disclosure sentence (a): "ISU and SNL were explored in a scratch pilot before their splits were fixed; their results are therefore secondary and not blind."
- Line 90 (section 3.4 title): "ISU-ILCC and SNL (not blind; ...)"; line 93: "ISU and SNL are labelled **not blind**".
- Line 95 (role under Design R2): "**There is no SNL replication (D028 (d) 7):** no scarce SNL window was fixed, and choosing one now on non-blind data would be a new design choice". SNL "stays secondary
  without a calendar arm"; the optional descriptive replication slot is ISU only.
- So SNL was struck from the replication list (not "pinned and merely unscored"). The split file is nevertheless pinned: FROZEN lists the split key `snl:B` (file hash and fold hash).
  runs/prereg/SCORED.jsonl has no row with `snl` (grep count 0): the SNL outer folds were never scored.

## 2. Was any SNL outcome inspected before the split was fixed (git history)
- 78d1731 (2026-11-04 23:01:45 +0545): pilot P1/P2 results. P1 (b) read **all 61 SNL cells** (capacity per cycle): "30 of 61 cells fall below 80 % of their first-cycle capacity" (corrected to 35 of 61 in the
  errata, runs/pilot_P1/RESULT.md line 50), replicate agreement, "capacity ... max difference 2 mAh". P2 fitted a PINN and a hard-ODE model on "SNL, all 61 cells, up to 80 observed points per
  cell (4,819 points)" for timing (runs/pilot_P2/RESULT.md line 9). These cells include the conditions that became Test B test conditions 13 minutes later.
- 16a9da4 (2026-11-04 23:14:03 +0545): splits fixed. runs/splits/README.md: "from identifiers only (conditions and cell names; no capacity values read)". The construction of the folds is
  therefore procedurally outcome-blind, **but** the capacity series of every SNL cell, test cells included, had been read and used to fit models in P1/P2 before the folds existed.
- 6de1c0a (2026-11-05): P3 headroom on SNL used training sides of Test B only ("SNL W = 100 cycles 1.13"); build smoke runs `build_v1_smoke_snl_B0`, `fb10_smoke_snl_B0`, `shk_smoke_snl_B0`
  are `mode: inner` (training side) with `steps_scale 0.3` and 2 trials.
- No SNL test-side outcome was scored after the split (no SNL run with `mode: confirmatory` exists; the run directories with `snl` in the name are the five inner/smoke/figure-slot runs above).

## 3. Decision
The user's condition was "run only if the split is outcome-blind; if unclear, do not run". The frozen preregistration itself labels SNL "not blind" and records the pre-split pilot exploration; the pilot
read the retention outcomes of the cells that later became test cells. The split-making code did not read capacities, but that does not make the experiment outcome-blind. **Not run.** No file of
runs/post_review/snl/ other than this one exists. If the authors still want an SNL replication it must be labelled "not blind, post hoc, descriptive" like ISU, and registered as a new decision first.

## 4. Open point (for the lead)
EXP_PLAN section 8 says "PREREG struck the SNL replication, so it is post hoc" and also "the outer folds were never scored" and "procedurally blind split". The first and the third are both
true in their own sense; neither makes the data blind. The wording in the paper should say: split fixed from identifiers, SNL data explored in pilots P1/P2 before the split (PREREG_v4 3.4).
