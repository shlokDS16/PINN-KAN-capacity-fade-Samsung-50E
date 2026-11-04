# Raw data inventory (data steward, 2026-11-04)

Reading depth: repository metadata (Zenodo, figshare, Mendeley APIs; NASA, CALCE and ORA pages), zip central
directories read by HTTP range request (XJTU, TJU, HUST, SNU, dynamic-sequence sets), and full local
verification of what was downloaded (size, SHA-256, zip CRC, parse, per-cell counts). Papers were not read;
cell counts and conditions quoted for sets that were not downloaded come from repository records and are marked.
Network on 2026-11-04: Zenodo about 50 KB/s at times, intermittent DNS failures, so only files under 300 MB were attempted.
Status of every file is in `PARSE_REPORT.json`; checksums are in `CHECKSUMS.sha256`; deferred files in `DEFERRED_DOWNLOADS.md` and `DEFERRED_URLS.tsv`.

## Table

Cycles to EOL: for (a), (b), (c), (d) taken from `feature_tables_summary.csv` of the author's earlier work (observed cycles per cell: median, min to max; share of cells that reached the table's EOL); for NASA from the local parse; "not in record" means the repository text does not state it and the data were not downloaded. Fit = whether the set can support learning degradation as a function of stress (temperature T, charge/discharge C-rate, depth of discharge DoD or SOC window).

| # | Dataset (source) | Licence | Cells | Chemistry | T | C-rate | DoD / SOC window | Cycles to EOL | Size | Fit for stress-conditioned law | PINN4SOH? | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| a | XJTU (Zenodo 10963339) | CC BY 4.0 | 55 | NCM 18650 | no (one compensation file) | yes, by protocol group (2C, 3C, random R2.5/R3/RW, satellite) | no | median 535 (121-942); 93% reach EOL | 2.44 GB | weak: 6 protocol groups, rate profiles not a clean grid | yes | lead downloads |
| b | TJU (Zenodo 6405084) | CC BY 4.0 | 130 | NCA 66, NCM 55, NCM+NCA 9 | yes: 25, 35, 45 C (unbalanced: 25 C 80%) | rate token in names (025, 05, 1), mostly 05 | no | NCA 570 (28-794), NCM 799 (42-1246), NCM+NCA 940 (871-985) | 1.67 GB | moderate: temperature is a real factor, 35 C has 7 cells | yes | lead downloads |
| c | MIT/Stanford (data.matr.io, offline; mirror Zenodo 19688272 MATR.zip) | mirror CC BY 4.0 | 125 in table (about 124 + closed-loop batch) | LFP 18650 | no (30 C) | yes: 72 fast-charge protocols | no (0-80% charge window by protocol) | median 805 (36-2156), only 12% reach EOL in the table | 4.86 GB (mirror) | moderate for charge-rate staging; no T or DoD | yes | deferred, portal broken |
| d | HUST (Mendeley nsc7hnsg4s) | CC BY 4.0 | 77 | LFP 18650 | no (30 C) | discharge multi-stage only | no | median 1921 (1123-2672), all reach EOL | 1.19 GB | weak (one stress family; pickles) | yes | lead downloads |
| e | NASA PCoE (S3 file 5) | none stated | 34 | LCO 18650 | yes: 4, 22/24, 43, 44 C | yes: 1, 2, 4 A, square wave | cut-off voltage 2.0-2.7 V (DoD proxy) | 25-197 discharge cycles per cell (many stop before 30% fade) | 209.7 MB | weak to moderate: 34 cells, conditions confounded in groups, but full curves | no | DOWNLOADED, verified |
| e2 | NASA PCoE randomized usage (file 11) | none stated | 28 (not verified) | LCO 18650 | yes | random load steps | not stated | not in record | 1.07 GB | moderate (variable loads) | no | deferred |
| e3 | NASA PCoE HIRF (file 15) | none stated | not verified | not verified | not verified | not verified | not verified | not in record | 1.09 GB | unknown | no | deferred |
| f | CALCE CS2 (official) | none stated | 4 fetched (CS2_34/35/36/38) of 15 listed | LiCoO2 prismatic | room | per cell, see CALCE articles | per cell | see PARSE_REPORT (cycle index per cell) | 4 x ~40 MB | weak (few cells) | no | DOWNLOADED |
| f2 | CALCE PL pouch (official /pl/) | none stated | 8 conditions (cells per condition not stated) | graphite/LiCoO2 pouch | room | 0.5C and 2C | SOC 0-60, 0-100, 20-80, 40-60, 40-100 | not stated | 658 MB (8 zips) | good for SOC window and rate (small, clean grid) | no | partly downloaded (files under 100 MB only) |
| D1 | Drive CALCE-EV Dataset.zip | author's | - | NMC/LFP profiles | 0, 25, 45 C | DST, FUDS, US06, BJDST | start-SOC tag | not ageing data | 5.6 MB | none (no ageing labels) | no | DOWNLOADED, verified |
| D2 | Drive NASA-EV.zip | derived from NASA PCoE | 34 | LCO | as e | as e | as e | as e | 239.5 MB | as e (same cells) | no | DOWNLOADED, verified |
| A1 | ISU-ILCC (figshare 22582234) | CC BY 4.0 | 251 | NMC/graphite pouch | no (room) | yes: charge and discharge rate | yes: DoD | not in record | 11.19 GB (summaries 48 MB) | strong: 63 conditions over three stresses | no | summaries downloaded; rest by lead |
| A2 | Samsung 50E DoE (figshare 25975315) | CC BY 4.0 | 279 | NCA/Gr 21700 | yes | yes | yes (SOC/DoD) | not in record | 10.29 GB | strongest: space-filling design, 71 conditions, calendar + cycle | no | conditions table only |
| A3 | Stanford dynamic cycling (SDR td676xr4322) | CC BY 4.0 | 92 | SiOx-graphite / NCA 21700 | no | discharge profile dynamics | not stated | not in record | 17.1 GB (summaries about 4 MB) | moderate: 4 profile types, not a classic grid | no | deferred |
| A4 | SNU (Mendeley zn82y35zr8) | CC BY 4.0 | 60 | NCA/Gr-Si 18650 (3 Ah) | yes: 10, 25, 45, 60 C | yes: low/high charge rate | voltage window groups | not in record | 1.42 GB | strong for T and window; 60 cells | no | deferred |
| A5 | Dynamic sequences (Mendeley h2y7mj4kt7) | CC BY 4.0 | 80 | NMC811/Gr-SiOx 18650 | no (25 C) | yes, stage-wise | yes, stage-wise | 600-cycle sequences (design), EOL not stated | 0.67 GB | strong for history-dependent (path) laws | no | deferred |
| A6 | Sandia SNL (mirror SNL.zip; original batteryarchive.org) | mirror CC BY 4.0 | see PARSE_REPORT | LFP, NCA, NMC 18650 | yes (several) | yes | yes | to EOL 80% by design | 115 MB | strong (T x DoD x rate, three chemistries) | no | downloading |
| A7 | CMU eVTOL (figshare 14226830) | CC BY 4.0 | 22 | Li-ion pouch | yes (ambient) | charge current, power | cruise length | mission data | 1.54 GB | moderate (22 cells) | no | deferred |
| A8 | Oxford Degradation 1 (ORA) | ODbL | 8 | Kokam 740 mAh pouch | no (40 C) | no | no | not stated; characterisation every 100 drive cycles | 254 MB | none (one condition) | no | downloading |
| A9 | TRI aging matrix (data.matr.io/11) | not verified | 359 | NCA/Gr+SiOx 21700 | not verified | 207 protocols | not verified | not verified | - | likely strong; portal offline | no | unreachable |
| A10 | WMG calendar LGM50 (Zenodo 14577286) | CC BY 4.0 | 39 conditions | NMC | storage T | no | storage SOC | calendar only | 10.3 GB | calendar part of a law only | no | not fetched |

