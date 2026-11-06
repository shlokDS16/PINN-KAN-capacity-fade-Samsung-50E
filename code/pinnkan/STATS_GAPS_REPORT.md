# STATS_GAPS_REPORT: gaps G1-G8 of `code/figures/ALIGN_V4_REPORT.md` section 3, built into the statistics step and the run writer

Status 2026-11-06. Nothing committed. Synthetic data only (no Samsung, ISU, SNL file, retention value or Samsung run output was opened). `runs/prereg/`, `research/`, `paper/`, every config
and `runs/prereg/stats_config.json` untouched; the figure scripts untouched (only `code/figures/README.md` formats updated). CPU only, one thread.

Changed under `code/`: new `pinnkan/stats_gaps.py` (all statistics-step functions), `pinnkan/stats_step.py` (`run_stats_v4` / CLI wiring and `_stats_gaps_v4`), `pinnkan/physval.py`
(`figure_inputs`), `pinnkan/emit.py` and `pinnkan/run.py` (run-writer inputs), new test `tests/test_pk_stats_gaps_g1_g8.py`. Because `code/` moves, the freeze commit (17.4) must be taken after this and the audit
re-shown on it.

## Statistician fixes F1-F6 (research/audits/SIGN_statistician_gaps.md), applied 2026-11-06

* **F1 registered controls.** NC-2, PC-2 and PC-3 (G3) ALWAYS run on the R2 path; `gaps=False` switches off only the descriptive gaps (G1, G2, G4, G6, G7, G8). An exception in G3_nc2 / G3_pc2 / G3_pc3 / G3_controls is recorded in
  controls.json (`{"status": "not evaluated: ERROR ...", "passed": None}`), in `STATS_GAPS_ERRORS.json` and a warning; in a strict run `RegisteredControlError` is then raised after controls.json is written and before
  contrasts_v4_B.json (lenient: recorded and provisional). A control that cannot be evaluated for want of inputs (no `negative_runs`, PC-3 R1 or A1 missing or unequal sets, PC-2 files missing) is listed in
  `contrasts_v4_B.json status.registered_controls_not_evaluated` and sets `status.provisional` and `outcome.provisional` (a label: no tier, state, title, count or margin changes). Descriptive gaps still only warn.
* **F2a PC-2** (`stats_gaps.pc2_v4`): all g4 runs must hold `stress_functions.json` and `storage_hull.json`, otherwise `not evaluated` (no dropped fold, no whole-grid fallback); `n_folds` is in the record.
  **F2b PC-3** (`pc3_v4`): R1 and A1 must score the same g4 conditions, otherwise `not evaluated` (n is never reduced). `NC2_ALPHA = 0.025` is a module constant used by NC-2 and PC-3 (statistician item 1, optional).
* **F3 physval:** `run_stats_v4(physval=True)` by default; `physval=False` is refused in a strict run (ValueError); CLI `--no-physval` (r2) is refused unless `--lenient`; `--physval` stays for v3_legacy.
* **F4:** `contrasts_v4_B.json gate_G.reported_checks` equals controls.json (asserted equal on tripped / reasons / not_evaluated / rule first; `gate_g` untouched; not applied when the caller supplies its own `gate`).
* **F5:** `seed_sd_pp` is the SD over the seeds of the SINGLE-SEED pooled mean (`mean_pp_per_seed`); the ensemble `mean_pp` has no seed replicate of its own (docstring, `definition` of arm_table.json, README). Table 1 must print `mean_pp_per_seed +- seed_sd_pp`, or `mean_pp` with the SD labelled "seed SD of single-seed fits".
* **F6 correction:** `gaps=False` is NOT the old path. G3 (registered controls) and the G5 keys of `physval_11a.json` (`physval.figure_inputs`, called inside `physval_11a`) are produced whatever `gaps` says. The no-regression evidence is
  therefore the comparison with the base commit, now a re-runnable script: `.venv/Scripts/python.exe -P code/tests/head_comparison.py --base 052eefd` (git archive, same synthetic grid and item (f) file, both codes run
  with physval on). Result after F1-F5: `contrasts_v4_B.json` 131143 characters IDENTICAL, `controls.json` IDENTICAL, `physval_11a.json` IDENTICAL, after removing exactly the registered new keys. Re-run it and the whole suite at the candidate frozen commit.
