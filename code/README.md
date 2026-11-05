# pinnkan: confirmatory code base (PREREG_v2; extended for the freeze candidate PREREG_v3 in build_v1 section 7)

New package `code/pinnkan/` plus tests `code/tests/test_pk_*.py`. The pilot modules (`code/models/*`, `code/pilots/*`, `code/data/*`) are
imported, never edited: `models.kan_spline`, `models.ageing_models.SolutionNet`, `models.ageing_p45.KANStack`, `pilots.p3_headroom` (A11/A12 learners).
Everything is CPU only (`CUDA_VISIBLE_DEVICES=-1` is forced by the package: an empty value is dropped by Windows and torch then sees the GPU),
one torch thread, `.venv\Scripts\python.exe -P`. Status of the equations and the numbers in `runs/build_v1/RESULT.md`.

## Run

```
cd "C:\Users\Shlok\Downloads\PINN KAN battery paper"
.venv\Scripts\python.exe -P code\run_pinnkan.py --config runs\build_v1\configs\smoke_isu_B0.json [--runs-dir runs]
.venv\Scripts\python.exe -P -m pytest code\tests -q -k pk_          # 74 new tests (115 with the older ones), about 50 s
```
(`python -P -m pinnkan.run` works when `code` is on `PYTHONPATH`.) A config is JSON or YAML; keys and defaults are in `pinnkan/run.py: DEFAULTS`.

