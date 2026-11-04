# Citation audit of draft sections 2 to 5

Date: 2026-11-05. Scope: the 26 keys in `refs_used.md`, every sentence that cites them in `02_related_work.md` to `05_evaluation.md`, the six `[CITE NEEDED]` marks and the Journal of Energy Storage (JES) candidates. The draft sections were not edited.

Method. (1) Metadata: Crossref REST for every DOI (title, authors, container, year, volume, issue, page or article number, `update-to`, `updated-by`, `relation`); arXiv API for arXiv ids; DataCite for the two dataset DOIs; proceedings pages for NeurIPS papers. (2) Support: each citing sentence was compared with our note for the paper, and the reading depth is stated. Where only a title or abstract is available the verdict is limited to that level. Abstracts for the Elsevier papers were obtained from OpenAlex where it had them (Crossref has none). (3) No Crossref record carries a retraction; the one correction notice is the erratum to SOH-KLSTM. Result of the retraction check: none retracted, none with an expression of concern.

## 0. Gate verdict

**FAIL (sentence level).** All 26 records resolve and match; none is unverified. Five sentences claim more than the available reading supports or state a number that the cited paper does not give (items S1 to S5 in section 2). Ledger rows were not written: `tools/ledger.py` does not exist in this project (`ROOT\tools` holds only download scripts).

Counts. Metadata verified without change: 22. Corrected: 4 (gasper2022, preger2020, piekan2026, jarraya2025). Unverifiable: 0. Keys with an unsupported sentence: 6 (piekan2026, liu2025verhulst, sohkpinn2026, li2024isu, preger2020, muehlbauer2022 for Sec. 4.4). Keys with a partial sentence: pgkan2026, gasper2022, zhang2025batlinet with severson2019, zhang2026.

## 1. One row per reference

Status vocabulary: verified, corrected, unverifiable, unsupported-sentence. "Partial" marks a sentence supported only at the level of an abstract or a title.

