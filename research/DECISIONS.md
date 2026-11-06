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

### D011 Contents of the frozen preregistration (2026-11-05, status: accepted; amends D005 contrast (iii) and D009's test)
- **Decision:** debates/D011_prereg/01_judge.md, verdict REVISE. (1) Primary Holm family = {H1a residual, H1b stress map
  (pool A3, A4, A5, A7), H6 dataset authors' semi-empirical model A10}, one-sided 0.025, tiers N then S; H1c (best of
  GP-ARD/LightGBM) becomes a key secondary, serially gatekept (tested at 0.025 only if all three reach S). Claim contract
  (iii) = A10, not the data-only learners. A10 gets one per-cell window factor (same prior as A1), published form as
  sensitivity. (2) Arms cut to the essential set: A6 dropped, A8 synthetic only, A14 and Test A exploratory, A13 (joint vs
  cycling-only) secondary; Test C arms A1, A9, A10, A11, A12; negative control A1, A9, R2. (3) Test C = "held-out
  temperature-laboratory domain (35 C, INT)"; never a temperature claim; lab-indicator sensitivity identified from INT at
  23 C; title never mentions 35 C. (4) Primary contrast on the log ratio of condition scores, margins ln(1.02) / -ln(1.10);
  test = studentized sign-flip permutation AND BCa bound; level verified by simulation (<= 1.2 x nominal, failure-
  contamination shape) before the freeze, else exact sign test (median estimand); pp difference always reported.
  (5) Outcome table and titles fixed (3.2); likely outcome title 3 (H6 S, H1a S/N, H1b tie, H1c closed/unresolved, H2
  unresolved): the lead tells Shlok now. (6) Gate conditions C1-C9 accepted with fixes; D008 (a) and (b) confirmed, (a)
  with a Samsung timing run and equal-budget Partial rule. (7) Physical checks (activation energy vs the authors' fit and
  verified literature only; SOC > 0.8 behaviour; Arrhenius monotonicity; superposition; cyclic signs) secondary,
  descriptive. (8) Freeze preconditions: Zhang JES 182, 125097 and Stroebl JES 142, 119552 full texts, Hallinger read;
  full Samsung download with manifest; stage assignment for 279 cells; analytic-vs-ZYK throughput check (median <= 5 %,
  max 10 %, else ZYK for all); window counts; simulation; timing run; second gate audit. 19 edits listed for PREREG_v2.md.
- **Alternatives and why they lost:** statistician's family with H1c inside (power about 19% needed, NI tier 24-40% at
  equality; mostly costs alpha); data-only learners as the headline comparator (contradicts P3 headroom); keeping all 14
  arms (compute, no hypothesis for A6/A8/A14 on real data); Wilcoxon + BCa on pp (liberal 1.6-2.3x under left skew; tests
  the pseudo-median, not the mean); exact sign test as primary (power loss; kept as fallback); Test C as temperature
  interpolation (35 C aliased with lab INT).
- **Evidence:** runs/prereg/PREREG_DRAFT.md, runs/prereg/STATS_RULING.md, runs/GATE_pilots_audit.md,
  debates/codex_panel/turn03_response.md, runs/pilot_P3-P5/RESULT.md, runs/samsung_pipeline/RESULT.md,
  debates/D010_topic/05_novelty_reaudit.md.
- **Proposer / opponent / judge:** experiment designer and statistician / gate auditor and Codex panel / D011 judge.
- **Re-open if:** Zhang or Hallinger contains the combination; the level simulation fails both rules; the timing run
  breaks the CPU week; Shlok rejects title 3 as an endpoint or asks for H1c back in the family.

### D012 Primary test = exact one-sided sign test on condition log error ratios (2026-11-05 01:25, status: accepted, pre-set fallback of D011)
- **Decision:** the studentized sign-flip permutation test + BCa bound failed the D011 acceptance rule
  (type-I <= 1.2x nominal): worst ratio 1.86 at n = 40 and 2.14 at n = 13 (left-skewed ISU mirror; 1.30 / 1.54
  under failure contamination) (runs/prereg/TYPE1_SIGNFLIP.md). Per D011's pre-set fallback, primary contrasts
  use the exact one-sided sign test on ln(S_comp / S_PINN) per held-out condition; estimand = median condition;
  abstract wording "typical held-out condition (median)"; mean-based tier is descriptive. Margins, hierarchy,
  Holm family (H1a, H1b, H6) and gatekept H2 unchanged. Test C (13 conditions) is descriptive only (sign test
  nearly powerless there). Power at n = 40, Holm step 1: detectable median gain about 9-12 / 12-16 / 17-22 %
  for assumed error correlation 0.95 / 0.90 / 0.75 (assumptions, not measurements).
- **Alternatives and why they lost:** sign-flip test (fails level); Wilcoxon (same skew problem per D009 ruling).
- **Evidence:** runs/prereg/TYPE1_SIGNFLIP.md, code/prereg/stats_signflip_sim.py, stats_signtest_sim.py (commit 127a1c3).
- **Proposer / opponent / judge:** statistician / D011 acceptance rule / rule pre-set by the D011 judge.
- **Re-open if:** the observed Samsung training-side error shape differs strongly from the simulated shapes.

### D013 Build choices of the confirmatory code (2026-11-05, status: accepted with changes; independent judge, no opponent convened)
- **Decision:** (a) one state factor h(y) shared by the time-driven and throughput-driven rate: accepted (closed form, equal H2 comparison, no extra dimension); wording "single state-dependent modulation", never "independent superposition";
  counterfactual share definition for 11a item 4. (b) per-cell offset on the term(s) the cell has (calendar term for storage cells): accepted, TAU = 0.15 fixed, scope differs from A10's total-loss factor (favours A10; printed), sensitivity row "delta on total rate".
  (c) A5 pairs: Samsung (3 prereg pairs) and ISU (all 3 pairs) accepted; **SNL changed** to the 7 design-based pairs (T x discharge; chemistry flags x T and x discharge) because the charge rate is constant (0.5 C) in every Test B training fold and DoD has two levels.
  (d) clip 20 and 40 % residual warm-up accepted as fixed recipe constants, **applied also to A9 (required) and A2 (uniform)**: an unclipped A9 was 0.1 to 0.7 pp worse on synthetic data (biased toward A1 in H1a); lam_res grid gains 1e-3 (lead to confirm; edge rule); sensitivity rows for clip {10, 50} and warm-up {0.2, 0.6}.
  (e) CUDA_VISIBLE_DEVICES = -1: accepted; add a run-start assertion and the CPU/library sentence.
- **Alternatives and why they lost:** separate h_cal and h_cyc (no closed form, re-timing, not testable on Samsung before the freeze; appendix row only); learned backbone shape (extra tuned dimension); offset on total rate for all cells (kept as sensitivity);
  no offset on storage cells (replicate scatter into the calendar surface); keep builder's SNL pairs (degenerate), all 21 SNL pairs (constant inputs), pairs by inner CV (extra search dimension); tune clip and warm-up (two extra dimensions for PINN arms only), drop the clip (10.25 pp at lam 0.01), leave A9 unclipped (biased).
- **Evidence:** debates/D013_build_choices/01_ruling.md and checks/ (clip_a.log, clip_b.log, a9.log, a2.log, snl_pairs0.log, snl_pairs4.log, snl_struct.txt); code/pinnkan/{law,pinn,hard,specs,synth,semi}.py; PREREG_v2 7, 7.1, 7.2, 9.8, 11a. Pilot checks: one synthetic design, one seed (clip), two inner-CV seeds (pairs); direction only.
- **Proposer / opponent / judge:** build implementer (choices) / none / independent judge (D013).
- **Re-open if:** the training-side Samsung tournament picks a non-simplest backbone in more than one fold; sd of fitted delta_c outside [0.5, 2] x 0.15 in most folds; tuned lam_res at the lower edge in most folds; a sensitivity row changes a primary tier; the A9 clip fix moves A9's inner-CV score by more than 10 %.
- **Lead confirmation of D013 item C3 (2026-11-05 02:10):** add lam_res = 1e-3 to the PINN residual-weight grid.
  Reason: on the synthetic well-specified law the optimum sat at the grid edge 0.01, and the project rule is to
  extend a grid whose optimum is at an edge; the data-only arm (A9, lam = 0) remains a separate contrast (H1a),
  so the extension does not favour A1. If the tuned optimum on Samsung training folds lands at 1e-3 the
  residual adds little, and H1a will show it; that is a result, not a reason to restrict the grid.

