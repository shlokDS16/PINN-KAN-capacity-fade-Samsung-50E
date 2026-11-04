"""v2 outer splits (pre-freeze) for Samsung INR21700-50E (preregistration draft, not frozen).

Reads ONLY data/raw/samsung50e_meta/experiments_meta.csv (identifiers and designed stress values; no capacity
value exists in that file). Writes runs/prereg/samsung_splits_v2.json. Same dealing routine as
code/pilots/p3_make_splits.py (fewest-so-far fold, random ties), copied so that this file has no import side effects.

Test B  : 40 cycling conditions, 5 folds, temperature strata (23, 35, 45 C), stress-space neighbourhoods dealt to
          different folds; the 5 conditions with more than 3 replicate cells (centre points) dealt first, one per fold.
Test C  : all 35 C cycling conditions held out (single split).
Test A  : held-out replicate cells of cycling conditions, 3 folds.
S2      : 19 storage conditions, 5 folds, blocks of consecutive storage SOC inside each temperature.
Usage: python -P make_samsung_splits.py <ROOT>
"""
import csv, json, hashlib, sys
import numpy as np
from sklearn.cluster import KMeans

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
SEED_B, SEED_A, SEED_S2 = 20261107, 20261108, 20261109      # DRAFT values (dates), fixed at freeze
NB, NA, NS = 5, 3, 5


def digest(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True).encode()).hexdigest()


def deal_into(blocks, rng, nfold, count, out):
    for blk in blocks:
        blk = list(blk)
        rng.shuffle(blk)
        used = set()
        for cid in blk:
            if len(used) == nfold:
                used = set()
            cand = [f for f in range(nfold) if f not in used]
            m = min(count[f] for f in cand)
            cand = [f for f in cand if count[f] == m]
            f = int(rng.choice(cand))
            out[cid] = f
            used.add(f)
            count[f] += 1


def cell_id(r):
    """Zip names (serial) repeat between stage 1 and stage 2 (138 of 141 names occur twice on figshare), so a cell is
    identified by <serial>_s<stage> (v2 key, same as runs/samsung_pipeline/folder_mapping.csv); the mapping of the two same-name files to the stages is a data-step rule (prereg 3.2)."""
    return "%s_s%s" % (r["serial"].strip(), r["stage"].strip())


def cond_id(r, kind):
    if kind == "z":
        return "T%g|SOCmax%g|DoD%g|Cch%g|Cdch%g" % tuple(float(r[c]) for c in
                ["amb_temp_tp", "soc_max_tp", "dod_tp", "c_ch_tp", "c_dch_tp"])
    return "T%g|SOC%g" % (float(r["amb_temp_tp"]), float(r["soc_max_tp"]))


