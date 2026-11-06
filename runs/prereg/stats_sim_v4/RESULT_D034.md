# D034 re-simulation: P3 against (32, 2), modifier M3, FWER guard of the primary graph (2026-11-06)

**Simulation outputs only.** Every number below is a property of the generating model of `RESULT.md` section 2 (code `sim_v4.py`, extended by
`code/prereg/stats_sim_d034.py`), not a result about PINN-KAN, the Samsung cells or any real data. No Samsung capacity value, outer-test score or
outer-test prediction was opened or produced; inputs are the condition identifiers/folds/labs (`cond_structure.csv`) and the ISU training-side
shape of the skew (`stats_ruling/cond_isu_W4.csv`), as before. CPU only, 3 processes. Role: statistician. Reading depth: full text of
`debates/D033_signoff/01_judge.md` (AD1, AD2), `RESULT_weights.md`, `RESULT.md` sections 1-5.3, `sim_v4.py` (generator, items b, d, g); `DECISIONS.md` D033, D034;
PREREG_v4 4.1-4.2 and 9.x partly (grep of the P+/PC-3/R1 passages).
Files: `d034_p3_power_*.csv`, `d034_p3_size_*.csv` (+ `d034_size_hist_*.json`), `d034_guard_k*.csv`, `d034_chain.csv`, `d034_m3_*.csv`, `d034_checks.json`, `d034_decision.json`,
logs `log_d034_*.txt`; code `code/prereg/stats_sim_d034.py` (simulation) and `code/prereg/stats_sim_d034_report.py` (this file).
Seeds: `SeedSequence([20261105, crc32(name)])`, names prefixed `d034`. Replicates: 40,000 (power, chain, M3), 100,000 per size scenario, 50,000 per guard configuration.

## 0. Verdicts

| Item | Finding (simulation) |
|---|---|
| **FWER guard of the primary graph, w = 0.78, new P3 contrast** | **PASS.** Maximum FWER over 72 configurations x 2 settings = 0.0188 at corr(g1, g4) = 0.6 (plan value) and 0.0192 over corr 0.3 / 0.6 / 0.9; bound 0.025 + 2 MC SE = 0.0264. Before D034 (RESULT_weights.md): 0.0189. |
| P3 power at the plan's effect sizes | up. With the plan's chain (r1 0.20, r2 0.15, gain at (32,2) = 0.05, rho 0.75, corr(g1,g4) 0.6, w = 0.78) P(P1N,P1S,P2,P3) rises from 0.530 to 0.674 (independent conditions) and from 0.485 to 0.587 (intra-fold 0.10, intra-lab 0.05); P3 alone (30 of 40) at a true median D of 0.15 / 0.20: 0.46 to 0.66 and 0.80 to 0.93. |
| Size of the P3 node (new contrast) | In region R4 (intra-fold <= 0.10, intra-lab <= 0.05, the region the fallback was set for) the worst simulated rejection rate of the 30-of-40 rule is 0.75 x 0.0195 (0.58 x 0.025); the old contrast gave 0.69 x 0.0195. Inside R4 the node is below 1.2 x nominal: yes. Outside R4 see section 4. |
| M3 (A1 not better than R1 at g1; 30 of 40; outside the graph) | The test has the same size as every other 30-of-40 node (0.80 x 0.025 at worst in R4). Effect on P(P+ title) (title = P+ with M3 passing; M1/M2 ignored): **loss 0 to 0.98 in absolute probability over the whole assumption range**, 0.000 to 0.002 if A1 beats persistence by 40-60 % (the training-side pilot ratio), 0.00 to 0.47 at 20-30 %, 0.01 to 0.92 at 10-15 %. See section 6. |

## 1. What changed and the assumption about L_c(32, 2)

