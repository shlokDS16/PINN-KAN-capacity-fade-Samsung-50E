"""Per-workbook cycle index range, time span and protocol currents for CALCE CS2 zips. Capacity columns are NOT read."""
import sys, zipfile, io, json, openpyxl
import numpy as np
out = {}
for zp in sys.argv[2:]:
    z = zipfile.ZipFile(zp); cell = zp.replace("\\","/").split("/")[-1][:-4]
    files = []
    for n in sorted(z.namelist()):
        if not n.endswith(".xlsx"): continue
        wb = openpyxl.load_workbook(io.BytesIO(z.read(n)), read_only=True, data_only=True)
        sheets = [ws.title for ws in wb.worksheets]
        cyc=[]; dts=[]; cur=[]; vol=[]; rows=0
        for ws in wb.worksheets:
            if not ws.title.startswith("Channel"): continue
            it = ws.iter_rows(values_only=True)
            hdr = next(it); ix = {h:i for i,h in enumerate(hdr)}
            for r in it:
                if r[ix["Cycle_Index"]] is None: continue
                rows += 1
                cyc.append(r[ix["Cycle_Index"]]); dts.append(r[ix["Date_Time"]]); cur.append(r[ix["Current(A)"]]); vol.append(r[ix["Voltage(V)"]])
        cur = np.array(cur, float); vol = np.array(vol, float); cyc = np.array(cyc, float)
        d = cur[cur < -0.01]; c = cur[cur > 0.01]
        files.append(dict(file=n.split("/")[-1], sheets=sheets, rows=rows, cmin=int(cyc.min()), cmax=int(cyc.max()), n_distinct=int(len(np.unique(cyc))),
            t0=str(min(dts)), t1=str(max(dts)),
            I_dis_med=float(np.median(d)) if d.size else None, I_chg_med=float(np.median(c)) if c.size else None,
            vmin=float(vol.min()), vmax=float(vol.max())))
        print(cell, files[-1]["file"], files[-1]["cmin"], files[-1]["cmax"], files[-1]["t0"][:10], files[-1]["t1"][:10], flush=True)
    out[cell] = files
json.dump(out, open(sys.argv[1], "w"), indent=1)
