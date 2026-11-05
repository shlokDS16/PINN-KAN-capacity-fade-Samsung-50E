# Pre-freeze simulations (a)-(e) of the D016 statistical plan, with the graph function (2026-11-05)

Role: statistician. **Everything below is a simulation output**: a property of the generating models stated in section 2,
not a result about PINN-KAN, about the Samsung cells, or about any real data set. No Samsung capacity value, outer-test score or
outer-test prediction was opened or produced. Inputs: the 40 Test B condition ids with fold and majority lab (identifiers only, from
`samsung_splits_v2.json` and the lab/temperature/stress columns of `experiments_meta.csv`; written to `cond_structure.csv`) and the
ISU training-side condition errors (`stats_ruling/cond_isu_W4.csv`, the shape of the skew, as in STATS_RULING 7). Reading depth: full text of CONTRACT.md,
`02_judge.md` (all), STATS_RULING, TYPE1_SIGNFLIP, P3 RESULT; PREREG_v3 sections 9 and 11 (partial).
Code: `sim_v4.py` (all items), `code/pinnkan/graph_test.py` + `code/tests/test_graph_test.py` (the graph, 12 tests, all pass).
Seeds: `numpy.random.SeedSequence([20261105, crc32(scenario name)])`, one stream per scenario. CPU only, 2 processes at most.

## 0. Verdicts

| Item | Finding (simulation) | Status |
|---|---|---|
| (a) size of the exact sign test under fold/lab shared random effects | **Not passed.** The plain exact sign test exceeds 1.2 x nominal as soon as the intra-fold correlation of the latent log ratio reaches 0.03-0.05, or a random intra-lab correlation reaches 0.015-0.023. A pre-set fallback (sign test with a fixed design effect, rho_s0 = 0.03: 31 of 40 at 0.0125, 30 of 40 at 0.025) stays below 1.2 x nominal in every cell and for P3 up to intra-fold 0.10 with intra-lab 0.05, at a power price (section 4.4) | fallback specified and simulated; **needs gate-auditor approval before any Samsung score** |
| (b) power of P1, chains P2 and P3, P3 itself | tables in section 5; with the fallback the 80 %-power relative reduction at g1 is 0.21 (rho 0.75, ISU-like skew; plain test 0.17) | reported |
| (c) power of K1, K2 | K1 non-inferiority has power 0.96 at equality for rho 0.95 and 0.73 for rho 0.90 (plain test); K2 superiority needs a 9-15 % gain for 80 % power | reported |
| (d) FWER of the graph | implementation check **passed**: independent-condition maximum 0.0204 over 72 configurations (global null 0.0169); with fold/lab effects the plain test breaks the 0.025 bound (0.088) and the fallback rho_s0 = 0.03 restores it (0.016) | passed (with the fallback) |
| (e) order-statistic intervals at 1 - 0.05/9, n = 40 | exist: [L(11), L(30)], coverage 0.9978 (nominal 0.9944); under clustering the coverage falls below nominal; rank 8, [L(8), L(33)], under the fallback | passed; fallback rank given |
| (f) rho estimation | code path `item_f_rho_report` written and smoke-tested on the ISU pilot (not on Samsung) | not run on Samsung, as instructed |

## 1. Graph function (tested)

`code/pinnkan/graph_test.py`: `graph_test(p, weights, G, alpha)` is the Bretz et al. sequentially rejective weight/graph update, valid for any
dependence between valid p-values. `pinnkan_graph()` returns the D016 graph: nodes P1N, P1S, P2, P3, K1, K2N, K2S; weights 1/2 on P1N and K1;
edges P1N->P1S->P2->P3, K1->K2N->K2S (weight 1) and the two hand-over edges P3->K1 and K2S->P1N (weight 1), so that a chain hands its
level to the other chain only when its last node is rejected, and a completed chain's level reaches the first open node of the other chain
(rejected nodes are removed and their edges re-routed). `sign_p`, `sign_crit`, `sign_test_p` and `order_stat_interval` are the exact sign-test and
interval helpers. 12 tests (`test_graph_test.py`) check: the thresholds of PREREG_v3 9.3 (28/28/27 of 40 at 0.025/3, 0.025/2, 0.025; 16/15/15 of 19; 12/11/11 of 13); the
reduction to Holm; the chain gating (P1S fails -> P2, P3 never reached); P chain alone runs at 0.0125 and K1 at 0.02 is not rejected; P3 rejected -> K1 at 0.025;
K chain complete -> P1N at 0.025 (27 of 40); the sum of open levels never exceeds alpha; batch equals single; FWER under independent uniform nulls <= 0.025. Only the new test file was run (12 passed).

## 2. Generating models (explicit)

Condition c = 1..40 (Test B), fold f(c) (5 folds of 8) and lab l(c) (majority lab: HM 17, INT 19, SIE 4; 3 mixed-lab conditions are assigned
to their majority lab; `cond_structure.csv`). For a vector of J log ratios (grid cells in (a); the contrasts L1(g1), L2, L1(g4), LK1, LK2 in (b)-(d)):

    Z_cj = sqrt(1 - s_F - s_L) W_cj + sqrt(s_F) U_f(c),j + sqrt(s_L) V_l(c),j ,     W, U, V ~ N(0, R) independent across c, f, l
    L_cj = med_j + sigma_j (T(Z_cj) - T(0))     (b)-(d)   (copula form: marginal law of L_cj is the same for every s_F, s_L)
    L_cj = med_j + sigma  (s_F^0.5 U + s_L^0.5 V + (1-s_F-s_L)^0.5 T(W))      (a)   (additive form: the skew sits on the condition-specific part;
                                                                                    medians calibrated by Monte Carlo to the null boundary, 10^6 conditions)

* T = identity ("normal") or the standardised ISU shape (power law minus LightGBM, training-side condition errors, smoothed by 0.2 SD jitter;
  skewness +1.00 after smoothing against +1.06 unsmoothed; "isu_left" is the mirror, -1.01). median(L_cj) = med_j exactly.
* s_F, s_L = intra-fold and intra-lab correlation of the latent variable ("ICC"). They are **assumptions, not measurements**: no fold or lab effect on a
  log ratio between two learners has been measured (anchor, section 4.5, is uninformative). Random lab effects (anchor: labs redrawn) are the pessimistic
  reading; "fixed lab offsets" (labs are design strata, not redrawn) is the optimistic one and is also reported.
* Marginal scale: sigma_j = sqrt((s sqrt(2(1-rho_j)))^2 + 0.001), with s = sqrt(ln(1 + 0.45^2)) = 0.429 (CV of condition errors 0.45, STATS_RULING 7) and 0.001 the seed-noise
  variance of a log ratio (SD of one seed 0.05, 5 seeds). rho_j = correlation of the two arms' log condition errors.
* Cross-cell structure in (a): 3 x 3 grid (m = 8, 16, 32; k = 0, 2, full), separable AR(1) correlation of the latent variable with coefficient a in both directions, so that corr(g1, g4) = a^3 in {0.3, 0.6, 0.9} (main grid 0.6);
  fold and lab shares scale with m by an **assumed** multiplier 1 / 0.75 / 0.5 (fewer training conditions, larger fold-to-fold variation of the fitted law; same for every k). The
  size at a cell depends only on that cell's shares; the cross-cell correlation matters for the P3 contrast.
* Arm structure in (b)-(d): log errors of A1, D*, A9, A15, G15 at g1 and g4 with unit variance; tree dependence (A1 is the centre; D*, A9, A15 are conditionally independent given A1; G15 hangs on A15), corr(A1,D*) = rho1 in {0.6, 0.75, 0.9},
  corr(A1,A9) = 0.95, corr(A1,A15) = 0.95 (0.90 in (c)), corr(A15,G15) = 0.93 (0.90, 0.95 in (c)); Kronecker with the cell correlation kappa = corr(g1,g4) of the same arm (L1(g1), L1(g4) then correlate kappa).
  Contrasts (positive favours the first-named side): L1 = ln S_D* - ln S_A1, L2 = ln S_A9 - ln S_A1, LK1 = ln S_A1 - ln S_A15, LK2 = ln S_G15 - ln S_A15, D = L1(g1) - L1(g4). A "gain" r means median(L) = -ln(1 - r).
* Tests: exact one-sided sign test of median(L) > margin (positives = number of conditions with L > margin, ties not positive), margins ln 1.02 (S) and -ln 1.10 (N), local levels 0.0125 (28 of 40) and 0.025 (27 of 40); P3 margin 0 on D.
* Replicates: 100,000 per scenario in (a) (Monte Carlo SE of a size 0.0125: 0.0004, ratio SE 0.03), 40,000 in (b), (c), 20,000 for the chains, 50,000 per configuration in (d). Analytic (exact binomial) where conditions are i.i.d.

## 3. Item (e) first: exact order-statistic intervals (analytic)

|   n | alpha_two_sided   | exists   |   rank_r | interval       |   coverage |   nominal |
|----:|:------------------|:---------|---------:|:---------------|-----------:|----------:|
|  13 | 0.05              | True     |        3 | [L(3), L(11)]  |     0.9775 |    0.9500 |
|  13 | 0.05/9            | True     |        2 | [L(2), L(12)]  |     0.9966 |    0.9944 |
|  13 | 0.05/18           | True     |        1 | [L(1), L(13)]  |     0.9998 |    0.9972 |
|  19 | 0.05              | True     |        5 | [L(5), L(15)]  |     0.9808 |    0.9500 |
|  19 | 0.05/9            | True     |        4 | [L(4), L(16)]  |     0.9956 |    0.9944 |
|  19 | 0.05/18           | True     |        3 | [L(3), L(17)]  |     0.9993 |    0.9972 |
|  40 | 0.05              | True     |       14 | [L(14), L(27)] |     0.9615 |    0.9500 |
|  40 | 0.05/9            | True     |       11 | [L(11), L(30)] |     0.9978 |    0.9944 |
|  40 | 0.05/18           | True     |       11 | [L(11), L(30)] |     0.9978 |    0.9972 |

For n = 40 a simultaneous 95 % interval over the 9 cells of one contrast (Bonferroni, two-sided alpha/9 = 0.0056) exists and is [L(11), L(30)] of the sorted condition log ratios, coverage 0.9978 (>= 0.9944).
It also exists for n = 19 (S2) and n = 13 (Test C). The unadjusted 95 % interval is [L(14), L(27)] (0.9615); nine of them cover simultaneously only 0.79 of the time at independence (table below).
Coverage under clustering (same scenarios as (a), ISU-like skew, g1 and all nine cells together):

|   fold ICC |   lab ICC |   coverage at g1 (nominal 0.9944) |   min over 9 cells |   all 9 cells together (target 0.95) |   unadjusted 95 % intervals (r=14), all 9 together |
|-----------:|----------:|----------------------------------:|-------------------:|-------------------------------------:|---------------------------------------------------:|
|     0.0000 |    0.0000 |                            0.9979 |             0.9974 |                               0.9840 |                                             0.7947 |
|     0.0500 |    0.0000 |                            0.9928 |             0.9926 |                               0.9621 |                                             0.7062 |
|     0.1000 |    0.0000 |                            0.9855 |             0.9853 |                               0.9364 |                                             0.6393 |
|     0.1000 |    0.0500 |                            0.9626 |             0.9626 |                               0.8658 |                                             0.5105 |
|     0.2000 |    0.0500 |                            0.9396 |             0.9378 |                               0.8034 |                                             0.4308 |

The rank-11 intervals lose their guarantee with fold/lab clustering (0.9626 at g1 for intra-fold 0.10 and intra-lab 0.05; 0.8658 for all nine cells together). Under the fallback of
section 4.4 the same arithmetic gives rank 8 ([L(8), L(33)]); minimum per-cell coverage over the scenario regions R3-R6 (R-definitions in 4.4):

| region                        |   min per-cell coverage, rank 11 |   min per-cell coverage, rank 8 |
|:------------------------------|---------------------------------:|--------------------------------:|
| R3: fold <= 0.10, lab <= 0.02 |                           0.9760 |                          0.9977 |
| R4: fold <= 0.10, lab <= 0.05 |                           0.9617 |                          0.9949 |
| R5: fold <= 0.20, lab <= 0.05 |                           0.9378 |                          0.9884 |
| R6: fold <= 0.20, lab <= 0.10 |                           0.9079 |                          0.9785 |

Rank 8 keeps every cell above 0.9944 up to R4 (intra-fold 0.10, intra-lab 0.05) and so, by Bonferroni, the nine-cell family above 0.95 there.

## 4. Item (a): size of the exact sign test and the fallback

### 4.1 Size of the plain exact test

Ratio of the simulated rejection rate at the null boundary to the nominal local level (0.0125 / 0.025), cell g1 = (m 8, k 2), corr(g1,g4) = 0.6, random lab effects; `*` = above 1.2.
At zero clustering the ratios are 0.65-0.69 / 0.76-0.78 (exact sizes 0.0083 / 0.0192 against nominal 0.0125 / 0.025). Rows: intra-fold correlation; columns: intra-lab correlation.