| Key | Metadata (Crossref / arXiv / DataCite, 2026-11-05) | Reading depth | Status |
|---|---|---|---|
| severson2019 | Nat. Energy 4(5), 383-391, 2019; 14 authors; DOI resolves | none in project (Crossref hit only) | verified. Sentence 2.1 "neither contains a physical law": unread, partial |
| zhang2025batlinet | Nat. Mach. Intell. 7(2), 270-277, 2025 (online 2025-01-15); 7 authors; preprint relation 10.21203/rs.3.rs-3718134/v1 | abstract only (OpenAlex abstract re-read today: no physics component is mentioned) | verified. Sentence 2.1: partial (absence claim from an abstract) |
| liu2024kan | arXiv:2404.19756 v5; 8 authors; ICLR 2025 poster page found; no DOI | full text (notes/papers/29_liu2024.md) | verified; sentence 2.1 and Sec. 4.3 supported |
| jarraya2025 | JES 122, 116541, 2025-06; 7 authors (Crossref spells "Abdelhadi"). `updated-by`: erratum 10.1016/j.est.2025.116868 (JES 124, 2025-07-15) | full text of the arXiv preprint 2509.10496v1; published version and corrigendum not read | corrected (cite the erratum or state that the published version was not compared; spelling of author 6). Sentence 2.1 supported (KAN term in an LSTM) |
| yuan2026timexer | JES 178, 123812, issue 2026-11; 4 authors | title only | verified. Sentence 2.1 supported at title level (multi-order KAN with TimeXer, a transformer-type forecaster) |
| wang2026meta | JES 163, 122207, 2026-06; 5 authors | title only | verified. Sentence 2.1 supported at title level (KAN with LSTM, meta-learning, small sample) |
| peng2024 | Batteries 10(9), 315, 2024-09-04; 8 authors | full text | verified; sentence 2.1 ("incremental-capacity features") supported |
| wang2024 | Nat. Commun. 15(1), 4332, 2024-05-21; 5 authors | full text of the 12-page article; Supplement unread | verified. Sentence 2.2 first clause supported (F, G, residual F_t - G, Eq. 4 of that paper); "introduced the form on which most later work builds" is partial (see S2) |
| pikan2026 | JES 153, 120860, 2026-04; 8 authors | abstract plus released code (full code reading); journal body unread | verified. Sentence 2.2 supported for PIKAN (code: four PINN4SOH feature tables, 16 charge-segment features plus cycle index, no temperature, C-rate or DoD input) |
| pgkan2026 | JES 182, 124768, issue 2026-12; 6 authors | abstract only | verified. Sentence 2.2: partial (abstract says "four public datasets encompassing 387 batteries", which matches the PINN4SOH totals; "charge-segment features" and "no stress input" are not in the abstract) |
| piekan2026 | Energy AI 26, 100928, issue 2026-12; 5 authors; first author "Yohannes, Zekariyas" | abstract only (OpenAlex abstract read today) | corrected (drop "(Abebe)"; DOI string resolves). **Sentence 2.2 contradicted by the abstract:** eight datasets, adaptive partial-charge SOC window chosen per chemistry, seven voltage-based descriptors, cross-chemistry transfer. Not "the four PINN4SOH datasets". unsupported-sentence (S1) |
| liu2025verhulst | Energies 18(22), 5865, 2025-11-07; 4 authors | full text | verified. **Sentence 2.2 contradicted by the full text:** data are the TRI/Severson set (124 cells) and XJTU; inputs are the whole discharge V and T curves (1024 points each) plus time, not a charge segment, and not the four PINN4SOH datasets. The Verhulst ODE has three global scalars and no G network. unsupported-sentence (S1) |
| sohkpinn2026 | Measurement 259, 119769, issue 2026-02; 7 authors | title only | verified. **Sentence 2.2 unsupported:** neither the data, the inputs nor "replaces one or both networks by KANs" can be known from a title. unsupported-sentence (S1, S3) |
| gasper2021 | JECS 168(2), 020502, 2021-02-01; 4 authors | abstract (re-read today) | verified. Sentence 2.3 supported by the abstract: bi-level optimisation and symbolic regression, LiFePO4/graphite calendar-ageing data |
| gasper2022 | JECS 169(8), 080518, 2022-08-01; **5 authors** (Gasper, Collath, Hesse, Jossen, Smith) | abstract (re-read today) | corrected (volume 169, issue 8, article 080518, author list). Sentence 2.3: partial. The abstract says "machine-learning assisted model identification", cycling-degradation models, bootstrap uncertainty, conversion to a state-equation form; it does not say "bilevel" or "symbolic regression" or "stress-factor". |
| kuzhiyil2025 | Appl. Energy 382, 125221, 2025-03; 4 authors | abstract (re-read today) | verified; sentence 2.3 supported (neural networks inside the state equations; calendar ageing, 39 storage conditions) |
| piddm2026 | arXiv:2607.29095 (2026-07-31; 6 authors, no DOI, no journal reference); SSRN DOI 10.2139/ssrn.7213804 resolves (posted-content, same six authors) | full text, 28 pages (notes/papers/priorart_piddm.md) | verified (preprint). Sentence 2.3 supported: Arrhenius SEI time term and Arrhenius DoD and throughput term, network [16,60,60,60,5] supplies five parameters, no storage cells, no SOC, no KAN, test cells share protocols with training cells (12 test cells, seen protocols) |
| guo2026 | arXiv:2607.16864 (2026-07-18; 7 authors; no DOI; no Crossref record) | full text of PDF; supplement unread | verified (preprint). Sentence 2.3 supported ("first 2 to 20 %" of an unseen cell, physics constraint). Note from our reading: the abstract percentages disagree with its Table 1 |
| kacrnn2026 | JES 158, 121853, 2026-05; 2 authors; arXiv:2512.15628 carries the same journal reference and DOI | full text of arXiv v2 | verified; sentence 2.3 supported (KAN functions of SOC inside an Arrhenius reaction network, DSC data) |
| stroebl2024 | Sci. Data 11(1), 1020, 2024-09-19; 6 authors. Dataset 10.6084/m9.figshare.25975315.v1 (DataCite, same six creators) | full text and SI | verified. Sec. 3.1 sentences supported except the condition counts (S4) |
| stroebl2026 | JES 142, 119552, issue 2026-01; 4 authors | abstract and highlights only; body unread | verified. Sentence 2.3 supported at abstract level: the abstract says pi-OED cannot reduce the cyclic-parameter uncertainty "of the underlying heuristic model ... explained by its inadequacy". It also says 279 cells under **71** conditions |
| muehlbauer2022 | JES 48, 103803, 2022-04; 5 authors. Title: "Pareto-optimal power flow control in heterogeneous battery energy storage systems" | Crossref only; paper unread | verified as a record. The data paper's SI S.1.1 says its ageing model is "motivated by Muehlbauer et al.". Sentence 2.3 ("dataset authors fit a semi-empirical superposition [stroebl2024; muehlbauer2022]") is supported by the SI. Sentence 4.4 ("Its published form sums ... each a power law in an Arrhenius term and the stresses") is supported by the SI, but not by Muehlbauer: unsupported-sentence for that key (S5) |
| palm2022 | IEEE Access 10, 112515-112528, 2022; 3 authors | Crossref only; paper unread | verified. Sentence 2.3 ("use it to design experiments") supported through the data paper (it names this method for choosing the stage-2 points) |
| zhang2026 | JES 182, 125097, issue 2026-12; 6 authors | bibliographic record and reference list only; no abstract | verified. Sentence 2.3 supported only for "cites the dataset" (reference list) and the topic (title). The draft's [TO VERIFY] is correct and must stay |
| li2024isu | CRPS 5(4), 101891, 2024-04; 5 authors; arXiv:2307.08382 journal reference matches. Dataset 10.25380/iastate.22582234 (DataCite) | main text of arXiv v2; supplement unread | verified. **Cell count in Sec. 3.2 does not come from the paper** (S4) |
| preger2020 | JECS 167(12), 120532, 2020-01-09 first date, online 2020-09-02; 8 authors | abstract (re-read today) | corrected (volume 167, issue 12, article 120532; year 2020). **The count "61 cells" is not from this paper** (S4) |

