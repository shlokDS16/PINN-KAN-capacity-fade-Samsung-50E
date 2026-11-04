# D010 judge's verdict: topic, title, method, datasets, experiments (2026-11-04, night)

Role: judge (did not propose or attack). Reading: **full text** of CONTRACT.md, 02_proposal.md,
03_opponent.md, codex_panel/turn02_response.md, 01_novelty_audit.md, notes/code/PIKAN.md, GAPS.md,
data/INVENTORY.md, research/DECISIONS.md, pilot_scratch/output.txt; JES guide **partial** (sections on
article types, title, abstract, highlights, tables, appendix policy). No paper read by me. The
Samsung 50E condition counts below were **counted by me from the local `experiments_meta.csv`**
(not from the Scientific Data paper, which nobody on the team has read). No model has been run; every
threshold below is a decision rule fixed now, not a result.

---

## 1. Verdict and the decision

**Verdict: REVISE (accepted with the changes below; the proposal as written is rejected).**
The opponent is right on four points that are fatal or near-fatal as written: there is no PINN in the
headline (1.1), the KAN at width [3,2] is a GAM by identity (2.1), the ISU primary cannot separate
calendar from cycle loss and cannot test temperature (3.4, 4.2, 3.6), and the programme does not fit a
CPU week (7.1). Codex agrees on scope and on the PINN question. But the proposer's core idea (a
stress-conditioned rate law whose stress dependence is a KAN, forecasting unseen cells from an early
window) survives, and it becomes a better paper when it is moved onto the one dataset in INVENTORY whose
**experimental design** separates the two ageing modes: Samsung INR21700-50E, with storage cells and
cycling cells of the same cell type.

The decision re-centres the paper on **PINN + KAN for calendar-plus-cycle ageing**, which is what the
author asked for and where both components can be shown to do work, or shown not to, by pre-stated tests.
Identifiability is demoted from headline to one supporting figure (it is not novel enough to carry the
paper: opponent 6.1).

**Research question.** Can a physics-informed neural network whose dynamics are a calendar-plus-cycle
ageing law with Kolmogorov-Arnold stress functions, trained jointly on storage and cycling cells, forecast
the capacity fade of a lithium-ion cell at an ageing condition absent from training (including an untested
temperature) from its first check-ups, and is each of its two parts (the physics residual and the KAN
stress functions) needed for that accuracy?

**Single falsifiable claim (primary).** On held-out cycling conditions of the Samsung 50E matrix
(Test B, primary window), the PINN-KAN has lower cell-level retention RMSE over the forecast set than
**every** model that removes one of its parts or replaces it with the strongest alternative:
(i) the same network without the physics residual (data-only, same inputs, lambda = 0);
(ii) the same PINN with the KAN stress functions replaced by the best of {parametric Arrhenius/power-law
factors, additive-spline GAM, GAM with prespecified interactions, degree-2 log-polynomial with all cross
terms, parameter-matched MLP};
(iii) the best tuned data-only learner (GP with ARD, LightGBM).
Refuted if any of the three paired contrasts (condition-level units, Holm over the three) is not
significant at 0.05 or its effect is below the margin fixed in the preregistration from inner-CV
replicate spread (section 6). The hard-ODE contrast (section 2) is preregistered separately: it does not
refute the claim; it decides how the PINN is framed.

**Titles** (JES guide: no abbreviations, no optimisation technique in the title).
1. **Preferred:** *Physics-informed neural networks with Kolmogorov-Arnold stress functions forecast
   calendar and cycle ageing of lithium-ion cells at untested conditions*
2. *Coupling calendar and cycle ageing in a physics-informed Kolmogorov-Arnold network to forecast
   lithium-ion capacity fade under unseen stress conditions*
3. *Learning stress-dependent calendar and cycle ageing laws of lithium-ion cells with physics-informed
   neural networks and Kolmogorov-Arnold networks*
