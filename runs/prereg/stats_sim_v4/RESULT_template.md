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

{{T:e_exact}}

For n = 40 a simultaneous 95 % interval over the 9 cells of one contrast (Bonferroni, two-sided alpha/9 = 0.0056) exists and is [L(11), L(30)] of the sorted condition log ratios, coverage 0.9978 (>= 0.9944).
It also exists for n = 19 (S2) and n = 13 (Test C). The unadjusted 95 % interval is [L(14), L(27)] (0.9615); nine of them cover simultaneously only 0.79 of the time at independence (table below).
Coverage under clustering (same scenarios as (a), ISU-like skew, g1 and all nine cells together):

{{T:e_cov}}

The rank-11 intervals lose their guarantee with fold/lab clustering (0.9626 at g1 for intra-fold 0.10 and intra-lab 0.05; 0.8658 for all nine cells together). Under the fallback of
section 4.4 the same arithmetic gives rank 8 ([L(8), L(33)]); minimum per-cell coverage over the scenario regions R3-R6 (R-definitions in 4.4):

{{T:e_cov_fb}}

Rank 8 keeps every cell above 0.9944 up to R4 (intra-fold 0.10, intra-lab 0.05) and so, by Bonferroni, the nine-cell family above 0.95 there.

## 4. Item (a): size of the exact sign test and the fallback

### 4.1 Size of the plain exact test

Ratio of the simulated rejection rate at the null boundary to the nominal local level (0.0125 / 0.025), cell g1 = (m 8, k 2), corr(g1,g4) = 0.6, random lab effects; `*` = above 1.2.
At zero clustering the ratios are 0.65-0.69 / 0.76-0.78 (exact sizes 0.0083 / 0.0192 against nominal 0.0125 / 0.025). Rows: intra-fold correlation; columns: intra-lab correlation.

**Normal**

{{T:a_main_normal}}

**ISU-like right skew (skewness +1.0)**

{{T:a_main_isu_right}}

**ISU-like left skew (mirror)**

{{T:a_main_isu_left}}

Fine sweeps (g1, ratio to nominal), and the interpolated break-even correlation at which the ratio crosses 1.2:

{{T:a_fine_fold}}

{{T:a_fine_lab}}

{{T:a_breakeven}}

So the plain test passes the "<= 1.2 x nominal" criterion only for intra-fold correlation below about 0.03-0.05 *or* random intra-lab correlation below about 0.015-0.023 (the lower value is the ISU-like skew). The
mean number of positives stays 20; the inflation is a variance effect: the variance of the positives count is 1.31 (intra-fold 0.05), 1.57 (0.10) and 2.15 (intra-fold 0.10 with intra-lab 0.05) times the binomial 10 (ISU-like skew, g1).

### 4.2 Grid cells and the P3 contrast

Ratio to nominal at level 0.0125 for the nine cells (ISU-like skew, corr(g1,g4) = 0.6), and for D = L(g1) - L(g4) (P3: sign test of D > 0):

{{T:a_cells}}

The scarce cells (m = 8) are worst because the assumed fold/lab share is largest there (multiplier 1 / 0.75 / 0.5); the k axis changes nothing (same shares). P3 behaves like a single cell with the
shares of g1 and g4 combined. Dependence of the P3 size on corr(g1,g4):

{{T:a_kappa}}

### 4.3 Lab effects as fixed design offsets

If labs are treated as strata of the design (offsets fixed, labs not redrawn; lab variance share l of the latent variable), lab effects make the sign test **conservative** (variance of the positives count below the binomial), and only fold clustering inflates it:

{{T:a_fixedlab}}

### 4.4 Pre-set fallback and why a permutation test cannot be it

* **Fold-blocked permutation / sign-flip of whole folds is not feasible:** 5 folds give 2^5 = 32 sign patterns, so the smallest attainable p-value is 1/32 = 0.031 > 0.025; it can reject nothing. Lab-blocked: 2^3 = 8 patterns. A cluster
  bootstrap on 5 folds has no usable coverage. A design effect **estimated** from the five folds (cluster-robust variance of the positives count, floor DE0) does not work either (selected rows below, ISU-like skew, nominal levels 0.0125 / 0.025):
  with DE0 = 1 (pure estimation) the t4 reference is vacuous (size 0.0000-0.0084) and the normal reference is liberal under clustering (0.0114-0.0429, up to 3.4 x nominal); with a floor of DE0 = 2 the normal-reference test behaves like a fixed design effect (size 0.0004-0.0186), so estimation adds nothing over a fixed value.

{{T:fb_est}}

* **Fallback adopted for specification: exact sign test with a fixed design effect.** The positives count under H0 is Beta-binomial(40; a = b = (1/rho_s0 - 1)/2) with pairwise sign correlation rho_s0 (design effect 1 + 39 rho_s0). A node is rejected at local level `a` iff
  P(BetaBin >= positives) <= a. No random numbers. The guarantee is **assumption-dependent, not distribution-free**: it holds when the average pairwise correlation of the sign indicators is at most rho_s0. Positives needed:

{{T:fb_crit}}

and at the other levels in use (secondary Holm family of five at 0.025; graph levels 0.0125, 0.025):

{{T:fb_crit_levels}}

Worst ratio of simulated size to nominal (level 0.0125 / level 0.025), maximum over all nine cells and the P3 contrast and over the three shapes, in the regions of (intra-fold, intra-lab random) correlation:

{{T:fb_region}}

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

{{T:b1_mde}}

Power at selected r, level 0.0125 (28 of 40 plain; 30 / 31 of 40 for rho_s0 0.02 / 0.03) and level 0.025:

{{T:b1_power_0125}}

{{T:b1_power_025}}

Non-inferiority tier P1N (margin -ln 1.10): r at which P1N reaches 80 % power, and its power at true equality (r = 0):

