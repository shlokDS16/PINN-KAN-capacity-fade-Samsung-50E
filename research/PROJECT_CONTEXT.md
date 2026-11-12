# Project context pack: PINN + KAN capacity-fade paper (read this first)

Every session and sub-session on this project reads this file before anything else. It says what we are
writing, for which journal, where the work stands and what comes next. Last updated 2026-11-07 by the lead
session. The Obsidian mirror is `C:\Users\Shlok\Downloads\obsidian\Claude code obsidian\Projects\PINN KAN battery paper\context\`.
Details live in the files named here; read only the ones your task needs.

## 1. Goal and venue
- **Journal: Journal of Energy Storage (JES), Elsevier, ISSN 2352-152X** (D001). Every display item, section
  and sentence is built for JES. The aim is the strongest paper in our niche the journal has published.
- **Author guide:** `notes/JES_guide_for_authors_2026-11-04.md`. **Style guide:** `notes/exemplars/JES_STYLE_GUIDE.md`.
  **What JES rewards, and where its best papers are weak:** `notes/exemplars/BLUEPRINT_v2.md`. Exemplar notes:
  `notes/exemplars/deep/` (Stroebl 2026, Lucu 2020 A/B, Richardson 2019, Guo 2022, PIKAN, PGKAN, KA-CRNN).
- **Author:** Shlok Kumar Goenka (VIT Vellore). Co-authors and the corresponding author are not yet recorded;
  ask Shlok, never guess.
- **Topic:** a physics-informed neural network whose degradation dynamics combine a storage (calendar) term
  (Arrhenius, Kolmogorov-Arnold network (KAN) of storage SOC) with a cycling term (KAN over temperature, SOC window,
  DoD and C-rates). It is trained jointly on storage and cycling cells and forecasts the capacity retention of
  cells at held-out stress conditions from their first check-ups (D005, D016).
- **Design R2** (`debates/D016_roles/02_judge.md`): data-efficiency grid m = 8/16/32 cycling conditions x k = 0/2/full
  check-ups (g1 = (8, 2) headline cell, g4 = (32, full)); PINN attribution by an ablation ladder; KAN closed-form law
  against an equally simplified GAM law; a closed outcome table of titles T1-T9 (PREREG_v4 section 11, approved by
  Shlok, D017/D019/D030). **The title is chosen by the table after the runs, never by hand.**
- **Data:** Samsung INR21700-50E (Stroebl et al., JES 142, 119552) is primary: 279 cells, 40 cycling + 19 storage
  conditions, 3 labs. ISU-ILCC is secondary and SNL is a check. NASA/CALCE is a descriptive addendum (D022).
- **Novelty (claim the combination only):** a closed-form PINN-KAN law with calendar and cycle ageing together, the
  check-up (k) axis, and paired condition-level tests. Nearest prior work: PIKAN, PGKAN (JES 2026), KA-CRNN
  (JES 158, 121853), PiDDM (arXiv 2607.29095), Lucu 2020 A/B (learning curves; D029). See `notes/papers/PRIORART_SUMMARY.md`.

## 2. State on 2026-11-07
- **Preregistration:** `runs/prereg/PREREG_v4.md` rev. 23. Statistician and red team have both SIGNED every row,
  including the C-rate ablation row 9.9 (u) (D041). Section 11 sha256 `001b1c79...c9e5` must never change.
- **FROZEN (2026-11-07):** `runs/prereg/FROZEN` written at commit `ce0cc0d` (PREREG_v4 rev. 24; code identical to
  `d13a8c6`); gate auditor FREEZE OK (`research/audits/GATE_freeze_recheck_ce0cc0d.md`); `verify_freeze` passes (D042, D043).
  All freeze-commit runs passed at `d13a8c6` (timing, convergence, NC-1 invariance, smoke, 888 tests, head comparison).
  **HEAD of the main checkout now stays at `ce0cc0d`.** Edits there are allowed only outside `code/` and `runs/prereg/`,
  and stay uncommitted until the confirmatory statistics are done.
- **After FROZEN:** the item (f) runs, then the confirmatory runs (about 32 CPU-h plus 4-5 CPU-h for row (u)).
  **Started 2026-11-07 12:21 on Shlok's go-ahead** by `runs/confirmatory/run_campaign.py` (3 single-thread CPU lanes; item (f)
  runs, then `stats_v4.build_item_f`, then the 276 configs in section 15 order). Status: `runs/confirmatory/campaign_status.json`
  and `logs/campaign.log` (return codes and times only). **No session reads a score, prediction or metric before the campaign
  ends** (stop rule 6). Pause: create `runs/confirmatory/STOP`. Keep other CPU jobs light and the charger in.
  Item (f) finished 13:35 (5 of 5 rc 0; item (f) file and record written). Worker count is read live from
  `runs/confirmatory/LANES` (1-3); it is 1 from 13:36 while the Thenboli-paper ACME GPU queue needs 6 GB free RAM, then 3.
  **3 lanes from 2026-11-08 01:32** (ACME queue ended 01:24); 3 jobs running, about 0.7 GB each, 6.4 GB RAM free. Observed:
  the g4 (m32) runs take about 5.0-5.4 h each on one thread (f0, f1 rc 0), so the 37 CPU-h estimate is too low.
  08 Nov 07:07: 6 of 276 rc 0, none failed. Rough rest from arm counts in the configs (about 0.29 h per arm at m 32,
  0.14 h at m 8): about 220 CPU-h, so about 3 days on 3 lanes (range 2-4 days), finishing around 10-12 Nov.
  Watchdog `runs/confirmatory/watchdog.py` (no scores read; every 10 min) exits to wake the lead on a failed or blocked run,
  a HALT, the end, RAM under 1.2 GB, the laptop on battery, or 9 h without a log line. Shlok asked (08 Nov) for mid-campaign
  training changes; declined: the frozen code and plan cannot change after FROZEN (D031, stop rule 6); improvements go to a
  labelled exploratory section after the confirmatory statistics.
  **Planned hibernation Mon 09 Nov 07:00 (Shlok travels):** the watchdog writes STOP at 04:00 so the running jobs finish and no
  job is in flight at hibernation (an interrupted confirmatory run leaves a folder that blocks its re-run). On return: delete
  `runs/confirmatory/STOP` and relaunch `run_campaign.py`; it resumes from the state file.
  08 Nov 16:02: free RAM fell to 0.6 GB (Claude app 6.8 GB, Chrome 6.1 GB, memory compression 3.4 GB; our 3 jobs about 2.2 GB).
  LANES set to 2 as a precaution; back to 3 when RAM frees up. Watchdog restarted with MIN_FREE_MB=300. 29 runs ended, all rc 0.
  08 Nov ~17:50: Shlok closed apps ("Done, use 3"); 1.5 GB free with 2 jobs running; LANES set back to 3 (written 18:19).
  08 Nov 20:53: watchdog fired at 298 MB free; commit charge 99.5 of 101.7 GB (node 212 procs 39 GB, Claude app 22 GB, our 3
  runs 3.4 GB). A full commit limit can crash a run mid-way (blocked folder). LANES set to 2; watchdog now also alarms on
  commit headroom < 1 GB (MIN_COMMIT_MB=1000, MIN_FREE_MB=200). 35 runs ended, all rc 0. Do not quit the Claude app while
  the driver runs: it was launched from a session shell.
  **09 Nov 02:52 HALT:** row_retain_B_f0_g1, _f0_g4, _f1_g1 rc 1 after ~6 s (setup crash; folders hold setup files only, so they
  are blocked). All 10 retain configs use retain_all: true (data.py:305), so all will likely fail. Not relaunched; error output
  not read (stop rule 6). 46 confirmatory + 5 item (f) rc 0. Decisions for Shlok in status/STATUS_MORNING.md (read the error
  line? code fix = new D row + gate audit; archive and re-run the 3 folders; run the rest with retain rows last).
  **09 Nov 22:3x (Shlok: "check why the error occurred"):** cause = 3 undated check-ups (no_start_date, NaN time) kept by
  retain_all (D044, proposed). Fix on branch `retainfix` (worktree `PINN KAN battery paper-retainfix`), test red on ce0cc0d, green
  with the fix. Campaign relaunched 22:34 with SKIP_PREFIX=row_retain_ (219 configs left, LANES 2); watchdog without a pause.
  Retain rows run last, after the fix is committed and FROZEN re-pinned (gate auditor + Shlok's yes).
  D044 approved by Shlok 09 Nov; fix committed on retainfix (76ba298). Shlok: use spare RAM, but ask other sessions first.
  CRP-S09 P2 replied "Fine, 3 ok" (no ACME GPU/RAM jobs planned; they lower LANES first if that changes); LANES = 3.
  Watchdog also wakes the lead when LANES < 3 and >= 4 GB RAM and >= 6 GB commit stay free for 30 min (ask, then raise).
  Gate audit D044: OK WITH CONDITIONS (research/audits/GATE_D044_retainfix.md); C1 (predecessor_commits in FROZEN) and C2 (drop
  rows with no capacity too; 6 rows total) applied on retainfix fdb7f44; suite identical to baseline apart from 7 new passing tests.
  C2 widening approved by Shlok 09 Nov. At the re-pin: write_frozen.py writes predecessor_commits=[ce0cc0d]; archive the old FROZEN first.
  10 Nov 00:06: paused for the night (STOP file; HALT logged; nothing running); 54 confirmatory rc 0. Resume: delete
  runs/confirmatory/STOP, LANES 3 (ask CRP-S09 if RAM is tight), relaunch run_campaign.py with SKIP_PREFIX=row_retain_ in the
  background, then the watchdog (MIN_FREE_MB=200 MIN_COMMIT_MB=1000 UP_FREE_MB=4000 UP_COMMIT_MB=6000).
- **Manuscript:** drafts of sections 1-5 in `paper/draft/` (outcome-independent text only). Prose check report:
  `paper/draft/PROSE_CHECK_REPORT.md` (232 flags). Figures are SYNTHETIC demos in `paper/figures/` until the runs exist.
- **Writing (branch `writing`, `78e2128`):** five outcome-independent blueprint gaps closed; 22 passages flagged for Shlok
  in `paper/draft/WRITING_REPORT_2026-11-07.md` on that branch (4 unverified cite keys, missing Guo 2022 and SEI refs, over the word budget).
- **Exemplars (branch `exemplars`, `6e8b80e`):** all 9 paywalled JES papers read with deep notes; every [PENDING] rule in
  BLUEPRINT_v2 and the style guide resolved; `notes/exemplars/EXEMPLARS_REPORT_2026-11-07.md` lists 8 items for the lead
  (2 would be new exploratory analyses: Nájera/Olmos fixed-form comparators, a leave-one-cell-out score; Shlok's call).
- Branches merge into main only after the confirmatory statistics (HEAD must not move before then).
- **Token plan to Mon 2026-11-09 ~07:00 (Shlok, relayed by CRP-S09 P2, 7 Nov 16:20):** this paper up to +20 weekly points
  (52% at the start), the ACME paper up to +22, 3 in reserve. Hard stop at account weekly 97%; past 94% finish the current step
  and start nothing new. No Fable. At most 1-2 agents at once (RAM). Check `get_usage` at each phase boundary; tell CRP-S09 P2 if
  the account passes 90% early.

## 3. Plan and workstreams
| Stream | Owner | Where | Done when |
|---|---|---|---|
| Freeze (record commit, audit, FROZEN) | lead session | main checkout | **done 2026-11-07** at ce0cc0d |
| Confirmatory runs and statistics step | lead (runs started 2026-11-07 12:21) | main checkout | strict statistics step outputs in `runs/` |
| Manuscript: blueprint gaps, outcome-independent text, prose QA | writing sub-session | branch worktree `writing` | sections pass prose_check, humanizer, hidden-unicode |
| Paywalled exemplars: read and fold into the blueprint | exemplar sub-session | branch worktree `exemplars` | **done** (6e8b80e) |
| Results text, figures from real runs, title from the table | lead + writer | after the runs | numbers all traced to `runs/` files |
| Novelty re-check (condition (d)) | novelty auditor | within 7 days of submission | verdict file |
| Submission package (JES Word template, highlights, graphical abstract, declarations) | lead + writer | last | render-checked PDF and Word |

## 4. Rules every session follows
- **Never move HEAD of the main checkout** (`C:\Users\Shlok\Downloads\PINN KAN battery paper`) once FROZEN exists, and
  never edit tracked files under `code/` or `runs/prereg/` there (D031; the guard refuses every run otherwise).
  Sub-sessions work in their own branch worktree: `git -C "<repo>" worktree add "<repo>-<name>" -b <name> d13a8c6`.
- **Never open Samsung retention values or any test fold before FROZEN.** The code guard enforces it; do not work around it.
- **No number in any document unless it comes from a file in `runs/<run-id>/`.** A number not yet available is written
  `[RESULT: what, file, field]`. No citation unless verified (DOI/Crossref) and checked against its sentence (`paper/draft/refs_verified.md`).
- **Claim sentences, titles and tier words are fixed** by PREREG_v4 sections 11 and 11a; never paraphrase them.
- **Retired topics** (Shlok's earlier paper): the effect of the evaluation split on SOH/RUL accuracy; conformal or
  uncertainty calibration under shift. Leakage-free evaluation is standard practice here, never a contribution.
- **AI use** is stated only in the Declaration of generative AI use (every tool, every use), nowhere else.
- **Prose QA on every text:** `research-humanizer` skill, `hidden-unicode` scan, then `tools/prose_check.py`
  (LanguageTool + Vale + JES rules; `tools/PROSE_CHECK_README.md`). Give Shlok the flagged passages with file:line.
- **Models:** no Fable. Sonnet for implementers, Haiku for mechanical work, Opus for the hardest piece or a final
  review; pass `model` explicitly. At most 3 agents at once per session. Proposer is never validator.
- **Compute:** CPU only unless Shlok says "GPU ok"; CRP sessions use the GPU. Keep our CPU jobs near 3 GB RAM.
- **Python:** call `.venv/Scripts/python.exe -P` with `</dev/null`; never a bare `python -` (it hangs). Untrusted
  downloads run with `-I` in their own directory. Use Write/Edit, not heredocs, for code with backslashes.
- **Browser:** never enter credentials, solve CAPTCHAs or answer Cloudflare checks; ask Shlok.
- **Decisions:** append-only rows in `research/DECISIONS.md` (D001-D041 so far); a re-opened decision gets a new row.

## 5. Where things are
- Shared spec for agents: `research/CONTRACT.md`. Running log: `research/progress.md`. Decisions: `research/DECISIONS.md`.
- Audits and signatures: `research/audits/`. Debates: `debates/`. Paper drafts: `paper/draft/`. Code: `code/pinnkan/`.
- Code graph: `graphify-out/` and the vault's `MODULE_MAP.md`; ask `graph-memory where <symbol>` before grepping.
- Writing agent: `.claude/agents/jes-research-writer.md`. Morning status for Shlok: `status/STATUS_MORNING.md`.
