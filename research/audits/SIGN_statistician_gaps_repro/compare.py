"""Statistician validation: (a) HEAD vs new vs gaps-off outputs after stripping only the registered new keys; (b) independent recomputation of NC-2, PC-3, PC-2, G1 from raw synthetic files."""
import copy, json, os, sys
import numpy as np
from scipy.stats import betabinom
W = sys.argv[1]
J = lambda *a: json.load(open(os.path.join(W, *a), encoding="utf8"))
canon = lambda o: json.dumps(o, sort_keys=True, default=str)


def strip_c(o):
    o = copy.deepcopy(o)
    o["secondary"]["tests"]["QT_g1"].pop("median_interval", None)
    o.pop("candidates_vs_a1", None); o.pop("stats_gaps", None)
    return o


def strip_ctl(c):
    c = copy.deepcopy(c)
    (c.get("negative") or {}).pop("nc2", None)
    for k in ("P2_monotone_in_T", "PC2_detail", "P3_passed", "PC3_detail", "P3_A1_beats_R1_median_L"):
        c["positive"].pop(k, None)
    c["gate_G"]["reported_checks"] = {"PC-2_calendar_rate_monotone_in_T": None, "PC-3_A1_beats_persistence": None}
    return c


def strip_pv(p):
    p = copy.deepcopy(p)
    for k in ("a_of_soc", "arrhenius_ln_rate", "partial_dependence_overlays"):
        p.pop(k, None)
    return p


def diffkeys(a, b, path=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append(f"{path}/{k} only in {'new' if k in b else 'head'}")
            else:
                out += diffkeys(a[k], b[k], f"{path}/{k}")
    elif canon(a) != canon(b):
        out.append(f"{path}: {str(a)[:80]} != {str(b)[:80]}")
    return out


H, N, O = "an_head", "an_new", "an_off"
for f, s in (("contrasts_v4_B.json", strip_c), ("controls.json", strip_ctl), ("physval_11a.json", strip_pv)):
    h, n, o = J(H, f), J(N, f), J(O, f)
    print(f, "| HEAD==off raw:", canon(h) == canon(o), "| HEAD==strip(new):", canon(s(h)) == canon(s(n)), "| raw lengths", len(canon(h)), len(canon(n)))
    d = diffkeys(h, n)
    print("   raw diff keys HEAD->new (first 12):", d[:12], "total", len(d))
print("contrasts gate_G.reported_checks:", J(N, "contrasts_v4_B.json")["gate_G"]["reported_checks"])
print("controls  gate_G.reported_checks:", J(N, "controls.json")["gate_G"]["reported_checks"])
print("status/provisional new:", J(N, "contrasts_v4_B.json")["status"])

# ---- independent recomputation (my own code, raw files) ----
p = J("paths.json")
def scores(dirs, arm, suf=""):
    out = {}
    for d in dirs:
        if json.load(open(os.path.join(d, "config.json")))["m"] != 32:
            continue
        cs = json.load(open(os.path.join(d, f"condition_scores{suf}.json")))
        out.update(cs.get(arm, {}))
    return out
real, perm, r1 = scores(p["dirs"], "A1"), scores(p["neg"], "A1"), scores(p["dirs"], "R1")
a, b = (1 / 0.03 - 1) / 2, (1 / 0.03 - 1) / 2
pv = lambda x, n: float(betabinom.sf(x - 1, n, a, b))
crit = lambda n, al: next(x for x in range(n + 1) if pv(x, n) <= al)
print("my crit n=40 at 0.025:", crit(40, 0.025), "| 0.0125:", crit(40, 0.0125), "| 0.005:", crit(40, 0.005))
c = sorted(real); L = np.log(np.array([perm[k] for k in c]) / np.array([real[k] for k in c]))
nc2 = J(N, "controls.json")["negative"]["nc2"]
x = int((L > 0).sum())
print("NC-2 mine: n", len(L), "pos", x, "p", round(pv(x, len(L)), 6), "pass", pv(x, len(L)) <= 0.025, "median", round(float(np.median(L)), 6),
      "| code:", nc2["n"], nc2["k_positive"], round(nc2["p_one_sided"], 6), nc2["passed"], round(nc2["median_L"], 6), "crit", nc2["crit_positives"])
LR = np.log(np.array([r1[k] for k in c]) / np.array([real[k] for k in c]))
pc3 = J(N, "controls.json")["positive"]["PC3_detail"]
x3 = int((LR > 0).sum())
print("PC-3 mine: n", len(LR), "pos", x3, "p", round(pv(x3, len(LR)), 6), "| code:", pc3["n"], pc3["positives"], round(pc3["p"], 6), pc3["passed"])
srt = np.sort(L)
print("NC-2 interval code", nc2["median_ci95"], "rank", nc2["interval_rank"], "| L(11), L(30):", srt[10], srt[29])
# G1 pooled mean and seed SD (independence and upper bound) for A1 at 32|full
blk = [json.load(open(os.path.join(d, "metrics.json")))["outer_test_by_k"]["full"]["A1"] for d in p["dirs"] if json.load(open(os.path.join(d, "config.json")))["m"] == 32]
w = np.array([x_["n_conditions"] for x_ in blk], float); w /= w.sum()
mp = float(np.sum(w * [x_["primary_pp"] for x_ in blk])); sd = np.array([x_["seed_sd_of_mean"] for x_ in blk])
at = J(N, "arm_table.json")["cells"]["32|full"]["A1"]
print("G1 mine mean", round(mp, 6), "sd_ind", round(float(np.sqrt(np.sum((w * sd) ** 2))), 6), "sd_ub", round(float(np.sum(w * sd)), 6),
      "| code", round(at["mean_pp"], 6), round(at["seed_sd_pp"], 6), round(at["seed_sd_pp_upper_bound"], 6))
print("G1 check: pooled mean over all 40 condition scores directly:", round(float(np.mean(list(real.values()))), 6), "(metrics primary_pp synthetic = mean of condition scores)")
