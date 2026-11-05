# D026 code review of f7edd5b (independent, read-only)

Reviewer: feature-dev code-reviewer agent (Sonnet), 2026-11-05. It had no write tool; the lead saved its report verbatim
in substance. Only findings with confidence >= 80 are listed. Counts: 0 critical, 1 important, 4 minor.

## Verified OK
- Gate order: `guard.require_item_f_record` (run.py:257-258) runs after `require_frozen` and `check_config_frozen`,
  before the run folder (264) and before `build_data` (316); `role="test"` only for `mode == "confirmatory"`.
- Dataset scope: Samsung only; ISU, SNL and synthetic untouched.
- Pre-freeze Samsung inner requests are downgraded to timing; the writer refuses runs whose `mode_effective` is not `inner`.
- SYNTHETIC exemption is an exact file-name match in one directory; only synthetic and demo code writes the marker.
- Pins: `build_freeze_payload(require_pins=True)` refuses missing, fewer or duplicate item (f) configs; `pins_missing`
  refused by `verify_freeze`.
- Ledger: Samsung rows without `item_f_sha256` refused; `require_item_f` fails on missing, mixed, mismatched hashes and on
  zero Samsung rows; `run_stats_v4` cannot skip the ledger check once FROZEN exists.

## Important
- **I1** `data.load_split(role="test")` was not gated by item (f); only run.py was. Any other post-FROZEN caller could load
  Samsung test cells with no record and no trace. Fix: gate inside `load_split` for Samsung, pass `runs_dir` through.

## Minor
- **m1** The SYNTHETIC marker overrode a Samsung `config.json`. Fix: exempt only a synthetic config or the
  `runs/figdemo_SYNTHETIC/` tree, and only with the marker.
- **m2** Ledger rows without `dataset`: writer failed closed, statistics step failed open; `record_scoring(dataset=None)`
  skipped the hash requirement. Fix: treat None as Samsung in `require_item_f`; refuse `dataset=None` when recording.
- **m3** `GUARD_LOG.clear()` erased the "item (f) record verified" entry from `guard.json`. Fix: re-append after the clear.
- **m4** `verify_freeze` accepted a pinned FROZEN with no `item_f_config_sha256s` (found only at `build_item_f`). Fix:
  a FROZEN with `pins` must list five distinct item (f) config hashes.

## Notes below threshold
- `build_item_f` does not compare each run's `git.json` commit with FROZEN (relies on `mode_effective == "inner"`).
- `write_item_f` stays public; the scorer does not check `rec["cell"]` / `rec["contrast"]`.
- Case-sensitive `os.path.dirname(d) != runs_dir` on Windows: spurious refusal possible (fail closed).

## Lead fixes (2026-11-05 23:10)
All five applied: data.py (gate + `runs_dir`), run.py (`build_data(..., runs_dir)`, log re-append), stats_v4.py (m1, m2),
guard.py (m2, m4). Tests: `code/tests/test_pk_d026_review.py` (7); two D026 tests updated (legacy row written directly;
figure-demo path name; new build_data call string); pin fixture lists five item (f) hashes.
