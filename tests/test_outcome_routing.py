from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.contracts import RequestedOutcome, RouterDecision  # noqa: E402
from netzoo_agent_core.interpretation import (  # noqa: E402
    deterministic_router_fallback,
    hydrate_router_decision,
    repair_router_decision,
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
