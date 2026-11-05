"""Pre-freeze simulations (a)-(e) of the D016 statistical plan, plus the code path of item (f).  SIMULATION OUTPUTS ONLY:
every number produced here is a property of an assumed generating model, not a result about PINN-KAN or about Samsung cells.
No Samsung capacity value, outer-test score or outer-test prediction is read: the only inputs are
  (1) runs/prereg/stats_sim_v4/cond_structure.csv   (40 condition ids, folds, majority lab, from identifiers only),
  (2) runs/prereg/stats_ruling/cond_isu_W4.csv      (ISU training-side condition errors, shape of the skew; as STATS_RULING 7).

Usage (ROOT = project root; run with the project venv, python -P):
  python -P sim_v4.py a  [nrep]     size of the exact sign test under fold/lab random effects with skew, 9 grid cells, P3 contrast; item (e) coverage
  python -P sim_v4.py fb [nrep]     fall-back candidates: fixed design-effect (beta-binomial) sign test; size on the (a) scenarios, power
  python -P sim_v4.py b  [nrep]     power of P1 (analytic + dependent), chain probabilities P1S -> P2 -> P3, P3 power
  python -P sim_v4.py c  [nrep]     power of K1, K2N, K2S and the K chain
  python -P sim_v4.py d  [nrep]     FWER of the graph, 72 configurations, several dependence settings
  python -P sim_v4.py e             exact order-statistic intervals: existence and rank (analytic)
  python -P sim_v4.py f             smoke test of the item (f) code path on the ISU PILOT training-side scores (never Samsung)

Generating model (all items), per held-out condition c (n = 40), fold f(c) (5 folds of 8) and lab l(c) (HM 17, INT 19, SIE 4):
  Z_{c,j} = sqrt(1 - s_F - s_L) * W_{c,j} + sqrt(s_F) * U_{f(c),j} + sqrt(s_L) * V_{l(c),j}
  with W (condition-specific), U (fold-shared), V (lab-shared) standard normal and correlated across the J variables j
  (grid cells in (a); the five contrasts in (b)-(d)) with the same correlation matrix R; s_F, s_L = intra-fold / intra-lab
  correlation of the latent variable.  Observed log ratios  L_{c,j} = med_j + sigma_j * (T(Z_{c,j}) - T(0)),  T = identity
  (normal) or the standardised smoothed ISU shape (skewness +1.06; 'isu_left' = mirror), so median(L_j) = med_j exactly and
  the marginal law of every L is the same whatever s_F, s_L (copula form; used in (b)-(d)).  In (a) the skew is put on the
  condition-specific part only (additive form), the medians are then calibrated by Monte Carlo to the null boundary.
"""
import os
import sys
import json
import time
import zlib

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np
import pandas as pd
from scipy import special, stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
from pinnkan import graph_test as gt          # noqa: E402

OUT = HERE
BASE_SEED = 20261105
N = 40
A_FAM = 0.025
LVL = {"0.0125": A_FAM / 2, "0.025": A_FAM}
KCRIT = {k: gt.sign_crit(N, a) for k, a in LVL.items()}          # {'0.0125': 28, '0.025': 27}
TAIL = gt.binom_tail_table(N)
M_S, M_N = float(np.log(1.02)), float(-np.log(1.10))
CV = 0.45
S_LN = float(np.sqrt(np.log(1 + CV ** 2)))
SEED_VAR = 2 * 0.05 ** 2 / 5                                        # seed noise on a log ratio (STATS_RULING 5, 7)
MULT_M = np.array([1.0, 0.75, 0.5])                                  # ICC multiplier at m = 8, 16, 32 (assumption, see RESULT)
G1, G4 = 1, 8                                                        # cell index = 3 * i_m + i_k ; g1 = (m=8, k=2), g4 = (32, k_full)


def rng_for(name):
    return np.random.default_rng(np.random.SeedSequence([BASE_SEED, zlib.crc32(name.encode())]))


# ------------------------------------------------------------------------------------------------ design, shapes
ST = pd.read_csv(os.path.join(OUT, "cond_structure.csv"))
FOLD = ST["fold"].to_numpy(int)
LABS = sorted(ST["lab_majority"].unique())
LAB = np.array([LABS.index(x) for x in ST["lab_majority"]])
LABW = np.bincount(LAB) / N                                          # lab shares of the 40 conditions
assert len(ST) == N and np.bincount(FOLD).tolist() == [8] * 5


class Shape:
    """Standardised (mean 0, sd 1) monotone transform T of N(0,1); cdf of T(Z); median t0 = T(0)."""

    def __init__(self, kind):
        self.kind = kind
        zg = np.linspace(-4.5, 4.5, 9001)
        if kind == "normal":
            tg = zg.copy()
        else:
            cond = pd.read_csv(os.path.join(ROOT, "runs", "prereg", "stats_ruling", "cond_isu_W4.csv")).dropna()
            emp = (cond["pl"] - cond["lgb"]).to_numpy()
            emp = (emp - emp.mean()) / emp.std(ddof=0)
            r = np.random.default_rng(np.random.SeedSequence([BASE_SEED, 99]))
            s = r.choice(emp, 2_000_000) + 0.2 * r.standard_normal(2_000_000)
            s = (s - s.mean()) / s.std()
            tg = np.quantile(s, special.ndtr(zg))
            if kind == "isu_left":
                tg = -tg[::-1]
            elif kind != "isu_right":
                raise ValueError(kind)
        tg = tg + 1e-9 * np.arange(tg.size)                           # strictly increasing for the inverse
        self.zg, self.tg = zg, tg
        self.t0 = float(np.interp(0.0, zg, tg))
        z = np.random.default_rng(1).standard_normal(2_000_000)
        self.skew = float(stats.skew(self.T(z)))
        self.sd = float(self.T(z).std())

    def T(self, z):
        return np.interp(z, self.zg, self.tg)

    def cdf(self, x):
        """P(T(Z) <= x)."""
        return special.ndtr(np.interp(x, self.tg, self.zg))


SHAPES = {k: Shape(k) for k in ("normal", "isu_right", "isu_left")}