**AD1.** P3 now tests the sign of D_c = L_c(g1) - L_c(32, 2), g1 = (m 8, k 2), same window, forecast set and caps at both cells.
**What the generator says about L_c(32, 2) against L_c(32, 4) (= g4).** `sim_v4.py` models the 9 grid cells (m = 8, 16, 32 by k = 0, 2, full; cell index 3 i_m + i_k, g1 = 1, (32,2) = 7, g4 = 8) with a **separable AR(1) latent variable**, coefficient a in both directions, corr(g1, g4) = a^3 = kappa14, and
a fold/lab share that depends on **m only** (multiplier 1 / 0.75 / 0.5, "same for every k"). Nothing else links the cells. Three consequences, none invented:
1. corr(L(g1), L(32,2)) = a^2 = kappa14^(2/3): **0.711** at the plan's 0.6 (it was 0.6 for g4); 0.448 and 0.932 for the 0.3 and 0.9 sensitivity values. corr(L(32,2), L(32,4)) = a = 0.843.
2. (32,2) has the **same fold/lab share and the same marginal law** as g4, so a (g1, (32,2)) contrast differs from a (g1, g4) contrast only through the cross-cell correlation: the new D model with kappa14 equals the old D model with kappa = kappa14^(2/3) (checked to 1e-9, `d034_checks.json`; the K and P1/P2 contrasts reproduce `sim_v4.build_model` to 1e-15).
3. **The generator does not say how large the PINN-KAN advantage is at (32,2).** The plan's effect sizes are a gain r1 at g1 and a gain r4 at g4 (the median of D is their difference on the log scale). I carry the gain at (32,2), r_c, as a parameter: the main reading is **r_c = r4 = 0.05** (k does not change the advantage at m = 32, the same way k does not change the fold/lab share in the generator), and r_c = 0, 0.10, 0.15 are shown (section 3.2). A smaller r_c is more favourable to P3 (larger median D). Power is also given as a function of the median of D itself (3.1), which needs no reading of r_c.
Whether the advantage really depends on k at fixed m is an empirical question that no file answers; if (32,2) lies between g1 and g4 in advantage, the median D is smaller than in the plan and power is lower than shown.

## 2. P3 power

### 2.1 P3 alone: sign test of D > 0, ISU-like right skew, rho(A1,D*) 0.75, corr(g1,g4) = 0.6 (so corr(g1,(32,2)) = 0.711), fallback rho_s0 = 0.03

"fb30" = 30 of 40, the count at both levels P3 can face with w = 0.78 (0.0195 with the P chain alone, 0.025 after the K chain); "fb31" = 31 of 40, the 0.0125 count of the earlier tables (RESULT.md 5.3) shown for comparison; old = D = L(g1) - L(g4), new = D = L(g1) - L(32,2); both have median D = "median_D" and come from the same draws.

| clustering | median_D | old_fb30 | new_fb30 | old_fb31 | new_fb31 | old_plain | new_plain |
|---|---|---|---|---|---|---|---|
| independent conditions | 0.050 | 0.021 | 0.032 | 0.008 | 0.014 | 0.089 | 0.119 |
| independent conditions | 0.100 | 0.149 | 0.248 | 0.081 | 0.148 | 0.359 | 0.502 |
| independent conditions | 0.150 | 0.462 | 0.661 | 0.323 | 0.519 | 0.728 | 0.868 |
| independent conditions | 0.200 | 0.795 | 0.928 | 0.674 | 0.858 | 0.938 | 0.986 |
| independent conditions | 0.300 | 0.994 | 1.000 | 0.982 | 0.998 | 0.999 | 1.000 |
| intra-fold 0.10 | 0.050 | 0.046 | 0.062 | 0.024 | 0.034 | 0.130 | 0.168 |
| intra-fold 0.10 | 0.100 | 0.191 | 0.284 | 0.120 | 0.190 | 0.386 | 0.507 |
| intra-fold 0.10 | 0.150 | 0.476 | 0.643 | 0.356 | 0.524 | 0.701 | 0.829 |
| intra-fold 0.10 | 0.200 | 0.758 | 0.893 | 0.652 | 0.826 | 0.907 | 0.969 |
| intra-fold 0.10 | 0.300 | 0.985 | 0.998 | 0.967 | 0.994 | 0.997 | 1.000 |
| intra-fold 0.10, intra-lab 0.05 | 0.050 | 0.072 | 0.092 | 0.042 | 0.056 | 0.166 | 0.202 |
| intra-fold 0.10, intra-lab 0.05 | 0.100 | 0.232 | 0.316 | 0.161 | 0.230 | 0.407 | 0.509 |
| intra-fold 0.10, intra-lab 0.05 | 0.150 | 0.485 | 0.632 | 0.381 | 0.527 | 0.682 | 0.807 |
| intra-fold 0.10, intra-lab 0.05 | 0.200 | 0.743 | 0.872 | 0.648 | 0.805 | 0.881 | 0.951 |
| intra-fold 0.10, intra-lab 0.05 | 0.300 | 0.973 | 0.995 | 0.950 | 0.990 | 0.993 | 0.999 |

