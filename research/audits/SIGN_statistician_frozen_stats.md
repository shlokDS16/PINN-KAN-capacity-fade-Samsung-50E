# Statistician sign-off: frozen confirmatory statistics step (Paper 7, PINN + KAN, Samsung INR21700-50E)

Date: 2026-11-12. Role: statistician (validator; the lead ran the step). HEAD c6a89b6 (FROZEN). Nothing under `code/` or `runs/prereg/` was edited; nothing committed.
Method: every number below was recomputed with my own script from the run files (scratchpad scripts, single thread, `OMP_NUM_THREADS=1`), not read from the stats outputs, then compared with `runs/stats_frozen/analysis/*.json`.
Reading depth: PREREG_v4 sections 9.1-9.9, 9.11, 10, 11 (full), 13; DECISIONS D044a, D045, "Frozen statistics step run", D046 (full); stats_step.py lines 60-140, 370-420, 761-800; stats_v4.py 148-240; stats_gaps.py 40-235 (partial, the functions named).

## Verdict: PASS WITH CONDITIONS

The outcome (state P0, K=, title T5) is reproduced exactly from the run files and follows from the closed table. No blocking issue. Conditions are disclosures and wording limits (section 6); none changes a tier, state, title or count.

## 1. Primary tests P1 and P2 (g1 = (m 8, k 2)): PASS (exact match)

Recompute: per-condition scores from `runs/conf_samsung_B_f{0-4}_m8/condition_scores_k2.json` (the k = 2 cell; the primary k label is "full", so k = 2 lives in the `_k2` file, see stats_v4.py:200-203). D* per fold from `comparators.json` (g1: fold 0 = A9, folds 1-4 = A12). n = 40 conditions (8 per fold), 40 distinct. L_c = ln(S_comparator / S_A1) (stats_step.py:~108), positive = L > margin (strict), n not reduced.

Beta-binomial null, rho_s0 = 0.03, a = b = (1/0.03 - 1)/2 = 16.167: critical counts recomputed 30 at level 0.0195 and 0.025, 32 at 0.0055 (as in 9.3 table).

| Node | margin | positives (mine = file) | p design-effect (mine = file) | needed | rejected |
|---|---|---|---|---|---|
| P1N (A1 vs D*) | -ln 1.10 | 22 | 0.376519 | 30 at 0.0195 | no |
| P1S | ln 1.02 | 19 | 0.623481 | (level 0, never reached) | no |
| P1-rev (D* better by S margin) | ln 1.02 on -L | 20 | 0.541732 | 30 at 0.025 | no |
| P2 (A1 vs A9) | ln 1.02 | 18 | 0.700282 | (level 0) | no |
| P3 (g1 vs (32,2), D_c) | 0 | 20 | 0.541732 | (level 0) | no |

Medians: L_D* = -0.02326, L_A9 = -0.10197 (both negative: the comparator is at least as good as A1 in the median). Mean paired difference (D* - A1) at g1 = +0.1359 pp (A1 better in the mean). Worst-condition error: A1 2.092 pp, D* 3.894 pp, A9 4.292 pp (all match `mean_vs_median`).
Tiers: P1 = "none" (not N: 22 < 30; not reverse S: 20 < 30), P2 = false, P3 = false. These equal `primary.tiers` in `contrasts_v4_B.json`. No node was rejected, so the graph never moved.
R1 at g1 (M3 input): 40 of 40 positive, p 8.8e-08 (file 8.84e-08), so "A1 better than R1" = true and M3 = false.
Abstract interval: rank-11 interval [L(11), L(30)] = [-0.3242, 0.3991]; X = 100(1 - exp(-L)) gives [-38.29, 32.91], printed [-38.3, 32.9]. Median X = -2.35. Matches. All four downgrade rows give P1 none / P2 false / R1 true (`downgrade.rows`), so the effective tier equals the primary, number source = primary (rule 9.8.6 tie goes to primary).
K chain (also checked, scored on per-seed tables as the registered D020 rule says; `condition_scores_seed.json`): K1 20 of 40 at -ln 1.10 (needs 32 at level 0.0055), K2N 29 (needs 30; also K2N has level 0 because K1 not rejected), K2S 19, K2-rev 16. All equal the file. So K1 = false, K2 = none.

## 2. Outcome row: PASS

