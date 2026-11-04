"""Arm registry (PREREG_v2 section 7.1): classes, tuned spaces, dimensions.

Interface:  arm = make_arm(arm_id, spec, hp, seed, ctx);  arm.fit(train_cells);  arm.predict(window_cells) -> {cell_id: retention at t_fc}
ctx keys: backbone, steps_scale (<1 shortens neural fits for smoke tests), rule (WindowRule), extra_twin_raw, oracle, per_cell_factor.
The backbone-tournament model is the hard-ODE-KAN with default settings (`TOURNAMENT_HP`)."""
from dataclasses import dataclass, field

import numpy as np
import torch

from . import baselines, semi
from .data import prepare_many
from . import free
from .hard import fit_hard, predict_hard
from .law import TAU, batch_from_cells
from .pinn import fit_data_only, fit_pinn, predict_data_only, predict_pinn

TOURNAMENT_HP = {"map": "kan", "h": 4, "grid": 5, "l2": 1e-4, "sparsity": 0.0}
DECADES = [1e-5, 1e-4, 1e-3, 1e-2]
LAM = [1e-3, 1e-2, 1e-1, 1.0, 10.0, 100.0]      # D013 C3: 1e-3 added (lower-edge precaution)
PLACE = ["record_end", "whole_axis"]

BASE_STEPS = {"hard": 1200, "pinn": 2000, "data": 1500, "free": 1000}


@dataclass
class ArmDef:
    arm_id: str
    label: str
    family: str
    space: dict = field(default_factory=dict)       # name -> ("cat", [..]) | ("logu", lo, hi) | ("int", lo, hi)
    fixed: dict = field(default_factory=dict)
    map_kind: str = ""
    tuned: bool = True

    @property
    def dims(self):
        return len(self.space)


ARMS = {
    "A1": ArmDef("A1", "PINN-KAN", "pinn", {"h": ("cat", [2, 3, 4, 6, 8]), "grid": ("cat", [2, 3, 5, 8, 12]), "l2": ("cat", DECADES),
                                            "sparsity": ("cat", [0.0, 1e-4, 1e-3, 1e-2]), "lam_res": ("cat", LAM), "placement": ("cat", PLACE)}, map_kind="kan"),
    "A2": ArmDef("A2", "hard-ODE-KAN", "hard", {"h": ("cat", [2, 3, 4, 6, 8]), "grid": ("cat", [2, 3, 5, 8, 12]), "l2": ("cat", DECADES),
                                                "sparsity": ("cat", [0.0, 1e-4, 1e-3, 1e-2])}, map_kind="kan"),
    "A3": ArmDef("A3", "PINN, parametric stress factors", "pinn", {"l2": ("cat", [1e-5, 1e-4, 1e-3, 1e-2, 1e-1]), "lam_res": ("cat", LAM), "placement": ("cat", PLACE)}, map_kind="param"),
    "A4": ArmDef("A4", "PINN, additive GAM", "pinn", {"grid": ("cat", [3, 5, 10, 20, 30]), "l2": ("cat", [1e-5, 1e-4, 1e-3, 1e-2, 1e-1]), "lam_res": ("cat", LAM), "placement": ("cat", PLACE)}, map_kind="gam"),
    "A5": ArmDef("A5", "PINN, interaction GAM", "pinn", {"grid": ("cat", [3, 5, 10, 20, 30]), "l2": ("cat", [1e-5, 1e-4, 1e-3, 1e-2, 1e-1]), "lam_res": ("cat", LAM),
                                                       "placement": ("cat", PLACE), "igrid": ("cat", [3, 5])}, map_kind="igam"),
    "A6": ArmDef("A6", "PINN, degree-2 log-polynomial (DROPPED by the prereg; optional, no numbers reported)", "pinn", {"l2": ("cat", [1e-5, 1e-4, 1e-3, 1e-2, 1e-1]), "lam_res": ("cat", LAM),
                                                                                                       "placement": ("cat", PLACE)}, map_kind="poly"),
    "A7": ArmDef("A7", "PINN, MLP stress map (PiDDM-style)", "pinn", {"width": ("cat", [4, 8, 16, 32]), "depth": ("cat", [1, 2, 3]), "l2": ("cat", DECADES), "lam_res": ("cat", LAM),
                                                                    "placement": ("cat", PLACE)}, map_kind="mlp"),
    "A8": ArmDef("A8", "free G (synthetic H7 only)", "free", {"width": ("cat", [16, 32, 64]), "wd": ("cat", DECADES)}),
    "A9": ArmDef("A9", "data-only F (lambda = 0)", "data", {"width": ("cat", [16, 32, 64, 128]), "depth": ("cat", [2, 3, 4]), "wd": ("cat", DECADES), "zdim": ("cat", [1, 2, 3])}),
    "A10": ArmDef("A10", "Stroebl semi-empirical (PROVISIONAL form)", "semi", tuned=False),
    "A11": ArmDef("A11", "GP-ARD", "p3", {"nu": ("cat", [1.5, 2.5, -1.0]), "noise_lo": ("logu", 1e-6, 1e-2), "fs": ("cat", ["full", "min"])}),
    "A12": ArmDef("A12", "LightGBM", "p3", {"n_est": ("int", 50, 600), "lr": ("logu", 0.01, 0.3), "leaves": ("int", 4, 32), "mcs": ("int", 5, 60), "l2": ("logu", 1e-3, 10.0)}),
    "A13": ArmDef("A13", "PINN-KAN, cycling cells only", "pinn", {"h": ("cat", [2, 3, 4, 6, 8]), "grid": ("cat", [2, 3, 5, 8, 12]), "l2": ("cat", DECADES),
                                                              "sparsity": ("cat", [0.0, 1e-4, 1e-3, 1e-2]), "lam_res": ("cat", LAM), "placement": ("cat", PLACE)}, map_kind="kan"),
    "A14": ArmDef("A14", "PINN-KAN, storage cells only (exploratory)", "pinn", {"grid_cal": ("cat", [2, 3, 5, 8, 12]), "l2": ("cat", DECADES), "lam_res": ("cat", LAM), "placement": ("cat", PLACE)}, map_kind="kan"),
    "R1": ArmDef("R1", "persistence", "ref", tuned=False),
    "R2": ArmDef("R2", "window-linear extrapolation", "ref", tuned=False),
}
NEURAL = ("A1", "A2", "A3", "A4", "A5", "A7", "A9", "A13", "A14")
H1B_POOL = ("A3", "A4", "A5", "A7")


