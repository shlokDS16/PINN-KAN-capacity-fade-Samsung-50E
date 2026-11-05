# Saxena, Hendricks, Pecht (2016): partial-SOC cycle-life study on graphite/LiCoO2 pouch cells (CALCE PL set)

File: `notes/papers/saxena2016_jps_calce_pl.md`. Written 2026-11-05 by the data steward for decision D022 (action A5).
Source file: `refs/pdf/saxena2016_jps_calce_pl.pdf` (1,274,288 bytes, saved by Shlok through the VIT library). Text converted
with markitdown to a temporary file; figures are images and were not read as numbers. Page references are the journal pages
394-400.

## Citation
S. Saxena, C. Hendricks, M. Pecht, "Cycle life testing and modeling of graphite/LiCoO2 cells under different state of charge
ranges", Journal of Power Sources 327 (2016) 394-400. DOI 10.1016/j.jpowsour.2016.07.057 (verified on Crossref 2026-11-05:
vol. 327, pp. 394-400, September 2016, authors Saxena, Hendricks, Pecht). Group: Center for Advanced Life Cycle
Engineering (CALCE), University of Maryland, College Park, USA. Received 1 April 2016, accepted 16 July 2016.

## Reading depth
**Full text** (all of pp. 394-400, tables 1 and 2 as text, equations, references list). Figures 1-6 are plots; only their
captions and the surrounding text were used. The CALCE data files themselves were not read beyond the operation table (no
capacity array).

## Problem and stated contribution
Partial charge-discharge cycling is the usual practice, but extensive long-term data on SOC range (mean SOC and change in SOC,
DSOC) for graphite/LiCoO2 cells were missing (Introduction, p. 395). The paper cycles pouch cells over five SOC windows and two
discharge rates and fits a power-law capacity-fade model with a mean-SOC and DSOC dependence (Section 4, p. 398-399). Claims:
mean SOC, DSOC and discharge rate all significantly affect the capacity-loss rate; mean SOC dominates the first 500 equivalent
full cycles, DSOC matters more later (Conclusions, p. 399).

## Data
- **Cell:** commercial graphite/LiCoO2 **pouch** cell, nominal 1.5 Ah (at C/5), nominal 3.7 V; manufacturer specifies
  end-of-charge 4.2 V and end-of-discharge 2.75 V (Section 2, p. 395). Manufacturer not named. (Dimensions 3.4 x 84.4 x 50.1 mm
  are from the CALCE data page, not the paper.) Note an inconsistency: the initial characterisation is described as a 4.2-2.7 V
  cycle, the limits as 2.75 V.
- **Test equipment:** Arbin BT2000, 16 independent channels (p. 395).
- **Temperature:** all tests in a "semi-temperature controlled room" at **25 +/- 2 C** (p. 395). Cell temperature rise: at C/2
  discharge the cells never exceeded ambient by more than 6 C; the same holds for 2C discharge between 40 and 60 % SOC; for 2C at
  **20-80 % and 0-100 % the rise exceeded ambient by more than 15 C** (p. 396). The paper concludes that the constant-temperature
  assumption fails for those 2C cells and excludes them from the model (p. 398).
- **Test matrix (Table 1, p. 396; also Table 2, p. 399):** five SOC ranges. Cells per condition: **2** in every cell of the matrix.

| SOC range | mean SOC | DSOC | C/2 discharge | 2C discharge |
|---|---|---|---|---|
| 0-100 % | 50 % | 100 % | 2 cells | 2 cells |
| 20-80 % | 50 % | 60 % | 2 | 2 |
| 40-60 % | 50 % | 20 % | 2 | 2 |
| 40-100 % | 70 % | 60 % | 2 | not tested |
| 0-60 % | 30 % | 60 % | 2 | not tested |

  Eight combinations of window and discharge rate, 16 cells. The 2C arm is stated to exist "for the SOC ranges with mean SOC of
  50 %" to see whether the relative ranking depends on rate (p. 395). Charge is always C/2 (0.75 A); discharge C/2 = 0.75 A or
  2C = 3 A (p. 395-396). This matches the CALCE page list (PL3/10, PL4/5, PL9/25, PL11/13, PL12/14, PL17/18, PL19/24, PL21/23).
- **SOC-window control:** Coulomb counting (Eq. 1). The discharge capacity Q in Eq. 1 is the "true" capacity measured at the
  latest check-up; the windows are therefore specified in **Ah of the current usable capacity**, not in fixed voltages
  (example: 20-80 % of a fresh 1.5 Ah cell = 0.3 to 1.2 Ah, 0.9 Ah used; the window shrinks as the cell fades, p. 396).
  First discharge from 100 % goes to the lower limit at C/2. For the 20-80 % range the C/2 charge can hit 4.2 V before 80 %
  SOC, in which case charging stops and the upper limit is slightly low; the paper says this does not occur for the other
  ranges (p. 396). The 40-100 % and 0-100 % ranges use CCCV charge; a cell reaching 2.75 V is taken as 0 % SOC.
- **Rest:** 30 min after every charge step and every discharge step (p. 396). Rest periods were sometimes longer "due to
  non-availability of testing equipment" (p. 397, on Fig. 4a).
- **Check-up cadence and capacity measurement:** after **every 50 or 100 partial cycles** a full cycle (CCCV charge, CC
  discharge) at C/2 between 2.75 V and 4.2 V gives the true discharge capacity (p. 395). Capacity is therefore measured at a
  fixed reference condition (C/2, 25 C ambient, full range), not at the cycling condition. Normalised discharge capacity =
  discharge capacity divided by the first-cycle capacity, in percent (p. 396).
