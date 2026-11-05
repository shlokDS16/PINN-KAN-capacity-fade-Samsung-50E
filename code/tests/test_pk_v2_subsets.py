"""build_v2 item 1: nested, temperature-constrained training subsets (PREREG_v4 4.1) and the random-subset variant. Identifiers only; no label is read.
    .venv/Scripts/python.exe -P -m pytest code/tests/test_pk_v2_subsets.py -q"""
import json
import os
import shutil
import sys
import zlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import pandas as pd
import pytest

from pinnkan import data as D
from pinnkan import negcontrol, run, subsets, tuning

SPLIT = os.path.join(ROOT, "runs", "prereg", "samsung_splits_v2.json")


def _folds():
    sp = json.load(open(SPLIT, encoding="utf8"))["B"]["folds"]
    return {f: sp[f]["train_cycling_conditions"] for f in sp}


def _design(n_per_temp=(10, 12, 10), seed=0):
    rng = np.random.default_rng(seed)
    ids = []
    for T, n in zip((23, 35, 45), n_per_temp):
        for i in range(n):
            dod = round(float(rng.uniform(0.05, 0.8)), 2)
            smax = round(float(rng.uniform(dod + 0.1, 1.0)), 2)
            ids.append("T%g|SOCmax%g|DoD%g|Cch%g|Cdch%g" % (T, smax, dod, round(float(rng.uniform(0.2, 1.2)), 1), round(float(rng.uniform(0.2, 2.2)), 1)))
    return sorted(set(ids))


# ------------------------------------------------------------------------------------------------ parsing, determinism, nesting
def test_parse_key_round_trip_and_rejection():
    x = subsets.parse_samsung_cond("T35|SOCmax0.55|DoD0.25|Cch0.5|Cdch1")
    assert np.allclose(x, [35, 0.55 - 0.125, 0.25, 0.5, 1.0])
    for bad in ("T23|SOC0.5", "C00", "T35|SOCmax0.5|DoD0.2|Cch1"):
        with pytest.raises(subsets.SubsetError):
            subsets.parse_samsung_cond(bad)


def test_seed_root_equals_the_negcontrol_root():
    assert subsets.MC_SEED_ROOT == negcontrol.MC_SEED_ROOT == 20261105


def test_order_is_a_permutation_independent_of_input_order_and_deterministic():
    ids = _design()
    o1 = subsets.order_for_ids(ids)
    rng = np.random.default_rng(5)
    shuffled = [ids[i] for i in rng.permutation(len(ids))]
    assert subsets.order_for_ids(shuffled) == o1 == subsets.order_for_ids(ids)
    assert sorted(o1) == sorted(ids)


def test_subsets_are_nested_prefixes():
    o = subsets.order_for_ids(_design())
    s8, s16, s32 = (subsets.subset_at(o, m) for m in (8, 16, 32))
    assert s8 == o[:8] and s16 == o[:16] and set(s8) < set(s16) < set(o) or len(o) <= 32
    assert set(s8) <= set(s16) <= set(s32)
    assert subsets.subset_at(o, None) == o and subsets.subset_at(o, len(o) + 5) == o


def test_first_pick_is_the_condition_nearest_the_centroid_and_later_picks_are_max_min():
    ids = _design(seed=2)
    X, _ = subsets.coords_samsung(sorted(ids))
    Z = subsets.standardise(X)
    sid = sorted(ids)
    order = subsets.order_for_ids(ids)
    assert order[0] == sid[int(np.argmin(np.linalg.norm(Z, axis=1)))]
    pos = [sid.index(c) for c in order]
    for k in range(subsets.CONSTRAINT_M, len(order)):                       # beyond the first eight the constraint is inactive: plain greedy max-min
        d = np.array([min(np.linalg.norm(Z[j] - Z[i]) for i in pos[:k]) for j in range(len(sid))])
        d[pos[:k]] = -1.0
        assert d[pos[k]] >= d.max() - 1e-9


