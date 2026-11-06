"""Writes runs/prereg/blinding_exclusions.json (PREREG_v4 3.3(11), pin 2b, C13): the kind (b) pre-freeze exposures of BLINDING_LOG.md that are outer-test cells of a confirmatory test
(B, C, S2). Identifiers only: the split file and the design table (cell identifiers and design parameters); no capacity or retention value is read.
    .venv/Scripts/python.exe -P code/prereg/make_blinding_exclusions.py [--splits runs/prereg/samsung_splits_v2.json] [--out runs/prereg/blinding_exclusions.json]
Also copies runs/prereg/samsung_splits_v2.json to runs/splits/samsung_splits_v2.json byte for byte with --copy-splits (C13) and prints both sha256."""
import argparse
import json
import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))

from pinnkan import blinding  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--splits", default=os.path.join(ROOT, "runs", "prereg", "samsung_splits_v2.json"))
    ap.add_argument("--cells", default=os.path.join(ROOT, blinding.CELLS_REL))
    ap.add_argument("--out", default=os.path.join(ROOT, blinding.EXCLUSIONS_REL))
    ap.add_argument("--copy-splits", action="store_true", help="copy the split file to runs/splits/ (byte-identical) and print both hashes")
    a = ap.parse_args(argv)
    rec = blinding.build_record(a.splits, a.cells)
    with open(a.out, "w", encoding="utf8") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True)
    print(a.out, rec["sha256"])
    if a.copy_splits:
        dst = os.path.join(ROOT, "runs", "splits", "samsung_splits_v2.json")
        shutil.copyfile(a.splits, dst)
        h1, h2 = blinding.sha256_file(a.splits), blinding.sha256_file(dst)
        assert h1 == h2, "the copy is not byte-identical"
        print("splits sha256", h1, h2)


if __name__ == "__main__":
    main()
