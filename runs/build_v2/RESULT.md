# build_v2 RESULT (Design R2 code; builder session 2026-11-05)

Reading: full text of PREREG_v4 (revision at the start), D016 judge 1-3, 5, 6, D018 judge 0-5, D020 judge 0-2, 6 and Actions; the `code/pinnkan` modules named below. No Samsung retention value, outer score or P6b file was opened. CPU only, no GPU. Python `.venv\Scripts\python.exe -P`.

## Test counts
Full suite at the last commit: **437 passed** (baseline at the start: 268 = 256 build_v1 + 12 graph tests). New test files (`code/tests/test_pk_v2_*.py`, 122 tests): subsets 16, windows 13, symbolic 15, dstar 11, stats 33, rows 15, scope 6, d020 13. Existing tests changed: arm-table dimensions (A11 5, A12 7); NC-2 (30 of 40 by default, plain 27 as the limiting case); V3-analysis tests now run with `design: "V3_legacy"`; the V3 gate test uses `gate_g_v3`; the old "lab_indicator is a hard error" test was replaced by the built row.

## Commits (all end with the Claude Opus 5.5 co-author line)
| item | commit |
|---|---|
| 1 nested subsets (+ random variant, inner-fold rule, `runs/prereg/subsets.json`) | d8df6e2 |
| 2 k = 0 / 2 / k_full paths, grid scoring, per-k NC-1 | 41496ce |
| 3 A15 / G15 symbolic extraction, hashed library | 0a26186 |
| 4 D* feature / storage options, A12R, selectors, h = 1 | 3d7347f |
| 5 statistics step (D018 folded in) | 8f2aac4 |
| 6 downgrade rows, Test C / S2 descriptive | 1e1631f |
| 7 struck pieces out of the confirmatory path | 2c1140b |
| D020 coder rows (ensemble endpoint, inner-fold config, tournament pin) and this file | last commit in `git log` |

## What was built
1. `subsets.py`, `data.apply_subset`, config `m / subset / subset_draw`: max-min order over the fold's 32 training conditions (standardised, nearest-to-centroid start, ties by id, temperature constraint at m = 8), nested prefixes; m = 32 returns the same list (bit for bit, tested); seeded random variant (3 draws). `code/prereg/make_subsets.py` wrote `runs/prereg/subsets.json` from identifiers (sha256 b75384ec...).
2. `data.WindowRule.for_grid`, `grid_ks`, `DesignReopenError` (k_full < 2); k = 0 for every arm (A1/A2/A4/A13/A15/G15 latents and offsets at prior means, A9 z at prior, A10 factor 1, A11/A12 stress + horizon, R1/R2 not scored); config `k: "grid"`; tuning window follows m; per-k predict-stage NC-1; `comparators.json` (D*, AG).
3. `symbolic.py` + `symbolic_library.json` (library sha256 2bb5532e...; cap null), `arms.SymbolicArm` for A15 and G15 (one class), end-to-end refit under the PINN loss, `CapNotSetError`. Tests: each family recovered, G15 == A15 (h = 1, linear outer), untruncated A15 == A1 (map and whole model), noiseless G0 law recovered through KAN fit and extraction.
4. A11/A12 feature set {raw, pinn abscissae + t, EFC raw and log} and storage rows {in, out} as tuned dimensions, A12R descriptive row, `selectors.py` (D*, AG), h = 1 in A1/A2/A13, A5 refused below m = 32.
5. `stats_v4.py`: Beta-binomial sign rule from config (default D018, rho_s0 = 0.03; `SignRuleNotSetError` if unset), primary graph with `graph_w` config (0.5 default; 0.78 tested: counts 30 / 32), reverse-S safety tests, K1 tier S unadjusted, secondary N_i/S_i graph (Q-A10 over two forms), simultaneous 9-cell intervals (rank 8), unadjusted interval (rank 11), ladder, window-information gain, lab rows, dependence sensitivity row with the fixed sentence, GAP-1 d_c test and the e1' switch (off), item (f) estimate and the hash/time guard, state / title / sentence assembly (constants tested as substrings of the D016 text), NC-2 at 30 of 40, `stats_step.run_stats_v4` and CLI `--design r2`.
6. `stats_rows.py`: lab-stratified row (1/3 per lab, within-stratum bootstrap), tier re-computation for rows (ii) lab-and-stage indicator (built into A1/A2/A4/A9/A10/A13/A15/G15 and the D* learners), (iii) retain-every-check-up, (iv) random subset (average of the three draws); `run_v4_full` combines them (lowest tier) and flags missing rows as provisional; Test C / S2 descriptive tables and the Test C abstract rule.
7. `design` config key (R2 default / V3_legacy), `arms.ARMS[a].scope`, `OutOfScopeError`; A3/A6/A7/A8/A14, h7 beyond G0, the V3 analysis and the V3 gate are refused on the Design R2 path; code and history stay.
D020: `metrics.ensemble_rows`, config `endpoint` (ensemble default), `condition_scores_seed*.json`, `Store.seed_view` for K1/K2, per-seed descriptive row; `inner_k_thin` (+ `p6b_decision`); tournament pinned per (fold, m). C3 not implemented. A11 is deterministic; A10 is seed-dependent (multi-start points) and is ensembled; non-finite handling is seed-wise (CHOICES.md, D020 section).

