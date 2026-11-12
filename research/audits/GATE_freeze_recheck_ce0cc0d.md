# Gate-auditor re-check of the freeze conditions at record commit ce0cc0d (2026-11-07)

- **Auditor:** gate-auditor (validator only).
- **HEAD:** ce0cc0da1e1c8750846a409935ff1c3dbd1e53bc. Candidate code commit d13a8c6.
- **How it was run:** read-only, CPU, every python call `-P ... </dev/null`.
- **Not done:** no Samsung retention value, prediction or test fold opened; no test role loaded; no commit; no tracked edit; FROZEN not
  written.
- **One metadata file read:** `data/processed/samsung_cells.csv`, used for the 7.3 count. Its columns are serials, design stresses,
  laboratory and check-up counts; it has no capacity column.
- **Prior record:** `research/audits/GATE_freeze_audit.md` (first audit, rev. 19 re-check, final re-check c702e1a).

## Verdict: PASS. FREEZE OK at ce0cc0d.

The lead may run `write_frozen.py` (without `--dry`) at HEAD ce0cc0d. After that, nothing may be committed until the confirmatory runs
end (D031).

## Findings

**1. Rev. 24 numbers (17.1 FB-8 to FB-10, `PREREG_v4.md:503-505`; change-log `:602`; D042): all confirmed from the files.**
- `queue.log`:
  - line 1 is `HEAD d13a8c6... dirty_code_prereg=0`;
  - all 16 runs have rc=0;
  - suite done 10:27:27, FB-8b done 10:32:19 (started at HEAD d13a8c6), head_comparison rc=0 at 10:32:42.
  - All of this precedes the ce0cc0d commit at 10:34:42 +0545.
  - Every `runs/fb*/git.json` (24 files) reads d13a8c6 with dirty_code [].
- **FB-8:**
  - The 10 configs equal the primary configs except `mode` and `run_id`, and the guard roles are train only.
  - Recomputed: median A1 31.47 s (max 48.66) and A2 5.41 s (max 10.57). The text says 31.5 / 48.7 / 5.4 / 10.6.
  - The triggers (90 s for A1, 30 s for A2) are not reached, so N = 40 stands.
  - The slower and more spread times are consistent with the stated shared CPU; no rule depends on them.
- **FB-8b:**
  - The script is unchanged since 11b0880, and the files are timestamped 10:30-10:32 at d13a8c6.
  - A1 and A9 each have 748 inverted cells, 0 non-converged, 0 non-finite latents and share 1.0 in every fold x m cell.
  - The inversion config sha equals HEAD's.
- **FB-9:** passed at m = 8, 16 and 32; rows 45,760 / 35,380 / 49,220; max diff 0.0 in the outer rows and the inner out-of-fold
  predictions; 0 non-finite predictions; arms equal to the grid config.
- **FB-10:** both smoke runs rc=0 at d13a8c6, and RUN.log ends "done".
- **Suite:** `suite.log` has 46 lines, and the file set is identical to `git ls-files code/tests/test_*.py`. All passed, 888 tests.
- **No-regression comparison:** `head_comparison.out` shows `contrasts_v4_B.json`, `controls.json` and `physval_11a.json` IDENTICAL to
  base 052eefd.
- **D042's 7.3 item 6 count is correct.** Counting z-type cells at T_C 45 by condition (the stress tuple, as in
  `runs/prereg/lab_map.json`): 17 conditions, of which 14 are HM only, 2 mixed HM/SIE and 1 SIE only.
  - The 2 mixed conditions are the two in `lab_map.json` `mixed_conditions_cell_counts`.
  - The old "12 of 15" no longer appears outside the change-log quote.
  - Counted by Testpoint instead, the numbers would be 16 / 13 HM / 3 SIE. The stress-tuple definition is the one the PREREG uses.

**2. Section 11: PASS.** sha256 of `## 11. Outcomes` up to `## 11a.` (now `:347-429`) is
`001b1c798342f5b44c040eff167989a7802f44fee704105cd695e30a0726c9e5`, with 0 CR bytes.

