# Red-team signature, PREREG_v4 rev. 20 (section 10; 9.3 "Where it applies" and the 9.11 rows for PC-3 and PC-2)

Date: 2026-11-06. Role: red team (signs sections 1, 10 and 11). The previous signature is `SIGN_redteam_rev16.md` (rev. 16, confirmed at rev. 17, `:144-166`).

**Verdict: NOT SIGNED.** I found 3 MAJOR and 5 MINOR findings and nothing FATAL. A MAJOR finding withholds the signature, the same rule as in rev. 16.

## Scope and reading
- **PREREG diff.** `git diff 92db4cb c702e1a -- runs/prereg/PREREG_v4.md`, restricted to section 10 (`:334-344`), 9.3 "Where it applies" (`:271`) and 9.11 (`:327-328`). Read in full: section 1 (`:15-25`), 9.3-9.11 (`:256-332`), section 10 (`:334-344`), the section 11 block (`:346-427`), 11a (`:429-442`) and section 12 (`:444-448`).
- **Code.** Read in full: `code/pinnkan/stats_gaps.py` (`:1-280`), the tail of `code/pinnkan/stats_step.py` (`:395-786`) and the `git diff 052eefd 39b14aa` of that file. Partial reads:
  - `stats_rows.run_v4_full` (`:253-282`);
  - `emit._cal_members` and `emit.storage_hull` (`:39-64`, `:292-295`);
  - `physval.merge_stress_functions` and `figure_inputs` (`:34-59`, `:236-253`);
  - the tests in `code/tests/test_pk_stats_gaps_g1_g8.py` at `:333-475`.
- **Records.** `research/audits/SIGN_statistician_gaps.md` (full), DECISIONS D038 (`:739-754`), and the final section of `GATE_freeze_audit.md`.
- **What I did not open.** No Samsung data, retention value or run output. `runs/prereg/FROZEN` is absent.

**Probe (synthetic only, CPU).** I wrote a probe file in the scratchpad. It reuses the module fixtures of the test file:
`C:\Users\Shlok\AppData\Local\Temp\claude\C--Users-Shlok-Downloads-Multi-Modality-Language-model--claude-worktrees-distracted-knuth-2988a8\d91c28c7-7463-4cd6-912a-36fe62f77487\scratchpad\rt20\test_rt20_probe.py`
(1 passed, 18.8 s). Results:
- (a) A strict run with NC-2 and (b) a strict run with NC-2 omitted give the same `P+`, `K=`, `T2` and M1-M3. Only (b) lists `registered_controls_not_evaluated: {NC-2: "no negative_runs given"}`.
- (c) A lenient run in which NC-2 raises writes `contrasts_v4_B.json` with title T2 and `provisional: true`.
- In all three runs, a strict run without the three downgrade-row inputs and without `h7_run` still produces title T2: `rows_not_run` lists 3 rows, `gate_not_evaluated` is `[PC-1]` and `provisional` is true.
- No code path writes strict or lenient into the output.
- If run (a) is re-run into the same directory without `negative_runs`, the NC-2 record disappears from `controls.json`.

**Hull probe.** Synthetic storage points were placed at 10, 23 and 45 C. The Delaunay test counts boundary points (the extreme temperatures) as inside. That part is correct.

## Answers to the brief's questions
1. **Can PC-2, PC-3 or the new failure and provisional rules change a gate, tier, title, state or claim of section 11?**
   - **Not through the code.**
     - `extend_controls` asserts that `gate_G.tripped`, `.reasons`, `.not_evaluated` and `.rule` are unchanged (`stats_gaps.py:269-273`).
     - `gate_g` reads PC-2 and PC-3 only into `reported_checks` (`stats_step.py:424`).
     - M3 uses R1 at g1 and never `P3_passed`.
     - Probes (a) and (b) give identical states and titles.
   - **The strict stop** decides only whether a contrasts file exists. It never decides which title it holds.
   - **But "provisional" has no defined meaning in the text** (M-1), so the text cannot show that a provisional outcome carries no title.
