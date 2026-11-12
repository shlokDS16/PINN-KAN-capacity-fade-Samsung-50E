# Progress

## RESUME (updated 2026-11-12 12:45 by the lead; read this first, after research/PROJECT_CONTEXT.md)
- **Manuscript FINAL (JES), submission package built:** writing worktree `paper/submission/` (manuscript .docx/.pdf, 67 pages,
  docx-PDF parity verified; highlights, cover letter, statements, graphical abstract, figures Figure_1-6, D1, D2; checklist;
  SHA256SUMS). Writing branch commit 8d88aac. Outcome P0/K=, title T5 (unchanged). Body 5,993 words, abstract 250, 10 display items.
- **Checks done:** acceptance-risk panel (red team, battery-domain reviewer, Codex session 01a1cde1-894c-7840-a8e9-8eea99cd1f9e,
  three rounds), fix rounds, final number audit (research/audits/GATE_manuscript_numbers_2026-11-12.md), research-writer prose
  loop (LanguageTool with n-grams at C:\Users\Shlok\tools\lt-ngrams + Vale), production page-by-page review of PDF and docx.
- **Deposits:** GitHub private repo shlokDS16/PINN-KAN-capacity-fade-Samsung-50E (main up to 4e339b0, tag v1.0-frozen = c6a89b6);
  Zenodo package release/zenodo_v1.0.0/ (DOI 10.5281/zenodo.24153388 reserved by Shlok; he uploads and publishes; ZENODO_FORM.md).