Size at median D = 0 (30 of 40): 0.0012 independent conditions; 0.0161 with intra-fold 0.10 and intra-lab 0.05 (copula form of items b-d, all contrasts share the same fold and lab shares).
80 %-power median D (30 of 40, linear interpolation on the grid 0, .05, .10, .15, .20, .30, .40): old 0.202, new 0.176 (independent); old 0.225, new 0.185 (clustered). Over all shapes, rho(A1,D*) 0.6 / 0.75 / 0.9 and corr 0.3 / 0.6 / 0.9 the new 80 % point is lower than the old by 0.009 to 0.051 (log units of median D). The new contrast has no lower power than the old one at equal median D beyond Monte Carlo noise (SE of a rate <= 0.0025) in any of the 567 cells simulated (smallest difference -0.0018; the gain comes only from the higher correlation, 0.711 against 0.6).

### 2.2 Why the power is higher, and what it does not mean
The SD of D falls because L(g1) and L(32,2) are more strongly correlated than L(g1) and L(g4). It is not evidence that the effect is larger: the **median D to be detected is a different quantity** whenever the gain at (32,2) differs from the gain at g4. Under r_c = r4 the medians coincide and the power gain is real; if the advantage at (32,2) lies above that at g4, the median D shrinks and part or all of the gain is lost (3.2: with independent conditions and rhoK 0.95, P(also P3) is 0.33 at r_c = 0.10 and 0.67 at r_c = 0.05).

## 3. P3 in the primary graph (w = 0.78, fallback counts, K chain running)

### 3.1 Plan point (rho(A1,D*) 0.75, rho(A1,A9) 0.95, r1 0.20, r2 0.15, r_c = r4 = 0.05, corr(g1,g4) 0.6, A15 as good as A1, K2 gain 0.05; 40,000 replicates; same draws for old and new)
`prior` = the value printed in `RESULT_weights.md` for the old contrast (20,000 replicates, different seeds; the difference to the `old` column, up to about 0.01, is Monte Carlo noise).

| clustering | rhoK | P_Pp | P_P2 | P_P3_old | prior_P3_RESULT_weights | P_P3_new | d_P3 | se_d_P3 | P_K1 |
|---|---|---|---|---|---|---|---|---|---|
| independent conditions | 0.900 | 0.823 | 0.821 | 0.533 | 0.525 | 0.676 | 0.144 | 0.002 | 0.379 |
| independent conditions | 0.950 | 0.821 | 0.819 | 0.530 | 0.525 | 0.674 | 0.144 | 0.002 | 0.766 |
| intra-fold 0.10, intra-lab 0.05 | 0.900 | 0.765 | 0.754 | 0.491 | 0.489 | 0.590 | 0.099 | 0.002 | 0.408 |
| intra-fold 0.10, intra-lab 0.05 | 0.950 | 0.761 | 0.750 | 0.485 | 0.491 | 0.587 | 0.102 | 0.002 | 0.709 |


P(P1N,P1S) and P(also P2) do not change (the new contrast does not enter those nodes); only P3 does. `P_K1` is for the new contrast (K1 receives the P3 hand-over when P3 is rejected); the old-contrast values are in RESULT_weights.md (0.734 / 0.693 at rhoK 0.95, K1 median 0).
Range over the four settings: old 0.485-0.533, new 0.587-0.676.

### 3.2 Dependence on r_c (gain at (32,2)), rhoK 0.95, r1 0.20, corr(g1,g4) 0.6

| clustering | r_c | P_P3_old | P_P3_new | d_P3 | P3_node_alone_new |
|---|---|---|---|---|---|
| independent conditions | 0.000 | 0.736 | 0.800 | 0.064 | 0.972 |
| independent conditions | 0.050 | 0.530 | 0.674 | 0.144 | 0.807 |
| independent conditions | 0.100 | 0.217 | 0.335 | 0.118 | 0.388 |
| independent conditions | 0.150 | 0.032 | 0.051 | 0.019 | 0.056 |
| intra-fold 0.10, intra-lab 0.05 | 0.000 | 0.645 | 0.708 | 0.063 | 0.929 |
| intra-fold 0.10, intra-lab 0.05 | 0.050 | 0.485 | 0.587 | 0.102 | 0.756 |
| intra-fold 0.10, intra-lab 0.05 | 0.100 | 0.270 | 0.349 | 0.079 | 0.425 |
| intra-fold 0.10, intra-lab 0.05 | 0.150 | 0.085 | 0.111 | 0.026 | 0.127 |

