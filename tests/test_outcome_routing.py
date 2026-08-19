from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.contracts import (  # noqa: E402
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
    RouterDecision,
    TaskDecision,
)
from netzoo_agent_core.interpretation import (  # noqa: E402
    deterministic_router_fallback,
    hydrate_router_decision,
    repair_router_decision,
)
from netzoo_agent_core.interpretation.outcome_consistency import (  # noqa: E402
    needs_outcome_repair,
    select_primary_hypothesis,
)
from netzoo_agent_core.llm import (  # noqa: E402
    build_router_repair_messages,
    build_routing_prompt,
)
from netzoo_agent_core.routing.outcome_matching import (  # noqa: E402
    match_outcome_hypotheses,
)
from netzoo_agent_core.settings import DEFAULT_ROUTER_MAX_TOKENS  # noqa: E402


def test_router_schema_allows_a_repairable_empty_outcome_classification():
    schema = RouterDecision.model_json_schema()

    assert "outcome_hypotheses" not in schema["required"]
    assert schema["properties"]["outcome_hypotheses"]["maxItems"] == 3


def test_router_reason_allows_bounded_repair_explanations():
    reason = "r" * 450

    decision = RouterDecision(
        action="no_tool",
        in_scope=True,
        intent_type="answer_question",
        confidence=0.9,
        reason=reason,
    )

    assert decision.reason == reason
    assert RouterDecision.model_json_schema()["properties"]["reason"][
        "maxLength"
    ] == 600


def test_router_budget_and_prompt_support_bounded_partial_hypotheses():
    assert DEFAULT_ROUTER_MAX_TOKENS >= 1_200
    source = inspect.getsource(build_routing_prompt)
    assert "Prefer one partial" in source
    assert "deterministic matcher will enumerate compatible" in source
    assert "Keep reason under 500 characters" in source


def test_router_repairs_an_omitted_outcome_hypothesis():
    decision = RouterDecision.model_validate(
        {
            "action": "no_tool",
            "in_scope": True,
            "intent_type": "answer_question",
            "confidence": 0.9,
            "reason": "provider omitted the classification",
        }
    )

    assert decision.outcome_hypotheses == []
    assert needs_outcome_repair(decision.outcome_hypotheses) is True


def test_router_repairs_an_empty_outcome_even_if_provider_marks_it_out_of_scope():
    decision = RouterDecision.model_validate(
        {
            "action": "no_tool",
            "in_scope": False,
            "intent_type": "unknown",
            "confidence": 0.9,
            "reason": "provider incorrectly rejected the domain goal",
        }
    )

    assert needs_outcome_repair(decision.outcome_hypotheses) is True


def test_router_normalizes_a_provider_hypothesis_with_flattened_outcome_fields():
    decision = RouterDecision.model_validate(
        {
            "action": "no_tool",
            "in_scope": True,
            "intent_type": "answer_question",
            "confidence": 0.9,
            "reason": "The request describes a sample-specific miRNA network.",
            "outcome_hypotheses": [
                {
                    "operation": "infer",
                    "artifact_type": "regulatory_network",
                    "entity_types": ["mirna", "gene"],
                    "regulator_types": ["mirna"],
                    "target_types": ["gene"],
                    "granularity": "sample_specific",
                    "unresolved_dimensions": ["confirmation"],
                    "confidence": 0.9,
                    "evidence": [],
                    "assumptions": ["Confirm the network interpretation."],
                }
            ],
        }
    )

    assert decision.outcome_hypotheses[0].outcome.regulator_types == ["mirna"]
    assert decision.outcome_hypotheses[0].outcome.granularity == "sample_specific"


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


def hypothesis(
    *,
    outcome: RequestedOutcome | None = None,
    confidence: float = 0.9,
    evidence: list[OutcomeEvidence] | None = None,
    assumptions: list[str] | None = None,
) -> OutcomeHypothesis:
    return OutcomeHypothesis(
        outcome=outcome or mirna_network_outcome(),
        confidence=confidence,
        evidence=evidence
        or [
            OutcomeEvidence(
                dimension="regulator_type",
                value="mirna",
                source="explicit",
                rationale="The request explicitly names miRNA.",
            )
        ],
        assumptions=assumptions or [],
    )


