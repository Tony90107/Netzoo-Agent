"""Four synthetic regressions; paid calls require --live. No patient files used."""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


class RecordedProvider:
    def __init__(self, calls):
        self.calls = iter(calls)

    def with_structured_output(self, schema, **kwargs):
        provider = self

        class Adapter:
            def invoke(self, messages):
                call = next(provider.calls)
                assert call["schema"] == schema.__name__
                value = (
                    call["raw_tool_calls"][0]["args"]
                    if call.get("raw_tool_calls")
                    else call["result"]
                )
                return schema.model_validate(value)

        return Adapter()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    output = HERE / ("replay-results.json" if args.replay else "results.json")
    cases = json.loads((HERE / "cases.json").read_text())
    if not args.live and not args.replay:
        rows = json.loads(output.read_text())
    else:
        from dotenv import load_dotenv
        from evaluate_routing import evaluate, RoutingScenario, _TraceCapture
        from netzoo_agent_core.llm import build_llm

        model = "openai/gpt-4o-mini"
        capture = _TraceCapture() if args.live else None
        if args.live:
            load_dotenv(ROOT / ".env")
            provider = build_llm(model, 0.0, max_output_tokens=2000, timeout_seconds=30)
        else:
            recorded = {
                r["id"]: r
                for r in json.loads((HERE / "trace.json").read_text())["results"]
            }
        rows = []
        for case in cases:
            if args.replay:
                provider = RecordedProvider(recorded[case["id"]]["calls"])
            row = evaluate(
                [RoutingScenario.model_validate(case)],
                provider=provider,
                model_name=model,
                source="live" if args.live else "fixture",
                review_policy="when_needed",
                trace_capture=capture,
            )["results"][0]
            rows.append(row)
            output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
            if capture is not None:
                (HERE / "trace.json").write_text(
                    json.dumps(
                        capture.document({"model": model}), ensure_ascii=False, indent=2
                    )
                    + "\n"
                )
            print(row["id"], row["passed"], row["errors"], flush=True)
        (HERE / "corrected-condor-answer.md").write_text(rows[0]["answer"] + "\n")
    checks = []
    for row, case in zip(rows, cases, strict=True):
        expected = case["expected"]
        # A clearly labelled, non-executable conditional fit is acceptable to
        # this UX regression, but is still NOT an exact-routing success above.
        status_ok = row["status"] == expected["status"] or (
            case["id"].startswith("condor-")
            and row["status"] == "fallback"
            and "not an exact semantic match" in row["answer"]
        )
        passed = (
            row["answer_passed"]
            and row["interaction_passed"]
            and status_ok
            and row["matched_actions"] == expected["actions"]
            and not row["safety_errors"]
            and row["action"] == "no_tool"
            and not row["should_execute"]
            and bool(row["clarification_question_asked"])
            == expected["require_clarification"]
        )
        if case["id"].startswith("condor-"):
            passed = passed and row["answer"].count("**CONDOR**") == 1
        checks.append(
            dict(
                id=row["id"],
                regression_passed=bool(passed),
                strict_routing_passed=row["passed"],
                status=row["status"],
            )
        )
        print(row["id"], "PASS" if passed else "FAIL", "routing:", row["status"])
    (HERE / ("replay-checks.json" if args.replay else "checks.json")).write_text(
        json.dumps(checks, indent=2) + "\n"
    )
    return 0 if len(checks) == 4 and all(r["regression_passed"] for r in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
