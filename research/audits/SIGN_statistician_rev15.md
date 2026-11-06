# Statistician signature, PREREG_v4 rev. 15 (commit 86f2170): sections 6, 9, 16 and the simulations of section 21

Date: 2026-11-06. Role: statistician (signature of 17.3). No Samsung data, score or prediction was opened.
Reading: full text of PREREG_v4 sections 6, 9, 16, 17.2 (C2, C10, C23, C24), 17.3, 21, 22 and the 9.x text on item (f); full text of `stats_sim_v4/RESULT_weights.md`, `g_decision.json`; RESULT.md sections 0, 3, 4, 9, 10 (partial: 4.1-4.3, 5.1, 7 by grep and table reading); `fb_tables.csv` (all 600 rows, recomputed); D018 judge (full), D026 judge (full), D028 judge (full), D020 judge (sections 1 and actions, partial); code `graph_test.py` (full), `stats_v4.py` (lines 24-545, 754-785, 845-855; item (f) writer 569-655), `stats_rows.py` (full), `margins.py` (full), `metrics.py` (ensemble functions).
Tests run (CUDA_VISIBLE_DEVICES=""): the four requested files, **74 passed**; `test_pk_d026_item_f.py`, 37 passed.
Independent recomputation: scipy `betabinom` / `binom` (not the project's code), script in the session scratchpad.

## 1. Critical counts: same in text, tables and code

Recomputed with scipy for a = b = (1/0.03 - 1)/2 = 16.1667, n = 40 (design effect 1 + 39 x 0.03 = 2.17).

| Local level | Text (PREREG 9.3 table, line 259-266) | scipy | `graph_test.betabin_crit` | `fb_tables.csv` (rho 0.03, Test B n 40) | Tail P(BB >= k) |
|---|---|---|---|---|---|
| 0.005 | 33 | 33 | 33 | 33 | 0.00249 |
| 0.0055 | 32 | 32 | 32 | 32 | 0.005352 |
| 0.00625 | 32 | 32 | 32 | 32 | 0.005352 |
| 0.00833 | 32 | 32 | 32 | 32 | 0.005352 |
| 0.0125 | 31 | 31 | 31 | 31 | 0.010558 (text 0.0106) |
| 0.0195 | 30 | 30 | 30 | 30 | 0.019356 (text 0.0194) |
| 0.025 | 30 | 30 | 30 | 30 | 0.019356 |

- Plain exact comparators in 9.3 (28 at 0.0125, 27 at 0.025, 29 at 0.00625; 0.0083 / 0.0192 sizes; 0.0003 / 0.0011 under independence): all reproduced (0.00034 and 0.00111).
- w = 0.78: levels 0.025 x 0.78 = 0.0195 and 0.025 x 0.22 = 0.0055, counts 30 and 32 (graph_test.py:74-87; `pinnkan_graph(W_ALT)`; test_fallback_weights_secondary.py:79-84; test_pk_v2_stats.py:66, 107-109). Discreteness argument of D018 section 3 re-derived: P1 drops to 30 at w >= 0.775, K1 stays at 32 up to w <= 0.786, so 0.78 is the only non-dominated alternative.
- NC-2: 30 of 40. `stats_step.py:33` ALPHA = 0.025, `nc2` uses `resolve_config()[0]` (betabin 0.03), crit(40, 0.025) = 30; PREREG lines 48, 269, 321 agree.
- Interval ranks: rank 8, [L(8), L(33)], coverage 0.995010 against target 0.99444 (rank 9 gives 0.98930, fails); rank 11, [L(11), L(30)], coverage 0.961288 = 1 - 2 x 0.019356 (rank 12 gives 0.93349, fails). Code `dep_interval_rank(40, 0.05/9) = (8, 0.99501)`, `(40, 0.05) = (11, 0.96129)`. Plain ranks 11 (0.9978) and 14 (0.9615) also reproduced. PREREG 9.7 (line 295) agrees to the digit.
- Reduced n (9.3 line 271, `fb_tables.csv`): 39: 30/32; 38: 29/31; 37: 28/30; 36: 28/30; 35: 27/29 at 0.0195/0.0055: all correct. All 600 rows of `fb_tables.csv` (tests and interval ranks, Test B 35-40, ISU 58-63, five rho values) match scipy: 0 mismatches.
- Secondary family 33/32/32/31/30 at 0.005/0.00625/0.00833/0.0125/0.025: PREREG 9.5 (line 286) = D018 judge section 2.1 = test_fallback_weights_secondary.py:40 = RESULT 4.4.
- `g_decision.json` against PREREG 9.4 (line 279): w 0.78; dP 0.16485, 0.1599, 0.12235, 0.1181; dK -0.03635, -0.0473, -0.0377, -0.03975; dP + dK all positive; guard max FWER 0.01886 (0.00148 independent), bound 0.0264: text rounds correctly everywhere. RESULT_weights.md sections 1-3 agree with the JSON.
- Section 9.3 simulation figures (0.054 / 0.081 at intra-fold 0.10 with intra-lab 0.05 = RESULT 4.1 ISU-right ratios 4.29 / 3.25; 1.83 / 1.72 = RESULT 4.3; worst ratios 0.88 / 0.79 = RESULT 4.4; FWER 0.0204 / 0.0169 / 0.0200 / 0.0157 / 0.0303 / 0.0877 / 0.0159 = RESULT 7): all found in RESULT.md.

## 2. Verdict per section

### Section 6 (endpoints): SIGNED
- PREREG 6 (line 132): one endpoint (cell RMSE, mean within condition, then over conditions); every primary and secondary contrast is the paired sign test on ln(S_C/S_T). Code: `Store.L` (stats_v4.py:140-143) is `log(b / a)` over conditions scored for both arms; nodes in `primary_nodes` (294-326).
- Ensemble endpoint (line 133, D020 C1): ensemble scores for the P chain, secondary family, ladder, rows, NC; per-seed scores for K1/K2 (`seed_view`, stats_v4.py:109-114; used at 297-298, 316-326 and stats_rows.py:80-83). The claim "RMSE of the mean forecast is at most the mean of the per-seed RMSEs" is correct (convexity of the norm), so the rule cannot disadvantage any arm. Item (f) inner scores are single-fit by design (9.9 (r)); D020 action A2 confirmed. The power paragraph is unchanged in form (the endpoint changes the arms' error and their log-error correlation, and rho 0.6-0.9 is simulated).
- Note (not a defect): the ensemble favours seeded arms (A1, A9, A12) over deterministic ones (A10, A11); the text already prints this parity statement and the one-fit-selection / ensemble-deployment mismatch. Keep both in Methods.

### Section 9 (statistical analysis): NOT SIGNED. Two defects must be fixed in code (or text) before the freeze, then re-checked.

**D1 (HIGH, freeze-blocking): the code defaults disagree with the frozen text, and nothing pins the statistics config.**
- `stats_v4.py:30` `DEFAULT_CONFIG` has `graph_w: 0.5` and `e1_prime_approved: False`. PREREG 9.4 (line 279) freezes w = 0.78 ("no person chooses"); 9.8 rule 4 (line 302) and D019 record clause e1' as approved by Shlok, "in force".
- `test_pk_v2_stats.py:74` asserts the wrong defaults (`c["graph_w"] == 0.5 ... e1_prime_approved is False`), so the test locks the discrepancy in.
- `run_stats_v4` / `run_pinnkan_stats.py` take the config from an optional `--sign-rule` JSON (stats_step.py:561, 573; code/README.md:167 shows `[--sign-rule '{"graph_w": 0.78}']` as optional). Section 18 step 2b pins `g_decision.json` but no code reads it (grep `g_decision|chosen_w` in code: none), and the freeze hashes no statistics config.
- Consequences if the step is run with defaults: P1N tested at 0.0125 (31 of 40) and K1 at 0.0125 instead of 0.0195 (30) and 0.0055 (32); and when "most" fails the code returns clause `e1` (`extent_clause`, stats_v4.py:845-854), the clause that D018 section 4 says would print a false statement. Both change tiers or abstract wording, and both are exactly the analyst degrees of freedom the preregistration closes.
- Fix (either): set `DEFAULT_CONFIG` to `graph_w = gt.W_ALT` (0.78) and `e1_prime_approved = True`, update test line 74, and add a test that `resolve_config()` reproduces the initial levels 0.0195 / 0.0055; or make `run_stats_v4` refuse without an explicit, hashed statistics config equal to these values. Preferred: the first, plus a refusal when `cfg` overrides `sign_rule`, `rho_s0`, `graph_w` or `alpha` after FROZEN exists.

**D2 (MEDIUM): ties with the margin are dropped and n is reduced in code; the frozen text says they are not positive and n is not reduced.**
- Text: 9.3 line 256 "ties and L_c = m are not positive; n is not reduced"; the simulations (RESULT.md:57 and 10.10) and the D018 judge (section 2.1) use the same rule.
- Code: `SignRule.test` (stats_v4.py:72-77) does `L = L[L != margin]` and tests with the reduced n; its docstring cites PREREG 9.3; the test `test_pk_v2_stats.py:80-83` is named "ties ... dropped and n reduced". Demonstration with the project code: 30 positives and 10 exact zeros at margin 0 gives `(30, 30, p = 1.4e-06)` against the frozen rule's `(30, 40, p = 0.0194)`; one tie turns 29 of 40 (fails, 30 needed) into 29 of 39 (passes, 29 needed at 0.025).
- Direction: anti-conservative. Likelihood is low for continuous L (margins ln 1.02 and -ln 1.10), but exact zeros are possible at margin 0 (P3, `most`, NC-2) when two arms share the persistence substitution of 6 (3). The same call is used by the graph nodes, rows (ii)-(iv), `most_test`, and `nc2`.
- Fix: delete the filtering (count `L > margin`, keep n = `L.size`) and rewrite the test to the text; or amend 9.3 and re-simulate (not recommended, since RESULT and D018 follow the text).

**D3 (LOW): Test C and S2 intervals in code differ from 9.7.** PREREG 9.7 (line 295): Test C and S2 use the plain intervals at 1 - 0.05/9 ([L(2), L(12)], [L(4), L(16)]). `stats_rows.descriptive_entries` (line 248) computes `PLAIN.interval(L, 0.05)`, the unadjusted 95 % interval (rank 3 at n = 13). Also `descriptive_entries`, `test_c_in_abstract` and `test_c_sentences` are called only from tests (grep): `run_stats_v4` does not produce the Test C / S2 tables or apply rule 9.8 (3), so a post-freeze ad hoc script would be needed (code cannot be added after the freeze, 17.4). State which interval the Test C sentence prints, make code and 9.7 agree, and wire the three functions into the statistics step.

**D4 (LOW, reporting): the item (f) estimator is not the one that was simulated.** `item_f_from_runs` (stats_v4.py:754-780) defines signs relative to each run's own median (exactly half positive within a run of 8 training conditions at m = 8) and groups by `outerfold:innerfold` (groups of 4, 2 inner folds) and by lab, pooling conditions that recur in four of five training sides. The coverage table of RESULT_weights.md section 5 simulated 5 outer folds of 8 conditions. Median-centring biases a within-run ICC downward and the repeated conditions break the independence behind the F-based upper limit, so the deployed estimator's calibration is unknown and the "exceeds 0.03" flag (it compares the intra-fold ICC, not the average pairwise correlation that rho_s0 bounds, `graph_test.py:287`) fires in 38 % of replicates with no effect (RESULT_weights.md section 5, own caution). No consequence for any tier (9.9 (r)), but the paper must not say the training-side estimate supports rho_s0 = 0.03; it can only state the estimate and that the assumption is unverified. Suggest one sentence to that effect in 9.9 (r).

**D5 (LOW): the noted n_expected default.** `Store.check_complete(n_expected=40)` (stats_v4.py:195) and `run_stats_v4(n_expected=40)` raise on a reduced n; after a blinding exclusion (n 36-39) the caller must pass the actual n or the step stops. Counts at reduced n recompute by rule (verified), so this fails closed, not silently.

Passed in section 9 (checked, no defect): the Beta-binomial pmf and tail table (graph_test.py:168-196) equal scipy; `graph_test` update rule (101-150) is the Bretz et al. weight/edge update with row sums <= 1 and no self-loops enforced; secondary graph structure and reduction to Holm (228-240; hand-worked tests; stated conservative property verified by hand: p_N = 0.001, 0.006 rejects only N1); reverse-S tests at 0.025 outside the graph and at the slot's final level for the secondary family; K1 tier S unadjusted; chain K struck gives P1 at 0.025 and 30 of 40; lab-stratified row weight 1/3 per lab with within-stratum bootstrap and lowest-tier combination (stats_rows.py); rows (ii)-(iv) at the primary final levels; pooled pp margins E, 0.02 E, 0.10 E and sensitivity values (margins.py:99-111); item (f) writer refusal conditions equal D026 (stats_v4.py:588-655; 37 tests pass); lab map weights HM 17 / INT 19 / SIE 4 and the stated pair counts 140 and 313 of 780.

### Section 16 (compute budget): SIGNED
- Arithmetic reproduced: fits per arm and outer fold 3N + 5 (65 at N = 20, 125 at N = 40); 13 arm-units x 1.2 = 15.6 (about 16) and x 4.5 = 58.5 (about 60); core 25 / 85 on 3 single-thread processes gives 8.3 h and 28.3 h; item (f) 1.1 / 4 CPU-h is 4.4 % / 4.7 % of the core (below the 15 % re-open line); P6b 22 / 6 = 3.7 equals the 4.5 / 1.2 ceiling ratio.
- It is arithmetic from V3 and J16, not a measurement; N stays provisional until the FB-8 timing run (the text says so). The 15 % item (f) re-open rule has a numeric trigger. No statistical defect.

### Simulations of section 21: SIGNED (with one wording defect)
- Items (a)-(e), the weight simulation (item g), the A3 tables and the guard: every number quoted in 9.3, 9.4, 9.5, 9.7, 9.11 and section 1 traces to RESULT.md, RESULT_weights.md, `g_decision.json` or `fb_tables.csv` (section 1 above); the counts and ranks were recomputed independently. All of them are labelled "simulation, not a result". Limits that stay disclosed: n = 40 only (reduced n tabulated, not simulated for size); rho_s0 = 0.03 is an assumption (SNL anchor ICC 0.15, range -0.14 to 0.25, cannot discriminate); region R4 is a judgement; R5 (intra-fold 0.20) gives 1.66 / 1.32 times nominal at rho_s0 = 0.03, so the test is not valid there, and the text says "assumption-based".
- **D6 (LOW, stale wording, conservative): the power bullet's headline is for the w = 1/2 count.** Section 1 (line 24) quotes the single-test 80 %-power gain 0.212 / 0.256 / 0.147 and "P1S power 0.05 / 0.28 / 0.71 / 0.96" at "local level 0.0125" (31 of 40). Under the chosen w = 0.78 the P chain tests every node at 30 of 40 (column "0.025" of RESULT 5.1: 0.197 at rho 0.75 ISU-like, 0.234 normal; the chain probability P(P1N, P1S) is 0.816 at a 20 % gain, as the same bullet's next sentence says). "21-25 %" should read about 20-23 % and "P0 likely unless the gain is near 25 %" is stronger than the frozen design implies. The error is in the conservative direction and no tier depends on it, but a claim whose wording exceeds its interval should be fixed: restate the single-test numbers at 30 of 40, or label them "w = 1/2, not used". Decision A5 ("tell Shlok") should quote the corrected number.
- Item (f) is, by design, not simulated or filled before the freeze (D026); signing does not cover its value, which does not exist. The estimator caveat is D4.

## 3. What is not claimed
- A p-value or tier says nothing about novelty or practical importance (the margins ln 1.02 and -ln 1.10 carry the practical part).
- No Samsung number is checked here, because none exists; all figures are simulation outputs.

## 4. Conditions for re-signing
1. D1 and D2 fixed in code with tests that follow the frozen text, committed before FROZEN (verify_freeze needs a clean `code/` tree).
2. D3 aligned or struck by a change-log row; D4, D5, D6 by one sentence each in 9.9 (r), 9.3 and section 1 (text-only, no number changes elsewhere).
3. Re-run the four test files plus `test_pk_d026_item_f.py`; re-check `resolve_config()` outputs (w 0.78, levels 0.0195 / 0.0055, e1' approved, ties not dropped).

Statistician signature: NOT SIGNED (sections 6, 16 and the simulations of section 21 are signed; section 9 is not, because the code defaults contradict the frozen graph weight and clause e1' (D1) and the code drops ties against the frozen rule (D2); fix both and re-check)