{{T:b1_N}}

With fold/lab clustering (rho = 0.75, ISU-like skew, simulated) the plain test's power moves little for r >= 0.15; the fallback (31 of 40) loses 0.24-0.40 of power against the plain test at r = 0.15-0.20 with or without clustering (clustering raises the fallback's own power slightly, 0.29 to 0.35 at r = 0.15):

{{T:b2_dep}}

**Reading.** A 10 % gain is nearly undetectable (power 0.05 to 0.28 at rho 0.75 depending on the test); 15 % is detected 0.28-0.69 of the time; 20 % 0.71-0.95. The fallback's 80 %-power gain at rho 0.75 is 0.212 (ISU-like skew) to 0.253 (normal) against
0.166 to 0.198 for the plain test.

### 5.2 Chains P1 -> P2 -> P3 in the graph (plain exact tests, i.i.d. conditions)

P(P1N and P1S rejected), P(also P2), P(also P3) in the graph, ISU-like skew, corr(L(g1),L(g4)) = 0.6, A1 vs A9 gain r2 = 0.15, g4 gain over D* r4 = 0.05 (so median D = ln((1-r4)/(1-r1)) is the "median D" column).
"K_never": the K chain never rejects (P-chain levels 0.0125); "K_first": the K chain completes first (levels 0.025):

{{T:b3_chain}}

Dependence of the chain on r2 (rho 0.75, r1 = 0.20, r4 = 0.05; K never) - P2 is the cheap node when A9 is a weak competitor and the binding one when the law adds 5 %:

{{T:b3_r2}}

Dependence of P3 on corr(L(g1), L(g4)) and r4 (rho 0.75, r1 = 0.20, r2 = 0.15):

{{T:b3_kappa}}

An extra (D*, A9) correlation of 0.15 beyond the tree structure changes the chain by < 0.002 (rho 0.75, r1 = 0.20): the chain probabilities are insensitive to the L1-L2 dependence.

### 5.3 P3 on its own: power of the trend test

D = L(g1) - L(g4), sign test D > 0, plain test, level 0.0125, i.i.d., ISU-like skew. delta = median(D) in log units (0.10 = the g1 advantage exceeds the g4 advantage by about 10 %). "SD of D" is the Gaussian SD on the log scale:

{{T:b4_p3}}

Level 0.025:

{{T:b4_p3_025}}

With the fallback (rho_s0 = 0.03) and with fold clustering 0.10 (rho 0.75):

{{T:b4_p3_dep}}

P3 is the least powered node: with corr(g1,g4) = 0.6 and rho 0.75 it needs delta about 0.15 for 0.73 (plain) and about 0.20 for 0.67 with the fallback; with weak cell correlation (0.3) the plain test reaches 0.73 only at delta = 0.20 and the fallback 0.32. At delta = 0 its size is 0.009 (plain) and 0.000 (fallback).

### 5.4 Chains under the fallback (rho_s0 = 0.03), and clustering

Same scenario as 5.2 (rho 1 varying, r2 = 0.15, r4 = 0.05), plain against fallback, with and without fold 0.10 + lab 0.05 clustering (simulated):

{{T:b5_chain}}

Effect of r2 and r4 on the chain under both tests (rho 0.75, r1 = 0.20, K never):

{{T:b5_chain_r2r4}}

## 6. Item (c): power of K1 and K2

K1: L = ln(S_A1/S_A15), tier N (non-inferiority, A15 no more than 10 % worse). Effect = relative excess error of A15 over A1 (S_A15 = (1 + effect) S_A1). K2: L = ln(S_G15/S_A15); effect = relative gain q of A15 over G15. Plain exact test, i.i.d. conditions, ISU-like skew; rho = corr(A15, A1) for K1 and corr(A15, G15) for K2:

{{T:c1}}

Largest A15 excess error (K1) / smallest A15 effect (K2) for 80 % power (blank = not reached; negative = the other side must already be better):

{{T:c1_80}}

K chain in the graph (plain tests), "P_never": P chain never rejects (K levels 0.0125), "P_first": the P chain completes first (K levels 0.025):

{{T:c2}}

Under the fallback (rho_s0 = 0.03; rho(A15,A1) = rho(A15,G15)):

{{T:c3}}

**Reading.** K1 passes when A15 is truly as good as A1 with probability 0.96 only if the two arms correlate at 0.95 (0.73 at 0.90); at the planned correlation 0.90-0.95 the K1 claim therefore has power 0.73-0.96 (plain) and 0.33-0.74 (fallback, level 0.0125) when A15 equals A1. K2 at tier S needs a true gain of 9 % (rho 0.95) to 12-15 % (0.90) for 80 % power, and the "K=" outcome (K2 not S) is the expected one if the KAN-GAM gap is as small as P4 found.

## 7. Item (d): FWER of the graph

72 configurations per setting: L1 median at the N boundary (-ln 1.10, both nulls true), at 0 (N false, S true), or at a gain of 0.40 (both false); L2 at ln 1.02 or at 0.40; D at 0 or 0.40; K1 at -ln 1.10 or at +0.15; K2 at -ln 1.10 / 0 / +0.35. A hypothesis is a true null iff its median is at or below its margin;
FWER = P(reject at least one true null). Dependence: the section 2 arm structure; the "highdep" setting uses rho1 = 0.90, A9 extra correlation 0.10 and corr(g1,g4) = 0.9; 50,000 replicates per configuration (SE of a rate near 0.02: 0.0006).

{{T:d_summary}}

Full distribution per setting (mean over configurations that contain a true null):

{{T:d_all}}

The six largest FWER among the independent-condition configurations (these are the partial nulls in which a chain's level is doubled by the other chain's completion):

{{T:d_top_iid}}

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