### 3.3 Dependence on corr(g1,g4) (r1 0.20, r_c 0.05, rhoK 0.95) and on r1 (corr 0.6)

| clustering | kappa14 | P_P3_old | P_P3_new | d_P3 |
|---|---|---|---|---|
| independent conditions | 0.300 | 0.281 | 0.378 | 0.097 |
| independent conditions | 0.600 | 0.530 | 0.674 | 0.144 |
| independent conditions | 0.900 | 0.819 | 0.820 | 0.001 |
| intra-fold 0.10, intra-lab 0.05 | 0.300 | 0.329 | 0.392 | 0.063 |
| intra-fold 0.10, intra-lab 0.05 | 0.600 | 0.485 | 0.587 | 0.102 |
| intra-fold 0.10, intra-lab 0.05 | 0.900 | 0.750 | 0.754 | 0.004 |

| clustering | r1 | P_Pp | P_P3_old | P_P3_new | d_P3 |
|---|---|---|---|---|---|
| independent conditions | 0.150 | 0.416 | 0.112 | 0.167 | 0.055 |
| independent conditions | 0.200 | 0.821 | 0.530 | 0.674 | 0.144 |
| independent conditions | 0.250 | 0.983 | 0.908 | 0.966 | 0.058 |
| intra-fold 0.10, intra-lab 0.05 | 0.150 | 0.457 | 0.171 | 0.213 | 0.041 |
| intra-fold 0.10, intra-lab 0.05 | 0.200 | 0.761 | 0.485 | 0.587 | 0.102 |
| intra-fold 0.10, intra-lab 0.05 | 0.250 | 0.947 | 0.816 | 0.892 | 0.076 |

## 4. Size of the P3 node and of the M3 test (generator (a) of sim_v4: additive skew form, fold/lab share scaled by m, random lab effects = pessimistic reading)

Worst simulated rejection rate at the null boundary of the 30-of-40 rule, over the scenarios of each region (3 error shapes; corr(g1,g4) 0.6; 100,000 replicates per scenario; MC SE of a rate of 0.02: 0.0004), as a multiple of the nominal level. "P3 new" and "P3 old" are against 0.0195 (the P-chain level at w = 0.78; against 0.025 divide by 1.28); "M3 at g1" is the sign test of L_R1 > 0 at g1 against 0.025.

| region | P3_new_vs_0.0195 | P3_new_vs_0_025 | P3_old_vs_0_0195 | M3_g1_vs_0_025 |
|---|---|---|---|---|
| R1: fold <= 0.05, lab 0 | 0.16 | 0.13 | 0.15 | 0.14 |
| R2: fold <= 0.10, lab 0 | 0.28 | 0.22 | 0.29 | 0.29 |
| R3: fold <= 0.10, lab <= 0.02 | 0.45 | 0.35 | 0.42 | 0.51 |
| R4: fold <= 0.10, lab <= 0.05 | 0.75 | 0.58 | 0.69 | 0.80 |
| R5: fold <= 0.20, lab <= 0.05 | 1.22 | 0.95 | 1.17 | 1.29 |
| R6: fold <= 0.20, lab <= 0.10 | 1.78 | 1.39 | 1.68 | 1.84 |

