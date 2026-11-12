"""V0: the harness must reproduce the frozen outer-test predictions (not only the training side).
Usage: python -P validate_v0.py <fold> <m> [arms...]      writes runs/post_review/_harness/V0_f{f}_m{m}.json
Compares seed-0 predictions of A1 (frozen path via make_arm, and the harness copy A1x with schedule frozen / zw 1), A2, A9 (make_arm and A9x), A15, G15 with the rows of
runs/conf_samsung_B_f{f}_m{m}/predictions.csv at every scored k (0, 2, full). Tolerance 1e-9."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness as H  # noqa: E402
import numpy as np  # noqa: E402

f, m = int(sys.argv[1]), int(sys.argv[2])
arms = sys.argv[3:] or ["A1", "A1x", "A2", "A9", "A9x", "A15", "G15"]
Hd = H.load_fold(f, m)
spec, train, KC, ctx = Hd["spec"], Hd["train"], Hd["KC"], Hd["ctx"]
fp = H.frozen_preds(f, m)
out = {"fold": f, "m": m, "seed": 0, "tolerance": 1e-9, "arms": {}}
for a in arms:
    base = a.rstrip("x")
    hp = Hd["hp"][base]
    if a == "A1x":
        arm = H.A1x(spec, hp, 0, ctx).fit(train)
    elif a == "A9x":
        arm = H.A9x(spec, hp, 0, ctx).fit(train)
    else:
        arm = H.make_arm(base, spec, hp, 0, dict(ctx, rule=KC["0"]["rule"])).fit(train)
    worst, n, per_k = 0.0, 0, {}
    for k, kc in KC.items():
        if base in ("R1", "R2") and k == "0":
            continue
        preds = arm.predict(kc["wc"])
        w = 0.0
        for p in kc["prep"]:
            cid = p.cell.cell_id
            t_f, pr_f = fp[(f"outer_test_k{k}", base, "0", cid)]
            assert np.allclose(t_f, p.win.t_fc), "forecast times differ"
            d = float(np.max(np.abs(np.asarray(preds[cid], float) - pr_f)))
            w = max(w, d)
            n += 1
        per_k[k] = w
        worst = max(worst, w)
    out["arms"][a] = {"max_abs_diff": worst, "per_k": per_k, "n_cells_checked": n, "pass": bool(worst <= 1e-9)}
    print(a, f, m, worst, flush=True)
H.wjson(os.path.join(H.OUT, "_harness", f"V0_f{f}_m{m}.json"), out)
print(json.dumps({a: v["pass"] for a, v in out["arms"].items()}))
