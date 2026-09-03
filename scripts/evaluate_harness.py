#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from netzoo_agent import (  # noqa: E402
    ProjectPolicyLoader,
    TaskDecision,
    build_workflow_plan,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate deterministic NetZoo harness scenarios.")
    parser.add_argument(
        "--scenarios",
        type=Path,
        default=PROJECT_ROOT / "tests" / "harness_scenarios.json",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def evaluate(scenarios: list[dict]) -> dict:
    if not scenarios:
        raise ValueError("Planner evaluation requires at least one scenario.")
    project_policy = ProjectPolicyLoader(PROJECT_ROOT).load()
    results = []
    status_correct = 0
    value_checks = 0
    value_correct = 0
    missing_checks = 0
    missing_correct = 0
    unsafe_autofill = 0
    unnecessary_questions = 0

    for scenario in scenarios:
        decision = TaskDecision.model_validate(scenario["decision"])
        plan = build_workflow_plan(
            decision,
            scenario["task"],
            project_policy=project_policy,
        )
        errors = []
        if plan.status == scenario["expected_status"]:
            status_correct += 1
        else:
            errors.append(f"status={plan.status}, expected={scenario['expected_status']}")

        for field_name, expected in scenario.get("expected_values", {}).items():
            value_checks += 1
            actual = plan.decision.get(field_name)
            if actual == expected:
                value_correct += 1
            else:
                errors.append(f"{field_name}={actual}, expected={expected}")

        for field_name in scenario.get("expected_missing", []):
            missing_checks += 1
            if field_name in plan.missing_inputs:
                missing_correct += 1
            else:
                errors.append(f"expected missing field was resolved: {field_name}")

        if "expected_steps" in scenario:
            actual_steps = [step.action for step in plan.steps]
            if actual_steps != scenario["expected_steps"]:
                errors.append(f"steps={actual_steps}, expected={scenario['expected_steps']}")

        if scenario["expected_status"] in {"needs_input", "needs_confirmation"} and plan.status == "ready":
            unsafe_autofill += 1
        if scenario["expected_status"] == "ready" and plan.status == "needs_input":
            unnecessary_questions += 1
        results.append({"name": scenario["name"], "passed": not errors, "errors": errors})

    total = len(scenarios)
    passed = sum(1 for result in results if result["passed"])
    return {
        "summary": {
            "scenarios": total,
            "passed": passed,
            "scenario_pass_rate": passed / total if total else 0.0,
            "plan_status_accuracy": status_correct / total if total else 0.0,
            "input_resolution_accuracy": value_correct / value_checks if value_checks else 1.0,
            "missing_input_accuracy": missing_correct / missing_checks if missing_checks else 1.0,
            "unnecessary_question_count": unnecessary_questions,
            "unsafe_autofill_count": unsafe_autofill,
            "policy_hash": project_policy.policy_hash,
        },
        "results": results,
    }


def main() -> int:
    args = parse_args()
    scenarios = json.loads(args.scenarios.read_text(encoding="utf-8"))
    report = evaluate(scenarios)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for result in report["results"]:
            marker = "PASS" if result["passed"] else "FAIL"
            print(f"[{marker}] {result['name']}")
            for error in result["errors"]:
                print(f"  - {error}")
        print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 0 if report["summary"]["passed"] == report["summary"]["scenarios"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
