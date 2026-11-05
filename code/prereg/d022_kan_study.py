"""D022 (KAN part): synthetic check of shape-constrained edges (M), library-aware training (L), both (ML) against the unchanged KAN (B). Rule: debates/D022_datasets_kan/kan_study_rule.md
(committed before the first run). CPU only, synthetic data only, no production file edited (the variants are defined here and plugged in as `law.cyc`).
    .venv/Scripts/python.exe -P code/prereg/d022_kan_study.py --proc 0 --nproc 2 --seeds 10 --deadline-min 45"""
import argparse
import copy
import json
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np  # noqa: E402
import torch  # noqa: E402
from scipy.stats import qmc  # noqa: E402
from torch import nn  # noqa: E402

torch.set_num_threads(1)

from models.kan_spline import KANLayer, bspline_basis  # noqa: E402
from pinnkan import arms as A  # noqa: E402
from pinnkan import data as D  # noqa: E402
from pinnkan import law as LAW  # noqa: E402
from pinnkan import metrics, symbolic, synth  # noqa: E402
from pinnkan.hard import make_law  # noqa: E402
from pinnkan.law import batch_from_cells  # noqa: E402
from pinnkan.pinn import fit_pinn, predict_pinn  # noqa: E402
from pinnkan.specs import SPECS  # noqa: E402

SPEC = SPECS["synthetic"]
OUT = os.path.join(ROOT, "runs", "D022_kan_synth")
LAM_LIB = 100.0
FORECAST = False        # the held-out forecast RMSE of the rule (reported, no consequence) is dropped to fit the 1 h limit; E_par/E_ext carry the decision
G = symbolic.G_GRID
SIGNS = np.array([+1.0, 0.0, +1.0, +1.0, 0.0])           # T, soc_mid, dod, c_ch, c_dch (physics sign prior of M)
VARIANTS = {"B": (False, False), "M": (True, False), "L": (False, True), "ML": (True, True)}
LINEAR_G0 = ("T_C", "dod", "c_ch", "c_dch")


# ------------------------------------------------------------------ truth G3 (not in synth.py): U-shaped C_ch effect
_orig_truth = synth._truth


def _truth3(kind, spec):
    if kind != "G3":
        return _orig_truth(kind, spec)
    _, f_cal = _orig_truth("G0", spec)

    def f3(raw):
        s = spec.norm(np.atleast_2d(raw))
        sT, ssoc, sdod, scch, scdch = (s[:, i] for i in range(5))
        return 0.5 * sT + 0.8 * scch ** 2 + 0.3 * scdch + 0.4 * sdod + 0.2 * np.sin(2.0 * ssoc)
    return f3, f_cal


synth._truth = _truth3


# ------------------------------------------------------------------ variant map
class MonoKANLayer(KANLayer):
    """KANLayer whose edges are monotone by construction for the inputs with sign +-1 (sign 0 = free): spline coefficients = sign x cumsum(softplus(raw)), base weight = sign x softplus(raw)"""

    def __init__(self, n_in, n_out, grid, lo, hi, signs):
        super().__init__(n_in, n_out, grid=grid, k=3, lo=lo, hi=hi)
        self.register_buffer("signs", torch.tensor(np.asarray(signs, float), dtype=torch.float32))
        with torch.no_grad():
            for i in range(n_in):
                if float(self.signs[i]) != 0.0:
                    self.base_w[:, i] = -4.0
                    self.spline_w[:, i, :] = -4.0 + 0.1 * torch.randn(n_out, self.spline_w.shape[-1])

    def eff(self):
        sg = self.signs
        free = sg == 0
        base = torch.where(free[None, :], self.base_w, sg[None, :] * nn.functional.softplus(self.base_w))
        spl = torch.where(free[None, :, None], self.spline_w, sg[None, :, None] * torch.cumsum(nn.functional.softplus(self.spline_w), -1))
        return base, spl

    def forward(self, x):
        b = bspline_basis(x, self.knots, self.k)
        base, spl = self.eff()
        return nn.functional.silu(x) @ base.T + b.reshape(x.shape[0], -1) @ spl.reshape(self.n_out, -1).T


