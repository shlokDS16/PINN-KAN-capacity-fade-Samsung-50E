"""Physical-validation analyses of PREREG_v3 section 11a (secondary, descriptive; no test, no Holm, no claim word beyond "consistent / not consistent").

Inputs: the `stress_functions.json` and `superposition.csv` that the run writer emits for every confirmatory run (one directory per outer fold; the members of a fold are its
final-refit seeds, so the envelopes are fold x seed envelopes). Output: `physval_11a.json` (written by the statistics step with `--physval`).

    item 1  effective activation energy E(SOC) [kJ/mol] with the fold x seed envelope; (a) comparison with the Arrhenius parameter of the dataset authors' own calendar fit
            (A10) -- needs the VERIFIED A10 form, otherwise `compare_with_a10_activation` raises UnverifiedArmError (FB-2); (b) published calendar activation energies only from
            sources the lead supplies with a verified DOI and a page/table location -- none are built in, so (b) is "omitted" unless `published` is given; the storage
            laboratory composition per temperature (3.3(7): storage at 10 C is all SIE and at 45 C all HM) from the design metadata (identifiers only)
    item 2  learned storage rate versus SOC at each storage temperature with the envelope, and whether the slope changes sign above SOC 0.8 (see `soc_turning`)
    item 3  Arrhenius monotonicity: already computed (control P2, `stats_step.build_controls`)
    item 4  superposition check: summary of `superposition.csv` (counterfactual calendar share and the number of cells with a physically impossible split)
    item 5  direction of the cyclic stress effects (sign of the partial-dependence change over each stress range, per member) and, when the A10 form is verified, its
            agreement with the sign of the dataset authors' cycle-model effect (`compare_with_a10_signs`, otherwise UnverifiedArmError)
Definitions chosen where the prereg leaves them open (the lead confirms): the turning rule of item 2 and the 'direction' of item 5 below."""
import json
import os

import numpy as np
import pandas as pd

from . import ROOT, semi
from .semi import UnverifiedArmError

CAVEATS = {"item1": "storage at 10 C is all SIE and at 45 C all HM, so E(SOC) is laboratory-confounded; the comparison with A10 is 'consistency with the semi-empirical fit', not independent validation",
           "item2": "SOC above 0.8 exists in stage 1 only (stage 2 stops at 0.8)",
           "item4": "the counterfactual y(a_cyc = 0) / y(full) is a model quantity, not a measurement"}


def _load(p):
    return json.load(open(p, encoding="utf8"))


def merge_stress_functions(run_dirs):
    """-> dict of member arrays concatenated over the fold runs: soc, E (m x nSOC), a (m x nSOC), rate (m x nT x nSOC), T_C, cyc {var: (x, members m x nx, A10 mean or None)}"""
    sfs = []
    for d in run_dirs:
        p = os.path.join(d, "stress_functions.json")
        if not os.path.exists(p):
            raise FileNotFoundError(f"{p} (written by the run writer of a Samsung/synthetic confirmatory or inner run)")
        sfs.append(_load(p))
    soc = np.array(sfs[0]["calendar"]["soc"], float)
    for sf in sfs:
        if not np.allclose(sf["calendar"]["soc"], soc):
            raise ValueError("stress_functions.json files with different SOC grids cannot be merged")
    out = dict(soc=soc, T_C=list(sfs[0]["storage_rate"]["T_C"]), n_runs=len(sfs))
    for s_ in sfs:
        if "members" not in s_:
            raise KeyError("stress_functions.json has no `members` block (written by emit.stress_functions since build_v1 section 7); rerun the run writer")
    for key, name in (("E", "E_kJmol"), ("a", "a_pp500"), ("rate", "storage_rate")):
        out[key] = np.concatenate([np.asarray(s_["members"][name], float) for s_ in sfs])
    out["A10_E_kJmol"] = [s["calendar"]["A10_E_kJmol"] for s in sfs if "A10_E_kJmol" in s["calendar"]]
    cyc = {}
    for var in sfs[0]["cyclic"]:
        cyc[var] = dict(x=np.array(sfs[0]["cyclic"][var]["x"], float), members=np.concatenate([np.asarray(s["members"][f"cyclic.{var}"], float) for s in sfs]),
                        a10=(np.array(sfs[0]["cyclic"][var]["A10"]["mean"], float) if "A10" in sfs[0]["cyclic"][var] else None))
    out["cyc"] = cyc
    out["n_members"] = int(out["E"].shape[0])
    return out


def _env(m):
    m = np.asarray(m, float)
    return dict(mean=m.mean(0).tolist(), median=np.median(m, 0).tolist(), lo=m.min(0).tolist(), hi=m.max(0).tolist())


