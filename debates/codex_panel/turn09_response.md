## 1. The defect is real; the proposal misses two code barriers

`item_f_from_runs` reads `tuning_done.json`, which is written only after tuning. Before a valid freeze, the Samsung blinding branch downgrades non-confirmatory runs to timing, and confirmatory runs require the freeze. Meanwhile, `build_freeze_payload(..., require_pins=True)` requires the item-f files because they are in `PIN_FILES`. As written, the required item-f evidence cannot both exist before the freeze and come from the specified Samsung training-side scores.

The two-phase proposal also needs more than a CLI flag:

- `run.py` sets `role = "test"` for `mode == "confirmatory"` and builds the data before tuning. A tune phase in confirmatory mode would therefore load the outer test fold unless this path is explicitly changed.
- `run.py` refuses an existing run directory unless overwrite is enabled; confirmatory runs on real data reject overwrite. A score phase cannot simply resume the tuning directory under the present rules.
- The scored-run guard only treats `condition_scores.json` as the “never replaced” marker. The score phase must not overwrite phase-one artifacts or permit a rerun after any score file exists, including suffixed condition-score files. `SCORED.jsonl` also remains append-only.

The proposal is right to flag that item (f) must be computed for every fold before the **first** outer score. Its rule is only a disclosure sentence, not a tier change, but that does not waive D18’s pre-score requirement.

## 2. O2 is valid only after stronger separation and guards

Two-phase execution can satisfy the pre-score rule if phase one uses training data only, produces the exact inner-CV artifacts used by the estimator, and all folds finish before item (f) is computed and written. Phase two then scores without changing those artifacts. The `tuning_done.json` hashes help detect edits, but do not prove the phase-one process never loaded test data.

The item-f file cannot remain a required **freeze-time** pin if it is generated after the freeze. Remove it from `PIN_FILES`/`require_pins` for the initial freeze, and define a separate immutable item-f hash record that the statistics step requires. Write it outside tracked `runs/prereg`, as proposed, and ensure the stats step verifies its hash and pre-score creation. Do not let item-f results alter critical counts or rules; the prereg already says they do not.

No test label needs to influence item (f) under this design. But the current runner’s unconditional test-role build and directory refusal mean that guarantee is not implemented yet.

## 3. Simpler option

**O1, separate post-freeze `inner` runs**, is simpler to audit: inner mode uses training-side data, item (f) is computed, then ordinary confirmatory runs begin. It costs duplicate tuning and compute, but avoids resume semantics and phase-boundary bugs. Speculation: a dedicated “training-side item-f” command could be cleaner still, but it would need an explicit fold-data audit and tests before trust.

## Verdict: revise

1. Prefer separate inner runs unless the two-phase path is implemented and tested to prove no test-role load, no outer prediction, and no artifact overwrite during tune.
2. Remove item (f) from freeze-time required pins; give its post-freeze record a hash, immutable location, and stats-step validation.
3. Enforce “all folds’ item (f) written before any outer score” through an explicit state/ledger check; do not rely on timestamps alone.