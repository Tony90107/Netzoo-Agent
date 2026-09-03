"""Keep the documented Planner evaluation command inside pytest coverage."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from evaluate_harness import PROJECT_ROOT, evaluate  # noqa: E402
from netzoo_agent_core.contracts import RequestedOutcome  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_requested_outcome  # noqa: E402


def scenarios():
    return json.loads((PROJECT_ROOT / "tests/harness_scenarios.json").read_text())


def test_documented_planner_corpus_passes_current_contracts():
    report = evaluate(scenarios())

    assert report["summary"]["passed"] == report["summary"]["scenarios"], report["results"]


def test_unsupported_planner_fixture_matches_the_upstream_scientific_contract():
    case = next(item for item in scenarios() if item["name"] == "unsupported_variant_calling")
    result = match_requested_outcome(RequestedOutcome.model_validate(case["decision"]["requested_outcome"]))

    assert result.status == case["decision"]["capability_match_status"] == "unsupported"
    assert result.matched_actions == []
    assert case["decision"]["action"] == "no_tool"
    assert not case["decision"]["should_execute"]


def test_unconfirmed_inputs_cannot_pass_by_status_alone(monkeypatch):
    case = copy.deepcopy(scenarios()[0])
    case["expected_status"] = "needs_confirmation"
    case["expected_values"] = {"should_execute": False}
    case["expected_steps"] = []
    monkeypatch.setattr("evaluate_harness.build_workflow_plan", lambda *_a, **_kw: SimpleNamespace(
        status="needs_confirmation", decision={"should_execute": False}, missing_inputs=[],
        steps=[SimpleNamespace(action="run_lioness_panda")],
    ))

    report = evaluate([case])

    assert report["summary"]["passed"] == 0
    assert "steps" in " ".join(report["results"][0]["errors"])


def test_confirmation_bypass_is_counted_as_unsafe_autofill(monkeypatch):
    case = copy.deepcopy(scenarios()[0])
    case["expected_status"] = "needs_confirmation"
    monkeypatch.setattr("evaluate_harness.build_workflow_plan", lambda *_a, **_kw: SimpleNamespace(
        status="ready", decision={}, missing_inputs=[], steps=[],
    ))

    assert evaluate([case])["summary"]["unsafe_autofill_count"] == 1


def test_empty_planner_evaluation_cannot_look_successful():
    with pytest.raises(ValueError):
        evaluate([])