### D014 Negative control redefined: label-invariance gate (NC-1) + stress-attribution check (NC-2) (2026-11-05 about 03:05, status: accepted)
- **Decision:** per runs/prereg/NEGCONTROL_RULING.md (70aaf5a): gate G detects leakage only, by label invariance:
  every held-out cell's post-window labels are replaced with garbage and predictions plus tuning records must be
  bit-identical (NC-1). "Stress functions carry the gain" is a separate, non-gating check (NC-2): permuting stress
  must raise A1's error, exact one-sided sign test per condition (Test B only; not run on Test C, about 0.39 power
  at n = 13). Monte Carlo seeds: SeedSequence([20261105, crc32(label)]).
- **Alternatives and why they lost:** the draft criteria (A1 vs A9 and A1 vs R2 under permuted stress): no valid
  null on a leak-free pipeline; on 9 synthetic leak-free datasets they failed the clean pipeline 9/9 and each
  leaking variant 9/9, so they cannot discriminate.
- **Evidence:** NEGCONTROL_RULING.md; NC-1 on the real code (synthetic, builder-demo budgets): 0/9 clean flagged,
  9/9 flagged for each of two deliberate leaks.
- **Proposer / opponent / judge:** statistician / builder's report of the failing demo / lead accepts (rule-level).
- **Re-open if:** NC-1 at Samsung size at the frozen commit flags a clean run.

### D015 Red team on PREREG_v3: two fatal findings open the freeze gate (2026-11-05, status: open)
- **Decision:** the freeze is blocked until F1 (expected outcome shows no demonstrable benefit of PINN or KAN)
  and F2 (outcome table not closed; "put to Shlok" rows) are resolved. F1 goes to debate D016 (proposer ->
  Codex opponent -> judge) and to Shlok; F2 is closed by an outcome table Shlok approves in advance. The other
  red-team demands (A10 settled with unread sources read; lab confound testable on Test B incl. A10; Holm
  ordering by the tested statistic; type-I with shared fold/lab effects; README, stats step and draft aligned
  with PREREG_v3; a window-information reference arm) are accepted as freeze conditions.
- **Evidence:** debates/D015_redteam_v3/01_redteam.md.
- **Proposer / opponent / judge:** red team (attack) / lead records / D016 judge and Shlok decide.