* Tests for each statistician defect: `test_f2b_pc3_with_one_missing_r1_condition...` (the n = 39 case), `test_f2a_pc2_does_not_drop_a_fold_or_fall_back_to_the_whole_grid` (missing `stress_functions.json` in a fold, missing `storage_hull.json`, none anywhere, empty hull),
  `test_f1_*` (strict stops, lenient provisional, missing inputs provisional, `gaps=False` keeps G3, a fold without stress functions in the run), `test_f3_*`, `test_f4_*`, `test_f5_*`.

## Red team rev. 20 code fixes (research/audits/SIGN_redteam_rev20.md), applied 2026-11-06 on HEAD c702e1a

* **M-1** (`stats_step.run_stats_v4`, right after the config pin, n and item (f) / ledger guards, before any store is read): if `strict` and `guard.is_frozen(root)`, `RegisteredControlError` is raised when `row_runs` lacks `lab_indicator`, `retain_all` or `random_subset`, or `h7_run` is absent. The random-subset
  exception needs `random_subset_struck=<id>` and that id as a whole token in `research/DECISIONS.md` of `root` (`_decision_row_exists`). Test `test_m1_*`.
* **M-2:** `stats_gaps.pc2_v4(run_dirs, require)` and `pc3_v4(..., require)`: with `require`, a g4 run without `stress_functions.json` or `storage_hull.json`, an empty hull, R1 or A1 not scored at g4, or R1 and A1 on different conditions
  raise ValueError (a failure to compute). "Not evaluated" is kept only for the data reason (no SOC level with two storage temperatures inside the hull). `_stats_gaps_v4(..., require)`: a missing `negative_runs`
  becomes `errors["G3_nc2"]` and a failed NC-2 record. Tests `test_m2_*`; the F1/F2 tests that expected a label now run with the development default and are kept.
  **Ruling needed (deviation):** `require` defaults to `strict and FROZEN` (`run_stats_v4(require_registered=None)`), not to `strict` alone, as M-1 and M-3 are also FROZEN-gated. With `strict` alone, ~20 existing development tests
  (fake grids with no stress functions, no R1 at g4, no permuted runs) would stop, and the red team's rejection condition is about confirmatory outputs. Before FROZEN the old behaviour stays: a provisional label, now also with
  `status.strict` and `status.head`. Flipping the default to `strict` is one line (`require = bool(strict)`); the tests pass `require_registered=True`.
* **M-3:** (a) `run_stats_v4` refuses `strict=False` on Samsung runs when FROZEN (ValueError). (b) `out["status"]["strict"]` and `["head"]` (git HEAD of `root`, None if unavailable). (c) before `RegisteredControlError` at the stop, `controls.json`
  and `STATS_GAPS_ERRORS.json` are copied to `analysis_dir/stopped_<n>/` with `SHA256.json` (a second stop makes `stopped_2`; the path is in the error message). Tests `test_m3_*`.
* **m-2:** `_inside_hull` raises `ValueError("storage points do not span (T, SOC): PC-2 hull undefined")`; no bounding box (the old test now expects the raise). **m-3:** `pc2_v4` raises if T != [10, 23, 45] or SOC != 0, 5, ..., 100 (`PC2_T_GRID`, `PC2_SOC_GRID`).
  **m-4:** `physval_11a.json arrhenius_ln_rate.soc_selected_in_pc2_evaluation` (per selected SOC: True/False, None without hulls) and `outside_hull_note`; `figures/fig6_storage.py` draws the levels outside the hull dashed, labels them
  "outside hull" and prints "dashed: SOC outside the storage hull, not in PC-2" (the caption must say that PC-2 excludes them). m-1 and m-5 are text only.
