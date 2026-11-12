"""Post-review exploratory harness (D048). POST-HOC, EXPLORATORY. Imports the frozen package from a detached worktree at c6a89b6 (read-only);
every output goes to MAIN/runs/post_review/<exp-id>/ . Nothing here calls guard.record_scoring or writes runs/prereg/ or code/.

Setup (done once by the lead of the run, see runs/post_review/SETUP.md):
  WT = detached worktree of c6a89b6 (+ copies of untracked runs/prereg/FROZEN and runs/item_f/*, junction data/processed -> MAIN/data/processed)
  python -P <script>  (interpreter: MAIN/.venv), CPU only, 1 thread per process.
"""
import os
import sys

MAIN = r"C:\Users\Shlok\Downloads\PINN KAN battery paper"
WT = r"C:\Users\Shlok\Downloads\PINN KAN battery paper-frozen"
OUT = os.path.join(MAIN, "runs", "post_review")
RUNS = os.path.join(MAIN, "runs")

os.environ["PINNKAN_ROOT"] = WT
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
sys.dont_write_bytecode = True
_CODE = os.path.join(WT, "code")
if _CODE not in sys.path:
    sys.path.insert(0, _CODE)

import contextlib  # noqa: E402
import csv  # noqa: E402
import dataclasses  # noqa: E402
import gzip  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import platform  # noqa: E402
import subprocess  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

torch.set_num_threads(1)

from pinnkan import guard, inversion, law, metrics, run  # noqa: E402
from pinnkan import pinn as P  # noqa: E402
from pinnkan.arms import ARMS, PINNArm, make_arm  # noqa: E402
from pinnkan.data import WindowRule, prepare_many  # noqa: E402
from pinnkan.hard import HardODE, predict_hard, split_by_cell  # noqa: E402
from pinnkan.law import GRAD_CLIP, SIGMA, WARMUP, batch_forecast_query, batch_from_cells, batch_from_windows, clip_and_count, clip_fraction, new_clip_stats, state_factor  # noqa: E402

