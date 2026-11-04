# SYNTHESIS B: refs 8, 15, 30, 31 read in full; 7 abstract only; 13, 14, 24 not served

## Patterns
1. **Physics is a global constant, never a stress function.** Liu's Verhulst law has three scalars (k, u_i, M) for 124 cells and 72 protocols; Deng's Arrhenius branch uses temperature only with fixed Ea and D0; Peng's circuit parameters are just features. No paper learns a rate as a function of measured stress.
2. **"Identified parameters" carry no uncertainty.** Liu quotes k = 0.003389, M = 0.956, u_i = 0.0167 from one seed. Deng's Table 7 shows two different SEI laws reach equal error after joint training (cycle error 11 vs 9): the data did not discriminate them. Nobody tests identifiability.
3. **No placebo for the physics.** No size-matched no-physics or wrong-physics control. Liu's KAN-without-physics is the only partial one (test MAE 1.648 vs 1.342 %, single seed).
4. **Weak statistics.** One seed (Liu), none reported (Peng, Deng), eight seeds on a fixed split (Nakano).
5. **Tuning leakage and unequal effort.** Liu picks KAN size by test RMSPE and gives baselines the same fixed settings; Deng judges training stages on test; only Nakano tunes all baselines on train/validation.
6. **Splits reward interpolation.** Shuffled cycles (Liu), random trips from three vehicles with mileage-interpolated labels (Nakano), one test cell (Peng).
7. **Internal inconsistencies** (Liu 2x16 vs 2x64; Deng DCNN 55 vs 65, headline 15 vs 11; Peng 18 vs 20 inputs): a frozen, scripted pipeline is itself a differentiator.
8. **Figures that worked:** Nakano's route-coloured parity plot with tolerance band and error insets; Peng's cycle-coloured IC stack; Deng's per-cell boxplot panels and staged-training schematic. None shows learned KAN splines or fitted law curves against data.

## Consequences for a PI-KAN stress-law paper
- Make the rate a KAN of stress; show the learned edge functions with seed bands and the implied law on held-out stress cells.
- Identifiability study: refits per seed, per cell subset and with truncated horizon; profile likelihood or bootstrap on law parameters; law-swap test (Arrhenius, power, sqrt-t) by predictive distance; size-matched no-physics and shuffled-stress placebos.
- Tune every baseline equally on training cells only; 5+ seeds with intervals; include a cycle- or mileage-linear floor predictor.
- Borrow Liu's efficiency table (train time, inference ms, size) and Deng's control-variable table.
