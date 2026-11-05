"""Nested, temperature-constrained training subsets of the grid (PREREG_v4 4.1; D016 judge 1.2).

Identifiers only: the coordinates come from the condition keys (Samsung, synthetic) or the design table (ISU); no label, no capacity and no
test information ever enters. The selector is deterministic and independent of the order in which the condition ids are passed.

max-min order over the fold's training cycling conditions (32 in Test B):
  * five stress coordinates (T, SOC_mid, DoD, C_ch, C_dch), standardised by their mean and SD over the fold's training conditions (SD 0 -> 1);
  * the order starts at the condition nearest the training centroid (the origin of the standardised space); ties by condition id;
  * every later condition maximises its minimum Euclidean distance to those already chosen; ties by condition id;
  * constraint: within the first CONSTRAINT_M = 8 picks every cycling temperature has at least MIN_PER_TEMP = 2 conditions (fewer when fewer exist):
    whenever the number of picks left within the first eight equals the total temperature deficit, the candidates are restricted to the deficient
    temperatures.
The subset at m is the first m conditions of the order, so the subsets are nested. m >= n_conditions is the unthinned training side (identity).

Random variant (downgrade row at g1): `random_order(ids, fold, j)` draws a seeded random permutation, SeedSequence([20261105, crc32("B|g1|randsubset|<fold>|<j>")]).
Nested as well (first m of the permutation). The temperature constraint is OFF by default (literal reading of the row; CHOICES.md).
"""
import hashlib
import json
import zlib

import numpy as np

MC_SEED_ROOT = 20261105      # = negcontrol.MC_SEED_ROOT (not imported: negcontrol imports data, data imports this module; a test pins the equality)
CONSTRAINT_M = 8
MIN_PER_TEMP = 2
GRID_M = (8, 16, 32)


class SubsetError(ValueError):
    pass


def parse_samsung_cond(key):
    """'T35|SOCmax0.55|DoD0.25|Cch0.5|Cdch1' -> (T, SOC_mid, DoD, C_ch, C_dch)"""
    p = str(key).split("|")
    if len(p) != 5 or not p[0].startswith("T") or not p[1].startswith("SOCmax") or not p[2].startswith("DoD"):
        raise SubsetError(f"not a cycling condition key: {key!r}")
    T, smax, dod = float(p[0][1:]), float(p[1][6:]), float(p[2][3:])
    return np.array([T, smax - dod / 2.0, dod, float(p[3][3:]), float(p[4][4:])])


def coords_samsung(ids):
    return np.stack([parse_samsung_cond(i) for i in ids]), 0          # (X, index of the temperature column)


def coords_isu(ids, cond_table):
    """ISU fallback: (charge_c, discharge_c, dod_pct) from the design table (identifiers/design only); no temperature constraint"""
    rows = []
    for i in ids:
        r = cond_table.loc[int(i)]
        rows.append([float(r["charge_c"]), float(r["discharge_c"]), float(r["dod_pct"])])
    return np.array(rows), None


def standardise(X):
    mu = X.mean(0)
    sd = X.std(0)
    sd = np.where(sd > 1e-12, sd, 1.0)
    return (X - mu) / sd


