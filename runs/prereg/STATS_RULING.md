# Statistics ruling for the confirmatory experiments (2026-11-05, before any Samsung label is scored)

Role: statistician (owner of OPEN-4, OPEN-5 and the D007 re-open clause). Does not edit `PREREG_DRAFT.md`; section 9 lists the edits
the experiment-designer must make. Reading: full text of CONTRACT.md, `04_judge.md` (all, section 6 in detail), PREREG_DRAFT.md,
P3/P4/P5 RESULT.md, DECISIONS D007, `p3_headroom.py`, and `experiments_meta.csv` (identifiers only). No Samsung capacity file was
opened. ISU and SNL were touched on **training sides only**, per outer fold, with the P3 enforcement (outer test cells dropped before
any computation; `stats_warp_calibration.py`, audit field `test_cells_read: false`). No outer test fold of any dataset was read,
predicted or scored. Nothing here is a result about PINN-KAN; every number below is a pilot training-side measurement or a stated
simulation assumption. Files: code in `code/prereg/` (`stats_rule.py` = the decision rule as code, `stats_warp_calibration.py`,
`stats_power_sim.py`, `stats_mde_table.py`); outputs in `runs/prereg/stats_ruling/`.

## 0. Rulings at a glance

| # | Question | Ruling |
|---|---|---|
| 1 | Replicate floor | It is **not a lower bound** for held-out conditions and is renamed *replicate spread* `R_LOO` (descriptive). A window-aware replicate predictor `R_WARP` is added as a second descriptive reference. **Neither is a margin and neither is a gate.** D007's rule (gate at 1.2) is superseded by a hierarchical superiority-then-non-inferiority test; D007's consequence for the abstract stands. |
| 2 | Margins | Relative to the comparator's training-side inner-CV score `E`: superiority `delta_S = 0.02 E`, non-inferiority `delta_N = 0.10 E`, per outer fold, pooled by test-condition count. Computed and written to `runs/prereg/margins.json` before any outer prediction exists. |
| 3 | Holm family | Four hypotheses: H1a (S), H1b (S), H1c (N, then S as fixed-sequence follow-up), **H6 (S) joins the family (OPEN-5: yes)**. H2 is gatekept, not in the family. Family level 0.025 one-sided (= 0.05 two-sided for a directional claim). |
| 4 | Unit and test | Unit = held-out condition (40 in Test B). Paired difference of seed-averaged condition scores. Exact one-sided Wilcoxon on `d - margin` AND BCa one-sided bound of the mean, both at the Holm step level. Lab and stage: not blocking factors in the primary; lab-stratified bootstrap and by-lab/stage tables are mandatory sensitivity rows. |
| 5 | Seeds | 5 final refits (0-4) per arm and fold; condition score = mean over seeds of the per-seed condition RMSE; seeds are never units; no best-seed reporting; tuning is not re-seeded (stated limitation). |
| 6 | Abstract | Per primary contrast: n, mean paired difference in pp with 95% BCa interval, relative reduction with interval, tier reached (S / N / none). No p-values, no "significant", no "outperforms" below tier S. |
| 7 | Power | n = 40 detects (80%, Holm-3 first step) a **9.8% / 13.7% / 19.4%** relative improvement when the arms' condition errors correlate 0.95 / 0.90 / 0.75. Title 1 (superiority over all three) needs about 10% for H1a, H1b and about 19% for H1c. Details in section 7. |

---

## 1. Replicate floor, a better reference, and D007

