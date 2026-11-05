# Freeze shake-down (lead, 2026-11-05 22:04-22:15; CPU only, 3 single-thread processes)

Purpose: run the FB-8 / FB-9 / FB-10 paths at the current HEAD (42c2a84 code) before the freeze, to find failures early.
These runs do NOT count for the freeze blockers: FB-8, FB-9 and FB-10 must be re-run at the freeze commit (PREREG_v4 17.1).
Configs: `configs/`; queue: `run_queue.sh`; logs: `logs/`; run directories `runs/shk_*`.

| run | result |
|---|---|
| timing_samsung_B0_m32 (blinded, all 13 grid arms) | ran after adding `window: {k_cycling: 4, k_storage: 2}` (the first attempt stopped at the review-M3 guard: real-data grid runs must state the FB-6 counts). Fit seconds: A1 26.1, A2 4.6, A4 16.4, A9 5.0, A10 8.2, A10P 8.3, A11 5.5, A12 0.1, A13 24.7, A15 19.4, G15 17.2. `tuning.choose_budget` on these single fits: N = 20, 3 inner folds (A1 > 20 s; A2 < 30 s, PINN < 90 s, so no Partial plan) |
| timing_samsung_B0_m8 | ran; same arms, 116 s total |
| nc1_full_synth_m8 (G2 synthetic, k grid, A15/G15 included) | passed: max abs diff of outer predictions 0.0 over 30816 rows |
| nc1_full_synth_m32 | passed: max abs diff 0.0 over 30816 rows |
| smoke_isu_B0, smoke_snl_B0 (build_v1 configs; out-of-scope arms A3, A7 removed for Design R2) | ran, rc 0 (93 s, 109 s) |

Lesson for the freeze configs: every Samsung grid config must carry `window: {"k_cycling": 4, "k_storage": 2}`.

Note: the queue log shows rc=0 for the first (failed) timing attempt because `$(date)` in the echo reset `$?`; fixed in run_queue.sh (rc captured first). The Python runner itself exits non-zero on an exception.
