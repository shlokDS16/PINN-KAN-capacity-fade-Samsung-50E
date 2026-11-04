# D010 novelty re-audit of the revised topic (2026-11-04, night)

Auditor: novelty-auditor (checks only; no rescue suggestions). Read: CONTRACT.md, 04_judge.md, 01_novelty_audit.md.
Reading depth tags: **FT** full text; **FT-partial** full text, some sections; **AB** abstract only (OpenAlex, Crossref,
publisher page or search snippet); **META** metadata and file listing only.
Tools that worked: OpenAlex (search, `cites:` filter), Crossref, DataCite, figshare API, arXiv abs pages, WebSearch,
WebFetch, Europe PMC. **Not available / not done:** Exa (the Exa fetch tool did not load; ToolSearch returned only
WebFetch and WebSearch), Semantic Scholar, **OpenReview (ICLR 2027, NeurIPS 2026) not searched**, Google Scholar
itself. The arXiv API returned few results for exact-phrase queries, so arXiv was covered mainly through OpenAlex
(which indexes arXiv) and WebSearch.

## 0. Verdict

**Revised claim (restated as one sentence).** A physics-informed neural network whose dynamics are a storage
(calendar) term, Arrhenius with KAN functions of storage SOC, plus a throughput-driven cycling term, a KAN over
(T, SOC window, DoD, C_ch, C_dch), trained jointly on storage and cycling cells of the Samsung INR21700-50E dataset,
forecasts the capacity of cells at held-out conditions from their first check-ups better than versions that remove
the physics residual or the KAN stress functions.

| Item | Verdict | Confidence |
|---|---|---|
| Specific claim (joint calendar + cycle PINN with KAN stress functions, forecast at held-out conditions from first check-ups, on Samsung 50E) | **NOVEL as a combination** (nothing found that does it; every ingredient is public) | 0.65 |
| Model class alone (physics-informed / UDE degradation law with learned stress dependence, Arrhenius + throughput) | **INCREMENTAL** (PiDDM, Shi et al., Kuzhiyil et al., Gasper et al., Li et al.) | 0.70 |
| "First KAN or PINN on Samsung 50E" | **Not found; no published model of any learned kind on the Stroebl et al. data was found**, except one analysis that uses the archive among ten (Zhong, preprint) | 0.65 |

Overall: **NOVEL (narrow, as a combination and as an evidence design), 0.6.** A hostile reviewer will assemble it from
PiDDM (law + neural parameters), Kuzhiyil (neural network inside a known state equation, calendar ageing),
Shi-Rivera-Wu (calendar-and-cycle stress-factor model + LSTM), Gasper (learned algebraic stress laws) and the dataset
authors' own calendar + cycle superposition model.

**Single paper most likely to be cited against us: PiDDM** (Chen et al., arXiv 2607.29095, 2026-07-31; read FT-partial
in the 01 audit): an Arrhenius/throughput rate law with network-produced parameters, integrated, negative by
construction. For the dataset specifically, the mandatory comparator is Stroebl et al., J. Energy Storage 142, 119552
(same data, same five stress variables, calendar + cycle superposition, fixed power-law forms).

## 1. Task 1: the Samsung 50E dataset paper

Full extraction: `ROOT/notes/papers/samsung50e_dataset_paper.md` (reading: **FT** of article, tables 3-6, SI; Figure 4
viewed). Facts that matter for the audit and for D010 section 4:

- Stroebl, Petersohn, Schricker, Schaeufl, Bohlen, Palm. Scientific Data 11, 1020 (2024-09-19). **DOI
  10.1038/s41597-024-03859-z, verified on Crossref.** Data: figshare **10.6084/m9.figshare.25975315.v1**, verified on
  DataCite and the figshare API, **CC BY 4.0**, published 2024-08-06. Groups: Munich University of Applied Sciences
  (ISES), Hoppecke (lab code INT), Siemens (SIE).
- **279 cells, 71 test points** (abstract, figshare, Crossref); the Background text of the same paper says "93
  different aging conditions" (paper-internal inconsistency). The Methods arithmetic gives 22 calendar TPs x 6 cells
  = 132 and 49 cycle TPs x 3 = 147, matching the judge's local count and the figshare listing (132 `TP_k` zips 2.04 GB,
  147 `TP_z` zips 8.25 GB).
