# D022a judge: revision of the extraction audit after the red-team review (2026-11-05)

Judge: the D022 judge (independent; I wrote 03_judge.md section 2, which the red team attacked, and none of the code). CONTRACT section 3 item 7.

**Reading depth.** Full text: `debates/D022_datasets_kan/04_redteam_audit.md` (commit bd67bd3), `calibration_rule.md`, `code/pinnkan/extraction_audit.json`; `runs/build_v2/CHOICES.md` items on the audit (grep). Partial: `runs/prereg/PREREG_v4.md` 7.3 items 1 and 6, 11a item 10, 15, 17.2 C26, 17.4 (grep plus the lines read); `runs/D021_cap_synth/log_p0.txt` and `log_p1.txt` (pipeline times only). Not read: the audit code itself. Where I rely on a red-team code citation (file:line), I accept it as reported; the coder must confirm each before fixing it.

**My computations** (no data): one-sided 95 % Clopper-Pearson upper limits (scipy); the mean and maximum of the 135 D021 pipeline times (43.2 s and 79 s, from the two logs). Every threshold below is a design choice fixed before any calibration result. No calibration has been run.

---

## 0. Verdict

**Both FATAL findings are upheld.** As built, the audit is not calibrated for the label it prints (F1), and no outcome could falsify it as a contribution (F2). My 03_judge.md section 2.2 caused both:
- It bounded a per-law rate while licensing on a 25-law vote.
- It compared point estimates with 0.10.
- Its re-open item 5 turned failure into a "negative finding".

**Ruling.** The audit can be made credible. The red team's single change is adopted in a modified form: calibrate the full printed label on whole synthetic datasets, with out-of-library, non-additive, weak-effect and laboratory-aliased strata, a family-wise bound with an upper confidence limit, and a usefulness-and-necessity floor fixed now.

**Cost.**
- About 1 to 1.5 days of code and red-team re-check before the freeze. This is an estimate, not a measurement.
- About 18 CPU-h expected (33 CPU-h ceiling) of calibration after FROZEN (section 3).
- The calibration need not precede the first outer score (section 2.8), so it does not hold up the confirmatory grid.

**This is within the lead's 2-day limit.** If the lead will not hold the freeze for it, the fallback of section 5 applies: no labels, no contribution bullet, a descriptive stability table only.

**The contribution is now conditional, and it can fail.** It stands only if the calibration shows the audit is calibrated, useful and necessary (section 2.6). Otherwise it is withdrawn by rule.

03_judge.md section 2.2 (a) item 3, section 2.2 (c) and section 7 item 5 are **superseded** by this file. The rest of section 2 stands where it does not conflict.

---

## 1. Dispositions

