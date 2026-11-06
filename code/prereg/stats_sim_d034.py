"""D034 re-simulation (statistician).  SIMULATION OUTPUTS ONLY: every number is a property of the assumed generating model of
runs/prereg/stats_sim_v4/RESULT.md section 2 (sim_v4.py), not a result about PINN-KAN or any real data.  CPU only; no Samsung
capacity value, outer-test score or prediction is read: inputs are cond_structure.csv (identifiers) and cond_isu_W4.csv (ISU
training-side shape of the skew), exactly as sim_v4.py.

Changes against sim_v4.py (D033 AD1, AD2; D034):
  AD1  P3 tests D_c = L_c(g1) - L_c(32, 2) instead of L_c(g1) - L_c(g4).  Cells of the 3 x 3 grid of sim_v4 (m = 8, 16, 32 by
       k = 0, 2, full):  g1 = (m8, k2) = index 1,  (32, 2) = index 7,  g4 = (32, full) = index 8.  The generator of sim_v4 makes the
       latent variable a separable AR(1) in both directions (coefficient a, corr(g1, g4) = a^3 = kappa14), the fold/lab share a
       function of m only.  Hence corr(g1, (32,2)) = a^2 = kappa14^(2/3), corr((32,2), g4) = a, and (32,2) has the same fold/lab
       share as g4.  Nothing else is added.  The median gain at (32,2) is not in the generator (sim_v4 has gains at g1 and g4
       only); it is a parameter r_c, bracketed (see RESULT_D034.md).
  AD2  Modifier M3: sign test of median L_R1 > 0 at g1 (L_R1 = ln S_R1 - ln S_A1), 30 positives of 40 (Beta-binomial rho_s0 = 0.03,
       level 0.025), outside the graph.  R1 is a leaf of the arm tree below A1 (like D*, A9, A15), correlation rhoR.

Usage (python -P, from anywhere):  python -P stats_sim_d034.py <item> [args]
  checks | power <shape> [nrep] | size <shape> [nrep] | guard <kappa14> [nrep] | chain [nrep] | m3 <shape> [nrep] | report
"""
import os
import sys
import json
import time
import itertools

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SIMDIR = os.path.join(ROOT, "runs", "prereg", "stats_sim_v4")
sys.path.insert(0, SIMDIR)
sys.path.insert(0, os.path.join(ROOT, "code"))
import numpy as np                      # noqa: E402
import pandas as pd                     # noqa: E402
import sim_v4 as S                      # noqa: E402  (module-level setup only; its __main__ block is not run)
from pinnkan import graph_test as gt    # noqa: E402

OUT = SIMDIR
N = S.N
W_ALT = 0.78
BB03 = S.BB03
CRIT = {lv: S.crit_from_tail(BB03, a) for lv, a in (("0.0055", 0.0055), ("0.0125", 0.0125), ("0.0195", 0.0195), ("0.025", 0.025))}
assert CRIT == {"0.0055": 32, "0.0125": 31, "0.0195": 30, "0.025": 30}, CRIT
K_M3 = CRIT["0.025"]                                                   # 30 of 40
G1, C2, G4 = 1, 7, 8                                                   # grid indices of g1, (32,2), g4
SETTINGS = [(0.0, 0.0, 0.90), (0.0, 0.0, 0.95), (0.10, 0.05, 0.90), (0.10, 0.05, 0.95)]   # as sim_v4.G_SETTINGS (f, l, rhoK)
KAPPAS = (0.3, 0.6, 0.9)                                               # corr(g1, g4) as in sim_v4 section 5.3
ARMS6 = ("A1", "D", "A9", "A15", "G15", "R1")
PARENT = {"D": "A1", "A9": "A1", "A15": "A1", "R1": "A1", "G15": "A15"}
NC = 7                                                                 # contrasts: L1g1, L2, Lc, LK1, LK2, LR, L1g4