def _proj_resid_mats(xs_fam):
    """for a list of design matrices X (G, p): the residual projectors I - X (X'X)^-1 X'"""
    out = []
    for X in xs_fam:
        P = X @ np.linalg.pinv(X.T @ X) @ X.T
        out.append(torch.tensor(np.eye(len(X)) - P, dtype=torch.float32))
    return out


class VariantMap(nn.Module):
    def __init__(self, d, hidden, grid, mono, lib, geos, s_train, l2):
        super().__init__()
        widths = [d, hidden, 1] if hidden else [d, 1]
        layers = []
        for li, (a, b) in enumerate(zip(widths[:-1], widths[1:])):
            r = 1.0 if li == 0 else 2.0
            sg = (SIGNS if li == 0 else np.ones(a)) if mono else None
            layers.append(MonoKANLayer(a, b, grid, -r, r, sg) if mono else KANLayer(a, b, grid=grid, k=3, lo=-r, hi=r))
        self.layers = nn.ModuleList(layers)
        self.mono, self.lib, self.l2 = mono, lib, float(l2)
        self.register_buffer("s_train", torch.tensor(np.clip(s_train, -1.0, 1.0 - 1e-6), dtype=torch.float32))
        if lib:
            t = np.linspace(-1.0, 1.0, G)
            self.first = []
            for g in geos:
                x = np.linspace(g.lo, g.hi, G)
                self.first.append((torch.tensor(x, dtype=torch.float32), _proj_resid_mats([np.stack([g.u(x), np.ones(G)], 1), np.stack([np.log(g.p(x) / g.pref), np.ones(G)], 1)])))
            tt = np.linspace(0, 1, G)
            self.hidden_mats = _proj_resid_mats([np.stack([2 * tt - 1, np.ones(G)], 1), np.stack([np.log(tt + 0.05), np.ones(G)], 1)])

    def _wb(self, layer):
        return layer.eff() if isinstance(layer, MonoKANLayer) else (layer.base_w, layer.spline_w)

    def forward(self, s):
        x = s.clamp(-1.0, 1.0 - 1e-6)
        for l in self.layers:
            x = l(x)
        return x[:, 0]

    def library_penalty(self):
        tot = 0.0
        for li, layer in enumerate(self.layers):
            base, spl = self._wb(layer)
            if li == 0:
                grids = [(g, mats) for g, mats in self.first]
            else:
                with torch.no_grad():
                    z = self.layers[0](self.s_train)
                grids = []
                for j in range(z.shape[1]):
                    lo, hi = z[:, j].min(), z[:, j].max()
                    if float(hi - lo) < 1e-6:
                        grids.append((None, None))
                    else:
                        grids.append((lo + (hi - lo) * torch.linspace(0, 1, G), self.hidden_mats))
            for i, (xg, mats) in enumerate(grids):
                if xg is None:
                    continue
                Bm = bspline_basis(xg.unsqueeze(1), layer.knots, layer.k)[:, 0, :]
                Y = nn.functional.silu(xg)[:, None] * base[:, i][None, :] + Bm @ spl[:, i, :].T          # (G, n_out)
                r = torch.stack([((M @ Y) ** 2).mean(0) for M in mats], 0).min(0).values                 # min over {linear, log}
                tot = tot + r.sum()
        return tot

    def spline_l2(self):
        ridge = sum((self._wb(l)[1] ** 2).sum() for l in self.layers)
        return ridge + ((LAM_LIB / self.l2) * self.library_penalty() if self.lib else 0.0)

    def sparsity(self):
        return torch.zeros(())

    def to_plain(self):
        """a law.KANMap with the effective weights (for symbolic.extract_law)"""
        d = self.layers[0].n_in
        h = self.layers[0].n_out if len(self.layers) == 2 else None
        km = LAW.KANMap(d, h, self.layers[0].grid)
        with torch.no_grad():
            for dst, src in zip(km.net.layers, self.layers):
                b, sw = self._wb(src)
                dst.base_w.copy_(b)
                dst.spline_w.copy_(sw)
        return km


