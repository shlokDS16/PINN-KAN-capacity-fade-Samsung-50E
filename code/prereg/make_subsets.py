"""Writes runs/prereg/subsets.json: the nested max-min training subsets (m = 8, 16, 32) of every Test B outer fold (PREREG_v4 4.1, pin 2b).
Reads samsung_splits_v2.json (condition identifiers only). No label, no capacity.
    .venv/Scripts/python.exe -P code/prereg/make_subsets.py [--out runs/prereg/subsets.json]"""
import argparse
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))

from pinnkan import subsets  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--splits", default=os.path.join(ROOT, "runs", "prereg", "samsung_splits_v2.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "runs", "prereg", "subsets.json"))
    a = ap.parse_args(argv)
    sp = json.load(open(a.splits, encoding="utf8"))["B"]
    rec = subsets.subsets_record({f: v["train_cycling_conditions"] for f, v in sp["folds"].items()})
    rec["split_file"] = os.path.relpath(a.splits, ROOT).replace("\\", "/")
    rec["split_fold_hash"] = sp["sha256_of_folds"]
    with open(a.out, "w", encoding="utf8") as fh:
        json.dump(rec, fh, indent=1)
    print(a.out, rec["sha256"])


if __name__ == "__main__":
    main()
