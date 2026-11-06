# Hallinger et al. 2026 - Efficient parameterization of mechanistic calendar aging models (SSRN 7417281, preprint)

Paper note per research/CONTRACT.md section 4, written for freeze blocker FB-2 (Hallinger part) and novelty condition (a). Auditor: novelty-auditor, 2026-11-06.

## Citation
L. Hallinger, C. Kirst, J. P. Singer, O. Bohlen. "Efficient parameterization of mechanistic calendar aging models: from a priori identifiability to reduced experimental effort". SSRN preprint 7417281, dated 4 September 2026, "not peer reviewed", "Preprint submitted to Journal of Energy Storage". No DOI (SSRN abstract id 7417281, https://ssrn.com/abstract=7417281). Munich University of Applied Sciences (ISES, Bohlen group), TU Munich, University of Applied Sciences Esslingen; Hallinger, Kirst and Singer are employed by TWAICE Technologies GmbH (competing-interest statement). Germany. Bohlen is also a co-author of the Stroebl et al. Samsung 50E papers (refs [4], [18] of this preprint).

## Reading depth
Full text of the main body, from the PDF (19 pages, re-extracted with pdftotext in reading order because `refs/fulltext/hallinger_ssrn7417281.md` is a garbled two-column conversion with missing spaces): abstract, Sections 1 to 6, data availability, all 33 references. Not inspected: figures as images (Fig. 1-6; captions read), appendix tables A.3, B.4-B.5, C.6-C.7 (identified by title only). Equation 24 (reduced LAM_PE factor) was read only through its description. Whole-file greps for "Samsung", "INR21700", "50E", "neural", "machine learning", "data-driven", "KAN", "Kolmogorov", "learning curve", "cycl": no hit besides the ones cited below.

## Problem and stated contribution
How to parameterise a mechanistic calendar-ageing model (Karger et al., J. Power Sources 578, 233208, 2023: power-law time dependence of lithium-inventory loss and cathode loss of active material, stress factors from temperature and electrode potential) with few experiments: a priori identifiability analysis (Fisher information, profile likelihood), model reduction, and a two-stage optimal experimental design (D-optimal and parameter-individual, after Palm et al. and Stroebl et al.). Headline: parameterisation from four conditions instead of 26 (MUR) with withheld-condition RMSE up by 0.16 and 0.33 percentage points (abstract; Section 4.3).

## Data
- **Not the Samsung INR21700-50E.** Two datasets only (Section 2): MUR = Murata/Sony US18650VTC5A, NCA/silicon-graphite 18650 cell, public (Wildfeuer et al., J. Power Sources 560, 232498, 2023; data doi 10.14459/2023MP1713382), 26 usable calendar conditions after dropping 100 % SOC at 60 C; LIW = LithiumWerks APR18650M1B, LFP/graphite, from TWAICE on request, 20 conditions (Section 4.3 states "all 20 conditions" and "16" withheld).
- The Stroebl multi-stage dataset (ref [4], "BaPoBs", 279 cells) appears only in the introduction as an example of a large public campaign and cost motivation ("196 and 279 cells"); it is not analysed.
- Calendar storage only; check-ups about every six weeks (20 C for MUR, 25 C for LIW); states of health of LLI, LAM_PE, LAM_NE obtained by OCV reconstruction (MSMR model; Kirst et al., J. Power Sources 602, 234341, 2024), not capacity.

## Model
Karger mechanistic calendar model for SOH_LI, SOH_PE (and SOH_NE where resolved); Arrhenius-type temperature term times an electrode-potential term; reduced forms (offset terms removed for LLI, SOC-scaling parameter removed and linearised for LAM_PE; Eq. 23, 24). Parametric least squares (maximum likelihood, scalar variance), parametric bootstrap. **No neural network, no learned map, no KAN, no cycling term, no capacity forecast.**

## Tuning
Not applicable in the ML sense (no hyperparameters). Design and calibration use the same cells as evaluation only through "OED-withheld" conditions (Section 4.3): calibration conditions chosen by OED from the full candidate set (the nearest available measured condition), the remaining conditions used as evaluation. Selection of the calibration conditions uses the model and early data, not the withheld trajectories, as far as the text states.

## Evaluation
Single partition per cell type; no seeds; no intervals on the RMSE. Section 4.3: MUR reduced model on four conditions, RMSE 0.59 % (SOH_LI) and 0.31 % (SOH_PE) on withheld data versus full benchmark on all 26 conditions 0.43 % and 0.28 %; LIW reduced LLI model on four conditions 1.60 % on 16 withheld conditions versus 1.27 % for the full benchmark on all 20. Conclusion: experimental effort reduced "by 80-85 %". Retrospective analysis of existing data; the authors say so (Section 5, limitations).

## Figures
Fig. 1 design-space coverage (T against SOC, filled/open markers), Fig. 2 check-up voltage profiles, Fig. 3 workflow diagram, Fig. 4 OED results (bootstrap RSD and chosen points), Fig. 5 parity plots of withheld data, Fig. 6 reconstructed stress factors against local per-condition estimates. Forms not inspected as images.

## Ablations
Reduced against full mechanistic formulation (Table 1, Table A.3); D-optimal against pi-OED; transferred against local initial parameters. No physics-on/off ablation (there is no learned component).

## Hidden assumptions
Model structure is correct for the cell (the authors state LAM_PE form was developed on an NCA cell and its validity for LFP "has yet to be demonstrated"); Gaussian homoscedastic residuals; nearest-measured-condition mapping of OED points; check-up-induced ageing compensation only for MUR.

## Weaknesses a reviewer would hit
Retrospective design, one cell per chemistry, calendar only, no repeats/seeds, "four of 26" is one comparison and not a curve over the number of conditions, a preprint.

## Overlap with our four-part claim and with A10
1. **Data-efficiency question: partial.** Same journal target (submitted to JES), same words ("reduced experimental effort"), but it is a parameter-identifiability and OED study of a fixed mechanistic calendar law, not a learning curve of a learned forecaster. The only count-of-conditions result is "four against 26 (MUR) and four against 20 (LIW)", evaluated on withheld conditions. A reviewer will cite it as a second in-journal precedent for "fewer experiments suffice", for calendar ageing.
2. **Joint calendar-plus-cycle law: none.** Calendar only; the conclusion lists a combined calendar and cyclic model as future work (a follow-up by this group is possible; none found in the search of 2026-11-06).
3. **Matched ablation ladder: none.** **KAN-extracted law against GAM: none.**
4. **Samsung 50E: not used** (only named as a dataset in the introduction). The D018 stop rule 12 ("a Hallinger result of that kind on this dataset") is not triggered.
5. **A10 (Stroebl JES 142 form, `code/pinnkan/semi.py`): no overlap.** A10 is the empirical power-law form (Eq. 17, 18, 21: Arrhenius term, SOC power, time power; cycle term with C-rates, DoD, FEC). Hallinger's model is a different law (negative- and positive-electrode-potential terms, sinh form). Hallinger cites Stroebl JES 142 only as an OED application ([18]) and says nothing about A10 or its adequacy.

## Gaps and hooks for our paper
- Cite as a calendar-ageing OED precedent (parameter count of experiments, mechanistic law) next to Stroebl JES 142; state the difference in one sentence (fixed mechanistic law, parameters from few conditions, no learned model, no cycling, no learning curve).
- Re-check at submission (condition (d)) for a cyclic-ageing follow-up by Hallinger/Kirst/Singer/Bohlen or by Stroebl/Palm on the 50E data.
- Cite carefully: it is an unreviewed preprint. If cited, mark as preprint with the SSRN id.

## Code/data availability
MUR data public; LIW on request; no code statement in the text read.