Notes on rows that did not go as planned.
- data.matr.io serves a page whose API address placeholder is unfilled (`%REACT_APP_API_URL%`); the front end loads empty, so the MIT/Stanford originals, the "Stanford" set (data.matr.io/8) and the aging matrix (data.matr.io/11) cannot be listed or fetched from this machine today. The BatteryLife mirror on Zenodo carries the MATR data in processed form (pickle files).
- batteryarchive.org and some Mendeley/figshare API calls failed on DNS at times; those lookups were retried.
- The Oxford main file listed on the ORA page is 253.8 MB; a first attempt stopped at 49 MB without an error and was deleted (the server ignores range requests, so a restart is needed).

## Author's PINN4SOH feature table (read only, not modified)

`C:\Users\Shlok\Downloads\research paper for proctor\Proctor Research paper 2\data\processed\feature_tables_long.parquet`
(51.6 MB, 310,705 rows, 30 columns, one row per cell and cycle). Rows per dataset: HUST 144,366; MIT 85,577; TJU 57,465; XJTU 23,297.
Cells: HUST 77 (LFP), MIT 125 (LFP), TJU 130 (66 NCA, 55 NCM, 9 NCM+NCA), XJTU 55 (NCM): 387 in total.
Columns: `cell_id`, `dataset`, `chemistry`, `group`, `cycle`; twelve charge-segment features (`voltage mean`, `voltage std`, `voltage kurtosis`,
`voltage skewness`, `voltage slope`, `voltage entropy`, `current mean`, `current std`, `current kurtosis`, `current skewness`, `current slope`,
`current entropy`) plus `CC Q`, `CC charge time`, `CV Q`, `CV charge time`; labels and bookkeeping: `capacity`, `nominal_Ah`, `soh_nominal`, `soh_initial`,
`soh_eol_basis`, `eol_cycle`, `total_cycles`, `rul`, `life_fraction`.
It has no temperature, charge-rate, depth-of-discharge or protocol column and no voltage curves, so a stress-dependent degradation law cannot be learned from it;
it is a summary of the charge segment only. The `group` column holds an empty string in the first rows (XJTU), so batch or protocol labels are not carried over.

