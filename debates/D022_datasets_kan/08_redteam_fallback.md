# D022b C3: red-team check of the fallback (2026-11-05)

Red team (checks only). Scope set by the lead: (1) can any path still print an identified-form or licence claim, or a temperature claim, in the confirmatory outputs; (2) does the banned list cover the D022 section 4 claims; (3) does the K1/K2 contribution text of PREREG 7.3 item 3 overclaim.

**Reading depth.** Full text: `07_judge_recheck.md`; `code/pinnkan/extraction_audit.py` (v2 plus the a3a8f7f diff) and `extraction_audit.json`; diffs of `stats_step.py`, `stats_v4.py`, `extraction_calibration.py` in a3a8f7f; PREREG_v4 7.3 items 1-6, 11a items 5-10 (rev. 7); `code/pinnkan/physval.py` lines 150-210; `D021_cap_synth/decision.json`; `D021_cap/01_architect.md` sections 1-4 (partial). Partial: `fig5_stress.py` (grep), PREREG section 11 claim sentences (grep lines 384-396), tests (names; the file passes: 29 passed in 15.9 s, run by me). Executed by me: the 29 audit tests, `_licensed` and `banned_phrases_in` on probe strings (identifier-free). No calibration was run; no data value was opened.

**Result.** No FATAL. 4 MAJOR, 5 MINOR. The default statistics path emits no licence word, no label and no calibration number, and T is never labelled. Four things still carry the claims the fallback was meant to remove.

---

## 1. Paths that can still print a licence or a temperature claim

### What holds (checked)
- `run_stats_v4` with `audit_dir=None` returns `edge_wording = {printed: False, ..., stability: <descriptive table>}`; the stability table is `audit_arm(laws, arm)` with `calibrated` defaulting to `False` (`extraction_audit.py:329-330`; `stats_v4.py:599-603`), so it holds family counts, sign votes, tie share, additivity share, not-retained share, and a note for T. It has no label, no "identified", no calibration number.
- `audit_dir` supplied without `licences=True` raises `AuditGuardError` (`stats_step.py`, diff), and the command line has no `licences` option, so the confirmatory command cannot reach the licensed branch.
- `label_input`/`label_law`/`audit_arm` default to `calibrated=False`; a bare `True` raises (`:46-53`, verified by me); T cannot receive a form or a sign even with a valid calibration (`:256-258`).
- The calibration script refuses a real run without `--future-version` (`extraction_calibration.py`, diff) and passes a sentinel when scoring.

### MAJOR A1. The permanent temperature rule is scoped to A15 and G15; the learned-law temperature direction and a "consistent / not consistent" verdict are still produced
- `physval.py:154-175` (`cyclic_directions`, `compare_with_a10_signs`) loops over every stress variable `M["cyc"]` with no exclusion of `T_C`, and `physval_11a` (`:195-202`) writes `item5.directions` (share increasing/decreasing, direction of the mean curve, envelope) and `item5.vs_A10` with `verdict = "consistent" | "not consistent"` per variable. These are the learned stress functions of the PINN-KAN members (A1), not the extracted laws.
- PREREG 7.3 item 6 (b) and 11a item 7 bar a T direction "from A15 or G15"; 11a item 5 (unchanged, line 428) is written for all "cyclic partial dependences"; 11a item 9 bars only "an Arrhenius statement for the cycling term". The judge's reason for the ban (07 section 1, N1(a)) is the laboratory confound of 35 C, which applies identically to A1's learned temperature effect. Fig. 5/6 panels plot the A1 partial dependence of every stress including T and an "A10, cyclic direction" line (`fig5_stress.py:88-92`).
- Failure scenario: the paper prints "the temperature effect of the PINN-KAN is consistent with the dataset authors' cycle model" from `physval_11a.json`, a temperature claim read from a cycling law whose temperature is aliased with laboratory, while the text says no T direction is read anywhere.

