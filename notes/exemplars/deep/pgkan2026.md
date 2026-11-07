# PGKAN (Zhao et al., J. Energy Storage 182, 124768, 2026): exemplar dissection

Reading depth: full text (saved extract `refs/fulltext/ft_zhao2026_PGKAN_JES182_124768.txt`: Sec 1-7, Tables 1-9, references) + figures 1-6, 9, 10, 11 viewed as images (`refs/figs/pgkan/gr*.jpg`, Elsevier CDN `_lrg.jpg`); Figs 7 and 8 were not opened individually (same bar-pair form as Figs 6 and 9). NOT read: the 922 KB supplementary PDF (MMC S1: split lists, baseline definitions, per-seed distributions, correlation diagnosis "Appendix IV", symbolic results for XJTU/TJU/MIT) and the abstract text (the saved extract repeats the Highlights; abstract numbers from `notes/exemplars/pgkan_2026.md`). "Paper reports" = E2 for the report only.

## (A) Contribution as stated; list pattern
- Problem: SOH estimators are accurate but not transparent; PINNs use soft physics penalties on black-box networks (Sec 1, paras 4-6); existing KAN SOH papers [32, 33] use KAN for accuracy only (Sec 1, para 7).
- Method: PGKAN = SOH estimator (SOHE, a spline KAN on 16 charging-window features + time, [17,60,32,32,1]) + Degradation Mechanism Surrogate (DMS, a sparse linear regression over a candidate library of terms, Eq 7-8) + degradation-sensing weights (Eq 10) + three extra loss terms (Eq 11-12).
- Four numbered contributions (end of Sec 1), each 3-5 lines: (1) architecture, "ante-hoc explainable" with co-evolutionary training; (2) generalisation on four datasets, and dominant PDE terms "consistent across datasets with identical chemistry"; (3) inference-free spline-based feature importance, "orders of magnitude faster than SHAP", whose top features "align" with the dominant PDE terms; (4) a compact closed-form expression with "comparable performance to neural networks". Unlike PIKAN, items 2-4 each carry a checkable statement.
- Highlights: 4 bullets, the last with numbers ("8.5%-19.7% lower MAPE across four datasets"). Abstract (earlier note): 387 batteries, MAPE reduced 8.5 to 19.7 %, three interpretability claims.
- Headline arithmetic I verified from Tab 3: XJTU 0.0084 vs next best (PINN) 0.0094 = 10.6 %; TJU 0.0127 vs GRU 0.0141 = 9.9 %; HUST 0.0057 vs LSTM 0.0071 = 19.7 %; MIT 0.0059 vs GRU 0.0064 computes to 7.8 % from the printed 4-decimal values, reported 8.5 % (inside the rounding range, but a reader cannot reproduce it). The headline is a relative improvement in MAPE over the best baseline per dataset, i.e. a minimum over five baselines; what the "8.5 %" means for the other baselines is not given.

## (B) Structure
| Section | Content | Approx. words (incl. tables, equations) |
|---|---|---|
| 1 Introduction | batteries/SOH, model-based vs data-driven vs hybrid, PINNs, post-hoc vs ante-hoc XAI, KAN gap, 4 contributions, roadmap (roadmap skips Section 6: says Section 7 for the conclusion) | 1,440 |
| 2 Methodology | SOHE (KAN, Eq 1-5, justification of spline vs Fourier basis), degradation modelling (Eq 6-9), degradation sensing (Eq 10), loss (Eq 11-12), procedure (Fig 2) | 1,630 |
| 3 Datasets and settings | Tab 1, Fig 3, feature extraction (moments, duration, charge, slope, entropy; Eq 13-15), split 4:1 by battery, 10 repeats, Tab 2, metrics | 700 |
| 4.1-4.2 Model evaluation and ablation | Fig 4-5, Tab 3-5 | 1,180 |
| 4.3 Dominant PDE analysis | Tab 6-8, stability of terms over 10 repeats, other regularisers | 1,190 |
| 5 Intrinsic interpretability | variable importance (Fig 6-9), symbolic regression (Fig 10-11, Tab 9) | 2,030 |
| 6 Limitations | three limitations | 180 |
| 7 Conclusion | summary, three limitations again | 310 |
About 8,700 words; 11 figures, 9 tables, 50 references; supplementary PDF. Order: model, data, accuracy, cost (Tab 4), ablation, PDE, interpretability, limitations, conclusion. This is the clearest "accuracy then interpretation then limitations" template of the three papers. No Data/Code availability statement in the saved text (earlier note: GitHub USTC-AI4EEE/PGKAN announced, not checked).

