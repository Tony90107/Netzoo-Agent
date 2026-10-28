"""Gates A1-A3: replay every recorded gpt-4o-mini-check turn (app-config-gap simulate.py rules) on the aligned app
settings with the old (30k) and new (45k) check allowance, call by call.

Run from docs/research-log/app-config-gap-2026-10-28: python3 ../check-allowance-2026-10-28/replay_allowance.py OUT
"""
import collections, contextlib, io, json, runpy, sys
from pathlib import Path

out_path = Path(sys.argv[1]).resolve()
sys.argv = ["simulate.py", str(out_path.with_suffix(".simulate.json"))]
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path("simulate.py")
rows, replay, medians, ALLOWANCE = g["rows"], g["replay"], g["medians"], g["ALLOWANCE"]
OLD = {"turn": 30000, "extra": 30000, "own_reserve": 4000, "other_reserve": 1200, "cap": 4000}
NEW = dict(OLD, extra=45000)
report = {"turns": len(rows), "old": OLD, "new": NEW, "run_to_refused": [], "refused_to_run": [],
          "refused": {"old": collections.Counter(), "new": collections.Counter()}, "family_refused_turns": {}}
for where, calls in rows:
    before, after = replay(calls, OLD, medians), replay(calls, NEW, medians)
    for a, b in zip(before, after):
        if a["sim"] == "ran" and b["sim"] == "refused":
            report["run_to_refused"].append([where, a["role"]])
        if a["sim"] == "refused" and b["sim"] == "ran":
            report["refused_to_run"].append([where, a["role"]])
        for name, call in (("old", a), ("new", b)):
            if call["sim"] == "refused":
                report["refused"][name][call["role"]] += 1
    for name, sim in (("old", before), ("new", after)):
        if any(c["sim"] == "refused" and c["role"] in ALLOWANCE for c in sim):
            report["family_refused_turns"].setdefault(name, []).append(where)
out_path.write_text(json.dumps(report, indent=1, default=dict))
print(json.dumps(report, indent=1, default=dict))
