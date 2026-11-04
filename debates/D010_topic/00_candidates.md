# D010 topic: candidate list for debate (2026-11-04, 21:40)

Sources: notes/PRIOR_ART_SCAN_lead.md (E1), notes/code/GAPS.md (full code reading of PIKAN and
PINN4SOH), debates/codex_panel/turn01_response.md (Codex panel, abstract-level prior art).

Verified by the lead in code: PIKAN selects (alpha, beta) by test MAPE
(`refs/code/PIKAN/main_our_models_optimize_HUST.py:74-85`); each cell's features and cycle index are
min-max scaled over that cell's whole life (`refs/code/PIKAN/dataloader/dataloader.py:56-61`), so
time is life fraction and the method cannot forecast.

## C1. Early-cycle trajectory and lifetime forecasting with a stress-conditioned physics-informed KAN rate law
dQ/dN = -r(Q, N, s) with r >= 0 by construction; s = operating condition (charge/discharge C-rate,
DOD, temperature). r = mechanistic backbone (e.g. power-law / sqrt-throughput SEI term with
Arrhenius temperature factor, plus a knee term) + small KAN correction, in physical cycle (or Ah
throughput) units, causal normalisation. Forecast a held-out cell's remaining trajectory and
end-of-life cycle from its first K cycles plus s. Datasets with designed stress variation (Sandia
batteryarchive, Oxford / other multi-condition sets, TJU temperatures, MIT charging protocols, HUST
discharge protocols).

## C2. Identifiability and predictive validity of KAN-discovered degradation laws
Do symbolic laws extracted from physics-informed KANs stay the same across seeds, folds and
training cells, survive coefficient rounding, and recover the generating law on synthetic cells
with known dynamics? Compare free-G (PIKAN-style) with a structured backbone + KAN correction.

## C3. What the physics residual does in Wang-2024-family PINN/KAN models
Partial-derivative residual at fixed features vs total-derivative residual along the trajectory;
u_t inside G (PINN4SOH degeneracy); factorial ablation of physics terms with training-cell-only
tuning. Most feasible, weakest standalone novelty (Codex panel).

## C4 (lead's merge, to be attacked). C1 as the method and headline, with C2's identifiability
tests as the evidence that the learned law is physics (not curve fitting), and C3's ablation as
the attribution study. One paper, one claim: a causal, cycle-unit physics-informed KAN that
forecasts unseen cells and yields a stable, compact stress law.