def main():
    rows = [{k.strip(): v for k, v in r.items()}
            for r in csv.DictReader(open(f"{ROOT}/data/raw/samsung50e_meta/experiments_meta.csv"))]
    z = [r for r in rows if r["type"] == "z"]
    k = [r for r in rows if r["type"] == "k"]
    zc, zcells, zx = {}, {}, {}
    for r in z:
        c = cond_id(r, "z")
        zc.setdefault(c, []).append(cell_id(r))
        zx[c] = [float(r[a]) for a in ["amb_temp_tp", "soc_max_tp", "dod_tp", "c_ch_tp", "c_dch_tp"]]
        zcells[cell_id(r)] = c
    kc, kcells, kx = {}, {}, {}
    for r in k:
        c = cond_id(r, "k")
        kc.setdefault(c, []).append(cell_id(r))
        kx[c] = [float(r["amb_temp_tp"]), float(r["soc_max_tp"])]
        kcells[cell_id(r)] = c
    # ------------------------------------------------------------------ Test B
    rng = np.random.default_rng(SEED_B)
    count = np.zeros(NB, int)
    fold_of = {}
    centre = sorted(c for c in zc if len(zc[c]) > 3)
    deal_into([centre], rng, NB, count, fold_of)                     # one per fold (5 centre points, 5 folds)
    for T in (23.0, 35.0, 45.0):
        ids = sorted(c for c in zc if zx[c][0] == T and c not in fold_of)
        X = np.array([zx[c][1:] for c in ids], float)
        Z = (X - X.mean(0)) / X.std(0)
        ncl = int(np.ceil(len(ids) / NB))
        lab = KMeans(n_clusters=ncl, n_init=10, random_state=SEED_B).fit(Z).labels_
        blocks = [[ids[i] for i in range(len(ids)) if lab[i] == j] for j in range(ncl)]
        deal_into(blocks, rng, NB, count, fold_of)
    B = {"dataset": "Samsung INR21700-50E", "test": "B", "seed": SEED_B, "n_folds": NB, "status": "v2 (pre-freeze)",
         "unit": "cycling condition = (T, SOC_max, DoD, C_ch, C_dch); 40 conditions", "folds": {}}
    for f in range(NB):
        tc = sorted(c for c, ff in fold_of.items() if ff == f)
        B["folds"][str(f)] = {"test_conditions": tc, "test_cells": sorted(s for c in tc for s in zc[c]),
                              "train_cycling_conditions": sorted(set(zc) - set(tc)),
                              "storage": "all 132 storage cells in training (cells without check-ups enter only per the inclusion rule)"}
    # ------------------------------------------------------------------ Test C
    tc = sorted(c for c in zc if zx[c][0] == 35.0)
    C = {"dataset": "Samsung INR21700-50E", "test": "C", "n_folds": 1, "status": "v2 (pre-freeze)",
         "rule": "all cycling conditions at 35 C held out; train on 23 and 45 C cycling plus all storage (10/23/45 C)",
         "folds": {"0": {"test_conditions": tc, "test_cells": sorted(s for c in tc for s in zc[c]),
                         "train_cycling_conditions": sorted(set(zc) - set(tc))}}}
    # ------------------------------------------------------------------ Test A
    rngA = np.random.default_rng(SEED_A)
    fa = {}
    for c in sorted(zc):
        cells = sorted(zc[c])
        perm = list(rngA.permutation(len(cells)))
        off = int(rngA.integers(NA))
        for j, i in enumerate(perm):
            fa[cells[i]] = (j + off) % NA
    A = {"dataset": "Samsung INR21700-50E", "test": "A", "seed": SEED_A, "n_folds": NA, "status": "v2 (pre-freeze)",
         "unit": "replicate cell of a seen cycling condition (every condition keeps >= 2 cells in training per fold)",
         "folds": {str(f): {"test_cells": sorted(s for s, ff in fa.items() if ff == f)} for f in range(NA)}}
    # ------------------------------------------------------------------ S2 storage
    rngS = np.random.default_rng(SEED_S2)
    cnt = np.zeros(NS, int)
    fs = {}
    blocks = []
    for T in (10.0, 23.0, 45.0):
        ids = sorted((c for c in kc if kx[c][0] == T), key=lambda c: kx[c][1])
        blocks += [ids[i:i + NS] for i in range(0, len(ids), NS)]
    deal_into(blocks, rngS, NS, cnt, fs)
    S = {"dataset": "Samsung INR21700-50E", "test": "S2", "seed": SEED_S2, "n_folds": NS, "status": "v2 (pre-freeze)",
         "unit": "storage condition = (T, storage SOC); 19 conditions; all cycling cells and the other storage conditions in training",
         "folds": {}}
    for f in range(NS):
        tc = sorted(c for c, ff in fs.items() if ff == f)
        S["folds"][str(f)] = {"test_conditions": tc, "test_cells": sorted(s for c in tc for s in kc[c]),
                              "scored_cells_rule": "cells 01-03 of the test point (cells 04-06 have only entry and final tests)"}
    S3 = {"test": "S3 (exploratory)", "rule": "all 23 C storage conditions held out, train on 10 and 45 C storage plus all cycling",
          "test_conditions": sorted(c for c in kc if kx[c][0] == 23.0)}
    out = {"B": B, "C": C, "A": A, "S2": S, "S3": S3}
    for name, o in out.items():
        if "folds" in o:
            o["sha256_of_folds"] = digest(o["folds"])
    json.dump(out, open(f"{ROOT}/runs/prereg/samsung_splits_v2.json", "w"), indent=1)
    # ---- report (identifiers only)
    for f in range(NB):
        tcs = B["folds"][str(f)]["test_conditions"]
        byT = {T: sum(1 for c in tcs if zx[c][0] == T) for T in (23.0, 35.0, 45.0)}
        print("B fold", f, len(tcs), byT, "cells", len(B["folds"][str(f)]["test_cells"]),
              "centre points", sum(1 for c in tcs if c in centre))
    print("C", len(tc := C["folds"]["0"]["test_conditions"]), "conditions", len(C["folds"]["0"]["test_cells"]), "cells")
    print("A fold sizes", {f: len(v["test_cells"]) for f, v in A["folds"].items()})
    print("S2", {f: (len(v["test_conditions"]), len(v["test_cells"])) for f, v in S["folds"].items()})
    for name, o in out.items():
        if "sha256_of_folds" in o:
            print(name, o["sha256_of_folds"][:12])


if __name__ == "__main__":
    main()
