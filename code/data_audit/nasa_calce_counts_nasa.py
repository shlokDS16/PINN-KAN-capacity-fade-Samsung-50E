"""Per-cell counts, ambient temperatures, time spans and protocol parameters of NASA PCoE battery set.
No Capacity field is read. Members are read in memory from the zip; nothing is extracted or executed."""
import sys, io, zipfile, json, datetime as dt
import numpy as np
from scipy.io import loadmat
outer = zipfile.ZipFile(sys.argv[1])
rows = {}
for i in outer.infolist():
    if not i.filename.endswith(".zip"): continue
    grp = i.filename.split("/")[-1]
    inner = zipfile.ZipFile(io.BytesIO(outer.read(i)))
    for j in inner.infolist():
        if not j.filename.endswith(".mat"): continue
        name = j.filename.split("/")[-1][:-4]
        m = loadmat(io.BytesIO(inner.read(j)), squeeze_me=True, struct_as_record=False)
        top = m[name]
        cyc = top.cycle
        types = [str(c.type) for c in cyc]
        amb = {}
        times = []
        cur = []; vmin = []; dur_n = []
        for c in cyc:
            t = str(c.type)
            amb.setdefault(t, set()).add(float(c.ambient_temperature))
            tv = np.asarray(c.time, dtype=float).ravel()
            times.append(dt.datetime(int(tv[0]), int(tv[1]), int(tv[2]), int(tv[3]), int(tv[4]), int(tv[5])))
            if t == "discharge":
                d = c.data
                I = np.atleast_1d(np.asarray(d.Current_measured, dtype=float))
                V = np.atleast_1d(np.asarray(d.Voltage_measured, dtype=float))
                if I.size:
                    cur.append(float(np.median(np.abs(I[np.abs(I) > 0.1]))) if np.any(np.abs(I) > 0.1) else 0.0)
                    vmin.append(float(np.min(V)))
        rows[name] = dict(
            group=grp, n_records=len(cyc),
            n_charge=types.count("charge"), n_discharge=types.count("discharge"), n_impedance=types.count("impedance"),
            amb={k: sorted(v) for k, v in amb.items()},
            first=min(times).isoformat(), last=max(times).isoformat(),
            span_days=(max(times) - min(times)).total_seconds() / 86400,
            disch_I_median_of_median=float(np.median(cur)) if cur else None,
            disch_I_min=float(np.min(cur)) if cur else None, disch_I_max=float(np.max(cur)) if cur else None,
            disch_vmin_median=float(np.median(vmin)) if vmin else None,
            disch_vmin_min=float(np.min(vmin)) if vmin else None, disch_vmin_max=float(np.max(vmin)) if vmin else None,
            nonmonotone_times=int(np.sum(np.diff([t.timestamp() for t in times]) < 0)),
        )
json.dump(rows, open(sys.argv[2], "w"), indent=1)
for k in sorted(rows):
    r = rows[k]
    print(k, r["group"][:22], "ch", r["n_charge"], "dis", r["n_discharge"], "imp", r["n_impedance"], r["amb"], "span_d %.0f" % r["span_days"],
          "I %.2f [%.2f,%.2f]" % (r["disch_I_median_of_median"], r["disch_I_min"], r["disch_I_max"]),
          "Vmin med %.2f [%.2f,%.2f]" % (r["disch_vmin_median"], r["disch_vmin_min"], r["disch_vmin_max"]), "nonmono", r["nonmonotone_times"])