# ------------------------------------------------------------------------------------------------ exact tools
def tail_betabin(n, rho_s):
    """t[k] = P(X >= k) for X ~ BetaBinomial(n, a, a) with pairwise correlation rho_s (mean 1/2); rho_s = 0 -> binomial."""
    if rho_s <= 0:
        return gt.binom_tail_table(n)
    a = (1.0 / rho_s - 1.0) / 2.0
    t = np.zeros(n + 2)
    k = np.arange(n + 1)
    t[: n + 1] = stats.betabinom.sf(k - 1, n, a, a)
    t[0] = 1.0
    return t


def crit_from_tail(t, alpha):
    for k in range(len(t)):
        if t[k] <= alpha * (1 + gt.TOL):
            return k
    return len(t)


def de_of(rho_s, n=N):
    return 1.0 + (n - 1) * rho_s


def hist_tail(hist, k):
    """P(pos >= k) from a histogram of positives."""
    h = np.asarray(hist, float)
    return h[k:].sum() / h.sum()


# ------------------------------------------------------------------------------------------------ (a) generator
def ar_corr(a, k=3):
    return a ** np.abs(np.subtract.outer(np.arange(k), np.arange(k)))


def cell_chol(kappa14):
    a = kappa14 ** (1.0 / 3.0)                                       # corr(g1, g4) = a_m^2 a_k = a^3
    R = np.kron(ar_corr(a), ar_corr(a))
    return np.linalg.cholesky(R)


def gen_a(nrep, shape, sf9, sl9, chol, fold, lab, nfold, nlab, lab_off, rng):
    """Additive form: skew on the condition-specific part. Returns (nrep, ncond, 9)."""
    nc = fold.size
    W = shape.T(rng.standard_normal((nrep, nc, 9)) @ chol.T)
    X = np.sqrt(1.0 - sf9 - sl9) * W
    if sf9.max() > 0:
        U = rng.standard_normal((nrep, nfold, 9)) @ chol.T
        X += np.sqrt(sf9) * U[:, fold, :]
    if sl9.max() > 0:
        if lab_off is None:
            V = rng.standard_normal((nrep, nlab, 9)) @ chol.T
            X += np.sqrt(sl9) * V[:, lab, :]
        else:
            X += np.sqrt(sl9) * lab_off[lab][None, :, None]
    return X


_MED_CACHE = {}


def medians_a(shape, sf9, sl9, chol, lab_off, nmc=1_000_000):
    """Marginal medians of the 9 cells and of D = L(g1) - L(g4) (superpopulation: every random effect redrawn per condition)."""
    key = (shape.kind, tuple(np.round(sf9, 6)), tuple(np.round(sl9, 6)), None if lab_off is None else tuple(lab_off), tuple(np.round(chol[-1], 6)))
    if key in _MED_CACHE:
        return _MED_CACHE[key]
    r = np.random.default_rng(np.random.SeedSequence([BASE_SEED, zlib.crc32(repr(key).encode())]))
    ids = np.arange(nmc)
    if lab_off is None:
        lab, nlab = ids, nmc                    # every condition draws its own lab effect (superpopulation of labs)
    else:
        lab, nlab = r.choice(3, nmc, p=LABW), 3  # lab offsets fixed, labs in the observed proportions
    X = gen_a(1, shape, sf9, sl9, chol, ids, lab, nmc, nlab, lab_off, r)[0]
    med9 = np.median(X, axis=0)
    medD = float(np.median((X[:, G1] - med9[G1]) - (X[:, G4] - med9[G4])))
    _MED_CACHE[key] = (med9, medD)
    return med9, medD


def lab_offsets(l=None):
    """Fixed lab offsets (HM, INT, SIE) proportional to (1, -1, 0), centred and scaled to unit variance across the 40-condition
    mixture; the share l enters through sqrt(sl9) in gen_a."""
    o = np.array([1.0, -1.0, 0.0])
    o = o - (LABW * o).sum()
    return o / np.sqrt((LABW * o ** 2).sum())


def sim_a_scenario(name, shape_kind, f, l, kappa14, labmode, nrep, bs=5000):
    """Size of the exact sign test at null boundary (median of every cell = margin) in the 9 cells and for D = L(g1) - L(g4)."""
    shape = SHAPES[shape_kind]
    rng = rng_for(name)
    sf9 = np.repeat(f * MULT_M, 3)
    sl9 = np.repeat(l * MULT_M, 3)
    chol = cell_chol(kappa14)
    off = None if (labmode == "random" or l == 0) else lab_offsets(l)
    med9, medD = medians_a(shape, sf9, sl9, chol, off)
    r40 = gt.order_stat_interval(np.arange(N), 0.05 / 9)[2]
    r95 = gt.order_stat_interval(np.arange(N), 0.05)[2]
    hist = np.zeros((10, N + 1), np.int64)
    cov_all9 = cov_all95 = 0
    done = 0
    while done < nrep:
        b = min(bs, nrep - done)
        X = gen_a(b, shape, sf9, sl9, chol, FOLD, LAB, 5, 3, off, rng)
        L = X - med9
        D = L[:, :, G1] - L[:, :, G4] - medD
        pos9 = (L > 0).sum(1)
        posD = (D > 0).sum(1)
        for c in range(9):
            hist[c] += np.bincount(pos9[:, c], minlength=N + 1)
        hist[9] += np.bincount(posD, minlength=N + 1)
        mn = np.minimum(pos9, N - pos9)
        cov_all9 += int((mn >= r40).all(1).sum())
        cov_all95 += int((mn >= r95).all(1).sum())
        done += b
    return hist, cov_all9 / nrep, cov_all95 / nrep, r40, r95