**Normal**

|   fold ICC | lab ICC 0.00   | lab ICC 0.02   | lab ICC 0.05   | lab ICC 0.10   | lab ICC 0.20   |
|-----------:|:---------------|:---------------|:---------------|:---------------|:---------------|
|      0.000 | 0.69 / 0.76    | 1.12 / 1.15    | 2.03 / 1.85 *  | 3.69 / 2.94 *  | 7.12 / 4.91 *  |
|      0.020 | 0.84 / 0.92    | 1.42 / 1.37 *  | 2.32 / 2.04 *  | 3.98 / 3.14 *  | 7.55 / 5.16 *  |
|      0.050 | 1.22 / 1.22 *  | 1.79 / 1.64 *  | 2.72 / 2.31 *  | 4.47 / 3.38 *  | 7.75 / 5.26 *  |
|      0.100 | 1.88 / 1.73 *  | 2.44 / 2.12 *  | 3.56 / 2.86 *  | 5.48 / 4.01 *  | 8.38 / 5.62 *  |
|      0.200 | 3.36 / 2.77 *  | 4.02 / 3.13 *  | 4.94 / 3.67 *  | 6.73 / 4.71 *  | 9.84 / 6.29 *  |

**ISU-like right skew (skewness +1.0)**

|   fold ICC | lab ICC 0.00   | lab ICC 0.02   | lab ICC 0.05   | lab ICC 0.10   | lab ICC 0.20   |
|-----------:|:---------------|:---------------|:---------------|:---------------|:---------------|
|      0.000 | 0.65 / 0.77    | 1.40 / 1.39 *  | 2.86 / 2.40 *  | 4.86 / 3.64 *  | 8.51 / 5.61 *  |
|      0.020 | 0.91 / 1.00    | 1.74 / 1.62 *  | 3.11 / 2.56 *  | 5.03 / 3.69 *  | 8.72 / 5.74 *  |
|      0.050 | 1.43 / 1.41 *  | 2.34 / 2.02 *  | 3.60 / 2.87 *  | 5.55 / 3.98 *  | 8.93 / 5.81 *  |
|      0.100 | 2.24 / 1.99 *  | 3.17 / 2.56 *  | 4.29 / 3.25 *  | 6.41 / 4.50 *  | 9.40 / 6.09 *  |
|      0.200 | 3.95 / 3.04 *  | 4.74 / 3.57 *  | 5.88 / 4.20 *  | 7.63 / 5.17 *  | 10.52 / 6.65 * |

**ISU-like left skew (mirror)**

|   fold ICC | lab ICC 0.00   | lab ICC 0.02   | lab ICC 0.05   | lab ICC 0.10   | lab ICC 0.20   |
|-----------:|:---------------|:---------------|:---------------|:---------------|:---------------|
|      0.000 | 0.68 / 0.78    | 1.37 / 1.35 *  | 2.74 / 2.36 *  | 4.44 / 3.44 *  | 8.01 / 5.48 *  |
|      0.020 | 0.97 / 1.00    | 1.77 / 1.63 *  | 2.92 / 2.45 *  | 4.73 / 3.61 *  | 8.29 / 5.65 *  |
|      0.050 | 1.42 / 1.41 *  | 2.15 / 1.94 *  | 3.35 / 2.74 *  | 5.25 / 3.90 *  | 8.73 / 5.83 *  |
|      0.100 | 2.24 / 1.98 *  | 3.00 / 2.51 *  | 4.02 / 3.18 *  | 5.96 / 4.34 *  | 9.43 / 6.20 *  |
|      0.200 | 3.87 / 3.07 *  | 4.64 / 3.52 *  | 5.72 / 4.19 *  | 7.39 / 5.10 *  | 10.55 / 6.72 * |

Fine sweeps (g1, ratio to nominal), and the interpolated break-even correlation at which the ratio crosses 1.2:

|   fold ICC |   normal 0.0125 |   normal 0.025 |   isu_right 0.0125 |   isu_right 0.025 |
|-----------:|----------------:|---------------:|-------------------:|------------------:|
|      0.000 |           0.690 |          0.760 |              0.650 |             0.770 |
|      0.010 |           0.760 |          0.870 |              0.830 |             0.880 |
|      0.020 |           0.840 |          0.920 |              0.910 |             1.000 |
|      0.030 |           0.960 |          1.020 |              1.150 |             1.180 |
|      0.040 |           1.090 |          1.130 |              1.320 |             1.310 |
|      0.050 |           1.220 |          1.220 |              1.430 |             1.410 |
|      0.060 |           1.390 |          1.360 |              1.590 |             1.510 |
|      0.080 |           1.540 |          1.550 |              1.990 |             1.790 |
|      0.100 |           1.880 |          1.730 |              2.240 |             1.990 |
|      0.150 |           2.540 |          2.200 |              3.200 |             2.600 |
|      0.200 |           3.360 |          2.770 |              3.950 |             3.040 |
|      0.300 |           4.990 |          3.690 |              5.740 |             4.100 |

|   lab ICC (random) |   normal 0.0125 |   normal 0.025 |   isu_right 0.0125 |   isu_right 0.025 |
|-------------------:|----------------:|---------------:|-------------------:|------------------:|
|              0.000 |           0.690 |          0.760 |              0.650 |             0.770 |
|              0.010 |           0.990 |          1.040 |              1.000 |             1.060 |
|              0.020 |           1.120 |          1.150 |              1.400 |             1.390 |
|              0.030 |           1.360 |          1.320 |              1.820 |             1.670 |
|              0.040 |           1.750 |          1.620 |              2.340 |             2.050 |
|              0.050 |           2.030 |          1.850 |              2.860 |             2.400 |
|              0.100 |           3.690 |          2.940 |              4.860 |             3.640 |
|              0.200 |           7.120 |          4.910 |              8.510 |             5.610 |

| shape     |   level |   fold ICC at which size = 1.2 x nominal (lab ICC 0) |   lab ICC at which size = 1.2 x nominal (fold ICC 0) |
|:----------|--------:|-----------------------------------------------------:|-----------------------------------------------------:|
| normal    |   0.013 |                                                0.049 |                                                0.023 |
| normal    |   0.025 |                                                0.047 |                                                0.023 |
| isu_right |   0.013 |                                                0.033 |                                                0.015 |
| isu_right |   0.025 |                                                0.032 |                                                0.014 |

So the plain test passes the "<= 1.2 x nominal" criterion only for intra-fold correlation below about 0.03-0.05 *or* random intra-lab correlation below about 0.015-0.023 (the lower value is the ISU-like skew). The
mean number of positives stays 20; the inflation is a variance effect: the variance of the positives count is 1.31 (intra-fold 0.05), 1.57 (0.10) and 2.15 (intra-fold 0.10 with intra-lab 0.05) times the binomial 10 (ISU-like skew, g1).

### 4.2 Grid cells and the P3 contrast

Ratio to nominal at level 0.0125 for the nine cells (ISU-like skew, corr(g1,g4) = 0.6), and for D = L(g1) - L(g4) (P3: sign test of D > 0):

|   fold ICC |   lab ICC |   m8,k0 |   m8,k1 |   m8,k2 |   m16,k0 |   m16,k1 |   m16,k2 |   m32,k0 |   m32,k1 |   m32,k2 |   D = L(g1)-L(g4) |   D at 0.025 |
|-----------:|----------:|--------:|--------:|--------:|---------:|---------:|---------:|---------:|---------:|---------:|------------------:|-------------:|
|      0.000 |     0.000 |   0.650 |   0.650 |   0.690 |    0.690 |    0.740 |    0.720 |    0.660 |    0.680 |    0.690 |             0.680 |        0.780 |
|      0.050 |     0.000 |   1.480 |   1.430 |   1.540 |    1.250 |    1.230 |    1.270 |    1.000 |    1.050 |    1.060 |             1.240 |        1.250 |
|      0.100 |     0.000 |   2.340 |   2.240 |   2.290 |    1.900 |    1.830 |    1.800 |    1.550 |    1.520 |    1.480 |             1.880 |        1.680 |
|      0.100 |     0.050 |   4.270 |   4.290 |   4.370 |    3.350 |    3.300 |    3.440 |    2.400 |    2.460 |    2.490 |             3.470 |        2.780 |

The scarce cells (m = 8) are worst because the assumed fold/lab share is largest there (multiplier 1 / 0.75 / 0.5); the k axis changes nothing (same shares). P3 behaves like a single cell with the
shares of g1 and g4 combined. Dependence of the P3 size on corr(g1,g4):

|   corr(g1,g4) |   fold ICC |   lab ICC |   P3 size 0.0125 |   ratio |   P3 size 0.025 |   ratio  |
|--------------:|-----------:|----------:|-----------------:|--------:|----------------:|---------:|
|        0.3000 |     0.0000 |    0.0000 |           0.0083 |  0.6624 |          0.0196 |   0.7820 |
|        0.3000 |     0.0500 |    0.0000 |           0.0145 |  1.1624 |          0.0301 |   1.2052 |
|        0.3000 |     0.1000 |    0.0500 |           0.0414 |  3.3144 |          0.0662 |   2.6488 |
|        0.6000 |     0.0000 |    0.0000 |           0.0086 |  0.6840 |          0.0196 |   0.7840 |
|        0.6000 |     0.0500 |    0.0000 |           0.0155 |  1.2368 |          0.0312 |   1.2472 |
|        0.6000 |     0.1000 |    0.0500 |           0.0433 |  3.4680 |          0.0696 |   2.7832 |
|        0.9000 |     0.0000 |    0.0000 |           0.0081 |  0.6488 |          0.0190 |   0.7584 |
|        0.9000 |     0.0500 |    0.0000 |           0.0184 |  1.4752 |          0.0360 |   1.4384 |
|        0.9000 |     0.1000 |    0.0500 |           0.0563 |  4.5000 |          0.0852 |   3.4076 |

### 4.3 Lab effects as fixed design offsets

If labs are treated as strata of the design (offsets fixed, labs not redrawn; lab variance share l of the latent variable), lab effects make the sign test **conservative** (variance of the positives count below the binomial), and only fold clustering inflates it:

|   lab offsets (var share) |   fold ICC |   size g1 0.0125 |   ratio |   size g1 0.025 |   ratio  |
|--------------------------:|-----------:|-----------------:|--------:|----------------:|---------:|
|                    0.1000 |     0.0000 |           0.0060 |  0.4816 |          0.0148 |   0.5916 |
|                    0.1000 |     0.0500 |           0.0138 |  1.1024 |          0.0287 |   1.1492 |
|                    0.1000 |     0.1000 |           0.0229 |  1.8296 |          0.0431 |   1.7244 |
|                    0.2000 |     0.0000 |           0.0040 |  0.3232 |          0.0106 |   0.4232 |
|                    0.2000 |     0.0500 |           0.0091 |  0.7312 |          0.0208 |   0.8320 |
|                    0.2000 |     0.1000 |           0.0181 |  1.4440 |          0.0351 |   1.4040 |
|                    0.4000 |     0.0000 |           0.0016 |  0.1320 |          0.0052 |   0.2072 |
|                    0.4000 |     0.0500 |           0.0041 |  0.3288 |          0.0107 |   0.4268 |
|                    0.4000 |     0.1000 |           0.0084 |  0.6704 |          0.0192 |   0.7664 |

### 4.4 Pre-set fallback and why a permutation test cannot be it

* **Fold-blocked permutation / sign-flip of whole folds is not feasible:** 5 folds give 2^5 = 32 sign patterns, so the smallest attainable p-value is 1/32 = 0.031 > 0.025; it can reject nothing. Lab-blocked: 2^3 = 8 patterns. A cluster
  bootstrap on 5 folds has no usable coverage. A design effect **estimated** from the five folds (cluster-robust variance of the positives count, floor DE0) does not work either (selected rows below, ISU-like skew, nominal levels 0.0125 / 0.025):
  with DE0 = 1 (pure estimation) the t4 reference is vacuous (size 0.0000-0.0084) and the normal reference is liberal under clustering (0.0114-0.0429, up to 3.4 x nominal); with a floor of DE0 = 2 the normal-reference test behaves like a fixed design effect (size 0.0004-0.0186), so estimation adds nothing over a fixed value.

