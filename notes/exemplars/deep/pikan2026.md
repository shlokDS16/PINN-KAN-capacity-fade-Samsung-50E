# PIKAN (Liu et al., J. Energy Storage 153, 120860, 2026): exemplar dissection

Reading depth: full text (saved ScienceDirect extract `refs/fulltext/ft_liu2026_PIKAN_JES153_120860.txt`, all sections, Tables 1-8, reference list) + all 10 main figures viewed as images (`refs/figs/pikan/gr1..gr10.jpg`, Elsevier CDN `_lrg.jpg`). NOT read: the 727 KB supplementary Word file (Notes 1-9: feature definitions, split, alpha/beta grid, baselines, Verhulst prior); the abstract text itself (the saved extract duplicates the Highlights under "ABSTRACT"; abstract numbers below come from `notes/exemplars/pikan_2026.md`). "Paper reports" = E2 for the report only. Location tags: Sec = section, Fig/Tab = display item.

## (A) Contribution as stated, and the list pattern
- Problem framed as three unresolved challenges (Sec 1, para 5): (1) data-driven models are flexible but weak on small samples, physical consistency and transparency; (2) PINNs gain consistency but stay black-box; (3) post-hoc explanation (SHAP, attention) says which features matter, not how they combine.
- Solution = one named framework, two KAN modules (SHEM: state-of-health estimator u = F(x,t); DDMM: degradation dynamics du/dt = G(x,t,u,u_x)) coupled by a residual loss, plus symbolic regression on both (Sec 3, Eq 8-12).
- Contribution list (end of Sec 1) has FOUR numbered items: (1) framework "unifying physical constraints, data fitting and symbolic analysis for the first time"; (2) "symbiotic co-evolution" mechanism (self-regularisation, bidirectional interaction); (3) symbolic regression "explicitly reveals" nonlinear relationships; (4) superiority on four public datasets in accuracy, stability, small-sample and transfer. Items 1-3 are method/novelty claims, only item 4 is empirical; there is no item that states a falsifiable quantitative result. The roadmap sentence follows immediately.
- Highlights: 4 bullets (Sec Highlights): proposes PIKAN; co-evolution mechanism; symbolic-regression logic; "superior accuracy and stability on four datasets, excelling in small-sample and transfer scenarios". No numbers in the highlights. (Abstract numbers: max 63.4 % RMSE reduction in small-sample scenarios, per earlier note; I re-derived it, see (E).)
- Pattern worth copying: three challenges -> three-way coupling -> evidence in four scenarios (conventional, small-sample, transfer) -> interpretability. Pattern not to copy: all novelty items are architectural labels; a JES reviewer cannot test them.

## (B) Structure
| Section | Content | Approx. words (incl. tables, equations, captions) |
|---|---|---|
| 1 Introduction | model-based vs data-driven, PINNs, post-hoc XAI, three challenges, four contributions, roadmap | 1,540 |
| 2 Datasets | Tab 1, Fig 1, 17 features (16 charging-window indicators + cycle index), preprocessing | 860 |
| 3 Methodology | KAN, SHEM, DDMM, fusion (loss Eq 9-12), symbolic regression, procedure (Figs 2-4) | 2,300 |
| 4.1 Settings and metrics | Tab 2, MAPE, RMSE | 430 |
| 4.2 Performance | conventional (Tab 3-4), small-sample (Tab 5), transfer (Tab 6) | 2,250 |
| 4.3-4.4 Interpretability + discussion | PIKAN* simplification (Tab 7), direct symbolisation (Tab 8, Fig 8-9), Verhulst-guided (Fig 10), engineering translation, transferability | 2,075 |
| 5 Conclusion | four numbered conclusions, future work | 540 |
Total body about 10,000 words. 10 figures, 8 tables, 45 references, no separate Limitations section (limits appear only as future work and in 4.4.2). No Data/Code availability statement in the saved text (earlier note: GitHub USTC-AI4EEE/PIKAN exists, no licence). Supplementary Note 1-9 holds splits, baselines, grid search, Verhulst details.
- Abstract/section pattern: problem (3 challenges) -> method (2 modules + coupling) -> headline accuracy number -> interpretability claim -> transferability claim.
- Results order: conventional -> ablation of loss terms -> small-sample -> transfer -> interpretability -> engineering discussion. This order (accuracy first, interpretability last, discussion of deployment) is the one JES reviewers have accepted.

