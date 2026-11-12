"""Registry of the post-review exploratory jobs (D048). task = (exp, variant, fold, m). POST-HOC, EXPLORATORY."""
import contextlib

import harness as H

LAMS = [1e-2, 1e-1, 1.0, 10.0]


def lam_tag(x):
    return {1e-2: "1e-2", 1e-1: "1e-1", 1.0: "1", 10.0: "10"}[x]


def variants(exp):
    if exp == "item2_lambda":
        return ["L0"] + [f"Lfix{lam_tag(x)}" for x in LAMS] + ["Lbalance", "Lanneal"]
    if exp == "item3_zc":
        return [f"Z1_w{w}" for w in ("10", "100", "10000")] + [f"Z9_w{w}" for w in ("10", "100", "10000")]
    if exp == "item5_cap":
        return ["A15_cap3", "G15_cap3", "A15_untrunc"]
    if exp == "item6_h":
        import hgrid
        return hgrid.VARIANTS
    raise KeyError(exp)


def build(exp, variant, f, m):
    """-> kwargs for harness.run_job (without exp, variant, f, m) or None when the variant coincides with the reference of this fold (not rerun; stated in the summary)"""
    Hd = H.load_fold(f, m)
    tuned_lam = Hd["hp"]["A1"]["lam_res"]
    if exp == "item2_lambda":
        if variant == "L0":
            return dict(arm_name="A1", config={"lam_res": tuned_lam, "schedule": "frozen", "role": "reference rerun"}, diag=True,
                        make_fit=lambda spec, hp, sd, ctx: H.A1x(spec, hp["A1"], sd, ctx))
        if variant.startswith("Lfix"):
            L = {"1e-2": 1e-2, "1e-1": 1e-1, "1": 1.0, "10": 10.0}[variant[4:]]
            if L == tuned_lam:
                return None
            return dict(arm_name="A1", config={"lam_res": L, "schedule": "frozen", "other_hyperparameters": "as tuned"}, diag=True,
                        make_fit=lambda spec, hp, sd, ctx: H.A1x(spec, {**hp["A1"], "lam_res": L}, sd, ctx))
        if variant == "Lbalance":
            return dict(arm_name="A1", config={"schedule": "balance", "start_lam": tuned_lam, "update_every": 10, "ema": 0.1, "clamp": [1e-3, 1e2], "other_hyperparameters": "as tuned"}, diag=True,
                        make_fit=lambda spec, hp, sd, ctx: H.A1x(spec, hp["A1"], sd, ctx, schedule="balance"))
        if variant == "Lanneal":
            return dict(arm_name="A1", config={"schedule": "anneal", "lam": "log-linear 1e-3 -> 1 over all steps", "other_hyperparameters": "as tuned"}, diag=True,
                        make_fit=lambda spec, hp, sd, ctx: H.A1x(spec, hp["A1"], sd, ctx, schedule="anneal"))
    if exp == "item3_zc":
        w = float(variant.split("_w")[1])
        if variant.startswith("Z1_"):
            return dict(arm_name="A1", config={"z_prior_weight_train_and_inversion": w, "lam_res": tuned_lam, "other_hyperparameters": "as tuned"}, diag=True,
                        make_fit=lambda spec, hp, sd, ctx: H.A1x(spec, hp["A1"], sd, ctx, zw=w))
        if variant.startswith("Z9_"):
            return dict(arm_name="A9", config={"z_prior_weight_train_and_inversion": w, "other_hyperparameters": "as tuned"}, diag=False,
                        make_fit=lambda spec, hp, sd, ctx: H.A9x(spec, hp["A9"], sd, ctx, zw=w))
    if exp == "item5_cap":
        import extraction_variants as XV
        return XV.build(variant, f, m)
    if exp == "item6_h":
        import hgrid
        return hgrid.build(variant, f, m)
    raise KeyError((exp, variant))