### 1.1 What the floor is and is not
`R_LOO` (judge, P3 `replicate_floor`): for cell j of condition k, RMSE of the mean trajectory of the other replicates against j at j's
forecast times; mean over replicates, median over training conditions. It is a valid lower bound only for an *oracle that knows the
condition's other replicates and not the held-out cell*. It is **not a bound for Test B** for three reasons, two of them mechanical:
1. Learners see the held-out cell's own window; `R_LOO` does not (P3 caution 1; ratios 0.82-1.04 on ISU).
2. The mean of r-1 other replicates carries its own noise: under iid replicate noise `R_LOO` is inflated over single-cell noise by
   sqrt(1 + 1/(r-1)) = 1.15 for 4 replicates (ISU) and 1.22 for 3 (Samsung's 35 of 40 conditions).
3. A model pools 39 other conditions to denoise a condition's curve; the replicate mean cannot.
Conversely it is not "reachable" either: for a held-out *condition* a model also pays a condition-generalisation error that no replicate
quantity measures. So no replicate-based number is a floor for Test B. It is a floor-like yardstick only for Test A (held-out replicates
of seen conditions).

### 1.2 Reference definitions (both descriptive, computed on training sides only, same window and forecast set as the endpoint)
Loss `l_j(t) = 1 - r_j(t)` (retention relative to the cell's own reference check-up). `m_{-j}(t)` = mean of `l_i(t)` over the other
replicates that reach t (linear interpolation in time, as P3). Window times `t_1..t_w` exclude the reference check-up; `t_w` is the last.
- `R_LOO`: as P3 (unchanged, kept for continuity). Named **replicate spread**.
- `R_WARP` (window-aware replicate predictor): forecast `l_hat_j(tau) = m_{-j}(tau) + [l_j(t_w) - m_{-j}(t_w)]` (additive form) or
  `l_hat_j(tau) = kappa_j m_{-j}(tau)`, `kappa_j = clip( sum_i l_j(t_i) m_{-j}(t_i) / sum_i m_{-j}(t_i)^2 , 0.25, 4)` (multiplicative form);
  no label after j's window is used for j. Condition value = mean over replicates of cell RMSE (pp); `R_WARP` = median over training
  conditions with >= 2 replicates, **for the form with the lower training-side median in that outer fold** (rule, ties to additive).
Report `E/R_LOO` and `E/R_WARP` (E = the arm's pooled score) in Table 1 as context. Neither enters a test or a margin.

### 1.3 Evidence (training sides, 5 outer folds of the P3 splits, W = 4 weeks ISU / 100 cycles SNL; `warp_*.json`)
| Dataset | `R_LOO` | `R_WARP` mult. | `R_WARP` add. | best tuned learner (P3) | ratio / `R_LOO` | / WARP mult. | / WARP add. |
|---|---|---|---|---|---|---|---|
| ISU | 5.75 pp | 5.60 | 5.24 | 5.13 pp | **0.90** | 0.92 | **0.98** (folds 0.89-1.15) |
| SNL | 2.62 pp | 3.38 | 1.45 | 2.97 pp | **1.13** | 0.89 | **2.06** (folds 1.60-2.60) |

ISU: the window barely helps a replicate predictor (5.75 to 5.24 pp): the learners are at the reference under every definition.
SNL: the additive window offset almost halves the reference (2.62 to 1.45 pp), the multiplicative form worsens it. The *same* learner
errors give 1.13, 0.89 or 2.06 depending on the definition. The reference quantifies noise plus window information; it does not say
how much a model can still gain at unseen conditions. A gate built on it cannot be trusted to decide the test type.

### 1.4 Does D007 stand?
D007 (contrast (iii) = non-inferiority on ISU and SNL, from the 1.2 gate) is **re-opened in part, as its own clause allows**.
- *ISU*: the NI conclusion stands under all three definitions (0.90, 0.92, 0.98; all below 1.2). Consistent with the data.
- *SNL*: the verdict is definition-dependent (1.13 / 0.89 / 2.06); the data do not support a pre-decided test type either way.
- *Samsung*: "decided by the same rule once data are in" is **withdrawn**. The gate is retired for all datasets.
- The draft margin `delta = R_LOO` could never be met as a superiority margin: on ISU it exceeds the comparator's own error (5.75 > 5.13 pp),
  on SNL it is 88% of it (2.62 of 2.97 pp). As a non-inferiority margin it would be 112% of E on ISU: vacuous. OPEN-4 is therefore answered: **the floor is not used as a margin**.
- Replacement: the **hierarchical rule** of section 2.3, applied to H1c on every dataset. It contains the NI outcome D007 wanted and
  allows superiority only if the interval earns it. D007's consequence stands unchanged: *the abstract cannot say "beats all
  data-driven models" unless H1c reaches tier S*. This change uses no Samsung data and no test fold; it is fixed before confirmatory runs.
  The lead should log it as a supersession row of D007 (not an edit).

---

## 2. Margins and the hierarchical test

### 2.1 Quantities (all from training-side data)
For comparator arm c and outer fold f: `E_f^c` = inner-CV condition-mean window-forecast RMSE (pp) of c's *selected* configuration on f's
training conditions (the same inner partition and metric used for tuning and for comparator selection; A10 and A3-type fixed-form arms get
the same 3-fold inner CV). Pooled `E^c = sum_f n_f E_f^c / sum_f n_f` with `n_f` = test conditions in fold f. For Test C, S2 use their own
training side. `margins.json` (E^c, delta_S, delta_N per contrast) is written and hashed after tuning ends and before any final refit
is applied to a test condition.

### 2.2 Margin values (rule)
- **Superiority margin `delta_S = 0.02 E^c`** (relative reduction of at least 2%). Purpose: exclude differences of no consequence while
  staying below the effect sizes the pilots suggest (P5: 3-14% per draw). Not zero, per the judge ("effect below the margin").
- **Non-inferiority margin `delta_N = 0.10 E^c`** ("no worse than 10% above the comparator"). Judgement, not derivation; stated as such.
  Sensitivity rows (descriptive): `delta_S` in {0, 0.05}, `delta_N` in {0.05, 0.15}.
- The replicate spread is **not** in the margin: with E = R on the pilots a margin of R is the whole error, and on Samsung E/R is unknown
  and may be far from 1.
- Illustration (pilot E, not Samsung): ISU E = 5.13 pp gives 0.10 and 0.51 pp; SNL E = 2.97 pp gives 0.06 and 0.30 pp.
- Contrast direction: `d_c = S_comp,c - S_PINN,c` (condition score in pp), positive favours PINN-KAN.
- Heteroscedasticity: condition-error CV is 0.45 on both pilots (training sides), so the pp-scale mean difference is dominated by hard
  conditions. The primary stays in pp (judge's endpoint). Mandatory robustness row: the same rule on `log(S_comp/S_PINN)` with margins
  `log(1.02)` and `-log(1.10)`; if the tier differs from the primary the abstract states both.

### 2.3 Hierarchical test for one contrast at Holm step level `a`
A contrast **passes margin m** iff (i) exact one-sided Wilcoxon signed-rank p of `d - m` (H0: pseudo-median <= m) is <= a, AND (ii)
the one-sided BCa lower limit of mean(d) at confidence 1 - a (10,000 condition resamples) exceeds m. Tiers: **S** passes `delta_S`; **N**
passes `-delta_N` but not S; **none** otherwise. Implementation: `stats_rule.tier`. The null of N is nested in the null of S, so testing
N then S in sequence at the same level needs no extra correction. "Equivalent" wording needs a two-sided TOST at `+-delta_N`; N alone is
"non-inferior".
Behaviour of the rule, from simulation (family level 0.025, section 7): rejection at the null boundary is below nominal for the skewed
shape measured on ISU (max 0.0045 / 0.0050 / 0.0155 at nominal 0.00625 / 0.00833 / 0.025) and about nominal for normal errors
(0.0075 / 0.0105 / 0.0275); for a strong **left** skew of d (a few conditions where PINN-KAN fails badly), it is liberal, up to
0.0145 / 0.017 / 0.0395 (1.6-2.3 times nominal). That is the price of using a mean-based bound with n = 40; the share of non-finite
forecasts and the trimmed-mean/log-ratio rows are therefore mandatory beside any tier claim.

---

## 3. Holm family (OPEN-5)

Family, one-sided level 0.025 (two-sided 0.05 for a directional claim; the 95% intervals in tables then agree with the decision):
1. H1a: A9 (lambda = 0) vs A1 - hypothesis S.
2. H1b: inner-CV-best of A3-A7 vs A1 - hypothesis S.
3. H1c: inner-CV-best of A11/A12 vs A1 - **enters with the N p-value**; its S claim is a fixed-sequence follow-up at the same
   multiplicity level (compare `p_S x (Holm multiplier of H1c)` with 0.025).
4. **H6: A10 (Stroebl semi-empirical) vs A1 - hypothesis S. Included.**
Why H6 joins: it is the closest prior art and the abstract will say how PINN-KAN stands against the dataset authors' model; any contrast
named in the abstract/title/highlights must be in the family or be labelled exploratory. Cost: if A10 is as inadequate as its authors
state, its p is tiny and it takes Holm step 1, costing the others nothing; worst case it raises the first threshold from alpha/3 to
alpha/4 and the 80%-power effect by at most 0.5 points of relative improvement (section 7). The judge's claim (the conjunction of the
three model-part contrasts) is unchanged; H6 failing triggers outcome row K, not refutation.
H2 (hard vs soft) is **not** in the family. Outcome A (soft better) is tested only if the family passes (gatekeeping, no extra error
cost). Outcome C (hard better) is tested regardless (safety finding). Order of evaluation: A (tier S on `d = S_hard - S_PINN`, margin
`delta_S` of the hard ODE's E), then C (reverse S at `delta_S`), then B (TOST at `+-delta_N`); otherwise "unresolved", worded as B.
H4 (Test C): Holm-3 within Test C, secondary, n = 13. H5/S2 and the rest: exploratory unless the abstract uses them, then labelled
secondary with their own N rule at `delta_N`. Windows k-1, k+2 and all other rows: descriptive.

---

## 4. Unit of analysis, paired test, lab and stage

- **Unit = held-out condition** (Test B 40, Test C 13, S2 19, ISU 63, SNL 23). Condition score = mean over seeds, then mean over the
  condition's scored cells, of cell RMSE (pp). Equal weight per condition (estimand: the designed region of stress space, not the
  replicate count; 5 centre conditions have 6-12 cells and are not up-weighted). Sensitivity: weights by scored cells; a two-stage
  bootstrap (conditions, then cells within).
- **Estimand** per contrast: `psi = (1/N) sum_c [S_comp(c) - S_PINN(c)]` over the held-out conditions for the frozen pipeline, expected
  over initialisation seeds. Inference is to conditions drawn from this design hull for this cell type; not to other chemistries and not to
  stress outside the hull.
- **Pairing:** by condition (both arms scored on the same cells and windows). Seeds are not paired across arms; they are averaged first.
- **Dependence not modelled:** neighbouring conditions share training information and conditions in one fold share one fitted model;
  the standard errors treat conditions as exchangeable. Report per-fold means and the number of folds where the sign agrees; this is
  descriptive. Design effect: section 7 gives n = 27 as a "design effect 1.5" scenario.
- **Lab and stage.** From the metadata (identifiers only): of the 40 cycling conditions 37 are single-lab (INT 19, HM 14, SIE 4) and 3 are mixed
  (23 C is INT 6, SIE 3, HM+INT 1; 35 C is INT 13; 45 C is HM 14, HM+SIE 2, SIE 1)
  and every condition lies in one stage (stage 1: 25, stage 2: 15). Temperature is almost a function of lab, and the Test B folds are already stratified by temperature, so
  lab/stage cannot be blocking factors without removing the temperature contrast. Ruling: **not** blocking in the primary. Mandatory
  sensitivity rows: (a) bootstrap resampling conditions *within lab strata* (stratum = majority lab) and the post-stratified mean; (b) the
  mean of d per lab and per stage, with n; (c) leave-one-lab-out mean. If the stratified tier is lower than the primary tier the abstract
  must say so (disclosure, not an automatic downgrade). For Test C and S2 the temperature contrast is confounded with lab by design and
  no statistical device removes that; the wording rule is in section 6.

---

## 5. Seeds

- 5 final refits per arm and outer fold (seeds 0-4), as CONTRACT 6. Per-condition score = mean over seeds of the per-seed condition RMSE.
  The seed SD of the cross-condition mean is shown beside every score in tables; it is a reproducibility statement, not a confidence interval.
- Seeds are not units and are not pooled with conditions in any test. Never report the best seed or best fold; the selection rule for the
  comparator is the inner-CV rule of section 3 and nothing else.
- Why 5 suffice: seed noise adds `2 sigma_s^2 / S` to Var(d_c). With a per-seed SD of 5% of E (assumed; no pilot measured it) this is 0.001 E^2
  against `sigma_d^2` of 0.02 E^2 (same-model contrasts): +5% variance, +2.5% on the standard error; 10 seeds would save 1.3%. At 10% seed
  SD it would be +20% variance (+10% SE); still not worth more than 5. Cost of a change to 10 seeds is only the final refits (5 of 65 fits per
  arm and fold), so it can be adopted if the lead prefers, but the ruling does not need it. No post-hoc seed addition is allowed.
- Limitation to state: the tuned configuration comes from one TPE search per outer fold (as P3); search-to-search variation is not in the
  standard errors. A second search seed on the primary contrasts is advisable if compute allows and is an appendix row, not a decision input.

---

## 6. What goes into the abstract

For each primary contrast (n, estimand and tier stated): mean paired difference in pp with the 95% BCa interval (`stats_rule.effect_summary`),
the relative reduction `mean(d)/mean(S_comp)` with its interval from the same resamples, and the tier. Also PINN-KAN's own score as mean
over conditions with the seed SD. Not in the abstract: p-values, rank statistics, results of unadjusted tests, the sensitivity margins.
Wording by tier:
- **S**: "lower by X pp (Y%; 95% CI a to b; n = 40 held-out conditions)". "Outperforms"/"beats" only at tier S.
- **N**: "no more than 10% worse than [comparator] (one-sided lower bound ...)" plus the observed difference with its interval. "Comparable",
  "on par", "equivalent": only after a two-sided TOST at `+-delta_N`; "matches" is not allowed.
- **none**: "could not be distinguished"; give the interval; no direction language.
Scope words: "held-out cycling conditions of one cell type in three laboratories"; "an untested temperature" only if H4 reaches N or S **and**
the sentence carries the lab-confound clause; storage-transfer sentence only if H5 reaches N. A claim on ISU/SNL is "also holds / does not
hold", with its own n; never pooled with Samsung. Relative-reduction intervals use fixed margins from training data; the pp and relative
intervals are not corrected for the training-side margin being an estimate (stated). The judge's refutation sentence ("lower RMSE than every
model") is carried by tier S on H1a, H1b, H1c; N on H1c supports only the tie wording (title 3).

---

## 7. Power and precision (simulation; assumptions, not Samsung numbers)

Code `stats_power_sim.py`; results `power_sim_alpha0.025.json` (family level used here) and `power_sim_alpha0.05.json` (earlier run at 0.05;
same conclusions, MDEs 0.4-1.1 points lower); MDE table `mde_table_alpha0.025.csv`. 2,000 simulations per cell, bootstrap B = 1,000 inside
the simulation (10,000 in the real analysis), the exact decision rule of section 2.3, scale E = 1.

**Assumptions.** (A1) Condition-level paired differences are iid across conditions: `d_c = mu + sigma_d Z + seed noise`. (A2) `sigma_d`
from the correlation `rho` between the two arms' condition errors with SD(error)/E = 0.45 (measured: ISU 0.45, SNL 0.45 on training
sides): `sigma_d = 0.45 sqrt(2(1-rho)) E`, i.e. 0.14 E (`rho` 0.95, variants of one model: H1a, H1b), 0.20 E (0.90), 0.32 E (0.75, different
families: H1c). Measured anchor: ISU power law vs LightGBM have `rho` = 0.75 and SD(d)/E = 0.39 on training sides. The `rho` for PINN-KAN
pairs is **not measured**; it can be estimated from inner-CV condition scores before the freeze as a power report only (no rule changes).
(A3) Shape of Z: standardised ISU (power law - LightGBM) differences (skewness 1.06, excess kurtosis 2.7), plus normal and mirrored
(left-skewed) versions. (A4) Seed noise: per-seed SD 0.05 E, S = 5. (A5) Margins `delta_S` = 0.02 E, `delta_N` = 0.10 E.

**Minimum detectable relative improvement** (80% power, superiority at `delta_S`, skewed shape; power = P(tier S)):

| n (conditions) | arms' error correlation | Holm-3 step 1 (a = 0.025/3) | Holm-4 step 1 (0.025/4) | last step (0.025) |
|---|---|---|---|---|
| 40 (Test B, ISU-like) | 0.95 (H1a, H1b) | **9.8%** | 10.3% | 9.1% |
| 40 | 0.90 | 13.7% | 13.8% | 12.5% |
| 40 | 0.75 (H1c) | **19.4%** | 19.8% | 17.5% |
| 27 (design effect 1.5) | 0.95 / 0.90 / 0.75 | 12.5% / 15.5% / > 20% | 12.8% / 16.2% / > 20% | 10.2% / 13.9% / 19.9% |
| 13 (Test C) | 0.95 / 0.90 / 0.75 | 16.8% / > 20% / > 20% | 17.4% / > 20% / > 20% | 14.3% / 19.0% / > 20% |

In pp: with E = 5 pp, n = 40 detects 0.49 / 0.69 / 0.97 pp at `rho` 0.95 / 0.90 / 0.75; with E = 3 pp, 0.29 / 0.41 / 0.58 pp. Samsung's E is
unknown, so quote the relative figure. Adding H6 to the family (Holm-4 instead of Holm-3) raises the MDE by about 0.1-0.5 relative points.
Power at selected true effects, n = 40, Holm-3 step 1: mu = 0.08: 0.47 / 0.20 / 0.07; 0.10: 0.83 / 0.43 / 0.13; 0.15: 1.00 / 0.94 / 0.47; 0.20:
1.00 / 1.00 / 0.84 (columns `rho` 0.95 / 0.90 / 0.75).

**Non-inferiority power at true equality** (`mu = 0`, `delta_N = 0.10 E`, P(tier S or N)), n = 40: Holm-3 step 1: 0.96 / 0.68 / 0.24; last
step 0.99 / 0.81 / 0.40. n = 27: 0.87 / 0.46 / 0.14. n = 13: 0.40 / 0.16 / 0.05. A tie with the best data-only learner (`rho` ~ 0.75) is
therefore **resolved as N only about a quarter to two fifths of the time** at 10%; with `delta_N = 0.15` the normal-approximation power at
Holm-3 step 1 is about 0.7 (not simulated). That is the price of a tight margin and the lead should know it: the tie outcome of the plan
is likely to read "unresolved" if the data-only learners are a different model family from PINN-KAN.

**Conjunction** (title 1 needs S on H1a, H1b, H1c), n = 40, equal true effect mu in all three, contrasts correlated 0.5, Holm, Wilcoxon only
(BCa omitted, so slightly optimistic): mu = 0.08: 0.45 (`rho` 0.95) / 0.18 (0.90); 0.10: 0.79 / 0.39; 0.15: 1.00 / 0.92.

**Plain reading.** The Samsung test-B design (40 conditions) can show that PINN-KAN beats the lambda = 0 network and the best alternative
stress map if the true gain is about 10% (same-model contrasts); it can show superiority over a different-family data-only learner only if
the true gain is about 19% (roughly 1 pp at E = 5 pp). The P3 pilots found the best data-only learner already at the replicate reference
on ISU (and on SNL by the judge's definition), so a 19% gain over it is unlikely; the plan should expect the N or "unresolved" tier on H1c
and title 3, and Shlok should be told so now rather than after the run. Test C (n = 13) cannot resolve anything below about 17% and is a
descriptive check. The power figures do not include fold-level dependence beyond the n = 27 scenario, and `rho` for PINN-KAN pairs is an
assumption.

---

## 8. Reported limits of this ruling
1. `rho`, seed SD and error shape for PINN-KAN pairs are assumptions; real values come from inner-CV condition scores, usable only for a power
   statement, not for changing rules.
2. The margins 2% and 10% are judgement; they are fixed now so that outcomes cannot move them. The sensitivity rows show the dependence.
3. SNL has 23 conditions, 20 with replicates; claims there are exploratory in strength (MDE > 20% for `rho` 0.75).
4. The `R_WARP` additive/multiplicative choice and the 0.25-4 clip are conventions; both forms are always reported.
5. The simulation uses B = 1,000 and 2,000 draws per cell (Monte Carlo SE of a power value about 0.01).
6. No Samsung number appears; the headroom quantities for Samsung (`E/R_LOO`, `E/R_WARP`) are to be computed on Samsung training sides after
   parsing, as descriptive entries in the PREREG section 11 slot; they decide nothing.

## 9. Edits required in PREREG_DRAFT.md (the experiment-designer applies them; this file does not edit it)
1. Section 9.3 (margin delta): replace by section 2 of this ruling; delete 9.5 (feasibility check) and OPEN-4.
2. Section 9.4: replace the test with the criterion of section 2.3 (Wilcoxon AND BCa bound at the Holm step level); fix the inconsistency
   in the draft ("mean >= delta" plus a bootstrap interval excluding 0): the bound must exceed the margin.
3. Section 9.9 and section 11 (rows 3, 4): H1c is hierarchical (N then S); P3 slot [a] becomes a descriptive entry; row 4 "[a] preregisters
   non-inferiority" is deleted; D007 is superseded by the log row.
4. Section 9.6: H2 order A, C, B with margins `delta_S`/`delta_N`; A gatekept by the family.
5. Section 3 / 9 family: four hypotheses (H1a, H1b, H1c, H6), level 0.025 one-sided; OPEN-5 closed.
6. Section 8: add "condition score = mean over seeds"; one search seed limitation; no best seed.
7. Section 9.10 and section 4: add the lab-stratified bootstrap, the by-lab/by-stage means, the log-ratio row and the two-stage bootstrap.
8. New section: write `margins.json` (E^c, delta_S, delta_N, hash) after tuning and before final refits are applied to test conditions;
   test-fold guard line in every run.
9. Section 6/14: report `E/R_LOO`, `E/R_WARP` in Table 1; rename "replicate floor" to "replicate spread" in all prose.
10. Add the power paragraph (section 7 here) and the abstract wording rules (section 6 here) to the claim contract.

Sign-off: statistician signs PREREG sections 6-9 and 16 **conditional on edits 1-8**. Not signed: the sensitivity of power to `rho` (no data).

## 10. Reproduce
`.venv/Scripts/python.exe -P code/prereg/stats_warp_calibration.py <ROOT>` (training sides, about 5 min);
`... stats_power_sim.py <ROOT> 2000 1000 0.025` (about 10 min, 1 thread); `... stats_mde_table.py <ROOT> 0.025`. Outputs:
`runs/prereg/stats_ruling/{warp_isu_W4,warp_snl_W100,cond_isu_W4,cond_snl_W100,power_sim_alpha0.025,power_sim_alpha0.05,mde_table_*}.*`.