* The re-open condition of D033 ("the node's size above 1.2 x nominal") is **not met inside R4** for the new contrast: worst 0.75. Beyond R4 the 30-of-40 rule (rho_s0 = 0.03) exceeds 1.2 x nominal in 22 of 75 scenario cells for the new contrast (20 for the old); the (intra-fold, intra-lab) pairs concerned are [(0.0, 0.2), (0.02, 0.2), (0.05, 0.2), (0.1, 0.1), (0.1, 0.2), (0.2, 0.05), (0.2, 0.1), (0.2, 0.2)], i.e. 0 scenario cells lie inside R4 (RESULT.md 4.4 already reported that the fallback does not cover R5-R6). The M3 test at g1 exceeds 1.2 x 0.025 in 21 scenario cells, 0 of them inside R4 (pairs: [(0.0, 0.2), (0.02, 0.2), (0.05, 0.2), (0.1, 0.1), (0.1, 0.2), (0.2, 0.05), (0.2, 0.1), (0.2, 0.2)]).
* The new contrast is slightly **less conservative** than the old one (higher cross-cell correlation, so less cancellation between the two cells): ratio new/old of the worst rate is 1.02 over all random-effect scenarios.
* With lab effects as fixed design offsets (the optimistic reading), the worst new rate is 0.31 x 0.0195 over 27 scenario cells.
* Sensitivity to corr(g1,g4) (isu_right, rates of the 30-of-40 rule; M3 at g1 does not depend on it):

| kappa14 | f | l | fb30_old | fb30_new | fb30_g1 |
|---|---|---|---|---|---|
| 0.3000 | 0.0000 | 0.0000 | 0.0011 | 0.0011 | 0.0012 |
| 0.6000 | 0.0000 | 0.0000 | 0.0011 | 0.0012 | 0.0013 |
| 0.9000 | 0.0000 | 0.0000 | 0.0011 | 0.0010 | 0.0011 |
| 0.3000 | 0.0500 | 0.0000 | 0.0026 | 0.0027 | 0.0036 |
| 0.6000 | 0.0500 | 0.0000 | 0.0030 | 0.0032 | 0.0034 |
| 0.9000 | 0.0500 | 0.0000 | 0.0039 | 0.0048 | 0.0039 |
| 0.3000 | 0.1000 | 0.0500 | 0.0126 | 0.0123 | 0.0197 |
| 0.6000 | 0.1000 | 0.0500 | 0.0134 | 0.0144 | 0.0201 |
| 0.9000 | 0.1000 | 0.0500 | 0.0201 | 0.0232 | 0.0206 |

## 5. FWER guard of the primary graph (w = 0.78 on P1N, 0.22 on K1; initial levels 0.0195 and 0.0055; counts 30 and 32)

Item (d)/(g) implementation guard re-run with the new P3 contrast: 72 configurations (L1 x L2 x D x K1 x K2 at null/mid/alt) x 2 settings (independent conditions; intra-fold 0.10 with intra-lab 0.05, random labs), fallback rho_s0 = 0.03, 50,000 replicates each (MC SE of a rate near 0.02: 0.0007). A configuration's FWER counts a replicate when any true-null node is rejected; D = null means median(L(g1) - L(32,2)) = 0. The graph test is valid under any dependence; this is an implementation check.

| kappa14 | setting | configs | max_FWER | config_at_max | mean_FWER | nrep |
|---|---|---|---|---|---|---|
| 0.3000 | fold10_lab05_fb0.03 | 72 | 0.0192 | null|alt|alt|alt|null | 0.0137 | 50000 |
| 0.3000 | iid_fb0.03 | 72 | 0.0016 | alt|null|null|null|mid | 0.0009 | 50000 |
| 0.6000 | fold10_lab05_fb0.03 | 72 | 0.0188 | alt|null|alt|null|null | 0.0137 | 50000 |
| 0.6000 | iid_fb0.03 | 72 | 0.0015 | alt|null|null|null|alt | 0.0009 | 50000 |
| 0.9000 | fold10_lab05_fb0.03 | 72 | 0.0190 | alt|null|null|null|alt | 0.0138 | 50000 |
| 0.9000 | iid_fb0.03 | 72 | 0.0015 | null|null|alt|null|mid | 0.0009 | 50000 |

Bound = 0.025 + 2 x 0.0007 = 0.0264. Maximum over everything = 0.0192; at the plan value (corr 0.6) 0.0188 (RESULT_weights.md, old contrast: 0.0189).
**FWER guard: PASS.** M3 is outside the graph and adds no rejection to it; the P+ title now requires P1S (graph) and M3, so the probability of a false P+ title cannot exceed the graph's FWER (intersection of two events). No alpha is added.

## 6. M3: effect on P(P+ title)

