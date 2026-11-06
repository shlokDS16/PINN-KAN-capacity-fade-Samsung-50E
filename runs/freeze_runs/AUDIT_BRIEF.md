# Gate-auditor brief: freeze audit of PREREG_v4 (lead, 2026-11-06)

Project root: `C:\Users\Shlok\Downloads\PINN KAN battery paper` (branch main, main checkout; D031). Operating rules: `research/CONTRACT.md`.
You are the validator, not the proposer. Read only what each check needs (PREREG_v4.md is 248 KB: grep `^## `/`^### ` and read line ranges).
Do NOT open any Samsung retention value, prediction or test-fold file. Do NOT run anything that loads a Samsung test role. Do not commit, do not
edit tracked files, do not write runs/prereg/FROZEN. Write your verdict to `research/audits/GATE_freeze_audit.md` (untracked) and reply in <= 5 lines.

## Commits
- FB runs ran at candidate commit 92db4cb (`runs/freeze_runs/logs/queue.log` line 1: HEAD and dirty count 0; every run's `git.json`).
- The lead then made one text-only commit (HEAD now): PREREG status line FROZEN-ready, 17.1/17.2 statuses of FB-8/9/10 and C27, the FB-8b script,
  DECISIONS row. Check `git diff --stat 92db4cb HEAD -- code` is EMPTY and `git diff 92db4cb HEAD -- runs/prereg` touches only PREREG_v4.md
  outside section 11 (section 11 = lines from `## 11. Outcomes` to before `## 11a.`).

## Checks (PREREG_v4 17.1 lines ~490-505, 17.2 lines ~506-537, 18 lines 554-566)
1. **C21:** sha256 of section 11 text equals the value the rev. 16/17 signatures record (001b1c79...e9; see
   `research/audits/SIGN_redteam_rev16.md` and `SIGN_statistician_rev16.md`) and section 11 = J16 section 4 as amended only by D030 and D034
   (`research/DECISIONS.md` rows D017, D030, D034; `debates/D016_roles/02_judge.md` section 4; `debates/D033_signoff/01_judge.md` AUTHOR DECISIONS).
2. **FB-8:** `runs/fb8_timing_samsung_B_f{0-4}_m{8,32}/timings.json`: median A2 fit <= 30 s and median A1 fit <= 90 s (Partial-plan trigger,
   PREREG 7 line ~151); all rc=0 in queue.log; configs = primary confirmatory configs with only run_id and mode changed (`runs/freeze_runs/make_configs.py`).
3. **C27 / D023 A8-A9:** `runs/freeze_runs/fb8b/fb8b_f{0-4}.json` (script `runs/freeze_runs/fb8b_convergence.py`): convergence share >= 0.99 for
   A1 and A9 at m 8 and 32, nonfinite 0, training side only (role 'train'). Check that `code/pinnkan/inversion_diag.py` reads no outer label (D023 A9).
4. **FB-9:** `runs/fb9_nc1_full_synth_m{8,16,32}/nc1_full.json` passed, k 0/2/full, every arm of the grid config, short-record cells present.
5. **FB-10:** `runs/fb10_smoke_{isu,snl}_B0` rc=0.
6. **C15:** `runs/freeze_runs/logs/suite.log`: every test file passed (one pytest process per file).
7. **C28 / D032:** `runs/freeze_runs/D025_capped_cells.md` vs the `window_capped.json` of the FB-8 runs (identifiers only).
8. **C9-C11, C24, C26:** each against its row's evidence pointer in 17.2.
9. **Pins:** every entry of `guard.PIN_FILES` (code/pinnkan/guard.py line ~25, incl. stats_config.json and blinding_exclusions.json) exists and
   is tracked and clean; `runs/prereg/confirmatory_configs/MANIFEST.json` lists 276 files (groups primary 26, rows 36, sensitivity 195,
   exploratory 4, replication 10 -> config_sha256s; item_f 5 -> item_f_config_sha256s), every one at n_trials 40, and each listed hash equals the
   canonical hash of the file on disk; five item (f) configs under
   `runs/item_f/configs/` match 18 step 2b (only mode, run_id, arms, diagnostics, refit_timing differ from the g1 config).
10. **Tree:** `git status --porcelain --untracked-files=no -- code runs/prereg` empty; `runs/prereg/FROZEN` absent.
11. **Dry build:** `.venv/Scripts/python.exe -P -c` calling `guard.build_freeze_payload(root, split_keys, config_paths,
   prereg_file="runs/prereg/PREREG_v4.md", item_f_config_paths=<5>, require_pins=True)` with split_keys of 18 step 4 and config_paths = the 271
   non-item_f MANIFEST entries; print only the key set and counts (do not write FROZEN). Use `</dev/null` on every python call.

Verdict per check: PASS / FAIL / PASS-WITH-NOTE, each with a file:line pointer. Overall: FREEZE OK or NOT OK.