def run_a(nrep):
    t0 = time.time()
    scen = []
    # main grid: fold ICC x lab ICC (random effects), three shapes, corr(g1,g4) = 0.6
    for shape in SHAPES:
        for f in (0.0, 0.02, 0.05, 0.10, 0.20):
            for l in (0.0, 0.02, 0.05, 0.10, 0.20):
                scen.append(dict(shape=shape, f=f, l=l, kappa=0.6, labmode="random"))
    # fine fold sweep for the break-even point (normal and right skew)
    for shape in ("normal", "isu_right"):
        for f in (0.01, 0.03, 0.04, 0.06, 0.08, 0.15, 0.30):
            scen.append(dict(shape=shape, f=f, l=0.0, kappa=0.6, labmode="random"))
    for shape in ("normal", "isu_right"):
        for l in (0.01, 0.03, 0.04):
            scen.append(dict(shape=shape, f=0.0, l=l, kappa=0.6, labmode="random"))
    # cross-cell correlation of the latent variable (matters for P3 only)
    for kap in (0.3, 0.9):
        for f, l in ((0.05, 0.0), (0.10, 0.05), (0.0, 0.0)):
            scen.append(dict(shape="isu_right", f=f, l=l, kappa=kap, labmode="random"))
    # lab effects as fixed offsets of the design (conditions i.i.d. within lab; labs not redrawn)
    for l in (0.10, 0.20, 0.40):
        for f in (0.0, 0.05, 0.10):
            scen.append(dict(shape="isu_right", f=f, l=l, kappa=0.6, labmode="fixed"))
    res, hists = [], {}
    for i, s in enumerate(scen):
        name = "a|%s|f%.3f|l%.3f|k%.2f|%s" % (s["shape"], s["f"], s["l"], s["kappa"], s["labmode"])
        hist, c9, c95, r40, r95 = sim_a_scenario(name, s["shape"], s["f"], s["l"], s["kappa"], s["labmode"], nrep)
        hists[name] = hist.tolist()
        row = dict(name=name, **s, nrep=nrep, cov_all9_a9=c9, cov_all9_a95=c95, r_a9=r40, r_a95=r95)
        for c in range(10):
            lab = "g%d" % c if c < 9 else "D"
            for lv, k in KCRIT.items():
                row["rej_%s_%s" % (lab, lv)] = hist_tail(hist[c], k)
            if c in (G1, 9):
                p = hist[c] / hist[c].sum()
                mean = (p * np.arange(N + 1)).sum()
                row["mean_pos_%s" % lab] = mean
                row["de_%s" % lab] = ((p * (np.arange(N + 1) - mean) ** 2).sum()) / (N / 4)
            m = np.minimum(np.arange(N + 1), N - np.arange(N + 1))
            row["cov_%s_a9" % lab] = float(((m >= r40) * hist[c]).sum() / hist[c].sum())
        res.append(row)
        if i % 10 == 0:
            print("a %d/%d %s %.0fs" % (i + 1, len(scen), name, time.time() - t0), flush=True)
    pd.DataFrame(res).to_csv(os.path.join(OUT, "a_size.csv"), index=False)
    json.dump(hists, open(os.path.join(OUT, "a_hist.json"), "w"))
    print("a done %.0fs" % (time.time() - t0))


# ------------------------------------------------------------------------------------------------ (b)-(d) J-variable model
ARMS = ("A1", "D", "A9", "A15", "G15")
CONTR = ("L1g1", "L2", "L1g4", "LK1", "LK2")


def build_model(rho1, rho2, rhoK1, rhoK2, kappa, extra=0.0):
    """Log errors of 5 arms at 2 cells (g1, g4), unit variance, tree dependence (A1 centre; D*, A9, A15 leaves of A1; G15 leaf of A15),
    Kronecker with the cell correlation kappa.  Contrasts (all 'positive favours the PINN-KAN side'):
      L1g1 = ln S_D*(g1) - ln S_A1(g1)   L2 = ln S_A9(g1) - ln S_A1(g1)   L1g4 = ln S_D*(g4) - ln S_A1(g4)
      LK1  = ln S_A1(g4) - ln S_A15(g4)  LK2 = ln S_G15(g4) - ln S_A15(g4)
    Returns R (5x5 correlation of the Gaussian contrasts) and sigma (their SD on the log scale incl. seed noise)."""
    C = np.eye(5)
    e = {(0, 1): rho1, (0, 2): rho2, (0, 3): rhoK1, (3, 4): rhoK2,
         (1, 2): rho1 * rho2 + extra, (1, 3): rho1 * rhoK1, (1, 4): rho1 * rhoK1 * rhoK2,
         (2, 3): rho2 * rhoK1, (2, 4): rho2 * rhoK1 * rhoK2, (0, 4): rhoK1 * rhoK2}
    for (i, j), v in e.items():
        C[i, j] = C[j, i] = v
    Cc = np.array([[1, kappa], [kappa, 1.0]])
    C10 = np.kron(C, Cc)                                              # index = 2 * arm + cell
    if np.linalg.eigvalsh(C10).min() < -1e-10:
        raise ValueError("model correlation matrix not PSD")
    def ix(arm, cell):
        return 2 * ARMS.index(arm) + cell
    M = np.zeros((5, 10))
    M[0, ix("D", 0)], M[0, ix("A1", 0)] = 1, -1
    M[1, ix("A9", 0)], M[1, ix("A1", 0)] = 1, -1
    M[2, ix("D", 1)], M[2, ix("A1", 1)] = 1, -1
    M[3, ix("A1", 1)], M[3, ix("A15", 1)] = 1, -1
    M[4, ix("G15", 1)], M[4, ix("A15", 1)] = 1, -1
    cov = M @ C10 @ M.T
    sd = np.sqrt(np.diag(cov))
    R = cov / np.outer(sd, sd)
    sigma = np.sqrt((S_LN * sd) ** 2 + SEED_VAR)
    return dict(R=R, sigma=sigma, chol=np.linalg.cholesky(R), rho=(rho1, rho2, rhoK1, rhoK2), kappa=kappa, extra=extra)


def gen_J(nrep, model, sf, sl, rng, lab_off=None):
    """Gaussian latent Z (nrep, 40, 5) with unit variance, dependence R, fold share sf and lab share sl."""
    ch = model["chol"]
    Z = np.sqrt(1.0 - sf - sl) * (rng.standard_normal((nrep, N, 5)) @ ch.T)
    if sf > 0:
        Z += np.sqrt(sf) * (rng.standard_normal((nrep, 5, 5)) @ ch.T)[:, FOLD, :]
    if sl > 0:
        if lab_off is None:
            Z += np.sqrt(sl) * (rng.standard_normal((nrep, 3, 5)) @ ch.T)[:, LAB, :]
        else:
            Z += np.sqrt(sl) * lab_off[LAB][None, :, None]
    return Z


