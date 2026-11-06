# Coder D034 report (2026-11-06)

Scope: step 1 of `research/HANDOFF_2026-11-06.md`; texts from `debates/D033_signoff/01_judge.md` (AUTHOR DECISIONS AD1-AD6), DECISIONS D034, D035; PREREG_v4 rev. 16 (9a05417) read only at 9.8 rules 2, 5, 6 and section 11 titles. CPU only; no Samsung value opened. Suite: 42 test files, one pytest process per file, **796 tests pass** (781 before; 15 new in `test_pk_d034_coder.py`).

## What was built

| Item | Where | Behaviour |
|---|---|---|
| AD1 P3 = L(g1) - L(32, 2) | `stats_v4.py`: `G32K2`, `p3_contrast`, `primary_nodes`; `stats_rows.py`: `row_tiers`, `lab_stratified_tiers` | One function builds D_c for the primary analysis and for every row. g4 no longer enters P3 (it stays an estimated cell and the K-chain cell). A store without the (32, 2) cell has no P3 node (p = 1); a row run without it does not cover P3 (no key, never silently passed). `k_full = 2` merges (32, 2) into (32, full) as before. |
| AD2 modifier M3 | `stats_v4.py`: node `R1g1` (outside `gt.NODES`), tier `R1_g1` (True = A1 shown better than R1), `assemble_outcome`, `_sentence`, `M3_SENTENCE`, `R1MissingError`, `primary_numbers` (`interval_R1`); `stats_rows.py`: `row_tiers` and `lab_stratified_tiers` compute `R1_g1` | L = ln(S_R1 / S_A1) at g1, margin 0, one-sided 0.025, 30 of 40 under the pinned rule (ties not positive, n not reduced). M3 = P+ and not `R1_g1`. M3 gives the K column's T4/T5/T6 (also instead of T9a/T9b; M1's title edit then does not apply) and the P+ sentence, then the M2 tail if M2 holds, then "; the physics-informed network was not shown more accurate than carrying the last check-up forward (95 % interval [a, b])". Rows only lower it (boolean AND, as for P2). The bracket comes from the analysis that set the tier (D033 F2 rule, `number_sources` picks `R1_g1` up automatically); a printed interval whose lower end is above zero raises `BracketSignError`. A P+ outcome with no R1 at g1 raises `R1MissingError` (fail closed). `Store.check_complete` now requires R1 at g1. `dependence_sensitivity` prints no D018 sentence for `R1_g1`. |
| AD4 | `T9A_NOP3`, `T9B_NOP3`; `assemble_outcome` | T9a/T9b read "Physics priors pay with few cycling tests: ..." unless P3 is S, then "... pay when cycling tests are few: ...". Same ids T9a/T9b. |
| AD5 | `TITLES` T1, T4, T7; `KCLAUSE_KEQ_FAIL` | "readable" -> "closed-form"; "no readable-law claim" -> "no closed-form-law claim". |
| AD6 | none | A9 stays in D*. |
| D035 | `code/prereg/make_confirmatory_configs.py` `N_TRIALS = 40`; all 277 files regenerated (`runs/prereg/confirmatory_configs/**`, MANIFEST with `n_trials` 40, `runs/item_f/configs/*.json`); `--check` exits 0 | Item (f) configs inherit 40 from the g1 config. `run.DEFAULTS["n_trials"]` (20) and `tuning.choose_budget` (the superseded "40 if every fit < 20 s" branch) are not touched: confirmatory configs carry `n_trials` explicitly and `auto_budget` is false. |
| Lead's addition (rev. 16, 9.8 rule 2) | same generator: `ROW_K`, `ROW_ARMS["g1"]` + R1, `RANDSUB_ARMS` + R1 | Rows (ii) and (iii) at m = 32 now score k in {2, full} (so the (32, 2) cell exists for P3 under each row; compute for those 20 row runs rises); rows (ii)-(iv) at g1 include R1 (no fit, no cost) so M3 can be recomputed. Counts unchanged (primary 26, rows 36, sensitivity 195, exploratory 4, replication 10, item (f) 5). Sensitivity configs keep k = ["full"] at g4. |

## Tests

* `code/tests/test_pk_d034_coder.py` (new, 15): P3 contrast value and cell (g4 changes nothing; (32, 2) changes it; missing cell; `k_full = 2`), P3 under row_tiers and the lab-stratified row; M3 count boundary 29/30 of 40, ties, outside the graph, graph untouched; title swap to T4/T5/T6 for each K state; interval content; M3 absent outside P+; `R1MissingError`; **all 3 x 3 x 2 x 2 x 2 x 2 x 2 = 288 state combinations** (P, K, M1, M2, P3, P2, R1_g1) map deterministically to exactly one title, with the modifiers acting as ruled; M2 + M3 order and M1 not editing the K-column title; row_tiers/lab-stratified/lab-indicator sources and `BracketSignError`; a case where only the lab-stratified row lowers M3; AD4 and AD5 strings.
* `test_pk_v2_stats.py`: `make_store` gains the (32, 2) cell (`P1g32k2`), R1 at g1 (`R1g1`) and keeps g4 (`P1g4`); title test follows the D030 pattern: the amendment phrases are asserted to be in the D033 judge file, every other word of an amended title against D016 (T5/T6 against D029/D030) after undoing the amendments; the PREREG section 11 test accepts rev. 15 wording or, once the amended strings are present (rev. 16 now), requires all of them plus the "when ... in place of with ... if P3 is S" statement.
* `test_pk_v2_rows.py`, `test_pk_v2_review.py` (R1 in the grid fixture), `test_c14_confirmatory_configs.py` (n_trials 40; R1 in the g1 row arms; rows at g4 score ["2", "full"]; randsub arms with R1).

## Open points for the lead

1. **M3 and M2 together:** the abstract keeps the M2 tail (the semi-empirical model more accurate still) and then adds the M3 clause. PREREG 9.8 rule 5 (rev. 16) says the same; the judge text only says "adds". Title is T4/T5/T6 in that case.
2. **Section 11 vs. T9 ids:** both T9 wordings share the ids T9a/T9b; the outcome dict does not carry a separate flag (the title string differs). Add one if the paper pipeline needs it.
3. **Row (iv) and P3:** row (iv) is g1 only, so it covers P1, P2, "most" and `R1_g1`, not P3 (unchanged from before).
4. **FB-8 cost:** the row runs at m = 32 now fit both k = 2 and k = full for 9 arms, 20 runs (rows ii and iii, 5 folds x ... at g4); include in the timing estimate.
5. **Not done (not asked):** `tuning.choose_budget` still has its N = 40 / 20 / 10 branches (only reachable with `auto_budget`); the FB-8 Partial plan N = 10 is a generator constant (`N_TRIALS`) to edit and regenerate.
6. `mean_vs_median` (9.8 rule 1) does not list M3's contrast; no rule asks for it.
