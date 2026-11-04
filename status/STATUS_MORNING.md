# Morning status for Shlok: PINN + KAN battery paper for JES (written 4 Nov 23:15; updated overnight)

Folder: `C:\Users\Shlok\Downloads\PINN KAN battery paper` (own git repo). Budget: weekly usage 5% at
start, 6% at 22:00 (see the end of this file for the latest); Fable 0%. CPU only, no GPU used.

## 00. LATEST (04:05): the design changed after a red team; your approval is needed
- At 03:30 the red team rated the plan FATAL: as designed, the likely result showed no measurable benefit of
  the PINN or the KAN (debates/D015_redteam_v3/01_redteam.md). A new debate (proposer, Codex opponent, Opus
  judge) produced **Design R2** (debates/D016_roles/02_judge.md, DECISIONS D016):
  - **PINN test:** with only 8 cycling conditions and 2 check-ups per held-out cell, does the PINN forecast
    held-out conditions better than the best tuned data-driven model, and is the gain due to the physics law
    (same network without it), shrinking as data grow (learning curve over 8/16/32 conditions x 0/2/full
    check-ups)?
  - **KAN test:** does the KAN give a closed-form stress law that predicts unseen conditions about as well as
    the full network, and better than an equally simplified additive (GAM) law, using a symbolic library frozen
    in advance?
  - **Cannot claim:** that the soft residual is necessary (the plain ODE uses the same law); any temperature
    mechanism or validated activation energy (temperature and lab are aliased); a "first".
  - **Realistic best case (title T2):** "Physics-informed neural networks with Kolmogorov-Arnold stress functions
    forecast lithium-ion capacity fade from few cycling tests and early check-ups". Equally plausible: T5, an
    honest learning-curve paper ("How many cycling tests and check-ups do physics-informed and data-driven
    forecasts ... need?"), weaker for JES.
- **Your decision:** approve or change the closed outcome table (nine cells T1-T8 plus modifiers M1, M2) in
  debates/D016_roles/02_judge.md section 4. After the freeze no sentence is chosen by anyone.
- Cost: about 3-3.5 more days of code before the freeze; the statistician must still simulate the sign test with
  fold- and lab-shared effects; an ISU training-side pilot (P6) gives the first signal; PREREG_v4 follows.

## 0. In one minute (written 03:25, before the red team; superseded where section 00 differs)
- **Topic fixed by debate:** a PINN whose physics combines calendar ageing (Arrhenius x KAN of SOC) and
  cycle ageing (KAN over temperature, SOC window, DoD, C-rates), trained on storage + cycling cells of the
  Samsung INR21700-50E dataset, forecasting held-out conditions from early check-ups. ISU and Sandia support.
- **Honest expectation:** it should beat the dataset authors' own model; the physics residual should help
  or tie; the KAN likely ties the best simpler stress function; it will probably not beat tuned data-only
  learners. So the likely title is the descriptive one (section 6). Tell us if you want a different framing.
- **Built overnight:** preregistration v2 (frozen only after the items below), full model + baseline code
  (204 tests, test folds locked), statistics step, all 8 figure scripts + 2 tables + graphical abstract on
  synthetic demos, draft manuscript sections 2-5 with an audited citation list.
- **Needed from you:** (1) e-gateway PDFs, Zhang JES 182, 125097 first; (2) the full Samsung download on a
  fast network; (3) a yes or a change to the framing. Nothing runs on real test data until these are done.

## 1. What is decided (all rows in research/DECISIONS.md, with alternatives and reasons)
- **Topic and title (D005, after a full debate: proposer, opponent, Codex panel, judge).** A PINN
  (solution network with a physics residual) whose dynamics add a calendar-ageing term (Arrhenius in
  temperature, KAN function of storage state of charge) to a cycle-ageing term (KAN over temperature, SOC
  window, depth of discharge and C-rates), trained on storage and cycling cells together, forecasting the
  capacity of cells at ageing conditions never seen in training, from their first check-ups.
  Preferred title: *Physics-informed neural networks with Kolmogorov-Arnold stress functions forecast
  calendar and cycle ageing of lithium-ion cells at untested conditions* (two alternatives in
  debates/D010_topic/04_judge.md; the word "forecast" stays only if the main result wins).
- **Why not the first idea (plain PINN+KAN SOH on XJTU/TJU/MIT/HUST):** already published twice in JES
  by the USTC group (PIKAN, JES 153, 120860; PGKAN, JES 182, 124768). Their code shows loss weights picked
  on the test set and per-cell whole-life scaling, so they cannot forecast; our paper targets that gap.
- **Novelty (D006):** "novel as a combination" (confidence 0.6): no PINN or KAN work on this dataset, no
  KAN battery paper with a calendar term or coupled calendar + cycle stress functions. Comparators we must
  beat: the dataset authors' own JES model (Stroebl et al., JES 142, 119552) and PiDDM (arXiv 2607.29095).
- **Data (D005):** Samsung INR21700-50E (Stroebl et al., Sci. Data 11, 1020, 2024; 279 EV-format cells,
  storage + cycling arms, 3 temperatures) primary; ISU-ILCC (251 cells, 63 cycling conditions) secondary;
  Sandia SNL external check. Your old datasets (XJTU/TJU/MIT/HUST) are not used, as you preferred.
- **Pre-set outcomes, so results cannot be spun:** the KAN is called better only if it beats an
  interaction GAM; if a plain integrated ODE beats the PINN, you choose the framing (see section 3).
- **Figures (D003, your instruction):** figure and table forms follow the best JES papers; catalogue in
  notes/exemplars/FIGURE_FORMS.md, blueprint in notes/exemplars/BLUEPRINT.md (in progress).

## 2. Needs you (sign-in or yes)
1. **VIT e-gateway: save PDFs into `refs/pdf/`.** List with links: `refs/PAYWALLED_FOR_SHLOK.md`
   (31 of your 35 references, plus exemplars). Most urgent, in this order:
   (a) **Zhang, JES 182, 125097** (doi 10.1016/j.est.2026.125097 to confirm): it cites our Samsung
   dataset and uses a PINN; its abstract is not in any open index, so it could pre-empt our novelty
   and must be read before any claim; (b) Stroebl et al., JES 142, 119552 (dataset authors' model, CC BY);
   (c) PGKAN (10.1016/j.est.2026.124768, CC BY); (d) PIKAN (10.1016/j.est.2026.120860); (e) KA-CRNN
   (Koenig and Deng, JES 158, 121853: Arrhenius parameters as KAN functions of SOC in a neural ODE, on
   thermal-abuse data; our nearest method precedent); (f) three JES papers the draft cites from their
   titles only, which must be read before submission (keys fan2025, chen2025pinn, ren2024 in
   paper/draft/refs_used.md); then the rest of the list.
2. **Samsung 50E data on a fast network (if the overnight fetch is incomplete; see section 4).** Full
   release is 10.29 GB at https://doi.org/10.6084/m9.figshare.25975315 ("Download all"); put the zip
   files in `data/raw/samsung50e_full/`. Tonight the link ran at 2-75 KB/s, so only the small check-up
   files are being fetched.
3. **Approve the title and framing** (section 1), or tell me what to change.

## 3. Open questions (decided by pre-registered tests, then put to you)
- If the plain integrated ODE beats the PINN (pilot P5 / confirmatory test), do you want the paper framed
  as "physics-informed KAN" with the PINN as a comparison? (Your brief says PINN + KAN; the judge kept the
  PINN central but fixed this rule in advance.)

## 4. Overnight work (updated as it finishes)
- Pilots: P0 Samsung file layout GO (capacity computable from check-up files); P1 data checks GO; P2 fit
  timing GO (PINN about 16-19 s per fit on CPU); P4 KAN vs additive GAM (synthetic) GO in 4 of 5 draws,
  small margin; P5 soft PINN vs plain ODE (synthetic) GO in 4 of 5 draws, small margin (5 draws: no
  significance claim; go signals only). **P3 headroom: tuned data-only learners already reach about the
  replicate noise floor on ISU (ratio 0.90) and Sandia (1.13, weak), so the claim "PINN-KAN beats the best
  data-driven model" is replaced by non-inferiority on those datasets (D007, a rule fixed in advance).**
  The paper's superiority claims then rest on: the physics residual helps, the KAN beats simpler stress
  functions, and forecasts at held-out conditions. Samsung's own headroom test runs once its data are in.
- Downloads: Samsung check-up files for all 279 cells by range requests (status:
  data/SAMSUNG_CU_STATUS.md; log data/logs/samsung_cu.log). Bulk downloader paused (data/STOP_DOWNLOADS)
  because of the slow link. At 23:20 the fetch ran at about one file per 30 s (figshare request latency),
  about 6 min per cycling cell, so the night covers roughly the first 60 cells: the fetch order puts one
  replicate of every cycling and storage condition first. **The full set needs your download on a fast
  network (item 2 of section 2).** To stop the fetch: create an empty file `data/STOP_SAMSUNG`.
- References read in full so far: 8 (refs 8, 11, 15, 23, 29, 30, 31, 33), plus the Samsung dataset paper
  and the ISU dataset paper; notes in notes/papers/.

## 5. Data facts found overnight (they shape the paper)
- **Samsung 50E is two campaigns.** 279 cells = 141 in stage 1 + 138 in stage 2; the stage-2 cells reuse the
  stage-1 names but are different cells at different conditions (figshare holds two zips per name). Fixed
  in the fetcher at 00:05; if you download "all" from figshare, keep every zip (do not let Windows
  overwrite same-named files: download into two folders, or keep figshare's file IDs).
- **Temperature is partly confounded with laboratory:** all 35 C cycling cells were tested at one lab
  (INT), 45 C mostly at another (HM), 10 C storage all at a third (SIE). The temperature-extrapolation
  test will state this and carry a lab/stage sensitivity check; no claim will separate the two.
- **Only 66 of 132 storage cells have intermediate check-ups.** The storage arm forecasts from those.
- **A preregistration draft exists** (runs/prereg/PREREG_DRAFT.md): hypotheses, splits, every model
  arm, statistics, and which title follows each outcome. It is frozen only after Zhang JES 182, 125097
  is read and the full Samsung data is in.

## 6. Likely outcome, said now (statistician D009 and judge D011)
- Final primary tests (D011): physics residual on vs off; KAN stress functions vs the best simpler stress map
  (GAM, interaction GAM, polynomial, MLP); and our model vs the dataset authors' own model (Stroebl et al.).
  Beating the best data-only learner is a key secondary test.
- With about 40 test conditions the design detects relative gains of roughly 10-19% only. The judge's most
  likely outcome: better than the authors' model, residual helps or is not worse, KAN ties the best GAM,
  data-only learners not beaten, PINN vs plain ODE unresolved. Then **title 3** applies (descriptive, no
  "forecast" verb): *Learning stress-dependent calendar and cycle ageing laws of lithium-ion cells with
  physics-informed neural networks and Kolmogorov-Arnold networks*. The paper's selling points would be
  the coupled calendar + cycle PINN-KAN, the learned stress laws and their physical checks, and the gain
  over the dataset authors' model, not raw accuracy over machine-learning baselines.
- **Your call:** are you happy with that framing as the likely result, or do you want the team to look for
  a design with more statistical power (e.g. adding the ISU and SNL cycling conditions to the primary test,
  at the cost of a less clean claim)?
- Before the preregistration is frozen: Zhang JES 182, 125097 and Stroebl JES 142, 119552 read (your
  e-gateway download), full Samsung data in (your download), throughput checked on cycling logs.
- (01:25) The significance test is now the exact sign test on the median held-out condition (D012); the
  35 C test is descriptive only. The abstract would say "for the typical (median) held-out condition".

## 7. Prior art read in full overnight (positioning)
- PiDDM (arXiv 2607.29095): physics law with network-predicted parameters on XJTU; no storage cells, no KAN, no
  held-out condition, needs the test cell's features every cycle (not an early forecast).
- Guo et al. (arXiv 2607.16864): closest on the task (PINN forecasts an unseen cell from 2-20 % of early life);
  no KAN, no calendar term; some abstract numbers do not match its own table.
- KA-CRNN (JES 158, 121853; arXiv 2512.15628): KAN functions of SOC inside an Arrhenius law, but for
  thermal-abuse kinetics, not ageing.
- Consequence: the paper claims only the combination (coupled calendar + cycle PINN with KAN stress functions,
  storage and cycling cells together, held-out conditions from early check-ups), never "first KAN in a rate
  law" or "first early-data physics forecast". Safe wording: notes/papers/PRIORART_SUMMARY.md.
