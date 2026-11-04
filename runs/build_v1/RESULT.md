# build_v1: confirmatory code base (2026-11-05)

Code: `code/pinnkan/` (package), `code/run_pinnkan.py` (launcher), `code/tests/test_pk_*.py`, `code/README.md` (how to run each arm). Commits "build:" 
aa9ac59, 281ce50, bc7f3c9 and the closing one. Nothing in this file shows Samsung retention. No outer test fold of any real dataset was built or scored; the flag
file `runs/prereg/FROZEN` was never created.
reading: of the sources, PREREG_v2 and CONTRACT in full; D010 judge section 2 and D011 judge sections 0 to 3 (arms, A10, Test C); the pilot modules named in the brief;
`samsung_pipeline/RESULT.md` in full; the dataset-paper note (`notes/papers/samsung50e_dataset_paper.md`, lines 60-160). Stroebl JES 142, 119552 was not available.

## 1. Tests

`.venv\Scripts\python.exe -P -m pytest code\tests -q`: **115 passed** in 49 s (74 new in `test_pk_*.py`, 41 older including the 19 pipeline tests). Single thread, CPU only.

| file | what is pinned |
|---|---|
| `test_pk_guard_data.py` (18) | guard raises without the flag and passes with it (temporary root); `load_split(role="train")` never returns a test cell or test condition (mini ISU root, real ISU and SNL folds 0-1, real Samsung B/C/S2 folds); `role="test"` raises for ISU, SNL, Samsung B/C/S2; stored fold hash equals the recomputed one; Samsung condition keys equal the split identifiers; EFC curve and causal tail; window count rule, forecast set (CU/exCU only, 70 % truncation), unscorable cells dropped; `k = round(n_med/3)` example |
| `test_pk_models.py` (42) | closed form equals RK4 for the three backbones with a piecewise-constant throughput rate; stress maps (KAN, GAM, interaction GAM, parametric, MLP cap, polynomial) incl. the spline-edge input; storage cells carry no cycling term and `delta_c` gates correctly; residual equals the analytic derivative; hard initial condition; collocation sets (record-end versus whole axis, hull, twins at nu = 0, extra 35 C twins); generator levels and reproducibility; **G2 is not additive and G0 is** (additive-floor ratio > 3); **hard-ODE recovers the G0 log-rate surface, nRMSE <= 0.15 (prereg P1 line) and beats persistence by > 65 %**; **a held-out cell's forecast does not change when its forecast labels change**; PINN fit and A9 run; **A10 parameter recovery on data from its own form (cost < 1e-7, relative parameter error < 5 %)**, per-cell factor removes a 30 % scale error, A10 refused for confirmatory use; R1, R2, A11, A12; arm table dimensions equal the prereg (A1 6, A2 4, A3 3, A4 4, A5 5, A7 5, A9 4, A10 0, A11 3, A12 5, A13 6, A14 4); every arm fits and predicts |
| `test_pk_tuning_run.py` (14) | inner folds grouped by condition, stratified by temperature, deterministic, replicates share a fold, storage never partitioned; budget rule (N 40 / 20, Partial plan 10 x 2); margins pooled by test-condition count; metrics (condition-then-cell averaging, non-finite scored with persistence, R2 argument order, log ratio); tuning uses training cells only and is deterministic, TPE seed = outer fold; backbone tournament picks the simplest within one SE; run record files; **confirmatory writes tuning_done, margins_inputs, margins before any test score**; **confirmatory on ISU, SNL, Samsung is refused before the freeze**; ISU training-fold run never touches test cells; **Samsung run is blinded** (forced to timing, no predictions, no tuning file) |

Two defects the tests caught and I fixed: (i) a confirmatory request on Samsung before the freeze was being downgraded to the blinded timing mode instead of reaching the guard;
(ii) `CUDA_VISIBLE_DEVICES=""` is dropped by Windows, so torch saw the GPU: the package now forces `-1` (the run record stores `cuda_available`).
One defect found by running: the PINN fit diverged for `lam_res` 0.1 and 1 on a synthetic design (data MSE 1.7 and 34, forecasts 14 and 64 pp); a global gradient-norm clip of 20 plus a 40 % residual warm-up
made all five grid values train (forecast 0.7 to 3.5 pp, G0). Both are in the code and frozen by the commit.