| shape     |   fold ICC |   lab ICC |   DE floor | reference   |   size 0.0125 |   size 0.025 |
|:----------|-----------:|----------:|-----------:|:------------|--------------:|-------------:|
| isu_right |     0.0000 |    0.0000 |     1.0000 | t4          |        0.0001 |       0.0008 |
| isu_right |     0.0000 |    0.0000 |     1.0000 | norm        |        0.0066 |       0.0152 |
| isu_right |     0.0000 |    0.0000 |     2.0000 | t4          |        0.0000 |       0.0001 |
| isu_right |     0.0000 |    0.0000 |     2.0000 | norm        |        0.0004 |       0.0010 |
| isu_right |     0.0000 |    0.0500 |     1.0000 | t4          |        0.0014 |       0.0082 |
| isu_right |     0.0000 |    0.0500 |     1.0000 | norm        |        0.0271 |       0.0459 |
| isu_right |     0.0000 |    0.0500 |     2.0000 | t4          |        0.0000 |       0.0007 |
| isu_right |     0.0000 |    0.0500 |     2.0000 | norm        |        0.0044 |       0.0095 |
| isu_right |     0.0500 |    0.0000 |     1.0000 | t4          |        0.0003 |       0.0027 |
| isu_right |     0.0500 |    0.0000 |     1.0000 | norm        |        0.0115 |       0.0225 |
| isu_right |     0.0500 |    0.0000 |     2.0000 | t4          |        0.0000 |       0.0002 |
| isu_right |     0.0500 |    0.0000 |     2.0000 | norm        |        0.0019 |       0.0039 |
| isu_right |     0.0500 |    0.0500 |     1.0000 | t4          |        0.0031 |       0.0123 |
| isu_right |     0.0500 |    0.0500 |     1.0000 | norm        |        0.0326 |       0.0515 |
| isu_right |     0.0500 |    0.0500 |     2.0000 | t4          |        0.0000 |       0.0018 |
| isu_right |     0.0500 |    0.0500 |     2.0000 | norm        |        0.0080 |       0.0151 |
| isu_right |     0.1000 |    0.0000 |     1.0000 | t4          |        0.0009 |       0.0054 |
| isu_right |     0.1000 |    0.0000 |     1.0000 | norm        |        0.0177 |       0.0318 |
| isu_right |     0.1000 |    0.0000 |     2.0000 | t4          |        0.0000 |       0.0004 |
| isu_right |     0.1000 |    0.0000 |     2.0000 | norm        |        0.0035 |       0.0073 |
| isu_right |     0.1000 |    0.0500 |     1.0000 | t4          |        0.0049 |       0.0152 |
| isu_right |     0.1000 |    0.0500 |     1.0000 | norm        |        0.0355 |       0.0541 |
| isu_right |     0.1000 |    0.0500 |     2.0000 | t4          |        0.0001 |       0.0031 |
| isu_right |     0.1000 |    0.0500 |     2.0000 | norm        |        0.0112 |       0.0199 |
| isu_right |     0.2000 |    0.0000 |     1.0000 | t4          |        0.0031 |       0.0100 |
| isu_right |     0.2000 |    0.0000 |     1.0000 | norm        |        0.0264 |       0.0418 |
| isu_right |     0.2000 |    0.0000 |     2.0000 | t4          |        0.0000 |       0.0024 |
| isu_right |     0.2000 |    0.0000 |     2.0000 | norm        |        0.0092 |       0.0158 |
| isu_right |     0.2000 |    0.0500 |     1.0000 | t4          |        0.0084 |       0.0206 |
| isu_right |     0.2000 |    0.0500 |     1.0000 | norm        |        0.0429 |       0.0623 |
| isu_right |     0.2000 |    0.0500 |     2.0000 | t4          |        0.0003 |       0.0062 |
| isu_right |     0.2000 |    0.0500 |     2.0000 | norm        |        0.0186 |       0.0305 |

* **Fallback adopted for specification: exact sign test with a fixed design effect.** The positives count under H0 is Beta-binomial(40; a = b = (1/rho_s0 - 1)/2) with pairwise sign correlation rho_s0 (design effect 1 + 39 rho_s0). A node is rejected at local level `a` iff
  P(BetaBin >= positives) <= a. No random numbers. The guarantee is **assumption-dependent, not distribution-free**: it holds when the average pairwise correlation of the sign indicators is at most rho_s0. Positives needed:

|   rho_s0 |   design effect |   positives needed at 0.0125 |   size under the BetaBin null |   positives needed at 0.025 |   size under the BetaBin null  | size if conditions independent (k1 / k2)   |   rank r of 1-0.05/9 interval |
|---------:|----------------:|-----------------------------:|------------------------------:|----------------------------:|-------------------------------:|:-------------------------------------------|------------------------------:|
|   0.0000 |          1.0000 |                           28 |                        0.0083 |                          27 |                         0.0192 | 0.0083 / 0.0192                            |                            11 |
|   0.0100 |          1.3900 |                           29 |                        0.0105 |                          28 |                         0.0213 | 0.0032 / 0.0083                            |                            10 |
|   0.0200 |          1.7800 |                           30 |                        0.0110 |                          29 |                         0.0209 | 0.0011 / 0.0032                            |                             9 |
|   0.0300 |          2.1700 |                           31 |                        0.0106 |                          30 |                         0.0194 | 0.0003 / 0.0011                            |                             8 |
|   0.0500 |          2.9500 |                           33 |                        0.0083 |                          31 |                         0.0249 | 0.0000 / 0.0003                            |                             6 |

and at the other levels in use (secondary Holm family of five at 0.025; graph levels 0.0125, 0.025):

| local level                                |   rho_s0=0.00: positives needed |   rho_s0=0.02: positives needed |   rho_s0=0.03: positives needed |
|:-------------------------------------------|--------------------------------:|--------------------------------:|--------------------------------:|
| 0.005 (Holm 1/5)                           |                              29 |                              32 |                              33 |
| 0.00625 (1/4)                              |                              29 |                              31 |                              32 |
| 0.00833 (1/3)                              |                              28 |                              31 |                              32 |
| 0.0125 (1/2; graph, one chain)             |                              28 |                              30 |                              31 |
| 0.025 (graph, both chains; last Holm step) |                              27 |                              29 |                              30 |

Worst ratio of simulated size to nominal (level 0.0125 / level 0.025), maximum over all nine cells and the P3 contrast and over the three shapes, in the regions of (intra-fold, intra-lab random) correlation:

| region (random effects)       | rho_s0=0.00   | rho_s0=0.01   | rho_s0=0.02   | rho_s0=0.03   | rho_s0=0.05   |
|:------------------------------|:--------------|:--------------|:--------------|:--------------|:--------------|
| R1: fold <= 0.05, lab 0       | 1.54 / 1.45 * | 0.71 / 0.77   | 0.30 / 0.35   | 0.13 / 0.15   | 0.02 / 0.06   |
| R2: fold <= 0.10, lab 0       | 2.34 / 2.03 * | 1.24 / 1.17 * | 0.60 / 0.62   | 0.28 / 0.30   | 0.05 / 0.14   |
| R3: fold <= 0.10, lab <= 0.02 | 3.20 / 2.58 * | 1.83 / 1.60 * | 1.03 / 0.92   | 0.52 / 0.52   | 0.10 / 0.26   |
| R4: fold <= 0.10, lab <= 0.05 | 4.37 / 3.35 * | 2.73 / 2.19 * | 1.59 / 1.36 * | 0.88 / 0.79   | 0.22 / 0.44   |
| R5: fold <= 0.20, lab <= 0.05 | 6.02 / 4.25 * | 4.05 / 3.01 * | 2.64 / 2.03 * | 1.66 / 1.32 * | 0.51 / 0.83   |
| R6: fold <= 0.20, lab <= 0.10 | 7.69 / 5.21 * | 5.53 / 3.85 * | 3.77 / 2.77 * | 2.51 / 1.88 * | 0.93 / 1.26 * |

Regions: R1 intra-fold <= 0.05 and no lab effect; R2 <= 0.10 and none; R3 <= 0.10 with intra-lab <= 0.02; R4 <= 0.10 with intra-lab <= 0.05; R5 <= 0.20 with <= 0.05; R6 <= 0.20 with <= 0.10 (the scenarios inside each region are those of the grids in 4.1 and the fine sweeps).
The smallest rho_s0 on the grid that keeps every ratio below 1.2 in R4 is **0.03** (worst 0.88 / 0.79); rho_s0 = 0.02 is enough for R3, i.e. for fold clustering up to 0.10 with fixed lab strata or random lab effects up to 0.02; none of the candidates covers R5 except 0.05. R4 is a judgement (fold 0.10, lab 0.05 is
not measured); the pre-set value rho_s0 and the region are the designer's and the gate auditor's to change, the tables allow it. With fixed lab offsets (4.3) rho_s0 = 0.02 and 0.03 give ratios 0.01-0.51 (conservative) and with other corr(g1,g4) = 0.3 and 0.9, rho_s0 = 0.03 stays at or below 0.92 of nominal.

**Cost.** Under independent conditions the fallback has size 0.0003 / 0.0011 (31 / 30 positives), i.e. 2 % and 4 % of nominal, so it is very conservative if there is no clustering. The loss of power is in section 5.1 and 5.4. The fallback is stricter than the plain test, so the plain-test tier can be reported as a descriptive row and the abstract
follows the fallback tier with no choice.

### 4.5 What is known about the correlation (anchor)

Nothing for Samsung. The only data-based number is the training-side SNL pilot: the intra-chemistry ICC of ln(power law / LightGBM) over 23 conditions in 3 chemistries (LFP 7, NCA 8, NMC 8) is 0.15 (ICC of the sign indicator: -0.02), against a permutation 90 % range of -0.14 to 0.25 without grouping
(`anchor_icc_snl.json`): the data cannot discriminate between 0 and 0.2. It is therefore not used to choose rho_s0. Item (f) provides the same estimate from the Samsung inner-CV training sides.

## 5. Item (b): power of P1 and the chains

### 5.1 P1 at g1, single test (i.i.d. conditions, exact binomial)

Relative reduction r of the median error needed for 80 % power of P1S (tier S, margin ln 1.02), plain test and fallbacks (level 0.0125 / 0.025). Three shapes, rho = corr of the two arms' log errors:

| shape     |   rho | plain         | fb0.01        | fb0.02        | fb0.03        | fb0.05        |
|:----------|------:|:--------------|:--------------|:--------------|:--------------|:--------------|
| normal    | 0.600 | 0.239 / 0.218 | 0.261 / 0.239 | 0.282 / 0.261 | 0.304 / 0.282 | 0.351 / 0.304 |
| normal    | 0.750 | 0.198 / 0.181 | 0.216 / 0.198 | 0.234 / 0.216 | 0.253 / 0.234 | 0.293 / 0.253 |
| normal    | 0.900 | 0.138 / 0.126 | 0.150 / 0.138 | 0.162 / 0.150 | 0.176 / 0.162 | 0.204 / 0.176 |
| isu_right | 0.600 | 0.201 / 0.182 | 0.219 / 0.201 | 0.238 / 0.219 | 0.256 / 0.238 | 0.298 / 0.256 |
| isu_right | 0.750 | 0.166 / 0.151 | 0.181 / 0.166 | 0.197 / 0.181 | 0.212 / 0.197 | 0.247 / 0.212 |
| isu_right | 0.900 | 0.116 / 0.105 | 0.126 / 0.116 | 0.136 / 0.126 | 0.147 / 0.136 | 0.172 / 0.147 |
| isu_left  | 0.600 | 0.246 / 0.215 | 0.278 / 0.246 | 0.306 / 0.278 | 0.331 / 0.306 | 0.374 / 0.331 |
| isu_left  | 0.750 | 0.204 / 0.178 | 0.231 / 0.204 | 0.255 / 0.231 | 0.275 / 0.255 | 0.313 / 0.275 |
| isu_left  | 0.900 | 0.141 / 0.124 | 0.160 / 0.141 | 0.177 / 0.160 | 0.191 / 0.177 | 0.218 / 0.191 |

Power at selected r, level 0.0125 (28 of 40 plain; 30 / 31 of 40 for rho_s0 0.02 / 0.03) and level 0.025:

| shape     |   rho | test   |   0.0125 r=0.10 |   0.0125 r=0.15 |   0.0125 r=0.20 |   0.0125 r=0.25 |   0.0125 r=0.30 |
|:----------|------:|:-------|----------------:|----------------:|----------------:|----------------:|----------------:|
| normal    |  0.60 | plain  |            0.10 |            0.29 |            0.58 |            0.85 |            0.97 |
| normal    |  0.60 | fb0.02 |            0.02 |            0.11 |            0.31 |            0.62 |            0.87 |
| normal    |  0.60 | fb0.03 |            0.01 |            0.06 |            0.20 |            0.48 |            0.78 |
| normal    |  0.75 | plain  |            0.16 |            0.47 |            0.81 |            0.97 |            1.00 |
| normal    |  0.75 | fb0.02 |            0.05 |            0.22 |            0.57 |            0.88 |            0.99 |
| normal    |  0.75 | fb0.03 |            0.02 |            0.13 |            0.42 |            0.78 |            0.96 |
| normal    |  0.90 | plain  |            0.41 |            0.88 |            1.00 |            1.00 |            1.00 |
| normal    |  0.90 | fb0.02 |            0.18 |            0.69 |            0.97 |            1.00 |            1.00 |
| normal    |  0.90 | fb0.03 |            0.10 |            0.55 |            0.94 |            1.00 |            1.00 |
| isu_right |  0.60 | plain  |            0.17 |            0.47 |            0.80 |            0.97 |            1.00 |
| isu_right |  0.60 | fb0.02 |            0.05 |            0.23 |            0.55 |            0.86 |            0.98 |
| isu_right |  0.60 | fb0.03 |            0.02 |            0.13 |            0.40 |            0.76 |            0.95 |
| isu_right |  0.75 | plain  |            0.28 |            0.69 |            0.95 |            1.00 |            1.00 |
| isu_right |  0.75 | fb0.02 |            0.10 |            0.41 |            0.82 |            0.98 |            1.00 |
| isu_right |  0.75 | fb0.03 |            0.05 |            0.28 |            0.71 |            0.96 |            1.00 |
| isu_right |  0.90 | plain  |            0.63 |            0.98 |            1.00 |            1.00 |            1.00 |
| isu_right |  0.90 | fb0.02 |            0.36 |            0.91 |            1.00 |            1.00 |            1.00 |
| isu_right |  0.90 | fb0.03 |            0.23 |            0.83 |            0.99 |            1.00 |            1.00 |
| isu_left  |  0.60 | plain  |            0.13 |            0.35 |            0.62 |            0.81 |            0.93 |
| isu_left  |  0.60 | fb0.02 |            0.03 |            0.14 |            0.35 |            0.57 |            0.77 |
| isu_left  |  0.60 | fb0.03 |            0.02 |            0.08 |            0.23 |            0.43 |            0.65 |
| isu_left  |  0.75 | plain  |            0.20 |            0.53 |            0.79 |            0.93 |            0.99 |
| isu_left  |  0.75 | fb0.02 |            0.06 |            0.26 |            0.54 |            0.78 |            0.96 |
| isu_left  |  0.75 | fb0.03 |            0.03 |            0.16 |            0.39 |            0.65 |            0.91 |
| isu_left  |  0.90 | plain  |            0.48 |            0.84 |            0.99 |            1.00 |            1.00 |
| isu_left  |  0.90 | fb0.02 |            0.23 |            0.62 |            0.93 |            1.00 |            1.00 |
| isu_left  |  0.90 | fb0.03 |            0.13 |            0.47 |            0.86 |            1.00 |            1.00 |

| shape     |   rho | test   |   0.025 r=0.10 |   0.025 r=0.15 |   0.025 r=0.20 |   0.025 r=0.25 |   0.025 r=0.30 |
|:----------|------:|:-------|---------------:|---------------:|---------------:|---------------:|---------------:|
| normal    |  0.60 | plain  |           0.17 |           0.41 |           0.71 |           0.91 |           0.99 |
| normal    |  0.60 | fb0.02 |           0.05 |           0.19 |           0.45 |           0.75 |           0.93 |
| normal    |  0.60 | fb0.03 |           0.02 |           0.11 |           0.31 |           0.62 |           0.87 |
| normal    |  0.75 | plain  |           0.25 |           0.60 |           0.89 |           0.99 |           1.00 |
| normal    |  0.75 | fb0.02 |           0.09 |           0.34 |           0.70 |           0.94 |           0.99 |
| normal    |  0.75 | fb0.03 |           0.05 |           0.22 |           0.57 |           0.88 |           0.99 |
| normal    |  0.90 | plain  |           0.55 |           0.94 |           1.00 |           1.00 |           1.00 |
| normal    |  0.90 | fb0.02 |           0.29 |           0.80 |           0.99 |           1.00 |           1.00 |
| normal    |  0.90 | fb0.03 |           0.18 |           0.69 |           0.97 |           1.00 |           1.00 |
| isu_right |  0.60 | plain  |           0.27 |           0.61 |           0.88 |           0.98 |           1.00 |
| isu_right |  0.60 | fb0.02 |           0.10 |           0.34 |           0.68 |           0.93 |           0.99 |
| isu_right |  0.60 | fb0.03 |           0.05 |           0.23 |           0.55 |           0.86 |           0.98 |
| isu_right |  0.75 | plain  |           0.40 |           0.80 |           0.98 |           1.00 |           1.00 |
| isu_right |  0.75 | fb0.02 |           0.18 |           0.55 |           0.90 |           0.99 |           1.00 |
| isu_right |  0.75 | fb0.03 |           0.10 |           0.41 |           0.82 |           0.98 |           1.00 |
| isu_right |  0.90 | plain  |           0.75 |           0.99 |           1.00 |           1.00 |           1.00 |
| isu_right |  0.90 | fb0.02 |           0.49 |           0.95 |           1.00 |           1.00 |           1.00 |
| isu_right |  0.90 | fb0.03 |           0.36 |           0.91 |           1.00 |           1.00 |           1.00 |
| isu_left  |  0.60 | plain  |           0.21 |           0.48 |           0.74 |           0.89 |           0.97 |
| isu_left  |  0.60 | fb0.02 |           0.07 |           0.23 |           0.49 |           0.70 |           0.87 |
| isu_left  |  0.60 | fb0.03 |           0.03 |           0.14 |           0.35 |           0.57 |           0.77 |
| isu_left  |  0.75 | plain  |           0.31 |           0.66 |           0.87 |           0.97 |           1.00 |
| isu_left  |  0.75 | fb0.02 |           0.12 |           0.39 |           0.67 |           0.87 |           0.98 |
| isu_left  |  0.75 | fb0.03 |           0.06 |           0.26 |           0.54 |           0.78 |           0.96 |
| isu_left  |  0.90 | plain  |           0.61 |           0.91 |           0.99 |           1.00 |           1.00 |
| isu_left  |  0.90 | fb0.02 |           0.34 |           0.74 |           0.97 |           1.00 |           1.00 |
| isu_left  |  0.90 | fb0.03 |           0.23 |           0.62 |           0.93 |           1.00 |           1.00 |

Non-inferiority tier P1N (margin -ln 1.10): r at which P1N reaches 80 % power, and its power at true equality (r = 0):

| shape     |   rho | plain (0.0125 / 0.025)   | fb0.03 (0.0125 / 0.025)   | power P1N at r=0, plain   | power P1N at r=0, fb0.03   |
|:----------|------:|:-------------------------|:--------------------------|:--------------------------|:---------------------------|
| normal    | 0.600 | 0.147 / 0.123            | 0.220 / 0.195             | 0.12 / 0.20               | 0.01 / 0.03                |
| normal    | 0.750 | 0.100 / 0.081            | 0.162 / 0.141             | 0.20 / 0.30               | 0.03 / 0.06                |
| normal    | 0.900 | 0.032 / 0.019            | 0.075 / 0.060             | 0.51 / 0.64               | 0.15 / 0.25                |
| isu_right | 0.600 | 0.103 / 0.082            | 0.166 / 0.144             | 0.21 / 0.32               | 0.03 / 0.07                |
| isu_right | 0.750 | 0.064 / 0.047            | 0.116 / 0.099             | 0.34 / 0.47               | 0.07 / 0.14                |
| isu_right | 0.900 | 0.008 / 0.000            | 0.043 / 0.031             | 0.73 / 0.83               | 0.33 / 0.46                |
| isu_left  | 0.600 | 0.154 / 0.119            | 0.249 / 0.222             | 0.16 / 0.25               | 0.02 / 0.05                |
| isu_left  | 0.750 | 0.107 / 0.078            | 0.187 / 0.164             | 0.25 / 0.37               | 0.04 / 0.09                |
| isu_left  | 0.900 | 0.037 / 0.017            | 0.093 / 0.076             | 0.56 / 0.69               | 0.19 / 0.30                |

With fold/lab clustering (rho = 0.75, ISU-like skew, simulated) the plain test's power moves little for r >= 0.15; the fallback (31 of 40) loses 0.24-0.40 of power against the plain test at r = 0.15-0.20 with or without clustering (clustering raises the fallback's own power slightly, 0.29 to 0.35 at r = 0.15):

|   fold ICC |   lab ICC |    r |   plain 0.0125 |   fb 0.02 (30/40) |   fb 0.03 (31/40) |   plain 0.025 |   fb 0.03 0.025 (30/40) |
|-----------:|----------:|-----:|---------------:|------------------:|------------------:|--------------:|------------------------:|
|       0.00 |      0.00 | 0.10 |           0.27 |              0.10 |              0.05 |          0.40 |                    0.10 |
|       0.00 |      0.00 | 0.15 |           0.68 |              0.41 |              0.29 |          0.80 |                    0.41 |
|       0.00 |      0.00 | 0.20 |           0.95 |              0.82 |              0.71 |          0.98 |                    0.82 |
|       0.00 |      0.00 | 0.25 |           1.00 |              0.98 |              0.96 |          1.00 |                    0.98 |
|       0.05 |      0.00 | 0.10 |           0.30 |              0.12 |              0.07 |          0.41 |                    0.12 |
|       0.05 |      0.00 | 0.15 |           0.68 |              0.43 |              0.31 |          0.78 |                    0.43 |
|       0.05 |      0.00 | 0.20 |           0.93 |              0.81 |              0.70 |          0.97 |                    0.81 |
|       0.05 |      0.00 | 0.25 |           1.00 |              0.97 |              0.94 |          1.00 |                    0.97 |
|       0.10 |      0.00 | 0.10 |           0.32 |              0.15 |              0.09 |          0.42 |                    0.15 |
|       0.10 |      0.00 | 0.15 |           0.66 |              0.43 |              0.32 |          0.76 |                    0.43 |
|       0.10 |      0.00 | 0.20 |           0.92 |              0.79 |              0.69 |          0.96 |                    0.79 |
|       0.10 |      0.00 | 0.25 |           0.99 |              0.97 |              0.93 |          1.00 |                    0.97 |
|       0.10 |      0.05 | 0.10 |           0.34 |              0.18 |              0.12 |          0.43 |                    0.18 |
|       0.10 |      0.05 | 0.15 |           0.65 |              0.45 |              0.35 |          0.73 |                    0.45 |
|       0.10 |      0.05 | 0.20 |           0.89 |              0.77 |              0.67 |          0.93 |                    0.77 |
|       0.10 |      0.05 | 0.25 |           0.98 |              0.95 |              0.91 |          0.99 |                    0.95 |
|       0.20 |      0.05 | 0.10 |           0.36 |              0.21 |              0.15 |          0.44 |                    0.21 |
|       0.20 |      0.05 | 0.15 |           0.64 |              0.46 |              0.37 |          0.72 |                    0.46 |
|       0.20 |      0.05 | 0.20 |           0.87 |              0.75 |              0.66 |          0.91 |                    0.75 |
|       0.20 |      0.05 | 0.25 |           0.97 |              0.93 |              0.89 |          0.99 |                    0.93 |

**Reading.** A 10 % gain is nearly undetectable (power 0.05 to 0.28 at rho 0.75 depending on the test); 15 % is detected 0.28-0.69 of the time; 20 % 0.71-0.95. The fallback's 80 %-power gain at rho 0.75 is 0.212 (ISU-like skew) to 0.253 (normal) against
0.166 to 0.198 for the plain test.

### 5.2 Chains P1 -> P2 -> P3 in the graph (plain exact tests, i.i.d. conditions)

P(P1N and P1S rejected), P(also P2), P(also P3) in the graph, ISU-like skew, corr(L(g1),L(g4)) = 0.6, A1 vs A9 gain r2 = 0.15, g4 gain over D* r4 = 0.05 (so median D = ln((1-r4)/(1-r1)) is the "median D" column).
"K_never": the K chain never rejects (P-chain levels 0.0125); "K_first": the K chain completes first (levels 0.025):

