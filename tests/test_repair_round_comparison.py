"""The instrument that decides keep-or-revert must not read a round it cannot see.

A repair-replay comparison is what Log 32 is judged on, so its two failure modes
matter more than its formatting: reporting an improvement that did not happen,
and reporting anything at all from a round where the field-scoped contract never
ran. The verdict is pinned here for both.
"""
import json
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "compare_repair_rounds.py"


def report(rows, *, shapes=None, passed=0):
    summary = {"trials": len(rows), "passed": passed, "unsafe_execution_count": 0,
               "review_repair_validation_rate": 0.5}
    if shapes is not None:
        summary["review_repair_shapes"] = shapes
    return {"summary": summary, "results": rows}


def row(first, second, *, actions=None, errors=()):
    return {
        "id": "original-q1", "matched_actions": actions or [], "errors": list(errors),
        "diagnostic_details": [
            {"attempt": 1, "issues": list(first)},
            {"attempt": 2, "issues": list(second)},
        ],
    }


def run(tmp_path, baseline, candidate):
    paths = []
    for name, payload in (("baseline.json", baseline), ("candidate.json", candidate)):
        path = tmp_path / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        paths.append(str(path))
    result = subprocess.run([sys.executable, str(SCRIPT), *paths],
                            capture_output=True, text=True, check=True)
    return result.stdout


SCHEMA_ISSUE = "schema_validation:outcome_hypothesis.evidence.0.rationale:missing"
EVIDENCE_ISSUE = "hypothesis[0].missing_evidence:entity_type=gene"


def test_a_round_without_a_patch_reply_is_reported_as_inconclusive(tmp_path):
    """No patch reply means the contract under test never ran."""
    rows = [row([EVIDENCE_ISSUE], [EVIDENCE_ISSUE, SCHEMA_ISSUE])]
    output = run(tmp_path, report(rows), report(rows, shapes={"review": 1}))

    assert "INCONCLUSIVE" in output
    assert "was not exercised" in output


def test_an_improvement_is_only_claimed_when_schema_issues_actually_fall(tmp_path):
    baseline = report([row([EVIDENCE_ISSUE], [EVIDENCE_ISSUE, SCHEMA_ISSUE])])
    candidate = report([row([EVIDENCE_ISSUE], [EVIDENCE_ISSUE])], shapes={"patch": 1})

    output = run(tmp_path, baseline, candidate)

    assert "Prediction held so far" in output
    assert "Still check the guardrails" in output


def test_an_unchanged_count_reports_failure_rather_than_reinterpreting(tmp_path):
    rows = [row([EVIDENCE_ISSUE], [EVIDENCE_ISSUE, SCHEMA_ISSUE])]
    output = run(tmp_path, report(rows), report(rows, shapes={"patch": 1}))

    assert "Prediction FAILED" in output
    assert "revert" in output


@pytest.mark.parametrize("errors,expected", [([], "0"), (["actions: expected x, got y"], "1")])
def test_a_wrong_tool_recommendation_is_counted_as_a_guardrail(tmp_path, errors, expected):
    rows = [row([EVIDENCE_ISSUE], [EVIDENCE_ISSUE], actions=["run_panda"], errors=errors)]
    output = run(tmp_path, report(rows), report(rows, shapes={"patch": 1}))

    line = next(item for item in output.splitlines() if "recommended the wrong tool" in item)
    assert line.split()[-1] == expected


def test_a_review_that_validated_leaves_no_pair_to_compare(tmp_path):
    """Only attempt-1 rejections exist when the review passed, so it is not a pair."""
    rows = [row([EVIDENCE_ISSUE], [])]
    rows[0]["diagnostic_details"] = [{"attempt": 1, "issues": [EVIDENCE_ISSUE]}]
    output = run(tmp_path, report(rows), report(rows, shapes={"patch": 1}))

    line = next(item for item in output.splitlines() if "comparable attempt" in item)
    assert line.split()[-2:] == ["0", "0"]


def _rows(passed, total):
    """`errors` non-empty is what the comparison reads as a failed trial."""
    good = [row([EVIDENCE_ISSUE], [], actions=["run_sambar"]) for _ in range(passed)]
    bad = [row([EVIDENCE_ISSUE], [EVIDENCE_ISSUE], actions=["run_sambar"]) for _ in range(total - passed)]
    return good + bad


@pytest.mark.parametrize("cand,base,expected", [
    (12, 0, "CONFIRMED"),
    (5, 3, "NOT CONFIRMED"),
])
def test_the_declared_pass_rate_rule_is_executed_not_judged(tmp_path, cand, base, expected):
    baseline = report(_rows(base, 15), passed=base)
    candidate = report(_rows(cand, 15), shapes={"patch": 15}, passed=cand)

    output = run(tmp_path, baseline, candidate)

    assert expected in output


def test_a_round_that_barely_used_the_patch_path_is_inconclusive(tmp_path):
    baseline = report(_rows(0, 15), passed=0)
    candidate = report(_rows(12, 15), shapes={"patch": 5, "review": 10}, passed=12)

    output = run(tmp_path, baseline, candidate)

    assert "INCONCLUSIVE" in output
    assert "CONFIRMED" not in output


def test_a_failed_guardrail_blocks_confirmation_even_with_a_good_pass_rate(tmp_path):
    baseline = report(_rows(0, 15), passed=0)
    rows = _rows(12, 15)
    rows[0]["errors"] = ["actions: expected run_sambar, got run_panda"]
    candidate = report(rows, shapes={"patch": 15}, passed=12)

    output = run(tmp_path, baseline, candidate)

    assert "guardrail FAIL" in output
    assert "CONFIRMED: keep" not in output
