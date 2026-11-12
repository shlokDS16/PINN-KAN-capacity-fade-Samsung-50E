VERDICT: D044 RE-PIN PASS WITH CONDITIONS. The lead may write the new FROZEN at c6a89b6 with `--predecessor ce0cc0da1e1c8750846a409935ff1c3dbd1e53bc`. The conditions below are about order and disclosure; no check failed.

Gate auditor, 2026-11-11. Scope: main checkout, HEAD c6a89b6b2125a0ccb5b6170538fe7d43c018d2ba (branch main), against the archived FROZEN of ce0cc0d. Earlier audit: research/audits/GATE_D044_retainfix.md (conditions C1, C2).
I did not fix anything. I wrote no file in the project except this report. FROZEN was never written; the payload was only built in memory.
Blinding was kept. I opened no score, prediction, metric, contrast or run log, and nothing under runs/conf_*, repl_*, expl_*, runs/item_f*, analysis/ or data/.
- For the 3 blocked folders I listed the files and read git.json. RUN.log is 0 bytes.
- From SCORED.jsonl I read only its keys: config_sha256, run_id, commit, dataset, item_f_sha256.
- From campaign_state.jsonl I read only run_id, rc and blocked. I did not print gate flags.
- I grepped campaign.log for "start HEAD" and "ALL DONE" only.
- The item (f) record was read only by `guard.require_item_f_record` inside the simulation (check 4b). I printed only pass or refuse and the returned file hash.
Scripts (scratchpad, read-only): repin_compare.py, repin_simulate.py, state_count.py in C:\Users\Shlok\AppData\Local\Temp\claude\7953349499a142df\d91c28c7-7463-4cd6-912a-36fe62f77487\scratchpad\.

## 1. Diff ce0cc0d..c6a89b6 is confined, and C1 and C2 are met: MET
- `git diff ce0cc0d c6a89b6 --stat` lists 4 files, +120/-5:
  - code/pinnkan/data.py (+5)
  - code/pinnkan/guard.py (1 line)
  - code/tests/test_d044_retain_undated.py (new, 100 lines)
  - runs/freeze_runs/write_frozen.py (+13/-4)
- `git diff --stat ce0cc0d c6a89b6 -- configs runs/prereg code/prereg` is empty: no config, no prereg file, no MANIFEST and no pin changed. No other analysis code changed (stats_step, stats_v4, stats_rows, run.py, blinding.py and extraction_audit are not in the diff).
- data.py:305-311: the only addition is an `else:` under `if not retain_all:` with `df = df[df["elapsed_days"].notna() & df["q_mean_ah"].notna()]`. This is the C2 widening Shlok approved (D044, "Approval of the C2 widening"). The `retain_all=False` path is unchanged (context lines only).
- guard.py:215: `rec.get("frozen_commit") not in [fz["commit"], *(fz.get("predecessor_commits") or [])]`. This is the C1 option (a) that the earlier audit preferred.
- The test covers C1 and C2:
  - C2: missing capacities stay missing in the scrubbed table, and the test asserts finite `ret`. It also asserts that the no-capacity rows are 3, all step22_missing, and all fail QC.
  - C1: a listed predecessor is accepted, and an unlisted commit is still refused (match "frozen_commit").
- write_frozen.py:43-48, `--predecessor`:
  - requires the full 40-hex commit and refuses HEAD itself;
  - requires `merge-base --is-ancestor` (check=True raises);
  - writes `predecessor_commits = [full]`.
  - Nothing else in the payload logic changed. The refusals for an existing FROZEN, dirty code/ or runs/prereg/, MANIFEST mismatch and 276 distinct configs are untouched (write_frozen.py:26-42).
- Tree state: `git status --porcelain --untracked-files=no -- code runs/prereg` is empty. `git status --untracked-files=all -- code` has no entry except __pycache__ (code/.pytest_cache carries its own ignore). `merge-base --is-ancestor ce0cc0d HEAD` is true.

