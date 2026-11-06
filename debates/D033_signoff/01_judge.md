# D033 judge: sign-off findings on PREREG_v4 rev. 15

Read: both rev. 15 signatures, Codex turn 11, PREREG sections 1, 2, 4.1, 9-11, DECISIONS D016-D032, the cited code lines. No Samsung data, no fits. Classes: (i) code, (ii) designer text (section 11 and gated decisions untouched), (iii) author.

## Rulings

| ID | Real? | Class | Ruling |
|---|---|---|---|
| F1 = D1 | yes, FATAL | i | Defaults are w 0.5, e1' off (`stats_v4.py:30`); the test locks them in (`test_pk_v2_stats.py:74`); nothing is pinned. |
| F2 | yes | i + ii | The brackets need a source rule; P- set by a row prints a negative X. |
| F3 | yes | iii | P3 changes m and k (and the capped cells) together; (32, 2) is already a grid cell (4.1). |
| F4 | yes | iii | No gated g1 check against persistence; R1 runs at every cell (7.1). |
| F5 | partly | iii | (a) T1-T3 with e3: tension, not falsehood. (b) T9 "when ... few" implies P3. (c) "readable" has only the closed form behind it. (d) D\* = A9: meaning sound (the advantage is then wholly the law's), size unaffected (graph valid under any dependence); power assumed distinct arms. |
| F6 | yes | i | `max` drops a non-first NaN. `compare_runs` fails closed but is untested. |
| F7 | yes | i + ii | Coverage text overstates (tuning check: synthetic, one fold, m 8/32). |
| F8 | partly | i + ii | `metrics.py:190` also swaps throughput; "cannot fail" too strong. |
| D2 = M2 | yes | i | Ties dropped, n reduced (`stats_v4.py:75`); anti-conservative. |
| D3 | yes | i + ii | Intervals differ from 9.7; functions not wired in. |
| D4, M5 | yes, bounded | ii | |
| D5 | yes, fails closed | i | |
| D6, M1 | yes, conservative | ii | Stale w = 1/2 power; K1 0.96 is the plain figure. |
| M3 | yes | i + ii | The P-/K= joiner deviates; the M1 no-op on T9 is in the table itself. |
| M4, M6 | yes | ii | Methods disclosure; the lead-in stays. |
| M7 | noted | none | Title scope was ruled in D029/D030; "few" names cell g1. |

## Coder action list (one batch, before FROZEN)

1. **F1:** in `stats_v4.py:30`, set `graph_w = gt.W_ALT` and `e1_prime_approved = True`. Pin a new `runs/prereg/stats_config.json` (betabin, rho_s0 0.03, w 0.78, alpha 0.025, e1' true, k_chain_struck false, sensitivity_rhos) in `guard.PIN_FILES` (`guard.py:25`). `run_stats_v4` (`stats_step.py:581`) refuses, once FROZEN exists, any `cfg` or `--sign-rule` (`:561`, `:573`) that differs. `contrasts_v4_B.json` records the config and its hash. Update README:167. Append a note to `build_v2/RESULT.md`. Tests:
   - rewrite `test_pk_v2_stats.py:69-77`;
   - levels 0.0195 / 0.0055 and counts 30 / 32 from `resolve_config()` and from `run_v4(cfg=None)`;
   - P2 S, P3 S and "most" false give e1';
   - an override after FROZEN is refused.
2. **D2:** in `stats_v4.py:72-77`, count `L > margin` with n = `L.size`; rewrite `test_pk_v2_stats.py:80-83` (30 positives and 10 zeros give (30, 40)).
3. **F2:** `primary_numbers` (`stats_v4.py:937`) fills each bracket from the analysis that set that contrast's effective tier: the primary analysis if it is lowest, else the first such row (i)-(iv).
   - Row (i): the weighted median with a two-sided 95 % within-stratum bootstrap interval.
   - Rows (ii)-(iv): their own median and rank-11 interval.
   - Raise if the printed sign contradicts the state.
   - Tests: the red team's probe gives a positive X; K- via a row; P0 via a row.
4. **F6:** in `negcontrol.py:76-79` and `:85`, fail on any non-finite prediction or diff. Tests: NaN at the first, middle and last cell; inf; NaN in both runs; `compare_runs`.
5. **F7:** run `nc1_full` (`run.py:297`) at m 8/16/32 with at least two short-record synthetic cells. Unit test: scramble post-window labels **before** `build_data` (keep lists, anchoring, cap, `lab_map`) and require byte-identical training data and windows; if that cannot be done, report it.
6. **F8:** in `metrics.py:188-191`, permute only the stress vector; keep each cell's own efc, times, retention and window. Test equality of those and a derangement within train and within test.
7. **D3:** `descriptive_entries` (`stats_rows.py:248`) adds the 1 - 0.05/9 plain interval; wire it, `test_c_in_abstract` and `test_c_sentences` into `run_stats_v4`.
8. **D5:** derive `n_expected` from the pinned `blinding_exclusions.json`; add a test at 39.
9. **M3:** `stats_v4.py:899` uses "whereas" for P-/K+ only.

Then re-run the four statistics test files, `test_pk_negcontrol.py` and `test_pk_d026_item_f.py`, and run FB-9 at the candidate frozen commit.

## Designer items (rev. 16)

- **F2:** a reading note outside the block giving item 3's source rule.
- **F7:** rewrite 10 "Grid coverage" to the true split: the predict check covers every (m, k) set, arm and seed; `nc1_full` covers tuning, selection, margins and D\*/AG.
- **F8:** in 10 NC-2, "(with design throughput)" becomes "(each cell keeps its own throughput and window)"; add that NC-2 is a partial control for E1.
- **F5(d):** report the folds with D\* = A9; on those folds P1 and P2 share a contrast and "most" holds by construction; power assumed distinct arms.
- **D3:** 9.7: the Test C abstract prints the plain 95 % interval; the tables print both.
- **D4:** 9.9 (r): the estimate is descriptive and does not support rho_s0.
- **M5:** 9.9 (r): the estimate covers P1 at g1 only, the concordance trigger changes no tier, and the upper-bound formula is written out.
- **D6, M1:** restate section 1's power at 30 of 40 (RES 5.1, column 0.025) and K1 at 0.734 / 0.343. The lead tells Shlok.
- **M3:** note that M1 has no effect on T9a/T9b.
- **M4:** Methods lists the D032 capped cells and the two unscored cells.
- **M6:** Methods defines X as the transformed median of log ratios, and D\* as the inner-CV winner per (fold, m).

## AUTHOR DECISIONS (Shlok)

**AD1 (F3).**
- Opt 1: "D_c = L_c(g1) - L_c(g4)" becomes "D_c = L_c(g1) - L_c(32, 2)" (sections 2 and 9.4). The clauses become literally true, with the same window, forecast set and caps at both cells and no extra compute. P3 power must be re-simulated; g4 stays estimated.
- Opt 2: keep the contrast. e1/e1' "larger with 8 than with 32 cycling conditions" becomes "larger with 8 cycling conditions and two check-ups than with 32 and all check-ups"; e2 "on the number of cycling conditions" becomes "on the amount of training data (8 conditions with two check-ups against 32 with all)". Power unchanged; m is not isolated.
- **Recommendation: Opt 1.**

**AD2 (F4).**
- Opt 1: modifier M3 = P+ and A1 not better than R1 at g1 (margin 0, 30 of 40 at 0.025, outside the graph; no alpha added, since both tests must pass). T1-T3 and T9a/T9b then become the K column's T4/T5/T6, and the sentence adds "; the physics-informed network was not shown more accurate than carrying the last check-up forward (interval)". It lowers P(P+ title) by an amount no file holds.
- Opt 2: titles unchanged; the abstract always carries the 4.3 qualifier for A1 against persistence at g1.
- Opt 3: keep as approved; PC-3 is also reported at g1, with a Limitations sentence if it fails.
- **Recommendation: Opt 1.**

**AD3 (F5(a)).**
- Opt 1: keep. The title names the network; e3 carries the attribution.
- Opt 2: under e3, use T4-T6. This costs most P+ titles (P(also P2) is 0.02 at a 5 % gain).
- **Recommendation: Opt 1.**

**AD4 (F5(b)).**
- Opt 1: "when cycling tests are few" becomes "with few cycling tests" unless P3 is S.
- Opt 2: always "with".
- Opt 3: keep.
- No power effect. **Recommendation: Opt 1.**

**AD5 (F5(c)).**
- Opt 1: "readable" becomes "closed-form" in T1, T4 and T7, and "no readable-law claim" becomes "no closed-form-law claim". This matches the approved clauses, at no cost.
- Opt 2: "readable" only above a stability threshold set before the freeze (a new descriptive gate).
- Opt 3: keep.
- **Recommendation: Opt 1.**

**AD6 (F5(d)).**
- Opt 1: keep A9 in D\*, with the disclosure.
- Opt 2: drop A9 from D\*, which lowers P1's bar.
- **Recommendation: Opt 1.**

If an item is unanswered, the approved text stands, and the red team signs only after the acceptance is recorded. AD1 and AD2 block the signature.

## Re-sign plan

1. The coder batch and Shlok's answers run in parallel.
2. The designer writes rev. 16, with one decision row per answer (D034 onward).
3. The statistician simulates P3 power at (32, 2) and the skill test's size if AD1 or AD2 is Opt 1.
4. The statistician re-signs section 9. The red team re-checks F1-F8 and signs sections 1, 10 and 11 at the fixed commit. FB-9 is filed. The gate auditor ticks.