## (C) Every figure
| Fig | Form | Encodings | Claim | Quality | What we would do better |
|---|---|---|---|---|---|
| 1 | KAN stack with spline glyph per edge; bottom: phi(x) = w b(x) + s spline(x) with three curves | monochrome blue arrows | architecture of SOHE | clear, light, but the three curves in the decomposition are an illustration not data | show a real learned phi with its basis terms (cf. KA-CRNN Fig B.1) |
| 2 | 4-stage flowchart with right-hand chevrons (preprocess / train / evaluate and PDE discovery / explain); SOHE (pink) and DMS (blue) boxes, degradation sensing (magenta), loss boxes; final panel carries the HUST PDE and the closed-form expression | colour per module | whole pipeline and the final deliverables | very informative; one inconsistency: the figure prints L_data as a sum of absolute errors, Eq 12 squares them | keep "pipeline ending in the deliverables" and make the equations in figure and text identical |
| 3 | 4 panels capacity vs cycle: XJTU legend by protocol (2C, 3C, R2.5, R3, RW, satellite), TJU by chemistry (NCA, NCM, NCM+NCA), HUST single colour, MIT by production date | categorical colours | distribution shift between and within datasets | better than PIKAN Fig 1 because legend names the condition; thin lines overplot; HUST/MIT panel order differs from Tab 1 | add condition axes (T, SOC, C-rate), mark held-out conditions |
| 4 | 2 x 2 parity scatter, colour = absolute error (0-0.10, blue to red) | continuous colour | accuracy; "within 5 % for the majority" | readable; TJU shows a red off-diagonal arm (error above 0.06) and scattered outliers; no per-cell breakdown | residual vs time per held-out unit |
| 5 | 4 panels (datasets); inside each, three metric groups (MAE, MAPE, RMSE) x six violins (PGKAN, PINN, LSTM, GRU, MLP, CNN); red mean, black mean +/- std, 10 dots each | pastel categorical | stability: PGKAN lowest and narrowest | best-organised distribution figure of the three papers (metrics grouped, same colours throughout); y-axes are truncated per panel (e.g. 0.60 to 1.20 %), violins hide n = 10; no paired information | paired differences per seed/unit with CI; keep the metric grouping |
| 6-9 | Horizontal bar pairs: SHAP importance (dark blue) vs spline importance (light blue), 16 variables sorted by SHAP, each normalised to max = 1; bold labels = variables that appear in the discovered PDE; MIT, HUST, XJTU, TJU | two blues, bold text | spline importance agrees with SHAP and with the PDE terms | clear; but the middle of the ranking differs (Fig 9: voltage skewness is 7th in SHAP, 4th in spline; Fig 6: voltage kurtosis is 2nd in SHAP, 6th in spline); no error bars though 10 repeats exist; no rank correlation | print Spearman rho with a bootstrap CI and a permutation null; show the 10-run spread as whiskers |
| 10 | pruning and symbolisation pipeline (three small KAN diagrams) + library chips (x, x^2..x^4, 1/x.., sqrt, abs, exp, log, sin, tan, tanh, arcsin, arctan, sgn, arctanh, gauss, cosh) | blue arrows, orange library | process | library includes tan and 1/x, singular within range | restrict library to bounded, monotone forms for stress laws and say so |
| 11 | one HUST cell ("HUST 2-8"): SOH vs cycle, ground truth, PGKAN, PINN, LSTM, GRU, "Expression"; inset zoom at SOH 0.8 +/- 50 cycles | line colours | expression is as good as models near end of life | persuasive by eye, but one cell; the expression is visibly offset from truth in the zoom (about 0.005) | show a median and worst held-out unit, not the cell that looks best |
Style note: all colours are default matplotlib pastels; PGKAN is shown in light blue in Fig 5 (same pastel family as the baselines).

