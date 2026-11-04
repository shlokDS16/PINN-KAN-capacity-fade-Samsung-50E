"""Statistics step launcher:  .venv/Scripts/python.exe -P code/run_pinnkan_stats.py --analysis-dir runs/<x>/analysis --runs B=runs/b_f0,runs/b_f1 --runs C=runs/c --negative-run runs/nc --h7-run runs/h7 --stress-run runs/b_f0"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pinnkan.stats_step import main  # noqa: E402

if __name__ == "__main__":
    main()
