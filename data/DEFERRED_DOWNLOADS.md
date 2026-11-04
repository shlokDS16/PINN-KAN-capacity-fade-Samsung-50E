# Deferred downloads (data steward, 2026-11-04)

The complete machine-readable list is `data/DEFERRED_URLS.tsv` (columns: dataset, file, bytes, checksum, url; rows are append-only;
`tools/resumable_download.py` reads it). Everything below resumes with `curl -L -C - --retry 5 -o <file> "<url>"`, except the Oxford
file and Google Drive files (see the notes). Rules in force: no file over 100 MB without the lead's yes; no traffic 00:05 to 00:30;
the lead's downloader owns ISU-ILCC (summary files), TJU, HUST and XJTU.

Why deferred: on 2026-11-04 the link gave 50 to 100 KB/s from Zenodo, with DNS failures at about 21:30, so nothing over 300 MB could finish
before the 22:50 cut-off, and the lead capped tonight's volume (mobile data).

## Owned by the lead's downloader (about 6 GB tonight)

| Dataset | File | Bytes | URL |
|---|---|---|---|
| XJTU | Battery Dataset.zip | 2,438,769,934 | https://zenodo.org/records/10963339/files/Battery%20Dataset.zip?download=1 (MD5 a635cef9678e0de21f9d5c1f78a4342c) |
| TJU | Dataset_1_NCA_battery.zip | 579,629,324 | https://zenodo.org/api/records/6405084/files/Dataset_1_NCA_battery.zip/content (MD5 cbd6d7eab2a296b52385e025e8d0f42a) |
| TJU | Dataset_2_NCM_battery.zip | 737,047,539 | https://zenodo.org/api/records/6405084/files/Dataset_2_NCM_battery.zip/content (MD5 a05c485df92f4af560d1d8d7f659ce1b) |
| TJU | Dataset_3_NCM_NCA_battery.zip | 356,066,478 | https://zenodo.org/api/records/6405084/files/Dataset_3_NCM_NCA_battery.zip/content (MD5 d11e68e410a638058906af5e2f5f60f3) |
| TJU | Impedance raw data and fitting data.zip | 1,349,129 | https://zenodo.org/api/records/6405084/files/Impedance%20raw%20data%20and%20fitting%20data.zip/content |
| HUST | our_data.zip (77 pickle files) | 1,188,136,932 | https://data.mendeley.com/public-files/datasets/nsc7hnsg4s/files/5ca0ac3e-d598-4d07-8dcb-879aa047e98b/file_downloaded (SHA-256 071d24617153693b0d29059568525e620f6af6512acc9d00c98c7adcf15125db) |
| ISU-ILCC | Valid_cells.csv, README_V2.0.pdf, capacity_fade.zip, Q_interpolated.zip | 1,727; 640,953; 140,256; 47,797,453 | already on disk in `data/raw/isu_ilcc_small/` (verified); the lead's copy duplicates them |

## Held for a dataset decision (not started)

