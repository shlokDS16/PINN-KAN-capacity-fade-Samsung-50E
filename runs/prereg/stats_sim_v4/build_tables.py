"""Builds tables.md (markdown tables keyed T:<name>) from the CSV outputs of sim_v4.py; RESULT.md takes them from there
(build_result.py replaces {{T:name}} in RESULT_template.md).  Reads only the CSV/JSON files in this folder.  Usage: python -P build_tables.py"""
import os
import sys
import json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0]]
sys.path.insert(0, HERE)
import sim_v4 as S                                   # noqa: E402  (constants and tail functions only)

P = lambda f: os.path.join(HERE, f)
T = {}


def md(df, floatfmt=".3f", index=False):
    return df.to_markdown(index=index, floatfmt=floatfmt)


def r(x, n=2):
    return ("%." + str(n) + "f") % x


# ------------------------------------------------------------------ (a)
A = pd.read_csv(P("a_size.csv"))
A["q1"] = A["rej_g1_0.0125"] / 0.0125
A["q2"] = A["rej_g1_0.025"] / 0.025
main = A[(A.kappa == 0.6) & (A.labmode == "random")]
for sh in ("normal", "isu_right", "isu_left"):
    m = main[main["shape"] == sh]
    fs, ls = (0.0, 0.02, 0.05, 0.10, 0.20), (0.0, 0.02, 0.05, 0.10, 0.20)
    rows = []
    for f in fs:
        row = {"fold ICC": f}
        for l in ls:
            x = m[(m.f == f) & (m.l == l)].iloc[0]
            row["lab ICC %.2f" % l] = "%s / %s%s" % (r(x.q1), r(x.q2), " *" if max(x.q1, x.q2) > 1.2 else "")
        rows.append(row)
    T["a_main_" + sh] = md(pd.DataFrame(rows))

fine = []
for f in (0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.15, 0.20, 0.30):
    row = {"fold ICC": f}
    for sh in ("normal", "isu_right"):
        x = main[(main["shape"] == sh) & (main.f == f) & (main.l == 0)].iloc[0]
        row[sh + " 0.0125"], row[sh + " 0.025"] = r(x.q1), r(x.q2)
    fine.append(row)
T["a_fine_fold"] = md(pd.DataFrame(fine))
fine = []
for l in (0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.10, 0.20):
    row = {"lab ICC (random)": l}
    for sh in ("normal", "isu_right"):
        x = main[(main["shape"] == sh) & (main.f == 0) & (main.l == l)].iloc[0]
        row[sh + " 0.0125"], row[sh + " 0.025"] = r(x.q1), r(x.q2)
    fine.append(row)
T["a_fine_lab"] = md(pd.DataFrame(fine))


def breakeven(sh, col, key):
    d = main[(main["shape"] == sh) & (main[key[1]] == 0)].sort_values(key[0])
    x, y = d[key[0]].to_numpy(), (d[col] / (0.0125 if "0.0125" in col else 0.025)).to_numpy()
    for i in range(1, len(x)):
        if y[i] > 1.2 >= y[i - 1]:
            return x[i - 1] + (1.2 - y[i - 1]) * (x[i] - x[i - 1]) / (y[i] - y[i - 1])
    return float("nan")


be = []
for sh in ("normal", "isu_right"):
    for col in ("rej_g1_0.0125", "rej_g1_0.025"):
        be.append({"shape": sh, "level": col.split("_")[-1] if col.endswith("0.025") else "0.0125", "fold ICC at which size = 1.2 x nominal (lab ICC 0)": breakeven(sh, col, ("f", "l")),
                   "lab ICC at which size = 1.2 x nominal (fold ICC 0)": breakeven(sh, col, ("l", "f"))})
be = pd.DataFrame(be)
be["level"] = be["level"].map(lambda x: {"0.0125": "0.0125", "0.025": "0.025"}[x])
T["a_breakeven"] = md(be, ".3f")

