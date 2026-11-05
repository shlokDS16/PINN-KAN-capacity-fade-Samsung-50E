# D026 proposal (lead, 2026-11-05 22:30): item (f) cannot be produced before the freeze under retention blinding

## The defect (found by the lead while scheduling the freeze compute; no ruling exists on it)
- Item (f) (PREREG_v4 9.9 (r), D18 A4, freeze condition C24) estimates the intra-fold and intra-lab sign correlation from the
  **inner-CV training-side condition scores of the Samsung outer-fold runs** (`stats_v4.item_f_from_runs` reads `tuning_done.json`).
- Retention blinding (prereg 3.3(9); `run.py` line 263-297): before a valid FROZEN, every Samsung run except `timing` and
  `confirmatory` is forced to `timing`, so no `tuning_done.json` with scores can exist before the freeze; `confirmatory` needs FROZEN.
- `guard.PIN_FILES` lists `item_f` and `item_f_record` (`runs/prereg/item_f_dependence*.json`), and the freeze is built with
  `build_freeze_payload(..., require_pins=True)`, so the freeze as now coded needs a file that blinding forbids. C24 cannot be met.
- Inside one confirmatory run, tuning (inner scores) and outer scoring happen in the same process, so "hashed before any outer
  score" cannot be met by running confirmatory runs either.
- Item (f) has no consequence for any count or tier (9.9 (r): "Nothing changes the critical counts after the freeze"); it only
  triggers a fixed Limitations sentence if the intra-fold point estimate exceeds 0.03.

## Options
- **O1 separate inner runs after FROZEN.** Run `inner` mode on the Samsung training sides of all outer folds (allowed once the freeze
  is valid), compute and hash item (f), then start the confirmatory runs. Cost: the tuning of A1 and the D* candidates is done twice
  (tuning is most of the 3N + 5 fits per arm and fold), roughly +30-40 % of core compute (lead arithmetic, not measured).
- **O2 two-phase confirmatory run (recommended).** A CLI flag (not in the config hash) `--phase tune` stops each confirmatory run after
  `tuning_done.json`, `inner_folds.json`, `margins_inputs.json` and `comparators.json` are written (no refit, no prediction, no test
  cell loaded: `load_split(role="test")` is not called in this phase). After all folds are tuned, the lead computes item (f) from those
  files and writes it with `write_item_f` to `runs/item_f/` (untracked, outside `runs/prereg/`, so the frozen tree stays clean).
  `--phase score` then resumes the same run directory: it verifies that `tuning_done.json` is unchanged (sha256 recorded at the end of
  phase 1) and that the item (f) record exists and is older than now, then refits, predicts and scores. No duplicated compute.
  Code: `item_f` and `item_f_record` leave the required freeze pins; the stats step keeps `require_item_f` (hash + mtime order +
  `written_unix` before the first outer score) and adds the phase-1 tuning hashes to its check. The SCORED.jsonl rule is unchanged.
- **O3 post-hoc.** Compute item (f) after scoring from the same files, disclosed as post hoc. Breaks D18 A4's "before any outer
  score"; weakest.
- **O4 ISU instead of Samsung.** Unblinded, available now, but a different dataset and estimand than D18 named.

## Recommendation
O2, plus a guard test that phase `tune` never calls `load_split(role="test")` and never writes `condition_scores*`, a test that
`--phase score` refuses when `tuning_done.json` changed or the item (f) record is missing, and a PREREG change-log row (rev. 11)
that rewrites C24 and 9.9 (r) to "after FROZEN, between the tuning phase and the scoring phase".
Applies also to FB-8: the timing run is unaffected (timing mode is allowed before the freeze).
