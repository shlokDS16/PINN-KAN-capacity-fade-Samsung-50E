# Graph weights (D018 section 3, item g) and fallback tables (A3), 2026-11-05

**Simulation outputs only.** Models and inputs as in `RESULT.md` section 2 (no Samsung score, no outer-test data). Fallback test: Beta-binomial sign test, rho_s0 = 0.03.
Files: `g_weights.csv`, `g_guard.csv`, `g_decision.json`, `fb_tables.csv`, `f_upper_bound_coverage.csv`; code `sim_v4.py` (items `gsim`, `gguard`, `gdecide`), `build_fb_tables.py`,
`code/pinnkan/graph_test.py` (additive: `pinnkan_graph(w_p)`, `betabin_*`, `dep_*`, `secondary_graph`, `sign_icc_anova`, `dependence_report`), tests `code/tests/test_fallback_weights_secondary.py` and `test_graph_test.py`: all pass.

## 1. Decision (printed by the script; no person chooses)

**Rule (D018 section 3):** adopt w = 0.78 on P1N (0.22 on K1) iff the implementation guard passes and, in all four settings, dP + dK > 0 and dK >= -0.10, where dP = change in P(P chain through P3) and dK = change in P(K1), both w = 0.78 minus w = 1/2.

**Result: the rule picks w = 0.78 on P1N and 0.22 on K1** (initial levels 0.0195 and 0.0055; positives needed 30 and 32 of 40 under rho_s0 = 0.03).
Guard: maximum FWER over the 72 configurations x 2 settings = 0.0189, bound 0.025 + 2 MC SE = 0.0264: passed = True.

## 2. Simulation: both graphs on the same draws

Generator: arm model of RESULT section 2, ISU-like right skew; P side rho(A1,D*) 0.75, rho(A1,A9) 0.95, r1 = 0.20, r2 = 0.15, r4 = 0.05, corr(g1,g4) 0.6; K side A15 as good as A1 (excess 0.00), q = 0.05 over G15,
rho(A15,A1) = rho(A15,G15) = rho_K. Settings: independent conditions or intra-fold 0.10 with intra-lab 0.05 (random labs, the pessimistic reading) x rho_K 0.90 / 0.95; 20000 replicates per setting; both graphs use the same L draws (common random numbers); seeds SeedSequence([20261105, crc32(name)]).
Both chains run in the graph together (the K chain is not forced to fail): hand-overs act. "P(..,P3)" = P(P1N, P1S, P2 and P3 all rejected).

| setting                |   w on P1N |   P(P1N,P1S) |   P(..,P2) |   P(..,P3) |   P(K1) |   P(K1,K2N) |   P(K1,K2N,K2S) |
|:-----------------------|-----------:|-------------:|-----------:|-----------:|--------:|------------:|----------------:|
| g|f0.00|l0.00|rhoK0.90 |      0.500 |        0.704 |      0.698 |      0.360 |   0.379 |       0.338 |           0.005 |
| g|f0.00|l0.00|rhoK0.90 |      0.780 |        0.816 |      0.814 |      0.525 |   0.343 |       0.300 |           0.005 |
| g|f0.00|l0.00|rhoK0.95 |      0.500 |        0.708 |      0.702 |      0.365 |   0.781 |       0.777 |           0.030 |
| g|f0.00|l0.00|rhoK0.95 |      0.780 |        0.817 |      0.815 |      0.525 |   0.734 |       0.728 |           0.028 |
| g|f0.10|l0.05|rhoK0.90 |      0.500 |        0.675 |      0.655 |      0.367 |   0.424 |       0.355 |           0.026 |
| g|f0.10|l0.05|rhoK0.90 |      0.780 |        0.763 |      0.752 |      0.489 |   0.386 |       0.317 |           0.023 |
| g|f0.10|l0.05|rhoK0.95 |      0.500 |        0.682 |      0.663 |      0.373 |   0.732 |       0.718 |           0.074 |
| g|f0.10|l0.05|rhoK0.95 |      0.780 |        0.765 |      0.753 |      0.491 |   0.693 |       0.674 |           0.064 |

Differences (0.78 minus 0.5) with the paired Monte Carlo SE:

| setting                |   dP(P1N,P1S) |     SE |   dP (chain through P3) |    SE  |   dK (K1) |   SE   |   d(K1,K2N) |   d(K1,K2N,K2S) |
|:-----------------------|--------------:|-------:|------------------------:|-------:|----------:|-------:|------------:|----------------:|
| g|f0.00|l0.00|rhoK0.90 |        0.1119 | 0.0022 |                  0.1648 | 0.0026 |   -0.0364 | 0.0020 |     -0.0377 |          0.0006 |
| g|f0.00|l0.00|rhoK0.95 |        0.1085 | 0.0022 |                  0.1599 | 0.0026 |   -0.0473 | 0.0020 |     -0.0498 |         -0.0022 |
| g|f0.10|l0.05|rhoK0.90 |        0.0880 | 0.0020 |                  0.1224 | 0.0023 |   -0.0377 | 0.0018 |     -0.0384 |         -0.0036 |
| g|f0.10|l0.05|rhoK0.95 |        0.0835 | 0.0020 |                  0.1181 | 0.0023 |   -0.0398 | 0.0018 |     -0.0444 |         -0.0095 |

Rule check:

| setting                |     dP |      dK |   dP + dK | rule met (dP+dK>0 and dK>=-0.10)   |
|:-----------------------|-------:|--------:|----------:|:-----------------------------------|
| g|f0.00|l0.00|rhoK0.90 | 0.1648 | -0.0364 |    0.1285 | True                               |
| g|f0.00|l0.00|rhoK0.95 | 0.1599 | -0.0473 |    0.1126 | True                               |
| g|f0.10|l0.05|rhoK0.90 | 0.1224 | -0.0377 |    0.0847 | True                               |
| g|f0.10|l0.05|rhoK0.95 | 0.1181 | -0.0398 |    0.0784 | True                               |

**Reading.** At w = 0.78 the P chain through P3 gains 0.12 to 0.16 (about 0.49 against 0.37 with clustering, 0.52-0.53 against 0.36 without), and K1 loses 0.036 to 0.047 (0.73 to 0.69 at rho_K 0.95 with clustering, 0.78 to 0.73 without). The K chain's last
node K2S is almost unchanged (it needs a gain that is rare at q = 0.05). The K1 floor of -0.10 is far from binding. The trade-off is disclosed in the paper whichever w is used (D018 section 3). These are simulation values under the stated generator, not results.

## 3. Implementation guard

Item (d)'s 72 configurations with weights 0.78 / 0.22, fallback counts, 50,000 replicates each (MC SE of a rate near 0.02: 0.0007):

| setting             |   configs |   max_FWER | config_at_max            |   mean_FWER |   nrep |   max_FWER at w=1/2 (RESULT 7) |
|:--------------------|----------:|-----------:|:-------------------------|------------:|-------:|-------------------------------:|
| fold10_lab05_fb0.03 |        72 |     0.0189 | null|null|null|null|null |      0.0137 |  50000 |                         0.0159 |
| iid_fb0.03          |        72 |     0.0015 | null|null|null|alt|null  |      0.0009 |  50000 |                         0.0014 |

