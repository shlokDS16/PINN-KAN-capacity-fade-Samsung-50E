"""D025 window cap (PREREG_v4 section 5, freeze condition C28): a cell with n <= k intermediate check-ups gets the window n - 1, is kept and is listed.
The cap only binds where the cell would otherwise have no forecast point, so every other cell's window is unchanged, and it reads point counts only (no label)."""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np

from pinnkan import data
from pinnkan.data import Cell, WindowRule, prepare, window_capped_cells


def _cell(cid, n_points, kind="cycling", ret=None):
    t = np.arange(n_points, dtype=float) * 50.0
    ret = np.linspace(1.0, 0.9, n_points) if ret is None else np.asarray(ret, dtype=float)
    return Cell(cid, "samsung", kind, "T23|SOCmax1.0|DoD1.0|Cch0.5|Cdch1.0", np.array([23.0, 1.0, 1.0, 0.5, 1.0]), t, ret, t * 0.1, np.ones(n_points, dtype=bool))


RULE = WindowRule(k_cycling=4, k_storage=2, min_window_points=3)


def test_short_cell_is_capped_and_kept_with_one_forecast_point():
    c = _cell("TP_short", 5)                      # reference + 4 intermediate check-ups, k = 4: before D025 the cell was dropped
    assert RULE.window_end(c) == 3
    p = prepare(c, RULE)
    assert p is not None and p.w_idx == 3 and len(p.fc_true) == 1
    assert RULE.capped(c)


def test_cap_does_not_change_any_cell_that_had_a_forecast_point():
    for n in range(6, 14):
        c = _cell(f"TP_{n}", n)
        assert RULE.window_end(c) == 4 and not RULE.capped(c)
        s = _cell(f"S_{n}", n, kind="storage")
        assert RULE.window_end(s) == 2 and not RULE.capped(s)


def test_storage_cells_follow_the_same_cap():
    s = _cell("S_short", 3, kind="storage")       # reference + 2 intermediates, k_sto = 2
    assert RULE.window_end(s) == 1 and RULE.capped(s)


def test_listing_names_only_capped_cells():
    cells = [_cell("A", 5), _cell("B", 9), _cell("C", 4)]
    assert window_capped_cells(cells, RULE) == ["A", "C"]


def test_cap_reads_no_label_so_the_nc1_scramble_cannot_change_the_window():
    a = _cell("X", 5)
    b = _cell("X", 5, ret=[1.0, 0.99, 0.98, 0.97, 123.0])        # post-window label replaced by garbage
    assert RULE.window_end(a) == RULE.window_end(b) and RULE.capped(a) == RULE.capped(b)


def test_time_windows_are_never_capped():
    rw = WindowRule(W=100.0, min_window_points=3)
    assert not rw.capped(_cell("T", 4))


def test_too_few_points_for_a_window_is_still_dropped():
    c = _cell("tiny", 3)                           # cap gives w = 1 < min_window_points - 1
    assert prepare(c, RULE) is None
