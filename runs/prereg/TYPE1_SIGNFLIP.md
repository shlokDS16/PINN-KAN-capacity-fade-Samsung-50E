# Type-I error of the log-ratio rule (studentized sign-flip AND BCa): verdict (2026-11-05)

Requested by D011 judge section 4.3. Role: statistician. Synthetic data only; no Samsung file and no test fold of any dataset was opened.
The only empirical input is the standardised ISU training-side shape (`cond_isu_W4.csv`, as in STATS_RULING section 7).

## VERDICT: the acceptance criterion FAILS at n = 40 and at n = 13. The fallback applies to Test B and to Test C: exact one-sided sign test.

Acceptance (D011 4.3): simulated rejection at the null boundary <= 1.2 x nominal in every cell.
Observed worst ratios (rule = sign-flip p <= a AND BCa lower bound > m; 40,000 simulations per cell; boundaries mean(L) = ln 1.02 and -ln 1.10; levels
a/4, a/3, a/2, a with a = 0.025, "a" being both the last Holm step and the gatekept level):

| Shape of L (CV 0.45; rho 0.95 / 0.90 / 0.75) | n = 40: max ratio to nominal | n = 13: max ratio | Passes 1.2? |
|---|---|---|---|
| ISU-derived, right skew (+1.06) | 0.66 | 0.59 | yes |
| normal | 1.06 | 1.08 | yes |
| failure contamination (10% of conditions, PINN score x 1.33 / 1.45 / 1.68 for rho 0.95 / 0.90 / 0.75, PP skewness -1.06) | **1.30** | **1.54** | **no** |
| ISU-derived, left skew (-1.06, mirror) | **1.86** | **2.14** | **no** |

Contamination, n = 40: ratio above 1.2 in 4 of 6 cells at a/4 (1.25-1.30), 2 of 6 at a/3 (1.23, 1.24), 1 of 6 at a/2 (1.23), none at a (max 1.15).
So even the single shape the ruling names explicitly (c) fails at n = 40 at the low Holm levels. The left-skewed ISU mirror is worse
(1.36-1.86 at every level). Normal and right-skewed errors are conservative or nominal, which is what the sign-flip test promises
under symmetry; the inflation is the usual one of a mean-based test under a heavy left tail with n = 40 (13).

Spot check at the final-analysis settings (100,000 sign flips, 10,000 BCa resamples, 20,000 simulations per cell; contamination, n = 40, six
boundary cells): ratios 1.04-1.38, 10 of 24 level cells above 1.2 (`signflip_spot_contam40.json`). The screening settings (4,000 flips, 1,000
resamples) are therefore not the cause. Note also that under sign flips sum(x^2) is invariant, so the studentized statistic is a monotone
function of the mean: the studentized and plain sign-flip tests are the same test; studentizing cannot repair this inflation.
Monte Carlo SE of a rejection rate at nominal 0.00625 with 40,000 simulations is 0.0004 (ratio SE 0.06); the ratios above 1.2 are well outside it.

## Fallback (D011 4.4): exact one-sided sign test on L - m
Estimand: median over conditions of ln(S_comp/S_PINN); size is exact for any continuous distribution at median(L) = m, so no skew
shape can inflate it. Passing at level a means #(L_c > m) >= k, equivalently the order-statistic lower bound L_(n-k+1) > m (coverage >= 1 - a).

| n | level | k (positives needed) | actual size (nominal) | lower bound |
|---|---|---|---|---|
| 40 | a/4 = 0.00625 | 29 | 0.0032 | 12th smallest |
| 40 | a/3 = 0.00833 | 28 | 0.0083 | 13th |
| 40 | a/2 = 0.0125 | 28 | 0.0083 | 13th |
| 40 | a = 0.025 | 27 | 0.0192 | 14th |
| 13 | a/4, a/3 | 12 | 0.0017 | 2nd smallest |
| 13 | a/2, a | 11 | 0.0112 | 3rd smallest |

Discreteness costs power (n = 40 at a: 0.019 not 0.025); at n = 13 the test is very conservative. Wording changes as the ruling states: "on the
typical held-out condition ... (median)"; relative reduction = 1 - exp(median L) is **not** the mean-based estimate; the pp mean difference and
mean log ratio with BCa intervals are reported beside it as descriptive. Rule `stats_rule.tier` stays for descriptive intervals only.

