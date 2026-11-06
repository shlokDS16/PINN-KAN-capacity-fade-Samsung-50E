# Red-team signature, PREREG_v4 rev. 16 (sections 1, 10, 11; plus 9.8 rule 5 for the M2 + M3 reading)

Scope: only what changed after my NOT SIGNED of rev. 15 (`research/audits/SIGN_redteam_rev15.md`, 6d34518).
- PREREG diff: `git diff 86f2170 9a05417 -- runs/prereg/PREREG_v4.md`. The file at HEAD is byte-identical to 9a05417.
- Code diff: `git diff 6d34518 83e4338 -- code/pinnkan/`. `code/` is unchanged from 83e4338 to HEAD.
- Rulings and decisions: `debates/D033_signoff/01_judge.md`, DECISIONS D034 and D035.
- Reports: `runs/prereg/CODER_D033_REPORT.md` and `CODER_D034_REPORT.md` (including the qc_pass note), `runs/d033_f7/RESULT.md`. I spot-checked the section 1 numbers against `runs/prereg/stats_sim_v4/RESULT_D034.md`.
- No Samsung data was opened, and nothing was edited except this file.

Tests run (CPU only, `CUDA_VISIBLE_DEVICES=""`, `.venv/Scripts/python.exe -P -m pytest`, one process per file):

| File | Result |
|---|---|
| `test_pk_negcontrol.py` | 34 passed |
| `test_pk_v2_stats.py` | 33 passed |
| `test_pk_d033_coder.py` | 39 passed |
| `test_pk_d034_coder.py` | 15 passed |

Total: 121 passed, 0 failed.

Probes I wrote myself, with no repository change:
1. A programmatic comparison of the code's title and clause strings (`stats_v4.TITLES`, T9 variants, E1-E3, T9_TAIL, LEAD_IN, M3_SENTENCE) against PREREG section 11.
2. `assemble_outcome` over 4 P1 tiers x P2 x P3 x K1 x 4 K2 tiers x Q-H x Q-A10 x R1_g1 x "most" (2048 inputs). This gave 60 distinct (P, K, M1, M2, M3, P3-if-P+) states, and each maps to exactly one title.
3. A rendered abstract sentence for P+/K+ with M1, M2 and M3 all holding.

Rating key: FATAL blocks the gate until a decision-ledger resolution. MAJOR also prevents the signature.

## Disposition of the rev. 15 findings