SEEDS = [0, 1, 2, 3, 4]
CELLS = [(f, m) for f in range(5) for m in (8, 32)]
KSEL = {8: "2", 32: "full"}          # g1 = m 8 scored at k = 2; g4 = m 32 scored at k = full (frozen cells)
GNAME = {8: "g1", 32: "g4"}


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for ch in iter(lambda: fh.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def wjson(path, obj):
    def default(o):
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
        return str(o)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf8") as fh:
        json.dump(obj, fh, indent=1, default=default)


def assert_out(path):
    """every write of this harness lands under MAIN/runs/post_review"""
    ap = os.path.abspath(path)
    if not ap.startswith(os.path.abspath(OUT) + os.sep):
        raise RuntimeError(f"refusing to write outside runs/post_review: {ap}")


# ------------------------------------------------------------------------------------------------ data
_CACHE = {}


def src_dir(f, m):
    return os.path.join(RUNS, f"conf_samsung_B_f{f}_m{m}")


def load_fold(f, m):
    """frozen data, windows, context and tuned hyperparameters of the confirmatory run (fold f, m); cached per process"""
    key = (f, m)
    if key in _CACHE:
        return _CACHE[key]
    d = src_dir(f, m)
    cfg_in = json.load(open(os.path.join(d, "config.json"), encoding="utf8"))["config_input"]
    cfg = run.validate_config(cfg_in, WT)
    guard.require_item_f_record(WT, RUNS)
    D = run.build_data(cfg, WT, "test", RUNS)
    spec, train = D["spec"], D["train"]
    wk = cfg["window"]
    rule = WindowRule.for_spec(spec, k_cycling=wk.get("k_cycling"), k_storage=wk.get("k_storage"), W=wk.get("W"), shift=wk.get("shift", 0))
    rule_test = dataclasses.replace(rule, min_fc_points=int(cfg["min_fc_points"]))
    rule_tune = WindowRule.for_grid(spec, 2 if int(cfg["m"]) < 32 else "full", rule)
    td = json.load(open(os.path.join(d, "tuning_done.json"), encoding="utf8"))
    ctx = {"backbone": td["backbone"], "steps_scale": cfg["steps_scale"], "rule": rule_tune, "extra_twin_raw": None, "oracle": cfg["oracle_throughput"],
           "per_cell_factor": cfg["per_cell_factor"], "lab_indicator": bool(cfg["lab_indicator"]), "a10_drop_soc100_storage": bool(cfg["a10_drop_soc100_storage"]),
           "symbolic": dict(cfg["symbolic"] or {}), "a10_starts": cfg.get("a10_starts", 8), "pinn": cfg["pinn"]}
    KC = {}
    for kl, rk in run._score_windows(cfg, rule_test, spec):
        pk = prepare_many(D["test"], rk, oracle=cfg["oracle_throughput"])
        KC[kl] = {"rule": rk, "prep": pk, "wc": [p.win for p in pk]}
    hp = {a: v["best_hp"] for a, v in td["arms"].items()}
    comp = json.load(open(os.path.join(d, "comparators.json"), encoding="utf8"))
    out = {"cfg": cfg, "D": D, "spec": spec, "train": train, "KC": KC, "ctx": ctx, "hp": hp, "backbone": td["backbone"], "dstar": comp["D*"]["arm"], "ag": (comp.get("AG") or {}).get("arm"),
           "src": d}
    _CACHE[key] = out
    return out


# ------------------------------------------------------------------------------------------------ frozen references
def frozen_cond_scores(f, m, k=None):
    """frozen condition scores {arm: {cond: pp}} of the confirmatory run at k (None = g-cell of that m)"""
    k = k or KSEL[m]
    d = src_dir(f, m)
    name = "condition_scores.json" if k == "full" else f"condition_scores_k{k}.json"
    return json.load(open(os.path.join(d, name), encoding="utf8"))


def frozen_seed_scores(f, m, k=None):
    k = k or KSEL[m]
    d = src_dir(f, m)
    name = "condition_scores_seed.json" if k == "full" else f"condition_scores_seed_k{k}.json"
    return json.load(open(os.path.join(d, name), encoding="utf8"))


_PRED = {}


def frozen_preds(f, m):
    """predictions.csv of the confirmatory run as {(phase, arm, seed, cell): (t array, pred array)}"""
    if (f, m) in _PRED:
        return _PRED[(f, m)]
    out = {}
    with open(os.path.join(src_dir(f, m), "predictions.csv"), encoding="utf8", newline="") as fh:
        r = csv.reader(fh)
        next(r)
        for ph, arm, sd, cell, cond, t, pr, tr in r:
            e = out.setdefault((ph, arm, sd, cell), ([], []))
            e[0].append(float(t))
            e[1].append(float(pr))
    out = {k: (np.array(v[0]), np.array(v[1])) for k, v in out.items()}
    _PRED[(f, m)] = out
    return out


# ------------------------------------------------------------------------------------------------ A1 variants
class ZPINNModel(P.PINNModel):
    """PINNModel with a weight zw on the z prior term of the training loss (zw = 1.0 reproduces the frozen loss exactly)"""
    zw = 1.0

    def loss(self, b, col, lam, l2, sparsity, gen, n_a=512, n_b=192, n_c=64):
        F = self.F(b.obs_t, b.s[b.obs_cell], self.z[b.obs_cell])
        r = F - b.obs_y
        n = r.numel()
        data = (r ** 2).mean()
        R = self.residual_terms(b, col, gen, self.delta, self.z, n_a, n_b, n_c)
        res = (R ** 2).mean()
        tot = (data + lam * res) / SIGMA ** 2 + ((self.delta - self.prior_mean(b.ind)) ** 2).sum() / (law.TAU ** 2 * n) + self.zw * ((self.z ** 2).sum() / n) + self.law.reg(l2, sparsity)
        return tot, data, res


def fit_pinn_x(b, spec, hp, backbone, seed, steps=2000, lr=5e-3, schedule="frozen", zw=1.0, warmup=WARMUP, clip=GRAD_CLIP, bal_every=10, bal_lo=1e-3, bal_hi=1e2, bal_ema=0.1):
    """copy of pinn.fit_pinn (pinn.py:163-196) with (a) a z-prior weight, (b) a residual-weight schedule:
        frozen   : lam_res x the frozen 0 -> 1 warm-up ramp (identical to fit_pinn when zw = 1)
        balance  : lam_state updated every `bal_every` steps to 0.9 lam_state + 0.1 ||grad data|| / ||grad res|| (gradients w.r.t. the solution network and the law, both /SIGMA^2),
                   clamped to [bal_lo, bal_hi]; applied lam_state x the frozen warm-up ramp; starts at the tuned lam_res (a simplification of Wang, Teng, Perdikaris 2020)
        anneal   : lam = 10^(-3 + 3 it / (steps - 1)) (log-linear 1e-3 -> 1 over all steps; no extra ramp)
    returns the model with .lam_final (value used at inversion) and .lam_traj"""
    torch.manual_seed(seed)
    lw = P.make_law(spec, b, hp, backbone)
    m = ZPINNModel(spec, lw, b.C, backbone, width=32, depth=3, zdim=2, n_ind=0 if b.ind is None else int(b.ind.shape[1]))
    m.zw = float(zw)
    col = P.make_collocation(spec, b, seed, placement=hp.get("placement", "record_end"), extra_twin_raw=None)
    m.col_t_max = col.t_max
    m.pts_per_cell = b.obs_t.numel() / b.C
    opt = torch.optim.Adam(m.parameters(), lr=lr)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=lr * 0.1)
    gen = torch.Generator().manual_seed(seed + 17)
    lam, l2, sp = float(hp.get("lam_res", 1.0)), float(hp.get("l2", 1e-4)), float(hp.get("sparsity", 0.0))
    last = (float("nan"), float("nan"))
    stats = new_clip_stats()
    lam_state, traj = lam, []
    shared = list(m.net.parameters()) + list(m.law.parameters())
    lam_eff = lam
    for it in range(steps):
        opt.zero_grad(set_to_none=True)
        ramp = min(1.0, (it + 1) / max(warmup * steps, 1.0))
        if schedule == "frozen":
            lam_eff = lam * ramp
        elif schedule == "balance":
            lam_eff = lam_state * ramp
        elif schedule == "anneal":
            lam_eff = 10.0 ** (-3.0 + 3.0 * it / max(steps - 1, 1))
        else:
            raise ValueError(schedule)
        L, data, res = m.loss(b, col, lam_eff, l2, sp, gen)
        if schedule == "balance" and it % bal_every == 0:
            gd = torch.autograd.grad(data / SIGMA ** 2, shared, retain_graph=True, allow_unused=True)
            gr = torch.autograd.grad(res / SIGMA ** 2, shared, retain_graph=True, allow_unused=True)
            nd = float(torch.sqrt(sum((g ** 2).sum() for g in gd if g is not None)))
            nr = float(torch.sqrt(sum((g ** 2).sum() for g in gr if g is not None)))
            if np.isfinite(nd) and np.isfinite(nr) and nr > 0:
                hat = nd / nr
                lam_state = float(np.clip((1.0 - bal_ema) * lam_state + bal_ema * hat, bal_lo, bal_hi))
            traj.append((it, lam_state))      # the update takes effect from the next step (this step's loss was built with the previous lam_state)
        L.backward()
        clip_and_count(m.parameters(), clip, stats)
        opt.step()
        sch.step()
        last = (float(data.detach()), float(res.detach()))
    m.train_data_mse, m.train_res_msq = last
    m.clip_fraction = clip_fraction(stats)
    m.lam_final = {"frozen": lam, "balance": lam_state, "anneal": 1.0}[schedule]
    m.lam_traj = traj
    return m


