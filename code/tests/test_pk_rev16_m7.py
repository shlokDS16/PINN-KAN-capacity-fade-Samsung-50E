"""Rev. 16 red-team m-7: once the project root is frozen, a caller-supplied root without FROZEN cannot skip the pinned statistics config."""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import pytest

from pinnkan import guard, stats_v4 as v4


def test_other_root_without_frozen_falls_back_to_the_frozen_project_root(tmp_path, monkeypatch):
    proj, other = str(tmp_path / "proj"), str(tmp_path / "other")
    os.makedirs(proj), os.makedirs(other)
    monkeypatch.setattr(guard, "_DEFAULT_ROOT", proj)
    monkeypatch.setattr(guard, "is_frozen", lambda r=None: os.path.abspath(r or proj) == os.path.abspath(proj))
    with pytest.raises(v4.StatsConfigPinError, match="absent"):       # the project's pin is enforced (its file is missing here, so it refuses)
        v4.effective_config({"graph_w": 0.5}, root=other)


def test_unfrozen_project_and_other_root_keep_the_pre_freeze_behaviour(tmp_path, monkeypatch):
    proj, other = str(tmp_path / "proj"), str(tmp_path / "other")
    os.makedirs(proj), os.makedirs(other)
    monkeypatch.setattr(guard, "_DEFAULT_ROOT", proj)
    monkeypatch.setattr(guard, "is_frozen", lambda r=None: False)
    cfg, rec = v4.effective_config({"graph_w": 0.5}, root=other)
    assert cfg == {"graph_w": 0.5} and rec == {"frozen": False, "pinned": False}
