"""Overnight fetch of Samsung 50E check-up (CU) members for all 279 cells, by HTTP range requests.

Order: one replicate of every cycling condition, then one of every storage condition, then all other
cells (download order only; the analysis uses every cell). Per cell: list members once (cached), then
fetch every *_CU.csv and *_CU_meta.txt plus the first *_ET_*_meta.txt (start date). Skips files that
exist, so it resumes after any drop or restart. Stops on data/STOP_SAMSUNG; pauses 00:05-00:30.
Status: data/SAMSUNG_CU_STATUS.md; log: data/logs/samsung_cu.log.
"""
import csv, datetime as dt, io, os, sys, time, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))  # our own folder only
from zip_range_fetch import HttpRangeFile  # noqa: E402

DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "raw", "samsung50e_members")
LISTS = os.path.join(ROOT, "runs", "pilot_P0", "member_lists")
LOG = os.path.join(DATA, "logs", "samsung_cu.log")
STATUS = os.path.join(DATA, "SAMSUNG_CU_STATUS.md")
STOP = os.path.join(DATA, "STOP_SAMSUNG")


def log(msg):
    with open(LOG, "a", encoding="utf8") as f:
        f.write(f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}\n")


def order():
    meta = list(csv.DictReader(open(os.path.join(DATA, "raw", "samsung50e_meta", "experiments_meta.csv"), encoding="utf8")))
    urls = {r["file"].rsplit(".", 1)[0]: r["url"] for r in
            csv.DictReader(open(os.path.join(DATA, "DEFERRED_URLS.tsv"), encoding="utf8"), delimiter="\t")
            if r["dataset"].startswith("samsung")}
    key = lambda m: (m["amb_temp_tp"], m["soc_max_tp"], m["dod_tp"], m["c_ch_tp"], m["c_dch_tp"])
    first, rest, seen = [], [], set()
    for ty in ("z", "k"):
        for m in sorted((m for m in meta if m["type"] == ty), key=lambda m: m["serial"]):
            (rest if (ty, key(m)) in seen else first).append(m["serial"])
            seen.add((ty, key(m)))
    return [(s, urls[s]) for s in first + rest if s in urls]


def wanted(names):
    et = sorted(n for n in names if "_ET_" in n and n.endswith("_meta.txt"))[:1]
    return [n for n in names if n.endswith("_CU.csv") or n.endswith("_CU_meta.txt")] + et


def do_cell(serial, url):
    os.makedirs(LISTS, exist_ok=True)
    lst = os.path.join(LISTS, f"{serial}.txt")
    zf = None
    if os.path.exists(lst):
        names = open(lst, encoding="utf8").read().split()
    else:
        zf = zipfile.ZipFile(io.BufferedReader(HttpRangeFile(url), buffer_size=1 << 16))
        names = [i.filename for i in zf.infolist() if not i.filename.endswith("/")]
        open(lst, "w", encoding="utf8").write("\n".join(names))
    todo = [n for n in wanted(names) if not os.path.exists(os.path.join(OUT, serial, os.path.basename(n)))]
    if not todo:
        return True
    zf = zf or zipfile.ZipFile(io.BufferedReader(HttpRangeFile(url), buffer_size=1 << 16))
    os.makedirs(os.path.join(OUT, serial), exist_ok=True)
    for n in todo:
        if os.path.exists(STOP):
            return False
        while dt.time(0, 5) <= dt.datetime.now().time() <= dt.time(0, 30):
            time.sleep(60)
        dst = os.path.join(OUT, serial, os.path.basename(n))
        with zf.open(n) as src, open(dst + ".part", "wb") as out:
            while chunk := src.read(1 << 16):
                out.write(chunk)
        os.replace(dst + ".part", dst)
    log(f"done {serial} ({len(todo)} files)")
    return True


def status(cells, done):
    lines = [f"# Samsung 50E check-up fetch ({dt.datetime.now():%Y-%m-%d %H:%M})", "",
             f"Cells complete: {len(done)} of {len(cells)}. Stop: create data/STOP_SAMSUNG.", ""]
    try:
        open(STATUS, "w", encoding="utf8").write("\n".join(lines + sorted(done)) + "\n")
    except OSError:
        pass


def main():
    cells, done = order(), set()
    log(f"start: {len(cells)} cells")
    while len(done) < len(cells) and not os.path.exists(STOP):
        for serial, url in cells:
            if serial in done or os.path.exists(STOP):
                continue
            try:
                if do_cell(serial, url):
                    done.add(serial)
            except Exception as e:
                log(f"error {serial}: {type(e).__name__}: {e}")
                time.sleep(60)
            status(cells, done)
    log("finished" if len(done) == len(cells) else "stopped")


if __name__ == "__main__":
    main()