class A1x:
    """A1 (PINNArm) with the harness fit; hp as tuned except the studied variable"""

    def __init__(self, spec, hp, seed, ctx, schedule="frozen", zw=1.0, arm_id="A1"):
        self.spec, self.hp, self.seed, self.ctx, self.schedule, self.zw, self.arm_id = spec, dict(hp), int(seed), ctx, schedule, float(zw), arm_id

    def fit(self, train):
        a = ARMS[self.arm_id]
        hp = dict(self.hp, map=a.map_kind)
        b = batch_from_cells(self.spec, train, bool(self.ctx.get("lab_indicator")))
        steps = max(int(2000 * float(self.ctx.get("steps_scale", 1.0))), 5)
        self.model = fit_pinn_x(b, self.spec, hp, self.ctx["backbone"], self.seed, steps=steps, schedule=self.schedule, zw=self.zw)
        return self

    def predict(self, wcells, with_latents=False):
        zw = None if self.zw == 1.0 else self.zw
        preds, lat = P.predict_pinn(self.model, self.spec, wcells, float(self.model.lam_final), self.seed, z_weight=zw)
        return (preds, lat) if with_latents else preds


class A9x:
    """A9 with a z-prior weight in training and inversion (zw = 1 reproduces fit_data_only)"""

    def __init__(self, spec, hp, seed, ctx, zw=1.0):
        self.spec, self.hp, self.seed, self.ctx, self.zw = spec, dict(hp), int(seed), ctx, float(zw)

    def fit(self, train):
        b = batch_from_cells(self.spec, train, bool(self.ctx.get("lab_indicator")))
        steps = max(int(1500 * float(self.ctx.get("steps_scale", 1.0))), 5)
        torch.manual_seed(self.seed)
        hp = self.hp
        m = P.DataOnlyF(self.spec, b.C, int(hp.get("width", 32)), int(hp.get("depth", 3)), int(hp.get("zdim", 2)), n_ind=0 if b.ind is None else int(b.ind.shape[1]))
        lr = 5e-3
        opt = torch.optim.Adam(m.parameters(), lr=lr)
        sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=lr * 0.1)
        wd = float(hp.get("wd", 1e-4))
        stats = new_clip_stats()
        for _ in range(steps):
            opt.zero_grad(set_to_none=True)
            r = m.F(b.obs_t, b.s[b.obs_cell], m.z[b.obs_cell]) - b.obs_y
            n = r.numel()
            ((r ** 2).mean() / SIGMA ** 2 + self.zw * (((m.z - m.z_prior(b.ind)) ** 2).sum() / n) + wd * m.weight_l2()).backward()
            clip_and_count(m.parameters(), GRAD_CLIP, stats)
            opt.step()
            sch.step()
        m.clip_fraction = clip_fraction(stats)
        self.model = m
        return self

    def predict(self, wcells):
        return P.predict_data_only(self.model, self.spec, wcells, z_weight=None if self.zw == 1.0 else self.zw)