| ID | rev. 15 | Status at rev. 16 / 83e4338 | Evidence |
|---|---|---|---|
| F1 | FATAL | **Fixed** | `stats_v4.py:33` sets `DEFAULT_CONFIG` to w = `gt.W_ALT` (0.78) with e1' on. `runs/prereg/stats_config.json` holds the same values and is pinned in `guard.PIN_FILES` (`guard.py:25-26`). After FROZEN, `effective_config` (`stats_v4.py:116-137`) refuses a missing file, an unpinned or altered file, or any differing key. `run_stats_v4` calls it first (`stats_step.py:619-620`) and records the config and its sha256. PREREG 9.4 states the pin. Tests: levels 0.0195 / 0.0055, counts 30 / 32 from `resolve_config()` and `run_v4(cfg=None)`; e1' when "most" fails; overrides refused (API, CLI, altered file, unpinned file, n_expected). |
| F2 | MAJOR | **Fixed** | `primary_numbers` / `_stat` (`stats_v4.py:1023-1114`) and `stats_rows.number_sources` take each bracket from the analysis that set the tier. `BracketSignError` stops on a contradicting sign. My rev. 15 probe (P- set by a row) now prints a positive X from the row. PREREG 9.8 rule 6 states the rule. Y stays primary, which is correct because its clause needs P2 in every analysis. |
| F3 | MAJOR | **Fixed by AD1 (D034)** | P3 is now D_c = L_c(g1) - L_c(32, 2) (`stats_v4.py:334-339`; rows at `stats_rows.py` `row_tiers`, `lab_stratified_tiers`). `check_complete` requires (32, "2") through `grid_ks_labels`. Clauses e1 and e1' ("larger with 8 than with 32 cycling conditions") are now literally about m at a fixed window, forecast set and cap. Residual wording point: m-1 below. |
| F4 | MAJOR | **Fixed by AD2 (D034)** | Modifier M3 (A1 against R1 at g1, margin 0, 30 of 40 at 0.025) can only lower a P+ title. When M3 holds, T1-T3 and T9a/T9b become T4/T5/T6 and the persistence clause is added (`stats_v4.py:918-944`, `:973-975`). A P+ outcome without R1 at g1 raises `R1MissingError`, and `check_complete` requires R1 at g1. No P+ title can now print when A1 is not shown better than persistence at g1. |
| F5 (a) | MAJOR | **Accepted by the author (AD3, D034)** | The tension between T1-T3 and e3 is kept by recorded decision. The judge's condition ("signs only after the acceptance is recorded") is met. |
| F5 (b) | MAJOR | **Fixed (AD4)** | T9a/T9b read "with few cycling tests" unless P3 is S (`stats_v4.py:859-863`, `:935-936`). |
| F5 (c) | MAJOR | **Fixed (AD5)** | "closed-form" replaces "readable" in T1, T4 and T7 and in the K1-fail clause. That matches what K+ tests (an extracted closed-form law). |
| F5 (d) | MAJOR | **Disclosed (AD6)** | Disclosure added in 9.8 rule 4. Residual wording point: m-3. |
| F6 | MAJOR | **Fixed** | `negcontrol.check_invariance` fails on a non-finite value, or a shape mismatch, at any position. `summarise`, `compare_runs` (with `n_non_finite_predictions`) and `nc1_from_runs` (`stats_step.py:363`) propagate NaN. Tests cover NaN at the first, middle and last position, ±inf, NaN in both runs, and inner OOF. |
| F7 | MAJOR | **Fixed in substance** | Section 10 "Grid coverage" now separates the predict-stage check from the synthetic-only `nc1_full`. It states that Samsung tuning, selection and margins rest on data-build rules and the guard, and names the loader unit test. `runs/d033_f7/RESULT.md` gives development evidence at m 8/16/32 with short-record cells (0.0 outer and inner OOF). Residual wording slip: m-4. |
| F8 | MAJOR | **Fixed** | `metrics.permute_stress` (`metrics.py:170-194`) moves only `raw` by a derangement. `efc`, `t`, `ret`, the forecast mask and the window curve stay, so NC-2 can now fail (if the law ignores stress, L is about 0). Section 10 says "(each cell keeps its own throughput and window)" and adds that NC-2 is a partial control for E1. |
| M1 | minor | Fixed | Section 1 Expected endpoint and Power give K1 as 0.734 / 0.343 under the design and label 0.96 as the plain-test figure. |
| M2 | minor | Fixed | `SignRule.test` (`stats_v4.py:80-84`): positives = #{L > margin}, n = L.size. |
| M3 | minor | Fixed | "whereas" is used only for P-/K+ (`stats_v4.py:970-971`). The M1 no-op on T9 is stated in 9.8 rule 5. |
| M4 | minor | Disclosed | Methods lists the capped and unscored cells (section 5, "Methods disclosure of the cap"). |
| M5 | minor | Disclosed | The 9.9 (r) reading note says the estimate is descriptive and covers P1 at g1 only, that the concordance trigger changes no tier, and gives the upper-bound formula. |
| M6 | minor | Fixed | Section 1 "Methods defines" gives X (transformed median log ratio) and D\* (inner-CV winner per fold and m). |
| M7 | minor | Noted (D029/D030) | No change was asked. |

## Section 11 check (D034 strings)

- Word diff of section 11 between rev. 15 and rev. 16: the only changes are
  - the added M3 line (AD2), copied word for word from the judge's AD2 Opt 1;
  - "readable" → "closed-form" in T1, T7 and the K1-fail clause, and "Readable" → "Closed-form" in T4 (AD5);
  - T9a and T9b: "when cycling tests are few" → "with few cycling tests", plus the parenthetical "when ... in place of ... if P3 is S" (AD4).
