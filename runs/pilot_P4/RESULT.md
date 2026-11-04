# P4 result: synthetic KAN vs additive GAM vs free G (G2 on the ISU design, 5 draws), 2026-11-04

Judge rule (D010 section 7, P4): **Go** if KAN has lower nRMSE than the additive GAM in >= 4 of 5 draws AND structured is below free G in >= 4 of 5 draws.
No-go (KAN): KAN ~ additive GAM even on G2, tell the lead tonight, no change to the plan. No-go (structure): free G as good, identifiability figure dropped.
Synthetic data only; no real label or test split is involved. Numbers below are all in `summary.json` and `draw_*.json` of this folder.

## Verdict: GO on both parts, with a small KAN margin
| Part | Result | Rule |
|---|---|---|
| KAN lower nRMSE than additive GAM | **4 of 5 draws** (draw 3 is the exception: GAM 0.079, KAN 0.082) | >= 4 -> Go |
| KAN-structured below free G | **5 of 5 draws** | >= 4 -> Go |

Recovery nRMSE of the log-rate surface on the fixed 500-point hull LHS (divided by the true range; absolute level included), per draw:

| Draw | KAN | additive GAM | free G | GAM class floor on the true surface |
|---|---|---|---|---|
| 0 | 0.078 | 0.097 | 0.100 | 0.050 |
| 1 | 0.101 | 0.119 | 0.157 | 0.070 |
| 2 | 0.079 | 0.142 | 0.210 | 0.074 |
| 3 | 0.082 | 0.079 | 0.141 | 0.066 |
| 4 | 0.081 | 0.103 | 0.133 | 0.065 |
| **median** | **0.081** | **0.103** | **0.141** | |

Median ratios: KAN/GAM 0.81, KAN/free 0.61, GAM/free 0.76. Against the section 6 thresholds (pass <= 0.15, fail > 0.30): KAN passes 5/5, GAM passes 5/5 (draw 2 at 0.142), free G passes 3/5 and is "partial" in draws 1 and 2.
Forecast RMSE on the 12 held-out conditions beyond a 4-check-up window (pp; noise sd is 0.5 pp), median over draws: KAN 0.89, GAM 0.96, free G 1.04
(KAN lower than GAM in 4 of 5, lower than free G in 5 of 5; differences of 0.0 to 0.1 pp between KAN and GAM, i.e. forecasting does not separate them).

## What to take from it (and what not)
1. **The KAN advantage over the GAM is real in sign but small.** The G2 I fixed has a weak interaction: the best additive spline fit of the TRUE surface already reaches nRMSE 0.05-0.07, so the GAM cannot fail the 0.15 pass line even in principle; the KAN gains about 0.02 nRMSE (median) on a 0.05-0.07 floor. With 5 draws no test is meaningful (a sign test at 4 of 5 has one-sided p = 0.19). Plan: the judge's "KAN superiority" wording is not supported by this pilot alone; the confirmatory G2 (20 draws, paired Wilcoxon) could still go either way. A stronger interaction (larger hinge H, product P) would be a defensible change of the confirmatory grid, but it must be fixed before looking at real data and I did not tune it after seeing results.
2. **Structured vs free G depends on how the level is scored.** The absolute metric has structured below free G in 5 of 5 draws for the KAN, but the free-G surface carries a level offset (its nRMSE falls from 0.141 to 0.102 median when means are removed: `nrmse_recovery_centered`). Centered, KAN < free G in 5 of 5 draws, but GAM < free G in only 1 of 5 and the median KAN/free ratio is 0.76, not 0.61. The section 6 criterion "structured median <= 0.67 x free-G median" holds on the absolute metric (KAN 0.61; GAM 0.76 fails) and fails centered (KAN 0.76). The identifiability figure survives for the KAN-structured model; for "any structured G" the claim is weaker. The free-G level offset comes from reading dy/dt at y = 0 of an unconstrained network and is a property of the arm as I defined it.
3. **Hyperparameter edges.** The KAN's hidden width sat at an edge of {2,3,4} in all 5 draws (4 in draws 0, 1, 2, 4; 2 in draw 3) and its grid at an edge of {3,5,8} in 4; GAM grid and L2 sat at an edge in 3 draws; free-G width at an edge in 4. The grids should be extended in the confirmatory run (judge rule: an edge optimum extends the grid); with 8 random trials out of 27 or 12 combinations per arm the search is also coarse.
4. **Capacity is not matched in parameters.** Chosen models: KAN 57-193 parameters, GAM 28-43, free G 402-1,314 (excluding per-cell offsets). The GAM search allowed grids up to 30 (up to 102 parameters) and the tuner preferred 5-10; the KAN's flexibility came from its hidden layer, which is the point of the test, but "matched effective capacity" is only bracketed by the search spaces, not enforced. Effective degrees of freedom were not computed.
5. All arms fit the training data to the noise floor (train RMSE 0.47-0.58 pp against the 0.5 pp noise), so differences are not under-fitting.

