"""Classify every recorded semantic_fallback by the issue kinds of its last failure.

Usage: python docs/research-log/tools/scan_fallbacks.py

Reads the `routing.semantic_interpreter_failed` event of each traced row whose
reason code is `semantic_fallback` (Log 196 used this to size the T2 class).
"""
import collections

from traces import traced_rows

kinds = collections.Counter(); only_missing = []
for path, index, row in traced_rows():
    trace = row["_trace"]
    if trace.get("reason_code") != "semantic_fallback":
        continue
    failures = [e for e in trace.get("events", []) if e["type"] == "routing.semantic_interpreter_failed"]
    if not failures:
        kinds[("no_failed_event",)] += 1
        continue
    issues = [x if isinstance(x, str) else str(x) for x in failures[-1]["payload"].get("validation_issues") or []]
    shape = tuple(sorted({issue.split(".", 1)[-1].split(":", 1)[0] for issue in issues}))
    kinds[shape] += 1
    if shape == ("missing_evidence",):
        only_missing.append((path.name, row.get("id"), index, [issue.split(":", 1)[1] for issue in issues]))
print("fallbacks:", sum(kinds.values()))
for shape, count in kinds.most_common():
    print(f"  {count} {shape}")
print("only missing_evidence:")
for item in only_missing:
    print(" ", item)