| ID | Finding (short) | Disposition | Reason / what changes |
|---|---|---|---|
| **F1** | Per-law rate calibrated; 25-law vote licensed; n_eff about 4; point estimate | **ADOPT, modified** | The unit of calibration becomes the **synthetic dataset**, run through the real procedure (5 folds x 5 refit seeds, the same label code). The bound is an upper confidence limit on a dataset-level, family-wise error (2.4). I **reject** "independent truth draws per fold": on the real data one truth is shared by all folds, and the calibration must copy that dependence, not remove it. The dataset as the unit counts it correctly. |
| **F2** | Always-abstain satisfies everything; no usefulness floor; failure pre-written as a result | **ADOPT** | Three pre-set conditions: calibrated, useful (a recall floor) and necessary (beats a stability-only baseline) (2.6). Failure withdraws the contribution bullet. 03 section 7 item 5 is deleted. Predictions fixed now: T can at best receive a sign label (linear and log tie on its hull, M4), and the level rule never binds (M8). |
| M1 | Pooled false-family rate (effective 0.20); point estimate; multiplicity | **ADOPT, modified** | The licence bound is family-wise over all statements printed for a dataset, so it cannot be diluted by easy truth classes. A point estimate is never compared with a bound. Per-stratum rates are printed with intervals as descriptive rows and license nothing. One bound per arm means one test per arm, not 54 cells. |
| M2 | Closed world; sign and pruned labels uncalibrated | **ADOPT** | Out-of-library strata (quadratic, hinge) and non-additive datasets enter the licence count. Sign licences on zero-truth or symmetric-quadratic inputs count as false. "Pruned" is no longer a claim about the truth: it is printed as "not retained by the extraction (below its tolerance)", never as "no effect", and its false-zero rate by amplitude band is printed descriptively. |
| M3 | Design-matched only on stress vectors; no lab aliasing; default hyperparameters; one amplitude | **ADOPT, modified** | Laboratory offsets go on the real laboratory map (aliased with T) in every dataset. Amplitudes are drawn per input over a range that includes weak effects. Hyperparameters, including A15's h, are drawn per (dataset, fold) from the tuned spaces of 7.1. This marginalises over the space rather than reproducing inner-CV tuning, which would multiply the cost by the trial count; disclosed. Noise, fade level and check-up cadence stay at PREREG 13 values (Limitations). |
| M4 | Family decided by floor and list order; stability trivial for T; BIC margin is not evidence | **ADOPT** | Labels are read from the extracted law's partial dependence, with an explicit tie rule (2.3). A tie gives no family. The BIC-margin column leaves the main table; it moves to the appendix with the caveat "computed on the KAN's grid, not a data statistic". A tie-share column is added. |
| M5 | A15 and G15 can express different labels | **ADOPT** | One label function on the partial dependence of any extracted law, with a numerical additivity test applied to both arms (2.3). G15 is calibrated on the same non-additive datasets as A15. No comparative wording between the arms' label counts (2.7). A15's h is marginalised in calibration and in the vote alike, so the mixed-variant worst-cell rule is removed. |
| M6 | A15 h = 1 always called additive | **ADOPT** (bug) | Replaced by the numerical additivity test. Unit test: A15 h = 1 with a log outer edge is non-additive. |
| M7 | Forgeable guard; mtime ordering; optional pin; calendar KAN unguarded | **ADOPT, modified** | Content control replaces time control (2.8): the calibration records the FROZEN SHA, rule and thresholds hashes, and the gate auditor re-runs a hash-seeded sample of datasets bit-identically. The thresholds pin is mandatory whenever edge wording is requested. `calibration_sha256` is a stats-step argument. The calendar extracted law gets no edge-level wording at all, refused by the stats step. Banned-word grep before submission. The paper's scope sentence says "fixed by the frozen commit and verified by re-run", never "enforced". |
| M8 | Level rule inert on Samsung; Raue-style terms borrowed | **ADOPT** | The paper states that every input has at least 3 training levels, so the level condition does not bind. The constant "identifiable parameters" column is dropped. The audit is called a **calibrated extraction audit**. "Identifiability" is used only in the sense "whether the training design lets the extraction tell the forms apart, as measured by calibration". No structural-identifiability claim, and Raue et al. are cited as background only. The distinction from Sovrano et al. now rests on the calibrated family-wise bound, abstention and the baseline comparison. |
| m1 | Approximation flag reference | **ADOPT** | Each arm is compared with its own parent (symmetric; this measures extraction loss). Renamed "extraction-loss flag". `approx_flag_min_share` 0.5 written into PREREG. No licence effect. |
| m2 | Dead sign check; ties go to + | **ADOPT** | A tie in sign votes gives no sign label. |
| m3 | Silent skips, unused key, missing h | **ADOPT** | Requires exactly 25 laws per arm at g4, otherwise an error. An unknown arm or a missing h is an error, never a silent default. `fold_by_seed_g4` is used for that check. |
| m4 | Assembly duplicates, torn line, minimum n not enforced | **ADOPT** | De-duplicate on the (dataset, arm, fold, seed) key; tolerate a torn last line on resume; enforce the minimum D of 2.5. |
| m5 | Script does not check pins; untracked files invisible | **ADOPT** | The script checks both pins. The calibration run uses `verify_freeze` with untracked files included under `code/`. |
| m6 | Sign read at the midpoint for non-additive inputs | **ADOPT** | A sign label requires additivity (2.3). |
| m7 | Generator constants may trace to Test B cells | **ADOPT as a check** | The gate auditor checks BLINDING_LOG against Test B membership. If any pilot cell was a Test B cell, Limitations says so. |

---

## 2. Revised audit rule (exact; replaces 03 section 2.2 (a) item 3 and (c))

### 2.1 Scope
- Labels are licensed **at g4 only** (m = 32, k_full), where the real procedure yields 5 folds x 5 seeds = 25 extracted laws per arm.
- At g1 the per-input table is printed without labels (descriptive).
- Arms: A15 (h as tuned per fold) and G15.
- Inputs: the five cyclic inputs.
- **The calendar extracted law is printed as a formula only.** No form, sign or "pruned" wording about its edges. The stats step refuses calendar edge wording. 11a items 1 to 3 stay on A1's learned calendar KAN, with their existing caveats.

