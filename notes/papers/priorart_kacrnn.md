# Prior art: KA-CRNN (Koenig and Deng, J. Energy Storage 158, 121853)

Extraction by paper-reader, 2026-11-05. Template: CONTRACT section 4. "Paper reports" statements are E2 for the report only.

## Citation
Koenig BC, Deng S. "Learning continuous state of charge dependent thermal decomposition kinetics for Li-ion cathodes using Kolmogorov-Arnold Chemical Reaction Neural Networks (KA-CRNNs)". Journal of Energy Storage 158, article 121853 (May 2026), doi 10.1016/j.est.2026.121853 (Crossref verified: title, volume, article number, issued 2026-05, authors Koenig and Deng). MIT, Department of Mechanical Engineering, USA.
An open preprint EXISTS: arXiv:2512.15628 (v1 2025-12-17, v2 2026-04-06, physics.chem-ph); the arXiv API lists the journal reference "Journal of Energy Storage 158 (2026) 121853" and the same DOI, so it is the same paper. The proof-of-concept it builds on is Koenig and Deng, "Kolmogorov-Arnold Chemical Reaction Neural Networks for learning pressure-dependent kinetic rate laws", arXiv:2511.07686 (2025-11-10; verified on the arXiv API; not read).
IMPORTANT for positioning: this paper is about thermal-runaway (abuse) kinetics of cathode decomposition from differential scanning calorimetry (DSC), not about capacity ageing.

## Reading depth
Full text of arXiv v2 (Abstract, Sections I to IV, appendices A to D, reference list) read from the arXiv HTML saved as `ROOT/refs/md/arxiv_2512.15628v2.html` and the text version `ROOT/refs/md/arxiv_2512.15628_c.md`. The PDF download kept truncating, so no rendered page images were viewed; Figures 1 to 4, A1, B1 to B3, C1 to C3 known from captions only. The supplementary numerical parameter files of the published version were not read. Several displayed reaction equations are mangled in the HTML conversion.

## Problem and stated contribution
Existing kinetic models of cathode and electrolyte exotherms use scalar parameters at 100 % SOC or a few discrete SOCs. The authors replace selected parameters of a Chemical Reaction Neural Network (Arrhenius plus mass-action ODE) by Kolmogorov-Arnold activations that are continuous functions of SOC, and fit them to DSC curves of NM, NMA and NCA cathode-plus-electrolyte samples. Claim: continuous, interpretable SOC dependence of activation energies, pre-exponential factors, enthalpies and an oxygen-release stoichiometry, reproducing a "critical SOC" jump; generalisation to one withheld SOC.

## Data
- DSC measurements reproduced from the authors' ref [6] (cathode powder with LP57 electrolyte, heating at 2 C/min, Netzsch STA 449; Sec. II.3). Three cathodes (NM, NMA, NCA), nine SOC levels each (lithium removal 58.3 % to 87.4 %), one DSC curve per SOC. No cycling or ageing data, no cells.
- Label: heat flow (DSC) as a function of temperature. Features: SOC (a single input) and temperature through the Arrhenius law.

## Model
- CRNN with three global reactions (layered to spinel R1, spinel to rock salt with O2 release R2, electrolyte oxidation R3); species rates, Eq. (2) to (4) of the paper; heat release sum of enthalpy times rate (Eq. 5); rates from Arrhenius and mass action (Eq. 1).
- KAN part: each of 11 parameters of R1 and R2 per cathode (reaction orders, ln A, temperature exponent, activation energy, enthalpy, oxygen stoichiometry nu) is a univariate Chebyshev KAN activation of SOC, polynomial degree N = 10 (11 weights per parameter, 121 per cathode) (Sec. II.2, Eq. 6 to 8). Five R3 parameters are scalars shared by all cathodes (Table 1). It is a single-layer, single-input KAN, not a multi-input network; "KAN variant" = Chebyshev, no grid.
- Physics: the reaction network is hard-wired (architecture); soft penalties in the loss (monotonic penalty on Delta H2 and nu, lower and upper bounds on reaction orders and temperature exponents; Eq. 16 to 18). Integration by Neural-ODE style solves in Julia (DifferentialEquations, ForwardDiff). Not a PINN residual loss.
- Training: Adam, lr 5e-4. The loss is called "MSE" in the text but Eq. (15) is written with absolute values; unresolved inconsistency.

## Tuning
N = 10 "was found to be a high-performing choice" and "experimentally selected" (Sec. II.2); the penalty weights and exponents are set by hand. No search protocol, no nested validation described. The single withheld SOC is called testing data, and whether it influenced the choice of N or the weights is not stated.

