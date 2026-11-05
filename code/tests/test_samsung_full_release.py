"""Tests for the full-release data path of the Samsung 50E pipeline (extractor, configure/CU_ONLY, regression against the first pipeline, audit helpers).

Run:  .venv/Scripts/python.exe -P -m pytest code/tests/test_samsung_full_release.py -q   (from ROOT)

Tests that need the downloaded data skip when it is absent. No test prints or asserts a capacity value: the regression compares hashes of row lines
(runs/samsung_pipeline_full/baseline_row_hashes.csv, written from the first pipeline's output).
"""
import hashlib
import os
import shutil
import sys
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
sys.path.insert(0, os.path.join(ROOT, "code", "data"))

import pandas as pd
import pytest

from data import samsung_checkups as S
import samsung_extract as X
import samsung_full_audit as A

RAWX = os.path.join(ROOT, "data", "raw", "samsung50e_full_x")
HASHES = os.path.join(ROOT, "runs", "samsung_pipeline_full", "baseline_row_hashes.csv")
MAPPING = os.path.join(ROOT, "runs", "samsung_pipeline", "folder_mapping.csv")
LISTS_FULL = os.path.join(ROOT, "runs", "samsung_pipeline_full", "member_lists")
# a cell whose entry-test meta file was not yet fetched when the first output was written: its first_test_date moved from the first capacity row to the ET meta
EXPLAINED_CHANGE_SINCE_FIRST_OUTPUT = {"TP_z08_03_s1"}


@pytest.fixture
def restore_config():
    saved = dict(RAW=S.RAW, LISTS=S.LISTS, OUT_DIR=S.OUT_DIR, OUT_CHECKUPS=S.OUT_CHECKUPS, OUT_CELLS=S.OUT_CELLS, CACHE=S.CACHE, RUN_DIR=S.RUN_DIR, CU_ONLY=S.CU_ONLY)
    yield
    for k, v in saved.items():
        setattr(S, k, v)


# ---------------------------------------------------------------- extractor
def test_safe_member_rejects_traversal_and_absolute_names():
    assert X.safe_member("TP_k01_01/") is None
    assert X.safe_member("TP_k01_01/TP_k01_01_02_CU.csv") == ("TP_k01_01", "TP_k01_01_02_CU.csv")
    for bad in ("../x.csv", "TP_k01_01/../../x.csv", "/abs/x.csv", "C:/x.csv", "a\\b.csv"):
        with pytest.raises(ValueError):
            X.safe_member(bad)


def test_wanted_selects_meta_and_capacity_csv_only():
    def w(n):
        return X.wanted(X.MEMBER_RE.match(n))
    assert w("TP_z01_01_01_ET_T10_meta.txt") and w("TP_z01_01_04_ZYK_meta.txt")
    assert w("TP_z01_01_03_CU.csv") and w("TP_z01_01_07_exCU.csv") and w("TP_z01_01_01_ET_T23.csv") and w("TP_z01_01_09_AT_T23.csv")
    assert not w("TP_z01_01_01_ET_T10.csv") and not w("TP_z01_01_01_ET_T45.csv") and not w("TP_z01_01_09_AT_T45.csv") and not w("TP_z01_01_02_ZYK.csv")


def test_extract_zip_flattens_skips_bad_names_and_writes_list(tmp_path):
    zp = tmp_path / "TP_z99_01__f1.zip"
    with zipfile.ZipFile(zp, "w") as z:
        z.writestr("TP_z99_01/", "")
        z.writestr("TP_z99_01/TP_z99_01_02_CU.csv", "a,b\n1,2\n")
        z.writestr("TP_z99_01/TP_z99_01_02_CU_meta.txt", "Laboratory identifier: X\n")
        z.writestr("TP_z99_01/TP_z99_01_04_ZYK.csv", "a\n1\n")
        z.writestr("TP_z99_01/notes.txt", "x")
        z.writestr("TP_z99_01/TP_z98_01_02_CU.csv", "a\n1\n")
    rows, problems = X.extract_zip(zp, tmp_path / "out", tmp_path / "lists")
    assert sorted(r["member"] for r in rows) == ["TP_z99_01_02_CU.csv", "TP_z99_01_02_CU_meta.txt"]
    assert not (tmp_path / "out" / "TP_z99_01__f1" / "TP_z99_01_04_ZYK.csv").exists()
    kinds = sorted(p["problem"] for p in problems)
    assert kinds == ["member_serial_differs_from_zip", "name_not_matching_pattern"]
    lst = (tmp_path / "lists" / "TP_z99_01__f1.txt").read_text().splitlines()
    assert lst[0] == "member\tsize\tcrc32" and len(lst) == 1 + 5          # every non-directory member, wanted or not
    assert rows[0]["sha256"] == hashlib.sha256((tmp_path / "out" / "TP_z99_01__f1" / rows[0]["member"]).read_bytes()).hexdigest()
    rows2, _ = X.extract_zip(zp, tmp_path / "out", tmp_path / "lists")      # resumable
    assert {r["action"] for r in rows2} == {"kept"}