# ------------------------------------------------------------------------------------------------ diagnostics (EXP_PLAN 0.4)
def a1_diagnostics(arm, wcells, prep, preds_F, lat, spec):
    """res_share, F-to-law gap, law readout, held-out residual at the inferred latents. Window cells and forecast query only (no label after the window enters any quantity;
    the law readout RMSE uses the scored labels exactly as any forecast score does)."""
    m = arm.model
    lam = float(m.lam_final)
    d = {"lam_final": lam, "train_data_mse": float(m.train_data_mse), "train_res_msq": float(m.train_res_msq)}
    tot = d["train_data_mse"] + lam * d["train_res_msq"]
    d["res_share"] = float(lam * d["train_res_msq"] / tot) if tot > 0 else float("nan")
    # law readout (no F, no z): delta_c by the frozen MAP inversion from the window
    hm = HardODE(spec, m.law, 1, m.backbone)
    law_preds, _ = predict_hard(hm, spec, wcells)
    law_rows = metrics.score_prepared(law_preds, prep)
    d["law_cond_scores"] = metrics.condition_scores(law_rows)
    gaps = []
    for p in prep:
        cid = p.cell.cell_id
        gaps.append(np.asarray(preds_F[cid], float) - np.asarray(law_preds[cid], float))
    g = np.concatenate(gaps) * 100.0
    d["F_minus_law_rms_pp"] = float(np.sqrt(np.mean(g ** 2)))
    d["F_minus_law_mean_abs_pp"] = float(np.mean(np.abs(g)))
    # held-out residual of F at the inferred latents over the forecast horizon
    z, delta = lat
    bq = batch_forecast_query(spec, wcells)
    to_n = spec.t_scale / spec.efc_scale
    nu = torch.tensor(np.concatenate([bq.curves[c].rate(bq.obs_t.numpy()[bq.obs_cell.numpy() == c] * spec.t_scale) * to_n for c in range(bq.C)]), dtype=torch.float32)
    # obs order is cell-major (series batch), so the concatenation above matches obs_t
    with torch.enable_grad():
        A_cal, A_cyc = m.law.amplitudes(bq.s, bq.is_cyc, delta.detach())
        oc = bq.obs_cell
        t = bq.obs_t.clone().requires_grad_(True)
        F = m.F(t, bq.s[oc], z.detach()[oc])
        dF = torch.autograd.grad(F.sum(), t)[0]
        rhs = (A_cal[oc] + A_cyc[oc] * nu) * state_factor(F, m.backbone)
        R = (dF - rhs).detach()
        rel = (R.abs() / rhs.detach().abs().clamp_min(1e-12))
    d["heldout_abs_R_median"] = float(R.abs().median())
    d["heldout_abs_R_mean"] = float(R.abs().mean())
    d["heldout_rel_R_median"] = float(rel.median())
    d["heldout_rel_R_mean"] = float(rel.mean())
    d["delta_sd_over_tau"] = float(m.delta.detach().std() / law.TAU)
    d["z_rms_heldout"] = float(torch.sqrt((z.detach() ** 2).mean()))
    return d