## (C) Every figure
| Fig | Form and panels | Encoding | Claim supported | Quality | What we would do better |
|---|---|---|---|---|---|
| 1 | 4 panels (a-d) capacity (Ah) vs cycle for XJTU, TJU, MIT, HUST; one line per cell | XJTU/TJU colour = batch (legend "batch 1-6"); MIT/HUST colour = total cycles (sequential colourbar, yellow-magenta, green-blue) | aging trajectories differ by protocol/chemistry (Sec 2.1) | legible, large fonts; heavy overplot (XJTU batch 3 in pale yellow is occluded); legend uses batch numbers, so the stress that defines each batch is only in the text; colour scales not colour-blind-safe | colour/label by the actual stress condition (T, SOC, C-rate), Okabe-Ito, mark held-out conditions, panel per condition family |
| 2 | (a) two KAN stacks (SHEM, DDMM) drawn with spline glyphs per edge, coloured layer bands, loss equation in a bar; (b) pruning to symbolisation pipeline with a symbolic-library strip | colour per layer, red = symbolised | architecture and loss | very dense but readable; the loss is typeset inside the figure, so it duplicates Eq 9-12 | one schematic that shows real data panels feeding the model and the held-out split, not only the network |
| 3 | flowchart of the symbolic-regression loop (data -> library -> train -> plot and prune -> "Manually Stop" diamond -> suggest symbolic per edge -> retrain affine parameters -> formula) | orange decision diamond | process of Sec 3.5 | clear, but it shows that pruning and stopping are manual | automate and log every manual decision, or do not draw the human in the loop as if it were an algorithm |
| 4 | tall 4-step chevron figure (dataset construction; model training with an alpha-beta RMSE heat map; evaluation with a scatter, a violin and a small-sample violin; interpretability with the symbolic formulas) | one colour per stage | whole workflow; the heat map shows RMSE for alpha, beta in {0.001..1000}^2, minimum 0.0041 in several cells | good summary figure; the heat map is the only place the tuning landscape is shown, and it does not say which split it was evaluated on | keep this "graphical abstract with real results" idea; state the split of any tuning plot |
| 5 | 11 small multiples (parity scatter, true vs estimated SOH), one per dataset/batch, diagonal in red dashed; colour = absolute error (0 to 0.10 diverging blue-red); shared colourbar | colour = error | accuracy and absence of outliers | clean; but a pooled parity plot hides per-cell errors; XJTU batch 2 and 5 show systematic S-shaped bias (visible), TJU batch 2 shows a displaced second cloud, MIT has isolated dark-red outliers | per-cell error bars, or one panel per held-out condition with residual vs time |
| 6 | 11 violin plots (RMSE in %), one panel per dataset/batch, six methods (PIKAN, KAN, PINN, Transformer, MLP, CNN); red line = mean, black bar = mean +/- std; 10 dots per violin | pastel fill per method; PIKAN legend swatch is grey and PIKAN's violin is nearly a line | seed stability: PIKAN narrowest | the best method is the least visible (violins collapse to a line); "(%)" label collides with tick labels in some panels; KDE violins extend below zero for KAN on XJTU batch 5; 10 points per violin only measure seed variance, not test-unit variance | forest plot of paired differences with CI; show the 10 points, not KDE |
| 7 | 2 panels (XJTU batch 1, HUST): violin per method, grouped by number of training batteries (1-4, light to dark cyan) | sequential cyan = training size | small-sample learning curve | the learning-curve idea is right (error vs number of training units); y-axes differ by 3x between panels; PIKAN again collapses to the baseline | plot mean +/- band against m on a log axis, one line per method (this is our learning-curve figure) |
| 8 | 4 panels: pruned KAN graphs for SHEM and DDMM on XJTU batch 1 and TJU batch 3 (pykan style; edge opacity = importance) | red edges, spline glyphs | which inputs matter | shows that in DDMM u_x is pruned away on both datasets; pykan glyphs are tiny | show the learned univariate curves large, with axes, not as thumbnails |
| 9 | (a,b) SOH vs sample index, real vs PIKAN* vs symbolic, two cells concatenated (visible jump); (c) bar chart of MAPE and RMSE before/after symbolisation | green/blue/red lines; four bar colours | symbolic formula reproduces the model | the x-axis is "sample index" so two test cells are fused; (c) shows RMSE rising from 0.40 to 0.50 % (XJTU b1) and from 0.58 to 0.62 % (TJU b3), a visible degradation the text calls "very close" | report the symbolic penalty with a CI and per held-out unit |
| 10 | two stacked 5-column panels (XJTU b1, TJU b3): train, prune, retrain, symbolic regression, formula; MAPE/RMSE printed under each stage; red equations with coefficient matching | stage columns | prior-guided symbolisation recovers Verhulst | most informative figure; it also exposes problems (see F, I): TJU stage 2 error 0.1182 RMSE after pruning; XJTU b1 gives r = -0.9829, C = -2.2171, K = 0.9882; TJU b3 gives r = -0.2072, C = 0.0366, K = 7.6789 | the same layout is a good template for our "extraction audit" figure, but with parameter values in physical units and fold-wise distributions |