## 2. Re-pin payload equals the archived FROZEN except `commit`: MET
- The archive runs/freeze_runs/archive/FROZEN_ce0cc0d.json has sha256 8fcfb33993a9b41b9314f0cd919f48176f01855ca91ba04b30b9dbc5f0d8ed2a. That equals the hash recorded at the freeze (DECISIONS.md:823, D043). The file is byte-identical to `json.dumps(old, indent=1)+"\n"`, the writer's format, so it is the unedited original.
- I built the payload in-process exactly as write_frozen.py:33-36 does: `guard.build_freeze_payload(ROOT, SPLIT_KEYS, mcc.freeze_config_paths(), prereg_file="runs/prereg/PREREG_v4.md", require_pins=True, item_f_config_paths=5 item (f) configs)`. Field by field against the archive:
  - commit: differs (ce0cc0da1e1c... -> c6a89b6b2125...). This is expected.
  - equal: config_sha256s (276, 276 distinct, same order), item_f_config_sha256s (5, same order), pins, pins_missing, prereg_file, prereg_sha256, splits.
  - The old dict with commit replaced and `predecessor_commits=[ce0cc0d]` added equals the new payload plus predecessor: True.
- runs/prereg/FROZEN is absent before and after the simulation (`guard.is_frozen` False).

## 3. Retain configs pinned, unscored; blocked folders setup only: MET
- The 10 configs row_retain_B_f{0..4}_g{1,4}.json all carry `retain_all: true`. Their canonical hashes (4b95a39c182d, 6e4c69432e69, 6f8d96647a7c, 5c1a16d54c62, 45edea4cea77, 8b9c6dd1a46e, b15e8b729b45, 19969062478f, 13071b9d28e8, 62196b1d6c2e) are all in the old and in the new config_sha256s.
- SCORED.jsonl:
  - 266 rows, 266 distinct hashes (samsung 256, isu 10), all at commit ce0cc0da1e.
  - 0 rows with row_retain in run_id; none of the 10 retain hashes is present.
  - FROZEN minus SCORED is exactly the 10 retain hashes.
  - All Samsung rows carry one item_f_sha256 (2823abd22e52...).
  - sha256 ea82eca80aa27a943c46e89865b3a9753af531ac331b976d43311b6ab6413090, unchanged and equal to SCORED_backup_pre_suite.jsonl.
- campaign_state.jsonl:
  - all 266 non-retain run_ids have rc 0; no retain run_id has rc 0;
  - the 3 retain rows are rc 1 and not blocked;
  - campaign.log:118 shows "campaign start HEAD ce0cc0d; 5 item (f) + 266 confirmatory configs", and :559 shows "campaign ALL DONE".
- Blocked folders runs/row_retain_B_f0_g1, _f0_g4, _f1_g1: each holds only config.json, env.json, git.json, seeds.json and RUN.log (0 bytes). There is no condition_scores, prediction or metric file. Each git.json commit is ce0cc0d. No other row_retain_* folder exists, and runs/_blocked_d044/ does not exist yet.

## 4. Does anything else break when FROZEN's commit moves to c6a89b6? NO (one driver behaviour to handle, see P3)
`git grep` for commit, frozen_commit, git.json and rev-parse over code/, runs/confirmatory and runs/freeze_runs, plus a grep of every read_freeze/verify_freeze consumer, gives:
- guard.verify_freeze (guard.py:98-100) compares HEAD with FROZEN commit and passes at c6a89b6. It is used by require_frozen (run.py:295, run.py:501, data.py:559), check_config_frozen (guard.py:157, check_git=False, hashes only), stats_v4.build_item_f (stats_v4.py:658, not re-entered: the item (f) file exists, run_campaign.py:184) and run_campaign.py:171-173 (FROZEN commit == HEAD).
- guard.require_item_f_record (guard.py:215): handled by C1, simulated below.
- extraction_audit.require_calibration (extraction_audit.py:555): reached only through stats_step.py:852-853 on the licences=True path, which D022b refuses (stats_step.py:846-848). It does not apply.
- stats_step.py: frozen state is `guard.is_frozen` (existence, :778, :786, :790). `prov["head"]` only records HEAD (:823). Nothing compares per-run commits.
- stats_v4.require_item_f (stats_v4.py:771-780) checks that all Samsung ledger rows carry one item_f_sha256. The retain rows will carry the same value, because require_item_f_record returns 2823abd22e52 under the new FROZEN (4b). The `commit` field of ledger rows is never checked for uniformity.
- run.py writes git.json (run.py:65, 353) and the ledger commit (run.py:502); neither is read back anywhere. blinding.py:108, :129 and stats_v4.py:129 read only `pins` (unchanged).
- read_freeze needs a superset of {commit, prereg_sha256, splits, config_sha256s} (guard.py:71), so the extra `predecessor_commits` key is accepted. No consumer compares the key set for equality.

