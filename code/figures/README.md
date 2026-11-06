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
| `fig5_stress.py` | Fig. 5 | `--physval analysis/physval_11a.json --stats ... --law-summary analysis/law_summary.json` | E(SOC), a(SOC), storage rate, cyclic PD with A4 / A10 / A15 / G15, law summary, sign votes, closed forms; T = fixed label |
| `fig6_storage.py` | Fig. 6 | `--run-s2 --runs <grid runs> --stats --physval --controls` | Q-T, S2 parity, calendar share, Arrhenius |
| `fig7_residual.py` | Fig. 7 | `--map analysis/residual_map.npz` | residual map pooled over the outer folds (descriptive) |
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

**Statistics-step outputs added for gaps G1-G8 (`code/pinnkan/STATS_GAPS_REPORT.md`; all are read by the figure scripts and tables as stated):**
- `analysis/arm_table.json` (G1; Table 1 reads it): `cells["m|k"][arm]`, `test_c[arm]`, `s2[arm]` with `mean_pp`, `seed_sd_pp` (and `seed_sd_pp_upper_bound`, `mean_pp_per_seed`), `n_conditions`,
  `n_params`, `n_train_used`, `fit_seconds` (plus ranges and `n_folds`). `seed_sd_pp` is the SD over seeds of the SINGLE-SEED pooled mean (`mean_pp_per_seed`); the ensemble `mean_pp` has no seed replicate of its own.
- `analysis/reference.json` (G2; Table 1 reads it): `values.B.{R_LOO, R_WARP, n_folds}` (the m = 32 runs), `values.C`, `values.S2` when those runs wrote `reference_values.json`.
- `analysis/controls.json` (G3): `negative.nc2` (keys of the V3 record that Table 2 reads: `k_positive`, `n`, `passed`; plus `median_L`, `median_ci95`, `crit_positives`, `descriptive`), `positive.P2_monotone_in_T`
  / `PC2_detail`, `positive.P3_passed` / `PC3_detail`, and the two reported checks in `gate_G.reported_checks` (`PC-2_calendar_rate_monotone_in_T`, `PC-3_A1_beats_persistence`; Fig. 6d and Table 2 read them).
  `contrasts_v4_B.json gate_G.reported_checks` carries the same two values (gate rule and fields unchanged); an unevaluated registered control (NC-2, PC-2, PC-3) is listed in `status.registered_controls_not_evaluated` there and marks the outcome provisional.
- `analysis/law_summary.json` (G4; Fig. 5 reads it): `arms.{A15, G15}.{n_laws, n_coefs, train_bic, stability, partial_dependence, representative, closed_forms}`; temperature carries the fixed label only.
- `analysis/physval_11a.json` (G5; Figs. 5, 6 read them): `a_of_soc`, `arrhenius_ln_rate` (envelope of ln rate against 1000 / T at the selected SOC), `partial_dependence_overlays.per_input`
  (grid, A1 envelope, `A4_mean`, `A10_mean` / `A10_lo` / `A10_hi`; the T entry is the fixed label only). Always written on the R2 path (`--no-physval` only with `--lenient`).
- `analysis/residual_map.npz` (G6; Fig. 7 reads it): the keys of the run writer's `residual_map.npz` pooled over the five outer folds from the raw cell-level values of `residual_cells.npz`
  (`n_cells_T_SOC`, `n_cells_cch_T` count the cells per bin; an empty bin is NaN).
- `contrasts_v4_B.json`: `secondary.tests.QT_g1.median_interval` (G7, an `estimated.rows` style record with `median_ci`) and `candidates_vs_a1.rows.{A11, A12, A4, A5}` (G8, the same record per candidate at g4, descriptive);
  `stats_gaps.status` lists what was formed.
New run-writer files (Samsung layout, m = 32 runs): `extracted_law_forms.json`, `residual_cells.npz`, `storage_hull.json`.
The demo produces every one of these files by running the statistics-step code (`stats_step._stats_gaps_v4`, `physval_11a`) on synthetic run directories (incl. `extracted_law_forms.json`, `residual_cells.npz`, `storage_hull.json` and synthetic permute_stress runs); no stand-in remains.

Demo runs: every output built from them is named `*_SYNTHETIC.*` and carries the watermark "SYNTHETIC DEMO - NOT RESULTS". LaTeX previews of the tables:
`paper/tables/preview/` (V3 previews there are stale).
