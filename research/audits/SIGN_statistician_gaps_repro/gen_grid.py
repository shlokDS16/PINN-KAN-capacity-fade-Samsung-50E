"""Statistician validation: build the synthetic grid of the coder's test (invented numbers) with the CURRENT tree's helpers; write paths to work/paths.json."""
import json, os, sys
ROOT = r"C:\Users\Shlok\Downloads\PINN KAN battery paper"
W = sys.argv[1]
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.join(ROOT, "code", "tests"))
import test_pk_stats_gaps_g1_g8 as T
os.makedirs(os.path.join(W, "g"))
dirs = T.make_grid(os.path.join(W, "g"))
fdir, sha = T._item_f(W, dirs)
neg = T.make_negative(W, dirs)
json.dump(dict(dirs=dirs, fdir=fdir, sha=sha, neg=neg), open(os.path.join(W, "paths.json"), "w"))
print("grid", len(dirs), "neg", len(neg))
