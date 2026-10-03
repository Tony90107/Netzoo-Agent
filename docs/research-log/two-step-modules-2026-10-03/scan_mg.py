"""Log 327: where MG1 changes validation, over every recorded model reading.

Usage (repository root): python docs/research-log/two-step-modules-2026-10-03/scan_mg.py

For each recorded SemanticInterpretation (multi-reading only) the readings are
checked with `separately_stated_gaps` (Log 327 supplement 2), i.e. where MG1 applies.
"""
import collections
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "docs" / "research-log" / "activity-witness-2026-10-03")]
from replay_ta import rows  # noqa: E402
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import separately_stated_gaps  # noqa: E402

fired, seen = collections.Counter(), 0
for row in rows():
    trace = row["_trace"]
    for call in trace.get("calls", []):
        if call.get("schema") != "SemanticInterpretation" or not isinstance(call.get("parsed"), dict):
            continue
        try:
            interpretation = SemanticInterpretation.model_validate(call["parsed"])
        except ValueError:
            continue
        hypotheses = interpretation.outcome_hypotheses
        if len(hypotheses) < 2:
            continue
        seen += 1
        if separately_stated_gaps(trace["prompt"], hypotheses):
            fired[(row.get("id"), trace["prompt"][:80],
                   tuple((h.outcome.artifact_type, h.outcome.granularity) for h in hypotheses))] += 1
print(f"recorded multi-reading first passes that parse: {seen}; MG1 applies: {sum(fired.values())}")
for key, n in fired.most_common():
    print(f"  {n:3d} {key}")
