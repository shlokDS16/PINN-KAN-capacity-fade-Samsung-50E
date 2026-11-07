# Batch R2 summary: Richardson 2019 and Guo 2022 (JES), 2026-11-06
Notes: `richardson2019.md`, `guo2022.md` in this folder. Full texts: `refs/fulltext/ft_richardson2019_JES23_320_ARXIV_V1.txt`, `ft_guo2022_JES56_105992.txt`. Figures: `refs/figs/richardson2019/gr1-6.jpg` (+ arxiv_p4/p6/p7.png), `refs/figs/guo2022/gr1-10.jpg` (all viewed). PDFs: `refs/pdf/jes_exemplars/`.

## Sources used (be exact about this)
- Guo: publisher PDF (version of record, CC-BY) from the Aalborg repository (vbn.aau.dk). Full reading.
- Richardson: **arXiv v1 (Jul 2018) only**, not the version of record. ScienceDirect is behind Cloudflare 403 (curl and Playwright; no bypass attempted). The six VoR figures were fetched from the CDN and match the preprint's six figures. Section numbers, word counts and reference count (28 vs 34 in Crossref) may differ in the VoR. If we need VoR wording, Shlok can save the CC-BY PDF from ScienceDirect into `refs/pdf/`.

## Findings that change our paper
1. **Richardson's "generalized conditions" are not held-out conditions.** Train = even cells, test = odd cells; all 7 regimes appear in both halves, and the authors say the split guarantees one training cell per group and that a block split would extrapolate and do worse (Sec. 5). Our condition-disjoint test is a real step beyond the closest JES precedent; say so with a precise, cited sentence.
2. Richardson's weak spots we can beat: feature innovation never ablated (Table 4 uses only dt, throughput, time); six configurations scored on the test set, best reported (NRMSE 4.3 %); one split, no spread; no semi-empirical or trivial baseline; GP vs boosting confounded with the time input.
3. What made it work and get 220 cites: a named unit ("load pattern"/transition model), one metric table (RMSE of increment and of state, plus calibration score), public NASA data, and one excellent figure (13 held-out trajectories with bands, failures shown).
4. Guo gives us a vocabulary and hooks. Taxonomy: data-driven assisted physics (parameter identification, reduced-order, UQ) vs physics-guided data-driven (data generation, residual learning, embedding a/b). **Our PINN+KAN = physics-based embedding (b)** with residual-learning (UODE Eq. 6) as nearest neighbour; our extracted laws = symbolic reduction in the Gasper et al. sense (their ref [128], Sec. 3.1.2).
5. Guo's own gap statements to cite: semi-empirical models under-covered in earlier reviews (Sec. 1); hybrids still need validation across more conditions (Sec. 3.2.2, 3.2.3); minimum test matrix and cost (Sec. 4.3); open multi-condition data (Sec. 5).
6. Guo trend statistics (Fig 10, Sec. 5): 190 papers; ML = 78 % of data-driven methods (54 % non-probabilistic + 24 % probabilistic; filtering 18 %, statistics 4 %); electrochemical models above 50 % of the physical part (no figure shows it); physics-guided data-driven about 1 (2011), 2 (2019), 10 (2020), 13 (2021), 7 (2022 to 1 June), read from the plot; semi-empirical never above 4 per year. No search protocol, so use as context only.
7. Guo flaws to avoid: no protocol or n on percentages, Abstract wording not matched by figures, unresolved "Error! Reference source not found." in the VoR (Sec. 3.2.2), no limitations section, Table 5 has no evaluation-protocol column (we add one).

## Concrete actions (tags as in the notes)
- [TEXT] Define held-out in one sentence plus a split table; cite Richardson's even/odd split as the contrast; place the model in Guo's taxonomy in one sentence; hook the three claims to Guo's gap statements.
- [TAB] Table 1 with trivial and semi-empirical baselines first, seed spread, paired condition-level contrasts, calibration/coverage column; related-work table with an evaluation-split column (fill only cells we have read).
- [FIG] Fig 3 forecast overlays in Richardson Fig 6 style with held-out boxed and per-panel error; joint condition-coverage map; schematic in Guo's yellow/blue/green grammar with real data panels.
- [ANALYSIS-EXPLORATORY] GP (Matern-5/2) baseline on our inputs; feature/stress-input ablation; a small, protocol-stated audit of how many exemplar hybrids hold out conditions (numerator and denominator stated).

## Not done / open
- No ledger rows written (brief limited writes to notes/ and refs/). Richardson VoR text not read. Plot-read counts from Guo Fig 10a are approximate.
