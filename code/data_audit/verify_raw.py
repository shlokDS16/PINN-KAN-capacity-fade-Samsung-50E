"""Verify raw downloads under data/raw/: size, SHA-256, zip CRC, parse check and per-cell cycle counts.

Run:  python -I code/data_audit/verify_raw.py <ROOT> [dataset_dir ...]
Nothing inside a download is executed. Pickles are scanned statically (pickletools) and, only if every
referenced global is on a small allowlist (plain containers and numpy array reconstruction), loaded with an
allowlist-only Unpickler. Zip members are read in memory; nothing is extracted to disk.

Outputs (written under <ROOT>/data/):
  CHECKSUMS.sha256       "<sha256>  <relative path>" for every file under data/raw (sha256sum -c compatible)
  PARSE_REPORT.json      per-dataset results (sizes, zip test, cycle counts, notes)
"""
import hashlib
import io
import json
import os
import pickle
import pickletools
import sys
import zipfile

# Trusted third-party libraries live in the user site; python -I does not add it, so append it explicitly.
USER_SITE = os.path.join(os.environ.get("APPDATA", ""), "Python", "Python314", "site-packages")
if os.path.isdir(USER_SITE) and USER_SITE not in sys.path:
    sys.path.append(USER_SITE)

import numpy as np  # noqa: E402

# Expected byte sizes from the repositories' own metadata (APIs / HTTP headers), keyed by path relative to data/raw.
EXPECTED = {
    "nasa_pcoe_battery/5.Battery_Data_Set.zip": 209708670,
    "drive_calce_ev/CALCE-EV_Dataset.zip": 5614245,
    "drive_nasa_ev/NASA-EV.zip": 239496734,
    "isu_ilcc_small/Valid_cells.csv": 1727,
    "isu_ilcc_small/README_V2.0.pdf": 640953,
    "isu_ilcc_small/capacity_fade.zip": 140256,
    "isu_ilcc_small/process_data.py.txt": 9769,
    "isu_ilcc_small/Q_interpolated.zip": 47797453,
    "calce_cs2/CS2_35.zip": 37056519,
    "calce_cs2/CS2_36.zip": 37881685,
    "calce_cs2/CS2_38.zip": 42811100,
    "calce_cs2/CS2_34.zip": 43836986,
    "batterylife_processed_snl/SNL.zip": 115187861,
    "calce_pl_pouch/SOC_0-60_HalfC.zip": 89357014,
    "calce_pl_pouch/SOC_40-60_HalfC.zip": 72818135,
    "calce_pl_pouch/SOC_40-60_2C.zip": 57740595,
    "calce_pl_pouch/SOC_0-100_HalfC.zip": 67460712,
    "calce_pl_pouch/SOC_0-100_2C.zip": 57559175,
    "calce_pl_pouch/SOC_20-80_2C.zip": 74575680,
    "calce_pl_pouch/SOC_40-100_HalfC.zip": 106626746,
    "calce_pl_pouch/SOC_20-80_HalfC.zip": 132710443,
    "oxford_degradation_1/ExampleDC_C1.mat": 72593,
    "oxford_degradation_1/Readme.txt": 5643,
}