# ------------------------------------------------------------------------------------------------ job runner
def ens_and_scores(per_seed_preds, prep):
    rows_seed = [metrics.score_prepared(p, prep) for p in per_seed_preds]
    ens_rows = metrics.ensemble_rows(per_seed_preds, prep)
    cs_ens = metrics.condition_scores(ens_rows)
    cs_seed, sd = metrics.seed_condition_scores(rows_seed)
    return {"ens_rows": ens_rows, "seed_rows": rows_seed, "cond_ens": cs_ens, "cond_seed": cs_seed, "seed_sd_of_mean": sd}


def write_predictions(path, phase, arm, seed_rows, ens_rows):
    assert_out(path)
    with gzip.open(path, "wt", newline="", encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["phase", "arm", "seed", "cell_id", "cond", "t", "pred_retention", "true_retention"])
        for sd, rows in list(zip(SEEDS, seed_rows)) + [("ens", ens_rows)]:
            for r in rows:
                for t, p, y in zip(r["_t"], r["_pred"], r["_true"]):
                    w.writerow([phase, arm, sd, r["cell"], r["cond"], float(t), float(p), float(y)])


def env_record():
    import optuna, scipy, sklearn  # noqa: E401
    return {"python": sys.version.split()[0], "platform": platform.platform(), "torch": torch.__version__, "numpy": np.__version__, "scipy": scipy.__version__, "sklearn": sklearn.__version__,
            "optuna": optuna.__version__, "torch_threads": torch.get_num_threads(), "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"), "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS"),
            "cuda_available": bool(torch.cuda.is_available()), "interpreter": sys.executable}


def git_record():
    def g(*a):
        return subprocess.run(["git", *a], cwd=WT, capture_output=True, text=True, timeout=30).stdout.strip()
    return {"worktree": WT, "commit": g("rev-parse", "HEAD"), "dirty_tracked": g("status", "--porcelain", "--untracked-files=no"), "harness_sha256": sha256_file(os.path.abspath(__file__))}


def job_dir(exp, variant, f, m):
    return os.path.join(OUT, exp, f"{variant}_f{f}_m{m}")


def is_done(exp, variant, f, m):
    return os.path.exists(os.path.join(job_dir(exp, variant, f, m), "condition_scores.json"))


