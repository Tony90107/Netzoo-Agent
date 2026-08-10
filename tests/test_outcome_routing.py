from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.contracts import RequestedOutcome, RouterDecision  # noqa: E402
from netzoo_agent_core.interpretation import (  # noqa: E402
    deterministic_router_fallback,
    hydrate_router_decision,
    repair_router_decision,
)


def test_router_schema_requires_an_explicit_outcome_classification():
    schema = RouterDecision.model_json_schema()

    assert "requested_outcome" in schema["required"]
    assert schema["properties"]["requested_outcome"]["description"].startswith(
        "Required classification field."
    )


def test_router_rejects_a_null_requested_outcome_from_the_provider():
    with pytest.raises(ValidationError, match="requested_outcome"):
        RouterDecision.model_validate(
            {
                "action": "no_tool",
                "in_scope": True,
                "intent_type": "answer_question",
                "confidence": 0.9,
                "reason": "provider omitted the classification",
                "requested_outcome": None,
            }
        )


def mirna_network_outcome() -> RequestedOutcome:
    return RequestedOutcome(
        operation="infer",
        artifact_type="regulatory_network",
        entity_types=["mirna", "gene"],
        display_entities=["miRNA", "gene"],
        regulator_types=["mirna"],
        target_types=["gene"],
        granularity="sample_specific",
        unresolved_dimensions=[],
    )


def mirna_measurement_outcome() -> RequestedOutcome:
    return RequestedOutcome(
        operation="acquire",
        artifact_type="measurement_dataset",
        entity_types=["mirna"],
        display_entities=["miRNA"],
        regulator_types=[],
        target_types=[],
        granularity="sample_specific",
        unresolved_dimensions=[],
    )


def test_router_outcome_is_descriptive_until_deterministic_repair():
    task = "Please build sample-specific miRNA-to-gene regulatory networks"
    hydrated = hydrate_router_decision(
        RouterDecision(
            action="run_puma",
            in_scope=True,
            intent_type="run_analysis",
            confidence=0.98,
            reason="proposed route",
            requested_outcome=mirna_network_outcome(),
        ),
        task,
    )

    assert hydrated.matched_actions == []
    assert hydrated.recommended_actions == []

    repaired = repair_router_decision(hydrated, task)
    assert repaired.action == "run_lioness_puma"
    assert repaired.matched_actions == ["run_lioness_puma"]
    assert repaired.recommended_actions == ["run_puma", "run_lioness_puma"]


def test_provider_failure_does_not_guess_an_unnamed_goal():
    decision = deterministic_router_fallback(
        "How can I obtain one miRNA dataset per patient?",
        TimeoutError(),
    )

    assert decision.action == "no_tool"
    assert decision.matched_actions == []
    assert decision.recommended_actions == []
    assert decision.clarification_question is not None


def test_provider_failure_preserves_explicit_named_workflow_information():
    decision = deterministic_router_fallback(
        "What inputs does PUMA require?",
        TimeoutError(),
    )

    assert decision.action == "no_tool"
    assert decision.should_execute is False
    assert decision.matched_actions == ["run_puma"]
    assert decision.recommended_actions == ["run_puma"]


@pytest.mark.parametrize(
    "task",
    [
        "How can I obtain one miRNA dataset per patient?",
        "我想取得每個樣本的 miRNA 原始資料，需要什麼工具？",
        "I need individual-level micro RNA measurements, not a network.",
    ],
)
def test_language_variations_cannot_promote_measurements_to_networks(task):
    hydrated = hydrate_router_decision(
        RouterDecision(
            action="run_lioness_puma",
            in_scope=True,
            intent_type="answer_question",
            confidence=0.99,
            reason="incorrect related workflow proposal",
            requested_outcome=mirna_measurement_outcome(),
        ),
        task,
    )

    repaired = repair_router_decision(hydrated, task)

    assert repaired.action == "no_tool"
    assert repaired.should_execute is False
    assert repaired.capability_match_status == "unsupported"
    assert repaired.matched_actions == []
    assert repaired.recommended_actions == []
    assert repaired.alternative_actions[0] == "run_lioness_puma"


@pytest.mark.parametrize(
    ("task", "should_execute"),
    [
        ("How do I infer per-sample miRNA-to-gene regulatory networks?", False),
        ("請建立每個樣本的微小 RNA 基因調控網路", True),
        ("Which workflow estimates individualized microRNA regulator-target edges?", False),
    ],
)
def test_language_variations_share_one_typed_network_match(task, should_execute):
    hydrated = hydrate_router_decision(
        RouterDecision(
            action="run_lioness_puma",
            in_scope=True,
            intent_type="run_analysis" if should_execute else "answer_question",
            confidence=0.99,
            reason="typed network outcome",
            requested_outcome=mirna_network_outcome(),
        ),
        task,
    )

    repaired = repair_router_decision(hydrated, task)

    assert repaired.should_execute is should_execute
    assert repaired.action == ("run_lioness_puma" if should_execute else "no_tool")
    assert repaired.capability_match_status == "exact"
    assert repaired.matched_actions == ["run_lioness_puma"]
    assert repaired.recommended_actions == ["run_puma", "run_lioness_puma"]


@pytest.mark.parametrize(
    "task",
    [
        "How can I obtain one miRNA dataset per patient?",
        "我想取得每個樣本的 miRNA 原始資料，需要什麼工具？",
        "Please build individualized microRNA regulator-target edges",
    ],
)
def test_provider_failure_never_guesses_unnamed_semantic_goals(task):
    decision = deterministic_router_fallback(task, TimeoutError())

    assert decision.action == "no_tool"
    assert decision.matched_actions == []
    assert decision.recommended_actions == []
    assert decision.clarification_question is not None