def test_ties_are_broken_by_condition_id():
    ids = ["T23|SOCmax0.5|DoD0.2|Cch0.5|Cdch1", "T23|SOCmax0.6|DoD0.2|Cch0.5|Cdch1", "T35|SOCmax0.5|DoD0.2|Cch0.5|Cdch1", "T35|SOCmax0.6|DoD0.2|Cch0.5|Cdch1"]
    X, tc = subsets.coords_samsung(ids)
    for _ in range(3):
        assert subsets.maxmin_order(ids, X, tc) == subsets.maxmin_order(ids[::-1], X[::-1], tc)


# ------------------------------------------------------------------------------------------------ temperature constraint
def _temp_counts(sub):
    return {T: sum(1 for c in sub if subsets.parse_samsung_cond(c)[0] == T) for T in (23.0, 35.0, 45.0)}


def test_constraint_is_active_and_satisfied_where_plain_max_min_violates_it():
    # a design in which the 35 C conditions sit in the middle of the stress space: plain max-min picks the extremes of 23 and 45 C first
    ids = []
    for i, (smax, dod, cch, cdch) in enumerate([(1.0, 0.8, 1.2, 2.2), (0.3, 0.05, 0.2, 0.2), (1.0, 0.05, 1.2, 0.2), (0.3, 0.8, 0.2, 2.2), (0.9, 0.7, 1.0, 2.0), (0.4, 0.1, 0.3, 0.3),
                                                 (0.95, 0.1, 0.3, 2.0), (0.4, 0.7, 1.0, 0.3), (0.7, 0.4, 0.7, 1.2), (0.6, 0.3, 0.5, 1.0)]):
        ids += ["T23|SOCmax%g|DoD%g|Cch%g|Cdch%g" % (smax, dod, cch, cdch), "T45|SOCmax%g|DoD%g|Cch%g|Cdch%g" % (smax, dod + 0.01, cch, cdch)]
    ids += ["T35|SOCmax%g|DoD%g|Cch%g|Cdch%g" % (0.65 + 0.01 * i, 0.35, 0.65, 1.1) for i in range(4)]
    X, tc = subsets.coords_samsung(ids)
    plain = subsets.maxmin_order(ids, X, None)
    constrained = subsets.maxmin_order(ids, X, tc)
    assert min(_temp_counts(plain[:8]).values()) < 2                 # the construction is a real test of the constraint
    assert min(_temp_counts(constrained[:8]).values()) >= 2
    assert constrained[0] == plain[0]
    for m in (8, 16):
        assert min(_temp_counts(constrained[:m]).values()) >= 2


def test_constraint_holds_on_every_real_outer_fold_identifiers_only():
    f = _folds()
    assert len(f) == 5
    for k, ids in f.items():
        assert len(ids) == 32
        o = subsets.order_for_ids(ids)
        assert sorted(o) == sorted(ids)
        assert min(_temp_counts(o[:8]).values()) >= 2
        assert subsets.order_for_ids(list(reversed(ids))) == o


def test_subsets_record_hash_is_stable_and_records_composition():
    f = _folds()
    r1, r2 = subsets.subsets_record(f), subsets.subsets_record(dict(reversed(list(f.items()))))
    assert r1["sha256"] == r2["sha256"] and set(r1["folds"]) == set(f)
    e = r1["folds"]["0"]
    assert e["subsets"]["8"] == e["order"][:8] and e["subsets"]["32"] == e["order"]
    assert sum(e["temperature_counts"]["8"].values()) == 8 and sum(e["temperature_counts"]["32"].values()) == 32