- Compared with `debates/D016_roles/02_judge.md` lines 219-291, the block is 74 lines against 73 and differs in exactly seven lines. One is the added M3 line. The other six are the P+, P0 and P- table rows (the P0 row also carries the D030 T5/T6 strings), the T9a line, the T9b line and the K1-fail line. This matches the designer's list.
- The sha256 of the text from "## 11. Outcomes" up to "## 11a." is `001b1c79...26c9e5`, the value stated in 19.5 (8b).
- Code strings against PREREG: T1-T8, T9a/T9b in their "with few" form, E1, E2, E3, LEAD_IN, T9_TAIL and the M3 clause all appear verbatim in section 11. The "when" forms of T9 and the K1-fail clause are assembled from the bracketed alternatives, and they match.
- Mapping: every combination of states maps to one title id and one title string (probe 2 and `test_pk_d034_coder.py`, 288 combinations).
  - M3 sends T1/T2/T3 and T9a/T9b to the K column's T4/T5/T6.
  - M1 and M2 do not edit the fall-back title.
  - Without M3, M2 gives T9a/T9b in the "when" form only when P3 is S, on the effective (row-lowered) tiers.

## 9.8 rule 5: the M2 + M3 reading

When M2 and M3 both hold, the title is T4/T5/T6 and the sentence reads: P+ sentence, then the M2 tail ("the dataset authors' semi-empirical model was [W] % more accurate still"), then the M3 clause (probe 3).
- This matches the section 11 M3 line ("T1-T3 and T9a/T9b then become ... T4/T5/T6, and the sentence adds ...").
- No approved clause is dropped and no title is strengthened. M3 only replaces a P+ title with a P0-column title, and the M2 tail states that A1 is the weaker of two models.
- The rows apply M3 as a binary that can only turn "better than R1" into "not better" (`stats_rows.py` `row_tiers`, `lab_stratified_tiers`, row (iv) at g1). `run_v4` merges it with AND.
- The M3 bracket comes from the analysis that set it, and it stops if the lower end is above 0. With the design-effect rank (lower end = L(11), test = 30 of 40), the sign check agrees with the test.
- Nothing new weakens a gated claim:
  - D035 is symmetric across arms.
  - The P3 contrast passes the FWER guard (0.0192 against a bound of 0.0264, simulation).
  - M3 adds a conjunct and removes no test.
  - Rows (ii) and (iii) gain the (32, 2) cell rather than losing coverage.
  - A9 stays in D\*.

## FATAL
None.

## MAJOR
None.

## MINOR

- **m-1. Section 1 and section 2 overstate "only the number of cycling conditions differs".**
  - Where: `PREREG_v4.md:18` (P3 bullet) and the section 2 P3 row.
  - At (8, 2) every tuned arm uses 2 inner folds. At (32, 2) it uses 3 (`PREREG_v4.md:151`, D020, D035). The hard-ODE law tournament (`:142`) and D\* are also re-chosen per (fold, m).
  - The window, forecast set and caps are equal, as stated, but the tuning protocol is not.
  - Cheapest alternative explanation of a P3 pass: the flexible data-driven learners lose more than A1 from noisier 2-fold selection on 8 conditions. That is a selection-noise effect, not only a data-quantity effect.
  - The approved clause wording ("larger with 8 than with 32 cycling conditions") stays defensible because the fold count follows m in the protocol. The words "only ... differs" do not.
- **m-2. 9.8 rule 5 inverts the M3 condition in its justification sentence.**
  - Where: `PREREG_v4.md:305`: "a P+ title needs P1S (in the graph) and the failure of the R1 test".
  - The P+ title needs the R1 test to pass (rejected), that is, M3 to fail. Section 1 (`:24`), section 2 (`:44`), 9.11 (`:325`), section 11 (`:363`) and the code (`stats_v4.py:930`) all say so.
  - The same sentence's bound ("cannot exceed the graph's family-wise rate") holds per title only at the nominal 0.025 (intersection-union). It does not hold at the graph's simulated 0.0192.
  - Across the claim family (P+ title together with K claims), the R1 test's 0.025 sits outside the graph, like the "most" test.
  - The same label confusion appears in `RESULT_D034.md` section 6, where the column "P(P+ & M3)" is in fact P(P+ title). The section 1 loss bands are read correctly from it.
  - Code is correct, so this is text only.
