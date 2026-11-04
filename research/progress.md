# Progress

## RESUME (update at every phase boundary)
- 2026-11-04 20:35 start. Lead: Opus session (side session of the Paper 2 TNNLS session).
- Budget: weekly all-models 5% at start, Fable 0%. Session cap tonight: +12 points (to 17%); may be
  extended for quality (memory quality-over-token-budget), Shlok told in the morning.
- CPU only tonight (D002). At most 3 agents at once (RAM 3.6 GB available).
- Phase 1 (running): references fetched/verified; PIKAN + PINN4SOH + kan-review read; dataset
  inventory and downloads.
- Next: paper extraction (35 refs, full text where available), exemplar dissection (PGKAN JES 2026
  first), candidate topics, debate, novelty audit, red team, preregistration, first CPU runs.

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