### MAJOR A2. The unlicensed output still carries a scope sentence that asserts a calibration that was not run
- `extraction_audit.py:330` returns `scope_sentence` in the descriptive (unlicensed) branch; its text is unchanged in `extraction_audit.json`: "The extraction rule, its thresholds and the calibration design are fixed by the frozen commit and verified by re-run." Under the fallback there is no calibration design and no re-run. The sentence is emitted into `contrasts_v4_B.json` (via `edge_wording.stability.arms.*.scope_sentence`) on every confirmatory statistics run that holds extracted laws.
- `extraction_audit.json` also keeps `results_sentence` ("the audit licensed the form of {j} ..."), `not_identified_input` ("the audit does not license ...") and `failure.*` ("The extraction audit did not meet its pre-set ... condition"). They are unreachable from the statistics step today, but they are in the file the paper's writer is told to take sentences from. The failure sentences in particular describe a calibration that never ran.

### MINOR B1. "Verified calibration" is not verified by `_licensed`
`_licensed` (`:46-53`) accepts any `dict` and the public sentinel `CALIBRATION_RUN`; I confirmed `_licensed({})` returns `True`. The check blocks the accidental `True`, not a deliberate or half-accidental call (`label_law(laws, calibrated=cal)` with any dict). `label_text` and `results_sentence` are unguarded: `results_sentence` on unlicensed labels prints "the audit licensed the form of 0 and the sign of 0; 5 were not identified". With `licences=True` the only gate is `require_calibration`, whose weaknesses (verdict not recomputed from records, unpinned lab map, omission undetected; 06 N2, N3) are unchanged and now unused.

### MINOR B2. Temperature statements that remain by design
The stability table prints T's family counts and sign votes (with the note); the closed-form law prints T's term; Fig. 5 plots T's partial dependence. PREREG allows the T vote counts (11a item 7) and the formula. A reader sees "T_C: log 25" or "+ 0.3 ln T" regardless of the sentence "no T direction is read from A15 or G15 anywhere". The rule is a wording rule for the text, not a property of the outputs.

### MINOR B3. PREREG 7.3 item 1 contradicts item 6
Item 1 still says the fitted equation may be printed "(for example a term linear in log C_dch) in full", which is the example of a named form, while item 6 says "no form or direction is named for its individual effects". One of the two will be quoted in the Methods.

### MINOR B5. The descriptive path can abort the statistics step
`stats_step.py:559-560` calls `edge_level_wording(run_dirs)` whenever any run holds `extracted_laws.json`; `collect_laws` then enforces exactly 25 laws per arm (`AuditError`). In strict mode the grid is complete beforehand; in `--lenient` or partial-grid use, an incomplete A15 or G15 set raises after the contrasts are computed and before `contrasts_v4_B.json` is written (`:561-563`).

---

## 2. Banned list versus the D022 section 4 claims

`extraction_audit.json` `banned_phrases` (14 entries; matching by `banned_phrases_in`, `:85-88`, word boundaries, case-insensitive). Probe results (run by me):

| Claim of 03 section 4 / PREREG 7.3 item 1 | Caught? |
|---|---|
| "recovered", "discovered" (exact forms) | yes |
| "recovers", "discovers", "discovery" | **no** |
| "shows" an Arrhenius / power-law / exponential / quadratic / hinge | only if the sentence also contains Arrhenius, power law or hinge; "shows an" is not matched by "shows a"; "shows the form" not matched |
| "power law" | yes; "power-law" (the form 7.3 item 1 itself uses), "power\nlaw" (LaTeX line break) **no** |
| "exponential", "quadratic" | **no** |
| "identified", "identifiable", "identifiability" (7.3 item 6 (a): "Not reported ... 'identified', 'identifiability'") | **no** (only "structurally identifiable", "structural identifiability", "more/better/fewer identified") |
| "activation energy" from the cycling law | **no** |
| "non-monotone" / "non-monotonic" SOC | **no** |
| "Arrhenius", "hinge", "threshold" | yes, with large false positives (below) |