- **Calendar cells 04-06 of each TP get only ET and AT** (no intermediate check-ups, only OCV-reset recharges). Only 66
  of 132 storage cells have a trajectory.
- **Capacity is not a table.** It is the mean of charge and discharge capacity from raw RPT steps (step_type 21/22,
  C/2 CCCV charge, 1C CCCV discharge, 23 C); relative to the ET capacity.
- **Cadence (Figure 4, read from the image):** calendar ET, then check-ups at about weeks 5 (CU), 9 (exCU), 17 (CU),
  25 (exCU), then every 8 weeks; cycling at weeks 1, 2, 3 (CU, CU, exCU), 5, 7, 9 (2-week blocks), then every 4 weeks.
  So the first three post-ET check-ups of a storage cell lie at about weeks 5, 9 and 17; of a cycling cell at weeks 1, 2, 3.
- CU = capacity + HPPC at 50 % SOC at 23 C (~15 h); exCU = capacity + HPPC at several SOCs at 23 C, no pOCV (~30 h);
  ET/AT = everything at 10, 45, 23 C (~220/200 h).
- Cell surface temperature (`c_surf_temp`) is logged in all files.
- Stage 1 storage above 80 % SOC showed non-monotonic capacity behaviour "not captured by the model"; stage 2 was
  limited to <= 80 % SOC. Stage 2 used a **new cell batch**. AT at 23 C is contaminated by the earlier 10 and 45 C tests.
- **Models fitted by the authors:** one semi-empirical model only (SI S.1.1; Muehlbauer et al., J. Energy Storage 48,
  103803, 2022, doi 10.1016/j.est.2021.103803, Crossref verified): Q_loss,rel = Q_cal + Q_cyc, linear superposition of
  independent calendar (T, SOC, t; 3 parameters, Arrhenius x power law) and cycle (T, SOC_max, C_ch, C_dch, DoD, FEC;
  6 parameters, Arrhenius x power laws) terms. No neural, PINN or KAN model in the data paper.
- Follow-up by the same group: Stroebl, Schaeufl, Bohlen, Palm, J. Energy Storage 142, 119552 (issued 2026), doi
  10.1016/j.est.2025.119552 (Crossref verified; **AB**): pi-OED cuts temperature-parameter uncertainty of the calendar
  model by 28 %; for the cycle model "pi-OED cannot reduce the parameter uncertainty ... explained by its inadequacy"
  (predicted sensitivity not confirmed by experiments). Related: Stroebl et al., IEEE Access 12, 120440 (2024), doi
  10.1109/ACCESS.2024.3446234 (Crossref verified; title only).

## 2. Task 2: works that model or predict ageing on this dataset

Method: OpenAlex `cites:W4402645230` (the data paper; cited_by_count 35, 40 records returned, all 40 screened by title and
source; abstracts read or fetched for 14), plus WebSearch/OpenAlex queries on the data title and cell name, plus figshare
mirror search. Result table (all DOIs resolved on Crossref unless marked):

