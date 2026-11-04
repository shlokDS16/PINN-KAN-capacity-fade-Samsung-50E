"""Outer splits for ISU-ILCC and SNL (Test A and Test B). Run once, BEFORE any model sees data.

Test B (primary): held-out CONDITIONS, 5 folds stratified over stress space.
  ISU: 63 conditions; stress = (charge C, discharge C, mean DoD), standardised; k-means with 13 clusters
       (seeded) forms stress-space neighbourhoods; inside each cluster the conditions are dealt to
       different folds (fold with the fewest conditions so far, ties broken at random).
  SNL: 23 conditions = (chemistry, temperature, SOC window, charge C, discharge C). Condition groups are the
       unique tuples in snl_cells.csv (1 to 4 replicate cells each). Neighbourhoods = consecutive blocks of
       5 conditions inside one chemistry sorted by (temperature, SOC window, discharge C); dealt like ISU.
Test A: held-out replicate CELLS, seen conditions. Within each condition the cells are permuted (seed) and
  dealt to folds 0..3; ISU keeps 3 of 4 replicates in training per fold. SNL conditions with a single cell
  have no Test A unit (cell stays in training in every fold).
Only cell/condition identifiers are read here (no capacity values).
"""
import json, hashlib, sys
import numpy as np, pandas as pd
from sklearn.cluster import KMeans

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
SEED_ISU, SEED_SNL = 20261104, 20261105
NFOLD_B, NFOLD_A = 5, 4


def deal(blocks, rng, nfold):
    """blocks: list of lists of condition ids (stress neighbourhoods). Returns dict id -> fold."""
    count = np.zeros(nfold, int)
    out = {}
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
    return out


def testA(cell_cond, rng, nfold=NFOLD_A):
    """cell_cond: dict cell -> condition id. Returns dict cell -> fold or -1 (never held out)."""
    out = {}
    byc = {}
    for cell, c in cell_cond.items():
        byc.setdefault(c, []).append(cell)
    for c in sorted(byc, key=str):
        cells = sorted(byc[c])
        if len(cells) < 2:
            out[cells[0]] = -1
            continue
        perm = list(rng.permutation(len(cells)))
        off = int(rng.integers(nfold))
        for j, k in enumerate(perm):
            out[cells[k]] = (j + off) % nfold
    return out


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def main():
    P = f"{ROOT}/data/processed"
    # ---------------- ISU
    cond = pd.read_csv(f"{P}/isu_conditions.csv")
    cap = pd.read_csv(f"{P}/isu_capacity.csv", usecols=["cell", "group"]).drop_duplicates()
    X = cond[["charge_c", "discharge_c", "dod_pct"]].values.astype(float)
    Z = (X - X.mean(0)) / X.std(0)
    km = KMeans(n_clusters=13, n_init=10, random_state=SEED_ISU).fit(Z)
    blocks = [[int(g) for g in cond.group.values[km.labels_ == k]] for k in range(13)]
    rng = np.random.default_rng(SEED_ISU)
    fold_of = deal(blocks, rng, NFOLD_B)
    B = {"dataset": "ISU-ILCC", "test": "B", "seed": SEED_ISU, "n_folds": NFOLD_B,
         "unit": "condition (group id in README Table A1)",
         "stratification": "k-means (13 clusters, standardised charge C, discharge C, DoD, random_state=seed); conditions of one cluster dealt to different folds",
         "folds": {str(f): {"test_conditions": sorted(g for g, ff in fold_of.items() if ff == f)} for f in range(NFOLD_B)}}
    for f in range(NFOLD_B):
        tc = set(B["folds"][str(f)]["test_conditions"])
        B["folds"][str(f)]["test_cells"] = sorted(cap.cell[cap.group.isin(tc)])
        B["folds"][str(f)]["train_conditions"] = sorted(set(cond.group) - tc)
    rngA = np.random.default_rng(SEED_ISU + 1)
    ccmap = dict(zip(cap.cell, cap.group))
    fa = testA(ccmap, rngA)
    A = {"dataset": "ISU-ILCC", "test": "A", "seed": SEED_ISU + 1, "n_folds": NFOLD_A,
         "unit": "replicate cell; each condition keeps >=3 of 4 (or 2 of 3) replicates in training per fold",
         "folds": {str(f): {"test_cells": sorted(c for c, ff in fa.items() if ff == f)} for f in range(NFOLD_A)}}
    # ---------------- SNL
    sc = pd.read_csv(f"{P}/snl_cells.csv")
    sc["cond"] = (sc.chemistry + "|" + sc.temp_c.astype(str) + "C|" + sc.soc_window + "|ch" + sc.charge_c.astype(str)
                  + "|dis" + sc.discharge_c.astype(str))
    cs = sc.drop_duplicates("cond")[["cond", "chemistry", "temp_c", "soc_window", "discharge_c"]]
    blocks = []
    for chem, d in cs.groupby("chemistry"):
        d = d.sort_values(["temp_c", "soc_window", "discharge_c"])
        ids = list(d.cond)
        blocks += [ids[i:i + NFOLD_B] for i in range(0, len(ids), NFOLD_B)]
    rng = np.random.default_rng(SEED_SNL)
    fold_of = deal(blocks, rng, NFOLD_B)
    nrep = sc.groupby("cond").size().to_dict()
    SB = {"dataset": "SNL", "test": "B", "seed": SEED_SNL, "n_folds": NFOLD_B,
          "unit": "condition = (chemistry, temperature, SOC window, charge C, discharge C); 23 conditions, 1-4 cells each; chemistries are pooled in the splits and every chemistry appears in several folds",
          "stratification": "blocks of 5 consecutive conditions inside one chemistry sorted by (temperature, SOC window, discharge C); conditions of a block dealt to different folds (fewest-so-far, random ties). Conditions are small in number (7-8 per chemistry), so folds hold 4-5 conditions.",
          "folds": {}}
    for f in range(NFOLD_B):
        tc = sorted(c for c, ff in fold_of.items() if ff == f)
        SB["folds"][str(f)] = {"test_conditions": tc, "test_cells": sorted(sc.cell[sc.cond.isin(tc)]),
                               "train_conditions": sorted(set(sc.cond) - set(tc))}
    fa = testA(dict(zip(sc.cell, sc.cond)), np.random.default_rng(SEED_SNL + 1))
    SA = {"dataset": "SNL", "test": "A", "seed": SEED_SNL + 1, "n_folds": NFOLD_A,
          "unit": "replicate cell; single-cell conditions (fold -1) are never held out", 
          "never_held_out_cells": sorted(c for c, ff in fa.items() if ff == -1),
          "folds": {str(f): {"test_cells": sorted(c for c, ff in fa.items() if ff == f)} for f in range(NFOLD_A)}}
    for name, obj in [("isu_testB", B), ("isu_testA", A), ("snl_testB", SB), ("snl_testA", SA)]:
        obj["sha256_of_folds"] = digest(obj["folds"])
        json.dump(obj, open(f"{ROOT}/runs/splits/{name}.json", "w"), indent=1)
        sizes = {f: len(v.get("test_conditions", v["test_cells"])) for f, v in obj["folds"].items()}
        print(name, sizes, obj["sha256_of_folds"][:12])


if __name__ == "__main__":
    main()
