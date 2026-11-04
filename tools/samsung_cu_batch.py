"""Overnight fetch of Samsung 50E check-up (CU) members for all 279 cells, by HTTP range requests.

Order: one replicate of every cycling condition, then one of every storage condition, then all other
cells (download order only; the analysis uses every cell). Per cell: list members once (cached), then
fetch every *_CU.csv and *_CU_meta.txt plus the first *_ET_*_meta.txt (start date). Skips files that
exist, so it resumes after any drop or restart. Stops on data/STOP_SAMSUNG; pauses 00:05-00:30.
Status: data/SAMSUNG_CU_STATUS.md; log: data/logs/samsung_cu.log.
"""
import csv, datetime as dt, io, os, struct, sys, time, zipfile, zlib
from concurrent.futures import ThreadPoolExecutor

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
    """Every per-cell zip (279: serial names repeat across the two stages, with different cells and
    conditions). Folder key = <serial>__f<figshare file id>. Download order: one replicate of each
    (type, stage, condition) first. Stage of a URL is assumed from upload order (lower file id =
    stage 1); this only affects download order, the pipeline assigns stages from the measured dates."""
    meta = list(csv.DictReader(open(os.path.join(DATA, "raw", "samsung50e_meta", "experiments_meta.csv"), encoding="utf8")))
    by_name = {}
    for r in csv.DictReader(open(os.path.join(DATA, "DEFERRED_URLS.tsv"), encoding="utf8"), delimiter="\t"):
        if r["dataset"].startswith("samsung") and r["file"].startswith("TP_"):
            by_name.setdefault(r["file"].rsplit(".", 1)[0], []).append(r["url"])
    fid = lambda u: int(u.rstrip("/").rsplit("/", 1)[1])
    for v in by_name.values():
        v.sort(key=fid)
    key = lambda m: (m["type"], m["stage"], m["amb_temp_tp"], m["soc_max_tp"], m["dod_tp"], m["c_ch_tp"], m["c_dch_tp"])
    first, rest, seen = [], [], set()
    for m in sorted(meta, key=lambda m: (m["type"] != "z", m["stage"], m["serial"])):
        urls = by_name.get(m["serial"], [])
        if not urls:
            continue
        u = urls[min(int(m["stage"]), len(urls)) - 1]
        item = (f"{m['serial']}__f{fid(u)}", u)
        (rest if key(m) in seen else first).append(item)
        seen.add(key(m))
    out, have = [], set()
    for item in first + rest:  # every URL exactly once, even if the stage guess pairs badly
        if item[1] not in have:
            out.append(item)
            have.add(item[1])
    for name, urls in by_name.items():
        for u in urls:
            if u not in have:
                out.append((f"{name}__f{fid(u)}", u))
                have.add(u)
    return out


def wanted(names, phase=1):
    """Phase 1: check-ups (CU) and their meta, plus one ET meta (start date), for every cell.
    Phase 2 (after phase 1 is complete for all cells): the 23 C entry and final tests and the
    extended check-ups, which give the fresh-cell capacity and the remaining trajectory points."""
    if phase == 1:
        et = sorted(n for n in names if "_ET_" in n and n.endswith("_meta.txt"))[:1]
        return [n for n in names if n.endswith("_CU.csv") or n.endswith("_CU_meta.txt")] + et
    keep = ("_ET_T23.csv", "_ET_T23_meta.txt", "_AT_T23.csv", "_AT_T23_meta.txt", "_exCU.csv", "_exCU_meta.txt")
    return [n for n in names if n.endswith(keep)]


def do_cell(serial, url, phase=1):
    os.makedirs(LISTS, exist_ok=True)
    lst = os.path.join(LISTS, f"{serial}.txt")
    hf = HttpRangeFile(url)
    if os.path.exists(lst):
        rows = [l.split("\t") for l in open(lst, encoding="utf8").read().splitlines() if "\t" in l]
    else:
        zf = zipfile.ZipFile(io.BufferedReader(hf, buffer_size=1 << 16))
        rows = [[i.filename, str(i.header_offset), str(i.compress_size), str(i.compress_type), str(i.CRC)]
                for i in zf.infolist() if not i.filename.endswith("/")]
        open(lst, "w", encoding="utf8").write("\n".join("\t".join(r) for r in rows))
    info = {r[0]: r for r in rows}
    todo = [n for n in wanted(list(info), phase) if not os.path.exists(os.path.join(OUT, serial, os.path.basename(n)))]
    if not todo:
        return True
    os.makedirs(os.path.join(OUT, serial), exist_ok=True)
    while dt.time(0, 5) <= dt.datetime.now().time() <= dt.time(0, 30):
        time.sleep(60)
    if os.path.exists(STOP):
        return False

    def one(n):  # requests are latency-bound, so members are fetched in parallel threads
        _, off, csize, method, crc = info[n]
        off, csize, method, crc = int(off), int(csize), int(method), int(crc)
        # one range request per member: local header (30 bytes + name + extra) plus the data
        blob = hf._get(off, min(off + 30 + len(n.encode()) + 2048 + csize, hf.size - 1))
        if blob[:4] != b"PK\x03\x04":
            raise ValueError(f"bad local header for {n}")
        ln, lx = struct.unpack("<HH", blob[26:30])
        start = 30 + ln + lx
        data = blob[start:start + csize]
        if len(data) < csize:
            data += hf._get(off + start + len(data), off + start + csize - 1)
        raw = zlib.decompressobj(-15).decompress(data) if method == 8 else data
        if zlib.crc32(raw) != crc:
            raise ValueError(f"CRC mismatch for {n}")
        dst = os.path.join(OUT, serial, os.path.basename(n))
        with open(dst + ".part", "wb") as out:
            out.write(raw)
        os.replace(dst + ".part", dst)

    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(one, todo))  # re-raises the first error, so the cell is retried later
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
    cells = order()
    log(f"start: {len(cells)} cells")
    for phase in (1, 2):
        done = set()
        while len(done) < len(cells) and not os.path.exists(STOP):
            for serial, url in cells:
                if serial in done or os.path.exists(STOP):
                    continue
                try:
                    if do_cell(serial, url, phase):
                        done.add(serial)
                except Exception as e:
                    log(f"error {serial} (phase {phase}): {type(e).__name__}: {e}")
                    time.sleep(60)
                status(cells, done)
        log(f"phase {phase} complete" if len(done) == len(cells) else f"phase {phase} stopped")
        if os.path.exists(STOP):
            break
    log("finished" if not os.path.exists(STOP) else "stopped")


if __name__ == "__main__":
    main()