## Evaluation
- Split: leave-one-SOC-out, one split: the fifth of nine SOCs withheld per cathode (Sec. II.3). Training on 8 curves per cathode.
- Metrics: none reported in numbers in the main text; fit quality judged by visual overlay of DSC curves (Fig. 3, Appendix C). No RMSE, no R2, no seeds, no uncertainty, no baseline numbers.
- Statements: test reconstruction "strong" for NM and NMA, "not quite as accurate" for NCA (Sec. III.1); at the highest SOCs the model does not fully reconstruct the R3 peak heights (Sec. III.3).

## Figures
Fig. 1 framework schematic (KAN activations of SOC vs scalar CRNN parameters, architecture, flowchart); Fig. 2 DSC training and test curves; Fig. 3 reconstructions at three SOCs per cathode, all-SOC overlays, oxygen stoichiometry activation showing the critical SOC; Fig. 4 learned ln A and E_a activations vs SOC; Appendix figures A1 (O2 production and consumption), B1 to B3 (all activations), C1 to C3 (all reconstructions). Style: colour-coded by cathode; not viewed as images.

## Ablations done
None reported (no scalar-CRNN vs KA-CRNN number, no degree sweep, no comparison with a Kissinger fit of the same data in this paper; the comparison with Kissinger is cited from earlier work).

## Hidden assumptions
- The three-reaction global scheme is the right mechanism; shared R3 across cathodes.
- SOC is the right variable (the authors themselves note voltage or dq/dV could be) (Sec. II.1.2).
- Eight points per cathode suffice to determine eleven functions at degree 10; the monotonic penalty is needed because nu and Delta H2 are "slightly underconstrained" (Sec. II.3). That is an admission of non-identifiability that is handled by a penalty, not tested.

## Weaknesses a reviewer would hit
1. One held-out SOC per cathode; no numbers; visual fit only.
2. Degrees of freedom (121 weights per cathode) against nine curves; interpretability of the learned functions rests on penalties.
3. Loss described inconsistently (MSE vs absolute value).
4. Abuse-kinetics setting: says nothing about forecasting ageing; no time-series of cells, no cycles.

## Gaps and hooks for our paper
- Hook 1: the closest published precedent for "KAN functions of SOC as the stress-dependent coefficients of an Arrhenius rate law" in a battery model, in the same journal as ours. We can cite it for the construction while stating that it covers thermal decomposition from DSC and gives no quantitative held-out error; ours is ageing forecast with a held-out score.
- Hook 2: it concedes under-constraint of oxygen stoichiometry and enthalpy; our identifiability test (recover known KAN functions from simulated data of our own law; coefficient stability across seeds and across held-out folds) addresses the same weakness with a number.
- Hook 3: a single-input Chebyshev KAN for SOC is the simplest case; our SOC-window and multi-variable stress KAN needs a justification beyond this.
- Hook 4: they report no baseline against a fixed-form scalar model; our scalar-form (Stroebl/Muehlbauer power-law) comparison and a no-KAN ablation fill that gap.

## Code/data availability
No GitHub or Zenodo link found in the text. Supplementary data (numerical parameter values) only in the published version at doi 10.1016/j.est.2026.121853. DSC data come from ref [6] of the paper.

## Exact overlap with our design
- KAN functions of SOC as coefficients of an Arrhenius rate law: same in idea (Eq. 6 to 8, Fig. 1A); different in setting (thermal decomposition) and input dimension (SOC only).
- KAN function over several stress variables (T, SOC window, DoD, C_ch, C_dch): different (single-input activations only).
- Storage (calendar) arm with Arrhenius times KAN of storage SOC: partial in form (Arrhenius with SOC-dependent parameters), different in quantity (heat release at heating ramps, not capacity loss under storage).
- Throughput-driven cycling term: different (none).
- Joint training on storage and cycling cells: different.
- PINN residual: different (hard-wired reaction network integrated as an ODE; soft penalties only).
- Ageing forecast at held-out conditions from early check-ups: different (one held-out SOC curve, no ageing).
- Ablation of physics and of KAN: different (none reported).
- Identifiability test: partial in spirit (acknowledges under-constraint, uses penalties; no test).
- Dataset (Samsung INR21700-50E storage and cycling): different (DSC of three cathode chemistries).
- Same journal (J. Energy Storage): same venue, so citing it is natural and expected by a reviewer.
