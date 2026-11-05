Turn 8 (you are the OPPONENT in debate D023: test-time inversion of the per-cell latent). Read:
- C:\Users\Shlok\Downloads\PINN KAN battery paper\debates\D023_inversion\01_proposal.md and
  C:\Users\Shlok\Downloads\PINN KAN battery paper\runs\check_D023_inversion\ (decision.json and results; rule committed before
  the run). Finding: fixed-step Adam inversion is unconverged; a per-cell Newton step (O2) converges for 99.4 % (A1) / 100 % (A9)
  of cells but different starts reach different local minima (start spread median 7.8 pp for A1; A9 p95 50 pp); lowest-loss
  multi-start (O3) is less stable. Pre-ruled verdict NONE. Proposer recommends O2 from the prior mode for every inverting arm,
  disclose multimodality, plus a separate pre-ruled check of the z-prior weight {1, 4, 16} (about 0.5 CPU-h).
- C:\Users\Shlok\Downloads\PINN KAN battery paper\runs\pilot_P6b\RESULT.md (where the problem was found; ISU development data).

Attack concretely:
1. Is "deterministic start at the prior mode" a defensible estimator (MAP-like, reproducible) or does it hide an identifiability
   failure a reviewer will find? What should the paper report about start dependence?
2. Is tuning the z-prior weight on ISU training sides legitimate and fair to A9 (and to non-inverting comparators D*)? Should the
   weight instead be chosen per Samsung fold by inner CV (training conditions only)?
3. Better options within 1-2 days, CPU-only: e.g. reparameterise the window so z is identified (F = t*g makes early-window
   sensitivity to z scale with t), shrink z to zero when the window is short, marginalise over z (average forecasts over the
   posterior or over starts), or drop z at k = 0/2. Weigh each; mark speculation.
4. Final: accept / revise / reject, with at most 3 required changes.
Under 800 words. No invented numbers or citations.