def sha256_file(path, block=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(block)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


# ---------- safe pickle handling ----------
_ALLOWED = {
    ("builtins", "dict"), ("builtins", "list"), ("builtins", "set"), ("builtins", "tuple"),
    ("builtins", "frozenset"), ("builtins", "slice"), ("builtins", "complex"),
    ("collections", "OrderedDict"), ("collections", "defaultdict"),
    ("numpy", "ndarray"), ("numpy", "dtype"),
    ("numpy.core.multiarray", "_reconstruct"), ("numpy._core.multiarray", "_reconstruct"),
    ("numpy.core.multiarray", "scalar"), ("numpy._core.multiarray", "scalar"),
}


def pickle_globals(data):
    """Static scan: return the set of (module, name) the pickle would import. Executes nothing."""
    out, strings = set(), []
    for op, arg, _ in pickletools.genops(data):
        if op.name in ("SHORT_BINUNICODE", "BINUNICODE", "UNICODE", "BINUNICODE8"):
            strings.append(arg)
        if op.name in ("GLOBAL", "INST"):
            m, n = arg.split(" ", 1)
            out.add((m, n))
        elif op.name == "STACK_GLOBAL" and len(strings) >= 2:
            out.add((strings[-2], strings[-1]))
    return out


# SECURITY NOTE: the files come from an untrusted download. They are never passed to plain pickle.load.
# pickle_globals() first lists every global the stream would import (static opcode scan, nothing runs);
# loading proceeds only if all are in _ALLOWED, and this Unpickler refuses anything else in find_class,
# so no callable outside plain containers / numpy array reconstruction can be invoked.
class _SafeUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if (module, name) in _ALLOWED:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(f"blocked global {module}.{name}")


def safe_pickle_load(data):
    g = pickle_globals(data)
    bad = sorted(x for x in g if x not in _ALLOWED)
    if bad:
        return None, {"blocked_globals": [".".join(b) for b in bad[:10]]}
    return _SafeUnpickler(io.BytesIO(data)).load(), {"globals": sorted(".".join(x) for x in g)}


# ---------- dataset parsers ----------
def parse_nasa_pcoe(path):
    from scipy.io import loadmat
    res = {"cells": {}, "inner_zips": []}
    with zipfile.ZipFile(path) as outer:
        bad = outer.testzip()
        res["zip_test"] = "ok" if bad is None else f"bad member {bad}"
        for info in outer.infolist():
            if not info.filename.endswith(".zip"):
                continue
            with zipfile.ZipFile(io.BytesIO(outer.read(info))) as inner:
                mats = [i for i in inner.infolist() if i.filename.lower().endswith(".mat") and not i.filename.startswith("__MACOSX")]
                res["inner_zips"].append({"name": info.filename.split("/")[-1], "mat_files": len(mats)})
                for mi in mats:
                    key = mi.filename.split("/")[-1][:-4]
                    try:
                        m = loadmat(io.BytesIO(inner.read(mi)), squeeze_me=False, struct_as_record=True)
                        var = [k for k in m if not k.startswith("__")][0]
                        cyc = m[var][0, 0]["cycle"][0]
                        types = [str(c["type"][0]) for c in cyc]
                        ndis = types.count("discharge")
                        caps = []
                        temps = set()
                        empty_fields = 0
                        for c, t in zip(cyc, types):
                            a = np.ravel(c["ambient_temperature"])
                            if a.size:
                                temps.add(float(a[0]))
                            else:
                                empty_fields += 1
                            if t == "discharge":
                                cp = np.ravel(c["data"][0, 0]["Capacity"])
                                if cp.size:
                                    caps.append(float(cp[0]))
                                else:
                                    empty_fields += 1
                        res["cells"][key] = {
                            "records": len(cyc), "charge": types.count("charge"), "discharge": ndis,
                            "impedance": types.count("impedance"),
                            "ambient_temp_C": sorted(temps),
                            "capacity_first_last_Ah": [caps[0], caps[-1]] if caps else None,
                            "records_with_empty_field": empty_fields,
                        }
                    except Exception as e:  # report, do not hide
                        res["cells"][key] = {"parse_error": f"{type(e).__name__}: {e}"}
    return res


def parse_oxford(path):
    res = {"cells": {}}
    try:
        from scipy.io import loadmat
        m = loadmat(path, squeeze_me=True, struct_as_record=True)
        for k, v in m.items():
            if k.startswith("__"):
                continue
            names = getattr(getattr(v, "dtype", None), "names", None)
            res["cells"][k] = {"fields": len(names) if names else None, "first_fields": list(names[:3]) if names else None}
        res["reader"] = "scipy.io.loadmat"
    except NotImplementedError:
        import h5py
        with h5py.File(path, "r") as f:
            for k in f.keys():
                g = f[k]
                res["cells"][k] = {"fields": len(g.keys()) if hasattr(g, "keys") else None}
        res["reader"] = "h5py (MATLAB v7.3)"
    return res


def parse_calce_ev(path):
    res = {"files": {}}
    with zipfile.ZipFile(path) as z:
        res["zip_test"] = "ok" if z.testzip() is None else "bad"
        for i in z.infolist():
            if i.filename.endswith(".csv"):
                with z.open(i) as f:
                    hdr = f.readline().decode("utf8", "replace").strip()
                    n = sum(1 for _ in f)
                res["files"][i.filename] = {"rows": n, "columns": hdr.count(",") + 1}
    return res


def parse_isu_capacity(path):
    res = {"cells": {}}
    with zipfile.ZipFile(path) as z:
        res["zip_test"] = "ok" if z.testzip() is None else "bad"
        for i in z.infolist():
            if i.filename.endswith(".csv"):
                t = z.read(i).decode("utf8", "replace").strip().splitlines()
                res["cells"][i.filename.split("/")[-1][:-4]] = {"rpt_points": len(t) - 1}
    return res


def parse_isu_q(path):
    res = {"cells": {}}
    with zipfile.ZipFile(path) as z:
        res["zip_test"] = "ok" if z.testzip() is None else "bad"
        for i in z.infolist():
            if i.filename.endswith(".csv"):
                raw = z.read(i).decode("utf8", "replace").strip().splitlines()
                res["cells"][i.filename.split("/")[-1][:-4]] = {"rows": len(raw), "columns": raw[0].count(",") + 1}
    return res


def parse_nasa_ev(path):
    import csv
    res = {"cells": {}}
    with zipfile.ZipFile(path) as z:
        res["zip_test"] = "ok" if z.testzip() is None else "bad"
        rows = list(csv.DictReader(z.read("cleaned_dataset/metadata.csv").decode("utf8").splitlines()))
        res["metadata_rows"] = len(rows)
        files = {i.filename.split("/")[-1] for i in z.infolist() if i.filename.startswith("cleaned_dataset/data/")}
        res["data_csv_files"] = len(files)
        res["metadata_files_missing_in_zip"] = sum(1 for r in rows if r["filename"] not in files)
        for r in rows:
            c = res["cells"].setdefault(r["battery_id"], {"charge": 0, "discharge": 0, "impedance": 0})
            c[r["type"]] += 1
    return res


def parse_cs2(path):
    """CALCE CS2/CX2 workbooks: one xlsx per test date; sheet 'Channel_*' holds the raw cycler log."""
    import openpyxl
    res = {"files": {}}
    with zipfile.ZipFile(path) as z:
        res["zip_test"] = "ok" if z.testzip() is None else "bad"
        total_rows, max_cyc, distinct_sum = 0, 0, 0
        for i in z.infolist():
            if not i.filename.endswith(".xlsx"):
                continue
            wb = openpyxl.load_workbook(io.BytesIO(z.read(i)), read_only=True, data_only=True)
            sn = [n for n in wb.sheetnames if n.startswith("Channel")]
            if not sn:
                res["files"][i.filename.split("/")[-1]] = {"error": "no Channel sheet", "sheets": wb.sheetnames}
                continue
            it = wb[sn[0]].iter_rows(values_only=True)
            hdr = list(next(it))
            ci = hdr.index("Cycle_Index")
            cyc, n = set(), 0
            for r in it:
                n += 1
                if r[ci] is not None:
                    cyc.add(int(r[ci]))
            total_rows += n
            distinct_sum += len(cyc)
            max_cyc = max(max_cyc, max(cyc) if cyc else 0)
            res["files"][i.filename.split("/")[-1]] = {"rows": n, "cycle_min": min(cyc) if cyc else None, "cycle_max": max(cyc) if cyc else None}
        res["workbooks"] = len(res["files"])
        res["total_rows"] = total_rows
        res["max_cycle_index_any_file"] = max_cyc
        res["sum_distinct_cycles_per_file"] = distinct_sum
    return res


def parse_zip_listing(path):
    """Fallback: CRC test and member listing summary."""
    res = {}
    with zipfile.ZipFile(path) as z:
        res["zip_test"] = "ok" if z.testzip() is None else "bad"
        inf = z.infolist()
        res["members"] = len(inf)
        ext = {}
        for i in inf:
            if not i.is_dir():
                e = i.filename.rsplit(".", 1)[-1].lower() if "." in i.filename else ""
                ext[e] = ext.get(e, 0) + 1
        res["extensions"] = ext
        res["uncompressed_bytes"] = sum(i.file_size for i in inf)
        res["first_members"] = [i.filename for i in inf[:8]]
    return res


def parse_snl_pickles(path):
    res = {"cells": {}}
    with zipfile.ZipFile(path) as z:
        res["zip_test"] = "ok" if z.testzip() is None else "bad"
        for i in z.infolist():
            if i.filename.endswith(".pkl"):
                obj, meta = safe_pickle_load(z.read(i))
                key = i.filename.split("/")[-1][:-4]
                if obj is None:
                    res["cells"][key] = {"not_loaded": meta}
                    continue
                entry = {"type": type(obj).__name__}
                if isinstance(obj, dict):
                    entry["keys"] = list(obj.keys())[:12]
                    cd = obj.get("cycle_data")
                    if cd is not None:
                        entry["cycles"] = len(cd)
                    for k in ("nominal_capacity_in_Ah", "charge_protocol", "discharge_protocol", "SOC_interval", "cathode_material"):
                        if k in obj:
                            entry[k] = str(obj[k])[:120]
                res["cells"][key] = entry
    return res


def main():
    root = sys.argv[1]
    only = set(sys.argv[2:])
    raw = os.path.join(root, "data", "raw")
    report, sums = {}, []
    for ds in sorted(os.listdir(raw)):
        d = os.path.join(raw, ds)
        if not os.path.isdir(d) or (only and ds not in only):
            continue
        entry = {"files": {}}
        for fn in sorted(os.listdir(d)):
            p = os.path.join(d, fn)
            if not os.path.isfile(p) or fn.endswith(".part"):
                continue
            rel = f"{ds}/{fn}"
            size = os.path.getsize(p)
            exp = EXPECTED.get(rel)
            fe = {"bytes": size, "expected_bytes": exp, "size_ok": (size == exp) if exp else None}
            if exp is not None and size != exp:
                fe["note"] = "INCOMPLETE or size mismatch; not hashed into CHECKSUMS"
                entry["files"][fn] = fe
                continue
            fe["sha256"] = sha256_file(p)
            sums.append((fe["sha256"], f"data/raw/{rel}"))
            try:
                if fn == "5.Battery_Data_Set.zip":
                    fe["parse"] = parse_nasa_pcoe(p)
                elif fn.endswith(".mat") and ds.startswith("oxford"):
                    fe["parse"] = parse_oxford(p)
                elif fn == "NASA-EV.zip":
                    fe["parse"] = parse_nasa_ev(p)
                elif ds == "calce_cs2" and fn.endswith(".zip"):
                    fe["parse"] = parse_cs2(p)
                elif fn == "CALCE-EV_Dataset.zip":
                    fe["parse"] = parse_calce_ev(p)
                elif fn == "capacity_fade.zip":
                    fe["parse"] = parse_isu_capacity(p)
                elif fn == "Q_interpolated.zip":
                    fe["parse"] = parse_isu_q(p)
                elif fn == "SNL.zip":
                    fe["parse"] = parse_snl_pickles(p)
                elif fn.endswith(".zip"):
                    fe["parse"] = parse_zip_listing(p)
                elif fn.endswith(".csv"):
                    with open(p, encoding="utf8", errors="replace") as fh:
                        fe["parse"] = {"rows": sum(1 for _ in fh) - 1}
            except Exception as e:
                fe["parse_error"] = f"{type(e).__name__}: {e}"
            entry["files"][fn] = fe
            print("verified", rel, flush=True)
        report[ds] = entry
    out_dir = os.path.join(root, "data")
    suffix = "" if not only else "." + "_".join(sorted(only))[:60]
    with open(os.path.join(out_dir, f"PARSE_REPORT{suffix}.json"), "w", encoding="utf8") as fh:
        json.dump(report, fh, indent=1, default=str)
    if not only:
        with open(os.path.join(out_dir, "CHECKSUMS.sha256"), "w", encoding="utf8", newline="\n") as fh:
            for h, rel in sums:
                fh.write(f"{h}  {rel}\n")
    else:
        with open(os.path.join(out_dir, f"CHECKSUMS{suffix}.sha256"), "w", encoding="utf8", newline="\n") as fh:
            for h, rel in sums:
                fh.write(f"{h}  {rel}\n")


if __name__ == "__main__":
    main()
