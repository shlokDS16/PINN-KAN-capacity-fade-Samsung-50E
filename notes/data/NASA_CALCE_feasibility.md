# NASA and CALCE datasets: what is available and what it can support (2026-11-05)

Role: data steward. Question from the lead (supervising professor wants NASA and CALCE in the experimental
results): what exactly is on disk or reachable, and which of the Samsung tasks can each subset support?

**Reading depth.** NASA zip READMEs (9 files): full text. NASA PCoE repository page and CALCE battery-data page: the
fetched summary of the page (a small-model digest, so every number taken from them is "page digest", not a reading of the
source text); the CALCE papers named below were not read. Archive members: listed; only counts, record types,
ambient temperatures, protocol currents and cut-off voltages, and time stamps were parsed. **No capacity, SOH or fade
value was read or computed** (instruction of the lead). Statements about how far a cell faded are therefore only what the
providers' READMEs say. Scripts: `code/data_audit/nasa_calce_counts_*.py`; outputs: `data/processed/nasa_calce_feasibility/` (git-ignored; regenerate with the scripts).

## 0. Summary and recommendation

| Subset | On disk | Cells | Distinct ageing conditions | Verdict for the Samsung task (leave-condition-out forecast, cycling-only law) | Recommended role |
|---|---|---|---|---|---|
| NASA PCoE set 5 (B0005-B0056) | complete (verified) | 34 (27 with one fixed protocol, 7 with conditions that change inside the cell) | 21 nominal (T, discharge current, cut-off V) tuples among the 27 | (a) possible at reduced scale; (b) only a coarse curve; (c) yes. Only temperature, discharge current and cut-off vary: charge protocol, charge rate and (almost) the SOC window are the same in every cell | **Descriptive generalisation** of the cycling law (two informative stresses), clearly labelled previously analysed. Not a replication of the Samsung hypotheses |
| NASA randomized usage (set 11) | not downloaded (1.07 GB, listed only) | about 28 per the earlier inventory (not verified) | random-walk loads, not static conditions | (a) no: a condition is a load distribution, not a point in (T, SOC, DoD, C-rates) | **Not usable** for this paper |
| NASA HIRF (set 15) | not downloaded (1.09 GB, listed only) | not verified | aircraft test chamber, not ageing | none | **Not usable** (the NASA page marks it "currently offline") |
| CALCE CS2 / CX2 (prismatic LiCoO2) | CS2_34, 35, 36, 38 complete | 28 cells exist (16 CS2, 12 CX2); 4 on disk | static constant-current types: 0.5C and 1C (CS2), 0.5C and 3C (CX2, 3C is one cell); the rest are variable-load or temperature-ramp cells | (a) no, (b) no, (c) yes | **Within-condition early-life forecasting only**, or not used. Same cells (CS2_33-38, CX2_16, 33-38 = 13 cells) were in the retired paper |
| CALCE PL pouch (graphite/LiCoO2, SOC windows) | none of 8 zips complete (2 of 16 cells readable from partial zips, section 4) | 16 (8 window-and-rate conditions, 2 cells each) | 8, over SOC window and discharge rate | (a) feasible in design (leave-one-condition-out, 8 folds); (b) only m of 2 to 6 conditions; (c) yes | **External replication of the cycling-law forecast at small scale**, the best match of the three because SOC mid-point, depth and discharge rate vary. Not used by the author before |
| Drive `NASA-EV.zip` | complete (verified) | the same 34 NASA cells | same as NASA set 5 | same cells, CSV copy: record counts per cell equal the original | **Not a separate dataset.** Use the original `.mat` files |
| Drive `CALCE-EV_Dataset.zip` | complete (verified) | not an ageing set | none (24 single-cycle dynamic-profile tests) | none | **Not usable** (state-of-charge estimation data) |