### 2.2 Per-law quantities (the same function for every arm, computed on the extracted law)
For input i:
- **PD_i**: the partial dependence of the extracted cyclic log-rate on x_i, with the other inputs at the hull midpoint, on 41 points of the fold's training hull.
- **r_lin, r_log**: the RMS residuals of the best linear-in-x_i and linear-in-log(x_i) fits to PD_i, as fractions of the PD_i range.
- **A_i, the additivity indicator**: the maximum absolute mixed second difference of the law's log-rate over a 5 x 5 grid of (x_i, x_j), for every j != i, is <= 0.01 of the PD_i range.
- **Retained**: PD_i range > 0, i.e. not every edge of input i is zero.

### 2.3 Label rule (applied to the 25 laws of one arm)
1. **"not retained (below the extraction tolerance)"**: input i is not retained in at least 20 of 25 laws. This is not a claim about the truth.
2. **"composed: no single form"**: A_i fails in more than 5 of the 25 laws.
3. **"form: F"**, F in {linear, log}: all four conditions hold.
   - (a) A_i holds in at least 20 of 25 laws.
   - (b) In at least 20 of 25 laws F *strictly wins*: r_F <= 0.01 and r_other > 0.01. If both residuals are <= 0.01 it is a **tie**, and a tie never counts for either family.
   - (c) The same F in all of those laws.
   - (d) The arm's calibration passes (2.6 C1).
4. **"sign: +/-"**: all four conditions hold.
   - (a) A_i holds in at least 20 of 25 laws.
   - (b) PD_i(hi) - PD_i(lo) has the same sign, with magnitude > 0.01 of the range, in at least 20 of 25 laws.
   - (c) There is no tie between + and - votes.
   - (d) The arm's calibration passes.
   - A form label implies the sign label.
5. **Everything else: "not identified by the audit"** (abstention). The law is printed in full.
- Retained thresholds (0.8 of laws, 0.01 tolerance) are design choices. The calibration now measures their consequence instead of assuming it.
- Prediction stated now: on the 23-45 C hull linear and log tie on T (the red team computed 0.27 % of range), so T can at most receive "sign".

### 2.4 Calibration design (runs from the FROZEN commit)
- **Unit = one synthetic dataset d.** One truth for all five inputs, shared by every fold, generated on the real Samsung design: the training cycling identifiers of each outer fold at m = 32 from `subsets.json`, and the 19 storage identifiers. It is run through the real procedure: per fold, `arms.SymbolicArm` with refit seeds 0-4, giving 25 laws per arm. Labels come from the same function as on real data.
- **Per-input truth strata** are rotated so that over D = 30 datasets each input meets each stratum 6 times: stratum of input i in dataset j = `S[(j + i) mod 5]`, S = (zero, linear, log, quadratic `A(2u^2 - 1)`, hinge `A(2 max(0, u - 0.2)/0.8 - 1)`), with u the hull coordinate in [-1, 1]. The sign alternates with (j + i) parity.
- **Non-additive datasets**: j = 0, 3, 6, ..., 27 (10 of 30) add an interaction A_int u_p u_q. The pair (p, q) runs through the 10 input pairs, once each.
- **Amplitudes**: A and A_int are drawn per (dataset, input) log-uniformly on [0.05, 0.5]. 0.5 is the PREREG 13 value; 0.05 represents a weak effect.
- **Laboratory aliasing**: an offset per laboratory, drawn N(0, 0.15^2) on the cyclic log-rate (sd equal to TAU), assigned by each condition's real majority laboratory (identifiers). Temperature and laboratory are therefore aliased exactly as in the design.
- **Hyperparameters**: drawn per (dataset, fold) uniformly from the tuned spaces of 7.1 (A15: h {1, 2} and A1's other five dimensions; G15: the A4 space). Fixed noise, offsets and fade follow PREREG 13.
- **Seeds**: the dataset seed is `SeedSequence([20261105, crc32("calib2|d<j>")])`, with derived streams for amplitude, offsets, hyperparameters and noise. The parent and refit seeds are 0-4, as on real data.
- **Stability-only baseline** (same fits, no extra cost): a family is named when at least 20 of 25 laws choose the same extracted edge family, by list order as the extractor does; a sign is named when at least 20 of 25 agree. No tie, additivity or calibration conditions.

### 2.5 Scoring of a dataset (fixed now)
A printed statement is **false** if any of the following holds:
- a form F is licensed and the input's truth is not F (zero, the other family, quadratic, hinge, or an input in the dataset's interaction);
- a sign is licensed and the truth's hull-averaged slope is zero (zero truth, or the symmetric quadratic) or has the other sign;
- for interacting inputs, a sign is licensed and differs from the sign of the hull-averaged slope of the truth.