Fallback if Samsung data cannot be obtained (section 4, no calendar arm): *Physics-informed neural
networks with Kolmogorov-Arnold stress functions forecast capacity fade of lithium-ion cells under unseen
cycling conditions.*
The verbs "forecast" in titles 1 and fallback are earned only if the primary claim passes; if it ties,
title 3 (descriptive, no performance verb) is used. "Identifiable" is removed from every title.

---

## 2. Where the PINN does real work, stated plainly, and how it is tested

**The honest premise (ruling).** For a scalar ageing ODE with a fully trusted rate law, a soft PINN
residual cannot enforce anything that exact integration (hard ODE) does not enforce more exactly; the
proposer, the opponent and Codex all say so, and I agree. A PINN differs from a hard ODE only where the
law is **not** fully trusted. Real cells are such a case. So the PINN is the headline formulation, and the
paper tests, with a pre-stated outcome, whether its soft coupling helps. This is not a straw man: the hard
ODE with the same KAN law is a full-strength competitor.

**Architecture (Wang-2024 F/G form, with G made physical and stress-conditioned).**
- **Solution network F:** y_hat = F_psi(t_tilde, s, z_c), retention loss y = 1 - Q/Q0,c, with
  t_tilde = time since the cell's first check-up (days, global scaling only, never per-cell life
  fraction: this is the PIKAN defect, PIKAN.md 4), s = stress vector, z_c = low-dimensional per-cell
  latent. Hard initial condition y_hat(0) = 0 by construction (y_hat = t_tilde * g(.)). F is a small MLP
  (the KAN's role is the stress map, so the two parts stay separable in ablation; F = KAN is one ablation
  row).
- **Dynamics G (the physics):** dy/dt = r_cal + r_cyc * nu, where nu = equivalent full cycles per day
  (from the cycling log; zero for storage cells),
  r_cal = exp(a(SOC) - E(SOC) (1/T - 1/T_ref)/R) * h_cal(y),
  r_cyc = exp(f(T, SOC_window, DoD, C_ch, C_dch) + delta_c) * h_cyc(y).
  a(.), E(.) (prefactor and activation energy as functions of storage SOC) and f(.) are the KAN stress
  functions (section 3). h_cal, h_cyc are state factors chosen by a small backbone tournament on training
  cells only (self-limiting 1/(y + y0); constant; accelerating exp(gamma y)), ties to the simpler.
  Terms are named **time-driven** and **throughput-driven**, never SEI or plating (opponent 4.2 accepted).
- **Residual:** R = dF/dt_tilde - [r_cal + r_cyc nu] by autograd. Loss = data term at check-ups +
  lambda_res * mean R^2 over collocation points + prior on z_c/delta_c. lambda_res by inner grouped CV on
  training conditions (log grid of 5; an edge optimum extends the grid).
- **Collocation points (fixed, label-free, not self-referential; opponent 1.2 accepted):**
  (a) along every training cell's time axis from the end of its observed record to a fixed horizon
  t_max set from the design's longest test duration (known before data); (b) at **unobserved stress
  points**: a fixed Latin-hypercube sample inside the convex hull of the training design;
  (c) at the **calendar twins** of cycling conditions: (T, SOC) with nu = 0, including T = 35 C, where the
  Samsung matrix has cycling cells but no storage cells (counted from `experiments_meta.csv`: storage at
  10/23/45 C, cycling at 23/35/45 C). Points are resampled from these fixed sets each step.

**What the PINN does that data and a hard ODE cannot.**
1. **Soft coupling under misspecification.** F is a flexible surface over (t, s) shared by all cells;
   where data exist and the law is wrong, F may depart from the law (paid for by the residual); where no
   data exist (beyond the window, at 35 C storage, between conditions) F is held to the law. A hard ODE
   has no such trade-off: its forecast is the law. A data-only F has no law outside the data.
2. **A residual map over stress space.** The trained residual |R| on a stress grid shows where the
   learned law and the data disagree (for example a storage-cycling superposition failure at high
   temperature and high SOC). A hard ODE has no residual; this diagnostic exists only in the PINN and is
   one figure (section 6, Fig. 7).