Section 11 (4.1 States, 4.2 table): "P0: P1 reaches tier N or none, and not reverse S"; "K=: every other case (K1 passes and K2 is N or none; or K1 fails without K2 reverse)". K1 fails and K2-rev is not reached (16 of 40 < 30), so K=. Row **P0 / K= -> T5**: "Physics-informed and data-driven forecasts of lithium-ion capacity fade against the number of cycling tests and check-ups: learning curves with Kolmogorov-Arnold stress functions" (identical to `outcome.title`). M1 requires Q-H reverse S at g1 (file: Q-H g1 tier none, median L +0.299); M2 and M3 require P+ (P1 is none). Abstract sentence, quoted from the table: lead-in "With eight cycling conditions and two check-ups per held-out cell," + P0 part with tier none ("could not be distinguished from" that of the best tuned data-driven learner, 95 % interval; n = 40) + the K= clause for K1 fail ("was not shown to stay within 10 % of the full network, so no closed-form-law claim is made"). `outcome.abstract_sentence` is that text with interval [-38.3, 32.9]. `extent_clause` None is correct (e1/e1'/e2/e3 belong to P+). Gate G not tripped (NC-1 15 runs, max abs diff 0; PC-1 below). Status: strict, frozen, provisional false, rows_not_run [], gate_not_evaluated [].

## 3. NC-2 and PC-3: PASS (recomputed)

NC-2: A1 real `conf_samsung_B_f{0-4}_m32/condition_scores.json` vs permuted `..._m32_nc2/condition_scores.json` (A1 only, 8 conditions per fold, same condition sets), L = ln(S_perm / S_real). Positives **28 of 40**, p (design effect) **0.053918** against needed 30 at 0.025: fail. Median L = +0.4721 (permuted 60.3 % worse in the median), interval [L(11), L(30)] = [-0.0472, 1.1147] (includes 0). Max |L_mine - L_file| = 0.0. The plain independent-conditions row would pass (plain p 0.0083): the fail is produced by the design effect, not by the data alone.
PC-3: ln(S_R1 / S_A1) at g4: **39 of 40**, p 1.12e-06, median 1.9018, interval [1.3308, 2.2406]. Equal to `controls.json`. Passed (reported check, outside the family).
PC-2 (not requested, read only): evaluated, 25 members, 0 failing; SOC 0 excluded outside hull.

## 4. PC-1: PASS

`runs/pc1_g0_synth/summary.json`: 20 of 20 G0 draws, unique ids. Recomputed medians of nRMSE: A1 0.10003, A2 0.04661, A4 0.10216 (the three equal `pc1_summary.json`, as do q25, q75, max and counts <= 0.15: A1 19/20, A2 20/20, A4 18/20). stats_step.py:~393: `P1_G0_nrmse_leq_0p15 = all(median over G0 draws <= 0.15 for A1, A2)`; A4 is not read by the gate (D045 C1 printed it beside). PC-1 passes under the median reading (D045 C2). Note `P1_full` / `P1_passed` are null by design (no learners in the G0 run; the "beat A11/A12" part was struck, RT F11).

## 5. D046 arm table: PASS

The copy `pool_blocks_tolerant` in `runs/stats_frozen/post_arm_table.py` equals `stats_gaps._pool_blocks` (stats_gaps.py:70-92) for mean_pp, mean_pp_per_seed, seed_sd_pp, seed_sd_pp_upper_bound, n_conditions, n_folds and the weights; n_params, n_train_used, fit_seconds are now `None` if any fold value is None instead of raising, otherwise the same mean and [min, max]. One additional detail, equivalent in spirit: `fit_seconds_ensemble` tests `x.get(...) is not None` where the original tested key presence (a key present with value None gave an error before, now gives None). The monkeypatch `sg._pool_blocks = ...` works because `arm_table` resolves the name at call time. None-valued fields in the output are only R1 and R2 `n_train_used` (arms with no fit).
Spot check at cell 8|2 (weights = condition counts, 8 per fold) against `metrics.json` `outer_test_by_k["2"][arm].primary_pp` of `conf_samsung_B_f0..4_m8`: A1 0.78955 (table 0.78955), A9 1.02001 (1.02001), R1 3.38967 (3.38967), A12 0.91789 (0.91789), A10 1.20605 (1.20605); n = 40 each. A1's mean of `condition_scores_k2` = 0.78955 too. The table carries `post_freeze_note`. The table is descriptive (G1) and sets no tier, state, count or gate input.

## 6. Disclosures and qualifiers the paper must carry

Required by the preregistration or by what the numbers show:
1. **Item (f) (9.9 (r)).** `item_f.exceeds_rho_s0` true because the intra-fold point estimate rho_fold = 0.0968 > 0.03 (graph_test.py:287; the prereg trigger is the intra-fold point estimate). The fixed Limitations sentence is required verbatim: "The training-side estimate of the sign correlation exceeded the value assumed by the test; the confirmatory tiers rest on that assumption." Print with it, from the same file: rho_fold 0.097 (upper 0.436), rho_lab -0.040 (upper 0.504), implied average pairwise sign correlation 0.0074 (upper 0.267), contrast P1 at g1 only, n = 40. The prereg says the estimate is descriptive, its flag fires in 38 % of replicates with no effect, and the paper must never say it supports the assumption. Honest consequence to state: the design-effect test is anti-conservative if the true dependence is above 0.03, which could only produce false rejections; the confirmatory outcome has no rejection among the graph nodes, so the exceedance cannot have created a tier. The two rejected tests outside the graph (R1 g1 40/40; PC-3 39/40) pass at every assumed correlation on the 9.9 (q) grid up to 0.05 (`dependence_sensitivity`: R1_g1 true at all five values) and the plain count. K1, K2, P3 have no dependence estimate (9.9 (r)).
2. **Mean-versus-median rule (9.8 rule 1), triggered for P1, P2 and K2** (`mean_vs_median.triggered`). The abstract must add the three sentences in `abstract_additions` (they are not inside `outcome.abstract_sentence`): P1 mean +0.14 pp [-0.04, 0.44] with median L -0.023, worst-condition 2.09 pp (A1) vs 3.89 pp; P2 mean +0.23 pp [-0.01, 0.59], median L -0.102, worst 2.09 vs 4.29 pp; K2 mean -0.06 pp [-0.20, 0.03], median L +0.011, worst 5.80 (A15) vs 4.48 pp. I recomputed the worst-condition values and the P1 mean.
3. **Wording limit on "none".** P1 "none" means P1N failed (22 of 40, needs 30); the interval [-38.3 %, +32.9 %] is wide. Only the fixed wording "could not be distinguished" is allowed; the paper must not say equivalent, matched or comparable. P2 is not "no effect of physics": median L_A9/A1 = -0.102 (A9, no physics law, lower median error at 18 of 40 positive), the claim is only "a gain attributable to the physics law was not shown" (e3 is not in the T5 sentence, and no extent clause is printed).
4. **Rule name.** Every sign test is "a sign test with a fixed design effect (assumed average pairwise sign correlation at most 0.03)", assumption-based, never "exact" or "distribution-free". Plain independent-conditions rows go beside each contrast (descriptive). Examples where the plain row differs: NC-2 28/40 (plain p 0.0083 vs design-effect 0.054), K2N 29/40 (plain p 0.0032, level 0 anyway since K1 fails). Print both.
5. **NC-2 failed.** The Discussion sentence "the accuracy of the learned law depends on the stress dependence it learns" is removed; state that stress dependence was not shown necessary for accuracy at g4 (median L +0.47, interval [-0.047, 1.11]), a partial control (10, D033 F8), not evidence of absence.
6. **D* membership.** 9.8 rule 4 requires listing the outer folds where D* = A9: g1: fold 0 (A9; folds 1-4 A12). g4 (m 32): folds 0-4 = A12, A11, A11, A12, A11, so none. In fold 0 P1 and P2 are one contrast on 8 of the 40 conditions.
7. **PC-1 reading.** Late run (after Samsung scoring, before any score read; D045 C3), the threshold applied to the median over 20 draws (C2); report per-draw counts: A1 19/20 (max 0.22), A2 20/20, A4 18/20 (max 0.166). A4's median 0.102 printed beside it (C1). G0 shares choices (a), (b) with the fitted law: a pipeline check only (printed circularity sentence).
8. **Post-freeze steps.** D044a re-pin: the 10 retain-every-check-up runs ran at the amended code (fdb7f44 lineage, FROZEN predecessor ce0cc0d; 266 other runs at ce0cc0d), three blocked folders archived (`_blocked_d044`); D046 arm table recomputed post-freeze with a None-tolerant copy (display item only). State both in the appendix.
9. **Endpoint kinds.** K1 and K2 use the per-seed rule; P chain, secondary, NC-2, PC-3 use the five-seed ensemble (ENDPOINT_NOTE, D020 C1 item 4). State it in Methods.
10. **Scope.** n = 40 Test B conditions, labs HM 17 / INT 19 / SIE 4, five outer folds, one dataset; estimand is the median condition log ratio; all non-graph results are descriptive or exploratory; the dependence sentence of 9.9 (q) is empty because no tier holds (`sentences: {}`), so nothing to print there. A p-value says nothing about practical importance; the R1 result (A1 about 4.6 times lower median error than carrying the last check-up forward at g1, exp(1.535)) is the only positive finding and rests on an easy persistence baseline.
11. **Not recomputed by me:** Test C, S2, the downgrade-row internals (only their printed tiers were read; all equal the primary), Q-H, Q-A10, Q-T intervals, C-rate row (u), 11a items. The outcome does not depend on them (P state, K state and M1-M3 are decided above; M1 would need Q-H reverse S, whose median L is +0.299 in the file).

## 7. Statistics-wording checks

- No claim exceeds its interval in the T5 sentence: both P1 and K statements are non-rejections.
- Multiplicity: one graph at FWER 0.025 (nodes P1N, P1S, P2, P3, K1, K2N, K2S, none rejected); R1, NC-2, PC-3, most-test are outside the family and labelled.
- Effect sizes and exact n are in the outputs; paired by condition, five seeds (ensemble or per-seed as above).
- Ledger rows: none added (the brief asked for the report only).