2. **Can a researcher exploit the rules after seeing results?** Yes, through "not evaluated" (M-2) and through the stop path (M-3).
   - The hull and the SOC/T grid cannot be re-chosen in any other way:
     - the grid is fixed in T1 and hard-coded at `emit.py:40, 43`;
     - the hull is built from the (T, SOC) design identifiers of the training storage cells (`emit.py:292-295`).
   - Two loose ends remain: the bounding-box fallback (m-2) and the fact that nothing asserts the grid (m-3).
3. **Are PC-2's every-member rule or PC-3's sign test a forking path?** No for the verdicts.
   - Both are fixed in advance, and neither carries a tier.
   - Every-member is the stricter reading.
   - PC-3 is the M3 machinery, `SignRule.test(L, 0)`, with n not reduced (`stats_gaps.py:176-183`).
   - The fork that remains is in the reporting (m-4).
4. **Is "provisional" defined well enough when read with 9.8 and 11?** No (M-1).
5. **Conflicts with section 1 and with NC-2's wording?** Two:
   - NC-2 says "It does not stop the study" (`:342`), but the new rule stops the step and gives no exit (M-3 (c)).
   - The section 1 E1 bullet (`:22`) relies on NC-2, and an NC-2 that is not evaluated has no stated consequence (M-2).

## Findings

### M-1 (MAJOR) "Provisional" is used once and defined nowhere
- **Where.** `PREREG_v4.md:344`, "is listed and marks the outcome provisional". This is the only occurrence of the word in sections 1-18 (grep). Neither 9.8 (`:299-306`) nor the section 11 block nor its reading note (`:348`) says what a provisional outcome is:
  - whether it carries a title and an abstract sentence;
  - whether the paper may be submitted from it;
  - where "listed" means (Results, Limitations, or only JSON);
  - how, and by when, the status is resolved.
- **What the code does.** Provisional is a JSON label: `stats_step.py:591-596`, `:742-755`, `stats_rows.py:276-281`. A full title and abstract sentence are still assembled under it. In the probe, title T2 was issued with three downgrade rows not run and gate input PC-1 not evaluated.
- **Why it matters.** Rows (ii)-(iv) of 9.8 rule 2 can only lower a tier. So a title formed without them may be stronger than the one 9.8 rule 2 allows. The row-omission behaviour predates rev. 20, but rev. 20 is what writes "provisional" into the registered text without bounding it. As frozen, the rule cannot be audited: an auditor cannot tell whether a paper written from a provisional outcome complies.
- **Rejection condition.** Any manuscript title, abstract sentence or tier word taken from an output whose `outcome.provisional` is true.
- **Fix (text, section 10, appended after the sentence at `:344`; section 11 is not touched).**
  > "A provisional outcome (a registered control of this section, a downgrade row of 9.8 rule 2, or a gate input of section 11 not evaluated) is not a result: no title, abstract sentence, tier word or extent clause is taken from it, and the paper is not submitted from it. The confirmatory outcome is the first strict statistics run at the FROZEN commit whose outcome is not provisional, apart from a control that is not evaluable for the data reason named in its rule."
- **Fix (code, `stats_step.run_stats_v4`, before `:739`).** If `strict and guard.is_frozen(root)`, raise `RegisteredControlError` when any of these is absent:
  - `row_runs["lab_indicator"]`;
  - `row_runs["retain_all"]`;
  - `row_runs["random_subset"]`, unless 9.9 (o) has been made descriptive by a change-log row under stop rule 5 (5);
  - `h7_run`.

### M-2 (MAJOR) "Not evaluated" costs less than "failed", and for NC-2 and PC-2 the caller can choose it
- **Text.**
  - NC-2: a fail obliges the Discussion to say that "stress dependence was not shown necessary" (`:342`).
  - PC-2 and PC-3: a fail is written into the audit note and a Limitations sentence (`:344`).
  - "Cannot be evaluated" only "is listed". No sentence is prescribed for it.
