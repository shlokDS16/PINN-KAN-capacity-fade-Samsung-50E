"""Item 5 (D048): extraction cap 3 (the full frozen library) and the untruncated ceiling for A15 / G15. POST-HOC, EXPLORATORY. No code edit: the cap is a config value read by
arms.SymbolicArm (ctx['symbolic']['cap']), the untruncated extraction is a run-time rebinding of symbolic.extract_law with untruncated=True (documented in symbolic.py:20)."""
import contextlib

import harness as H
from pinnkan import symbolic

SPEC = {"A15_cap3": ("A15", 3, False), "G15_cap3": ("G15", 3, False), "A15_untrunc": ("A15", 3, True)}


@contextlib.contextmanager
def untruncated_extraction():
    orig = symbolic.extract_law

    def patched(law, spec, s_cyc_train, s_cal_train, cap=None, untruncated=False):
        return orig(law, spec, s_cyc_train, s_cal_train, cap, True)
    symbolic.extract_law = patched
    try:
        yield
    finally:
        symbolic.extract_law = orig


def family_counts(report):
    cnt = {}
    for part in ("cyclic", "calendar"):
        blk = report.get(part)
        if not blk:
            continue
        for lay in blk["layers"]:
            for row in lay["edges"]:
                for e in row:
                    cnt[e["family"]] = cnt.get(e["family"], 0) + 1
    return cnt


class SymWrap:
    def __init__(self, arm_id, spec, hp, seed, ctx, cap):
        self.arm_id, self.spec, self.hp, self.seed, self.ctx, self.cap = arm_id, spec, hp, seed, ctx, cap

    def fit(self, train):
        c = dict(self.ctx, symbolic={"cap": self.cap})
        self.arm = H.make_arm(self.arm_id, self.spec, self.hp, self.seed, c).fit(train)
        self.model = self.arm.model
        return self

    def predict(self, wcells):
        # a refit that diverged leaves non-finite parameters and the frozen latent inversion raises LinAlgError; such a forecast is non-finite and is scored with the persistence error and counted
        # (PREREG_v4 6, metrics.clean_forecast); the wrapper returns NaN forecasts and records the event, the frozen code is not edited
        import numpy as np
        try:
            return self.arm.predict(wcells)
        except Exception as e:  # noqa: BLE001
            self.predict_failure = f"{type(e).__name__}"
            return {w.cell_id: np.full(len(w.t_fc), np.nan) for w in wcells}

    def extra_record(self):
        a = self.arm
        fc = family_counts(a.report)
        return {"n_coefs": int(a.n_coefs), "train_bic": float(a.train_bic), "refit_diverged": bool(a.refit_diverged), "parent_train_data_mse": float(a.parent_train_data_mse),
                "train_data_mse_after_refit": float(a.model.train_data_mse), "family_counts": fc, "n_quadratic_edges": int(fc.get("quadratic", 0)), "n_hinge_edges": int(fc.get("hinge", 0)),
                "input_family_labels": a.report["input_family_labels"], "cap": a.report["cap"], "untruncated": a.report["untruncated"], "predict_failure": getattr(self, "predict_failure", None)}


def build(variant, f, m):
    arm, cap, untr = SPEC[variant]
    return dict(arm_name=arm, config={"variant": variant, "cap": cap, "untruncated": untr, "other_hyperparameters": "as tuned at cap 2", "endpoint_files": "ensemble condition_scores.json; per-seed condition_scores_seed_k*.json"},
                diag=False, make_fit=lambda spec, hp, sd, ctx: SymWrap(arm, spec, hp[arm], sd, ctx, cap), cm=(untruncated_extraction if untr else None))

