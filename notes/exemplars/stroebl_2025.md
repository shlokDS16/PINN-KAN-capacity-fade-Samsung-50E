# Stroebl et al. 2025 (JES 142, 119552) and the dataset authors' related work

**Citation.** F. Stroebl, F. Schaeufl, O. S. Bohlen, H. Palm, "Model-based optimal experimental design for lithium-ion battery aging: Insights from a comprehensive multi-stage study with real-world data", J. Energy Storage 142 (2026-01 issue; online 2025-11-25), article 119552, DOI 10.1016/j.est.2025.119552 (verified on Crossref; PII S2352152X25042665). Munich University of Applied Sciences, Germany. Licence CC-BY (hybrid OA per Unpaywall/OpenAlex).

**Reading depth: abstract + 5 highlight bullets + full reference list only.** ScienceDirect returned HTTP 403 to a script request; Exa served metadata, abstract, highlights and the 38-item reference list but not the body. SSRN preprint (accepted version, https://doi.org/10.2139/ssrn.5245049) gives only the abstract page. I did not try to get past the bot check. **The body (figures, tables, section structure) is unread. Shlok to save it by hand (CC-BY, free in a browser).**

## What the abstract and highlights say (paraphrase)
- Uses the Samsung INR21700-50E multi-stage dataset: 279 commercial cells under **71 conditions** (note: the judge counted 59 conditions, 19 storage + 40 cycling, from `experiments_meta.csv`; see Flags).
- Parameter-individual optimal experimental design (pi-OED) vs non-optimised designs. Calendar aging: pi-OED cuts uncertainty of the temperature-dependent parameters by 28 %. Cycle aging: no gain, because the heuristic cycle model is inadequate: it predicts a sensitivity that experiments did not confirm (rate parameters explain the pattern "at the noise level").
- Five highlights (bullets with numbers), e.g. "OED cuts calendar aging parameter uncertainty by 28%", "Model inadequacy explains failure of OED in cycle aging".
- Reference list shows the model lineage: Schmalstieg 2014 holistic aging model, Naumann 2018/2020 LFP calendar and cycle models, Karger 2023 mechanistic calendar model, Gewald 2020 sensitivity analysis of cyclic stress factors, Rogge 2023 path dependence, Mayemba 2024 datasets review.

## Claim structure (from abstract/highlights)
Three claims: (1) a structured OED framework for aging studies, (2) quantified efficiency gain for calendar aging, (3) a negative finding that model validity is the prerequisite. No numbered contribution list visible; five highlights carry the numbers.

## Figure/table forms
Unknown (body unread). Do not add rows to FIGURE_FORMS for this paper until it is saved.

## Why it matters for our paper (hooks, testable)
1. **The dataset's own authors report that their heuristic cycle model is inadequate** (abstract). That is a published, citable motivation for a flexible, interaction-capable stress law (our hidden-layer KAN over T, SOC window, DoD, C_ch, C_dch) on exactly this dataset. Cite it as motivation, never as something we "fix" without evidence.
2. It uses a calendar model with temperature-dependent parameters on the same cells: our calendar arm (Arrhenius x KAN of SOC) is the learned analogue; compare to their parametric form as the "parametric Arrhenius/power-law" baseline in the 9-arm list (use the form from the paper once read).
3. No machine-learning or PINN forecasting appears in the abstract; their task is parameter-uncertainty reduction, not held-out-condition forecasting.

## Other work by the same group (not JES 2026)
- No 2026 JES follow-up by these authors was found in OpenAlex (author A5060104574) or Crossref (author query on ISSN 2352-152X, from 2025-01). The only other JES items with Stroebl are Reiter, Schutte, Rosenmuller, Stroebl et al., JES 140, 118897 (entropy variation vs aging, temperature, hysteresis; not a forecasting model; green copy RWTH, DOI 10.18154/rwth-2026-02022) and the non-JES paper Cui, Stroebl, Uppaluri, Lam et al., J. Electrochem. Soc. 2025, DOI 10.1149/1945-7111/adde16 (semi-empirical, symbolic-regression and data-driven calendar-aging models on the Stanford calendar dataset, interpolation and extrapolation across conditions; abstract read via OpenAlex only). The latter is directly relevant prior art for "learned calendar law with extrapolation".
- Stroebl et al., IEEE Access 12:120440 (2024), DOI 10.1109/access.2024.3446234, multi-stage OED; Palm et al., IEEE Access 10:112515 (2022). Not read.

## Flags for the lead
- **Condition count mismatch:** 71 conditions (paper abstract) vs 59 (judge, from local metadata). Resolve before Figure 2 and Table 1 are written (maybe the paper counts check-up/stage variants or different replicates). Needs the dataset paper (`refs/samsung50e_paper`) or this JES body.
- Citing works of the dataset (OpenAlex "cites" list, 2026-11-04) that the novelty re-audit must check: Li et al., Applied Energy 2025, DOI 10.1016/j.apenergy.2025.125703 (capacity-fade model coupled with ML, early prediction of trajectory; abstract not served); van Vlijmen/Lam et al., Energy Environ. Sci. 2025, 10.1039/d4ee05609d; Hallinger, Kirst, Singer, Bohlen, SSRN 7417281 (calendar-aging identifiability and reduced experiments); Zhong and Rogge, SSRN 7589132 and Zenodo 22498593 (preregistration, reversible history state, "read from ordinary check-ups"); Zhang et al., JES 182, 125097; Ponce-Alcantara et al., Sci. Data 2026, 10.1038/s41597-026-08369-8 (a different dataset on Samsung INR21700-50E cells; check it is not the same cell data under a new DOI).