def test_task_decision_keeps_hypotheses_separate_from_exact_matches():
    item = hypothesis(assumptions=["network means regulatory network"])

    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        confidence=0.9,
        reason="advisory hypothesis",
        outcome_hypotheses=[item],
        hypothesis_actions=["run_lioness_puma"],
    )

    assert decision.requested_outcome is None
    assert decision.matched_actions == []
    assert decision.hypothesis_actions == ["run_lioness_puma"]


def unknown_hypothesis() -> OutcomeHypothesis:
    return OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="unknown",
            artifact_type="unknown",
            granularity="not_applicable",
            unresolved_dimensions=[],
        ),
        confidence=0.9,
        evidence=[],
        assumptions=[],
    )


def test_semantically_empty_classifications_always_get_one_repair_attempt():
    assert needs_outcome_repair([unknown_hypothesis()]) is True


def test_tied_hypotheses_have_no_primary_outcome():
    first = hypothesis(confidence=0.9)
    second = hypothesis(
        confidence=0.9,
        assumptions=["co-expression interpretation"],
    )

    assert select_primary_hypothesis([first, second]) is None


def test_router_repair_prompt_preserves_request_and_structured_failure():
    first_decision = RouterDecision(
        action="no_tool",
        in_scope=True,
        intent_type="answer_question",
        confidence=0.9,
        reason="under-classified",
        outcome_hypotheses=[unknown_hypothesis()],
    )
    request = "Which method can infer an individualized regulator graph?"

    messages = build_router_repair_messages(
        "validated routing policy",
        request,
        first_decision,
    )
    combined = "\n".join(str(message.content) for message in messages)

    assert request in combined
    assert "under-classified" in combined
    assert "Return one to three evidence-bearing hypotheses" in combined
    assert "if i want to get sample specific network data" not in combined.casefold()


def test_router_outcome_is_descriptive_until_deterministic_repair():
    task = "Please build sample-specific miRNA-to-gene regulatory networks"
    hydrated = hydrate_router_decision(
        RouterDecision(
            action="run_puma",
            in_scope=True,
            intent_type="run_analysis",
            confidence=0.98,
            reason="proposed route",
            outcome_hypotheses=[hypothesis()],
        ),
        task,
    )

    assert hydrated.matched_actions == []
    assert hydrated.recommended_actions == []

    repaired = repair_router_decision(hydrated, task)
    assert repaired.action == "run_lioness_puma"
    assert repaired.matched_actions == ["run_lioness_puma"]
    assert repaired.recommended_actions == ["run_puma", "run_lioness_puma"]


def test_repair_preserves_semantic_read_only_discovery_route():
    decision = TaskDecision(
        action="discover_workspace_resources",
        in_scope=True,
        should_execute=True,
        intent_type="inspect_input",
        confidence=0.93,
        reason="Inspect local workspace resources.",
    )

    repaired = repair_router_decision(
        decision,
        "Can you inspect what compatible data is available?",
    )

    assert repaired.action == "discover_workspace_resources"
    assert repaired.should_execute is True


def test_hydration_preserves_tied_hypotheses_without_primary_outcome():
    route = RouterDecision(
        action="no_tool",
        in_scope=True,
        intent_type="answer_question",
        confidence=0.9,
        reason="network type is ambiguous",
        outcome_hypotheses=[
            hypothesis(outcome=mirna_network_outcome(), confidence=0.8),
            hypothesis(
                outcome=mirna_network_outcome().model_copy(
                    update={
                        "artifact_type": "coexpression_network",
                        "entity_types": ["gene"],
                        "regulator_types": [],
                        "target_types": [],
                    }
                ),
                confidence=0.8,
            ),
        ],
    )

    decision = hydrate_router_decision(route, "Which sample network should I infer?")

    assert decision.requested_outcome is None
    assert len(decision.outcome_hypotheses) == 2


