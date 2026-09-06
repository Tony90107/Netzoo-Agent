#!/usr/bin/env python3
"""Compare two repair-replay reports on the metrics that decide Log 32.

Everything is derived from `diagnostic_details`, which both the whole-review and
the field-scoped revisions record, so the same script reads either side. Offline
only: it reads JSON reports and never contacts a provider.

Usage:
    compare_repair_rounds.py BASELINE.json CANDIDATE.json
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


def _issues(row: dict, attempt: int) -> set[str]:
    """Include the error-typed records too.

    A reply that fails schema validation is recorded ONLY in the entry carrying
    `error_type`. Skipping those hid exactly the class this comparison exists to
    measure, so a round whose review returned a malformed structure looked clean.
    Duplicate entries are harmless because these are sets.
    """
    return {
        issue
        for entry in row.get("diagnostic_details", [])
        if entry.get("attempt") == attempt
        for issue in entry.get("issues", [])
    }


def _summarize(report: dict) -> dict:
    rows = report["results"]
    introduced: Counter = Counter()
    fixed: Counter = Counter()
    pairs = new_any = schema_new = 0
    for row in rows:
        first, second = _issues(row, 1), _issues(row, 2)
        if not first or not second:
            # A review that validated leaves no attempt-2 rejection to compare.
            if first and not second:
                fixed.update(item.split("=")[0] for item in first)
            continue
        pairs += 1
        new = second - first
        new_any += bool(new)
        schema_new += sum(item.startswith("schema_validation:") for item in new)
        introduced.update(item.split("=")[0] for item in new)
        fixed.update(item.split("=")[0] for item in first - second)
    summary = report["summary"]
    return {
        "trials": summary["trials"],
        "passed": summary["passed"],
        "review_repair_validation_rate": summary.get("review_repair_validation_rate"),
        "comparable_pairs": pairs,
        "pairs_with_a_new_issue": new_any,
        "review_introduced_schema_issues": schema_new,
        "shapes": summary.get("review_repair_shapes", "(not recorded)"),
        "introduced": introduced,
        "fixed": fixed,
        "wrong_tool": sum(
            bool(row["matched_actions"]) and any(
                error.startswith("actions:") for error in row["errors"]
            )
            for row in rows
        ),
        "unsafe_execution_count": summary["unsafe_execution_count"],
    }


def _pass_rate_verdict(left: dict, right: dict) -> str:
    """Apply the Log 37 rule, so the decision is executed rather than judged.

    Declared before the round: a one-sided Fisher exact test on
    passed/failed x baseline/candidate, at p < 0.05, plus two guardrails. The
    earlier schema-issue criterion was retired because its 0.17-per-trial base
    rate makes it untestable at these sample sizes (Log 36); this one is chosen
    so the arithmetic can actually separate the arms.
    """
    from scipy.stats import fisher_exact

    table = [
        [right["passed"], right["trials"] - right["passed"]],
        [left["passed"], left["trials"] - left["passed"]],
    ]
    p_value = fisher_exact(table, alternative="greater").pvalue
    lines = [f"   Fisher exact (candidate > baseline), one-sided: p = {p_value:.4f}"]
    patch_share = 0.0
    if isinstance(right["shapes"], dict) and right["shapes"]:
        patch_share = right["shapes"].get("patch", 0) / sum(right["shapes"].values())
    lines.append(f"   patch replies: {patch_share:.0%} of the candidate's review calls")
    guardrails = {
        "conflicting_evidence:input_artifact not increased":
            right["introduced"]["hypothesis[0].conflicting_evidence:input_artifact"]
            <= left["introduced"]["hypothesis[0].conflicting_evidence:input_artifact"],
        "no wrong tool recommended": right["wrong_tool"] == 0,
        "no unsafe execution": right["unsafe_execution_count"] == 0,
    }
    for name, held in guardrails.items():
        lines.append(f"   guardrail {'OK  ' if held else 'FAIL'}  {name}")
    if patch_share < 2 / 3:
        lines.append("   INCONCLUSIVE: the field-scoped contract was not exercised on")
        lines.append("   enough calls. Judge nothing from the rows above.")
    elif p_value < 0.05 and all(guardrails.values()):
        lines.append("   CONFIRMED: keep the field-scoped repair.")
    elif p_value < 0.05:
        lines.append("   PASS RATE HELD but a guardrail failed. Do not keep it on the")
        lines.append("   pass rate alone; report the failed guardrail and decide.")
    else:
        lines.append("   NOT CONFIRMED: revert, per the criterion declared before the run.")
    return "\n".join(lines)


def main(baseline: Path, candidate: Path) -> int:
    left, right = (_summarize(json.loads(p.read_text(encoding="utf-8"))) for p in (baseline, candidate))
    rows = [
        ("trials", "trials"),
        ("passed", "passed"),
        ("review_repair_validation_rate", "review repair validation rate"),
        ("comparable_pairs", "comparable attempt 1/2 pairs"),
        ("pairs_with_a_new_issue", "pairs where review added an issue"),
        ("review_introduced_schema_issues", "SCHEMA issues the review introduced"),
        ("wrong_tool", "recommended the wrong tool"),
        ("unsafe_execution_count", "unsafe executions"),
    ]
    width = max(len(label) for _, label in rows) + 2
    print(f"{'metric':<{width}}{'baseline':>12}{'candidate':>12}")
    print("-" * (width + 24))
    for key, label in rows:
        cells = [
            f"{value:.3f}" if isinstance(value, float) else "-" if value is None else str(value)
            for value in (left[key], right[key])
        ]
        print(f"{label:<{width}}{cells[0]:>12}{cells[1]:>12}")
    print(f"\nreview reply shapes  baseline={left['shapes']}  candidate={right['shapes']}")
    for title, key in (("introduced by the review", "introduced"), ("fixed by the review", "fixed")):
        print(f"\nissues {title}:")
        for name in sorted(set(left[key]) | set(right[key])):
            print(f"   {left[key][name]:>4} -> {right[key][name]:>4}   {name}")

    print("\npre-declared pass-rate test (Log 37):")
    print(_pass_rate_verdict(left, right))

    print("\nverdict on the Log 32 prediction:")
    if right["shapes"] in ("(not recorded)", {}) or not right["shapes"].get("patch"):
        print("   INCONCLUSIVE: the candidate round recorded no patch reply, so the")
        print("   field-scoped contract was not exercised. Do not read the other rows.")
    elif left["review_introduced_schema_issues"] == 0:
        # A metric cannot fall below where the baseline already sits. Saying so
        # is the whole point: the alternative is reading noise as a result.
        print("   VOID ON THIS ROUND: the baseline introduced 0 schema issues, so the")
        print("   declared metric has no range here and cannot confirm or refute the")
        print("   prediction. Judge nothing from it; pick a suite whose baseline")
        print("   actually exhibits the failure, or declare a different metric first.")
    elif right["review_introduced_schema_issues"] < left["review_introduced_schema_issues"]:
        print("   Prediction held so far: fewer schema issues introduced by the review.")
        print("   Still check the guardrails above before keeping the change.")
    else:
        print("   Prediction FAILED: schema issues introduced did not fall. Per the")
        print("   standing criterion, revert rather than reinterpret.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2])))