## 2. Smoke runs (all CPU, 1 thread, one or two processes, under 1 GB each)

Run folders in `runs/` (each has config, env, git, split, manifest, seeds, guard, timings, metrics; configs in `runs/build_v1/configs/`, logs `runs/build_v1/*.log`).
They were made at commit 281ce50; `git.json` of each lists the uncommitted additions of that moment (the optional arms A6 and A8, which no other arm uses). Re-run at the freeze.

| run | data | what it checks |
|---|---|---|
| `build_v1_timing_synth_samsung_size` | synthetic G0, 32 + 19 conditions, 97 training cells | one full-step fit per arm: timing for [FB-8]-style planning |
| `build_v1_timing_samsung_B0_blinded` | real Samsung, Test B fold 0, **training side only, 17 cells** (16 cycling, 1 storage; the download is partial) | loader + guard + every arm run on the real layout; blinded: timing and parameter counts only |
| `build_v1_timing_samsung_C_blinded` | same, Test C (13 cycling cells), 35 C twins from identifiers | Test C plumbing |
| `build_v1_smoke_isu_B0`, `build_v1_smoke_snl_B0` | ISU fold 0 (203 train cells), SNL fold 0 (52) | tuning + inner-CV on training conditions, 2 trials x 2 inner folds, 30 % steps: plumbing only, the inner-CV values are not results |
| `build_v1_synth_g0_confirmatory_smoke` | synthetic G0, 91 train cells, 8 held-out conditions | end-to-end confirmatory path (tournament, tuning, margins files, 3 seeds, scoring), 3 trials x 2 folds, 50 % steps |

### Fit time per arm, one fit at full step counts (seconds)

| arm | synthetic Samsung-size (97 cells) | parameters (without per-cell latents) | real Samsung, 17 train cells |
|---|---|---|---|
| A1 PINN-KAN | 14.5 | 2669 | 13.2 |
| A2 hard-ODE-KAN | 2.5 | 236 | 2.1 |
| A3 parametric | 9.4 | 2459 | 8.4 |
| A4 additive GAM | 10.6 | 2523 | 9.6 |
| A5 interaction GAM | 14.5 | 2715 | 13.7 |
| A7 MLP map | 9.9 | 2838 | 9.5 |
| A9 data-only F | 2.7 | 8961 | 1.4 |
| A10 semi-empirical (8 starts) | 2.9 | 11 | 0.5 |
| A11 GP-ARD / A12 LightGBM | 2.2 / 0.0 | - | 0.0 / 0.0 |
| A13 / A14 | 13.4 / 6.1 | 2669 | 12.4 / 5.8 |
| R1, R2 | 0.0 | - | 0.0 |

A PINN fit costs a fixed number of collocation steps, so time hardly depends on the number of cells (17 versus 97 cells: 13.2 versus 14.5 s). On this machine, with other jobs running,
the hard-ODE median is far under 30 s, the PINN under 90 s and every neural arm under 20 s, which is the prereg's condition for **N = 40** (`tuning.choose_budget`). That is an indication from a
synthetic design of Samsung size, not the [FB-8] measurement: the real one needs the complete download. Tuning fits are on 2/3 of the cells with other hyper-parameters (grid 30, width 128), so
the median tuning fit differs from the table (synthetic confirmatory smoke at 50 % steps: A1 6.6 s, A2 1.2 s, A4 5.1 s, A8 13.9 s, A9 1.7 s).

Projected cost of Samsung Test B (arithmetic from the table, not a measured full run): at N = 40 and 3 inner folds a tuned arm needs 125 fits. Six PINN-type arms (A1, A3, A4, A5, A7, A13) at 10 to 15 s,
plus A9 (2.7 s) and A2 (2.5 s), come to 2.3 to 3.3 CPU-h per outer fold, 11 to 17 CPU-h for five folds (about 4 to 6 h on three processes). The prereg's Test B entry is 18.1 CPU-h expected at N = 40, so the measurement agrees with it.