| key | meaning |
|---|---|
| `run_id` | folder `runs/<run_id>/`; an existing folder is refused unless `overwrite: true` |
| `dataset` | `samsung`, `isu`, `snl`, `synthetic` (`synthetic: {kind: G0\|G1\|G2, n_cyc_cond, n_sto_cond, reps, seed, test_frac}`) |
| `test`, `fold` | split name (Samsung `B C A S2 S3`; ISU/SNL `B A`) and outer fold |
| `mode` | `inner` (tuning + out-of-fold scores, training conditions only), `timing` (one fit per arm, nothing scored), `confirmatory` (see below) |
| `arms` | list of arm ids (table below) |
| `n_trials`, `inner_k`, `seeds` | tuning budget (prereg 7: 20 or 40 trials x 3 inner folds; Partial plan 10 x 2); final-refit seeds (default 0-4) |
| `backbone` | `constant`, `self_limiting`, `accelerating` or `tournament` (hard-ODE-KAN, simplest within one SE, training conditions only) |
| `window` | `{k_cycling, k_storage, W, shift}`; defaults: Samsung k = 4 / 2 placeholders until [FB-6] counts them, ISU W = 4 weeks, SNL W = 100 cycles; `shift` = -1 / +2 for the secondary windows |
| `steps_scale` | scales the neural step counts (smoke tests only; 1.0 for confirmatory runs) |
| `oracle_throughput` | logged throughput after the window (sensitivity row) |
| `per_cell_factor` | A10 per-cell factor on/off (off = "A10 as published") |
| `retain_all`, `throughput` | keep every check-up regardless of QC flags (sensitivity); `analytic` (default) or `zyk` (ZYK-logged EFC from `data/processed/samsung_zyk_efc.csv`, built by `python -P -m pinnkan.zyk --build` after the download; `ZykDataMissing` while the table or a cycling cell's entries are absent) |
| `target_kind` | derived from `test` (B, C, A: cycling; S2, S3: storage); a contradicting value raises `ConfigError` |
| `permute_stress` | NC-2 (D014, interpretive, NOT gating, Test B only; `ConfigError` for other tests): stress vectors with their design throughput permuted among cycling conditions, separately in training and test; run A1 (A9, R1, R2 optional); scored by `stats_step.nc2` against the real Test B run |
| `nc1_scramble_test` | synthetic confirmatory runs: replace the held-out cells' post-window labels by garbage before scoring (used by `mode: nc1_full`) |
| `mc_seed_root` | fixed at 20261105 (NEGCONTROL_RULING 5.2); every Monte Carlo step uses `SeedSequence([root, crc32(label)])`; in `seeds.json` and the config hash |
| `pinn` | `{clip, warmup, lr}` overrides of the optimiser recipe (D013); `clip` also reaches A2 and A9 |
| `diagnostics` | default true: one refit per gradient-trained arm at its tuned settings, written to `diagnostics.json` (tuned `lam_res` and grid-edge flag, sd of fitted `delta_c` against TAU, clipped-step fraction) |
| `auto_budget` | N and inner folds are fixed from one timing fit per neural arm BEFORE tuning (`budget_rule.json`) |
| `throughput_fallback` | `none` (default) or `analytic`: with `throughput: zyk`, a cycling cell without any ZYK entry then uses the designed throughput (recorded in `meta`); an interval whose segment is missing or has a sampling gap takes the designed throughput in every case (prereg 3.3(4)) |
| `include_at`, `include_storage_0406`, `min_fc_points` | sensitivity rows 9.8(i): AT check-ups join the forecast set; storage cells 04-06 enter as their (two-point) records; scored cells need this many forecast points (training windows unchanged) |
| `law_overrides` | rows (l) and (m): `{tau, Y0, gamma}` for A2 only, `{delta_scope: "total"}` for A1 only (`ConfigError` for other arms); restored after the run |
| `forecast_failure`, `lab_indicator` | rows 9.8(3.3(8)) and 9.8(f): **not built**, `NotBuiltError` with the reason (see RESULT.md section 7) |
| `twins` | `auto` (Test C adds the 35 C calendar twins from the held-out condition identifiers), `train`, `c35` |

**Modes and the guard.** `inner` and `timing` build only the training side (`load_split(..., role="train")`: an outer-test cell or condition is filtered
out before any array is built). `confirmatory` calls `load_split(role="test")`, which calls `guard.require_frozen`: without `runs/prereg/FROZEN` it raises
`TestFoldAccessError` before anything is read, and the scorer calls the same guard again. Order inside a confirmatory run: tune every arm on training
conditions -> `tuning_done.json`, `margins_inputs.json`, `margins.json` -> refit seeds on the full training side -> predict and score the test cells.
Samsung before the freeze is **blinded**: any non-confirmatory request is forced to `timing` (fit seconds and parameter counts only; no score, no
prediction, no retention-derived number under `runs/`; prereg 3.3(9)). Synthetic data have no outer test fold, so `confirmatory` works there (used by the tests).
Confirmatory use of A10 on a real dataset raises `UnverifiedArmError` until `semi.A10_FORM["verified"]` is set after [FB-2].

**FROZEN is a JSON file** (review M2): `{commit, prereg_file, prereg_sha256, splits: {"<ds>:<test>": {file_sha256, fold_hash}}, config_sha256s: [...]}`. `guard.verify_freeze` checks HEAD = commit, tracked files under `code/` and `runs/prereg/` clean, prereg hash; `load_split` checks the split file and fold hash against the pins (and always raises when the stored fold hash differs from the recomputed one, or when a loaded training condition is not listed in the split); a confirmatory run on real data also needs its canonical config hash among `config_sha256s`, `steps_scale = 1`, no `overwrite`, and is recorded in the append-only `runs/prereg/SCORED.jsonl` (a second scoring of the same config is refused; a folder holding `condition_scores.json` is never replaced). `guard.build_freeze_payload` returns the dict for the lead; nothing in the package writes the file. At run start the runner raises `DeviceError` if CUDA is visible.

Run record in `runs/<run_id>/`: `config.json`, `env.json`, `git.json` (commit + dirty-file list), `split.json` (file, sha256, stored vs recomputed fold hash),
`manifest.json` (input files: path, size, sha256), `seeds.json`, `guard.json` (every guard decision), `tuning_<arm>.json`, `tuning_done.json`,
`backbone_tournament.json`, `margins_inputs.json`, `margins.json`, `timings.json`, `metrics.json`, `condition_scores.json`, `predictions.csv`
(phase `inner_oof` or `outer_test`, arm, seed, cell, condition, time, predicted and true retention), `RUN.log`.

## Negative control (runs/prereg/NEGCONTROL_RULING.md, D014)

- **NC-1, gate G (label invariance).** In every confirmatory run, after the final predictions, each fitted arm and seed predicts again from windows rebuilt out of cells whose post-window retention was replaced by garbage
  (`negcontrol.scramble_cells`; with a life level the forecast set is kept and asserted). Predictions must be bit-identical (max |diff| = 0, same forecast times); the result is `invariance.json`; a difference writes `GATE_G_TRIPPED` and raises
  `InvarianceError`. `mode: "nc1_full"` (synthetic only) runs the whole pipeline twice, clean and with scrambled test labels, and compares predictions (inner OOF and outer), `tuning_done.json` and `margins_inputs.json` (`nc1_full.json`): the mandatory pre-freeze run at the candidate commit.
- **NC-2 (interpretive).** `permute_stress` run vs the real Test B run: `L_c = ln(S_A1,permuted / S_A1,real)` paired by condition, exact one-sided sign test at 0.025 (`controls.json: negative.nc2`; descriptive rows beside it). The score-contrast criteria of the draft (A9 - A1, A1 vs R2) and the sign-flip p-value are gone.
- **No use of the forecast-set extent.** `test_no_arm_depends_on_the_extent_of_its_forecast_set` (all 15 arms) shows predictions at a check-up are unchanged (float32 rounding, 1e-6) when later times are cut or added; a static test forbids `t_fc[-1]`, `t_fc.max` etc. in the model modules. (ISU/SNL forecast sets end at the 70 % crossing.)

## Figure inputs and the statistics step (code/figures/README.md formats)

Written by the run writer (`pinnkan/emit.py`, called at the end of every `inner` and `confirmatory` run; a failure is recorded in `emit_errors.json`, not hidden):
`window.csv` (model-visible window check-ups of every scored cell; in `inner` mode of the cells scored out-of-fold), `reference_values.json` (training-side `R_LOO`, `R_WARP`),
and for datasets with a calendar term and the Samsung stress layout (Samsung, synthetic) `stress_functions.json` (calendar E(SOC) in kJ/mol and a(SOC) as pp lost after 500 d at 25 C,
storage rate in pp per 500 d, Arrhenius lines, centred cyclic partial dependences; A1 envelope = min/max over the run's final-refit seeds, A4 and A10 curves when those arms ran),
`residual_map.npz` (median |R| of the A1 residual on bins, training points) and `superposition.csv` (counterfactual calendar share `y(a_cyc = 0) / y(full)` of A1 and A2 at the last check-up,
scored cycling cells; confirmatory runs only). Runs on synthetic data carry a `SYNTHETIC` marker file, which the figure scripts turn into a watermark.
`mode: "h7"` (synthetic only, config `h7: {gens, n_draws, arms, arms_by_gen, n_trials, inner_k, steps_scale, design, shard, resume}`) runs the identifiability driver of `pinnkan/h7.py`: every (generator, draw) unit is written to `draws/<gen>_<draw>.json` when finished, a rerun skips finished units, `shard: [k, n]` shares the 60 units between up to three processes on one run directory (`resume: true`), and the process that completes the set writes `summary.json`, `surfaces_<gen>.npz` and the section-13 `verdicts` (recovery status, structured vs free-G with paired Wilcoxon, G2 validity and gate, G0 KAN vs GAM, positive control P1, hard vs soft on G1, Kendall tau). The batch configs are `runs/build_v1/configs/h7_batch_shard{0,1,2}of3.json` (not run by the builder).

Statistics step (`pinnkan/stats_step.py`, sensitivity rows `pinnkan/stats_ext.py`, 11a `pinnkan/physval.py`, launcher `code/run_pinnkan_stats.py`; `--physval` writes `physval_11a.json`, `--h7-run` supplies the G2 gate of H3 and P1):

```
.venv/Scripts/python.exe -P code/run_pinnkan_stats.py --analysis-dir runs/<x>/analysis --runs B=runs/b_fold0,runs/b_fold1 --runs C=runs/c --runs S2=runs/s2 \
    --runs ISU=runs/isu_fold0 --negative-run runs/neg --h7-run runs/h7 --stress-run runs/b_fold0
```
It reads `condition_scores.json`, `metrics.json` (`inner_cv_pp`) and `config.json` of the fold runs (one directory per outer fold; conditions are merged, comparators are chosen per fold by
the inner-CV score of that fold's training side, never by test error) and writes `contrasts_<test>.json`, `reference.json` (median over folds of the training-side reference values) and
`controls.json` (NC-1 from the `invariance.json` of the real runs, NC-2 from `--negative-run`, one directory per Test B fold). Rule: exact one-sided sign test on `ln(S_comp / S_A1)` (median estimand, order-statistic 95 % interval), tiers S (ln 1.02) and N (-ln 1.10), Holm over {H1a, H1b, H6} by the N-tier p-values,
H1c tested only when all three are tier S (and only for the inner-CV-best of A11/A12), H2 outcome A/C/B/unresolved (PREREG_v2 9.6), Test C Holm-2 (H4a, H4b), S2 one non-inferiority test (H5),
ISU/SNL as Test B on their pool (A4, A5, A7; H1c unadjusted). Beside each tier: mean paired pp difference with a BCa interval and the pp-scale tier of D009 (0.02 E, 0.10 E; E = the comparator's
inner-CV score pooled by test-condition count); `tier_pp_differs` flags a disagreement. A directory without `condition_scores.json` (a training-fold `inner` run) is read from its out-of-fold inner-CV scores and the
output says `source: inner_cv_training_conditions` (not a confirmatory result). P2 from `stress_functions.json`; P1 from the H7 summary (G0).

## Arms (config ids; spaces and dimensions as PREREG_v2 7.1, tested in `test_arm_table_matches_prereg_dimensions`)

| id | what | module |
|---|---|---|
| A1 | PINN-KAN: F + residual, cyclic KAN [d,h,1], calendar KAN [1,2] | `pinn.py` (`PINNArm`) |
| A2 | hard-ODE-KAN, same law, closed-form integration, delta_c by MAP from the window | `hard.py` |
| A3 | PINN with parametric log-linear stress factors (Arrhenius abscissa, log C-rates, log DoD, SOC and SOC^2) | `law.ParamMap` |
| A4 / A5 | PINN with additive GAM (= KAN [d,1]) / GAM + tensor products (T x C_ch, T x SOC_mid, DoD x SOC_mid) | `law.KANMap`, `law.IGAMMap` |
| A7 | PINN with a tanh MLP stress map, parameter count capped at the largest A1 map | `law.MLPMap` |
| A9 | data-only solution network (same z_c, inputs, window inversion; no residual, no law) | `pinn.fit_data_only` |
| A10 | dataset authors' semi-empirical superposition, multi-start least squares + per-cell factor. **PROVISIONAL form** | `semi.py` |
| A11 / A12 | GP-ARD / LightGBM on (stress, window summary, horizon), the P3 learners | `baselines.py` |
| A13 / A14 | A1 on cycling cells only (X1) / storage cells only (exploratory) | `PINNArm` |
| R1 / R2 | persistence / least-squares line through the window | `baselines.py` |
| A6, A8 | A6 dropped (prereg); A8 (free G) is synthetic-only and **not implemented here** (the P4 `FreeFit` exists in `models/ageing_p45.py`) | |

Law (`law.py`): `dy/dt = [r_cal(T, SOC) + r_cyc(s) nu(t)] h(y)`, `y_s = 10 (1 - retention)`, `t_n = days / 500`, `E_n = EFC / 500`; with one backbone `h` per fold
(`constant`, `self_limiting` 1/(1 + y/Y0), `accelerating` exp(gamma y), Y0 = 1, gamma = 0.3) the law integrates in closed form,
`y = Psi^-1(a_cal t_n + a_cyc E_n(t))` (checked against RK4 with piecewise-constant nu). PINN loss, collocation sets (a) record-end or whole axis, (b) Latin-hypercube points in the
training hull, (c) calendar twins, and the causal test-time inversion follow D010 judge section 2.

## Data interface (`data.py`)

`load_split(dataset, test, fold, role)` is the only way to get cells of a real dataset (the whole-dataset loaders are private). Cell = `<serial>_s<stage>`
(Samsung), time since the reference check-up, retention, cumulative EFC (analytic `efc_est_cum` of the pipeline; ZYK-logged is the [FB-5] stub),
condition key identical to the split files. `WindowRule` + `prepare` give the model-visible `WindowCell` (window data, forecast times, a causal throughput curve:
logged inside the window, the window's mean rate afterwards) and keep the forecast labels in `Prepared.fc_true` for the scorer only. Forecast set: later CU/exCU
(ET and AT excluded), cut at the first point below 70 % retention for ISU/SNL. `window_rule_from_counts` implements `k = round(n_med / 3)` (Python rounding: halves go to even).

## Decisions made while building (not in the prereg; the lead should confirm or overrule)

1. One backbone `h` for both terms of a fold (needed for the closed form; the prereg text allows `h_cal` and `h_cyc` separately).
2. Per-cell offset `delta_c` scales the cycling term of a cycling cell and the calendar term of a storage cell (storage cells have no cycling term).
3. Calendar term of a cycling cell uses `(T, SOC_mid)`; calendar twins are `(T, SOC_mid)` of the training cycling conditions (+ the 35 C twins in Test C).
4. Calendar KAN is the same in A3 to A7 (only the cyclic stress map differs between pool arms).
5. Optimiser recipe (D013 (d), accepted): Adam 5e-3 with cosine decay, global gradient-norm clip 20 in **every gradient-trained arm** (A1, A2, A3-A7, A9, A13, A14; `law.GRAD_CLIP`), residual weight ramped 0 -> `lam_res` over the first 40 % of steps in arms with a residual (`law.WARMUP`). Without the clip the PINN fit diverged
   for `lam_res` 0.1 and 1 on a synthetic design (data MSE 1.7 and 34). Both stay configurable: config key `pinn: {clip, warmup, lr}` (clip 0 = off), default = the frozen constants. The clipped-step fraction is logged (`diagnostics.json`).
6. KAN sparsity penalty (L1 + entropy) is computed on parameter magnitudes of each edge, a proxy for the activation-based penalty of Liu et al.
7. A5 pair sets: Samsung the three preregistered pairs; ISU all three pairs (complete second-order GAM); SNL (D013 C2) T x discharge plus each chemistry flag x T and x discharge = 7 pairs, because in every Test B training fold the charge rate is constant and DoD has two levels.
8. ISU forcing: analytic cycles per week with the pilots' 0.5 h rest; the calibration on the 6 `Cycling_json` members (prereg 3.4) is not done.
9. A11 fixes `m = 4`, `tau_log = True`; A12 fixes subsample 0.8, column 0.8 and a monotone constraint on the horizon (`mono=True`: the predicted drop does not decrease with the horizon), so that the tuned dimensions are 3 and 5 as in the prereg table.
10. Stress ranges for the [-1, 1] scaling are fixed physical ranges with a margin (Samsung T 5-50 C, SOC 0-1, DoD 0-0.8, C_ch 0-1.2, C_dch 0-2.2); inputs are clamped inside the spline grid.
11. Incident files of prereg 3.3(4) are dropped by `(serial, file number, kind)` for both stages (the paper does not name the stage; over-drop is possible).

## Stubs and TODO (nothing is guessed)

- **A10 equations** [FB-2]: the form in `semi.py` is the one in `notes/papers/samsung50e_dataset_paper.md` (exponent placement garbled there). Marked PROVISIONAL, refused in confirmatory runs. Open: exponent placement,
  the SOC argument of the calendar term for cycling cells (SOC_mid assumed), published bounds and start values, EOLC and reference values (absorbed by free log-scales). The ISU/SNL analogue is the cyclic term with the stresses the dataset has.
- **Throughput validation** [FB-5]: the ZYK branch is built (`pinnkan/zyk.py`, tested on a synthetic ZYK-format file) but no ZYK file is on disk; `python -P -m pinnkan.zyk --validate` applies the prereg-5 rule once the table exists. Two named assumptions to fix after the first ZYK files are read: the sampling-gap threshold `GAP_FLAG_S` and the DoD classes `DOD_CLASS_EDGES`. Oracle row = `oracle_throughput: true`.
- **Window counts** [FB-6]: `window_rule_from_counts` exists; Samsung k_cyc = 4 and k_sto = 2 in the defaults are placeholders until the member listings are counted.
- **Reference Q0,c** [FB-3]: the loader uses the pipeline's `retention` (ET_T23 if present, else first CU) and renormalises to the first retained check-up.
- **Consecutive-file incident drops** (prereg 3.3(4), second sentence): implemented as `data.INCIDENT_CONSECUTIVE_DROPS` (entries of the prereg text; a key without a cell number matches all cells of the test point); the stage of each named incident file is still not mapped (both stages are matched) [FB-4].
- **H7** (`mode: "h7"`): driver, A8, recovery metric, Kendall tau, the section-13 thresholds, P1 and the G1 hard-versus-soft contrast are built (build_v1 section 7); the 60-unit batch at the pilot tuning effort is a long CPU job (about 6 CPU-h) that the builder did not launch. No rank-correlation threshold for the residual map exists (Fig. 7 carries no claim).
- **Review m1 (left for the lead)**: the pipeline's isolated-outlier QC rule (`code/data/samsung_checkups.py`, prereg 3.3(3)) looks at the next capacity, so whether the last window point survives depends on the first post-window value. Changing it (preceding neighbours only) changes a preregistered rule and a pipeline output; not done here.
- **Review m2**: the forecast-time list of ISU/SNL still ends at the 70 % crossing (it is the scored set); every arm predicts pointwise and `test_m2_forecast_does_not_depend_on_where_the_query_list_ends` pins that predictions at a check-up do not depend on later query times (A8's integration grid does; synthetic only).
- **Review m6**: A11/A12 train on the cells that have enough window and forecast points; the other arms on all cells. `n_train_used` and `n_train_scorable_cells` are in the run record; with the secondary window k-1 all storage cells drop out of A11/A12 (k_sto = 1 gives 2 window points < 3).
- **Statistics**: `stats_step.py` implements the D012 sign-test rule for the contrasts; the type-I simulations stay in `code/prereg/`. BCa intervals use the registered per-contrast streams. H3 (KAN wording against A4/A5, needs the H7 batch for the G2 gate) is assembled; `controls.json` carries `gate_G`.
- Implemented after review: the negative control (D014: NC-1 invariance gate, NC-2 permuted stress; see above), and the secondary metrics R^2, MAPE, error by horizon and RUL error in the outer-test `metrics.json`.
- **Physical validation analyses** of prereg 11a items 1, 2, 4, 5: built in `physval.py`; the comparisons with A10 (items 1(a) and 5) raise `UnverifiedArmError` until `A10_FORM["verified"]`, and 1(b) (published activation energies) is omitted unless the lead supplies sources with a DOI and a location.
- Sensitivity rows implemented: windows (`shift`), oracle throughput, A10 as published, retain-every-check-up, AT included, storage cells 04-06, cells with >= 3 forecast points, clip and warm-up (`pinn`), delta scope total and the A2-only tournament scales (`law_overrides`), margin sensitivities, lab/stage rows, leave-one-lab-out, lab-stratified and two-stage bootstraps (`sensitivity_<test>.json`). Not built (hard errors): lab-indicator rows and the forecast-failure rule.

## Design R2 (build_v2; PREREG_v4, D016-D018). Supersedes the V3 statements above where they differ

Read `runs/build_v2/RESULT.md` and `CHOICES.md` first. The V3 text above (Holm over H1a/H1b/H6, the H1c gate, H2 order, H3, Test C Holm-2, H5, "A8 not implemented", PREREG_v2 references) is history.

| piece | module | notes |
|---|---|---|
| nested max-min training subsets, m in {8, 16, 32}; random variant | `subsets.py`, `data.apply_subset`, config `m`, `subset`, `subset_draw` | identifiers only; `runs/prereg/subsets.json` by `code/prereg/make_subsets.py`; m = 32 is the unthinned side (bit for bit) |
| k = 0 / 2 / k_full windows | `data.WindowRule.for_grid`, `data.grid_ks`, config `k` ("grid" or a list) | k = 0: reference only, design throughput, latents at prior means; R1/R2 not scored at k = 0; tuning at k = 2 (m < 32) or k_full (m = 32) |
| A15 / G15 symbolic laws | `symbolic.py`, `symbolic_library.json`, `arms.SymbolicArm` | one code path; per-edge cap must be set (`symbolic.cap` or the library file), else `CapNotSetError` |
| D* options, A12R, h = 1, selectors | `arms.py` (FEAT, STORAGE, H_GRID), `baselines.py`, `selectors.py` | `comparators.json` written after tuning; A5 only at m = 32 |
| statistics | `stats_v4.py` (+ `stats_step.run_stats_v4`, CLI `--design r2`), `graph_test.py` | sign rule from config (D018: Beta-binomial, rho_s0 = 0.03), graph weight `graph_w`, item (f) guard |
| downgrade rows | `stats_rows.py`; run options `lab_indicator`, `retain_all`, `m` + `subset: random` | `run_v4_full` |
| scope | config `design` ("R2" default, "V3_legacy" history); `arms.ARMS[a].scope`; `stats_step.OutOfScopeError` | A3, A6, A7, A8, A14, H3, the G2 "KAN win", the V3 analysis are refused on the grid / confirmatory path |

Run (grid cell): `{"design": "R2", "m": 8, "k": "grid", "window": {"k_cycling": <k_full>}, "arms": [...]}`; files `condition_scores.json` (k_full cell), `condition_scores_k0.json`, `condition_scores_k2.json`, `comparators.json`, `subsets.json`, `train_condition_meta.json`.
Statistics: `.venv/Scripts/python.exe -P code/run_pinnkan_stats.py --analysis-dir <dir> --runs B=<run dirs of every (fold, m)> --item-f-dir <dir> [--sign-rule '{"graph_w": 0.78}']`.
Tests: `code/tests/test_pk_v2_*.py`.
