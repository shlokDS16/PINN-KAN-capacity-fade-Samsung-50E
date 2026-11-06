# code/figures: figure and table scripts (JES paper, PINN-KAN calendar + cycle ageing), aligned with PREREG_v4 (section 14, section 20)

**Binding rule (GATE_freeze_audit, re-check rev. 19, ruling on D037).** Every script here reads only the outputs of the frozen statistics step
(`code/run_pinnkan_stats.py` -> `pinnkan/stats_step.py`, `stats_v4.py`, `stats_rows.py`, `physval.py`) and the run writer's files (`pinnkan/run.py`, `emit.py`). No script computes an
interval, test, p-value, tier, count of positive conditions, effect size or bootstrap. Allowed: selecting and sorting supplied rows, rank picks (`pk_data.rank_pick`: the item at
a given rank of a supplied value, no quantile), unit conversion of a supplied log ratio (`pk_data.pct_from_log`), axis limits, deterministic display jitter, and the min / max
envelope merge of run-writer bands (`pk_data.merge_bands`; exact for min / max). `tests/test_figures_read_only.py` enforces it by AST (no `scipy.stats`, no bootstrap / quantile /
spread / test call, no random generator in any script except the demo generator, which only simulates run files and RUNS the statistics step).

Style module `pk_style.py` (Okabe-Ito palette, one colour + marker + line style per arm, 8 pt text at 16 cm width, watermark and `_SYNTHETIC` suffix when an input carries a
`SYNTHETIC` marker file, refusal to read Samsung data before `runs/prereg/FROZEN`). Loaders in `pk_data.py`. Output: vector PDF + 600 dpi PNG to `paper/figures/` (tables:
`paper/tables/*.tex` + `.csv`); `--out-dir` redirects.

```
.venv\Scripts\python.exe -P code\figures\make_demo_runs.py [--out DIR]           # SYNTHETIC demo runs + analysis (the statistics-step code on synthetic runs)
.venv\Scripts\python.exe -P code\figures\run_all_demo.py [--regen] [--demo-dir D] [--out-dir O]
```
The demo reads no Samsung / ISU / SNL / prereg file (invented design). Its default directory `runs/figdemo_SYNTHETIC` still holds the old V3-layout files: regenerate into a new
directory (or delete the old one) before use; tests use a temporary directory.

| script | output | arguments | PREREG_v4 section 14 item |
|---|---|---|---|
| `fig1_schematic.py` | Fig. 1 | `--run-s2 --run-b <grid runs> --run-c` | schematic + grid of m and k |
| `fig2_design.py` | Fig. 2 | `--meta experiments_meta.csv --fade <check-up table> --subset-runs <grid runs> [--fold]` | design map, nested subsets (panel g) |
| `fig3_forecasts.py` | Fig. 3 | `--runs-b <grid runs> --run-c` | forecasts at g1 and g4, Test C row |
| `fig4_forest.py` (file name kept) | Fig. 4 | `--stats analysis/contrasts_v4_B.json` | learning curves over 3 x 3, ladder, mean pp (BCa), tiers |
| `fig5_stress.py` | Fig. 5 | `--physval analysis/physval_11a.json --stats ... --runs <grid runs>` | E(SOC), a(SOC), storage rate, cyclic PD, stability table; T = fixed label |
| `fig6_storage.py` | Fig. 6 | `--run-s2 --runs <grid runs> --stats --physval --controls` | Q-T, S2 parity, calendar share, Arrhenius |
| `fig7_residual.py` | Fig. 7 | `--run <grid runs> [--fold]` | residual map (descriptive) |
| `fig8_synthetic.py` | Fig. 8 | `--run <synthetic_H7> --controls` | G0 recovery, 0.15 line |
| `table1.py` | Table 1 | `--analysis <analysis dir>` | arms x grid, Test C, S2 |
| `table2.py` | Table 2 | `--analysis <analysis dir>` | ablations, controls, Q-T, outcome |
| `fig_graphical_abstract.py` | graphical abstract, 13 x 5.2 cm | `--meta --stats` | |

"Grid runs" = the run directories of the confirmatory grid (one per outer fold and m; every run holds the three k cells), given as one directory, its parent, or a comma list.

## Inputs, by producer

**Run writer** (`code/README.md`): per run `config.json` (`m`, `fold`, `design`), `metrics.json` (`k_labels`, `k_primary`, `outer_test_by_k[k][arm]`: `primary_pp`, `seed_sd_of_mean`,
`n_conditions`, `n_params`, `n_train_used`, `fit_seconds_one_fit`), `condition_scores[_k<k>].json`, `cell_scores[_k<k>].json` (cell -> `cond, rmse_pp, n_fc`), `comparators.json`
(`D*`, `AG` -> arm), `predictions.csv` (`phase` = `outer_test` for the primary k, `outer_test_k<k>` otherwise; `seed` = 0..4 or `ens`, the seed ensemble, which is what is scored),
`window.csv` (primary k; the window of a smaller k is the rows before that cell's first forecast point), `subsets.json`, `train_condition_meta.json`, `stress_functions.json`
(bands `mean, lo, hi` = min / max over members, plus `members`), `residual_map.npz`, `superposition.csv`, `extracted_laws.json`, `reference_values.json`, `invariance.json`.
Test C and S2 runs: the same files with plain names (one cell).

**Statistics step** (`run_stats_v4`): `analysis/contrasts_v4_B.json` with `estimated.rows` (per comparator in D*, A9, AG, A2, A10, A10P and cell: `median_L`, `rel_reduction_pct`,
`simultaneous.{lo, hi, rel_reduction_ci_pct, is_range}`, `mean_pp`, `mean_pp_ci`, `n_wins`), `estimated.ladder`, `effective_tiers` (P1, P2, P3, R1_g1, K1, K2, QH_g1, QA10_g1),
`secondary.tests.<Q>.tier`, `mean_vs_median.contrasts`, `qualifier_sentences`, `outcome` (states, extent clause, title), `test_c.rows`, `s2.rows`, `gate_G`,
`edge_wording.stability` (descriptive stability table of A15 and G15); `analysis/physval_11a.json` (E(SOC) envelope, storage-rate envelopes, direction envelopes, superposition
summary; temperature carries the fixed label only); `analysis/controls.json` (NC-1, PC-1, Gate G, reported checks).

**Statistics-step outputs that DO NOT EXIST yet (gaps, see `ALIGN_V4_REPORT.md`):** `analysis/arm_table.json` (Table 1: per arm and cell `mean_pp`, `seed_sd_pp`, `n_conditions`,
`n_params`, `n_train_used`, `fit_seconds`; keys `cells["m|k"]`, `test_c`, `s2`), `analysis/reference.json` on the Design R2 path (`values.B.{R_LOO, R_WARP}`), NC-2, PC-2 and PC-3 in
`controls.json`, the A15 / G15 closed forms with coefficient counts, BIC and Latin-hypercube stability metric (Fig. 5), a(SOC) / A4 / A10 curves and Arrhenius lines in
`physval_11a.json` (Figs. 5, 6 read the run writer's `stress_functions.json` meanwhile), the merged residual map (Fig. 7 shows one outer fold), Q-T interval in the estimated tables.
The demo writes a SYNTHETIC stand-in for `arm_table.json` only (its `producer` field says so).

Demo runs: every output built from them is named `*_SYNTHETIC.*` and carries the watermark "SYNTHETIC DEMO - NOT RESULTS". LaTeX previews of the tables:
`paper/tables/preview/` (V3 previews there are stale).