_D0_CACHE = {}


def med0_D(model, shape):
    """Median of the pure-shape part of D = L1g1 - L1g4 (both medians 0): needed to place the D-median exactly."""
    key = (shape.kind, round(model["R"][0, 2], 8), round(model["sigma"][0], 8), round(model["sigma"][2], 8))
    if key not in _D0_CACHE:
        if shape.kind == "normal":
            _D0_CACHE[key] = 0.0
        else:
            r = np.random.default_rng(7)
            z = r.standard_normal((2_000_000, 2)) @ np.linalg.cholesky(model["R"][np.ix_([0, 2], [0, 2])]).T
            d = model["sigma"][0] * (shape.T(z[:, 0]) - shape.t0) - model["sigma"][2] * (shape.T(z[:, 1]) - shape.t0)
            _D0_CACHE[key] = float(np.median(d))
    return _D0_CACHE[key]


def to_L(Z, model, shape, med):
    """med: length-5 vector of target medians of (L1g1, L2, L1g4, LK1, LK2)."""
    return np.asarray(med) + model["sigma"] * (shape.T(Z) - shape.t0)


def meds(model, shape, mu1, mu2, delta, muK1, muK2):
    """Medians of the five contrasts so that median(L1g1) = mu1, median(L2) = mu2, median(D) = delta, ..."""
    mu4 = mu1 - delta + med0_D(model, shape)
    return np.array([mu1, mu2, mu4, muK1, muK2])


def node_counts(L):
    """Positive counts of the seven graph nodes and of D (batch). L: (B, 40, 5)."""
    D = L[:, :, 0] - L[:, :, 2]
    c = lambda x, m: (x > m).sum(1)
    return dict(P1N=c(L[:, :, 0], M_N), P1S=c(L[:, :, 0], M_S), P2=c(L[:, :, 1], M_S), P3=c(D, 0.0),
                K1=c(L[:, :, 3], M_N), K2N=c(L[:, :, 4], M_N), K2S=c(L[:, :, 4], M_S))


def pvals_from_counts(cnt, tail):
    return np.stack([tail[cnt[k]] for k in gt.NODES], axis=1)


def log_ratio(r):
    return -np.log1p(-r)          # relative reduction r -> median log ratio ln(1/(1-r))


# ------------------------------------------------------------------------------------------------ (b) power
def p_pos(shape, mu, sigma, margin):
    """P(L > margin) for L = mu + sigma * (T(Z) - t0)."""
    return 1.0 - shape.cdf((margin - mu) / sigma + shape.t0)


def power_exact(p, k):
    return stats.binom.sf(k - 1, N, p)


def mde(fn, lo=0.0, hi=0.95, target=0.8):
    """Smallest r with fn(r) >= target (fn increasing); nan if none below hi."""
    if fn(hi) < target:
        return float("nan")
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if fn(mid) >= target else (mid, hi)
    return hi


FB_RHOS = (0.01, 0.02, 0.03, 0.05)                                    # candidate pre-set pairwise sign correlations


def fb_crits():
    out = {}
    for rho in FB_RHOS:
        t = tail_betabin(N, rho)
        out[rho] = {lv: crit_from_tail(t, a) for lv, a in LVL.items()}
    return out


