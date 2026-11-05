# D016 novelty re-check: data-efficiency framing (2026-11-05)

Auditor: novelty-auditor (checks only; no rescue suggestions). Read first: CONTRACT.md, D016 `02_judge.md` (sections 1, 4, 5),
D010 `05_novelty_reaudit.md`, `notes/PRIOR_ART_SCAN_lead.md`, `notes/papers/PRIORART_SUMMARY.md`, `priorart_guo2607.md`.
Reading tags: **FT** full text; **FT-partial** (stated); **AB** abstract only (Crossref/OpenAlex/arXiv/publisher text);
**META** title and metadata only. Citation status: **V** = DOI resolved on Crossref this session; **V-arXiv** = id and title
resolved on arXiv; **unverified** = not resolved.

## 0. Claim restated (falsifiable)

With 8 of 40 cycling conditions and 2 early check-ups per held-out cell, a PINN with a joint calendar-plus-cycle law
(Arrhenius x KAN(SOC) storage term plus a KAN stress map over T, SOC window, DoD, C-rates) forecasts held-out Samsung 50E cycling
conditions with a lower median error than the best tuned data-driven learner; a matched ladder (same network without the law, law
with GAM map, law with KAN map) attributes the gain; learning curves over m = 8/16/32 and k = 0/2/full are reported; and a
closed-form law extracted from the KAN predicts held-out conditions no worse than an equally simplified GAM law.

## 1. Verdicts

| Item | Verdict | Conf. | Closest 3 verified papers |
|---|---|---|---|
| (i) Data-efficiency framing (how few cycling tests and check-ups) | **INCREMENTAL** | 0.70 | Lucu et al., JES 30, 101410 (Part B, cycling) and 101409 (Part A); Jia et al., IEEE TTE 2024; Guo et al., arXiv 2607.16864. Fourth: Stroebl et al., JES 142, 119552 |
| (ii) Ablation attribution of the gain to the physics law (matched ladder, simultaneous intervals) | **INCREMENTAL** | 0.60 | Jia et al. (physics vs no physics, cells needed); Navidi et al., Energy Storage Mater. 2024; Guo et al. (data-efficiency curves, no law ablation) |
| (iii) Closed-form law extracted from KAN vs an equally simplified GAM law, scored on held-out conditions | **NOVEL** | 0.60 | Cui et al., J. Electrochem. Soc. 2025 (symbolic regression vs semi-empirical vs data-driven, calendar); Gasper et al., JES 169 (2022); Ghosh and Roy, arXiv 2604.00400 (KAN closed form, one cell). Koenig and Deng, J. Energy Storage 158 (KAN in Arrhenius law) is the construction precedent |
| (iv) The combination on Samsung 50E | **NOVEL (narrow)** | 0.60 | Lucu Part B (question), PiDDM arXiv 2607.29095 (law), Guo arXiv 2607.16864 (task) |

**Single paper most likely cited against us by a JES reviewer:** Lucu, Martinez-Laserna, Gandiaga et al., *J. Energy Storage* 30,
101410 (2020), doi 10.1016/j.est.2020.101410 (V; AB). Same journal; its stated aim is to "quantify the minimal number of
laboratory tests required for the design of an accurate ageing model"; 124 cycled cells; 26 cells reach 1.04 % MAE on
capacity curves, validated under a wide window of temperature, DoD, mid-SOC and C-rates. Part A (101409, V; AB) does the
same for storage (18 of 32 cells, 0.53 % MAE). Gaussian process, not physics-informed, no ablation, no KAN, not the Samsung data.
This weakens "data efficiency" as a new question; it does not touch the law, the ladder or the KAN-law test.
For the model class the single paper remains PiDDM (D010).

**Why (i) is INCREMENTAL and not TAKEN:** the question "how few ageing tests suffice" has been asked in JES (Lucu 2020), for
physics-guided learning in battery prognostics (Jia 2024: 14 cells with physics against at least 100 without, abstract claim, early-cycle
lifetime, NMC), and for experiment count against parameter information on this very dataset (Stroebl 2026). What was not found
is a learning curve over the number of **cycling ageing conditions** and **early check-ups per held-out cell**, for a **joint calendar +
cycle learned law**, scored on **held-out stress combinations** against **tuned data-driven learners**, on a **designed storage-and-cycling
dataset**.