## (D) Every table
| Tab | Content, layout | What it proves |
|---|---|---|
| 1 | dataset, batch, chemistry, nominal capacity, cut-off voltage, temperature, number of cells (55 + 66/55/9 + 125 + 77 = 387) | data coverage; no stress-condition columns beyond temperature |
| 2 | hyperparameters (SHEM [17,60,60,32,32,1], DDMM [34,60,60,1], alpha and beta in {1e-3..1e3}, 10 repeats, early stop 20) | reproducibility; one row, same for all four datasets |
| 3 | 11 test units (6 XJTU batches, 3 TJU batches, MIT, HUST) x 6 models x (MAPE, RMSE), single numbers; PIKAN lowest in every cell | "lowest error across all datasets"; no SD, no test |
| 4 | ablation, two datasets (XJTU batch 1, HUST): full, w/o L_Phys, w/o L_Cons, both | both loss terms help (HUST MAPE 0.0057 -> 0.0088 with neither, RMSE 0.0066 -> 0.0103) |
| 5 | small-sample: 1-4 training batteries, XJTU b1 and HUST, 6 models | headline 63.4 % reduction is PINN vs PIKAN at 1 training battery on HUST (RMSE 0.0339 -> 0.0124, I recomputed 63.4 %) |
| 6 | pairwise transfer 4 x 4 (few-shot after fine-tuning on the first target cell, zero-shot), PINN vs PIKAN only, RMSE | PIKAN wins 9/12 (few-shot) and 8/12 (zero-shot) (I recounted both); orientation of rows vs columns is stated inconsistently with the worked examples in the text |
| 7 | original PIKAN (75,960 parameters, RMSE 0.0040 / 0.0051) vs simplified PIKAN* ([2,4,1] and [4,2,1], 120 parameters, 0.0041 / 0.0052) | two inputs (charging time, cycle index) suffice on these batches |
| 8 | symbolic formulas and R2 for SHEM and DDMM, two datasets | R2 0.9959-0.9996 for symbolic vs the PIKAN* model |
All tables report seed-averaged means; none reports SD, CI or p-values. Tables are plain, 4-decimal fractions (e.g. 0.0031), no best-bold marking.