## 2. Sentences that claim more than the reading supports

S1. Sec. 2.2, last sentence: "According to their abstracts and, for PIKAN, the released code, these frameworks estimate SOH from charge-segment features of the four PINN4SOH datasets and take no stress condition as input." The sentence covers five papers. Evidence per paper: PIKAN supported by the code; PGKAN partial (abstract: four public datasets, 387 batteries); PI-EKAN contradicted (abstract: eight datasets, adaptive partial-charge windows, seven voltage descriptors); Liu 2025 contradicted (TRI/Severson and XJTU cells, discharge curves, measured temperature trace as input); SOH-KPINN unread (title). Suggested wording: say what each source supports, for example "PIKAN and PGKAN use the four public PINN4SOH data sets; PI-EKAN uses eight data sets with a chemistry-specific partial-charge window; the Verhulst KAN-PINN uses discharge curves of TRI and XJTU cells; SOH-KPINN was not read (title only). None of the papers read conditions the law on cycling temperature, state of charge, depth of discharge or rate [PIKAN code; Liu 2025 full text; PI-EKAN abstract]". The clause "none ... conditions" is supported only for PIKAN and Liu 2025 (read) and for PI-EKAN at abstract level; keep [TO VERIFY] for PGKAN and SOH-KPINN.

S2. Sec. 2.2, first sentence: "Wang et al. introduced the form on which most later work builds." The form is supported (full text). "Most later work" is not: Liu 2025 uses a fixed Verhulst ODE without a G network, PiDDM keeps only the weights of Wang et al. as a baseline, and the other three are abstract- or title-level. Suggested: "Wang et al. proposed ... ; PIKAN keeps it with KANs" (code reading) and drop the priority claim, or name the papers that follow it.

