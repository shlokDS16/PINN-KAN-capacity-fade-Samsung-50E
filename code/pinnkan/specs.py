"""Dataset specifications: time/throughput scales, stress ranges (label-free, fixed physical ranges), forcing formulas.

State y_s = y_scale * (1 - retention) (y_scale = 10, i.e. units of 10 percentage points), time t_n = t / t_scale,
cumulative throughput E_n = EFC / efc_scale (EFC = equivalent full cycles)."""
from dataclasses import dataclass, field

import numpy as np

REST_H_ISU = 0.5  # nominal rest per cycle in the P4/P5 pilots (ISU forcing calibration on Cycling_json members: TODO, prereg 3.4)


@dataclass(frozen=True)
class DatasetSpec:
    name: str
    time_unit: str
    t_scale: float
    efc_scale: float
    stress_names: tuple
    stress_lo: tuple
    stress_hi: tuple
    has_calendar: bool
    t_index: object = None  # index of temperature (deg C) in the stress vector
    soc_index: object = None  # index of the SOC used by the calendar term (SOC_mid for cycling, SOC for storage)
    life_level: object = None  # forecast set ends at the first point below this retention (ISU, SNL)
    window: tuple = ("count", 4)  # ('count', k) or ('time', W)
    param_kinds: dict = field(default_factory=dict)  # for the parametric stress map: name -> arr | log | quad | lin
    interaction_pairs: tuple = ()
    y_scale: float = 10.0
    efc_rate_kind: str = "samsung"
    min_window_points: int = 3

    @property
    def d(self):
        return len(self.stress_names)

    def norm(self, raw):
        raw = np.asarray(raw, float)
        lo, hi = np.array(self.stress_lo), np.array(self.stress_hi)
        return (raw - lo) / (hi - lo) * 2.0 - 1.0

    def denorm(self, s):
        lo, hi = np.array(self.stress_lo), np.array(self.stress_hi)
        return lo + (np.asarray(s, float) + 1.0) / 2.0 * (hi - lo)

    def efc_rate(self, raw):
        """Analytic design EFC per time unit for raw stress rows (..., d). Cycling rows only (storage = 0 via is_cyc gate)."""
        raw = np.asarray(raw, float)
        if self.efc_rate_kind == "samsung":      # per day; CC only, zero rest (pipeline efc_est): 24 * Cch*Cdch/(Cch+Cdch)
            cch, cdch = raw[..., 3], raw[..., 4]
            return 24.0 * cch * cdch / np.maximum(cch + cdch, 1e-9)
        if self.efc_rate_kind == "isu":          # per week; stress = (charge_c, discharge_c, dod_pct)
            cch, cdch, dod = raw[..., 0], raw[..., 1], raw[..., 2] / 100.0
            cyc_per_week = 168.0 / (dod / cch + dod / cdch + REST_H_ISU)
            return cyc_per_week * dod
        if self.efc_rate_kind == "snl":          # per cycle; stress = (is_LFP, is_NCA, is_NMC, temp_c, dod, charge_c, discharge_c)
            return raw[..., 4]
        raise ValueError(self.efc_rate_kind)


SAMSUNG = DatasetSpec(
    name="samsung", time_unit="day", t_scale=500.0, efc_scale=500.0,
    stress_names=("T_C", "soc_mid", "dod", "c_ch", "c_dch"),
    stress_lo=(5.0, 0.0, 0.0, 0.0, 0.0), stress_hi=(50.0, 1.0, 0.8, 1.2, 2.2),   # margins: no design value sits on the spline edge
    has_calendar=True, t_index=0, soc_index=1, window=("count", 4),
    param_kinds={"T_C": "arr", "soc_mid": "quad", "dod": "log", "c_ch": "log", "c_dch": "log"},
    interaction_pairs=(("T_C", "c_ch"), ("T_C", "soc_mid"), ("dod", "soc_mid")),
    efc_rate_kind="samsung")

# synthetic data share the Samsung stress structure and units (days, EFC)
SYNTH = DatasetSpec(**{**SAMSUNG.__dict__, "name": "synthetic"})

ISU = DatasetSpec(
    name="isu", time_unit="week", t_scale=50.0, efc_scale=1000.0,
    stress_names=("charge_c", "discharge_c", "dod_pct"),
    stress_lo=(0.0, 0.0, 0.0), stress_hi=(3.3, 3.3, 100.0),
    has_calendar=False, life_level=0.70, window=("time", 4.0),
    param_kinds={"charge_c": "log", "discharge_c": "log", "dod_pct": "log"},
    # the prereg names A5 for ISU (3.4) without listing its terms: pair choice below is the builder's, flagged in README
    interaction_pairs=(("charge_c", "discharge_c"), ("charge_c", "dod_pct"), ("discharge_c", "dod_pct")),
    efc_rate_kind="isu")

SNL = DatasetSpec(
    name="snl", time_unit="cycle", t_scale=1000.0, efc_scale=1000.0,
    stress_names=("is_LFP", "is_NCA", "is_NMC", "temp_c", "dod", "charge_c", "discharge_c"),
    stress_lo=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0), stress_hi=(1.2, 1.2, 1.2, 50.0, 1.1, 3.3, 3.3),
    has_calendar=False, life_level=0.70, window=("time", 100.0),
    param_kinds={"is_LFP": "lin", "is_NCA": "lin", "is_NMC": "lin", "temp_c": "arr", "dod": "log", "charge_c": "log", "discharge_c": "log"},
    interaction_pairs=(("temp_c", "charge_c"), ("temp_c", "dod"), ("dod", "discharge_c")),
    efc_rate_kind="snl")

SPECS = {s.name: s for s in (SAMSUNG, SYNTH, ISU, SNL)}
