# Post-review exploratory runs: setup, harness and rules (D048)

POST-HOC, EXPLORATORY. Binding rules: D048 (research/DECISIONS.md, committed d7fc17f before any new score) and the contract in paper/review/TEACHER_REVIEW_2026-11-12.md of the writing worktree.
Plan: paper/review/EXP_PLAN_2026-11-12.md (amended by CODEX_TEACHER_2026-11-12.md and D048). CPU only; at most 16 worker processes; one thread per process.

## Worktree
- `git worktree add --detach "C:\Users\Shlok\Downloads\PINN KAN battery paper-frozen" c6a89b6` (checkout with core.autocrlf=false, then the files whose bytes are pinned by hash in FROZEN
  and the extraction audit / calibration rule files were copied byte-exact from the main checkout, because the main checkout holds a mix of LF and CRLF files that the FROZEN pins were
  computed over; `git diff` of the worktree against c6a89b6 is empty after `git add -u`, HEAD = c6a89b6b2125a0ccb5b6170538fe7d43c018d2ba).
- Untracked inputs added to the worktree: copy of runs/prereg/FROZEN (the main checkout tracks it only from d4f3ba8), copies of runs/item_f/item_f_dependence.json and .sha256.json, junction
  data/processed -> MAIN/data/processed. The guard is satisfied legitimately (HEAD = frozen commit, code/ and runs/prereg/ clean, all pins verify); it is never patched.
- runs_dir passed to the frozen loaders = MAIN/runs (the item (f) artifacts are verified there). Nothing calls guard.record_scoring: runs/prereg/SCORED.jsonl is not touched.
- `code/`, `runs/prereg/`, `runs/stats_frozen/` of the main checkout are not edited. `harness.assert_out` refuses any write outside runs/post_review/.
- The worktree is removed at the end (`git worktree remove`).

## Harness (runs/post_review/_harness/)
- harness.py: data and window loading exactly as run.py `_run`; A1 copy with z-prior weight and residual-weight schedules (`fit_pinn_x`, `A1x`), A9 copy with z weight (`A9x`), diagnostics, job runner.
- validate_v0.py: V0 gate. Seed-0 refits of A1 (frozen path and harness copy), A2, A9 (both paths), A15, G15 at fold 0, m 8 and m 32, predicted at k = 0, 2, full on the outer test windows, compared
  with runs/conf_samsung_B_f0_m*/predictions.csv: max abs difference 0.0 for every arm and k (files V0_f0_m8.json, V0_f0_m32.json). Also: the L0 rerun of item 2 (all folds, five seeds, ensemble)
  reproduces the frozen A1 condition scores of all 40 conditions at g1 and g4 with max abs difference 0 (RESULTS_SUMMARY.md, integrity table).
- experiments.py / run_exp.py (items 2, 3, 5, 6), extraction_variants.py (item 5), hgrid.py (item 6), nc2.py (item 7), summarize.py (RESULTS_SUMMARY.md).
- Job directory: runs/post_review/<exp>/<variant>_f{fold}_m{m}/ with config.json, git.json, env.json, RUN.log, predictions_k*.csv.gz, condition_scores*.json, metrics.json, diagnostics.json /
  extras.json; per experiment SHA256.json over every file.

## Variable studied per item (everything else as tuned in the frozen run of that fold and m)
- Item 2: lambda (training and inversion) fixed at 1e-2, 1e-1, 1, 10; gradient-norm balancing; annealing. Item 3: z prior weight 10, 100, 1e4 (training and inversion), A1 and A9; law readout.
- Item 5: extraction cap 3, untruncated ceiling (A15). Item 6: h grid of 8 members for A2 and A1; inner-fold choice. Item 7: stress-permutation draws, full re-tuning per draw (variant F).
- Item 8 (SNL): not run, see snl/BLINDING_CHECK.md.

## Deviations from the plan, stated
- The adaptive weighting starts at the tuned lambda and takes effect one step after each update; annealing uses the schedule alone (no extra warm-up ramp) and the inversion at lambda = 1.
- Items 1 (horizon errors), 4 (seed-spread coverage) and 9 (rho sweep) of D048 were not part of this run's brief.
