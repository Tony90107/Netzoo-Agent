from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.contracts import RequestedOutcome, TaskDecision  # noqa: E402
from netzoo_agent_core.interpretation.concept_answers import (  # noqa: E402
    render_capability_gap,
    render_outcome_clarification,
    render_workflow_composition_guidance,
    render_spec_backed_concept_answer,
)
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402


def _decision() -> TaskDecision:
    return TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="concept question",
    )


def _measurement_outcome() -> RequestedOutcome:
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


def test_purpose_question_uses_registered_workflow_description():
    policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()

    answer = render_spec_backed_concept_answer(
        "what is the function of PANDA", _decision(), policy
    )

    assert answer is not None
    assert "Infer an aggregate TF-to-gene regulatory network" in answer
    assert "No files were inspected and no analysis ran." in answer


def test_non_purpose_question_keeps_response_model_path():
    policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()

    assert render_spec_backed_concept_answer("compare PANDA and PUMA", _decision(), policy) is None


def test_composition_guidance_uses_registered_workflow_metadata():
    policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="Guidance was requested.",
        recommended_actions=["run_puma", "run_lioness_puma"],
    )

    answer = render_workflow_composition_guidance(
        decision,
        policy,
        {"relationship": "composition"},
    )

    assert answer is not None
    assert "PUMA: Infer an aggregate TF/miRNA-to-gene regulatory network with PUMA." in answer
    assert "LIONESS-PUMA: Infer aggregate PUMA and sample-specific LIONESS-PUMA networks." in answer
    assert "final workflow in this composition is LIONESS-PUMA" in answer
    assert "clarify" not in answer


def test_measurement_request_explains_gap_before_offering_network():
    policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="unsupported requested outcome",
        requested_outcome=_measurement_outcome(),
        capability_match_status="unsupported",
        alternative_actions=["run_lioness_puma"],
        mismatch_dimensions=["operation", "artifact_type"],
    )

    answer = render_capability_gap(decision, policy)

    assert answer is not None
    assert "do not acquire sample-specific miRNA measurement data" in answer
    assert "can instead infer" in answer
    assert "LIONESS-PUMA" in answer
    assert "Did you mean" in answer
    assert "No files were inspected and no analysis ran." in answer


def test_ambiguous_outcome_asks_only_the_validated_question():
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="ambiguous outcome",
        capability_match_status="ambiguous",
        clarification_question=(
            "Do you want measurement data or a regulatory network?"
        ),
    )

    assert render_outcome_clarification(decision) == (
        "I cannot select a workflow until the requested result is clear. "
        "Do you want measurement data or a regulatory network?\n\n"
        "No files were inspected and no analysis ran."
    )