**Prior-use statement (must go into the plan and the paper).** NASA PCoE set 5 (29 cells of the 34 after cleaning, also the
fifth target of the few-cell experiment) and CALCE CS2_33-38 plus CX2_16, 33-38 (13 cells, through the BatteryLife
processed release) were analysed in the author's retired evaluation-protocol paper (`research paper for proctor/Proctor
Research paper 2`, `progress.md` and `README.md`, corpus B: "CALCE 13", "NASA 29"). The labels of these cells have been
seen by the author, and both datasets are widely used by others. Any NASA or CALCE-CS2/CX2 result in this paper is
therefore **"previously analysed data"**, never blind, never confirmatory, and the plan must say so. The CALCE PL pouch
set does not appear in the retired paper's README or progress log (searched for "pouch", "SOC_20-80", "SOC_0-100"), so
the author has not seen its labels; it has been used by others (Saxena et al. 2016, J. Power Sources 327, 394-400, named
by CALCE). The file `README.md`/`progress.md` search is a text search, not an audit of the retired paper's code.

**Honest value for a Journal of Energy Storage reviewer.** None of these sets has the Samsung campaign's space-filling
design, so they cannot carry the main claim. They can answer the professor's request ("include NASA and CALCE") as a
robustness section: the same law and the same leave-condition-out protocol on three small, differently designed sets,
with the main claim made on Samsung only. The PL pouch set is the one with a design that exercises the law's SOC-window,
depth and rate terms; NASA exercises temperature and discharge current; CS2/CX2 exercise almost nothing.

## 1. NASA PCoE Li-ion Battery Aging set (set 5)

**Source and licence.** `5.Battery_Data_Set.zip`, NASA Ames Prognostics Center of Excellence data-set repository;
cite B. Saha and K. Goebel (2007), "Battery Data Set" (repository entry). Licence: none stated; the repository page
says users act at their own risk and publications should acknowledge the repository and the data donors (page digest,
2026-11-05). File `data/raw/nasa_pcoe_battery/5.Battery_Data_Set.zip`, 209,708,670 bytes, SHA-256 `82302a7d...`
in `data/CHECKSUMS.sha256`; six inner zips; retrieval date as in `data/INVENTORY.md`.
**Chemistry and format.** The READMEs say "Li-ion" and a rated capacity of 2 Ah (end of life defined as 2 Ah to 1.4 Ah
or 1.6 Ah). They do not state chemistry or format. The common description (18650, LiCoO2) is secondary-literature
knowledge and is **not verified here**; do not print it as a provider fact.
**Conditions in the READMEs.** Charge: 1.5 A constant current to 4.2 V, constant voltage until 20 mA, for every cell.
Discharge: constant current (or square wave) to a cell-specific cut-off voltage of 2.0 to 2.7 V. Impedance sweep
(0.1 Hz to 5 kHz) between cycles; impedance records carry ambient 24 C in all cells.
**Capacity measurement.** Every discharge record is a full discharge to the cut-off and carries a `Capacity` field (the
copy in `NASA-EV` has a capacity entry for every discharge record). So capacity is available at every discharge cycle,
but it is measured **at the cycling condition itself** (the stress current, the stress temperature, the cell's own
cut-off), not at a fixed reference condition. Capacity therefore mixes ageing with rate, temperature and cut-off effects
(the README says capacity is "till 2.7V" even for cells whose cut-off is 2.0 to 2.5 V).

Per cell (counts and spans from the `.mat` files; conditions from the READMEs; script `nasa_calce_counts_nasa.py`):

| cell | ambient C | discharge | cut-off V | README stop rule | charge / discharge / impedance records | calendar span (days) |
|---|---|---|---|---|---|---|
| B0005 | 24 | 2 A CC | 2.7 | 30 % fade | 170 / 168 / 278 | 56 |
| B0006 | 24 | 2 A CC | 2.5 | 30 % fade | 170 / 168 / 278 | 56 |
| B0007 | 24 | 2 A CC | 2.2 | 30 % fade | 170 / 168 / 278 | 56 |
| B0018 | 24 | 2 A CC | 2.5 | 30 % fade | 134 / 132 / 53 | 44 |
| B0025 | 24 | 4 A square wave (0.05 Hz, 50 %) | 2.0 | not stated | 31 / 28 / 21 | 34 |
| B0026 | 24 | 4 A square wave | 2.2 | not stated | 31 / 28 / 21 | 34 |
| B0027 | 24 | 4 A square wave | 2.5 | not stated | 31 / 28 / 21 | 34 |
| B0028 | 24 | 4 A square wave (data: about 2 A, see anomalies) | 2.7 | not stated | 31 / 28 / 21 | 34 |
| B0029 | 43 | 4 A CC | 2.0 | not stated | 40 / 40 / 17 | 10 |
| B0030 | 43 | 4 A CC | 2.2 | not stated | 40 / 40 / 17 | 10 |
| B0031 | 43 | 4 A CC | 2.5 | not stated | 40 / 40 / 17 | 10 |
| B0032 | 43 | 4 A CC | 2.7 | not stated | 40 / 40 / 17 | 10 |
| B0033 | 24 | 4 A CC | 2.0 | 20 % fade | 197 / 197 / 92 | 67 |
| B0034 | 24 | 4 A CC | 2.2 | 20 % fade | 197 / 197 / 92 | 67 |
| B0036 | 24 | 2 A CC | 2.7 | 20 % fade | 197 / 197 / 92 | 67 |
| B0038 | 24 and 44 | 1, 2 and 4 A levels | 2.2 | 20 % fade | 47 / 47 / 28 | 20 |
| B0039 | 24 and 44 | 1, 2 and 4 A levels | 2.5 | 20 % fade | 47 / 47 / 28 | 20 |
| B0040 | 24 and 44 | 1, 2 and 4 A levels | 2.7 | 20 % fade | 47 / 47 / 28 | 20 |
| B0041 | 4 | 4 A and 1 A | 2.0 | 30 % fade | 67 / 67 / 29 | 14 |
| B0042 | 4 (and 22 in records) | 4 A and 1 A | 2.2 | 30 % fade | 113 / 112 / 50 | 27 |
| B0043 | 4 (and 22 in records) | 4 A and 1 A | 2.5 | 30 % fade | 113 / 112 / 50 | 27 |
| B0044 | 4 (and 22 in records) | 4 A and 1 A | 2.7 | 30 % fade | 113 / 112 / 50 | 27 |
| B0045-B0048 | 4 | 1 A CC | 2.0, 2.2, 2.5, 2.7 | 30 % fade | 72 / 72 / 40 each | 27 |
| B0049-B0052 | 4 | 2 A CC | 2.0, 2.2, 2.5, 2.7 | software crash | 25 / 25 / 12 each | 6 |
| B0053 | 4 | 2 A CC | 2.0 | 30 % fade | 55 / 56 / 26 | 13 |
| B0054 | 4 | 2 A CC | 2.2 | 30 % fade | 102 / 103 / 48 | 27 |
| B0055, B0056 | 4 | 2 A CC | 2.5, 2.7 | 30 % fade | 102 / 102 / 48 each | 27 |

Cell-to-condition structure.
- **27 cells have one fixed protocol**, giving **21 distinct nominal (T, discharge, cut-off) tuples**: 24 C/2 A (cut-offs 2.7,
  2.5, 2.2: 5 cells), 24 C/4 A square wave (4), 24 C/4 A CC (2), 43 C/4 A (4), 4 C/1 A (4), 4 C/2 A (4 tuples, 2 cells
  each: B0049-52 and B0053-56). **Replicates exist only for 5 tuples** (B0005 and B0036; B0006 and B0018; the four 4 C/2 A
  pairs). The other 7 cells (B0038-B0044) change temperature or current inside the cell and are not a point in a static
  stress space.
- **Stresses that vary:** ambient temperature (4, 24, 43 C), discharge current (1, 2, 4 A, i.e. 0.5C, 1C, 2C of the rated
  2 Ah), waveform (constant versus square wave), cut-off voltage (2.0 to 2.7 V, a weak depth-of-discharge lever).
  **Constant in all cells:** the charge protocol (about 0.75C to 4.2 V, full CV), so the charge-rate and upper-SOC terms of
  the law cannot be tested; the SOC window is nearly the same in every cell.
- **Confounding.** Temperature groups were run as separate batches in different periods, so temperature is confounded with
  batch and date; each temperature group has a different current set.
- **Depth of data.** Discharge cycles per cell: 25 to 197; **15 of 34 cells have 47 or fewer** (B0025-32, B0038-40,
  B0049-52), and 13 have at least 100 (B0005-07, B0018, B0033, B0034, B0036, B0042-44, B0054-56). The calendar span is 6 to 67 days. How far each cell actually faded is **not computed here**; a
  go/no-go on observed fade per cell must be run by the lead's analyst before any forecasting claim, from `runs/` files.
- **Known anomalies (READMEs and parse).** (i) B0041-48 and B0053-56: "several discharge runs where the capacity was very low;
  reasons not analyzed"; B0049-52: capacity and voltage "very low" in several runs, stopped by a software crash.
  (ii) README says capacity is for discharge "till 2.7V" although cut-offs differ. (iii) B0025-28 appear in two inner
  zips (set 2 and set 3) with identical CRCs: **duplicates, count once**. (iv) B0028: README says 4 A square wave for all
  four cells, but the discharge samples have a median absolute current of about 2.0 A (B0025-27: about 4 A); the README and
  the data disagree. (v) B0050 and B0052 contain discharge records with all-zero current or sub-1 V minimum voltage (parse
  and earlier inventory: empty field needing tolerant reading). B0033 (minimum about 1.0 V against a 2.0 V cut-off) and B0040 (about 1.75 V against 2.7 V) also contain discharge records
  whose minimum voltage is far below the stated cut-off. (vi) B0053 has 55 charge but 56 discharge records. (vii) Mixed-condition cells
  listed above. (viii) Impedance is always measured at 24 C even in the 4 C groups.
- **Calendar and storage.** Continuous cycling, no storage arm and no rest design; time and cycle count are almost the
  same coordinate (a cycling-only law cannot separate calendar from cycle effects here and does not need to).

**What it can support.**
- (a) Leave-condition-out forecast, cycling-only law: **mechanically possible** on the 27 fixed-protocol cells (21 tuples;
  5-fold on tuples gives about 4 held out per fold), forecasting from an early prefix of each held-out cell's own record
  (capacity is available every cycle, so any "k check-ups" is a choice, not a limit). Two informative stresses
  (T, discharge current) plus cut-off. Not testable: charge rate, SOC mid-point, DoD (beyond cut-off), the KAN stress
  functions for those inputs.
- (b) Learning curve: only m of about 4, 8, 16 tuples; with 21 tuples and heavy grouping the curve would be coarse.
- (c) Within-condition early-life forecasting: yes for the 13 cells with at least 100 discharge cycles (how far they faded is not computed here).
- Role: **descriptive generalisation** in a short results subsection or supplement, with the stop-rule and short-record
  caveats. It must not enter any gated confirmatory test of the Samsung design.

## 2. NASA randomized usage (set 11) and HIRF (set 15)

Not downloaded. The remote archive member lists were read by HTTP range requests (central directory only).
- **Randomized usage**: `11.+Randomized+Battery+Usage+Data+Set.zip`, 1,065,821,095 bytes, 7 inner zips (uniform-distribution
  charge/discharge, room-temperature discharge, variable charge, skewed high/low random walks at room temperature and 40 C).
  Citation B. Bole, C. Kulkarni, M. Daigle, "Randomized Battery Usage Data Set", PHM Society 2014. Page digest: random
  current profiles with periodic reference charge and discharge cycles; the NASA catalog entry for the room-temperature random
  walk lists four 18650 cells (RW3-RW6) with random discharge currents of 0.5 to 4 A, discharge to 3.2 V, and reference cycles
  after every 50 random-walk cycles (catalog digest, secondary; the inner READMEs were not read). A "condition" there is a
  load distribution plus a temperature, with about four cells per part, and a secondary study excluded RW2, RW3 and RW18 for
  anomalous temperature behaviour. It supports history-dependent usage modelling, not a static stress law.
- **HIRF**: `15.+HIRF+Battery+Data+Set.zip`, 1,088,895,795 bytes, Set1-Set6; experiments on an Edge 540 aircraft in a HIRF
  chamber (page digest); the page marks it "currently offline". Not an ageing study.
- Both are below 2 GB; they were not fetched because neither can serve the task. If the lead wants them, the entries are in
  `data/DEFERRED_URLS.tsv` and `tools/resumable_download.py` handles them.

## 3. CALCE CS2 and CX2

**Source and licence.** CALCE battery data page (University of Maryland), cite He, Williard, Osterman, Pecht, J. Power
Sources 196(23), 2011, 10314-10321 and Xing, Ma, Tsui, Pecht, Microelectronics Reliability 53(6), 2013, 811-820 (both
CS2 and CX2), and for CS2 Williard et al., Int. J. Prognostics and Health Management 4, 2013, 1-7 (page digest). Licence:
**none stated**; the page asks that use in publications cite the CALCE articles and describes the data as open access.
**Cells (page digest).** CS2: LiCoO2 prismatic, rated 1.1 Ah, 16 cells. CX2: LiCoO2 prismatic, rated 1.35 Ah, 12 cells (jellyroll
orientation differs from CS2). Charge 0.5C CC to 4.2 V then CV to below 0.05 A; discharge cut-off 2.7 V unless stated.
Ambient temperature is not stated on the page except that CX2-4 is ramped from 25 to 55 C by 10 C every 10 cycles.

| Type | Discharge | Cells |
|---|---|---|
| CS2 type 1 | 0.5C CC | CS2_8, 21, 33, 34 |
| CS2 type 2 | 1C CC | CS2_35, 36, 37, 38 |
| CS2 types 3-6 | alternating currents / random cut-off changes / partial-range cycling | CS2_3, 9; 7; 5, 6; 24, 25 |
| CX2 types 1-2 | 0.5C CC | CX2_16, 31, 33, 35; 34, 36, 37, 38 |
| CX2 types 3-6 | 3C (CX2_8); pulses (CX2_3, 32); temperature ramp (CX2_4) | one or two cells each |

**On disk (verified by parse; script `nasa_calce_counts_cs2.py`).** Zips are workbook collections (one `.xlsx` per test
date, raw Arbin log: step, `Cycle_Index`, current, voltage, capacity columns). `Cycle_Index` restarts in every workbook.

| cell | zip bytes (SHA-256 prefix) | workbooks | cycles (sum of per-workbook cycle indices, after removing duplicate workbooks) | first to last record | protocol seen in the log |
|---|---|---|---|---|---|
| CS2_34 (type 1) | 43,836,986 (`229dcdc8`), complete 2026-11-05 | 23 | 781 | 2010-08-16 to 2011-03-04 (199 d) | discharge 0.55 A (0.5C), charge 0.55 A, 2.7 to 4.2 V |
| CS2_35 (type 2) | 37,056,519 (`84d88cb9`) | 25 | 886 (936 with a duplicate workbook) | 2010-08-16 to 2011-02-03 (171 d) | discharge 1.1 A (1C), charge 0.55 A |
| CS2_36 (type 2) | 37,881,685 (`2e674f58`) | 26 | 976 | 2010-08-16 to 2011-02-02 (169 d) | same |
| CS2_38 (type 2) | 42,811,100 (`98787427`) | 28 | 1032 (1082 with a duplicate workbook) | 2010-08-16 to 2011-02-03 (171 d) | same |

Capacity is measured at **every cycle** (each cycle is a full 4.2 V to 2.7 V cycle at the stress rate; the log carries cumulative
capacity columns). Known anomalies: duplicate workbooks (`CS2_35_2_4_11` equals `CS2_35_2_10_11` and `CS2_38_2_4_11` equals
`CS2_38_2_10_11` in rows and time range, so earlier cycle counts of 936 and 1082 double count 50 cycles); the first three
workbooks of each cell are single-cycle characterisation runs; several workbooks hold fewer than 50 cycles (test restarts);
the cell housing, temperature and rest design are not in the log. The earlier inventory's "936, 976, 1082" are the
uncorrected sums. CS2_34 SHA-256 is new and is added below.
- CS2_37, CS2_33, CS2_8, CS2_21 and the CX2 zips are **not downloaded** (sizes 4 to 164 MB in `data/DEFERRED_URLS.tsv`,
  some unsized) because they would not change the verdict: all remaining static types are 0.5C versus 1C discharge on one
  cell model, one or two conditions.

**What it can support.** (a) No: the static types give two discharge rates within CS2 (0.5C against 1C, 4 cells each) and
0.5C against one 3C cell within CX2, with temperature not stated. (b) No. (c) Yes: 800 to 1,000 cycles per cell with a full
capacity every cycle. Role: **within-condition early-life forecasting** as a descriptive row, or leave out. It adds the
word "CALCE" to the paper but not evidence about the law. The retired paper used 13 of these cells.

## 4. CALCE PL pouch SOC-window set

**Source and licence.** `web.calce.umd.edu/batteries/data/pl/`; cite Saxena, Hendricks, Pecht, "Cycle life testing and
modeling of graphite/LiCoO2 cells under different state of charge ranges", J. Power Sources 327 (2016) 394-400 (page digest;
paper not read). Licence: none stated, cite CALCE (as above).
**Cells and design (page digest).** Graphite/LiCoO2 pouch, rated 1.5 Ah, 3.4 x 84.4 x 50.1 mm. Initial full characterisation
CCCV charge and C/2 discharge between 4.2 V and 2.7 V. Partial cycling: charge C/2, discharge C/2 or 2C, durations set by
Coulomb counting to hold the SOC window, 30 min rest after each charge and discharge step; a full C/2 characterisation cycle
(2.75 to 4.2 V) every 50 or 100 partial cycles; about 50 cycles took roughly 10 days. Temperature is not stated on the page.
**Two cells per window**, 16 cells:

| SOC window (%) | mid / depth (%) | discharge rate | cells | zip (bytes) |
|---|---|---|---|---|
| 0-60 | 30 / 60 | C/2 | PL3, PL10 | `SOC_0-60_HalfC` (89,357,014) |
| 40-60 | 50 / 20 | C/2 | PL4, PL5 | `SOC_40-60_HalfC` (72,818,135) |
| 40-60 | 50 / 20 | 2C | PL9, PL25 | `SOC_40-60_2C` (57,740,595) |
| 0-100 | 50 / 100 | C/2 | PL11, PL13 | `SOC_0-100_HalfC` (67,460,712) |
| 0-100 | 50 / 100 | 2C | PL12, PL14 | `SOC_0-100_2C` (57,559,175) |
| 20-80 | 50 / 60 | 2C | PL17, PL18 | `SOC_20-80_2C` (74,575,680) |
| 40-100 | 70 / 60 | C/2 | PL19, PL24 | `SOC_40-100_HalfC` (106,626,746) |
| 20-80 | 50 / 60 | C/2 | PL21, PL23 | `SOC_20-80_HalfC` (132,710,443) |

Total about 658 MB, all far below 2 GB. Each zip holds one MATLAB v5 `.mat` per cell with a table (operation, start date,
data). Parsed schedule so far (operation table only; `nasa_calce_counts_pl.py`; arrays not read):

| cell | state of its zip | operation rows | nominal partial cycles (sum of block labels) | "Data Missing" blocks | first to last block date |
|---|---|---|---|---|---|
| PL11 (0-100 %, C/2) | readable from a partial zip (member CRC ok) | 13 | 916 | 0 | 2014-08-06 to 2015-07-31 (359 d) |
| PL17 (20-80 %, 2C) | readable (member CRC ok) | 30 (2 single-cycle rows) | 1,450 | 2 | 2014-12-10 to 2015-12-23 (378 d) |
| PL12, PL13, PL18, PL04 | member cut off by the incomplete download | not read | not read | not read | not read |
| the other 10 cells | zips not yet fetched or empty | not read | not read | not read | not read |

Only 2 of the 16 cells could be parsed in this session; the cycle count and time span of the others are therefore **not
verified** and the cell count per window is the CALCE page's, not a count of members. The fetch is still running
(`tools/fetch_calce_queue.sh`); `SOC_20-80_2C.zip` is at 73.4 of 74.6 MB, `SOC_0-100_HalfC` at 40.0 of 67.5 MB, the other six
have not started (`SOC_0-100_2C` and `SOC_40-60_HalfC` hold under 0.5 MB).

**Anomalies seen so far.** Blocks labelled "50 Partial Cycles (Data Missing)" (PL17 has two); the data file holds nominal
block counts, so the number of usable partial cycles can be lower than the nominal sum. Window drift: windows are held by
Coulomb counting, so the realised SOC window shifts as the cell fades. The rest steps make calendar time a large share of
elapsed time (PL17: 378 days for 1,450 nominal partial cycles).

**What it can support.**
- (a) Leave-condition-out forecast, cycling-only law: **feasible in design.** Eight conditions in (SOC mid-point, depth,
  discharge rate), two cells each; leave-one-condition-out gives 8 folds with 2 held-out cells. Charge rate and temperature
  are constant (temperature not stated), so these law terms are not exercised; the SOC-window, depth and discharge-rate terms
  are. Checkups are every 50 or 100 partial cycles, so the "k check-ups per held-out cell" axis maps directly.
- (b) Learning curve: only m of 2, 4, 6 (training pool 7 conditions): too few points for a trend claim; at most a descriptive
  curve with intervals clustered by condition.
- (c) Within-condition forecasting: yes.
- Role: **external replication of the cycling-law forecast at small scale**, preregistered as descriptive; the hypotheses of
  the Samsung design are not transferred. Pre-requisites before use: finish all 8 zips, run the schedule/CRC check, confirm
  where the characterisation capacity sits in each cell's table, and fix the splits before any model sees data
  (CONTRACT section 6).

## 5. Drive archives

- **`drive_nasa_ev/NASA-EV.zip`** (239,496,734 bytes, SHA-256 `787ba917...bf96efee`): `cleaned_dataset/` with 7,565 CSV
  (one per charge, discharge or impedance record), `metadata.csv` (columns type, start_time, ambient_temperature, battery_id,
  test_id, uid, filename, Capacity, Re, Rct) and the nine NASA READMEs. 34 batteries, 7,565 rows. Charge, discharge and impedance
  counts per battery equal those in the original `.mat` files for all 34 batteries. It adds no cells and no conditions; the
  archive does not document how it was "cleaned". Use the original files. `start_time` is stored as a vector string.
- **`drive_calce_ev/CALCE-EV_Dataset.zip`** (5,614,245 bytes, SHA-256 `0219442a...2546c610`): 24 CSV, 209,161 rows;
  `Train/` (BJDST, DST) and `Test/` (FUDS, US06); file names `<profile>_<T><SOC>` with T of 0, 25, 45 and start SOC 50 or 80
  (reading of the names, not documented in the archive). Columns include current, voltage, cumulative capacities, `T`, `SOC`,
  `QAccu`. Every file has one distinct `Cycle_Index`: **single-cycle dynamic-profile tests, no ageing**. Cell type is not
  stated. Not usable for a degradation law.

## 6. Download state and checksums (2026-11-05)

- Completed this session: `calce_cs2/CS2_34.zip` (resumed from 33,095,680 bytes; zip test passed; SHA-256
  `229dcdc836f140f746c26316569c357b346994fddd3be1223b1e457805c484b4`, no checksum is published by CALCE).
- The CALCE server was slow and reset connections (about 30 to 60 KB/s, with refusals). A resumable background fetch of the
  eight PL zips runs from `tools/fetch_calce_queue.sh` (40 KB/s cap, stops when `data/STOP_CALCE` exists). A file is complete
  only when its size equals the byte count in section 4; a file in progress carries its final name until then and cannot be
  opened by `zipfile`. `data/STOP_DOWNLOADS` was not touched and the main downloader stays paused.
- No download above 2 GB was needed. Nothing was fetched from NASA beyond zip directory listings (range requests).
- CALCE and NASA sets are licence-free by statement only: cite the repositories and the named articles; there is no
  redistribution licence, so do not publish raw files with the paper's code.

## 7. Text for the plan (copy into the preregistration)

"NASA PCoE set 5 and CALCE CS2/CX2 were analysed by the first author in an earlier study of evaluation protocols (cell
identifiers and capacity labels were seen). They are therefore treated as previously analysed data: results on them are
descriptive, are reported after the Samsung analysis is frozen, and carry no gate. The CALCE PL pouch set was not analysed
by the authors before; its labels are public and have been used by others. No model is fitted to any of these sets before the
splits, stress coordinates and the go/no-go on observed fade per cell are written to `runs/splits/`."

## 8. Open items for the lead

1. The professor's request can be met with NASA set 5 (descriptive) and the CALCE PL pouch set (small external replication).
   CS2/CX2 add little; say so rather than padding.
2. Before any NASA forecast: a go/no-go from `runs/` files on observed fade per cell (not computed here by instruction).
3. PL pouch: the background fetch must finish (about 550 MB left at the time of writing, at the server's pace perhaps hours);
   then rerun `code/data_audit/nasa_calce_counts_pl.py` to fill the table in section 4.
4. Confirm with Shlok whether "NASA and CALCE" should mean the sets above or also the NASA randomized-usage set (not
   recommended).
