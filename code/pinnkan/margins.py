"""margins.json inputs (PREREG_v2 9.2): E = comparator's training-side inner-CV condition-mean score per outer fold, pooled by test-condition
count; delta_S = 0.02 E, delta_N = 0.10 E (pp); log-scale margins ln(1.02) and -ln(1.10) need no E. Written after tuning ends and before any final
refit is applied to a test condition (the runner enforces the order)."""
import hashlib
import json

import numpy as np

LOG_MARGIN_S = float(np.log(1.02))
LOG_MARGIN_N = float(-np.log(1.10))


def pooled_E(per_fold):
    """per_fold: list of (n_test_conditions, E_fold) -> E pooled by test-condition count"""
    n = np.array([p[0] for p in per_fold], float)
    e = np.array([p[1] for p in per_fold], float)
    return float((n * e).sum() / n.sum())


def margin_record(per_fold):
    E = pooled_E(per_fold)
    return {"E_pp": E, "delta_S_pp": 0.02 * E, "delta_N_pp": 0.10 * E, "per_fold": [list(map(float, p)) for p in per_fold],
            "log_margin_S": LOG_MARGIN_S, "log_margin_N": LOG_MARGIN_N}


def write_margins(path, contrasts):
    """contrasts: {name: per_fold list} -> writes json with a content hash"""
    body = {k: margin_record(v) for k, v in sorted(contrasts.items())}
    h = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    with open(path, "w", encoding="utf8") as fh:
        json.dump({"contrasts": body, "sha256": h}, fh, indent=1)
    return h
