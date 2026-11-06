"""C14 / C14b: the pre-registered run configurations (runs/prereg/confirmatory_configs/** and the five item (f) configs): reproducible from code/prereg/make_confirmatory_configs.py, every config
passes run.validate_config (the ConfigError checks of the runner, no data loaded), the grid configs score the cells {0, 2, full} (review D027 C1), item (f) differs from the g1 config only as
D026 allows, and the downgrade-row, sensitivity, exploratory and replication groups follow PREREG 9.8 / 9.9."""
import dataclasses
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
from pinnkan.data import WindowRule
from pinnkan.specs import SPECS

CONF = M.CONF_DIR
ITEM_F = M.ITEM_F_DIR


def _load_dir(d):
    return {f: run.load_config(os.path.join(d, f)) for f in sorted(os.listdir(d)) if f.endswith(".json") and f != "MANIFEST.json"}


def _all():
    """{group: {file: config}} read from disk"""
    return {g: _load_dir(os.path.join(CONF, sub) if sub else CONF) for g, sub in M.GROUP_DIRS.items()}


def _flat():
    return {c["run_id"]: c for d in _all().values() for c in d.values()}


def labels(cfg):
    """the k cells _score_windows yields for a config, without loading data (the rule of run._run)"""
    c = run.validate_config(cfg, ROOT)
    spec = SPECS[c["dataset"]]
    wk = c["window"]
    rule = WindowRule.for_spec(spec, k_cycling=wk.get("k_cycling"), k_storage=wk.get("k_storage"), W=wk.get("W"), shift=wk.get("shift", 0))
    rule_test = dataclasses.replace(rule, min_fc_points=int(c["min_fc_points"]))
    return [lab for lab, _ in run._score_windows(c, rule_test, spec)]


def test_the_files_on_disk_are_exactly_what_the_script_produces():
    assert M.main(["--check"]) == 0
    flat = {k: v for g in _all().values() for k, v in g.items()}
    assert len(flat) == len(M.confirmatory_configs()) and set(_load_dir(ITEM_F)) == set(M.item_f_configs())


def test_every_config_passes_the_runner_validation_without_loading_data():
    n = 0
    for c in list(_flat().values()) + list(_load_dir(ITEM_F).values()):
        cfg = run.validate_config(c, ROOT)                       # raises ConfigError on any static violation
        assert cfg["design"] == "R2" and cfg["mode"] in ("confirmatory", "inner"), c["run_id"]
        if cfg["dataset"] == "samsung":
            assert cfg["window"] in ({"k_cycling": 4, "k_storage": 2}, {"k_cycling": 3, "k_storage": 2}, {"k_cycling": 6, "k_storage": 2}) and cfg["throughput"] == "zyk", c["run_id"]
        n += 1
    assert n == 26 + 36 + 180 + 4 + 10 + 5


def test_validation_is_not_vacuous():
    c = _all()["primary"]["conf_samsung_B_f0_m32.json"]
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
        run.validate_config({**_all()["primary"]["conf_samsung_B_f0_m8.json"], "arms": ["A1", "A5"]}, ROOT)
    with pytest.raises(run.ConfigError, match="law_overrides"):
        run.validate_config({**c, "law_overrides": {"Y0": 2.0}}, ROOT)                 # a sensitivity override with the full arm list is refused
    with pytest.raises(run.NotBuiltError):
        run.validate_config({**c, "forecast_failure": True}, ROOT)


def test_every_test_b_grid_config_scores_the_cells_0_2_full_and_item_f_inherits_k_grid():
    prim = _all()["primary"]
    grid = {n: c for n, c in prim.items() if c["test"] == "B" and not c.get("permute_stress")}
    assert len(grid) == 15
    for n, c in grid.items():
        assert c["k"] == "grid", n
        assert labels(c) == ["0", "2", "full"], n                                      # g1 = (8, 2), the k = 0 cells and k_full are all scored
    for n, c in _load_dir(ITEM_F).items():
        assert c["k"] == "grid", n
    for n, c in prim.items():
        if c["test"] in ("C", "S2") or c.get("permute_stress"):
            assert "k" not in c and labels(c) == [None], n                            # the single primary window (k_full for cycling, k_sto for storage)


