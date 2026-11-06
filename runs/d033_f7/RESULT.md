# D033 F7: full-pipeline NC-1 (`nc1_full`) at m 8 / 16 / 32 with short-record synthetic cells (coder, 2026-11-06)

Synthetic data only (G2, 40 cycling + 19 storage conditions, 3 replicates, seed 31, test_frac 0.2); CPU only; no Samsung data. This is development evidence for the judge's action 5. It does not
replace FB-9, which is run at the frozen commit.

Configs: `configs/nc1_full_synth_m{8,16,32}.json` (shake-down configs plus `m` and `synthetic.short_records = {"train_n_points": [4, 5], "test_n_points": [4, 3]}`: the first two training
cycling cells are cut to 4 and 5 check-ups and the first two test cycling cells to 4 and 3 check-ups, so the D025 cap binds for the 4- and 5-point cells and the 3-point cell has no window of three
points and is not scored; implemented by `synth.shorten_cells`, applied in `run.build_data`). Arms A1, A2, A9, A10, A12, A15, G15, R1, R2, seeds 0-2, k grid (0, 2, full), n_trials 2, inner_k 2,
steps_scale 0.15. Each run: one clean pipeline plus one scrambled pipeline per k (labels after that k's window replaced by garbage), tuning included. Run time 424 / 449 / 520 s (three processes in parallel).

| m | passed | outer rows compared (k = 0 / 2 / full) | max abs diff, outer | max abs diff, inner OOF | non-finite predictions | tuning_done.json and margins_inputs.json equal | cells with the D025 cap (clean run) | predict-stage invariance (75 arm x seed records) |
|---|---|---|---|---|---|---|---|---|
| 8 | yes | 28460 (9380 / 10332 / 8748) | 0.0 | 0.0 | 0 | yes, all k | SYN_G2_31_C01_1, SYN_G2_31_C01_2 | passed, 0.0, 21345 rows |
| 16 | yes | 28460 (9380 / 10332 / 8748) | 0.0 | 0.0 | 0 | yes, all k | same two | passed, 0.0, 21345 rows |
| 32 | yes | 28460 (9380 / 10332 / 8748) | 0.0 | 0.0 | 0 | yes, all k | SYN_G2_31_C00_1, SYN_G2_31_C00_2, SYN_G2_31_C01_1, SYN_G2_31_C01_2 | passed, 0.0, 21345 rows |

(At m = 8 and 16 the two shortened training cells are not in the training subset, so they are absent from the cap list; at m = 32 they are in training and capped.) Files: `results/m*/nc1_full.json`, `invariance.json`,
`window_capped.json`, `git.json` (HEAD at run time `de2b4e8` plus the uncommitted D033 working tree; the code that ran is the code of the D033 commit).

What is NOT covered (reported, not fixed):
- The real-data loader (`data._load_samsung`, ET/first-CU anchoring, `keep` lists, `lab_map`) is covered by `code/tests/test_pk_d033_coder.py::test_scrambling_post_window_capacities_before_the_loader_...`:
  capacities after each cell's window are garbled in the pipeline table before the loader runs; training cells, the cap list, the window arrays and the causal throughput curve are byte-identical. The
  loader reads `qc_pass` as a column.
- `qc_pass` is made upstream (`code/data/samsung_checkups.py`, `flag_outliers`). That rule is causal (the flag of a check-up never changes when later capacities change, documented in its docstring and
  asserted in `test_qc_flags_are_causal_...`), so window labels, the anchor and training sides cannot depend on post-window labels through it. A garbage value after the window can however be flagged
  and dropped, which shortens the retained record: the forecast set of any cell and the D025 window `min(k, n - 2)` of a short cell then depend on post-window labels through the QC. NC-1 scrambles
  after `build_data`, so it holds the retained set fixed by construction. The same dependence is the reason D025 makes the window depend on the record length (red team M4). It is a property of the
  design, not of the code, and is reported here for the red team; no code change was made.
