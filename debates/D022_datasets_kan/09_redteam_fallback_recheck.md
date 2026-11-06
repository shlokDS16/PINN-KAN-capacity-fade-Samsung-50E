# C26 red-team re-check of the D022b fallback (2026-11-05)

Red team (checks only). Re-check of `08_redteam_fallback.md` (0 FATAL, 4 MAJOR, 5 MINOR) against HEAD 835d1aa (fixes a3a8f7f, b9e5926). `git status` shows no uncommitted change under `code/` or `runs/prereg/`.

**Reading depth.** Full text: `08_redteam_fallback.md`; `code/pinnkan/extraction_audit.py` and `extraction_audit.json`; `code/tests/test_extraction_fallback.py`; `stats_step.py` 395-430 and 480-580; `stats_v4.py` 728-751; `physval.py` 150-215; `fig5_stress.py` 40-110; diff of b9e5926 for physval, fig5, symbolic, stats_step; PREREG_v4 7.3 items 1-3, 6 and 11a items 5-10. Partial: `emit.py` (VARS, `stress_functions`), `run.py` 490-555, test_extraction_calibration.py 395-470. Not read: Samsung data (not opened), the calibration script body. Executed by me (CPU, `CUDA_VISIBLE_DEVICES=""`): `test_extraction_fallback.py` plus `test_extraction_calibration.py`, 57 passed in 52 s; probes of `_licensed`, `banned_phrases_in` and `gate_g`+`check_generated_sentences` on identifier-free strings; an AST scan of every string constant longer than 25 characters in stats_v4, stats_step, stats_rows and physval against the banned list.

**Result.** All four MAJOR findings of 08 are closed except A4, which is closed only in part and now carries one new defect of its own (N1). The licence, temperature and calibration-number properties asked for hold on the confirmatory path. One new MAJOR (N1), no FATAL.

## 1. Properties asked for

| Property | Status | Evidence |
|---|---|---|
| `label_input` and `label_law` default to `calibrated=False` (also `audit_arm`) | holds | `extraction_audit.py:290`, `:335`, `:381` (signatures printed by me); `_licensed` `:46-55` returns False for None/False, refuses a bare `True` (AuditGuardError, verified) |
| Unlicensed `audit_arm` returns no label, no licence sentence, no scope sentence | holds | `:385-386` returns `labels_printed False`, the stability table and the caption only; the test at `test_extraction_fallback.py:84-90` asserts no "calibration design", "re-run", "verified" |
| The confirmatory configuration passes no `audit_dir` | holds | grep of all `.py/.json/.sh/.ps1/.md/.yml/.toml` outside tests and debates: `audit_dir` appears only in `stats_step.py` (signature, CLI, the two branches) and `stats_v4.py`; no config, run list or script sets it. The CLI has `--audit-dir` but no `licences` option; with `--audit-dir` the step raises `AuditGuardError` (`stats_step.py:568-570`) |
| Default stats output has no licence word, label or calibration number | holds | `stats_step.py:560-567` -> `stats_v4.edge_level_wording(run_dirs)` with `licences=False` (`stats_v4.py:736-740`): `printed False`, `descriptive_only`, `contribution False`, stability tables and the caption. `test_extraction_calibration.py:~417-420` asserts the absence of "identified:", "form: ", "sign: ", "verdict", "upper_limit" |
| Banned-phrase list with word boundaries, applied fail-closed | holds in form, defective in effect | `banned_phrases_in` `:95-119` (lookarounds against letters and `_`, hyphens/line breaks/case normalised); `check_generated_sentences` `:122-141` called at `stats_step.py:575-576` before any file is written. See A4 and N1 |

## 2. Finding-by-finding