rows = []
for (f, l) in ((0.0, 0.0), (0.05, 0.0), (0.10, 0.0), (0.10, 0.05)):
    x = main[(main["shape"] == "isu_right") & (main.f == f) & (main.l == l)].iloc[0]
    row = {"fold ICC": f, "lab ICC": l}
    for g in range(9):
        row["m%d,k%d" % ((8, 16, 32)[g // 3], (0, 2, "full")[g % 3] if False else g % 3)] = r(x["rej_g%d_0.0125" % g] / 0.0125)
    row["D = L(g1)-L(g4)"] = r(x["rej_D_0.0125"] / 0.0125)
    row["D at 0.025"] = r(x["rej_D_0.025"] / 0.025)
    rows.append(row)
T["a_cells"] = md(pd.DataFrame(rows))

rows = []
for kap in (0.3, 0.6, 0.9):
    for (f, l) in ((0.0, 0.0), (0.05, 0.0), (0.10, 0.05)):
        x = A[(A["shape"] == "isu_right") & (A.kappa == kap) & (A.f == f) & (A.l == l) & (A.labmode == "random")].iloc[0]
        rows.append({"corr(g1,g4)": kap, "fold ICC": f, "lab ICC": l, "P3 size 0.0125": x["rej_D_0.0125"], "ratio": x["rej_D_0.0125"] / 0.0125,
                     "P3 size 0.025": x["rej_D_0.025"], "ratio ": x["rej_D_0.025"] / 0.025})
T["a_kappa"] = md(pd.DataFrame(rows), ".4f")

fx = A[A.labmode == "fixed"]
rows = [{"lab offsets (var share)": x.l, "fold ICC": x.f, "size g1 0.0125": x["rej_g1_0.0125"], "ratio": x.q1, "size g1 0.025": x["rej_g1_0.025"], "ratio ": x.q2} for _, x in fx.iterrows()]
T["a_fixedlab"] = md(pd.DataFrame(rows), ".4f")

# intervals: coverage under dependence (alpha/9 two-sided intervals, rank 11)
rows = []
for (f, l) in ((0.0, 0.0), (0.05, 0.0), (0.10, 0.0), (0.10, 0.05), (0.20, 0.05)):
    x = main[(main["shape"] == "isu_right") & (main.f == f) & (main.l == l)].iloc[0]
    cells = [x["cov_g%d_a9" % g] for g in range(9)]
    rows.append({"fold ICC": f, "lab ICC": l, "coverage at g1 (nominal 0.9944)": x["cov_g1_a9"], "min over 9 cells": min(cells),
                 "all 9 cells together (target 0.95)": x["cov_all9_a9"], "unadjusted 95 % intervals (r=14), all 9 together": x["cov_all9_a95"]})
T["e_cov"] = md(pd.DataFrame(rows), ".4f")


# per-cell coverage of the 1 - 0.05/9 intervals with the plain rank (11) and the fall-back rank (8)
H = json.load(open(P("a_hist.json")))
def _cov(h, rk):
    h = np.array(h, float)
    m = np.minimum(np.arange(S.N + 1), S.N - np.arange(S.N + 1))
    return ((m >= rk) * h).sum() / h.sum()
rows = []
for rn, msk in (("R3: fold <= 0.10, lab <= 0.02", (A.f <= 0.10) & (A.l <= 0.02)), ("R4: fold <= 0.10, lab <= 0.05", (A.f <= 0.10) & (A.l <= 0.05)),
                ("R5: fold <= 0.20, lab <= 0.05", (A.f <= 0.20) & (A.l <= 0.05)), ("R6: fold <= 0.20, lab <= 0.10", (A.f <= 0.20) & (A.l <= 0.10))):
    names = A[msk & (A.labmode == "random")].name
    row = {"region": rn}
    for rk in (11, 8):
        row["min per-cell coverage, rank %d" % rk] = min(_cov(H[nm][c], rk) for nm in names for c in range(9))
    rows.append(row)
T["e_cov_fb"] = md(pd.DataFrame(rows), ".4f")

# ------------------------------------------------------------------ fall-back
fbc = S.fb_crits()
rows = []
for rs in (0.0,) + S.FB_RHOS:
    t = S.tail_betabin(S.N, rs)
    k1, k2 = (S.KCRIT["0.0125"], S.KCRIT["0.025"]) if rs == 0 else (fbc[rs]["0.0125"], fbc[rs]["0.025"])
    # rank of the alpha/9 interval under this design effect
    r_int = 0
    for rr in range(1, 21):
        if 1 - 2 * (1 - t[rr]) >= 1 - 0.05 / 9 - 1e-12:
            r_int = rr
    rows.append({"rho_s0": rs, "design effect": S.de_of(rs), "positives needed at 0.0125": k1, "size under the BetaBin null": float(t[k1]), "positives needed at 0.025": k2,
                 "size under the BetaBin null ": float(t[k2]), "size if conditions independent (k1 / k2)": "%.4f / %.4f" % (S.TAIL[k1], S.TAIL[k2]), "rank r of 1-0.05/9 interval": r_int})
_fc = pd.DataFrame(rows)
for _c in ("positives needed at 0.0125", "positives needed at 0.025", "rank r of 1-0.05/9 interval"):
    _fc[_c] = _fc[_c].astype(int)
T["fb_crit"] = md(_fc, ".4f")

F = pd.read_csv(P("fb_size.csv"))
F["level"] = F["level"].map(lambda x: "%g" % x)
F = F[(F.labmode == "random") & (F.kappa == 0.6)]
regs = {"R1: fold <= 0.05, lab 0": (F.f <= 0.05) & (F.l == 0),
        "R2: fold <= 0.10, lab 0": (F.f <= 0.10) & (F.l == 0),
        "R3: fold <= 0.10, lab <= 0.02": (F.f <= 0.10) & (F.l <= 0.02),
        "R4: fold <= 0.10, lab <= 0.05": (F.f <= 0.10) & (F.l <= 0.05),
        "R5: fold <= 0.20, lab <= 0.05": (F.f <= 0.20) & (F.l <= 0.05),
        "R6: fold <= 0.20, lab <= 0.10": (F.f <= 0.20) & (F.l <= 0.10)}
rows = []
for rn, m in regs.items():
    row = {"region (random effects)": rn}
    for rs in (0.0,) + S.FB_RHOS:
        g = F[m & (F.rho_s0 == rs)]
        w1 = max(g[g.level == "0.0125"].ratio_max9.max(), g[g.level == "0.0125"].ratio_D.max())
        w2 = max(g[g.level == "0.025"].ratio_max9.max(), g[g.level == "0.025"].ratio_D.max())
        row["rho_s0=%.2f" % rs] = "%s / %s%s" % (r(w1), r(w2), " *" if max(w1, w2) > 1.2 else "")
    rows.append(row)
T["fb_region"] = md(pd.DataFrame(rows))


rows = []
for nm, a in (("0.005 (Holm 1/5)", 0.025 / 5), ("0.00625 (1/4)", 0.025 / 4), ("0.00833 (1/3)", 0.025 / 3), ("0.0125 (1/2; graph, one chain)", 0.0125), ("0.025 (graph, both chains; last Holm step)", 0.025)):
    row = {"local level": nm}
    for rs in (0.0, 0.02, 0.03):
        t = S.tail_betabin(S.N, rs)
        k = S.crit_from_tail(t, a)
        row["rho_s0=%.2f: positives needed" % rs] = k
    rows.append(row)
T["fb_crit_levels"] = md(pd.DataFrame(rows), ".0f")

B1 = pd.read_csv(P("b1_p1_power_iid.csv"))
B1["level"] = B1["level"].map(lambda x: "%g" % x)
mm = B1[B1.mde80.notna() & (B1.tier == "S")]
rows = []
for sh in ("normal", "isu_right", "isu_left"):
    for rho in (0.6, 0.75, 0.9):
        row = {"shape": sh, "rho": rho}
        for test in ("plain", "fb0.01", "fb0.02", "fb0.03", "fb0.05"):
            a = mm[(mm["shape"] == sh) & (mm.rho == rho) & (mm.test == test)]
            row[test] = "%s / %s" % (r(a[a.level == "0.0125"].mde80.iloc[0], 3), r(a[a.level == "0.025"].mde80.iloc[0], 3))
        rows.append(row)
T["b1_mde"] = md(pd.DataFrame(rows))

FE = pd.read_csv(P("fbest_size.csv"))
rows = []
for _, x in FE.iterrows():
    if x["shape"] == "isu_right" and x.de_floor in (1.0, 2.0):
        rows.append({"shape": x["shape"], "fold ICC": x.f, "lab ICC": x.l, "DE floor": x.de_floor, "reference": x.ref, "size 0.0125": x.size_0125, "size 0.025": x.size_025})
T["fb_est"] = md(pd.DataFrame(rows), ".4f")

# ------------------------------------------------------------------ (b)
rows = []
sub = B1[B1.mde80.isna() & (B1.tier == "S") & (B1.test.isin(["plain", "fb0.02", "fb0.03"])) & (B1.r.isin([0.10, 0.15, 0.20, 0.25, 0.30]))]
for sh in ("normal", "isu_right", "isu_left"):
    for rho in (0.6, 0.75, 0.9):
        for test in ("plain", "fb0.02", "fb0.03"):
            row = {"shape": sh, "rho": rho, "test": test}
            for lv in ("0.0125", "0.025"):
                for rr in (0.10, 0.15, 0.20, 0.25, 0.30):
                    pw = sub[(sub["shape"] == sh) & (sub.rho == rho) & (sub.test == test) & (sub.level == lv) & (sub.r == rr)].power.iloc[0]
                    row["%s r=%.2f" % (lv, rr)] = pw
            rows.append(row)
pw = pd.DataFrame(rows)
T["b1_power_0125"] = md(pw[["shape", "rho", "test"] + [c for c in pw.columns if c.startswith("0.0125")]], ".2f")
T["b1_power_025"] = md(pw[["shape", "rho", "test"] + [c for c in pw.columns if c.startswith("0.025")]], ".2f")

nn = B1[B1.mde80.notna() & (B1.tier == "N")]
rows = []
for sh in ("normal", "isu_right", "isu_left"):
    for rho in (0.6, 0.75, 0.9):
        row = {"shape": sh, "rho": rho}
        for test in ("plain", "fb0.03"):
            a = nn[(nn["shape"] == sh) & (nn.rho == rho) & (nn.test == test)]
            row[test + " (0.0125 / 0.025)"] = "%s / %s" % (r(a[a.level == "0.0125"].mde80.iloc[0], 3), r(a[a.level == "0.025"].mde80.iloc[0], 3))
        # power of P1N at true equality (r = 0)
        for test in ("plain", "fb0.03"):
            a = B1[(B1["shape"] == sh) & (B1.rho == rho) & (B1.tier == "N") & (B1.test == test) & (B1.r == 0.0)]
            row["power P1N at r=0, %s" % test] = "%s / %s" % (r(a[a.level == "0.0125"].power.iloc[0]), r(a[a.level == "0.025"].power.iloc[0]))
        rows.append(row)
T["b1_N"] = md(pd.DataFrame(rows))

B2 = pd.read_csv(P("b2_p1_power_dep.csv"))
rows = []
for _, x in B2[(B2.rho == 0.75) & B2.r.isin([0.10, 0.15, 0.20, 0.25])].iterrows():
    rows.append({"fold ICC": x.f, "lab ICC": x.l, "r": x.r, "plain 0.0125": x["plain_0.0125"], "fb 0.02 (30/40)": x["fb0.02_0.0125"], "fb 0.03 (31/40)": x["fb0.03_0.0125"],
                 "plain 0.025": x["plain_0.025"], "fb 0.03 0.025 (30/40)": x["fb0.03_0.025"]})
T["b2_dep"] = md(pd.DataFrame(rows), ".2f")

B3 = pd.read_csv(P("b3_chain.csv"))
sel = B3[(B3.kappa == 0.6) & (B3.extra == 0) & (B3.r4 == 0.05)]
rows = []
for kmode in ("K_never", "K_first"):
    for rho1 in (0.6, 0.75, 0.9):
        for r1 in (0.10, 0.15, 0.20, 0.30):
            for r2 in (0.15,):
                x = sel[(sel.kmode == kmode) & (sel.rho1 == rho1) & (sel.r1 == r1) & (sel.r2 == r2)]
                if len(x):
                    x = x.iloc[0]
                    rows.append({"K chain": kmode, "rho(A1,D*)": rho1, "r1 (g1 gain vs D*)": r1, "r2 (A1 vs A9)": r2, "r4 (g4 gain)": 0.05, "median D": x.med_D,
                                 "P(P1N,P1S)": x.P_P1S, "P(..., P2)": x.P_P2, "P(..., P3)": x.P_P3})
T["b3_chain"] = md(pd.DataFrame(rows), ".2f")
rows = []
for r2 in (0.05, 0.15, 0.30):
    x = B3[(B3.kmode == "K_never") & (B3.rho1 == 0.75) & (B3.kappa == 0.6) & (B3.extra == 0) & (B3.r1 == 0.20) & (B3.r4 == 0.05) & (B3.r2 == r2)].iloc[0]
    rows.append({"r2 (A1 vs A9 gain)": r2, "P(P1N,P1S)": x.P_P1S, "P(..,P2)": x.P_P2, "P(..,P3)": x.P_P3})
T["b3_r2"] = md(pd.DataFrame(rows), ".2f")
rows = []
for kap in (0.3, 0.6, 0.9):
    for r4 in (0.0, 0.05, 0.10):
        x = B3[(B3.kappa == kap) & (B3.extra == 0) & (B3.rho1 == 0.75) & (B3.r1 == 0.20) & (B3.r2 == 0.15) & (B3.r4 == r4) & (B3.kmode == "K_never")]
        if len(x):
            x = x.iloc[0]
            rows.append({"corr(L(g1),L(g4))": kap, "r4": r4, "median D": x.med_D, "P(P1N,P1S,P2)": x.P_P2, "P(P1N,P1S,P2,P3)": x.P_P3})
T["b3_kappa"] = md(pd.DataFrame(rows), ".2f")
ex = B3[(B3.kmode == "K_never") & (B3.rho1 == 0.75) & (B3.kappa == 0.6) & (B3.r1 == 0.20) & (B3.r2 == 0.15) & (B3.r4 == 0.05)]
T["b3_extra"] = md(ex[["extra", "P_P1S", "P_P2", "P_P3"]].rename(columns={"extra": "extra D*-A9 correlation"}), ".3f")

B4 = pd.read_csv(P("b4_p3_power.csv"))
rows = []
for rho1 in (0.6, 0.75, 0.9):
    for kap in (0.0, 0.3, 0.6, 0.9):
        x = B4[(B4["shape"] == "isu_right") & (B4.f == 0) & (B4.rho1 == rho1) & (B4.kappa == kap)].sort_values("delta")
        row = {"rho(A1,D*)": rho1, "corr(L(g1),L(g4))": kap, "SD of D": x.sd_D.iloc[0]}
        for _, y in x.iterrows():
            row["delta=%.2f" % y.delta] = y["plain_0.0125"]
        rows.append(row)
T["b4_p3"] = md(pd.DataFrame(rows), ".2f")
rows = []
for rho1 in (0.6, 0.75, 0.9):
    for kap in (0.3, 0.6, 0.9):
        x = B4[(B4["shape"] == "isu_right") & (B4.f == 0) & (B4.rho1 == rho1) & (B4.kappa == kap)].sort_values("delta")
        row = {"rho(A1,D*)": rho1, "corr": kap}
        for _, y in x.iterrows():
            if y.delta in (0.10, 0.15, 0.20, 0.30):
                row["delta=%.2f" % y.delta] = y["plain_0.025"]
        rows.append(row)
T["b4_p3_025"] = md(pd.DataFrame(rows), ".2f")
rows = []
for rho1 in (0.75,):
    for kap in (0.3, 0.6, 0.9):
        for f in (0.0, 0.10):
            for tst in ("plain_0.0125", "fb0.03_0.0125"):
                x = B4[(B4["shape"] == "isu_right") & (B4.f == f) & (B4.rho1 == rho1) & (B4.kappa == kap)].sort_values("delta")
                row = {"rho(A1,D*)": rho1, "corr": kap, "fold ICC": f, "test": tst}
                for _, y in x.iterrows():
                    if y.delta in (0.0, 0.10, 0.15, 0.20, 0.30):
                        row["delta=%.2f" % y.delta] = y[tst]
                rows.append(row)
T["b4_p3_dep"] = md(pd.DataFrame(rows), ".3f")

# ------------------------------------------------------------------ (c)
C1 = pd.read_csv(P("c1_k_power_iid.csv"))
rows = []
for test, effs in (("K1_N", (-0.05, 0.0, 0.02, 0.05, 0.08, 0.10)), ("K1_S", (-0.10, -0.05, -0.02, 0.0)),
                   ("K2_N", (-0.10, -0.05, 0.0, 0.02, 0.05)), ("K2_S", (0.0, 0.02, 0.05, 0.08, 0.10, 0.12, 0.15))):
    for eff in effs:
        row = {"test": test, "effect": eff}
        for rho in (0.90, 0.95):
            x = C1[(C1["shape"] == "isu_right") & (C1.test == test) & (C1.rho == rho) & (C1.effect.round(3) == eff)].iloc[0]
            row["rho=%.2f 0.0125" % rho], row["rho=%.2f 0.025" % rho] = x["plain_0.0125"], x["plain_0.025"]
        rows.append(row)
T["c1"] = md(pd.DataFrame(rows), ".3f")
rows = []
for test in ("K1_N", "K2_N", "K2_S"):
    for rho in (0.90, 0.95):
        for sh in ("normal", "isu_right", "isu_left"):
            sub = C1[(C1["shape"] == sh) & (C1.test == test) & (C1.rho == rho)].sort_values("effect")
            # smallest effect with power >= 0.8 (K1: largest tolerated excess error; K2: smallest gain needed)
            for lv in ("0.0125", "0.025"):
                pw = sub["plain_" + lv].to_numpy()
                e = sub.effect.to_numpy()
                if test == "K1_N":
                    ok = e[pw >= 0.8]
                    val = ok.max() if len(ok) else np.nan
                else:
                    ok = e[pw >= 0.8]
                    val = ok.min() if len(ok) else np.nan
                rows.append({"test": test, "rho": rho, "shape": sh, "level": lv, "effect at 80 % power": val})
T["c1_80"] = md(pd.DataFrame(rows).pivot_table(index=["test", "rho", "shape"], columns="level", values="effect at 80 % power").reset_index(), ".2f")
C2 = pd.read_csv(P("c2_k_chain.csv"))
rows = []
for pm in ("P_never", "P_first"):
    for rk1, rk2 in ((0.95, 0.95), (0.90, 0.90)):
        for d1 in (0.0, 0.03):
            for q in (0.0, 0.05, 0.10):
                x = C2[(C2.pmode == pm) & (C2.rhoK1 == rk1) & (C2.rhoK2 == rk2) & (C2.d1 == d1) & (C2.q == q)].iloc[0]
                rows.append({"P chain": pm, "rho(A15,A1)": rk1, "rho(A15,G15)": rk2, "A15 vs A1: excess error": d1, "A15 vs G15: gain q": q,
                             "P(K1)": x.P_K1, "P(K1,K2N)": x.P_K1_K2N, "P(K1,K2N,K2S)": x.P_K1_K2N_K2S})
T["c2"] = md(pd.DataFrame(rows), ".2f")

# ------------------------------------------------------------------ (d)
D = pd.read_csv(P("d_fwer.csv")) if os.path.exists(P("d_fwer.csv")) else None
if D is not None:
    rows = []
    for st, g in D.groupby("setting", sort=False):
        w = g.loc[g.fwer.idxmax()]
        gl = g[g.cfg == "null|null|null|null|null"].iloc[0]
        se = np.sqrt(0.025 * 0.975 / g.nrep.iloc[0])
        rows.append({"setting": st, "global null FWER": gl.fwer, "max FWER over 72 configs": w.fwer, "config at max (L1|L2|D|K1|K2)": w.cfg,
                     "configs with FWER > 0.025 + 2 MC SE": int((g.fwer > 0.025 + 2 * se).sum()), "nrep": g.nrep.iloc[0]})
    T["d_summary"] = md(pd.DataFrame(rows), ".4f")
    iid = D[D.setting == "iid_plain"].sort_values("fwer", ascending=False).head(6)
    T["d_top_iid"] = md(iid[["cfg", "n_true_null", "fwer"]], ".4f")


# ------------------------------------------------------------------ (b5, c3) chains under the fall-back
if os.path.exists(P("b5_chain_fallback.csv")):
    B5 = pd.read_csv(P("b5_chain_fallback.csv"))
    rows = []
    for (f, l) in ((0.0, 0.0), (0.10, 0.05)):
        for km in ("K_never", "K_first"):
            for rho1 in (0.6, 0.75, 0.9):
                for r1 in (0.15, 0.20, 0.25, 0.30):
                    if rho1 != 0.75 and km == "K_first":
                        continue
                    for tn in ("plain", "fb0.03"):
                        x = B5[(B5.f == f) & (B5.l == l) & (B5.kmode == km) & (B5.rho1 == rho1) & (B5.r1 == r1) & (B5.r2 == 0.15) & (B5.r4 == 0.05) & (B5.test == tn)]
                        if len(x):
                            x = x.iloc[0]
                            rows.append({"fold ICC": f, "lab ICC": l, "K chain": km, "rho(A1,D*)": rho1, "r1": r1, "test": tn, "P(P1N,P1S)": x.P_P1S, "P(..,P2)": x.P_P2, "P(..,P3)": x.P_P3})
    T["b5_chain"] = md(pd.DataFrame(rows), ".2f")
    rows = []
    for (f, l) in ((0.0, 0.0), (0.10, 0.05)):
        for r2 in (0.05, 0.15, 0.30):
            for r4 in (0.0, 0.05, 0.10):
                x = B5[(B5.f == f) & (B5.l == l) & (B5.kmode == "K_never") & (B5.rho1 == 0.75) & (B5.r1 == 0.20) & (B5.r2 == r2) & (B5.r4 == r4)]
                row = {"fold ICC": f, "lab ICC": l, "r2": r2, "r4": r4}
                for tn in ("plain", "fb0.03"):
                    y = x[x.test == tn].iloc[0]
                    row["P(P1S) %s" % tn], row["P(..P2) %s" % tn], row["P(..P3) %s" % tn] = y.P_P1S, y.P_P2, y.P_P3
                rows.append(row)
    T["b5_chain_r2r4"] = md(pd.DataFrame(rows), ".2f")
if os.path.exists(P("c3_kchain_fallback.csv")):
    C3 = pd.read_csv(P("c3_kchain_fallback.csv"))
    rows = []
    for pm in ("P_never", "P_first"):
        for rk in (0.90, 0.95):
            for d1 in (0.0, 0.03):
                for q in (0.0, 0.05, 0.10):
                    row = {"P chain": pm, "rho(A15,A1)=rho(A15,G15)": rk, "A15 vs A1 excess error": d1, "A15 vs G15 gain q": q}
                    for tn in ("plain", "fb0.03"):
                        y = C3[(C3.pmode == pm) & (C3.rhoK == rk) & (C3.d1 == d1) & (C3.q == q) & (C3.test == tn)].iloc[0]
                        row["P(K1) %s" % tn], row["P(K1,K2N) %s" % tn], row["P(K1,K2N,K2S) %s" % tn] = y.P_K1, y.P_K1_K2N, y.P_K1_K2N_K2S
                    rows.append(row)
    T["c3"] = md(pd.DataFrame(rows), ".2f")

# ------------------------------------------------------------------ (d) detail for the fall-back settings
if D is not None:
    rows = []
    for st in D.setting.unique():
        g = D[D.setting == st]
        rows.append({"setting": st, "configs": len(g), "max FWER": g.fwer.max(), "global-null FWER": g[g.cfg == "null|null|null|null|null"].fwer.iloc[0],
                     "mean FWER over configs with a true null": g[g.n_true_null > 0].fwer.mean()})
    T["d_all"] = md(pd.DataFrame(rows), ".4f")

# ------------------------------------------------------------------ (e)
E = pd.read_csv(P("e_intervals_exact.csv"))
T["e_exact"] = md(E[["n", "alpha_two_sided", "exists", "rank_r", "interval", "coverage", "nominal"]], ".4f")

with open(P("tables.md"), "w", encoding="utf-8") as fh:
    for k, v in T.items():
        fh.write("<!--T:%s-->\n%s\n<!--/T-->\n\n" % (k, v))
print("tables:", len(T))
