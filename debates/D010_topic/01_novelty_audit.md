# D010 novelty audit of candidates C1-C4 (2026-11-04)

Auditor: novelty-auditor (checks only, proposes nothing; no rescue suggestions).
Reading depth: **FT** full text; **FT-partial** full text, some sections; **AB** abstract only (paywalled or not downloaded); **CODE** released repo read by the lead (`notes/code/PIKAN.md`), journal paper unread.
Tools: OpenAlex (search, cites filter), Crossref, arXiv API, WebSearch. **Exa was unavailable** (OAuth not authorised). Semantic Scholar returned nothing (rate limit). **OpenReview (ICLR 2027, NeurIPS 2026) was not searched** (no tool). arXiv was searched by date to 2026-11-02, which covers the last 90 days.

## 0. Verdicts

| Cand. | Verdict | Conf. | Most dangerous prior work |
|---|---|---|---|
| C1 stress-conditioned PI-KAN rate law, early-cycle forecast | **INCREMENTAL** (model class occupied; KAN correction plus causal first-K forecast of an unseen cell is the open slice) | 0.70 | PiDDM, arXiv 2607.29095 |
| C2 identifiability of KAN-discovered laws | **NOVEL as a question**; contribution type is an audit | 0.65 | PGKAN (JES 182, 124768) and Gasper 2021/2022 |
| C3 what the physics residual does | **INCREMENTAL, leaning TAKEN** as a standalone paper | 0.60 | PIKAN's own JES paper (ablation in the paper unread) |
| C4 merge | **INCREMENTAL overall**; coherent only if identifiability is the headline and C3 is reduced to a control table | 0.65 | PiDDM (model), PGKAN (discovered-law claim) |

## 1. The single most dangerous prior work: PiDDM