- **Code.** In a strict run, NC-2 is optional:
  - `stats_step.py:576-578` turns a missing `negative_runs` into a provisional label;
  - `--negative-run` is optional on the CLI (`:667`).
  This holds even though the five NC-2 configurations `conf_samsung_B_f*_m32_nc2.json` are in the frozen confirmatory set. For NC-2, "cannot be evaluated" can therefore only mean "not supplied".
- **PC-2.** Removing `stress_functions.json` or `storage_hull.json` from one g4 run directory gives "not evaluated" (`stats_gaps.py:215-218`; `test_pk_stats_gaps_g1_g8.py:380-396` shows exactly this). The statistics step checks no hash of these files.
- **The path.** The step is re-runnable and overwrites `controls.json` (probe). So: run, see an NC-2, PC-2 or PC-3 fail, re-run without the input. The fail sentence is replaced by a label that has no defined consequence (M-1). The section 1 control for E1 (`:22`) is lost without a trace in the manuscript.
- **Rejection condition.** Any confirmatory output in which NC-2 or PC-2 is "not evaluated" while its registered inputs exist under `runs/`.
- **Fix (text, replacing the sentence "A control that cannot be evaluated ... before the contrasts are written." at `:344`).**
  > "A control is not evaluable only for the data reason named in its rule (PC-2: no SOC level with two storage temperatures inside the hull); it is then listed in the Results with that reason and the paper prints the consequence of a failed control in the form '[control] could not be evaluated: [reason]'. Every other absence (NC-2 runs not supplied, a g4 run without `stress_functions.json` or `storage_hull.json`, R1 and A1 scored on different conditions) is a failure to compute."
- **Fix (code).**
  - `stats_step.py:576-578`: in strict mode, set `errors["G3_nc2"] = "no negative_runs given (registered: conf_samsung_B_f*_m32_nc2)"` and `nc2 = failed("G3_nc2")`. Keep the `reg_missing` branch only for `not strict`.
  - `stats_gaps.py:215-218`, `:224-225` (PC-2 inputs) and `:174-178` (PC-3 sets): `raise ValueError(...)` instead of returning a "not evaluated" record, so that a strict run stops.
  - Keep "not evaluated" only at `:244-245`.
  - Adjust `test_f1_missing_inputs_*` and `test_f1_pc2_inputs_missing_*` to expect `RegisteredControlError` in strict mode.

### M-3 (MAJOR) The strict stop can be bypassed, has no defined exit, and contradicts NC-2's "does not stop the study"
- **(a) Bypass.** The stop exists only when `strict` (`stats_step.py:780`). D038 says "stops a strict statistics run" (`DECISIONS.md:745`), but the prereg says unconditionally "stops the statistics step".
  - `--lenient` (`:679`) turns the stop into a provisional label and writes `contrasts_v4_B.json` (probe (c)).
  - Nothing in the prereg requires the confirmatory statistics step to run in strict mode.
  - The output does not record the mode (no code path writes it).
  - Nothing refuses lenient on Samsung runs after FROZEN.
- **(b) No defined exit.** After a stop, `controls.json`, holding the NC-2, PC-2 and PC-3 verdicts and the gate, has been written and can be read. The text does not limit what the "fix" may change, does not require a commit or disclosure, and does not keep the stopped record. The re-run overwrites `controls.json`.
- **(c) No exit when the cause is in the inputs.** Some NC-2 failures are integrity errors in the inputs:
  - `stats_gaps.py:142, 145, 148`: no A1 at g4, unequal condition sets, other folds;
  - `stats_step.py:570-571`: a run that is not a permute_stress run of Test B.
  These cannot be cured without re-running a scored configuration (stop rule 6, `:447`). The registered text gives no exit, so an interpretive, non-gating control can hold the confirmatory output indefinitely, against "It does not stop the study" (`:342`). It also hands the researcher a choice of exit after seeing `controls.json`.
- **Rejection condition.** Any of the following:
  - a confirmatory `contrasts_v4_B.json` produced with `strict = False`;
  - a re-run after a stop whose fix commit touches code outside the failing control's function;
  - a stopped record that is not filed.