## (D) Every table
| Tab | Content | What it proves |
|---|---|---|
| 1 | dataset, "distinction" (aging strategy / cathode composition / production date), batch, composition, capacity, voltage, temperature, quantity (55 + 130 + 125 + 77 = 387) | coverage; XJTU = NCM, TJU = mixed NCM/NCA, MIT/HUST = LFP |
| 2 | hyperparameters per dataset: batch 256/512/512/512, early stop 20/20/10/20, lr 0.01, SOHE [17,60,32,32,1], alpha 0.7/2.0/1.0/1.0, beta 0.2/0.5/0.05/1.0, xi 1e-6, gamma, eta* | reproducible settings (same architecture and lr for all datasets) |
| 3 | six models x four datasets x (MAE, MAPE, RMSE), single means, PGKAN first row | PGKAN best in all 12 columns |
| 4 | inference cost: parameters, FLOPs, latency (microseconds), throughput; PGKAN 39,960 / 71,928 / 1604.8 / 289,391 vs PINN and MLP 7,781 / 15,192 / about 143 / about 3.6 million | honest cost: about 11 x the latency of MLP; 5 x the parameters |
| 5 | ablation: PGKAN, w/o DS, w/o L_deg, w/o L_dir, 4 datasets x 3 metrics | every removal worsens; e.g. XJTU MAPE 0.0084 -> 0.0085 / 0.0090 / 0.0091 |
| 6 | PDE expressions per dataset (3 terms with coefficients) | the "dominant PDEs"; XJTU 0.445 du/d(CV time) - 0.199 du/d(current slope) + 0.165 u du/d(CV time); HUST 0.134 du/d(CC charge) + 0.124 du/d(voltage entropy) + 0.103 du/d(voltage skewness) |
| 7 | how often each of the top-3 terms is "significant" (> 30 % of the largest |coefficient|) in 10 repeats: XJTU 6/4/3, TJU 5/3/0, MIT 10/5/2, HUST 6/2/2 | stability of the discovered terms (a strength) and its limit (below) |
| 8 | top-3 terms by L1 vs ElasticNet vs MLP-based sparse regression | cross-method agreement on rank 1 for XJTU, TJU, MIT; HUST rank 1 differs (Delta Q_C, t, H_V) |
| 9 | HUST SOHE structures: [17,60,32,32,1] 0.0064 MAPE (RMSE 0.0077); [17,2,1] 0.0075 (0.0085); [2,60,32,32,1] 0.0084 (0.0101); [2,2,1] 0.0084 (0.0099); expression (17) 0.0091 (0.0109) | expression is close to the 2-input model |
Layout: plain horizontal-rule tables, 4 decimals, no bold marking, no SD.

