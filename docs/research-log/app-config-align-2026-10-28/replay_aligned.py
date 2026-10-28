"""G3: replay the 778 recorded turns (app-config-gap simulate.py rules) on the aligned app settings.

Run from docs/research-log/app-config-gap-2026-10-28: python3 ../app-config-align-2026-10-28/replay_aligned.py OUT.json
"""
import collections, contextlib, io, json, runpy, statistics, sys
from pathlib import Path

out_path = Path(sys.argv[1]).resolve()
sys.argv = ["simulate.py", str(out_path.with_suffix(".simulate.json"))]
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path("simulate.py")
rows, replay, medians, OWN = g["rows"], g["replay"], g["medians"], g["OWN"]
ALIGNED = {"turn": 30000, "extra": 30000, "own_reserve": 4000, "other_reserve": 1200, "cap": 4000}
report = {"turns": len(rows), "settings": ALIGNED}
for name, config in (("app_before", g["CONFIGS"]["app"]), ("aligned", ALIGNED)):
    refused, cut, hit = collections.Counter(), collections.Counter(), set()
    for where, calls in rows:
        for call in replay(calls, config, medians):
            if call["sim"] == "refused":
                refused[call["role"]] += 1
                hit.add(where)
            if call["cut"]:
                cut[call["role"]] += 1
                hit.add(where)
    report[name] = {"turns_hit": len(hit), "refused_by_role": dict(refused), "cut_by_role": dict(cut)}
out_path.write_text(json.dumps(report, indent=1))
print(json.dumps(report, indent=1))