def test_the_set_has_one_config_per_outer_fold_and_arm_group_with_the_arms_of_the_prereg():
    conf = _all()["primary"]
    assert len(conf) == 26 and len({c["run_id"] for c in conf.values()}) == 26
    grid = {(c["fold"], c["m"]): c for c in conf.values() if c["test"] == "B" and not c.get("permute_stress")}
    assert set(grid) == {(f, m) for f in range(5) for m in (8, 16, 32)}
    common = {"A1", "A2", "A4", "A9", "A10", "A10P", "A11", "A12", "A12R", "R1", "R2"}
    for (f, m), c in grid.items():
        extra = {8: {"A13", "A15", "G15"}, 16: set(), 32: {"A5", "A13", "A15", "G15"}}[m]
        assert set(c["arms"]) == common | extra and len(c["arms"]) == len(set(c["arms"])), (f, m)
    nc2 = [c for c in conf.values() if c.get("permute_stress")]
    assert {tuple(c["arms"]) for c in nc2} == {("A1",)} and sorted(c["fold"] for c in nc2) == [0, 1, 2, 3, 4] and {c["m"] for c in nc2} == {32}
    assert [c["fold"] for c in conf.values() if c["test"] == "C"] == [0] and sorted(c["fold"] for c in conf.values() if c["test"] == "S2") == [0, 1, 2, 3, 4]
    assert all(c["test"] != "C" or ("m" not in c and set(c["arms"]) == {"A1", "A9", "A10", "A10P", "A11", "A12"}) for c in conf.values())
    assert all(c["test"] != "S2" or ("m" not in c and set(c["arms"]) == {"A1", "A9", "A10", "A10P"}) for c in conf.values())
    split = json.load(open(os.path.join(ROOT, "runs", "prereg", "samsung_splits_v2.json")))
    for t in ("B", "C", "S2"):
        assert sorted({c["fold"] for c in conf.values() if c["test"] == t}) == sorted(int(f) for f in split[t]["folds"]), t
    assert sorted(c["fold"] for c in _all()["exploratory"].values() if c["test"] == "A") == sorted(int(f) for f in split["A"]["folds"])


def test_every_config_has_the_fixed_confirmatory_keys_and_the_pinned_hashes():
    inv, ext = inversion.config_sha256(), extraction_audit.thresholds_sha256()
    rule = extraction_audit.sha256_file(os.path.join(ROOT, "debates", "D022_datasets_kan", "calibration_rule_v2.md"))
    for rid, c in _flat().items():
        assert c["mode"] == "confirmatory" and c["steps_scale"] == 1.0 and not c.get("overwrite") and not c.get("auto_budget") and c["n_trials"] == 20, rid
        assert c["inversion_config_sha256"] == inv and set(c["arms"]) <= set(A.ARMS) and not set(c["arms"]) & set(A.OUT_OF_SCOPE_ARMS), rid
        assert c["backbone"] == ("self_limiting" if rid.startswith("sens_selflim") else "tournament"), rid
        if {"A15", "G15"} & set(c["arms"]):
            assert c["extraction_audit_sha256"] == ext and c["calibration_rule_sha256"] == rule, rid
        else:
            assert "extraction_audit_sha256" not in c and "calibration_rule_sha256" not in c, rid
        assert "mc_seed_root" not in c and "seeds" not in c


def test_downgrade_rows_follow_prereg_9_8_cells_and_arms():
    rows = _all()["rows"]
    assert len(rows) == 36
    g1_arms, g4_arms = {"A1", "A2", "A9", "A10", "A10P", "A11", "A12", "A13"}, {"A1", "A2", "A9", "A10", "A10P", "A11", "A12", "A15", "G15"}
    for tag, key in (("labind", "lab_indicator"), ("retain", "retain_all")):
        sel = {n: c for n, c in rows.items() if n.startswith(f"row_{tag}_B")}
        assert len(sel) == 10
        for n, c in sel.items():
            g1 = n.endswith("_g1.json")
            assert c[key] is True and c["m"] == (8 if g1 else 32) and c["k"] == ([2] if g1 else ["full"]) and set(c["arms"]) == (g1_arms if g1 else g4_arms), n
            assert labels(c) == (["2"] if g1 else ["full"]), n
        assert sorted({c["fold"] for c in sel.values()}) == [0, 1, 2, 3, 4]
    rs = {n: c for n, c in rows.items() if n.startswith("row_randsub")}
    assert len(rs) == 15 and {(c["fold"], c["subset_draw"]) for c in rs.values()} == {(f, d) for f in range(5) for d in range(3)}
    assert all(c["subset"] == "random" and c["m"] == 8 and c["k"] == [2] and set(c["arms"]) == {"A1", "A9", "A11", "A12"} for c in rs.values())
    lc = rows["row_labind_C_f0.json"]
    assert lc["test"] == "C" and lc["lab_indicator"] is True and set(lc["arms"]) == {"A1", "A9", "A10", "A10P", "A11", "A12"}


