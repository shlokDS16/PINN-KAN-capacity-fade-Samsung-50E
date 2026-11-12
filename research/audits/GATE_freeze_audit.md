# Gate-auditor freeze audit, PREREG_v4 rev. 18 (2026-11-06)

Auditor: gate-auditor (validator; I propose nothing and fixed nothing). Brief: `runs/freeze_runs/AUDIT_BRIEF.md`. Rules: `research/CONTRACT.md`.
HEAD audited: 11b0880 (text-only commit on candidate 92db4cb). CPU only, every python call `-P ... </dev/null`.
I opened no Samsung retention value, prediction or test-fold file, and loaded no Samsung test role. The only Samsung files I read were
identifier, count and timing files (`timings.json`, `window_capped.json`, `git.json`, `guard.json`, `config.json`, `fb8b_f*.json`).
I made no commit, edited no tracked file and did not write `runs/prereg/FROZEN`. I added no ledger row and did not edit `progress.md`,
because the brief forbids edits to tracked files.

## Overall: FREEZE NOT OK (one step away)

- All 11 briefed checks: **PASS or PASS-WITH-NOTE. None FAIL.**
- What blocks: two rows of the 17.2 checklist that the brief did not list. The PREREG says it "freezes only when every item of the
  checklist in section 17.2 is met" (`runs/prereg/PREREG_v4.md:3`), and 17.3 asks the gate auditor to audit against "this checklist".
  - **C17: missing** (`PREREG_v4.md:525`). `paper/draft` holds none of the disclosure sentences. Its last commit is 2ec4b95, and
    `PREFREEZE_STATUS.md:48,72` assigns this work to the writer.
  - **C3: partly** (`PREREG_v4.md:511`). The code is aligned. `paper/draft/03_data.md`, `04_methods.md` and `05_evaluation.md` still
    cite PREREG_v2 / H1a-H6.
  - `research/DECISIONS.md` has no row (D001-D036) that waives or defers either item.
- **Remedy (no re-run needed):** either Shlok writes a decision row that defers the paper-text items (C3 draft part, C17) to after
  FROZEN, or the writer completes them. Both are outside `code/` and `runs/prereg/`, so none of the evidence below changes. Under my
  rules I cannot waive a criterion. Once either is done, the freeze is OK, subject to the must-do of check 11 (the S3 split key).

## Commits
- `git diff --stat 92db4cb HEAD -- code` is empty.
- `git diff --stat 92db4cb HEAD -- runs/prereg` touches only `PREREG_v4.md` (7 insertions, 6 deletions).
- The hunks are at lines 1, 3, 500-502, 535 and 593. Section 11 spans lines 344-426, so no hunk touches it.
- The whole commit changes `research/DECISIONS.md` (D036), `runs/freeze_runs/AUDIT_BRIEF.md`, `runs/freeze_runs/fb8b_convergence.py`
  and PREREG_v4.md.
- 92db4cb is 4e29223 plus the two rev. 17 confirmation commits (2384ffe, 92db4cb), with no change under `code/`, `runs/prereg`,
  `runs/item_f` or `runs/freeze_runs`. The red-team and statistician signatures of rev. 16, confirmed at rev. 17 (scope 4e29223),
  therefore cover the frozen code.
- `queue.log:1`: `HEAD 92db4cb... dirty_code_prereg=0`.

## Checks

| # | Check | Verdict | Evidence |
|---|---|---|---|
| 1 | C21 section 11 | PASS-WITH-NOTE | See 1 below |
| 2 | FB-8 | PASS | See 2 |
| 3 | C27 / FB-8b / D23 A9 | PASS-WITH-NOTE | See 3 |
| 4 | FB-9 | PASS | See 4 |
| 5 | FB-10 | PASS | See 5 |
| 6 | C15 suite | PASS | See 6 |
| 7 | C28 / D032 | PASS-WITH-NOTE | See 7 |
| 8 | C9-C11, C24, C26 | PASS | See 8 |
| 9 | Pins, MANIFEST, item (f) | PASS-WITH-NOTE | See 9 |
| 10 | Tree | PASS | See 10 |
| 11 | Dry build | PASS-WITH-NOTE | See 11 |

