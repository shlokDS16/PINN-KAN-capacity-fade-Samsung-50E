# PINEAPPLE (Pugalenthi et al., JES 153, 120944)

**Citation.** K. Pugalenthi, J. C. Wong, Q. Yang, P.-H. Chiu, M. H. Dao, N. Raghavan (corresponding), C. C. Ooi (corresponding), "PINEAPPLE: Physics-informed neuro-evolution algorithm for prognostic parameter inference in lithium-ion battery electrodes", J. Energy Storage 153 (issue 2026-04), article 120944, DOI 10.1016/j.est.2026.120944 (verified on Crossref). A*STAR (Singapore), SUTD, CUHK. arXiv 2602.18042 v1.

**Reading depth: full text of arXiv v1 HTML (submitted version) + 3 figures viewed (schematic, inverse-inference boxplots; others from captions).** JES published version, Highlights and graphical abstract not seen. Files in `refs/exemplars/html|md|img/` (`arxiv_2602.18042*`, `pineapple_*`).

## Problem and claims
Problem: infer internal single-particle-model (SPM) parameters (diffusion coefficients, etc.) per cycle from discharge V-t curves, quickly. **Four numbered contributions** at the end of the Introduction: (1) framework combining meta-learned PINNs with evolutionary search; (2) Baldwinian meta-learning of a generalisable PINN (zero-shot, 10x faster than PyBaMM at similar accuracy; abstract: test errors below 0.1 %); (3) inverse inference as evolutionary search over scaling factors, no cell-specific calibration; (4) recovery of consistent, interpretable degradation trends on real CALCE data. A roadmap paragraph follows. Sections: 1 Introduction, 2 Real-world dataset, 3 First-principle model (SPM, terminal voltage), 4 Method (4.1 internal state, 4.2 PINEAPPLE-pretrain, 4.3 PINEAPPLE-inference), 5 Results and discussion (5.1-5.6, **5.6 is an explicit "Limitations of SPM" subsection**), 6 Conclusion ("Key Findings", then "Future Extensions" as a numbered list), Appendix A (parameter table). 9 figures + 2 tables in the main text; no baselines table because the claim is a method for inference (comparison is against a numerical solver, Fig. 4).

## Data, model
CALCE CX2 LCO-graphite cells, 4 cells (CX2-34/36/37/38), 50 to about 1950 cycles (Fig. 1 caption). PINN "LE-PINN" meta-learned on simulated SPM data; physics enters through the PINN residual of the diffusion PDE (pre-training), then the final layer is fitted by pseudo-inverse. Evolutionary search (20 independent runs per cycle) infers scaling factors eta_Dp, eta_Dn, eta_Gp, eta_cmax,p.

## Figures (form, message)
| Fig | Form | Message | Note |
|---|---|---|---|
| 1 | V-t curves of 4 cells, colour gradient by cycle number (blue, green, orange, red) | degradation changes the curve | rainbow (not CVD-safe) |
| 2 (viewed) | **Pipeline schematic**: top strip of three small real-data panels (early, mid, late cycle; green solid = measured, red dash-dot = model) feeding an argmin equation; below a network sketch with coloured blocks (beige = meta-learned layers, violet = fine-tuned final layer) and rounded boxes for SPM and voltage model | what is learned offline vs inferred online, with real data attached to the diagram | strongest schematic of the set: data at the top, equation in a bracket, shaded training stages |
| 3 | forward prediction vs ground truth for out-of-sample (top) and out-of-distribution (bottom) parameters | zero-shot generalisation | paired with Table 1 (train/test relative error, mean +- sd, evaluation time) |
| 4 | error and wall-clock vs numerical solver at different mesh sizes | 10x speed-up at equal accuracy | cost figure; single representative case |
| 5, 6 | simulated V-t curves for early/mid/late states; synthetic validation, 4 rows: curve overlay, inference error vs MSE with Spearman coefficients, parameter distributions with dotted ground truth, overlays after filtering | identifiability check on synthetic truth before real data | **synthetic-then-real** order is the pattern we need for Fig. 8 |
| 7 (viewed) | grid of boxplots: 4 columns (cells) x 5 rows (eta_Dp, eta_Dn, eta_Gp, eta_cmax,p, MSE), x = cycle, boxes coloured by cycle (purple to red), log y for diffusion and MSE, row labels in colour, shared axes | consistent trends across cells; MSE grows late | caption: only the 50 % of runs with lowest MSE are plotted (selection stated) |
| 8 | sensitivity of V-t to one-at-a-time scaling-factor perturbations | which parameters are identifiable | |
| 9 | scatter of each inferred parameter vs discharge capacity, four cells | which parameters are usable as health indicators | |
Table 1: relative error (train/test) as mean +- sd with evaluation time, one row per electrode parameter. Table 2: SPM parameter values.

## Ablations, statistics
No ablation tables. Uncertainty shown as run-to-run spread of the optimiser (boxplots, Spearman correlation of error vs MSE). No held-out-cell test in the forecasting sense.

## Weaknesses a reviewer could hit (and the paper's own limitations section)
4 cells of one chemistry; isothermal; SPM omits electrolyte and SEI film resistance (said in 5.6); no forecasting; boxplots exclude the worst 50 % of optimiser runs.

## Use for us
- Claim pattern: **4 numbered contributions + roadmap**, an explicit limitations subsection, a "Key findings / Future extensions" conclusion.
- Forms: Fig. 2 as the model of a method schematic with real data attached; synthetic-validation figure (Fig. 6) as the template for our G1/G2 recovery figure; log-y boxplot grid coloured by stage for distributions over cells.