# ------------------------------------------------------------------------------------------------ random variant
def test_random_orders_are_seeded_nested_permutations_and_differ_by_draw():
    ids = _folds()["0"]
    o = [subsets.random_order(ids, 0, j) for j in range(3)]
    assert all(sorted(x) == sorted(ids) for x in o) and len({tuple(x) for x in o}) == 3
    assert subsets.random_order(list(reversed(ids)), 0, 1) == o[1]
    assert subsets.random_order(ids, 1, 1) != o[1]
    rng = np.random.default_rng(np.random.SeedSequence([20261105, zlib.crc32(b"B|g1|randsubset|0|2")]))
    assert o[2] == [sorted(ids)[i] for i in rng.permutation(32)]
    assert subsets.subset_at(o[0], 8) == o[0][:8] and set(subsets.subset_at(o[0], 8)) <= set(subsets.subset_at(o[0], 16))


# ------------------------------------------------------------------------------------------------ loader: thinning, m = 32 is Test B bit for bit
def _fake_root(tmp_path, fold=0):
    sp = json.load(open(SPLIT, encoding="utf8"))
    fdef = sp["B"]["folds"][str(fold)]
    rows = []
    n = 0
    for cond in list(fdef["train_cycling_conditions"]) + list(fdef["test_conditions"]):
        T, smax, dod, cch, cdch = (float(x) for x in (cond.split("|")[0][1:], cond.split("|")[1][6:], cond.split("|")[2][3:], cond.split("|")[3][3:], cond.split("|")[4][4:]))
        n += 1
        for r in range(4):
            rows.append(dict(cell_id=f"FAKE_z{n:02d}_01_s1", serial=f"FAKE_z{n:02d}_01", type="z", lab="HM", tp=n, cell=1, stage=1, T_C=T, SOC_max=smax, DoD=dod, C_ch=cch, C_dch=cdch,
                             kind="CU", file_idx=2 * r + 1, elapsed_days=7.0 * r, q_mean_ah=4.8 - 0.002 * r * (1 + n % 3), qc_pass=True, efc_est_cum=10.0 * r))
    for j, (T, soc) in enumerate([(10.0, 0.5), (23.0, 0.8)]):
        for r in range(4):
            rows.append(dict(cell_id=f"FAKE_k{j:02d}_01_s1", serial=f"FAKE_k{j:02d}_01", type="k", lab="SIE", tp=100 + j, cell=1, stage=1, T_C=T, SOC_max=soc, DoD=0.0, C_ch=0.0, C_dch=0.0,
                             kind="CU", file_idx=2 * r + 1, elapsed_days=30.0 * r, q_mean_ah=4.8 - 0.001 * r, qc_pass=True, efc_est_cum=np.nan))
    p = tmp_path / "data" / "processed"
    p.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(p / "samsung_checkups.csv", index=False)
    (tmp_path / "runs" / "prereg").mkdir(parents=True)
    shutil.copy(SPLIT, tmp_path / "runs" / "prereg" / "samsung_splits_v2.json")
    return str(tmp_path)


def _same_cells(a, b):
    assert [c.cell_id for c in a] == [c.cell_id for c in b]
    for x, y in zip(a, b):
        assert x.cond == y.cond and x.kind == y.kind
        for f in ("raw", "t", "ret", "efc", "fc_ok"):
            assert np.array_equal(getattr(x, f), getattr(y, f))


def test_m32_reproduces_the_unthinned_training_side_bit_for_bit(tmp_path):
    root = _fake_root(tmp_path)
    base = D.load_split("samsung", "B", 0, role="train", root=root)
    full = D.load_split("samsung", "B", 0, role="train", root=root, m=32)
    _same_cells(base.train, full.train)
    assert base.subset_info is None and full.subset_info["thinned"] is False and full.subset_info["m"] == 32
    assert len({c.cond for c in base.train if c.kind == "cycling"}) == 32


