# code/figures: figure and table scripts (JES paper, PINN-KAN calendar + cycle ageing)

Style module `pk_style.py` (Okabe-Ito palette, one colour + marker + line style per arm, 8 pt text at 16 cm / 13 cm width, one label per unit,
watermark and `_SYNTHETIC` suffix when any input directory carries a `SYNTHETIC` marker file, refusal to read Samsung data before
`runs/prereg/FROZEN`). Loaders in `pk_data.py`. Every script reads **only** run directories passed as arguments and writes vector PDF + 600 dpi
PNG to `paper/figures/` (tables: `paper/tables/*.tex` + `.csv` for the Word layout).

```
.venv\Scripts\python.exe -P code\figures\make_demo_runs.py          # SYNTHETIC demo runs -> runs/figdemo_SYNTHETIC
.venv\Scripts\python.exe -P code\figures\run_all_demo.py [--regen]  # every figure and table on the demo runs (about 25 s, CPU)
```

| script | output | arguments (run directories) | prereg item |
|---|---|---|---|
| `fig1_schematic.py` | Fig. 1 | `--run-s2 --run-b --run-c` | mechanism |
| `fig2_design.py` | Fig. 2 | `--meta experiments_meta.csv --fade <check-up table>` | 3.3(7), H4, E3 |
| `fig3_forecasts.py` | Fig. 3 | `--run-b --run-c` | H1, H4 |
| `fig4_forest.py` | Fig. 4 | `--run <test_B> --contrasts analysis/contrasts_B.json` | H1a, H1b, H6, H1c, H2 |
| `fig5_stress.py` | Fig. 5 | `--run <test_B>` | H3, 11a items 1, 2, 5 |
| `fig6_storage.py` | Fig. 6 | `--run-s2 --run-b` | H5, X1, S3, 11a items 3, 4 |
| `fig7_residual.py` | Fig. 7 | `--run <test_B>` | H2 mechanism |
| `fig8_synthetic.py` | Fig. 8 | `--run <synthetic_H7>` | H7, H3 |
| `table1.py` | Table 1 | `--run-b --run-c --run-s2 --run-isu --run-snl --analysis` | H1, H4-H6 |
| `table2.py` | Table 2 | `--run-b --analysis` | H1b, X1, section 10 |
| `fig_graphical_abstract.py` | graphical abstract, 13 x 5.2 cm (3071 x 1228 px) | `--meta --run-b --run-s2 --contrasts` | |

## Files each script reads

Existing run-writer files (code/README.md): `config.json`, `metrics.json` (`outer_test[arm]`: `primary_pp`, `seed_sd_of_mean`, `n_conditions`,
`n_params`), `condition_scores.json` (arm -> condition -> pp), `predictions.csv` (`phase, arm, seed, cell_id, cond, t, pred_retention,
true_retention`), `timings.json`, `margins.json`.

**Not yet written by the run record or the statistics step; the figure scripts need them (formats = those of the demo runs):**

| file | written by | content |
|---|---|---|
| `<run>/window.csv` | run writer | `cell_id, cond, t, retention`: the model-visible window check-ups of every scored cell (Figs. 1, 3) |
| `<run>/stress_functions.json` | analysis step | `soc`, `calendar.{E_kJmol, a_pp500}.{mean,lo,hi}`, `calendar.A10_E_kJmol`, `storage_rate.{T_C,soc,mean,lo,hi}`, `arrhenius.{soc,T_C,ln_rate.{mean,lo,hi}}`, `cyclic.<var>.{x, A1.{mean,lo,hi}, A4.mean, A10.mean}` for `T, soc_mid, dod, c_ch, c_dch`; lo/hi = min/max over `n_members` (outer folds x seeds) (Figs. 5, 6) |
| `<run>/residual_map.npz` | analysis step | bin edges `T_edges, soc_edges, cch_edges`, median `absR_T_SOC [nT x nSOC]`, `absR_cch_T [nT x nC]`, training points `train_T_SOC`, `train_cch_T` (Fig. 7) |
| `<run>/superposition.csv` | analysis step | `cell_id, cond, arm, share_cal, cal_exceeds_total` (11a item 4; Fig. 6c) |
| `analysis/contrasts_<B|C|S2|ISU|SNL>.json` | statistics step | per contrast: `comp` (arm), `L_by_cond` (ln comparator/A1 per condition), `median_L`, `median_ci95` (order statistics), `n`, `n_wins`, `mean_pp`, `mean_pp_ci95` (BCa), `tier` (S/N/-/null), `status`; top level `margins.{S,N}` (Fig. 4, Tables 1-2, graphical abstract) |
| `analysis/reference.json` | statistics step | `values.<test>.{R_LOO, R_WARP}` (Table 1) |
| `analysis/controls.json` | statistics step | negative and positive controls of prereg section 10 (Table 2) |
| `synthetic_H7/summary.json`, `surfaces_<gen>.npz` | H7 driver | per draw `gen, draw, additive_floor, nrmse{arm}`; surfaces `lhs, f_true, f_A1..f_A8` of shape (draws, 500) (Fig. 8; the pilot P4 layout is the model) |
| fade table for Fig. 2e-f | pipeline | the columns of `data/processed/samsung_checkups.csv` (`cell_id, lab, type, stage, T_C, SOC_max, DoD, C_ch, C_dch, elapsed_days, retention`); refused before the freeze |

The Fig. 4 estimand follows `runs/prereg/TYPE1_SIGNFLIP.md` (exact sign test adopted: median over conditions of ln(comparator/PINN-KAN) with its
order-statistic interval); PREREG_v2 section 9.3 still describes the studentized sign-flip rule and is to be updated at the freeze.

Demo runs: `runs/figdemo_SYNTHETIC/` (invented ageing laws; design identifiers only from the metadata and the split file). Every output built from it is
named `*_SYNTHETIC.*` and carries the watermark "SYNTHETIC DEMO - NOT RESULTS". LaTeX previews of the tables: `paper/tables/preview/`.