- **Fix (text, appended to the sentence at `:344` after M-2's text).**
  > "The confirmatory statistics step runs in strict mode at the FROZEN commit, and its output records the mode and the commit; a lenient output is never a result. After a stop, the fix is a new commit that changes only the failing control's function (`stats_gaps.nc2_v4`, `pc2_v4`, `pc3_v4` or `extend_controls`); the stopped run's `controls.json` and `STATS_GAPS_ERRORS.json` are kept with their sha256 and disclosed with the fix in the appendix. If the cure needs a scored configuration to be run again, the control is recorded as failed, with its failed-control sentence, and the step continues; NC-2 never stops the study."
- **Fix (code, `stats_step.run_stats_v4`).**
  - At entry: `if not strict and guard.is_frozen(root) and any(_load(os.path.join(d, "config.json")).get("dataset") == "samsung" for d in run_dirs): raise ValueError("lenient is refused on Samsung runs after FROZEN")`.
  - Set `out["status"]["strict"] = bool(strict)` and `out["status"]["head"] = guard._git(root, "rev-parse", "HEAD")`.
  - At `:780`, before raising, copy `controls.json` and `STATS_GAPS_ERRORS.json` to `analysis_dir/stopped_<n>/` and write their sha256 there.

### m-1 (MINOR) PC-3 "with no alpha added" borrows M3's justification without having it
- **Where.** `PREREG_v4.md:344` and the 9.11 row (`:327`).
- **Problem.** M3 adds no alpha because it acts only together with P1S, an intersection-union argument (9.8 rule 5, `:305`). PC-3 has no partner test. It is a separate one-sided 0.025 test outside every family. Its pass can still be stated in the Results.
- **Rejection condition.** A PC-3 pass described in the paper as covered by the family-wise error rate.
- **Fix.** At `:344`, replace "outside the graph and with no alpha added" with "outside the graph and outside the family-wise count of 9.11, labelled like the safety findings". At `:327`, change "outside the graph, reported" to "outside the graph and the family-wise count, labelled like the safety findings, reported".

### m-2 (MINOR) PC-2's hull falls back to a bounding box, a substitute rule that T1 does not contain
- **Where.** `stats_gaps.py:203-205`, tested at `test_pk_stats_gaps_g1_g8.py:472-474`.
- **Problem.** On a Qhull error (storage points that do not span the plane), the code uses the bounding box. T1 says "convex hull" and "no substitute rule". For collinear points that are not aligned with an axis, the box is much larger than the hull.
- **Rejection condition.** A PC-2 verdict whose `hull` field begins "bounding box".
- **Fix.** In `_inside_hull`, on the exception, re-raise `ValueError("storage points do not span (T, SOC): PC-2 hull undefined")`. With M-2 this is a failure to compute. The test at `:472` should then expect the raise.

### m-3 (MINOR) The T1 grid is not asserted
- **Where.** `pc2_v4` takes `T_C` and `soc` from whatever `stress_functions.json` holds (`stats_gaps.py:219-222`). T1 fixes T = 10, 23, 45 C and SOC = 0, 5, ..., 100 %. Only the emitter (`emit.py:40, 43`) enforces this.
- **Rejection condition.** A PC-2 record whose `T_C` differs from [10, 23, 45] or whose SOC grid differs from the T1 grid.
- **Fix.** After `:222`, add `if T.tolist() != [10.0, 23.0, 45.0] or soc.tolist() != list(np.arange(0, 101, 5.0)): raise ValueError("PC-2 grid differs from PREREG_v4 10 (T1)")`.

### m-4 (MINOR) PC-2 and PC-3 outcomes have no fixed sentences, and Fig. 6 can show monotonicity outside the hull
- **The reporting fork.** T1 reports "the mean curve and the number of failing members" beside the verdict. With no fixed sentence, a failed every-member verdict can be narrated through the mean curve.
- **The figure inputs ignore the hull.** `physval.py:250` writes `share_members_increasing_in_T` at SOC 5, 50, 80 and 100 % regardless of the hull. So Fig. 6 can show a T-monotone share at SOC levels that PC-2 excluded.
- **The lab confound is missing.** The statistician's caveat (`SIGN_statistician_gaps.md:63`) is not attached to PC-2: 10 C storage is all SIE and 45 C all HM.
- **Rejection condition.** Any Results, Discussion or caption sentence on PC-2 or PC-3 that is not one of the fixed sentences below, or a Fig. 6 panel at an excluded SOC that is not marked.
- **Fix (text, section 10 after T1).**
  > "Fixed sentences: pass: 'Inside the storage hull the fitted calendar rate increased with storage temperature at every evaluated SOC for every fold and seed; storage temperature is aliased with laboratory (10 C all SIE, 45 C all HM), so this is consistent with, not evidence for, an Arrhenius-type dependence.' Fail: 'The fitted calendar rate did not increase with storage temperature for [k] of [n] fold-seed members at [SOC list] inside the storage hull.'"
- **Fix (text, after T2).**
  > "Fixed sentence: 'At g4 the network's median condition error was [lower / not shown lower] than carrying the last check-up forward ([positives] of [n]; a reported check outside the family-wise count).'"
- **Fix (Fig. 6 caption).** The caption marks the SOC levels outside the hull.

### m-5 (MINOR) "The fitted A1 storage rate" is not defined
- **Where.** The code evaluates `law.r_cal` at DoD = C_ch = C_dch = 0, as the initial rate, without the per-cell latent or the state modulation (`emit.py:55-58`). T1 does not say so.
- **Rejection condition.** A PC-2 computed on any other quantity.
- **Fix.** At `:344`, replace "the fitted A1 storage rate" with "the initial calendar rate r_cal of the fitted A1 law at zero cycling stress, without the per-cell latent (`stress_functions.json` `storage_rate`)".

## Not found (checked)
- **The gate is unchanged.** Gate G is still NC-1 + PC-1 (`stats_step.py:406-426`).
- **No new tier or title path.** PC-2, PC-3 and NC-2 have none (probe a = b).
- **PC-3 counts.** 30 of 40 at 0.025, with ties not positive. PC-3 is listed in 9.3 and 9.11 consistently.
- **NC-2 level.** It is fixed at 0.025 (`NC2_ALPHA`, `stats_gaps.py:31`).
- **Section 11** is not touched by rev. 20 (gate auditor's sha256 check).

## Ledger
This project has no `tools/ledger.py`, so no ledger rows were added. A resolution of M-1 to M-3 goes into a DECISIONS row.

**Red-team signature (section 10 at rev. 20; sections 1 and 11 carried from rev. 17): NOT SIGNED.** Re-signing needs only a check of the M-1 to M-3 fixes and of whichever minors are applied.

## Re-sign (2026-11-06, scoped to M-1 to M-3 and m-1 to m-5)

**Scope.** I checked three things, all synthetic, on CPU:
- the working-tree word diff of `runs/prereg/PREREG_v4.md` against c702e1a (`:327`, `:344`);
- `git diff` of `stats_step.py`, `stats_gaps.py`, `physval.py` and `fig6_storage.py`, all uncommitted on c702e1a;
- `test_pk_stats_gaps_g1_g8.py`: **46 passed** (40.5 s).

I opened no Samsung data and no run output, and edited nothing except this file.

| Item | Status | Evidence |
|---|---|---|
| M-1 | FIXED | Text at `:344`: a provisional outcome is "not a result": no title, abstract sentence, tier word or extent clause is taken from it, and the paper is not submitted from it. Code: a strict run with FROZEN refuses a run that lacks `lab_indicator`, `retain_all`, `random_subset` (or a struck-row id) or `h7_run` (`stats_step.py:767-770`). Test `test_m1_*`. |
| M-2 | FIXED (deviation accepted, see below) | Text: "not evaluable" covers only the PC-2 data reason. Every other absence is a failure to compute. T1 and T2 now say "has failed to compute". Code: `_absent(require, ...)` raises (`stats_gaps.py:172-176, 225-239`), and missing NC-2 runs become an error under `require` (`stats_step.py:603-606`). Tests `test_m2_*`. |
| M-3 | FIXED | Text: strict mode at the FROZEN commit; a lenient output is never a result; the fix is confined to the failing control; the stopped record is kept and disclosed; a cure that needs a re-score means the control is recorded as failed; "NC-2 never stops the study". Code: lenient is refused on Samsung runs after FROZEN (`:752-754`); `status.strict` and `status.head` are recorded; `stopped_<n>/` is written with `SHA256.json` (`:825-827`). Tests `test_m3_*`. |
| m-1 | FIXED | `:344` and the 9.11 row (`:327`) now say "outside the family-wise count ..., labelled like the safety findings". |
| m-2 | FIXED | `_inside_hull` raises when the points do not span the plane. The bounding-box fallback is gone. Test `test_m2_pc2_collinear_*`. |
| m-3 | FIXED | `PC2_T_GRID` and `PC2_SOC_GRID` are asserted (`stats_gaps.py` after the merge). Test `test_m3_the_pc2_grid_*`. |
| m-4 | FIXED (caption pending) | The fixed pass/fail sentences for PC-2 (with the lab confound) and the fixed PC-3 sentence are in `:344`. Fig. 6 draws SOC levels outside the hull dashed, from `soc_selected_in_pc2_evaluation`. The caption sentence is manuscript text and goes to `debates/D-figures.md`, which I accept. |
| m-5 | FIXED | `:344` now says "initial calendar rate r_cal of the fitted A1 law at zero cycling stress, without the per-cell latent". |

**Ruling on the deviation (require only when the run is strict and FROZEN exists): ACCEPTED.**
- No Samsung outer score can exist before FROZEN. The scorer refuses without the item (f) record, and the item (f) writer needs FROZEN and HEAD equal to the FROZEN commit.
- The text is the backstop. Suppose a run escapes the code check: a caller passes `require_registered=False`, or a `root` without FROZEN, or runs lenient. Its output is then provisional, or records `strict: false`. By `:344` such an output is not a result.
- So the gate costs no protection on confirmatory data, and it keeps the development fixtures usable.

**New minors (non-blocking; a fix is welcome before the freeze commit):**
- **n-1 (text, `:344`).** "The confirmatory outcome is the first strict statistics run at the FROZEN commit ..." contradicts "After a stop, the fix is a new commit". Read literally, no run after a fix can be confirmatory. Fix: after "at the FROZEN commit" insert ", or at a fix commit made under the stop rule of this paragraph,".
- **n-2 (code, `stats_step.py:767-768`; `stats_rows.py:276-277`).**
  - `_decision_row_exists` accepts any id present in DECISIONS.md, so `random_subset_struck="D001"` passes.
  - A legitimately struck random-subset row is still counted in `rows_not_run`, so the outcome stays provisional, which by M-1 means not a result. That contradicts stop rule 5 (5), where the row becomes descriptive rather than missing.
  - Fix:
    - require that the row text names "9.9 (o)" and "stop rule 5";
    - when the row is struck, drop `random_subset` from `rows_not_run` before the provisional flag is computed;
    - record the row id in `status`.
- **n-3 (code).** `status` records `strict` and `head` but not `require` and `frozen`. A run with `require_registered=False` or a non-FROZEN `root` is detectable only through the provisional flag. Fix: `prov["require_registered"] = require` and `prov["frozen"] = frozen`.
- **n-4 (code).** The text says a cure that needs a re-score is "recorded as failed ... and the step continues", but no code path does this. It would itself need a fix commit. This is acceptable because the text fixes the outcome.

**Section 11** is not touched by this change (per the lead; the hunks are at `:327` and `:344` only).

**Red-team signature (sections 1, 10 and 11 at rev. 20 as amended): SIGNED.** M-1 to M-3 and m-1 to m-5 are resolved. n-1 to n-4 are minor and do not block.