def run_b(nrep):
    t0 = time.time()
    rows = []
    # B1: analytic power (conditions i.i.d.), P1N and P1S, three shapes, rho in {0.6, 0.75, 0.9}
    fbc = fb_crits()
    for shape_kind, shape in SHAPES.items():
        for rho in (0.6, 0.75, 0.9):
            sig = np.sqrt((S_LN * np.sqrt(2 * (1 - rho))) ** 2 + SEED_VAR)
            for tier, margin in (("S", M_S), ("N", M_N)):
                tests = [("plain", lv, KCRIT[lv]) for lv in LVL] + [("fb%.2f" % rho_s, lv, fbc[rho_s][lv]) for rho_s in FB_RHOS for lv in LVL]
                for test, lv, k in tests:
                    fn = lambda r, margin=margin: power_exact(p_pos(shape, log_ratio(r), sig, margin), k)
                    for r in np.round(np.arange(0.0, 0.401, 0.01), 3):
                        rows.append(dict(shape=shape_kind, rho=rho, tier=tier, test=test, level=lv, k=k, r=r, power=float(fn(r)), mde80=np.nan))
                    rows.append(dict(shape=shape_kind, rho=rho, tier=tier, test=test, level=lv, k=k, r=np.nan, power=np.nan, mde80=mde(fn)))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "b1_p1_power_iid.csv"), index=False)
    print("b1 done %.0fs" % (time.time() - t0), flush=True)

    # B2: P1S power with fold / lab random effects (simulation), plain vs fall-back thresholds
    rows = []
    shape = SHAPES["isu_right"]
    for rho in (0.6, 0.75, 0.9):
        model = build_model(rho, 0.95, 0.95, 0.93, 0.6)
        for (f, l) in ((0, 0), (0.05, 0), (0.10, 0), (0.10, 0.05), (0.20, 0.05)):
            for r in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40):
                rng = rng_for("b2|%s|%.2f|%.2f|%.2f|%.2f" % (shape.kind, rho, f, l, r))
                h = np.zeros(N + 1, np.int64)
                done = 0
                while done < nrep:
                    b = min(5000, nrep - done)
                    Z = gen_J(b, model, f, l, rng)
                    L = to_L(Z, model, shape, meds(model, shape, log_ratio(r), 0, 0, 0, 0))
                    h += np.bincount((L[:, :, 0] > M_S).sum(1), minlength=N + 1)
                    done += b
                row = dict(rho=rho, f=f, l=l, r=r, nrep=nrep)
                for lv in LVL:
                    row["plain_%s" % lv] = hist_tail(h, KCRIT[lv])
                    for rho_s in FB_RHOS:
                        row["fb%.2f_%s" % (rho_s, lv)] = hist_tail(h, fbc[rho_s][lv])
                rows.append(row)
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "b2_p1_power_dep.csv"), index=False)
    print("b2 done %.0fs" % (time.time() - t0), flush=True)

    # B3: chain probabilities in the graph (P chain alone: K never rejects -> levels 0.0125; K complete first: K p-values 0 -> levels 0.025)
    rows = []
    nodes, w, G = gt.pinnkan_graph()
    shape = SHAPES["isu_right"]
    nb3 = min(nrep, 20000)
    for rho1 in (0.6, 0.75, 0.9):
        for kappa in (0.3, 0.6, 0.9):
            for extra in (0.0, 0.15):
                try:
                    model = build_model(rho1, 0.95, 0.95, 0.93, kappa, extra)
                except ValueError:
                    continue
                for r1 in (0.10, 0.15, 0.20, 0.30):
                    for r2 in (0.05, 0.15, 0.30):
                        for r4 in (0.0, 0.05, 0.10):
                            if r4 >= r1:
                                continue
                            rng = rng_for("b3|%.2f|%.2f|%.2f|%.2f|%.2f|%.2f" % (rho1, kappa, extra, r1, r2, r4))
                            mu4, mu1 = log_ratio(r4), log_ratio(r1)
                            med = np.array([mu1, log_ratio(r2), mu4, 0, 0])
                            chain = {"K_never": np.zeros(4), "K_first": np.zeros(4)}
                            done = 0
                            while done < nb3:
                                b = min(5000, nb3 - done)
                                L = to_L(gen_J(b, model, 0.0, 0.0, rng), model, shape, med)
                                P0 = pvals_from_counts(node_counts(L), TAIL)
                                for kmode, val in (("K_never", 1.0), ("K_first", 0.0)):
                                    P = P0.copy()
                                    P[:, 4:] = val
                                    rj = gt.graph_test(P, w, G, A_FAM).rejected
                                    chain[kmode] += np.array([rj[:, 0].sum(), (rj[:, 0] & rj[:, 1]).sum(), (rj[:, :3].all(1)).sum(), (rj[:, :4].all(1)).sum()])
                                done += b
                            Dmed = mu1 - mu4 + med0_D(model, shape)
                            for kmode in chain:
                                c = chain[kmode] / nb3
                                rows.append(dict(rho1=rho1, kappa=kappa, extra=extra, r1=r1, r2=r2, r4=r4, kmode=kmode, med_D=Dmed, nrep=nb3,
                                                 P_P1N=c[0], P_P1S=c[1], P_P2=c[2], P_P3=c[3]))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "b3_chain.csv"), index=False)
    print("b3 done %.0fs" % (time.time() - t0), flush=True)

    # B4: P3 stand-alone power: sign test of D > 0, true median(D) = delta, level 0.0125 / 0.025, corr(L1g1, L1g4) = kappa
    rows = []
    for shape_kind in ("normal", "isu_right", "isu_left"):
        shape = SHAPES[shape_kind]
        for rho1 in (0.6, 0.75, 0.9):
            for kappa in (0.0, 0.3, 0.6, 0.9):
                model = build_model(rho1, 0.95, 0.95, 0.93, kappa)
                for f in (0.0, 0.10):
                    for delta in (0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40):
                        rng = rng_for("b4|%s|%.2f|%.2f|%.2f|%.2f" % (shape_kind, rho1, kappa, f, delta))
                        h = np.zeros(N + 1, np.int64)
                        done = 0
                        while done < nrep:
                            b = min(5000, nrep - done)
                            L = to_L(gen_J(b, model, f, 0.0, rng), model, shape, meds(model, shape, 0.2, 0, delta, 0, 0))
                            h += np.bincount(((L[:, :, 0] - L[:, :, 2]) > 0).sum(1), minlength=N + 1)
                            done += b
                        # SD of D on the log scale (Gaussian version)
                        s1, s4, c14 = model["sigma"][0], model["sigma"][2], model["R"][0, 2]
                        sdD = float(np.sqrt(s1 ** 2 + s4 ** 2 - 2 * c14 * s1 * s4))
                        rows.append(dict(shape=shape_kind, rho1=rho1, kappa=kappa, f=f, delta=delta, sd_D=sdD,
                                         **{"plain_%s" % lv: hist_tail(h, KCRIT[lv]) for lv in LVL},
                                         **{"fb%.2f_%s" % (rs, lv): hist_tail(h, fbc[rs][lv]) for rs in FB_RHOS for lv in LVL}))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "b4_p3_power.csv"), index=False)
    print("b4 done %.0fs" % (time.time() - t0), flush=True)