### MAJOR A4. The list has holes, false positives on required text, and no caller
- Gaps as in the table. The ban is on "claims", and a phrase list cannot see the verb forms and variants listed.
- False positives on text the PREREG requires: 7.3 item 1 says the paper states the superset library (quadratic, power, exponential, Arrhenius, hinge) and the cap; 11a items 1 and 3 and the calendar figure use "Arrhenius" for A10's parameter and the monotonicity control P2; "threshold" occurs in any state-of-health or end-of-life definition. The grep will flag legitimate sentences, which in practice leads to the grep being waived, and the real claim sentences are then not separated from the legitimate ones.
- `banned_phrases_in` has no caller outside the tests (grep of `code/`): it is not run by the figure build, the paper build or any check. The 07 ruling keeps it as a manual gate-auditor grep, so the coverage claim "carries the claims of 7.3 item 1" in PREREG 7.3 item 6 (c) is not a property of the pipeline.

---

## 3. PREREG 7.3 item 3: does the K1/K2 contribution text overclaim?

### MAJOR A3. The cap justification is circular on its headline number and omits two D021 flags
- Item 3: "the cap that makes the law compact is justified ... by the D21 synthetic false-structure study (37 of 40 linear-truth edges given false structure at cap 3, 0 at cap 2)". The "0" is definitional: D021 architect section 2 states the cap is a three-way switch and cap 2 leaves only {zero, linear, log}, so a 3-coefficient family on a linear-truth edge cannot be selected; the repository's own regression test says "cap 2: no 3-coefficient form exists" (`test_extraction_audit.py`). The study therefore shows what cap 3 does, not that cap 2 is free of false structure. Linear-versus-log confusion, which the study does not count as false structure, is exactly what the red team and judge found to decide the cap-2 labels (06 M4, N1(b)).
- The held-out accuracy evidence that does discriminate is thin and is not mentioned: D2 on G0 at m = 32 has cap 3 worse than cap 2 by 0.0168 with a 95 % upper bound of 0.0210 against the 0.02 threshold (`decision.json`); at m = 8 on G2 the entry is NaN. The D4b guard on A15/G15 symmetry at cap 2 was **flagged**: A15 h = 1 minus G15 = +0.0225 (m = 32) and +0.0225 (m = 8), above the 0.02 limit (`decision.json`; `01_architect.md` line 45). Item 3 reports the supportive count only.
- "Reported as a synthetic methods result with the generator caveat" is right as far as it goes; the sentence "justified by" is stronger than a definitional zero plus a 0.021-against-0.02 margin supports.

### MINOR B4. "Equally simplified" and the K2 reading
Item 3 and the claim sentences of section 11 (lines 384-396, a block the PREREG says is copied byte for byte) call G15 "an equally simplified additive law". It is simplified by the same procedure; it is not equal in size or in extraction loss (A15 with h = 2 has twice the edges, D021 section 3 point 5; D4b above shows the cap-2 extraction costing A15 h = 1 more than G15 on additive truth). Item 2 prints the coefficient counts beside K2, which is the right mitigation; the D4b flag is not printed with it. A K2 outcome of K= or K- is then open to the reading "composition does not help" when a pre-known extraction asymmetry is also in play.

### Statements in item 3 that are fine
"Scored on Test B conditions that the extraction never saw" matches the split design; the contribution is stated as a test, not as a new KAN; the item ends "The paper has no audit contribution bullet"; item 6 (e) keeps "new KAN"/"first" conditional on the novelty repeat check. The "NOVEL 0.60" rating is an auditor's confidence quoted inside the PREREG and must not be carried into the manuscript as "novel". "Readable" (titles T1, T4, T7 in K+) now rests on "a short closed form that can be written out", which is true and says little; the Discussion sentence of 11a item 10 states exactly that, so it is not an overclaim.

---

## 4. Items not changed by the fallback
- BLINDING_LOG versus Test B membership (m7): still open with the gate auditor (07 section 2).
- `run.py` still requires the thresholds and rule-v2 hashes as config keys for real-data confirmatory runs with A15/G15 (`run.py:197-205`), so the frozen config hashes depend on files of a struck audit. Harmless; noted.

## 5. Sign-off for C3

No FATAL. The fallback path is clean at the code level for licence words and labels. Recorded as open for the orchestrator: A1 (T direction and verdict in `physval` item 5), A2 (scope sentence and unreachable licence sentences in the shipped wording), A3 (cap justification), A4 (banned list). MINOR: B1-B5 (B4 above; B2, B3, B5 as listed).
