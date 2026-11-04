# Prior-art summary (2026-11-05)

Details in `priorart_piddm.md`, `priorart_guo2607.md`, `priorart_kacrnn.md`. All ids verified (arXiv API, Crossref).

**Must cite**
1. PiDDM, Chen et al., arXiv 2607.29095 (SSRN 10.2139/ssrn.7213804). Closest law: Arrhenius time term plus Arrhenius DoD and throughput term, network-supplied parameters, Euler integration. Do not claim the learned-parameter physics law. Differences, each checked in the text: no storage cells, no SOC, no KAN, test cells share protocols with training, and it needs the test cell's charging features and usage over the whole horizon, so it is no early-check-up forecast. No identifiability test, no seeds.
2. Guo et al., arXiv 2607.16864 (preprint). Closest task: forecast from 2 to 20 % of an unseen cell under a physics constraint. Cite as prior work; our addition is calendar plus cycle coverage, KAN stress functions, held-out stress combinations, ablations. Its abstract percentages disagree with its own Table 1; quote only values we re-derive.
3. KA-CRNN, Koenig and Deng, J. Energy Storage 158, 121853 (open version arXiv 2512.15628). Precedent for KAN functions of SOC inside an Arrhenius law, in our target journal, but thermal-abuse DSC kinetics, one held-out SOC, no error numbers. Cite as construction precedent.

Also cite Wang et al., Nat. Commun. 15, 4332 (2024), the PINN baseline.

**Do not claim:** first physics-informed or learned-parameter ageing law; first early-data physics-constrained forecast; first KAN with Arrhenius-type coefficients.

**Safe wording, if our evidence holds:** to our knowledge, the first joint calendar-plus-cycle law with KAN stress functions fitted to storage and cycling cells of one dataset and scored on held-out conditions, with physics and KAN ablations and a parameter-recovery test, none of which these three works report.