- **Open for Shlok:** processor and memory (App. B.3); funding grant number and sponsor-role sentence; keywords; preprint status;
  never rejected by JES; suggested reviewers (optional); co-authors confirm CRediT and competing interests; publish Zenodo before
  submitting; decide whether the AI declaration should be widened (actual use broader than "language and grammar"); venue choice
  (lead's estimates: JES roughly 25-40 %, Energy and AI 40-55 %, Sci Rep / PLOS ONE 60-75 %; judgement, not data).
- **Before the repo goes public:** remove publisher PDFs under refs/ from the history.

## RESUME (updated 2026-11-12 06:50 by the lead; read this first, after research/PROJECT_CONTEXT.md)
- **Confirmatory statistics DONE** (06:15, strict, frozen at c6a89b6, not provisional). Outcome from the table: gate G not
  tripped; P0, K=; title T5. Validated: statistician (research/audits/SIGN_statistician_frozen_stats.md) and gate auditor
  (research/audits/GATE_stats_frozen.md), both PASS WITH CONDITIONS. Details and hashes: DECISIONS D045, "Frozen statistics step
  run", D046 (post-freeze arm table, runs/stats_frozen/post/).
- **Running (12 Nov, 06:45):** descriptive extras into runs/stats_frozen/extras/ (statistician); real figures and tables into
  the writing worktree paper/figures, paper/tables (figure-smith); Results, Discussion, Conclusions, abstract, highlights in the
  writing worktree (manuscript-writer). Shared spec: writing worktree paper/draft/RESULTS_BRIEF_2026-11-12.md.
- **Next:** fill [EXTRAS]/[FIG] placeholders, red-team the manuscript, prose QA (research-humanizer, hidden-unicode), build and
  render-check PDF and docx. Deadline Fri 13 Nov night.
- **HEAD:** still c6a89b6; doc edits in research/ and runs/stats_frozen/ uncommitted (commit after the extras are done).

## RESUME (updated 2026-11-09 03:20 by the lead; read this first, after research/PROJECT_CONTEXT.md)
- **Campaign HALTED 2026-11-09 03:16** (driver rule: 3 failed runs). Nothing is running; laptop hibernated for travel.
  Done with rc 0: 5 item (f) + 47 confirmatory (main grid g4/g1/m16, NC-2, Test C, lab-indicator rows, random-subset rows).
- **Failed:** row_retain_B_f0_g1, row_retain_B_f0_g4, row_retain_B_f1_g1: rc 1 after ~6 s (setup crash, no training,
  folders hold setup files only, so they are blocked). All 10 retain configs set retain_all: true (data.py:305); expect all to fail.
  The error output (logs/row_retain_*.out) has NOT been read (stop rule 6).
- **Waiting on Shlok** (status/STATUS_MORNING.md, top entry): (1) may the lead read only the error line; (2) a code fix
  breaks the freeze: new D row, gate-auditor re-check, Shlok's yes; (3) archive the 3 blocked folders and re-run after the fix,
  logged as a deviation; (4) run the rest of the plan with the retain rows last (order change, logged as a deviation).
  The stats step needs the retain-all row (stats_step.py:796).
- **To resume after a decision:** charger in; check RAM and commit headroom (09 Nov: other sessions' node helpers held 39 GB of
  commit); LANES = 2 unless RAM allows 3; no STOP file exists; relaunch
  `.venv/Scripts/python.exe -P runs/confirmatory/run_campaign.py </dev/null` in the background, then the watchdog
  (`MIN_FREE_MB=200 MIN_COMMIT_MB=1000 .venv/Scripts/python.exe -P runs/confirmatory/watchdog.py </dev/null`).
  HEAD ce0cc0d, code/ clean (checked 03:00).

## RESUME (updated 2026-11-07 by the lead; read this first, after research/PROJECT_CONTEXT.md)
- **State:** FROZEN at ce0cc0d (PREREG_v4 rev. 24; code identical to d13a8c6). Gate auditor FREEZE OK
  (research/audits/GATE_freeze_recheck_ce0cc0d.md); verify_freeze passes; FROZEN sha256 8fcfb339...ed2a (D042, D043).
  Statistician and red team signed every row, including C-rate row 9.9 (u). Freeze runs at d13a8c6 all pass (D042).
- **HEAD must not move** in the main checkout; D043 and the status/context edits stay uncommitted until the statistics are done.
- **Branches:** writing (78e2128; blueprint gaps, 22 flagged passages), exemplars (6e8b80e; 9 paywalled papers read).
- **Campaign STARTED 2026-11-07 12:21 (Shlok: "Yes, start runs"):** `runs/confirmatory/run_campaign.py` (untracked, outside code/),
  3 CPU lanes: 5 item (f) inner runs -> stats_v4.build_item_f -> 276 confirmatory configs in section 15 order (g4, g1, m16,
  NC-2, C, rows, sensitivity, crate, S2, replication, A/S3). Return codes in runs/confirmatory/campaign_state.jsonl; status in
  campaign_status.json; pause with runs/confirmatory/STOP; a re-launch resumes. No score is read before the end (stop rule 6).
- **Was next:** item (f) runs (5 configs, runs/item_f/configs), then the confirmatory runs
  (276 configs, about 37 CPU-h; A1 fit time was 31.5 s under shared CPU), then the strict statistics step at ce0cc0d.
- **Context for every session:** PROJECT.md, research/PROJECT_CONTEXT.md; Obsidian knowledge hub (tools/vault_knowledge.py).

## RESUME (updated 2026-11-06 11:00 by the lead; read this first)
- **State:** Design R2 approved (D016/D017/D019); PREREG_v4 rev. 13 (d551e8a; section 11 byte-identical to J16). Decisions
  D026 (item (f) after FROZEN, ledger-gated), D027 review, D028 config rulings. Code: 740 tests pass (53abf0e); 276 confirmatory
  configs + MANIFEST (code/prereg/make_confirmatory_configs.py). Pilot P6 done: stop rule 10 not triggered (d8d7034).
  C26 signed by the red team (bc9e4c4). D025 window cap coded (835d1aa).
- **Checklist:** runs/prereg/PREFREEZE_STATUS.md (gate auditor, f24c2a3; needs a refresh) + PREREG 17 (rev. 13 statuses);
  remaining code-side items in runs/prereg/CODER_QUEUE.md (item 10: untracked negctl folders under runs/prereg).
- **Blocked on Shlok:** Hallinger SSRN 7417281 PDF or waiver (FB-2, C8); Lucu 2020 A/B and Jia 2024 PDFs or waiver (C4).
- **Next (lead):** novelty auditor confirms FB-1 and does C4 when the PDFs arrive; designer C20 final-text pass (stale evidence
  cells, markers); statistician and red-team signatures; candidate freeze commit in a FROZEN worktree (CRLF: compute pins
  there); FB-8 timing on a pinned primary config (zyk, tournament, k grid), FB-9 nc1_full, FB-10 smoke, full suite; gate-auditor
  freeze audit (C21, C28, pins); lead writes FROZEN; then the item (f) runs, then the confirmatory runs.
- **Data:** Samsung full release verified; CALCE PL 7 of 8 zips (tools/fetch_calce_queue.sh retrying the last).
- **Lesson:** the 5-6 Nov overnight stall was low battery (Kernel-Power 42); charger in for overnight runs; tools/keep_awake_while.py covers idle sleep only.

## RESUME (older: 2026-11-05 ~04:15 by the overnight lead session)
- **State:** topic and method decided by debate (D005 -> D011 -> D016). Current design = **Design R2**
  (debates/D016_roles/02_judge.md): data efficiency (8/16/32 cycling conditions x 0/2/full check-ups), PINN
  attribution by ablation ladder, KAN closed-form law vs equally simplified GAM law on held-out conditions,
  closed outcome table T1-T8 + M1/M2 **awaiting Shlok's approval**. PREREG_v3 exists (24ac12c) but predates
  D016: next is **PREREG_v4** implementing D016 + V3_EDITS + red-team freeze conditions (D015).
- **Freeze blockers:** FB-1 Zhang JES 182, 125097 read (Shlok's e-gateway); FB-2 Stroebl JES 142, 119552 read +
  A10 equations verified; FB-3/4 full Samsung download (10.29 GB, Shlok, fast network; keep both same-named zips)
  + stage assignment of all 279 cells; FB-5 ZYK throughput check (code ready: pinnkan/zyk.py); FB-6 window counts;
  FB-8 Samsung timing; FB-9 NC-1 full run at the candidate commit; FB-10 smoke re-run; statistician simulations
  for D016 (sign test with fold/lab-shared effects, power at the scarce cell); novelty re-check of the D016 framing;
  blinding exposures resolved (runs/prereg/BLINDING_LOG.md).
- **Code:** code/pinnkan (256 tests pass, ca66522/e24d4e8); FROZEN guard JSON-verified; NC-1 label-invariance in
  every confirmatory run. D016 needs about 3-3.5 days more code (subset selector over m, k = 0/2 windows, symbolic
  extraction with a frozen library for KAN and GAM, learning-curve statistics). Builder's 6 choices in
  runs/build_v1/RESULT.md 7.3 need an independent reviewer.
- **Data:** Samsung check-up fetch running detached (tools/run_samsung_cu_forever.ps1; log data/logs/samsung_cu.log;
  stop with data/STOP_SAMSUNG); ISU, SNL processed; bulk downloader paused (data/STOP_DOWNLOADS).
- **Papers:** 8 of 35 references read in full + dataset papers + PiDDM, Guo, KA-CRNN; draft sections 2-5 in
  paper/draft (citation audit fixed; 3 title-only JES cites to read). Figures: code/figures (synthetic demos only).
- **Next session order:** (1) Shlok's answers (table approval, PDFs, download); (2) PREREG_v4 (designer) +
  statistician simulations + novelty re-check; (3) D016 code; (4) ISU pilot P6; (5) freeze; (6) confirmatory runs;
  (7) manuscript on the JES Word template.
- **Budget:** weekly 11% at 03:30 (started 5%); Fable 0%. Lead context was about 76% at hand-off.

## Log
- 20:35 folder, contract, decisions ledger created; sign-in list sent to Shlok.
- 21:00 lead prior-art scan: PINN+KAN SOH with symbolic discovery is taken (PIKAN, PGKAN in JES 2026,
  PI-EKAN). See notes/PRIOR_ART_SCAN_lead.md.
- 21:15 Shlok: figure and table FORM must match the best JES papers; added CONTRACT 6a, D003, figure-form catalogue in the exemplar step. Codex panel thread live (debates/codex_panel/SESSION.md).
- 21:40 code reader done (notes/code/*.md). Lead verified PIKAN test-set tuning and per-cell whole-life scaling. PIKAN = JES 153, 120860 (2026). Candidates C1-C4 in debates/D010_topic/00_candidates.md; novelty audit running.
- 21:35-21:48 network drop (DNS) stopped 3 agents; resumed. Shlok: network fluctuating, downloads must resume; then "5 Mbps unlimited for one day". Built tools/resumable_download.py + tools/run_downloader_forever.ps1 (detached, restarts itself, resumes from bytes on disk, verifies checksums). Whitelist in data/DOWNLOAD_ALLOW.txt (core ISU/TJU/HUST/XJTU, then CALCE, SNU, NASA HIRF/randomized, eVTOL, TBSI, Samsung 50E; BatteryLife 31 GB and Stanford 17 GB wait). Live status: data/DOWNLOAD_STATUS.md. D004.
- 21:50 novelty audit done (debates/D010_topic/01_novelty_audit.md): C2 identifiability NOVEL (0.65), C1 INCREMENTAL, C3 leaning TAKEN; most dangerous prior work PiDDM arXiv 2607.29095. Proposer running (02_proposal.md).
- 22:00-22:20 debate D010: proposal (02), opponent REVISE (03), Codex turn 2 REVISE (codex_panel/turn02_response.md). Judge (Opus) running (04_judge.md).
- Network measured about 50 KB/s total (not 5 Mbps); downloader capped at 30 KB/s (data/DOWNLOAD_RATE.txt) to keep agent traffic alive; ISU Cycling_json/RPT_json skipped (too big tonight). tools/zip_range_fetch.py lists/fetches single members of remote zips by HTTP range (ISU cycling: 253 members, about 40 MB each). Samsung 50E metadata local: 132 calendar cells (19 cond.), 147 cycling cells (40 cond.), 3 temperatures; 10.3 GB total. SNL verified.
- 22:20 JUDGE (04_judge.md, D005): REVISE -> PINN (solution net + residual) with calendar term (Arrhenius x KAN(SOC)) + cycling term (KAN over T, SOC window, DoD, C-rates); Samsung 50E primary, ISU secondary, SNL check; pilots P0-P5 tonight; fallback ISU primary if Samsung check-ups not parsed by 07 Nov 09:00.
- 22:25 P0: Samsung per-cell zips hold ET/CU/exCU/ZYK/AT CSVs + tiny meta txt; CU about 0.1-0.35 MB each (runs/pilot_P0/*_members.tsv). Fetching CU+meta of 4 cells. Novelty re-audit (05) and two paper-extraction agents running. Project venv .venv (py3.14, torch 2.11 CPU use, pykan 0.2.8, optuna 5.0.0; requirements.txt).
- 22:40 P0 GO on schema: CU step_type 22 = full 1C-ish discharge -> capacity (4.88 / 4.82 Ah in the two probed cells). Bulk downloader paused (data/STOP_DOWNLOADS; link at 2-50 KB/s). Detached Samsung CU fetch for all 279 cells running (tools/samsung_cu_batch.py, status data/SAMSUNG_CU_STATUS.md). Note TP_k10_05 has no intermediate CU.
- 22:50 novelty re-audit: NOVEL as combination (0.6); mandatory comparator Stroebl JES 142, 119552 (dataset authors). D006.
- 23:05 P1 GO (ISU Table A1 0 mismatches; SNL 61 cells, no duplicates, one cell with 90 invalid rows excluded). P2: PINN GO (16-19 s per fit, 32 s for 279 tiled cells at 3 threads); hard ODE 38 s at 80 nodes per cell (1.28x budget) but cost scales with nodes, about 11 s at 20 nodes: lead rules hard-ODE arm GO for Samsung (<= about 20 check-ups per cell), 1 thread per process, 3 processes in parallel; partial plan (10 trials, 2 inner folds) only if a dataset needs > 40 nodes per cell. runs/pilot_P1, runs/pilot_P2.
- 23:30 exemplar dissection done (notes/exemplars/*.md, BLUEPRINT.md, 16 more FIGURE_FORMS rows). Flags: KA-CRNN (JES 158, 121853, MIT) = nearest method precedent (Arrhenius parameters as KAN of SOC in a neural ODE, thermal-abuse data); Zhang JES 182, 125097 cites Samsung data and uses a PINN, unread: top e-gateway item, novelty claim on hold until read. Samsung metadata: 59 unique stress conditions (19 storage, 40 cycling) vs 71 test points in the paper (tp numbers repeat across 3 labs); Table 1 must state both. Samsung CU fetch about 1 file / 30 s (figshare latency) -> about 60 cells by morning.
- 23:55 P4 GO (synthetic G2 on ISU design: KAN recovery nRMSE below additive GAM in 4/5 draws, median 0.081 vs 0.103; below free G 5/5; small margin, GAM oracle floor 0.05-0.07; tuned KAN at grid edges -> extend grids). P5 GO (soft PINN below hard ODE beyond window in 4/5, median 4.72 vs 5.37 pp; lambda=10 worse everywhere; no data-only arm in P5 -> add lambda=0 arm in confirmatory design). Constants in the generators are round numbers, not data-derived. runs/pilot_P4, runs/pilot_P5. Needs gate-auditor check before preregistration.
- 00:10 Preregistration DRAFT (runs/prereg/PREREG_DRAFT.md; H1-H7, arms A1-A14, decision table, compute 11-35 h on 3 processes at 20 trials; OPEN-4 margin feasibility, OPEN-5 Stroebl in Holm family). DATA BUG found by it and fixed: Samsung serial names repeat across 2 stages (141 stage-1 + 138 stage-2 = 279 distinct cells, different conditions); the CU fetcher had kept one zip per name. Fetcher now covers all 279 zips, folders <serial>__f<fileid>; 18 old folders renamed; pipeline agent told to key by (serial, stage) from measured dates. Confound flagged: 35 C cycling all lab INT, 45 C mostly HM, 10 C storage all SIE (temperature tests mix with lab; disclosed, lab/stage sensitivity row).
- 00:15 P3: non-inferiority for contrast (iii) on ISU (0.90) and SNL (1.13, weak) -> D007. Samsung pipeline done (runs/samsung_pipeline; cells keyed <serial>_s<stage>; stage 1 ran Sep 2021-Aug 2022, stage 2 from Jan 2023); fetcher now 2-phase (CU for all cells, then ET_T23/exCU/AT_T23).
- 00:25 Codex turn 3 (debates/codex_panel/turn03_response.md): viable as narrow conditional advance; primary contrasts should be (i) residual vs none, (ii) KAN vs strongest GAM/MLP stress map, (iii') Stroebl semi-empirical comparator, with data-only learners as non-inferiority; 35 C holdout framed as joint temperature-lab domain transfer, not temperature extrapolation; read Zhang/Hallinger/Stroebl first; activation-energy plausibility check only after literature verified. To go to a judge (D011, prereg revision) with the statistician ruling and gate audit.
- 01:00 D011 judge: primary Holm family H1a, H1b, H6 (Stroebl, with per-cell window factor); H1c key secondary; Test C = joint temperature-lab domain transfer; sign-flip permutation on log error ratios if type-I <= 1.2x nominal; likely outcome title 3. Designer making PREREG_v2; statistician running type-I simulation.
- 01:05 PREREG_v2 committed (f891119; freeze blockers FB-1..FB-8; splits v2 keyed <serial>_s<stage>; compute about 23 CPU-h expected, 67 ceiling at 20 trials). Started: confirmatory code build (runs/build_v1; test-fold guard needs runs/prereg/FROZEN), errata task (Haiku). Statistician type-I simulation running. Usage 8% weekly.
- 01:25 D012: sign-flip failed type-I check; exact sign test (median condition) per pre-set fallback; Test C descriptive. Errata committed (da467e8). FB-7 closed.
- 01:50 build_v1 done (code/pinnkan, 115 tests pass, FROZEN guard holds; A1 fit 14.5 s; A10 Stroebl provisional until FB-2). Started: code review (runs/build_v1/CODE_REVIEW.md), ML-expert ruling on 5 build choices (D013), figure scripts on SYNTHETIC demo runs (D-figures.md, code/figures).
- 02:00 code review: no blocker, 4 major (split hash fail-open, FROZEN file-exists only, S2/S3 target_kind default, negative control missing), 8 minor; builder fixing all (runs/build_v1/CODE_REVIEW.md).
- 02:15 D013 (ML expert): choices a, b, e accepted with wording; SNL pairs changed (charge rate constant in SNL training folds); clip 20 + warm-up 0.4 fixed recipe, clip also on A9/A2 (fairness for H1a); lam_res grid gains 1e-3 (lead confirmed). Builder applying review fixes + D013 C1/C2/C3/C4/C7. Prereg text edits C5/C6/C8/C9 pending (designer, with PREREG_v3 at the freeze).
- 02:12 builder fixes committed (c2ba6bf; 157 tests pass after the lead pinned the two probed-file tests to their zip). Lead rulings: m1 QC rule made causal (preceding check-ups only), m6 disclosed. Queued prereg edits in runs/prereg/V3_EDITS.md. Figure scripts still running.
- 02:35 figure scripts done (1a8c95f; 8 figures, 2 tables, graphical abstract; synthetic demos watermarked; lead render-checked fig1/fig2, notes in D-figures.md). Builder adding figure-input emitters + stats step (sign test). Prior-art full reading started (PiDDM, arXiv 2607.16864, KA-CRNN).
- 02:45 prior art read in full (notes/papers/priorart_*.md, PRIORART_SUMMARY.md): claim only the combination.
- 03:00 run writer emits all figure inputs; stats step implements D012/D009/Holm/H2; 170 tests pass (35b242a); figures regenerate end to end on synthetic outputs. Open: negative-control criteria may fail on leak-free pipeline -> statistician ruling (NEGCONTROL_RULING.md). Manuscript writer drafting outcome-independent sections (paper/draft/).
- 03:20 manuscript draft sections 2-5 (paper/draft/, 9da10dc, d46b7b2; about 3,900 words; A10 equations TO VERIFY; appendices A-C to write). Started: causal QC outlier fix (review m1), citation audit of the draft.
- 03:20 citation audit (80f17d2): 26 refs real, 4 corrected; gate FAILS on sentence support (sec 2.2 dataset claims, sec 3 count attributions, A10 source); writer fixing. QC drop rule ruled time-scaled (V3 edit 5).
- note: lead timestamps between 02:30 and 03:20 were estimated and partly too late; corrected where found; from 03:20 all times are taken from the system clock.
- 03:23 writer fixed all audit-flagged sentences (7976c1a, 2ec4b95); 3 title-only JES cites added to the e-gateway list. QC drop rule time-scaled (3415db2; 0 flags). Status file has a one-minute summary.
- 03:26 NC-1/NC-2 + seed rule + t_fc tests implemented (f3e0b2f; 205 tests pass; nc1_full synthetic demo max diff 0.0). Designer assembling PREREG_v3 (freeze-ready, blockers open).
- 03:32 PREREG_v3 committed (24ac12c; FB-1..6, 8, 9, 10 open; freeze procedure section 18). Started: builder for pre-freeze code gaps (H3, H7 pieces, ZYK branch, 11a, sensitivity rows, PREREG_DEFAULT=v3); red team on v3 + package (D015).
- 03:39 red team on v3: FATAL F1 (no demonstrable PINN/KAN benefit expected), F2 (outcome table open), 13 major. D015 recorded; D016 debate started (proposer). Builder filling code gaps.
- 03:52 D016: proposer Design R (data efficiency); Codex opponent REVISE; Opus judge running (02_judge.md).
- 04:05 D016 judge: REVISE -> Design R2 (data efficiency; ablation ladder; KAN law vs simplified GAM law on held-out conditions; closed table T1-T8 + M1/M2) committed. Status file section 00 asks Shlok to approve the table.
- 04:07 builder gap-fill done (ca66522, e24d4e8; 256 tests); 6 choices to confirm (RESULT.md 7.3) by an independent reviewer next session. Blinding log started (runs/prereg/BLINDING_LOG.md).
- 07:50 Shlok approved the D016 outcome table (D017, 9b9e0ee). Started: designer PREREG_v4, statistician sims (a)-(e) + graph_test, novelty re-check of D016 framing. Samsung fetch 115/279 at 07:42. Weekly 12%, cap for today 20%.
- 08:44 full Samsung download started (tools/samsung_full_download.py, 16 workers, md5; data/raw/samsung50e_full). Per-member CU fetch stopped (data/STOP_SAMSUNG).
- 08:50-09:45 e-gateway texts via Shlok's Chrome (VIT access): ScienceDirect PDFs cannot be saved by script; article full text captured into refs/fulltext/ (git-ignored). Chrome allows one automatic download per tab; texts staged in the site's localStorage and exported in batches. Rate limit ("Problem processing your request") after about 20 pages.
- 09:05 PREREG_v4 draft committed (adbd3d7). Novelty re-check: framing INCREMENTAL (Lucu JES 2020), KAN-law test NOVEL, "first" only as 4-part conjunction. Stats sims (0b2234b): size criterion FAILS for the plain sign test under fold/lab clustering; fallback rho_s0 = 0.03.
- 09:21-09:37 network drops. Codex turn 5 (opponent, REVISE). D018 judge (Opus, b29f6dd): fallback adopted, labs fixed strata, GAP-1 rule via d_c, w = 0.78 to be decided by a pre-ruled simulation, clause e1' needs Shlok (A6). Coder started D016 build (runs/build_v2). Designer (A1) and statistician (A2, A3) working on D018 actions.

- 10:30 Shlok approved e1' (D019, a9b8d87). Professor proposal published (paper/proposal/professor_proposal.html, https://claude.ai/artifact/SvUPGJp9zR6R75ufJ4gzAM; references Crossref-verified). Shlok: 'ensure we are producing only best outcomes' -> ML-expert (Opus) pre-freeze strengthening audit started (debates/D020_strengthen/01_mlexpert.md); legitimate levers only, comparators equal, no test-side choices.
- Afternoon: FB-2 closed (1b72843, A10 verified vs Stroebl JES 142). Code review saved (440cfb3); coder fixing I1-I7/M1-M9. Professor suggested adding NASA and CALCE datasets to the experiments; Shlok asked for novelty in the KAN itself. Combined debate D022 opened: data steward inventory (notes/data/NASA_CALCE_feasibility.md) running; KAN-novelty proposal (candidate: physics-shape-constrained KAN stress edges; novelty check vs monotonic-KAN work needed) goes to the method-architect after the cap task.
- Freeze lock extended (20e7a9d, 475 tests): FROZEN pins subsets.json, symbolic_library.json, item (f) file. AT THE FREEZE: call guard.build_freeze_payload(..., require_pins=True). Cap set to 2 (D021, 2334666) but re-opened inside D022 (KAN novelty). NASA/CALCE feasibility: notes/data/NASA_CALCE_feasibility.md (15fd0da).
- D022 ruled (179d4d2): NASA/CALCE descriptive addendum after FROZEN (card in runs/prereg_ext/); KAN contribution = identifiability-audited extraction (calibrated false-structure table + abstention); monotone KAN deferred; cap 2 confirmed. Actions A1 (designer), A2 (coder), A5 (data steward) running. Proposal page is shared publicly by Shlok: local update committed, republish only with Shlok's OK. Professor message (judge 1.7) waits for A5 confirmation of the PL design.
- D022 A2 done (3183bfb, 496 tests): extraction audit + calibration rule (3f0d492 first) + pins + stats guard; calibration NOT run (A4 runs from FROZEN). FREEZE HAZARD: core.autocrlf=true writes CRLF in a fresh checkout, so pinned hashes differ between main tree and worktree; compute FROZEN and config pins INSIDE the FROZEN worktree (or set core.autocrlf=false and renormalise first). verify_freeze needs HEAD == frozen SHA and clean code/ runs/prereg; copy untracked FROZEN and data/processed into the worktree. P6b: keep 2 inner folds (adopt false, e4edc74); inversion of A1/A9 not converged -> D023 proposal running. Saxena 2016 PDF requested from Shlok (CALCE PL design facts).
- Saxena 2016 PDF saved by Shlok (refs/pdf/saxena2016_jps_calce_pl.pdf); CALCE PL design confirmed (df45ff6). Professor message on NASA/CALCE approved by Shlok, he sends it (notes/data/professor_message_D022.md). Rev. 4 (D023, 7b557a5) and rev. 5 (D022a, 40ddc61) in PREREG; coder on D023 inversion then D022a audit; C26, C27 open.
- Red-team re-check of D022a audit (ba67242): no FATAL open; new MAJOR N1 = C1-C3 success likely unreachable for both arms (T sign licensed under lab aliasing; hinge truths labelled linear; G15 additive by construction scored as false on interacting inputs), N2 lab map from unpinned data/processed/samsung_cells.csv, N3 dropped-dataset detection/verdict recomputation. Next: D022 judge to rule on N1-N3 fixes (pre-calibration design fixes) or decide the descriptive fallback now. PAUSED at 21% weekly (cap 20%); Fable shows 3% though no agent in this session used Fable (all model params explicit) - reported to Shlok.
- D022b (8ded810): audit falls back to a descriptive stability table, no contribution claim, calibration skipped; KAN novelty = held-out K1/K2 test of the extracted law vs matched additive law (NOVEL 0.60), cap from D021. Weights: rule picked w = 0.78 (RESULT_weights.md; PREREG rev. 6 b242f71). Samsung download 279/280; TP_z05_01 had an empty md5 in DEFERRED_URLS (fixed to figshare supplied md5 f31e069a...), downloader restarted. Weekly cap raised to 30% by Shlok.