- **m-3. The AD6 disclosure says "most holds there by construction once P2 is S".**
  - Where: `PREREG_v4.md:303`.
  - In folds with D\* = A9, d_c = 0.5 L_law,c, so the sign of d_c equals the sign of L_law,c on those conditions. The most-test count there equals the P2 count, so the most-test carries no information beyond P2 on those folds.
  - P2 S is a pooled statement, so it does not make each of those conditions positive. "Holds by construction" is stronger than the algebra.
  - This sentence is to be reported in the paper.
- **m-4. Section 10 still says one Samsung fold is compared.**
  - Where: `PREREG_v4.md:338`: "four of the five outer folds of the Samsung tuning records are never compared".
  - `nc1_full` is synthetic-only, so none of the five Samsung folds is compared between a clean and a scrambled pipeline.
  - The same sentence says that Samsung tuning is "not [protected] by a real-data invariance comparison", so the paragraph contradicts itself.
- **m-5. NC-1's stated purpose is broader than what it can see, now that a flow is disclosed.**
  - Where: `PREREG_v4.md:333` ("detect any flow from held-out post-window labels into predictions") against the qc_pass paragraph (`:337`).
  - A post-window outlier can be dropped by QC. That shortens n, changes the forecast set, and changes the D025 window min(k, n - 2) of a short cell, and so changes predictions. NC-1 holds that fixed by construction.
  - The effect is shared by every arm, so no contrast is favoured, and it is disclosed in Limitations. The "any flow" wording is not true without that qualification.
- **m-6. The F7 development evidence covers a reduced arm set.**
  - Where: `runs/d033_f7/configs/nc1_full_synth_m*.json`: arms A1, A2, A9, A10, A12, A15, G15, R1, R2.
  - A11, A13, A4 and A10P are absent, so D\* was chosen from {A9, A12}. It is not evidence for the full D\*/AG selection path.
  - The PREREG does not count it, and FB-9 ("all confirmatory arms") is still due at the frozen commit.
- **m-7. The config pin can be bypassed through `root`.**
  - Where: `stats_step.py:619-620` and `stats_v4.py:120`.
  - `effective_config` checks FROZEN in the `root` passed by a Python caller. A tree root without FROZEN skips the refusal.
  - The CLI cannot pass `root`. The output records `config_pin.frozen = false`, so this is auditable, but it is not fail-closed.
- **m-8. Two section 11 lines inside the approved block no longer cover M3.**
  - Where: `PREREG_v4.md:348`. The evaluation-order line still reads "modifiers M1 and M2".
  - The reading note's symbol list omits M3 and R1. M3's position is defined only outside the block (9.8 rule 5).
  - The mapping is unambiguous, because the M3 line overrides T1-T3 and T9.
- **m-9. Ambiguous word in section 1.**
  - Where: `PREREG_v4.md:23`: "K1 is rejected with probability 0.734".
  - It means that the K1 null is rejected, that is, K1 passes. As written, it reads as the claim failing.

## Checked and found sound
- NC-2 can now fail, and its Discussion consequence is earned as worded (partial control).
- The M3 test sits outside the graph and only lowers. A P+ outcome without R1 fails closed.
- The P3 node is absent (p = 1, never a pass) when (32, 2) is missing, and `check_complete` makes it present in a strict run.
- Row (iv) covers P1, P2, "most" and M3, and not P3. This is stated in 9.8 rule 2.
- The section 1 restated numbers I checked are present in `RESULT_D034.md`: 0.674-0.676, 0.587-0.590, 0.335 / 0.349, 0.051 / 0.111, 0.176 / 0.185, 0.0188 / 0.0192 / 0.0264, and the M3 loss bands 0.000-0.002, 0.000-0.466, 0.012-0.916 and 0.368-0.982.

## Result that would force rejection of a claim
- **P+ title:** the R1 test at g1 fails under the primary analysis or any row, which is now enforced. Or P3 passes at (32, 2) and disappears when both cells use the same inner-fold count (m-1).
- **NC-1 trust:** a non-finite value in any invariance record, which now fails, or FB-9 not run with all confirmatory arms at the frozen commit.
- **"Closed-form" titles (T1, T4, T7):** a K+ state whose extracted law cannot be written out for the fold-by-seed laws of the stability table.