S3. Sec. 2.2: "Later papers replace one or both networks by KANs, namely PIKAN and PGKAN ..., PI-EKAN, ... and SOH-KPINN." For SOH-KPINN nothing beyond its title ("wavelet-enhanced physics-informed Kolmogorov-Arnold network") is known; the F/G structure is not known for it. PI-EKAN: the lead's scan note (PRIOR_ART_SCAN_lead.md) describes F and G networks, both Efficient-KAN; the abstract confirms "feed-coupled solution and dynamics networks". PGKAN: the abstract confirms a KAN estimator and an adaptive-PDE surrogate. So only SOH-KPINN needs the [TO VERIFY] tag.

S4. Sec. 3.1 and 3.2 data counts.
- Sec. 3.1 "132 cells at 19 conditions" and "147 cells at 40 conditions": the data paper reports 22 storage test points and 49 cycling test points (71 in total), and the Stroebl 2026 abstract also says 71 conditions. The values 19 and 40 are our own count of distinct conditions after repeated centre points across stages (note samsung50e_dataset_paper.md, "the lead's count ... is consistent"). Add one sentence that gives both counts, or a reader checking [@stroebl2024] will find 71.
- Sec. 3.2 ISU: "251 cells at 63 conditions [@li2024isu]". The paper (abstract and main text) says 225 cells. The numbers 251 and 63 are from the dataset record (DataCite 10.25380/iastate.22582234: "251 ... cells ... 63 unique conditions. The current release contains 238 cells"). Cite the dataset and say how many cells enter the analysis. Our processed file has 251 cells while the record says the current release holds 238, so check the file against the release before the count is printed.
- Sec. 3.2 SNL: "61 commercial 18650 cells ... [@preger2020]". The abstract of Preger et al. gives no cell count; Sandia design-of-experiment reports list 88 cells (web search, secondary source). The 61 are the pickles of the BatteryLife-processed mirror (Zenodo 19688272, per `data/INVENTORY.md`), which `refs_used.md` says is unverified and uncited. Say "61 cells of the processed release of the data of Preger et al." and cite the release.
- Sec. 3.1 values such as surface temperature 31.6 and 29.8 C are our own computation, not the paper's; they are correctly marked as coming from `runs/samsung_pipeline`.

S5. Sec. 4.4 A10: "Its published form sums a calendar and a cycle loss, each a power law in an Arrhenius term and the stresses [stroebl2024; muehlbauer2022]." The data-paper SI S.1.1 supports the structure (linear superposition, Arrhenius and power-law factors) and names Muehlbauer et al. as the motivation; the exponent placement is garbled in our conversion, and the Muehlbauer paper and the JES 142 body were not read. Say "the dataset authors' model (SI S.1.1 of [@stroebl2024], motivated by [@muehlbauer2022])" and keep the existing [TO VERIFY] on the exponents.

Minor.
- Sec. 2.1 "neither [Severson nor BatLiNet] contains a physical law": Severson unread, BatLiNet abstract only. Acceptable as stated about well-known models, but keep it to "data-driven models" if the claim cannot be tied to a reading.
- Sec. 2.3 Gasper pair: replace "bilevel symbolic regression" and "stress-factor laws" by the abstract wording for 2022 (see the row for gasper2022).
- Sec. 2.3 "Zhang et al. [@zhang2026]": acceptable with the existing tag.