| K chain   |   rho(A1,D*) |   r1 (g1 gain vs D*) |   r2 (A1 vs A9) |   r4 (g4 gain) |   median D |   P(P1N,P1S) |   P(..., P2) |   P(..., P3) |
|:----------|-------------:|---------------------:|----------------:|---------------:|-----------:|-------------:|-------------:|-------------:|
| K_never   |         0.60 |                 0.10 |            0.15 |           0.05 |       0.05 |         0.17 |         0.17 |         0.02 |
| K_never   |         0.60 |                 0.15 |            0.15 |           0.05 |       0.11 |         0.47 |         0.47 |         0.16 |
| K_never   |         0.60 |                 0.20 |            0.15 |           0.05 |       0.17 |         0.80 |         0.80 |         0.53 |
| K_never   |         0.60 |                 0.30 |            0.15 |           0.05 |       0.31 |         1.00 |         1.00 |         0.99 |
| K_never   |         0.75 |                 0.10 |            0.15 |           0.05 |       0.05 |         0.27 |         0.27 |         0.04 |
| K_never   |         0.75 |                 0.15 |            0.15 |           0.05 |       0.11 |         0.69 |         0.69 |         0.35 |
| K_never   |         0.75 |                 0.20 |            0.15 |           0.05 |       0.17 |         0.95 |         0.95 |         0.81 |
| K_never   |         0.75 |                 0.30 |            0.15 |           0.05 |       0.31 |         1.00 |         1.00 |         1.00 |
| K_never   |         0.90 |                 0.10 |            0.15 |           0.05 |       0.05 |         0.62 |         0.62 |         0.19 |
| K_never   |         0.90 |                 0.15 |            0.15 |           0.05 |       0.11 |         0.98 |         0.98 |         0.84 |
| K_never   |         0.90 |                 0.20 |            0.15 |           0.05 |       0.17 |         1.00 |         1.00 |         1.00 |
| K_never   |         0.90 |                 0.30 |            0.15 |           0.05 |       0.31 |         1.00 |         1.00 |         1.00 |
| K_first   |         0.60 |                 0.10 |            0.15 |           0.05 |       0.05 |         0.27 |         0.27 |         0.05 |
| K_first   |         0.60 |                 0.15 |            0.15 |           0.05 |       0.11 |         0.61 |         0.61 |         0.28 |
| K_first   |         0.60 |                 0.20 |            0.15 |           0.05 |       0.17 |         0.88 |         0.88 |         0.68 |
| K_first   |         0.60 |                 0.30 |            0.15 |           0.05 |       0.31 |         1.00 |         1.00 |         0.99 |
| K_first   |         0.75 |                 0.10 |            0.15 |           0.05 |       0.05 |         0.39 |         0.39 |         0.09 |
| K_first   |         0.75 |                 0.15 |            0.15 |           0.05 |       0.11 |         0.80 |         0.80 |         0.49 |
| K_first   |         0.75 |                 0.20 |            0.15 |           0.05 |       0.17 |         0.98 |         0.98 |         0.89 |
| K_first   |         0.75 |                 0.30 |            0.15 |           0.05 |       0.31 |         1.00 |         1.00 |         1.00 |
| K_first   |         0.90 |                 0.10 |            0.15 |           0.05 |       0.05 |         0.75 |         0.75 |         0.31 |
| K_first   |         0.90 |                 0.15 |            0.15 |           0.05 |       0.11 |         0.99 |         0.99 |         0.92 |
| K_first   |         0.90 |                 0.20 |            0.15 |           0.05 |       0.17 |         1.00 |         1.00 |         1.00 |
| K_first   |         0.90 |                 0.30 |            0.15 |           0.05 |       0.31 |         1.00 |         1.00 |         1.00 |

Dependence of the chain on r2 (rho 0.75, r1 = 0.20, r4 = 0.05; K never) - P2 is the cheap node when A9 is a weak competitor and the binding one when the law adds 5 %:

|   r2 (A1 vs A9 gain) |   P(P1N,P1S) |   P(..,P2) |   P(..,P3) |
|---------------------:|-------------:|-----------:|-----------:|
|                 0.05 |         0.95 |       0.17 |       0.14 |
|                 0.15 |         0.95 |       0.95 |       0.81 |
|                 0.30 |         0.95 |       0.95 |       0.81 |

Dependence of P3 on corr(L(g1), L(g4)) and r4 (rho 0.75, r1 = 0.20, r2 = 0.15):

|   corr(L(g1),L(g4)) |   r4 |   median D |   P(P1N,P1S,P2) |   P(P1N,P1S,P2,P3) |
|--------------------:|-----:|-----------:|----------------:|-------------------:|
|                0.30 | 0.00 |       0.22 |            0.95 |               0.79 |
|                0.30 | 0.05 |       0.17 |            0.95 |               0.56 |
|                0.30 | 0.10 |       0.12 |            0.95 |               0.27 |
|                0.60 | 0.00 |       0.22 |            0.95 |               0.93 |
|                0.60 | 0.05 |       0.17 |            0.95 |               0.81 |
|                0.60 | 0.10 |       0.12 |            0.95 |               0.48 |
|                0.90 | 0.00 |       0.22 |            0.95 |               0.95 |
|                0.90 | 0.05 |       0.17 |            0.95 |               0.95 |
|                0.90 | 0.10 |       0.12 |            0.95 |               0.94 |

An extra (D*, A9) correlation of 0.15 beyond the tree structure changes the chain by < 0.002 (rho 0.75, r1 = 0.20): the chain probabilities are insensitive to the L1-L2 dependence.

### 5.3 P3 on its own: power of the trend test

D = L(g1) - L(g4), sign test D > 0, plain test, level 0.0125, i.i.d., ISU-like skew. delta = median(D) in log units (0.10 = the g1 advantage exceeds the g4 advantage by about 10 %). "SD of D" is the Gaussian SD on the log scale:

|   rho(A1,D*) |   corr(L(g1),L(g4)) |   SD of D |   delta=0.00 |   delta=0.05 |   delta=0.10 |   delta=0.15 |   delta=0.20 |   delta=0.30 |   delta=0.40 |
|-------------:|--------------------:|----------:|-------------:|-------------:|-------------:|-------------:|-------------:|-------------:|-------------:|
|         0.60 |                0.00 |      0.55 |         0.01 |         0.03 |         0.09 |         0.19 |         0.35 |         0.72 |         0.93 |
|         0.60 |                0.30 |      0.46 |         0.01 |         0.04 |         0.12 |         0.28 |         0.50 |         0.87 |         0.99 |
|         0.60 |                0.60 |      0.34 |         0.01 |         0.06 |         0.22 |         0.50 |         0.77 |         0.99 |         1.00 |
|         0.60 |                0.90 |      0.17 |         0.01 |         0.23 |         0.79 |         0.99 |         1.00 |         1.00 |         1.00 |
|         0.75 |                0.00 |      0.43 |         0.01 |         0.04 |         0.14 |         0.32 |         0.55 |         0.90 |         0.99 |
|         0.75 |                0.30 |      0.36 |         0.01 |         0.05 |         0.19 |         0.45 |         0.73 |         0.98 |         1.00 |
|         0.75 |                0.60 |      0.27 |         0.01 |         0.09 |         0.36 |         0.73 |         0.94 |         1.00 |         1.00 |
|         0.75 |                0.90 |      0.14 |         0.01 |         0.38 |         0.95 |         1.00 |         1.00 |         1.00 |         1.00 |
|         0.90 |                0.00 |      0.28 |         0.01 |         0.08 |         0.35 |         0.71 |         0.93 |         1.00 |         1.00 |
|         0.90 |                0.30 |      0.23 |         0.01 |         0.12 |         0.50 |         0.86 |         0.99 |         1.00 |         1.00 |
|         0.90 |                0.60 |      0.17 |         0.01 |         0.22 |         0.77 |         0.98 |         1.00 |         1.00 |         1.00 |
|         0.90 |                0.90 |      0.09 |         0.01 |         0.79 |         1.00 |         1.00 |         1.00 |         1.00 |         1.00 |

Level 0.025:

|   rho(A1,D*) |   corr |   delta=0.10 |   delta=0.15 |   delta=0.20 |   delta=0.30 |
|-------------:|-------:|-------------:|-------------:|-------------:|-------------:|
|         0.60 |   0.30 |         0.20 |         0.41 |         0.64 |         0.93 |
|         0.60 |   0.60 |         0.33 |         0.63 |         0.86 |         1.00 |
|         0.60 |   0.90 |         0.88 |         1.00 |         1.00 |         1.00 |
|         0.75 |   0.30 |         0.30 |         0.59 |         0.83 |         0.99 |
|         0.75 |   0.60 |         0.49 |         0.83 |         0.97 |         1.00 |
|         0.75 |   0.90 |         0.97 |         1.00 |         1.00 |         1.00 |
|         0.90 |   0.30 |         0.63 |         0.93 |         0.99 |         1.00 |
|         0.90 |   0.60 |         0.86 |         0.99 |         1.00 |         1.00 |
|         0.90 |   0.90 |         1.00 |         1.00 |         1.00 |         1.00 |

With the fallback (rho_s0 = 0.03) and with fold clustering 0.10 (rho 0.75):

|   rho(A1,D*) |   corr |   fold ICC | test          |   delta=0.00 |   delta=0.10 |   delta=0.15 |   delta=0.20 |   delta=0.30 |
|-------------:|-------:|-----------:|:--------------|-------------:|-------------:|-------------:|-------------:|-------------:|
|        0.750 |  0.300 |      0.000 | plain_0.0125  |        0.009 |        0.192 |        0.454 |        0.730 |        0.977 |
|        0.750 |  0.300 |      0.000 | fb0.03_0.0125 |        0.000 |        0.029 |        0.124 |        0.324 |        0.813 |
|        0.750 |  0.300 |      0.100 | plain_0.0125  |        0.025 |        0.246 |        0.471 |        0.701 |        0.955 |
|        0.750 |  0.300 |      0.100 | fb0.03_0.0125 |        0.002 |        0.060 |        0.172 |        0.356 |        0.780 |
|        0.750 |  0.600 |      0.000 | plain_0.0125  |        0.009 |        0.364 |        0.726 |        0.937 |        0.999 |
|        0.750 |  0.600 |      0.000 | fb0.03_0.0125 |        0.000 |        0.083 |        0.323 |        0.674 |        0.981 |
|        0.750 |  0.600 |      0.100 | plain_0.0125  |        0.024 |        0.384 |        0.700 |        0.902 |        0.997 |
|        0.750 |  0.600 |      0.100 | fb0.03_0.0125 |        0.002 |        0.122 |        0.353 |        0.654 |        0.967 |
|        0.750 |  0.900 |      0.000 | plain_0.0125  |        0.008 |        0.946 |        1.000 |        1.000 |        1.000 |
|        0.750 |  0.900 |      0.000 | fb0.03_0.0125 |        0.000 |        0.697 |        0.987 |        1.000 |        1.000 |
|        0.750 |  0.900 |      0.100 | plain_0.0125  |        0.023 |        0.913 |        0.998 |        1.000 |        1.000 |
|        0.750 |  0.900 |      0.100 | fb0.03_0.0125 |        0.002 |        0.672 |        0.973 |        0.999 |        1.000 |

P3 is the least powered node: with corr(g1,g4) = 0.6 and rho 0.75 it needs delta about 0.15 for 0.73 (plain) and about 0.20 for 0.67 with the fallback; with weak cell correlation (0.3) the plain test reaches 0.73 only at delta = 0.20 and the fallback 0.32. At delta = 0 its size is 0.009 (plain) and 0.000 (fallback).

### 5.4 Chains under the fallback (rho_s0 = 0.03), and clustering

Same scenario as 5.2 (rho 1 varying, r2 = 0.15, r4 = 0.05), plain against fallback, with and without fold 0.10 + lab 0.05 clustering (simulated):

