"""C14: the confirmatory configuration set (runs/prereg/confirmatory_configs/) and the five item (f) configs: reproducible from code/prereg/make_confirmatory_configs.py, every config passes
run.validate_config (the ConfigError checks of the runner, no data loaded), item (f) differs from the g1 config only as D026 allows."""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.join(ROOT, "code", "prereg"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import pytest

import make_confirmatory_configs as M
from pinnkan import arms as A
from pinnkan import extraction_audit, guard, inversion, run

CONF = M.CONF_DIR
ITEM_F = M.ITEM_F_DIR


def _load(d):
    return {f: run.load_config(os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.endswith(".json") and f != "MANIFEST.json"}


def test_the_files_on_disk_are_exactly_what_the_script_produces():
    assert M.main(["--check"]) == 0
    assert set(_load(CONF)) == set(M.confirmatory_configs()) and set(_load(ITEM_F)) == set(M.item_f_configs())


def test_every_config_passes_the_runner_validation_without_loading_data():
    for d in (CONF, ITEM_F):
        for name, c in _load(d).items():
            cfg = run.validate_config(c, ROOT)                       # raises ConfigError on any static violation
            assert cfg["dataset"] == "samsung" and cfg["window"] == {"k_cycling": 4, "k_storage": 2}, name


def test_validation_is_not_vacuous():
    c = _load(CONF)["conf_samsung_B_f0_m32.json"]
    for key, needle in (("extraction_audit_sha256", "required"), ("calibration_rule_sha256", "required"), ("inversion_config_sha256", "required"), ("window", "window.k_cycling")):
        bad = {k: v for k, v in c.items() if k != key}
        with pytest.raises(run.ConfigError, match=needle):
            run.validate_config(bad, ROOT)
    with pytest.raises(run.ConfigError, match="does not match"):
        run.validate_config({**c, "extraction_audit_sha256": "0" * 64}, ROOT)
    with pytest.raises(run.ConfigError, match="steps_scale"):
        run.validate_config({**c, "steps_scale": 0.5}, ROOT)
    with pytest.raises(run.ConfigError, match="overwrite"):
        run.validate_config({**c, "overwrite": True}, ROOT)
    with pytest.raises(run.ConfigError, match="A5"):
        run.validate_config({**_load(CONF)["conf_samsung_B_f0_m8.json"], "arms": ["A1", "A5"]}, ROOT)


def test_the_set_has_one_config_per_outer_fold_and_arm_group_with_the_arms_of_the_prereg():
    conf = _load(CONF)
    assert len(conf) == 26 and len({c["run_id"] for c in conf.values()}) == 26
    grid = {(c["fold"], c["m"]): c for c in conf.values() if c["test"] == "B" and not c.get("permute_stress")}
    assert set(grid) == {(f, m) for f in range(5) for m in (8, 16, 32)}
    common = {"A1", "A2", "A4", "A9", "A10", "A10P", "A11", "A12", "A12R", "R1", "R2"}
    for (f, m), c in grid.items():
        extra = {8: {"A13", "A15", "G15"}, 16: set(), 32: {"A5", "A13", "A15", "G15"}}[m]
        assert set(c["arms"]) == common | extra and len(c["arms"]) == len(set(c["arms"])), (f, m)
    assert {tuple(c["arms"]) for c in conf.values() if c.get("permute_stress")} == {("A1",)}
    nc2 = [c for c in conf.values() if c.get("permute_stress")]
    assert sorted(c["fold"] for c in nc2) == [0, 1, 2, 3, 4] and {c["m"] for c in nc2} == {32} and {c["test"] for c in nc2} == {"B"}
    assert [c["fold"] for c in conf.values() if c["test"] == "C"] == [0] and sorted(c["fold"] for c in conf.values() if c["test"] == "S2") == [0, 1, 2, 3, 4]
    assert all(c["test"] != "C" or ("m" not in c and set(c["arms"]) == {"A1", "A9", "A10", "A10P", "A11", "A12"}) for c in conf.values())
    assert all(c["test"] != "S2" or ("m" not in c and set(c["arms"]) == {"A1", "A9", "A10", "A10P"}) for c in conf.values())
    split = json.load(open(os.path.join(ROOT, "runs", "prereg", "samsung_splits_v2.json")))
    for t in ("B", "C", "S2"):
        assert sorted({c["fold"] for c in conf.values() if c["test"] == t}) == sorted(int(f) for f in split[t]["folds"]), t


def test_every_config_has_the_fixed_confirmatory_keys_and_the_pinned_hashes():
    inv, ext = inversion.config_sha256(), extraction_audit.thresholds_sha256()
    rule = extraction_audit.sha256_file(os.path.join(ROOT, "debates", "D022_datasets_kan", "calibration_rule_v2.md"))
    for name, c in _load(CONF).items():
        assert c["mode"] == "confirmatory" and c["dataset"] == "samsung" and c["steps_scale"] == 1.0 and not c.get("overwrite") and not c.get("auto_budget"), name
        assert c["window"] == {"k_cycling": 4, "k_storage": 2} and c["n_trials"] == 20 and c["backbone"] == "tournament" and c["inversion_config_sha256"] == inv, name
        assert set(c["arms"]) <= set(A.ARMS) and not set(c["arms"]) & set(A.OUT_OF_SCOPE_ARMS), name
        if {"A15", "G15"} & set(c["arms"]):
            assert c["extraction_audit_sha256"] == ext and c["calibration_rule_sha256"] == rule, name
        else:
            assert "extraction_audit_sha256" not in c and "calibration_rule_sha256" not in c, name
        assert "seeds" not in c and "m" not in c or c["subset"] == "maxmin"
    assert "mc_seed_root" not in c                                                                          # the MC seed root is a code constant (NEGCONTROL ruling), not a config value


def test_config_hashes_are_distinct_and_match_the_manifest():
    conf, item_f = _load(CONF), _load(ITEM_F)
    hashes = [guard.canonical_config_hash({**run.DEFAULTS, **c}) for c in list(conf.values()) + list(item_f.values())]
    assert len(set(hashes)) == len(hashes) == 31
    man = json.load(open(os.path.join(CONF, "MANIFEST.json")))
    by_id = {r["run_id"]: r for r in man["files"]}
    for c in list(conf.values()) + list(item_f.values()):
        assert by_id[c["run_id"]]["config_sha256"] == guard.canonical_config_hash({**run.DEFAULTS, **c})
    assert man["n_trials"] == 20 and sum(r["kind"] == "item_f" for r in man["files"]) == 5


def test_item_f_configs_are_the_g1_config_with_only_the_d026_differences():
    conf, item_f = _load(CONF), _load(ITEM_F)
    assert len(item_f) == 5
    for name, c in item_f.items():
        f = c["fold"]
        g1 = conf[f"conf_samsung_B_f{f}_m8.json"]
        assert (c["dataset"], c["test"], c["mode"], c["m"], c["subset"]) == ("samsung", "B", "inner", 8, "maxmin") and c["arms"] == ["A1", "A9", "A11", "A12"]
        assert c["diagnostics"] is False and c["refit_timing"] is False
        differing = {k for k in set(c) | set(g1) if c.get(k) != g1.get(k)}
        assert differing == {"run_id", "mode", "arms", "diagnostics", "refit_timing"}, (name, differing)
        assert c["window"] == g1["window"] and c["backbone"] == g1["backbone"] and c["n_trials"] == g1["n_trials"]