| 08 finding | Verdict | Where |
|---|---|---|
| **A1** (MAJOR) temperature direction and "consistent / not consistent" from the learned law | **Fixed** | `physval.py:153` `T_VARS = ("T", "T_C")`; `cyclic_directions` `:161-170` and `compare_with_a10_signs` `:177-190` return only the fixed label for T (no shares, no sign, no verdict, no envelope); `status` key no longer hides the case that only T exists (`:190`). `fig5_stress.py:74-77` draws no curve and no A10 line in the T panel, only the label; `symbolic.py:445-460` `describe` masks the first-layer T edge (but see B2). Tests `test_extraction_fallback.py:35-60`. The variable name used by `emit.VARS` is "T" and by the spec "T_C"; both are covered |
| **A2** (MAJOR) unlicensed output asserts a calibration | **Fixed** | `scope_sentence` is no longer returned by the unlicensed branch (`:386`); the word "calibration" and "re-run" are absent from `wording` in `extraction_audit.json`; the scope, results, "not identified" and failure sentences moved under `future_version_wording` (`extraction_audit.json:116-`, with a note that nothing there is reachable). Test `:84-90` |
| **A3** (MAJOR) cap justification circular, D021 flags omitted | **Fixed (PREREG text, rev. 8)** | PREREG_v4 7.3 item 3 now says the zero at cap 2 holds by construction, states the D2 margin (0.0210 against 0.02; found in `runs/D021_cap_synth/decision.json` as 0.02098), the D4b flag (+0.0225; `decision.json` 0.02254) and the two non-finite cap-3 refits; "justified by" no longer used. Numbers traced to `decision.json` (0.0168, 0.0225, 0.0210); the others (9 of 10 seeds, 0.045-0.084 against 0.078-0.102, 1.5 to 19 %) are quoted from `01_architect.md` and not re-read in the json by me |
| **A4** (MAJOR) banned list: holes, false positives, no caller | **Partly fixed; not closed** | Caller: now `stats_step.py:575-576` (fixed). Variants (recover*/discover*, identified/identifiable/identifiability, power-law, line break, exponential, quadratic, activation energy, non-monotone): caught, 21 parametrised claims pass (`test_extraction_fallback.py:69-82`). Not fixed: holes N2, N3 below. New defect: N1 |
| **B1** (MINOR) "verified calibration" not verified by `_licensed` | **Partly fixed** | `_licensed({})` and `{"verdict": {}}` are now False (`:53-54`, verified). `_licensed({"verdict": True})` and `{"verdict": {"void": True}}` are still True: any dict with a truthy verdict licenses. `label_text` (`:340`) and `results_sentence` (`:350`) remain unguarded |
| **B2** (MINOR) temperature statements remain by design | **Fixed in the outputs, open in the equation** | Stability table T row carries only the label and the note, no family counts, no sign votes (`:369-371`; test `:155-161`); Fig. 5 shows no T curve. The printed closed-form equation: PREREG 7.3 items 1 and 6(a) allow printing it in full, which shows T's term; the masking `describe` has no production caller (grep), so what produces the printed equation is not code in the repository |
| **B3** (MINOR) item 1 contradicts item 6 | **Fixed** | PREREG 7.3 item 1 now reads "the fitted equation may be printed in full ... (shown, not described), while no form or direction is named for its individual effects (item 6)"; the "linear in log C_dch" example is gone |
| **B4** (MINOR) "equally simplified" and the K2 reading | **Fixed (text)** | 7.3 item 2 defines the phrase once; item 3 (i) states that a K= or K- outcome can partly reflect extraction loss. The flag is a stated limitation, not an automatic printed line beside K2 (no code) |
| **B5** (MINOR) descriptive path aborts the step on a partial grid | **Partly fixed** | `stats_step.py:562-567` catches `AuditError` and records "not available". `edge_level_wording` raises `AuditGuardError` ("no extracted laws", `stats_v4.py:739`) when `extracted_laws.json` files exist but none is a g4 (`m = 32`) run; `AuditGuardError` is a `RuntimeError` (`extraction_audit.py:33`), `AuditError` a `ValueError` (`:58`), so the `except` does not catch it and the step aborts after the contrasts are computed |

## 3. New and residual issues

### N1 (MAJOR). The fail-closed check aborts the statistics step when Gate G trips on PC-1
- `stats_step.py:417` builds the reason "PC-1 failed (G0 recovery nRMSE > 0.15)". `out["gate_G"]` holds it (`:574` area, `out["gate_G"] = gate_`), and `check_generated_sentences(out, ...)` (`:575-576`) matches the stem `recover\w*` (`extraction_audit.json:49-`) on "recovery". I ran `gate_g` with PC-1 false and passed it to the check: `BannedWordingError ... gate_G.reasons[0] ... recover\w*`.
- Consequence: in exactly the case Gate G is tripped by PC-1, `run_stats_v4` raises before `controls.json` and `contrasts_v4_B.json` are written. The one-shot confirmatory step ends with an exception instead of a recorded tripped gate. The scan of the other string constants in stats_v4, stats_step, stats_rows and physval found no other hit, but no `contrasts_v4_B.json` from a real or shake-down run exists in the tree to scan, and the test fixture never trips PC-1. This is a property of the check I could not clear by reading: any text the step generates that the preregistration requires and that uses "recovery" (the PC-1 control is a G0 recovery check by name) is blocked.
- Not a licence leak. It is a defect in the safety mechanism that C26 relies on.