Both maxima are below 0.025 (bound 0.0264). With clustering the maximum is higher than at w = 1/2 (the P chain's first node now runs at 0.0195), still within the bound. The guard passed, so the decision rule applies. Unit test (`test_weight_alternative_initial_levels_and_counts`): initial levels 0.0195 and 0.0055; counts 30 and 32;
P(BetaBin >= 32) = 0.005352 <= 0.0055 and P(BetaBin >= 30) = 0.019356 <= 0.0195; hand-worked chain and K1 threshold tests also pass (30 positives reject the whole P chain at w = 0.78 and nothing at w = 1/2; K1 needs 32).

## 4. Fallback tables (A3, `fb_tables.csv`)

`fb_tables.csv` holds, for rho_s0 in (0, 0.01, 0.02, 0.03, 0.05), Test B n = 40 down to 35 and ISU n = 63 down to 58, the positives needed at every level in use (0.005, 0.00625, 0.00833, 0.0125, 0.025, and 0.0195 / 0.0055 for w = 0.78) with the size under the Beta-binomial null,
the size under independence and the one-sided lower-bound order statistic L_(n-k+1); and the interval ranks (two-sided 0.05, 0.05/9, 0.05/18) with their coverage. The Test B minimum is 36: only four z-type outer-test cells are exposed before the freeze (3.3(11), BL), so at most four conditions can be dropped; 35 is a margin.
ISU has 63 conditions (62 with both pilot scores, 60 at the 6-week window); the ISU rows apply only if the ISU fallback applies (D005), and the dependence simulation was for the Samsung fold/lab structure (D018 GAP-5).

Positives needed (rho_s0 = 0.03), Test B ("lvl" = local level):

|   n |   lvl 0.005 |   lvl 0.0055 |   lvl 0.00625 |   lvl 0.0083333 |   lvl 0.0125 |   lvl 0.0195 |   lvl 0.025 |
|----:|------------:|-------------:|--------------:|----------------:|-------------:|-------------:|------------:|
|  35 |          29 |           29 |            29 |              28 |           28 |           27 |          27 |
|  36 |          30 |           30 |            29 |              29 |           28 |           28 |          27 |
|  37 |          30 |           30 |            30 |              30 |           29 |           28 |          28 |
|  38 |          31 |           31 |            31 |              30 |           30 |           29 |          29 |
|  39 |          32 |           32 |            32 |              31 |           31 |           30 |          29 |
|  40 |          33 |           32 |            32 |              32 |           31 |           30 |          30 |

ISU:

|   n |   lvl 0.005 |   lvl 0.0055 |   lvl 0.00625 |   lvl 0.0083333 |   lvl 0.0125 |   lvl 0.0195 |   lvl 0.025 |
|----:|------------:|-------------:|--------------:|----------------:|-------------:|-------------:|------------:|
|  58 |          46 |           45 |            45 |              45 |           44 |           43 |          42 |
|  59 |          46 |           46 |            46 |              45 |           44 |           43 |          43 |
|  60 |          47 |           47 |            47 |              46 |           45 |           44 |          44 |
|  61 |          48 |           48 |            47 |              47 |           46 |           45 |          44 |
|  62 |          49 |           48 |            48 |              47 |           47 |           46 |          45 |
|  63 |          49 |           49 |            49 |              48 |           47 |           46 |          46 |

Interval ranks r (the interval is [L(r), L(n+1-r)]; r = 0 means no pair attains the level and the labelled range (min, max) is used), rho_s0 = 0.03:

| domain   |   n |   two-sided 0.05 (95 % interval) |   two-sided 0.05/9 (simultaneous over 9 cells) |
|:---------|----:|---------------------------------:|-----------------------------------------------:|
| ISU      |  58 |                               17 |                                             12 |
| ISU      |  59 |                               17 |                                             13 |
| ISU      |  60 |                               17 |                                             13 |
| ISU      |  61 |                               18 |                                             13 |
| ISU      |  62 |                               18 |                                             13 |
| ISU      |  63 |                               18 |                                             14 |
| Test B   |  35 |                                9 |                                              6 |
| Test B   |  36 |                               10 |                                              7 |
| Test B   |  37 |                               10 |                                              7 |
| Test B   |  38 |                               10 |                                              7 |
| Test B   |  39 |                               11 |                                              7 |
| Test B   |  40 |                               11 |                                              8 |

At n = 40 the 95 % interval is [L(11), L(30)] (coverage 0.9613 = 1 - 2 x 0.0194; the plain exact test gives rank 14) and the simultaneous 1 - 0.05/9 interval is [L(8), L(33)] (0.9950), as D018 2.1 states.
**Confirmation requested by the lead (PREREG_v4 rev. 1).** The unadjusted 95 % interval under the fallback at n = 40 is rank 11, [L(11), L(30)], coverage 0.961288 = 1 - 2 x 0.019356, where 0.019356 = P(BetaBin >= 30) (rho_s0 = 0.03); rank 12 would have coverage 1 - 2 x P(BetaBin >= 29) < 0.95, so 11 is the largest admissible rank. Confirmed from `fb_tables.csv` (row kind = interval, Test B, n = 40, rho_s0 = 0.03, two-sided 0.05): rank 11, lo index 11, hi index 30, coverage 0.961288. The simultaneous 1 - 0.05/9 interval is rank 8, [L(8), L(33)], coverage 0.995010.

Dependence-sensitivity counts at n = 40 (rows: level; columns: rho_s0):

| level_label                                                       |   0.0 |   0.01 |   0.02 |   0.03 |   0.05 |
|:------------------------------------------------------------------|------:|-------:|-------:|-------:|-------:|
| 0.005 (secondary Holm 1/5)                                        |    29 |     30 |     32 |     33 |     34 |
| 0.0055 (w=0.78, K chain)                                          |    29 |     30 |     31 |     32 |     34 |
| 0.00625 (Holm 1/4)                                                |    29 |     30 |     31 |     32 |     34 |
| 0.00833 (Holm 1/3)                                                |    28 |     30 |     31 |     32 |     33 |
| 0.0125 (graph, w=1/2, one chain)                                  |    28 |     29 |     30 |     31 |     33 |
| 0.0195 (w=0.78, P chain)                                          |    27 |     29 |     30 |     30 |     32 |
| 0.025 (graph both chains; reverse S; last Holm step; NC-2; GAP-1) |    27 |     28 |     29 |     30 |     31 |

## 5. Item (f): estimator of the one-sided upper limit (defined in code before the freeze)

`graph_test.sign_icc_anova(signs, groups, conf=0.95)`: one-way ANOVA intraclass correlation of the 0/1 sign indicators (indicator that a condition's inner-CV training-side score difference exceeds its median) with groups = outer folds, and with groups = majority labs.
Upper limit (Searle, one-way random model, unbalanced through n0): F = MSB/MSW; F_U = F x F(0.95; N-k, k-1); rho_U = (F_U - 1)/(F_U + n0 - 1). `avg_pairwise_sign_corr` converts the intra-fold and intra-lab values into the average pairwise sign correlation that rho_s0 bounds
((same-fold pairs x rho_F + same-lab pairs x rho_L)/C(N,2); 140 and 313 of 780 pairs for the Test B structure; negatives set to 0). `dependence_report` returns point values and upper limits and the flag `exceeds_rho_s0` (intra-fold point estimate > 0.03), which triggers the fixed Limitations sentence of D018 2.3 (ii). It changes no count and no tier.

Behaviour in simulation (40 conditions, 5 folds of 8, Gaussian latent fold effect; 4,000 replicates; true sign correlation = (2/pi) asin(ICC)):

|   latent_fold_icc |   true_sign_corr |   mean_point |   mean_upper |   coverage_of_upper_limit |   share_point_above_0_03 |     nrep |
|------------------:|-----------------:|-------------:|-------------:|--------------------------:|-------------------------:|---------:|
|             0.000 |            0.000 |       -0.001 |        0.322 |                     0.985 |                    0.378 | 4000.000 |
|             0.050 |            0.032 |        0.027 |        0.378 |                     0.993 |                    0.490 | 4000.000 |
|             0.100 |            0.064 |        0.061 |        0.435 |                     0.918 |                    0.588 | 4000.000 |
|             0.200 |            0.128 |        0.121 |        0.523 |                     0.956 |                    0.739 | 4000.000 |

**Caution to state with it:** with 5 folds the upper limit is very wide (mean 0.32 to 0.52) and the point estimate exceeds 0.03 in 38 % of replicates even with no fold effect, so the "exceeded the assumed value" sentence will often be printed and carries little information; the limit is reported evidence, as D018 rules.

## 6. Secondary graph (GAP-2): hand-worked unit tests

`secondary_graph(5)` (nodes N1..N5, S1..S5; weights 1/5 on each N_i, 0 on S_i; edges N_i -> S_i = 1, S_i -> N_j = 1/4) is tested in `test_fallback_weights_secondary.py` with hand-worked cases:
the structure and the initial level 0.005; reduction to Holm when every S_i is rejected (p_N = 0.001, 0.0055, 0.008, 0.02, 0.5: levels at rejection 0.005, 0.00625, 0.00833, then 0.0125 stops; p_N = 0.001, 0.0055, 0.008, 0.012, 0.02 rejects all five); equality with Holm on 200 random p-vectors; FWER under independent uniform nulls <= 0.025.

**Finding for the designer (not a change):** with the graph exactly as written in PREREG_v4 9.5, a test whose S_i is **not** rejected keeps its level at S_i and never releases it. A family in which most tests end at tier N therefore does **not** gain Holm's rising levels:
p_N = (0.001, 0.006, 1, 1, 1) with p_S = 1 rejects only N1 (N2 stays at 0.005), whereas Holm on the N p-values alone would reject N2 (0.006 <= 0.00625). The reduction to Holm holds when each test's S node is rejected (or with one node per test). The procedure remains valid (Bonferroni-based); it is only more conservative for tier-N results.

## 7. Limits
- All numbers are simulation values under the generator of RESULT section 2 (rho_s0 = 0.03 assumed adequate; no measured dependence). The decision rule uses one P-side and one K-side effect size, as fixed in D018 section 3; other effect sizes were not simulated.
- 20,000 replicates per setting (paired SE of a difference about 0.002); 50,000 per guard configuration.
- Counts at reduced n were tabulated, not simulated for size (the dependence simulation covered n = 40, as D018 discloses).
