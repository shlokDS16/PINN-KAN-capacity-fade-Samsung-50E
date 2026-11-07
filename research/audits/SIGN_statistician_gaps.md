# Statistician validation of the statistics-gap code G1-G8 (uncommitted diff on 052eefd)

Date: 2026-11-06. Role: statistician (validator; the coder is not me). **Verdict: NOT SIGNED.** Fixes F1-F6 and text T1-T3 below are required. Once they are in, re-signing needs only a check of those items.
I accept the statistics of items 1 and 6 as they stand. Items 2-5 need changes. For item 7, the evidence holds for the code as it is, and has to be re-run after the fixes.

Reading: `research/CONTRACT.md` (full); `code/pinnkan/STATS_GAPS_REPORT.md` (full); `runs/prereg/PREREG_v4.md` sections 9.3, 9.5-9.7, 9.10, 9.11, 10, 11a, 12 (rule 5), 14 and 7.1 "Arms by test" (full text of those passages);
`code/pinnkan/stats_gaps.py` (full); `git diff 052eefd` of `stats_step.py`, `physval.py`, `run.py` (full) and of `emit.py` (partial: `lhs_points`, `_edges_record`, `law_extras` header, `storage_hull`);
`stats_v4.py` (SignRule, Store, check_complete, entry); `stats_step.py` (build_controls, gate_g, run_stats_v4, CLI); `figures/table2.py`, `figures/fig6_storage.py` (the lines that read the gate). `code/figures/ALIGN_V4_REPORT.md` was not opened, because the brief and the coder's report quote its section 3.
I opened no Samsung, ISU or SNL data and no run output. Everything I ran used the coder's synthetic grid or the synthetic G2 run writer, on CPU with one thread.

## Evidence I produced (not taken from the coder)

* **HEAD against the working tree, statistics step.** I exported `git archive 052eefd code` and built the synthetic grid of the coder's test, then ran `run_stats_v4` three ways: HEAD, new code with gaps on, and new code with `gaps=False`.
  Results: `contrasts_v4_B.json` and `controls.json` from HEAD and from `gaps=False` are **byte-identical** to each other. Once the coder's list of new keys is stripped, HEAD and the gaps-on run match exactly in all three files.
  The only differences before stripping are the registered new keys: 3 in contrasts, 8 in controls, 3 in physval.
  One exception to "gaps=False = old path": `physval_11a.json` from `gaps=False` is NOT identical to HEAD. G5 (`physval.figure_inputs`) runs whatever the `gaps` flag says (see F6).