**1. C21.**
- I took the bytes on disk from `## 11. Outcomes` up to `## 11a.`. The span has 0 CR bytes.
- sha256 = `001b1c798342f5b44c040eff167989a7802f44fee704105cd695e30a0726c9e5`. This equals `SIGN_redteam_rev16.md:58,160` (001b1c79...26c9e5)
  and `PREREG_v4.md:675`.
  - The brief's suffix "...e9" is a typo in the brief. No file records "...e9".
- I compared lines against `debates/D016_roles/02_judge.md` section 4. Every difference inside the J16 block (J16 lines 219-291) is one of
  these strings:
  - the added M3 line, D034 AD2. It matches `debates/D033_signoff/01_judge.md` AD2 Opt 1 word for word;
  - "closed-form" in T1, T4 and T7 and in the K1-fail clause (AD5);
  - T5 and T6 (D030 text, exact);
  - T9a and T9b "with few cycling tests", with the "when ... if P3 is S" alternative (AD4).
- No "readable" is left in section 11.
- Outside the block, section 11 also contains:
  - the reading note (line 346);
  - the Test C wording and the Pilot P3 entry (lines 423-425). These stand where J16 has its closing `---`.
  - All of this is unchanged since the rev. 16 signatures (same hash).
- Note: the reading note still says the block is "copied byte for byte ... not edited". That is stale after D030/D034. It is inside the
  hash-pinned section, so only Shlok can change it. The red team records it as m-8, left by design.

**2. FB-8.**
- Ten runs `runs/fb8_timing_samsung_B_f{0-4}_m{8,32}`, all `rc=0` in `queue.log`.
- Every `git.json` reads commit 92db4cb with `dirty_code` = []. The n_dirty of 195-210 is untracked run output.
- Every `guard.json` holds only `load_split(samsung, B, fold f)` with role `train`.
- Median single fit over the ten runs (recomputed):
  - A1 29.74 s (max 32.97). Trigger 90 s.
  - A2 5.07 s (max 6.15). Trigger 30 s.
  - The Partial plan is not triggered (`PREREG_v4.md:151`). The PREREG figures 29.7 / 33.0 / 5.1 / 6.2 (line 500) agree.
- Configs: each `runs/freeze_runs/configs/fb8_*` differs from `runs/prereg/confirmatory_configs/conf_samsung_B_f*_m*.json` only in
  `mode` and `run_id`, at n_trials 40. Each run's `config.json` equals its input file. The generator is `make_configs.py:20-24`.

**3. C27 / D023 A8-A9, FB-8b.**

Numbers:
- `runs/freeze_runs/fb8b/fb8b_f{0-4}.json`: A1 and A9 each have 748 inverted cells over 5 folds x m {8, 32}, 0 non-converged, share 1.0
  in every cell, `nonfinite` 0, inner_k 2 at m = 8 and 3 at m = 32.
- `inversion_config_sha256` 3e902bea... equals `inversion.config_sha256()` at HEAD.
- `lane3.out` ends rc=0.

**Ruling: FB-8b is a faithful, training-side-only way to log the share that `PREREG_v4.md:237` asks for.**
- It calls `run.validate_config`, then `run.build_data(cfg, ROOT, "train")`, which returns `test=None` for real data
  (`run.py:129-145`). It also asserts `D["test"] is None`.
- It rebuilds `rule` and `rule_tune` exactly as `run.py:375,389` does.
- Its inner folds are `tuning.inner_folds(train, inner_k, 1000 + fold, spec, tk)`, the same call as `tuning.tune` (`tuning.py:79`) and
  `run.py:445`.
- Its fit/validation partition and `prepare_many(val, rule_tune)` mirror `tuning.cv_rows` (`tuning.py:60-72`).
- It calls the production `arm.predict`, so it uses `invert_latents` at the production CAP and TOL.
- The records come from `inversion.log_result` / `drain_log` / `pooled_convergence` (`inversion.py:118-139`).
- It writes counts and gnorm_max only. No prediction, retention value or score is written.
- `inversion_diag.py` reads no outer label. It receives `WindowCell`s only (`data.py:81-92`: window `t_win`/`y_win`, forecast times
  `t_fc`, causal EFC curve; no forecast label). It is called from `_inversion_diagnostics` after `condition_scores.json` is written
  (`run.py:583-584`). The scoring of rows (v)/(vi) happens in the run writer, as D023 section 4 prescribes. D23 A9 holds.