# ------------------------------------------------------------------------------------------------ (c) K1, K2
def run_c(nrep):
    t0 = time.time()
    fbc = fb_crits()
    rows = []
    # C1: analytic power of K1 (tier N at -ln 1.10; tier S reported), K2N, K2S (iid conditions)
    for shape_kind, shape in SHAPES.items():
        for rho in (0.90, 0.95):
            sig = np.sqrt((S_LN * np.sqrt(2 * (1 - rho))) ** 2 + SEED_VAR)
            # d = S_A15 / S_A1 - 1 for K1 ; q = relative reduction of A15 against G15 for K2
            for test, margin, effects in (("K1_N", M_N, np.round(np.arange(-0.10, 0.1301, 0.01), 3)),
                                          ("K1_S", M_S, np.round(np.arange(-0.10, 0.1301, 0.01), 3)),
                                          ("K2_N", M_N, np.round(np.arange(-0.15, 0.1501, 0.01), 3)),
                                          ("K2_S", M_S, np.round(np.arange(-0.10, 0.3001, 0.01), 3))):
                for eff in effects:
                    mu = -np.log1p(eff) if test.startswith("K1") else -np.log1p(-eff)      # K1: eff = relative excess error of A15 over A1 ; K2: eff = relative reduction of A15 vs G15
                    p = float(p_pos(shape, mu, sig, margin))
                    row = dict(shape=shape_kind, rho=rho, test=test, effect=eff, p_pos=p)
                    for lv in LVL:
                        row["plain_%s" % lv] = float(power_exact(p, KCRIT[lv]))
                        for rs in FB_RHOS:
                            row["fb%.2f_%s" % (rs, lv)] = float(power_exact(p, fbc[rs][lv]))
                    rows.append(row)
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "c1_k_power_iid.csv"), index=False)
    print("c1 done %.0fs" % (time.time() - t0), flush=True)
    # C2: K chain probabilities in the graph
    rows = []
    nodes, w, G = gt.pinnkan_graph()
    shape = SHAPES["isu_right"]
    for rhoK1 in (0.90, 0.95):
        for rhoK2 in (0.90, 0.95):
            model = build_model(0.75, 0.95, rhoK1, rhoK2, 0.6)
            for d1 in (-0.05, 0.0, 0.03, 0.06, 0.10):
                for q in (-0.05, 0.0, 0.02, 0.05, 0.10, 0.20):
                    for pmode in ("P_never", "P_first"):
                        rng = rng_for("c2|%.2f|%.2f|%.2f|%.2f|%s" % (rhoK1, rhoK2, d1, q, pmode))
                        med = np.array([0, 0, 0, -np.log1p(d1), -np.log1p(-q)])
                        chain = np.zeros(3)
                        done = 0
                        while done < nrep:
                            b = min(5000, nrep - done)
                            L = to_L(gen_J(b, model, 0.0, 0.0, rng), model, shape, med)
                            P = pvals_from_counts(node_counts(L), TAIL)
                            P[:, :4] = 1.0 if pmode == "P_never" else 0.0
                            rj = gt.graph_test(P, w, G, A_FAM).rejected
                            chain += np.array([rj[:, 4].sum(), (rj[:, 4] & rj[:, 5]).sum(), rj[:, 4:].all(1).sum()])
                            done += b
                        rows.append(dict(rhoK1=rhoK1, rhoK2=rhoK2, d1=d1, q=q, pmode=pmode, P_K1=chain[0] / nrep, P_K1_K2N=chain[1] / nrep, P_K1_K2N_K2S=chain[2] / nrep))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "c2_k_chain.csv"), index=False)
    print("c2 done %.0fs" % (time.time() - t0), flush=True)


# ------------------------------------------------------------------------------------------------ (d) FWER
LEVELS_CFG = {
    "L1": {"null": -np.log(1.10), "mid": 0.0, "alt": log_ratio(0.40)},
    "L2": {"null": M_S, "alt": log_ratio(0.40)},
    "D": {"null": 0.0, "alt": 0.40},
    "K1": {"null": M_N, "alt": 0.15},
    "K2": {"null": M_N, "mid": 0.0, "alt": 0.35},
}


def run_d(nrep):
    import itertools
    t0 = time.time()
    nodes, w, G = gt.pinnkan_graph()
    settings = [
        dict(tag="iid_plain", model=(0.75, 0.95, 0.95, 0.93, 0.6, 0.0), f=0.0, l=0.0, shape="isu_right", test=("plain",)),
        dict(tag="iid_plain_highdep", model=(0.90, 0.95, 0.95, 0.95, 0.9, 0.10), f=0.0, l=0.0, shape="isu_left", test=("plain",)),
        dict(tag="fold05_plain", model=(0.75, 0.95, 0.95, 0.93, 0.6, 0.0), f=0.05, l=0.0, shape="isu_right", test=("plain",)),
        dict(tag="fold10_lab05_plain", model=(0.75, 0.95, 0.95, 0.93, 0.6, 0.0), f=0.10, l=0.05, shape="isu_right", test=("plain",)),
    ]
    for rs in FB_RHOS:
        settings.append(dict(tag="fold10_lab05_fb%.2f" % rs, model=(0.75, 0.95, 0.95, 0.93, 0.6, 0.0), f=0.10, l=0.05, shape="isu_right", test=("fb", rs)))
        settings.append(dict(tag="iid_fb%.2f" % rs, model=(0.75, 0.95, 0.95, 0.93, 0.6, 0.0), f=0.0, l=0.0, shape="isu_right", test=("fb", rs)))
    rows = []
    for st in settings:
        model = build_model(*st["model"])
        shape = SHAPES[st["shape"]]
        tail = TAIL if st["test"][0] == "plain" else tail_betabin(N, st["test"][1])
        for cfg in itertools.product(LEVELS_CFG["L1"], LEVELS_CFG["L2"], LEVELS_CFG["D"], LEVELS_CFG["K1"], LEVELS_CFG["K2"]):
            c1, c2, cd, ck1, ck2 = cfg
            rng = rng_for("d|%s|%s" % (st["tag"], "|".join(cfg)))
            med = meds(model, shape, LEVELS_CFG["L1"][c1], LEVELS_CFG["L2"][c2], LEVELS_CFG["D"][cd], LEVELS_CFG["K1"][ck1], LEVELS_CFG["K2"][ck2])
            true_null = np.array([c1 == "null", c1 in ("null", "mid"), c2 == "null", cd == "null", ck1 == "null", ck2 == "null", ck2 in ("null", "mid")])
            anyfalse = 0
            per = np.zeros(7)
            done = 0
            while done < nrep:
                b = min(5000, nrep - done)
                L = to_L(gen_J(b, model, st["f"], st["l"], rng), model, shape, med)
                P = pvals_from_counts(node_counts(L), tail)
                rj = gt.graph_test(P, w, G, A_FAM).rejected
                anyfalse += int(rj[:, true_null].any(1).sum()) if true_null.any() else 0
                per += rj.sum(0)
                done += b
            rows.append(dict(setting=st["tag"], cfg="|".join(cfg), n_true_null=int(true_null.sum()), fwer=anyfalse / nrep, nrep=nrep,
                             **{"rej_" + k: per[i] / nrep for i, k in enumerate(gt.NODES)}))
        print("d %s %.0fs" % (st["tag"], time.time() - t0), flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "d_fwer.csv"), index=False)
    print("d done %.0fs" % (time.time() - t0))