# ------------------------------------------------------------------ helpers
def probe_rows(train, n=300, seed=0):
    cyc = np.array([c.raw for c in train if c.kind == "cycling"])
    lo, hi = cyc[:, 1:].min(0), cyc[:, 1:].max(0)
    u = qmc.LatinHypercube(d=4, seed=seed).random(n)
    return np.column_stack([np.resize(np.array([23.0, 35.0, 45.0]), n), lo + u * (hi - lo)])


def fvals(fn, raw):
    s = np.clip(SPEC.norm(raw), -1.0, 1.0 - 1e-6)
    with torch.no_grad():
        return fn(torch.tensor(s, dtype=torch.float32)).numpy().ravel().astype(float)


def law_err(fn, raw, t_y, rng_y):
    f = fvals(fn, raw)
    e = (f - f.mean()) - (t_y - t_y.mean())
    return float(np.sqrt(np.mean(e ** 2)) / rng_y)


def mono_violation(fn, raw):
    """fraction of probe rows where raising a signed input by 0.05 (normalised) lowers the map (sign +1 for T, DoD, C_ch)"""
    s = np.clip(SPEC.norm(raw), -1.0, 1.0 - 0.06)
    base = fvals(fn, SPEC.denorm(s))
    viol = []
    for i in (0, 2, 3):
        s2 = s.copy()
        s2[:, i] += 0.05
        viol.append(np.mean(fvals(fn, SPEC.denorm(s2)) < base - 1e-9))
    return [float(v) for v in viol]


def fam_first_layer(rep):
    edges = rep["cyclic"]["layers"][0]["edges"]
    return {nm: [edges[j][i]["family"] for j in range(len(edges))] for i, nm in enumerate(SPEC.stress_names)}