|   fold ICC |   lab ICC | K chain   |   rho(A1,D*) |   r1 | test   |   P(P1N,P1S) |   P(..,P2) |   P(..,P3) |
|-----------:|----------:|:----------|-------------:|-----:|:-------|-------------:|-----------:|-----------:|
|       0.00 |      0.00 | K_never   |         0.60 | 0.15 | plain  |         0.47 |       0.47 |       0.16 |
|       0.00 |      0.00 | K_never   |         0.60 | 0.15 | fb0.03 |         0.13 |       0.13 |       0.01 |
|       0.00 |      0.00 | K_never   |         0.60 | 0.20 | plain  |         0.80 |       0.80 |       0.54 |
|       0.00 |      0.00 | K_never   |         0.60 | 0.20 | fb0.03 |         0.41 |       0.41 |       0.13 |
|       0.00 |      0.00 | K_never   |         0.60 | 0.25 | plain  |         0.97 |       0.97 |       0.87 |
|       0.00 |      0.00 | K_never   |         0.60 | 0.25 | fb0.03 |         0.76 |       0.76 |       0.46 |
|       0.00 |      0.00 | K_never   |         0.60 | 0.30 | plain  |         1.00 |       1.00 |       0.99 |
|       0.00 |      0.00 | K_never   |         0.60 | 0.30 | fb0.03 |         0.95 |       0.95 |       0.83 |
|       0.00 |      0.00 | K_never   |         0.75 | 0.15 | plain  |         0.69 |       0.69 |       0.34 |
|       0.00 |      0.00 | K_never   |         0.75 | 0.15 | fb0.03 |         0.28 |       0.28 |       0.05 |
|       0.00 |      0.00 | K_never   |         0.75 | 0.20 | plain  |         0.95 |       0.95 |       0.80 |
|       0.00 |      0.00 | K_never   |         0.75 | 0.20 | fb0.03 |         0.71 |       0.70 |       0.36 |
|       0.00 |      0.00 | K_never   |         0.75 | 0.25 | plain  |         1.00 |       1.00 |       0.98 |
|       0.00 |      0.00 | K_never   |         0.75 | 0.25 | fb0.03 |         0.96 |       0.95 |       0.81 |
|       0.00 |      0.00 | K_never   |         0.75 | 0.30 | plain  |         1.00 |       1.00 |       1.00 |
|       0.00 |      0.00 | K_never   |         0.75 | 0.30 | fb0.03 |         1.00 |       0.99 |       0.98 |
|       0.00 |      0.00 | K_never   |         0.90 | 0.15 | plain  |         0.98 |       0.98 |       0.84 |
|       0.00 |      0.00 | K_never   |         0.90 | 0.15 | fb0.03 |         0.83 |       0.82 |       0.43 |
|       0.00 |      0.00 | K_never   |         0.90 | 0.20 | plain  |         1.00 |       1.00 |       1.00 |
|       0.00 |      0.00 | K_never   |         0.90 | 0.20 | fb0.03 |         0.99 |       0.99 |       0.93 |
|       0.00 |      0.00 | K_never   |         0.90 | 0.25 | plain  |         1.00 |       1.00 |       1.00 |
|       0.00 |      0.00 | K_never   |         0.90 | 0.25 | fb0.03 |         1.00 |       0.99 |       0.99 |
|       0.00 |      0.00 | K_never   |         0.90 | 0.30 | plain  |         1.00 |       1.00 |       1.00 |
|       0.00 |      0.00 | K_never   |         0.90 | 0.30 | fb0.03 |         1.00 |       0.99 |       0.99 |
|       0.00 |      0.00 | K_first   |         0.75 | 0.15 | plain  |         0.79 |       0.79 |       0.49 |
|       0.00 |      0.00 | K_first   |         0.75 | 0.15 | fb0.03 |         0.41 |       0.41 |       0.11 |
|       0.00 |      0.00 | K_first   |         0.75 | 0.20 | plain  |         0.98 |       0.98 |       0.89 |
|       0.00 |      0.00 | K_first   |         0.75 | 0.20 | fb0.03 |         0.82 |       0.82 |       0.53 |
|       0.00 |      0.00 | K_first   |         0.75 | 0.25 | plain  |         1.00 |       1.00 |       0.99 |
|       0.00 |      0.00 | K_first   |         0.75 | 0.25 | fb0.03 |         0.98 |       0.98 |       0.91 |
|       0.00 |      0.00 | K_first   |         0.75 | 0.30 | plain  |         1.00 |       1.00 |       1.00 |
|       0.00 |      0.00 | K_first   |         0.75 | 0.30 | fb0.03 |         1.00 |       1.00 |       0.99 |
|       0.10 |      0.05 | K_never   |         0.60 | 0.15 | plain  |         0.50 |       0.50 |       0.22 |
|       0.10 |      0.05 | K_never   |         0.60 | 0.15 | fb0.03 |         0.22 |       0.22 |       0.05 |
|       0.10 |      0.05 | K_never   |         0.60 | 0.20 | plain  |         0.74 |       0.73 |       0.49 |
|       0.10 |      0.05 | K_never   |         0.60 | 0.20 | fb0.03 |         0.45 |       0.43 |       0.18 |
|       0.10 |      0.05 | K_never   |         0.60 | 0.25 | plain  |         0.92 |       0.92 |       0.78 |
|       0.10 |      0.05 | K_never   |         0.60 | 0.25 | fb0.03 |         0.73 |       0.71 |       0.45 |
|       0.10 |      0.05 | K_never   |         0.60 | 0.30 | plain  |         0.98 |       0.98 |       0.94 |
|       0.10 |      0.05 | K_never   |         0.60 | 0.30 | fb0.03 |         0.91 |       0.88 |       0.73 |
|       0.10 |      0.05 | K_never   |         0.75 | 0.15 | plain  |         0.65 |       0.65 |       0.36 |
|       0.10 |      0.05 | K_never   |         0.75 | 0.15 | fb0.03 |         0.36 |       0.35 |       0.10 |
|       0.10 |      0.05 | K_never   |         0.75 | 0.20 | plain  |         0.89 |       0.89 |       0.71 |
|       0.10 |      0.05 | K_never   |         0.75 | 0.20 | fb0.03 |         0.67 |       0.65 |       0.36 |
|       0.10 |      0.05 | K_never   |         0.75 | 0.25 | plain  |         0.98 |       0.98 |       0.93 |
|       0.10 |      0.05 | K_never   |         0.75 | 0.25 | fb0.03 |         0.91 |       0.88 |       0.72 |
|       0.10 |      0.05 | K_never   |         0.75 | 0.30 | plain  |         1.00 |       1.00 |       0.99 |
|       0.10 |      0.05 | K_never   |         0.75 | 0.30 | fb0.03 |         0.99 |       0.96 |       0.92 |
|       0.10 |      0.05 | K_never   |         0.90 | 0.15 | plain  |         0.94 |       0.93 |       0.76 |
|       0.10 |      0.05 | K_never   |         0.90 | 0.15 | fb0.03 |         0.77 |       0.75 |       0.42 |
|       0.10 |      0.05 | K_never   |         0.90 | 0.20 | plain  |         1.00 |       0.99 |       0.98 |
|       0.10 |      0.05 | K_never   |         0.90 | 0.20 | fb0.03 |         0.98 |       0.94 |       0.85 |
|       0.10 |      0.05 | K_never   |         0.90 | 0.25 | plain  |         1.00 |       1.00 |       1.00 |
|       0.10 |      0.05 | K_never   |         0.90 | 0.25 | fb0.03 |         1.00 |       0.97 |       0.96 |
|       0.10 |      0.05 | K_never   |         0.90 | 0.30 | plain  |         1.00 |       1.00 |       1.00 |
|       0.10 |      0.05 | K_never   |         0.90 | 0.30 | fb0.03 |         1.00 |       0.97 |       0.97 |
|       0.10 |      0.05 | K_first   |         0.75 | 0.15 | plain  |         0.73 |       0.73 |       0.46 |
|       0.10 |      0.05 | K_first   |         0.75 | 0.15 | fb0.03 |         0.45 |       0.45 |       0.17 |
|       0.10 |      0.05 | K_first   |         0.75 | 0.20 | plain  |         0.93 |       0.93 |       0.80 |
|       0.10 |      0.05 | K_first   |         0.75 | 0.20 | fb0.03 |         0.76 |       0.75 |       0.49 |
|       0.10 |      0.05 | K_first   |         0.75 | 0.25 | plain  |         0.99 |       0.99 |       0.96 |
|       0.10 |      0.05 | K_first   |         0.75 | 0.25 | fb0.03 |         0.95 |       0.93 |       0.81 |
|       0.10 |      0.05 | K_first   |         0.75 | 0.30 | plain  |         1.00 |       1.00 |       1.00 |
|       0.10 |      0.05 | K_first   |         0.75 | 0.30 | fb0.03 |         0.99 |       0.98 |       0.96 |

Effect of r2 and r4 on the chain under both tests (rho 0.75, r1 = 0.20, K never):

|   fold ICC |   lab ICC |   r2 |   r4 |   P(P1S) plain |   P(..P2) plain |   P(..P3) plain |   P(P1S) fb0.03 |   P(..P2) fb0.03 |   P(..P3) fb0.03 |
|-----------:|----------:|-----:|-----:|---------------:|----------------:|----------------:|----------------:|-----------------:|-----------------:|
|       0.00 |      0.00 | 0.05 | 0.00 |           0.95 |            0.17 |            0.16 |            0.70 |             0.02 |             0.01 |
|       0.00 |      0.00 | 0.05 | 0.05 |           0.95 |            0.17 |            0.15 |            0.71 |             0.02 |             0.01 |
|       0.00 |      0.00 | 0.05 | 0.10 |           0.95 |            0.17 |            0.09 |            0.71 |             0.02 |             0.00 |
|       0.00 |      0.00 | 0.15 | 0.00 |           0.95 |            0.95 |            0.93 |            0.71 |             0.70 |             0.58 |
|       0.00 |      0.00 | 0.15 | 0.05 |           0.95 |            0.95 |            0.80 |            0.71 |             0.70 |             0.36 |
|       0.00 |      0.00 | 0.15 | 0.10 |           0.95 |            0.95 |            0.47 |            0.71 |             0.70 |             0.12 |
|       0.00 |      0.00 | 0.30 | 0.00 |           0.95 |            0.95 |            0.93 |            0.70 |             0.70 |             0.58 |
|       0.00 |      0.00 | 0.30 | 0.05 |           0.95 |            0.95 |            0.81 |            0.71 |             0.71 |             0.37 |
|       0.00 |      0.00 | 0.30 | 0.10 |           0.95 |            0.95 |            0.48 |            0.71 |             0.71 |             0.12 |
|       0.10 |      0.05 | 0.05 | 0.00 |           0.89 |            0.23 |            0.21 |            0.68 |             0.05 |             0.04 |
|       0.10 |      0.05 | 0.05 | 0.05 |           0.89 |            0.23 |            0.19 |            0.68 |             0.06 |             0.03 |
|       0.10 |      0.05 | 0.05 | 0.10 |           0.89 |            0.23 |            0.12 |            0.67 |             0.06 |             0.02 |
|       0.10 |      0.05 | 0.15 | 0.00 |           0.89 |            0.89 |            0.83 |            0.67 |             0.65 |             0.51 |
|       0.10 |      0.05 | 0.15 | 0.05 |           0.89 |            0.89 |            0.71 |            0.67 |             0.65 |             0.36 |
|       0.10 |      0.05 | 0.15 | 0.10 |           0.89 |            0.89 |            0.48 |            0.68 |             0.66 |             0.19 |
|       0.10 |      0.05 | 0.30 | 0.00 |           0.89 |            0.89 |            0.84 |            0.68 |             0.68 |             0.54 |
|       0.10 |      0.05 | 0.30 | 0.05 |           0.89 |            0.89 |            0.71 |            0.68 |             0.68 |             0.38 |
|       0.10 |      0.05 | 0.30 | 0.10 |           0.90 |            0.90 |            0.47 |            0.68 |             0.68 |             0.19 |

## 6. Item (c): power of K1 and K2

K1: L = ln(S_A1/S_A15), tier N (non-inferiority, A15 no more than 10 % worse). Effect = relative excess error of A15 over A1 (S_A15 = (1 + effect) S_A1). K2: L = ln(S_G15/S_A15); effect = relative gain q of A15 over G15. Plain exact test, i.i.d. conditions, ISU-like skew; rho = corr(A15, A1) for K1 and corr(A15, G15) for K2:

| test   |   effect |   rho=0.90 0.0125 |   rho=0.90 0.025 |   rho=0.95 0.0125 |   rho=0.95 0.025 |
|:-------|---------:|------------------:|-----------------:|------------------:|-----------------:|
| K1_N   |   -0.050 |             0.985 |            0.994 |             1.000 |            1.000 |
| K1_N   |    0.000 |             0.729 |            0.830 |             0.960 |            0.982 |
| K1_N   |    0.020 |             0.514 |            0.646 |             0.818 |            0.894 |
| K1_N   |    0.050 |             0.198 |            0.303 |             0.391 |            0.524 |
| K1_N   |    0.080 |             0.037 |            0.072 |             0.062 |            0.113 |
| K1_N   |    0.100 |             0.008 |            0.019 |             0.008 |            0.019 |
| K1_S   |   -0.100 |             0.628 |            0.747 |             0.909 |            0.954 |
| K1_S   |   -0.050 |             0.090 |            0.156 |             0.176 |            0.275 |
| K1_S   |   -0.020 |             0.009 |            0.020 |             0.009 |            0.020 |
| K1_S   |    0.000 |             0.001 |            0.004 |             0.001 |            0.002 |
| K2_N   |   -0.100 |             0.008 |            0.019 |             0.008 |            0.019 |
| K2_N   |   -0.050 |             0.198 |            0.303 |             0.391 |            0.524 |
| K2_N   |    0.000 |             0.729 |            0.830 |             0.960 |            0.982 |
| K2_N   |    0.020 |             0.887 |            0.941 |             0.995 |            0.998 |
| K2_N   |    0.050 |             0.985 |            0.994 |             1.000 |            1.000 |
| K2_S   |    0.000 |             0.001 |            0.004 |             0.001 |            0.002 |
| K2_S   |    0.020 |             0.009 |            0.020 |             0.009 |            0.020 |
| K2_S   |    0.050 |             0.090 |            0.156 |             0.176 |            0.275 |
| K2_S   |    0.080 |             0.376 |            0.507 |             0.662 |            0.776 |
| K2_S   |    0.100 |             0.628 |            0.747 |             0.909 |            0.954 |
| K2_S   |    0.120 |             0.838 |            0.908 |             0.989 |            0.996 |
| K2_S   |    0.150 |             0.979 |            0.992 |             1.000 |            1.000 |

Largest A15 excess error (K1) / smallest A15 effect (K2) for 80 % power (blank = not reached; negative = the other side must already be better):