"Not retained" and abstentions are never false statements. **E_d = 1 if dataset d has at least one false statement for that arm.**

D = 30 datasets per arm, run in a fixed order. Results are computed once, at the end. If the CPU cap of section 3 stops the run, the verdict is computed on the completed datasets, provided at least D = 22 are complete; otherwise the calibration is void and section 5 applies.

### 2.6 Bound and usefulness floor (the conditions under which the audit is a contribution)
- **C1, calibrated (per arm).** The one-sided 95 % Clopper-Pearson upper limit of P(E_d = 1) is <= 0.20.
  - My arithmetic: at D = 30 at most 2 datasets with a false statement pass (upper limits 0.095, 0.149, 0.195 for 0, 1, 2); at D = 22 at most 1 (0.127, 0.198).
  - Read as a guarantee on the whole printed table of a law, not on one edge. With up to ten statements per dataset, it is stricter than a per-statement 0.10.
  - **If C1 fails for an arm, that arm prints no form or sign label on the real data.**
- **C2, useful (per arm).** Among the (dataset, input) events on the four many-level inputs (soc_mid, dod, c_ch, c_dch) whose truth is linear or log and not in an interaction, the share where the audit licenses the correct form is >= 0.5 (point estimate; usefulness floor, not a guarantee).
- **C3, necessary (per arm).** The stability-only baseline fails C1 on the same datasets. If the baseline passes C1, a stability vote suffices and the audit adds nothing.
- **Consequence.** The audit is the paper's KAN-side contribution only if C1, C2 and C3 hold for G15 and for A15.
  - If any fails, the contribution bullet is withdrawn.
  - The audit and calibration tables go to an appendix as a descriptive report.
  - Labels are printed only for arms that passed C1.
  - The Discussion states which condition failed, in one fixed sentence: *"The extraction audit did not meet its pre-set [calibration / usefulness / necessity] condition, so it is reported as a description, not as a method result."*
  - This is a stop, not an alternative finding.
- **Always printed (descriptive).** Per arm: D, the false-statement count with its upper limit, recall with an exact interval, the baseline's two numbers, and per (input, stratum) confusion rows with exact intervals. None of these license anything.

### 2.7 Symmetry and wording
- One label function for both arms, the same strata, the same D, the same bound.
- The A15 and G15 sentences are printed side by side with no comparative word ("more", "fewer", "better identified").
- The 11a item 10 sentence becomes: *"Of the [n] inputs of the extracted [KAN/additive] law, the audit licensed the form of [j] and the sign of [s]; [a] were not identified and [p] were not retained by the extraction."*

### 2.8 Guard scope
- **Calibration content** is fixed by the FROZEN commit.
  - The script refuses to run unless `verify_freeze` passes with untracked files included under `code/`, and both pins match.
  - `calibration.json` records the FROZEN SHA, the rule and thresholds hashes, D completed, and per-dataset records.
  - The gate auditor re-runs 3 datasets, chosen by the first bytes of `sha256(calibration.json)`, from a FROZEN worktree and requires bit-identical records.
  - mtime ordering is logged but is not the control. The calibration may therefore run before, alongside or after the confirmatory grid.
- **Stats step.**
  - Edge wording needs a mandatory `audit_thresholds_pin` and a `calibration_sha256` argument.
  - The record's commit must equal the FROZEN SHA.
  - At g4 there must be exactly 25 laws per arm.
  - Calendar edge wording is refused.
  - The label, sentence and audit functions are called only from `edge_level_wording`; a test asserts that the stats step does not import them elsewhere.
- **Manuscript.** Before submission, a banned-words grep over `paper/draft/` (section 4 of 03 plus "no effect" for non-retained inputs). Gate auditor.

---

## 3. CPU budget of the calibration (arithmetic, not a measurement)