Chen, Jian, Sigdel, Xiong, Wang, Luo, "PiDDM: Physics-Informed Differentiable Degradation Modeling for Lithium-Ion Battery State-of-Health Prediction", arXiv 2607.29095v1, 2026-07-31 (arXiv API verified). Reading: **FT-partial** (PDF converted; read Sections 1, 2.1 to 2.4.6, introductions of 3.1 and 3.2, conclusion; not every table).
Does (from the PDF):
- Rate law (Eq. 1): dQ/dn = -[kSEI exp(-ESEI/RT) t^alpha + kLLI exp(-ELLI/RT) DoD^b1 Ah^b2]; negative by construction.
- A 3x60 MLP maps 16 charge-segment features of cycle n to five "effective, cycle-dependent kinetic parameters" (ESEI, alpha, ELLI, b1, b2); kSEI and kLLI are global trainable scalars; known operating variables z_n = (T_n, t_n, DoD_n, Ah_n) enter the rate law. Forward Euler on the cycle coordinate from the measured Q0 (Eqs. 2 to 3).
- XJTU, 55 cells, 6 protocols, cell-level split (43 train, 12 test). "Extrapolation" = train on the first 90 percent of each training cell, evaluate complete test trajectories; baselines MLP and Wang-style PINN (Tables 3, 4).
Does not: no KAN; no early-cycle-only forecast (the test cell's charge features are inputs at every cycle, including the extrapolated region); no identifiability or stability analysis (the paper says the five outputs "should not be interpreted as independently measured electrochemical parameters"); no symbolic law; code "available upon request"; preprint, not peer reviewed. Whether T varies across XJTU cells was not checked.
Consequence: "Arrhenius/throughput rate law with neural parameters, integrated in cycle units, negative by construction, on XJTU" is public since July 2026.

## 2. C1

Claim: dQ/dN = -r(Q, N, s), r >= 0, mechanistic backbone plus small KAN correction, cycle units, causal normalisation; forecasts a held-out cell's remaining trajectory and EOL from its first K cycles plus stress s. S = same, P = partial, D = different.

| Work (id) | Question | Mechanism | Method | Evidence | Scale | Result |
|---|---|---|---|---|---|---|
| PiDDM, arXiv 2607.29095 (FT-partial) | P | S | D (MLP) | D (XJTU, 12 test cells) | P | not comparable |
| E Lixin et al., J. Electrochem. Soc. 2025, doi 10.1149/1945-7111/addd4e (AB, OpenAlex) | P (trajectory plus RUL) | P (multi-factor aging model with knee; DOD, temperature, C-rate; LSTM PINN) | D (CNN+LSTM) | P (132 LFP cells, fast-charge protocols) | P | RUL RMSE 75.62 cycles; trajectory RMSE cut 38 to 85 percent vs no-physics ablations |
| Guo, Vilsen, Stroe et al., arXiv 2607.16864 (AB) | S ("trajectory and lifetime ... using only 2 percent early-life observations") | P (particle-cracking mechanism as soft constraint, latent design parameters) | D | P | ? | 6 to 8 times error cut vs ML baselines |
| Kuzhiyil, Damoulas, Planella, Widanage, Applied Energy 382, 125221 (2025), Crossref verified (AB) | P | S in spirit (NN inside a physics state equation, UDE) | D | D (calendar ageing, 39 storage conditions) | D | calendar fade only |
| Gasper, Collath, Hesse, Jossen, J. Electrochem. Soc. 2022, doi 10.1149/1945-7111/ac86a8 (AB, OpenAlex); Gasper, Gering, Dufek, Smith, J. Electrochem. Soc. 168, 020502 (2021), doi 10.1149/1945-7111/abdde1 (AB, Crossref) | P | S (algebraic stress-factor law; converted to state-equation form and validated on cells under varying loads) | D (bilevel symbolic regression) | P (LFP/Gr) | P | half the MAE of an expert model; bootstrap UQ |
| Navidi, Bajarunas, Arias Chao, Hu, eTransportation 25, 100432 (2025), Crossref verified (AB via search summary) | S (capacity forecast, different usage, two-cell training) | P (aging-aware electrochemical model + RNN) | D | P | P | 40 to 70 percent RMSE cut |
| Wang, Ma, Gao, Chen, Reliab. Eng. Syst. Saf. 260, 111003 (2025), Crossref verified (AB: title + search snippet) | P (neural ODE with KAN for degradation states, solid-state RUL) | P | P (KAN in an ODE) | ? | ? | not extractable |

What each closest work does not do relative to C1:
1. PiDDM: see Section 1.
2. JECS addd4e: already puts DOD, temperature and C-rate into a physics-informed degradation model and predicts trajectory and RUL; no KAN; early-K causal protocol and identifiability not stated in the abstract.
3. arXiv 2607.16864: early-life to trajectory and lifetime under a physics constraint; constraint is a latent mechanism, not a stress-conditioned rate law; no KAN.
4. Kuzhiyil 2025: "known state equation plus learned correction" is public (calendar ageing, UDE); C1 is that idea for cycling with a KAN correction.
5. Gasper 2021/2022: the stress-dependent algebraic law and its state-equation form are public; a mandatory baseline.
6. RESS 260, 111003: shows KAN plus neural ODE for battery degradation states exists; not a stress-conditioned rate law with a physics backbone, as far as the snippet shows.

PIKAN and PGKAN for C1: neither forecasts, neither uses operating conditions in the dynamics (Section 6).

**Verdict C1: INCREMENTAL, 0.70.** Not found in any search: a KAN correction on a structured backbone with a causal first-K forecast of an unseen cell under held-out stress. Each ingredient is public.

## 3. C2

Claim: symbolic laws extracted from physics-informed KANs on SOH data are not stable across seeds, folds and cells, do not survive rounding, and do not recover a known generating law, unlike a structured backbone plus KAN correction.

| Work | Question | Mechanism | Method | Evidence | Scale | Result |
|---|---|---|---|---|---|---|
| PGKAN, J. Energy Storage 182, 124768 (AB) | P (claims "dominant degradation PDEs governing each dataset"; stability tests, if any, unread) | S | S | D (4 datasets, 387 cells) | S | MAPE 8.5 to 19.7 percent better |
| PIKAN, J. Energy Storage 153, 120860 (README abstract, CODE) | P (claims "structural similarity to electrochemical models"; repo has no synthetic recovery or seed test) | S | S | P | S | rounding to 4 digits: MAPE 0.0042 to 0.1458 (XJTU); per-dataset parabolas differ (lead's reading, PIKAN.md 6.5 and 6.6) |
| Gasper 2021 / 2022 (AB) | P (rediscovery of known relations; cross-validation, sensitivity, bootstrap UQ) | D (algebraic SR) | D | D | P | identifiability-adjacent, not a KAN test |
| Ghosh and Roy, arXiv 2604.00400 (AB) | D | S (KAN closed-form SoH) | S | D (one eVTOL cell) | D | no stability test stated |
| TIDE, arXiv 2607.14640 (AB) | D | P (symbolic distillation of a trained backbone) | D | ? | ? | no identifiability test stated |

Found: no battery paper (2019 to 2026-11) that tests seed/fold/cell stability, rounding survival, or synthetic recovery of a KAN- or PINN-discovered degradation equation. Absence is weak evidence; PGKAN and PIKAN full texts are unread.
**Verdict C2: NOVEL as a question, 0.65.** A hostile reviewer will note the audit targets two papers of one group and rests partly on a repo the lead found to be a mid-experiment snapshot.

## 4. C3

Claim: in Wang-2024-family models the fixed-feature partial-derivative residual (and u_t inside G) adds nothing measurable beyond the data-only network; a total-derivative residual changes that, under training-cell-only tuning.

| Work | Question | Mechanism | Method | Evidence | Scale | Result |
|---|---|---|---|---|---|---|
| PIKAN, JES 153 (CODE) | P (paper may hold an ablation; code already removes u_t from G, fixing the PINN4SOH degeneracy) | S | P | P | S | physics at alpha=beta=1e-3 close to data-only KAN in released means |
| PI-EKAN, Energy and AI 26, 100928, Crossref verified (AB: "component ablation identifies bounded adaptive weighting as key") | P | S | P | P | 8 datasets | ablation exists |
| PiDDM (FT-partial) | P (own physics structure vs Wang-style PINN and MLP) | D | D | D | D | beats baseline PINN, Table 3 |
| Navidi, Thelen, Li, Hu, Energy Storage Mater. 2024, doi 10.1016/j.ensm.2024.103343 (title only; arXiv 2404.04429) | P (comparison of physics-informed methods for degradation diagnostics) | D | D | D | D | not extractable |

**Verdict C3: INCREMENTAL, leaning TAKEN as a standalone paper, 0.60.** Every Wang-family follow-up reports a component ablation. The total-versus-partial-derivative point was not found stated in any paper I found; that is weak evidence.

## 5. C4

**Verdict: INCREMENTAL, 0.65.**
Hostile-reviewer judgement, coherent or glued:
- C1 and C2 are linked by one thing: the stress-conditioned law has named parameters (activation energy, throughput exponent) whose recovery can be tested, a free-G KAN has none. That link is real; C1+C2 can be one paper.
- C3 asks about the residual in a different model family (estimation, Wang-style PDE). A forecasting model without that residual has nothing for C3 to attribute; as described it is glued on. A control table of the proposed model's own components (structure on/off, KAN correction on/off) is a different, in-scope thing.
- Two-paper risk: forecasting accuracy and identifiability compete for the same 8 to 10 JES figures; each can end up thin.

Sharpest novel claim surviving this audit (what is new, not advice): a stress-conditioned learned degradation law, evaluated on held-out cells from their first K cycles, is tested for recovery of known stress exponents on synthetic cells and for parameter stability across seeds, cells and folds, and a PIKAN-style free-G KAN law fails the same tests. The model is not new (PiDDM, JECS addd4e, Kuzhiyil); the unoccupied part is the identifiability test on such a law together with causal early-K forecasting.

## 6. PIKAN and PGKAN

| Item | PIKAN (JES 153, 120860) | PGKAN (JES 182, 124768) |
|---|---|---|
| Reading | README abstract plus full repo code; journal text unread (ScienceDirect 403) | AB (Crossref/OpenAlex). Abstract says code "will be available"; no PGKAN repo among the 6 popular of 34 repos on github.com/USTC-AI4EEE (only those 6 were visible) |
| Forecasts a trajectory | No: SOH_k from charge features of cycle k; time is life fraction (CODE) | "SOH estimation"; no forecast stated |
| Operating conditions in the dynamics | No (16 summary features) (CODE) | none stated |
| Identifiability | none in repo; dataset-specific parabola, rounding collapse (CODE) | claims discovered PDEs per dataset and spline-to-term alignment; stability not mentioned |

Corrections to `PRIOR_ART_SCAN_lead.md`: PGKAN is volume 182 (issued 2026-12; article 124768; Crossref); PI-EKAN is evaluated on eight datasets, first author Zekariyas Yohannes Abebe (Crossref family name "Yohannes").

## 7. Wang et al. 2024 follow-ups (OpenAlex W4398164319)

cited_by_count 902; 914 records retrieved and scanned by title/abstract keywords. KAN users: SOH-KLSTM (JES, doi 10.1016/j.est.2025.116541; KAN+LSTM, not physics); Wei et al., Expert Syst. Appl. 296, 128969 (title only); SOH-KPINN (Measurement 259, 119769); Liu et al. Energies 18, 5865 (Verhulst KAN-PINN); PGKAN; PI-EKAN. Trajectory/path users: Yang et al., Applied Energy 398, 126427 (2025), multi-task transformer PINN with SOH, RUL and "short-term degradation path" (AB via search summary; voltage/current around CV; no stress dynamics, no KAN); Navidi et al. (above). Found no follow-up combining KAN with early-cycle trajectory forecast. OpenAlex counted 1 citation for PIKAN JES and 0 for PGKAN.

## 8. Other works checked

- Severson et al., Nat. Energy 4 (2019), doi 10.1038/s41560-019-0356-8 (Crossref hit): cycle life, no trajectory, no physics.
- Preger et al., J. Electrochem. Soc. 2020, doi 10.1149/1945-7111/abae37 (Crossref hit; volume not checked): Sandia dataset. arXiv 2410.14347 (Murgai et al., SciML UDE/NeuralODE forecasting of battery degradation; AB): the abstract names no dataset, so the lead's "Sandia NMC set" is unverified by me.
- Zhang et al., Nat. Mach. Intell. 7, 270 (2025), doi 10.1038/s42256-024-00972-x (BatLiNet; AB): early-cycle lifetime across ageing conditions, no physics.
- Zhang et al., Nature 2026, doi 10.1038/s41586-025-09951-7 (Discovery Learning; press summary only): cycle-life prediction with a physics simulator, not a trajectory.
- Aitio and Howey, Joule 5, 3204 (2021), doi 10.1016/j.joule.2021.11.006 (Crossref): field-data end of life, lead-acid.
- Sulzer et al. (Joule 2021, doi 10.1016/j.joule.2021.06.005): OpenAlex title hit "The challenge and opportunity of battery lifetime prediction from field data"; authorship not verified.
- **Schofer et al. Adv. Sci. 2022: DOI unresolved** (Crossref and OpenAlex gave no match; only the lead's PMC9561774 pointer).
- van Vlijmen et al., ChemRxiv 2023, doi 10.26434/chemrxiv-2023-zdl2n (363 cells, 218 protocols, interpretable ML on degradation modes; AB): data source and interpretability prior art, no rate law or KAN.
- arXiv 2506.17755 (PIMOE, 207 cells, 77 conditions), 2607.11943 (BattVAE-GP, simulated, latent GP over cycle and C-rate), 2611.03150 (FlowBatt, 2026-11-02, flow-matching trajectory from early cycles, five public benchmarks): trajectory-from-early-cycles without a physics rate law; they set the accuracy baseline for that claim.
- J. Power Sources, doi 10.1016/j.jpowsour.2025.238028 (knee, AB); Commun. Chem. 2026, doi 10.1038/s42004-026-02220-2 (Li-S physics-informed NeuralODE lifetime forecasting, AB).

Query log: OpenAlex `search=` on ~35 strings covering physics-informed KAN trajectory/RUL/symbolic, neural ODE and UDE battery degradation, stress-dependent rate learning, early-cycle trajectory, hybrid semi-empirical plus NN, identifiability, SINDy, knee models, Gasper/Schofer/Aitio/Sulzer/Kuzhiyil names, KAN symbolic stability, "does the physics loss help", PINN critiques; OpenAlex `cites:W4398164319`; arXiv API date-sorted queries on KAN+battery, physics-informed+battery+trajectory, neural ODE+battery, identifiability, symbolic regression+fade, UDE+battery, early-cycle trajectory, Arrhenius+neural, Sandia, TIDE; WebSearch on PIKAN title, Discovery Learning, Yang 2025, Wang RESS 2025, Navidi 2025. About 300 titles screened, abstracts read for about 45, one closest paper (PiDDM) read in partial full text.

## 9. Residual risk
- Exa unavailable; OpenReview (ICLR 2027, NeurIPS 2026) not searched; a concurrent conference submission would be invisible.
- PIKAN and PGKAN full texts unread: they may contain a seed-stability check, an operating-condition experiment or an ablation that weakens C2 or C3.
- Eight "closest" works are abstract-only (JECS addd4e, arXiv 2607.16864, Gasper x2, Kuzhiyil, Navidi, Wang RESS, Yang 2025). Read JECS addd4e and arXiv 2607.16864 first; both claim physics-informed trajectory work under varying conditions.
- Absence of a KAN-law identifiability paper is weak evidence; OpenAlex citation lists lag for mid-2026 onwards.
