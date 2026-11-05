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