Notes:
- (a) **Wording.** PREREG line 500, line 535 and D036 say "0 non-finite steps". The `nonfinite` field counts cells whose final latent is
  non-finite (`inversion.py:122`). The solver silently rejects a non-finite trial step (`inversion.py:106-107`), so non-finite steps
  are not counted anywhere. The evidence supports "0 non-finite latents; every cell converged". Line 237's "any Newton step is
  non-finite" cannot be measured by the frozen code. This is text-only, outside section 11.
- (b) **Provenance.** The JSONs carry no commit field ("see queue.log HEAD"). Their mtimes, 16:49-16:51, are before 11b0880
  (16:53:36 +0545), so HEAD was 92db4cb, and `code/` is identical at both commits. The dirty state during the run was not recorded,
  and the run is not in `queue.log`. The docstring says "untracked", but the script is now committed.
- (c) **Scope.** FB-8b covers only the tuning windows: k = 2 at m = 8 and k_full at m = 32. It uses the self_limiting backbone (not the
  tournament winner) and default hyperparameters. It does not cover m = 16, (8, full) or (32, 2). It is a proxy by design, like the
  timing mode it replaces.
- (d) **Blinding.** FB-8b bypasses the pre-freeze switch of `run.py:331-333` (PREREG 3.3(9): "fit seconds and parameter counts only").
  What it writes shows no retention value by cell or condition, so the 3.3(9) rule as worded holds.

**4. FB-9.** `runs/fb9_nc1_full_synth_m{8,16,32}/nc1_full.json`:
- passed = true at k = 0, 2 and full;
- max_abs_diff_outer 0.0 and max_abs_diff_inner_oof 0.0 at every k;
- 0 non-finite predictions;
- outer rows 45,760 / 35,380 / 49,220, matching line 501.

The arms equal those of the grid config at every fold: 14 / 11 / 15 arms, with A15 and G15 at m = 8 and 32, and none at m = 16 by the
grid design. Short-record cells are configured, and the clean runs' `window_capped.json` lists 2 / 2 / 4 capped synthetic cells. Every
sub-run's `git.json` reads 92db4cb with dirty_code [].

**5. FB-10.**
- `runs/fb10_smoke_{isu,snl}_B0`: rc=0 (`queue.log`), commit 92db4cb, dirty_code [], and RUN.log ends "done".
- The configs equal `runs/build_v1/configs/smoke_{isu,snl}_B0.json` except `run_id` and the removal of A3 (ISU) and A7 (SNL).

**6. C15.**
- `suite.log`: 43 lines, one per file. The file set is identical to `git ls-files code/tests/test_*.py` (43).
- Every line reads "N passed" (total 798), with no failure, error or skip.
- It includes `test_pk_a10_paper_form.py` (8), `test_pk_models.py` (which holds `test_arm_table_matches_prereg_dimensions`) and
  `test_inversion.py` (18).
- The suite ran in the 92db4cb queue: "suite done 16:43:52".

**7. C28 / D032.** I compared identifiers only.
- The union over folds of the `window_capped.json` files of the FB-8 runs at m = 32 has 8 cells:
  - the 6 scoreable cycling cells: TP_z04_01_s1, TP_z20_02_s2, TP_z20_03_s2, TP_z23_01_s2, TP_z23_02_s2, TP_z23_03_s2;
  - the 2 unscoreable cells: TP_z24_01_s1, TP_z25_01_s1.
  - This matches `runs/freeze_runs/D025_capped_cells.md`. The m = 8 lists are subsets of it.
- Note: FB-8 writes the cap list at k_full only, so the k = 2 list (TP_z20_02_s2, TP_z23_01_s2) and "condition-level n stays 40" are
  not recomputed here. Recomputing them would need loading Samsung cells.
- The NC-1 interaction is covered by FB-9: capped short-record cells were present, and invariance passed at every k.