## (E) Evaluation
- Task: estimation (SOH of cycle k from features of cycle k plus the cycle index as an input), not forecasting. 17 inputs per sample; cycle index is the 17th feature (Sec 2.2).
- Split: 6:2:2 train/validation/test (Sec 3.6 Step 1, Fig 4). Whether the split unit is a cell or a cycle is NOT stated in the main text (Supplementary Note 5). Fig 9 shows a test series that has one discontinuity (appears to be two concatenated cells), which suggests cell-level splitting for at least XJTU batch 1; this is an inference from the figure, not stated.
- Test units: XJTU 6 batches, TJU 3 batches, MIT 1, HUST 1 (Tab 3). Number of test cells per row unknown (about 20 % of each batch).
- Baselines: KAN (data loss only), PINN (Wang et al. [29], MLP backbone), MLP, CNN, Transformer. Layers/neurons "kept consistent" for comparable scale (Sec 4.2). A KAN-only baseline is present (strength, and a different attribution than PGKAN gives).
- Metrics: MAPE, RMSE (as fractions in the tables, % in text and Fig 6).
- Seeds/statistics: 10 repeats, mean in tables, violin per method (Fig 6, 7). No paired test, no CI on the difference, no multiplicity control, no standard deviation in any table. Claims such as "best stability" rest on violin width only.
- Headline numbers I verified from the tables: mean RMSE over the batches 0.76 / 0.89 / 0.69 / 0.66 % (XJTU six batches 0.0040, 0.0096, 0.0082, 0.0070, 0.0102, 0.0068 average 0.00763; TJU 0.0097, 0.0120, 0.0051 average 0.00893) (Tab 3); small-sample 63.4 % = HUST, 1 training battery (Tab 5); transfer counts as above (Tab 6).
- Tuning: alpha, beta by grid search over 7 x 7 values (Sec 4.1, Tab 2, Fig 4) "to reduce impact on the results of 10 repeated experiments"; the split on which the grid was scored is not stated in the main text. The earlier code note (notes/code/PIKAN.md) found test-set selection in the released code; not re-verified here. Baseline tuning is not described in the main text.
- Transfer: zero-shot RMSE for PIKAN ranges 0.0246-0.1988 (Tab 6) i.e. 2.5-20 % SOH error; the paper calls this "excellent cross-dataset generalization".

## (F) How the symbolic / "discovered law" claim is made, and strength of evidence
1. Direct symbolisation (Sec 4.3.1): simplify to PIKAN* ([2,4,1] SHEM with inputs charging time and cycle index; [4,2,1] DDMM), prune by edge opacity (manual), fit each edge from a library (Fig 2b: x, sqrt, 1/x, abs, arccos, arcsin, arctan, arctanh, exp, log, relu, softmax, sin, cos, tan, sigmoid, bessel, erf, sinc, gaussian...), retrain affine parameters. Result (Tab 8): nested cosh/arcsinh/sinh/sinc/erf/bessel expressions, R2 >= 0.99.
2. Prior-guided (Sec 4.3.2, Fig 10): DDMM restricted to input u only, activations only x and x^2, architecture [1,2,1], pick "the lowest complexity among top N" by hand. Output: du/dt = a(bu+d)^2 + e, matched to the improved Verhulst form r(u-C)(1-(u-C)/(K-C)) by coefficient matching.
Strength of evidence (low):
- The restricted form (any quadratic in u) maps onto Verhulst parameters by algebra, so recovering a Verhulst equation is a consequence of the restriction, not a discovery. There is no test that a non-quadratic form fits worse.
- Parameter values are non-physical: XJTU batch 1 gives C = -2.2171 (an SOH asymptote below zero) and TJU batch 3 gives K = 7.6789 (an upper bound on SOH near 768 %) (Fig 10); the text still calls this "deep correlation with known physical models". The text also labels r, C, K as "degradation constant, initial SOH loss, SOH loss upper limit", which contradicts Eq 15's definitions.
- No stability across seeds, folds or batches: one symbolic fit per dataset is shown. The same dataset (XJTU batch 1) has three different SHEM formulas in the paper (Tab 8 cosh form; Fig 10a long sinh/bessel/sigmoid form; Fig 4 inset a third cosh/sinc form); the text does not say these come from different runs, but they do differ, which in itself is evidence of non-uniqueness. The authors concede (Sec 4.4.2) that formulas for XJTU b1 vs TJU b3 are "fundamentally different" and cannot be transferred.
- Faithfulness: symbolic vs model error rises from RMSE 0.40 to 0.50 % (XJTU b1) and 0.58 to 0.62 % (TJU b3) (Fig 9c); Fig 10 stage values differ again from Tab 7 and Fig 9c (e.g. TJU b3 RMSE 0.0065 at stage 1, 0.0071 after symbolisation; Tab 7 gives 0.0052 for PIKAN*), unexplained.
- R2 >= 0.99 (Tab 8) is a fit to the model output or to the data (not stated), on training samples (not stated).
- No GAM, spline or polynomial baseline for the same two-input mapping; Tab 7 itself shows that a 120-parameter two-input KAN equals the 75,960-parameter model, which says the mapping is trivially smooth (charging time vs cycle), so a symbolic fit is easy and uninformative.
- Engineering "knowledge" in Sec 4.4.1 (hyperbolic sinusoidal coupling means accelerated ageing late in life) is read off one fitted expression; no test.