def test_m8_and_m16_keep_exactly_the_nested_subset_and_every_storage_cell(tmp_path):
    root = _fake_root(tmp_path)
    base = D.load_split("samsung", "B", 0, role="train", root=root)
    order = subsets.order_for_ids(_folds()["0"])
    prev = None
    for m in (8, 16):
        v = D.load_split("samsung", "B", 0, role="train", root=root, m=m)
        assert {c.cond for c in v.train if c.kind == "cycling"} == set(order[:m])
        assert [c.cell_id for c in v.train if c.kind == "storage"] == [c.cell_id for c in base.train if c.kind == "storage"] and sum(c.kind == "storage" for c in v.train) == 2
        assert v.subset_info["kept"] == order[:m] and v.subset_info["n_train_conditions"] == 32
        assert D.load_split("samsung", "B", 0, role="train", root=root, m=m).subset_info["sha256"] == v.subset_info["sha256"]
        _same_cells([c for c in v.train], [c for c in base.train if c.kind != "cycling" or c.cond in set(order[:m])])       # surviving cells untouched, same order
        prev = v
    r = D.load_split("samsung", "B", 0, role="train", root=root, m=8, subset="random", subset_draw=1)
    assert {c.cond for c in r.train if c.kind == "cycling"} == set(subsets.random_order(_folds()["0"], 0, 1)[:8]) and r.subset_info["kind"] == "random"


def test_thinning_never_touches_the_test_side_or_other_datasets_without_a_definition(tmp_path):
    with pytest.raises(ValueError):
        D.apply_subset([], "samsung", "A", {}, 0, 8)
    with pytest.raises(ValueError):
        D.apply_subset([], "snl", "B", {"train_conditions": ["a"]}, 0, 8)
    with pytest.raises(ValueError):
        D.apply_subset([], "samsung", "B", {"train_cycling_conditions": ["T23|SOCmax0.5|DoD0.2|Cch0.5|Cdch1"]}, 0, 8, subset="bogus")


# ------------------------------------------------------------------------------------------------ run writer
CFG = {"dataset": "synthetic", "arms": ["R1", "R2"], "n_trials": 1, "steps_scale": 0.05, "seeds": [0], "mode": "inner", "diagnostics": False,
       "synthetic": {"kind": "G0", "n_cyc_cond": 20, "n_sto_cond": 6, "reps": 2, "seed": 3}}


def test_inner_k_rule():
    assert [tuning.inner_k_for_m(m) for m in (8, 16, 32, None)] == [2, 2, 3, 3]
    assert tuning.inner_k_for_m(32, partial=True) == 2


def test_run_writes_subsets_json_and_sets_inner_k_from_m(tmp_path):
    d = run.run({**CFG, "run_id": "m8", "m": 8}, runs_dir=str(tmp_path))
    s = json.load(open(os.path.join(d, "subsets.json")))
    assert s["m"] == 8 and len(s["kept"]) == 8 and s["n_train_conditions"] == 15 and s["thinned"] is True
    assert json.load(open(os.path.join(d, "tuning_R1.json")))["inner_k"] == 2
    cfg = json.load(open(os.path.join(d, "config.json")))
    assert cfg["inner_k"] == 2 and cfg["m"] == 8
    d32 = run.run({**CFG, "run_id": "m32", "m": 32}, runs_dir=str(tmp_path))
    assert json.load(open(os.path.join(d32, "subsets.json")))["thinned"] is False and json.load(open(os.path.join(d32, "config.json")))["inner_k"] == 3
    d0 = run.run({**CFG, "run_id": "none"}, runs_dir=str(tmp_path))
    assert not os.path.exists(os.path.join(d0, "subsets.json"))
    assert json.load(open(os.path.join(d32, "tuning_R1.json")))["cond_scores"] == json.load(open(os.path.join(d0, "tuning_R1.json")))["cond_scores"]      # m = 32 == unthinned


def test_run_rejects_grid_values_outside_the_preregistered_grid(tmp_path):
    for bad in ({"m": 10}, {"m": 8, "test": "A"}, {"m": 8, "subset": "random", "subset_draw": 3}, {"m": 8, "subset": "x"}):
        with pytest.raises(run.ConfigError):
            run.run({**CFG, "run_id": "bad", **bad}, runs_dir=str(tmp_path))
