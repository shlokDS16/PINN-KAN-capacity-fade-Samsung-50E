"""Launcher:  .venv/Scripts/python.exe -P code/run_pinnkan.py --config <json|yaml> [--runs-dir DIR]   (equivalent to -m pinnkan.run with code/ on the path)"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pinnkan.run import main  # noqa: E402

if __name__ == "__main__":
    main()
