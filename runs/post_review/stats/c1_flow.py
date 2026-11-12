"""C1: flow-diagram content (nodes and edges for a figure maker) and the practitioner paragraph. Every number is read from the frozen JSON (stored files) or t2_rho_sweep.json."""
import sys
sys.path.insert(0, r"C:\Users\Shlok\Downloads\PINN KAN battery paper\runs\post_review\stats")
import re
from common import *

c = jload(os.path.join(FROZEN, "contrasts_v4_B.json"))
ct = jload(os.path.join(FROZEN, "controls.json"))
t2 = jload(os.path.join(OUT, "t2_rho_sweep.json"))
pr = c["primary"]["nodes"]
cfg = c["config_full"]
n = pr["P1N"]["n"]
rho0 = cfg["rho_s0"]
deff = 1 + (n - 1) * rho0
mN, mS = pr["P1N"]["margin"], pr["P1S"]["margin"]
import math
pctN, pctS = round((math.exp(-mN) - 1) * 100, 1), round((math.exp(mS) - 1) * 100, 1)
crit025 = t2["sweep"]["0.03"]["crit_levels"]["0.025"]
lv = c["primary"]["initial_levels"]
nc2, pc3 = ct["negative"]["nc2"], ct["positive"]["PC3_detail"]
nc1 = ct["negative"]["nc1"]
out = c["outcome"]
sec_lvl = c["secondary"]["tests"]["QA10_g1"]["slot_level"]

nodes = [
    dict(id="N1", label="Data and splits", kind="design",
         lines=["%d cycling conditions; five outer folds of 8 held-out conditions; contrasts paired by condition" % n, "history m = 8, 16, 32 conditions; check-ups used k = 0, 2, full",
                "confirmatory cells g1 = (m 8, k 2) and g4 = (m 32, k full)", "endpoint: median over held-out conditions of the condition RMSE", "contrast L_c = ln(S_comparator / S_target)"]),
    dict(id="N2", label="Gate G", kind="gating",
         lines=["NC-1 label invariance (%d runs checked, maximum difference %.1f)" % (nc1["runs_checked"], nc1["max_abs_diff"]), "PC-1 synthetic recovery",
                "fail: no title, no claim; pass: continue", "result: gate tripped = %s" % c["gate_G"]["tripped"]]),
    dict(id="N3", label="Controls reported beside the tests (never change a tier)", kind="reported",
         lines=["NC-2 permuted stress: %d of %d, p = %.4f, needed %d, not passed (interpretive)" % (nc2["k_positive"], nc2["n"], nc2["p_one_sided"], nc2["crit_positives"]),
                "PC-2 calendar rate monotone in temperature: %s" % ct["positive"]["PC2_detail"]["passed"],
                "PC-3 PINN-KAN against persistence at g4: %d of %d, passed = %s" % (pc3["positives"], pc3["n"], pc3["passed"])]),
    dict(id="N4", label="Test", kind="gating",
         lines=["sign test with a fixed design effect (assumed average pairwise sign correlation %.2f; design effect %.2f)" % (rho0, deff),
                "margins on the log-ratio scale: tier N %.4f (%.1f %%), tier S %+.4f (%.1f %%)" % (mN, pctN, mS, pctS),
                "%d of %d conditions needed at level 0.025" % (crit025, n)]),
    dict(id="N5", label="Graph, one-sided family-wise level %.3f" % cfg["alpha"], kind="gating",
         lines=["chain P: P1 (tier N, then S) -> P2 -> P3; chain K: K1 (tier N) -> K2 (tier N, then S)", "joined by P3 -> K1 and K2S -> P1N; a level passes on only after a rejection",
                "initial local levels: P1N %.4f, K1 %.4f (weight on P1N %.2f)" % (lv["P1N"], lv["K1"], cfg["graph_w"]),
                "second graph for five qualifiers: initial level %.3f each, family-wise %.3f" % (sec_lvl, cfg["alpha"])]),
    dict(id="N6", label="Outputs", kind="gating",
         lines=["states P and K; modifiers M1 to M3; title from one closed table fixed before scoring", "reverse-direction tests and persistence comparisons sit outside the graph (reported)"]),
    dict(id="N7", label="Reading", kind="reported", lines=["tier none = not shown, not equal", "descriptive numbers carry no tier"]),
    dict(id="N8", label="Outcome reached", kind="result",
         lines=["gate passed", "P1: %d of %d positive, %d needed" % (pr["P1N"]["positives"], pr["P1N"]["n"], pr["P1N"]["crit_positives"]),
                "K1: %d of %d positive, %d needed" % (pr["K1"]["positives"], pr["K1"]["n"], pr["K1"]["crit_positives"]),
                "states %s and %s; M1, M2, M3 all %s; title %s" % (out["P"], out["K"], str(out["M1"]).lower(), out["title_id"])]),
    dict(id="N_stop", label="Stop: no title, no claim", kind="terminal", lines=["reached only if the gate fails"]),
]
edges = [
    dict(src="N1", dst="N2", label="", style="solid"),
    dict(src="N2", dst="N4", label="pass", style="solid"),
    dict(src="N2", dst="N_stop", label="fail", style="dashed"),
    dict(src="N1", dst="N3", label="same cells", style="dashed"),
    dict(src="N4", dst="N5", label="p-values", style="solid"),
    dict(src="N5", dst="N6", label="rejections", style="solid"),
    dict(src="N3", dst="N6", label="reported only", style="dashed"),
    dict(src="N6", dst="N7", label="", style="solid"),
    dict(src="N6", dst="N8", label="", style="solid"),
]
para_template = ("How to read the results. Three questions are answered in order. First, the checks for leaked labels and for failed synthetic recovery did not trip. "
                 "Second, P1 asks whether PINN-KAN is no more than %d %% worse than the best tuned learner at g1: %d of %d held-out conditions agreed, %d were needed, "
                 "so the comparison is undecided, which is not a finding of equality. Third, K1 asks the same of the extracted law against PINN-KAN at g4: %d of %d, %d needed. "
                 "Persistence was beaten in %d of %d conditions at g1.")
para = para_template % (round(pctN), pr["P1N"]["positives"], pr["P1N"]["n"], pr["P1N"]["crit_positives"], pr["K1"]["positives"], pr["K1"]["n"], pr["K1"]["crit_positives"],
                        pr["R1g1"]["positives"], pr["R1g1"]["n"])
words = len(re.findall(r"\S+", para))
assert words <= 100, words
assert "withdrawn" not in para
res = dict(note="Figure content for a figure maker; numbers from stored frozen JSON. Colour rule: kind gating / reported / design / result / terminal.", nodes=nodes, edges=edges,
           practitioner_paragraph=para, practitioner_paragraph_word_count=words,
           sources={"contrasts": "runs/stats_frozen/analysis/contrasts_v4_B.json", "controls": "runs/stats_frozen/analysis/controls.json", "critical_count_at_0.025": "t2_rho_sweep.json sweep[0.03].crit_levels"})
jdump(res, "c1_flow.json")
print(words, para)