| test   |   rho | shape     |   0.0125 |   0.025 |
|:-------|------:|:----------|---------:|--------:|
| K1_N   |  0.90 | isu_left  |    -0.04 |   -0.02 |
| K1_N   |  0.90 | isu_right |    -0.01 |    0.00 |
| K1_N   |  0.90 | normal    |    -0.04 |   -0.02 |
| K1_N   |  0.95 | isu_left  |     0.00 |    0.01 |
| K1_N   |  0.95 | isu_right |     0.02 |    0.03 |
| K1_N   |  0.95 | normal    |     0.00 |    0.01 |
| K2_N   |  0.90 | isu_left  |     0.04 |    0.02 |
| K2_N   |  0.90 | isu_right |     0.01 |    0.00 |
| K2_N   |  0.90 | normal    |     0.04 |    0.02 |
| K2_N   |  0.95 | isu_left  |     0.00 |   -0.01 |
| K2_N   |  0.95 | isu_right |    -0.02 |   -0.03 |
| K2_N   |  0.95 | normal    |     0.00 |   -0.01 |
| K2_S   |  0.90 | isu_left  |     0.15 |    0.13 |
| K2_S   |  0.90 | isu_right |     0.12 |    0.11 |
| K2_S   |  0.90 | normal    |     0.14 |    0.13 |
| K2_S   |  0.95 | isu_left  |     0.11 |    0.10 |
| K2_S   |  0.95 | isu_right |     0.09 |    0.09 |
| K2_S   |  0.95 | normal    |     0.11 |    0.10 |

K chain in the graph (plain tests), "P_never": P chain never rejects (K levels 0.0125), "P_first": the P chain completes first (K levels 0.025):

| P chain   |   rho(A15,A1) |   rho(A15,G15) |   A15 vs A1: excess error |   A15 vs G15: gain q |   P(K1) |   P(K1,K2N) |   P(K1,K2N,K2S) |
|:----------|--------------:|---------------:|--------------------------:|---------------------:|--------:|------------:|----------------:|
| P_never   |          0.95 |           0.95 |                      0.00 |                 0.00 |    0.96 |        0.92 |            0.00 |
| P_never   |          0.95 |           0.95 |                      0.00 |                 0.05 |    0.96 |        0.96 |            0.17 |
| P_never   |          0.95 |           0.95 |                      0.00 |                 0.10 |    0.96 |        0.96 |            0.87 |
| P_never   |          0.95 |           0.95 |                      0.03 |                 0.00 |    0.70 |        0.67 |            0.00 |
| P_never   |          0.95 |           0.95 |                      0.03 |                 0.05 |    0.69 |        0.69 |            0.12 |
| P_never   |          0.95 |           0.95 |                      0.03 |                 0.10 |    0.69 |        0.69 |            0.63 |
| P_never   |          0.90 |           0.90 |                      0.00 |                 0.00 |    0.73 |        0.53 |            0.00 |
| P_never   |          0.90 |           0.90 |                      0.00 |                 0.05 |    0.73 |        0.72 |            0.07 |
| P_never   |          0.90 |           0.90 |                      0.00 |                 0.10 |    0.73 |        0.73 |            0.46 |
| P_never   |          0.90 |           0.90 |                      0.03 |                 0.00 |    0.40 |        0.30 |            0.00 |
| P_never   |          0.90 |           0.90 |                      0.03 |                 0.05 |    0.40 |        0.39 |            0.04 |
| P_never   |          0.90 |           0.90 |                      0.03 |                 0.10 |    0.40 |        0.40 |            0.26 |
| P_first   |          0.95 |           0.95 |                      0.00 |                 0.00 |    0.98 |        0.97 |            0.00 |
| P_first   |          0.95 |           0.95 |                      0.00 |                 0.05 |    0.98 |        0.98 |            0.27 |
| P_first   |          0.95 |           0.95 |                      0.00 |                 0.10 |    0.98 |        0.98 |            0.94 |
| P_first   |          0.95 |           0.95 |                      0.03 |                 0.00 |    0.80 |        0.79 |            0.00 |
| P_first   |          0.95 |           0.95 |                      0.03 |                 0.05 |    0.80 |        0.80 |            0.22 |
| P_first   |          0.95 |           0.95 |                      0.03 |                 0.10 |    0.80 |        0.80 |            0.77 |
| P_first   |          0.90 |           0.90 |                      0.00 |                 0.00 |    0.83 |        0.69 |            0.00 |
| P_first   |          0.90 |           0.90 |                      0.00 |                 0.05 |    0.83 |        0.82 |            0.13 |
| P_first   |          0.90 |           0.90 |                      0.00 |                 0.10 |    0.83 |        0.83 |            0.62 |
| P_first   |          0.90 |           0.90 |                      0.03 |                 0.00 |    0.53 |        0.45 |            0.00 |
| P_first   |          0.90 |           0.90 |                      0.03 |                 0.05 |    0.53 |        0.53 |            0.09 |
| P_first   |          0.90 |           0.90 |                      0.03 |                 0.10 |    0.53 |        0.53 |            0.40 |

Under the fallback (rho_s0 = 0.03; rho(A15,A1) = rho(A15,G15)):

| P chain   |   rho(A15,A1)=rho(A15,G15) |   A15 vs A1 excess error |   A15 vs G15 gain q |   P(K1) plain |   P(K1,K2N) plain |   P(K1,K2N,K2S) plain |   P(K1) fb0.03 |   P(K1,K2N) fb0.03 |   P(K1,K2N,K2S) fb0.03 |
|:----------|---------------------------:|-------------------------:|--------------------:|--------------:|------------------:|----------------------:|---------------:|-------------------:|-----------------------:|
| P_never   |                       0.90 |                     0.00 |                0.00 |          0.73 |              0.53 |                  0.00 |           0.33 |               0.11 |                   0.00 |
| P_never   |                       0.90 |                     0.00 |                0.05 |          0.73 |              0.72 |                  0.07 |           0.33 |               0.28 |                   0.00 |
| P_never   |                       0.90 |                     0.00 |                0.10 |          0.73 |              0.73 |                  0.46 |           0.32 |               0.32 |                   0.08 |
| P_never   |                       0.90 |                     0.03 |                0.00 |          0.40 |              0.30 |                  0.00 |           0.10 |               0.04 |                   0.00 |
| P_never   |                       0.90 |                     0.03 |                0.05 |          0.40 |              0.39 |                  0.04 |           0.10 |               0.08 |                   0.00 |
| P_never   |                       0.90 |                     0.03 |                0.10 |          0.40 |              0.40 |                  0.26 |           0.10 |               0.10 |                   0.03 |
| P_never   |                       0.95 |                     0.00 |                0.00 |          0.96 |              0.92 |                  0.00 |           0.74 |               0.55 |                   0.00 |
| P_never   |                       0.95 |                     0.00 |                0.05 |          0.96 |              0.96 |                  0.17 |           0.74 |               0.74 |                   0.02 |
| P_never   |                       0.95 |                     0.00 |                0.10 |          0.96 |              0.96 |                  0.87 |           0.74 |               0.74 |                   0.44 |
| P_never   |                       0.95 |                     0.03 |                0.00 |          0.70 |              0.67 |                  0.00 |           0.29 |               0.22 |                   0.00 |
| P_never   |                       0.95 |                     0.03 |                0.05 |          0.70 |              0.70 |                  0.12 |           0.29 |               0.29 |                   0.01 |
| P_never   |                       0.95 |                     0.03 |                0.10 |          0.70 |              0.70 |                  0.63 |           0.29 |               0.29 |                   0.17 |
| P_first   |                       0.90 |                     0.00 |                0.00 |          0.83 |              0.69 |                  0.00 |           0.47 |               0.22 |                   0.00 |
| P_first   |                       0.90 |                     0.00 |                0.05 |          0.83 |              0.82 |                  0.13 |           0.46 |               0.43 |                   0.01 |
| P_first   |                       0.90 |                     0.00 |                0.10 |          0.83 |              0.83 |                  0.63 |           0.46 |               0.46 |                   0.17 |
| P_first   |                       0.90 |                     0.03 |                0.00 |          0.53 |              0.45 |                  0.00 |           0.18 |               0.09 |                   0.00 |
| P_first   |                       0.90 |                     0.03 |                0.05 |          0.53 |              0.53 |                  0.09 |           0.18 |               0.16 |                   0.00 |
| P_first   |                       0.90 |                     0.03 |                0.10 |          0.53 |              0.53 |                  0.40 |           0.18 |               0.18 |                   0.07 |
| P_first   |                       0.95 |                     0.00 |                0.00 |          0.98 |              0.97 |                  0.00 |           0.85 |               0.72 |                   0.00 |
| P_first   |                       0.95 |                     0.00 |                0.05 |          0.98 |              0.98 |                  0.27 |           0.85 |               0.85 |                   0.05 |
| P_first   |                       0.95 |                     0.00 |                0.10 |          0.98 |              0.98 |                  0.94 |           0.85 |               0.85 |                   0.62 |
| P_first   |                       0.95 |                     0.03 |                0.00 |          0.80 |              0.79 |                  0.00 |           0.42 |               0.36 |                   0.00 |
| P_first   |                       0.95 |                     0.03 |                0.05 |          0.81 |              0.81 |                  0.22 |           0.43 |               0.43 |                   0.03 |
| P_first   |                       0.95 |                     0.03 |                0.10 |          0.80 |              0.80 |                  0.77 |           0.43 |               0.43 |                   0.31 |

**Reading.** K1 passes when A15 is truly as good as A1 with probability 0.96 only if the two arms correlate at 0.95 (0.73 at 0.90); at the planned correlation 0.90-0.95 the K1 claim therefore has power 0.73-0.96 (plain) and 0.33-0.74 (fallback, level 0.0125) when A15 equals A1. K2 at tier S needs a true gain of 9 % (rho 0.95) to 12-15 % (0.90) for 80 % power, and the "K=" outcome (K2 not S) is the expected one if the KAN-GAM gap is as small as P4 found.

## 7. Item (d): FWER of the graph

72 configurations per setting: L1 median at the N boundary (-ln 1.10, both nulls true), at 0 (N false, S true), or at a gain of 0.40 (both false); L2 at ln 1.02 or at 0.40; D at 0 or 0.40; K1 at -ln 1.10 or at +0.15; K2 at -ln 1.10 / 0 / +0.35. A hypothesis is a true null iff its median is at or below its margin;
FWER = P(reject at least one true null). Dependence: the section 2 arm structure; the "highdep" setting uses rho1 = 0.90, A9 extra correlation 0.10 and corr(g1,g4) = 0.9; 50,000 replicates per configuration (SE of a rate near 0.02: 0.0006).

| setting             |   global null FWER |   max FWER over 72 configs | config at max (L1|L2|D|K1|K2)   |   configs with FWER > 0.025 + 2 MC SE |   nrep |
|:--------------------|-------------------:|---------------------------:|:--------------------------------|--------------------------------------:|-------:|
| iid_plain           |             0.0169 |                     0.0204 | alt|null|null|alt|alt           |                                     0 |  50000 |
| iid_plain_highdep   |             0.0157 |                     0.0200 | alt|alt|alt|null|null           |                                     0 |  50000 |
| fold05_plain        |             0.0303 |                     0.0318 | alt|alt|alt|null|alt            |                                    39 |  50000 |
| fold10_lab05_plain  |             0.0877 |                     0.0892 | null|alt|alt|null|mid           |                                    70 |  50000 |
| fold10_lab05_fb0.01 |             0.0514 |                     0.0542 | null|alt|alt|null|null          |                                    62 |  50000 |
| iid_fb0.01          |             0.0066 |                     0.0089 | alt|alt|alt|null|alt            |                                     0 |  50000 |
| fold10_lab05_fb0.02 |             0.0281 |                     0.0299 | alt|null|null|null|alt          |                                    33 |  50000 |
| iid_fb0.02          |             0.0022 |                     0.0037 | null|alt|alt|alt|alt            |                                     0 |  50000 |
| fold10_lab05_fb0.03 |             0.0147 |                     0.0159 | null|alt|alt|null|null          |                                     0 |  50000 |
| iid_fb0.03          |             0.0005 |                     0.0014 | alt|alt|null|alt|alt            |                                     0 |  50000 |
| fold10_lab05_fb0.05 |             0.0030 |                     0.0080 | alt|alt|alt|null|null           |                                     0 |  50000 |
| iid_fb0.05          |             0.0001 |                     0.0005 | alt|null|null|alt|alt           |                                     0 |  50000 |

Full distribution per setting (mean over configurations that contain a true null):

| setting             |   configs |   max FWER |   global-null FWER |   mean FWER over configs with a true null |
|:--------------------|----------:|-----------:|-------------------:|------------------------------------------:|
| iid_plain           |        72 |     0.0204 |             0.0169 |                                    0.0134 |
| iid_plain_highdep   |        72 |     0.0200 |             0.0157 |                                    0.0127 |
| fold05_plain        |        72 |     0.0318 |             0.0303 |                                    0.0245 |
| fold10_lab05_plain  |        72 |     0.0892 |             0.0877 |                                    0.0703 |
| fold10_lab05_fb0.01 |        72 |     0.0542 |             0.0514 |                                    0.0417 |
| iid_fb0.01          |        72 |     0.0089 |             0.0066 |                                    0.0053 |
| fold10_lab05_fb0.02 |        72 |     0.0299 |             0.0281 |                                    0.0233 |
| iid_fb0.02          |        72 |     0.0037 |             0.0022 |                                    0.0019 |
| fold10_lab05_fb0.03 |        72 |     0.0159 |             0.0147 |                                    0.0120 |
| iid_fb0.03          |        72 |     0.0014 |             0.0005 |                                    0.0006 |
| fold10_lab05_fb0.05 |        72 |     0.0080 |             0.0030 |                                    0.0032 |
| iid_fb0.05          |        72 |     0.0005 |             0.0001 |                                    0.0001 |