def one_cell(kind, m, seed, log):
    S0 = synth.make_synthetic(kind, n_cyc_cond=40, n_sto_cond=8, reps=2, seed=seed)
    train32, test = synth.split_conditions(S0.cells, 0.2, seed)
    ids = {c.cond for c in train32 if c.kind == "cycling"}
    train = D.apply_subset(train32, "synthetic", "B", None, 0, m, ids=ids)[0] if m < 32 else train32
    raw_probe = probe_rows(train, seed=seed)
    t_probe = np.asarray(S0.log_rate_cyc(raw_probe), float).ravel()
    rng_y = float(np.ptp(t_probe))
    te_raw = np.unique(np.array([c.raw for c in test if c.kind == "cycling"]), axis=0)
    t_te = np.asarray(S0.log_rate_cyc(te_raw), float).ravel()
    prep = D.prepare_many([c for c in test if c.kind == "cycling"], D.WindowRule.for_spec(SPEC, k_cycling=3, k_storage=2))
    b = batch_from_cells(SPEC, train)
    cyc = (b.is_cyc > 0.5).numpy()
    s_cyc = np.unique(b.s.numpy()[cyc], axis=0)
    s_cal = b.s.numpy()[:, SPEC.soc_index]
    geos = symbolic.stress_geos(SPEC, s_cyc)
    recs = []
    for vname, (mono, lib) in VARIANTS.items():
        for arm_name, arm_id, over in (("KAN", "A15", {"h": 1}), ("GAM", "G15", {})):
            t0 = time.time()
            hp = {**A.default_hp(arm_id), **over, "sparsity": 0.0}
            hpm = dict(hp, map=A.ARMS[arm_id].map_kind)
            rec = {"kind": kind, "m": m, "seed": seed, "variant": vname, "arm": arm_name, "n_train_cyc_conditions": len({c.cond for c in train if c.kind == "cycling"})}
            try:
                if vname == "B":
                    model = fit_pinn(b, SPEC, hpm, "self_limiting", seed, steps=A.BASE_STEPS["pinn"])
                    cyc_fn, plain = model.law.cyc, model.law.cyc
                else:
                    torch.manual_seed(seed)
                    law = make_law(SPEC, b, hpm, "self_limiting")
                    law.cyc = VariantMap(SPEC.d, hp.get("h") if arm_name == "KAN" else None, int(hp["grid"]), mono, lib, geos, s_cyc, hp["l2"])
                    model = fit_pinn(b, SPEC, hpm, "self_limiting", seed, steps=A.BASE_STEPS["pinn"], law=law)
                    cyc_fn, plain = model.law.cyc, model.law.cyc.to_plain()
                rec["E_par"] = law_err(cyc_fn, raw_probe, t_probe, rng_y)
                rec["E_test"] = law_err(cyc_fn, te_raw, t_te, rng_y)
                rec["mono_violation_T_dod_cch"] = mono_violation(cyc_fn, raw_probe)
                law_p = copy.deepcopy(model.law)
                law_p.cyc = plain
                for cap in (2, 3):
                    sym_cyc, _, rep = symbolic.extract_law(law_p, SPEC, s_cyc, s_cal, cap)
                    rec[f"E_ext{cap}"] = law_err(sym_cyc, raw_probe, t_probe, rng_y)
                    rec[f"n_coefs_cyc{cap}"] = int(rep["cyclic"]["n_coefs"])
                    rec[f"fam{cap}"] = fam_first_layer(rep)
                try:
                    if not FORECAST:
                        raise RuntimeError('forecast skipped (time limit)')
                    preds, _ = predict_pinn(model, SPEC, [p.win for p in prep], float(hp["lam_res"]), seed, steps=60)
                    rec["forecast_rmse_pp"] = float(np.mean([r["rmse_pp"] for r in metrics.score_prepared(preds, prep)]))
                except Exception as ex:
                    rec["forecast_rmse_pp"] = float("nan")
                    rec["forecast_error"] = repr(ex)[:160]
            except Exception as ex:                                   # a failed fit must not lose the cell
                rec["error"] = repr(ex)[:300]
            rec["seconds"] = time.time() - t0
            recs.append(rec)
            log(f"{kind} m={m} s={seed} {vname:2s} {arm_name:3s} {rec['seconds']:.0f}s E_par {rec.get('E_par', float('nan')):.3f} ext2 {rec.get('E_ext2', float('nan')):.3f} ext3 {rec.get('E_ext3', float('nan')):.3f}")
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--proc", type=int, default=0)
    ap.add_argument("--nproc", type=int, default=2)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--deadline-min", type=float, default=45.0)
    ap.add_argument("--only", default=None, help="kind:m:seed timing run")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"kan_p{a.proc}.jsonl")
    t_start = time.time()

    def log(s):
        print(f"[{(time.time() - t_start) / 60:6.1f} min] {s}", flush=True)
    if a.only:
        k, m, s = a.only.split(":")
        cells = [(k, int(m), int(s))]
    else:
        cells = [(k, m, s) for s in range(a.seeds) for k in ("G0", "G2", "G3") for m in (32, 8)]
        cells = [c for c in cells if c[2] % a.nproc == a.proc]
    last = 0.0
    for kind, m, seed in cells:
        if (time.time() - t_start) / 60.0 + last * 1.1 > a.deadline_min:
            log(f"deadline: stop before seed {seed} ({kind}, m={m})")
            break
        t = time.time()
        recs = one_cell(kind, m, seed, log)
        with open(path, "a", encoding="utf8") as fh:
            for r in recs:
                fh.write(json.dumps(r) + "\n")
        last = (time.time() - t) / 60.0


if __name__ == "__main__":
    main()
