"""Test helper: write a valid FROZEN in a TEMPORARY root (never the real one) and stub git so that verification passes."""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code"))

from pinnkan import guard  # noqa: E402

FAKE_COMMIT = "a" * 40


def make_freeze(tmp_path, monkeypatch, splits=None, config_hashes=(), commit=FAKE_COMMIT, dirty="", head=None, prereg_text="prereg v2 frozen"):
    root = str(tmp_path)
    assert os.path.realpath(root) != os.path.realpath(ROOT), "refusing to write a FROZEN flag into the real root"
    os.makedirs(os.path.join(root, "runs", "prereg"), exist_ok=True)
    with open(os.path.join(root, "runs", "prereg", "PREREG_v2.md"), "w") as fh:
        fh.write(prereg_text)
    payload = {"commit": commit, "prereg_file": "runs/prereg/PREREG_v2.md", "prereg_sha256": guard.sha256_file(os.path.join(root, "runs", "prereg", "PREREG_v2.md")),
               "splits": splits or {}, "config_sha256s": list(config_hashes)}
    with open(os.path.join(root, "runs", "prereg", "FROZEN"), "w") as fh:
        json.dump(payload, fh)

    def fake_git(r, *args):
        if args[:2] == ("rev-parse", "HEAD"):
            return head or commit
        if args[0] == "status":
            return dirty
        return ""
    monkeypatch.setattr(guard, "_git", fake_git)
    return payload
