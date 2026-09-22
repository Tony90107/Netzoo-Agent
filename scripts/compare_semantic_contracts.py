#!/usr/bin/env python3
"""Compare matched legacy/claims routing reports before changing the default.

This is an offline promotion gate. It reads reports produced by
``evaluate_routing.py`` and never calls a provider. A passing result means the
candidate met the declared non-regression guardrails on this corpus; it is not a
claim of general model quality or statistical significance.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


_COMPARABLE_METADATA = (
    "source",
    "model",
    "temperature",
    "review_policy",
    "first_pass_source",
    "corpus_sha256",
    "repeat",
)
_TERMINAL_ERROR_PREFIXES = (
    "input_artifacts:",
    "artifact_type:",
    "granularity:",
    "entity_types:",
    "discriminator:",
    "request_mode:",
)


def _count_rows(report: dict[str, Any], field: str) -> int:
    return sum(bool(row.get(field)) for row in report.get("results", []))


def _wrong_tool_count(report: dict[str, Any]) -> int:
    return sum(
        bool(row.get("matched_actions"))
        and any(
            str(error).startswith("actions:") for error in row.get("errors", [])
        )
        for row in report.get("results", [])
    )


def _terminal_goal_error_count(report: dict[str, Any]) -> int:
    return sum(
        str(error).startswith(_TERMINAL_ERROR_PREFIXES)
        for row in report.get("results", [])
        for error in row.get("errors", [])
    )


def _conflicting_evidence_count(report: dict[str, Any]) -> int:
    return sum(
        ".conflicting_evidence:" in str(issue)
        for row in report.get("results", [])
        for entry in row.get("diagnostic_details", [])
        for issue in entry.get("issues", [])
    )


def _metrics(report: dict[str, Any]) -> dict[str, int]:
    summary = report.get("summary", {})
    return {
        "trials": int(summary.get("trials", len(report.get("results", [])))),
        "passed": int(summary.get("passed", _count_rows(report, "passed"))),
        "route_passed": _count_rows(report, "route_passed"),
        "semantic_passed": _count_rows(report, "semantic_passed"),
        "wrong_tool": _wrong_tool_count(report),
        "unsafe_execution": int(summary.get("unsafe_execution_count", 0)),
        "terminal_goal_errors": _terminal_goal_error_count(report),
        "conflicting_evidence": _conflicting_evidence_count(report),
        "provider_calls": int(summary.get("provider_calls", 0)),
        "repair_attempts": int(summary.get("review_repair_attempts", 0)),
        "review_introduced_schema_issues": int(
            summary.get("review_introduced_schema_issues", 0)
        ),
    }


def _case_trial_identities(report: dict[str, Any]) -> Counter[tuple[str, int]]:
    identities: Counter[tuple[str, int]] = Counter()
    for row in report.get("results", []):
        if "id" not in row or "trial" not in row:
            raise ValueError(
                "Reports are not comparable: every result needs case/trial identities"
            )
        identities[(str(row["id"]), int(row["trial"]))] += 1
    return identities


def _validate_report_integrity(report: dict[str, Any]) -> None:
    results = report.get("results", [])
    summary = report.get("summary", {})
    actual_trials = len(results)
    if "trials" in summary and int(summary["trials"]) != actual_trials:
        raise ValueError(
            "Report integrity error: summary.trials does not match results"
        )
    actual_passed = _count_rows(report, "passed")
    if "passed" in summary and int(summary["passed"]) != actual_passed:
        raise ValueError(
            "Report integrity error: summary.passed does not match results"
        )
    identities = _case_trial_identities(report)
    if any(count != 1 for count in identities.values()):
        raise ValueError("Report integrity error: duplicate case/trial identities")


def _guardrail(
    baseline: int,
    candidate: int,
    *,
    passed: bool,
) -> dict[str, int | bool]:
    return {"baseline": baseline, "candidate": candidate, "passed": passed}


def compare_contract_reports(
    legacy: dict[str, Any],
    claims: dict[str, Any],
    *,
    interleaved: bool = False,
) -> dict[str, Any]:
    """Return a machine-readable non-regression verdict for matched reports."""
    left_meta = legacy.get("metadata", {})
    right_meta = claims.get("metadata", {})
    if left_meta.get("semantic_contract") != "legacy":
        raise ValueError("Baseline report must use semantic_contract=legacy")
    if right_meta.get("semantic_contract") != "claims":
        raise ValueError("Candidate report must use semantic_contract=claims")
    mismatches = {
        key: {"legacy": left_meta.get(key), "claims": right_meta.get(key)}
        for key in _COMPARABLE_METADATA
        if left_meta.get(key) != right_meta.get(key)
    }
    if mismatches:
        raise ValueError(
            "Reports are not comparable: " + ", ".join(sorted(mismatches))
        )
    if left_meta.get("source") != "live":
        raise ValueError("Promotion evidence must come from live reports")

    _validate_report_integrity(legacy)
    _validate_report_integrity(claims)
    if _case_trial_identities(legacy) != _case_trial_identities(claims):
        raise ValueError("Reports are not comparable: case/trial identities")

    left = _metrics(legacy)
    right = _metrics(claims)
    if left["trials"] != right["trials"]:
        raise ValueError("Reports are not comparable: trials")

    guardrails = {
        "pass_count_not_lower": _guardrail(
            left["passed"], right["passed"], passed=right["passed"] >= left["passed"]
        ),
        "route_pass_count_not_lower": _guardrail(
            left["route_passed"], right["route_passed"],
            passed=right["route_passed"] >= left["route_passed"],
        ),
        "semantic_pass_count_not_lower": _guardrail(
            left["semantic_passed"], right["semantic_passed"],
            passed=right["semantic_passed"] >= left["semantic_passed"],
        ),
        "no_wrong_tool": _guardrail(
            left["wrong_tool"], right["wrong_tool"], passed=right["wrong_tool"] == 0
        ),
        "no_unsafe_execution": _guardrail(
            left["unsafe_execution"], right["unsafe_execution"],
            passed=right["unsafe_execution"] == 0,
        ),
        "terminal_goal_errors_not_increased": _guardrail(
            left["terminal_goal_errors"], right["terminal_goal_errors"],
            passed=right["terminal_goal_errors"] <= left["terminal_goal_errors"],
        ),
        "conflicting_evidence_not_increased": _guardrail(
            left["conflicting_evidence"], right["conflicting_evidence"],
            passed=right["conflicting_evidence"] <= left["conflicting_evidence"],
        ),
        "provider_calls_not_increased": _guardrail(
            left["provider_calls"], right["provider_calls"],
            passed=right["provider_calls"] <= left["provider_calls"],
        ),
        "repair_attempts_not_increased": _guardrail(
            left["repair_attempts"], right["repair_attempts"],
            passed=right["repair_attempts"] <= left["repair_attempts"],
        ),
        "no_review_introduced_schema_issues": _guardrail(
            left["review_introduced_schema_issues"],
            right["review_introduced_schema_issues"],
            passed=right["review_introduced_schema_issues"] == 0,
        ),
    }
    guardrails_passed = all(item["passed"] for item in guardrails.values())
    repeated = int(left_meta.get("repeat", 0)) >= 3
    promotion_ready = guardrails_passed and interleaved and repeated
    blockers = [name for name, item in guardrails.items() if not item["passed"]]
    if not interleaved:
        blockers.append("interleaved_execution_not_attested")
    if not repeated:
        blockers.append("fewer_than_three_repetitions")
    return {
        "comparable": True,
        "guardrails_passed": guardrails_passed,
        "promotion_ready": promotion_ready,
        "interleaved": interleaved,
        "repetitions": left_meta.get("repeat"),
        "blockers": blockers,
        "metrics": {"legacy": left, "claims": right},
        "guardrails": guardrails,
        "scope": (
            "routing-only; execution and biological outputs remain unevaluated"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("legacy", type=Path)
    parser.add_argument("claims", type=Path)
    parser.add_argument(
        "--interleaved",
        action="store_true",
        help="Attest that the two arms were run in an interleaved schedule.",
    )
    args = parser.parse_args(argv)
    try:
        reports = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in (args.legacy, args.claims)
        ]
        verdict = compare_contract_reports(
            reports[0], reports[1], interleaved=args.interleaved
        )
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Semantic contract comparison error: {error}")
        return 2
    print(json.dumps(verdict, ensure_ascii=False, indent=2))
    return 0 if verdict["promotion_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
