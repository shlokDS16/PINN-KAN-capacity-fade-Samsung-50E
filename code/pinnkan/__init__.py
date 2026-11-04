"""pinnkan: confirmatory code base for the PINN + KAN calendar-and-cycle ageing study (PREREG_v2).

Everything here is CPU-only and single-threaded by default. The package never reads an outer test fold unless
runs/prereg/FROZEN exists (see guard.py)."""
import os

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"   # CPU only, forced. An empty value is dropped by Windows (torch then sees the GPU); -1 hides every device
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import sys

ROOT = os.environ.get("PINNKAN_ROOT") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_CODE = os.path.join(ROOT, "code")
if _CODE not in sys.path:
    sys.path.insert(0, _CODE)  # makes `models.*` (pilot modules, imported not edited) importable