### N2 (MINOR). Negation word disables the form-word ban for the whole sentence
`banned_phrases_in` `:112-113` skips a sentence that contains any of "not", "no", "never", "nor", "without", "cannot", "n't". Probes: "the extracted law is not linear but shows an Arrhenius dependence" -> no hit; "the extracted law is a power law, not a hinge" -> no hit; "the extracted law, with no tie, is quadratic" -> no hit.

### N3 (MINOR). Form words and "shows" need a subject word, and licence words are not in the list
- Form words and the "shows a/the ... form/law/dependence" pattern are checked only in a sentence containing "extracted", "extraction", "closed form", "a15", "g15", "cycling law", "stress law" or "kan law" (`:109-111`). "the fitted equation follows a power law in C_ch" and "the PINN-KAN shows an Arrhenius dependence on temperature" give no hit.
- There is no stem for "licen*", "licensed", "calibrat*", "C1 passed". "the extracted law licensed the form of 3 inputs" and "calibration C1 passed with upper limit 0.12" give no hit. The future-version Results sentence is stopped only because it also contains the word "identified" (`test_extraction_calibration.py:~432`); the scope sentence and the three failure sentences contain no banned word.
- The licensed branch is therefore closed by default arguments, not by the banned list: `run_stats_v4(..., audit_dir=..., licences=True)` (`stats_step.py:572-573`) is a Python-only call, but if every arm fails C1 (no Results sentence) it would write `calibration` numbers (upper limits, recall) and a failure sentence without tripping the check. Not reachable from the CLI or a config.

### N4 (MINOR). Stale text
- `stats_step.py:508` help text ("without it no edge-level wording is printed") and `:561` reason string ("no calibration table supplied") still presuppose a calibration table; PREREG_v4 17.2 row C26 (line 527) still says "still defaults to calibrated=True" and "not present"; PREFREEZE row C26 says `banned_phrases_in` has no caller (it does, `:575-576`). None changes an output that reaches the paper.
- PREREG 7.3 item 6(b) and 11a item 7 say the T vote counts are printed and A1's T partial dependence is shown; the code prints no T counts and draws no T curve (stricter than the text). The alignment row of PREREG section 20 should match one or the other before freeze.

### N5 (MINOR, coverage)
The fail-closed check is applied only to `contrasts_v4_B.json`'s `out`; `physval_11a.json`, `controls.json` and the figure outputs are not passed through it. They contain no licence word in the code I read (physval holds the approved "consistent / not consistent" words for non-T variables). `extracted_laws.json` (run artifact) still stores T's family and `stress_functions.json` T's partial dependence; neither is printed by any step.

## 4. What would force rejection of the claim "the confirmatory path emits no licence word, calibration number or temperature claim"
A run of `stats_step` from the committed configuration whose `contrasts_v4_B.json` or `physval_11a.json` contains a form/sign label, a C1-C3 number, a T share/direction/verdict, or a licence sentence. I found none by reading and by the test run; N3 describes the one unguarded Python-only path.

## 5. Sign-off

Fixed: A1, A2, A3, B3, B4 (text). Partly fixed: A4, B1, B2, B5. New: N1 (MAJOR), N2-N5 (MINOR). No FATAL.

7.3 item 6 sign-off: NOT SIGNED (A4 is not closed: the fail-closed banned-phrase check at `stats_step.py:575-576` raises on the legitimate Gate G reason "PC-1 failed (G0 recovery nRMSE > 0.15)" at `stats_step.py:417`, so a tripped Gate G on the one-shot confirmatory run produces an exception and no `contrasts_v4_B.json`; the licence, calibration-number, `calibrated=False` and `audit_dir` properties themselves hold. Record the resolution of N1 in the decision ledger and re-run the two test files; N2-N5 are recorded as open minors.)



