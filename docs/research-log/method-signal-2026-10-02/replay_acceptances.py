"""Log 302 offline gate: which recorded discriminator acceptances MS1 would change.

Usage (from the repository root): python docs/research-log/method-signal-2026-10-02/replay_acceptances.py

Reads every traced report (`docs/research-log/tools/traces.py`), takes each
trial whose discriminator was accepted, and applies the repository's
`_unstated_tags` to the tags it accepted and the quotes the provider (or the
bounded recovery) gave for them. Prints distinct payloads, trials, and the
ones whose tags MS1 would remove.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "docs" / "research-log" / "tools"), str(ROOT / "scripts")]

from traces import report_paths, traced_rows  # noqa: E402
from netzoo_agent_core.contracts.outcomes import OutcomeEvidence  # noqa: E402
from netzoo_agent_core.graph.discriminator import _unstated_tags  # noqa: E402


def quoted(value, span):
    return OutcomeEvidence.model_construct(dimension="selection_tag", value=value, text_span=span,
                                           source="explicit", rationale="")


def main():
    seen = {}
    for path, _, row in traced_rows(report_paths()):
        trace = row["_trace"]
        events = [e for e in trace["events"] if e["type"].startswith("routing.semantic_discriminator_")]
        accepted = next((e["payload"] for e in events if e["type"].endswith("_accepted")), None)
        if not accepted:
            continue
        calls = [c for c in trace["calls"] if c.get("schema") == "SemanticDiscriminator"]
        args = ((calls[-1].get("raw_tool_calls") or [{}])[0].get("args") or {}) if calls else {}
        evidence = [quoted(e.get("value"), e.get("text_span")) for e in args.get("evidence", [])
                    if isinstance(e, dict) and e.get("dimension") == "selection_tag"]
        evidence += [quoted(e["payload"]["evidence"]["value"], e["payload"]["evidence"]["text_span"])
                     for e in events if e["type"].endswith("_recovered")]
        tags = set(accepted.get("selection_tags") or [])
        key = (trace["prompt"], tuple(sorted(tags)), tuple((e.value, e.text_span) for e in evidence))
        record = seen.setdefault(key, [0, row["id"], sorted(_unstated_tags(tags, evidence)), path.name])
        record[0] += 1
    print("distinct", len(seen), "trials", sum(item[0] for item in seen.values()))
    print("changed:", [tuple(item) for item in seen.values() if item[2]])


if __name__ == "__main__":
    main()