- 2 arms x 30 datasets x 5 folds x 5 seeds = **1500 pipeline fits** at m = 32. The baseline reuses them.
- Per-fit time from the D021 logs: mean 43.2 s, maximum 79 s over 135 pipelines. Those included two refits (cap 2 and 3) against one here; the hyperparameter draws (grid 12, h = 2) may be slower. I therefore keep both figures as they are.
- **Expected about 18 CPU-h, ceiling about 33 CPU-h**; on 3 single-thread processes about 6 h and about 11 h of wall time.
- **Cap 36 CPU-h.** At the cap, the stop rule of 2.5 applies (verdict on the completed datasets if at least 22).
- The calibration shares the 3 processes with the Samsung grid. It runs after the core g4 set (PREREG 15 step 4) unless the lead schedules it earlier. It never displaces the "never dropped" list (PREREG 12 rule 5).

## 4. Delay to the freeze
- **Code**: PD-based labels and the additivity test, the strata generator, hyperparameter draws, dataset scoring, baseline, C1-C3, guard changes, and fixes m1-m6, with unit tests. About 1 day, an estimate.
- **Red-team re-check**: about half a day.
- **Designer**: PREREG edits; can proceed in parallel.
- **Total about 1 to 1.5 days.** Nothing here needs Samsung data or holds up any freeze blocker, so it can run in parallel with FB-3 to FB-10.
- If the lead cannot hold the freeze for it, section 5 applies.

## 5. Fallback (if the revision is not built, tested and re-checked by the freeze)
- The audit is struck by a change-log row (17.4). The paper prints the extracted laws only.
- The existing 11a item 6 stability table (per-input family votes across folds and seeds, with A15 and G15 side by side) is reported descriptively, with the tie note for T and no licence words.
- No contribution bullet for the audit.
- The KAN-side content of the paper then is: the K1/K2 tests, the cap justified by the D021 synthetic false-structure study (reported in Methods as a synthetic result), and the readable closed form.
- The v1 calibration code, if it is in the frozen commit, is not run for the paper (F1 makes its numbers misleading).
- The answer to the author changes to: "the KAN contribution is the tested closed-form law and its cap justification; no audit claim".

## 6. Actions

| # | Action | Owner | File |
|---|---|---|---|
| B1 | Implement 2.2-2.6 and 2.8; fix M6 and m1-m6; unit tests: tie gives no family; A15 h = 1 with a log outer edge is non-additive; G15 and A15 use one label function; 25-law completeness; sign tie gives no sign; calendar wording refused; pins mandatory; bit-identical re-run of one dataset; C1-C3 arithmetic against the counts in 2.6 | coder | `code/pinnkan/extraction_audit.py`, `extraction_audit.json` (v2), `code/prereg/extraction_calibration.py`, `code/pinnkan/stats_v4.py`, `stats_step.py`, `guard.py`, `code/tests/test_extraction_audit.py`, `test_extraction_calibration.py` |
| B2 | Rewrite the calibration rule to 2.4-2.6 and 3, committed before B1's script changes; the old rule kept as superseded | coder (rule text from this file) | `debates/D022_datasets_kan/calibration_rule_v2.md` |
| B3 | PREREG_v4: 7.3 item 6 and 11a item 10 rewritten to this file; C26 updated (C1-C3, re-run check); 15 (calibration order and cap); 17.4 fallback = section 5; 19.1 change-log row D022a; remove the "negative finding" wording | experiment-designer | `runs/prereg/PREREG_v4.md` |
| B4 | Re-check of B1-B3 against F1, F2, M1-M8 (pass/fail per finding) before signing 7.3 item 6 | red team | `debates/D022_datasets_kan/06_redteam_recheck.md` |
| B5 | After FROZEN: run the calibration; file `calibration.json`; re-run 3 hash-chosen datasets bit-identically; check BLINDING_LOG for m7 | coder runs; gate auditor checks | `runs/extraction_calibration/`, `research/audits/D022a-calibration-<date>.md` |
| B6 | Methods text: "calibrated extraction audit", the M8 statement, the C1-C3 sentences, no Raue-style claim; Sovrano positioning on the bound, abstention and baseline | manuscript writer | `paper/draft/` |
| B7 | Decide whether the freeze waits about 1 to 1.5 days for B1-B4, or section 5 applies | lead | `research/progress.md` |

## 7. Re-open if
- B4 finds any FATAL unresolved.
- The bit-identical re-run fails (the calibration is void and section 5 applies).
- Fewer than 22 datasets complete under the cap.
- The tuned hyperparameters on real data fall outside the spaces sampled in 2.4.
- A Samsung outer score is used to change anything in this rule.
- Shlok asks for labels at g1 or on the calendar law (that needs its own calibration and a new decision row).
