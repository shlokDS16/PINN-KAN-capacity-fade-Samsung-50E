"""Test-fold guard (PREREG_v2 sections 12.4, 12.6, 18): no outer test fold of a real dataset is loaded or scored
unless the frozen-preregistration flag file ROOT/runs/prereg/FROZEN exists.

Every loader that can release test-fold data calls `require_frozen`; every scorer calls it too. Decisions are logged in
GUARD_LOG and copied into each run record. Tests use a temporary root; they never create the real flag file."""
import os

from . import ROOT as _DEFAULT_ROOT

FROZEN_REL = os.path.join("runs", "prereg", "FROZEN")
GUARD_LOG = []


class TestFoldAccessError(RuntimeError):
    """Raised when an outer test fold would be read or scored before the preregistration is frozen."""
    __test__ = False  # not a pytest class


def frozen_path(root=None):
    return os.path.join(root or _DEFAULT_ROOT, FROZEN_REL)


def is_frozen(root=None):
    return os.path.isfile(frozen_path(root))


def require_frozen(what, root=None):
    """The test-fold guard line. Call before any read or score of outer-test data."""
    ok = is_frozen(root)
    GUARD_LOG.append({"what": what, "frozen": ok, "flag": frozen_path(root)})
    if not ok:
        raise TestFoldAccessError(
            f"refused: {what}. Outer test folds are readable only after the preregistration is frozen "
            f"(flag file {frozen_path(root)} is absent).")
    return True


def guard_role(role, what, root=None):
    """role 'train' is always allowed; any other role is an outer-test access."""
    if role == "train":
        GUARD_LOG.append({"what": what, "role": role, "frozen": is_frozen(root), "allowed": True})
        return True
    return require_frozen(f"{what} (role={role})", root)
