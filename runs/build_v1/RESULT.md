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
