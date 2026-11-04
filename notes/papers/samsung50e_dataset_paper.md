# Stroebl et al. 2024: Samsung INR21700-50E multi-stage ageing dataset (extraction note)

Written 2026-11-04 by the novelty auditor (D010 re-audit). Template: CONTRACT section 4.

## Citation
- Florian Stroebl, Ronny Petersohn, Barbara Schricker, Florian Schaeufl, Oliver Bohlen, Herbert Palm.
  "A multi-stage lithium-ion battery aging dataset using various experimental design methodologies."
  Scientific Data 11, article 1020 (published 2024-09-19).
- DOI **10.1038/s41597-024-03859-z** (verified on Crossref: title, six authors, date, volume 11, article 1020,
  licence CC BY 4.0).
- Dataset: "Multi-Stage Lithium Ion Battery Aging Study", figshare, DOI **10.6084/m9.figshare.25975315.v1**
  (verified on DataCite and the figshare API: same six creators, 2024, version 1, licence CC BY 4.0,
  published 2024-08-06, last modified 2024-09-19).
- Groups: Institute for Sustainable Energy Systems (ISES), Munich University of Applied Sciences (HM, lead);
  Hoppecke Systemtechnik (Zwickau; the lab is coded INT = Intilion); Siemens AG Technology (Erlangen; SIE). Germany.
- Note: the paper's reference list entry for "Raj 2020, Path dependent battery degradation dataset part 1" prints
  the figshare DOI 10.6084/m9.figshare.25975315 (a reference-list slip in the paper); the dataset's own entry
  (ref. 92, Stroebl et al. 2024) is the correct one.

## Reading depth
**Full text** of the article (nature.com HTML, converted to text locally: Background, Methods, Data Records,
Technical Validation, Usage Notes, Code availability; Tables 3, 4, 5, 6 read from the article's table pages;
Figure 4 (check-up schedule) viewed as an image) and **full text of the Supplementary PDF** (3 pages, section
S.1.1 semi-empirical models; some Greek symbols are garbled by conversion, the structure is clear).
Files: `ROOT/refs/samsung50e_paper/` (paper.html, paper.txt, si.pdf, si.md, t3-t6.html, fig4.png).
Not read: the authors' related IEEE Access 2024 paper (doi 10.1109/ACCESS.2024.3446234, Crossref verified) and
the JES 2026 follow-up (doi 10.1016/j.est.2025.119552; abstract only, via OpenAlex).

## Problem and stated contribution
Public ageing datasets rarely use optimised experimental design. The authors run a two-stage campaign on one
commercial cell type with calendar and cycle ageing in the same design, to quantify what model-based optimal
experimental design (parameter-individual OED, pi-OED) gains over full-factorial and conditioned-Latin-hypercube
sampling when calibrating a semi-empirical ageing model. They also offer the data for ML lifetime models and for
calibrating physics-based or (semi-)empirical models. Reference performance tests (RPTs) were given varying scope
to limit their own ageing influence, and test points with and without regular RPTs quantify the RPT impact.

## Data
- Cell: Samsung INR21700-50E, 4.9 Ah rated, max charge 1C (4.9 A), max discharge 2C (9.8 A). The cathode/anode
  chemistry is not stated in the text read, so it is not asserted here (the paper cites the manufacturer sheet, ref. 86).
- **279 cells, 71 test points (TPs) in two stages** (abstract, figshare description, Crossref; the Springer
  Background text says "93 different aging conditions", an internal inconsistency in the paper; the Methods
  arithmetic gives 71):
  - Calendar TPs: stage 1 = 11 (full-factorial motivated); stage 2 = 4 pi-OED + 7 non-model-based (3 manual grid
    fills + 4 exploratory) = 11; total **22 TPs x 6 cells = 132 cells**.
  - Cycle TPs: stage 1 = 25 (conditioned Latin hypercube); stage 2 = 12 pi-OED + 12 cLH = 24; total **49 TPs x 3
    cells = 147 cells**.
  - The figshare file listing matches: 132 `TP_k*` zips (2.04 GB), 147 `TP_z*` zips (8.25 GB), one
    `experiments_meta.csv`; total 280 files. The lead's count of 19 + 40 unique conditions (judge) is consistent:
    22 and 49 TPs include repeated centre points across stages.
- Conditions: ambient temperature limited to 10, 23, 35, 45 C (chamber availability); cycling at 23, 35, 45 C
  only. SOC_max and DoD kept inside 20-80 % SOC during cycling (to avoid CV phases). C_ch in [0.05, 1], C_dch in
  [0.05, 2]. Storage: open-loop at 5-100 % SOC (set by CCCV charge); stage 2 restricted SOC_max to <= 80 %
  because stage 1 showed **non-monotonic behaviour above 80 %** that the authors' model did not capture.
