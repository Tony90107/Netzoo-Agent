"""Log 172: check that grid changes are confined to `sample` on axis artifacts.

Usage: python log172_diff.py <kind> <old.json> <new.json>
kind: single (Log 136), evidence (Log 148), pair (Log 150), guidance (Log 170)
"""
import json
import sys
from pathlib import Path

AXIS = {"coexpression_network", "pvalue_matrix"}
RESOLVED = {"exact", "fallback"}


def _result(kind, value):
    if kind == "single":
        return value["hyp"]
    if kind == "evidence":
        return value["hyp"]
    return value


def _in_scope(kind, key):
    row = json.loads(key)
    outcomes = [row["a"], row["b"]] if kind == "pair" else [row]
    return any("sample" in o["entity_types"] and o["artifact_type"] in AXIS for o in outcomes)


kind, old_path, new_path = sys.argv[1:4]
old = json.loads(Path(old_path).read_text())
new = json.loads(Path(new_path).read_text())
if kind == "pair":
    old, new = old["rows"], new["rows"]
assert old.keys() == new.keys()
changed = outside = lost = 0
transitions = {}
examples = []
for key in old:
    b, c = _result(kind, old[key]), _result(kind, new[key])
    if b == c and (kind != "single" or old[key] == new[key]):
        continue
    changed += 1
    transitions[(b[0], c[0])] = transitions.get((b[0], c[0]), 0) + 1
    if not _in_scope(kind, key):
        outside += 1
        examples.append(("outside", key, b, c))
    if b[0] in RESOLVED and (c[0] not in RESOLVED or b[1] != c[1]):
        lost += 1
        examples.append(("lost", key, b, c))
print(f"{kind}: rows={len(old)} changed={changed} outside_scope={outside} resolved_lost_or_swapped={lost}")
for t, n in sorted(transitions.items()):
    print("  transition", t, n)
for e in examples[:3]:
    print("  example:", e)
