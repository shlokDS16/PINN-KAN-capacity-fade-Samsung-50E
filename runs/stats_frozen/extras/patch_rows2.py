d = r"C:\Users\Shlok\Downloads\PINN KAN battery paper\runs\stats_frozen\extras" + "\\"
p = d + "run_rows.py"
s = open(p, encoding="utf8").read()
old = 'r["pct_reduction_ci95"] = [pr(r["median_L_ci95"][1]), pr(r["median_L_ci95"][0])] if "median_L_ci95" in r else None'
new = 'r["pct_reduction_ci95"] = [pr(r["median_L_ci95"][0]), pr(r["median_L_ci95"][1])] if "median_L_ci95" in r else None   # pr is increasing in L: no swap (fixed after re-check 2)'
assert old in s
s = s.replace(old, new)
old2 = '''    e = est.get((comp, cell))
    mk = f"m{cell[0]}_k{cell[1]}"'''
new2 = '''    e = est.get((comp, cell))
    mk = f"m{cell[0]}_k{cell[1]}"
    if e is None and name == "A1 vs A13":              # not an estimated comparator of the frozen step: same entry() function, BCa label by the frozen convention
        e = v4.entry(P, name, "A1", comp, cell, rule, bca=True, bca_label=f"B|{name}|g{cell[0]}-{cell[1]}|BCa_mean_pp")'''
assert old2 in s
s = s.replace(old2, new2)
old3 = 'dump("row_e_pp_scale.json", rows_e)'
new3 = '''for name, tgt, comp, kk in (("A15 vs A1", "A15", "A1", "K1"), ("A15 vs G15", "A15", "G15", "K2")):      # K1, K2: per-seed endpoints (seed view), same entry() and BCa as the other rows
    mk = "m32_kfull"
    m = mg.get(name, {}).get(mk)
    lab = f"{name} {mk} ({kk}; per-seed endpoints)"
    sv = P.seed_view()
    if m is None or not (sv.has(tgt, *G4) and sv.has(comp, *G4)):
        rows_e["rows"][lab] = "not computed: no margin entry or arm missing in the per-seed tables"
        continue
    e = v4.entry(sv, name, tgt, comp, G4, rule, bca=True, bca_label=f"B|{name}|g32-full|BCa_mean_pp")
    lo, hi = e["mean_pp_ci"]
    tier = "S" if lo > m["delta_S_pp"] else ("N" if lo > -m["delta_N_pp"] else "none")
    rows_e["rows"][lab] = {"n": e["n"], "mean_pp_diff": e["mean_pp"], "mean_pp_bca95": [lo, hi], "E_pp": m["E_pp"], "delta_S_pp": m["delta_S_pp"], "delta_N_pp": m["delta_N_pp"], "pp_scale_tier_it_would_reach": tier}
dump("row_e_pp_scale.json", rows_e)'''
assert old3 in s
s = s.replace(old3, new3)
open(p, "w", encoding="utf8").write(s)
p = d + "run_extras.py"
s = open(p, encoding="utf8").read()
old = 'D = ["", "## D. Rows (b) per stage'
new = 'D = ["", "CHANGE LOG (re-check 2): (a) row (d) intervals were printed upper-bound first (bounds swapped in the percent conversion); fixed, row_d_two_stage_bootstrap.json and D3 regenerated, no other number changed. (b) row (e): A1 vs A13 (g1) is now computed from margins.json and entry() (it was wrongly listed as having no margin entry), and K1 and K2 are listed explicitly in D4. All other rows are unchanged.", "", "## D. Rows (b) per stage'
assert old in s
open(p, "w", encoding="utf8").write(s.replace(old, new))
print("ok")
