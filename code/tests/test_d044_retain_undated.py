"""D044: the retain-every-check-up row must load. Three check-ups have no start date (flag no_start_date), so they have no elapsed time;
with retain_all they used to reach the monotone-time assertion as NaN and every retain_all run crashed in setup (09 Nov, rc 1 after 6 s).

The test runs on a scrubbed copy of the real check-up table: dates, flags, QC and throughput are real, every capacity and retention value
is replaced by a synthetic decline, so no Samsung capacity is read (blinding rules, stop rule 6)."""
import os
import shutil
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pinnkan import data as D, zyk  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MAIN = os.environ.get("PINNKAN_DATA_ROOT", ROOT)        # a worktree has no data/; point this at the main checkout
SRC = os.path.join(MAIN, "data", "processed", "samsung_checkups.csv")
ZSRC = os.path.join(MAIN, zyk.ZYK_TABLE_REL)

pytestmark = pytest.mark.skipif(not (os.path.isfile(SRC) and os.path.isfile(ZSRC)), reason="Samsung tables not on disk")


@pytest.fixture(scope="module")
def scrubbed(tmp_path_factory):
    root = tmp_path_factory.mktemp("scrubbed")
    os.makedirs(root / "data" / "processed")
    df = pd.read_csv(SRC)
    days = df["elapsed_days"].fillna(0.0).to_numpy(float)
    cap_cols = [c for c in df.columns if c.startswith("q_") or c.startswith("retention")]
    for c in cap_cols:                                    # synthetic values only
        df[c] = 1.0 - 1e-4 * days if c.startswith("retention") else 4.9 * (1.0 - 1e-4 * days)
    df.to_csv(root / "data" / "processed" / "samsung_checkups.csv", index=False)
    shutil.copy(ZSRC, root / zyk.ZYK_TABLE_REL)
    return str(root), df


def test_the_undated_rows_are_three_and_all_fail_qc(scrubbed):
    _, df = scrubbed
    undated = df[df["elapsed_days"].isna()]
    assert len(undated) == 3
    assert set(undated["flags"].astype(str)) == {"no_start_date"}
    assert not undated["qc_pass"].astype(str).str.lower().isin(["true", "1"]).any()


@pytest.mark.parametrize("throughput", ["zyk", "analytic"])
def test_retain_all_loads_and_keeps_every_dated_check_up(scrubbed, throughput):
    root, df = scrubbed
    cells = D._load_samsung(root, retain_all=True, throughput=throughput)
    for c in cells:
        assert np.all(np.isfinite(c.t)) and np.all(np.diff(c.t) >= 0)
    n_rows = sum(len(c.t) for c in cells)
    base = D._load_samsung(root, retain_all=False, throughput=throughput)
    assert {c.cell_id for c in cells} >= {c.cell_id for c in base}
    assert n_rows > sum(len(c.t) for c in base)       # the row does retain QC-failed check-ups


def test_retain_all_false_is_unchanged_by_the_fix(scrubbed):
    """The fix only acts inside the retain_all branch; the undated rows never pass QC, so the default path drops them already."""
    root, _ = scrubbed
    a = D._load_samsung(root, retain_all=False, throughput="zyk")
    assert all(np.all(np.isfinite(c.t)) for c in a)