def suggest_hp(trial, space):
    hp = {}
    for name, sp in space.items():
        if sp[0] == "cat":
            hp[name] = trial.suggest_categorical(name, sp[1])
        elif sp[0] == "logu":
            hp[name] = trial.suggest_float(name, sp[1], sp[2], log=True)
        elif sp[0] == "int":
            hp[name] = trial.suggest_int(name, sp[1], sp[2])
        else:
            raise ValueError(sp)
    return hp


def default_hp(arm_id):
    """first value of every categorical / geometric middle: a valid configuration for smoke tests and the tournament"""
    d = {}
    for name, sp in ARMS[arm_id].space.items():
        d[name] = sp[1][len(sp[1]) // 2] if sp[0] == "cat" else (float(np.sqrt(sp[1] * sp[2])) if sp[0] == "logu" else int((sp[1] + sp[2]) // 2))
    return d


class Arm:
    def __init__(self, arm_id, spec, hp, seed, ctx):
        self.arm_id, self.spec, self.hp, self.seed, self.ctx = arm_id, spec, dict(hp), int(seed), dict(ctx)
        self.n_params = 0
        self.n_train_used = None      # training cells this arm actually used (differs from the others for A11/A12, review m6)

    def steps(self, key):
        return max(int(BASE_STEPS[key] * float(self.ctx.get("steps_scale", 1.0))), 5)


class DiagMixin:
    def diagnostics(self):
        """D013 C7: fraction of clipped steps and sd of the fitted per-cell offsets (law-based arms) against TAU"""
        m = self.model
        d = {"clip_fraction": float(getattr(m, "clip_fraction", float("nan")))}
        if hasattr(m, "delta"):
            sd = float(m.delta.detach().std())
            d.update(delta_sd=sd, tau=TAU, delta_sd_over_tau=sd / TAU, delta_sd_flag_outside_0p5_2=bool(not 0.5 <= sd / TAU <= 2.0))
        return d


class PINNArm(DiagMixin, Arm):
    def fit(self, train_cells):
        a = ARMS[self.arm_id]
        cells = train_cells
        if self.arm_id == "A13":
            cells = [c for c in train_cells if c.kind == "cycling"]
        if self.arm_id == "A14":
            cells = [c for c in train_cells if c.kind == "storage"]
        hp = dict(self.hp, map=a.map_kind)
        if self.arm_id == "A14":
            hp["grid_cal"] = hp.get("grid_cal", 5)
        if self.arm_id == "A7":
            hp["map"] = "mlp"
        b = batch_from_cells(self.spec, cells)
        pk = {k: v for k, v in (self.ctx.get("pinn") or {}).items() if k in ("clip", "warmup", "lr")}     # configurable (D013): clip / warm-up / lr
        self.n_train_used = len(cells)
        self.model = fit_pinn(b, self.spec, hp, self.ctx["backbone"], self.seed, steps=self.steps("pinn"), extra_twin_raw=self.ctx.get("extra_twin_raw"), **pk)
        self.n_params = sum(p.numel() for p in self.model.parameters()) - self.model.z.numel() - self.model.delta.numel()
        return self

    def predict(self, wcells):
        preds, _ = predict_pinn(self.model, self.spec, wcells, float(self.hp.get("lam_res", 1.0)), self.seed)
        return preds


class HardArm(DiagMixin, Arm):
    def fit(self, train_cells):
        hp = dict(self.hp, map="kan")
        self.n_train_used = len(train_cells)
        pk = {k: v for k, v in (self.ctx.get("pinn") or {}).items() if k == "clip"}
        self.model = fit_hard(batch_from_cells(self.spec, train_cells), self.spec, hp, self.ctx["backbone"], self.seed, steps=self.steps("hard"), **pk)
        self.n_params = sum(p.numel() for p in self.model.law.parameters())
        return self

    def predict(self, wcells):
        return predict_hard(self.model, self.spec, wcells)[0]


class DataOnlyArm(DiagMixin, Arm):
    def fit(self, train_cells):
        self.n_train_used = len(train_cells)
        pk = {k: v for k, v in (self.ctx.get("pinn") or {}).items() if k == "clip"}
        self.model = fit_data_only(batch_from_cells(self.spec, train_cells), self.spec, self.hp, self.seed, steps=self.steps("data"), **pk)
        self.n_params = sum(p.numel() for p in self.model.net.parameters())
        return self

    def predict(self, wcells):
        return predict_data_only(self.model, self.spec, wcells)


class FreeArm(Arm):
    def fit(self, train_cells):
        self.n_train_used = len(train_cells)
        self.model = free.fit_free(batch_from_cells(self.spec, train_cells), self.spec, self.hp, self.seed, steps=self.steps("free"))
        self.n_params = sum(p.numel() for p in self.model.net.parameters()) + 1
        return self

    def predict(self, wcells):
        return free.predict_free(self.model, self.spec, wcells)


class SemiArm(Arm):
    def fit(self, train_cells):
        self.form = semi.SemiForm(self.spec)
        self.n_train_used = len([c for c in train_cells if c.n > 1 and (self.form.has_cal or c.kind == "cycling")])
        self.theta, self.cost = semi.fit_semi(self.form, train_cells, n_starts=int(self.ctx.get("a10_starts", 8)), seed=self.seed)
        self.n_params = self.form.n_params
        return self

    def predict(self, wcells):
        return semi.predict_semi(self.form, self.theta, wcells, per_cell_factor=bool(self.ctx.get("per_cell_factor", True)))


class P3Arm(Arm):
    def fit(self, train_cells):
        prep = prepare_many(train_cells, self.ctx["rule"])
        self.n_train_used = len(prep)          # cells without enough window / forecast points are dropped here only (documented, review m6)
        self.learner = baselines.P3Learner("gp" if self.arm_id == "A11" else "lgb", self.hp, self.spec.name, self.seed).fit(prep)
        return self

    def predict(self, wcells):
        return self.learner.predict(wcells)


class RefArm(Arm):
    def fit(self, train_cells):
        return self

    def predict(self, wcells):
        return baselines.persistence(wcells) if self.arm_id == "R1" else baselines.window_linear(wcells)


_CLS = {"free": FreeArm, "pinn": PINNArm, "hard": HardArm, "data": DataOnlyArm, "semi": SemiArm, "p3": P3Arm, "ref": RefArm}


def make_arm(arm_id, spec, hp, seed, ctx):
    return _CLS[ARMS[arm_id].family](arm_id, spec, hp, seed, ctx)
