"""Log 325 offline evidence: the second call each recorded schema-failed first pass now takes.

Usage (repository root): python docs/research-log/schema-patch-2026-10-03/replay_sp.py

Every distinct recorded first pass (all traced reports under docs/research-log)
that fails `SemanticInterpretation` is routed by the current code with a
stopping second call (`replay_first_pass.route`): printed are the recorded
errors, the salvage, the second call and its issues, grouped. Nothing calls a
model.
"""
import collections
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "docs" / "research-log" / "tools"),
                str(ROOT / "docs" / "research-log" / "activity-witness-2026-10-03")]
from pydantic import ValidationError  # noqa: E402
from replay_first_pass import route  # noqa: E402
from replay_ta import rows  # noqa: E402
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402


def main():
    seen, routes, detail = set(), collections.Counter(), collections.Counter()
    for row in rows():
        trace = row["_trace"]
        calls = trace.get("calls") or []
        if not calls or calls[0].get("schema") != "SemanticInterpretation" or not calls[0].get("raw_tool_calls"):
            continue
        if calls[0].get("finish_reason") == "injected_recorded_first_pass":
            continue
        first = calls[0]["raw_tool_calls"][0]["args"]
        key = hashlib.sha256(json.dumps([row.get("id"), first], sort_keys=True).encode()).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        try:
            SemanticInterpretation.model_validate(first)
            continue
        except ValidationError as error:
            errors = tuple(sorted({(str(e["loc"][-1]), e["type"]) for e in error.errors()}))
        salvaged, taken, issues = route(trace["prompt"], first)
        second = taken.split(" [")[0]
        routes[second] += 1
        kinds = tuple(sorted(salvaged)) if salvaged else ()
        schema_issues = tuple(sorted({i.split(":")[0].split(".")[-1] + ":" + i.split(":", 1)[1].split("=")[0]
                                      for i in (issues or []) if "schema_" in i}))
        detail[(errors, kinds, second, schema_issues, trace.get("reason_code"))] += 1
    print(f"distinct first passes: {len(seen)}; schema failures by second call: {dict(routes)}")
    for (errors, kinds, second, schema_issues, recorded), n in detail.most_common():
        print(f"  {n:3d} errors={errors} salvage={kinds} -> {second} {schema_issues} (recorded end: {recorded})")


if __name__ == "__main__":
    main()
