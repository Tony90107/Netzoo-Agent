"""Check recorded results by default; --live explicitly spends provider calls.

The eight public synthetic prompts include no patient data. The scientific
answer key is never sent to the provider. Raw structured IO is captured without
credentials by the existing evaluator.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def check_science(case, row, *, prose=False):
    errors = []
    groups = {}
    for claim in row.get("stated_hypotheses", []):
        groups.setdefault(claim["text_span"], []).append(claim)
    expected = case["scientific_groups"]
    if len(groups) != len(expected):
        errors.append(f"hypotheses: {len(groups)}, expected {len(expected)}")
    for index, (claims, want) in enumerate(zip(groups.values(), expected), 1):
        actions = {c["basis"] for c in claims}
        if not set(want["required"]) <= actions or not actions <= set(want["allowed"]):
            errors.append(f"hypothesis {index}: wrong methods {sorted(actions)}")
        if {c["target_artifact"] for c in claims} != {want["target"]}:
            errors.append(f"hypothesis {index}: wrong scientific target")
    answer = row.get("answer", "")
    if prose:
        if answer.count("You would need") < len(expected):
            errors.append("missing method input/result explanations")
        for label in ("Algorithmic assumptions:", "Required inputs:", "Outputs:"):
            if label in answer:
                errors.append(f"unexpected API-style heading: {label}")
    else:
        for label in ("Algorithmic assumptions:", "Required inputs:", "Outputs:"):
            if answer.count(label) < len(expected) and answer.count("You would need") < len(expected):
                errors.append(f"missing comparison detail: {label}")
    if "Which scientific" not in answer:
        errors.append("missing final choice question")
    if not row.get("passed"):
        errors.extend(row.get("errors", ["routing evaluation failed"]))
    return errors


class RecordedProvider:
    """Replay captured model arguments against today's validation and rendering."""
    def __init__(self, calls):
        self.calls = iter(calls)

    def with_structured_output(self, schema, **kwargs):
        provider = self

        class Adapter:
            def invoke(self, messages):
                call = next(provider.calls)
                if call["schema"] != schema.__name__:
                    raise AssertionError("The recorded pipeline no longer matches")
                return schema.model_validate(call["raw_tool_calls"][0]["args"])

        return Adapter()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true", help="Run eight prompts using .env provider credentials")
    mode.add_argument("--replay", action="store_true", help="Replay saved structured responses offline")
    parser.add_argument("--model", default="openai/gpt-4o-mini")
    args = parser.parse_args()
    cases = json.loads((HERE / "cases.json").read_text())
    output = HERE / ("replay-results.json" if args.replay else "live-results.json")
    if args.live or args.replay:
        from evaluate_routing import evaluate, RoutingScenario, _TraceCapture
        capture = _TraceCapture() if args.live else None
        if args.live:
            from dotenv import load_dotenv
            from netzoo_agent_core.llm import build_llm
            load_dotenv(ROOT / ".env")
            provider = build_llm(args.model, 0.0, max_output_tokens=2000, timeout_seconds=30)
        else:
            recorded = {r["id"]: r for r in json.loads((HERE / "live-trace.json").read_text())["results"]}
        rows = []
        for case in cases:
            scenario = RoutingScenario.model_validate({k: v for k, v in case.items() if k != "scientific_groups"})
            if args.replay:
                provider = RecordedProvider(recorded[case["id"]]["calls"])
            row = evaluate([scenario], provider=provider, model_name=args.model if args.live else "recorded",
                           source="live" if args.live else "fixture", trace_capture=capture)["results"][0]
            rows.append(row)
            output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
            if capture is not None:
                (HERE / "live-trace.json").write_text(json.dumps(capture.document({"model": args.model}), ensure_ascii=False, indent=2) + "\n")
    else:
        rows = json.loads(output.read_text())
    by_id = {r["id"]: r for r in rows}
    report = []
    for case in cases:
        errors = check_science(case, by_id.get(case["id"], {}), prose=args.replay or args.live)
        report.append(dict(id=case["id"], passed=not errors, errors=errors))
        print(case["id"], "PASS" if not errors else "FAIL", "; ".join(errors))
    if args.replay:
        (HERE / "corrected-original-answer.md").write_text(rows[0]["answer"] + "\n")
    (HERE / ("replay-science-check.json" if args.replay else "live-science-check.json")).write_text(json.dumps(report, indent=2) + "\n")
    return 0 if all(r["passed"] for r in report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