## Setup (so that the numbers can be read)
- **Design:** the real ISU design: 63 conditions (C_ch, C_dch, DoD), 251 cells with their own check-up weeks (columns `cell, group, week` only; no capacity value read). Stress scaled to [-1, 1]. Forcing nu = cycles/week from a nominal cycle duration (DoD/C_ch + DoD/C_dch + 0.5 h rest), normalised by the median.
- **G2 truth** (`code/pilots/synth_gen.py`): log-rate surface f(x) = b.x + q x3^2 + H relu(x1 - (c0h + c1h x3)) + P x2 x3, dy/dt = exp(f + c0 + delta_c) nu_norm / (1 + y), state y_s = 10 x retention loss. Parameters drawn per draw from a fixed grid (`config.json`), level constant c0 solved so the median final y_s is exactly 2.0 (20 pp) per draw; per-cell log-rate offsets delta_c ~ N(0, 0.15^2); noise sd 0.05 in y_s (0.5 pp), first check-up exact. Truth is never fitted from a model.
- **Adaptation to ISU (needed, stated):** ISU has one temperature and no SOC window, so the judge's "charge-rate hinge whose threshold shifts with temperature" became a charge-rate hinge whose threshold shifts with DoD, and "DoD x SOC" became DoD x C_dch. Nominal constants (noise, offset sd, fade level 2.0) are round numbers chosen by me, not computed from ISU labels.
- **Models:** hard ODE with exact integration (y = sqrt(1 + 2At) - 1, tested against RK4) and stress map KAN [3,h,1] or additive spline GAM (= KAN [3,1]); free G = dy/dt = exp(MLP(y, x, log nu, z_c)) integrated by RK4 (dt 0.1 in t_n) with Hermite interpolation. Own compact B-spline KAN from `code/models/kan_spline.py` (reused by import) with hidden-layer grid widened to [-2, 2] in the new module `code/models/ageing_p45.py`; no pykan. Same nominal noise/offset scales in every loss.
- **Protocol per draw:** 12 of 63 conditions held out (seeded); on the 51 training conditions, 8 random hyperparameter trials per arm x 2 inner folds grouped by condition (score = window-forecast RMSE on the inner held-out conditions), then one refit; held-out cells: delta_c / z_c fitted on the first 4 check-ups after the initial one, forecast the rest, cells with >= 8 check-ups scored (40-48 cells). Recovery metric on the same fixed 500-point LHS inside the 63-condition hull (seed 12345), saved per draw in `surfaces_draw_*.npz` (columns: lhs, f_true, f_kan, f_gam, f_free) for the identifiability figure. Kendall tau of variance-based importance was not computed.
- **Code and tests:** commit 992b5b4 (`config.json` records it; code files clean at run time). 14 unit tests pass before any run (`code/tests/test_p45_units.py`): known G2/G1 parameters reproduce known surface values and curves (RK4 against the closed form), level matching, noise statistics, hull LHS, additive-GAM floor, KAN parameter counts, exact-solution PINN residual = 0, and a noiseless additive truth recovered by GAM and KAN with nRMSE < 0.10.
- **Cost:** 1,331 s CPU in total (one process, 1 thread; 255-290 s per draw, of which about 220 s is the free-G arm); peak RAM was not measured (under 1 GB expected: same stack as P2, 735-840 MB there).
- **Not done / limits:** G0 (well-specified sanity) and the "KAN must not exceed GAM by > 10 % on G0" check; interval widths; 20 draws; PINN and hard-ODE-KAN as separate arms (here hard-ODE-KAN is the structured arm, as the brief for P4 specifies).

Files: `config.json`, `summary.json`, `draw_0..4.json` (hyperparameter tables, chosen settings, all metrics), `surfaces_draw_*.npz`, `driver.log`.