| Work | Uses the Stroebl data? | What it does | Neural / PINN / KAN? | Depth |
|---|---|---|---|---|
| Stroebl et al. JES 142, 119552 | yes (279 cells, 71 conditions) | OED for the semi-empirical calendar + cycle model; cycle model found inadequate | no | AB |
| Zhong and Rogge, SSRN 7589132 (doi 10.2139/ssrn.7589132, Crossref verified); Zenodo evidence layer (v1.4.0, doi 10.5281/zenodo.23309134 per the record page) | listed ("Stroebl" archive among ten public archives, 637 cells) | preregistered test of a "reversible history state" and a cycling-adjacency penalty read from ordinary check-ups; claims transfer of lifetime models between test schedules | not stated; derived tables only, files restricted | META plus WebFetch of the Zenodo page (abstract-level) |
| Hallinger, Kirst, Singer, Bohlen, SSRN 7417281 (doi verified) | cites the data paper (Bohlen is a data-paper author) | mechanistic calendar-ageing parameterisation with a priori identifiability | not stated | title only (SSRN 403) |
| Gama et al., INDUSCON 2025 (doi 10.1109/induscon66435.2025.11241678, Crossref verified) | cites it | enhanced semi-empirical calendar + cycle model with asymmetric-Gaussian SOC stress factor and two-exponential DoD factor; calibrated on "digitized experimental data" | no | AB |
| Li et al., Applied Energy 389, 125703 (2025), doi 10.1016/j.apenergy.2025.125703 | cites it (dataset use not shown) | empirical capacity-fade model whose parameters are estimated by an ML model from early-life features, end-to-end; <2 % MAE in-distribution, <4 % out-of-distribution | ML, not PINN/KAN | AB (publisher page via Penn State pure) |
| Zhang et al., J. Energy Storage 182, 125097 (2026), doi 10.1016/j.est.2026.125097 | cites it | "physics-informed learning of health-aware ECM parameter evolution" | PI learning, ECM | title only |
| Qaadan et al., IEEE Access 13 (2025), doi 10.1109/ACCESS.2025.3556314 | **no**: uses "Samsung INR21700-50E" from the group's own Data in Brief set (256 cells, 32 batches, 25 C, C/2-C/5; read via Europe PMC), not the Stroebl data | CPIHL, a causal physics-informed hybrid network for health forecasting | PINN-like; same cell type, **different dataset** | AB (IEEE paper), DIB data description FT-partial |
| Ponce-Alcantara et al., Sci. Data 2026, doi 10.1038/s41597-026-08369-8 | **no** (160 other 50E cells, room temperature, diagnostic protocols) | dataset descriptor | no | AB |
| Others among the 40 citing records | cite as a dataset in reviews (Madani; Kampker; Nyachionjeka; Tu; Vega-Garita; Kostenko), in SOH-estimation or other-topic papers | no ageing model on this data identified | no | titles |

**Finding.** No paper applying a neural, physics-informed, UDE, PINN or KAN model to the Stroebl et al. data was found. The
only models fitted to it that I could identify are the authors' own parametric semi-empirical models (and Gama et al.'s
variant calibrated on digitised data) and Zhong and Rogge's archive-level analysis. Caution: "Samsung INR21700-50E" is also the
cell of two other public datasets (Qaadan et al. 2025; Ponce-Alcantara et al. 2026), so title-level searches for "Samsung
50E + PINN" return papers on those sets; a reviewer or editor may conflate them. Residual risk: citation lists lag; a
2026 preprint using the data without citing the data paper is invisible to `cites:`; the repository
`fst2112/Multi-Stage-Lithium-Ion-Battery-Aging-Dataset-Analysis` exists (GitHub API) but its contents were not read.

## 3. Task 2b: coupled calendar + cycle ageing in one learned model since 2020

Query log (OpenAlex `search=` unless noted; filter from 2019-06; plus WebSearch): "physics-informed neural network
calendar and cyclic aging lithium-ion capacity fade operating conditions"; "hybrid neural network semi-empirical
calendar aging cyclic aging unseen operating conditions"; "neural network learns stress factors temperature SOC DoD
C-rate ageing" (timed out once, covered by WebSearch); "Kuzhiyil universal differential equations"; "Gasper Smith symbolic
regression calendar cycle"; "Naumann Jossen calendar cycle semi-empirical LFP"; "Kolmogorov-Arnold physics-informed
lithium-ion degradation ODE"; "Sandia battery archive neural ODE"; "degradation rate law learned neural Arrhenius
calendar cycle"; "mixed calendar and cycling model dynamic load neural network"; "Kiefer lithium-ion ageing"; "Schmitt
Jossen aging neural network"; "interpretable neural additive battery capacity fade"; "neural ODE calendar aging storage
SOC"; "Bayesian hierarchical semi-empirical"; "Gaussian process mixed storage and cycling held-out"; "physics-informed ML
held-out operating conditions Arrhenius throughput"; arXiv API (date-sorted) on Kolmogorov-Arnold + battery, INR21700,
Stroebl, calendar + cycling + physics-informed, scientific ML battery; WebSearch on PINN calendar/cycle stress
functions, Kiefer/Jossen, Kuzhiyil, Wildfeuer/Lienkamp GP hybrid, KAN capacity fade C-rate/DoD, Stroebl + ML, KAN/PINN
+ figshare 25975315. About 150 titles screened; abstracts read for about 30; full text read for four (below).