- **Calendar cells 04-06 of every calendar TP receive only the initial (ET) and final (AT) check-up**; they are
  recharged to their reference OCV periodically without characterisation. Only calendar cells 01-03 (66 cells)
  have intermediate check-ups. Cycling cells: all 3 have regular check-ups.
- Labs: three (SIE, INT, HM), identical protocol; BaSyTec testers, Binder/ATT chambers. Cell-to-cell
  comparability: DVA curve of every initial RPT vs the mean, R^2 > 0.99 for all cells (single-batch claim).
- Measured per file: run_time, c_vol, c_cur (negative on discharge), c_surf_temp (cell surface NTC, so cell
  temperature IS logged), amb_temp, step_type (Table 5). Per-cell `*_meta.txt`; `experiments_meta.csv` columns:
  serial, lab, type (k/z), tp, cell, amb_temp_tp, soc_max_tp, dod_tp, c_ch_tp, c_dch_tp, sampling, stage, m_0,
  R_1khz_0, U_0 (Table 4).
- File types: ET, exCU, CU, AT (RPT files) and ZYK (cycling). **No files exist for calendar storage periods** (open
  circuit). All CSV inside per-cell zips; ~10 GB compressed, ~100 GB uncompressed.
- **Capacity is not provided as a table.** It must be computed from the raw RPT time series: step_type 21/22 =
  capacity measurement (CCCV charge at C/2 to 4.2 V with C/20 cut-off; discharge at **1C** to 2.5 V with C/20
  cut-off); the paper defines capacity as the **mean of charge and discharge capacity** from the RPT; relative
  capacity Q_rel = Q_i / Q_0 with Q_0 from the initial RPT (ET). DCIR from a 1C, 10 s discharge pulse at 50 % SOC.
- Label definition used by the authors: Q_rel above an end-of-life criterion (EOLC) in the semi-empirical model.

## Check-up (CU) and extended check-up (exCU)
Three RPT types (Methods, Table 3):

| RPT | Ambient T of the test | Contents | Duration |
|---|---|---|---|
| ET (initial) / AT (final) | 10, 45, 23 C | capacity (A), pOCV at C/20 (B), HPPC at 5-40 % (C), 50 % (D), 60-95 % (E) SOC | ~220 h / ~200 h |
| exCU | 23 C | capacity, HPPC at multiple SOCs (no pOCV) | ~30 h |
| CU | 23 C | capacity and HPPC at 50 % SOC only | ~15 h |

Three full break-in cycles at 23 C precede ET. The authors warn that the AT capacity at 23 C may deviate from the
trend because the earlier 10 C and 45 C tests in ET/AT put extra stress on the cells.

## Check-up cadence (Figure 4, read from the image; weeks are test weeks)
- Calendar (panel a): ET, 5 W, CU, 4 W, exCU, 8 W, CU, 8 W, exCU, ... then AT. Check-ups therefore fall at about
  weeks 5 (CU), 9 (exCU), 17 (CU), 25 (exCU), then every 8 W alternating CU/exCU, about 7 intermediate points in a
  year.
- Cycling (panel b): ET, 1 W, CU, 1 W, CU, 1 W, exCU (weeks 1, 2, 3), then 2 W blocks (CU at 5, CU at 7, exCU at 9),
  then 4 W blocks (CU 13, CU 17, exCU 21, CU 25, ...) then AT; about 15-17 intermediate points in a year.
- Cycling cells that sat through chamber downtime or lab outages have paused intervals (list in Technical
  Validation; e.g. stage 2 TP_z[13-17,19,20,22,23,24] were paused 15 days before one check-up and 20 days
  before another; several 4-day or 2-day logging gaps).

## Model (what the authors fit)
Supplementary S.1.1: **semi-empirical, linear superposition** of independent calendar and cycle loss, motivated
by Muehlbauer et al. (J. Energy Storage 48, 103803, 2022; DOI verified on Crossref):
- Q_loss,rel = Q_cal + Q_cyc, each scaled by (1 - EOLC).
- Q_cal(T, SOC, t) = (1 - EOLC) * [ exp(-theta0 (1/T - 1/Tref)) * (SOC/SOCref)^theta1 * (t/tref) ]^(1/theta2)
  style form with 3 parameters (theta0..theta2; the exact placement of exponents is garbled in the conversion).
