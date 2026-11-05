"""Extract the capacity-relevant members of the full Samsung 50E release into their own directory (data only).

Run (from ROOT):  .venv/Scripts/python.exe -I code/data/samsung_extract.py [--zips DIR] [--out DIR] [--lists DIR] [--manifest CSV]

Inputs:   data/raw/samsung50e_full/<serial>__f<figshare file id>.zip   (279 zips, two per serial name except 3)
Outputs:  data/raw/samsung50e_full_x/<serial>__f<id>/<member>           folder key = zip stem (stage-aware, as in the fetcher)
          runs/samsung_pipeline_full/member_lists/<serial>__f<id>.txt   one line per zip member: name, size, crc32
          runs/samsung_pipeline_full/extract_manifest.csv               one row per extracted file (size, sha256)

What is extracted (everything else, the ET_T10/T45 and AT_T10/T45 and the ZYK segment csv files, stays in the zip and is
streamed by code/data/samsung_full_audit.py):  every *_meta.txt, and the csv of the kinds the pipeline reads:
CU, exCU, ET_T23, AT_T23. A zip is third-party data: nothing in it is executed, a member name is only used after it
matches the dataset's file-name pattern and contains no path separator or parent reference; the inner folder is dropped
(files are flattened into the folder named after the zip). Existing files of the right size are skipped (resumable).
Only the standard library is used. No capacity value is read or printed here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ZIP_RE = re.compile(r"^(?P<serial>TP_[kz]\d{2}_\d{2})__f(?P<fid>\d+)\.zip$")
MEMBER_RE = re.compile(r"^(?P<serial>TP_[kz]\d{2}_\d{2})_(?P<idx>\d{2})_(?P<kind>ET|CU|exCU|AT|ZYK)(?:_T(?P<temp>\d+))?"
                       r"(?P<meta>_meta\.txt)?(?P<csv>\.csv)?$")
KEEP_CSV = {("CU", None), ("exCU", None), ("ET", "23"), ("AT", "23")}
CHUNK = 1 << 20


def wanted(m: re.Match) -> bool:
    if m.group("meta"):
        return True
    return bool(m.group("csv")) and (m.group("kind"), m.group("temp")) in KEEP_CSV


def safe_member(name: str) -> tuple[str, str] | None:
    """(inner folder, base name) of a zip member, or None for a directory entry / unsafe name."""
    if name.endswith("/"):
        return None
    if name.startswith("/") or "\\" in name or ":" in name or ".." in name.split("/"):
        raise ValueError(f"unsafe member name {name!r}")
    parts = name.split("/")
    return ("/".join(parts[:-1]), parts[-1])


def extract_zip(zpath: Path, out_root: Path, lists_dir: Path) -> tuple[list[dict], list[dict]]:
    """-> (manifest rows of extracted files, problem rows)"""
    zm = ZIP_RE.match(zpath.name)
    folder = zpath.stem
    rows, problems = [], []
    dest = out_root / folder
    dest.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    list_lines = ["member\tsize\tcrc32"]
    with zipfile.ZipFile(zpath) as z:
        for info in z.infolist():
            try:
                sm = safe_member(info.filename)
            except ValueError as e:
                problems.append({"folder": folder, "member": info.filename, "problem": str(e)})
                continue
            if sm is None:
                continue
            inner, base = sm
            list_lines.append(f"{info.filename}\t{info.file_size}\t{info.CRC:08x}")
            m = MEMBER_RE.match(base)
            if not m:
                problems.append({"folder": folder, "member": info.filename, "problem": "name_not_matching_pattern"})
                continue
            if m.group("serial") != zm.group("serial") or (inner and inner != zm.group("serial")):
                problems.append({"folder": folder, "member": info.filename, "problem": "member_serial_differs_from_zip"})
                continue                      # a foreign member is listed, not extracted
            if base in seen:
                problems.append({"folder": folder, "member": info.filename, "problem": "duplicate_base_name"})
                continue
            seen.add(base)
            if not wanted(m):
                continue
            target = dest / base
            if target.exists() and target.stat().st_size == info.file_size:
                h = hashlib.sha256()
                with open(target, "rb") as f:
                    for blk in iter(lambda: f.read(CHUNK), b""):
                        h.update(blk)
                rows.append({"folder": folder, "member": base, "size": info.file_size, "crc32": f"{info.CRC:08x}", "sha256": h.hexdigest(), "action": "kept"})
                continue
            tmp = dest / (base + ".part")
            h = hashlib.sha256()
            with z.open(info) as src, open(tmp, "wb") as out:   # zipfile verifies the CRC at the end of the member
                for blk in iter(lambda: src.read(CHUNK), b""):
                    h.update(blk)
                    out.write(blk)
            os.replace(tmp, target)
            rows.append({"folder": folder, "member": base, "size": info.file_size, "crc32": f"{info.CRC:08x}", "sha256": h.hexdigest(), "action": "extracted"})
    lists_dir.mkdir(parents=True, exist_ok=True)
    (lists_dir / f"{folder}.txt").write_text("\n".join(list_lines) + "\n", encoding="utf-8")
    return rows, problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zips", default=str(ROOT / "data" / "raw" / "samsung50e_full"))
    ap.add_argument("--out", default=str(ROOT / "data" / "raw" / "samsung50e_full_x"))
    ap.add_argument("--lists", default=str(ROOT / "runs" / "samsung_pipeline_full" / "member_lists"))
    ap.add_argument("--manifest", default=str(ROOT / "runs" / "samsung_pipeline_full" / "extract_manifest.csv"))
    ap.add_argument("--only", default="", help="comma-separated zip stems (testing)")
    a = ap.parse_args(argv)
    zdir, out, lists = Path(a.zips), Path(a.out), Path(a.lists)
    only = {s for s in a.only.split(",") if s}
    zips = sorted(p for p in zdir.iterdir() if ZIP_RE.match(p.name) and (not only or p.stem in only))
    out.mkdir(parents=True, exist_ok=True)
    all_rows, all_problems = [], []
    for k, zp in enumerate(zips, 1):
        r, p = extract_zip(zp, out, lists)
        all_rows += r
        all_problems += p
        print(f"[{k}/{len(zips)}] {zp.name}: {sum(x['action'] == 'extracted' for x in r)} extracted, {sum(x['action'] == 'kept' for x in r)} kept, {len(p)} problems", flush=True)
    man = Path(a.manifest)
    man.parent.mkdir(parents=True, exist_ok=True)
    with open(man, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["folder", "member", "size", "crc32", "sha256", "action"])
        w.writeheader()
        w.writerows(all_rows)
    with open(man.with_name("extract_problems.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["folder", "member", "problem"])
        w.writeheader()
        w.writerows(all_problems)
    print(f"zips {len(zips)}, files {len(all_rows)}, bytes {sum(x['size'] for x in all_rows)}, problems {len(all_problems)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
