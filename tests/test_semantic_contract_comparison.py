"""Promotion guardrails for the experimental semantic claims contract."""

from __future__ import annotations

import sys
from copy import deepcopy
from json import dumps
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from compare_semantic_contracts import compare_contract_reports, main  # noqa: E402


def report(contract: str) -> dict:
    rows = [
        {
            "id": f"case-{index % 3}",
            "trial": index // 3 + 1,
            "passed": True,
            "route_passed": True,
            "semantic_passed": True,
            "matched_actions": ["run_sambar"],
            "errors": [],
            "safety_errors": [],
            "diagnostic_details": [],
        }
        for index in range(9)
    ]
    return {
        "metadata": {
            "source": "live",
            "model": "openai/gpt-4o-mini",
            "temperature": 0.0,
            "semantic_contract": contract,
            "review_policy": "when_needed",
            "first_pass_source": "live",
            "corpus_sha256": "same-corpus",
            "repeat": 3,
        },
        "summary": {
            "trials": 9,
            "passed": 9,
            "pass_rate": 1.0,
            "route_pass_rate": 1.0,
            "semantic_pass_rate": 1.0,
            "unsafe_execution_count": 0,
            "provider_calls": 18,
            "review_repair_attempts": 0,
            "review_introduced_schema_issues": 0,
        },
        "results": rows,
    }


def test_equal_safe_claims_report_passes_every_promotion_guardrail():
    legacy = report("legacy")
    claims = deepcopy(report("claims"))

    verdict = compare_contract_reports(legacy, claims, interleaved=True)

    assert verdict["comparable"]
    assert verdict["promotion_ready"]
    assert all(item["passed"] for item in verdict["guardrails"].values())


def test_silence_is_not_misreported_as_a_wrong_tool_recommendation():
    legacy = report("legacy")
    claims = deepcopy(report("claims"))
    claims["results"][0]["matched_actions"] = []
    claims["results"][0]["errors"] = [
        "actions: expected ['run_sambar'], got []"
    ]

    verdict = compare_contract_reports(legacy, claims, interleaved=True)

    assert verdict["metrics"]["claims"]["wrong_tool"] == 0
    assert verdict["guardrails"]["no_wrong_tool"]["passed"]


def test_wrong_tool_recommendation_blocks_promotion():
    legacy = report("legacy")
    claims = deepcopy(report("claims"))
    claims["results"][0]["matched_actions"] = ["run_bonobo"]
    claims["results"][0]["errors"] = [
        "actions: expected ['run_sambar'], got ['run_bonobo']"
    ]

    verdict = compare_contract_reports(legacy, claims, interleaved=True)

    assert verdict["metrics"]["claims"]["wrong_tool"] == 1
    assert not verdict["guardrails"]["no_wrong_tool"]["passed"]
    assert not verdict["promotion_ready"]
    assert "no_wrong_tool" in verdict["blockers"]


def test_sequential_reports_cannot_claim_promotion_readiness():
    verdict = compare_contract_reports(report("legacy"), report("claims"))

    assert verdict["guardrails_passed"]
    assert not verdict["promotion_ready"]
    assert "interleaved_execution_not_attested" in verdict["blockers"]


def test_mismatched_corpus_is_rejected_before_metrics_are_compared():
    legacy = report("legacy")
    claims = report("claims")
    claims["metadata"]["corpus_sha256"] = "different-corpus"

    with pytest.raises(ValueError, match="corpus_sha256"):
        compare_contract_reports(legacy, claims, interleaved=True)


def test_same_counts_with_different_case_trials_are_not_matched_reports():
    legacy = report("legacy")
    claims = report("claims")
    claims["results"][0]["id"] = "different-case"

    with pytest.raises(ValueError, match="case/trial identities"):
        compare_contract_reports(legacy, claims, interleaved=True)


def test_stale_summary_is_rejected_instead_of_overriding_trial_results():
    legacy = report("legacy")
    claims = report("claims")
    claims["results"][0]["passed"] = False

    with pytest.raises(ValueError, match="summary.passed"):
        compare_contract_reports(legacy, claims, interleaved=True)


def test_cli_reads_reports_and_emits_a_promotion_verdict(tmp_path, capsys):
    legacy_path = tmp_path / "legacy.json"
    claims_path = tmp_path / "claims.json"
    legacy_path.write_text(dumps(report("legacy")), encoding="utf-8")
    claims_path.write_text(dumps(report("claims")), encoding="utf-8")

    exit_code = main([str(legacy_path), str(claims_path), "--interleaved"])

    assert exit_code == 0
    assert '"promotion_ready": true' in capsys.readouterr().out
