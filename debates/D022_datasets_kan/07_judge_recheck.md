# D022b judge: ruling on the red-team re-check of the revised audit (2026-11-05)

Judge: the D022 judge (independent of the code; I wrote 03 section 2 and 05, which are under review here). CONTRACT section 3 item 7.

**Reading depth.**
- Full text: `debates/D022_datasets_kan/06_redteam_recheck.md` (ba67242).
- Code, by grep and the lines read: `code/pinnkan/extraction_audit.py` (signatures of `label_input`, `label_law`, `stability_table`, `banned_phrases_in`), `code/pinnkan/stats_step.py` lines 524-561 (the `audit_dir is None` path), `stats_v4.py` line 591.
- Status of the KAN-law test: `debates/D016_roles/03_novelty_recheck.md` row (iii).
- I rely on the red team's file:line citations and its geometry computations as reported.
- No calibration has been run. No data value was opened.

---

## 0. Verdict

**Fallback now.** The extraction audit is not run as a calibrated contribution in this submission. The ~18 CPU-h (33 at the ceiling) calibration is not run.

- The extracted cyclic laws are printed in closed form, with a descriptive per-input stability table and no form or sign licences.
- The paper has no audit contribution bullet.
- The KAN-side contribution is the one rated NOVEL (0.60) in `03_novelty_recheck.md` row (iii): the held-out test of the closed-form law extracted from the KAN against an equally simplified additive law (K1, K2). The cap that makes this law compact is justified in Methods by the D021 synthetic false-structure study (37 of 40 linear-truth edges given false structure at cap 3, 0 at cap 2).

**Why now, and why this is not outcome tuning.** No calibration fit exists. The decision rests on what the labels would claim and on what the design contains, not on any result.

1. **(a)-(c) can be fixed, but a fourth mechanism remains and no rule can fix it in this design.**
   - The labels claim that the training design lets the extraction tell an effect's direction or form apart.
   - The Samsung design aliases laboratory with temperature: 35 C is INT in all 13 pinned conditions, and 45 C is HM in 12 of 15 (06 N1(a), from identifier columns).
   - The extraction has no laboratory term. A laboratory offset is therefore systematic bias, shared by all 25 laws (folds share most of their conditions; seeds share the data). A stability vote cannot detect it.
   - Removing T from the licences (fix (a)) does not remove the bias from the other inputs, to the extent that their levels are unbalanced across laboratories.
   - The calibration's pass or fail would then be set by an invented parameter, the laboratory-offset sd of 0.15 (06 M3, n8). So a pass would be weak evidence and a fail uninformative about the method.
2. **C3 is nearly automatic** (06 n4): the stability-only baseline fails C1 for the same reasons. So even a pass would not show that the audit's own rules matter.
3. **Cost.** A further round (label semantics, parent-lack-of-fit evidence, the laboratory map pinned from FROZEN, omission control, red-team re-check) costs about another day of code and half a day of review. That is beyond the lead's limit of about 2 days counted from 05, for an outcome the red team predicts from the code as most likely a fail (06 N1, labelled a prediction).
4. **The fallback is the conservative default** that the plan already carries (05 section 5; PREREG 17.4). It removes no scored arm and no claim of the D017/D019 table.

**Answer to the author, updated.** The KAN novelty in this paper is the tested closed-form KAN stress law: it is extracted under a cap that a synthetic false-structure study justifies, and scored on held-out conditions against an equally simplified additive law. No identifiability-audit claim is made.

---

## 1. Rulings on the new findings

| ID | Remedy | Ruling | Reason |
|---|---|---|---|
| N1(a) | Never license a T sign in the cycling law | **ADOPT** (permanent, in any version) | It follows from 11a item 9 and 03 section 4: no temperature statement for the cycling term, because of the laboratory confound. Under the fallback this means no T direction is read from A15/G15 anywhere. 11a item 7 prints the T vote counts with "temperature and laboratory cannot be separated" and no consistency word. |
| N1(b) | Score each label against what it asserts (form = "approximately F over the hull"; sign = "monotone with that direction"), and license a form only with parent lack-of-fit evidence | **ADOPT in principle; not built now** | This is the right semantics for any future version. A cap-2 extracted PD is library-exact, so evidence of shape must come from the parent. Moot under the fallback, where no form is licensed. |
| N1(c) | G15 symmetry on interacting inputs | **ADOPT in principle** (both arms' labels assert the effect *at the centre of the other stresses* and are scored against the truth at the same point; additivity disclosed as G15's built-in assumption); **REJECT** a separate A15-only criterion | A criterion only one arm can meet breaks the K2 symmetry that the whole K chain rests on. Moot under the fallback. |
| N2 | Pin the laboratory map from the FROZEN commit | **ADOPT for any future calibration**; moot now | Any re-run (revision) must build the map from the post-QC included cells of PREREG 3.3, written to a tracked file pinned by FROZEN. |
| N3 | Prefix rule; recompute the verdict from records; label functions default `calibrated=True` | **ADOPT**: the default part **now**, the rest for any future calibration | Now: `label_input`/`label_law` default `calibrated=False` and refuse to emit a licence word without a verified calibration, so no script can print a licence by accident. For any future run: datasets must form the prefix 0..D-1, with missing ones recorded; `finalize` runs once; the verdict is recomputed from the records by the stats step and by the gate auditor. |