### Synthetic confirmatory smoke (G0, held-out conditions, not a result of the study)

Primary endpoint on 8 held-out synthetic conditions, mean of 3 seeds (seed SD of the cross-condition mean): R1 11.81, R2 10.03, A9 2.59 (0.13), A10 1.58, A12 1.19, A1 1.14 (0.08),
A8 0.95 (0.07), A4 0.90 (0.04), A2 0.81 (0.01) pp. The pipeline separates the structured arms from the references and from the data-only network, and the hard ODE, whose law equals the generator's, is best. The PINN-KAN
is worse than the hard ODE here at half the training steps and 3 trials; it was not tuned to the point of a comparison. Files: `runs/build_v1_synth_g0_confirmatory_smoke/` (`metrics.json`, `condition_scores.json`, `margins.json`).

## 3. What exists and what is stubbed

Built: common data interface for Samsung, ISU, SNL with window and forecast-set rules, causal throughput, stage-aware cell key, incident drops at file level, split hash check, test-fold guard in loader, run script and scorer;
PINN-KAN (A1, A13, A14) and the pool A3, A4, A5, A7 (A6 optional), A2 hard ODE, A9 data-only F, A10, A11, A12, R1, R2, A8 (synthetic); synthetic generators G0, G1, G2; nested tuning (TPE, grouped and temperature-stratified inner folds,
budget rule, backbone tournament); margins inputs; run writer (config, env, git commit and dirty files, seeds, split and manifest hashes, per-cell predictions, metrics, timings, guard log); Samsung blinding.

Stubs and open items (details in `code/README.md`):
1. **A10 equations** [FB-2]: provisional form from the dataset-paper note; refused for confirmatory use (`UnverifiedArmError`). Open: exponent placement, SOC argument of the calendar term for cycling cells, published bounds, EOLC.
2. ZYK-logged throughput [FB-5] (`throughput="zyk"` raises `NotImplementedError`); the analytic EFC of the pipeline is used.
3. Window counts [FB-6]: Samsung k_cyc = 4, k_sto = 2 are placeholders; `window_rule_from_counts` is ready.
4. Reference Q0,c [FB-3] and consecutive-file incident drops, stage mapping of incident files [FB-4].
5. Not built: the 240-fit synthetic H7 batch driver, Kendall-tau importance, the G1 hard-versus-soft batch; physical-validation analyses (11a); lab-indicator, AT-included and forecast-failure sensitivity rows; figure scripts; the sign-flip / BCa / Holm / TOST tests (`code/prereg/stats_rule.py`, the other agent).
6. Choices made without a prereg line, for the lead to confirm (README, "Decisions made while building"): one backbone for both terms; `delta_c` on the calendar term of storage cells; calendar KAN identical across pool arms; ISU and SNL interaction pairs; KAN sparsity as a parameter-magnitude proxy; ISU forcing without calibration; fixed A11/A12 sub-settings.
7. Python `round` sends halves to even in `k = round(n_med/3)` (3.5 -> 4); say if the freeze wants half-up.

## 4. Review fixes (2026-11-05; `CODE_REVIEW.md` M1-M4, m2-m8, D013 C1-C4 and C7)

Tests: `code/tests/test_pk_review_fixes.py` (42 new tests, one or more per fix). Full suite: **155 passed, 2 failed**. The two failures are `test_samsung_checkups.py::test_probed_file_capacity_matches_probe` (older pipeline tests): `_find(name)` now meets two same-named
CU files after the stage-aware fetch (stage 1 and stage 2 have the same zip names) and reads the other cell; they import no `pinnkan` code and need the pipeline owner to key the probe by `<serial>__f<id>`. No `FROZEN` and no `SCORED.jsonl` was created.