## (G) Limitations and negative results
- No limitations section. Stated in 4.4.2: unconstrained symbolic formulas are dataset-specific (not transferable); SHEM formulas stay non-transferable even with Verhulst guidance. Future work: separate transferable from non-transferable terms; cross-temperature transfer.
- Visible but unremarked in the figures: S-shaped bias for XJTU batches 2 and 5 (Fig 5); PIKAN worse than PINN in 3/12 few-shot and 4/12 zero-shot transfers (Tab 6); PIKAN ties KAN on MIT (0.0060 MAPE both, Tab 3); small-sample errors are non-monotone in training size (acknowledged in 4.2.2, explained as distribution shift).

## (H) Data and code availability
Public datasets only (XJTU, TJU, MIT, HUST, with citations); no data/code availability statement in the saved text; supplementary Word file with notes. Earlier code note records the GitHub repository (no licence file).

## (I) What a hostile reviewer would attack
1. "Estimation" with the cycle index as an input and charging-window features of the same cycle: the model can read the label's neighbour, not forecast.
2. No test of any claim: 10 seeds, no paired test, no CI; the 63.4 % headline is a single best cell (HUST, one training battery).
3. Tuning split unspecified in the main text; baseline tuning undocumented, so "PIKAN beats PINN by 63.4 %" cannot be separated from unequal tuning effort (the earlier code note reports test-set selection for the released code).
4. The "discovery" is circular (restricted library = Verhulst) and the recovered constants are unphysical (C = -2.22, K = 7.68).
5. Three different symbolic formulas for the same dataset; manual pruning and stopping (Fig 3).
6. Unit of evaluation unclear; transfer errors 2.5-20 % are called excellent.
7. Novelty is the combination PINN + KAN; PGKAN (same group) appears the same year.

## (J) Lessons for our paper
1. [TEXT] Keep the problem -> three challenges -> numbered contributions -> roadmap shape, but make every contribution a falsifiable, numbered claim with its test named (PIKAN's items 1-3 cannot be falsified).
2. [FIG] Reuse the "workflow with real results" tall figure (Fig 4): one graphical abstract carrying the real learning curve and the real stress-function panel; add the held-out split drawn explicitly.
3. [FIG] Small-sample learning curve vs number of training units (their Fig 7) is the right idea; ours is m (conditions) and k (check-ups); plot a line and a band per method, not violins that hide the best method.
4. [TAB] Put the headline in a table with mean +/- SD over seeds, paired p (Holm) and the number of held-out units; PIKAN's Tab 3 has none of these.
5. [TAB] Include a tiny-model ablation like their Tab 7 (120-parameter model equals the 75,960-parameter one): if a 2-input model matches ours, say so, and show where ours beats it (held-out conditions).
6. [FIG] Do not show interpretability as thumbnails; show the learned univariate stress functions large, with seed or fold bands and a GAM overlay (their Fig 8 is too small to read).
7. [ANALYSIS-EXPLORATORY] Report every extracted-law parameter in physical units and check bounds before interpreting; their C = -2.2171 and K = 7.6789 show what happens if you do not (our A15 vs G15 comparison must include coefficient stability across folds and a plausibility check, plus the symbolic-vs-model penalty with a CI).
8. [ANALYSIS-EXPLORATORY] Show that a restricted library recovers a known form only if the unrestricted fit prefers it; run the synthetic recovery of a known law with noise before claiming discovery.
9. [TEXT] Add a Limitations subsection (they have none); state split unit, number of held-out units and tuning split in the main text, not the supplement.
10. [FIG] Fix their Fig 6 failure: colour so the proposed method is the most visible, no KDE tails below zero, no axis-label collisions, and condition labels instead of batch numbers (Fig 1).
