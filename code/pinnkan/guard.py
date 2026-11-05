"""Test-fold guard (PREREG_v2 sections 12.4, 12.6, 18): no outer test fold of a real dataset is loaded or scored
unless the frozen-preregistration flag file ROOT/runs/prereg/FROZEN exists AND verifies.

FROZEN is a JSON file (review M2):
    {"commit": "<40-hex git commit of the frozen code>",
     "prereg_file": "runs/prereg/PREREG_v3.md" (optional, default; name the frozen successor explicitly if the final text has another name), "prereg_sha256": "<sha256 of that file>",
     "splits": {"<dataset>:<test>": {"file_sha256": "...", "fold_hash": "..."}, ...},
     "config_sha256s": ["<canonical sha256 of each frozen run config>", ...]}
Verification (`verify_freeze`): valid JSON with those keys; HEAD equals `commit`; the tracked files under code/ and runs/prereg/ are clean
(untracked files and unrelated data/ edits do not count); the prereg file hashes to `prereg_sha256`. Split hashes and config hashes are checked by
data.load_split and run.run against the same file. Nothing in this package writes FROZEN; `build_freeze_payload` only returns the dict.

Every loader that can release test-fold data and every scorer calls `require_frozen`; decisions are logged in GUARD_LOG and copied into each run record.
Tests use a temporary root and a stubbed `_git`; they never create the real flag file."""
import hashlib
import json
import os
import subprocess

from . import ROOT as _DEFAULT_ROOT

FROZEN_REL = os.path.join("runs", "prereg", "FROZEN")
SCORED_REL = os.path.join("runs", "prereg", "SCORED.jsonl")
PIN_FILES = {"subsets": "runs/prereg/subsets.json", "symbolic_library": "code/pinnkan/symbolic_library.json", "item_f": "runs/prereg/item_f_dependence.json", "item_f_record": "runs/prereg/item_f_dependence.sha256.json"}   # Design R2 pins (build_v2): nested subsets, frozen symbolic library + cap, item (f) dependence file (stats_v4.ITEM_F_FILE)
PREREG_DEFAULT = "runs/prereg/PREREG_v3.md"    # the freeze candidate (PREREG_v3 section 18.3); FROZEN stores the name of the final file explicitly
GUARD_LOG = []


class TestFoldAccessError(RuntimeError):
    """Raised when an outer test fold would be read or scored before the preregistration is frozen and verified."""
    __test__ = False  # not a pytest class


def frozen_path(root=None):
    return os.path.join(root or _DEFAULT_ROOT, FROZEN_REL)


def is_frozen(root=None):
    """the flag file exists (cheap, no verification). Use `verify_freeze` / `require_frozen` before releasing anything."""
    return os.path.isfile(frozen_path(root))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=60).stdout.strip()


def read_freeze(root=None):
    """-> dict, or None when the flag file is absent; raises TestFoldAccessError when it is not the JSON described above"""
    p = frozen_path(root)
    if not os.path.isfile(p):
        return None
    try:
        d = json.load(open(p, encoding="utf8"))
    except Exception as e:  # noqa: BLE001
        raise TestFoldAccessError(f"FROZEN exists but is not valid JSON ({e})") from e
    need = {"commit", "prereg_sha256", "splits", "config_sha256s"}
    if not isinstance(d, dict) or not need <= set(d):
        raise TestFoldAccessError(f"FROZEN lacks required keys {sorted(need - set(d)) if isinstance(d, dict) else sorted(need)}")
    return d


def verify_freeze(root=None, check_git=True):
    """full verification of the flag file; returns the parsed dict or raises TestFoldAccessError"""
    root = root or _DEFAULT_ROOT
    d = read_freeze(root)
    if d is None:
        raise TestFoldAccessError(f"flag file {frozen_path(root)} is absent")
    pf = os.path.join(root, d.get("prereg_file", PREREG_DEFAULT))
    if not os.path.isfile(pf) or sha256_file(pf) != d["prereg_sha256"]:
        raise TestFoldAccessError("prereg file hash differs from the value pinned in FROZEN")
    if d.get("pins_missing"):
        raise TestFoldAccessError(f"FROZEN was built without the pins {d['pins_missing']}: a freeze needs subsets.json, the symbolic library (cap set) and the item (f) file pinned")
    for name, ent in (d.get("pins") or {}).items():                # Design R2: files pinned by hash in FROZEN; any difference or absence refuses (a FROZEN without "pins" keeps the older behaviour)
        fp = os.path.join(root, ent["file"])
        if not os.path.isfile(fp):
            raise TestFoldAccessError(f"pinned file {ent['file']} ({name}) is absent")
        if sha256_file(fp) != ent["sha256"]:
            raise TestFoldAccessError(f"pinned file {ent['file']} ({name}) differs from the hash pinned in FROZEN")
    if check_git:
        head = _git(root, "rev-parse", "HEAD")
        if head != d["commit"]:
            raise TestFoldAccessError(f"HEAD {head[:10]} is not the frozen commit {str(d['commit'])[:10]}")
        dirty = _git(root, "status", "--porcelain", "--untracked-files=no", "--", "code", "runs/prereg")
        if dirty:
            raise TestFoldAccessError("tracked files under code/ or runs/prereg/ differ from the frozen commit: " + dirty.splitlines()[0])
    return d


