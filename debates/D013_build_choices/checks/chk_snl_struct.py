import os, sys
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
ROOT = r"C:\Users\Shlok\Downloads\PINN KAN battery paper"
sys.path.insert(0, ROOT + r"\code")
import numpy as np, collections
from pinnkan.data import load_split
for ds in ("snl", "isu"):
    D = load_split(ds, "B", 0, role="train")
    cells = D.train
    conds = {}
    for c in cells: conds[c.cond] = c.raw
    X = np.array(list(conds.values()))
    print(ds, "cells", len(cells), "conditions", len(conds))
    print(" unique per column", [len(np.unique(X[:, j])) for j in range(X.shape[1])])
    if ds == "snl":
        chem = [tuple(r[:3]) for r in X]
        print(" chem counts", collections.Counter(chem))
        for ch in set(chem):
            sub = X[[i for i, c in enumerate(chem) if c == ch]]
            print(" ", ch, "T", sorted(set(sub[:, 3])), "DoD", sorted(set(sub[:, 4])), "ch", sorted(set(sub[:, 5])), "dch", sorted(set(sub[:, 6])))