**3. D031 order: PASS.**
- `git diff --stat d13a8c6 ce0cc0d -- code` is empty.
- The record commit changes only `CLAUDE.md`, `PROJECT.md`, `research/*`, `runs/freeze_runs/run_all_d13a8c6.sh`,
  `runs/freeze_runs/write_frozen.py`, `tools/vault_knowledge.py` and `runs/prereg/PREREG_v4.md`.
  - The PREREG hunks are at lines 3, 191 (7.3 item 6), 503-505 and 602, all outside section 11.
- `git status --porcelain -- code runs/prereg` is empty, including untracked files, which `verify_freeze(untracked_under=("code",))`
  also refuses.
- FROZEN is absent.
- The dry payload's `commit` is ce0cc0d, which is HEAD.
- The only modified tracked files are under `data/` (`DEFERRED_URLS.tsv`, `SAMSUNG_CU_STATUS.md`, `logs/samsung_cu.log`). They are
  outside the guarded paths; do not commit them before the runs end.

**4. Earlier audit items still stand: PASS.**
- **Unchanged since 11b0880:** `inversion.py`, `inversion_diag.py` (D23 A9: window cells only), `guard.py`, `data.py`, the pin files,
  the item (f) configs, and the freeze-run configs and scripts.
- **Code changes since c702e1a** (`pinn._hull_sample` for constant columns, `neutralise_stress` for row (u), statistics-step controls)
  are covered by signatures:
  - the red team signed sections 1, 10 and 11 at rev. 20 as amended (`SIGN_redteam_rev20.md:197`), which closes my c702e1a C18
    finding;
  - the red team signed row 9.9 (u) (`SIGN_redteam_rows.md:153`);
  - the statistician signed row (u) (`SIGN_statistician_gaps.md:198`).
- **Text minors applied:**
  - the statistician's M1 is present ("mirrored test (at least 30 of 40");
  - M2 and the red team's n-1 are present as "runs that are not the five pinned configurations stop the step; a pairing integrity error
    between the pinned runs is recorded as not computed" (`:309`), which is the same content in the red team's wording.
- C3/C17 draft items are unchanged: no PREREG_v2/v3 or H1a reference in `paper/draft`.
- The marker grep returns 0 lines.
- **17.2 rows:**
  - C1 is met (FB-1 to FB-6 per their cells; FB-8 to FB-10 per finding 1).
  - C14 is met: the MANIFEST lists 281 files (primary 26, rows 36, sensitivity 195, exploratory 4, replication 10, crate_ablation 5,
    item_f 5). All are tracked and at n_trials 40, and every `config_sha256` and `file_sha256` equals the file on disk (0 mismatches).
  - C15 is met (finding 1, suite).
  - C16 is met (FB-9).
  - C18 is met (above).
  - C19 is met (D042 is the freeze row).
  - C20 is met (grep at ce0cc0d).
  - All other rows are as in the c702e1a re-check.
  - C4 (d), C12 and C24 are post-freeze by design.
- **Stale text, not blocking:** the C14 and C19 cells still read "partly", and C20 reads "met on the text of rev. 15". This audit is the
  tick record.

**5. FROZEN payload: PASS.**
- `write_frozen.py --dry` exits rc=0 and writes nothing. It reports:
  - commit ce0cc0d;
  - `prereg_sha256` ec51ca2107d615683aa6f770026351762b5eb746ad3e0b1163664f9632435f5a;
  - 7 splits (isu:B, samsung:A/B/C/S2/S3, snl:B);
  - 276 configs;
  - 5 item (f) configs;
  - pins blinding_exclusions, stats_config, subsets and symbolic_library (= `guard.PIN_FILES`).
- I rebuilt the payload myself from MANIFEST paths and got the same result:
  - 276 distinct config hashes and 5 distinct item (f) hashes;
  - the 5 crate_ablation hashes (`crate_ablation/conf_samsung_B_f{0-4}_m32_crate.json`) are in `config_sha256s`;
  - `pins_missing` [];
  - `prereg_sha256` equals the disk bytes.
- The script checks the clean tree, absent FROZEN, the MANIFEST equality of both hash lists (as sets), 276 distinct configs, no missing
  pin and commit = HEAD. It then writes FROZEN and runs `verify_freeze(check_git=True, untracked_under=("code",))`.
- Note: the 5 item (f) configs are checked only through `require_pins` (5 distinct) and the MANIFEST equality, which is sufficient.
