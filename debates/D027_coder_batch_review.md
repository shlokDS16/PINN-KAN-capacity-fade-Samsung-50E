# Review of the coder batch (dbabeba C12, d02c54c C13, 580c389 C14), 2026-11-06

Independent reviewer (feature-dev code-reviewer, Sonnet). It had no Bash or write tool; the lead saved its report. Item (1)
was judged from the working tree, not a line-by-line diff.

## Critical
**C1. The 15 Test B grid configs have no `"k": "grid"`, so g1 and the k = 0 cells are never scored** (confidence 90).
`code/prereg/make_confirmatory_configs.py:49-58, 65-67`; `run._score_windows` (run.py:569-587) returns the single legacy window
when `cfg["k"]` is None. Consequences: g1 = (8, 2) never scored (P1, P2, Q-A10 g1, Q-H g1, Q-T g1 cannot be formed); no
`k_labels` in metrics.json; margins fall back to `["full"]` (P1, P2, QA10_g1 margins None); `Store.check_complete` raises under
strict; inversion rows (v), (vi) empty. README:166 and the shake-down configs use `"k": "grid"`. Tests miss it.
Fix: `k="grid"` on the 15 Test B grid configs (item (f) inherits it); Test C, S2, NC-2 keep k None; regenerate + MANIFEST;
test that every Test B grid config has `k == "grid"` and a dry check that `_score_windows` yields {0, 2, "full"}.

## Important
**I1. Confirmatory runs of PREREG 15 / 9.8 / 9.9 without a config** (confidence 80; disclosed by the coder).
`guard.check_config_frozen` refuses an unpinned real-data confirmatory run, and missing downgrade rows make the outcome
`provisional`. Missing: row (ii) lab-indicator (Test B g1, g4 with A10 and D*; Test C), row (iii) retain-every-check-up (g1, g4),
row (iv) random subset (g1, draws 0-2, A1 + D* candidates, 5 folds); Test A, S3; sensitivity rows (windows k_full-1/k_full+2 at
g4, include_at, include_storage_0406, min_fc_points 3, oracle throughput, fixed self_limiting backbone, score_blinded_cells,
law_overrides (l)(m), clip/warm-up (k), A10 without SOC 100 % storage (t)); ISU/SNL replication.
Fix: generate and pin at least (ii)-(iv) before the freeze; generate or explicitly strike the rest.

## Checked, no finding >= 80
validate_config refactor (only error precedence changes; every bad config still refuses, no run dir created); blinding
exclusions (test side only, identical across arms, hash-verified, pinned, n unchanged at 40 / 19); margins (training-side E,
pooled by test-condition count, delta_S = 0.02 E, delta_N = 0.10 E, per (m, k), written before scoring); item (f) configs equal
the g1 config except run_id, mode, arms, diagnostics, refit_timing; common config keys consistent.