* Strip list of `head_comparison.py` / the test: `status.strict`, `status.head` added. Result against 052eefd after these fixes: contrasts_v4_B.json 131143 characters IDENTICAL, controls.json IDENTICAL, physval_11a.json IDENTICAL.

## Red team minors n-2, n-3, n-4 (re-sign of rev. 20), applied 2026-11-06

* **n-2:** `random_subset_struck=<id>` must name a line of `research/DECISIONS.md` that holds the id as a whole token, "9.9 (o)" and "descriptive" (`_decision_row_exists`); otherwise `RegisteredControlError` whenever the parameter is given. When it is valid and no
  random-subset runs are supplied, the row is dropped from `status.rows_not_run`, recorded as `status.rows_struck = {"random_subset": id}` (and `downgrade.rows_struck`), and `outcome.provisional_downgrade_rows_incomplete` follows the remaining rows,
  so the struck row no longer makes the outcome provisional. Test `test_n2_*`.
* **n-3:** `status.require_registered` (effective value) and `status.frozen` are written beside `strict` and `head`. Test `test_n3_*` and `test_n2_*`.
* **n-4:** `stats_gaps.NeedsRescoreError` (a ValueError) marks the input-integrity errors whose cure needs a scored configuration to be run again: NC-2 without A1 at g4, unequal condition sets, other outer folds, and a negative run that is not a
  permute_stress run of Test B; PC-3 with R1 and A1 on different conditions (when required). The control is then recorded in controls.json as `{"passed": False, "failed_needs_rescore": True, "reason", "fail_sentence"}` (`stats_gaps.rescore_record`;
  fixed sentences: NC-2 "stress dependence was not shown necessary for the accuracy", PC-3 the fixed PC-3 sentence with "not shown lower"), listed in `status.registered_controls_failed_needs_rescore`, reported checks follow (PC-3 False), the step
  continues, no `RegisteredControlError`, no provisional label for that reason, no change to any tier or title (compared against a normal run in the test). Any other exception (code / compute error) still stops. PC-2 input absences stay failures to compute
  (they can be cured without a re-score). Tests `test_n4_*`; the F1 / M-3 tests now use a patched `nc2_v4` raising RuntimeError for the stop. Ruling: the PC-3 "R1 or A1 not scored at g4" absence stays a stop (only the unequal-set case is classed as needing a re-score).
* Strip list: `status.require_registered`, `status.frozen`, `status.registered_controls_failed_needs_rescore` added. `head_comparison.py --base 052eefd`: contrasts_v4_B.json 131143 characters, controls.json, physval_11a.json IDENTICAL.

## No-regression rule (how it is held and checked)

* Every new quantity is computed AFTER every confirmatory quantity of `run_stats_v4` is formed and is added under new keys or new files only; `status.provisional` / `outcome.provisional` can only become True through F1.
* Registry of the new or changed-by-design keys (the `strip_*` functions of the test and of `head_comparison.py`): `contrasts_v4_B.json`: `secondary.tests.QT_g1.median_interval`, `candidates_vs_a1`, `stats_gaps`,
  `status.registered_controls_not_evaluated` (+ the provisional flags it sets), `gate_G.reported_checks` values. `controls.json`: `negative.nc2`, `positive.P2_monotone_in_T`, `PC2_detail`, `P3_passed`, `PC3_detail`,
  `P3_A1_beats_R1_median_L`, `gate_G.reported_checks` values (None before), `registered_controls_error`. `physval_11a.json`: `a_of_soc`, `arrhenius_ln_rate`, `partial_dependence_overlays`, `figure_inputs_error`. New files:
  `arm_table.json`, `reference.json`, `law_summary.json`, `residual_map.npz`, `STATS_GAPS_ERRORS.json` (on an error).
