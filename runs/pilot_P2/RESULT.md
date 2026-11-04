# P2 result: seconds per fit, CPU (2026-11-04)

Judge rule (D010 section 7, P2): **Go** if hard fit <= 30 s and PINN fit <= 90 s; **Partial** if up to 3x slower
(trials 20 -> 10, inner folds 3 -> 2, seeds stay 5); **No-go** beyond 3x.
This is a timing pilot: the losses in the run files are finiteness checks, not results; no test split exists or was touched.

## Verdict: PARTIAL as specified (hard ODE 38 s at 80 nodes per cell); PINN GO; hard ODE inside budget at 40 nodes or fewer

Setting of the specified pilot: SNL, all 61 cells, up to 80 observed points per cell (4,819 points), 2,000 Adam steps,
3 seeds each, one fresh process per fit. Full table: `summary.md`; every run: `raw/*.json`; configuration: `config.json`.

| Model | Setting | 1 thread, s (min-max) | 3 threads, s (min-max) | Budget | Rule outcome |
|---|---|---|---|---|---|
| Hard ODE (RK4, KAN law) | 61 cells, 80 nodes | 38.4 (38.2-38.9) | 38.3 (37.7-38.8) | 30 | **Partial** (1.28x) |
| Hard ODE | 61 cells, 40 nodes (1 seed) | 18.5 | 18.4 | 30 | Go |
| Hard ODE | 61 cells, 20 nodes | 11.4 (10.7-12.5) | 10.6 (10.5-10.8) | 30 | Go |
| Hard ODE | 279 cells (61 tiled), 80 nodes (1 seed) | 42.0 | 43.5 | 30 | Partial (1.45x) |
| PINN (F + residual) | 61 cells, 80 points | 18.9 (18.7-19.1) | 15.6 (15.2-16.1) | 90 | **Go** |
| PINN | 61 cells, 20 points | 13.3 (12.6-14.4) | 12.8 (11.9-14.4) | 90 | Go |
| PINN | 279 cells (tiled), 80 points (1 seed) | 50.6 | 32.0 | 90 | Go |
| PINN | every cycle, 96,341 points (1 seed) | 219.4 | 102.0 | 90 | Partial (2.4x; 1.1x at 3 threads); not a planned design |

Peak RAM (Windows peak working set, including about 690 MB just for importing torch): 691-710 MB for the 61-cell
fits, 735 MB for 279 cells, 840 MB for the 96k-point PINN. Far below the 3 GB limit.

## What drives the time
- **Hard ODE: sequential RK4 nodes, not cells and not threads.** Per step 5.7 ms at 20 nodes, 9.3 ms at 40, 19.2 ms at 80;
  tiling to 279 cells adds only 10 %. Threads do nothing (tensors are 61 to 279 elements): use 1 thread per process.
  The 30 s budget is met at up to about 60 nodes per cell (linear interpolation of the three measured points, not measured).
  The Samsung check-up count per cell is what matters: P0 reports 7 check-ups for one cycling cell in its sample, so the
  hard-ODE arm is probably inside the budget there, but that is an inference from node count, not a measurement on Samsung data.
- **PINN: data and collocation volume.** 9.4 ms/step at 4.8k points (3 threads: 7.8 ms), 25 ms/step at 22k points
  (3 threads: 16 ms), 110 ms/step at 96k points (3 threads: 51 ms). Threads help only when the data term is large.
- Hard ODE is slower than the PINN at the same data size here because eager PyTorch pays per-op overhead for 79 sequential
  RK4 steps (about 320 stage evaluations forward and again backward); the PINN is one batched network pass plus one
  double-backward.

## Budget per arm and outer fold (fits only; the 3 inner folds train on 2/3 of the conditions)
- Plan as written (20 trials x 3 inner folds + 1 refit = 61 fits): hard ODE at 80 nodes 61 x 38 s = 39 min; at 20 nodes
  61 x 11 s = 11 min; PINN at 80 points 61 x 17 s = 17 min (cheaper in the inner folds, since PINN cost falls with data).
- Partial plan (10 trials x 2 inner folds + 1 refit = 21 fits): hard 80 nodes 13 min; PINN 6 min.
- Multiply by arms and outer folds; run three single-thread processes in parallel rather than one 3-thread process.

## Limits of this measurement (state when quoting the numbers)
- Minimal law: one state factor (no backbone tournament), nu_c constant per cell, no storage cells in SNL (the calendar KAN
  runs but is unidentified), no prior beyond 1e-3 on delta_c. The real arms add per-trial tuning of grid, hidden width,
  sparsity and lambda_res; they change cost per fit very little but change the number of fits.
- Own compact B-spline KAN (`code/models/kan_spline.py`), not pykan MultKAN (pykan was not used; its grid-update and
  symbolic bookkeeping are not needed in the inner loop). A pykan-based implementation may be slower.
- 61 SNL cells, up to 80 points per cell. 279 cells were emulated by tiling the 61 cells (timing proxy only). Samsung check-up
  cadence is not in these numbers.
- Other sessions were running: system CPU load before each run was 11 to 36 %. The first launch of the driver was killed after
  one run when its shell exited (34.3 s, `raw_aborted/`, not used); it agrees with the re-run (38.2 s) within load noise.
- 2,000 Adam steps fixed; whether 2,000 steps suffice for convergence on the real task is untested (losses were finite and
  fell in all 32 runs: `all_finite` true in every file).

## Recommendation to the lead (decision is the lead's)
Treat hard-ODE budget as **go if the Samsung check-up count per cell is at most about 40**, otherwise apply the partial plan
(10 trials, 2 inner folds) to the hard-ODE arm only; the PINN arm keeps the full plan. Unit tests (8) passed before any timing run.