## One paragraph per dataset

**(a) XJTU.** Wang et al., Nature Communications 2024, record "Physics-informed neural network for lithium-ion battery degradation stable modeling and prognosis" (Zenodo 10963339, CC BY 4.0, MD5 a635cef9678e0de21f9d5c1f78a4342c). One zip of 2,438,769,934 bytes; 55 cells in six batches (8, 15, 8, 8, 8, 8) named 2C, 3C, R2.5, R3, RW and Sim_satellite, one `.mat` per cell, plus `Temperature_Compensation_Data.mat` and two PDFs. The stress factor that varies is the charge/discharge strategy, not temperature (a temperature-compensation file is the only temperature artefact). Used by the author's earlier paper through the PINN4SOH feature table. Not downloaded tonight (2.4 GB; Zenodo throttled); URL in `DEFERRED_URLS.tsv`.

**(b) TJU.** Zhu et al., Nature Communications 2022 (Zenodo 6405084, v2, CC BY 4.0; the record's concept DOI is 10.5281/zenodo.6379165). Three zips of one CSV per cell: Dataset 1 NCA (66 files: CY25-025 7, CY25-05 19, CY25-1 9, CY35-05 3, CY45-05 28), Dataset 2 NCM (55 files: CY25-05 23, CY35-05 4, CY45-05 28), Dataset 3 NCM+NCA (9 files, CY25-05); plus impedance data. File names encode temperature (25, 35, 45 C) and a rate token; the mapping of the token to C-rate must be read from the paper before use. Uncompressed 5.6 GB. Used through the feature tables. Deferred (1.67 GB in total).

**(c) MIT/Stanford.** Severson et al. 2019 and Attia et al. 2020: LFP/graphite A123 APR18650M1A cells, 30 C, 72 fast-charge protocols (cycle lives 150 to 2,300). The official portal is currently non-functional (see note), so nothing was downloaded and cell counts here are from the author's feature table (125) and secondary descriptions, not from the portal. The processed mirror `MATR.zip` (4,864,920,138 bytes) is the realistic route; originals should be re-tried later. Used through the feature tables.

**(d) HUST.** Ma et al. 2022, Mendeley Data nsc7hnsg4s v2 (CC BY 4.0), 77 LFP/graphite cells (1.1 Ah), same charge protocol, 77 multi-stage discharge protocols, 30 C. One zip (1,188,136,932 bytes, SHA-256 071d2461...25cf8f of the file as published by Mendeley) with 77 `.pkl` files. Pickles must not be loaded with plain pickle; use the allowlist loader in `code/data_audit/verify_raw.py` after a static scan. Used through the feature tables. Deferred.

**(e) NASA PCoE.** `5.+Battery+Data+Set.zip` from the PCoE repository (209,708,670 bytes), six inner zips with 34 `.mat` batteries (B0005 to B0056 with gaps). Per-cycle charge, discharge and impedance records with full voltage/current/temperature curves; ambient temperatures seen: 4, 22, 24, 43, 44 C; discharge current and cut-off voltage vary by group (README texts are in `drive_nasa_ev`). Number of discharge cycles per cell ranges from 25 to 197 (see PARSE_REPORT.json). Two cells (B0050, B0052) have records with an empty field that needed tolerant parsing. No licence text is published on the repository page; cite the PCoE repository and Saha and Goebel. Not in the author's earlier tables. Randomized-usage (1.07 GB) and HIRF (1.09 GB) files are listed in the same repository and deferred.

**(f) CALCE.** The official page offers CS2 and CX2 (prismatic LiCoO2), A123 LFP and INR18650-20R dynamic-profile sets, PL pouch SOC-window sets and storage sets; no licence is stated, only open access and a request to cite the CALCE articles. CS2_34, 35, 36, 38 (one xlsx per test date, raw cycler log with `Cycle_Index`, current, voltage, capacities) were fetched as the smallest typical cells; CS2_3, 5, 7, 21, 25, 37 and the CX2 files timed out on a size probe and are listed unsized. The eight PL pouch zips (SOC window by C-rate) are the cleanest official stress-variation set on the page and are queued. The Drive "CALCE-EV Dataset.zip" is a different thing: 24 CSV files of dynamic-profile tests, not ageing data.

**(A1) ISU-ILCC.** 251 NMC/graphite pouch cells, 63 cycling conditions varying charge rate, discharge rate and depth of discharge, reference tests about weekly. Downloaded and verified: `Valid_cells.csv` (251 names), `README_V2.0.pdf`, `capacity_fade.zip` (251 CSV, 2 to 80 capacity points per cell, median 19), `Q_interpolated.zip` (251 CSV, 47.8 MB, four columns per file) and the shipped `process_data.py` stored as `.txt` (never run). Per-cycle data (`Cycling_json.zip`, 10.2 GB) and `RPT_json.zip` (929 MB) are deferred. This is the best candidate for learning degradation as a function of three stresses, but only the weekly capacity points are on disk so far. It is a strong alternative to the four PINN4SOH sets.

**(A2) Samsung INR21700-50E.** 279 cells, 71 aging conditions from full-factorial, Latin-hypercube and model-based optimal designs over temperature, depth of discharge and C-rates, with calendar and cycle ageing (Scientific Data 2024, figshare 25975315, CC BY 4.0). 10.29 GB as 278 per-cell zips; only the conditions table is local (when the download completed). Best fit to "learn a law over stress", because the design is a space-filling design rather than a few groups.

**(A3) Stanford dynamic cycling.** Geslin et al., Nature Energy 2025, Stanford Digital Repository td676xr4322, CC BY 4.0: SiOx-graphite/NCA 21700 cells under constant and dynamic discharge profiles; per-cell `aging_summary_*.csv` (25 to 74 KB) and `raw_data_*.csv` (60 to 434 MB). 17.1 GB in total; bulk transfer is intended through Globus. Individual files download through `https://stacks.stanford.edu/file/druid:td676xr4322/<basename>`. A `diagnostic_capacities.pkl` is also present and was not fetched.

**(A4) SNU.** 60 Samsung INR18650-30Q cells (NCA/Gr-Si, 3 Ah) in a temperature-controlled chamber at four temperatures (10, 25, 45, 60 C), with charge-rate and voltage-window groups visible in the file names; 784 CSV and 8 xlsx including processed features and second-life tables; zip 1,418,420,089 bytes. The record title concerns knee-point detection. Deferred.

**(A5) Dynamic operating sequences.** 80 LG INR18650-MJ1 (NMC811/Gr-SiOx, 3.5 Ah) cells at 25 C: 72 cells in 24 sequences x 3 replicates (four 150-cycle stages with changing conditions) and 8 highly dynamic cells (condition changes every 25 cycles). Suited to path-dependent (history-dependent) degradation laws, which a static stress law cannot represent. 80 CSV, 674,610,935 bytes. Deferred.

**(A6) Sandia (SNL).** Preger et al., J. Electrochem. Soc. 2020: commercial LFP (A123), NCA (Panasonic) and NMC (LG) 18650 cells cycled at several temperatures, depths of discharge and discharge rates (charge always C/2). The original is hosted at batteryarchive.org, which did not resolve from this machine; the Zenodo mirror in BatteryLife processed format (`SNL.zip`, 115,187,861 bytes) was queued. See SNL status in PARSE_REPORT.json.

**(A7) CMU eVTOL.** 22 cells (VAH01..VAH30) under eVTOL duty cycles with ambient temperature, cruise length, power and charge current varied; per-cell CSV (20 to 138 MB) plus impedance CSVs; 1.54 GB. Mission-profile rather than lifetime-to-80% data. Deferred.

**(A8) Oxford.** Eight 740 mAh Kokam pouch cells at 40 C with Artemis urban discharge; characterisation every 100 drive cycles (1C and pseudo-OCV curves); CC-CV charge. No stress factor varies, so it adds nothing to a stress law but is a popular PINN benchmark. ODbL licence; cite the dataset DOI and Birkl's thesis (the readme asks for both).

## Choice guidance for the team (data only; not a decision)

1. A degradation law "as a function of stress" needs per-cell stress labels and many conditions: A1 (63 conditions, 251 cells), A2 (71 conditions by design), A4 (temperature and window), and the CALCE PL set (SOC window by rate) fit; the author's feature table does not.
2. Only (e), (f), A8 and A1 have anything on disk today, and of those only (e) and (f) have full per-cycle curves.
3. The four PINN4SOH sets remain available but carry no stress columns (fixed temperature in HUST and MIT; XJTU varies protocol; TJU varies temperature but the feature table dropped it).
