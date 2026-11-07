# Batch R3 summary: PIKAN, PGKAN, KA-CRNN (JES 2026), 2026-11-06
Files: `pikan2026.md`, `pgkan2026.md`, `kacrnn2026.md` (same folder). Figures: `refs/figs/{pikan,pgkan,kacrnn}/` (Elsevier CDN, all downloaded and the key ones viewed). Reading: full text of all three; supplements NOT read (PIKAN Word file, PGKAN PDF, KA-CRNN CSVs).

## What makes them publishable in JES (common pattern)
1. A named framework with a 3-4 item contribution list and a tall "pipeline" figure (PIKAN Fig 4, PGKAN Fig 2, KA-CRNN Fig 1). KA-CRNN has no list but a mechanism-first story (about 60 % of words before any result).
2. Accuracy table on 11-ish test units vs 5 baselines, violin of 10 seeds, loss-term ablation, then an interpretability section ending in a formula or curves. Order: accuracy, ablation, small-sample/transfer, law, limits.
3. Public data only (XJTU, TJU, MIT, HUST x2; DSC data of ref [18]); 45-50 references; 8-11 figures; 2-9 tables; about 8,100-10,000 words.
4. Honest-sounding hedges are rewarded: PGKAN Sec 4.3 ("library-constrained surrogate, not a governing equation"), a Limitations section (PGKAN Sec 6), stability checks (PGKAN Tab 7, Tab 8, xi plateau).

## Where they are weak (verified in the texts and figures)
- No paired test, CI, SD or multiplicity control in any of the three; PIKAN/PGKAN rely on 10-seed violins that measure seed, not unit, variance.
- PIKAN headline 63.4 % = one cell (HUST, 1 training cell, PINN 0.0339 vs 0.0124 RMSE, Tab 5). Zero-shot transfer RMSE 0.025-0.199 called "excellent" (Tab 6). PGKAN MIT "8.5 %" computes to 7.8 % from printed values.
- Both USTC papers estimate SOH from same-cycle charging features plus time; no unseen stress, no forecasting.
- Discovered laws: PIKAN's Verhulst recovery is forced by the restricted library; recovered C = -2.2171 (XJTU b1) and K = 7.6789 (TJU b3) are non-physical (Fig 10); three different symbolic SHEM formulas exist for XJTU b1 (Tab 8, Fig 10a, Fig 4 inset). PGKAN's closed form (HUST RMSE 0.0109, Tab 9) is worse than every baseline in its own Tab 3 (0.0083-0.0090); its TJU rank-3 PDE term is significant in 0 of 10 repeats (Tab 7); PGKAN HUST MAPE is 0.0057 in Tab 3/5 but 0.0064 for the same architecture in Tab 9.
- Attribution: PGKAN has no KAN-only baseline and no "no physics" ablation row; its baselines have 5 x fewer parameters than PGKAN (7,781 vs 39,960, Tab 4) despite "at least comparable" (Sec 4.1).
- KA-CRNN: one interpolated test SOC per cathode, no metric, no baseline, no seeds; ln A2 and Ea,2 co-vary with the same shape (Fig 4B, D; single 2 C/min heating rate, compensation not discussed); monotone penalty on nu imposes part of the story; text says MSE, equation says absolute error.
- Visuals: default pastel matplotlib palettes; the proposed method's violin collapses to a line (PIKAN Fig 6); tiny pykan edge glyphs; KDE tails below zero; axis-label collisions (PIKAN Fig 6, KA-CRNN Fig 4); no uncertainty band on any learned function.

## How ours must exceed them (concrete)
- Held-out STRESS conditions with condition-level units, learning curves over m and k (their Fig 7 idea done properly: line + band per method), paired condition-level tests with Holm, forest plot of differences. This is the single biggest gap in all three.
- Law extraction (A15 vs G15): synthetic recovery first; seed AND fold stability table (their Tab 7 extended, failures reported); A15 vs GAM vs polynomial agreement (their Tab 8 extended); coefficients in physical units with bound checks; compensation/identifiability check between a(SOC) and E(T); penalty-off ablation; symbolic-vs-neural penalty with a CI and the same units as all baselines.
- Tables: include "no physics" and "no KAN" rows, equal-parameter arms, an inference-cost table (their PGKAN Tab 4), a tiny-model row (their PIKAN Tab 7), a parameter-roles table (their KA-CRNN Tab 1).
- Figures to copy (with fixes): KA-CRNN Fig 2 design grid with held-out in red; Fig 3 overlays (markers, bold line, grey components, gradient arrow) + band; Fig 4/B.1 stress-function panels + rug of training conditions + envelope + GAM overlay; PGKAN Fig 3 legends by condition; PGKAN Fig 5 metric grouping; PIKAN Fig 4 graphical abstract carrying real results.
- Text: numbered, falsifiable contributions with the test named; mechanism subsection ending in numbered conclusions (KA-CRNN Sec 2.1.2); Limitations subsection; one results ledger so Tab/Fig numbers never disagree; split unit, number of held-out units and tuning split in the main text.

## Open items / not verified
- Supplements of all three unread (splits, baseline tuning, per-seed distributions). Whether PIKAN's alpha-beta grid used the test set is from the earlier code note, not re-verified. KA-CRNN's physical magnitudes (ln A about 270, Ea about 1 MJ/mol) and the compensation argument are domain-knowledge judgements, not computed here.
- Figures not opened: PGKAN Figs 7-8, KA-CRNN Figs A.1, B.2-B.3, C.1-C.3 (judged from captions / sibling figures).