# ------------------------------------------------------------------------------------------------ (e) intervals
def run_e():
    rows = []
    for n in (13, 19, 40):
        pmf = stats.binom.pmf(np.arange(n + 1), n, 0.5)
        cdf = np.cumsum(pmf)
        for label, alpha in (("0.05", 0.05), ("0.05/9", 0.05 / 9), ("0.05/18", 0.05 / 18)):
            r = 0
            for rr in range(1, n // 2 + 1):
                if 1 - 2 * cdf[rr - 1] >= 1 - alpha - 1e-12:
                    r = rr
            rows.append(dict(n=n, alpha_two_sided=label, alpha=alpha, exists=r > 0, rank_r=r,
                             interval="[L(%d), L(%d)]" % (r, n + 1 - r) if r else "none",
                             coverage=(1 - 2 * cdf[r - 1]) if r else np.nan, nominal=1 - alpha,
                             ))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "e_intervals_exact.csv"), index=False)
    print(pd.DataFrame(rows).to_string())


# ------------------------------------------------------------------------------------------------ (f) code path
def item_f_rho_report(scores: pd.DataFrame, comp_col: str, pinn_col: str, source: str, fold_col=None, lab_col=None):
    """Item (f), POWER REPORT ONLY (no rule changes).  `scores`: one row per condition, positive condition scores of two arms from the
    INNER-CV of the training sides.  `source` must be the literal 'inner_cv_training_side': outer-test scores are refused.
    Returns n, Pearson rho of the log scores (the rho of the simulation models), CV of both arms, SD and skew of L = ln(comp/pinn),
    the rho implied by SD(L), the share of positives, the ANOVA intra-fold / intra-lab correlation of the signs of (L - median), and the
    exact i.i.d. power (P1S, plain sign test, both levels) at relative reductions r = 0.05 ... 0.30 with the implied sigma."""
    if source != "inner_cv_training_side":
        raise ValueError("item (f) accepts inner-CV scores of training sides only")
    d = scores.dropna(subset=[comp_col, pinn_col])
    a, b = np.log(d[comp_col].to_numpy(float)), np.log(d[pinn_col].to_numpy(float))
    L = a - b
    n = len(d)
    s = float(np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2))
    rho = float(np.corrcoef(a, b)[0, 1])
    out = dict(n=n, rho_log=rho, rho_raw=float(np.corrcoef(np.exp(a), np.exp(b))[0, 1]),
               cv_comp=float(d[comp_col].std(ddof=1) / d[comp_col].mean()), cv_pinn=float(d[pinn_col].std(ddof=1) / d[pinn_col].mean()),
               sd_L=float(L.std(ddof=1)), skew_L=float(stats.skew(L)), median_L=float(np.median(L)),
               rho_implied_by_sdL=float(1 - L.var(ddof=1) / (2 * s ** 2)), share_L_gt_0=float((L > 0).mean()))
    sg = (L > np.median(L)).astype(float)
    for nm, col in (("fold", fold_col), ("lab", lab_col)):
        if col is not None:
            g = d[col].to_numpy()
            groups = [sg[g == u] for u in np.unique(g)]
            k = len(groups)
            nbar = (n - sum(len(x) ** 2 for x in groups) / n) / (k - 1)
            msb = sum(len(x) * (x.mean() - sg.mean()) ** 2 for x in groups) / (k - 1)
            msw = sum(((x - x.mean()) ** 2).sum() for x in groups) / (n - k)
            out["icc_sign_" + nm] = float((msb - msw) / (msb + (nbar - 1) * msw))
    sig = np.sqrt(L.var(ddof=1) + 1e-12)
    out["power_iid_S"] = {lv: {"%.2f" % r: float(power_exact(p_pos(SHAPES["normal"], log_ratio(r), sig, M_S), KCRIT[lv])) for r in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30)} for lv in LVL}
    return out


def run_f():
    d = pd.read_csv(os.path.join(ROOT, "runs", "prereg", "stats_ruling", "cond_isu_W4.csv")).dropna(subset=["pl", "lgb"])
    rep = item_f_rho_report(d, "pl", "lgb", "inner_cv_training_side")
    json.dump(rep, open(os.path.join(OUT, "f_smoke_isu_pilot.json"), "w"), indent=1)
    print(json.dumps(rep, indent=1))


# ------------------------------------------------------------------------------------------------ fall-back evaluation
def run_fb():
    """Size of the fixed design-effect sign tests on the (a) scenarios (from stored histograms) and the P3 contrast."""
    H = json.load(open(os.path.join(OUT, "a_hist.json")))
    A = pd.read_csv(os.path.join(OUT, "a_size.csv"))
    fbc = fb_crits()
    rows = []
    for _, s in A.iterrows():
        h = np.array(H[s["name"]])
        for rs in (0.0,) + FB_RHOS:
            for lv, a in LVL.items():
                k = KCRIT[lv] if rs == 0 else fbc[rs][lv]
                sizes = [hist_tail(h[c], k) for c in range(10)]
                rows.append(dict(name=s["name"], shape=s["shape"], f=s["f"], l=s["l"], kappa=s["kappa"], labmode=s["labmode"], rho_s0=rs, level=lv, k=k,
                                 size_g1=sizes[G1], size_max9=max(sizes[:9]), size_D=sizes[9], ratio_g1=sizes[G1] / a, ratio_max9=max(sizes[:9]) / a, ratio_D=sizes[9] / a))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "fb_size.csv"), index=False)
    print({rs: fbc[rs] for rs in fbc})