## Open choices (details in CHOICES.md)
Indicator coding (HM, stage 1 reference); where indicators enter A9 (z prior) and A10 (ridge intercept + coefficients); BIC noise floor (1 % of the largest edge range) and G = 101 grid; A15/G15 tuned as the scored arm and refit with 0.5 x steps warm start; random subsets unconstrained; k = 0 throughput = design rate; joiners "whereas" and ", " for the P-/K= and K- sentences; definition of the slot level for reverse-S in the secondary family; the `adopt` key name in the P6b `decision.json`; second A10 form = arm id A10P.

## Blocks the freeze (code side)
1. **[ARCH: cap]** is unset: no A15/G15 run (including the FB-9 NC-1 full-pipeline run on the grid paths, which needs A15/G15 in the arm list) can start until the method-architect fills `max_coeffs_per_edge` in `code/pinnkan/symbolic_library.json`. The library hash (rule) is 2bb5532e...; pin the file hash and the cap value.
2. **A10 equations unverified (FB-2):** `semi.A10_FORM["verified"]` is False; A10, A10P and every contrast that uses them are refused on real data.
3. **Item (f) file** must be produced from Samsung training sides (`stats_v4.item_f_from_runs` after the inner-mode runs exist) and hashed with `write_item_f` before any outer score; the statistics step refuses otherwise.
4. FB-8 timing, FB-9 `nc1_full` at the candidate commit (k = 0/2, m in {8, 32}, A15/G15; needs the cap), FB-10 smoke re-run and the data-side blockers FB-3/4/5/6 are untouched by this build.
5. The e1' decision (D018 A6) is a config switch (`e1_prime_approved`), off by default.
6. P6b: the code reads `decision.json` only if `inner_k_thin: 4` is requested and expects a boolean `adopt` (assumed key).

## Not built / deviations
- Optional GRU member of D* (J16 drop order 3): not built; needs a change-log row striking it.
- `margins.json` per contrast and grid cell (pp-scale descriptive row): the run still writes the inner-CV E at the tuning k only.
- Figure inputs for Fig. 4 / Fig. 5 (`emit.py`), the stability metric and per-input family-label table (11a item 6), the blinding-exclusion list in the scorer (3.3(11)), `guard.build_freeze_payload` additions (subsets.json, blinding_exclusions.json, library hash, stats_sim files) and `PREREG_DEFAULT`: not touched (the guard was left intact as instructed).
- Rows (ii) and (iv) and the Samsung grid are re-run configs; their CPU cost is the lead's to schedule (PREREG 16, J16 6). The ISU fallback grid (`W` in {0, 2, 4}) is supported by `for_grid` for time windows but not exercised on real ISU files.

## Review fixes (CODE_REVIEW.md: 0 critical, 7 important, 9 minor)
Suite after the fixes: **464 passed, 0 failed** (run as one pytest process per test file; `test_pk_v2_review.py` has 17 tests, one or more per finding). `symbolic_library.json`, `semi.py` and the A10 code were not touched.

