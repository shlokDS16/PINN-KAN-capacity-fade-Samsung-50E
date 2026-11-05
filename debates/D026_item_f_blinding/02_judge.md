# D026 judge (2026-11-05): item (f) under retention blinding

## Ruling: O1, restricted to g1, with a ledger gate
The defect is real (verified in `run.py` ~263-297, `guard.PIN_FILES`). O2 is rejected: a confirmatory run sets `role = "test"` and calls `build_data` before tuning (~312), and real-data confirmatory runs forbid `overwrite`, so O2 needs phase-split resume logic in the most guarded path to save about 1 CPU-h. O1 inner runs use `role = "train"` only. O3 breaks D18 2.3 (ii); O4 changes dataset.

## Estimand
D18 2.3 (ii) names no cell; naming one before any score specifies, not changes, the estimand. The code default (D\*, A1) is P1, gated at g1. At m = 8 the inner CV is scored at k = 2 (`rule_tune`), which is g1's own k.
- Cell g1 = (8, 2), max-min subset, outer folds 0-4, inner_k = 2.
- Arms A1, A9, A11 (GP; not LightGBM as the lead wrote) and A12 (LightGBM). D\* comes from `selectors.DSTAR_CANDIDATES` (A9, A11, A12).
- Config: the g1 confirmatory config, with only `mode = "inner"`, `run_id`, the four arms, `diagnostics = false` and `refit_timing = false` changed.
- Estimator: `item_f_from_runs(run_dirs, ("D*", "A1"))`, using each run's own D\*. There is no g4 estimate.
- Cost: tuning of A1 and A9 at about 0.5 of a full fit comes to about 1.1 CPU-h expected and 4 at the ceiling, or 4-5 % of the core. Judge arithmetic from section 16, not measured.

## Location and record
`runs/item_f/` (untracked, outside `runs/prereg/`) holds `item_f_dependence.json` and its `.sha256.json` record. The record gains:
- `frozen_commit`, `cell`, `contrast` and `folds`;
- for each run, the run_id, the config hash, and the sha256 of `config.json`, `tuning_done.json`, `inner_folds.json`, `comparators.json` and `train_condition_meta.json`.

## Order, enforced by state
1. **Writer.** The new `stats_v4.build_item_f` refuses when any of these holds:
   - the freeze is invalid, or HEAD is not the FROZEN commit;
   - a run's `mode_effective` is not `inner`;
   - a config hash is not in FROZEN `item_f_config_sha256s`;
   - the folds are not exactly 0-4;
   - any Samsung row exists in `SCORED.jsonl`, or any Samsung `condition_scores*.json` exists under `runs/`.
2. **Scorer.** The new `guard.require_item_f_record` runs before `build_data` in every Samsung real-data confirmatory run. It refuses when the record is absent, when its hash, `frozen_commit` or any listed artifact hash differs, or when the folds are not exactly 0-4.
3. **Ledger.** Every Samsung `SCORED.jsonl` row carries `item_f_sha256`. `require_item_f` takes this as `pinned_sha256` and requires that all rows carry the same value. The mtime check stays secondary.

## Freeze pins
- Remove `item_f` and `item_f_record` from `PIN_FILES`.
- `build_freeze_payload(..., item_f_config_paths)` writes `item_f_config_sha256s`; with `require_pins=True` it requires five entries.
- The `verify_freeze` message no longer names the item (f) file.

## Actions
**Implementer** (`guard.py`, `stats_v4.py` ~540-650, `run.py` ~238-245 and ~452; tests in `code/tests/`):
1. **Pin change.** Tests: the payload builds without the item (f) files; it refuses without the item-f configs.
2. **`build_item_f`.** One refusal test per writer condition.
3. **`require_item_f_record` before `build_data`.** Tests: on each refusal, a mocked `load_split` is never called; ISU/SNL runs are unaffected.
4. **`item_f_sha256` in `SCORED.jsonl` rows and the ledger check.** Tests: a row without the hash fails; mismatched hashes fail.
5. **Smoke test.** Synthetic four-arm inner runs → `build_item_f` → report.
6. **Concordance row after scoring.** Descriptive, no consequence: A1/D\* `best_hp` and `cond_scores` of each item-f run against the confirmatory g1 run.

**Designer** (PREREG rev. 11; the change-log row cites D026):
1. 9.9 (r): "after FROZEN, before any Samsung test fold is loaded", plus estimand, location, enforcement.
2. C24 rewritten; met at the freeze by the pinned configs and guard code.
3. Section 15: item (f) moves from step 3 to a new step 3b (after FROZEN, before step 4).
4. Section 16: add the cost line.
5. Section 18: 2b drops the item (f) file and adds the five configs; step 4 adds `item_f_config_paths`; a new 6b orders the steps as item-f runs, then `build_item_f`, then confirmatory runs.
6. 17.4 and section 22 row (f) updated; FB-8 unchanged.

**Re-open if:** the timing run puts the item-f runs above 15 % of the core; an item-f fold cannot finish (the statistics step is blocked); or the concordance row shows a different D\* in more than one fold.
