import os, sys
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
ROOT = r"C:\Users\Shlok\Downloads\PINN KAN battery paper"
sys.path.insert(0, ROOT + r"\code")
import numpy as np, collections
from pinnkan.data import load_split
for f in range(5):
    try:
        D = load_split("snl", "B", f, role="train")
    except Exception as e:
        print(f, "ERR", str(e)[:80]); break
    conds = {c.cond: c.raw for c in D.train}
    X = np.array(list(conds.values()))
    print("fold", f, "cells", len(D.train), "cond", len(conds), "n distinct [LFP,NCA,NMC,T,DoD,ch,dch]", [len(np.unique(X[:, j])) for j in range(7)],
          "ch", sorted(set(X[:,5])), "dod", sorted(set(X[:,4])), "dch", sorted(set(X[:,6])))