def maxmin_order(ids, X, temp_col=0, constraint_m=CONSTRAINT_M, min_per_temp=MIN_PER_TEMP):
    """-> list of ids in max-min order (see module docstring). `ids` and the rows of X correspond."""
    ids = [str(i) for i in ids]
    if len(set(ids)) != len(ids):
        raise SubsetError("duplicate condition ids")
    idx = sorted(range(len(ids)), key=lambda i: ids[i])               # canonical order: ids sorted -> independent of the caller's order
    ids = [ids[i] for i in idx]
    X = np.asarray(X, float)[idx]
    n = len(ids)
    Z = standardise(X)
    temps = None if temp_col is None else X[:, temp_col]
    need = {}
    if temps is not None:
        for T in sorted(set(temps.tolist())):
            need[T] = min(min_per_temp, int(np.sum(temps == T)))
    order = []
    first = int(np.argmin(np.linalg.norm(Z, axis=1)))                 # argmin returns the first minimum = smallest id on exact ties
    order.append(first)
    dmin = np.linalg.norm(Z - Z[first], axis=1)
    while len(order) < n:
        cand = [j for j in range(n) if j not in order]
        if temps is not None and len(order) < constraint_m:
            counts = {T: sum(1 for j in order if temps[j] == T) for T in need}
            deficit = sum(max(0, need[T] - counts[T]) for T in need)
            if deficit > 0 and constraint_m - len(order) <= deficit:
                cand = [j for j in cand if counts.get(temps[j], need.get(temps[j], 0)) < need.get(temps[j], 0)]
        best = max(dmin[j] for j in cand)
        pick = min(j for j in cand if dmin[j] >= best - 1e-12 * max(1.0, abs(best)))      # tie -> smallest id (ids are sorted)
        order.append(pick)
        dmin = np.minimum(dmin, np.linalg.norm(Z - Z[pick], axis=1))
    return [ids[j] for j in order]


def random_order(ids, fold, j):
    """seeded random nested order (downgrade row (iv)); SeedSequence([20261105, crc32('B|g1|randsubset|<fold>|<j>')]); no temperature constraint"""
    ids = sorted(str(i) for i in ids)
    rng = np.random.default_rng(np.random.SeedSequence([MC_SEED_ROOT, zlib.crc32(f"B|g1|randsubset|{int(fold)}|{int(j)}".encode())]))
    return [ids[i] for i in rng.permutation(len(ids))]


def subset_at(order, m):
    if m is None or m >= len(order):
        return list(order)
    if m < 1:
        raise SubsetError("m must be >= 1")
    return list(order[:m])


def order_for_ids(ids, dataset="samsung", cond_table=None):
    """max-min order of the training cycling conditions `ids` of one outer fold"""
    if dataset in ("samsung", "synthetic"):
        X, tc = coords_samsung(ids)
    elif dataset == "isu":
        X, tc = coords_isu(ids, cond_table)
    else:
        raise SubsetError(f"no subset selector for dataset {dataset!r}")
    return maxmin_order(ids, X, tc)


def thin_cells(cells, keep_conditions):
    """training cells with the cycling cells of dropped conditions removed; storage cells (and the order of the rest) untouched"""
    keep = set(keep_conditions)
    return [c for c in cells if c.kind != "cycling" or c.cond in keep]


def subsets_record(per_fold_ids, ms=GRID_M, dataset="samsung", cond_table=None, lab_of=None):
    """subsets.json content: per outer fold the order and the nested subsets, composition by temperature; hash over the ids"""
    rec = {"rule": __doc__.strip().split("\n")[0], "ms": list(ms), "constraint_m": CONSTRAINT_M, "min_per_temp": MIN_PER_TEMP, "folds": {}}
    for f in sorted(per_fold_ids, key=lambda x: int(x)):
        ids = per_fold_ids[f]
        order = order_for_ids(ids, dataset, cond_table)
        ent = {"order": order, "subsets": {str(m): subset_at(order, m) for m in ms}}
        if dataset in ("samsung", "synthetic"):
            ent["temperature_counts"] = {str(m): {str(int(T)): int(sum(1 for c in ent["subsets"][str(m)] if parse_samsung_cond(c)[0] == T))
                                                  for T in sorted({parse_samsung_cond(c)[0] for c in ids})} for m in ms}
        if lab_of:
            ent["lab_counts"] = {str(m): {lab: int(sum(1 for c in ent["subsets"][str(m)] if lab_of.get(c) == lab)) for lab in sorted(set(lab_of.values()))} for m in ms}
        rec["folds"][str(f)] = ent
    rec["sha256"] = hashlib.sha256(json.dumps(rec["folds"], sort_keys=True).encode()).hexdigest()
    return rec