def test_hypotheses_that_differ_only_by_granularity_ask_that_dimension():
    aggregate = mirna_network_outcome().model_copy(
        update={"granularity": "aggregate"}
    )
    sample_specific = mirna_network_outcome()
    result = match_outcome_hypotheses(
        [
            hypothesis(
                outcome=aggregate,
                assumptions=["Granularity is not specified."],
            ),
            hypothesis(
                outcome=sample_specific,
                assumptions=["Granularity is not specified."],
            ),
        ]
    )

    assert result.status == "ambiguous"
    assert result.clarification_question == (
        "Should the result be aggregate or sample-specific?"
    )


def test_higher_confidence_hypothesis_does_not_preserve_a_lower_ranked_choice():
    aggregate = mirna_network_outcome().model_copy(
        update={"granularity": "aggregate"}
    )
    result = match_outcome_hypotheses(
        [
            hypothesis(
                outcome=mirna_network_outcome(),
                confidence=0.9,
                assumptions=["Input files have not been supplied yet."],
            ),
            hypothesis(
                outcome=aggregate,
                confidence=0.8,
                assumptions=["Aggregate output may also be useful."],
            ),
        ]
    )

    assert result.status == "ambiguous"
    assert result.hypothesis_actions == ["run_lioness_puma"]
    assert result.clarification_question is None


def test_partial_and_sample_specific_hypotheses_still_ask_only_for_granularity():
    partial = mirna_network_outcome().model_copy(
        update={"granularity": "unknown", "unresolved_dimensions": ["granularity"]}
    )
    result = match_outcome_hypotheses(
        [
            hypothesis(
                outcome=partial,
                assumptions=["The requested network granularity is unknown."],
            ),
            hypothesis(
                assumptions=["The user may want a sample-specific network."],
            ),
        ]
    )

    assert result.status == "ambiguous"
    assert result.clarification_question == (
        "Should the result be aggregate or sample-specific?"
    )


def test_advisory_hypothesis_cannot_authorize_execution():
    raw = TaskDecision(
        action="run_lioness_puma",
        in_scope=True,
        should_execute=True,
        intent_type="run_analysis",
        confidence=0.99,
        reason="provider proposed execution",
        outcome_hypotheses=[
            hypothesis(assumptions=["network means regulatory network"])
        ],
    )

    repaired = repair_router_decision(
        raw,
        "Build my sample-specific miRNA network",
    )

    assert repaired.action == "no_tool"
    assert repaired.should_execute is False
    assert repaired.matched_actions == []
    assert repaired.hypothesis_actions == ["run_lioness_puma"]


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


def test_contextual_input_format_question_remains_stable_workflow_guidance():
    raw = TaskDecision(
        action="query_context7",
        in_scope=True,
        should_execute=True,
        intent_type="answer_question",
        confidence=0.85,
        reason="Provider proposed documentation retrieval.",
    )
    task = (
        "Previous NetZoo goal: Which tools produce sample-specific miRNA networks?\n"
        "Registered workflow context: PUMA, LIONESS-PUMA\n"
        "User follow-up: What format should the motif prior use?"
    )

    repaired = repair_router_decision(raw, task)

    assert repaired.action == "no_tool"
    assert repaired.should_execute is False
    assert repaired.intent_type == "answer_question"


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
            outcome_hypotheses=[hypothesis(outcome=mirna_measurement_outcome())],
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
        (
            "Which workflow estimates individualized microRNA regulator-target edges?",
            False,
        ),
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
            outcome_hypotheses=[hypothesis()],
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