**8. C9-C11, C24, C26.**
- **C9:** `runs/build_v2/RESULT.md` items 5-6 present. `test_pk_v2_rows.py` (15) and `test_pk_v2_review.py` (17) pass.
- **C10:**
  - `graph_test.py`, `test_graph_test.py` (12), `test_fallback_weights_secondary.py` (17) and `test_pk_d033_coder.py` pass.
  - `stats_config.json` is in `guard.PIN_FILES` (`guard.py:25-26`).
  - The D034 code exists: `stats_v4.py:30` (G32K2) and `:338-413` (p3_contrast, M3), per `runs/prereg/CODER_D034_REPORT.md`, and
    `test_pk_d034_coder.py` passes.
- **C11:** `data.WindowRule.for_grid` (`data.py:123`). The `test_k0_*` tests and `test_the_window_gains_information_between_k0_and_k2`
  are in `test_pk_v2_windows.py:80-118` (18 passed).
- **C24:**
  - five configs in `runs/item_f/configs/`;
  - `stats_v4.build_item_f` (`:647`) and `guard.require_item_f_record` (`guard.py:197`);
  - `item_f_sha256` passed to `record_scoring` (`run.py:491`);
  - `test_pk_d026_item_f.py` 37 passed.
- **C26:**
  - `label_input` and `label_law` default to `calibrated=False` (`extraction_audit.py:313,359`);
  - no `audit_dir` in any of the 276 configs;
  - `09_redteam_fallback_recheck.md:105`: "7.3 item 6 sign-off: SIGNED";
  - `test_c26_recheck.py` (30) and `test_extraction_fallback.py` (30) pass.

**9. Pins.**
- Every `guard.PIN_FILES` entry exists, is tracked and is clean: subsets, symbolic_library (`max_coeffs_per_edge` 2), blinding_exclusions
  and stats_config.
- `MANIFEST.json` lists 276 files: primary 26, rows 36, sensitivity 195, exploratory 4, replication 10, item_f 5.
  - All are at n_trials 40, all are tracked, and all have distinct hashes.
  - Each `config_sha256` equals `guard.canonical_config_hash({**DEFAULTS, **file})`.
  - Each `file_sha256` equals the sha256 of the bytes on disk (0 CRLF files).
- The item (f) configs differ from `conf_samsung_B_f*_m8.json` only in `mode` (inner), `run_id`, `arms` (A1, A9, A11, A12;
  `make_confirmatory_configs.py:54`), `diagnostics` false and `refit_timing` false. This matches 18 step 2b.
- Row configs at m = 8 carry R1 (25 of 25), and the m = 32 rows carry k [2, full] (D034).
- The five NC-2 configs (A1, permute_stress, m = 32) are in the set (C16).
- Note: `core.autocrlf=true`. `prereg_sha256` is a disk-byte hash, and PREREG_v4.md is LF on disk now. Any re-checkout would write CRLF
  and break `verify_freeze`, so keep D031 (main checkout, no re-checkout). The config pins are canonical-JSON hashes and are immune.

**10. Tree.** `git status --porcelain --untracked-files=no -- code runs/prereg` is empty, and `runs/prereg/FROZEN` is absent (checked
before and after check 11).

**11. Dry build.**
- I called `guard.build_freeze_payload(root, split_keys of 18 step 4, the 271 non-item_f MANIFEST paths,
  prereg_file="runs/prereg/PREREG_v4.md", item_f_config_paths=<5>, require_pins=True)`.
- It returned keys {commit, config_sha256s, item_f_config_sha256s, pins, pins_missing, prereg_file, prereg_sha256, splits}:
  - commit 11b0880;
  - 6 splits (isu:B, samsung:A/B/C/S2, snl:B);
  - 271 config hashes, equal to the MANIFEST in order;
  - 5 item (f) hashes, equal to the MANIFEST;
  - 4 pins, `pins_missing` [];
  - `prereg_sha256` equal to the disk bytes.