The six largest FWER among the independent-condition configurations (these are the partial nulls in which a chain's level is doubled by the other chain's completion):

| cfg                    |   n_true_null |   fwer |
|:-----------------------|--------------:|-------:|
| alt|null|null|alt|alt  |             2 | 0.0204 |
| alt|alt|alt|alt|null   |             2 | 0.0203 |
| alt|alt|null|alt|alt   |             1 | 0.0201 |
| null|alt|null|alt|alt  |             3 | 0.0201 |
| alt|alt|alt|null|null  |             3 | 0.0199 |
| null|null|null|alt|alt |             4 | 0.0193 |

* With independent conditions the graph never exceeds 0.025 in any of the 72 configurations (max 0.0204 plain, 0.0200 with strong dependence between P1, P2, P3; global null 0.0169 and 0.0157): the implementation is consistent with the theory (Bonferroni-based, so also with the chosen dependence).
* With fold 0.05 the **plain** test already violates the bound (global null 0.0303, 39 of 72 configurations above 0.025 + 2 SE); with fold 0.10 and lab 0.05 it is 0.088. The graph is valid only if its local tests are valid; this is the item (a) result seen through the graph.
* The fallback restores validity at the R4 corner only for rho_s0 >= 0.03 (max FWER 0.0159; rho_s0 = 0.02: 0.0299 with 33 configurations above 0.025; 0.01: 0.0542). Under independent conditions the fallback's global-null FWER is 0.0005 (maximum 0.0014; rho_s0 = 0.03).

## 8. Item (f): code path (not run on Samsung)

`item_f_rho_report(scores, comp_col, pinn_col, source, fold_col=None, lab_col=None)` in `sim_v4.py` takes one row per condition with the two arms' **inner-CV training-side** scores (the argument `source` must be the literal
`'inner_cv_training_side'`; anything else raises). It returns n, Pearson rho of the log scores and on the raw scale, the CVs, the SD, skew and median of L = ln(comp/pinn), the rho implied by SD(L), the share of L > 0, the ANOVA intra-fold and intra-lab correlation of the signs, and the exact i.i.d. power
of P1S at r = 0.05-0.30 for both levels. It is a power report only; no rule reads it. Smoke test on the **ISU pilot** (power law against LightGBM, 62 conditions; `f_smoke_isu_pilot.json`): rho of the log errors 0.54 (raw 0.70), CV 0.45 / 0.45, SD(L) 0.40, skew of L -1.42, so the ISU pair sits **below** the rho = 0.6 end of the
(b) grid on the log scale (STATS_RULING 7 quotes 0.75 for a raw-scale correlation of a different definition); the Samsung estimate must say which scale it uses.

## 9. Values for PREREG_v4

Paste-ready blocks. All are simulation values under the models of section 2 and are to be labelled "simulation, not a result".

**[SIM: a]** Under shared fold and lab random effects with ISU-like skew and nested-subset correlation across the nine grid cells (100,000 replicates per scenario; 5 folds of 8 conditions, labs HM 17 / INT 19 / SIE 4), the exact one-sided sign test has size 0.0083 (28 of 40) and 0.0192 (27 of 40) for independent
conditions, but exceeds 1.2 times its nominal level (0.0125, 0.025) once the intra-fold correlation of the latent log ratio reaches 0.03-0.05, or a random intra-lab correlation reaches 0.015-0.023; at intra-fold 0.10 with intra-lab 0.05 the size is 0.054 / 0.081 (4.3 and 3.3 times nominal). The criterion of D016 (<= 1.2 x nominal)
is therefore **not met** by the plain exact test. Pre-set fallback, to be approved by the gate auditor before any Samsung score: the same sign test with a fixed design effect (Beta-binomial null with pairwise sign correlation rho_s0 = 0.03, design effect 2.17, a = b = (1/0.03 - 1)/2 = 16.17);
positives needed at n = 40: 33 at local level 0.005, 32 at 0.00625 and 0.00833, 31 at 0.0125, 30 at 0.025; the P3 test uses the same table. Simulated worst size over all nine cells and P3, three shapes, intra-fold <= 0.10, random intra-lab <= 0.05: 0.88 (level 0.0125) and 0.79 (level 0.025) times nominal; it is not
distribution-free: it holds when the average pairwise correlation of the sign indicators does not exceed 0.03. A fold-blocked permutation is infeasible with five folds (smallest p-value 1/32 = 0.031). Under independent conditions the fallback has size 0.0003 / 0.0011. Plain exact-test results stay as a descriptive row.

**[SIM: b]** Power of P1 at g1 (simulation; exact binomial for independent conditions; relative reduction of the median condition error needed for 80 % power of tier S at local level 0.0125 / 0.025, ISU-like right skew; normal and left skew in section 5.1): rho 0.6: 0.201 / 0.182 (plain), 0.256 / 0.238 (fallback rho_s0 = 0.03);
rho 0.75: 0.166 / 0.151 (plain), 0.212 / 0.197 (fallback); rho 0.9: 0.116 / 0.105 (plain), 0.147 / 0.136 (fallback). With the fallback at level 0.0125 and rho 0.75 the power of P1S is 0.05 / 0.28 / 0.71 / 0.96 for a true relative reduction of 0.10 / 0.15 / 0.20 / 0.25
(plain test: 0.28 / 0.69 / 0.95 / 1.00). Chains in the graph (fallback, rho 0.75, r1 = 0.20 gain over D*, A1-A9 gain 0.15, g4 gain 0.05, corr(g1,g4) = 0.6): P(P1N and P1S) = 0.71, P(also P2) = 0.70, P(also P3) = 0.36 when the K chain never rejects; 0.82 / 0.82 / 0.53 when the K chain completes first
(plain tests: 0.95 / 0.95 / 0.80 and 0.98 / 0.98 / 0.89). P3 alone (rho 0.75, corr(g1,g4) = 0.6): power for a true median D of 0.10 / 0.15 / 0.20 / 0.30 is 0.36 / 0.73 / 0.94 / 1.00 (plain test) and 0.08 / 0.32 / 0.67 / 0.98 (fallback); with corr 0.3 the plain test reaches 0.73 only at D = 0.20 and the fallback 0.32. P2 is
bound by the A1-A9 gain: for a 5 % gain P(also P2) is 0.17 (plain) and 0.02 (fallback).

**[SIM: c]** K1 (tier N, margin -ln 1.10): power at true equality of A15 and A1 is 0.96 / 0.98 (levels 0.0125 / 0.025) for rho(A15, A1) = 0.95 and 0.73 / 0.83 for 0.90 (plain test); 0.74 and 0.33 at 0.0125 with the fallback; with A15 2 % worse the plain power is 0.82 (rho 0.95) and 0.51 (0.90) at 0.0125. K2 (A15 against G15): tier N at equality
0.96 / 0.73; tier S needs a true gain of about 9 % (rho 0.95) or 12 % (rho 0.90) for 80 % power, and has power 0.18 (rho 0.95) / 0.09 (0.90) at a 5 % gain (plain, 0.0125). Chain P(K1, K2N, K2S) with A15 as good as A1 and a 5 % gain over G15: 0.17 (plain, rho 0.95, K levels 0.0125), 0.02 (fallback).

**[SIM: d]** The graph with the seven nodes, weights 1/2 on P1N and K1 and the two hand-over edges was checked in 72 hypothesis configurations per setting, 50,000 replicates each, with the dependence of the section 2 arm model: with independent conditions the largest FWER is 0.0204 (global null 0.0169; strong-dependence variant 0.0200 / 0.0157), below 0.025 in every configuration. With
shared fold and lab effects the plain exact test breaks the bound (global null 0.0303 at intra-fold 0.05, 0.0877 at intra-fold 0.10 with intra-lab 0.05); with the fallback (rho_s0 = 0.03) the maximum is 0.0159 at that corner.

**[SIM: e]** Exact order-statistic interval of the median at coverage 1 - 0.05/9 with n = 40 exists: [L(11), L(30)], coverage 0.9978 (target >= 0.9944); n = 19: [L(4), L(16)] (0.9956); n = 13: [L(2), L(12)] (0.9966). Unadjusted 95 %: [L(14), L(27)] (0.9615) - nine such intervals cover simultaneously 0.79 at independence. Under fold/lab clustering the rank-11 interval undercovers
(per-cell 0.9626 at intra-fold 0.10 with intra-lab 0.05); the fallback rank is 8, [L(8), L(33)], per-cell coverage >= 0.9949 up to that corner.

## 10. Deviations from the judge's design, assumptions and limits

1. **The fallback is not a permutation test.** The judge's example (fold-blocked permutation) cannot reject at 0.025 with 5 folds; the fixed design-effect sign test is what could be simulated and shown valid on a stated region. It is assumption-dependent (average sign correlation <= rho_s0), not distribution-free.
2. **The ICC range and the cell multiplier are assumptions.** No intra-fold or intra-lab correlation of a log ratio is measured; the SNL anchor is uninformative (section 4.5). The scenario regions R1-R6 and the choice of R4 are judgements. The multiplier 1 / 0.75 / 0.5 over m = 8 / 16 / 32 makes the scarce cells worst by construction.
3. **Lab as random effect is the pessimistic reading** (3 labs, drawn anew); with labs as fixed strata the plain test is conservative against lab effects (4.3) and rho_s0 = 0.02 suffices for fold clustering up to 0.10. The designer must say which target the estimand has.
4. **Skew.** The smoothed ISU shape has skewness +1.00 (not +1.06 as in the earlier sims); in (a) the skew is on the condition-specific part and increases the size for the same ICC (break-even 0.033 against 0.049).
5. **rho grid.** The judge's grid {0.6, 0.75, 0.9} is used for the arms' log-error correlation of P1. The ISU pilot pair (power law against LightGBM) has 0.54 on the log scale (62 conditions), below the grid; A1 vs D* on Samsung is unmeasured (item (f)).
6. **Dependence among the nodes** (tree structure, conditional independence of D* and A9 given A1, kappa) is an assumption; the chain probabilities were insensitive to extra D*-A9 correlation (< 0.002) and sensitive to kappa for P3 only.
7. **Replicates** were set to fit the time limit: 20,000 for chain probabilities (SE <= 0.0035), 40,000 for dependent power (SE <= 0.0025), 50,000 per configuration in (d), 100,000 in (a). Total CPU about 36 minutes (a 7, b 10, c 3, d 13, b5/c3 3, fallback checks 1; two processes at a time).
8. Levels in the graph are 0.0125 and 0.025; the secondary Holm family's levels (0.005 to 0.025) are tabulated for the fallback (`fb_crit_levels`) but not simulated as a family.
9. Reverse-S safety tests (outside the graph, 0.025 one-sided) use the same table (30 of 40 under the fallback) and were not simulated separately.
10. Ties with a margin count as not positive (conservative); the simulation has none.

## 11. Files and reproduction

`runs/prereg/stats_sim_v4/`: `sim_v4.py` (a, fb, fbest, b, b5 (chains under the fallback), c, d, e, f), `make_structure.py` (writes `cond_structure.csv`), `anchor_icc.py`, `build_tables.py` + `build_result.py` (this file from `RESULT_template.md` and `tables.md`);
data: `a_size.csv`, `a_hist.json` (histograms of positives per scenario and cell), `fb_size.csv`, `fbest_size.csv`, `b1_p1_power_iid.csv`, `b2_p1_power_dep.csv`, `b3_chain.csv`, `b4_p3_power.csv`, `b5_chain_fallback.csv`, `c1_k_power_iid.csv`, `c2_k_chain.csv`, `c3_kchain_fallback.csv`, `d_fwer.csv`, `e_intervals_exact.csv`, `f_smoke_isu_pilot.json`, `anchor_icc_snl.json`; logs `log_*.txt`.
Reproduce (project root, `.venv/Scripts/python.exe -P`): `make_structure.py .`; `sim_v4.py a 100000`; `sim_v4.py fb`; `sim_v4.py fbest 40000`; `sim_v4.py b 40000`; `sim_v4.py b5 20000`; `sim_v4.py c 40000`; `sim_v4.py d 50000`; `sim_v4.py e`; `sim_v4.py f`; `anchor_icc.py .`; `build_tables.py`; `build_result.py`.
Tests: `.venv/Scripts/python.exe -P -m pytest code/tests/test_graph_test.py -q`.