# ------------------------------------------------------------------------------------------------ item 1
def storage_lab_composition(meta_csv):
    """storage cells 01-03 per design temperature and laboratory (counts), from experiments_meta.csv (identifiers only)"""
    d = pd.read_csv(meta_csv)
    d = d[(d["type"] == "k") & (d["cell"] <= 3)]
    return {str(float(T)): {str(l): int(n) for l, n in g["lab"].value_counts().sort_index().items()} for T, g in d.groupby("amb_temp_tp")}


def activation_energy(M, sel_soc=(5.0, 50.0, 80.0, 100.0)):
    soc = M["soc"]
    idx = [int(np.argmin(abs(soc - v))) for v in sel_soc]
    env = _env(M["E"])
    return dict(n_members=M["n_members"], soc=soc.tolist(), E_kJmol=env, at_selected_soc={f"{soc[i]:g}": dict(median=env["median"][i], lo=env["lo"][i], hi=env["hi"][i]) for i in idx},
                range_of_envelope_kJmol=[float(np.min(env["lo"])), float(np.max(env["hi"]))])


def compare_with_a10_activation(M):
    """(a) The activation-energy parameter of A10's calendar fit against the envelope of E(SOC). Needs the VERIFIED A10 form (FB-2): raises UnverifiedArmError otherwise."""
    semi.require_verified()
    ev = M["A10_E_kJmol"]
    if not ev:
        return dict(status="A10 did not run in these runs (no A10_E_kJmol in stress_functions.json)")
    e10 = float(np.mean(ev))
    env = _env(M["E"])
    lo, hi = float(np.min(env["lo"])), float(np.max(env["hi"]))
    return dict(A10_E_kJmol=e10, envelope_range=[lo, hi], verdict="consistent" if lo <= e10 <= hi else "not consistent", label="consistency with the semi-empirical fit (not independent validation)")


def compare_with_published(M, published):
    """(b) published calendar activation energies. Each item must be {doi, location, E_kJmol_range [lo, hi], chemistry, note}; nothing is built in, nothing is invented.
    -> omitted when the list is empty; otherwise 'consistent' when the published range overlaps the envelope range."""
    pub = [p for p in (published or []) if p.get("doi") and p.get("location") and p.get("E_kJmol_range")]
    if not pub:
        return dict(status="omitted: no source with a verified DOI and a page/table location was supplied (PREREG 11a item 1(b))")
    env = _env(M["E"])
    lo, hi = float(np.min(env["lo"])), float(np.max(env["hi"]))
    return dict(envelope_range=[lo, hi], sources=[dict(doi=p["doi"], location=p["location"], E_kJmol_range=p["E_kJmol_range"], overlaps=bool(p["E_kJmol_range"][0] <= hi and p["E_kJmol_range"][1] >= lo)) for p in pub])


# ------------------------------------------------------------------------------------------------ item 2
def soc_turning(soc, rate, start=80.0):
    """Turning of a rate-versus-SOC curve above `start` (SOC in %): with d_k = r[k+1] - r[k] on the SOC grid, a turning point is a grid point s_k >= start where d_{k-1} and d_k
    are nonzero with opposite signs; 'peak' (d_{k-1} > 0 > d_k) or 'trough'. -> list of (soc, 'peak'|'trough')"""
    soc, r = np.asarray(soc, float), np.asarray(rate, float)
    d = np.diff(r)
    out = []
    for k in range(1, len(d)):
        if soc[k] >= start - 1e-9 and d[k - 1] * d[k] < 0:
            out.append((float(soc[k]), "peak" if d[k - 1] > 0 else "trough"))
    return out


def soc_dependence(M, start=80.0):
    soc, T = M["soc"], M["T_C"]
    out = dict(caveat=CAVEATS["item2"], rule=f"turning point = grid point with SOC >= {start:g} % where the slope of the storage rate changes sign (peak or trough)", per_temperature={})
    i80, i100, i50 = (int(np.argmin(abs(soc - v))) for v in (80.0, 100.0, 50.0))
    for j, t in enumerate(T):
        R = M["rate"][:, j, :]
        env = _env(R)
        tm = [soc_turning(soc, R[m], start) for m in range(R.shape[0])]
        mean_t = soc_turning(soc, np.array(env["mean"]), start)
        out["per_temperature"][f"{t:g}"] = dict(
            rate_pp500d=env, n_members=int(R.shape[0]), share_members_with_turning=float(np.mean([len(x) > 0 for x in tm])),
            share_members_with_peak=float(np.mean([any(k == "peak" for _, k in x) for x in tm])), share_members_with_trough=float(np.mean([any(k == "trough" for _, k in x) for x in tm])),
            mean_curve_turning=mean_t, mean_slope_sign_50_to_80=float(np.sign(env["mean"][i80] - env["mean"][i50])), mean_slope_sign_80_to_100=float(np.sign(env["mean"][i100] - env["mean"][i80])),
            slope_sign_changes_above_80=bool(len(mean_t) > 0 or np.sign(env["mean"][i100] - env["mean"][i80]) != np.sign(env["mean"][i80] - env["mean"][i50])))
    return out