**Not found:** works by "Kiefer" (2024/2025) and "Schmitt" on coupled neural ageing models could not be identified by any
query (OpenAlex returned nothing for the Kiefer query; the Schmitt query returned unrelated items). They may exist under
titles my queries did not match; I cannot confirm or exclude them. The Warwick/Kuzhiyil, NREL/Gasper-Smith, and
TUM-Jossen strands were found and are in the matrix below.

### Difference matrix (S = same, P = partial, D = different; relative to the revised claim)

Columns: question (forecast unseen conditions from early data) / mechanism (calendar + cycle in one law, stress
functions) / method (PINN or UDE with learned stress functions, KAN) / evidence (joint storage + cycling DoE data) / scale
/ result.

| # | Work (depth) | Question | Mechanism | Method | Evidence | Scale | Result |
|---|---|---|---|---|---|---|---|
| 1 | PiDDM, Chen et al., arXiv 2607.29095 (FT-partial, 01 audit) | P (extrapolates to last 10 % of own trajectory; no early-window forecast) | P (Arrhenius SEI term + throughput/DoD term, summed; no storage arm) | P (MLP gives kinetic parameters, integrated law; no KAN, not a PINN residual) | D (XJTU 55 cells, 6 protocols) | D | not comparable |
| 2 | Stroebl et al. JES 142, 119552 (AB) + data paper SI (FT) | D (calibration and OED, not forecasting) | S (calendar + cycle superposition with the same five stress variables) | D (parametric power-law, no learning) | S (same data) | S | cycle model deemed inadequate (abstract) |
| 3 | Shi, Rivera, Wu, Mech. Syst. Signal Process. 179, 109347 (2022), doi 10.1016/j.ymssp.2022.109347 (FT-partial: abstract, Sections 1, 3.1-3.2, data section; grep of Section 3-4) | P (RUL under different operating conditions; coefficients fitted on one cell of the same dataset) | S (physics-based calendar + cycle aging model with five operating stress factors, summed per cycle) | D (stress factors are fixed parametric forms; an LSTM layer learns the non-linear stage; no KAN) | D (NASA PCoE; eleven cells) | D | high accuracy on eleven cells |
| 4 | Kuzhiyil, Damoulas, Planella, Widanage, Applied Energy 382, 125221 (2025), doi 10.1016/j.apenergy.2024.125221 (AB, Crossref verified) | P | P (neural network inside physics-based state equations; calendar ageing only) | S in spirit (UDE) | D (calendar storage, LG M50, 39 storage conditions, WMG data) | D | not extracted |
| 5 | Gasper et al. JES 168, 020502 (2021), doi 10.1149/1945-7111/abdde1 (AB; **calendar-ageing only**, LFP/graphite) and JES 169 (2022), doi 10.1149/1945-7111/ac86a8 (AB; **cycling**, validated by converting to a state equation and testing on varying loads) | P | P (two papers, one per mode, none joint) | D (bi-level symbolic regression; interpretable algebraic laws, bootstrap UQ) | D (LFP/graphite) | D | 2022: about half the MAE of an expert model |
| 6 | Li et al., Applied Energy 389, 125703 (2025) (AB) with the ISU paper (FT, below) | S (early-life features to full trajectory, in- and out-of-distribution) | P (empirical fade model with ML-estimated parameters; cycling only as far as the abstract shows) | D (not PINN/KAN) | D | D | <2 % in-distribution, <4 % OOD MAE |
| 7 | Wang et al., Nat. Commun. 15, 4332 (2024), doi 10.1038/s41467-024-48779-z (FT-partial: model section and grep) | D (SOH estimation from charge features of the same cycle) | D (the general degradation form dF/dt with a stress vector x is introduced in the text, but x = health indicators from charging data; no calendar term) | P (PINN, F/G structure) | D (55 NCM cells) | D | not comparable |
| 8 | Zhong and Rogge, SSRN 7589132 (META plus Zenodo page) | P (transfer between test schedules) | P (history state, cycling-adjacency penalty) | not stated | P (Stroebl data among ten archives) | P | preregistered archive-level tests |