Red-team signature (sections 1, 10, 11): SIGNED


## Rev. 17 confirmation

Scope: `git diff a03ff81 4e29223` on `runs/prereg/PREREG_v4.md`, `code/pinnkan/stats_v4.py`, `code/tests/test_pk_rev16_m7.py`, `runs/freeze_runs/make_configs.py`. Samsung data not opened. Nothing else edited. Checks run: sha256 of section 11, grep for the old phrases, the K1 figures against `RESULT_D034.md` 3.1, the generated FB-9 configs, `python -m pytest code/tests/test_pk_rev16_m7.py code/tests/test_pk_d033_coder.py` (41 passed).

| Item | Status | Evidence |
|---|---|---|
| m-1 | FIXED | Section 1 P3 bullet (`:18`) and section 2 P3 row (`:36`) now say the tuning protocol follows m (2 inner folds at m = 8, 3 at m = 32; tournament and D\* re-chosen per (fold, m)) and name the selection-noise reading as an alternative the design does not separate. "Only ... differs" is gone (grep). The claim is weakened, not strengthened. |
| m-2 | FIXED | 9.8 rule 5 (`:305`) now reads "R1 test rejected (A1 better than R1), that is, M3 fails", consistent with `:24`, `:325`, `stats_v4.py`. The bound is stated per title at the nominal 0.025 (intersection-union), says it can exceed the graph's simulated 0.0192 when the false part is A1 against persistence, and places the R1 test outside the family-wise count. The `RESULT_D034.md` 6 column label is corrected in a note. Weaker claim than before. |
| m-3 | FIXED | 9.8 rule 4 (`:303`): "by construction" removed. It now says that on D\* = A9 folds the most-test count equals the P2 count and adds no information, and that P2 S is a pooled statement. |
| m-4 | FIXED | Section 10 (`:338`): "none of the five Samsung outer folds is compared ... (`nc1_full` is synthetic-only)". The self-contradiction is gone. |
| m-5 | FIXED | NC-1 purpose (`:333`) now excepts the QC-drop path and names its effect (retained record, forecast set, D025 window), that NC-1 holds it fixed, and that it is shared by all arms and disclosed in Limitations. |
| m-6 | FIXED | `make_configs.py`: FB-9 configs at m 8, 16, 32. Each takes `arms` from `conf_samsung_B_f0_m{m}.json` (14, 11, 15 arms: A4, A10P, A11, A13, A15, G15 etc. now present where the grid config has them). Short-record cells (`short_records`) are set, and `run.py:136` and `synth.shorten_cells` read exactly those keys. The generated `runs/freeze_runs/configs/fb9_*.json` match. This is configuration only. FB-9 is still due, unrun, at the frozen commit. |
| m-7 | FIXED | `effective_config`: a caller `root` without FROZEN falls back to the frozen project root and then enforces the pin. Both new tests pass, and the existing D033 pin tests (41 in total) still pass. The two tests monkeypatch `guard`, so the real pin path under a copied tree is not exercised. This is a coverage note only. |
| m-8 | LEFT BY DESIGN | Inside section 11, unchanged. The mapping stays unambiguous (the M3 line overrides T1-T3 and T9). It remains open for the author. It is not a defect of this revision. |
| m-9 | FIXED | "the K1 null is rejected (K1 passes)" in both places in section 1. |

Section 11: sha256 of "## 11. Outcomes" up to, not including, "## 11a." is 001b1c798342... at both a03ff81 and 4e29223. Untouched.

No claim strengthened. Two observations that do not block:
- The K1 figures changed 0.734 / 0.343 / 0.693 / 0.386 to 0.766 / 0.379 / 0.709 / 0.408 (statistician N2). They match `RESULT_D034.md` 3.1, rows `P_K1`, and the old figures are kept and labelled "former contrast". They are simulation power figures for the expected endpoint, not a test, margin or claim. The 0.03 shift is larger than the roughly 0.01 Monte Carlo noise that `RESULT_D034.md` quotes for P3, and it is attributed there to the new contrast. I did not re-simulate.
- m-1 and m-2 add reading text only. No title, tier, margin, count or graph weight changed.

Red-team signature carried to rev. 17: CONFIRMED
