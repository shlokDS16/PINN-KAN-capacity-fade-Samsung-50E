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