def tree_corr(edge, x, y):
    def path(u):
        p = []
        while u != "A1":
            p.append(u)
            u = PARENT[u]
        return p
    px, py = set(path(x)), set(path(y))
    r = 1.0
    for u in px ^ py:
        r *= edge[u]
    return r


def build_model(rho1, rho2, rhoK1, rhoK2, rhoR, kappa14):
    """7 contrasts from 6 arms x 3 cells (g1, (32,2), g4); arm tree as sim_v4.build_model (R1 a further leaf of A1);
    cell correlation matrix of the separable AR(1) grid: g1-(32,2) a^2, g1-g4 a^3, (32,2)-g4 a, with a = kappa14^(1/3)."""
    a = kappa14 ** (1.0 / 3.0)
    edge = {"D": rho1, "A9": rho2, "A15": rhoK1, "G15": rhoK2, "R1": rhoR}
    C = np.eye(6)
    for i, x in enumerate(ARMS6):
        for j, y in enumerate(ARMS6):
            if i != j:
                C[i, j] = tree_corr(edge, x, y)
    Cc = np.array([[1, a ** 2, a ** 3], [a ** 2, 1, a], [a ** 3, a, 1.0]])
    C18 = np.kron(C, Cc)                                               # index = 3 * arm + cell
    if np.linalg.eigvalsh(C18).min() < -1e-10:
        raise ValueError("not PSD")
    ix = lambda arm, cell: 3 * ARMS6.index(arm) + cell                 # noqa: E731
    M = np.zeros((NC, 18))
    for r, (x, y, cell) in enumerate([("D", "A1", 0), ("A9", "A1", 0), ("D", "A1", 1), ("A1", "A15", 2), ("G15", "A15", 2), ("R1", "A1", 0), ("D", "A1", 2)]):
        M[r, ix(x, cell)], M[r, ix(y, cell)] = 1, -1
    cov = M @ C18 @ M.T
    sd = np.sqrt(np.diag(cov))
    R = cov / np.outer(sd, sd)
    sigma = np.sqrt((S.S_LN * sd) ** 2 + S.SEED_VAR)
    return dict(R=R, sigma=sigma, chol=np.linalg.cholesky(R), kappa14=kappa14)


def gen_Z(nrep, model, sf, sl, rng):
    ch = model["chol"]
    J = ch.shape[0]
    Z = np.sqrt(1.0 - sf - sl) * (rng.standard_normal((nrep, N, J)) @ ch.T)
    if sf > 0:
        Z += np.sqrt(sf) * (rng.standard_normal((nrep, 5, J)) @ ch.T)[:, S.FOLD, :]
    if sl > 0:
        Z += np.sqrt(sl) * (rng.standard_normal((nrep, 3, J)) @ ch.T)[:, S.LAB, :]
    return Z


_M0 = {}


def med0_pair(model, shape, i, j):
    """Median of sigma_i (T(Z_i) - t0) - sigma_j (T(Z_j) - t0): places the median of L_i - L_j exactly (0 for the normal shape)."""
    if shape.kind == "normal":
        return 0.0
    key = (shape.kind, i, j, round(model["R"][i, j], 8), round(model["sigma"][i], 8), round(model["sigma"][j], 8))
    if key not in _M0:
        r = np.random.default_rng(7)
        z = r.standard_normal((2_000_000, 2)) @ np.linalg.cholesky(model["R"][np.ix_([i, j], [i, j])]).T
        d = model["sigma"][i] * (shape.T(z[:, 0]) - shape.t0) - model["sigma"][j] * (shape.T(z[:, 1]) - shape.t0)
        _M0[key] = float(np.median(d))
    return _M0[key]


def to_L(Z, model, shape, med):
    return np.asarray(med) + model["sigma"] * (shape.T(Z) - shape.t0)


