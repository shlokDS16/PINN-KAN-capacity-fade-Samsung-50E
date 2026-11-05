"""Writes RESULT_weights.md from g_weights.csv, g_guard.csv, g_decision.json, fb_tables.csv, f_upper_bound_coverage.csv. Usage: python -P build_weights_result.py"""
import os
import json
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)
md = lambda df, f=".3f": df.to_markdown(index=False, floatfmt=f)
G = pd.read_csv(P("g_weights.csv"))
GG = pd.read_csv(P("g_guard.csv"))
DEC = json.load(open(P("g_decision.json")))
FB = pd.read_csv(P("fb_tables.csv"))
CV = pd.read_csv(P("f_upper_bound_coverage.csv"))
sims = G[G.w_P1N != "delta (0.78 - 0.5)"].copy()
dl = G[G.w_P1N == "delta (0.78 - 0.5)"].copy()
t1 = sims[["setting", "w_P1N", "P_P1", "P_P2", "P_P3", "P_K1", "P_K1K2N", "P_K1K2NK2S"]].rename(
    columns={"w_P1N": "w on P1N", "P_P1": "P(P1N,P1S)", "P_P2": "P(..,P2)", "P_P3": "P(..,P3)", "P_K1": "P(K1)", "P_K1K2N": "P(K1,K2N)", "P_K1K2NK2S": "P(K1,K2N,K2S)"})
t2 = dl[["setting", "dP1", "se_dP1", "dP3", "se_dP3", "dK1", "se_dK1", "dK1K2N", "dK1K2NK2S"]].rename(
    columns={"dP1": "dP(P1N,P1S)", "se_dP1": "SE", "dP3": "dP (chain through P3)", "se_dP3": "SE ", "dK1": "dK (K1)", "se_dK1": "SE  ", "dK1K2N": "d(K1,K2N)", "dK1K2NK2S": "d(K1,K2N,K2S)"})
t3 = pd.DataFrame(DEC["settings"]).rename(columns={"dP_plus_dK": "dP + dK", "ok": "rule met (dP+dK>0 and dK>=-0.10)"})
gm = GG.groupby("setting").apply(lambda d: pd.Series(dict(configs=len(d), max_FWER=d.fwer.max(), config_at_max=d.loc[d.fwer.idxmax(), "cfg"], mean_FWER=d.fwer.mean(), nrep=int(d.nrep.iloc[0]))),
                                 include_groups=False).reset_index()
old = pd.read_csv(P("d_fwer.csv"))
old = old[old.setting.isin(["iid_fb0.03", "fold10_lab05_fb0.03"])].groupby("setting").fwer.max()
gm["max_FWER at w=1/2 (RESULT 7)"] = gm.setting.map(old)
tb = FB[(FB.kind == "test") & (FB.domain == "Test B") & (FB.rho_s0 == 0.03)].pivot_table(index="n", columns="level", values="positives_needed").reset_index()
tb.columns = ["n"] + ["lvl %.5g" % c for c in tb.columns[1:]]
iv = FB[(FB.kind == "interval") & (FB.rho_s0 == 0.03) & (FB.level_label != "two-sided 0.05/18 (descriptive)")].pivot_table(index=["domain", "n"], columns="level_label", values="interval_rank").reset_index()
isu = FB[(FB.kind == "test") & (FB.domain == "ISU") & (FB.rho_s0 == 0.03)].pivot_table(index="n", columns="level", values="positives_needed").reset_index()
isu.columns = ["n"] + ["lvl %.5g" % c for c in isu.columns[1:]]
sens = FB[(FB.kind == "test") & (FB.domain == "Test B") & (FB.n == 40)].pivot_table(index=["level_label"], columns="rho_s0", values="positives_needed").reset_index()
ch = DEC["chosen_w_P1N"]
nrep = int(G.nrep.iloc[0])
gd = DEC["guard"]