### D016 Roles of the PINN and the KAN: Design R2 and the closed outcome table (2026-11-05, status: revised; awaits Shlok's approval of the table)
- **Decision:** debates/D016_roles/02_judge.md, verdict REVISE of Design R. The confirmatory question becomes data efficiency on the unchanged
  Test B (n = 40): grid m in {8, 16, 32} training cycling conditions (nested, temperature-constrained max-min subsets from identifiers) x
  k in {0, 2, k_full} check-ups; storage cells kept in every cell (titles say "few cycling tests").
  - PINN role, chain P: P1 = A1 vs best data-only learner D* (A9, GP, LightGBM, with physics features and storage-row options) at
    g1 = (8, 2); then P2 = A1 vs A9 (attribution to the law in the same network); then P3 = the advantage is larger at g1 than at g4.
  - KAN role, chain K: K1 = extracted closed-form law A15 is non-inferior to A1 at g4; then K2 = A15 vs G15 (the same frozen
    symbolic library applied to the additive GAM).
  - Primary error control: a Bonferroni-based graph, family-wise 0.025 (weights 1/2, 1/2); reverse-S findings are reported as safety
    findings.
  - Secondary Holm family: Q-H (soft vs hard ODE), Q-A10 (dataset authors' model) and Q-T (storage on/off).
  - Matched ladder A9 -> GAM law -> A1, plus A2, estimated at all 9 cells with simultaneous exact intervals; a full 2 x 2 factorial is
    rejected (no stress map exists without the law).
  - Closed table: 3 P states x 3 K states give titles T1-T8, modifier M1 (hard ODE better at g1), modifier M2 (A10 better at g1:
    T9a/T9b) and the ISU fallback; one claim sentence per cell; automatic tier downgrade by the lab, lab-indicator (incl. A10, D*),
    retain-all and random-subset rows; mean/worst-case rule.
  - Struck: H3, the G2 KAN "win", H7 beyond the G0 pipeline check, A3/A5/A7 on the grid.
- **Alternatives and why they lost:** Design R as written: its fixed sequence erases evidence at g2-g4, its family comparator cannot be
  attributed to a component, and its KAN thresholds of 4 of 5 are arbitrary and internal. Full 2 x 2 factorial: undefined without a law,
  and costly. P1 vs A9 as the headline: a low bar (D015 F5). P1 vs A10: A10 is physics, not data. A KAN accuracy race vs GAMs: P4 gap
  of 0.0-0.1 pp, cannot be won. Misspecification dose-response: reads as a straw man. Keeping PREREG_v3: F1.
- **Evidence:** debates/D016_roles/01_proposal.md, 02_judge.md; debates/codex_panel/turn04_response.md; debates/D015_redteam_v3/01_redteam.md;
  runs/pilot_P3-P5/RESULT.md; runs/prereg/STATS_RULING.md section 7; PREREG_v3 sections 9, 11, 16.
- **Proposer / opponent / judge:** method-architect (Design R) / Codex panel turn 4 (REVISE) / D016 judge.
- **Freeze conditions added:**
  - the statistician's items (a)-(f): size under fold- and lab-shared effects with a pre-set fallback, power of P1/P3/K1/K2, graph
    check, interval existence;
  - PREREG_v4, with code, README and draft aligned;
  - a novelty re-check of the data-efficiency framing;
  - the new code with its limiting-case tests;
  - the P6 ISU reading told to Shlok;
  - Shlok's approval row for the table.

  FB-1 to FB-6 and FB-8 to FB-10 are unchanged.
- **Re-open if:**
  - P6 shows data-only learners ahead at the smallest m on most ISU sides (Shlok may stop);
  - the size simulation fails without an accepted fallback;
  - Zhang, Hallinger or Stroebl JES 142 contain a data-efficiency study of learned laws on this dataset;
  - the extraction is not ready by the freeze (chain K struck, K state fixed at K=, its weight goes to P);
  - k_full < 2;
  - Shlok changes the table.

### D017 Shlok approves the closed outcome table of D016 (2026-11-05 07:50, status: accepted)
- **Decision:** Shlok approved the closed outcome table in debates/D016_roles/02_judge.md section 4 as written
  (states G, P+/P0/P-, K+/K=/K-, modifiers M1 and M2, titles T1-T8, T9a/T9b, ISU fallback, abstract claim
  sentences, qualifier sentences, banned words). This meets the D016 freeze condition "Shlok's approval row for
  the table". Any later change to the table is a new decision row made before the freeze, never after scoring.
- **Alternatives and why they lost:** "Discuss changes" (offered, not chosen).
- **Evidence:** Shlok's reply "Approve the table" in the lead session, 2026-11-05 07:50 (system clock).
- **Proposer / opponent / judge:** D016 judge (table) / Codex turn 4 and red team D015 (attacks) / Shlok (approval).
- **Re-open if:** Shlok changes the table before the freeze; D016 re-open conditions apply unchanged.

### D018 Confirmatory test rule after the size simulation failed (2026-11-05, status: accepted)
- **Decision:**
  - Estimand: labs are fixed strata, with equal weight per held-out condition (implied lab weights HM 17, INT 19, SIE 4 of 40).
    Every gated contrast is reported per lab. No claim about new labs or about temperature alone.
  - Confirmatory test for every Test B sign test with a tier, safety, wording or downgrade consequence: the Beta-binomial
    design-effect sign test with a fixed rho_s0 = 0.03. Positives needed of 40: 33 at 0.005, 32 at 0.00625 and 0.00833,
    31 at 0.0125, 30 at 0.025. This includes NC-2 (30, not 27).
  - Interval ranks: 8 for the simultaneous interval; 11 for the 95 % interval (judge's arithmetic, to be confirmed by the
    statistician). The test is named assumption-based, never exact or distribution-free.
  - The plain exact test becomes a descriptive "independent-conditions" row. Also reported, with no tier consequence: a
    dependence-sensitivity row (rho_s0 0-0.05) and the item (f) training-side sign-correlation estimate, hashed before any
    outer score.
  - The gate auditor's pre-score approval of the fallback (D016 section 2 (a); PREREG_v4 17.2 C2 sub-item) is given. C2 as a
    whole stays open.
  - Graph weights: 1/2-1/2 by default. w = 0.78 on P1N (local 0.0195, 30 of 40) and 0.22 on K1 (0.0055, 32 of 40) is
    adopted only by the pre-fixed simulation rule of 01_judge.md section 3: in all four settings, dP + dK > 0 and
    dK >= -0.10. If not filed before the freeze, 1/2 stands.
  - GAP-1: "most" holds iff e1 is reached and the fallback sign test of median(d_c) > 0 at 0.025 reaches 30 of 40, with
    d_c = ln(S_A9/S_A1) - 0.5 ln(S_D*/S_A1) at g1. The test sits outside the graph and is disclosed. If "most" fails, the
    added clause e1' (words of e1 only) needs Shlok's approval; this is a freeze condition. e1, e2 and e3 are unchanged.
  - GAP-2 to GAP-11 accepted; GAP-2, GAP-4 (lab weights 1/3), GAP-5 and GAP-7 with specifications.
  - Novelty: the "first" scope of 03_novelty_recheck section 3 is adopted. The abstract has no novelty sentence until
    conditions (a)-(d) hold. The Introduction presents data efficiency and the ladder as extensions of Lucu, Jia, Stroebl
    JES 142 and Guo.
  - Stroebl JES 142 and Zhang JES 182 (FT-partial) do not trigger the D016 re-open condition. Titles and abstract claim
    sentences are unchanged.
- **Alternatives and why they lost:**
  - Plain exact test: fails the 1.2 x nominal criterion from intra-fold 0.03-0.05; graph FWER 0.0877 at the R4 corner;
    fixed labs do not rescue it (1.83 / 1.72).
  - rho_s0 = 0.02 under fixed labs: fails at the R4 corner (FWER 0.0299) and rests on an unmeasured fold bound with no
    lab-by-fold component; the power gain is modest (0.82 against 0.71 at r = 0.20).
  - Training-side upper-bound rule: too few, non-independent inner-CV clusters; estimated design effects are liberal or
    vacuous (RESULT 4.4); D016 (f) "no rule changes"; the critical count would be unknown at the freeze.
  - Permutation, bootstrap or mixed model: 1/32 = 0.031 minimum p; too few clusters.
  - Labs as a random effect: 3 labs, temperature aliased.
  - Graph weights 2/3 or 3/4: dominated by discreteness. Fixed sequence: costs K1.
  - Opponent's difference-of-medians "most": no exact interval.
- **Evidence:** debates/D018_test_rule/01_judge.md; runs/prereg/stats_sim_v4/RESULT.md (sections 3-7, 9-10);
  debates/codex_panel/turn05_response.md; runs/prereg/PREREG_v4.md (9, 10, 11, 21, 22); debates/D016_roles/02_judge.md;
  debates/D016_roles/03_novelty_recheck.md; refs/fulltext/ft_stroebl2025_OED_JES142_119552.txt;
  refs/fulltext/ft_zhang2026_JES182_125097.txt. Judge's recomputation of the Beta-binomial counts matches RESULT 4.4;
  code/tests/test_graph_test.py 12 passed.
- **Proposer / opponent / judge:** statistician (RESULT.md sections 9-10) / Codex panel turn 5 (REVISE) / D018 judge
  (gate auditor, independent).
- **Re-open if:**
  - the counts are not reproduced by the code or tables;
  - the weight simulation's FWER guard fails;
  - any Samsung outer score is computed before FROZEN;
  - Shlok declines e1' (GAP-1 only);
  - Hallinger, Lucu A/B or Jia full texts contain a learning curve of a learned forecaster over ageing conditions on held-out
    conditions;
  - the ISU fallback triggers (its counts must be filed first);
  - the fallback's size is shown above 1.2 x nominal inside R4.

### D019 Shlok approves clause e1' (2026-11-05, status: accepted)
- **Decision:** Shlok approved clause e1' as proposed in debates/D018_test_rule/01_judge.md section 4 (action A6): when P2 and
  P3 reach tier S but the "most" test (PREREG_v4 9.8 rule 4, median d_c > 0, 30 of 40 under the fallback) fails, the abstract
  uses "(e1') the same network without the physics law was [Y] % worse, and the advantage was larger with 8 than with 32
  cycling conditions". e1, e2 and e3 and the rest of the D017 table stay word for word. Meets PREREG_v4 17.2 C22.
- **Alternatives and why they lost:** declining e1' (offered, not chosen) would have left no true approved clause for that
  outcome.
- **Evidence:** Shlok's reply "Approve e1'" in the lead session, 2026-11-05.
- **Proposer / opponent / judge:** D018 judge (clause) / Codex turn 5 (GAP-1 attack) / Shlok (approval).
- **Re-open if:** Shlok changes it before the freeze.

### D020 Pre-freeze strengthening: ensemble endpoint, inner folds, loss weighting (2026-11-05, status: accepted in part, revised in part)
- **Decision:**
  - C1 adopted modified: every arm with final-refit seeds 0-4 (A1, A2, A4/A5 and AG, A9, A12, A13) is scored as the mean of its
    five refit forecasts, with no pilot gate; deterministic arms unchanged; K1/K2 (A1, A15, G15) stay per-seed (one law);
    per-seed scores descriptive; tuning and D\*/AG selection stay one fit per trial.
  - C2 adopted modified and conditional: inner folds for m in {8, 16} become 4 for every tuned arm and the tournament iff pilot
    P6b (ISU training sides, development only, arms A1, A2, A4, A9, A11, A12) gives q_a > 0 in at least 5 of 6 arms and min q_a
    > -ln(1.02); otherwise 2; the Partial plan forces 2; unfinished P6b means no change.
  - C3 rejected for this run (loss weighting disparity disclosed instead). R1 and the optional C3 factor of P6b deleted.
  - PREREG 7 text corrected: tournament once per (outer fold, m) on the thinned training side.
  - No Samsung-label pilot before FROZEN. C4-C8 not adopted (not before the judge).
  - D017/D019 table, g1, margins, rho_s0, w, subsets and folds unchanged.
- **Alternatives and why they lost:**
  - R1 gate on A1/A9: favourable selection among two arms.
  - Ensemble for A1/A9 only or in the K chain: A1-only advantage; five laws are not one law.
  - Five-seed scoring inside tuning: five-fold tuning cost.
  - Four folds unconditionally: no measurement, CPU cost.
  - The expert's R2 (median of four): adopts a null change about half the time and omits A2, A4.
  - C3 in all objectives, or for A1/A9 only: unmeasurable before the freeze (storage), A11 cannot be made condition-balanced
    in the same sense, weakening D\* is forbidden, A1-only is forbidden.
- **Evidence:** debates/D020_strengthen/01_mlexpert.md; debates/D020_strengthen/02_judge.md;
  debates/codex_panel/turn06_response.md; runs/prereg/PREREG_v4.md (3.4, 4.1, 6, 7, 8, 16, 17); debates/D018_test_rule/01_judge.md.
- **Proposer / opponent / judge:** ml-expert / Codex panel turn 6 (REVISE) / D020 judge. No outer-test data or score was read.
- **Re-open if:** a Samsung outer score exists before FROZEN; the ensemble cannot be applied seed-wise or breaks NC-1; the P6b
  script or decision.json is altered after the first fit; Shlok asks for a change not applied to every comparator.

### D022 NASA/CALCE descriptive addendum; KAN contribution = identifiability-audited extraction; cap 2 confirmed (2026-11-05, status: revised)
- **Decision:** debates/D022_datasets_kan/03_judge.md, verdict REVISE (both parts adopted with modifications).
  - Datasets: one descriptive, ungated section on CALCE PL pouch (EXT-PL) and NASA set 5 (EXT-NA), each analysed only
    inside its own campaign (no pooling, no transfer, no cross-campaign comparison or win count). The addendum card
    `runs/prereg_ext/PREREG_EXT_v1.md` is frozen after the Samsung FROZEN and before any model sees these data. Samsung
    confirmatory runs execute from the FROZEN commit. Direction labels are dropped; one symmetric count template is used.
    No coverage figure or p-value appears in the paper. No abstract, title or Highlights mention. NASA is labelled
    "previously analysed data" in Methods and in every caption. CS2/CX2 are "considered, not analysed" (two discharge
    rates, previously analysed); the professor is told by the 1.7 message. Go/no-go: PL completeness (6 of 8), S-gate,
    F-gate, NC-1/PC-1 per campaign, A10c separability.
  - KAN contribution: the identifiability-audited extraction protocol is adopted as the paper's KAN-side
    methodological contribution, framed as an audit, not a new KAN. It is applied identically to A15 and G15. It has a
    design-matched calibration on the Samsung training stress vectors and the label rule of judge 2.2 ("identified"
    needs L_e >= 3, at least 80 % fold-by-seed stability, a calibrated wrong-family rate <= 0.10 and additivity in the
    input; otherwise abstention). It goes into PREREG_v4 7.3 item 6, 11a item 10 and C26; it is built before the freeze
    or struck by rule. It changes edge-level wording only, never a state, title or abstract sentence.
  - Monotone KAN (M): deferred. No pre-freeze round and no Samsung M run in this submission. An optional synthetic
    second round may run after FROZEN under a rule file committed first. The paper never says M was rejected. L is not
    adopted (L1 failed).
  - Cap: `max_coeffs_per_edge` = 2 confirmed (D021 has no ledger row; it is recorded here). Banned: recovered,
    discovered or identified Arrhenius, power-law, exponential, quadratic or hinge forms; non-monotone SOC from the
    extracted law; any cycling activation energy. D016 3.5 is struck for the extracted law; the SOC question moves to
    A1's calendar KAN (11a item 2), descriptive only.
  - Titles: "readable Kolmogorov-Arnold stress laws" and "Kolmogorov-Arnold stress functions" are still true; no change
    is needed. The D017/D019 table is untouched.
- **Alternatives and why they lost:**
  - Decline the datasets: the professor asked, and the cost is modest.
  - Confirmatory parity: n = 8 and 5 cannot pass; it would change the Holm levels; NASA is not blind.
  - Pooling or transfer: the retired topic.
  - CS2/CX2: one input with two levels, previously analysed.
  - Direction labels: a sign rule without error control.
  - M before the freeze: TAKEN method; the post hoc gain is best-of-4 inits on 2 seeds; it changes the primary arm;
    unfair to the GP.
  - L: failed L1 (79 % against 25 %).
  - Typed bases: TAKEN, no numerical effect.
  - Cap 3 or a calendar-only cap 3: false structure (37 of 40 at cap 3), new hash and study.
  - A title change: not needed.
- **Evidence:** debates/D022_datasets_kan/{01_proposal_datasets,01_proposal_kan,kan_study_rule,02_novelty_kan,03_judge}.md;
  debates/codex_panel/turn07_response.md; debates/D021_cap/01_architect.md; notes/data/NASA_CALCE_feasibility.md;
  runs/D022_kan_synth/{decision.json,posthoc_mono_init.txt} (rule 6686344 committed before results 3e65aed);
  runs/D021_cap_synth/decision.json; runs/prereg/PREREG_v4.md (1, 7, 9, 10, 11, 11a, 12, 17).
- **Proposer / opponent / judge:** data proposer and method-architect / Codex panel turn 7 (REVISE both) and the
  novelty auditor / D022 judge (independent). No Samsung, NASA or CALCE capacity value was read.
- **Re-open if:**
  - the professor insists on CS2/CX2 or a NASA confirmatory role;
  - Saxena et al. contradict the PL design;
  - Samsung runs cannot execute from the FROZEN commit while extras commits exist (the extras then wait);
  - the novelty repeat finds a calibrated per-edge identifiability protocol for KAN or symbolic extraction;
  - no input can reach "identified" at g4 (reported as a negative audit finding);
  - the audit is not built by the freeze;
  - a Samsung outer score exists before FROZEN;
  - Shlok changes the table or asks for the closed-form SOC readout.

### D021 Per-edge cap of the symbolic library (record-only row; 2026-11-05, status: accepted, confirmed in D022)
- **Decision:** max_coeffs_per_edge = 2 for A15 and G15 (eligible forms zero, linear, log), set by the method-architect with the
  decision rule committed before the synthetic study (c0a9793, 2334666). Confirmed by the D022 judge, with the list of forbidden
  claims (no recovered Arrhenius, power, hinge or non-monotone SOC form) in debates/D022_datasets_kan/03_judge.md section 4.
- **Alternatives and why they lost:** cap 3+ (whole library): chose 3-coefficient forms on 37 of 40 truly linear synthetic edges;
  cap 0-1: prunes every edge. Details in debates/D021_cap/01_architect.md.
- **Evidence:** debates/D021_cap/01_architect.md, study_rule.md, runs/D021_cap_synth/.
- **Proposer / opponent / judge:** method-architect / Codex turn 7 (D022) / D022 judge.
- **Re-open if:** D022 re-open conditions.

### D023 Test-time latent inversion for every inverting arm (2026-11-05, status: accepted with revisions)
- **Decision:** (1) One routine for A1, A4/A5/AG, A9, A13, A15, G15 and A2: per-cell Levenberg-Marquardt Newton, float64, started at the prior mode,
  stop at ||g_c|| <= 1e-6 (1 + |f_c|) or 100 iterations, accepted steps never raise the cell's objective, non-converged cells keep the last accepted
  iterate and are counted, k = 0 rule and objective unchanged, no multi-start selection; adopted by the judge as a computational convention after the
  committed check rule returned NONE (O2 fails only criterion (c), start spread, which measures the model's multimodality). (2) z-prior weight fixed at 1
  (equal to the training-loss prior), not tuned: no {1, 4, 16} search. (3) Mandatory diagnostics without consequence: convergence share, cap-doubling change,
  start spread over the prior mode plus three seeded starts, basin shares; Methods paragraph, Supplement table, one fixed Limitations sentence; descriptive
  sensitivity rows (v) other starts and (vi) weights 4 and 16, inference only. (4) The outcome table (D017, D019) is unchanged; the latent is described as
  "the local posterior mode reached from the prior mode", never identified, unique, start-independent or global; P2 is stated as a contrast between two
  estimators sharing one inversion rule.
- **Alternatives and why they lost:** production Adam budgets (200 / 150 / 300 steps; forecasts move up to 42.3 pp for A9 when the steps double; unequal
  between A1 and A9); Adam 4000 steps with cosine decay (A1 convergence share 0.627); multi-start selection by objective (self-disagreement p95 5.49 pp A1,
  descriptively worse for A9 fold 3: 9.05 to 16.34); delta-only inversion (changes P2 and the identity of A1; kept as fallback); posterior mean or Laplace forecast
  (larger change, deferred); tuned z-prior weight (applied across k of one m, two-condition inner folds, no measurement of the weight, would have to reach A4/A5
  as well, new dimension in 7.1); ISU check of the weight R-b (changes the estimator, spends ISU exposure, no decision depends on it).
- **Evidence:** debates/D023_inversion/01_proposal.md, 02_judge.md; runs/check_D023_inversion/decision.json (development data, ISU training sides);
  runs/pilot_P6b/RESULT.md Table E; debates/codex_panel/turn08_response.md; code/pilots/d023_inversion_check.py.
- **Proposer / opponent / judge:** ml-expert / Codex panel turn 8 (revise) / D023 judge (independent).
- **Re-open if:** the Samsung dry run shows a convergence share below 0.99 for A1 or A9 or a Newton failure; a development rule committed beforehand shows a fixed
  weight above 1 passes the start-spread criteria with non-inferior pseudo-test score for both A1 and A9 (changes the fixed weight only, never makes it tuned);
  ISU becomes primary; an identified inversion is required (new estimator, new version); the ported routine fails the regression test against the check's O2;
  an outer-test score exists before FROZEN.

### D022a Extraction audit revised after the red-team review (2026-11-05, status: revised; supersedes 03_judge.md 2.2 (a) item 3, 2.2 (c) and 7 item 5)
- **Decision:** debates/D022_datasets_kan/05_judge_audit_revision.md. FATAL F1 and F2 are upheld; M1-M8 and m1-m7 are
  adopted (F1, M1, M3 and M7 in modified form).
  - The unit of calibration is a whole synthetic dataset on the real fold design, run through the real 5-fold x 5-seed
    procedure and the same label code.
  - Labels are read from the extracted law's partial dependence, with a numerical additivity test for both arms and a
    tie rule (a tie gives no family). Labels are licensed at g4 only. The calendar extracted law gets no edge wording.
  - Strata: zero, linear, log, quadratic, hinge; 10 of 30 datasets non-additive; amplitudes log-uniform 0.05-0.5;
    laboratory offsets on the real laboratory map; hyperparameters (including A15's h) drawn from the tuned spaces.
  - C1, calibrated: the one-sided 95 % Clopper-Pearson upper limit of the share of datasets with any false printed
    statement is <= 0.20 (D = 30: at most 2; D = 22: at most 1).
  - C2, useful: correct-form recall >= 0.5 on the four many-level inputs.
  - C3, necessary: the stability-only baseline fails C1.
  - The audit is a contribution only if C1-C3 hold for A15 and G15. Otherwise the bullet is withdrawn and the audit is
    reported descriptively (a stop, not a finding). An arm that fails C1 prints no labels.
  - Guard: content controlled by the FROZEN SHA and a hash-chosen bit-identical re-run, not by mtimes; pins mandatory.
  - CPU: 1500 fits, about 18 CPU-h expected and 33 ceiling (D021 times), cap 36, after FROZEN. The calibration need not
    precede outer scores.
  - Freeze delay about 1 to 1.5 days (estimate). If not held, the fallback is: strike the audit, report the 11a item 6
    stability table descriptively, no contribution bullet.
- **Alternatives and why they lost:**
  - Keep v1: not calibrated for its label; unfalsifiable.
  - Independent truths per fold: mis-models the shared-truth dependence.
  - Per-stratum bounds at 0.10: needs at least 29 datasets per stratum, over 100 CPU-h.
  - Inner-CV tuning inside the calibration: multiplies the cost by the trial count.
  - Calibrating labels at g1 and on the calendar law: doubles the strata and cost.
  - Strike now: gives up a contribution that can be tested within 2 days.
- **Evidence:** debates/D022_datasets_kan/{04_redteam_audit,05_judge_audit_revision,calibration_rule}.md;
  code/pinnkan/extraction_audit.json; runs/D021_cap_synth/log_p0.txt, log_p1.txt (pipeline times); judge's
  Clopper-Pearson arithmetic.
- **Proposer / opponent / judge:** D022 judge 2.2 and the coder (v1) / red team A3 (2 FATAL, 8 MAJOR, 7 MINOR) / D022
  judge (independent of the code). No Samsung, NASA or CALCE capacity value was read.
- **Re-open if:**
  - the red-team re-check (B4) leaves a FATAL open;
  - the re-run is not bit-identical;
  - fewer than 22 datasets complete;
  - the real tuned hyperparameters fall outside the sampled spaces;
  - an outer score is used to change the rule;
  - Shlok asks for labels at g1 or on the calendar law.

### D022b Extraction audit: fallback adopted after the red-team re-check (2026-11-05, status: accepted; supersedes D022a's calibration plan)
- **Decision:** debates/D022_datasets_kan/07_judge_recheck.md.
  - The audit is not run as a calibrated contribution. The ~18 CPU-h calibration is not run.
  - Laws are printed in closed form, with the 11a item 6 stability table (votes, tie share, additivity share, sign
    votes; descriptive, no licence words).
  - No audit contribution bullet. The KAN-side contribution is the held-out K1/K2 test of the KAN-extracted
    closed-form law against an equally simplified additive law (NOVEL 0.60, 03_novelty_recheck row iii). The cap is
    justified by the D021 synthetic false-structure study.
  - N1(a) is adopted permanently: no T sign from the cycling law.
  - N1(b), N1(c), N2 and the N3 omission control are adopted for any future version only.
  - Now: label functions default `calibrated=False`; the banned-phrase list is extended with word-boundary matching;
    the n3 wording is fixed.
  - m7 stays open with the gate auditor (it also concerns PC-1).
- **Alternatives and why they lost:**
  - Fix N1-N3 and run the calibration: about 1.5 more days, beyond the ~2-day limit, for a predicted fail.
  - The verdict would hinge on an invented laboratory-offset sd that the extraction cannot model, so even a pass is
    weak evidence.
  - C3 is near-automatic (n4).
  - A separate A15-only additivity criterion: breaks K2 symmetry.
- **Evidence:** debates/D022_datasets_kan/{06_redteam_recheck,07_judge_recheck,05_judge_audit_revision}.md;
  code/pinnkan/stats_step.py 557 (fallback path); debates/D016_roles/03_novelty_recheck.md row (iii). No calibration fit
  and no data value were used.
- **Proposer / opponent / judge:** coder (v2 build) / red team B4 (re-check) / D022 judge.
- **Re-open if:**
  - Shlok asks for the audit as a contribution and accepts the delay (new version with laboratory-aware licences and
    the N1-N3 fixes, fixed before any fit);
  - a reviewer asks for an operating characteristic (descriptive run of the frozen v2 code);
  - the K-chain test is found published.

---

### D024 Pre-freeze data-definition rules: ZYK gap, retention anchor, outlier series, lab map, incident stage, serial conflicts (2026-11-05, status: accepted with revisions)
- **Decision:** (1) FB-5: a ZYK file is incomplete iff a gap > 600 s has an endpoint with |I| > 0.05 A, or time is not monotonic, or NaN current, or < 10 rows, or a rest-only gap > 24 h; 22 cells have an incomplete file, 125 of 147 are fully logged; the 6 ZYK metas without csv (stage 2, file 24, TP_z01 and TP_z03) are the paper's documented missing-data incident: `missing_file`, designed throughput for that interval, cells kept; DoD classes (0.15, 0.35); validation run once on the ruled rule, 60 s and any-gap as information. (2) Q0 = ET_T23 (PREREG 3.3(2), availability met for 279 of 279; dataset paper Q_rel from the initial RPT); first-CU column descriptive only. (3) The causal outlier series is ET_T23, CU and exCU (AT excluded); the 2 flipped CU rows stay flagged, no review; disclose that thresholds were set on CU rows. (4) Lab map: one frozen file `runs/prereg/lab_map.json` from the design table; most cells, exact tie to the lab with more cycling cells in the design (HM 69 > INT 60), so HM 17 / INT 19 / SIE 4 stands; INT-tie is a descriptive 9.9 (a) sensitivity; the lab-indicator row is cell-level and unaffected. (5) Incident files: the paper's list is under stage headings and all six check-up files are Stage 1; drop stage 1 only (4 stage-2 rows restored), consecutive drops likewise (TP_z07_03 is stage 2; TP_z17 read as cell 03); the ET entry is deleted (the incident is ET_T45, which is not read). **Defect found:** the kind-"ET" drop removes the ET_T23 row of TP_z25_01_s1 and makes the loader fall back to the first-CU anchor for all cells; fixed by the stage-aware drop and a loader test. (6) The 49 meta-serial conflicts: no exclusion or re-assignment, disclose, add `meta_serial_conflict`, and a logged-discharge-current identity check on cycling cells (> 10 % deviation excludes under 3.2).
- **Alternatives and why they lost:** any-gap 600 s (flags 72 % of files, 9 fully logged cells, logged branch vacuous); 60 s active (tolerance 10x tighter than needed, kept as information); first-CU anchor (loses early fade, departs from the data authors' Q_rel); exCU out of the outlier series (untested forecast points or stale neighbours); post-hoc restore of the 2 rows (outcome-based); "mixed" lab stratum, exclusion of the tied condition, fractional membership, tie to INT (break weight 1/3 per lab, change n, or force redoing simulation labels and tests); drop incident files in both stages "to be safe" (removes data on no ground); exclude the 49 serial-conflict cells (nothing reads the field; 49 of INT's 102 cells).
- **Evidence:** `debates/D024_data_rules/01_judge.md`; `runs/samsung_pipeline_full/RESULT.md`, `zyk_files.csv`, `zyk_per_cell.csv`; `refs/samsung50e_paper/paper.txt` lines 94-125; `runs/prereg/PREREG_v4.md` 3.2, 3.3, 5, 9.1, 9.8, 9.9; `code/pinnkan/zyk.py`, `code/pinnkan/data.py` 223-312, `code/prereg/extraction_calibration.py` majority_labs. No capacity or retention value was read.
- **Proposer / opponent / judge:** data steward (RESULT.md 10) / none (judge ruled on the steward's concerns directly) / gate-auditor judge.
- **Re-open if:** the FB-5 validation fails for a reason traceable to the gap rule; the identity check finds a cycling cell whose logged current contradicts its zip-name condition; aggregate flag counts show ET or exCU rows drive many outlier flags or the first CU after ET is flagged as a rise for more than 10 % of cells; Shlok prefers the wider TP_z17 cell scope or the first-CU anchor.

### D025 Window cap for cells with too few check-ups (2026-11-05, status: accepted; gate auditor checks at the freeze)
- **Decision:** for any cell whose number of intermediate check-ups n is not greater than the window k (k = 2 or k_full = 4),
  the window is capped at n - 1, so at least one post-window check-up is forecast. The cap is applied identically to every arm
  and every grid cell; the cell is kept and listed (currently TP_z20_02, TP_z23_01 at k_full = 4; counts from
  runs/samsung_pipeline_full/RESULT.md section 5). This mirrors the existing min(k, k_sto) storage rule of PREREG_v4.
- **Alternatives and why they lost:** excluding the cells (changes n of their conditions on the k axis only and reads as
  convenience); excluding them from k_full only (makes the k_full and k = 2 sets differ); padding the window (impossible).
- **Evidence:** PREREG_v4 rev. 9 section 5 flag; counts only, no capacity value read.
- **Proposer / opponent / judge:** lead (rule from the existing min() convention) / none convened (mechanical) / gate auditor
  at the freeze.
- **Re-open if:** the gate auditor finds the rule changes any condition-level n or interacts with the NC-1 window scramble.

### D026 Item (f) under retention blinding: separate post-freeze inner runs at g1 (2026-11-05, status: accepted; gate auditor checks at the freeze)
- **Decision:** O1. After FROZEN and before any Samsung test fold is loaded, five `inner` runs (g1 = (8, 2), max-min, folds
  0-4, arms A1, A9, A11, A12; configs = the g1 confirmatory configs with mode, run_id, arms, diagnostics and refit_timing
  changed, pinned in FROZEN as `item_f_config_sha256s`) feed `item_f_from_runs(("D*", "A1"))`; the file and its record live in
  `runs/item_f/` (untracked). Order is enforced by state: `build_item_f` refuses after any Samsung score or SCORED row;
  `require_item_f_record` runs before `build_data` in every Samsung confirmatory run; every Samsung SCORED row carries
  `item_f_sha256`. `item_f`/`item_f_record` leave `PIN_FILES`. PREREG rev. 11 rewrites 9.9 (r), C24, sections 15, 16, 18, 22.
- **Alternatives and why they lost:** O2 two-phase run (the confirmatory path loads role=test before tuning and forbids
  overwrite, so it needs resume logic in the most guarded path to save about 1 CPU-h); O3 post hoc (breaks D18 2.3 (ii));
  O4 ISU (other dataset and estimand).
- **Evidence:** run.py ~238-312 and ~452, guard.py PIN_FILES / build_freeze_payload / verify_freeze, stats_v4.py 540-650,
  selectors.DSTAR_CANDIDATES; cost about 1.1 CPU-h expected, 4 ceiling (judge arithmetic from section 16, not measured).
- **Proposer / opponent / judge:** lead (debates/D026_item_f_blinding/01_proposal.md, O2) / Codex panel turn 9 (REVISE, O1) /
  judge (debates/D026_item_f_blinding/02_judge.md).
- **Re-open if:** the timing run puts the item-f runs above 15 % of core compute; an item-f fold cannot finish; or the
  descriptive concordance row shows a different D* in more than one fold.

### D010 Topic debate identifier (record-only row; written 2026-11-05 23:45 by the lead to close RT F12.6 / freeze condition C19)
- **Decision:** none of its own. "D010" is the identifier of the topic debate folder `debates/D010_topic/` (00 candidates,
  01 novelty audit, 02 proposal, 03 opponent, 04 judge, 05 novelty re-audit); its judge ruling is recorded as **D005** and the
  re-audit as **D006**. Citations of "D010" in D005 and the PREREG files point to that folder, not to a separate ruling.
  D008's "open to the D011 judge" was confirmed inside D011 (no separate row).
- **Alternatives and why they lost:** renumbering D005/D006 would break append-only history.
- **Evidence:** debates/D010_topic/04_judge.md, 05_novelty_reaudit.md; debates/D015_redteam_v3/01_redteam.md finding F12.6.
- **Proposer / opponent / judge:** lead (record-only; no ruling).
- **Re-open if:** never (bookkeeping only).

### D028 Confirmatory config set rulings: ZYK throughput, arm lists, strike list (2026-11-06, status: accepted; gate auditor checks at the freeze)
- **Decision:** (a) `throughput: zyk` in every Samsung config is correct (FB-5 ruled validation rejects analytic throughput);
  the git-ignored ZYK table gets `zyk_table_sha256` pinned in every Samsung config and checked at load; FB-8 timing runs a
  pinned primary config. (b) Override checks in `validate_config` accepted. (c) Downgrade-row arm lists, 9.9 descriptive arms
  (A1 A9 A11 A12 A10 A10P at g1/g4), Test A and S3 (= S2 arms, both A10 forms) confirmed; ISU "full-data analogue" = unthinned
  training side at W = 4 weeks (not m = 32). (d) Struck: first-CU row, forecast-failure row 3.3(8) (superseded by the D025
  cap), 9.9 (n), A14 leftovers, SNL replication; ISU fallback lapsed (Samsung parsed 2026-11-05); built: 9.9 (p) `tpe_seed`
  and 9.9 (t) `a10_drop_soc100_storage`. PREREG rev. 13 items T1-T6; coder items C1-C5.
- **Alternatives and why they lost:** analytic throughput (fails FB-5 as written); ISU g4 analogue at m = 32 (thins ISU, the
  PREREG says full data, impossible on SNL); keeping unrunnable rows as written (the guard refuses unpinned confirmatory runs);
  building the first-CU and h_cal/h_cyc rows (not small, not specified); choosing an SNL scarce window now (new design choice
  on non-blind data).
- **Evidence:** runs/samsung_pipeline_full/fb5_validation.json (`ruled`), RESULT.md C4; runs/prereg/CODER_BATCH_REPORT.md
  (C14b); PREREG_v4 3.3(8), 3.4, 4.1, 5, 7.1, 9.8, 9.9, 15; runs/splits/isu_testB.json (63 conditions); debates/D028_config_rulings/01_judge.md.
- **Proposer / opponent / judge:** coder (C14b, 7438718) / reviewer (debates/D027_coder_batch_review.md) / judge
  (debates/D028_config_rulings/01_judge.md).
- **Re-open if:** the ZYK table is rebuilt after the pin; the FB-8 timing run makes the descriptive rows displace any
  "never dropped" item; or Shlok wants a struck row back before FROZEN.

### D029 Novelty scope after Lucu A/B; T5/T6 wording (2026-11-06, status: accepted for framing; title change pending the author)
- **Decision:** debates/D029_novelty_scope/01_judge.md, verdict REVISE. Lucu A/B (JES 30, 2020) contain a nested GP
  learning curve over the number of ageing conditions on held-out cells, so the D018 section 7 fifth bullet fired and
  D018 section 6 "Effect on framing" is replaced: contribution list order (1) A15 versus G15 held-out test under the D022
  protocol, novelty on the matched test only; (2) matched ladder and tuned comparators, Jia cross-dataset stated;
  (3) m and k learning curves as an extension of Lucu A/B, Stroebl, Guo; (4) conjunction sentence after (d).
  Auditor 5.2 bans adopted plus any "how many tests is open" sentence and "first" in every form. Condition (d) gates
  every "to our knowledge" / "we found no earlier study" sentence and adds a method-level check of PIKAN/PGKAN and
  KA-CRNN. Recommended to Shlok: T5/T6 drop the question form ("How many cycling tests and check-ups do ... need?"
  becomes "Physics-informed and data-driven forecasts of lithium-ion capacity fade against the number of cycling tests
  and check-ups:"), second halves unchanged; default if unanswered at FROZEN: keep as approved. No change to design,
  tests, states, alpha, stop rules or freeze conditions other than C4.
- **Alternatives and why they lost:** keep D018 section 6 as written (item 1 misstates Lucu as "number of cells" and
  leaves the m-curve looking new); fix T5/T6 only through Introduction text (opponent: a question-form title is not
  cured by body text); lead with the m-curve (now generic prior art); edit section 11 here (only Shlok may, D017).
- **Evidence:** debates/D016_roles/04_novelty_C4_audit.md; notes/papers/lucu2020_A_B_JES30.md;
  debates/codex_panel/turn10_response.md; debates/D018_test_rule/01_judge.md sections 6-7; runs/prereg/PREREG_v4.md 11.
- **Proposer / opponent / judge:** novelty-auditor / Codex panel turn 10 / judge (debates/D029_novelty_scope/01_judge.md).
- **Re-open if:** the (d) pass finds concurrent work (same-dataset learned-law data efficiency: stop rule 12; a matched
  extracted-law versus additive-law held-out test: item 1 and the conjunction lose their novelty phrase); a reading finds
  a k axis or physics-informed arm in a condition-count study; Shlok declines the T5/T6 replacement (record only).

### D030 Shlok approves the replacement of titles T5 and T6 (2026-11-06, status: accepted)
- **Decision:** the question-form titles T5 and T6 of the closed outcome table (PREREG_v4 section 11; D016 / D017) are replaced
  by the D029 judge's wording: T5 "Physics-informed and data-driven forecasts of lithium-ion capacity fade against the number of
  cycling tests and check-ups: learning curves with Kolmogorov-Arnold stress functions"; T6 the same with the ending "learning
  curves on a designed ageing dataset". Same states (P0/K=, P0/K-), same evidence words, no change to state selection.
- **Why:** Lucu et al. (JES 30, 101409 and 101410, 2020) already asked how many ageing tests a learned forecaster needs, so a
  question-form title would present a published question as open (D029; novelty audit de07eb5; Codex turn 10).
- **Alternatives:** keep T5/T6 as approved (D029 fallback; Introduction carries the Lucu extension sentence).
- **Evidence:** debates/D029_novelty_scope/01_judge.md (table of old and new text); Shlok's reply "Approve new T5/T6" (2026-11-06).
- **Proposer / opponent / judge:** novelty auditor / Codex turn 10 / D029 judge; approved by Shlok.
- **Re-open if:** Shlok changes his answer before FROZEN.

### D031 Freeze in the main checkout, not a separate worktree (lead, procedural; 2026-11-06)
- **Decision:** FROZEN is written and every confirmatory run executes in the main checkout
  (`C:\Users\Shlok\Downloads\PINN KAN battery paper`, branch main) at the frozen commit. Nobody commits to main afterwards until
  the confirmatory runs finish (verify_freeze requires HEAD = frozen commit). Work that must continue (manuscript, figures) runs
  on a separate branch in its own git worktree.
- **Why:** core.autocrlf=true. A fresh worktree checks text files out with CRLF, so byte hashes already embedded in the committed
  configs (extraction_audit_sha256, the split file hash inside blinding_exclusions.json) would not match there, and regenerating the
  configs in the worktree would move HEAD. The main checkout is the copy in which those hashes were computed.
- **Alternatives:** `.gitattributes` with `-text` (changes checkout bytes of files Git wrote earlier; same mismatch risk); freeze in a
  worktree and regenerate every hashed artifact there (circular with HEAD).
- **Proposer / judge:** lead (procedure only; no rule, test or outcome changes). The gate auditor checks it at the freeze audit.

### D032 D025 cell list corrected from the code (record-only; lead, 2026-11-06)
- **Decision:** D025's rule stands; its example list is corrected: at k_full = 4 the cap binds for six scoreable cycling cells
  (TP_z04_01_s1, TP_z20_02_s2, TP_z20_03_s2, TP_z23_01_s2, TP_z23_02_s2, TP_z23_03_s2), at k = 2 for TP_z20_02_s2 and TP_z23_01_s2.
  Counts are post-QC check-ups (the code's cell.n), D025 had counted listings. Condition-level n stays 40 at k = 4 and k = 2, so
  D025's re-open condition is not triggered.
- **Evidence:** runs/freeze_runs/D025_capped_cells.md (identifiers and counts only); every run also writes window_capped.json.
- **Proposer / judge:** lead (record-only); gate auditor checks at the freeze audit (C28).

### D033 Sign-off findings on PREREG_v4 rev. 15 (2026-11-06, status: accepted for code and text items; author items AD1-AD6 pending)
- **Decision:** debates/D033_signoff/01_judge.md. Red-team F1 (= statistician D1, FATAL), F2, F6, F7, F8, D2, D3, D5 and M3 are
  code fixes (one coder batch before FROZEN: pinned `runs/prereg/stats_config.json` with w 0.78 and e1' approved, refusal of
  overrides after FROZEN, ties not dropped, bracket-source rule for row-set states, NaN-safe NC-1, wider `nc1_full` plus a
  pre-`build_data` invariance test, NC-2 keeps each cell's throughput, Test C/S2 intervals wired in, n_expected from the pinned
  exclusions, P-/K= joiner). F2, F5(d), F7, F8, D3, D4, D6, M1, M3-M6 get designer text in rev. 16 (section 11 and gated
  decisions untouched). M7: no action (D029/D030). Author items for Shlok: AD1 (F3) P3 at (8, 2) against (32, 2), recommended,
  or reworded e1/e1'/e2; AD2 (F4) modifier M3 on persistence R1 at g1, recommended, or an abstract qualifier, or keep; AD3 (F5a)
  keep T1-T3 under e3, recommended; AD4 (F5b) T9 "with few cycling tests" unless P3 S, recommended; AD5 (F5c) "readable" ->
  "closed-form", recommended; AD6 (F5d) keep A9 in D* with disclosure, recommended. Unanswered items keep the approved text;
  AD1 and AD2 block the red-team signature.
- **Alternatives and why they lost:** accepting the clause/title gaps by text edits alone (cannot change section 11, D017);
  narrowing NC-1 text only (leaves the m = 16 and build-path gap untested); amending 9.3 to the code's tie rule (RES and D018
  follow the text); dropping A9 from D* (lowers P1's bar).
- **Evidence:** research/audits/SIGN_redteam_rev15.md; research/audits/SIGN_statistician_rev15.md;
  debates/codex_panel/turn11_response.md; runs/prereg/PREREG_v4.md (rev. 15) sections 1, 2, 4.1, 9-11; code lines cited in the
  judge file.
- **Proposer / opponent / judge:** red team and statistician (findings) / Codex panel turn 11 (second reviewer) / D033 judge.
- **Re-open if:** the coder cannot run the pre-`build_data` invariance test on synthetic records; the P3 re-simulation at
  (32, 2) shows the node's size above 1.2 x nominal; Shlok chooses an option that changes a state definition other than those
  listed.

### D034 Shlok accepts the judge's recommendation on all six author decisions of D033 (2026-11-06, status: accepted)
- **Decision:** AD1 Opt 1 (P3 compares g1 = (8, 2) with (32, 2): D_c = L_c(g1) - L_c(32, 2) in sections 2 and 9.4; P3 power
  re-simulated); AD2 Opt 1 (modifier M3: P+ and A1 not better than R1 persistence at g1, margin 0, 30 of 40 at 0.025, outside the
  graph; T1-T3 and T9a/T9b then take the K column's T4/T5/T6 with the added sentence); AD3 Opt 1 (keep; e3 carries the
  attribution); AD4 Opt 1 ("when cycling tests are few" -> "with few cycling tests" unless P3 is S); AD5 Opt 1 ("readable" ->
  "closed-form" in T1, T4, T7 and the matching "no ... claim" phrase); AD6 Opt 1 (keep A9 in D*, with the disclosure).
  Exact texts: debates/D033_signoff/01_judge.md, AUTHOR DECISIONS (17e74af).
- **Evidence:** Shlok's reply "Accept all six" (2026-11-06); D033 judge; red-team and statistician rev. 15 reports; Codex turn 11.
- **Proposer / opponent / judge:** red team + statistician (findings) / Codex turn 11 / D033 judge; approved by Shlok.
- **Re-open if:** the P3 re-simulation shows the AD1 contrast breaks the FWER guard (statistician), or Shlok changes an answer before FROZEN.

### D035 Tuning budget raised to N = 40 trials for every arm (Shlok, 2026-11-06, status: accepted)
- **Decision:** every tuned arm (A1, A2, A4, A9, A10/A10P where tuned, A11, A12, A13, A15, G15 and every comparator) uses
  n_trials = 40 in every confirmatory, row, sensitivity and item (f) config. Inner folds unchanged (3 at m = 32; 2 at m in {8, 16},
  D020). The equal-for-all Partial plan trigger (median hard-ODE fit > 30 s or PINN fit > 90 s -> N = 10, 2 inner folds) still
  applies to every arm alike at the FB-8 timing run. The "N = 40 if every neural fit < 20 s" branch is superseded.
- **Why:** the shake-down timings (A1 about 23-26 s) put the study just over the 20 s line; doubling the search for all arms is
  symmetric, raises the chance that every model reaches its best tuned form, and is fixed before any Samsung score.
- **Cost:** about twice the CPU of the tuning stage (PREREG 16: about 16 -> about 32 CPU-h expected for the grid; the ceiling
  doubles too); 3 single-thread processes.
- **Alternatives:** N = 20 (rule as written); N = 40 only for the PINN arms (rejected: asymmetric).
- **Evidence:** runs/freeze_shakedown/RESULT.md; Shlok "Go with your recommended option" (2026-11-06).
- **Proposer / judge:** lead / Shlok (budget choice, symmetric; no test, margin or outcome rule changes).

### D036 Freeze-commit runs recorded; freeze order (lead, record-only and procedural; 2026-11-06)
- **Decision:** the freeze-commit runs at candidate commit 92db4cb close FB-8, FB-9, FB-10 and the C27 convergence item:
  FB-8 timing trigger not reached (N = 40 stands, no Partial plan); FB-8b convergence share 1.0 for A1 and A9 at m 8 and 32,
  every fold; `nc1_full` passed at m 8, 16, 32; smoke return code 0; 43 of 43 test files passed. PREREG_v4 rev. 18 records them
  and sets the status line to FROZEN (section 18 step 3). The frozen commit is the commit that contains this row; its code/ tree
  equals 92db4cb byte for byte, and runs/prereg differs only in PREREG_v4.md outside section 11. Order: this commit, then the
  gate-auditor freeze audit on it (`research/audits/GATE_freeze_audit.md`, untracked), then the lead writes FROZEN (untracked)
  and runs `verify_freeze`; HEAD then stays put until the confirmatory runs end (D031).
- **Why FB-8b:** timing mode fits only and runs no inversion, so FB-8 could not log the convergence share that the section 7
  "Dry run and fallbacks" paragraph and C27 ask for. `runs/freeze_runs/fb8b_convergence.py` uses the training side only, the
  tuning inner folds and window, default hyperparameters and the production `predict`, and writes counts only.
- **Alternatives:** a code change in timing mode (moves code/ off the commit the FB runs used, so every FB run repeats);
  logging the share in the item (f) runs after FROZEN (too late: the fallbacks of section 7 must be decided before the freeze).
- **Evidence:** runs/freeze_runs/logs/queue.log and suite.log; runs/fb8_timing_samsung_B_f*_m*/timings.json;
  runs/freeze_runs/fb8b/fb8b_f{0-4}.json; runs/fb9_nc1_full_synth_m{8,16,32}/nc1_full.json; runs/fb10_smoke_{isu,snl}_B0.
- **Proposer / judge:** lead (record-only; no rule, test, margin, weight or title changes). The gate auditor checks it.

### D037 Freeze-audit remedies: paper-text items closed, figure scripts after the runs (lead, procedural; 2026-11-06)
- **Decision:** the gate auditor's freeze audit (`research/audits/GATE_freeze_audit.md`, untracked) passed all briefed checks and
  blocked on C3 (draft alignment) and C17 (disclosure sentences). Both are closed in `paper/draft/` by the writer
  (`paper/draft/WRITER_C3_C17_REPORT.md`) and recorded in PREREG_v4 rev. 19 with the audit's text notes. The section 20 rows for
  the figure scripts (`code/figures/*`) are done after the confirmatory runs, on a branch (D031): the scripts read only the
  statistics outputs, and editing code/ now would move the frozen tree off the commit on which the FB runs ran.
  Correction to D036 (rows are append-only): FB-8b counted 0 cells with a non-finite final latent, not "0 non-finite steps".
  FROZEN gets split key ("samsung", "S3") as well (an exploratory S3 config is pinned; 18 step 4 "plus A/S3 entries as run").
- **Alternatives:** Shlok defers C3/C17 by a decision row (the disclosures would then not be fixed before scoring); edit the
  figure scripts now and repeat FB-8 to FB-10 (about 1.5 h CPU, no gain to the evidence).
- **Evidence:** the audit file; the writer report; PREREG_v4 rev. 19 change-log row.
- **Proposer / judge:** lead / gate auditor re-check.

### D038 Statistics-step gaps G1-G8 built before the freeze; registered controls wired into Design R2 (lead; statistician SIGNED; 2026-11-06)
- **Decision:** the figure alignment of C3 showed that `stats_step.run_stats_v4` (the Design R2 entry point) never computed NC-2,
  PC-2 or PC-3 (section 10) and lacked descriptive inputs promised by sections 9.10, 11a and 14 (Table 1 arm table, R_LOO/R_WARP,
  extracted-law forms and stability metric, 11a curves, pooled residual map, Q-T interval, candidates against A1). All are built
  (`code/pinnkan/stats_gaps.py`, `stats_step.py`, `emit.py`, `physval.py`, `run.py`; report `code/pinnkan/STATS_GAPS_REPORT.md`).
  NC-2 and PC-3 use the P-chain design-effect sign test of 9.3 at 0.025 (30 of 40), outside the graph, no alpha added; PC-2 is the
  every-member monotonicity rule. A registered control that fails to compute stops a strict statistics run before the contrasts;
  one that cannot be evaluated marks the outcome provisional. physval (11a) is on by default for R2. Gate G stays NC-1 + PC-1.
  PREREG_v4 rev. 20 adds the statistician's operational rules T1 (PC-2), T2 (PC-3) and T3 (9.3 and 9.11 rows) verbatim. The figure
  scripts read only these outputs and compute no statistic (`code/tests/test_figures_read_only.py`). This replaces D037's
  deferral of the figure rows; D037's other content stands.
- **Evidence:** `research/audits/SIGN_statistician_gaps.md` (NOT SIGNED with F1-F6, then SIGNED); `code/tests/head_comparison.py
  --base 052eefd` (pre-existing outputs identical after stripping the new keys); 39 tests in `test_pk_stats_gaps_g1_g8.py`.
- **Consequence:** code/ moves off 92db4cb, so FB-8 to FB-10 and the suite are repeated at the new candidate commit; the
  92db4cb outputs are kept under `runs/freeze_runs/at_92db4cb/`.
- **Proposer / validator:** coder (gaps) / statistician; lead (procedure).