**Stroebl et al. JES 142, 119552 (lead's point, weighed here).** AB (Crossref abstract; full text pending, saved by lead later):
parameter-individual OED on 279 cells and 71 conditions; calendar temperature-parameter uncertainty cut by 28 %; for cycling OED
"cannot reduce the parameter uncertainty ... explained by its inadequacy". It is the same-dataset, same-group work closest to
"experiment count vs information", so it forces the wording in section 3: ours is forecast error of held-out conditions under a
learned law, theirs is parameter variance of a fixed parametric law. It also gives a published statement that the semi-empirical
cycle model is inadequate on these data, which supports a fair A10 comparison but does not pre-empt our claim. Not a learning-curve
study as far as the abstract shows; read the full text before freeze (judge re-open condition in 02_judge section 8).

## 2. Evidence

### 2.1 Query log (every query run; OpenAlex 429 rate limits cost about half of the planned OpenAlex runs, noted per row)
OpenAlex (2022+ filter): physics-informed battery degradation learning curve number of training cells; PINN battery ageing data
efficiency few training conditions; battery ageing prediction how many cells needed training set size; design of experiments battery
ageing machine learning number of tests reduce; reduce number of cycling tests battery lifetime model machine learning;
Kolmogorov-Arnold network battery degradation symbolic regression closed-form. **Failed on rate limit and not recovered:** few-shot
transfer unseen stress conditions; learning curve battery lifetime prediction training data size; symbolic regression battery
degradation stress factors; GAM lithium-ion ageing (GAM covered by WebSearch only); universal differential equation calendar cycle
(covered by D010); Samsung 50E (covered by D010 `cites:`).
WebSearch: physics-informed ageing learning curve number of conditions; Samsung INR21700-50E + Stroebl + NN/PINN/KAN; KAN calendar
cycle stress-law extraction; how many ageing tests needed unseen conditions; symbolic regression/KAN vs GAM held-out conditions;
PINN cycle ageing few conditions extrapolate JES; Gaussian process / neural additive / EBM battery fade; JES hybrid semi-empirical NN
calendar+cycle; Hallinger SSRN title; Zhang JES 125097 title; JES-Soc 2025 calendar symbolic regression; GAM stress factors;
Lam/Cui/Stroebl Joule; reduced-training-condition NN ageing; Stroebl/Palm ML Samsung 50E; KAN Arrhenius SOC capacity fade; arXiv 2026
data-efficient held-out calendar cycle Arrhenius; ICLR 2027/NeurIPS 2026 battery; PORTAL title; Tao/Zhang cross-operating-condition;
Chalmers Jia page; TU Darmstadt/EES page.
OpenReview (search API, `term` queries): "battery ageing calendar cycle" completed (30 notes); three other queries (battery degradation
physics-informed; capacity fade unseen conditions; Kolmogorov-Arnold battery) **timed out**. The ICLR 2027 venue listing is behind a
challenge (HTTP 403) and could not be listed.
arXiv API/abs pages: 2601.17978, 2601.17983, 2604.01229, 2601.00862, 2511.12053, 2404.04429, 2406.00276, 2604.00400, 2410.14347,
2509.10496, 2410.06422, 2604.09217. Crossref: DOI checks in 2.2.

About 90 hits screened by title/snippet; abstracts read for about 25; **no full text read by me in this check** except Zhang JES 182
(FT-partial, below). Full-text readings already on file (D010, Guo 2607.16864 FT) are relied on as recorded there.

### 2.2 Difference matrix (S same, P partial, D different, relative to the claim; closest works)
Columns: Q = question (data efficiency for held-out conditions); Mech = mechanism (joint calendar+cycle law, stress functions);
Meth = method (PINN/UDE + KAN); Ev = evidence type (designed ageing campaign, held-out conditions); Scale; Res = result.

| # | Work (V = Crossref; depth) | Q | Mech | Meth | Ev | Scale | Res |
|---|---|---|---|---|---|---|---|
| 1 | Lucu et al., JES 30, 101410 and 101409, 10.1016/j.est.2020.101410 / .101409 (V; AB) | S (minimal number of lab tests) | P (GP kernel tailored to ageing; calendar and cycle in two papers; no law) | D (GP, nonparametric) | S (124 cycled, 32 stored cells, held-out validation conditions) | P | 26 cells: 1.04 % MAE (cycling); 18 cells: 0.53 % (storage) |
| 2 | Jia et al., IEEE TTE 10(1), 1056, 2024, 10.1109/tte.2023.3266386 (V; AB via Chalmers page) | P (cells needed for a target lifetime error) | P (electrode-level physics for knee point; cycling only) | P (physics-guided ML) | P (NMC cells, first 50 cycles) | P | 14 cells with physics vs at least 100 without, 2.02 % lifetime error (authors' claim) |
| 3 | Guo et al., arXiv 2607.16864 (V-arXiv; FT per `priorart_guo2607.md`) | P (source-ratio 50-80 %, target 2-10 % curves) | D (cracking+SEI law, no calendar, no Arrhenius) | P (PINN, soft law) | P (unique conditions per cell, about 10 test cells) | D | trajectory MAE about 5 % vs 9-10 % at 2 % early data |
| 4 | Stroebl et al., JES 142, 119552, 10.1016/j.est.2025.119552 (V; AB) | P (experiment count vs parameter information) | S (calendar+cycle semi-empirical, same data) | D (parametric, no learning, OED) | S (same 279 cells, 71 conditions) | S | calendar: 28 % lower parameter uncertainty; cycle: no gain, model inadequate |
| 5 | Navidi et al., Energy Storage Mater. 68, 103343, 2024, 10.1016/j.ensm.2024.103343; arXiv 2404.04429 (V; AB) | P (short-term data, untested conditions, small data) | D (degradation diagnostics, component level) | P (four PIML methods) | P (24 cells, T and C-rate) | D | comparison, no curve over condition count in the abstract |
| 6 | Cui et al., J. Electrochem. Soc. 172, 060521, 2025, 10.1149/1945-7111/adde16 (V; AB) | P (interpolate/extrapolate across storage conditions) | P (calendar only) | P (semi-empirical vs symbolic regression vs data-driven) | P (Lam et al. calendar data, Joule 9, 2025) | P | data-driven model best on unseen cell trajectory |
| 7 | Koenig and Deng, J. Energy Storage 158, 121853, 2026 (V; per PRIORART_SUMMARY) | D | P (KAN in Arrhenius law, SOC) | S (KAN-CRNN) | D (thermal abuse DSC) | D | no error numbers |
| 8 | de Oliveira et al., Energies 14, 5295, 2021, 10.3390/en14175295 (V; AB) | S (how much testing time and data needed) | D | D (linear regression) | P (large accelerated-ageing campaign) | P | similar properties with one fifth of the cells and half the testing time |

### 2.3 Samsung 50E dataset check
Known from D010: no neural/PINN/KAN model on the Stroebl data except those below. **New in this check, and it changes the scope of
any "first" sentence:** Zhang et al., *J. Energy Storage* 182, 125097 (2026), doi 10.1016/j.est.2026.125097 (V), **does** use the
Stroebl Samsung 50E data (ECM-PINN, 1RC, joint SOH estimation and SOC-SOH-dependent ECM parameter inversion; 104 cells, 529 HPPC
diagnostics, cell-level train/test split; reading: **FT-partial**, introduction, data section, split table and grep of the whole file
for data-efficiency, KAN, learning-curve and held-out terms). It does not forecast capacity fade, has no calendar/cycle law,
no KAN model (it cites SOH-KLSTM only) and no data-efficiency analysis. Consequence: a statement "first PINN on this dataset"
is not allowed. Other users of the data: Stroebl JES 142 (above); Hallinger et al., SSRN 7417281 (META: title "Efficient
parameterization of mechanistic calendar aging models: from a priori identifiability to reduced experimental effort"; no abstract
available to me; mechanistic, calendar, "reduced experimental effort" is the same theme; **full text must be read**); Zhong and
Rogge (SSRN 7589132, archive-level, META). The 50E label is shared with Qaadan et al. and Ponce-Alcantara et al. (other data).

### 2.4 Last 90 days (about 2026-08-07 to 2026-11-05)
arXiv listing pages were not browsed; coverage is by search. Items in range that matter: none fits the claim. Seen and judged
not to fit: arXiv 2607.29095 (PiDDM, on file), 2607.16864 (Guo, on file), 2608.14764 (PINN partial-discharge SOH, snippet only,
unread), Zhong and Rogge (Oct 2026), Zhang JES 182 (Oct 2026). OpenReview: one ICLR 2027 desk-rejected submission seen by title,
"PORTAL: A Physically Consistent Retrieval-Augmented Lifetime Model for Early Battery Life Prediction" (unread, unverified; early lifetime
prediction, not a stress-law forecast); "Pretrained Battery Transformer (PBT)" (CoRR 2025, title only). ICLR 2027 and NeurIPS 2026
submissions could not be enumerated, so a concurrent submission cannot be excluded.

### 2.5 What was NOT found (specific questions)
- A learning curve over the number of **cycling ageing conditions** (m) combined with early check-ups per held-out cell (k) for a
  physics-informed battery model: **not found** (nearest: Lucu B by number of cells, Jia by number of cells, Guo by trajectory fraction).
- A matched ladder "same network without law / law + additive-map / law + KAN-map" with held-out-condition intervals: **not found**.
- KAN-extracted closed-form stress law compared with an equally simplified GAM law on held-out conditions: **not found**. No battery
  paper using a GAM as an ageing-law comparator was found by WebSearch; absence is weak evidence (OpenAlex GAM query failed).
- Any KAN or PINN forecast of fade on the Stroebl data: **not found** (Zhang ECM-PINN is parameter inversion).

## 3. "To our knowledge, first": allowed scope

**Allowed only in this form (and only if the pre-submission conditions below hold):**
"To our knowledge, no earlier study has reported learning curves over the number of cycling ageing conditions and early check-ups
per held-out cell for a physics-informed network with a joint calendar-plus-cycle law and Kolmogorov-Arnold stress functions,
attributed the gain by a matched ablation ladder to the physics law, and tested a closed-form law extracted from the KAN against an
equally simplified additive law on held-out conditions of a designed storage-and-cycling dataset."
This is a conjunction of four elements; each element alone is NOT first. Use "we found no earlier study", not "first", in the
abstract; "to our knowledge" belongs in the Introduction contribution list.

**Not allowed (each has a verified counterexample):**
- "first data-efficiency / few-test study of battery ageing" (Lucu 2020 JES, de Oliveira 2021, Jia 2024, Stroebl 2026).
- "first physics-informed model shown to need fewer cells/tests" (Jia 2024 states 14 vs at least 100 cells).
- "first physics-informed or learned-parameter ageing law", "first KAN with Arrhenius-type terms" (PiDDM, Koenig and Deng, PRIORART_SUMMARY).
- "first PINN/physics-informed learning on the Samsung 50E (Stroebl) data" (Zhang JES 182, 125097).
- "first early-data physics-constrained forecast" (Guo 2607.16864).
- "first symbolic or closed-form degradation law" (Gasper 2021/2022, Cui 2025, Schofer 2022).

**Conditions before the sentence is used:** (a) full text of Stroebl JES 142 and Hallinger read and shown not to contain a learning
curve of a learned forecaster; (b) Lucu A/B full text read to confirm they have no physics-informed arm; (c) Jia full text read to confirm the
14-vs-100 claim is a lifetime-from-early-cycles task and not condition-extrapolation; (d) a repeat of the arXiv/OpenReview check within 7 days of
submission, including an ICLR 2027 enumeration that this check could not do.

## 4. Verified JES papers for the introduction (Crossref V this session; reading AB unless noted)

| Paper | DOI | Relevance (one line) |
|---|---|---|
| Lucu et al., JES 30, 101409 (Part A, storage) | 10.1016/j.est.2020.101409 | Minimal number of lab tests for a calendar-ageing model (GP, 18 of 32 cells reach 0.53 % MAE); the JES precedent for the data-efficiency question |
| Lucu et al., JES 30, 101410 (Part B, cycling) | 10.1016/j.est.2020.101410 | Same for cycling (26 of 124 cells, 1.04 % MAE); must be cited and distinguished (no physics law, no ablation) |
| Stroebl et al., JES 142, 119552 | 10.1016/j.est.2025.119552 | OED on this dataset; calendar parameters gain, cycle model inadequate; supports a fair semi-empirical baseline |
| Zhang et al., JES 182, 125097 | 10.1016/j.est.2026.125097 | Physics-informed learning (ECM-PINN) on this dataset; different task (HPPC parameter inversion, FT-partial) |
| Zhao et al., JES 182, 124768 (PGKAN) | 10.1016/j.est.2026.124768 | Physics-guided KAN with symbolic expressions for SOH estimation; the KAN-in-JES precedent we differ from (estimation, not forecast) |
| Koenig and Deng, JES 158, 121853 | 10.1016/j.est.2026.121853 | KAN functions of SOC inside an Arrhenius kinetic law; construction precedent |
| Pepe et al., JES 50, 104209 (2022) | 10.1016/j.est.2022.104209 | Neural ODE + RNN for SOH; a JES neural-ODE precedent (relevance modest; title/abstract only) |

Cite-worthy outside JES (V): Navidi et al., Energy Storage Mater. 68, 103343 (10.1016/j.ensm.2024.103343); Jia et al., IEEE TTE 10 (10.1109/tte.2023.3266386);
Cui et al., J. Electrochem. Soc. 172, 060521 (10.1149/1945-7111/adde16); Gasper et al., J. Electrochem. Soc. 169, 080518 (10.1149/1945-7111/ac86a8);
Zhang et al., Nat. Mach. Intell. 7, 270 (BatLiNet, 10.1038/s42256-024-00972-x); Guo et al., Joule 8, 1820 (few-shot lifetime,
10.1016/j.joule.2024.02.020; title and venue only, abstract not available); Dufek et al., Joule 6, 1363 (calendar ageing and ML perspective,
10.1016/j.joule.2022.06.007; abstract not available); Lam et al., Joule 9 (10.1016/j.joule.2024.11.013); Roman-Ramirez and Marco, Applied Energy 320, 119305 (DoE review,
10.1016/j.apenergy.2022.119305; author list on Crossref has 2 names, check spelling before use); Stroebl et al., Sci. Data 11, 1020 (10.1038/s41597-024-03859-z).
No JES 2025-2026 paper on hybrid calendar+cycle neural ageing models was found; a JES 2024 "semi-empirical model for cycling and short rest" surfaced
only in a search summary and is **unverified** (not listed).

## 5. Residual risk
- Half of the OpenAlex queries and three of four OpenReview queries failed (rate limits and timeouts); search for "few-shot transfer to
  unseen stress conditions" and "symbolic regression battery stress factors" rests on WebSearch and D010.
- No full text read of Lucu A/B, Jia, Navidi, Cui, Stroebl JES 142 or Hallinger: all rows 1, 2, 4, 5, 6 are abstract-level, so the cells
  marked S/P could move. Jia's "14 vs 100" is quoted from the Chalmers repository page of the abstract, not from the article.
- ICLR 2027 and NeurIPS 2026 could not be enumerated; arXiv listing pages not browsed.
- The GAM comparator: absence of a battery GAM ageing law in search results is weak evidence; GAM/EBM as a baseline is trivially
  available to anyone, so (iii) is novel mainly as a test design, not as a method.
- "Kiefer" and "Schmitt" works flagged in D010 remain unlocated.
- Unverified items, not to be cited: Kenney et al. arXiv 2410.06422 (V-arXiv, abstract only, no data-efficiency statement), arXiv 2601.00862,
  2603.10527, 2604.01229, 2608.14764, PORTAL (OpenReview), PBT, the Aalborg thesis (Guo W.), Fraunhofer item, Murgai arXiv 2410.14347.

## 6. Ledger
No ledger name was given in the brief; no rows added.