# ---------------------------------------------------------------- configure / CU_ONLY
def test_capacity_csv_kinds(restore_config):
    S.configure(cu_only=False)
    assert S._is_capacity_csv("CU", None) and S._is_capacity_csv("exCU", None) and S._is_capacity_csv("ET", "23") and S._is_capacity_csv("AT", "23")
    assert not S._is_capacity_csv("ET", "10") and not S._is_capacity_csv("AT", "45") and not S._is_capacity_csv("ZYK", None)
    S.configure(cu_only=True)
    assert S._is_capacity_csv("CU", None) and not S._is_capacity_csv("exCU", None) and not S._is_capacity_csv("ET", "23") and not S._is_capacity_csv("AT", "23")


def test_defaults_point_at_the_full_release():
    assert os.path.basename(str(S.RAW_FULL)) == "samsung50e_full_x" and os.path.basename(str(S.LISTS_FULL)) == "member_lists"
    assert str(S.RAW_FULL) != str(S.RAW_MEMBERS)


# ---------------------------------------------------------------- listing counts (FB-6)
def test_count_listing_counts_csv_members_not_meta():
    names = ["TP_z01_01_01_ET_T10_meta.txt", "TP_z01_01_01_ET_T23.csv", "TP_z01_01_01_ET_T23_meta.txt", "TP_z01_01_02_ZYK.csv", "TP_z01_01_02_ZYK_meta.txt",
             "TP_z01_01_03_CU.csv", "TP_z01_01_03_CU_meta.txt", "TP_z01_01_04_ZYK_meta.txt", "TP_z01_01_05_exCU.csv", "TP_z01_01_05_exCU_meta.txt",
             "TP_z01_01_07_CU_meta.txt", "TP_z01_01_09_AT_T23.csv", "TP_z01_01_09_AT_T10.csv"]
    c = A.count_listing(names)
    assert (c["n_cu"], c["n_excu"], c["n_et23_csv"], c["n_et_csv"], c["n_at23_csv"], c["n_at_csv"]) == (1, 1, 1, 1, 1, 2)
    assert (c["n_zyk_csv"], c["n_zyk_meta"], c["n_cu_meta_only"], c["n_excu_meta_only"]) == (1, 2, 1, 0)


# ---------------------------------------------------------------- regression against the first pipeline (needs the extraction)
def _line_hashes(path):
    lines = open(path, encoding="utf-8", newline="").read().split("\n")
    out = {}
    for ln in lines[1:]:
        if ln:
            out.setdefault(ln.split(",", 1)[0], []).append(ln)
    return {c: (len(v), hashlib.sha256("\n".join(v).encode()).hexdigest()) for c, v in out.items()}


@pytest.mark.skipif(not (os.path.isdir(RAWX) and os.path.exists(HASHES) and os.path.exists(MAPPING)), reason="full extraction or baseline hashes absent")
def test_cu_only_rows_on_full_release_match_first_pipeline(tmp_path, restore_config):
    ref = pd.read_csv(HASHES, dtype=str)
    mp = pd.read_csv(MAPPING)
    pick = []
    for kind in ("k", "z"):
        ids = sorted(ref[ref.cell_id.str.startswith("TP_" + kind)].cell_id.unique())
        pick += ids[::max(1, len(ids) // 5)][:5]
    pick += sorted(EXPLAINED_CHANGE_SINCE_FIRST_OUTPUT)
    pick = sorted(set(pick))
    raw = tmp_path / "raw"
    for cid in pick:
        folder = mp[mp.cell_id == cid].iloc[0]["folder"]
        src = os.path.join(RAWX, folder)
        os.makedirs(raw / folder)
        for f in os.listdir(src):
            if "_CU" in f or f.endswith("_meta.txt"):
                shutil.copy(os.path.join(src, f), raw / folder / f)
    S.configure(raw=raw, lists=LISTS_FULL, out_dir=tmp_path / "proc", run_dir=tmp_path / "run", cu_only=True)
    df, _, _, _, _ = S.build(jobs=1, use_cache=False)
    out = tmp_path / "rows.csv"
    df.to_csv(out, index=False)
    got = _line_hashes(out)
    for set_name in ("per_member_pipeline_rerun_147_cells", "pre_full_processed_csv_76_cells"):
        r = ref[ref.set == set_name]
        for row in r.itertuples():
            if row.cell_id not in pick:
                continue
            if set_name.startswith("pre_full") and row.cell_id in EXPLAINED_CHANGE_SINCE_FIRST_OUTPUT:
                continue
            assert got[row.cell_id] == (int(row.n_rows), row.sha256_of_row_lines), (set_name, row.cell_id)


@pytest.mark.skipif(not os.path.exists(MAPPING), reason="folder mapping absent")
def test_stage_aware_cell_ids_are_unique_and_cover_the_design():
    mp = pd.read_csv(MAPPING)
    if len(mp) < 279:
        pytest.skip("pipeline not yet run on the full release")
    design = S.load_design()
    assert mp.cell_id.is_unique and not mp.cell_id.str.endswith("_s?").any()
    assert set(mp.cell_id) == {f"{r.serial}_s{int(r.stage)}" for r in design.itertuples()}
    assert mp.folder.str.contains("__f").all()
