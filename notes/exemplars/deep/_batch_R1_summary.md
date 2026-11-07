# Batch R1 summary: Stroebl 2026, Lucu 2020 Part A and Part B (JES exemplars)
Notes: `stroebl2025.md`, `lucu2020_A.md`, `lucu2020_B.md` (this folder). All three read in full text; Figures viewed as images (in `refs/figs/`): Stroebl 12 of 13, Lucu A 8 of 9, Lucu B 7 of 12; the rest judged from captions. Tables 1/3/C1 of Part B are unreadable in the capture.

## What JES published here
1. Weak statistics are accepted if the design is clear: none of the three papers reports a hypothesis test across units (Stroebl uses one bootstrap run per arm; Lucu A/B report means with no interval, no baseline, one fixed ordering). Our paired condition-level tests with Holm control are a real differentiator; say so once in the abstract and once in the methods.
2. A headline number about data efficiency sells (Lucu: 18 cells to 0.53 %, 26 cells to 1.04 %); Stroebl's number is a 28 % uncertainty cut. Put N cells, M conditions and the held-out error in the last abstract sentence.
3. Negative results are publishable when diagnosed (Stroebl: highlights 3-5 are failure and boundary statements; Fig. 7 gets equal size). Ours should pre-state which arms may tie and report ties in the same figure size.
4. Honesty about calibration is tolerated (Lucu CS_Q 86.55 % / about 75 % against 95.4 % target, explained in one paragraph); do not drop an interval metric that looks bad.

## Structure norms
5. Skeleton to copy: Intro with 3-5 labelled contributions (Stroebl bold-label bullets; Lucu main vs secondary) then roadmap; Methods; per-case results with identical run-in headings (Stroebl mirrors its flowchart boxes); Discussion with limitations; Conclusions; appendices for diagnostics.
6. Size: Stroebl ~6,500 words, 9 body display items + 7 appendix items; Lucu A ~10,000 words and 16 items; Lucu B ~9,000 words and 18 items. The 2026 guide asks about 6,000 words and 8-10 figures and tables, so Stroebl is the length model and Lucu the content model.
7. Highlights: 5 bullets, 1-2 numbers, at least one boundary condition and one transferable rule (Stroebl).

## Figure forms worth copying (and what to fix)
8. Learning curve (Lucu A Fig. 3, B Fig. 4): ordered ladder on x, a top banner naming which factor each rung adds, dashed dividers, held-out-only and "targeted held-out" panels. Fix: band over random orderings, noise-floor line, one axis per quantity, k as a second dimension (colour, columns, or an (m, k) heat map with the threshold contour).
9. One held-out condition at four rungs as small multiples (Lucu A Fig. 4, B Fig. 5), colour = role of the cell. Add our closed-form law overlay.
10. Design map: scatter-matrix over all stress factors with shaded physical constraints (Stroebl Fig. B.10) but in the body and with held-out conditions marked; replicate-curve overview with factor banners (Lucu B Fig. 2).
11. Uncertainty-narrowing plots over the stress axis (Lucu Fig. 5 / 6) and an extrapolation axis well beyond the data (B Fig. 6 runs to 5 C charge and 10 C discharge). Ours: empirical envelope of the learned law over resamples, data-supported range shaded.
12. Known-truth recovery (Stroebl Fig. 8) as a possibility proof; report frequency of failure, not only the extreme pair.

## Tables worth copying
13. Ladder table (conditions added, cells, share of data), retained-data table per condition, replicate-variance table with a footnote naming the cause of each large value (Lucu A Tables 3, 5, A1; B Table B1), model-adequacy table with noise floor (Stroebl Table 1).

## Risks they expose for us
14. Stroebl reports on this very cell type that dropping C_ch and C_dch leaves the heuristic cycle model's residuals unchanged (Table 1: p 0.76-0.98, rho_s > 0.995, full-model R2_adj 0.83-0.93) and that the heuristic model is inadequate. A reviewer will ask what our learned C-rate laws add. Pre-register a leave-one-factor-out arm on held-out conditions.
15. Lucu's "held-out" error is largely interpolation; ours must say how far outside the training hull each held-out condition is.
16. Both series and Stroebl have editorial slips (copy-forward text, unused legend entries, duplicate paragraphs, number mismatches). Run a numbers-vs-tables reconciliation before submission.
17. Open points in the capture: Stroebl's real abstract, reference list and any data-availability statement are missing; Stroebl cites at least 46 references while the older note counted 38; verify on the live page.