| Dataset | File(s) | Bytes | Where |
|---|---|---|---|
| ISU-ILCC | Cycling_json.zip (per-cycle JSON) | 10,208,088,439 | https://ndownloader.figshare.com/files/43777470 (MD5 27ac156b31f7c35d4f27a78267c0dd56); URL is a redirect to a signed link, refetch on each attempt |
| ISU-ILCC | RPT_json.zip | 929,406,930 | https://ndownloader.figshare.com/files/43756491 |
| Samsung 50E | 278 per-cell zips (TP_k01_01.zip ...) | 10,292,649,424 in total | figshare article 25975315; every file with its figshare download URL is in the TSV (dataset `samsung50e_figshare_25975315`) |
| Stanford dynamic cycling | aging_summary_cell_NNN.csv (about 4 MB in total), raw_data_cell_NNN.csv (60 to 434 MB each) | 17,132,620,714 in total | `https://stacks.stanford.edu/file/druid:td676xr4322/<basename>`; bulk via Globus (link in the SDR record). `diagnostic_capacities.pkl` deliberately left out (pickle) |
| SNU | Battery raw data.zip | 1,418,420,089 | https://data.mendeley.com/public-files/datasets/zn82y35zr8/files/12adc948-6231-4344-8606-1e8205162379/file_downloaded |
| Dynamic sequences | Battery raw data.zip | 674,610,935 | https://data.mendeley.com/public-files/datasets/h2y7mj4kt7/files/deb660ea-9d02-441b-9b04-edda17ea32fc/file_downloaded |
| CMU eVTOL | 22 cell CSVs + impedance CSVs | about 1.54 GB | figshare 14226830; per-file URLs in the TSV |
| NASA PCoE | randomized usage (11), HIRF (15) | 1,065,821,095; 1,088,895,795 | https://phm-datasets.s3.amazonaws.com/NASA/11.+Randomized+Battery+Usage+Data+Set.zip ; .../15.+HIRF+Battery+Data+Set.zip |
| BatteryLife processed mirror (Zenodo 19688272) | MATR.zip (MIT/Stanford), Stanford.zip, Stanford_2.zip, XJTU.zip (397 MB), Tongji.zip, HUST.zip, MICH.zip (120 MB), MICH_EXP.zip (68 MB), HNEI.zip (43 MB), UL_PUR.zip (6 MB), CALCE.zip (89 MB), ISU_ILCC.zip (10 GB) ... | 30.87 GB in total (20 files) | https://zenodo.org/records/19688272/files/<name>?download=1 ; processed pickles, derived from the originals |
| BatteryLife raw mirror (Zenodo 17960956) | raw_data.zip (Zn-ion, Na-ion, CALB) | 6,308,061,910 | not relevant to Li-ion SOH; not queued |
| CALCE pouch | SOC_40-100_HalfC.zip, SOC_20-80_HalfC.zip | 106,626,746; 132,710,443 | https://web.calce.umd.edu/batteries/data/pl/<name> (over 100 MB, left for a decision) |
| CALCE | CS2_6, 9, 24, 33; CX2_8, 16, 31, 33, 37, 38 (sized, 4 to 164 MB); CS2_3, 5, 7, 21, 25, 37 and CX2_3, 4, 32, 34, 35, 36 (unsized: HEAD timed out) | see TSV | https://web.calce.umd.edu/batteries/data/<name>.zip |
| TBSI Sunwoda | RawData.zip, ProcessedData.zip | 727,042,350; 152,116,922 | https://zenodo.org/records/10715209 |
| Farasis (Nature 2026) | raw_data.zip | 8,988,222,015 | https://zenodo.org/records/17654407 (not queued; stress factors not verified) |
| WMG calendar LGM50 | Calendar ageing dataset.zip | 10,340,654,262 | https://zenodo.org/records/14577286 (calendar ageing only; not queued) |

## Not reachable today (retry later; no URL to queue)

- MIT/Stanford originals, the "Stanford" set (data.matr.io/8) and the aging matrix (data.matr.io/11): the platform's front end ships with an unfilled API address and shows an empty page. Retry; if it stays broken, use the BatteryLife mirror above.
- batteryarchive.org (Sandia, HNEI, Michigan originals): DNS did not resolve from this machine.
- data.nasa.gov dataset page (licence text): timed out from the shell. The files themselves come from the PCoE repository on nasa.gov (reachable).

## Interrupted tonight: complete or restart

- Oxford main file `Oxford_Battery_Degradation_Dataset_1.mat` (253.8 MB per the ORA page): https://ora.ox.ac.uk/objects/uuid:03ba4b01-cfed-46d3-9b1a-7d4a7bdf6fac/files/m5ac36a1e2073852e4f1f7dee647909a7 . The server ignores range requests, so a stopped transfer restarts from zero; two attempts (49 MB, then 35 MB) were deleted. Needs one uninterrupted run on a good link. Lowest priority: all eight cells are at 40 C.
- CALCE (web.calce.umd.edu) ran at about 2 KB/s from 21:50. Resumable partials are saved as `.part` in `data/raw/calce_cs2/` (CS2_34, 33,095,680 of 43,836,986 bytes) and `data/raw/calce_pl_pouch/` (SOC_0-100_HalfC 39,960,576 of 67,460,712; SOC_20-80_2C 62,603,264 of 74,575,680; two near-empty). Resume: rename `x.zip.part` to `x.zip` and run `curl -L -C - -o x.zip <url>` (urls in `DEFERRED_URLS.tsv`). Not started: SOC_40-60_2C (57.7 MB), SOC_0-60_HalfC (89.4 MB).
- Nothing else is half-done: SNL and the Samsung conditions table completed and verified.
