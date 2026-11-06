# ALIGN_V4_REPORT: code/figures aligned with PREREG_v4 (section 14 and the section 20 rows), read-only on the statistics step

Status 2026-11-06. Nothing committed. Files changed: all of `code/figures/*.py`, `code/figures/README.md`, new `code/tests/test_figures_read_only.py`. NOT touched: `code/pinnkan/*`
(`stats_*.py`, `run.py`, `emit.py`, `physval.py` unchanged; the section 20 row for `emit.py` / `physval.py` was already met in code: the temperature row is suppressed in
`physval.cyclic_directions` / `compare_with_a10_signs`), `runs/prereg/`, `research/`, `paper/draft/`, configs, the tracked `runs/figdemo_SYNTHETIC/` and `paper/figures/*_SYNTHETIC.*`
(all demo output of this work went to scratch / temporary directories; the tracked V3-layout previews are stale and should be regenerated into a fresh directory by the lead).
No Samsung / ISU / SNL / prereg file was opened or read by any script written here; the demo design is invented (two attempts of mine to probe the metadata and the split file were
refused by the permission layer and not retried).

## 1. What was removed (statistics in figure code)

| where | removed | replaced by |
|---|---|---|
| `fig4_forest.py` (old lines 36-53, 84, 113) | own bootstrap mean CI (`ps.bootstrap_mean_ci`), own median-L interval (`ps.median_order_ci`), own win count `(L > 0).sum()`, fallback `build_from_scores`, RNG jitter | Fig. 4 is rebuilt as the learning curves; every number comes from `contrasts_v4_B.json` |
| `pk_style.py` | `bootstrap_mean_ci` (BCa, `scipy.stats`) and `median_order_ci` (`binom.cdf`) deleted entirely | nothing |
| `make_demo_runs.py` | `sign_tier`, `make_contrasts` (own sign tests, Holm, bootstrap), `scipy.stats` import | the demo now runs the statistics step itself on synthetic run directories |
| `fig3_forecasts.py` / `fig1` / `pk_data.median_cell` | RMSE of the median cell computed from predictions; seed-mean `Y.mean(0)` | rank pick on the supplied `cell_scores`; the supplied `ens` ensemble rows |
| `fig6_storage.py` | `(ya < xa).sum()` count in the panel title; per-condition median of shares; own overlap counts `sup.cal_exceeds_total.sum()` | `stats['s2']['rows']['A10']['k_ratio_below_1']`; one point per cell; `physval_11a item4` counts |
| `fig8_synthetic.py` | boxplot quartiles and median line; `np.median` of the GAM floor; G1, G2 | dots per draw, 0.15 line, PC-1 verdict from `controls.json`; G0 only |
| tables | `ent['median_ci95']`, own tier text from V3 `contrasts_<test>.json` | `estimated.rows`, `effective_tiers`, `secondary.tests`, `controls.json`, `outcome` |
| `fig_graphical_abstract.py`, `fig2_design.py` | V3 forest keys; typed "19 / 40 conditions"; RNG jitter | `estimated.rows` at g1; counts from the metadata groups; deterministic jitter |

Grep justification (bootstrap / percentile / quantile / median / binom / scipy / rng, run over every script except the generator): the only hits left are docstrings and dictionary
keys of supplied values (`r["median_L"]`, `mean_vs_median`, `k_positive` of a supplied NC-2 record); no call remains. Remaining non-trivial operations, all plot-only: `rank_pick`
(sorted by a supplied value), `pct_from_log` (unit conversion of a supplied `median_L`, same formula as `stats_v4.pct_reduction`), `Y.min(0) / Y.max(0)` (range of the five supplied seed
forecasts in Figs. 1 and 3, drawn as a band, not an interval), `merge_bands` (min of `lo`, max of `hi`, average of the run means of run-writer bands; exact for min / max), axis limits from
supplied values, deterministic jitter by row index. In the generator, `rng` simulates run-writer files only. The lead may veto the seed-range band and `merge_bands`.

## 2. Per display item: inputs read, statistics removed, gaps

| item | inputs read | statistics removed | gaps |
|---|---|---|---|
| Fig. 1 | grid runs (largest m: `predictions.csv` ens + seeds, `window.csv`, `cell_scores.json`, `metrics.json k_labels`), Test C and S2 runs | median-cell RMSE | none; grid glyph (m x k, g1 and g4) added; m, k read from runs |
| Fig. 2 | metadata CSV, check-up table (refused before FROZEN), grid runs `subsets.json` + `train_condition_meta.json` (panel g: nested subsets at m = 8, 16, 32, one fold) | RNG jitter, typed counts | panel g shows one outer fold (no merged composition is produced; it is a design count, not a statistic) |
| Fig. 3 | grid runs at g1 (m 8, k 2) and g4 (32, full), Test C run: `predictions` (`ens`, seeds), `window`, `condition_scores`, `cell_scores`, `comparators` (D* arm) | cell RMSE from predictions | none. Test C exists at g4 only (stated in the figure) |
| Fig. 4 | `contrasts_v4_B.json`: `estimated.rows`, `.ladder`, `effective_tiers`, `secondary.tests` | own bootstrap CI, median interval, win count | tier of P3 shown as met / not met text; Q-T (A13) is not an estimated row (G7) |
| Fig. 5 | `physval_11a.json` (item 1, 2, 5), `contrasts_v4_B.json edge_wording.stability`, run `stress_functions.json` (a(SOC), A4, A10 overlays) | none present before; T panel = fixed label, A10 direction never drawn for T | G4, G5 |
| Fig. 6 | S2 run (`ens` predictions, `condition_scores`), `contrasts_v4_B.json` (`s2`, `secondary`, `mean_vs_median`, `qualifier_sentences`), `physval_11a item4`, grid `superposition.csv` / `stress_functions.json`, `controls.json` | win count title, median shares, overlap counts | G3 (PC-2 not evaluated), G5, G7 |
| Fig. 7 | one m = 32 run `residual_map.npz` | none | G6 (no map merged over folds; one fold shown) |
| Fig. 8 | `synthetic_H7/summary.json`, `surfaces_G0.npz`, `controls.json` | boxplot, median floor, G1 / G2 | none (G1, G2, floor are struck from the confirmatory path) |
| Table 1 | `analysis/arm_table.json`, `analysis/reference.json` | none | G1, G2 (inputs do not exist yet) |
| Table 2 | `contrasts_v4_B.json`, `controls.json` | `median_ci95` V3 tiers | G3, G8 |
| graphical abstract | `contrasts_v4_B.json` (g1 rows: D*, A9, A10; tiers) | V3 forest | none |

