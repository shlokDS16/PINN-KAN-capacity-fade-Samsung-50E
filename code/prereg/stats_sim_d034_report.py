"""Builds runs/prereg/stats_sim_v4/RESULT_D034.md and d034_decision.json from the CSV files written by stats_sim_d034.py.
SIMULATION OUTPUTS ONLY.  Usage: python -P stats_sim_d034_report.py"""
import os
import sys
import glob
import json

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "runs", "prereg", "stats_sim_v4")
import numpy as np      # noqa: E402
import pandas as pd     # noqa: E402

BOUND_SD = 2


def T(df, fmt="%.3f", cols=None):
    cols = cols or list(df.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            cells.append((fmt % v) if isinstance(v, (float, np.floating)) else str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def cat(pattern):
    fs = sorted(glob.glob(os.path.join(OUT, pattern)))
    return pd.concat([pd.read_csv(f) for f in fs], ignore_index=True), [os.path.basename(f) for f in fs]


def mde80(deltas, power):
    """Smallest delta with power >= 0.8, linear interpolation on the grid (coarse: grid 0, .05, .10, .15, .20, .30, .40)."""
    for i in range(1, len(deltas)):
        if power[i] >= 0.8 > power[i - 1]:
            return deltas[i - 1] + (0.8 - power[i - 1]) * (deltas[i] - deltas[i - 1]) / (power[i] - power[i - 1])
    return float("nan")


pw, f_pw = cat("d034_p3_power_*.csv")
sz, f_sz = cat("d034_p3_size_*.csv")
gd, f_gd = cat("d034_guard_k*.csv")
ch = pd.read_csv(os.path.join(OUT, "d034_chain.csv"))
m3, f_m3 = cat("d034_m3_*.csv")
old_w = pd.read_csv(os.path.join(OUT, "g_weights.csv"))
chk = json.load(open(os.path.join(OUT, "d034_checks.json")))
SET_LAB = {(0.0, 0.0): "independent conditions", (0.1, 0.0): "intra-fold 0.10", (0.1, 0.05): "intra-fold 0.10, intra-lab 0.05"}

# ------------------------------------------------------------------ P3 stand-alone power
base = pw[(pw["shape"] == "isu_right") & (pw.rho1 == 0.75) & (pw.kappa14 == 0.6)]
rows = []
for (f, l), lab in SET_LAB.items():
    for d in (0.05, 0.10, 0.15, 0.20, 0.30):
        r = base[(base.f == f) & (base.l == l) & (np.isclose(base.delta, d))].iloc[0]
        rows.append(dict(clustering=lab, median_D=d, old_fb30=r.fb30_old, new_fb30=r.fb30_new, old_fb31=r.fb31_old, new_fb31=r.fb31_new,
                         old_plain=r["plain_0.0125_old"], new_plain=r["plain_0.0125_new"]))
t_pw = pd.DataFrame(rows)
size0 = base[(base.f == 0) & (base.l == 0) & (base.delta == 0)].iloc[0]
size_clu = base[(base.f == 0.10) & (base.l == 0.05) & (base.delta == 0)].iloc[0]

mrows = []
for sh in ("isu_right", "normal", "isu_left"):
    for rho1 in (0.6, 0.75, 0.9):
        for kap in (0.3, 0.6, 0.9):
            for (f, l) in ((0.0, 0.0), (0.1, 0.05)):
                q = pw[(pw["shape"] == sh) & (pw.rho1 == rho1) & (pw.kappa14 == kap) & (pw.f == f) & (pw.l == l)].sort_values("delta")
                if len(q) < 7:
                    continue
                mrows.append(dict(shape=sh, rho1=rho1, kappa14=kap, clustering=SET_LAB[(f, l)],
                                  mde_old_fb30=mde80(q.delta.values, q.fb30_old.values), mde_new_fb30=mde80(q.delta.values, q.fb30_new.values)))
mde = pd.DataFrame(mrows)
mde["gain_in_delta"] = mde.mde_old_fb30 - mde.mde_new_fb30
sel = mde[(mde["shape"] == "isu_right") & (mde.rho1 == 0.75) & (mde.kappa14 == 0.6)]
mde_rng = mde.dropna()
nonneg = bool((pw.fb30_new >= pw.fb30_old - 0.004).all())            # allow MC noise (SE of a rate <= 0.0025 at 40,000)
min_gain_pw = float((pw.fb30_new - pw.fb30_old).min())

# ------------------------------------------------------------------ chain
cp = ch[(ch.kappa14 == 0.6) & (ch.r1 == 0.20) & (np.isclose(ch.r_c, 0.05))].copy()
cp["clustering"] = [SET_LAB[(f, l)] for f, l in zip(cp.f, cp.l)]
ow = old_w[old_w.w_P1N.astype(str) == "0.78"]
chain_old_prior = {(round(r.f, 2), round(r.rhoK, 2)): r.P_P3 for _, r in ow.iterrows()}
cp["prior_P3_RESULT_weights"] = [chain_old_prior.get((round(f, 2), round(rk, 2)), np.nan) for f, rk in zip(cp.f, cp.rhoK)]
t_chain = cp[["clustering", "rhoK", "P_Pp", "P_P2", "P_P3_old", "prior_P3_RESULT_weights", "P_P3_new", "d_P3", "se_d_P3", "P_K1"]]

cv = ch[(ch.rhoK == 0.95) & (ch.kappa14 == 0.6) & (ch.r1 == 0.20)].copy()
cv["clustering"] = [SET_LAB[(f, l)] for f, l in zip(cv.f, cv.l)]
t_rc = cv[["clustering", "r_c", "P_P3_old", "P_P3_new", "d_P3", "P3_node_alone_new"]]
ck = ch[(ch.rhoK == 0.95) & (ch.r1 == 0.20) & (np.isclose(ch.r_c, 0.05))].copy()
ck["clustering"] = [SET_LAB[(f, l)] for f, l in zip(ck.f, ck.l)]
t_kap = ck[["clustering", "kappa14", "P_P3_old", "P_P3_new", "d_P3"]]
cr1 = ch[(ch.rhoK == 0.95) & (ch.kappa14 == 0.6) & (np.isclose(ch.r_c, 0.05))].copy()
cr1["clustering"] = [SET_LAB[(f, l)] for f, l in zip(cr1.f, cr1.l)]
t_r1 = cr1[["clustering", "r1", "P_Pp", "P_P3_old", "P_P3_new", "d_P3"]]

# ------------------------------------------------------------------ size of P3 (a)-type
REG = [("R1: fold <= 0.05, lab 0", lambda d: (d.f <= 0.05) & (d.l == 0)), ("R2: fold <= 0.10, lab 0", lambda d: (d.f <= 0.10) & (d.l == 0)),
       ("R3: fold <= 0.10, lab <= 0.02", lambda d: (d.f <= 0.10) & (d.l <= 0.02)), ("R4: fold <= 0.10, lab <= 0.05", lambda d: (d.f <= 0.10) & (d.l <= 0.05)),
       ("R5: fold <= 0.20, lab <= 0.05", lambda d: (d.f <= 0.20) & (d.l <= 0.05)), ("R6: fold <= 0.20, lab <= 0.10", lambda d: (d.f <= 0.20) & (d.l <= 0.10))]
rnd = sz[(sz.labmode == "random") & (sz.kappa14 == 0.6)]
srows = []
for name, fn in REG:
    q = rnd[fn(rnd)]
    srows.append({"region": name, "P3_new_vs_0.0195": q.fb30_new.max() / 0.0195, "P3_new_vs_0_025": q.fb30_new.max() / 0.025,
                  "P3_old_vs_0_0195": q.fb30_old.max() / 0.0195, "M3_g1_vs_0_025": q.fb30_g1.max() / 0.025})
t_size = pd.DataFrame(srows)
r4 = t_size[t_size.region.str.startswith("R4")].iloc[0]
size_pass_R4 = bool(r4["P3_new_vs_0.0195"] <= 1.2 and r4["M3_g1_vs_0_025"] <= 1.2)
fix = sz[sz.labmode == "fixed"]
fix_max_new = float(fix.fb30_new.max() / 0.0195)
kapt = sz[(sz.labmode == "random") & (sz["shape"] == "isu_right") & (((sz.f == 0.1) & (sz.l == 0.05)) | ((sz.f == 0.05) & (sz.l == 0.0)) | ((sz.f == 0.0) & (sz.l == 0.0)))]
t_kapsize = kapt[["kappa14", "f", "l", "fb30_old", "fb30_new", "fb30_g1"]].sort_values(["f", "l", "kappa14"])
exceed = rnd[(rnd.fb30_new / 0.0195 > 1.2)][["shape", "f", "l", "fb30_new"]]
exceed_old = rnd[(rnd.fb30_old / 0.0195 > 1.2)][["shape", "f", "l", "fb30_old"]]
exceed_g1 = rnd[(rnd.fb30_g1 / 0.025 > 1.2)][["shape", "f", "l", "fb30_g1"]]

# ------------------------------------------------------------------ guard
grows = []
for kap, g in gd.groupby("kappa14"):
    for st, h in g.groupby("setting"):
        i = h.fwer.idxmax()
        grows.append(dict(kappa14=kap, setting=st, configs=len(h), max_FWER=h.fwer.max(), config_at_max=h.loc[i, "cfg"], mean_FWER=h.fwer.mean(), nrep=int(h.nrep.iloc[0])))
t_guard = pd.DataFrame(grows)
se = float(np.sqrt(0.025 * 0.975 / t_guard.nrep.iloc[0]))
bound = 0.025 + BOUND_SD * se
guard_max = float(gd.fwer.max())
guard_pass = bool(guard_max <= bound)
guard_pass_k06 = bool(gd[gd.kappa14 == 0.6].fwer.max() <= bound)
prior_guard = json.load(open(os.path.join(OUT, "g_decision.json")))["guard"]["max_fwer"]

# ------------------------------------------------------------------ M3
m3["rel_loss"] = 1 - m3.P_Pplus_M3pass / m3.P_Pplus
m3["abs_loss"] = m3.P_Pplus - m3.P_Pplus_M3pass
prim = m3[(m3["shape"] == "isu_right") & (m3.r1 == 0.20) & (m3.rhoK == 0.95)]
rows = []
for (f, l), lab in ((k, v) for k, v in SET_LAB.items() if k in ((0.0, 0.0), (0.1, 0.05))):
    for gR in sorted(prim.gR.unique()):
        r = dict(clustering=lab, gR=gR)
        q0 = prim[(prim.f == f) & (prim.l == l) & (prim.gR == gR)]
        r["P(P+)"] = q0.P_Pplus.iloc[0]
        for rr in (0.5, 0.75, 0.9):
            r["P(P+ & M3) rhoR=%.2f" % rr] = q0[q0.rhoR == rr].P_Pplus_M3pass.iloc[0]
        rows.append(r)
t_m3 = pd.DataFrame(rows)
BANDS = [("anchored: gR 0.40-0.60", (0.40, 0.60)), ("moderate: gR 0.20-0.30", (0.20, 0.30)), ("weak: gR 0.10-0.15", (0.10, 0.15)), ("none: gR 0-0.05", (0.0, 0.05))]
brow = []
pr = m3[m3["shape"] == "isu_right"]
for name, (lo, hi) in BANDS:
    q = pr[(pr.gR >= lo - 1e-9) & (pr.gR <= hi + 1e-9)]
    brow.append(dict(band=name, abs_loss_min=q.abs_loss.min(), abs_loss_max=q.abs_loss.max(), rel_loss_min=q.rel_loss.min(), rel_loss_max=q.rel_loss.max(),
                     P_Pplus_min=q.P_Pplus.min(), P_Pplus_max=q.P_Pplus.max(),
                     P_title_after_min=q.P_Pplus_M3pass.min(), P_title_after_max=q.P_Pplus_M3pass.max()))
t_band = pd.DataFrame(brow)
shp = m3[(m3.r1 == 0.20) & (m3.rhoK == 0.95) & (m3.rhoR == 0.75) & (m3.gR.isin([0.05, 0.10, 0.15, 0.20, 0.30]))]
t_shape = shp.pivot_table(index=["shape", "gR"], columns="f", values="rel_loss").reset_index()
t_shape.columns = ["shape", "gR", "rel_loss_independent", "rel_loss_fold10_lab05"]
# P3 chain with M3
p3m = prim[(prim.rhoR == 0.75) & (prim.gR.isin([0.10, 0.20, 0.30, 0.60]))][["f", "gR", "P_P3chain", "P_P3chain_M3pass"]]

# ------------------------------------------------------------------ text
now = pd.Timestamp.now().strftime("%Y-%m-%d")
rc_ = ch[(ch.rhoK == 0.95) & (ch.kappa14 == 0.6) & (ch.r1 == 0.20) & (ch.f == 0)]
rc10, rc05 = rc_[np.isclose(rc_.r_c, 0.10)].iloc[0], rc_[np.isclose(rc_.r_c, 0.05)].iloc[0]
p20 = base[(base.f == 0) & (base.l == 0) & np.isclose(base.delta, 0.20)].iloc[0]
cp_iid = cp[(cp.f == 0)].iloc[0]
cp_clu = cp[(cp.f == 0.1)].iloc[0]
cp_iid95 = cp[(cp.f == 0) & (cp.rhoK == 0.95)].iloc[0]
cp_clu95 = cp[(cp.f == 0.1) & (cp.rhoK == 0.95)].iloc[0]
cp_all = cp
lo_old, hi_old = cp_all.P_P3_old.min(), cp_all.P_P3_old.max()
lo_new, hi_new = cp_all.P_P3_new.min(), cp_all.P_P3_new.max()
band_a, band_m, band_w, band_n = [t_band.iloc[i] for i in range(4)]
Pp_lo, Pp_hi = prim.P_Pplus.min(), prim.P_Pplus.max()
verdict = "PASS" if guard_pass else "FAIL"

md = f"""# D034 re-simulation: P3 against (32, 2), modifier M3, FWER guard of the primary graph ({now})

**Simulation outputs only.** Every number below is a property of the generating model of `RESULT.md` section 2 (code `sim_v4.py`, extended by
`code/prereg/stats_sim_d034.py`), not a result about PINN-KAN, the Samsung cells or any real data. No Samsung capacity value, outer-test score or
outer-test prediction was opened or produced; inputs are the condition identifiers/folds/labs (`cond_structure.csv`) and the ISU training-side
shape of the skew (`stats_ruling/cond_isu_W4.csv`), as before. CPU only, 3 processes. Role: statistician. Reading depth: full text of
`debates/D033_signoff/01_judge.md` (AD1, AD2), `RESULT_weights.md`, `RESULT.md` sections 1-5.3, `sim_v4.py` (generator, items b, d, g); `DECISIONS.md` D033, D034;
PREREG_v4 4.1-4.2 and 9.x partly (grep of the P+/PC-3/R1 passages).
Files: `d034_p3_power_*.csv`, `d034_p3_size_*.csv` (+ `d034_size_hist_*.json`), `d034_guard_k*.csv`, `d034_chain.csv`, `d034_m3_*.csv`, `d034_checks.json`, `d034_decision.json`,
logs `log_d034_*.txt`; code `code/prereg/stats_sim_d034.py` (simulation) and `code/prereg/stats_sim_d034_report.py` (this file).
Seeds: `SeedSequence([20261105, crc32(name)])`, names prefixed `d034`. Replicates: 40,000 (power, chain, M3), 100,000 per size scenario, 50,000 per guard configuration.

## 0. Verdicts

| Item | Finding (simulation) |
|---|---|
| **FWER guard of the primary graph, w = 0.78, new P3 contrast** | **{verdict}.** Maximum FWER over 72 configurations x 2 settings = {t_guard[t_guard.kappa14 == 0.6].max_FWER.max():.4f} at corr(g1, g4) = 0.6 (plan value) and {guard_max:.4f} over corr 0.3 / 0.6 / 0.9; bound 0.025 + 2 MC SE = {bound:.4f}. Before D034 (RESULT_weights.md): {prior_guard:.4f}. |
| P3 power at the plan's effect sizes | up. With the plan's chain (r1 0.20, r2 0.15, gain at (32,2) = 0.05, rho 0.75, corr(g1,g4) 0.6, w = 0.78) P(P1N,P1S,P2,P3) rises from {cp_iid95.P_P3_old:.3f} to {cp_iid95.P_P3_new:.3f} (independent conditions) and from {cp_clu95.P_P3_old:.3f} to {cp_clu95.P_P3_new:.3f} (intra-fold 0.10, intra-lab 0.05); P3 alone (30 of 40) at a true median D of 0.15 / 0.20: {base[(base.f == 0) & (base.l == 0) & np.isclose(base.delta, 0.15)].iloc[0].fb30_old:.2f} to {base[(base.f == 0) & (base.l == 0) & np.isclose(base.delta, 0.15)].iloc[0].fb30_new:.2f} and {p20.fb30_old:.2f} to {p20.fb30_new:.2f}. |
| Size of the P3 node (new contrast) | In region R4 (intra-fold <= 0.10, intra-lab <= 0.05, the region the fallback was set for) the worst simulated rejection rate of the 30-of-40 rule is {r4['P3_new_vs_0.0195']:.2f} x 0.0195 ({r4['P3_new_vs_0_025']:.2f} x 0.025); the old contrast gave {r4['P3_old_vs_0_0195']:.2f} x 0.0195. Inside R4 the node is below 1.2 x nominal: {'yes' if r4['P3_new_vs_0.0195'] <= 1.2 else 'NO'}. Outside R4 see section 4. |
| M3 (A1 not better than R1 at g1; 30 of 40; outside the graph) | The test has the same size as every other 30-of-40 node ({r4['M3_g1_vs_0_025']:.2f} x 0.025 at worst in R4). Effect on P(P+ title) (title = P+ with M3 passing; M1/M2 ignored): **loss 0 to {band_n.abs_loss_max:.2f} in absolute probability over the whole assumption range**, {band_a.abs_loss_min:.3f} to {band_a.abs_loss_max:.3f} if A1 beats persistence by 40-60 % (the training-side pilot ratio), {band_m.abs_loss_min:.2f} to {band_m.abs_loss_max:.2f} at 20-30 %, {band_w.abs_loss_min:.2f} to {band_w.abs_loss_max:.2f} at 10-15 %. See section 6. |

## 1. What changed and the assumption about L_c(32, 2)

**AD1.** P3 now tests the sign of D_c = L_c(g1) - L_c(32, 2), g1 = (m 8, k 2), same window, forecast set and caps at both cells.
**What the generator says about L_c(32, 2) against L_c(32, 4) (= g4).** `sim_v4.py` models the 9 grid cells (m = 8, 16, 32 by k = 0, 2, full; cell index 3 i_m + i_k, g1 = 1, (32,2) = 7, g4 = 8) with a **separable AR(1) latent variable**, coefficient a in both directions, corr(g1, g4) = a^3 = kappa14, and
a fold/lab share that depends on **m only** (multiplier 1 / 0.75 / 0.5, "same for every k"). Nothing else links the cells. Three consequences, none invented:
1. corr(L(g1), L(32,2)) = a^2 = kappa14^(2/3): **{chk['corr(L1g1, Lc) at kappa14 = 0.6']:.3f}** at the plan's 0.6 (it was 0.6 for g4); 0.448 and 0.932 for the 0.3 and 0.9 sensitivity values. corr(L(32,2), L(32,4)) = a = 0.843.
2. (32,2) has the **same fold/lab share and the same marginal law** as g4, so a (g1, (32,2)) contrast differs from a (g1, g4) contrast only through the cross-cell correlation: the new D model with kappa14 equals the old D model with kappa = kappa14^(2/3) (checked to 1e-9, `d034_checks.json`; the K and P1/P2 contrasts reproduce `sim_v4.build_model` to 1e-15).
3. **The generator does not say how large the PINN-KAN advantage is at (32,2).** The plan's effect sizes are a gain r1 at g1 and a gain r4 at g4 (the median of D is their difference on the log scale). I carry the gain at (32,2), r_c, as a parameter: the main reading is **r_c = r4 = 0.05** (k does not change the advantage at m = 32, the same way k does not change the fold/lab share in the generator), and r_c = 0, 0.10, 0.15 are shown (section 3.2). A smaller r_c is more favourable to P3 (larger median D). Power is also given as a function of the median of D itself (3.1), which needs no reading of r_c.
Whether the advantage really depends on k at fixed m is an empirical question that no file answers; if (32,2) lies between g1 and g4 in advantage, the median D is smaller than in the plan and power is lower than shown.

## 2. P3 power

### 2.1 P3 alone: sign test of D > 0, ISU-like right skew, rho(A1,D*) 0.75, corr(g1,g4) = 0.6 (so corr(g1,(32,2)) = 0.711), fallback rho_s0 = 0.03

"fb30" = 30 of 40, the count at both levels P3 can face with w = 0.78 (0.0195 with the P chain alone, 0.025 after the K chain); "fb31" = 31 of 40, the 0.0125 count of the earlier tables (RESULT.md 5.3) shown for comparison; old = D = L(g1) - L(g4), new = D = L(g1) - L(32,2); both have median D = "median_D" and come from the same draws.

{T(t_pw)}

Size at median D = 0 (30 of 40): {size0.fb30_new:.4f} independent conditions; {size_clu.fb30_new:.4f} with intra-fold 0.10 and intra-lab 0.05 (copula form of items b-d, all contrasts share the same fold and lab shares).
80 %-power median D (30 of 40, linear interpolation on the grid 0, .05, .10, .15, .20, .30, .40): old {sel[sel.clustering == 'independent conditions'].mde_old_fb30.iloc[0]:.3f}, new {sel[sel.clustering == 'independent conditions'].mde_new_fb30.iloc[0]:.3f} (independent); old {sel[sel.clustering != 'independent conditions'].mde_old_fb30.iloc[0]:.3f}, new {sel[sel.clustering != 'independent conditions'].mde_new_fb30.iloc[0]:.3f} (clustered). Over all shapes, rho(A1,D*) 0.6 / 0.75 / 0.9 and corr 0.3 / 0.6 / 0.9 the new 80 % point is lower than the old by {mde_rng.gain_in_delta.min():.3f} to {mde_rng.gain_in_delta.max():.3f} (log units of median D). {'The new contrast has no lower power than the old one at equal median D beyond Monte Carlo noise (SE of a rate <= 0.0025) in any of the ' + str(len(pw)) + ' cells simulated' if nonneg else 'The new contrast is below the old one by more than Monte Carlo noise in some cells of the ' + str(len(pw)) + ' simulated'} (smallest difference {min_gain_pw:+.4f}; the gain comes only from the higher correlation, 0.711 against 0.6).

### 2.2 Why the power is higher, and what it does not mean
The SD of D falls because L(g1) and L(32,2) are more strongly correlated than L(g1) and L(g4). It is not evidence that the effect is larger: the **median D to be detected is a different quantity** whenever the gain at (32,2) differs from the gain at g4. Under r_c = r4 the medians coincide and the power gain is real; if the advantage at (32,2) lies above that at g4, the median D shrinks and part or all of the gain is lost (3.2: with independent conditions and rhoK 0.95, P(also P3) is {rc10.P_P3_new:.2f} at r_c = 0.10 and {rc05.P_P3_new:.2f} at r_c = 0.05).

## 3. P3 in the primary graph (w = 0.78, fallback counts, K chain running)

### 3.1 Plan point (rho(A1,D*) 0.75, rho(A1,A9) 0.95, r1 0.20, r2 0.15, r_c = r4 = 0.05, corr(g1,g4) 0.6, A15 as good as A1, K2 gain 0.05; {int(cp.nrep.iloc[0]):,} replicates; same draws for old and new)
`prior` = the value printed in `RESULT_weights.md` for the old contrast (20,000 replicates, different seeds; the difference to the `old` column, up to about 0.01, is Monte Carlo noise).

{T(t_chain)}


P(P1N,P1S) and P(also P2) do not change (the new contrast does not enter those nodes); only P3 does. `P_K1` is for the new contrast (K1 receives the P3 hand-over when P3 is rejected); the old-contrast values are in RESULT_weights.md (0.734 / 0.693 at rhoK 0.95, K1 median 0).
Range over the four settings: old {lo_old:.3f}-{hi_old:.3f}, new {lo_new:.3f}-{hi_new:.3f}.

### 3.2 Dependence on r_c (gain at (32,2)), rhoK 0.95, r1 0.20, corr(g1,g4) 0.6

{T(t_rc)}

### 3.3 Dependence on corr(g1,g4) (r1 0.20, r_c 0.05, rhoK 0.95) and on r1 (corr 0.6)

{T(t_kap)}

{T(t_r1)}

## 4. Size of the P3 node and of the M3 test (generator (a) of sim_v4: additive skew form, fold/lab share scaled by m, random lab effects = pessimistic reading)

Worst simulated rejection rate at the null boundary of the 30-of-40 rule, over the scenarios of each region (3 error shapes; corr(g1,g4) 0.6; {int(sz.nrep.iloc[0]):,} replicates per scenario; MC SE of a rate of 0.02: 0.0004), as a multiple of the nominal level. "P3 new" and "P3 old" are against 0.0195 (the P-chain level at w = 0.78; against 0.025 divide by 1.28); "M3 at g1" is the sign test of L_R1 > 0 at g1 against 0.025.

{T(t_size, "%.2f")}

* The re-open condition of D033 ("the node's size above 1.2 x nominal") is **not met inside R4** for the new contrast: worst {r4['P3_new_vs_0.0195']:.2f}. Beyond R4 the 30-of-40 rule (rho_s0 = 0.03) exceeds 1.2 x nominal in {len(exceed)} of {len(rnd)} scenario cells for the new contrast ({len(exceed_old)} for the old); the (intra-fold, intra-lab) pairs concerned are {sorted(set(zip(exceed.f, exceed.l)))}, i.e. {len(exceed[(exceed.f <= 0.10) & (exceed.l <= 0.05)])} scenario cells lie inside R4 (RESULT.md 4.4 already reported that the fallback does not cover R5-R6). The M3 test at g1 exceeds 1.2 x 0.025 in {len(exceed_g1)} scenario cells, {len(exceed_g1[(exceed_g1.f <= 0.10) & (exceed_g1.l <= 0.05)])} of them inside R4 (pairs: {sorted(set(zip(exceed_g1.f, exceed_g1.l)))}).
* The new contrast is slightly **less conservative** than the old one (higher cross-cell correlation, so less cancellation between the two cells): ratio new/old of the worst rate is {(rnd.fb30_new.max() / rnd.fb30_old.max()):.2f} over all random-effect scenarios.
* With lab effects as fixed design offsets (the optimistic reading), the worst new rate is {fix_max_new:.2f} x 0.0195 over {len(fix)} scenario cells.
* Sensitivity to corr(g1,g4) (isu_right, rates of the 30-of-40 rule; M3 at g1 does not depend on it):

{T(t_kapsize, "%.4f")}

## 5. FWER guard of the primary graph (w = 0.78 on P1N, 0.22 on K1; initial levels 0.0195 and 0.0055; counts 30 and 32)

Item (d)/(g) implementation guard re-run with the new P3 contrast: 72 configurations (L1 x L2 x D x K1 x K2 at null/mid/alt) x 2 settings (independent conditions; intra-fold 0.10 with intra-lab 0.05, random labs), fallback rho_s0 = 0.03, 50,000 replicates each (MC SE of a rate near 0.02: {se:.4f}). A configuration's FWER counts a replicate when any true-null node is rejected; D = null means median(L(g1) - L(32,2)) = 0. The graph test is valid under any dependence; this is an implementation check.

{T(t_guard, "%.4f")}

Bound = 0.025 + 2 x {se:.4f} = {bound:.4f}. Maximum over everything = {guard_max:.4f}; at the plan value (corr 0.6) {t_guard[t_guard.kappa14 == 0.6].max_FWER.max():.4f} (RESULT_weights.md, old contrast: {prior_guard:.4f}).
**FWER guard: {verdict}.** M3 is outside the graph and adds no rejection to it; the P+ title now requires P1S (graph) and M3, so the probability of a false P+ title cannot exceed the graph's FWER (intersection of two events). No alpha is added.

## 6. M3: effect on P(P+ title)

**Model.** R1 (persistence) is a further leaf of the arm tree below A1 (like D*, A9, A15), correlation rhoR of the log condition errors with A1, same error shape, same fold/lab shares as the other contrasts, same draws as the graph. L_R1 = ln S_R1 - ln S_A1 at g1; gR = true median relative gain of A1 over R1 (median L_R1 = ln(1/(1 - gR))). M3 passes iff at least 30 of 40 conditions have L_R1 > 0 (fallback, level 0.025). "P(P+)" = P(P1N and P1S rejected in the graph); "P(P+ title)" = P(P+ and M3 passes); the loss is the difference. Titles T1-T3 (and T9a/T9b) are what M3 removes; M1 and M2 are not modelled (M3 acts independently of them).
**What the files hold.** Nothing about A1 against R1 at g1: no Samsung value exists and no pilot file gives A1 against persistence at g1. The only anchor is the training-side pilot P3 (ISU W4/W6, SNL W100/W200, full training data, not g1, best data-only learner not A1): cell RMSE of persistence is 13.22 / 12.54 / 10.83 / 7.71 pp against 5.21 / 4.87 / 2.97 / 2.54 for tuned LightGBM, i.e. persistence is 2.5-3.6 times worse, a relative reduction of 0.60-0.72 for a learner. That is an RMSE ratio of means, not a median of condition log ratios, and at g1 (8 conditions, 2 check-ups) the learners are weaker; it is why the bands start at 0.40 for "anchored". rhoR is not anchored at all (0.50 / 0.75 / 0.90 shown).

Primary table (ISU-like skew, r1 0.20, rhoK 0.95, w = 0.78): P(P+ title) = P(P+ & M3) for each gR and rhoR, and P(P+) without M3.

{T(t_m3)}

Range over everything simulated (ISU-like skew; settings independent / clustered, rhoK 0.90 / 0.95, r1 0.15 / 0.20 / 0.25, rhoR 0.50 / 0.75 / 0.90; the band is the range of the gR values listed):

{T(t_band)}

Shape sensitivity (relative loss of P(P+ title), r1 0.20, rhoK 0.95, rhoR 0.75):

{T(t_shape)}

P(P1N,P1S,P2,P3 rejected) and with M3 passing (rhoR 0.75, rhoK 0.95, r1 0.20):

{T(p3m)}

**Reading.** P(P+) is {pr.P_Pplus.min():.2f}-{pr.P_Pplus.max():.2f} across all simulated P-side settings (r1 0.15-0.25) and {prim.P_Pplus.min():.2f}-{prim.P_Pplus.max():.2f} at the plan's r1 0.20. If A1 beats persistence by 30 % or more at g1, M3 costs at most {pr[pr.gR >= 0.30 - 1e-9].abs_loss.max():.2f} in absolute probability (rhoR <= 0.90) and at 40 % or more at most {pr[pr.gR >= 0.40 - 1e-9].abs_loss.max():.3f}; at a 20 % gain it costs {pr[np.isclose(pr.gR, 0.20)].abs_loss.min():.2f} to {pr[np.isclose(pr.gR, 0.20)].abs_loss.max():.2f} depending on rhoR and the setting; at 10-15 % it removes {band_w.rel_loss_min:.0%} to {band_w.rel_loss_max:.0%} of the P+ titles; at 0-5 % it removes {band_n.rel_loss_min:.0%} to {band_n.rel_loss_max:.0%}, which is the intended behaviour: a network no better than carrying the last check-up forward should not carry T1-T3. The loss is therefore not a fixed number: it is the probability that A1 is within roughly 10-20 % of persistence at g1 (more exactly, that fewer than 30 of 40 conditions favour A1), and no file holds that probability. The lower rhoR is, the more the 30-of-40 rule demands of a given gain.

## 7. Limits
* All numbers are simulation values under the generator of `RESULT.md` section 2; rho_s0 = 0.03 is assumed adequate (no measured dependence); the m-scaling of fold/lab shares in section 4 is the assumption of sim_v4 (1 / 0.75 / 0.5), while the power tables of sections 2-3 use one share for all contrasts, as items b-d did.
* The gain at (32,2), the effect of M3's R1 comparison (gR, rhoR) and the correlation of R1 with A1 are assumptions with no data behind them.
* Section 2.1's 80 % points are interpolated on a coarse grid. Section 4 covers the 3 error shapes, the guard only ISU-like right skew (as in RESULT_weights.md). Counts at reduced n were not simulated.
* Not tested here: the P3 contrast if (32,2) is capped or scored on fewer conditions than g1 (D032 lists capped cells; condition-level n stays 40).
"""
open(os.path.join(OUT, "RESULT_D034.md"), "w", encoding="utf-8").write(md)
dec = dict(fwer_guard=verdict, max_fwer_all=guard_max, max_fwer_kappa0_6=float(t_guard[t_guard.kappa14 == 0.6].max_FWER.max()), bound=bound, mc_se=se,
           prior_max_fwer=prior_guard, p3_size_R4_new_vs_0_0195=float(r4["P3_new_vs_0.0195"]), p3_size_pass_R4=size_pass_R4,
           chain_P3_plan={"iid_rhoK0.95": [float(cp_iid95.P_P3_old), float(cp_iid95.P_P3_new)], "cluster_rhoK0.95": [float(cp_clu95.P_P3_old), float(cp_clu95.P_P3_new)]},
           m3_loss_abs_by_band={r.band: [float(r.abs_loss_min), float(r.abs_loss_max)] for _, r in t_band.iterrows()},
           label="SIMULATION")
json.dump(dec, open(os.path.join(OUT, "d034_decision.json"), "w"), indent=1)
print("written", verdict, guard_max, bound)