What each does and does not do relative to the claim:
1. **PiDDM:** the closest model; it lacks a calendar/storage arm and any joint-trained storage + cycling design, has no KAN,
   no early-window forecast of an unseen condition, no identifiability test (01 audit).
2. **Stroebl/Muehlbauer:** the only on-dataset calendar + cycle model; fixed forms; no learning, no forecast protocol from
   check-ups; its stated inadequacy of the cycle part is a published statement about this data a reviewer will quote.
3. **Shi et al.:** the coupling idea (calendar + cycle stress factors summed) is public since 2022; learned part is an LSTM, not
   the stress functions; tiny NASA cell set.
4. **Kuzhiyil et al.:** "known state equation + learned part" is public for calendar ageing; no cycling, no KAN.
5. **Gasper et al.:** learned (symbolic) stress laws per mode, validated in state-equation form; no neural joint model, no
   forecasting from early check-ups. Correction to 01_novelty_audit: Gasper 2021 is calendar-only; the cycling paper and the
   state-equation validation are the 2022 JES paper.
6. **Li et al. 2025:** early prediction of the whole trajectory with an empirical fade model and ML parameters; closest on the
   "first check-ups" task formulation.

**Not found (specific questions asked):**
- A KAN (or PIKAN) used on the Samsung 50E data of Stroebl et al.: **not found.** (KAN battery works found: SOH-KLSTM,
  Hybrid Transformer-KAN, PGKAN/PIKAN/PI-EKAN SOH estimation, Ghosh and Roy KAN relation discovery on one eVTOL cell,
  Wang et al. RESS 2025 KAN neural ODE for solid-state RUL; none on this data.)
- A PINN on that data: **not found.**
- Coupling calendar + cycle ageing with **KAN** stress functions: **not found.** Among KAN papers, none has a calendar term.
- A learned-stress-function calendar + cycle ageing model trained jointly on storage and cycling cells that forecasts
  held-out conditions from early check-ups: **not found** (nearest: items 3, 4, 6).

## 4. ISU arXiv 2307.08382 re-read (FT: main text of arXiv v2 HTML, abstract to Section 3.9; supplement not read)

Li, Zhou, Thelen, Howey, Hu. "Predicting Battery Lifetime Under Varying Usage Conditions from Early Aging Data." arXiv
2307.08382v2 (2023-10-20); published as Cell Reports Physical Science 5 (2024), **doi 10.1016/j.xcrp.2024.101891 (Crossref
verified)**. Dataset DOI 10.25380/iastate.22582234 ("ISU and ILCC NMC/Gr dataset").
- **Data:** 225 NMC/graphite 502030-size Li-polymer cells (Honghaosheng) in groups of four per condition, cycled over C_ch,
  C_dch (0.5 to 3C) and DoD (4 to 100 %, measured DoD used); weekly RPTs (two cycles at C/2 and C/5); 1 week cycling then
  an RPT, until 80 % of rated capacity. Lifetimes 1.5 to 60.9 weeks. No calendar-ageing arm. Temperature is controlled in a
  chamber (the HTML dropped the number; the judge's 30 C is not confirmed by my text). Note: the arXiv text says 225 cells;
  the judge's count of 63 conditions x 4 replicates is a larger figure (the released dataset may have been extended; not
  checked against the figshare README).
- **Task and metric:** early prediction of cell **lifetime (EOL, weeks)** from RPT features of weeks 0 and 3 (just under 18 %
  of mean lifetime); metrics **MAPE and RMSE (weeks)** on the lifetime, not on trajectory points.
- **Models:** elastic net on features from incremental-capacity curves (a window feature, change in CV hold time, DoD,
  stress feature sqrt(C_ch x DoD)-type); hierarchical Bayesian linear model with condition-level clustering (4 clusters by
  average stress). No physics law, no neural network.
- **Splits:** **group-level** (condition) split. Train: high-DoD region (116 cells); in-distribution test: high-DoD held-out
  groups (60 cells); out-of-distribution test: all low-DoD (< 40 %) groups (49 cells).
