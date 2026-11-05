"""Adds the boolean key "adopt" to runs/pilot_P6b/decision.json, as the lead's file contract requires (confirmatory code reads exactly this key).
Derived mechanically from the verdict that p6b_inner_folds.py `aggregate` wrote; nothing is decided here and p6b_inner_folds.py is unchanged.
adopt = True only if verdict == 'ADOPT_4_INNER_FOLDS_m8_m16' AND the run is complete; otherwise False (the default: keep 2 inner folds)."""
import json
import os
import sys

p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "runs", "pilot_P6b", "decision.json") if len(sys.argv) < 2 else sys.argv[1]
d = json.load(open(p, encoding="utf8"))
d["adopt"] = bool(d["verdict"] == "ADOPT_4_INNER_FOLDS_m8_m16" and d.get("complete") is True)
d["adopt_key_note"] = "true = use 4 inner folds at m in {8, 16}; false = keep 2. Added mechanically by code/pilots/p6b_add_adopt_key.py from 'verdict' (lead's file contract); the rule text is in 'rule', per-arm values in 'q_a'."
json.dump(d, open(p, "w", encoding="utf8"), indent=1)
print("adopt =", d["adopt"])