- **Cycle count:** partial-cycle counts are not well defined (also for 0-100 % at 2C), so results use **equivalent full cycles**
  (EFC): cumulative discharge Ah divided by the true capacity at each check-up, summed (p. 396). Results shown to about 800 EFC
  (about 1,000 Ah cumulative discharge) for all ranges except 40-60 %, which reaches only about 450 EFC (about 600 Ah) because
  few Ah accumulate per day; 30 min rests are why 40-60 % has fewer partial cycles than a proportional scaling would give (p. 396).
- **Anomalies reported:** (i) 0-60 % shows "unexpectedly" little fade and some normalised capacities above 100 % (initial
  kick-in and structural change at low SOC), which the paper removes before fitting (p. 397-398). (ii) The 0-100 % range at C/2
  shows a sudden increase of fade rate after about 500 EFC, read as a new mechanism (p. 397-399). (iii) Extra-long rests in
  some cells (above). (iv) Temperature rise at 2C (above). (v) Differences between 20-80 % and 0-100 % at 2C nearly vanish by
  800 EFC and are attributed to heating (p. 396, 399).
- **Data availability:** the paper does not state a repository or licence. The raw data are the CALCE "PL" files.

## Model
Power law in EFC: NDC(%) = 100 - A (EFC/100)^b (Eq. 4); b is nearly constant (0.451-0.454 across ranges, Table 2), averaged to
0.453; A as a function of mean SOC and DSOC: A = 3.25 SOC_mean (1 + 3.25 DSOC - 2.25 DSOC^2) (Eq. 5; fitted to the four ranges
other than 0-60 %), final model Eq. 6 with k1 = 3.25, k2 = 3.25, k3 = -2.25. Fitted with MATLAB's curve-fitting toolbox; fit
quality R2 0.95-0.99 for the four ranges, 0.42 for 0-60 % (Table 2). Only C/2 data and only the first 500 EFC are used; 2C
cells are excluded for temperature reasons; the 40-60 % set is short (p. 398). No physics beyond an SEI sqrt-time reading of b.
No KAN, no neural model.

## Tuning
Not applicable (curve fitting on all cells; no held-out cells, no cross-validation). The model is fitted and shown on the same
data (Fig. 6).

## Evaluation
No held-out evaluation. Results are plots of normalised capacity versus EFC, averages of two cells per condition for Figs. 2-3,
individual cells for Figs. 4-5 (p. 396-398). No statistics, no test; "significant" is used descriptively.

## Figures
Fig. 1 current and voltage profile of the 20-80 % C/2 cycling. Fig. 2 mean SOC 50 % (DSOC 100/60/20 %) at C/2 and at 2C. Fig. 3
DSOC 60 % with mean SOC 30/50/70 % at C/2. Fig. 4 and 5 individual cells for changed lower or upper SOC limits at C/2. Fig. 6
data against the fitted power law.

## Ablations
Informal, by design contrast: lower limit changed at fixed upper limit and vice versa (Figs. 4 and 5); rate 2C against C/2 for
the mean-50 ranges.

## Hidden assumptions
Constant temperature (explicitly violated at 2C for two ranges); window defined by Coulomb counting against a capacity that is
updated every 50 or 100 cycles (error between check-ups); equivalence of "equivalent full cycles" across ranges; two cells are
enough to describe a condition; cells are replicates (no cell-to-cell variance estimate).

## Weaknesses a reviewer would hit
Two cells per condition and no variance; the model is fitted and displayed on the same data; the 0-60 % condition is treated
as an outlier and dropped from the fit; the 40-60 % arm has only about 450 EFC; temperature uncontrolled at the cell at 2C;
manufacturer and exact chemistry detail absent; inconsistent end-of-discharge voltage (2.7 vs 2.75 V).

## Gaps and hooks for our paper
1. **A published baseline law for exactly this design:** a power law in EFC with an A that depends on mean SOC and DSOC. It can
   be refitted as a named external comparator on the leave-condition-out task (the arm is "a semi-empirical power-law cycle
   model", D022 judge 1.2 item 5; the Stroebl cycle term is a different model).
2. **Temperature is not constant for four cells:** the 2C cells in 20-80 % and 0-100 % ran more than 15 C above the 25 +/- 2 C
   room. The files carry **no temperature channel** (data-table variables: time, date, step, cycle, current, voltage,
   charge Ah, discharge Ah; verified on PL17 by variable names only), so the rise cannot be recovered; those four cells need a
   flag and the extension must say that temperature is not an input here.
3. **The stress coordinates are windows in Ah of the current capacity**, so SOC_mid and DSOC are nominal; the real window
   shrinks with fade and the 20-80 % cells may under-reach 80 %.
4. **Check-up capacity is at a fixed reference (C/2, 2.75-4.2 V)**, which is the property the Samsung task also has; the
   cadence (50 or 100 partial cycles) maps to a check-up axis in cycles, not days.
5. The paper's own range of validity is about 500 EFC at C/2; the sudden change in the 0-100 % arm after 500 EFC is a built-in
   hard case for any smooth forecasting law.

## Code/data availability
No code. No data statement in the paper. Data are the CALCE PL zips on `web.calce.umd.edu/batteries/data/pl/`; CALCE asks that
publications cite the CALCE articles; no licence text is given.