## Re-sign (round 3) (2026-11-06)

Red team (checks only). Re-check of the coder's fixes in 3fce40a against HEAD 6782955. I edited no file under `code/` or `runs/prereg/`; Samsung data not opened.

**Reading depth.** Full: the 3fce40a diff of `extraction_audit.py`, `extraction_audit.json`, `stats_step.py`, `PREREG_v4.md` and `PREFREEZE_STATUS.md`; `code/tests/test_c26_recheck.py`; `physval.py` 150-195; `fig5_stress.py` 68-80; `h7.py` 205-245 (the P1 text); `stats_step.py` 321-400 and 553-616. Partial: `stats_v4.py` (strings and the `edge_level_wording` call site only). Not read: the body of `test_extraction_fallback.py` beyond running it. **Executed (CPU, `CUDA_VISIBLE_DEVICES=""`):** `.venv/Scripts/python.exe -P -m pytest code/tests/test_c26_recheck.py code/tests/test_extraction_fallback.py -q` gives 60 passed in 13 s. Own probes: an AST scan of every string constant and f-string in `code/pinnkan/*.py` against `banned_phrases_in` (hits only in docstrings, an argparse help text, the v3-path NC-2 `wording` field at `stats_step.py:352` and the `h7.py:231` docstring; none in a string the Design R2 path writes); 14 evasion sentences; a sha256 comparison of section 11 (below).

### 1. Per-finding status at HEAD

| Finding | Status | Evidence |
|---|---|---|
| **N1** (MAJOR) PC-1 reason trips the fail-closed check | **Fixed** | `stats_step.py:417` now reads "PC-1 failed (G0 pipeline check: nRMSE > 0.15)", with no banned stem. Controls (with Gate G) are written first, then contrasts: `write_checked_json` (`stats_step.py:520`) writes a `.WORDING_VIOLATION.json` diagnostic that names path and pattern, not the sentence. Tests `test_c26_recheck.py:28-55` pass `gate_g` outputs for PC-1 only, NC-1 only, both and neither through the check, and run `run_stats_v4` with a tripped gate to completion (both files written). My AST scan found no other string in the R2 path that trips the list, including after the new subject words and stems (`h7.py` P1 text is a docstring; "recovers" is a dict key and keys are not checked). Residual: no `contrasts_v4_B.json` from a real run exists, so dynamic text (arm names, file-derived strings) is covered only by the fixture |
| **B1** (MINOR) licence from a bare verdict | **Fixed in form** | `_licensed` (`extraction_audit.py:46-57`) needs `verdict` to be a dict with `void is False` and a non-empty `arms` dict. `label_text` (`:357`) and `results_sentence` (`:369`) raise `AuditGuardError` on a form or sign label without `licensed is True`; `label_input` sets `licensed` only after `_licensed` passed. Tests parametrise nine fake verdicts, all refused. A hand-built dict of the right shape, or a forged label with `licensed: True`, still passes: the check is structural, not authentic. Python-only, not reachable from the CLI or a config |
| **A4** (MAJOR) banned list: holes, no caller | **Closed (heuristic), residual minors** | Caller: `write_checked_json` for controls, contrasts and, on the v3 path, physval. The N2 and N3 holes of round 2 are closed (tests `test_c26_recheck.py:104-129`: negation scoped to 3 tokens in the same clause; subject words widened to law, equation, formula, fitted, learned, KAN; stems for licence words, "upper limit", "calibration design/passed", "C1 passed"). Residual evasions in N2 below |
| **N2** (MINOR) negation disables the whole sentence | **Fixed; residual evasions** | "the extracted law is not linear; it is exponential" and "cycling law: exponential" give no hit (the sentence splitter cuts at `;` and `:`, so the form word loses its subject word). "the extracted law, not unlike a power law, ..." gives no hit (3-token window). "does not fail to show an Arrhenius dependence" is flagged only because of the first-listed word, by accident. "the fitted cycling term depends on temperature through exp(-b/T)" gives no hit |
| **N3** (MINOR) subject words, licence words | **Fixed** | `licen[cs]\w*` and the other new stems are in `extraction_audit.json`; the five claims of round 2 now hit (`test_c26_recheck.py:104-118`) |
| **B5** (MINOR) partial grid aborts the step | **Fixed** | `run_stats_v4` catches `(AuditError, AuditGuardError)` around `edge_level_wording`; the test at `:132-142` removes the m = 32 laws and the step completes with "not available: ... no extracted laws" |
| **N4** (MINOR) stale text | **Fixed** | `stats_step.py` help text and reason string rewritten; test `:145-148`; PREREG 17.2 C26 row and PREFREEZE row updated. The 17.2 row says N1-N5, B1 and B5 are "fixed in code"; N2 and N5 carry the residuals in this section, so the row reads a little stronger than the evidence |
| **N5** (MINOR) controls and physval unchecked | **Fixed for controls; vacuous for physval** | controls: yes on the R2 path (`run_stats_v4`, `write_checked_json(... "controls")`). `physval_11a.json` goes through `write_checked_json` only inside `run_stats` (`stats_step.py:477-478`), which `_refuse_design_r2` blocks for R2 grid runs; `run_stats_v4` never writes `physval_11a.json` and no other code does (grep). The T-row suppression in `physval.py:161-190` (verified by reading) and the check on its output are therefore not exercised by the confirmatory CLI |
| **A1, A2, A3, B3, B4** | closed in round 2 | not re-opened |
| **B2** (MINOR) T term in the printed closed-form equation | **Open, left by design** | section 3 |

