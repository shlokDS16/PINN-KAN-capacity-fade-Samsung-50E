"""run_stats_v4 from a given code tree. argv: code_dir work_dir out_name mode(head|new|off)"""
import json, os, sys
code, W, name, mode = sys.argv[1:5]
sys.path.insert(0, code)
from pinnkan import stats_step as ss
import pinnkan
assert os.path.abspath(pinnkan.__file__).startswith(os.path.abspath(code)), pinnkan.__file__
p = json.load(open(os.path.join(W, "paths.json")))
kw = dict(item_f_dir=p["fdir"], item_f_sha256=p["sha"], physval=True)
if mode == "new":
    kw["negative_runs"] = p["neg"]
if mode == "off":
    kw["gaps"] = False
ss.run_stats_v4(os.path.join(W, name), p["dirs"], **kw)
print(mode, "ok", sorted(os.listdir(os.path.join(W, name))))
