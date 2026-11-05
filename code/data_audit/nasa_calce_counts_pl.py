"""Schedule summary (operations, dates) of every complete .mat member in the CALCE PL zips (complete or partial).
Walks local zip headers; nothing is extracted to disk; only the Operation/Start Date table is read, not the data arrays."""
import sys, os, re, struct, zlib, io, glob, json, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from scipy.io import loadmat
out = {}
for p in sorted(glob.glob(sys.argv[1] + "/*")):
    sz = os.path.getsize(p); base = os.path.basename(p)
    with open(p, "rb") as f:
        pos = 0
        while pos + 30 <= sz:
            f.seek(pos); h = f.read(30)
            if h[:4] != b"PK\x03\x04": break
            ver, flag, comp, mt, md, crc, csz, usz, nl, el = struct.unpack("<HHHHHIIIHH", h[4:])
            name = f.read(nl).decode("cp437"); start = pos + 30 + nl + el
            if flag & 8 and csz == 0: break
            end = start + csz
            if name.endswith(".mat"):
                if end > sz: out.setdefault(base, {})[name] = "incomplete"
                else:
                    f.seek(start); data = zlib.decompress(f.read(csz), -15)
                    ok = zlib.crc32(data) & 0xffffffff == crc
                    var = os.path.basename(name)[:-4]
                    a = loadmat(io.BytesIO(data), squeeze_me=False)[var]
                    ops = [(str(a[r,0].ravel()[0]), str(a[r,1].ravel()[0])) for r in range(1, a.shape[0])]
                    tot = sum(int(re.match(r"(\d+)", o).group(1)) for o,_ in ops if o[0].isdigit())
                    miss = sum(1 for o,_ in ops if "Missing" in o)
                    sing = sum(1 for o,_ in ops if o.startswith("Single"))
                    ds = [dt.datetime.strptime(d, "%B %d, %Y") for _,d in ops]
                    out.setdefault(base, {})[name] = dict(crc_ok=ok, rows=len(ops), partial_total=tot, missing_blocks=miss, single=sing,
                        first=str(min(ds).date()), last=str(max(ds).date()), span_days=(max(ds)-min(ds)).days, bytes=usz)
            pos = end
json.dump(out, open(sys.argv[2], "w"), indent=1)
for z, d in out.items():
    for n, v in d.items(): print(z, n, v)
