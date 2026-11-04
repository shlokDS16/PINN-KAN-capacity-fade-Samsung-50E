# KA-CRNN (Koenig and Deng, JES 158, 121853): the closest published precedent for "Arrhenius law with KAN-valued parameters"

**Citation.** B. C. Koenig, S. Deng (MIT, Mechanical Engineering), "Learning continuous state of charge dependent thermal decomposition kinetics for Li-ion cathodes using Kolmogorov-Arnold Chemical Reaction Neural Networks (KA-CRNNs)", J. Energy Storage 158 (issue 2026-05), article 121853, DOI 10.1016/j.est.2026.121853 (verified on Crossref). arXiv 2512.15628 (v2, CC BY-NC-ND per Unpaywall).

**Reading depth: full text of the arXiv v2 HTML (submitted version) + 2 of its 4 main figures viewed as images (Fig. 3, Fig. 4).** The JES published version, its Highlights and its graphical abstract are not seen; the arXiv figure numbering may differ. Files: `refs/exemplars/html/arxiv_2512.15628.html`, `refs/exemplars/md/arxiv_2512.15628.txt`, `refs/exemplars/img/kacrnn_*.png`.

## Problem and claim structure
Problem: kinetic models of cathode-electrolyte decomposition use scalar parameters at one or a few SOCs. Claim: Arrhenius parameters (frequency factor A, activation energy Ea, reaction order, enthalpy, oxygen stoichiometry nu) are **continuous functions of SOC**, each a univariate KAN activation (Chebyshev basis, degree N), inside a fixed mechanistic reaction network (mass action + Arrhenius, solved as a neural ODE in Julia). **No numbered contribution list**; novelty is stated in prose in the Introduction and Conclusions ("a key novelty ... continuous response of the kinetic parameters to the SOC"). Sections: I Introduction, II Methodology (II.1 mechanistic literature review with numbered conclusions 1-4, II.2 model, II.3 training), III Results (III.1 predictions, III.2 parameter visualisations, III.3 outlook), IV Conclusions, Appendices A-D (rates, activations, reconstructions, data). Length: 4 main figures + 2 tables + 7 appendix figures.

## Data, model, training (so that we can position ourselves)
- Data: DSC heat-release curves of 3 Ni-rich cathodes (NM, NMA, NCA) x 9 SOC levels (from ref [6] of the paper; the text cites it as the critical-SOC DSC study, key cui_navigating_2025); one SOC level (fifth, about 200 mAh/g) **withheld per cathode as the only test point**. That is a very small evaluation; there is no baseline model and no seeds.
- Model: Eq. 8 Arrhenius rate with ln A, b ln T, Ea; mass-action species ODEs (Eqs. 9-11); each SOC-dependent parameter = one univariate Chebyshev KAN activation phi_i(SOC) (Eqs. 13-15). 11 SOC-dependent parameters per cathode (Table 1); electrolyte-oxidation parameters are scalars shared across cathodes (Table 2).
- Physics enters as **structure** (reaction network) plus **soft constraints in the loss**: monotone penalties on Delta H2 and nu across SOC (Eq. 16), minimum/maximum bounds on reaction orders (Eqs. 17-18). Loss = mean absolute error on heat release + these penalties. Adam, lr 5e-4. Chebyshev chosen explicitly "to accommodate the relatively sparse training data" instead of a gridded B-spline KAN.

## Figures (form, what it says)
| Fig | Form | Message | Notes |
|---|---|---|---|
| 1 | Five-panel schematic A-E: (A) KAN-valued parameters as curves vs SOC, (B) standard scalar CRNN, (C) example predictions vs SOC, (D) full network/reaction diagram, (E) forward/backward flowchart with cross-references to A-D | what is new vs the standard CRNN, and the whole pipeline | caption doubles as a reading guide; panel E cross-references A-D |
| 2 | Data figure: 3 rows (chemistry) x 9 columns (SOC), y-axis rescaled from column 7 on | the training data and the critical-SOC regime change | row/column label design is reusable for a design-of-experiments figure |
| 3 (viewed) | 3x3 grid (rows NM/NMA/NCA, columns lowest/test/highest SOC): markers = data, bold line = model total, grey solid/dashed/dotted = components R1-R3, white legend box in each panel; colour = chemistry (light-blue/orange/green) with a gradient arrow "Inc. SOC"; **held-out SOC labelled in red italics**; panel B overlay of all 9 SOC per chemistry as gradient (light to dark = SOC); panel C = nu(SOC) activation, one line style per chemistry (dotted/solid/dashed) | model reproduces unseen SOC; the critical SOC appears as a jump in the learned nu | train vs test marked by colour of the label, not by a separate figure; component curves in grey keep the message readable |
| 4 (viewed) | 2x2 line panels: ln A1, ln A2, Ea1, Ea2 vs SOC (mAh/g), 3 smooth lines (blue/orange/green = chemistry), boxed legend, panel letters (A)-(D) outside axes | learned **stress functions** as readable curves; second reaction shifts at each chemistry's critical SOC | **exact form we need for a(SOC), E(SOC) panels**; no envelope (single fit), which we must add (seed or fold band) |
| A1, B1-B3, C1-C3 | appendix: rates, Chebyshev terms (green) summed to the black activation, all-SOC reconstructions | completeness | decomposition into basis terms shown in the appendix, not the main text |
Tables: Table 1 = classification of parameters (KAN activation vs scalar); Table 2 = learned scalar values. No results table (no baselines).

## Ablations / statistics
None. No uncertainty quantification, no seeds, no comparison with a non-KAN parameterisation. A JES reviewer of our paper will expect the opposite (GAM, MLP, parametric forms, seeds).

## Hidden assumptions and weaknesses
Evaluation on one withheld SOC per material; no baseline (a spline or polynomial parameterisation would very likely fit equally well with nine SOC levels); KAN is univariate and therefore a GAM component by identity; Chebyshev basis rather than splines; the interpretation (critical SOC, oxygen release) rests on a literature argument, not on a test.

## Why it matters for our paper
1. **Prior art for our calendar term.** An Arrhenius law with KAN-valued parameters as functions of SOC, inside a physics ODE with a Neural-ODE solver, is published in JES 2026 (their earlier proofs of concept: Koenig and Deng, KA-CRNN for pressure-dependent kinetic rate laws, 2025; Koenig, Kim, Deng, KAN-ODEs, 2024, both in the arXiv v2 reference list (the 'KA-CRNN' proof of concept is item [18]); **DOIs not verified, send to citation-validator**). It is thermal-abuse chemistry on DSC data, not ageing forecasting, so the novelty gap stays open (calendar plus cycle, forecasting held-out conditions, aging data). The novelty audit must include it, and our introduction should cite it as the nearest use of "KAN-valued Arrhenius parameters".
2. **Form to copy:** Fig. 4 (stress-function panels) and Fig. 3 (marker data, line model, grey components, red label for held-out, gradient for ordered stress).
3. **Do better:** add fold/seed envelopes, a GAM/MLP comparison, and a held-out-condition test with more than one point.