| id | fix | test |
|---|---|---|
| M1 | stored vs recomputed fold hash now raises `SplitIntegrityError`; split file sha256 and fold hash are compared with the values pinned in FROZEN (also for the training role; a missing pin after the freeze fails closed); every loaded training condition must be listed in the split (`train_cycling_conditions` / `train_conditions`), conditions listed but absent are reported as `missing_train_conditions` and block a confirmatory run | `test_m1_*` (4) |
| M2 | FROZEN is JSON (commit, prereg sha256, split pins, config hashes) and `verify_freeze` checks HEAD, a clean tracked tree under `code/` and `runs/prereg/`, the prereg hash; confirmatory real-data runs need a pinned config hash, `steps_scale = 1`, no `overwrite`, and are written to the append-only `SCORED.jsonl` (a second scoring of a config is refused); a folder with `condition_scores.json` is never replaced; Samsung un-blinds only on a valid freeze; `guard.build_freeze_payload` returns the dict for the lead and writes nothing | `test_m2_*` (5) |
| M3 | `target_kind` derived from the test name (S2, S3 -> storage), contradiction raises `ConfigError`; inner folds and the CV assert that the partitioned kind is the scored kind; test cells of another kind raise | `test_m3_*` (2) |
| M4 | `permute_stress` negative control (separate permutations of train and test stress vectors, no fixed points, design throughput recomputed, windows and forecasts untouched) with the acceptance checks of prereg 10 in `metrics.json`; R2, MAPE, error by horizon and RUL error are written for the outer test | `test_m4_*` (4) |
| m1 | **not fixed**: the QC outlier rule is a preregistered rule (3.3(3)) in the pipeline module; documented in the README, left for the lead | - |
| m2 | forecast-time list encodes the 70 % crossing: invariance test that every arm predicts a check-up identically whatever later times are queried (A8's grid excepted, synthetic only) | `test_m2_*` (8) |
| m3 | one reference rule for all cells (ET only if ET exists for every analysed cell, else first CU for everybody; retention recomputed from `q_mean_ah`) | `test_m3_*` |
| m4 | cumulative EFC forward-filled and made monotone (count of fixes in `meta`), time and EFC asserted non-decreasing; zero-width intervals get rate 0 | `test_m4_efc_*` |
| m5 | inversion collocation seeded per (seed, cell id): a cell's prediction does not depend on its batch | `test_m5_*` |
| m6 | not equalised (neural arms keep every cell): `n_train_used` per arm and `n_train_scorable_cells` are recorded; storage cells drop out of A11/A12 at window k-1 | `test_m6_*` (2) |
| m7 | failed trials are redrawn until N valid ones exist; more than max(2, N/4) failures raise | `test_m7_*` |
| m8 | A12 `mono=True` documented in the README; SNL inner folds stratified by temperature (`spec.strat_index`); `auto_budget` fixes N and inner folds before tuning; `log_ratio` raises on unequal condition sets | `test_m8_*` (4) |
| D013 C1 | `GRAD_CLIP` 20 now in A2 and A9 as in the PINN arms (constants in `law.py`, `clip` configurable through `pinn: {clip, warmup, lr}`) | `test_d013_c1_*` (4) |
| D013 C2 | SNL A5 pairs = T x discharge + chemistry flag x T + flag x discharge (7); ISU and Samsung unchanged; A5 still 5 dimensions | `test_d013_c2_*` |
| D013 C3 | `lam_res` grid gains 1e-3 in A1, A3, A4, A5, A7, A13, A14 (still 6 dimensions for A1) | `test_d013_c3_*` |
| D013 C4 | run-start `DeviceError` when CUDA is visible; older tests set `-1` | `test_d013_c4_*` |
| D013 C7 | `diagnostics.json` per run: tuned `lam_res` with grid-edge flags and edge share, sd of fitted `delta_c` against TAU (flag outside [0.5, 2]), clipped-step fraction for A1, A9 and the other gradient-trained arms; tournament table in `backbone_tournament.json` | `test_d013_c7_*` |

Not touched (lead assigns): D013 C5, C6, C8, C9 (prereg and paper text). The smoke runs of section 2 were made before these changes (A1 now has a 6-value `lam_res` grid and A2/A9 are clipped); re-run at the freeze.

## 5. Figure inputs and statistics step (2026-11-05)

New: `pinnkan/emit.py`, `pinnkan/stats_step.py`, `pinnkan/h7.py`, launchers `code/run_pinnkan_stats.py` and `code/run_figures_on_build.py`; formats of `code/figures/README.md`.
Tests: `code/tests/test_pk_emit_stats.py` (13 tests). **Full suite: 170 passed, 0 failed** (the two older probe tests pass again after the data layout settled). No FROZEN, no SCORED.jsonl.

| file | written by | where |
|---|---|---|
| `window.csv`, `reference_values.json` | run writer (every inner and confirmatory run; not for blinded Samsung) | each run dir |
| `stress_functions.json`, `residual_map.npz`, `superposition.csv` | run writer, datasets with a calendar term and the Samsung layout (superposition: confirmatory only) | each such run dir |
| `contrasts_<test>.json`, `reference.json`, `controls.json` | `run_pinnkan_stats.py` (D012 exact sign test on ln(S_comp/S_A1), order-statistic interval, BCa mean pp, D009 pp tier from the inner-CV E, Holm for H1a/H1b/H6, gate for H1c, H2 A/C/B, Test C Holm-2, S2 H5) | analysis dir |
| H7 `summary.json`, `surfaces_<gen>.npz` | `mode: "h7"` | run dir |

Definitions chosen where the figure README leaves them open: `a_pp500` = calendar loss in pp after 500 d at 25 C with the fold backbone; `E_kJmol` = E / (1/298.15 - 1/308.15) x R; storage rate in pp per 500 d (initial rate); cyclic partial dependence = mean over the training cycling conditions, centred; A10 curves from its fitted exponents (SOC_max = SOC_mid + median DoD / 2); superposition counterfactual `y(a_cyc = 0) / y(full)` (D013); `R_LOO`, `R_WARP` = median over training conditions with at least 2 replicates (STATS_RULING 1.2). Comparators for H1b, H1c, H4, H5 are chosen by the inner-CV score of each fold's training side, never by test error.
Synthetic condition keys now use the Samsung key format so the figure scripts can parse them (all earlier synthetic runs used another key format; they stay on disk).

End-to-end checks (all CPU, synthetic or training folds only):
- Synthetic confirmatory runs `build_v1_fig_synth_B2` (13 arms), `_C` (35 C domain), `_S2` (storage conditions held out), `_NEG` (permuted stress, A1/A9/R2), `_ISUslot`, `_SNLslot`, H7 `build_v1_emit_synth_H7` (3 generators x 3 draws, A1/A2/A4/A8, demo size) -> `build_v1_fig_analysis_SYNTHETIC/` -> `python -P code/run_figures_on_build.py --b runs/build_v1_fig_synth_B2 --h7 runs/build_v1_emit_synth_H7`: **all 11 figure and table scripts exit OK** (outputs `paper/figures/*_SYNTHETIC.*`, watermarked). Fig. 2 uses the figure demo's invented fade table (not a run-writer output). The ISU/SNL slots of Table 1 are synthetic stand-ins: the real ISU/SNL outer tests are blocked by the guard and their training-fold runs have no outer metrics.
- Real ISU and SNL **training folds** (mode inner, `build_v1_emit_isu_B0_inner`, `_snl_B0_inner`): window.csv and reference values written, contrasts from out-of-fold inner-CV scores labelled `source: inner_cv_training_conditions`; a confirmatory request on ISU is still refused by the guard (test).
- Superseded and kept on disk: `build_v1_emit_synth_S2` (failed: superposition on a run without cycling test cells, fixed), `build_v1_emit_synth_B/C/S2_r2/NEG`, `build_v1_fig_synth_B` (earlier key format or before the A10 partial-dependence floor).

Observations for the statistician (synthetic G2 demo, tiny budgets, not results): (i) under the permuted-stress control A1 is clearly worse than A9 (mean L = -0.74, two-sided p = 0.03, so the control "fails" its p > 0.05 criterion although mean L < ln 1.02 holds) and A1 still beats R2 by a large margin (median L = 1.31, criterion "A1 does not beat R2" fails): the window-fitted per-cell terms and the time law carry information that does not depend on stress, so criterion (ii) as written may fail even for a leak-free pipeline; the criteria need a ruling before the freeze. (ii) P1 shows False at demo size (H7 with 1 trial and 15 % steps).

## 6. Negative control of D014 / NEGCONTROL_RULING.md (2026-11-05)

Tests: `code/tests/test_pk_negcontrol.py` (34 tests) and adapted older tests. **Full suite: 205 passed, 0 failed.** No FROZEN, no SCORED.jsonl. Files `code/data/samsung_checkups.py` and `code/tests/test_samsung_checkups.py` were not touched.

| item | implementation | test |
|---|---|---|
| NC-1 in every confirmatory run | after the final predictions each fitted arm and seed re-predicts from windows rebuilt out of cells with garbage post-window retention (`negcontrol.scramble_cells`, ruling section 3; with a life level the forecast set is kept and asserted); `invariance.json` = max abs diff, rows, per arm and seed; any difference writes `GATE_G_TRIPPED` and raises `InvarianceError` | all 15 arms bit-identical; a leaky window (one check-up too long) is caught for R2 and A2; the gate trips when the check fails; `invariance.json` exists in every confirmatory run |
| NC-1 full pipeline (mandatory before the freeze) | `mode: "nc1_full"` (synthetic): the whole pipeline twice, clean and with scrambled test labels; predictions (inner OOF and outer), `tuning_done.json`, `margins_inputs.json` compared | test; demo run `build_v1_nc1_full_synth`: **passed**, 6,336 outer rows, max abs diff 0.0 (inner OOF 0.0), both records identical, scores differ (labels really changed) |
| NC-2 | `permute_stress` allowed on Test B only (ConfigError otherwise); `stats_step.nc2`: `L_c = ln(S_A1,perm / S_A1,real)` per condition on the same conditions, exact one-sided sign test at 0.025, median L, `exp(median) - 1`, k of n, order-statistic interval, descriptive rows (A9/A1 real and permuted, scores of every arm); non-gating. The draft criteria (A9 vs A1, A1 vs R2), `run.negative_control` and `metrics.signflip_p_two_sided` are removed | exact-test and pairing tests (27 of 40 passes, 26 fails) |
| Seed rule | `negcontrol.mc_rng(label)` = `SeedSequence([20261105, crc32(label)])`; BCa intervals use labels `<test>\|<hyp>\|<comparator>\|BCa_mean_pp`; root and rule in `seeds.json`, root in `DEFAULTS` (config hash), labels in `contrasts_<test>.json` (`mc_labels`); a different root is a `ConfigError` | stream, labels, seeds.json, config hash |
| No use of the forecast-set extent | behavioural test for all 15 arms: predictions at a check-up are equal (1e-6, float32 rounding of a differently sized matmul; NC-1 itself compares identical query lists and is bit-exact) when later times are cut, added or the list has length 1; static test forbids `t_fc[-1]`, `t_fc.max` etc. in every model module. The only reader is `emit.superposition` (an output computed after scoring) | tests |
| Ruling section 6 | code edits done (run.py, metrics.py, stats_step.py `build_controls`, `invariance.json`, unit tests incl. the deliberate leak). Prereg text edits (section 10 first bullet, stop rule 3, checklist 17.2, outcome row G) are left to the lead | - |

`controls.json` now holds `negative.nc1` (gate) and `negative.nc2` (interpretive); `code/figures/table2.py` Part B was changed to read them (two rows replace the three draft rows; the file is the figure owner's, one small edit). Demo (`build_v1_fig_analysis_SYNTHETIC`, synthetic G2, 8 held-out conditions): NC-1 passed (10,296 rows, max abs diff 0); NC-2 not passed (5 of 8 positive, median L = 0.43, p = 0.36), which at n = 8 is the test's power limit and not a finding. All 11 figure and table scripts run on these outputs.
Superseded demo runs kept on disk: `build_v1_fig_synth_B2` and `_NEG` (before invariance.json and the new controls).