**Model.** R1 (persistence) is a further leaf of the arm tree below A1 (like D*, A9, A15), correlation rhoR of the log condition errors with A1, same error shape, same fold/lab shares as the other contrasts, same draws as the graph. L_R1 = ln S_R1 - ln S_A1 at g1; gR = true median relative gain of A1 over R1 (median L_R1 = ln(1/(1 - gR))). M3 passes iff at least 30 of 40 conditions have L_R1 > 0 (fallback, level 0.025). "P(P+)" = P(P1N and P1S rejected in the graph); "P(P+ title)" = P(P+ and M3 passes); the loss is the difference. Titles T1-T3 (and T9a/T9b) are what M3 removes; M1 and M2 are not modelled (M3 acts independently of them).
**What the files hold.** Nothing about A1 against R1 at g1: no Samsung value exists and no pilot file gives A1 against persistence at g1. The only anchor is the training-side pilot P3 (ISU W4/W6, SNL W100/W200, full training data, not g1, best data-only learner not A1): cell RMSE of persistence is 13.22 / 12.54 / 10.83 / 7.71 pp against 5.21 / 4.87 / 2.97 / 2.54 for tuned LightGBM, i.e. persistence is 2.5-3.6 times worse, a relative reduction of 0.60-0.72 for a learner. That is an RMSE ratio of means, not a median of condition log ratios, and at g1 (8 conditions, 2 check-ups) the learners are weaker; it is why the bands start at 0.40 for "anchored". rhoR is not anchored at all (0.50 / 0.75 / 0.90 shown).

Primary table (ISU-like skew, r1 0.20, rhoK 0.95, w = 0.78): P(P+ title) = P(P+ & M3) for each gR and rhoR, and P(P+) without M3.

| clustering | gR | P(P+) | P(P+ & M3) rhoR=0.50 | P(P+ & M3) rhoR=0.75 | P(P+ & M3) rhoR=0.90 |
|---|---|---|---|---|---|
| independent conditions | 0.000 | 0.821 | 0.001 | 0.001 | 0.001 |
| independent conditions | 0.050 | 0.821 | 0.010 | 0.021 | 0.071 |
| independent conditions | 0.100 | 0.821 | 0.060 | 0.160 | 0.483 |
| independent conditions | 0.150 | 0.821 | 0.205 | 0.469 | 0.802 |
| independent conditions | 0.200 | 0.821 | 0.445 | 0.746 | 0.826 |
| independent conditions | 0.300 | 0.821 | 0.797 | 0.822 | 0.827 |
| independent conditions | 0.400 | 0.821 | 0.821 | 0.822 | 0.827 |
| independent conditions | 0.500 | 0.821 | 0.821 | 0.822 | 0.827 |
| independent conditions | 0.600 | 0.821 | 0.821 | 0.822 | 0.827 |
| intra-fold 0.10, intra-lab 0.05 | 0.000 | 0.763 | 0.012 | 0.012 | 0.012 |
| intra-fold 0.10, intra-lab 0.05 | 0.050 | 0.763 | 0.043 | 0.064 | 0.132 |
| intra-fold 0.10, intra-lab 0.05 | 0.100 | 0.763 | 0.121 | 0.211 | 0.444 |
| intra-fold 0.10, intra-lab 0.05 | 0.150 | 0.763 | 0.256 | 0.436 | 0.710 |
| intra-fold 0.10, intra-lab 0.05 | 0.200 | 0.763 | 0.424 | 0.652 | 0.763 |
| intra-fold 0.10, intra-lab 0.05 | 0.300 | 0.763 | 0.710 | 0.765 | 0.765 |
| intra-fold 0.10, intra-lab 0.05 | 0.400 | 0.763 | 0.762 | 0.767 | 0.765 |
| intra-fold 0.10, intra-lab 0.05 | 0.500 | 0.763 | 0.763 | 0.767 | 0.765 |
| intra-fold 0.10, intra-lab 0.05 | 0.600 | 0.763 | 0.763 | 0.767 | 0.765 |

Range over everything simulated (ISU-like skew; settings independent / clustered, rhoK 0.90 / 0.95, r1 0.15 / 0.20 / 0.25, rhoR 0.50 / 0.75 / 0.90; the band is the range of the gR values listed):