## (E) Evaluation
- Task: estimation of SOH from per-cycle charging features plus time t, as in PIKAN (not forecasting).
- Split: about 4:1 train:test "within each batch/dataset ... performed based on different batteries" (Sec 3.2): cell-level split stated explicitly (a plus over PIKAN). Number of test cells per dataset is in the supplement (not read). alpha and beta chosen "on the validation set" (Sec 3.3).
- Baselines: MLP, CNN [from ref 32], LSTM, GRU, PINN [Wang]. No plain KAN baseline and no ablation without the physics terms altogether (rows are w/o DS, w/o L_deg, w/o L_dir only), so the gain cannot be assigned to KAN vs physics vs the sensing weights. "Structural complexity at least comparable" (Sec 4.1) conflicts with Tab 4 (PINN/MLP have 7,781 parameters, PGKAN 39,960).
- Metrics: MAE, MAPE, RMSE; 10 repeats; seeds vs resplits not stated.
- Statistics: none beyond violins (Fig 5) and means (Tab 3, 5). No paired tests, no CIs, no multiplicity control. Ablation differences in Tab 5 are 0.0001 to 0.0012 in MAPE (e.g. w/o DS on MIT 0.0059 -> 0.0060; w/o L_dir on HUST 0.0057 -> 0.0069) and cannot be judged without SDs (supplement Section III has the distributions).
- Internal inconsistency: PGKAN HUST MAPE is 0.0057 in Tab 3 and Tab 5, but the same architecture [17,60,32,32,1] has 0.0064 in Tab 9 (RMSE 0.0077 vs 0.0069); the text does not say what differs.
- Best practice found: the xi sweep (7 values, plateau 5e-7 to 5e-6 where the dominant terms do not change; Sec 3.3) and the 10-repeat term-frequency table (Tab 7).

## (F) The "discovered law" claim and its evidence
Two separate claims.
1. DMS "dominant PDE" (Sec 4.3): a linear combination of library terms {1, u, x_i, du/dx_i, u du/dx_i, u^2 du/dx_i, ...} fitted with an L1 penalty on the network's own derivatives (e_i = u_t - G(...)); term ranking by mean coefficient over 10 repeats; "significant" = |lambda| > 30 % of the max in a run.
   - Evidence for: Tab 7 (rank-1 term significant in 5 to 10 of 10 repeats), Tab 8 (ElasticNet and MLP regression agree on rank 1 for three datasets), xi plateau.
   - Evidence against / weaknesses: rank 1 is significant in only 5/10 (TJU), 6/10 (XJTU, HUST) repeats; the TJU rank-3 term (0.059 u^2 t) is significant in 0 of 10 repeats yet is printed in Tab 6 as part of the law; the 30 % threshold is arbitrary; averaging coefficients over repeats mixes runs; no stability across data splits or folds (only repeats); no null/permutation test; features are min-max normalised, so lambda are not physical rates; the terms du/dx_i are derivatives of the same trained network that produces u, so the "PDE" mostly summarises that network's own sensitivities; no GAM/spline/polynomial baseline for the same relationship.
   - Text is careful in one place (Sec 4.3, para 2): "library-constrained surrogate", not a governing equation. Still, the abstract and highlights say "reveals the dominant degradation PDEs".
   - Physical story (Sec 4.3): constant-voltage time is "a proxy for cumulative exposure to a high-voltage aging window". A reviewer will note that CV duration itself lengthens as the cell ages (it is an effect of degradation), so reverse causation is not excluded; no test.
