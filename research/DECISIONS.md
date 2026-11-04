# Decision ledger (append-only)

Row format:

### D<NNN> <short name> (<date>, status: proposed | accepted | revised | rejected | superseded by D<MMM>)
- **Decision:**
- **Alternatives and why they lost:**
- **Evidence:** (file paths, debate file)
- **Proposer / opponent / judge:**
- **Re-open if:**

---

### D001 Project folder and venue (2026-11-04, status: accepted)
- **Decision:** project lives in `C:\Users\Shlok\Downloads\PINN KAN battery paper` (own git repo,
  outside the DLM repo); venue Journal of Energy Storage (Elsevier), as Shlok set.
- **Alternatives and why they lost:** inside the DLM repo (mixes projects and their ledgers); inside
  the old battery Paper 2 folder (risks reuse of its retired framing).
- **Evidence:** task brief from the lead session, 2026-11-04.
- **Proposer / opponent / judge:** lead (Shlok's brief; no debate needed).
- **Re-open if:** Shlok names another folder.

### D002 Compute and access for the night of 4-5 Nov (2026-11-04, status: accepted)
- **Decision:** CPU only tonight unless Shlok says "GPU ok"; at most 3 agents at once (3.6 GB RAM
  available at 20:35); no Chrome automation (no browser connected); paywalled full texts listed for
  Shlok to save by hand.
- **Alternatives and why they lost:** short guarded GPU chunks (standing order of 27 Oct: no
  unattended GPU; the CRP-S07 session uses the GPU tonight; PINN+KAN SOH models are small enough for
  CPU); 5 agents (RAM too low; crash history with low free RAM on 17-18 Oct).
- **Evidence:** memories laptop-gpu-crashes, parallel-research-sessions; `nvidia-smi` at 20:30.
- **Proposer / opponent / judge:** lead; rule-driven.
- **Re-open if:** Shlok gives a GPU go-ahead, or RAM frees up.

### D003 Figure and table form follows the best JES exemplars (2026-11-04, status: accepted)
- **Decision:** add a figure-form stage: catalogue the figure and table forms of the strongest JES
  papers, debate the form of each of our figures against that catalogue, build from run files,
  render-check against the exemplars (CONTRACT.md section 6a).
- **Alternatives and why they lost:** default matplotlib forms chosen by the implementer (looks
  weaker than what JES prints); forms copied from one exemplar (may not fit our claims).
- **Evidence:** Shlok's instruction, 2026-11-04 evening.
- **Proposer / opponent / judge:** Shlok (author's instruction).
- **Re-open if:** never dropped; the forms themselves are debated per figure.

### D004 Overnight download whitelist and resumable manager (2026-11-04 21:40, status: accepted)
- **Decision:** `tools/resumable_download.py` (detached process; pid in data/logs/downloader.pid)
  downloads only ISU-ILCC small files + Q_interpolated, TJU (3 zips + impedance), HUST and XJTU,
  about 6 GB, one file at a time, resuming from the bytes on disk after every drop (curl -C -),
  waiting with backoff while offline, pausing 00:05-00:30, verifying size and checksum.
  Status: data/DOWNLOAD_STATUS.md. Everything else in data/DEFERRED_URLS.tsv (about 76 GB:
  BatteryLife processed 31 GB, Stanford dynamic 17 GB, ISU cycling 10 GB, Samsung 50E 10 GB, others)
  waits for the dataset decision.
- **Alternatives and why they lost:** download the whole 82 GB queue overnight (mobile data from
  about 23:00, and most of it may never be used); download nothing until the topic is fixed (loses
  the night; TJU/HUST/XJTU and ISU are likely needed by the leading candidates or as comparison
  with prior art); several parallel connections (memory: at most 4 connections; one file at a time
  resumes most reliably).
- **Evidence:** Shlok, 21:35: network fluctuating; downloads must resume from where they stopped.
- **Proposer / opponent / judge:** lead; rule-driven (no debate needed for logistics).
- **Re-open if:** the dataset decision needs Samsung 50E, Stanford, MIT or the ISU cycling files.

### D005 Topic, title, method, datasets and experiments of the JES paper (2026-11-04 night, status: revised)
- **Decision:** debate D010, judge's verdict REVISE. The paper is a physics-informed neural network
  (solution network F with residual; dynamics G = storage (time-driven, Arrhenius with KAN functions of
  storage SOC) plus cycling (throughput-driven, hidden-layer KAN over T, SOC window, DoD, charge and
  discharge rate)) trained jointly on storage and cycling cells, forecasting retention of cells at
  held-out conditions from their first check-ups. Single claim: on held-out Samsung 50E cycling
  conditions the PINN-KAN beats (i) the same network without the residual, (ii) the same PINN with the KAN
  replaced by the best parametric/GAM/interaction-GAM/polynomial/MLP stress map, (iii) the best tuned
  data-only learner (paired, condition units, Holm). Hard-ODE vs PINN preregistered with outcomes
  A (PINN better) / B (tie, title 3) / C (hard better: framing choice to Shlok). Preferred title:
  "Physics-informed neural networks with Kolmogorov-Arnold stress functions forecast calendar and cycle
  ageing of lithium-ion cells at untested conditions". Datasets: Samsung INR21700-50E primary (storage +
  cycling by design; check-up schema by range request tonight; full download by Shlok on a faster
  network if needed), ISU-ILCC secondary (cyclic law, weeks + analytic throughput, 6 Cycling_json members),
  [lead note 22:50: see D006 for the novelty re-audit and the mandatory comparator]
  Sandia SNL external check and development set. Identifiability reduced to one figure with misspecified
  generators and thresholds fixed in the judge file. Pilots P0-P5 tonight, CPU only.
- **Alternatives and why they lost:** proposal as written (no PINN in headline; KAN [3,2] = GAM; ISU
  cannot separate calendar from cycle loss or test temperature; programme beyond a CPU week);
  identifiability-first title of Codex (drops PINN and KAN; identifiability not novel enough to carry the
  paper); SOH estimation on XJTU/TJU/HUST/MIT (crowded by PIKAN/PGKAN, cannot forecast; CONTRACT data
  preference); ISU as primary (weaker physical claim; kept as fallback); retired topics excluded (no
  protocol-comparison ratios, no interval calibration headline).
- **Evidence:** debates/D010_topic/02_proposal.md, 03_opponent.md, 04_judge.md,
  debates/codex_panel/turn02_response.md, debates/D010_topic/01_novelty_audit.md, notes/code/PIKAN.md,
  notes/code/GAPS.md, data/INVENTORY.md, data/raw/samsung50e_meta/experiments_meta.csv (condition counts).
- **Proposer / opponent / judge:** proposer agent / opponent agent (REVISE) and Codex panel (REVISE) /
  judge agent.
- **Re-open if:** Samsung check-ups not parsed by 07 Nov 09:00 (fallback: ISU primary, no calendar arm);
  the novelty re-audit finds a neural model coupling calendar and cycle ageing with learned stress
  functions forecasting unseen conditions (or prior modelling of Samsung 50E that pre-empts the claim);
  Samsung cadence too sparse for a window; hard-ODE outcome C (framing to Shlok); P2 compute no-go
  (re-plan arms); Shlok rejects the framing.

### D006 Novelty re-audit of D005 and the mandatory comparator (2026-11-04 22:50, status: accepted)
- **Decision:** keep D005. Re-audit (debates/D010_topic/05_novelty_reaudit.md): the combination
  (PINN with residual + calendar term with KAN SOC function + cycling KAN stress term, trained jointly
  on storage and cycling cells, forecasting held-out conditions) is NOVEL as a narrow combination
  (confidence 0.6); the model class alone is INCREMENTAL (0.7). Mandatory comparators: Stroebl et al.
  (dataset authors) J. Energy Storage 142, 119552 (parametric calendar + cycle superposition fitted to
  this dataset; their 2026 JES follow-up states the cycle part is inadequate) and PiDDM (arXiv
  2607.29095). Facts that constrain the design: dataset paper Stroebl et al., Sci. Data 11, 1020
  (doi 10.1038/s41597-024-03859-z); only 66 of 132 storage cells have intermediate check-ups (cells 04-06
  of each storage test point have initial and final only); capacity must be computed from raw CU steps.
- **Alternatives and why they lost:** re-open the topic (no work found that does the combination); drop
  the calendar arm (it is the part no KAN battery paper has and the dataset's distinctive design).
- **Evidence:** 05_novelty_reaudit.md; notes/papers/samsung50e_dataset_paper.md; runs/pilot_P0/RESULT.md.
- **Proposer / opponent / judge:** novelty auditor (check) / judge's D005 conditions / lead records.
- **Re-open if:** JES 182, 125097 (Zhang) or the Hallinger SSRN preprint (both cite the dataset, unread)
  contain a neural calendar + cycle model with learned stress functions; PIKAN/PGKAN/JECS addd4e full
  texts (unread) contain an operating-condition dynamics model.