@pytest.mark.parametrize(
    ("task", "outcome", "expected"),
    [
        (
            "Which tools estimate one miRNA network for every patient?",
            RequestedOutcome(
                operation="infer",
                artifact_type="regulatory_network",
                entity_types=["mirna", "gene"],
                display_entities=["miRNA", "gene"],
                regulator_types=["mirna"],
                target_types=["gene"],
                granularity="sample_specific",
                unresolved_dimensions=["confirmation"],
            ),
            ["run_lioness_puma"],
        ),
        (
            "如何建立每個樣本的轉錄因子調控網路？",
            RequestedOutcome(
                operation="infer",
                artifact_type="regulatory_network",
                entity_types=["tf", "gene"],
                display_entities=["TF", "gene"],
                regulator_types=["tf"],
                target_types=["gene"],
                granularity="sample_specific",
                unresolved_dimensions=["confirmation"],
            ),
            ["run_lioness_panda"],
        ),
        (
            "What method gives individualized gene coexpression edges?",
            RequestedOutcome(
                operation="infer",
                artifact_type="coexpression_network",
                entity_types=["gene"],
                display_entities=["gene"],
                regulator_types=[],
                target_types=[],
                granularity="sample_specific",
                unresolved_dimensions=["confirmation"],
            ),
            ["run_lioness_coexpression"],
        ),
    ],
)
def test_partial_hypotheses_generalize_across_network_families(
    task,
    outcome,
    expected,
):
    decision = repair_router_decision(
        TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            intent_type="answer_question",
            confidence=0.9,
            reason="advisory hypothesis",
            outcome_hypotheses=[
                OutcomeHypothesis(
                    outcome=outcome,
                    confidence=0.9,
                    evidence=[],
                    assumptions=["Confirm the inferred network interpretation."],
                )
            ],
        ),
        task,
    )

    assert decision.hypothesis_actions == expected
    assert decision.matched_actions == []
    assert decision.should_execute is False


def test_generic_sample_network_keeps_compatible_families_unranked():
    outcome = RequestedOutcome(
        operation="infer",
        artifact_type="unknown",
        entity_types=[],
        display_entities=[],
        regulator_types=[],
        target_types=[],
        granularity="sample_specific",
        unresolved_dimensions=["network type"],
    )
    decision = repair_router_decision(
        TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            intent_type="answer_question",
            confidence=0.9,
            reason="network family is unknown",
            outcome_hypotheses=[
                OutcomeHypothesis(
                    outcome=outcome,
                    confidence=0.9,
                    evidence=[
                        OutcomeEvidence(
                            dimension="granularity",
                            value="sample_specific",
                            source="explicit",
                            rationale="The request explicitly asks for per-sample output.",
                        )
                    ],
                    assumptions=["The requested network family is not specified."],
                )
            ],
        ),
        "if i want to get sample specific network data, what tools do i need?",
    )

    assert set(decision.hypothesis_actions) == {
        "run_lioness_panda",
        "run_lioness_puma",
        "run_lioness_coexpression",
    }
    assert decision.matched_actions == []
    assert decision.action == "no_tool"


@pytest.mark.parametrize(
    "task",
    [
        "I need sample-specific miRNA expression measurements, not a network.",
        "取得每個樣本的 miRNA 原始數值，不要推論網路。",
        "Which tool downloads per-patient microRNA abundance data?",
    ],
)
def test_measurement_hypotheses_never_gain_network_authority(task):
    decision = repair_router_decision(
        TaskDecision(
            action="run_lioness_puma",
            in_scope=True,
            should_execute=True,
            intent_type="run_analysis",
            confidence=0.99,
            reason="provider proposed a related network",
            outcome_hypotheses=[
                OutcomeHypothesis(
                    outcome=mirna_measurement_outcome(),
                    confidence=0.99,
                    evidence=[
                        OutcomeEvidence(
                            dimension="artifact_type",
                            value="measurement_dataset",
                            source="explicit",
                            rationale="The request asks for measured miRNA values.",
                        )
                    ],
                    assumptions=[],
                )
            ],
        ),
        task,
    )

    assert decision.hypothesis_actions == []
    assert decision.matched_actions == []
    assert decision.action == "no_tool"
    assert decision.should_execute is False


def test_motivating_sentences_are_not_production_routing_rules():
    root = Path(__file__).parents[1] / "scripts"
    production = "\n".join(
        path.read_text(encoding="utf-8") for path in root.rglob("*.py")
    ).casefold()

    assert "if i want to get sample specific network data" not in production
    assert "if i want to get sample specific mi-rna network data" not in production
