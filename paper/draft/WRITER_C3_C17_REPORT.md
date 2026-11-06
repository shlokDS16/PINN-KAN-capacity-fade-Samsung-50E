# Writer report: closing C3 and C17 in `paper/draft/` (2026-11-06)

Scope: `00_open_items.md`, `03_data.md`, `04_methods.md`, `05_evaluation.md` and this report. Nothing under `code/`, `runs/`, `research/` or the PREREG was touched; nothing was committed. Source: `runs/prereg/PREREG_v4.md` rev. 18 (section 17.2 rows C3 and C17; section 20 rows for the draft). No data, run result file or retention value was opened. The only numbers added are design constants and counts already printed in the PREREG (n = 40, w = 0.78, N = 40, k_cyc = k_full = 4, k_sto = 2, 30/31/32/33 of 40, rho_0 = 0.03, power figures from section 1, labelled simulation). No new citation keys; no AI-use sentence. The files are Markdown and were not compiled.

## C17: disclosure sentences (each carries an HTML comment `C17:` with its source)

| Sentence (PREREG source) | Now at |
|---|---|
| 3.3(10)(a) parsing of 18 cycling cells (163 check-ups); ISU and SNL scratch pilot | `03_data.md:17` |
| 3.3(10)(b) optimiser recipe fixed after a synthetic divergence; SNL pairs | `04_methods.md:45` (end of the training paragraph; it is about the optimiser, so it sits with the recipe) |
| 3.3(10)(c) data-only learners trained on cells with enough points; `n_train_used`; inputs not claimed identical | `04_methods.md:73` (below the comparator table) |
| 3.3(10)(d) CPU, float32, one thread, library versions, bitwise claim | `04_methods.md:81` (tuning and seeds; `[AUTHOR: processor and memory]` kept) |
| 3.3(10)(e) outlier rule developed on CU rows; ET_T23 and exCU enter; thresholds unchanged | `03_data.md:17` |
| 3.3(10)(f) 49 cells with conflicting meta serial (also the 3.2 disclosure sentence) | `03_data.md:15` |
| 3.3(10)(g) retention anchored on ET_T23; order of entry tests unverified; one-time offset | `03_data.md:13` |
| 3.3(11)(c) a few capacity values of five cells displayed; excluded if test cells | `03_data.md:17` |
| 7.2 A10 scope sentence (factor on total loss, two free exponents, favours A10) | `04_methods.md:75` |
| 7.2 scope sentence on the map to the published model (free scales, joint fit, calendar term of cycled cells, 1/r) | `04_methods.md:75` |
| 13 synthetic-circularity sentence (G0 shares choices (a) and (b)) | `05_evaluation.md:71` |

Placement note: the brief put 3.3(10)/(11) in the data section. (a), (e), (f), (g) and 11(c) are there; (b), (c) and (d) are about method and computation and are in Section 4. The auditor traces by the `C17:` comments, so the file differs from the brief only for those three.

## C3: section 20 rows for the draft