def test_sensitivity_exploratory_and_replication_groups():
    allg = _all()
    sens = allg["sensitivity"]
    assert len(sens) == 180
    assert sum(n.endswith("_g1.json") for n in sens) == 85 and sum(n.endswith("_g4.json") for n in sens) == 95
    for n, c in sens.items():
        if n.startswith("sens_kfull"):
            assert c["window"]["k_cycling"] == (3 if "m1" in n else 6) and c["m"] == 32 and c["k"] == ["full"], n
        assert labels(c) == (["2"] if c["m"] == 8 else ["full"]), n
    assert sens["sens_blinded_B_f0_g1.json"]["score_blinded_cells"] is True and sens["sens_at_B_f1_g4.json"]["include_at"] is True
    assert sens["sens_clip10_B_f0_g1.json"]["pinn"] == {"clip": 10} and sens["sens_warm06_B_f0_g4.json"]["pinn"] == {"warmup": 0.6}
    assert sens["sens_deltatotal_B_f0_g1.json"]["law_overrides"] == {"delta_scope": "total"} and sens["sens_deltatotal_B_f0_g1.json"]["arms"] == ["A1"]
    a2 = {n: c for n, c in sens.items() if n.startswith("sens_a2_")}
    assert len(a2) == 60 and all(c["arms"] == ["A2"] and len(c["law_overrides"]) == 1 for c in a2.values())
    assert {tuple(sorted(c["law_overrides"].items())) for c in a2.values()} == {(("Y0", 0.5),), (("Y0", 2.0),), (("gamma", 0.15),), (("gamma", 0.6),), (("tau", 0.075),), (("tau", 0.3),)}
    ex = allg["exploratory"]
    assert sorted(ex) == ["expl_samsung_A_f0.json", "expl_samsung_A_f1.json", "expl_samsung_A_f2.json", "expl_samsung_S3_f0.json"]
    assert all(set(c["arms"]) == {"A1", "A2", "A9"} for n, c in ex.items() if "_A_" in n) and ex["expl_samsung_S3_f0.json"]["test"] == "S3"
    rep = allg["replication"]
    assert len(rep) == 10 and all(c["dataset"] == "isu" and c["test"] == "B" and "window" not in c for c in rep.values())
    for n, c in rep.items():
        assert labels(c) == (["2"] if c["m"] == 8 else ["full"]), n
    for g in ("rows", "sensitivity"):
        for n, c in allg[g].items():
            assert c["test"] in ("B", "C"), n


def test_config_hashes_are_distinct_and_match_the_manifest():
    conf, item_f = _flat(), _load_dir(ITEM_F)
    allc = list(conf.values()) + list(item_f.values())
    hashes = [guard.canonical_config_hash({**run.DEFAULTS, **c}) for c in allc]
    assert len(set(hashes)) == len(hashes) == 261 and len({c["run_id"] for c in allc}) == 261
    man = json.load(open(os.path.join(CONF, "MANIFEST.json")))
    by_id = {r["run_id"]: r for r in man["files"]}
    for c in allc:
        assert by_id[c["run_id"]]["config_sha256"] == guard.canonical_config_hash({**run.DEFAULTS, **c})
    assert man["n_trials"] == 20 and man["counts"] == {"primary": 26, "rows": 36, "sensitivity": 180, "exploratory": 4, "replication": 10, "item_f": 5}


def test_item_f_configs_are_the_g1_config_with_only_the_d026_differences():
    conf, item_f = _all()["primary"], _load_dir(ITEM_F)
    assert len(item_f) == 5
    for name, c in item_f.items():
        f = c["fold"]
        g1 = conf[f"conf_samsung_B_f{f}_m8.json"]
        assert (c["dataset"], c["test"], c["mode"], c["m"], c["subset"]) == ("samsung", "B", "inner", 8, "maxmin") and c["arms"] == ["A1", "A9", "A11", "A12"]
        assert c["diagnostics"] is False and c["refit_timing"] is False
        differing = {k for k in set(c) | set(g1) if c.get(k) != g1.get(k)}
        assert differing == {"run_id", "mode", "arms", "diagnostics", "refit_timing"}, (name, differing)
        assert c["window"] == g1["window"] and c["backbone"] == g1["backbone"] and c["n_trials"] == g1["n_trials"] and c["k"] == g1["k"] == "grid"
