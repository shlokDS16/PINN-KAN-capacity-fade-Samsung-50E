# P5 result: hard ODE vs soft PINN under misspecification (G1 on the ISU design, 5 draws), 2026-11-04

Judge rule (D010 section 7, P5): **Go** if the PINN's forecast RMSE beyond the window is below the hard ODE's in >= 3 of 5 draws. No-go: expect outcome B or C on real data and ask Shlok in the morning which framing he prefers if C occurs.
Synthetic data only; no real label or test split is involved. All numbers are in `summary.json`, `draw_*.json`, `sens_lambda_10.json` of this folder.

## Verdict: GO (4 of 5 draws), but the margin is small and one draw reverses
Forecast RMSE beyond the 4-check-up window on 12 held-out conditions (percentage points; per cell, mean within condition, then over conditions; 40-48 scored cells per draw; observation noise is 0.5 pp):

| Draw | Hard ODE | PINN, collocation from record end (judge spec, primary) | lambda_res chosen | PINN, whole time axis (sensitivity) | lambda_res chosen |
|---|---|---|---|---|---|
| 0 | 5.37 | **4.72** | 1.0 | 4.78 | 1.0 |
| 1 | **5.88** | 6.28 | 0.1 | 4.96 | 1.0 |
| 2 | 5.63 | **5.38** | 0.1 | 4.65 | 1.0 |
| 3 | 4.57 | **4.43** | 0.1 | 4.11 | 1.0 |
| 4 | 4.74 | **4.10** | 1.0 | 3.83 | 1.0 |
| median | 5.37 | 4.72 (ratio to hard 0.96) | | 4.65 (ratio 0.84) | |
| PINN below hard | | **4 of 5 -> Go** | | 5 of 5 | |

Per-draw differences (PINN minus hard, primary): -0.65, +0.40, -0.25, -0.14, -0.64 pp. With five draws no significance is claimed.

## What to take from it (and what not)
1. **The soft coupling helps a little under this misspecification, not a lot.** Both models are dominated by misspecification: forecast errors are 4-6 pp against 0.5 pp noise, and both fit the training data only to 2.3-3.3 pp when the law is enforced (the law A/(1+y) cannot represent a t^z curve plus a throughput knee). The PINN gain is 0.1-0.7 pp in four draws and reverses by 0.4 pp in draw 1. Outcome A (PINN better) is the expected direction on real data if misspecification of this size exists there, but this pilot cannot say how large the margin will be relative to the preregistered replicate-spread margin.
2. **The residual weight matters, and the optimum is not hiding beyond the grid.** Inner-CV forecast error (training conditions only) at lambda_res = 0.01 (nearly data-only F) was 4.30-6.33 pp, against 4.01-5.66 pp at the chosen value, in all 5 draws; and the best inner-CV PINN score was below the best hard-ODE inner-CV score (5.83, 6.13, 5.83, 5.21, 4.94 pp) in all 5 draws. lambda_res = 1.0 (the top of the grid) was chosen in 2 of 5 draws (primary) and 5 of 5 (whole axis), so I ran a post hoc sensitivity at lambda_res = 10 (`sens_lambda_10.json`, not used for selection): forecast error rose to 5.57-6.63 pp (primary) and 5.14-6.32 pp (whole axis), worse than the hard ODE in every draw. The judge's edge rule would extend the grid to 10 and keep 1.0, so the verdict is unchanged. Trade-off: too small a residual weight leaves F a free curve fit that forecasts poorly, too large ties F to a wrong law.
3. **Attribution is not clean.** The PINN also has a flexible F and a 2-dimensional per-cell latent z_c that the hard ODE lacks; a lambda -> 0 data-only arm (D010 section 1 contrast (i)) is the right control for the real data but was not part of this pilot's definition. The lambda = 0.01 inner-CV numbers are the nearest thing here.
4. **Collocation placement matters.** The judge-spec set (collocation only from the end of each training record) gives a smaller and less stable gain (4 of 5, median ratio 0.96) than collocation over the whole time axis (5 of 5, ratio 0.84); the latter picks lambda = 1.0 every time. Which one the confirmatory run uses should be decided on training-condition inner CV, not on this table.
5. If the real data behave like draw 1, the framing question of D010 section 2 (outcome C) is live; a pilot of five synthetic draws does not move that prior much.