- **Numbers (Table 2):** dummy 31.5 / 47.5 % MAPE (high / low DoD); conditions-only model 19.0 / 23.7 %; degradation-informed
  elastic net (2 features) 16.0 / 24.4 % (3 features 15.1 / 33.0 %); HBM (2 features) 16.9 / 21.8 % MAPE, RMSE 3.1 / 7.3
  weeks. Note the conditions-only baseline is competitive with the 2-feature elastic net on low-DoD MAPE (23.7 vs 24.4 %).
- Consequence for D010: the ISU EOL MAPE to be reported alongside ours is **lifetime MAPE in weeks-based EOL**, not
  retention RMSE; the ISU authors' method requires the full-life training data and early features from the first 3 weeks.

## 5. Other checks

- OpenAlex: PIKAN and PGKAN citation lists not re-run (01 audit holds). PiDDM, JECS addd4e (doi
  10.1149/1945-7111/addd4e), PIKAN/PGKAN full texts remain **unread by me** (the judge asked for them; not part of this
  brief's task list; still outstanding).
- **arXiv 2607.16864** (Guo, Vilsen, Stroe, Li, Huang, Verma, Brandell; submitted 2026-07-18; title "Bridging battery
  design and health assessment through virtual sensing and physics-informed learning"; arXiv abs page read, **AB**): particle-
  cracking soft constraint plus virtual sensing of design parameters; fast-charging and driving profiles; 2 % early-life data;
  abstract does not mention calendar ageing or a stress-function law. The 01 audit's description stands; full text not read.
- arXiv 2410.14347 (Murgai et al., UDE/NeuralODE for EV battery degradation; AB): abstract names no dataset and does not say
  whether calendar and cycle are separated; unresolved.
- Last 90 days (since about 2026-08-06): items found in range are Zhong and Rogge (SSRN/Zenodo, Oct 2026), Prakash et al. (J.
  Power Sources, cost-aware BOED, not ageing model), the ISU-related Chen et al. SSRN version of PiDDM, Eltamaly and Almutairi
  (Sci. Rep. 2026, LSTM with Arrhenius/Wohler physics loss, cross-chemistry SOH; not calendar + cycle stress learning).
  Nothing found in range that fits the claim. OpenReview not searched.

## 6. Residual risk (state of the evidence)
- Exa and OpenReview unavailable; no ICLR 2027 / NeurIPS 2026 check. A concurrent submission would be invisible.
- Six of the eight matrix rows rest on abstracts or partial text (rows 2, 4, 5, 6, 8, plus Hallinger and Zhang JES 125097
  unread). The two works that could weaken the verdict if their full text shows a joint neural calendar + cycle model on this
  data are **Zhang et al., J. Energy Storage 182, 125097** (cites the data paper; abstract unavailable) and **Hallinger et al.
  SSRN 7417281** (Bohlen is a data-paper author; likely mechanistic calendar only).
- "Kiefer 2024/2025" and "Schmitt" from the brief could not be located; unresolved, not excluded.
- Absence of a KAN or PINN paper on the Stroebl data is weak evidence: the data are 14 months old, the OpenAlex citation list
  has 35 to 40 records and lags mid-2026.
- The Samsung 50E label is shared by three public datasets; a reviewer may conflate them or claim a prior PINN on "Samsung
  50E" (Qaadan et al., IEEE Access 2025, which uses a different data set at 25 C).

## 7. Reading ledger (depth per work)
FT: Stroebl et al. 2024 (article, tables, SI); Li et al. ISU arXiv 2307.08382 (main text); Qaadan et al. Data in Brief (data
description, via Europe PMC, FT-partial). FT-partial: Shi, Rivera, Wu 2022; Wang et al. Nat. Commun. 2024; PiDDM (01 audit).
AB: Stroebl JES 2026; Li et al. Applied Energy 2025; Kuzhiyil 2025; Gasper 2021, 2022; Gama et al.; Qaadan IEEE Access;
Zhong and Rogge (Zenodo page); Ponce-Alcantara 2026; arXiv 2607.16864; arXiv 2410.14347. META: Hallinger SSRN; Zhang JES
125097. Files saved under `ROOT/refs/` (samsung50e_paper, isu_2307_08382, nsf_cca, wang_natcomm2024, qaadan_dib).
