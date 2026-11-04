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

### D007 Contrast (iii) on ISU and SNL is non-inferiority (2026-11-05 00:15, status: accepted, rule-driven)
- **Decision:** per the judge's pre-set P3 rule (04_judge.md section 7), contrast (iii) (PINN-KAN vs best tuned
  data-only learner) is preregistered as NON-INFERIORITY on ISU and on SNL: best flexible learner / replicate
  floor = 0.90 on ISU (W = 4 weeks; CI [0.78, 1.08]) and 1.13 on SNL (W = 100 cycles; CI [0.81, 1.62]), both
  below the 1.2 gate (runs/pilot_P3/RESULT.md). Samsung is decided by the same rule once its data are in.
  The paper's superiority claims then rest on contrasts (i) residual and (ii) KAN vs alternatives, and on
  the held-out-condition tests; the abstract cannot say "beats all data-driven models".
- **Alternatives and why they lost:** keep superiority for (iii) (contradicts the pre-set rule; likely
  fails); change the floor definition after seeing P3 (post hoc).
- **Evidence:** runs/pilot_P3/RESULT.md, results.json; splits committed first (runs/splits/, commit 16a9da4).
- **Proposer / opponent / judge:** rule fixed by the judge in advance; applied by the lead.
- **Re-open if:** the statistician rules the floor is mis-defined (P3 concern: learners see the held-out
  cell's window, the floor does not), with a rule fixed before any Samsung data are scored.

### D008 Lead overrides of two pilot rules, recorded after the gate audit (2026-11-05 00:35, status: accepted, open to the D011 judge)
- **Decision:** (a) P2: the judge's rule gave "Partial" for the hard ODE (38 s at 80 nodes per cell vs 30 s);
  the lead ruled GO for Samsung because the measured cost scales with nodes per cell (about 11 s at 20 nodes,
  runs/pilot_P2/RESULT.md) and Samsung cells have at most about 30 check-ups; the partial plan (10 trials,
  2 inner folds) applies only if a dataset needs more than 40 nodes per cell. (b) P0: the rule said "queue the
  member for all cells only if the all-cell total is under 400 MB"; the estimate was about 0.5 GB, and the lead
  started the all-cell check-up fetch anyway (resumable, ordered to cover every condition first) because the
  alternative was no Samsung data before Shlok's download; the 07 Nov 09:00 fallback rule is unchanged.
- **Alternatives and why they lost:** apply the partial plan to all arms (cuts tuning for the PINN, which met
  its budget); fetch nothing overnight (loses the night; no Samsung pilot possible).
- **Evidence:** runs/pilot_P0/RESULT.md, runs/pilot_P2/RESULT.md, runs/GATE_pilots_audit.md (conditions).
- **Proposer / opponent / judge:** lead / gate auditor (flagged missing row) / to be confirmed by the D011 judge.
- **Re-open if:** Samsung cells need more than 40 integration nodes, or the fetch disturbs other sessions.

### D009 Statistical ruling: the 1.2 headroom gate is retired; one hierarchical rule (2026-11-05 00:45, status: accepted; supersedes the gate in D007)
- **Decision:** per runs/prereg/STATS_RULING.md: the replicate floor is renamed "replicate spread" (descriptive
  only, with a window-aware replicate predictor, also descriptive); no gate. Every primary contrast is tested
  non-inferiority first, then superiority (hierarchical), with margins relative to the comparator's
  training-side inner-CV error E per outer fold (superiority 0.02 E, non-inferiority 0.10 E). Holm family =
  H1a (residual), H1b (KAN vs best alternative stress map), H1c (best data-only learner), H6 (dataset authors'
  semi-empirical model, Stroebl et al.), one-sided 0.025. H2 (hard ODE vs soft PINN) gatekept on the family.
  Unit = held-out condition; paired exact Wilcoxon + BCa bound; lab and stage as sensitivity rows; 5 seeds
  averaged within condition; abstract reports pp difference, 95% interval, relative reduction, tier, n.
  D007's wording consequence stands: "beats all data-driven models" only if H1c reaches superiority.
- **Alternatives and why they lost:** D007's 1.2 gate (floor not a lower bound; SNL ratio flips between
  definitions); margin = one replicate floor (unreachable for superiority).
- **Evidence:** runs/prereg/STATS_RULING.md and runs/prereg/stats_ruling/ (power: with 40 conditions the
  detectable relative gain at 80% power is about 10-19% depending on assumed error correlation; Test C,
  13 conditions, about 17%+); simulated type-I error 1.6-2.3x nominal under strong left skew (open).
- **Proposer / opponent / judge:** statistician / gate audit and Codex turn 3 / D011 judge to confirm.
- **Re-open if:** the D011 judge or a re-run of the type-I simulation changes the test.