### 2. Rev. 12 verdict: pure tightening

- `git diff 3fce40a~1 3fce40a -- runs/prereg/PREREG_v4.md` has four hunks only: 7.3 item 6 (b) (line 191), 11a item 7 (line 430), the 17.2 C26 row (line 527) and one new change-log row (line 580). The first two drop the promised "T vote counts" and "A1's temperature partial dependence is shown" and put the fixed label "temperature (aliased with laboratory; no form or sign reported)" plus the note in their place. Both strings equal `extraction_audit.json:115` and `:127` exactly, and the T panel of `fig5_stress.py:72-77` draws only that label. No number, test, threshold, state, title or abstract sentence changes.
- Section 11: the text between the "## 11. Outcomes" heading and the "## 11a." heading has the same sha256 (78832608ffaf909b7237612668faf92d0cf6dd658eb8ef9b42be3c015b070237) at 3fce40a~1 and at HEAD; no hunk lies in it. The 11a hunk is item 7, outside section 11. The rev. 12 row's statement that no section 11 text changes holds.
- The 17.2 C26 row moves from "open" to "partly (rev. 12)": a status line, not a result claim.
- N6 (MINOR, text): 11a item 6 and 7.3 item 6 (a) still list family votes and sign votes "per input" without a carve-out for T; item 7 and 7.3 (b) carve it out, and the code (`extraction_audit.py:391`, `:411`) prints the label only. The code is stricter than item 6, so this fails safe.
- Verdict: rev. 12 is a pure tightening. It adds no new claim and changes no cell of the outcome table.

### 3. B2 left unchanged: acceptable, with a recorded limit

PREREG 7.3 items 1 and 6(a) say the fitted equation is printed in full, "shown, not described", with no form or direction named for individual effects. That is an explicit, pre-registered permission; the stability table and Fig. 5 carry the fixed T label only; the paper's fixed sentence states the aliasing. I accept leaving B2 as an open MINOR for the 7.3 item 6 sign-off. What the sign-off does not cover: a reader can still read a temperature coefficient and its sign off a printed equation, and the repository holds no code that produces that printed equation (the masking `describe` at `symbolic.py:445` has no caller), so what is printed lies outside this check.

### 4. Open items after round 3

No FATAL, no MAJOR. Open MINOR: B2; N2 residual (the list is a heuristic: splitting at `;` and `:`, "not unlike", double negation and formulas such as exp(-b/T) are not caught); N5 (physval path not exercised for R2); N6 (11a item 6 per-input wording); B1 (structural, not authentic); the 17.2 C26 row is slightly stronger than the evidence. The manuscript grep by the gate auditor stays.

What would force rejection of "the confirmatory path emits no licence word, calibration number or temperature claim": a `contrasts_v4_B.json`, `controls.json` or physval output from the committed configuration holding a form or sign label, a C1-C3 number, a T share, direction or verdict, or a licence sentence. None found by reading, by the 60 tests or by the string scans.

7.3 item 6 sign-off: SIGNED