3. **Physics-regularised test-time inversion.** For an unseen cell, z_c is fitted to its window points
   plus the residual over the forecast horizon (causal: no label after the window).

**Fair hard-ODE vs soft-PINN comparison (preregistered).** Same G, same KAN, same backbone, same per-cell
offset, same inner-CV tuning budget, same data; hard ODE = vectorised RK4 through G with delta_c MAP from
the window. Endpoint: the primary endpoint. Outcomes, stated now:
- **(A) PINN better** (paired, margin as in section 6): the soft residual is a contribution; the
  headline stands as titled.
- **(B) tie:** the paper says plainly that the residual is equivalent to exact integration for
  forecasting at this design; the PINN remains the formulation because it is the only one giving the
  residual map and solver-free training; the claim rests on the calendar-cycle KAN law and on contrast (i)
  of section 1. Title 3.
- **(C) hard ODE better:** using the PINN as headline would knowingly present the weaker tool. The lead
  must then **put the choice to Shlok**: (C1, judge's recommendation) headline becomes the hard-constrained
  physics-informed KAN, title 2 with "physics-informed Kolmogorov-Arnold network", the PINN reported as
  the soft variant; or (C2) keep the PINN headline with the hard ODE reported as stronger in the ablation
  (a weaker paper, but the brief's wording kept).
The same contrast is run on synthetic data with a misspecified generator (section 6, G1), where theory
predicts (A) is most likely; a PINN that does not beat the hard ODE even there is evidence for (B)/(C).

---

## 3. Where the KAN does real work, and the fair GAM test

**Placement.** The KAN is the stress-to-log-rate map, nowhere else:
- calendar: KAN [1, 2] from storage SOC to (a, E); this is univariate and therefore a spline GAM in KAN
  basis; I rule that **no superiority is claimed for this part** (opponent 2.1 accepted). Its value is
  the shape of the SOC dependence of prefactor and activation energy, read from the edges;
- cycling: KAN [5, h, 1] over (T, SOC window, DoD, C_ch, C_dch), **with a hidden layer**, h in {2, 3, 4}
  by inner CV. This is where a KAN differs from a GAM: it can represent interactions (for example a
  charge-rate effect that changes with temperature or with SOC window) without the interaction set being
  written down. Identifiability is judged at **function level** (response surfaces and partial
  dependences), never at edge level, because hidden-layer edges have permutation and scale symmetries.
- B-spline KAN (cubic, grid 3 to 6 by inner CV, sparsity L1 + entropy weights by inner CV). Temperature
  enters G through the Arrhenius form; Test C (35 C) is inside the 23-45 C grid, so the B-spline
  extrapolation weakness (opponent 2.2) does not bite there; stress extrapolation outside the hull is not
  claimed.

**Fair contrast (Codex 4 and opponent 2.2 accepted in full).** Same G, same splits, inputs and
training-only scaling, equal TPE budget, comparable effective degrees of freedom (reported):
additive-spline GAM (= KAN [5,1]); GAM with prespecified pairwise interactions (tensor-product splines
on T x C_ch, T x SOC, DoD x SOC); degree-2 log-polynomial with all cross terms; parameter-matched MLP;
parametric Arrhenius/power-law factors. Symbolic rounding (proposal 3.8) is applied to the GAM and
polynomial as well as to the KAN (opponent 2.3), and moves to the Appendix.

**Pre-stated KAN outcomes.**
- KAN better than every contrast on the primary endpoint (paired, Holm) and on synthetic interaction
  recovery (G2): KAN superiority is claimed.
- **Tie** (within the margin) with the best GAM: the claim made instead is "KAN stress functions reach
  the accuracy of the best prespecified-interaction GAM without specifying the interactions, and their
  response curves agree with it"; no superiority wording; the title keeps "Kolmogorov-Arnold" because it
  names the model used.
- KAN **worse** than a GAM by the margin: using it would make the paper wrong; KAN leaves the headline,
  and the lead puts the retitle to Shlok.

---

## 4. Datasets

**Primary: Samsung INR21700-50E** (Scientific Data 2024, figshare 25975315, CC BY 4.0). Counted from the
local metadata: 132 storage cells in 19 conditions (10/23/45 C x storage SOC, 6 replicates; 24 at one
23 C centre point) and 147 cycling cells in 40 conditions over 23/35/45 C x SOC window x DoD 5-60 % x
charge 0.2-1C x discharge 0.2-2C (mostly 3 replicates; four centre points with 6 to 12). Why primary:
(1) it is the only set on our list where calendar and cycle loss are separable **by design**, which
answers opponent 4.1 (two mechanisms separable only by curve shape) and 3.4/4.2 (throughput clock for a
time law) by experiment, not by modelling; (2) temperature has 4 levels overall, with 35 C cycling and no
35 C storage, which gives the PINN a natural place to work (section 2); (3) EV-format 21700 NCA/graphite
cells (opponent 9); (4) not a PINN4SOH set (CONTRACT 1). Unknowns that decide whether it stays primary:
check-up cadence, per-cell file schema, whether check-up capacities are a small separable member of each
per-cell zip. **Nobody has read the Scientific Data paper; the novelty re-audit must search for existing
models (semi-empirical, ML, PINN) fitted to this very dataset, including by its authors, before
confirmatory runs.**

**Secondary: ISU-ILCC** (figshare 22582234; 63 cycling conditions over C_ch x C_dch x DoD at 30 C,
4 replicates, weekly reference tests; `capacity_fade` and `Q_interpolated` local). Role: the cyclic KAN
law with many conditions and replicates (interactions in C_ch x DoD; a second chemistry and format).
Cyclic term only (no storage arm; claims restricted accordingly). Time coordinate: weeks on test with an
analytic cycles-per-week forcing, its error checked on fetched `Cycling_json` members (opponent 3.3:
the full 10.2 GB is **not** a dependency). The ISU authors' arXiv 2307.08382 must be read in full and
their EOL MAPE metric reported alongside ours on ISU (opponent 3.2 accepted).

**External generality check: Sandia SNL** (local, verified, per-cycle): temperature 15/25/35 C x
discharge rate per chemistry. One table row and one panel; no Arrhenius curvature claim (3 levels,
unbalanced, possible duplicated records per INVENTORY; opponent 3.7 accepted). It is also tonight's
development set because per-cycle throughput is on disk.

**Not used:** XJTU, TJU, HUST, MIT (PINN4SOH sets; no stress columns; PIKAN/PGKAN own SOH estimation
there). PIKAN is discussed from its code, never claimed reproduced.

**Fetch tonight (exact, small; at about 30 KB/s):**
1. Samsung: HTTP range-read of the zip central directory of 4 per-cell zips (2 storage: one 10 C, one
   45 C; 2 cycling: one 35 C, one 45 C centre point), a few KB each, URLs from `DEFERRED_URLS.tsv`. If a
   check-up/capacity member exists, fetch that member only for the same 4 cells (stop if any member is
   above 5 MB). If such members are small, queue the same member for all 279 cells overnight in the
   resumable downloader, provided the listed total is under 400 MB (about 4 h at 30 KB/s).
2. ISU `Cycling_json`: after item 1, member range-fetch of 6 cells at the corners of the design
   (low/high C_ch x low/high DoD, plus G26 low-DoD and G9 fast-failing), about 25 min each, resumable,
   for the cycles-per-week calibration. Not more tonight.
3. Nothing else. Do not start long single requests around 23:00 or 00:15.

**Waits for a better network or Shlok:** the full Samsung release (storage 2.04 GB, cycling 8.25 GB), to
be downloaded by Shlok on a faster network on 05 Nov if item 1 shows capacities are not separable. All
279 cells are fetched (no convenient subset; Codex 3). The remaining ISU `Cycling_json` is not needed.
**Deadline:** if Samsung check-ups are not on disk and parsed by **07 Nov 09:00**, the fallback applies:
ISU primary (cyclic law, weekly), SNL secondary, the calendar component and titles 1-3 drop, fallback
title used.

---

## 5. Answers to the opponent and to Codex

| Point | Ruling | Change |
|---|---|---|
| Opp 1.1 no PINN in headline | **Accepted** | PINN (F/G with residual) is the headline formulation; hard ODE is a preregistered full-strength control with outcomes A/B/C (section 2); outcome C goes to Shlok |
| Opp 1.2 self-referential collocation | Accepted | Fixed, label-free collocation sets (time horizon, design hull, calendar twins) |
| Opp 1.3 "network" oversells [3,2] | Accepted | Cyclic KAN has a hidden layer; univariate calendar part claims no superiority |
| Opp 2.1 KAN [3,2] = GAM | Accepted | Hidden-layer KAN main; additive KAN is the GAM ablation; function-level identifiability |
| Opp 2.2 unfair R4, S2 additive, Test C extrapolation | Accepted | Interaction polynomial and interaction GAM added; non-additive generator G2; Test C is interpolation in T only |
| Opp 2.3 rounding trivially passes | Accepted | Same rounding test for GAM/polynomial; Appendix only |
| Opp 3.1 ISU weak; DoD estimated; RPT schedule varies | Accepted | ISU demoted to secondary; RPT-schedule group recorded as a covariate in the window description; claims "per realised mean DoD" |
| Opp 3.2 ISU authors' hierarchical paper | Accepted | Full read; their EOL MAPE reported on ISU |
| Opp 3.3 10.2 GB dependence | Accepted | Not a dependency; 6 members calibrate an analytic forcing |
| Opp 3.4 coordinate artefact, calendar loss | Accepted | Solved by design on Samsung (storage arm); on ISU, exponent ranking reported in weeks and in throughput |
| Opp 3.5 outcome-based exclusion | Accepted | No cell excluded by outcome: cells failing inside the window are scored as forecast failures in a preregistered sensitivity row; primary set definition fixed from cadence before data |
| Opp 3.6 Samsung not examined | **Accepted** | Samsung primary |
| Opp 3.7 SNL cannot carry DoD/Arrhenius | Accepted | SNL = generality row and development set only |
| Opp 4.1 two mechanisms not separable | Accepted | Separated by the storage arm; one per-cell offset by default (Codex 1), second only if inner CV supports it |
| Opp 4.2 mechanism labels, self-heating, SOC window | Accepted | Terms named time-driven/throughput-driven; SOC window is a stress input; self-heating stated as a limitation (no cell-temperature claim unless logged temperature exists in the files) |
| Opp 4.3 DoD a measured property | Accepted (ISU) | Stated in limitations |
| Opp 5.1 circular synthetic truth, thresholds after pilot | **Accepted** | Truth never from model fits; misspecified generators carry the evidence; thresholds fixed in this file (section 6) |
| Opp 5.2 free-G straw man | Partly accepted | Free-G arm kept, labelled "unstructured dynamics with stress inputs", not PIKAN; matched constrained-flexible arms added (parametric G, GAM G, MLP G) so the source of any identifiability is located |
| Opp 5.3, 7.1 compute | **Accepted** | Design-size sweep dropped; 3 generators x 20 draws; baselines cut to 9 arms; budget gate from measured seconds per fit (P2) |
| Opp 5.4 interactions not orthogonal in ISU | Accepted | Interaction claims made on Samsung (space-filling design) first |
| Opp 6.1 identifiability novelty overclaimed | **Accepted** | Not claimed as novel; supporting figure only |
| Opp 6.2 editor sees ML-methods paper | Accepted | Experimentally checkable claim added: the storage law learned jointly predicts held-out storage conditions (secondary S2) |
| Opp 7.2 two papers glued | Accepted | One paper: forecasting with a calendar-cycle PINN-KAN; identifiability one figure |
| Opp 8.1 noise floor / tie | Accepted | Tie plan below; P3 headroom on training folds only |
| Opp 8.2 test folds touched in P1 | **Accepted** | P3 uses inner CV inside training conditions only; splits fixed first |
| Opp 8.3 effective units | Partly accepted | Condition-level units, cluster bootstrap by condition, per-fold results shown; neighbour correlation not modelled (stated) |
| Opp 9 weaker than best JES papers | Partly accepted | EV-format primary + 2 more datasets; PINN4SOH-style sub-percent MAPE is estimation, not forecasting, and is said so in the text, not chased |
| Codex 1 too much bundled | Accepted | Cuts above |
| Codex 1 exp(gamma y) blow-up | Accepted | Backbone tournament on training cells; share of diverging forecasts reported; tie goes to simpler |
| Codex 2 PINN not central by default | **Rejected** as a default (the brief requires PINN), but its substance is adopted: the hard ODE is a fair control and outcome C hands the framing to Shlok |
| Codex 3 dataset | Accepted | Samsung if accessible, all cells, no convenient subset; ISU otherwise |
| Codex 4 KAN vs GAM | Accepted in full | |
| Codex 5 title "When are ... identifiable" | **Rejected** | Drops PINN and KAN, makes identifiability the headline although it is not novel (opponent 6.1) |
| Codex 5 four figures | Accepted in spirit | Plan below |
| Codex 6 cheapest pilot | Accepted | P3-P5 |

---

## 6. Experiments, endpoints, tie plan, reduced identifiability

**Task (identical for every model).** Inputs: s_c, Q0,c (first check-up), check-ups inside the window.
Output: retention at every later check-up. SOH = Q/Q0,c of the cell's own first check-up.
**Primary window:** the first k check-ups after the initial one, k fixed in `runs/prereg/` from the
cadence alone (after P0, before any model sees a test label). Secondary: k-1 and k+2.
**Tests.**
- **Test B (primary):** grouped folds over the 40 cycling conditions (5 folds of 8, stratified by
  temperature); all storage cells are in training (they are a different experiment; no test cycling cell
  enters training or tuning).
- **Test C (secondary):** all 35 C cycling conditions held out (13 conditions counted from the metadata);
  train on 23/45 C cycling plus all storage. This is a physical interpolation test in temperature, not a
  protocol comparison; no ratio between Tests B and C is reported (retired topic).
- **S2 storage transfer (secondary, physical check):** grouped folds over the 19 storage conditions;
  forecast held-out storage cells from their window.
- ISU and SNL: Test B analogue only (held-out conditions).
**Primary endpoint:** cell-level retention RMSE (percentage points) over the forecast set, averaged within
condition then over conditions, Test B, primary window, 5 seeds, frozen configuration.
**Secondary:** error at fixed horizons after the window (CONTRACT 6); RUL error in days where the cell
reaches 80 % inside the record; MAE, MAPE, R^2 with correct argument order; Test C; S2; ISU EOL MAPE
for comparison with the ISU authors; wall clock and parameter count.
**Arms (9, each with its own TPE budget, same for all learned arms):** PINN-KAN (main); hard-ODE-KAN;
PINN with parametric stress factors (PiDDM-style: fixed law, parameters by a small MLP of s); PINN with
additive GAM; PINN with interaction GAM; PINN with interaction polynomial; PINN with free G (stress
inputs); data-only F (lambda = 0); semi-empirical calendar + cycle model (parametric, least squares);
plus data-only GP-ARD and LightGBM on (s, window summary, t). LSTM/Transformer, PiDDM reimplementation
from its paper, BatLiNet/FlowBatt: dropped (discussed, no numbers).
**Tuning:** inner grouped CV by condition inside the training folds only; 20 TPE trials x 3 inner folds
per arm per outer fold, unless P2 shows fits under 20 s (then 40). Test folds touched once per frozen
configuration.
**Statistics:** paired Wilcoxon on condition-level differences, cluster bootstrap (10,000) by condition
for mean differences, Holm over the three primary contrasts; effect sizes always shown.
**Margin (fixed by rule now, value computed before confirmatory runs):** the non-inferiority / superiority
margin is the median, over training conditions, of the leave-one-replicate-out RMSE of the condition-mean
trajectory (replicate floor), computed by inner CV inside training folds only.
**Tie plan (stated now).** If the PINN-KAN beats (i) and (ii) but not (iii) the data-only learners: the
paper claims parity in accuracy plus physical consistency (S2 storage transfer, Test C, residual map) and
uses title 3; this is a JES applied-modelling paper with a weaker results section, and the lead tells
Shlok before writing. If it fails (i) (the residual does not help) or (ii) (KAN does not help): the
corresponding part is reported as unnecessary and section 2 outcome C or section 3 "worse" logic applies,
with the choice put to Shlok.

**Reduced identifiability programme (one figure + Appendix; not circular).**
- Design: the real Samsung design (conditions, replicates, cadence from P0); the ISU design in tonight's
  pilot.
- Generators, written before any real-data fit: **G0** well-specified (sanity only, never cited as
  evidence); **G1** misspecified time law (storage loss proportional to t^z with z depending on T, and a
  logistic knee in throughput whose onset shifts with stress; neither is in the model's state form);
  **G2** non-additive stress law (a charge-rate hinge whose threshold shifts with temperature, plus a
  DoD x SOC product term). Optional G3: storage and cycle terms not additive (cycling scales the storage
  rate), to test whether the PINN residual map flags the superposition failure.
- Truth: functional forms and coefficients from a grid fixed in normalised units in `runs/prereg/`;
  only the **overall fade level** at the last check-up and the **noise level** are matched to summary
  statistics of the training cells (median fade and replicate spread), never to fitted model parameters.
- Metrics: nRMSE of the recovered log-rate surface on a fixed 500-point Latin hypercube in the design
  hull, divided by the true log-rate range; Kendall tau of variance-based stress importance with truth;
  forecast RMSE on held-out conditions.
- **Thresholds (fixed here):** pass nRMSE <= 0.15 on G1 and G2; fail > 0.30; in between "partial".
  Structured (any structured G) vs free G: structured median nRMSE <= 0.67 x free-G median and paired
  Wilcoxon p < 0.05 over 20 draws. KAN vs additive GAM on G2: KAN lower nRMSE, paired p < 0.05; on G0
  the KAN must not exceed the additive GAM's nRMSE by more than 10 % (no penalty for flexibility).
  Interval widths are reported as a diagnostic only; no coverage or calibration claim (retired topic).
- Size: 3 generators x 20 draws x 4 models (PINN-KAN, hard-ODE-KAN, additive GAM, free G) = 240 fits.

**Figure/table plan (forms to `debates/D-figures.md` against FIGURE_FORMS.md, CONTRACT 6a):** 1 method
schematic (F/G, KAN stress functions, storage + cycle arms, collocation sets); 2 design map (59
conditions, storage vs cycling, replicate fade); 3 forecast overlays at held-out conditions incl. 35 C;
4 forest plot of paired differences (primary endpoint) for all arms; 5 learned stress functions (storage
SOC prefactor and activation energy; cyclic partial dependences) with seed/fold envelopes; 6 storage
transfer and storage share of cycled cells' fade; 7 PINN residual map over stress space; 8 synthetic
recovery (G1, G2): structured vs GAM vs free G; Table 1 main results (Samsung B, C, S2; ISU; SNL);
Table 2 ablations. Replication detail, sensitivity rows and symbolic rounding go to the Appendix (JES
supplementary policy).

---

## 7. Pilots for tonight (CPU only, each under about 1 h CPU, in this order; at most 3 agents at once)

| # | Pilot | Data | Go / no-go |
|---|---|---|---|
| P0 | **Samsung schema by range request** (section 4 item 1); parse fetched members with `python -I` (CSV text only; nothing from inside a zip is executed) | 4 per-cell zips, KB to a few MB | **Go:** a member gives (time, cumulative Ah or cycle count, check-up capacity) per check-up and the all-cell total of that member is < 400 MB: queue it for all 279 cells overnight. **No-go:** capacity only inside the full raw files: write the full download list for Shlok (05 Nov, faster network) and continue on ISU/SNL. Record cadence (number of check-ups, days between) for the window rule either way. |
| P1 | **Local data readiness:** (a) re-check ISU Table A1 (63 conditions) against `README_V2.0.pdf` via markitdown; (b) SNL per-cycle schema: capacity, time, throughput per cycle per cell through the allowlist loader; flag duplicated records (INVENTORY caution) | local | **Go:** Table A1 matches the scratch transcription; SNL gives per-cycle capacity and throughput. **No-go:** fix transcription; drop duplicated SNL cells from all analyses. |
| P2 | **Seconds per fit:** minimal hard-ODE-KAN (RK4) and minimal PINN-KAN (F + residual, fixed collocation) on SNL (or ISU capacity_fade with weeks), all cells, CPU, 1 thread and 3 threads | local | **Go:** hard fit <= 30 s and PINN fit <= 90 s: budget in section 6 holds. **Partial:** up to 3x slower: trials 20 -> 10 and inner folds 3 -> 2, seeds stay 5. **No-go:** > 3x: the lead re-plans the arm list before day 2. Write the measured budget to `runs/pilot_P2/`. |
| P3 | **Headroom on training folds only (ISU, then SNL):** fix Test B splits in `runs/splits/` first; inside the training conditions only, inner grouped CV: replicate floor (section 6 margin rule) vs tuned GP-ARD/LightGBM on (s, window summary, t) vs per-cell power law | local | **Go:** best flexible learner's inner-CV error > 1.2 x replicate floor: superiority is winnable on that dataset. **No-go:** <= 1.2 x: on that dataset the primary contrast (iii) is preregistered as non-inferiority, decided now, before confirmatory runs. No test fold is read. |
| P4 | **Synthetic KAN-vs-GAM and structured-vs-free-G mini (G2, ISU design, 5 draws):** hard-ODE with KAN [3,h,1] vs additive GAM vs free G | synthetic | **Go:** KAN lower nRMSE than additive GAM in >= 4 of 5 draws and structured below free G in >= 4 of 5. **No-go (KAN):** KAN ~ additive GAM even on G2: tell the lead tonight that the KAN claim will likely be the tie wording; no change to the plan. **No-go (structure):** free G as good: identifiability figure is dropped. |
| P5 | **Hard vs soft under misspecification (G1, ISU design, 5 draws, lambda_res in 3 values chosen by inner CV)** | synthetic | **Go:** PINN forecast RMSE beyond the window below the hard ODE in >= 3 of 5 draws. **No-go:** expect outcome B or C on real data; the lead asks Shlok in the morning which framing he prefers if C occurs (no work stops). |

Order matters: P0 first because it uses the network while it is up; start the ISU 6-member fetch (and the
Samsung member queue if P0 says go) in the background after P0; P1-P2 next (they gate implementation);
P3-P5 last. All outputs to `runs/pilot_P*/` with config, commit and seed; scratch numbers are not results.

---

## 8. What would re-open this decision

1. Samsung check-ups not on disk and parsed by 07 Nov 09:00 -> fallback (ISU primary, SNL secondary,
   no calendar arm, fallback title). Re-open D010 only if ISU's P3 also shows no headroom.
2. The novelty re-audit (required before confirmatory runs; must include the Samsung 50E Scientific Data
   paper and any work modelling that dataset, PIKAN/PGKAN full texts, JECS addd4e, arXiv 2607.16864,
   arXiv 2307.08382) finds a PINN or neural model that couples calendar and cycle ageing with learned
   stress functions and forecasts unseen conditions -> re-open topic.
3. P0/P2 show the Samsung check-up cadence is too sparse for any window (fewer than 3 post-window
   check-ups for most cycling cells) -> Samsung becomes secondary for storage transfer only.
4. Section 2 outcome C on real data -> framing choice to Shlok (not a re-open of the topic).
5. P2 compute no-go -> re-plan arms (not the topic).
6. Shlok rejects a calendar-plus-cycle framing or names another dataset.

---

## 9. Decision row

Appended to `research/DECISIONS.md` as D005.