| Item (section 20 row) | Done at |
|---|---|
| `05` banner cites v4 chains, NC-1/NC-2, design-effect test | `05_evaluation.md:1` |
| `05` 5.1 splits: grid, Test C untouched, S2 descriptive, ISU/SNL not in run list | `05_evaluation.md:5-13` |
| `05` 5.2 endpoint: window grid, per-condition ensemble score, K chain per-seed | `05_evaluation.md:15-21` |
| `05` 5.3 target/comparator convention, Eq. (8) | `05_evaluation.md:23-29` |
| `05` 5.3 sign-flip text replaced by fixed design-effect sign test, assumption stated (Eq. (9)) | `05_evaluation.md:31-35` |
| `05` 5.3 power sentence (17-22 %) replaced by the simulated figures | `05_evaluation.md:37` (see concern 1) |
| `05` 5.4 H1a-H6 family, H1c gate, H2, H3-H5 replaced by chains P and K, graph, secondary family, ladder (Eq. (10), (11)), closed table, reverse-S findings | `05_evaluation.md:39-63` |
| `05` 5.5 negative control: withdrawn criteria replaced by NC-1 and NC-2; positive controls G0 only, no "beat A11/A12"; identifiability paragraph and G2 sentence removed | `05_evaluation.md:65-71` |
| `05` 5.6 downgrade rows and the lowest-tier rule | `05_evaluation.md:73-79` |
| `05` Limitations dependence sentence (9.9 (r)) | `05_evaluation.md:81-83` (new 5.7) |
| `04` arms table: H1a/H1b/H2/H6/H1c naming dropped; A3, A7 off the grid; A5 at m = 32 only; A15, G15, D*, AG added | `04_methods.md:51-71` |
| `04` the m x k grid and nested subsets, k = 0 | `04_methods.md:13` |
| `04` the window (k_full = 4, k_sto = 2, D025 cap and its disclosure) | `04_methods.md:11` |
| `04` h grid now includes 1; tournament per (fold, m); N = 40; inner folds 2/3; tune once per (fold, m); new 4.6 for A15 and G15; test-time inversion as in 7.5 | `04_methods.md:29`, `:45` (inversion), `:49`, `:77-81`, `:83-85` |
| `03` the "[TO VERIFY: ... neighbour]" line replaced by the causal outlier rule | `03_data.md:15` |
| `03` reference capacity now ET_T23; throughput rule; source comments to v4 | `03_data.md:13` (text), `:7`, `:19`, `:33` (source comments) |
| `00` stale sentence "the prereg 9.3 still names the sign-flip rule" replaced; stale placeholders and verify-list updated | `00_open_items.md:9-13` |

Every remaining "PREREG_v2/v3" or H1a-H6 mention in `03` to `05` is gone (`grep` clean). The `H1`-style names appear nowhere; claim names are P1-P3, K1, K2, Q-H, Q-A10, Q-T, M3.

## Concerns

1. Power figure: section 20 says "simulated 21-25 % at rho 0.75", but section 1 (Power bullet, after D033 D6) gives 0.197 (right-skewed), 0.234 (normal), 0.255 (left-skewed) at 30 of 40. I followed section 1 (0.24 / 0.20 / 0.14 at rho 0.6 / 0.75 / 0.9, with the 0.20-0.26 range at 0.75). The lead should confirm which the auditor reads.
2. 3.3(10)(a) says 18 cycling cells (163 check-ups); 3.3(11)(a) says 163 check-ups of 19 cells. I kept (a) verbatim.
3. `[AUTHOR: define EOLC from the source]` added in the A10 map sentence; the PREREG uses "(1 - EOLC)" without defining it. The A10 equation placements now cite Eqs. 17, 18, 21 of `stroebl2026` and S.1-S.3 of `stroebl2024` as 7.2 states; I did not check them against the papers.
4. `[RESULT: cells excluded]` in `03_data.md` kept although 3.2 reports 0 stage disagreements; I did not turn an identity count into text without your say. The unrelated ISU 238-versus-251 `[TO VERIFY]` in `03_data.md:23` remains.
5. Not placed (no Introduction, Abstract, Discussion or Limitations file exists): the contribution list and abstract novelty rule (D18 6), the Limitations sentence on the monotone-by-construction law, the Discussion readability sentence, the "four rows were not run" appendix note, the fixed Test C/S2 sentences. They are listed in `00_open_items.md:13`.
6. `wilcoxon1945` is no longer cited in the draft; `refs_used.md` was not edited. Draft length grew from about 3,800 to about 7,800 raw words across Sections 3 to 5 (counts include LaTeX and comments), well past the 6,000-word journal limit noted in `00_open_items.md`. Trimming is needed before submission; candidates for the appendices: 5.3 power and simulation sentences, 5.6 second paragraph, 5.7, 4.6, the A10 paragraph in 4.4.