## Power at the effect sizes of the MDE table (20,000 simulations per cell for the sign test, 5,000 for the sign-flip rule)
Effect = relative reduction r, so the target is median(L) = -ln(1-r) for the sign test (mean(L) for the sign-flip rule). Tier S (margin ln 1.02),
level a/3 (Holm step 1). Columns rho 0.95 / 0.90 / 0.75. Ranges are over the four shapes (min-max).

**Adopted fallback, exact sign test (`signtest_fallback.json`)**

| r | n = 40 | n = 13 |
|---|---|---|
| 0.06 | 0.15-0.28 / 0.08-0.15 / 0.04-0.06 | 0.01-0.02 / 0.01 / 0.01 |
| 0.08 | 0.35-0.63 / 0.17-0.35 / 0.07-0.14 | 0.03-0.07 / 0.02-0.03 / 0.01 |
| 0.10 | 0.61-0.89 / 0.32-0.61 / 0.13-0.26 | 0.07-0.17 / 0.03-0.07 / 0.01-0.02 |
| 0.15 | 0.97-1.00 / 0.77-0.98 / 0.39-0.67 | 0.26-0.58 / 0.11-0.28 / 0.04-0.08 |
| 0.20 | 1.00 / 0.97-1.00 / 0.71-0.94 | 0.55-0.93 / 0.27-0.61 / 0.09-0.21 |

Non-inferiority (tier N, margin -ln 1.10) at true equality, a/3: n = 40: 0.71-0.95 / 0.40-0.72 / 0.16-0.32 (previous Wilcoxon + BCa: 0.96 / 0.68 / 0.24);
n = 13: 0.09-0.22 / 0.04-0.10 / 0.02-0.03 (the test cannot support a non-inferiority claim at n = 13).

Approximate 80%-power effects of the fallback at n = 40: about 0.09-0.12 (rho 0.95), 0.12-0.16 (0.90), 0.17-0.22 (0.75), against 9.8 / 13.7 / 19.4%
for the earlier rule (which was liberal under skew): a loss of about 1-3 relative points, largest under contamination. Test C (n = 13) cannot reach 80% below r = 0.20 for
any rho except 0.95 with right-skewed or normal errors: it is a descriptive check, as already ruled.

**For information, the rejected sign-flip rule** (`signflip_*.json`, same level, n = 40): S power at r = 0.10 is 0.75-0.94 / 0.45-0.64 / 0.20-0.28, but under left
skew and contamination these powers include the excess rejection shown above and must not be quoted.

## Consequences for the freeze
1. Primary test for every contrast in Test B and Test C: exact one-sided sign test on L - m at the Holm step level; abstract wording about the median condition.
2. The Wilcoxon-AND-BCa rule and the sign-flip-AND-BCa rule are both appendix-only. The pp mean tier of STATS_RULING 2.3 remains a descriptive row; if its tier differs
   from the sign-test tier the abstract states both (D011 4.1).
3. Because the estimand is now the median, the Holm family, the margins (ln 1.02, -ln 1.10), the hierarchy (N then S), H6 in the family and the
   gatekept H2 are unchanged. The power numbers of STATS_RULING section 7 are superseded by the table above. Remaining assumptions: rho, CV 0.45, seed SD 0.05 E and
   the contamination design (fraction 0.10) are assumptions; the ISU shape is a training-side measurement.
4. No rule changes after this (D011 4.5).

## Files
Code `code/prereg/stats_signflip_sim.py` (null and power, all shapes), `code/prereg/stats_signtest_sim.py` (fallback). Outputs in `runs/prereg/stats_ruling/`:
`signflip_{isu_right,isu_left,normal,contam}.json`, `signflip_spot_contam40.json`, `signtest_fallback.json`, logs. Reproduce:
`.venv/Scripts/python.exe -P code/prereg/stats_signflip_sim.py <ROOT> <shape> 40,13 <shape> 40000 5000 4000 1000` (about 2.5 min per shape);
spot check `... spot_contam40 40 contam 20000 0 100000 10000 spot` (about 5 min); `... stats_signtest_sim.py <ROOT> 20000`.