2. Alignment of spline importance with the PDE terms (Sec 5.1, contribution 3). Visually (Figs 6, 9) the bold PDE variables sit in the top four of at least one of the two rankings (MIT voltage kurtosis is 2nd in SHAP but 6th in spline; TJU CV charge time is 4th in SHAP, 5th in spline), but the top-1 variable on XJTU and TJU ("current entropy") is not in the PDE at all. With 16 features and 3 PDE terms, a top-4 overlap of 2 has no stated null probability. No correlation statistic is reported between SHAP and spline rankings, only "same top and bottom variables".
3. Closed form for SOHE (Sec 5.2, Eq 17): HUST only in the main text, inputs voltage entropy and time step, two-layer KAN, library functions cosh, tan, sin, arctan; R2 = 0.98 (lower than PIKAN's 0.996-0.9996). Tab 9: expression RMSE 0.0109; Tab 3 baselines on HUST have RMSE 0.0083 to 0.0090 (PINN 0.0087, MLP 0.0090, CNN 0.0087, GRU 0.0085, LSTM 0.0083). So the closed form is worse than every baseline in Tab 3 on the same dataset, which contradicts contribution (4) "comparable performance to neural networks" unless read as "comparable to the two-input model". tan(...) terms are unbounded; extrapolation behaviour is not examined. Results for XJTU, TJU, MIT are only in the supplement.

## (G) Limitations and negative results
Dedicated Sec 6 (three items, about 180 words): library-constrained PDE; needs near-complete charging segments; compute cost grows with width/depth/library. Conclusion repeats them. Negative-ish results kept in the text: PGKAN is 11 x slower than MLP (Tab 4); HUST top-1 term differs by regulariser (Tab 8); ElasticNet adds spurious t and u^2 t^2 terms on HUST (Sec 4.3); the sparsity profile is flatter on HUST (Sec 5.1). Not stated: the 0/10 significance of the TJU rank-3 term is shown in Tab 7 but not discussed; symbolic regression results for three datasets are hidden in the supplement.

## (H) Data and code availability
Four public datasets with citations; supplementary PDF; no explicit Data/Code availability statement in the saved text; earlier note records an announced GitHub repository (not verified here). Hardware: 4 x RTX 4090D, dual Xeon (Sec 3.3).

## (I) What a hostile reviewer would attack
1. Estimation, not forecasting; features from the same cycle plus time; no unseen stress.
2. No test of any claim, no SD, no CI; ablation effects as small as 0.0001 in MAPE.
3. No KAN-only baseline and no "no physics" row, so "physics-guided KAN" is not isolated; MLP/PINN baselines have 5 x fewer parameters than the claimed "at least comparable".
4. The discovered PDE is derived from the network's own derivatives, features are normalised, terms are significant in only half the runs; the 3rd TJU term is never significant.
5. The closed-form law is worse than all baselines (Tab 9 vs Tab 3) and uses tan/cosh.
6. Table 3/5 vs Table 9 mismatch for the same architecture.
7. Importance "alignment" is eyeballed, with no rank statistic and no null.
8. CV-time interpretation is reverse-causal.

## (J) Lessons for our paper
1. [TAB] Report an inference-cost table (parameters, FLOPs, latency); admit the overhead as they do (Tab 4). Our KAN stress-function model is small; show it.
2. [FIG] Name the experimental condition in legends (their Fig 3 does, PIKAN's does not), and use conditions on both axes of our design map.
3. [ANALYSIS-EXPLORATORY] Copy the term-frequency table (Tab 7) but over folds and seeds, with an explicit pre-stated significance rule, and report even the terms that fail (their TJU rank-3: 0/10).
4. [ANALYSIS-EXPLORATORY] Copy Tab 8 (law re-identified by different regularisers) with our own pair: A15 closed forms vs a GAM (G15) vs a polynomial in the same inputs; pre-register agreement criteria.
5. [TAB] Ablation must contain the row "no physics at all" and a "same backbone, MLP" row; PGKAN lacks both. Also state parameters of each arm.
6. [FIG] Keep their metric-grouped violin idea but add a paired-difference panel with CI; do not truncate the axis without saying so.
7. [FIG] Pair importance bars with whiskers from repeats and print a rank correlation with a permutation null (their Figs 6-9 show visible rank disagreement and report none).
8. [TEXT] Use their Sec 4.3 disclaimer language ("library-constrained surrogate ... not a governing equation") and a short Limitations section; make the abstract match that language.
9. [TAB] Report the symbolic form vs the neural model vs every baseline on identical held-out units in one table; if the closed form is worse than a baseline (their Tab 9 vs Tab 3), say so.
10. [TEXT] Keep one results ledger: PGKAN HUST MAPE is 0.0057 in Tab 3/5 and 0.0064 in Tab 9, and the L_data form differs between Fig 2 and Eq 12; such mismatches are what a referee quotes.