* `gate_G.tripped / reasons / not_evaluated / rule` are asserted unchanged (stats_gaps.extend_controls and run_stats_v4); PC-2, PC-3 and NC-2 are not gate inputs.
* Checked: (1) the in-tree test (gaps off against gaps on, both stripped); (2) `head_comparison.py` against 052eefd (above); (3) the whole suite.
* Isolation of the descriptive gaps: an exception or banned sentence in one record goes to `STATS_GAPS_ERRORS.json` with a warning and that record is left out. The run-writer emitters are guarded the same way (a failure leaves the file missing and writes `emit_errors_*.json`; a scored run is never lost).

## Per gap

| gap | function (file:line) | what it writes | test (`tests/test_pk_stats_gaps_g1_g8.py`) |
|---|---|---|---|
| G1 | `stats_gaps.arm_table` (stats_gaps.py:108), `_pool_blocks` (:54) | `analysis/arm_table.json`: `cells["m|k"][arm]`, `test_c[arm]`, `s2[arm]` with `mean_pp, seed_sd_pp, n_conditions, n_params, n_train_used, fit_seconds` (+ `seed_sd_pp_upper_bound, mean_pp_per_seed, n_folds`, ranges) from `metrics.json` | `test_g1_arm_table_pools_the_folds_by_condition_count`, `test_g1_test_c_and_s2_come_from_the_plain_outer_test_block` |
| G2 | `stats_gaps.reference_record` (:118) calling the existing `stats_step.reference_from_runs` | `analysis/reference.json` via the existing `write_reference` (`values.B`, `.C`, `.S2` when the runs wrote `reference_values.json`) | `test_g2_*` (2) |
| G3 NC-2 | `stats_gaps.nc2_v4` (:135), wired in `stats_step._stats_gaps_v4` (stats_step.py:531) and `run_stats_v4(negative_runs=...)` / CLI `--negative-run` | `controls.json negative.nc2`: L_c = ln(S_A1,permuted / S_A1,real) paired at g4 (`Store.from_runs` on the permuted runs, cell (32, full)); `SignRule.test(L, 0)` = the P-chain function (ties and 0 not positive, n not reduced), Beta-binomial rho_s0 from the pinned config, `passed` iff p <= 0.025 (1 + 1e-9), i.e. 30 of 40; plain exact row, median, order-statistic interval, descriptive rows (L(A9/A1) real / permuted, mean scores of A1, A9, R1, R2 real / permuted, None where the permuted runs did not fit the arm; the permuted configs fit A1 only) | `test_nc2_is_the_design_effect_sign_test_30_of_40_at_0p025`, `..._ties_are_not_positive...`, `..._descriptive_rows...`, `..._refuses_unpaired...`, `..._in_the_run_matches_the_hand_computed_test_and_a_wrong_run_is_recorded_not_fatal` |
| G3 PC-2 | `stats_gaps.pc2_v4` (:203) | `positive.P2_monotone_in_T`, `PC2_detail`, `gate_G.reported_checks` in controls.json | `test_pc2_*` (2) |
| G3 PC-3 | `stats_gaps.pc3_v4` (:170) | `positive.P3_passed`, `PC3_detail` (L = ln(S_R1 / S_A1) at g4, margin 0, the same sign test at 0.025) | `test_pc3_is_the_m3_machinery_at_g4_with_margin_zero` |
| G3 gate | `stats_gaps.extend_controls` (:245) | controls copy; gate fields asserted unchanged | `test_the_reported_checks_never_trip_or_clear_the_gate`, `test_the_gate_and_every_tier_state_title_count_and_margin_are_untouched` |
| G4 | run writer: `emit.law_extras` (emit.py:242), `emit.law_forms_header` (:262), `emit.lhs_points` (:215), called in `run.py:530` and written at `run.py:589` as `extracted_law_forms.json`; statistics step: `stats_gaps.law_summary` (:337), `stability_metric` (:310) | `analysis/law_summary.json`: per arm (A15, G15) number of laws, coefficient counts, training-side BIC (median, min, max), stability metric, partial-dependence envelopes of the four non-temperature inputs, closed forms of all laws and a `representative` | `test_g4_*` (5) including the real run writer on a synthetic dataset (A1, A15, G15), real fitted symbolic arms were also checked by hand |
| G5 | `physval.figure_inputs` (physval.py:231), called at the end of `physval_11a` | `physval_11a.json`: `a_of_soc`, `arrhenius_ln_rate`, `partial_dependence_overlays` (written with `--physval`) | `test_g5_physval_carries_a_of_soc_arrhenius_lines_and_overlays_but_no_temperature_curve` |
| G6 | run writer: `emit.residual_cells` (emit.py:269), `run._emit_gap_inputs` (run.py:713); statistics step: `stats_gaps.merge_residual_cells` (:381) | `analysis/residual_map.npz` (same keys as the run writer's map, plus `n_cells_T_SOC`, `n_cells_cch_T`, `n_cells`, `n_outside_*`) | `test_g6_*` (3) |
| G7 | `stats_gaps.qt_interval` (:271) | `contrasts_v4_B.json secondary.tests.QT_g1.median_interval` = a `stats_v4.entry` record (median L, `median_ci` = the unadjusted fallback 95 % order-statistic interval with the design-effect rank, i.e. the interval of `stats_v4._stat` that prints the secondary family's qualifier numbers, relative reduction with interval, n, wins, mean pp with BCa, worst condition) | `test_g7_*` (2) |
| G8 | `stats_gaps.candidates_vs_a1` (:282) | `contrasts_v4_B.json candidates_vs_a1.rows.{A11, A12, A4, A5}` (`stats_v4.entry` records at g4), labelled descriptive and outside every family and the graph, no tier, no p | `test_g8_*` |

## Rulings needed from the statistician (the prereg text does not fix these; the most conservative option was taken)

1. **PC-2 and PC-3 verdicts** are in `gate_G.reported_checks` of controls.json AND contrasts_v4_B.json (F4); the gate rule is unchanged.
2. **PC-2 reading.** Strictly increasing in T between the storage temperatures of the grid (10, 23, 45 C) at every SOC grid level with at least two temperatures inside the convex hull of the training storage cells in
   (T, SOC %); EVERY fold x seed member must pass (the mean curve is reported beside). The hull needs the new run-writer file `storage_hull.json` in every g4 run; without it PC-2 is not evaluated (F2a, no substitute rule). SOC levels
   with fewer than two temperatures inside the hull are excluded and listed. Alternatives: the mean curve only; or the old whole-grid rule.
3. **PC-3 at g4.** Uses the P-chain rule on the ensemble scores of the grid store at (32, full); R1 at g4 is not required by `check_complete`: if it is missing or scores other conditions than A1 the record says `not evaluated`, the reported check stays None and the outcome is provisional (F1, F2b).
4. **NC-2 inputs.** The permuted runs are read through `Store.from_runs` (so they must carry design R2; config `test` must be B, `permute_stress` true) and compared at the cell (32, full) of the real grid. Same condition
   set and same outer folds are required (ValueError otherwise, recorded as a gap error, not fatal). The generated text says "permits" instead of the prereg's "licenses" because the wording check bans the stem "licen*".
5. **G1 definitions.** `mean_pp` = pooled over all scored conditions (fold means weighted by condition counts) of the run's primary endpoint; `seed_sd_pp` = sqrt(sum (w_f sd_f)^2), which assumes independent seed noise across folds
   (the run files hold only the per-fold SD of the seed means, not per-seed fold means); the assumption-free upper bound sum w_f sd_f is written beside it. `n_params`, `n_train_used`, `fit_seconds` (one fit) = mean over the fold runs.
6. **G2.** R_LOO / R_WARP for Table 1 come from the m = 32 runs (full-data training sides), median over folds (the existing `reference_from_runs`); C and S2 added when their runs wrote the file.
7. **G4 stability metric.** Fixed 500-point Latin hypercube in the NORMALISED stress space [-1, 1)^5 (local RandomState, seed 20261106) evaluated by every run's own extracted laws; restricted in the statistics step to the points
   inside the intersection of the five training hulls (Delaunay hull of each fold's unique normalised training cycling stress rows; bounding box if the hull is degenerate, recorded). Metric = median over those points of
   sqrt(mean over seeds of the across-fold variance (ddof 1)) divided by the range over those points of the fold-and-seed mean log-rate (the smaller of the plausible ranges, so the larger metric). A15 pools h = 1 and 2.
   The `representative` law is the one with the median training-side BIC (ties: fold, seed), a training-side rule fixed in advance. The closed forms are the FINAL coefficients after the end-to-end refit (the existing
   `report` / `describe` hold the pre-refit extraction); calendar edges are included; temperature is masked to the fixed label in every record, and no temperature partial-dependence curve is written.
   The family names of the edges appear as data in the closed forms (the prereg prints the law in closed form but names no edge-level form wording): the file passes the banned-wording check; confirm that this is intended.
8. **G5.** A10 overlays are written only while `semi.A10_FORM["verified"]` (as the other A10 comparisons); no temperature curve of A1, A4 or A10 anywhere (permanent rule extended to A4 and A10). A4 overlay = mean over folds of
   the per-fold mean of that fold's A4 seeds; A10 = mean and min / max over folds. physval is on by default for R2 (F3).
9. **G6.** The merged map pools the raw |R| of every fitted A1 member at the scored cycling cells' OWN stress vectors (latent z = 0, as in the existing map; 6 normalised times) from the m = 32 runs; each cell id must occur
   once (ValueError otherwise); the bin value is the median of all raw values in the bin (no median of medians); bins as the run writer's map; an empty bin is NaN (`n_cells_*` counts the cells per bin); storage cells have no
   cyclic residual and are not in it; the training-point overlay is the union over folds. This is a different quantity from the run writer's grid map (model evaluated on a regular grid with the other inputs at their median).
10. **G7 interval type** = the unadjusted fallback 95 % interval of the rule (as `_stat`, used for the qualifier numbers), not the simultaneous Bonferroni interval of the estimated rows.
11. **G8** gives per candidate the same record as an estimated row (no simultaneous interval, no tier) at g4 only.
12. **Run-writer additions are guarded, not fatal** (the statistics step then marks the outcome provisional when PC-2 inputs are missing). They run after scoring; a failure writes `emit_errors_*.json`, leaves the figure input missing and the statistics step then says `not available`.

## Figure readers (not edited)

Already compatible with the new files without edits: Table 1 (`arm_table.json`, `reference.json`), Table 2 (`negative.nc2` keys `k_positive, n, passed`; `reported_checks` PC-2 / PC-3), Fig. 6d (PC-2). To wire later (listed, not trivial):
Fig. 5 (`law_summary.json`, the new `physval_11a.json` keys), Fig. 7 (reads a run directory's `residual_map.npz`; it should read `analysis/residual_map.npz`), Table 2 (`candidates_vs_a1`, `QT_g1.median_interval`).

## Tests

`tests/test_pk_stats_gaps_g1_g8.py`: 50 tests (about 40 s, CPU, one thread). Whole suite, one process per file (after the rev. 20 fixes): 45 files, 868 tests, all pass after n-2 to n-4 (earlier: two files, test_pk_d026_item_f and test_pk_d033_coder, first failed because the M-1 check ran before the pin / ledger guards they test; moved after them and re-run: 37 and 39 passed; the 46 tests of the gap file pass).