## 2. PARTLY and OPEN items (from 06 section 1)

| ID | Ruling under the fallback |
|---|---|
| M3 (strata realism) | Moot. It is recorded for any future version: offset sd sensitivity, offsets on storage cells, tuned rather than uniform hyperparameters. |
| M4 (geometry-only form test) | Moot. N1(b) is the fix if the audit returns. |
| M5 (additivity blind for G15) | Moot. N1(c) is the fix if the audit returns. |
| M7 (guard) | (a) fixed now via N3; (b) and (c) for any future version; (d) **now**: the banned-phrase list in `extraction_audit.json` gets the 03 section 4 claims ("recovered", "discovered", "shows a", "power law", "Arrhenius", "hinge", "threshold", "no effect") and a word-boundary match, so "unenforced" is not hit (n6). The gate auditor still runs the grep before submission. |
| m4, m5 | Moot (the calibration is not run). n1 (torn-write resume) is recorded for any future run. |
| **m7** (pilot constants traced to Test B cells) | **Stays OPEN and stays with the gate auditor.** It concerns the generator constants that PC-1 also uses, so it does not go away with the audit. If any of the 19 pilot cells is a Test B cell, the PC-1 circularity sentence in Limitations says so. |

Minor n3 (wording), fixed **now**: the Discussion sentence becomes *"Readable means that the extracted law is a short closed form that can be written out and evaluated; we name no form or direction for its individual effects."* The 11a item 10 Results sentence is struck. The stability table prints vote counts under the caption *"descriptive; not evidence that the training design identifies these forms"*.

## 3. What the paper reports under the fallback (binding)

- **Methods.** The cap and the D021 synthetic false-structure study, as a synthetic methods result with the generator caveat.
  - The extracted law: library, BIC on the KAN's grid, cap 2, refit.
  - The sentence: "we do not name forms or directions of individual extracted effects, because the training design aliases laboratory with temperature and the extraction has no laboratory term".
- **Results.** A15 and G15 printed in closed form at g4 (and g1 descriptive), K1/K2 as in the table, and the 11a item 6 stability table. Per input it gives the family votes over the 25 fold-by-seed laws, the tie share, the additivity share and the sign votes, for A15 and G15 side by side, with no licence words and no comparative wording between the arms.
- **11a item 7.** Sign votes beside A10's exponent signs, labelled "consistency with same-data models". For T only: "temperature and laboratory cannot be separated".
- **Not reported:** any calibration number, "identified", "identifiability" (except in the sentence above), or an audit contribution bullet.
- 03 section 4 bans are unchanged.

## 4. Actions

| # | Action | Owner | File |
|---|---|---|---|
| C1 | Set `calibrated=False` as the default; a licence word without a verified calibration raises; extend the banned-phrase list with word-boundary matching; Discussion sentence and stability-table caption per section 2; tests for both; the confirmatory configuration passes no `audit_dir` (the existing `stats_step.py:557` path); the calibration script stays in the tree, inert, and is not in the run list | coder | `code/pinnkan/extraction_audit.py`, `extraction_audit.json`, `code/tests/test_extraction_audit.py`, run configs |
| C2 | PREREG_v4: strike the licensing part of 7.3 item 6 and 11a item 10 by a change-log row (D022b); keep the stability table under 11a item 6; T rule in 11a item 7; C26 struck (fallback recorded); remove the calibration run from 15; 17.4 states that the fallback applies; 19.1 row | experiment-designer | `runs/prereg/PREREG_v4.md` |
| C3 | Short check that the fallback path emits no licence word or calibration number in any stats output and that the C1 tests pass; sign 7.3 item 6 as struck | red team | `debates/D022_datasets_kan/08_redteam_fallback.md` |
| C4 | Methods and Discussion text per section 3; no audit bullet; the KAN contribution bullet is the K-chain test with the cap justification | manuscript writer | `paper/draft/` |
| C5 | m7 check (BLINDING_LOG against Test B membership) and banned-phrase grep before submission | gate auditor | `research/audits/` |
| C6 | Tell the author the updated KAN answer (section 0) | lead | status file |

## 5. Re-open if
- Shlok asks for the audit as a contribution and accepts the delay. It then returns as a new version with the N1(a)-(c) semantics, a laboratory-aware licence (for example within-laboratory sign agreement where a laboratory has at least two levels of the input), the N2 pin, the N3 omission control, an offset-sd sensitivity, and a red-team re-check, all fixed before any calibration fit.
- A reviewer asks for an operating characteristic of the extraction. The v2 code in the frozen commit may then be run descriptively for the response letter, with the n8 mixture caveat and no licence.
- The novelty repeat check finds the K-chain test (03_novelty_recheck row iii) already published.