| finding | fix | commit |
|---|---|---|
| I1 [W] of the T9 clause | taken only from the A10 forms that are reverse S | b5df90b |
| I2 "most" under rows | d_c test recomputed in rows (ii)-(iv) and the lab-stratified row (binary, 0.025) | 6134369, ed4d123 |
| I3 chain K silently struck | `ChainKMissingError` unless `k_chain_struck` is set; initial levels reported correctly | dea1f65 |
| I4 `symbolic` config | in DEFAULTS, hashed, passed to the arm; refuses to start if `cap` disagrees with `symbolic_library.json`; unknown keys refused. Ruling (a): A15/G15 parent + refit steps = one A1 fit (`refit_frac` default 0.4) | ca6a4bb |
| I6, M9 silent missing inputs | `Store.check_complete` (5 folds, all (m, k) cells, n = 40, required arms, D*/AG complete, both A10 forms), design and legacy-marker checks, per-seed files all or none | 8275d17 |
| I5, M5 routing, provisional, pin | `run_stats_v4` and the CLI call `run_v4_full`; rows via `--row`; gate G from NC-1 and PC-1 (unseen = not evaluated); `status.provisional`; item (f) hash pinnable; `inner_folds.json` | 9dc0bf8 |
| I7 rule 1 | `mean_vs_median` with `outcome.abstract_additions` | eb38a61 |
| M1, M2, M3, M4, M6, M7 | fit-only timing; p6b hash in the hashed config and pinned-subsets check; counted window required; `auto_budget` refused on real confirmatory runs and A15/G15 in the Partial trigger; `nc1_full` per k; A9 latent forced at k = 0 (one commit, 1b13406) | 1b13406 |
| M8 | left to the A10 verification agent | - |

Lead rulings recorded in CHOICES.md: (a) matched budget; (b) random subsets unconstrained, with the reviewer's justification; (c) GRU struck; (d) cap/library agreement.
Still open on the code side: the freeze payload (`guard.build_freeze_payload`) does not yet list `subsets.json`, the library file hash or the item (f) hash (guard left untouched); GRU strike needs the change-log row in PREREG_v4.

## D022a: calibrated extraction audit (2026-11-05)
Rule v2 committed first (c4ee1fb), then code. Audit: PD-based labels (retained, strict win / tie, numerical additivity on a 5 x 5 lattice, sign with magnitude and tie rules, "not retained" label, extraction-loss flag against the arm's own parent, tie-share column, BIC margin only as an appendix field), exactly 25 laws per arm at g4 (error otherwise), one label function for A15 and G15, unknown arm or missing h an error. Calibration: whole synthetic datasets (D = 30, strata rotation, 10 interaction datasets, amplitudes 0.05-0.5, laboratory aliasing, hyperparameter draws, 1500 fits), dataset-level false-statement scoring, C1 / C2 / C3 with the Clopper-Pearson arithmetic of the judge (D = 30: <= 2 false datasets; D = 22: <= 1), D >= 22 enforced, de-duplication, torn-line tolerance, CPU cap 36 h, bit-identical re-run of 3 hash-chosen datasets. Guards: `verify_freeze(untracked_under)`, mandatory pins and the FROZEN-commit match in the stats step, calendar wording refused, label functions reachable only from `edge_level_wording` (AST test). Not run: the calibration (after FROZEN). Details and my readings: CHOICES.md "D022a".


## D033 coder batch (2026-11-06; supersedes the defaults stated in sections 25 and 38 above)
The lines above that say `graph_w` "0.5 default" and the e1-prime switch "off by default" are history. Since D033 (F1/D1) `stats_v4.DEFAULT_CONFIG` is the registered configuration: graph weight `gt.W_ALT` = 0.78 (levels 0.0195 / 0.0055, counts 30 / 32), clause e1-prime on (approved, D019), Beta-binomial rho_s0 = 0.03, alpha 0.025, chain K not struck. The same values are pinned in `runs/prereg/stats_config.json` (`guard.PIN_FILES["stats_config"]`); once FROZEN exists `run_stats_v4` uses that file and refuses a differing `cfg` or `--sign-rule`; `contrasts_v4_B.json` records the config, its hash and the file hash. Ties with a margin are not positive and n is not reduced (D2). Details: `runs/prereg/CODER_D033_REPORT.md`.