| band | abs_loss_min | abs_loss_max | rel_loss_min | rel_loss_max | P_Pplus_min | P_Pplus_max | P_title_after_min | P_title_after_max |
|---|---|---|---|---|---|---|---|---|
| anchored: gR 0.40-0.60 | 0.000 | 0.002 | 0.000 | 0.002 | 0.412 | 0.983 | 0.412 | 0.983 |
| moderate: gR 0.20-0.30 | 0.000 | 0.466 | 0.000 | 0.474 | 0.412 | 0.983 | 0.235 | 0.983 |
| weak: gR 0.10-0.15 | 0.012 | 0.916 | 0.028 | 0.932 | 0.412 | 0.983 | 0.032 | 0.954 |
| none: gR 0-0.05 | 0.368 | 0.982 | 0.820 | 0.999 | 0.412 | 0.983 | 0.000 | 0.159 |

Shape sensitivity (relative loss of P(P+ title), r1 0.20, rhoK 0.95, rhoR 0.75):

| shape | gR | rel_loss_independent | rel_loss_fold10_lab05 |
|---|---|---|---|
| isu_left | 0.050 | 0.981 | 0.923 |
| isu_left | 0.100 | 0.872 | 0.779 |
| isu_left | 0.150 | 0.622 | 0.567 |
| isu_left | 0.200 | 0.368 | 0.373 |
| isu_left | 0.300 | 0.017 | 0.049 |
| isu_right | 0.050 | 0.975 | 0.917 |
| isu_right | 0.100 | 0.806 | 0.725 |
| isu_right | 0.150 | 0.430 | 0.432 |
| isu_right | 0.200 | 0.093 | 0.150 |
| isu_right | 0.300 | 0.000 | 0.003 |
| normal | 0.050 | 0.985 | 0.937 |
| normal | 0.100 | 0.906 | 0.818 |
| normal | 0.150 | 0.660 | 0.591 |
| normal | 0.200 | 0.301 | 0.321 |
| normal | 0.300 | 0.005 | 0.024 |

P(P1N,P1S,P2,P3 rejected) and with M3 passing (rhoR 0.75, rhoK 0.95, r1 0.20):

| f | gR | P_P3chain | P_P3chain_M3pass |
|---|---|---|---|
| 0.000 | 0.100 | 0.672 | 0.131 |
| 0.000 | 0.200 | 0.672 | 0.610 |
| 0.000 | 0.300 | 0.672 | 0.672 |
| 0.000 | 0.600 | 0.672 | 0.672 |
| 0.100 | 0.100 | 0.591 | 0.164 |
| 0.100 | 0.200 | 0.591 | 0.502 |
| 0.100 | 0.300 | 0.591 | 0.589 |
| 0.100 | 0.600 | 0.591 | 0.591 |

**Reading.** P(P+) is 0.41-0.98 across all simulated P-side settings (r1 0.15-0.25) and 0.76-0.83 at the plan's r1 0.20. If A1 beats persistence by 30 % or more at g1, M3 costs at most 0.07 in absolute probability (rhoR <= 0.90) and at 40 % or more at most 0.002; at a 20 % gain it costs 0.00 to 0.47 depending on rhoR and the setting; at 10-15 % it removes 3% to 93% of the P+ titles; at 0-5 % it removes 82% to 100%, which is the intended behaviour: a network no better than carrying the last check-up forward should not carry T1-T3. The loss is therefore not a fixed number: it is the probability that A1 is within roughly 10-20 % of persistence at g1 (more exactly, that fewer than 30 of 40 conditions favour A1), and no file holds that probability. The lower rhoR is, the more the 30-of-40 rule demands of a given gain.

## 7. Limits
* All numbers are simulation values under the generator of `RESULT.md` section 2; rho_s0 = 0.03 is assumed adequate (no measured dependence); the m-scaling of fold/lab shares in section 4 is the assumption of sim_v4 (1 / 0.75 / 0.5), while the power tables of sections 2-3 use one share for all contrasts, as items b-d did.
* The gain at (32,2), the effect of M3's R1 comparison (gR, rhoR) and the correlation of R1 with A1 are assumptions with no data behind them.
* Section 2.1's 80 % points are interpolated on a coarse grid. Section 4 covers the 3 error shapes, the guard only ISU-like right skew (as in RESULT_weights.md). Counts at reduced n were not simulated.
* Not tested here: the P3 contrast if (32,2) is capped or scored on fewer conditions than g1 (D032 lists capped cells; condition-level n stays 40).