Sentences supported at the stated level (no action): 2.1 on KAN definition; 2.1 on jarraya, yuan, wang2026 (titles), peng; 2.2 on Wang F/G residual; 2.3 on Kuzhiyil, PiDDM, Guo, KA-CRNN, Stroebl 2026 abstract claim, Palm 2022; 3.1 on protocol, capacity definition, stage-2 SOC limit, cells 01-03 check-ups, laboratory aliasing; 4.3 on the KAN layer form.

## 3. Resolution of `[CITE NEEDED]` marks

| Location | Method | Source (key in `refs_verified.md`, section B or C) | Note |
|---|---|---|---|
| 4.2 | Adam optimiser | kingma2015adam (arXiv:1412.6980) | print the arXiv form unless the ICLR 2015 venue is confirmed |
| 4.4 | LightGBM | ke2017lightgbm (NeurIPS 2017, no DOI) | `requirements.txt` pins lightgbm 4.7.0; mention version in the software statement |
| 4.5 | Tree-structured Parzen Estimator | bergstra2011tpe (NIPS 2011, no DOI); implementation akiba2019optuna (10.1145/3292500.3330701) | the code uses Optuna `TPESampler` |
| 5.3 | exact order-statistic interval for a median | thompson1936median (10.1214/aoms/1177732502) | classical source for the sign-test (binomial) interval; the exact sign test: dixon1946sign (10.1080/01621459.1946.10501898) |
| 5.3 | BCa bootstrap | efron1987bca (10.1080/01621459.1987.10478410) | |
| 5.4 | Holm step-down | holm1979 (no DOI; catalogue evidence only) | JSTOR 4615733 not opened; verify against the printed paper or the JSTOR page before submission |
| 2.2, 4.2 (refs_used: "original PINN reference") | physics-informed neural network | raissi2019pinn (10.1016/j.jcp.2018.10.045) | |
| refs_used: semi-empirical life models, Arrhenius | optional | wang2011cyclelife (10.1016/j.jpowsour.2010.11.134), schmalstieg2014 (10.1016/j.jpowsour.2014.02.012), arrhenius1889 (10.1515/zpch-1889-0416) | not currently cited in the draft; add only where a sentence names them |
| not marked, but named in the text | paired Wilcoxon (5.5), Latin hypercube (4.2, 5.5), Gaussian process with ARD (4.4) | wilcoxon1945, mckay1979lhs, rasmussen2006gp | the text names these methods without a source |

Not resolved: the Zenodo mirror of the SNL data (still unverified, see S4); `data/INVENTORY.md` should carry its DOI check before it is cited.

## 4. JES papers that could support existing sentences

Source: `refs\exemplars\JES_CANDIDATES.csv` and the exemplar notes. All DOIs below were re-resolved on Crossref today (title, authors, volume, article number all match the CSV; no update notices). **None has been read beyond its title** (OpenAlex and Crossref hold no abstract for them), so each proposal is limited to a title-level statement and the abstract must be read before the sentence is written.