# ------------------------------------------------------------------------------------------------ item 4
def superposition_summary(run_dirs):
    """per arm: cells, quantiles of the counterfactual calendar share, number and share of cells with the calendar loss alone above the observed total fade"""
    dfs = [pd.read_csv(os.path.join(d, "superposition.csv")) for d in run_dirs if os.path.exists(os.path.join(d, "superposition.csv"))]
    if not dfs:
        return dict(status="not available: no superposition.csv (written by confirmatory runs with scored cycling cells)")
    df = pd.concat(dfs)
    out = dict(caveat=CAVEATS["item4"], arms={})
    for arm, g in df.groupby("arm"):
        q = g["share_cal"].quantile([0.0, 0.25, 0.5, 0.75, 1.0]).tolist()
        n_bad = int(g["cal_exceeds_total"].astype(str).str.lower().isin(["true", "1"]).sum())
        out["arms"][arm] = dict(n_cells=int(len(g)), share_cal_min_q25_median_q75_max=q, share_cal_mean=float(g["share_cal"].mean()), n_calendar_exceeds_observed_total=n_bad,
                                share_cells_impossible_split=n_bad / len(g))
    return out


# ------------------------------------------------------------------------------------------------ item 5
def cyclic_directions(M):
    """per stress variable and member: direction = sign of PD(x_last) - PD(x_first); monotone = all finite differences of one sign; shares over members"""
    out = {}
    for var, c in M["cyc"].items():
        m = c["members"]
        sgn = np.sign(m[:, -1] - m[:, 0])
        d = np.diff(m, axis=1)
        mono = np.all(d >= -1e-9, axis=1) | np.all(d <= 1e-9, axis=1)
        out[var] = dict(n_members=int(m.shape[0]), share_increasing=float(np.mean(sgn > 0)), share_decreasing=float(np.mean(sgn < 0)), share_monotone=float(np.mean(mono)),
                        direction_of_mean_curve=float(np.sign(m.mean(0)[-1] - m.mean(0)[0])), envelope=_env(m), x=c["x"].tolist())
    return out


def compare_with_a10_signs(M):
    """Sign of the cyclic effect of A1 (majority of members) against the sign of the dataset authors' cycle model (A10 partial dependence). Needs the VERIFIED A10 form."""
    semi.require_verified()
    rows = {}
    for var, c in M["cyc"].items():
        if c["a10"] is None:
            continue
        s10 = float(np.sign(c["a10"][-1] - c["a10"][0]))
        share = float(np.mean(np.sign(c["members"][:, -1] - c["members"][:, 0]) == s10))
        rows[var] = dict(sign_A10=s10, share_members_same_sign=share, verdict="consistent" if share > 0.5 else "not consistent")
    return rows or dict(status="A10 did not run in these runs")


# ------------------------------------------------------------------------------------------------ driver
def physval_11a(run_dirs, published=None, meta_csv=None, strict=False):
    """-> dict for physval_11a.json. The A10 comparisons (item 1(a), item 5) are recorded as `blocked` (with the UnverifiedArmError message) while the A10 form is
    unverified; `strict=True` raises instead."""
    M = merge_stress_functions(run_dirs)
    if meta_csv is None and _load(os.path.join(run_dirs[0], "config.json")).get("dataset") == "samsung":
        meta_csv = os.path.join(ROOT, "data", "raw", "samsung50e_meta", "experiments_meta.csv")
    out = dict(prereg="11a (descriptive; no test, no Holm; words 'consistent / not consistent' only)", n_runs=M["n_runs"], n_members=M["n_members"], a10_verified=bool(semi.A10_FORM["verified"]),
               blocked={}, caveats=CAVEATS)
    out["item1"] = dict(activation_energy=activation_energy(M), published=compare_with_published(M, published))
    if meta_csv and os.path.exists(meta_csv):
        out["item1"]["storage_lab_composition"] = storage_lab_composition(meta_csv)
    try:
        out["item1"]["vs_A10"] = compare_with_a10_activation(M)
    except UnverifiedArmError as e:
        if strict:
            raise
        out["blocked"]["item1a_vs_A10"] = str(e)
    out["item2"] = soc_dependence(M)
    out["item3"] = "Arrhenius monotonicity: controls.json positive.P2_monotone_in_T"
    out["item4"] = superposition_summary(run_dirs)
    out["item5"] = dict(directions=cyclic_directions(M))
    try:
        out["item5"]["vs_A10"] = compare_with_a10_signs(M)
    except UnverifiedArmError as e:
        if strict:
            raise
        out["blocked"]["item5_vs_A10"] = str(e)
    return out