def is_valid_freeze(root=None):
    try:
        verify_freeze(root)
        return True
    except TestFoldAccessError:
        return False


def require_frozen(what, root=None):
    """The test-fold guard line. Call before any read or score of outer-test data."""
    try:
        verify_freeze(root)
        GUARD_LOG.append({"what": what, "frozen": True, "verified": True, "flag": frozen_path(root)})
    except TestFoldAccessError as e:
        GUARD_LOG.append({"what": what, "frozen": is_frozen(root), "verified": False, "reason": str(e), "flag": frozen_path(root)})
        raise TestFoldAccessError(f"refused: {what}. Outer test folds are readable only after a verified freeze: {e}") from e
    return True


def guard_role(role, what, root=None):
    """role 'train' is always allowed; any other role is an outer-test access."""
    if role == "train":
        GUARD_LOG.append({"what": what, "role": role, "frozen": is_frozen(root), "allowed": True})
        return True
    return require_frozen(f"{what} (role={role})", root)


def pinned_split(root, dataset, test):
    """pinned {file_sha256, fold_hash} of a split from FROZEN, or None before the freeze. After the freeze a missing entry is an error (fail closed)."""
    d = read_freeze(root)
    if d is None:
        return None
    key = f"{dataset}:{test}"
    if key not in d["splits"]:
        raise TestFoldAccessError(f"FROZEN pins no hash for split {key}")
    return d["splits"][key]


def canonical_config_hash(cfg):
    body = {k: v for k, v in cfg.items() if k not in ("run_id", "overwrite")}
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()


def check_config_frozen(cfg, root=None):
    """a confirmatory run on real data must use a config whose canonical hash is pinned in FROZEN"""
    d = verify_freeze(root, check_git=False)
    h = canonical_config_hash(cfg)
    if h not in d["config_sha256s"]:
        raise TestFoldAccessError(f"run config hash {h[:12]} is not among the frozen configs")
    return h


def scored_before(config_hash, root=None):
    p = os.path.join(root or _DEFAULT_ROOT, SCORED_REL)
    if not os.path.isfile(p):
        return False
    return any(json.loads(l).get("config_sha256") == config_hash for l in open(p, encoding="utf8") if l.strip())


def record_scoring(config_hash, run_id, commit, root=None):
    """append-only ledger of scored outer-test configurations: a second scoring of the same config is refused (stop rule 6)"""
    if scored_before(config_hash, root):
        raise TestFoldAccessError(f"config {config_hash[:12]} was already scored on an outer test fold (stop rule 6): refusing a second scoring")
    p = os.path.join(root or _DEFAULT_ROOT, SCORED_REL)
    with open(p, "a", encoding="utf8") as fh:
        fh.write(json.dumps({"config_sha256": config_hash, "run_id": run_id, "commit": commit}) + "\n")


def build_freeze_payload(root, split_keys, config_paths, prereg_file=PREREG_DEFAULT, pin_files=None, require_pins=False):
    """Helper for the lead at freeze time: returns the dict to put in FROZEN (does NOT write the file).
    split_keys: [(dataset, test)], config_paths: run-config JSON files whose canonical hashes are pinned."""
    from .data import _digest, split_path  # local import: data imports guard
    splits = {}
    for ds, test in split_keys:
        p = split_path(root, ds, test)
        sp = json.load(open(p, encoding="utf8"))
        block = sp[test] if ds == "samsung" else sp
        splits[f"{ds}:{test}"] = {"file_sha256": sha256_file(p), "fold_hash": block.get("sha256_of_folds") or _digest(block)}
    from .run import DEFAULTS  # the runner hashes DEFAULTS + the file's keys
    cfgs = [canonical_config_hash({**DEFAULTS, **json.load(open(c, encoding="utf8"))}) for c in config_paths]
    pins, missing = {}, []
    for name, rel in (PIN_FILES if pin_files is None else pin_files).items():      # subsets.json, symbolic_library.json (cap set) and the item (f) file must exist at the freeze
        fp = os.path.join(root, rel)
        if not os.path.isfile(fp):
            if require_pins:
                raise TestFoldAccessError(f"cannot pin {name}: {rel} does not exist")
            missing.append(name)                                          # listed in the payload; verify_freeze refuses a FROZEN that has a missing pin
            continue
        pins[name] = {"file": rel.replace("\\", "/"), "sha256": sha256_file(fp)}
    return {"commit": _git(root, "rev-parse", "HEAD"), "prereg_file": prereg_file, "prereg_sha256": sha256_file(os.path.join(root, prereg_file)),
            "splits": splits, "config_sha256s": cfgs, "pins": pins, "pins_missing": missing}