| Paper (JES) | Sentence it could support | Limit |
|---|---|---|
| Fan, Li et al., 139, 118887 (2025), 10.1016/j.est.2025.118887, "An explainable state of health estimation method for sodium-ion batteries based on Kolmogorov-Arnold networks" | Sec. 2.1: "KANs ... for SOH estimation, including papers in this journal" (a fourth JES KAN paper, on a different chemistry) | title |
| Chen L., Chang C. et al., 122, 116559 (2025), 10.1016/j.est.2025.116559, "Physics-informed neural networks for small sample state of health estimation of lithium-ion batteries" | Sec. 2.2 opening: physics-informed SOH estimation is established in this journal; also Sec. 2.4 "physics-informed SOH networks estimate health from features" (after the abstract is read) | title |
| Zhang W., Zhang H., Bi Z., 142, 119549 (2026), 10.1016/j.est.2025.119549, "A time series physics-informed neural network framework for the state of health estimation of lithium-ion batteries" | Sec. 2.2, same purpose | title |
| Liu Z., Zhou P. et al., 154, 121266 (2026), 10.1016/j.est.2026.121266, "A battery state of health prediction method based on fuzzy stochastic configuration physics-informed neural network" | Sec. 2.2, same purpose | title |
| Liu Zhengxin et al., 174, 123208 (2026), 10.1016/j.est.2026.123208, "State-of-health estimation of lithium-ion batteries from random charging segments using a discrete-time physics-informed neural network" | Sec. 2.2: SOH from charging segments with a physics-informed network, a counterpart to the PINN4SOH feature route | title |
| Ren Y., Tang T. et al., 79, 110065 (2024), 10.1016/j.est.2023.110065, "A data and physical model joint driven method for lithium-ion battery remaining useful life prediction under complex dynamic conditions" | Sec. 2.3: a physical model combined with data under varying conditions, published in this journal | title |
| Long Z., Yuan L. et al., 79, 110248 (2024), 10.1016/j.est.2023.110248, "A neural-driven stochastic degradation model for state-of-health estimation of lithium-ion battery" | Sec. 2.3: a learned degradation process inside a stochastic model | title |
| Qu J., Wang Y. et al., 99, 113086 (2024), 10.1016/j.est.2024.113086, "A novel sequential estimation framework for battery state of health and remaining useful life based on sparse and limited data" | Sec. 2.3 / 2.4: forecasting from limited records, beside Guo et al. | title |
| Gao Z. et al., 141, 119138 (2026), 10.1016/j.est.2025.119138, "Bidirectional-Mamba-based iterative prediction for long-cycle battery remaining useful life with physical constraints" | Sec. 2.3: physical constraints in a forecasting network | title |
| Zhou Z. et al., 117, 115959 (2025), 10.1016/j.est.2025.115959, "Physically enhanced neural network for lithium-ion battery state of health estimation" | Sec. 2.2, same purpose | title |

Read in full or in part but not topical for the existing sentences (use only for form): Jiang et al., JES 182, 124592 (CDUA); Pugalenthi et al., JES 153, 120944 (PINEAPPLE); Hassanaly et al. (Gasper is a coauthor), JES 179, 123823 (neural posterior estimation); Zhou K. Q. et al., JES 100, 113502 (graph network on partial discharge curves). All four DOIs resolve on Crossref.

## 5. Corrections to `refs_used.md`

1. gasper2022: volume 169, issue 8, article 080518; five authors (Gasper, Collath, Hesse, Jossen, Smith).
2. preger2020: volume 167, issue 12, article 120532.
3. piekan2026: first author is Zekariyas Yohannes ("Yohannes" is the Crossref family name); remove "(Abebe)" and the instruction to re-check the DOI string (it resolves: 10.1016/j.egyai.2026.100928).
4. jarraya2025: record the erratum 10.1016/j.est.2025.116868 (JES 124); Crossref spelling of author 6 is "Abdelhadi".
5. liu2024kan: record "ICLR 2025" with the arXiv id; no DOI.
6. zhang2025batlinet: add issue 2 and pages 270-277; severson2019: add issue 5 and pages 383-391.
7. li2024isu: add the dataset DOI to the cited keys for Sec. 3.2 (see S4).
8. Column "Verified in" for yuan2026timexer, wang2026meta and sohkpinn2026 should read "title only" (it does), and the sentences should keep that level.

## 6. Limits of this audit

- No full text of any paywalled paper was opened. The scripted ScienceDirect access is blocked, so the support judgements for JES, Measurement and Energy and AI papers rest on notes made earlier and on abstracts.
- Holm 1979 was not opened on JSTOR; Adam's ICLR 2015 venue was not checked on a proceedings page; the ICLR 2025 poster page of KAN appeared in search results only.
- The Sandia cell count (88) is from a web search of Sandia reports (secondary).
- Crossref prints the JES 178, 182 issues as dated 2026-11 and 2026-12; the draft cites the volume and article number, which is correct.