## Setup
- **Design and truth:** same ISU design as P4 (63 conditions, 251 cells with their own check-up weeks). G1 truth (`code/pilots/synth_gen.py`): y(t) = exp(b.x + c0 + delta_c) (t_n/0.4)^z(x) + K [sig((tau - tau0(x))/0.08) - sig(-tau0/0.08)], z = z0 + z1 x3 (DoD), tau = equivalent full cycles / reference throughput, tau0 = clip(0.65 - 0.2 x1 - 0.15 x3, 0.25, 1.1): a stress-dependent time exponent plus a logistic throughput knee whose onset shifts with charge rate and DoD; neither is of the model's form dy/dt = A/(1+y). Parameter grid fixed in `config.json`, a draw picks values with a seeded RNG; c0 solved so the median final y_s = 2.0; delta_c sd 0.15; noise sd 0.05 in y_s; no model fit enters the truth.
- **Adaptation to ISU (needed, stated):** the judge's G1 uses storage loss ~ t^z with z depending on T; ISU has a single temperature and no storage arm, so z depends on DoD, and the knee onset on C_ch and DoD.
- **Arms:** identical law, KAN [3,3,1] (grid 5) stress map, per-cell offset delta_c, loss scales and data. Hard ODE: exact integration, delta_c MAP from the window, tuned over 3 values of the spline L2 (the one regulariser). Soft PINN: F(t,x,z) = t g(t,x,z), tanh MLP 32x3, z in R^2, residual dF/dt - A/(1+F), lambda_res in {0.01, 0.1, 1} (the one regulariser), Adam 2,500 steps; label-free fixed collocation sets resampled each step: (a) 24 times per training cell from the end of its record (primary) or from 0 (sensitivity) to the fixed horizon t_n = 1.8, (b) 256 Latin-hypercube stress points inside the design hull x 16 times; no calendar twins (no storage arm). Test cells: (z_c, delta_c) inferred from the window plus the residual over (window end, t_max] with network and law frozen, same MAP weights as training; no label after the window is used.
- **Protocol per draw:** 12 of 63 conditions held out (same split as P4, seeded); inner grouped CV (2 folds by condition) on the 51 training conditions, equal budget (3 values x 2 folds + 1 refit per arm); window = first 4 check-ups after the initial one; cells with >= 8 check-ups scored.
- **Code and tests:** commit 992b5b4 (`config.json`; code files clean at run time); 14 unit tests pass (`code/tests/test_p45_units.py`, includes: known G1 parameters give the linear/knee curves, PINN residual is zero for the exact solution and non-zero for a wrong rate, RK4/closed-form agreement). `code/pilots/p5_lambda_sensitivity.py` was added after the main run (post hoc, committed with these results).
- **Cost:** about 1,160 s CPU for the main run (two processes, 1 thread each; 210-242 s per draw, about 100-115 s per PINN variant), plus the sensitivity run. `config.json` was written by both processes (the later one overwrote the field `draws_in_this_process`: draws 0-2 ran in `driver_a.log`, 3-4 in `driver_b.log`). Peak RAM not measured (same stack as P2: under 1 GB).
- **Limits:** one PINN architecture and optimiser setting (no tuning beyond lambda_res); 5 draws; hard ODE tuned only over the spline L2 (insensitive: inner-CV 4.9-6.2 pp for all three values); stress-map hidden width and grid fixed at 3 and 5 in both arms; no G0 and no real-data cell touched.

Files: `config.json`, `summary.json`, `draw_0..4.json` (inner-CV tables, per-cell RMSE, train RMSE), `sens_lambda_10.json`, `driver_a.log`, `driver_b.log`, `driver_sens.log`.