- FROZEN was not written.
- **Must-do when writing FROZEN:** the MANIFEST pins `exploratory/expl_samsung_S3_f0.json` (samsung S3). `guard.pinned_split`
  (`guard.py:139-147`) fails closed for an unpinned split key, so add `("samsung", "S3")` to `split_keys` (18 step 4: "plus A/S3
  entries as run"). With it the payload has 7 splits and builds cleanly.

## Other 17.2 rows (full-checklist audit)
- **Met:**
  - C1: FB-1 to FB-6 met on their cells. Spot-checked: `04_novelty_C4_audit.md:50` "FB-1: CONFIRMED NOT TRIGGERED";
    `semi.A10_FORM["verified"]` True; fb5 sha256 d3d45fb5...; and the split copy byte-identical (sha256 0446d5cf...) to the prereg copy.
    FB-8 to FB-10 are met per checks 2, 4 and 5.
  - C2: statistician SIGNED rev. 16 and CONFIRMED rev. 17. Item (f) is after FROZEN by design.
  - C5, C6, C7, C8, C13 and C22-C26, on their evidence cells.
  - C14: MANIFEST regenerated at n_trials 40 (check 9).
  - C15 and C16 (checks 6, 4, 9).
  - C18: red team and statistician signed and confirmed; 7.3 item 6 signed; this file is the gate auditor's audit.
  - C19: D010 row and D036.
  - C20: the marker grep at HEAD returns nothing.
- **Post-freeze by design (not blocking):**
  - C4 (d), at submission;
  - C12 (`margins.json` after tuning);
  - item (f) of C24.
- **Not met, no waiver:** C3 (partly) and C17 (missing). See Overall.
- **Text notes for the lead (outside section 11; none changes a rule):**
  - The status line (`PREREG_v4.md:3`) says both "FROZEN rev. 18" and "NOT YET FROZEN", and also "the lead, not this revision, changes
    the status line to FROZEN".
  - The 17.2 status cells C1 (open), C2, C10, C15 (partly), C16 (open), C18, C21 and C28 still read open/partly against the met FB-9 and
    FB-10 cells. That contradicts the C20 (c) consistency claim. This audit file is the tick record.
  - See also note 3 (a).

## Number audit (rev. 18 text against files; all recomputed)
- Line 500:
  - A1 29.7 / 33.0 s and A2 5.1 / 6.2 s: confirmed (29.74 / 32.97 / 5.07 / 6.15).
  - 748 cells per arm, 0 non-converged, share 1.0: confirmed.
  - "0 non-finite steps": not what the field measures (note 3 (a)).
- Line 501: 45,760 / 35,380 / 49,220 rows, max diff 0.0: confirmed.
- Line 502: 43 of 43 files: confirmed (798 tests).
- Line 593: section 11 hash 001b1c79...c9e5: confirmed.

Observation (not caused by this audit): tracked files outside code/ and runs/prereg are modified in the working tree (data/DEFERRED_URLS.tsv, data/SAMSUNG_CU_STATUS.md, data/logs/samsung_cu.log, paper/figures/*_SYNTHETIC.*, paper/tables/*_SYNTHETIC.*), probably from the suite and the downloader. verify_freeze checks only code/ and runs/prereg, so they do not block; do not commit them into the frozen commit by accident.

## Re-check rev. 19 (HEAD 02a8efc, one commit on 11b0880)

Same constraints as the first audit. I opened nothing beyond paper/draft, the PREREG text and config/identifier files.

**Overall: FREEZE NOT OK (one decision row away).**
- Items (1), (3) and (4) PASS.
- In item (2), the paper/draft part of C3 is met, but D037 defers the section 20 figure-script rows (and the 05 row's Introduction/abstract
  items) on the lead's authority alone. Under C3's own text that is a partial waiver, and only Shlok can grant it.

Correction to my first audit: I wrote "C3: partly (code aligned; paper/draft not)". The C3 evidence cell (`PREREG_v4.md:511`) and
`PREFREEZE_STATUS.md:34` both list "the section 20 rows for the draft **and the figures**" as not aligned. I missed the figures part.

**(1) C17: PASS.**
- Every sentence is in the draft with a `<!-- C17: ... -->` source comment, and its content matches the PREREG:
  - 3.3(10)(a) `03_data.md:17`;
  - (b) `04_methods.md:45`;
  - (c) `04_methods.md:73`;
  - (d) `04_methods.md:81`;
  - (e) `03_data.md:17`;
  - (f) `03_data.md:15`;
  - (g) `03_data.md:13`;
  - 3.3(11)(c) `03_data.md:17`;
  - the 7.2 A10 scope sentence and the 7.2 map sentence `04_methods.md:75`;
  - the section 13 circularity sentence `05_evaluation.md:71`.
- (a), (b), (c), (d), (f), 11(c), the 7.2 scope sentence and the circularity sentence are verbatim, apart from LaTeX for symbols.
- The editorial expansions do not change content:
  - (e) spells out CU, ET_T23 and exCU;
  - (g) writes Q0 as $Q_{0,c}$;
  - the map sentence has "ambient temperature" for "ambient T", reorders "the exponents of the per-factor terms", and carries an
    `[AUTHOR: define EOLC]` placeholder.
- Notes (content, not C17):
  - (i) Sentence (d), "All computations ran on CPU, float32", conflicts with the float64 ("double precision") inversion of 7.5 and
    `04_methods.md:45`. The sentence is the PREREG's own text, so the conflict is inherited, but a reviewer will see it.
  - (ii) 3.3(10)(a) says 18 cells and 3.3(11)(a) says 19 cells for the same 163 check-ups (writer concern 2).

**(2) C3.**
- Draft part: **met.**
  - A grep of `00_open_items.md`, `03_data.md`, `04_methods.md` and `05_evaluation.md` for `PREREG_v[23]`, `PREREG_DRAFT` and `H[1-7][a-c]`
    finds nothing.
  - The `[TO VERIFY: ... neighbour]` line is gone. `03_data.md:15` now states the causal rule. The remaining `[TO VERIFY]` at
    `03_data.md:23` is the unrelated ISU count.
  - The stale sign-flip sentence of `00_open_items.md` has been replaced (`:13`).
  - The section 20 rows 05 (5.1-5.6, the design-effect test, Limitations dependence), 04 (arms, window, grid, A15/G15/D*) and 03/00 are
    done at the lines that `WRITER_C3_C17_REPORT.md` gives.
  - The power figure follows section 1 (0.20-0.26 at rho 0.75), not the "21-25 %" of the section 20 row. Section 1 is the controlling
    text, so this is acceptable.
- **Ruling on D037: not acceptable as a lead-only procedural row.**
  - (a) C3's criterion is "code, `stats_step.py`, README and draft 5.5 aligned with it". `code/figures/*` is code. Section 20 row
    `PREREG_v4.md:710` ("`code/figures/*` ... `fig4_forest.py` plots the V3 forest") is one of the rows C3 was blocked on.
  - (b) D037's premise, that "the scripts read only the statistics outputs", is false at HEAD. `code/figures/fig4_forest.py:50-52`
    computes its own bootstrap mean CI, median-L interval and win count. That is analysis code under 17.4 (`PREREG_v4.md:542`:
    analysis code not in the frozen commit "cannot be added afterwards"; each item is built or struck by a change-log row).
  - (c) The section 20 row for 05 also lists "Introduction contribution list and the abstract rule on novelty (D18 6, A8)". There is no
    Introduction file, so this item is not placed; it is listed in `00_open_items.md:13`.
  - Deferring (a) and (c) is a waiver of part of C3, which only Shlok can grant.
  - What would make it acceptable: a decision row by Shlok deferring the figure-script and Introduction/abstract rows to the post-run
    branch (D031), with this binding condition: *the post-run figure and table scripts read only the outputs of the frozen statistics
    step (`run_pinnkan_stats.py` / `stats_v4`); they compute no interval, test, tier, count or effect size; `fig4_forest.py`'s own
    bootstrap and median intervals are removed; forms follow section 14 and `debates/D-figures.md`.*
  - Alternatives: align the scripts now (this moves `code/` off 92db4cb, so FB-8 to FB-10 and the suite must repeat), or strike the
    rows by a change-log row with Shlok's approval.

**(3) Text notes: applied. PASS.**
- Status line (`:3`): "FROZEN rev. 19 ...". The only remaining "NOT YET FROZEN" is the change-log quote at `:594`.
- 17.2 cells: C1, C2, C3, C15, C16, C17, C18, C21, C27 and C28 now read met.
- Non-finite wording: lines 500 and 535 now say "0 cells with a non-finite final latent (the solver rejects a non-finite trial step
  without counting it ...)". D037 corrects D036, keeping the ledger append-only.
- Change-log row rev. 19 is at `:594`.
- Marker grep returns 0 lines at rev. 19, so C20 holds on this commit.
- Section 11 sha256 = `001b1c798342f5b44c040eff167989a7802f44fee704105cd695e30a0726c9e5`, unchanged, 0 CR bytes. The rev. 19 hunks are at
  lines 3, 500, 509-511, 523-526, 529, 535-536 and 594, all outside 344-426.
- `git diff --stat 92db4cb HEAD -- code` is empty.
- `git status --porcelain --untracked-files=no -- code runs/prereg` is empty, and FROZEN is absent.
- Leftover stale fragments (minor; they block nothing):
  - C10 (`:518`) still says "gate-auditor tick pending". I tick C10 met here, as in check 8.
  - The C18 evidence cell still says "signatures **partly**".

**(4) Dry build with ("samsung","S3"): PASS.**
- `build_freeze_payload(..., require_pins=True)` returned:
  - keys {commit, config_sha256s, item_f_config_sha256s, pins, pins_missing, prereg_file, prereg_sha256, splits};
  - commit 02a8efc;
  - **7 splits** (isu:B, samsung:A/B/C/S2/S3, snl:B);
  - 271 config hashes (distinct), equal to the MANIFEST in order;
  - 5 item (f) hashes, equal to the MANIFEST;
  - 4 pins, `pins_missing` [];
  - `prereg_sha256` equal to the disk bytes.
- FROZEN was not written. No config, item (f) config or `guard.py` changed since 11b0880.

## Final re-check (c702e1a)

HEAD is c702e1a, a text-only commit on candidate code commit 39b14aa. Same constraints as before: no Samsung outcome file opened, no
Samsung test role loaded, no commit, no tracked edit, no FROZEN.

**Overall: FREEZE NOT OK. The only item open is a signature.**
- Checks (1)-(4) pass. Check (5) passes for every 17.2 row except C18.
- **C18 / 17.3 is not met.** 17.3 has the red team sign sections 1, 10 and 11.
  - Rev. 20 (commit 39b14aa) changed **section 10**, `PREREG_v4.md:344`:
    - it inserts operational rule T1 (PC-2) and rule T2 (PC-3);
    - it adds a new outcome rule: "A control that cannot be evaluated (NC-2, PC-2, PC-3) is listed and marks the outcome provisional;
      one that fails to compute stops the statistics step before the contrasts are written".
  - The code implementing these rules is new: `stats_step.py` `RegisteredControlError` / `_stats_gaps_v4`, `stats_gaps.pc2_v4` / `pc3_v4`.
  - The text was written by the statistician (T1-T3), who then confirmed its own insertion verbatim (`SIGN_statistician_gaps.md:155`).
  - No red-team review of the rev. 20 diff exists. The last red-team signature is the rev. 17 confirmation at 4e29223,
    `SIGN_redteam_rev16.md:144-166`.
  - The C18 cell (`:526`) cites only the rev. 16/17 signatures, so it does not cover this change. Proposer is not validator, and this
    project has re-signed every revision that touched a signed section (rev. 16, rev. 17).
- **Remedy:** a scoped red-team confirmation of the rev. 20 section 10 diff and of the registered-control code path (the provisional
  marking and the strict stop). It is text and code review only, needs no re-run, and can be written outside `code/` and `runs/prereg`.
  With it on file, the freeze is OK.

**(1) C3 and D038: PASS.**
- **Figure rows (section 20, `PREREG_v4.md:710`):**
  - `code/figures/fig4_forest.py` no longer computes a bootstrap or interval. The only aggregations left in code/figures outside the
    demo generator are plot-only: `pk_data.merge_bands` (`:227-233`) takes the min of lo, the max of hi and the mean of run means, as an
    envelope for plotting.
  - `code/tests/test_figures_read_only.py` (AST check of forbidden calls, imports and random draws, plus a render smoke test of every
    section 14 item) passes: 20 tests in `suite.log`.
- **Introduction and abstract item:** `paper/draft/01_introduction.md:11-28` holds the contribution list (D18 6 / A8, in D029 order) and
  the abstract novelty rule. The "to our knowledge" sentence is gated on C4 (d), "first" is banned, and no result is stated.
- **C17 still holds after the 052eefd wording change.** The draft's 3.3(10)(a) ("19 cells (18 cycling and 1 storage; 163 check-ups)",
  `03_data.md`) and (d) ("float32 except the per-cell latent inversion, which runs in float64", `04_methods.md`) are verbatim the new
  PREREG text. This resolves my rev. 19 notes (i) and (ii).
- **D038 is acceptable.** It replaces D037's deferral by doing the work before the freeze:
  - the new code is validated by the statistician (NOT SIGNED, then SIGNED, `SIGN_statistician_gaps.md:141-158`);
  - `code/` moved, so FB-8 to FB-10 and the suite were repeated (check 2);
  - the no-regression comparison shows the pre-existing outputs are unchanged.
  - The section 10 part of the change is the one item that still needs its signer (see above).

**(2) Repeated runs at 39b14aa: PASS. Rev. 21's numbers are supported.**
- `queue.log:1`: `HEAD 39b14aa... dirty_code_prereg=0`. All 16 runs report rc=0, and ALL DONE is at 20:39:36. Every
  `runs/fb*/git.json` reads 39b14aa with dirty_code [].
- **FB-8:**
  - The 10 configs equal the primary configs except `mode` and `run_id`, and guard roles are train only.
  - Median A1 **26.62 s** (max 28.40) and A2 **4.65 s** (max 5.27). PREREG `:502` says 26.6 / 28.4 / 4.7 / 5.3, and the triggers are
    not reached.
- **FB-8b:**
  - The script, `make_configs.py` and `run_queue.sh` are unchanged since 11b0880.
  - A1 and A9 each have **748 cells, 0 non-converged, 0 non-finite latents, share 1.0** in every cell, and the inversion config sha
    equals HEAD's.
  - The files are timestamped 20:42-20:44, after 39b14aa (19:45:22) and before c702e1a (20:46:11), and `code/` is identical at both.
- **FB-9:**
  - passed at m = 8, 16 and 32;
  - rows 45,760 / 35,380 / 49,220;
  - max diff 0.0 in the outer rows and the inner out-of-fold predictions;
  - 0 non-finite predictions;
  - arms equal to the grid config.
- **FB-10:** both smoke runs rc=0 at 39b14aa.
- **Suite:** 45 lines, and the file set equals `git ls-files code/tests/test_*.py`. All passed, **857 tests** (`:504`).
- `head_comparison.out`: `contrasts_v4_B.json`, `controls.json` and `physval_11a.json` are IDENTICAL to base 052eefd.
- The rev. 21 change-log row (`:598`), the status line (`:3`) and D039 state the same figures.

**(3) Tree: PASS.**
- `git diff --stat 39b14aa HEAD -- code` is empty.
- `runs/prereg` differs only in `PREREG_v4.md`, at hunks 3, 502-504 and 598. Section 11 now spans `:346` to before 11a, so no hunk is in
  it.
- Section 11 sha256 = `001b1c798342f5b44c040eff167989a7802f44fee704105cd695e30a0726c9e5`, unchanged, 0 CR bytes.
- `git status --porcelain --untracked-files=no -- code runs/prereg` is empty, and FROZEN is absent.
- The marker grep returns 0 lines.
- No config, item (f) config, pin file, `guard.py` or `inversion.py` changed since 11b0880. `run.DEFAULTS` is unchanged, so the
  canonical hashes still equal the MANIFEST: 276 of 276, 0 mismatches, all at n_trials 40.

**(4) Dry build, 7 split keys: PASS.**
- It returned:
  - commit c702e1a;
  - 7 splits (isu:B, samsung:A/B/C/S2/S3, snl:B);
  - 271 distinct config hashes and 5 distinct item (f) hashes;
  - pins {blinding_exclusions, stats_config, subsets, symbolic_library}, `pins_missing` [];
  - `prereg_sha256` equal to the disk bytes.
- FROZEN was not written.

**(5) 17.2 rows.**
- **Met:** C1-C3, C5-C11, C13, C15-C17, C20 (grep at c702e1a), C21-C23 and C25-C28.
- **C14 is met in substance:** the MANIFEST is regenerated at N = 40 and verified in (3). Its cell still reads "partly".
- **C19 is met:** the freeze row is D039, with D036-D038 present. Its cell still reads "partly".
- **Post-freeze by design:** C4 (d) at submission, C12 (`margins.json` after tuning), and C24 (item (f) after FROZEN; its pins are in the
  payload).
- **Not met: C18** (see Overall).
- Stale text, not blocking: the C14 and C19 cells read "partly", the C20 cell reads "met on the text of rev. 15", and the C18 evidence
  cell still contains "signatures **partly**".
