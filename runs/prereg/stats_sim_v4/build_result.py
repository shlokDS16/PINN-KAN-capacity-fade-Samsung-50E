"""Fills {{T:name}} placeholders of RESULT_template.md with the tables of tables.md and writes RESULT.md.
Usage: python -P build_result.py  (after build_tables.py)"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
tabs = dict(re.findall(r"<!--T:(\w+)-->\n(.*?)\n<!--/T-->", open(os.path.join(HERE, "tables.md"), encoding="utf-8").read(), flags=re.S))
tpl = open(os.path.join(HERE, "RESULT_template.md"), encoding="utf-8").read()
used = set()


def sub(m):
    k = m.group(1)
    if k not in tabs:
        raise KeyError(k)
    used.add(k)
    return tabs[k]


out = re.sub(r"\{\{T:(\w+)\}\}", sub, tpl)
open(os.path.join(HERE, "RESULT.md"), "w", encoding="utf-8").write(out)
print("tables used:", len(used), "unused:", sorted(set(tabs) - used))
