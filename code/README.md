# pinnkan: confirmatory code base (PREREG_v2)

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
| `retain_all`, `throughput` | keep every check-up regardless of QC flags (sensitivity); `analytic` (default) or `zyk` ([FB-5] stub) |
| `target_kind` | derived from `test` (B, C, A: cycling; S2, S3: storage); a contradicting value raises `ConfigError` |
| `permute_stress` | negative control (prereg 10): stress vectors with their design throughput permuted among cycling conditions, separately in the training and the test set; run A1, A9, R2; `metrics.json` gets `negative_control` with the acceptance checks |
| `pinn` | `{clip, warmup, lr}` overrides of the optimiser recipe (D013); `clip` also reaches A2 and A9 |
| `diagnostics` | default true: one refit per gradient-trained arm at its tuned settings, written to `diagnostics.json` (tuned `lam_res` and grid-edge flag, sd of fitted `delta_c` against TAU, clipped-step fraction) |
| `auto_budget` | N and inner folds are fixed from one timing fit per neural arm BEFORE tuning (`budget_rule.json`) |
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
- **Throughput validation** [FB-5]: `throughput="zyk"` raises `NotImplementedError` (no ZYK-logged EFC on disk). Oracle row = `oracle_throughput: true`.
- **Window counts** [FB-6]: `window_rule_from_counts` exists; Samsung k_cyc = 4 and k_sto = 2 in the defaults are placeholders until the member listings are counted.
- **Reference Q0,c** [FB-3]: the loader uses the pipeline's `retention` (ET_T23 if present, else first CU) and renormalises to the first retained check-up.
- **Consecutive-file incident drops** (prereg 3.3(4), second sentence) and the stage mapping of each named incident file [FB-4]: not implemented (`INCIDENT_CONSECUTIVE_DROPS_IMPLEMENTED = False`).
- **A8** (free G) for the synthetic H7 figure, the G1 hard-versus-soft batch, the Kendall-tau / variance-importance metrics and the 240-fit synthetic driver: the generator, the recovery metric (nRMSE on a hull sample) and the arms A1, A2, A4 exist; the batch driver does not.
- **Review m1 (left for the lead)**: the pipeline's isolated-outlier QC rule (`code/data/samsung_checkups.py`, prereg 3.3(3)) looks at the next capacity, so whether the last window point survives depends on the first post-window value. Changing it (preceding neighbours only) changes a preregistered rule and a pipeline output; not done here.
- **Review m2**: the forecast-time list of ISU/SNL still ends at the 70 % crossing (it is the scored set); every arm predicts pointwise and `test_m2_forecast_does_not_depend_on_where_the_query_list_ends` pins that predictions at a check-up do not depend on later query times (A8's integration grid does; synthetic only).
- **Review m6**: A11/A12 train on the cells that have enough window and forecast points; the other arms on all cells. `n_train_used` and `n_train_scorable_cells` are in the run record; with the secondary window k-1 all storage cells drop out of A11/A12 (k_sto = 1 gives 2 window points < 3).
- **Statistics** (sign-flip test, BCa, Holm, TOST) belong to `code/prereg/stats_rule.py`; `margins.py` only prepares the margin inputs.
- Implemented after review: the negative control (`permute_stress`, with the acceptance checks of prereg 10; the sign-flip p uses a placeholder RNG seed), and the secondary metrics R^2, MAPE, error by horizon and RUL error in the outer-test `metrics.json`.
- **Physical validation analyses** of prereg 11a (activation energy, SOC slope, superposition check) and the figure scripts are not part of this build.
- Sensitivity rows implemented as options: windows (`shift`), oracle throughput, A10 as published, retain-every-check-up. Not implemented: lab-indicator rows, AT-included (`include_at` exists in `load_split`), forecast-failure rule, lab-stratified bootstraps.