def counts_nodes(L, newD=True):
    """Positive counts of the seven graph nodes; P3 = D_new (col 2) if newD else D_old (col 6 = L1g4)."""
    c = lambda x, m: (x > m).sum(1)    # noqa: E731
    d = L[:, :, 0] - (L[:, :, 2] if newD else L[:, :, 6])
    return dict(P1N=c(L[:, :, 0], S.M_N), P1S=c(L[:, :, 0], S.M_S), P2=c(L[:, :, 1], S.M_S), P3=c(d, 0.0),
                K1=c(L[:, :, 3], S.M_N), K2N=c(L[:, :, 4], S.M_N), K2S=c(L[:, :, 4], S.M_S))


def graph_P(cnt):
    return np.stack([BB03[cnt[k]] for k in gt.NODES], axis=1)


def chains(rj):
    p = rj[:, 0] & rj[:, 1]
    return dict(Pp=p, P2=p & rj[:, 2], P3=p & rj[:, 2] & rj[:, 3], K1=rj[:, 4])


def write(df, name):
    df.to_csv(os.path.join(OUT, name), index=False)


# --------------------------------------------------------------------------------------------------------- checks
def run_checks():
    """Structure checks: the 7-contrast model reproduces sim_v4.build_model on the common contrasts."""
    out = {}
    for rho1, kap in ((0.75, 0.6), (0.6, 0.3), (0.9, 0.9)):
        new = build_model(rho1, 0.95, 0.95, 0.93, 0.75, kap)
        old = S.build_model(rho1, 0.95, 0.95, 0.93, kap)
        sel = [0, 1, 6, 3, 4]
        out["R_maxdiff_rho1=%.2f_kappa=%.1f" % (rho1, kap)] = float(np.abs(new["R"][np.ix_(sel, sel)] - old["R"]).max())
        out["sigma_maxdiff_rho1=%.2f_kappa=%.1f" % (rho1, kap)] = float(np.abs(new["sigma"][sel] - old["sigma"]).max())
        # new D contrast equals the old model at kappa' = kappa^(2/3)
        old2 = S.build_model(rho1, 0.95, 0.95, 0.93, kap ** (2 / 3))
        out["Dnew_equals_old_at_kappa^(2/3)_rho1=%.2f_kappa=%.1f" % (rho1, kap)] = float(
            max(abs(new["R"][0, 2] - old2["R"][0, 2]), abs(new["sigma"][2] - old2["sigma"][2])))
    out["corr(L1g1, Lc) at kappa14 = 0.6"] = float(build_model(0.75, 0.95, 0.95, 0.93, 0.75, 0.6)["R"][0, 2])
    out["corr(L1g1, L1g4) at kappa14 = 0.6"] = float(build_model(0.75, 0.95, 0.95, 0.93, 0.75, 0.6)["R"][0, 6])
    out["crit_counts_BB03"] = CRIT
    json.dump(out, open(os.path.join(OUT, "d034_checks.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
    assert max(v for k, v in out.items() if k.startswith(("R_max", "sigma_max", "Dnew"))) < 1e-9


# --------------------------------------------------------------------------------------------------------- P3 stand-alone power
def run_power(shape_kind, nrep):
    """P3 alone, old contrast (g1 - g4, correlation kappa14) and new contrast (g1 - (32,2), correlation kappa14^(2/3)) from the same draws.
    median(D) = delta for both (so the comparison isolates the change of correlation).  Tests: plain 28 / 27 of 40, fallback 31 / 30 of 40."""
    t0 = time.time()
    shape = S.SHAPES[shape_kind]
    rows = []
    for rho1 in (0.6, 0.75, 0.9):
        for kap in KAPPAS:
            model = build_model(rho1, 0.95, 0.95, 0.93, 0.75, kap)
            sd = lambda i, j: float(np.sqrt(model["sigma"][i] ** 2 + model["sigma"][j] ** 2 - 2 * model["R"][i, j] * model["sigma"][i] * model["sigma"][j]))   # noqa: E731
            for (f, l) in ((0.0, 0.0), (0.10, 0.0), (0.10, 0.05)):
                for delta in (0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40):
                    rng = S.rng_for("d034p|%s|%.2f|%.2f|%.2f|%.2f|%.2f" % (shape_kind, rho1, kap, f, l, delta))
                    mu1 = 0.2
                    med = np.zeros(NC)
                    med[0] = mu1
                    med[2] = mu1 - delta + med0_pair(model, shape, 0, 2)
                    med[6] = mu1 - delta + med0_pair(model, shape, 0, 6)
                    hn, ho = np.zeros(N + 1, np.int64), np.zeros(N + 1, np.int64)
                    done = 0
                    while done < nrep:
                        b = min(5000, nrep - done)
                        L = to_L(gen_Z(b, model, f, l, rng), model, shape, med)
                        hn += np.bincount(((L[:, :, 0] - L[:, :, 2]) > 0).sum(1), minlength=N + 1)
                        ho += np.bincount(((L[:, :, 0] - L[:, :, 6]) > 0).sum(1), minlength=N + 1)
                        done += b
                    row = dict(shape=shape_kind, rho1=rho1, kappa14=kap, f=f, l=l, delta=delta, nrep=nrep, sd_D_new=sd(0, 2), sd_D_old=sd(0, 6))
                    for tag, h in (("new", hn), ("old", ho)):
                        row["plain_0.0125_" + tag] = S.hist_tail(h, 28)
                        row["plain_0.025_" + tag] = S.hist_tail(h, 27)
                        row["fb31_" + tag] = S.hist_tail(h, CRIT["0.0125"])
                        row["fb30_" + tag] = S.hist_tail(h, CRIT["0.025"])
                    rows.append(row)
        print("power %s rho1=%.2f %.0fs" % (shape_kind, rho1, time.time() - t0), flush=True)
    write(pd.DataFrame(rows), "d034_p3_power_%s.csv" % shape_kind)


# --------------------------------------------------------------------------------------------------------- (a)-type size of D_new, D_old, g1
def lab_off():
    return S.lab_offsets()


_MC = {}


def medians_pairs(shape, sf9, sl9, chol, off, nmc=1_000_000):
    key = (shape.kind, tuple(np.round(sf9, 6)), tuple(np.round(sl9, 6)), None if off is None else tuple(off), tuple(np.round(chol[-1], 6)))
    if key in _MC:
        return _MC[key]
    import zlib
    r = np.random.default_rng(np.random.SeedSequence([S.BASE_SEED, zlib.crc32(repr(key).encode())]))
    ids = np.arange(nmc)
    if off is None:
        lab, nlab = ids, nmc
    else:
        lab, nlab = r.choice(3, nmc, p=S.LABW), 3
    X = S.gen_a(1, shape, sf9, sl9, chol, ids, lab, nmc, nlab, off, r)[0]
    med9 = np.median(X, axis=0)
    medD = {}
    for tag, c2 in (("new", C2), ("old", G4)):
        medD[tag] = float(np.median((X[:, G1] - med9[G1]) - (X[:, c2] - med9[c2])))
    _MC[key] = (med9, medD)
    return _MC[key]


def run_size(shape_kind, nrep):
    """Size at the null boundary of: the P3 sign test with D_new = L(g1) - L(32,2), D_old = L(g1) - L(g4), and the M3-type sign test at g1
    (margin 0, median of the cell calibrated to 0).  Generator (a) of sim_v4: additive form, fold/lab share scaled by m (1 / 0.75 / 0.5),
    random lab effects (pessimistic) and fixed lab offsets."""
    t0 = time.time()
    shape = S.SHAPES[shape_kind]
    scen = []
    for kap in KAPPAS:
        for f in (0.0, 0.02, 0.05, 0.10, 0.20):
            for l in (0.0, 0.02, 0.05, 0.10, 0.20):
                if kap == 0.6 or (f, l) in ((0.0, 0.0), (0.05, 0.0), (0.10, 0.05)):
                    scen.append((kap, f, l, "random"))
    for l in (0.10, 0.20, 0.40):
        for f in (0.0, 0.05, 0.10):
            scen.append((0.6, f, l, "fixed"))
    rows, hists = [], {}
    for i, (kap, f, l, lm) in enumerate(scen):
        name = "d034a|%s|f%.3f|l%.3f|k%.2f|%s" % (shape_kind, f, l, kap, lm)
        rng = S.rng_for(name)
        sf9, sl9 = np.repeat(f * S.MULT_M, 3), np.repeat(l * S.MULT_M, 3)
        chol = S.cell_chol(kap)
        off = None if (lm == "random" or l == 0) else lab_off()
        med9, medD = medians_pairs(shape, sf9, sl9, chol, off)
        h = {k: np.zeros(N + 1, np.int64) for k in ("g1", "new", "old")}
        done = 0
        while done < nrep:
            b = min(5000, nrep - done)
            X = S.gen_a(b, shape, sf9, sl9, chol, S.FOLD, S.LAB, 5, 3, off, rng)
            L = X - med9
            h["g1"] += np.bincount((L[:, :, G1] > 0).sum(1), minlength=N + 1)
            h["new"] += np.bincount(((L[:, :, G1] - L[:, :, C2] - medD["new"]) > 0).sum(1), minlength=N + 1)
            h["old"] += np.bincount(((L[:, :, G1] - L[:, :, G4] - medD["old"]) > 0).sum(1), minlength=N + 1)
            done += b
        row = dict(shape=shape_kind, kappa14=kap, f=f, l=l, labmode=lm, nrep=nrep)
        for t in h:
            row["plain_0.0125_" + t] = S.hist_tail(h[t], 28)
            row["plain_0.025_" + t] = S.hist_tail(h[t], 27)
            row["fb30_" + t] = S.hist_tail(h[t], 30)
            row["fb31_" + t] = S.hist_tail(h[t], 31)
            p = h[t] / h[t].sum()
            mean = (p * np.arange(N + 1)).sum()
            row["de_" + t] = float(((p * (np.arange(N + 1) - mean) ** 2).sum()) / (N / 4))
        rows.append(row)
        hists[name] = {k: v.tolist() for k, v in h.items()}
        if i % 10 == 0:
            print("size %s %d/%d %.0fs" % (shape_kind, i + 1, len(scen), time.time() - t0), flush=True)
    write(pd.DataFrame(rows), "d034_p3_size_%s.csv" % shape_kind)
    json.dump(hists, open(os.path.join(OUT, "d034_size_hist_%s.json" % shape_kind), "w"))


# --------------------------------------------------------------------------------------------------------- FWER guard
def run_guard(kappa14, nrep):
    """Item (d)/(g) guard with w = 0.78 on P1N, new P3 contrast: 72 configurations x 2 settings, fallback counts (rho_s0 = 0.03)."""
    t0 = time.time()
    nodes, w, G = gt.pinnkan_graph(W_ALT)
    shape = S.SHAPES["isu_right"]
    L_ = S.LEVELS_CFG
    rows = []
    for tag, f, l in (("iid_fb0.03", 0.0, 0.0), ("fold10_lab05_fb0.03", 0.10, 0.05)):
        model = build_model(0.75, 0.95, 0.95, 0.93, 0.75, kappa14)
        for cfg in itertools.product(L_["L1"], L_["L2"], L_["D"], L_["K1"], L_["K2"]):
            c1, c2, cd, ck1, ck2 = cfg
            rng = S.rng_for("d034g|k%.2f|%s|%s" % (kappa14, tag, "|".join(cfg)))
            mu1 = L_["L1"][c1]
            med = np.zeros(NC)
            med[0], med[1] = mu1, L_["L2"][c2]
            med[2] = mu1 - L_["D"][cd] + med0_pair(model, shape, 0, 2)
            med[3], med[4] = L_["K1"][ck1], L_["K2"][ck2]
            med[5] = 0.0
            med[6] = mu1 - L_["D"][cd] + med0_pair(model, shape, 0, 6)
            true_null = np.array([c1 == "null", c1 in ("null", "mid"), c2 == "null", cd == "null", ck1 == "null", ck2 == "null", ck2 in ("null", "mid")])
            anyfalse, done = 0, 0
            while done < nrep:
                b = min(5000, nrep - done)
                L = to_L(gen_Z(b, model, f, l, rng), model, shape, med)
                rj = gt.graph_test(graph_P(counts_nodes(L, True)), w, G, S.A_FAM).rejected
                anyfalse += int(rj[:, true_null].any(1).sum()) if true_null.any() else 0
                done += b
            rows.append(dict(setting=tag, kappa14=kappa14, w_P1N=W_ALT, cfg="|".join(cfg), n_true_null=int(true_null.sum()), fwer=anyfalse / nrep, nrep=nrep))
        print("guard k=%.2f %s %.0fs" % (kappa14, tag, time.time() - t0), flush=True)
    write(pd.DataFrame(rows), "d034_guard_k%.2f.csv" % kappa14)


# --------------------------------------------------------------------------------------------------------- chains with the new P3
def run_chain(nrep):
    """w = 0.78 graph (fallback counts), K chain running together, plan effect sizes: rho(A1,D*) 0.75, rho(A1,A9) 0.95, r1 = 0.20, r2 = 0.15,
    A15 as good as A1 (K1 median 0), K2 gain 0.05 (settings of RESULT_weights.md).  r_c = gain of A1 over D* at (32,2) (r4 in the old contrast),
    same value used for g4 in the old contrast, so old/new differ only through the correlation of the contrast.  Old and new P3 on the same draws."""
    t0 = time.time()
    nodes, w, G = gt.pinnkan_graph(W_ALT)
    shape = S.SHAPES["isu_right"]
    rows = []
    for (f, l, rk) in SETTINGS:
        for kap in KAPPAS:
            model = build_model(0.75, 0.95, rk, rk, 0.75, kap)
            for r1 in (0.15, 0.20, 0.25):
                for rc in (0.0, 0.05, 0.10, 0.15):
                    if rc > r1:
                        continue
                    rng = S.rng_for("d034c|f%.2f|l%.2f|rk%.2f|k%.2f|r1%.2f|rc%.2f" % (f, l, rk, kap, r1, rc))
                    med = np.array([S.log_ratio(r1), S.log_ratio(0.15), S.log_ratio(rc), 0.0, S.log_ratio(0.05), 0.0, S.log_ratio(rc)])
                    acc = {k: [] for k in ("Pp", "P2", "P3n", "P3o", "K1", "p3alone_n", "p3alone_o")}
                    done = 0
                    while done < nrep:
                        b = min(5000, nrep - done)
                        L = to_L(gen_Z(b, model, f, l, rng), model, shape, med)
                        for tag, nd in (("n", True), ("o", False)):
                            cnt = counts_nodes(L, nd)
                            ev = chains(gt.graph_test(graph_P(cnt), w, G, S.A_FAM).rejected)
                            acc["P3" + tag].append(ev["P3"])
                            acc["p3alone_" + tag].append(cnt["P3"] >= CRIT["0.0195"])
                            if tag == "n":
                                acc["Pp"].append(ev["Pp"]); acc["P2"].append(ev["P2"]); acc["K1"].append(ev["K1"])
                        done += b
                    a = {k: np.concatenate(v).astype(float) for k, v in acc.items()}
                    dd = a["P3n"] - a["P3o"]
                    rows.append(dict(f=f, l=l, rhoK=rk, kappa14=kap, r1=r1, r_c=rc, nrep=nrep, P_Pp=a["Pp"].mean(), P_P2=a["P2"].mean(),
                                     P_P3_old=a["P3o"].mean(), P_P3_new=a["P3n"].mean(), d_P3=dd.mean(), se_d_P3=dd.std(ddof=1) / np.sqrt(nrep),
                                     P_K1=a["K1"].mean(), P3_node_alone_old=a["p3alone_o"].mean(), P3_node_alone_new=a["p3alone_n"].mean()))
        print("chain f=%.2f l=%.2f rk=%.2f %.0fs" % (f, l, rk, time.time() - t0), flush=True)
    write(pd.DataFrame(rows), "d034_chain.csv")


# --------------------------------------------------------------------------------------------------------- M3 effect on P(P+ title)
GR = (0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.60)
RHOR = (0.5, 0.75, 0.9)


def run_m3(shape_kind, nrep):
    """P(P+ and M3 passes) against P(P+), graph w = 0.78, the K chain running.  gR = true median relative gain of A1 over R1 at g1 (R1 persistence),
    rhoR = correlation of the log condition errors of A1 and R1.  M3 passes iff >= 30 of 40 conditions have L_R1 > 0 (fallback, 0.025)."""
    t0 = time.time()
    nodes, w, G = gt.pinnkan_graph(W_ALT)
    shape = S.SHAPES[shape_kind]
    r1s = (0.15, 0.20, 0.25) if shape_kind == "isu_right" else (0.20,)
    rows = []
    for (f, l, rk) in SETTINGS:
        for r1 in r1s:
            for rhoR in RHOR:
                model = build_model(0.75, 0.95, rk, rk, rhoR, 0.6)
                rng = S.rng_for("d034m|%s|f%.2f|l%.2f|rk%.2f|r1%.2f|rR%.2f" % (shape_kind, f, l, rk, r1, rhoR))
                med = np.array([S.log_ratio(r1), S.log_ratio(0.15), S.log_ratio(0.05), 0.0, S.log_ratio(0.05), 0.0, 0.0])
                acc = {"Pp": [], "P3": [], **{("m3_%.2f" % g): [] for g in GR}}
                done = 0
                while done < nrep:
                    b = min(5000, nrep - done)
                    Z = gen_Z(b, model, f, l, rng)
                    L = to_L(Z, model, shape, med)
                    ev = chains(gt.graph_test(graph_P(counts_nodes(L, True)), w, G, S.A_FAM).rejected)
                    acc["Pp"].append(ev["Pp"]); acc["P3"].append(ev["P3"])
                    T5 = shape.T(Z[:, :, 5]) - shape.t0
                    for g in GR:
                        cntR = ((S.log_ratio(g) + model["sigma"][5] * T5) > 0).sum(1)
                        acc["m3_%.2f" % g].append(cntR >= K_M3)
                    done += b
                a = {k: np.concatenate(v) for k, v in acc.items()}
                for g in GR:
                    m = a["m3_%.2f" % g]
                    rows.append(dict(shape=shape_kind, f=f, l=l, rhoK=rk, r1=r1, rhoR=rhoR, gR=g, nrep=nrep,
                                     P_Pplus=a["Pp"].mean(), P_Pplus_M3pass=(a["Pp"] & m).mean(), P_M3pass=m.mean(),
                                     P_P3chain=a["P3"].mean(), P_P3chain_M3pass=(a["P3"] & m).mean()))
        print("m3 %s f=%.2f l=%.2f rk=%.2f %.0fs" % (shape_kind, f, l, rk, time.time() - t0), flush=True)
    write(pd.DataFrame(rows), "d034_m3_%s.csv" % shape_kind)


if __name__ == "__main__":
    cmd = sys.argv[1]
    a2 = sys.argv[2] if len(sys.argv) > 2 else None
    a3 = int(sys.argv[3]) if len(sys.argv) > 3 else None
    if cmd == "checks":
        run_checks()
    elif cmd == "power":
        run_power(a2, a3 or 40000)
    elif cmd == "size":
        run_size(a2, a3 or 100000)
    elif cmd == "guard":
        run_guard(float(a2), a3 or 50000)
    elif cmd == "chain":
        run_chain(int(a2) if a2 else 40000)
    elif cmd == "m3":
        run_m3(a2, a3 or 40000)
    else:
        raise SystemExit(__doc__)