## 3. Gaps: inputs a figure needs that the statistics step or run writer does not produce (not added to the figures; nothing in `pinnkan/` edited)

- **G1 `analysis/arm_table.json`** (Table 1: per arm x grid cell, Test C, S2: pooled mean pp, seed SD, `n_conditions`, `n_params`, `n_train_used`, fit seconds). The run writer holds
  per-fold values in `metrics.json outer_test_by_k`; pooling across folds (n-weighted mean, SD over seeds of the pooled mean) is a statistic and belongs in `stats_step`.
  Format: `{"cells": {"m|k": {arm: {mean_pp, seed_sd_pp, n_conditions, n_params, n_train_used, fit_seconds}}}, "test_c": {arm: ...}, "s2": {arm: ...}}`. The demo writes a labelled
  SYNTHETIC stand-in. Proposed owner: a small function in `stats_step.run_stats_v4`.
- **G2 `analysis/reference.json` on the R2 path** (R_LOO, R_WARP; `stats_step.reference_from_runs` exists but `run_stats_v4` does not call it). Without it Table 1 prints "--" for E/R.
- **G3 controls on the R2 path:** NC-2 (permuted stress at g4) is not in `controls.json`; PC-2 (calendar rate monotone in T) and PC-3 (A1 beats persistence at g4) are `None` because
  `run_stats_v4` calls `build_controls` without `stress_functions` and with no V3 `contrasts_B.json`. Tables and Fig. 6d print "not evaluated".
- **G4 Fig. 5 extracted-law content (section 14, 11a items 6-7):** closed forms of A15 / G15, coefficient counts and training-side BIC, the 500-point Latin-hypercube stability metric
  (median of the fold-to-fold SD of the log-rate over its range), and A15 / G15 partial-dependence curves are not written (`law_record` keeps per-input summaries only; `stability_table`
  has votes, tie / additive shares). Only the stability table is drawn.
- **G5 `physval_11a.json` lacks** a(SOC), the Arrhenius ln-rate lines (item 3 is only the P2 boolean) and the A4 / A10 partial-dependence overlays; Figs. 5-6 read the run writer's
  per-run `stress_functions.json` and merge bands (`merge_bands`). Better: extend `physval` to carry them.
- **G6 residual map** is per outer fold; no merged map (a median of medians is not valid); Fig. 7 shows one fold.
- **G7 Q-T:** A13 is not in `ESTIMATED_COMPARATORS`; the secondary test gives tier, nodes, `mean_vs_median` (mean pp with BCa, `median_L`) and the sentence, but no structured median interval.
- **G8 Table 2:** the candidates A11, A12, A4, A5 against A1 individually (section 14 "candidates against A1") are not in the estimated tables.
- **G9 window.csv** is written for the primary k only; the figures derive the smaller-k window as the rows before that cell's first forecast point (no gap in content, noted for the writer).

## 4. Tests

`code/tests/test_figures_read_only.py` (19 tests): AST check of every module (no `scipy.stats`, no bootstrap / quantile / median / std / test call, no name containing bootstrap /
binom / sign_p, no random generator, no import of the statistics modules; the generator may import them and use `np.random` but no statistic and no `scipy`); style module has no interval
routine; README lists every script; smoke test builds the SYNTHETIC demo in a temporary directory (the project's own `Store.from_runs`, `run_v4_full`, `build_controls`, `_test_c_s2`,
`edge_level_wording`, `physval_11a` on synthetic runs) and renders all 9 figures and 2 tables with the SYNTHETIC suffix; demo does not reference Samsung or prereg paths. 19 passed (about 50 s,
CPU, one thread). Whole suite, one process per file (44 files): all pass. One existing test, `test_extraction_fallback.py::test_the_figure_5_temperature_panel_...`, pins the source text of
`fig5_stress.py` (literal T label after `if name == "T":`, `continue`, then `band(P, x, d["A1"]`); my first fig5 failed it and fig5 was adjusted to keep that pinned form (no test edited).

## 5. Render check (synthetic demo, PNGs opened)

Fig. 4, 3, 1, 2, 5, 6 and the graphical abstract were opened and fixed (legend / label overlaps, clipped headers, stability-table overflow). Fig. 8 was opened and is fine. Fig. 7 and Tables 1-2 rendered
without error but were not opened as images (Tables 1-2 were not compiled with LaTeX in this pass). Demo values are invented; tiers in the demo (P+ / K=) are not results.

## 6. Consequence for the freeze

The scripts no longer compute any statistic, so D037's premise holds. Changing `code/figures/*` moves `code/` off 92db4cb: the audit's alternative path ("align the scripts now") requires
FB-8 to FB-10 and the suite to repeat. G1 to G3 are the items the lead should rule on before the post-run figure pass; they need edits to `stats_step.py` (not made).