- Q_cyc(T, SOC_max, C_ch, C_dch, DoD, FEC) = (1 - EOLC) * [ exp(-theta0 (1/T - 1/Tref)) * (SOCmax/ref)^theta1 *
  (C_ch/ref)^theta2 * (C_dch/ref)^theta3 * (DoD/ref)^theta4 * (FEC/FECref) ]^(1/theta5)-type power-law form with 6
  parameters.
- Parameter-individual OED (Palm, Stroebl, Palm, IEEE Access 10, 112515, 2022, doi 10.1109/ACCESS.2022.3216364,
  Crossref verified) chooses 4 calendar and 12 cycle test points to sharpen temperature-related (calendar) and
  current-rate-related (cycle) parameters.
The data paper reports no machine-learning, neural, PINN or KAN model. Their JES follow-up (abstract only; DOI
10.1016/j.est.2025.119552, Crossref: J. Energy Storage 142, 119552, issue date 2026) reports pi-OED cuts the
temperature parameter uncertainty of the calendar model by 28 % but cannot reduce the cycle-parameter
uncertainty, "explained by its inadequacy" (the predicted sensitivity of the heuristic cycle model was not
confirmed by experiments).

## Tuning
Not applicable (no learned model). Parameter calibration by the OED/least-squares route is in the JES paper (not
read in full).

## Evaluation
Technical Validation is descriptive: DVA comparability (R^2 > 0.99), voltage curves vs capacity (Fig. 7),
capacity and DCIR trajectories for all cells (Fig. 8 over time and fully equivalent cycles, Fig. 9 relative).
"Sublinear and some superlinear and knee-shaped trends for capacity decay, mainly linear DCIR rise." No
forecasting benchmark or metric is given in the data paper.

## Figures (data paper)
1 test setup schematic; 2 ageing-protocol time series; 3 RPT protocol (sections A-E); 4 check-up schedules
(calendar and cycle, in weeks); 5 calendar DoE (SOC vs T, stage and sampling method as markers); 6 cycle DoE
scatter-matrix (T, SOC_max, DoD, C_ch, C_dch); 7 discharge-curve families; 8 and 9 trajectories of all cells
(absolute and relative capacity and DCIR, per stage).

## Ablations
None (dataset paper). Stage 2 contains matched pi-OED vs non-model-based test points for comparing designs.

## Hidden assumptions
- Single batch (DVA R^2 > 0.99) so cell-to-cell scatter is small; labs treated as exchangeable.
- Capacity measured at 23 C, 1C discharge; cells are comparable across three laboratories and 2 stages (new cell
  batch in stage 2: "A new batch of battery cells was tested during stage 2", so stage is a batch effect).
- RPT stress is negligible or quantified by the no-RPT calendar cells (04-06), which have no intermediate data.

## Weaknesses a reviewer would hit (for users of the data)
- Paper-internal inconsistency in condition count (71 vs 93).
- Capacity must be derived from raw RPT steps; no official capacity table; known corrupted/malfunction files
  listed in Technical Validation must be dropped.
- Sparse storage check-ups (about 7 in a year, first at about 5 weeks; calendar cells 04-06 have none).
- Stage 1 vs stage 2 are different cell batches; storage at 100 % SOC (stage 1 only) shows non-monotonic
  trends; AT value contaminated by the 10 C / 45 C tests.
- Cycling within 20-80 % SOC only; no high-SOC cycling; temperatures 10 C only in storage and RPTs.

## Gaps and hooks for our paper (facts that bear on D010; no proposal made here)
- Cell surface temperature is logged during cycling (c_surf_temp), so self-heating can be checked.
- The authors' own model is a power-law superposition with fixed functional forms; the JES follow-up states the
  cycle part is inadequate. A learned stress map is therefore a different object from the authors' model; the
  authors' model is the natural parametric baseline (their Eq. S.1-S.3).
- Test-point numbering: TP_k01..., TP_z01... per stage; replicate cells 01-03 (and 04-06 for calendar).

## Code/data availability
- Data: figshare doi 10.6084/m9.figshare.25975315 (CC BY 4.0), 280 files, ~10.3 GB.
- Code: github.com/fst2112/Multi-Stage-Lithium-Ion-Battery-Aging-Dataset-Analysis (repo exists per the GitHub
  API; contents not read): Python processing functions and a Jupyter notebook. "No custom code was used to
  generate the dataset."
- A Hugging Face raw mirror (bsebench-org/imperial-multistage-aging-2024-raw) exists; it states "pending
  validation" and makes no benchmark claim.
