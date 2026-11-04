# Blueprint: a top JES paper on PINN + KAN calendar-plus-cycle ageing (2026-11-04)

Basis: three arXiv full texts (KA-CRNN, PINEAPPLE, CDUA), captions of two more, earlier FIGURE_FORMS rows. PIKAN, PGKAN, Stroebl, Zhang bodies are unread (PAYWALLED_FOR_SHLOK.md); revise after Shlok saves them.

## Claim pattern
- Abstract with two numbers (PINEAPPLE, CDUA, Stroebl do this). Highlights: 3-5 bullets, each carrying a number or a falsifiable statement (Stroebl has five).
- Introduction ends with **3-4 numbered contributions** and a roadmap paragraph (PINEAPPLE 4, CDUA 3). State the primary claim and its three paired contrasts.
- Results in the order baselines, ablation by component, ablation by input (CDUA 4.1-4.3), then physical interpretation, then an **explicit Limitations subsection** (PINEAPPLE 5.6). Put the pre-stated tie/negative outcomes in the text; Stroebl shows JES publishes a negative finding when it is explained.
- 8-10 display items; hyper-parameter spaces and noise sensitivity in appendix tables (NPE Tables 5-8).

## Figure and table forms
| Ours | Recommended form | Why; exemplar that sets the standard |
|---|---|---|
| 1 Method schematic | Pipeline: top strip of three real data panels (storage, cycling, held-out) feeding the F/G network boxes; shaded blocks for solution network, KAN stress functions, collocation sets; equation in a bracket | PINEAPPLE Fig 2 (data attached to diagram, shaded stages); KA-CRNN Fig 1 for cross-referenced panels A-E |
| 2 Design map | 3 panels: storage (T x SOC), cycling (T x DoD, colour C-rate, marker = replicates), replicate fade curves coloured by condition | KA-CRNN Fig 2 (rows/columns of the design); Yuan Fig 1 (3x3 data grid) |
| 3 Forecast overlays | Small multiples, rows = temperature (35 C row boxed as held-out), columns = condition; markers = observed, shaded window, one line per model (at most 3), seed band; held-out label in colour | KA-CRNN Fig 3 (marker data, line model, red held-out label); CDUA Fig 7 (two window lengths). Avoid Yuan Fig 8: 4 overlapping lines, tiny insets |
| 4 Primary endpoint | Forest plot of paired condition-level differences with Holm CIs, each arm one row, raw condition dots behind | Yuan Fig 14 (raw points on violins) for honesty; forest form because no exemplar shows paired contrasts |
| 5 Learned stress functions | 2x2 curve panels a(SOC), E(SOC), and cyclic partial dependences; seed/fold envelope; GAM overlay dashed | KA-CRNN Fig 4; Liu Fig 4.1 for edge glyphs. Theirs lack uncertainty; ours needs it |
| 6 Storage transfer | Parity per held-out storage condition coloured by T, error band at +-grey; side bar of storage share of cycled-cell fade | Nakano Figs 7, 9 (colour by nuisance factor) |
| 7 Residual map | Heat map |R| over (T, SOC) and (C-rate, T) with training points overlaid and printed values in cells | Yuan Fig 15 (annotated heat maps, per-panel scale) |
| 8 Synthetic recovery | Rows: truth vs recovered surface, error vs generator, boxplot per model with thresholds 0.15/0.30 as lines, truth dotted | PINEAPPLE Fig 6 (synthetic first, truth dotted); CDUA Fig 9 (boxplots per ablation) |
| Table 1 | Arms x column groups (Test B, C, S2, ISU, SNL), mean +- SD over seeds, best bold, Holm p in last column, runtime and parameters | Wang 2024 Table 4 (top-3 marking); Liu 2025 Table 2 (cost columns) |
| Table 2 | Control-variable table: what changes per ablation, parameters, delta primary endpoint | Deng 2025 Table 4; CDUA Tables 4-5 |

## Standards we must beat
- Evaluation: the exemplars use 1-4 test units (KA-CRNN one SOC per chemistry; PINEAPPLE four cells; CDUA 4-vehicle folds) with no paired tests. Our condition-level units, 5 seeds, paired Wilcoxon and Holm are the differentiator; say it once in the abstract.
- Interpretability: PIKAN/PGKAN claim discovered laws; ours is stress functions with envelopes and a GAM contrast.
- Pair one mismatch case with a success (NPE Fig 4).
- Colour: Okabe-Ito, not rainbow.

## Positioning flags
KA-CRNN (JES 158, 121853) already uses KAN-valued Arrhenius parameters as functions of SOC (thermal-abuse DSC); cite as nearest precedent. Zhang (JES 182, 125097) cites the Samsung data and uses a PINN; read before claiming novelty. Stroebl (JES 142, 119552) states the dataset's own cycle model is inadequate: our motivation.
