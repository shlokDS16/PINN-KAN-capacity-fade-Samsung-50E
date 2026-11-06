"""D028 coder actions C1-C5: the ZYK table hash pin, tpe_seed, a10_drop_soc100_storage, the forecast-failure refusal text, and the config set they change."""
import dataclasses
import json
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.join(ROOT, "code", "prereg"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pytest

import make_confirmatory_configs as M
from pinnkan import arms as A
from pinnkan import data, run, synth, tuning, zyk
from pinnkan.data import WindowRule
from pinnkan.specs import SPECS
from test_c14_confirmatory_configs import _all, _load_dir, ITEM_F

SPEC = SPECS["synthetic"]
TABLE = os.path.join(ROOT, zyk.ZYK_TABLE_REL)


# ------------------------------------------------------------------------------------------------ C1
def _samsung_zyk_configs():
    flat = [c for g in _all().values() for c in g.values() if c["dataset"] == "samsung"] + list(_load_dir(ITEM_F).values())
    return [c for c in flat if c.get("throughput") == "zyk"]


def test_every_samsung_zyk_config_carries_the_on_disk_table_hash_and_item_f_inherits_it():
    h = data.sha256_file(TABLE)
    cfgs = _samsung_zyk_configs()
    assert len(cfgs) == 26 + 36 + 195 + 4 + 5 and all(c["zyk_table_sha256"] == h for c in cfgs)
    assert all(c["zyk_table_sha256"] == h for c in _load_dir(ITEM_F).values())
    assert all("zyk_table_sha256" not in c for c in _all()["replication"].values())              # ISU has no ZYK table


def test_validate_config_requires_a_64_hex_table_hash_with_zyk_on_samsung():
    c = _all()["primary"]["conf_samsung_B_f0_m8.json"]
    bad = {k: v for k, v in c.items() if k != "zyk_table_sha256"}
    with pytest.raises(run.ConfigError, match="zyk_table_sha256 is required"):
        run.validate_config(bad, ROOT)
    for v in ("abc", "G" * 64, "A" * 64, 5):
        with pytest.raises(run.ConfigError, match="64 lower-case hex"):
            run.validate_config({**c, "zyk_table_sha256": v}, ROOT)
    run.validate_config(c, ROOT)


def test_a_wrong_table_hash_is_refused_before_any_data_is_read(tmp_path):
    root = tmp_path / "tree"
    (root / "data" / "processed").mkdir(parents=True)
    (root / "data" / "processed" / "samsung_zyk_efc.csv").write_text("cell_id,file_idx,efc\n")
    with pytest.raises(run.ConfigError, match="zyk_table_sha256 does not match"):
        data._load_samsung(str(root), throughput="zyk", zyk_table_sha256="0" * 64)
    ok = data.sha256_file(str(root / "data" / "processed" / "samsung_zyk_efc.csv"))
    with pytest.raises(FileNotFoundError):                                                           # the hash check passed; the next step reads samsung_checkups.csv, absent here
        data._load_samsung(str(root), throughput="zyk", zyk_table_sha256=ok)
    empty = tmp_path / "none"
    (empty / "data" / "processed").mkdir(parents=True)
    with pytest.raises(run.ConfigError, match="zyk_table_sha256 does not match"):                    # an absent table with a pinned hash is a mismatch
        data._load_samsung(str(empty), throughput="zyk", zyk_table_sha256=ok)


# ------------------------------------------------------------------------------------------------ C2
def test_the_isu_full_data_analogue_is_the_unthinned_training_side_at_four_weeks():
    rep = _all()["replication"]
    assert len(rep) == 10 and not any(n.endswith("_g4.json") for n in rep)
    full = {n: c for n, c in rep.items() if n.endswith("_full.json")}
    assert len(full) == 5 and sorted(c["fold"] for c in full.values()) == [0, 1, 2, 3, 4]
    for n, c in full.items():
        assert "m" not in c and "subset" not in c and c["k"] == ["full"] and "window" not in c, n
        cfg = run.validate_config(c, ROOT)
        rule = WindowRule.for_spec(SPECS["isu"], k_cycling=None, k_storage=None, W=None, shift=0)
        assert rule.W == 4.0 and [lab for lab, _ in run._score_windows(cfg, rule, SPECS["isu"])] == ["full"]          # W = full = 4 weeks
    scarce = [c for n, c in rep.items() if n.endswith("_g1.json")]
    assert len(scarce) == 5 and all(c["m"] == 8 and c["k"] == [2] for c in scarce)


# ------------------------------------------------------------------------------------------------ C3
@pytest.fixture(scope="module")
def g0():
    S = synth.make_synthetic("G0", n_cyc_cond=16, n_sto_cond=6, reps=2, seed=3)
    return synth.split_conditions(S.cells, 0.25, 3)


def test_tpe_seed_default_is_the_outer_fold_and_a_value_replaces_only_the_sampler_seed(g0, monkeypatch):
    tr, _ = g0
    rule = WindowRule.for_spec(SPEC)
    ctx = {"backbone": "self_limiting", "steps_scale": 0.05, "rule": rule}
    assert tuning.tune("R2", tr, SPEC, rule, 0, 2, 3, ctx)["tpe_seed"] == 3                         # default: the outer fold, as before
    r = tuning.tune("R2", tr, SPEC, rule, 0, 2, 3, ctx, tpe_seed=103)
    assert r["tpe_seed"] == 103 and r["tuning_seed"] == 1003                                          # the tuning-fit seed (1000 + fold) and the inner folds do not move
    seen = []

    class Stop(Exception):
        pass

    def fake(seed):
        seen.append(seed)
        raise Stop
    monkeypatch.setattr(tuning.optuna.samplers, "TPESampler", fake)
    for kw, want in (({}, 3), ({"tpe_seed": 103}, 103)):
        with pytest.raises(Stop):
            tuning.tune("A2", tr, SPEC, rule, 2, 2, 3, ctx, **kw)
        assert seen[-1] == want


def test_validate_config_checks_tpe_seed_and_the_configs_use_100_plus_fold():
    c = _all()["primary"]["conf_samsung_B_f0_m8.json"]
    assert run.DEFAULTS["tpe_seed"] is None
    for v in (-1, 1.5, "7", True):
        with pytest.raises(run.ConfigError, match="tpe_seed"):
            run.validate_config({**c, "tpe_seed": v}, ROOT)
    run.validate_config({**c, "tpe_seed": 0}, ROOT)
    sens = _all()["sensitivity"]
    tp = {n: x for n, x in sens.items() if n.startswith("sens_tpe2")}
    assert sorted(tp) == [f"sens_tpe2_B_f{f}_g1.json" for f in range(5)]
    for n, x in tp.items():
        assert x["tpe_seed"] == 100 + x["fold"] and x["m"] == 8 and x["k"] == [2] and x["arms"] == ["A1", "A9", "A11", "A12"], n


# ------------------------------------------------------------------------------------------------ C4
def _with_soc100_storage(cells):
    """copies of two storage cells moved to SOC = 1.0 (the synthetic design has none)"""
    sto = [c for c in cells if c.kind == "storage"][:2]
    moved = [dataclasses.replace(c, cell_id=c.cell_id + "_s100", raw=np.array([c.raw[0], 1.0, 0.0, 0.0, 0.0])) for c in sto]
    return list(cells) + moved, len(moved)


def test_a10_drops_soc100_storage_cells_from_its_own_fit_only(g0):
    tr, te = g0
    tr2, n_moved = _with_soc100_storage(tr)
    rule = WindowRule.for_spec(SPEC)
    base = {"backbone": "self_limiting", "steps_scale": 0.05, "rule": rule, "a10_starts": 2}
    full = A.make_arm("A10", SPEC, A.default_hp("A10"), 0, base).fit(tr2)
    drop = A.make_arm("A10", SPEC, A.default_hp("A10"), 0, {**base, "a10_drop_soc100_storage": True}).fit(tr2)
    assert full.n_train_used - drop.n_train_used == n_moved
    assert not np.allclose(full.theta, drop.theta) or full.n_train_used != drop.n_train_used
    # without SOC = 100 % storage cells in the training set the flag changes nothing
    same = A.make_arm("A10", SPEC, A.default_hp("A10"), 0, {**base, "a10_drop_soc100_storage": True}).fit(tr)
    plain = A.make_arm("A10", SPEC, A.default_hp("A10"), 0, base).fit(tr)
    assert same.n_train_used == plain.n_train_used and np.allclose(same.theta, plain.theta)
    # the scored cells are the caller's and the other arms never read the flag
    src = open(os.path.join(ROOT, "code", "pinnkan", "arms.py"), encoding="utf8").read()
    assert len(re.findall(r'a10_drop_soc100_storage', src)) == 1 and src.index("a10_drop_soc100_storage") > src.index("class SemiArm") and src.index("a10_drop_soc100_storage") < src.index("class P3Arm")
    p = full.predict([])
    assert len(p) == len(drop.predict([])) == 0


def test_the_flag_needs_an_a10_arm_and_the_configs_exist_for_g1_and_g4():
    c = _all()["primary"]["conf_samsung_B_f0_m8.json"]
    with pytest.raises(run.ConfigError, match="a10_drop_soc100_storage"):
        run.validate_config({**c, "a10_drop_soc100_storage": True, "arms": ["A1", "A9"]}, ROOT)
    assert run.DEFAULTS["a10_drop_soc100_storage"] is False
    sens = _all()["sensitivity"]
    a10 = {n: x for n, x in sens.items() if n.startswith("sens_a10nosoc100")}
    assert sorted(a10) == sorted(f"sens_a10nosoc100_B_f{f}_{g}.json" for f in range(5) for g in ("g1", "g4"))
    assert all(x["a10_drop_soc100_storage"] is True and x["arms"] == ["A1", "A10", "A10P"] for x in a10.values())


# ------------------------------------------------------------------------------------------------ C5 and the struck rows
def test_forecast_failure_stays_refused_and_says_struck_and_no_struck_row_has_a_config():
    c = _all()["primary"]["conf_samsung_B_f0_m8.json"]
    with pytest.raises(run.NotBuiltError, match=r"Struck \(D028\)"):
        run.validate_config({**c, "forecast_failure": True}, ROOT)
    names = {n for g in _all().values() for n in g}
    assert not any("firstcu" in n or "forecastfail" in n or "hcal" in n or "snl" in n.lower() or "a14" in n.lower() for n in names)
    flat = [x for g in _all().values() for x in g.values()]
    assert not any(x["dataset"] == "snl" or "A14" in x["arms"] or x.get("forecast_failure") for x in flat)