* **HEAD against the working tree, run writer** (the coder's G2 config: A1, A15, G15, 2 seeds). `predictions.csv`, `condition_scores*.json`, `cell_scores.json`, `invariance.json`, `tuning_done.json`, `margins_inputs.json`, `stress_functions.json`, `superposition.csv`, `window.csv`, `reference_values.json`, `diagnostics.json` and `margins.json` are identical, and `metrics.json` matches once the timing fields are removed.
  `extracted_laws.json` differs in one field only, `extraction_audit_sha256`. The cause is line endings in my export (git archive with `core.autocrlf=true` writes CRLF; the bytes match once CR is removed), not code. So the new emitters do not disturb RNG or model state before scoring.
* **Independent recomputation** with scipy `betabinom` (a = b = 16.17), not the project's code. Critical counts at n = 40: 30 at 0.025, 31 at 0.0125, 33 at 0.005, which match 9.3.
  NC-2 on the synthetic grid: n 40, 40 positive, median L 0.232487, interval [L(11), L(30)] (rank 11, the 9.7 fallback), all equal to the code. PC-3 is equal too. The G1 pooled mean (2.064763) and seed SD (independent 0.031937, upper bound 0.07) are equal.
  The scripts are filed in `research/audits/SIGN_statistician_gaps_repro/` (README gives the commands).
* **Defect shown by a run.** `pc3_v4` on a store where R1 scores 39 of the 40 g4 conditions returns `status evaluated, n 39, crit 29, passed True`: n is reduced silently (F2b).
* **Tests** (one process per file, CPU): see section 8.

## Per-item rulings

### 1. NC-2 at g4: ACCEPTED (one optional change)
* Pairing. L_c = ln(S_A1,perm,c / S_A1,real,c), paired by condition at G4 = (32, full), on the ensemble endpoint store (the same scores as the P chain) (stats_gaps.py:141-148).
  The condition sets must be equal (:142-143), and so must the fold sets (:144-146). The negative runs must be `test = B` and `permute_stress` (stats_step.py:560-563), and Design R2 (`Store.from_runs(strict)`). This is section 10's estimand.
* Test. It is `SignRule.test(L, 0.0)` (stats_gaps.py:149 → stats_v4.py:80-84), the same function as the P chain: positives = #{L > 0}, so ties and 0 are not positive, and n = L.size is never reduced.
  The p-value is the Beta-binomial upper tail with rho_s0 from the resolved config (0.03 pinned), with `passed` iff p <= 0.025 (1 + 1e-9). That gives 30 of 40, and at a reduced n the 9.3 rule applies through `rule.crit(n)`.
  The descriptive rows of section 10 are present: L(A9/A1) real and permuted, and the scores of A1, A9, R1, R2 (None where the arm was not fitted).
  The plain exact row carries the independent-conditions label, and the interval is the rank-11 fallback.
* Optional: section 10 fixes NC-2's level at 0.025 whatever the graph alpha is, so fix it in the code. Replace `c["alpha"]` (stats_step.py:564) with a module constant `NC2_ALPHA = 0.025`. The effect is nil while the pinned config holds alpha 0.025, and `effective_config` refuses another after FROZEN.
* The record says "permits" where the prereg says "licenses" (the banned stem). That is acceptable: the Discussion sentence itself is quoted verbatim (stats_gaps.py:31).

### 2. PC-2 and PC-3: the operationalisations are ACCEPTED and must be written into the prereg (T1, T2); two code defects need fixing (F2)
* PC-2: strict increase in T at every SOC inside the storage hull, for every fold x seed member. This is an acceptable reading of "increases monotonically with temperature at every SOC inside the storage hull".
  It is the stricter of the two readings, so a pass is the stronger statement and a fail costs only a Limitations sentence. It changes no tier, and it reports the mean curve and the number of failing members beside the verdict.
  The T grid is the three storage temperatures (emit.py `_cal_members`: Ts = 10, 23, 45; SOC 0-100 in steps of 5).
* PC-3: L = ln(S_R1/S_A1) at g4, margin 0, the 9.3 sign test at 0.025 one-sided (stats_gaps.py:170-180) = the M3 machinery (stats_v4.py:364-367, 411-413) moved to g4. This is correct.
  9.3 "Where it applies" covers it, because PC-3 has a wording consequence (a Limitations sentence). But 9.11 does not list PC-3, so as the text stands it falls under "all other contrasts: none". T2 closes that.
* **F2a (PC-2 must not quietly change rule or sample).**
  (i) stats_gaps.py:208 keeps only the g4 runs that hold `stress_functions.json`, so a missing fold drops out and PC-2 is judged on fewer than 25 members.
  (ii) stats_gaps.py:183-189, 215-216 and 227-228 build the hull from whichever runs have `storage_hull.json`, and with none of them they fall back to the whole SOC grid. That is a different rule, and it can produce a spurious "PC-2 failed".
  Fix (replace stats_gaps.py:208-216):
  ```python
  all32 = _g4_dirs(run_dirs)
  dirs = _g4_dirs(run_dirs, "stress_functions.json")
  if not dirs or len(dirs) != len(all32):
      return dict(status=f"not evaluated: stress_functions.json in {len(dirs)} of {len(all32)} g4 runs", passed=None, gating=False)
  if not all(os.path.exists(os.path.join(d, "storage_hull.json")) for d in dirs):
      return dict(status="not evaluated: storage_hull.json missing in a g4 run (no substitute rule)", passed=None, gating=False)
  ```
  Also: delete the `pts`-empty branch (:227-228), and add `n_folds=len(dirs)` to the returned record.
* **F2b (PC-3 must not reduce n).** `store.L` intersects the condition sets (stats_v4.py:177-185). R1 at g4 is not required by `check_complete` (stats_v4.py:255-259), although 7.1 says R1 runs at all cells with k >= 1. I showed n = 39 / crit 29 above.
  Fix (insert after stats_gaps.py:173):
  ```python
  a1, r1 = store.scores("A1", *G4_), store.scores("R1", *G4_)
  if set(a1) != set(r1):
      return dict(status=f"not evaluated: R1 scores {len(r1)} and A1 {len(a1)} conditions at g4 (n would be reduced)", passed=None, gating=False)
  ```
* Caveat for the Limitations and caption text (not code): PC-2 tests a lab-confounded temperature axis, because 10 C storage is all SIE and 45 C all HM (11a items 1 and 9). A pass is "consistent with Arrhenius-type monotonicity", nothing more.

### 3. Failure handling: the lead is right; the coder's warn-only handling is NOT ACCEPTED for NC-2, PC-2 and PC-3 (F1)
Ruling. NC-2, PC-2 and PC-3 are registered controls (section 10), and their outcome sets manuscript sentences (the NC-2 Discussion sentence; the PC-2/PC-3 Limitations sentences). A warning plus an omitted record makes it possible to drop a registered control without anyone noticing. So:
* **An exception** in G3_nc2 (when negative runs were given), G3_pc2, G3_pc3 or G3_controls (this includes the gate assertion of `extend_controls`) means **refuse in strict mode**.
  `controls.json` is still written first, with the failed control recorded as `{"status": "not evaluated: ERROR ...", "passed": None, "gating": False}`, and so are `STATS_GAPS_ERRORS.json` and the warning. Then `RegisteredControlError` is raised before `contrasts_v4_B.json` is written.
  Re-running the statistics step after a fix is not a re-score (stop rule 6 is untouched). Code changes after FROZEN still need the usual new commit and disclosure.
  In lenient mode: record it, warn, and mark the outcome provisional.
* **Not evaluable for want of inputs** means **provisional**. Cases: no `negative_runs`; PC-3 R1 or A1 missing, or unequal sets (F2b); PC-2 files missing (F2a); no SOC level inside the hull.
  Write `out["status"]["registered_controls_not_evaluated"] = {name: reason}`, then `out["status"]["provisional"] = True` and `out["outcome"]["provisional"] = True`. The provisional flag is a label and changes no tier, state or title. NC-2 is not on the drop list of stop rule 5, so omitting it must stay visible.
* **Descriptive gaps** (G1, G2, G4, G5, G6, G7, G8) may warn and record their status (as now, stats_step.py:541-551, 584).
* `gaps=False` must not switch off G3. Either G3 always runs on the R2 path, or `gaps=False` is refused when `strict` holds.
* Code (stats_step.py). Define `REGISTERED = {"G3_nc2": "NC-2", "G3_pc2": "PC-2", "G3_pc3": "PC-3", "G3_controls": "NC-2/PC-2/PC-3 record"}`.
  At the end of `_stats_gaps_v4` (before :592): form `reg_err = {REGISTERED[k]: v for k, v in errors.items() if k in REGISTERED}` and `reg_missing` (as above). Write the not-evaluated records into the returned controls, set the two provisional flags when `reg_err or reg_missing`, and `return controls_out, reg_err`.
  In `run_stats_v4` (:739-741): `controls, reg_err = _stats_gaps_v4(...)`, write controls.json, then `if reg_err and strict: raise RegisteredControlError(...)`.
  The test `test_nc2_in_the_run_matches_the_hand_computed_test_and_a_wrong_run_is_recorded_not_fatal` must become: strict raises `RegisteredControlError`, controls.json exists and contrasts_v4_B.json does not; lenient is recorded and provisional.

### 4. `--physval` default: must be ON for the R2 confirmatory call (F3)
11a is registered (secondary, descriptive), and Figs. 5 and 6 and the appendix table depend on it. An opt-in flag means the analysis can be run or skipped after the results are seen. That is a selective-reporting opening, even though no tier depends on it.
Fix: `run_stats_v4(..., physval=True, ...)` (stats_step.py:671). On the CLI, the r2 path uses `physval = not a.no_physval`, with a new `--no-physval` refused unless `--lenient`. `--physval` stays for v3_legacy.
`out["physval"]` always carries a status. If it says "not available", PC-2 is also not evaluated, and item 3 then marks the outcome provisional; 11a itself adds no provisional flag.

### 5. PC-2/PC-3 values in controls.json but None in contrasts_v4_B.json: make them consistent (F4)
Two files from one analysis must not give different values for the same key `gate_G.reported_checks`. Today the figures read controls.json (table2.py:46, 84, 91; fig6_storage.py:127), so the split is latent, but any later reader of the contrasts file would get None.
Fix in `run_stats_v4` after `_stats_gaps_v4`:
```python
for k in ("tripped", "reasons", "not_evaluated", "rule"):
    assert controls["gate_G"][k] == out["gate_G"][k]
out["gate_G"] = {**out["gate_G"], "reported_checks": controls["gate_G"]["reported_checks"]}   # a new dict: gate_ (already used by run_v4_full) is not mutated
```
This does not change the gate rule (G = NC-1 + PC-1; `gate_g` stats_step.py:405-425 is untouched). Add the key path to the no-regression strip list.

### 6. G1, G4, G6, G7, G8: ACCEPTED; none can change a count, tier, title or FWER quantity (one text fix, F5)
* Why none can change those: every new quantity is formed after `run_v4_full`, the outcome and the provisional status (stats_step.py:704-737), and is written only under new keys. My HEAD comparison (above) shows every pre-existing key unchanged.
  None of the new records is read by `run_graph`, the outcome table or the sentence assembly. `QT_g1.median_interval` sits inside a gated test's record but is only written, never read.
* **G1.** The pooled mean weights fold means by condition count, which is equal weight per condition (9.1). `seed_sd_pp = sqrt(sum (w_f sd_f)^2)` is the SD of the pooled mean when each fold's seed draw is independent.
  That is the natural model: seed s of fold f and seed s of fold f' are separate fits on different data, so pairing them by label means nothing. The upper bound `sum w_f sd_f` (correlation 1, by Minkowski) is correct and harmless. I recomputed both (above).
  **F5 (text):** `mean_pp` is the ensemble endpoint (run.py:546-553), but `seed_sd_of_mean` is the SD over seeds of the single-seed mean (metrics.py:73-79). So "SD over seeds of the pooled mean" (stats_gaps.py:56, 112-113) mislabels it.
  Replace with: "seed_sd_pp = SD over the seeds of the single-seed pooled mean (`mean_pp_per_seed`), folds independent; the ensemble endpoint `mean_pp` has no seed replicate of its own". Table 1 must then print either `mean_pp_per_seed ± seed_sd_pp`, or `mean_pp` with the SD labelled "seed SD of single-seed fits".
* **G4.** The stability metric is median(SD)/range, with SD = sqrt(mean over seeds of across-fold variance) and the range taken on the fold-and-seed mean surface. This is 11a item 6, read conservatively: seed noise enters "fold-to-fold", and the smaller range gives a larger metric. The definition string states it, and the per-seed metric is written beside it.
  The fixed local LHS (seed 20261106) and the restriction to the intersection of the five training hulls are correct. The bounding-box fallback is recorded.
  "Representative" = the law with the median training-side BIC, with ties broken by fold and seed. That is a training-side rule fixed before any score, so it is not test-selected; with 25 laws it is the exact median. With an even count it is the lower median, and the rule string should say so.
  Showing the edge family names as data inside the printed closed forms is consistent with "printed in closed form" (D022b), as long as the caption says nothing about named forms, and temperature stays masked (verified in the test). That wording belongs to the red team/gate auditor, not to me.
* **G6.** The median of all raw |R| values per bin (no median of medians), each cell once (a repeat raises), and equal members x times per cell. This is correct, and Fig. 7 carries no claim. It must be labelled as a different quantity from the run writer's grid map (the coder says so).
* **G7.** The rank-11 fallback unadjusted 95 % interval (coverage 0.9613 = 1 - 2 x 0.0194) is the interval 9.7 assigns to qualifier and abstract numbers. Q-T exists at g1 only, so the 9-cell Bonferroni does not apply. I confirmed that the G7 median_L equals `mean_vs_median.QT_g1.median_L`. Correct.
* **G8.** It reports all four candidates (A11 and A12 of D\*, A4 and A5 of AG), not the selected one, at g4 with the unadjusted 95 % interval and no p and no tier, so it sits outside every family. That is acceptable; reporting every candidate is the opposite of selection.
  The Table 2 caption must name the cell (g4) and the interval ("unadjusted 95 %"). That keeps it apart from the 9.6 simultaneous intervals of A1 vs D\*/AG. A11, A12, A4 and A5 are not in `check_complete`, so `entry` can intersect: print n per row (`entry` already carries n).

### 7. No-regression evidence: SUFFICIENT for the code as it is now; must be re-run after F1-F5 (F6)
* The in-tree test (gaps on against off) on its own does not prove that the old path equals HEAD. The git-archive comparison does, and I reproduced it independently, adding the run-writer comparison, which the coder did not report. Both pass.
* **F6.**
  (a) Correct STATS_GAPS_REPORT.md: "`gaps=False` is the old path" is false for `physval_11a.json`, because the G5 keys are added whatever the flag says. Either put `figure_inputs` under the flag, or state the exception.
  (b) File the HEAD comparison as a script that can be re-run (mine is in `research/audits/SIGN_statistician_gaps_repro/`; the coder may move it under `code/tests/` or `analysis/`). Re-run it, together with the whole suite, at the candidate frozen commit after F1-F5.
  F1, F3 and F4 deliberately change existing keys: `status.provisional` and `outcome.provisional` when a registered control is not evaluated, `gate_G.reported_checks` in contrasts, and the default physval. Add each to the strip list, with a test that the tiers, states, titles, counts, margins and gate fields still match HEAD.
  (c) The integration grid has 40/40 positives for NC-2 and PC-3. The 29/30 boundary is unit-tested only. Optionally, add an integration case at 30 and at 29 of 40.
* Note outside scope: `extraction_audit_sha256` hashes the file bytes, so it depends on the checkout's line endings (CRLF from `git archive` under `core.autocrlf=true`, against LF in the working tree). The freeze pins hashes, so the gate auditor should check that the pinned value was taken on the tree that runs.

## Text for the lead to add to PREREG_v4 (before FROZEN)

**T1 (section 10, after "PC-2 (reported, not a gate): ... inside the storage hull (also 11a item 3)."):**
"Operational rule: on the five g4 runs (m = 32, k_full), the fitted A1 storage rate is evaluated at SOC 0, 5, ..., 100 % and at the storage temperatures 10, 23 and 45 C.
At every SOC level with at least two of these temperatures inside the convex hull, in (T, SOC), of the training storage conditions pooled over the five outer folds, the rate must increase strictly from each storage temperature to the next, for every fold x seed member.
SOC levels with fewer than two temperatures inside the hull are excluded and listed. The mean curve and the number of failing members are reported beside the verdict. If any g4 run lacks the stress functions or the storage hull, PC-2 is not evaluated (no substitute rule)."

**T2 (section 10, after "PC-3 (reported, not a gate): A1 beats R1 (persistence) at g4 with margin 0."):**
"Operational rule: L_c = ln(S_R1,c / S_A1,c) on the Test B conditions at g4 (ensemble endpoint), tested with the sign test with the fixed design effect of 9.3, one-sided at 0.025 (30 of 40; ties and L_c = 0 are not positive; n is not reduced), outside the graph and with no alpha added.
R1 and A1 must be scored on the same conditions; otherwise PC-3 is not evaluated. A control that cannot be evaluated (NC-2, PC-2, PC-3) is listed and marks the outcome provisional; one that fails to compute stops the statistics step before the contrasts are written."

**T3 (9.3 "Where it applies": after "NC-2 (30 of 40; ...)" insert "PC-3 (30 of 40; section 10)"; and a 9.11 row):**
"| PC-3 | 0.025 one-sided (30 of 40), outside the graph, reported, changes no tier | 10 |" and "| PC-2 | no test (every-member monotonicity rule), reported, changes no tier | 10 |".

## Fix list (all required for SIGNED)
F1 registered-control failure handling (item 3). F2a/F2b PC-2 inputs and PC-3 n (item 2). F3 physval default on (item 4). F4 reported_checks consistent (item 5). F5 G1 SD label (item 6). F6 report correction, filed HEAD comparison, re-run after the fixes (item 7). T1-T3 prereg text (item 2).

## 8. Tests run by me
`test_pk_stats_gaps_g1_g8.py` 30 passed (31.8 s). The related files, run one process each: test_c12_margins 12, test_c26_recheck 30, test_figures_read_only 19, test_n2_n5_wording 16, test_pk_build2_stats 27, test_pk_d026_item_f 37, test_pk_d033_coder 39, test_pk_emit_stats 13, test_pk_negcontrol 34, test_pk_v2_review 17, test_pk_v2_scope 8, test_pk_v2_stats 33: **285 passed, 0 failed** (plus the 30 above). I did not re-run the whole 45-file suite; the coder reports 847 passed.
No ledger rows: this project has no `tools/ledger.py`.

## Re-sign (2026-11-06, scoped to F1-F6 and T1-T3): **SIGNED**

Reading: the current `stats_gaps.py` (`NC2_ALPHA`, `pc2_v4`, `pc3_v4`, `_pool_blocks`/`arm_table` definitions), `stats_step.py` (`RegisteredControlError`, `REGISTERED`, `_stats_gaps_v4`, the tail of `run_stats_v4`, the CLI),
the strip registry in `tests/test_pk_stats_gaps_g1_g8.py`, `tests/head_comparison.py`, and the word-level diff of `runs/prereg/PREREG_v4.md` against 052eefd. Synthetic data only, CPU.

| Fix | Status | Evidence |
|---|---|---|
| F1 | **Fixed** | G3 always runs (`descriptive=gaps` gates only G1, G2, G4, G6, G7, G8; stats_step.py:774). An error gives a `not evaluated: ERROR` record, and strict raises `RegisteredControlError` after controls.json and before contrasts (:779-781). Missing inputs give `status.registered_controls_not_evaluated` plus both provisional flags (:590-596). Tests `test_f1_*` (4). |
| F2a | **Fixed** | `pc2_v4` (stats_gaps.py:213-225): every g4 run must hold stress_functions.json and storage_hull.json, otherwise not evaluated; the whole-grid fallback is removed; `n_folds` is recorded. Tests `test_f2a_*`, `test_f1_pc2_*`. |
| F2b | **Fixed** | `pc3_v4` (stats_gaps.py:176-178): unequal A1/R1 condition sets give not evaluated, so n is not reduced. Test `test_f2b_*`. |
| F3 | **Fixed** | `physval=True` is the default; `physval=False` with strict raises (stats_step.py:717-718); the CLI refuses `--no-physval` without `--lenient` (:682, 689-690). Test `test_f3_*`. |
| F4 | **Fixed** | contrasts `gate_G.reported_checks` = controls' value, as a new dict, and the four gate fields are asserted equal (stats_step.py:775-778). My re-run shows True/True in both files. Gate rule untouched. |
| F5 | **Fixed** | The label reads "SD over the seeds of the single-seed pooled mean (mean_pp_per_seed) ... the ensemble endpoint mean_pp has no seed replicate" (stats_gaps.py:57-58, 114-115). |
| F6 | **Fixed** | `tests/head_comparison.py --base 052eefd`, run by me: contrasts_v4_B.json (131143 characters), controls.json and physval_11a.json are **IDENTICAL** after stripping. The strip list is exact: it recomputes `provisional` from the pre-existing flags and does not drop it (test file :175-180). My own repro on a new grid: the only raw differences from HEAD are the registered new keys plus the intended F4 values. NC-2 and PC-3 recomputed with scipy match again (n 40, crit 30). |
| T1-T3 | **Inserted verbatim** | Word diff of PREREG_v4.md against 052eefd: exactly five insertions (T1 and T2 in section 10, "PC-3 (30 of 40; section 10);" in 9.3, two rows in 9.11). Nothing else changed. |

Tests run by me: `test_pk_stats_gaps_g1_g8.py` **39 passed** (36 s). I did not re-run the 857-test suite; the coder reports it passed, and it must be run again at the candidate frozen commit together with `head_comparison.py` (17.4).
Non-blocking: when a caller passes `gate=` explicitly, contrasts keep that gate record without copying the reported checks (stats_step.py:775). The confirmatory CLI never passes `gate=`, so this affects tests only.


## Row (s): descriptive C-rate ablation (9.9 (s), D041 and its correction), uncommitted on a46d7b8: **NOT SIGNED** (one prereg text fix T4 and one small code fix F-s1; everything else accepted)

Reading: PREREG_v4.md 9.9 (s), the 9.11 table, the section 14 Table 2 row, the rev. 23 status and change-log text (full passages); DECISIONS D041 and its correction; STATS_GAPS_REPORT.md "Row (s)";
the `git diff a46d7b8` of `metrics.py`, `run.py`, `stats_step.py`, `figures/table2.py`; `stats_gaps.crate_row`; the five `crate_ablation/` configs, diffed key by key against the primary g4 and NC-2 configs of each fold.
I opened no Samsung data and no run output. Synthetic data only, CPU.

Evidence I produced:
* **Configs.** In every fold the crate config equals the NC-2 config except for `permute_stress` → `neutralise_stress: [C_ch, C_dch]` and `run_id`. Against the primary g4 config it differs only in `arms` (A1 only), `k` (absent = single window, not grid), the two audit pins and `run_id`. So n_trials, inner folds, TPE seed, seeds, endpoint, tournament and inversion pin are the same.
* **Pairing identity (synthetic R2, run by me).** With neutralisation off, an A1-only single-window run reproduces A1 of a multi-arm k-grid run at k_full exactly: max |difference| = 0.0 over the conditions. With it on, A1 changes (max 0.68 pp).
  The reason: `for_grid(..., "full")` is the base rule with the same `min_fc_points` (data.py:133-134), and at m = 32 tuning uses `for_grid("full")` in both runs (run.py:399). So L_c measures the neutralisation and nothing else in the procedure.
* **Ranks and duality.** I checked them with scipy `betabinom` against `rule.interval` and `rule.crit` for n = 35-40. At n = 40 the interval is [L(11), L(30)] with coverage 0.961288.
  For every n, lower bound > 0 ⇔ #{L_c > 0} >= crit(n, 0.025): 27, 27, 28, 29, 29, 30 for n = 35-40, with tail 0.0146-0.0232.
* **No regression.** `head_comparison.py --base 052eefd`: all three outputs IDENTICAL.
  Against a46d7b8 (exported by me, same grid, same arguments) contrasts, controls and physval are identical once `crate_ablation` and its `G9_crate` status are removed. `head_comparison.py --base a46d7b8` prints DIFFERENT only because its strip list is built for a base without the gap keys.
  `test_pk_crate_ablation.py` 15, `test_pk_stats_gaps_g1_g8.py` 50, `test_c14_confirmatory_configs.py` 10, `test_d028_config_rulings.py` 9: **84 passed**. These include the check that every pre-existing config hash is unchanged against `tests/fixtures/config_hashes_a46d7b8.json`.

| Item | Ruling |
|---|---|
| (1) Estimand, pairing, neutralisation | **Accepted.** L_c = ln(S_A1crate,c / S_A1,c) at G4 on the ensemble endpoint, oriented so that L > 0 means the full model is better (`entry(pair, "A1", "A1_crate")` gives ln(S_comp/S_target), stats_gaps.py:327-328). The pairing checks are those of NC-2: equal condition sets and fold sets (:319-326). The median is taken over the distinct training cycling conditions of the fold, so equal weight per condition (9.1), training side only, one value per fold and component (metrics.py `neutralise_stress`). It is applied after the data build and before any window, tuning or fit, and both training and test cycling cells get it (run.py:366-369). Throughput, times, retention, windows and QC are untouched, and storage cells are unchanged, which is correct because their cycling inputs are structurally 0. The median also enters the inner-CV validation cells. That is one label-free constant per component, not a leak. |
| (2) Interval | **Accepted.** `rule.interval(L, 0.05)` is the 9.7 unadjusted fallback (design-effect rank; [L(11), L(30)] at n = 40, coverage 1 - 2 x 0.0194; at reduced n the fb_tables ranks). One cell means no Bonferroni over 9 cells. The design-effect rank is wider than the plain [L(14), L(27)], so it is the conservative choice. |
| (3) Sentence rule | **The rule itself is accepted; the prereg wording "No test" is not.** By the duality above, "lower bound > 0" is exactly the one-sided 9.3 sign test at 0.025 with margin 0 (30 of 40). The "raised" sentence therefore is an unadjusted one-sided inference at level 0.0194 under the 9.3 assumption, not a purely descriptive statement. It cannot enter any family or the FWER count of 9.11, because no title, state, tier, downgrade or section-11 sentence depends on it: it has the status of NC-2, outside the graph with no alpha added. But 9.11 currently files it under "none; intervals only", which understates it. Fix: **T4**. |
| (4) Own N = 40 search | **The ruling: own search is the fair comparison.** Reusing A1's tuned configuration would hand the ablated model hyperparameters, and a backbone, chosen for inputs it no longer has. That biases L upward, i.e. towards "C-rate contributes". The re-run gives both arms the same budget, space, inner folds, TPE seed and seeds (configs above). The estimand is then "the full training-side pipeline with against without informative C-rate inputs". Tuning-path noise enters L as spread, not as bias, and the interval carries it. The paper should say "A1 re-tuned with the same budget". |
| (5) Not computed / strict | **Accepted.** A pairing or config integrity error raises `NeedsRescoreError`, which gives `not computed ... failed_needs_rescore`, printed by Table 2, with no substitute and no stop. This is right, because the cure would be a second scoring, which the guard refuses. Any other exception is in `REGISTERED` (`G9_crate`), so it stops a strict run. Once FROZEN exists, a missing `crate_runs` stops a strict run (`absent` list, stats_step.py:799), which matches "as for the rows of 9.8 rule 2". `not run` and `not computed` set no provisional flag; that is correct for a row with no outcome consequence. |
| (6) Hashes and outputs | **Accepted.** See the evidence above: the key is absent from DEFAULTS, the 271 + 5 existing hashes are unchanged, the outputs are identical to 052eefd and a46d7b8 apart from the new key, and the run writer is unaffected when the key is absent (run.py:191, 366). |

**T4 (prereg text, required).**
* In 9.9 (s), replace "No test, no p-value, no tier;" with: "No p-value and no tier are printed. The sentence rule is the dual of the sign test with the fixed design effect of 9.3 at margin 0: the lower bound L(11) > 0 holds exactly when at least 30 of 40 L_c are positive (one-sided level 0.0194 at n = 40; at reduced n the counts of `fb_tables.csv`). The first sentence therefore carries an unadjusted one-sided error rate of at most 0.025 under the 9.3 assumption. It is outside every family and the family-wise count of 9.11 because no title, state, tier or downgrade depends on it;"
* In 9.11, remove "C-rate ablation row (s) of 9.9" from the "none; intervals only" row and add the row: "| C-rate ablation row (s) | descriptive row; its sentence rule equals the one-sided 9.3 sign test at 0.025 with margin 0 (30 of 40), unadjusted, outside the graph, no alpha added, changes no tier | 9.9 (s) |".
* Optional, for clarity: in the second sentence, replace "did not raise the median condition error at g4 beyond its interval" with "did not clearly raise the median condition error at g4 (the interval includes a ratio of 1)".

**F-s1 (code, required, small).** The prereg fixes one full sentence with the numbers filled in. `crate_row` emits only a fragment (`CRATE_SENTENCES`, stats_gaps.py:310), which leaves the final wording to hand editing.
Add the two prereg sentences verbatim, as amended by T4 if the optional change is taken, as `CRATE_FULL = {"consistent": "...(median ratio {x:.2f}, interval {a:.2f} to {b:.2f})...", "not consistent": "..."}`. Return `sentence_full=CRATE_FULL[key].format(x=math.exp(e["median_L"]), a=math.exp(e["median_ci"][0]), b=math.exp(e["median_ci"][1]))`, so it passes the existing wording check in `gap()`.
Add one test: at 30 of 40 the "consistent" text contains the exp-transformed interval; at 29 of 40 the other text is used.

Re-sign needs only T4 (grep "dual of the sign test") and F-s1 with its test. Nothing else has to be re-run.


## Row (u) re-sign (relabelled from (s); T4, F-s1 and the red team's batch): **SIGNED**, with two text-only minors (M1, M2) for the lead before FROZEN

Reading: PREREG_v4.md 9.9 (u) and the 9.11 row "C-rate ablation row (u)" (full); `stats_gaps.CRATE_SENTENCES`, `check_crate_runs`, `crate_row`; `pinn._hull_sample`; the `table2.py` lines that print the row; STATS_GAPS_REPORT.md lines 79-82. Synthetic data and design identifiers only, CPU.

| Item | Status | Evidence |
|---|---|---|
| T4 | **Applied** | 9.9 (u) carries "No p-value and no tier are printed. The sentence rule is the dual of the sign test with the fixed design effect of 9.3 at margin 0 ..." verbatim. 9.11 has its own row (`C-rate ablation row (u)`, 0.025 one-sided, 30 of 40, outside the graph). The optional "did not clearly raise ... (the interval includes a ratio of 1 ...)" wording was taken. |
| F-s1 | **Fixed** | `CRATE_SENTENCES` holds the three prereg sentences verbatim (raised / lowered / not clearly raised, each with the laboratory-and-stage caveat). The key is chosen only by the interval: lo > 0 → raised, hi < 0 → lowered, else not clearly raised (stats_gaps.py:357). `sentence_full` is filled with exp(median L) and exp of the bounds to 2 decimals (:358). Table 2 prints `sentence_full` (table2.py:117). Tests at 30 and 29 of 40 and on both tails pass. |
| Third sentence ("lowered") | **Accepted** | upper bound L(30) < 0 ⇔ at least 30 of 40 L_c < 0, the mirrored 9.3 test at the same level. The two tails together make a directional two-sided rule at about 0.039, with each sentence at most 0.025 one-sided. See M1. |
| `check_crate_runs` (red team m-1) | **Accepted** | A run that is not one of the five pinned configurations (canonical hash against MANIFEST, folds 0-4 once) raises, and so stops a strict run. That is stricter than "not computed" and right: the cure is to pass the pinned runs, not to re-score. See M2. |
| `_hull_sample` constant columns | **Accepted** | I checked it against the a46d7b8 function: bit-identical on 30 random non-constant inputs. With constant columns those columns are held exactly and the free columns stay inside the box.
  I also checked whether any registered Samsung fit can hit the new branch. Using design identifiers only (`runs/prereg/subsets.json` order and the `tuning.inner_folds` rule reproduced), there is no constant stress column in any outer training set (folds 0-4 x m 8/16/32) or in any inner training set (inner k 2, 3 and 4; 115 sets). So primary fits are unaffected. |
| No regression | **Holds** | `head_comparison.py --base 052eefd`: all three IDENTICAL. Tests run by me: `test_pk_crate_ablation` 20, `test_pk_stats_gaps_g1_g8` 50, `test_pk_models` 42, `test_pk_build2_stats` 27, `test_figures_read_only` 20, `test_c14_confirmatory_configs` 10: **169 passed**. I did not re-run the 888-test suite. |

**M1 (text only, 9.9 (u)).** After "The first sentence therefore carries an unadjusted one-sided error rate of at most 0.025 under the 9.3 assumption." add: "The second sentence is the dual of the mirrored test (at least 30 of 40 L_c < 0) and carries the same bound in the other direction."
**M2 (text only, 9.9 (u)).** After "a pairing or configuration integrity error is recorded as not computed and printed as such, without a substitute" add: "; a run that is not one of the five pinned configurations stops the step".
These are wording minors in the precedent of rev. 17. Neither changes the code or any number, and the gate auditor can tick them by grep ("mirrored test (at least 30 of 40", "five pinned configurations stops").