def run_fbest(nrep):
    """Candidate: sign test with a design effect ESTIMATED from the five folds (cluster-robust variance of the positives count,
    floor DE_0), z reference t_4 or normal.  Size under the (a) model at the null boundary, cell g1 (normal and right-skewed)."""
    from scipy.stats import t as tdist, norm
    rows = []
    for shape_kind in ("normal", "isu_right"):
        shape = SHAPES[shape_kind]
        for f in (0.0, 0.05, 0.10, 0.20):
            for l in (0.0, 0.05):
                rng = rng_for("fbest|%s|%.2f|%.2f" % (shape_kind, f, l))
                chol = cell_chol(0.6)
                sf9, sl9 = np.repeat(f * MULT_M, 3), np.repeat(l * MULT_M, 3)
                med9, _ = medians_a(shape, sf9, sl9, chol, None)
                Xp = np.zeros(nrep); Xf = np.zeros((nrep, 5))
                done = 0
                while done < nrep:
                    b = min(5000, nrep - done)
                    L = gen_a(b, shape, sf9, sl9, chol, FOLD, LAB, 5, 3, None, rng)[:, :, G1] - med9[G1]
                    sg = (L > 0).astype(float)
                    Xp[done:done + b] = sg.sum(1)
                    Xf[done:done + b] = np.stack([sg[:, FOLD == q].sum(1) for q in range(5)], 1)
                    done += b
                phat = Xp / N
                V = (5 / 4) * ((Xf - 8 * phat[:, None]) ** 2).sum(1)
                for de0 in (1.0, 1.4, 2.0):
                    de = np.maximum(V / (N / 4), de0)
                    z = (Xp - N / 2 - 0.5) / np.sqrt((N / 4) * de)
                    for ref in ("t4", "norm"):
                        pv = tdist.sf(z, 4) if ref == "t4" else norm.sf(z)
                        rows.append(dict(shape=shape_kind, f=f, l=l, de_floor=de0, ref=ref, nrep=nrep,
                                         size_0125=float((pv <= 0.0125).mean()), size_025=float((pv <= 0.025).mean())))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "fbest_size.csv"), index=False)
    print("fbest done")


def run_b5(nrep):
    """Chain probabilities of the P chain and the K chain under the FALL-BACK tests (fixed design effect), iid and with fold/lab effects."""
    t0 = time.time()
    nodes, w, G = gt.pinnkan_graph()
    shape = SHAPES["isu_right"]
    tails = {"plain": TAIL, "fb0.02": tail_betabin(N, 0.02), "fb0.03": tail_betabin(N, 0.03)}
    rows = []
    for (f, l) in ((0.0, 0.0), (0.10, 0.05)):
        for rho1 in (0.6, 0.75, 0.9):
            model = build_model(rho1, 0.95, 0.95, 0.93, 0.6)
            for r1 in (0.15, 0.20, 0.25, 0.30):
                for r2 in (0.05, 0.15, 0.30):
                    for r4 in (0.0, 0.05, 0.10):
                        rng = rng_for("b5|%.2f|%.2f|%.2f|%.2f|%.2f|%.2f" % (f, l, rho1, r1, r2, r4))
                        med = np.array([log_ratio(r1), log_ratio(r2), log_ratio(r4), 0, 0])
                        acc = {(tn, km): np.zeros(4) for tn in tails for km in ("K_never", "K_first")}
                        done = 0
                        while done < nrep:
                            b = min(5000, nrep - done)
                            L = to_L(gen_J(b, model, f, l, rng), model, shape, med)
                            cnt = node_counts(L)
                            for tn, tl in tails.items():
                                P0 = pvals_from_counts(cnt, tl)
                                for km, val in (("K_never", 1.0), ("K_first", 0.0)):
                                    P = P0.copy(); P[:, 4:] = val
                                    rj = gt.graph_test(P, w, G, A_FAM).rejected
                                    acc[(tn, km)] += np.array([rj[:, 0].sum(), (rj[:, 0] & rj[:, 1]).sum(), rj[:, :3].all(1).sum(), rj[:, :4].all(1).sum()])
                            done += b
                        for (tn, km), c in acc.items():
                            c = c / nrep
                            rows.append(dict(f=f, l=l, rho1=rho1, r1=r1, r2=r2, r4=r4, test=tn, kmode=km, P_P1N=c[0], P_P1S=c[1], P_P2=c[2], P_P3=c[3]))
        print("b5 P chain f=%.2f l=%.2f %.0fs" % (f, l, time.time() - t0), flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "b5_chain_fallback.csv"), index=False)
    rows = []
    for rhoK in (0.90, 0.95):
        model = build_model(0.75, 0.95, rhoK, rhoK, 0.6)
        for d1 in (-0.05, 0.0, 0.03, 0.06):
            for q in (0.0, 0.05, 0.10, 0.20):
                rng = rng_for("c3|%.2f|%.2f|%.2f" % (rhoK, d1, q))
                med = np.array([0, 0, 0, -np.log1p(d1), -np.log1p(-q)])
                acc = {(tn, pm): np.zeros(3) for tn in tails for pm in ("P_never", "P_first")}
                done = 0
                while done < nrep:
                    b = min(5000, nrep - done)
                    L = to_L(gen_J(b, model, 0.0, 0.0, rng), model, shape, med)
                    cnt = node_counts(L)
                    for tn, tl in tails.items():
                        P0 = pvals_from_counts(cnt, tl)
                        for pm, val in (("P_never", 1.0), ("P_first", 0.0)):
                            P = P0.copy(); P[:, :4] = val
                            rj = gt.graph_test(P, w, G, A_FAM).rejected
                            acc[(tn, pm)] += np.array([rj[:, 4].sum(), (rj[:, 4] & rj[:, 5]).sum(), rj[:, 4:].all(1).sum()])
                    done += b
                for (tn, pm), c in acc.items():
                    c = c / nrep
                    rows.append(dict(rhoK=rhoK, d1=d1, q=q, test=tn, pmode=pm, P_K1=c[0], P_K1_K2N=c[1], P_K1_K2N_K2S=c[2]))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "c3_kchain_fallback.csv"), index=False)
    print("b5/c3 done %.0fs" % (time.time() - t0))


if __name__ == "__main__":
    cmd = sys.argv[1]
    nrep = int(sys.argv[2]) if len(sys.argv) > 2 else None
    if cmd == "a":
        run_a(nrep or 100000)
    elif cmd == "fb":
        run_fb()
    elif cmd == "b":
        run_b(nrep or 40000)
    elif cmd == "c":
        run_c(nrep or 40000)
    elif cmd == "d":
        run_d(nrep or 50000)
    elif cmd == "b5":
        run_b5(nrep or 20000)
    elif cmd == "fbest":
        run_fbest(nrep or 40000)
    elif cmd == "e":
        run_e()
    elif cmd == "f":
        run_f()
    else:
        raise SystemExit(__doc__)