txt = f"""# Graph weights (D018 section 3, item g) and fallback tables (A3), 2026-11-05

**Simulation outputs only.** Models and inputs as in `RESULT.md` section 2 (no Samsung score, no outer-test data). Fallback test: Beta-binomial sign test, rho_s0 = 0.03.
Files: `g_weights.csv`, `g_guard.csv`, `g_decision.json`, `fb_tables.csv`, `f_upper_bound_coverage.csv`; code `sim_v4.py` (items `gsim`, `gguard`, `gdecide`), `build_fb_tables.py`,
`code/pinnkan/graph_test.py` (additive: `pinnkan_graph(w_p)`, `betabin_*`, `dep_*`, `secondary_graph`, `sign_icc_anova`, `dependence_report`), tests `code/tests/test_fallback_weights_secondary.py` and `test_graph_test.py`: all pass.

## 1. Decision (printed by the script; no person chooses)

**Rule (D018 section 3):** adopt w = 0.78 on P1N (0.22 on K1) iff the implementation guard passes and, in all four settings, dP + dK > 0 and dK >= -0.10, where dP = change in P(P chain through P3) and dK = change in P(K1), both w = 0.78 minus w = 1/2.

**Result: the rule picks w = {ch:.2f} on P1N and {1 - ch:.2f} on K1** (initial levels 0.0195 and 0.0055; positives needed 30 and 32 of 40 under rho_s0 = 0.03).
Guard: maximum FWER over the 72 configurations x 2 settings = {gd['max_fwer']:.4f}, bound 0.025 + 2 MC SE = {gd['bound']:.4f}: passed = {gd['passed']}.

## 2. Simulation: both graphs on the same draws

Generator: arm model of RESULT section 2, ISU-like right skew; P side rho(A1,D*) 0.75, rho(A1,A9) 0.95, r1 = 0.20, r2 = 0.15, r4 = 0.05, corr(g1,g4) 0.6; K side A15 as good as A1 (excess 0.00), q = 0.05 over G15,
rho(A15,A1) = rho(A15,G15) = rho_K. Settings: independent conditions or intra-fold 0.10 with intra-lab 0.05 (random labs, the pessimistic reading) x rho_K 0.90 / 0.95; {nrep} replicates per setting; both graphs use the same L draws (common random numbers); seeds SeedSequence([20261105, crc32(name)]).
Both chains run in the graph together (the K chain is not forced to fail): hand-overs act. "P(..,P3)" = P(P1N, P1S, P2 and P3 all rejected).

{md(t1, ".3f")}

Differences (0.78 minus 0.5) with the paired Monte Carlo SE:

{md(t2, ".4f")}

Rule check:

{md(t3, ".4f")}

**Reading.** At w = 0.78 the P chain through P3 gains 0.12 to 0.16 (about 0.49 against 0.37 with clustering, 0.52-0.53 against 0.36 without), and K1 loses 0.036 to 0.047 (0.73 to 0.69 at rho_K 0.95 with clustering, 0.78 to 0.73 without). The K chain's last
node K2S is almost unchanged (it needs a gain that is rare at q = 0.05). The K1 floor of -0.10 is far from binding. The trade-off is disclosed in the paper whichever w is used (D018 section 3). These are simulation values under the stated generator, not results.

## 3. Implementation guard

Item (d)'s 72 configurations with weights 0.78 / 0.22, fallback counts, 50,000 replicates each (MC SE of a rate near 0.02: {gd['mc_se']:.4f}):

{md(gm, ".4f")}

Both maxima are below 0.025 (bound {gd['bound']:.4f}). With clustering the maximum is higher than at w = 1/2 (the P chain's first node now runs at 0.0195), still within the bound. The guard passed, so the decision rule applies. Unit test (`test_weight_alternative_initial_levels_and_counts`): initial levels 0.0195 and 0.0055; counts 30 and 32;
P(BetaBin >= 32) = 0.005352 <= 0.0055 and P(BetaBin >= 30) = 0.019356 <= 0.0195; hand-worked chain and K1 threshold tests also pass (30 positives reject the whole P chain at w = 0.78 and nothing at w = 1/2; K1 needs 32).

## 4. Fallback tables (A3, `fb_tables.csv`)

`fb_tables.csv` holds, for rho_s0 in (0, 0.01, 0.02, 0.03, 0.05), Test B n = 40 down to 35 and ISU n = 63 down to 58, the positives needed at every level in use (0.005, 0.00625, 0.00833, 0.0125, 0.025, and 0.0195 / 0.0055 for w = 0.78) with the size under the Beta-binomial null,
the size under independence and the one-sided lower-bound order statistic L_(n-k+1); and the interval ranks (two-sided 0.05, 0.05/9, 0.05/18) with their coverage. The Test B minimum is 36: only four z-type outer-test cells are exposed before the freeze (3.3(11), BL), so at most four conditions can be dropped; 35 is a margin.
ISU has 63 conditions (62 with both pilot scores, 60 at the 6-week window); the ISU rows apply only if the ISU fallback applies (D005), and the dependence simulation was for the Samsung fold/lab structure (D018 GAP-5).

Positives needed (rho_s0 = 0.03), Test B ("lvl" = local level):

{md(tb, ".0f")}

ISU:

{md(isu, ".0f")}

Interval ranks r (the interval is [L(r), L(n+1-r)]; r = 0 means no pair attains the level and the labelled range (min, max) is used), rho_s0 = 0.03:

{md(iv, ".0f")}

At n = 40 the 95 % interval is [L(11), L(30)] (coverage 0.9613 = 1 - 2 x 0.0194; the plain exact test gives rank 14) and the simultaneous 1 - 0.05/9 interval is [L(8), L(33)] (0.9950), as D018 2.1 states.
**Confirmation requested by the lead (PREREG_v4 rev. 1).** The unadjusted 95 % interval under the fallback at n = 40 is rank 11, [L(11), L(30)], coverage 0.961288 = 1 - 2 x 0.019356, where 0.019356 = P(BetaBin >= 30) (rho_s0 = 0.03); rank 12 would have coverage 1 - 2 x P(BetaBin >= 29) < 0.95, so 11 is the largest admissible rank. Confirmed from `fb_tables.csv` (row kind = interval, Test B, n = 40, rho_s0 = 0.03, two-sided 0.05): rank 11, lo index 11, hi index 30, coverage 0.961288. The simultaneous 1 - 0.05/9 interval is rank 8, [L(8), L(33)], coverage 0.995010.

Dependence-sensitivity counts at n = 40 (rows: level; columns: rho_s0):

{md(sens, ".0f")}

## 5. Item (f): estimator of the one-sided upper limit (defined in code before the freeze)

`graph_test.sign_icc_anova(signs, groups, conf=0.95)`: one-way ANOVA intraclass correlation of the 0/1 sign indicators (indicator that a condition's inner-CV training-side score difference exceeds its median) with groups = outer folds, and with groups = majority labs.
Upper limit (Searle, one-way random model, unbalanced through n0): F = MSB/MSW; F_U = F x F(0.95; N-k, k-1); rho_U = (F_U - 1)/(F_U + n0 - 1). `avg_pairwise_sign_corr` converts the intra-fold and intra-lab values into the average pairwise sign correlation that rho_s0 bounds
((same-fold pairs x rho_F + same-lab pairs x rho_L)/C(N,2); 140 and 313 of 780 pairs for the Test B structure; negatives set to 0). `dependence_report` returns point values and upper limits and the flag `exceeds_rho_s0` (intra-fold point estimate > 0.03), which triggers the fixed Limitations sentence of D018 2.3 (ii). It changes no count and no tier.

Behaviour in simulation (40 conditions, 5 folds of 8, Gaussian latent fold effect; 4,000 replicates; true sign correlation = (2/pi) asin(ICC)):

{md(CV, ".3f")}

**Caution to state with it:** with 5 folds the upper limit is very wide (mean 0.32 to 0.52) and the point estimate exceeds 0.03 in 38 % of replicates even with no fold effect, so the "exceeded the assumed value" sentence will often be printed and carries little information; the limit is reported evidence, as D018 rules.

## 6. Secondary graph (GAP-2): hand-worked unit tests

`secondary_graph(5)` (nodes N1..N5, S1..S5; weights 1/5 on each N_i, 0 on S_i; edges N_i -> S_i = 1, S_i -> N_j = 1/4) is tested in `test_fallback_weights_secondary.py` with hand-worked cases:
the structure and the initial level 0.005; reduction to Holm when every S_i is rejected (p_N = 0.001, 0.0055, 0.008, 0.02, 0.5: levels at rejection 0.005, 0.00625, 0.00833, then 0.0125 stops; p_N = 0.001, 0.0055, 0.008, 0.012, 0.02 rejects all five); equality with Holm on 200 random p-vectors; FWER under independent uniform nulls <= 0.025.

**Finding for the designer (not a change):** with the graph exactly as written in PREREG_v4 9.5, a test whose S_i is **not** rejected keeps its level at S_i and never releases it. A family in which most tests end at tier N therefore does **not** gain Holm's rising levels:
p_N = (0.001, 0.006, 1, 1, 1) with p_S = 1 rejects only N1 (N2 stays at 0.005), whereas Holm on the N p-values alone would reject N2 (0.006 <= 0.00625). The reduction to Holm holds when each test's S node is rejected (or with one node per test). The procedure remains valid (Bonferroni-based); it is only more conservative for tier-N results.

## 7. Limits
- All numbers are simulation values under the generator of RESULT section 2 (rho_s0 = 0.03 assumed adequate; no measured dependence). The decision rule uses one P-side and one K-side effect size, as fixed in D018 section 3; other effect sizes were not simulated.
- 20,000 replicates per setting (paired SE of a difference about 0.002); 50,000 per guard configuration.
- Counts at reduced n were tabulated, not simulated for size (the dependence simulation covered n = 40, as D018 discloses).
"""
open(P("RESULT_weights.md"), "w", encoding="utf-8").write(txt)
print("written", len(txt))