def run_job(exp, variant, f, m, arm_name, make_fit, config, diag=False, seeds=SEEDS, ks=None, cm=None, per_seed_endpoint=False):
    """fit `make_fit(spec, hp, seed, ctx)` for each seed on the frozen training side, predict at the scored k (and `ks`), write the job record.
    make_fit returns an object with fit(train) and predict(wcells). cm: optional context manager factory wrapping the whole job (law overrides, library patches)."""
    jd = job_dir(exp, variant, f, m)
    if is_done(exp, variant, f, m):
        return jd
    assert_out(os.path.join(jd, "x"))
    os.makedirs(jd, exist_ok=True)
    t0 = time.time()
    H = load_fold(f, m)
    spec, train, KC, ctx = H["spec"], H["train"], H["KC"], H["ctx"]
    ks = ks or [KSEL[m]]
    log = open(os.path.join(jd, "RUN.log"), "a", encoding="utf8")

    def L(msg):
        log.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        log.flush()
    wjson(os.path.join(jd, "config.json"), {"exp": exp, "variant": variant, "fold": f, "m": m, "arm": arm_name, "seeds": seeds, "scored_k": ks, "backbone_ctx": ctx["backbone"], "hp_used": config.get("hp_used"),
                                          "variable": config, "frozen_source_run": H["src"], "role": "POST-HOC EXPLORATORY (D048)"})
    wjson(os.path.join(jd, "git.json"), git_record())
    wjson(os.path.join(jd, "env.json"), env_record())
    per_k = {k: [] for k in ks}
    diags, fit_secs, extras = [], [], []
    with (cm() if cm else contextlib.nullcontext()):
        for sd in seeds:
            tf = time.time()
            arm = make_fit(spec, H["hp"], sd, ctx).fit(train)
            fit_secs.append(time.time() - tf)
            for k in ks:
                inversion.LOG.clear()
                if diag and k == KSEL[m]:
                    preds, lat = arm.predict(KC[k]["wc"], with_latents=True)
                else:
                    preds = arm.predict(KC[k]["wc"])
                per_k[k].append(preds)
                if diag and k == KSEL[m]:
                    d = a1_diagnostics(arm, KC[k]["wc"], KC[k]["prep"], preds, lat, spec)
                    d["seed"] = sd
                    d["inversion_nonconverged"] = int(sum(r.get("n_nonconverged", 0) for r in inversion.LOG))
                    d["inversion_calls_cells"] = int(sum(r.get("n_inverted", 0) for r in inversion.LOG))
                    if getattr(arm.model, "lam_traj", None):
                        d["lam_traj_first_mid_last"] = [arm.model.lam_traj[0], arm.model.lam_traj[len(arm.model.lam_traj) // 2], arm.model.lam_traj[-1]]
                    diags.append(d)
                inversion.LOG.clear()
            if hasattr(arm, "extra_record"):
                extras.append(dict(arm.extra_record(), seed=sd))
            L(f"seed {sd}: fit {fit_secs[-1]:.1f} s")
    res = {}
    for k in ks:
        r = ens_and_scores(per_k[k], KC[k]["prep"])
        res[k] = r
        write_predictions(os.path.join(jd, f"predictions_k{k}.csv.gz"), f"post_review_k{k}", arm_name, r["seed_rows"], r["ens_rows"])
        endpoint = r["cond_seed"] if per_seed_endpoint else r["cond_ens"]
        wjson(os.path.join(jd, f"condition_scores_k{k}.json"), {arm_name: endpoint})
        wjson(os.path.join(jd, f"condition_scores_ens_k{k}.json"), {arm_name: r["cond_ens"]})
        wjson(os.path.join(jd, f"condition_scores_seed_k{k}.json"), {arm_name: r["cond_seed"]})
    wjson(os.path.join(jd, "metrics.json"), {"arm": arm_name, "endpoint": "per_seed" if per_seed_endpoint else "ensemble", "fit_seconds": fit_secs, "wall_seconds": time.time() - t0,
                                               "seed_sd_of_mean": {k: res[k]["seed_sd_of_mean"] for k in ks}, "primary_pp_ens": {k: float(np.mean(list(res[k]["cond_ens"].values()))) for k in ks},
                                               "primary_pp_per_seed": {k: float(np.mean(list(res[k]["cond_seed"].values()))) for k in ks}})
    if diags:
        wjson(os.path.join(jd, "diagnostics.json"), diags)
    if extras:
        wjson(os.path.join(jd, "extras.json"), extras)
    kp = KSEL[m]            # condition_scores.json (the g-cell of this m) is written last: its presence marks a finished job
    wjson(os.path.join(jd, "condition_scores.json"), {arm_name: (res[kp]["cond_seed"] if per_seed_endpoint else res[kp]["cond_ens"])})
    L(f"done in {time.time() - t0:.0f} s")
    log.close()
    return jd


def shas_for(exp_dir):
    """SHA256.json over every file under an experiment directory (except SHA256.json itself)"""
    out = {}
    for root, _, files in os.walk(exp_dir):
        for fn in sorted(files):
            if fn == "SHA256.json":
                continue
            p = os.path.join(root, fn)
            out[os.path.relpath(p, exp_dir).replace("\\", "/")] = sha256_file(p)
    wjson(os.path.join(exp_dir, "SHA256.json"), out)
    return out