4b. Simulation with the would-be FROZEN, in memory only: `guard.read_freeze` and the FROZEN isfile check were patched, nothing was written.
- verify_freeze(check_git=True, untracked_under=("code",)) with new payload + predecessor: PASS.
- require_item_f_record with new payload + predecessor: PASS (returns 2823abd22e52).
- require_item_f_record with new payload WITHOUT predecessor: REFUSED, "the item (f) record's frozen_commit is not the FROZEN commit". So `--predecessor` is required.
- Control, archived ce0cc0d FROZEN: require_item_f_record PASS, and verify_freeze at HEAD c6a89b6 REFUSED ("HEAD c6a89b6b21 is not the frozen commit ce0cc0da1e"). So the old FROZEN could not have been reused.
- check_config_frozen for row_retain_B_f0_g1 and row_retain_B_f4_g4: PASS (4b95a39c182d, 62196b1d6c2e).

## 5. Test suite at c6a89b6 (main checkout): SUITE PENDING
- At this report's writing, scratchpad\suite_c6a89b6.txt has no final summary line. Progress is at 56%+, with no F or E characters in any progress line so far.
- Baseline (worktrees, ce0cc0d and fdb7f44): 22 failed + 12 errors, all from missing data/run files in a worktree. The main checkout has those files, so fewer failures are expected.
- The lead compares the result. A failure in data.py retain logic, guard.py (item (f) record / predecessor), write_frozen or test_d044_retain_undated.py is a blocker: do not write FROZEN.

## Conditions (all before or at the re-pin; none reopens the code)
- **P1 (order):** write FROZEN only after the suite has finished and the comparison in item 5 is clean. Re-run `git status --porcelain --untracked-files=all -- code` just before, so no untracked non-cache file under code/ makes write_frozen.py:59 fail after it has written. Command: `.venv/Scripts/python.exe -P runs/freeze_runs/write_frozen.py --predecessor ce0cc0da1e1c8750846a409935ff1c3dbd1e53bc`, with the full 40-hex commit and without --dry.
- **P2 (record):** after writing:
  - compare the new FROZEN with the archive; only `commit` (c6a89b6) and the new `predecessor_commits` may differ;
  - record the new FROZEN sha256 in a D row. The archive stays at sha256 8fcfb339...ed2a.
- **P3 (driver):** move the 3 blocked folders to runs/_blocked_d044/ BEFORE relaunching run_campaign.py. If a folder exists, run_campaign.py:111-114 logs BLOCKED and skips the config instead of running it. Then relaunch with SKIP_PREFIX unset. The expected queue is exactly the 10 retain configs (266 already rc 0 in campaign_state.jsonl, run_campaign.py:128-129). HEAD must not move while those runs are in flight.
- **P4 (disclosure correction, append-only):** D044 says "the other 219 configs run at ce0cc0d" (DECISIONS.md:844, :850), and my earlier audit repeated 219 (GATE_D044_retainfix.md items 5 and C3). The evidence says 266: SCORED.jsonl has 266 rows at ce0cc0d, campaign.log:118 shows 266, and campaign_state has 266 rc 0. Append a correction row; do not edit the old text. The paper's disclosure must say 266 runs at ce0cc0d and 10 at c6a89b6.
- **P5 (carried over, non-blocking):** the D044 test's `pd.read_csv(SRC)` still loads the real capacity columns into memory before scrubbing them. Nothing is printed. A `usecols` that excludes them would be stricter.

Gate status: re-pin authorised under P1-P4, subject to a clean suite comparison (item 5).
