"""Log 321 (supplement 3) offline evidence: where the new TA fires on recorded model readings.

Usage (repository root): python docs/research-log/activity-witness-2026-10-03/replay_ta.py

Every recorded SemanticInterpretation and SemanticPatch output in traced
trials is checked with `_tf_only_artifact_yields`, the only place TA changes
`restore_stated_fields`. RA is checked on every distinct recorded prompt: the
role mentions with and without the insufficiency rule. Nothing calls a model.
"""
import collections
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "docs" / "research-log" / "tools")]
from traces import load_report  # noqa: E402
from netzoo_agent_core.contracts.outcomes import RequestedOutcome  # noqa: E402
from netzoo_agent_core.interpretation import request_integrity as ri  # noqa: E402
from netzoo_agent_core.interpretation.stated_field_restoration import _tf_only_artifact_yields  # noqa: E402


def outcomes(call):
    parsed = call.get("parsed") or {}
    if call.get("schema") == "SemanticInterpretation":
        return [h.get("outcome") for h in parsed.get("outcome_hypotheses") or []]
    if call.get("schema") == "SemanticPatch":
        return [parsed.get("outcome")]
    return []


def rows():
    """Every traced row under docs/research-log (plain or gzip), as replay_cards.py reads them."""
    research = ROOT / "docs" / "research-log"
    for path in sorted({*research.glob("**/live-*.json"), *research.glob("**/live-*.json.gz")}):
        if ".provider-error" in path.name or ".unpaired" in path.name:
            continue
        try:
            report = load_report(path)
        except (OSError, ValueError):
            continue
        for row in report.get("results", []) if isinstance(report, dict) else []:
            if isinstance(row, dict) and row.get("_trace"):
                yield row


def main():
    fired, readings, prompts = collections.Counter(), 0, set()
    for row in rows():
        trace = row["_trace"]
        prompts.add(trace["prompt"])
        for call in trace.get("calls", []):
            for raw in outcomes(call):
                if not isinstance(raw, dict) or not raw.get("artifact_type"):
                    continue
                readings += 1
                try:
                    outcome = RequestedOutcome.model_validate(raw)
                except ValueError:
                    continue
                if _tf_only_artifact_yields(trace["prompt"], outcome, []) is not None:
                    fired[(trace["prompt"][:100], outcome.artifact_type, tuple(outcome.regulator_types))] += 1
    print(f"TA: recorded model readings {readings}; fired {sum(fired.values())}")
    for key, n in fired.most_common():
        print(f"  {n:3d} {key}")
    changed = []
    for task in sorted(prompts):
        for clause, scope in ri._scoped_clauses(task):
            if scope != "current":
                continue
            for match in ri._REGULATORY_ROLE_PAIR.finditer(clause):
                if not ri._NEGATED.search(clause[:match.start()]) and ri._rejected_role(clause, match):
                    changed.append((match.group(0), clause.strip()[:120]))
    print(f"RA: distinct prompts {len(prompts)}; role mentions no longer counted {len(changed)}")
    for item in changed:
        print("  ", item)


if __name__ == "__main__":
    main()
