"""PREREG_v4 9.9 (u): the descriptive C-rate ablation row (config option `neutralise_stress`, the group `crate_ablation`, the statistics row `crate_ablation`). Synthetic data only.
    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_crate_ablation.py -q"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.join(ROOT, "code", "prereg"))
sys.path.insert(0, os.path.dirname(__file__))
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["OMP_NUM_THREADS"] = "1"

import numpy as np
import pytest

import make_confirmatory_configs as M
from pinnkan import extraction_audit as X
from pinnkan import guard, metrics, run, stats_gaps as sg, stats_step as ss
from pinnkan import stats_v4 as v4
from pinnkan.data import Cell
from pinnkan.specs import SAMSUNG
from test_pk_stats_gaps_g1_g8 import CONDS, FOLD, G4, RULE, _dump, _item_f, make_grid, make_negative, strip_contrasts

CONF = os.path.join(ROOT, "runs", "prereg", "confirmatory_configs")


# ------------------------------------------------------------------------------------------------ the neutralisation
def _cell(cid, kind, cond, raw, n=4):
    return Cell(cell_id=cid, dataset="samsung", kind=kind, cond=cond, raw=np.array(raw, float), t=np.arange(n, dtype=float), ret=np.linspace(1, 0.9, n), efc=np.arange(n) * 3.0,
                fc_ok=np.ones(n, bool), lab="HM", stage="1")


def _sets():
    # training: four cycling conditions (two cells each) with C_ch 0.2 0.4 0.8 1.2 and C_dch 1 2 3 4, one storage condition; test: two conditions with other C-rates
    train = []
    for i, (cc, cd) in enumerate(zip((0.2, 0.4, 0.8, 1.2), (1.0, 2.0, 3.0, 4.0))):
        for j in range(2):
            train.append(_cell(f"t{i}{j}", "cycling", f"c{i}", [23.0, 0.5, 0.3, cc, cd]))
    train.append(_cell("s0", "storage", "s", [23.0, 0.5, 0.0, 0.0, 0.0]))
    test = [_cell("x0", "cycling", "x0", [45.0, 0.6, 0.4, 2.0, 5.0]), _cell("x1", "cycling", "x1", [45.0, 0.7, 0.2, 9.0, 9.0])]
    return train, test


def test_neutralisation_uses_the_training_median_once_and_changes_nothing_else():
    train, test = _sets()
    tr, te, rec = metrics.neutralise_stress(train, test, SAMSUNG, ["C_ch", "C_dch"])
    # medians over the four distinct training CONDITIONS (not the eight cells, not the test cells): C_ch (0.4 + 0.8) / 2 = 0.6, C_dch 2.5
    assert rec["value"] == {"c_ch": pytest.approx(0.6), "c_dch": pytest.approx(2.5)} and rec["n_training_conditions"] == 4 and rec["components"] == ["c_ch", "c_dch"]
    for c in (c for c in tr + te if c.kind == "cycling"):
        assert c.raw[3] == pytest.approx(0.6) and c.raw[4] == pytest.approx(2.5)
    for o, n in zip(train + test, tr + te):                                  # everything else is untouched; the inputs are not mutated
        assert o is not n or o.kind == "storage"
        assert np.array_equal(o.t, n.t) and np.array_equal(o.ret, n.ret) and np.array_equal(o.efc, n.efc) and np.array_equal(o.fc_ok, n.fc_ok) and (o.lab, o.stage, o.cond, o.cell_id) == (n.lab, n.stage, n.cond, n.cell_id)
        if o.kind == "cycling":
            assert np.array_equal(o.raw[:3], n.raw[:3]) and n.meta["stress_neutralised"] == ["c_ch", "c_dch"]
    assert test[0].raw[3] == 2.0 and train[0].raw[3] == 0.2                  # originals unchanged
    assert tr[-1] is train[-1] and tr[-1].raw.tolist() == [23.0, 0.5, 0.0, 0.0, 0.0]          # storage cells are left as they are


def test_the_median_is_a_training_side_quantity_only():
    train, test = _sets()
    a = metrics.neutralise_stress(train, test, SAMSUNG, ["C_ch"])[2]["value"]
    b = metrics.neutralise_stress(train, [_cell("y", "cycling", "y", [45.0, 0.6, 0.4, 100.0, 100.0])], SAMSUNG, ["C_ch"])[2]["value"]
    assert a == b == {"c_ch": pytest.approx(0.6)}
    tr2, te2, rec = metrics.neutralise_stress(train, None, SAMSUNG, ["C_dch"])
    assert te2 is None and tr2[0].raw[3] == 0.2 and tr2[0].raw[4] == pytest.approx(2.5)                # only the named component moves


def test_unknown_repeated_and_empty_components_and_the_permute_conflict_are_refused():
    for bad in (["C_rate"], ["C_ch", "c_ch"], [], "C_ch", [3]):
        with pytest.raises(ValueError):
            metrics.resolve_neutralise(bad, SAMSUNG)
    assert metrics.resolve_neutralise(["C_ch", "C_dch"], SAMSUNG) == [3, 4] and metrics.resolve_neutralise(["dod"], SAMSUNG) == [2]
    base = json.load(open(os.path.join(CONF, "crate_ablation", "conf_samsung_B_f0_m32_crate.json")))
    assert run.validate_config(base, ROOT)["neutralise_stress"] == ["C_ch", "C_dch"]
    for patch, msg in (({"permute_stress": True}, "cannot be combined with permute_stress"), ({"neutralise_stress": ["C_x"]}, "unknown stress component"), ({"neutralise_stress": ["C_ch", "C_ch"]}, "twice")):
        with pytest.raises(run.ConfigError, match=msg):
            run.validate_config({**base, **patch}, ROOT)


def test_the_real_run_writer_applies_it_after_the_build_and_records_it(tmp_path):
    import torch
    torch.set_num_threads(1)
    cfg = {"design": "V3_legacy", "dataset": "synthetic", "mode": "confirmatory", "n_trials": 1, "inner_k": 2, "steps_scale": 0.04, "seeds": [0, 1], "backbone": "self_limiting", "arms": ["A1"],
           "synthetic": {"kind": "G2", "n_cyc_cond": 16, "n_sto_cond": 8, "reps": 2, "seed": 7}, "test": "B"}
    run.run({**cfg, "run_id": "N", "neutralise_stress": ["C_ch", "C_dch"]}, runs_dir=str(tmp_path))
    run.run({**cfg, "run_id": "P"}, runs_dir=str(tmp_path))
    n = json.load(open(tmp_path / "N" / "neutralise_stress.json"))
    sp = json.load(open(tmp_path / "N" / "split.json"))
    assert sp["neutralise_stress"] == n and n["components"] == ["c_ch", "c_dch"] and set(n["value"]) == {"c_ch", "c_dch"} and not (tmp_path / "P" / "neutralise_stress.json").exists()
    assert json.load(open(tmp_path / "N" / "config.json"))["neutralise_stress"] == ["C_ch", "C_dch"] and "neutralise_stress" not in json.load(open(tmp_path / "P" / "config.json"))
    sn, sq = json.load(open(tmp_path / "N" / "condition_scores.json"))["A1"], json.load(open(tmp_path / "P" / "condition_scores.json"))["A1"]
    assert set(sn) == set(sq) and any(abs(sn[c] - sq[c]) > 1e-9 for c in sq)           # the ablation changes the model, the conditions scored are the same
    with pytest.raises(run.ConfigError, match="cannot be combined"):
        run.run({**cfg, "run_id": "Q", "neutralise_stress": ["C_ch"], "permute_stress": True}, runs_dir=str(tmp_path))


# ------------------------------------------------------------------------------------------------ the configs and the hashes
def test_the_key_is_not_in_defaults_and_every_pre_existing_config_hash_is_unchanged():
    assert "neutralise_stress" not in run.DEFAULTS
    pinned = json.load(open(os.path.join(ROOT, "code", "tests", "fixtures", "config_hashes_a46d7b8.json")))["hashes"]
    assert len(pinned) == 276
    man = json.load(open(os.path.join(CONF, "MANIFEST.json")))
    by_id = {r["run_id"]: r for r in man["files"]}
    assert len(by_id) == 281 and man["counts"]["crate_ablation"] == 5
    for rid, h in pinned.items():
        assert by_id[rid]["config_sha256"] == h, rid                                  # the MANIFEST row
        path = os.path.join(CONF if by_id[rid]["group"] != "item_f" else os.path.join(ROOT, "runs", "item_f", "configs"), *by_id[rid]["file"].split("/"))
        assert guard.canonical_config_hash({**run.DEFAULTS, **json.load(open(path, encoding="utf8"))}) == h, rid        # recomputed from the file on disk
    assert not any("neutralise_stress" in json.load(open(os.path.join(CONF, *r["file"].split("/")), encoding="utf8"))
                   for r in man["files"] if r["group"] not in ("crate_ablation", "item_f"))


def test_the_five_crate_configs_are_the_g4_config_with_one_extra_key_and_are_pinned_by_the_freeze_list():
    conf = M.confirmatory_configs()
    crate = {k: v for k, v in conf.items() if k.startswith("crate_ablation/")}
    assert sorted(v["fold"] for v in crate.values()) == [0, 1, 2, 3, 4]
    nc2 = {c["fold"]: c for c in M.primary_configs().values() if c.get("permute_stress")}
    prim = {c["fold"]: c for c in M.primary_configs().values() if c["test"] == "B" and c.get("m") == 32 and c.get("k") == "grid"}
    for c in crate.values():
        assert c["run_id"] == f"conf_samsung_B_f{c['fold']}_m32_crate" and c["arms"] == ["A1"] and c["m"] == 32 and c["neutralise_stress"] == ["C_ch", "C_dch"] and c["mode"] == "confirmatory"
        ref = dict(nc2[c["fold"]])
        ref.pop("permute_stress")
        ref.update(run_id=c["run_id"], neutralise_stress=["C_ch", "C_dch"])
        assert c == ref                                                               # identical to the NC-2 / g4 single-window config (same N = 40, tournament, zyk, inversion pins) except the key
        for k in ("n_trials", "backbone", "throughput", "zyk_table_sha256", "inversion_config_sha256", "window", "subset", "steps_scale"):
            assert c[k] == prim[c["fold"]][k], k
    paths = M.freeze_config_paths()
    assert len(paths) == 271 + 5 and sum("crate_ablation" in p for p in paths) == 5
    hashes = {guard.canonical_config_hash({**run.DEFAULTS, **json.load(open(p, encoding="utf8"))}) for p in paths}
    man = json.load(open(os.path.join(CONF, "MANIFEST.json")))
    assert {r["config_sha256"] for r in man["files"] if r["group"] == "crate_ablation"} <= hashes and len(hashes) == 276


def test_the_files_on_disk_are_what_the_generator_produces():
    assert M.main(["--check"]) == 0


# ------------------------------------------------------------------------------------------------ the statistics row
def _pinned():
    man = json.load(open(os.path.join(CONF, "MANIFEST.json")))
    return {r["run_id"]: r["config_sha256"] for r in man["files"] if r["group"] == "crate_ablation"}


def make_crate(tmp, store_dirs, shift=0.25, noise=0.05, seed=9):
    """five neutralised runs (A1 only) at g4 whose config.json carries the pinned config hash of their fold: S_A1,crate = S_A1,real * exp(shift + noise)"""
    dirs = make_negative(tmp, store_dirs, shift=shift, noise=noise, seed=seed)
    pin = _pinned()
    for d in dirs:
        cf = json.load(open(os.path.join(d, "config.json")))
        cf.pop("permute_stress")
        cf["neutralise_stress"] = ["C_ch", "C_dch"]
        cf["config_sha256"] = pin[f"conf_samsung_B_f{cf['fold']}_m32_crate"]
        _dump(cf, os.path.join(d, "config.json"))
    return dirs


@pytest.fixture(scope="module")
def grid(tmp_path_factory):
    tmp = str(tmp_path_factory.mktemp("crate"))
    os.makedirs(tmp + "/g")
    dirs = make_grid(tmp + "/g")
    fdir, sha = _item_f(tmp, dirs)
    os.makedirs(tmp + "/c1")
    os.makedirs(tmp + "/c0")
    return dict(tmp=tmp, dirs=dirs, fdir=fdir, sha=sha, neg=make_negative(tmp, dirs), crate=make_crate(tmp + "/c1", dirs), crate0=make_crate(tmp + "/c0", dirs, shift=0.0, noise=0.1))


def _stores(L):
    n = len(L)
    conds = CONDS[:n]
    real = v4.Store({G4: {"A1": {c: 2.0 for c in conds}}}, {c: "HM" for c in conds}, FOLD)
    cr = v4.Store({G4: {"A1": {c: 2.0 * float(np.exp(l)) for c, l in zip(conds, L)}}}, {c: "HM" for c in conds}, FOLD)
    return real, cr


def test_the_row_is_the_unadjusted_median_interval_the_mean_pp_with_bca_and_the_share():
    L = np.array([0.4] * 30 + [-0.2] * 10) * np.linspace(0.8, 1.2, 40)
    r = sg.crate_row(*_stores(L), RULE)
    lo, hi, rank, cov = RULE.interval(L, 0.05)
    assert r["status"] == "computed" and r["n"] == 40 and r["median_L"] == pytest.approx(float(np.median(L))) and r["median_ci"] == [lo, hi] and r["interval_rank"] == rank == 11 and r["interval_coverage"] == pytest.approx(cov)
    d = 2.0 * (np.exp(L) - 1.0)
    assert r["mean_pp_difference"] == pytest.approx(float(d.mean())) and len(r["mean_pp_ci"]) == 2 and r["n_L_positive"] == 30 and r["share_L_positive"] == pytest.approx(0.75)
    assert "9.7" in r["interval_type"] and "unadjusted" in r["interval_type"]
    assert not any(k in r for k in ("p", "p_value", "tier", "rejected", "level", "p_one_sided"))                 # no p-value, no tier
    X.check_generated_sentences(r, "crate")                                                                       # the fixed sentences pass the wording check


def _prereg_sentences():
    import re
    text = open(os.path.join(ROOT, "runs", "prereg", "PREREG_v4.md"), encoding="utf8").read()
    seg = text[text.index("(u) *C-rate ablation"):]
    return re.findall(r"'(Setting both[^']*)'", seg)


def test_the_three_fixed_sentences_are_the_prereg_text_verbatim():
    pre = _prereg_sentences()
    assert len(pre) == 3 and [sg.CRATE_SENTENCES[k] for k in ("raised", "lowered", "not clearly raised")] == pre
    assert all(x.endswith("the C-rate inputs may also carry laboratory and stage identity.") and "[x]" in x and "[a, b]" in x for x in pre)
    assert "which is consistent with the learned C-rate dependence contributing to accuracy" in pre[0] and "did not clearly raise the median condition error at g4 (the interval includes a ratio of 1;" in pre[2]


def test_the_sentence_is_chosen_only_by_the_interval_and_filled_from_it():
    # the interval is [L(11), L(30)]: with 30 positive conditions L(11) > 0 -> raised; with 29 L(11) <= 0 -> not clearly raised; upper bound < 0 -> lowered
    pre = _prereg_sentences()
    for k, key in ((30, "raised"), (29, "not clearly raised"), (40, "raised"), (0, "lowered"), (20, "not clearly raised")):
        L = np.array([0.3] * k + [-0.3] * (40 - k)) + np.linspace(0, 1e-3, 40)
        r = sg.crate_row(*_stores(L), RULE)
        lo, hi = r["median_ci"]
        assert r["sentence_key"] == key and ((lo > 0) if key == "raised" else (hi < 0) if key == "lowered" else (lo <= 0 <= hi)), k
        x, a, b = np.exp(r["median_L"]), np.exp(lo), np.exp(hi)
        expect = pre[("raised", "lowered", "not clearly raised").index(key)].replace("[x]", f"{x:.2f}").replace("[a, b]", f"[{a:.2f}, {b:.2f}]")
        assert r["sentence_full"] == expect and "[x]" not in r["sentence_full"] and "sentence" not in r, k
    # lowered: all conditions clearly negative
    r = sg.crate_row(*_stores(np.linspace(-0.5, -0.1, 40)), RULE)
    assert r["sentence_key"] == "lowered" and r["median_ci"][1] < 0 and r["sentence_full"].startswith("Setting both C-rate inputs to their training median lowered the median condition error at g4 (median ratio 0.")
    # a degenerate sample is decided by the interval only
    assert sg.crate_row(*_stores(np.full(40, 0.2)), RULE)["sentence_key"] == "raised"
    for key in ("raised", "lowered", "not clearly raised"):                                                       # every filled sentence passes the wording check (also in gap())
        X.check_generated_sentences({"s": sg.CRATE_SENTENCES[key].replace("[x]", "1.02").replace("[a, b]", "[1.01, 1.04]")}, "crate")


def test_the_row_refuses_unpaired_conditions_and_other_folds_like_nc2():
    real, cr = _stores(np.full(40, 0.2))
    cr.tables[G4]["A1"].pop(CONDS[0])
    with pytest.raises(sg.NeedsRescoreError, match="same held-out conditions"):
        sg.crate_row(real, cr, RULE)
    real, cr = _stores(np.full(40, 0.2))
    real.notes["cell_folds"], cr.notes["cell_folds"] = {G4: {0, 1, 2, 3, 4}}, {G4: {0, 1}}
    with pytest.raises(sg.NeedsRescoreError, match="outer folds"):
        sg.crate_row(real, cr, RULE)
    with pytest.raises(sg.NeedsRescoreError, match="needs A1 at g4"):
        sg.crate_row(real, v4.Store({G4: {"A9": {c: 2.0 for c in CONDS}}}, {}, {}), RULE)


def test_run_stats_v4_writes_the_row_into_contrasts_and_changes_nothing_else(grid):
    kw = dict(item_f_dir=grid["fdir"], item_f_sha256=grid["sha"], negative_runs=grid["neg"])
    base = ss.run_stats_v4(os.path.join(grid["tmp"], "an_nocrate"), grid["dirs"], **kw)
    new = ss.run_stats_v4(os.path.join(grid["tmp"], "an_crate"), grid["dirs"], crate_runs=grid["crate"], **kw)
    assert base["crate_ablation"]["status"] == "not run (no crate_runs given)" and base["stats_gaps"]["status"]["G9_crate"].startswith("not run")
    ca = json.load(open(os.path.join(grid["tmp"], "an_crate", "contrasts_v4_B.json")))["crate_ablation"]
    real = v4.Store.from_runs(grid["dirs"]).scores("A1", *G4)
    cr = v4.Store.from_runs(grid["crate"]).scores("A1", *G4)
    L = np.array([np.log(cr[c] / real[c]) for c in sorted(real)])
    assert ca["status"] == "computed" and ca["n"] == 40 and ca["median_L"] == pytest.approx(float(np.median(L))) and ca["sentence_key"] == "raised" and ca["n_L_positive"] == int((L > 0).sum())
    assert ca == json.loads(json.dumps(new["crate_ablation"]))
    assert json.dumps(strip_contrasts(new), sort_keys=True, default=str) == json.dumps(strip_contrasts(base), sort_keys=True, default=str)     # tiers, states, titles, counts, margins, gate untouched
    for k in ("effective_tiers", "outcome", "gate_G", "status"):
        assert json.dumps(new[k], sort_keys=True, default=str) == json.dumps(base[k], sort_keys=True, default=str), k
    zero = ss.run_stats_v4(os.path.join(grid["tmp"], "an_crate0"), grid["dirs"], crate_runs=grid["crate0"], **kw)["crate_ablation"]
    assert zero["status"] == "computed" and zero["sentence_key"] in ("not clearly raised", "lowered")


def test_m1_a_crate_run_that_is_not_the_pinned_configuration_stops_a_strict_run(grid):
    """red team m-1: the config hash of every run must be the MANIFEST hash of its fold, folds 0-4 exactly once; a mismatch is a ValueError (a stop), not a pairing mismatch"""
    tmp = grid["tmp"] + "/wrong"
    os.makedirs(tmp)
    cases = {}
    w1 = make_crate(tmp + "/a", grid["dirs"]) if os.makedirs(tmp + "/a") is None else None
    cf = json.load(open(os.path.join(w1[1], "config.json")))
    cf["config_sha256"] = "0" * 64
    _dump(cf, os.path.join(w1[1], "config.json"))
    cases["hash of another configuration"] = (w1, "is not the pinned configuration conf_samsung_B_f1_m32_crate")
    w2 = make_crate(tmp + "/b", grid["dirs"]) if os.makedirs(tmp + "/b") is None else None
    cases["only four folds"] = (w2[:4], "folds 0-4 exactly once")
    w3 = make_crate(tmp + "/c", grid["dirs"]) if os.makedirs(tmp + "/c") is None else None
    cf = json.load(open(os.path.join(w3[2], "config.json")))
    cf["fold"] = 1                                                                                           # fold 1 twice (and the hash of fold 2 no longer matches its id)
    _dump(cf, os.path.join(w3[2], "config.json"))
    cases["fold twice"] = (w3, "is not the pinned configuration")
    for label, (dirs, msg) in cases.items():
        with pytest.raises(ValueError, match=msg):
            sg.check_crate_runs(dirs)
        an = os.path.join(tmp, "an_" + label.split()[0])
        with pytest.warns(UserWarning, match="G9_crate"):
            with pytest.raises(ss.RegisteredControlError, match="C-rate ablation"):
                ss.run_stats_v4(an, grid["dirs"], item_f_dir=grid["fdir"], item_f_sha256=grid["sha"], negative_runs=grid["neg"], crate_runs=dirs)
        assert not os.path.exists(os.path.join(an, "contrasts_v4_B.json")), label
    sg.check_crate_runs(grid["crate"])                                                                       # the correctly pinned set passes


def test_a_pairing_mismatch_between_correctly_pinned_runs_is_recorded_not_computed_and_does_not_stop(grid):
    tmp = grid["tmp"] + "/pairing"
    os.makedirs(tmp)
    dirs = make_crate(tmp, grid["dirs"], shift=0.2)
    sc = json.load(open(os.path.join(dirs[0], "condition_scores.json")))
    sc["A1"].pop(next(iter(sc["A1"])))                                                                       # one condition not scored: the pinned run is incomplete
    _dump(sc, os.path.join(dirs[0], "condition_scores.json"))
    out = ss.run_stats_v4(os.path.join(tmp, "an"), grid["dirs"], item_f_dir=grid["fdir"], item_f_sha256=grid["sha"], negative_runs=grid["neg"], crate_runs=dirs)
    ca = out["crate_ablation"]
    assert ca["failed_needs_rescore"] is True and ca["status"].startswith("not computed") and "same held-out conditions" in ca["reason"]
    assert os.path.exists(os.path.join(tmp, "an", "contrasts_v4_B.json"))


def test_a_compute_error_in_the_row_stops_a_strict_run(grid, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr(sg, "crate_row", boom)
    with pytest.warns(UserWarning, match="G9_crate"):
        with pytest.raises(ss.RegisteredControlError, match="C-rate ablation"):
            ss.run_stats_v4(os.path.join(grid["tmp"], "an_crate_boom"), grid["dirs"], item_f_dir=grid["fdir"], item_f_sha256=grid["sha"], negative_runs=grid["neg"], crate_runs=grid["crate"])
    assert not os.path.exists(os.path.join(grid["tmp"], "an_crate_boom", "contrasts_v4_B.json"))


def test_once_frozen_a_strict_run_without_crate_runs_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(guard, "is_frozen", lambda root=None: True)
    from pinnkan import blinding
    monkeypatch.setattr(v4, "effective_config", lambda cfg, root: (cfg, {}))
    monkeypatch.setattr(blinding, "expected_n", lambda root, test: 40)
    monkeypatch.setattr(v4, "require_item_f", lambda *a, **k: {})
    root = tmp_path / "root"
    (root / "research").mkdir(parents=True)
    rows = {"lab_indicator": ["x"], "retain_all": ["x"], "random_subset": [["x"]]}
    with pytest.raises(ss.RegisteredControlError, match=r"\['crate_runs'\]"):
        ss.run_stats_v4(str(tmp_path / "an"), [], row_runs=rows, h7_run="h", item_f_dir=str(tmp_path), root=str(root))
    with pytest.raises(Exception) as e:                                                   # with the runs given the M-1 check passes (the next step fails for another reason)
        ss.run_stats_v4(str(tmp_path / "an"), [], row_runs=rows, h7_run="h", crate_runs=["c"], item_f_dir=str(tmp_path), root=str(root))
    assert not isinstance(e.value, ss.RegisteredControlError)


def test_the_cli_takes_crate_run_and_table_2_reads_the_row():
    src = open(os.path.join(ROOT, "code", "pinnkan", "stats_step.py"), encoding="utf8").read()
    assert '"--crate-run"' in src and "crate_runs=a.crate_run" in src and "(u)" in src and "9.9 (s)" not in src
    t2 = open(os.path.join(ROOT, "code", "figures", "table2.py"), encoding="utf8").read()
    assert 'S.get("crate_ablation")' in t2 and "ca[\"sentence_full\"]" in t2 and "not computed: " in t2 and "ca['median_ci']" in t2


# ------------------------------------------------------------------------------------------------ red team M-2, m-6
def _old_hull_sample(X, n, seed):
    """the function as it was before the constant-column fix (copied)"""
    from scipy.spatial import Delaunay
    from scipy.stats import qmc
    lo, hi = X.min(0), X.max(0)
    span = np.where(hi - lo > 1e-9, hi - lo, 1.0)
    pts = []
    try:
        tri = Delaunay(X, qhull_options="QJ")
        for rep in range(8):
            u = qmc.LatinHypercube(d=X.shape[1], seed=seed + rep).random(4 * n)
            p = lo + u * span
            pts.append(p[tri.find_simplex(p) >= 0])
            if sum(len(q) for q in pts) >= n:
                break
        P = np.concatenate(pts)
    except Exception:
        P = np.empty((0, X.shape[1]))
    if len(P) < n:
        P = np.concatenate([P, lo + qmc.LatinHypercube(d=X.shape[1], seed=seed + 99).random(n - len(P)) * span])
    return P[:n]


def test_m2_hull_sample_keeps_constant_columns_exactly_and_is_unchanged_without_them():
    from pinnkan import pinn
    rs = np.random.default_rng(1)
    X = rs.uniform(-0.8, 0.8, (30, 5))
    for seed in (0, 7):
        assert np.array_equal(pinn._hull_sample(X, 64, seed), _old_hull_sample(X, 64, seed))                       # no constant column: the same numbers as before
    neutral = -0.3125
    Xc = X.copy()
    Xc[:, 3] = Xc[:, 4] = neutral
    P = pinn._hull_sample(Xc, 64, 3)
    assert P.shape == (64, 5) and np.all(P[:, 3] == neutral) and np.all(P[:, 4] == neutral)                       # exactly the neutral value, span 0
    assert np.all(P[:, :3] >= Xc[:, :3].min(0) - 1e-12) and np.all(P[:, :3] <= Xc[:, :3].max(0) + 1e-12) and len({tuple(r) for r in P[:, :3]}) == 64        # the free columns are sampled
    old = _old_hull_sample(Xc, 64, 3)
    assert not np.all(old[:, 3] == neutral)                                                                         # the old code scattered them (the defect)
    one = Xc.copy()
    one[:, 1:] = 0.25
    P1 = pinn._hull_sample(one, 16, 2)
    assert np.all(P1[:, 1:] == 0.25) and P1[:, 0].min() >= one[:, 0].min() and P1[:, 0].max() <= one[:, 0].max()
    P0 = pinn._hull_sample(np.tile(Xc[:1], (5, 1)), 8, 0)
    assert np.all(P0 == Xc[0])


def test_m2_neutralised_collocation_points_carry_exactly_the_neutral_values():
    import torch
    from pinnkan import law, pinn, specs, synth
    spec = specs.SPECS["synthetic"]
    S0 = synth.make_synthetic("G0", n_cyc_cond=14, n_sto_cond=6, reps=2, seed=4)
    tr, te = synth.split_conditions(S0.cells, 0.25, 4)
    ntr, nte, rec = metrics.neutralise_stress(tr, te, spec, ["C_ch", "C_dch"])
    b = law.batch_from_cells(spec, ntr)
    col = pinn.make_collocation(spec, b, 0)
    neut_s = spec.norm(np.array([[0, 0, 0, rec["value"]["c_ch"], rec["value"]["c_dch"]]], float))[0, 3:]
    bs = col.b_s.numpy()
    assert bs.shape[0] > 0 and np.all(bs[:, 3] == np.float32(neut_s[0])) and np.all(bs[:, 4] == np.float32(neut_s[1]))
    base = pinn.make_collocation(spec, law.batch_from_cells(spec, tr), 0)
    assert len(np.unique(base.b_s.numpy()[:, 3])) > 1                                                               # the un-neutralised set varies in C_ch


def test_m6_the_crate_config_without_the_key_reproduces_the_primary_g4_a1_scores_exactly(tmp_path):
    """the pairing changes C-rate alone: A1 of the crate configuration with neutralise_stress removed (A1 only, single window) equals A1 of the multi-arm k-grid primary run at k = full"""
    import torch
    torch.set_num_threads(1)
    cfg = {"design": "R2", "dataset": "synthetic", "mode": "confirmatory", "test": "B", "n_trials": 1, "inner_k": 2, "steps_scale": 0.04, "seeds": [0, 1], "backbone": "self_limiting", "m": 32, "subset": "maxmin",
           "synthetic": {"kind": "G2", "n_cyc_cond": 16, "n_sto_cond": 8, "reps": 2, "seed": 7}}
    run.run({**cfg, "run_id": "P", "arms": ["A1", "A9"], "k": "grid"}, runs_dir=str(tmp_path))
    run.run({**cfg, "run_id": "C0", "arms": ["A1"]}, runs_dir=str(tmp_path))                                       # the crate config minus the key (and the crate run's own run_id)
    a = json.load(open(tmp_path / "P" / "condition_scores.json"))["A1"]
    b = json.load(open(tmp_path / "C0" / "condition_scores.json"))["A1"]
    assert set(a) == set(b) and len(a) > 3 and max(abs(a[c] - b[c]) for c in a) == 0.0
    run.run({**cfg, "run_id": "C1", "arms": ["A1"], "neutralise_stress": ["C_ch", "C_dch"]}, runs_dir=str(tmp_path))
    c = json.load(open(tmp_path / "C1" / "condition_scores.json"))["A1"]
    assert max(abs(a[k] - c[k]) for k in a) > 1e-6                                                                  # with the key the model changes
