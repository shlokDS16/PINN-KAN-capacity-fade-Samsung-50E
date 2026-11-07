"""Write runs/prereg/FROZEN (untracked) at the record commit and verify it. Lead's freeze step (PREREG_v4 section 18; D031).

Usage: .venv/Scripts/python.exe -P runs/freeze_runs/write_frozen.py [--dry]
--dry builds and checks the payload but writes nothing.
Refuses when FROZEN already exists, when code/ or runs/prereg/ has tracked changes, or when a pinned config hash
differs from MANIFEST.json.
"""
import json, os, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path[:0] = [os.path.join(ROOT, "code"), os.path.join(ROOT, "code", "prereg")]
from pinnkan import guard                       # noqa: E402
import make_confirmatory_configs as mcc         # noqa: E402

SPLIT_KEYS = [("samsung", "B"), ("samsung", "C"), ("samsung", "S2"), ("samsung", "A"), ("samsung", "S3"), ("isu", "B"), ("snl", "B")]
PREREG = "runs/prereg/PREREG_v4.md"


def git(*a):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True, check=True).stdout.strip()


def main(dry):
    if guard.is_frozen(ROOT):
        sys.exit("FROZEN already exists; refusing to overwrite")
    dirty = git("status", "--porcelain", "--untracked-files=no", "--", "code", "runs/prereg")
    if dirty:
        sys.exit("tracked changes under code/ or runs/prereg/: " + dirty.splitlines()[0])
    cfg_paths = mcc.freeze_config_paths()
    item_dir = os.path.join(ROOT, "runs", "item_f", "configs")
    item_paths = [os.path.join(item_dir, f"item_f_samsung_B_g1_f{f}.json") for f in range(5)]
    d = guard.build_freeze_payload(ROOT, SPLIT_KEYS, cfg_paths, prereg_file=PREREG, require_pins=True, item_f_config_paths=item_paths)
    man = json.load(open(os.path.join(ROOT, "runs", "prereg", "confirmatory_configs", "MANIFEST.json"), encoding="utf8"))
    want = [e["config_sha256"] for e in man["files"] if e["group"] != "item_f"]
    want_f = [e["config_sha256"] for e in man["files"] if e["group"] == "item_f"]
    assert sorted(d["config_sha256s"]) == sorted(want), "config hashes differ from MANIFEST"
    assert sorted(d["item_f_config_sha256s"]) == sorted(want_f), "item (f) hashes differ from MANIFEST"
    assert len(set(d["config_sha256s"])) == len(d["config_sha256s"]) == 276, len(d["config_sha256s"])
    assert not d["pins_missing"], d["pins_missing"]
    assert d["commit"] == git("rev-parse", "HEAD")
    summary = {"commit": d["commit"], "prereg_sha256": d["prereg_sha256"], "splits": sorted(d["splits"]), "n_configs": len(d["config_sha256s"]),
               "n_item_f": len(d["item_f_config_sha256s"]), "pins": sorted(d["pins"])}
    print(json.dumps(summary, indent=1))
    if dry:
        print("dry run: nothing written")
        return
    with open(guard.frozen_path(ROOT), "w", encoding="utf8", newline="\n") as fh:
        json.dump(d, fh, indent=1)
        fh.write("\n")
    v = guard.verify_freeze(ROOT, check_git=True, untracked_under=("code",))
    print("verify_freeze: ok, commit", v["commit"][:10], "FROZEN sha256", guard.sha256_file(guard.frozen_path(ROOT)))


if __name__ == "__main__":
    main("--dry" in sys.argv[1:])
