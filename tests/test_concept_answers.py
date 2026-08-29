from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.contracts import (  # noqa: E402
    OutcomeHypothesis,
    RequestedOutcome,
    TaskDecision,
)
from netzoo_agent_core.interpretation.concept_answers import (  # noqa: E402
    render_capability_gap,
    render_cobra_expression_boundary,
    render_registered_handoff_script_guidance,
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

    assert (
        render_spec_backed_concept_answer("compare PANDA and PUMA", _decision(), policy)
        is None
    )


def test_cobra_output_cannot_be_routed_as_panda_expression():
    answer = render_cobra_expression_boundary(
        "請將 COBRA 的結果直接當成 expression input 跑 PANDA。"
    )

    assert answer is not None
    assert "cannot be used directly as PANDA expression input" in answer
    assert "covariance decomposition" in answer


def test_registered_handoff_script_uses_artifact_not_expression_substitution():
    policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        confidence=1.0,
        reason="registry-selected handoff",
        recommended_actions=["run_cobra", "run_panda"],
    )
    answer = render_registered_handoff_script_guidance(
        "Please write a script for high-order correlation batch correction then "
        "PANDA using expression, motif, and PPI matrices.",
        decision,
        policy,
    )

    assert answer is not None
    assert "run-cobra" in answer
    assert "run-panda-precomputed" in answer
    assert "adjusted_coexpression.tsv" in answer
    assert "original expression matrix as `expression_file`" in answer
    assert "design row IDs must exactly match expression sample IDs" in answer
    assert "One-hot encode categorical batches" in answer
    assert "existence guards only" in answer
    assert "square/symmetric numeric matrix" in answer


def test_handoff_script_uses_registry_signals_when_semantic_routing_selected_only_final_action():
    policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="semantic routing selected the final result",
        capability_match_status="exact",
        matched_actions=["run_panda"],
        recommended_actions=["run_panda"],
        requested_outcome=RequestedOutcome(
            operation="infer",
            artifact_type="regulatory_network",
            entity_types=["tf", "gene"],
            regulator_types=["tf"],
            target_types=["gene"],
            granularity="aggregate",
        ),
    )

    answer = render_registered_handoff_script_guidance(
        "Write a script: first perform high-order correlation batch correction, "
        "then PANDA.",
        decision,
        policy,
    )

    assert answer is not None
    assert "**COBRA → PANDA**" in answer
    assert "run-cobra" in answer
    assert "run-panda-precomputed" in answer
    assert "from cobra import" not in answer
    assert "from panda import" not in answer


def test_handoff_script_does_not_invent_an_undeclared_cli_variant():
    policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        confidence=1.0,
        reason="registered but unrenderable handoff",
        recommended_actions=["run_cobra", "run_otter"],
    )

    answer = render_registered_handoff_script_guidance(
        "Please write a script.", decision, policy
    )

    assert answer is not None
    assert "no typed executable adapter is registered" in answer
    assert "run-cobra" not in answer


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
        None,
    )

    assert answer is not None
    assert "**PUMA**" in answer
    assert "**LIONESS-PUMA**" in answer
    assert "`expression_file`" in answer
    assert "`motif_file`" in answer
    assert "`ppi_file`" in answer
    assert "`mirna_file`" in answer
    assert "Aggregate workflow output (`output_file`)" in answer
    assert "Sample-specific LIONESS output (`lioness_output`)" in answer
    assert "Use LIONESS-PUMA directly" in answer
    assert "running the aggregate workflow first is unnecessary" in answer
    assert "clarify" not in answer


def test_composition_guidance_does_not_assume_mirna_or_puma():
    policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="Guidance was requested.",
        recommended_actions=["run_panda", "run_lioness_panda"],
    )

    answer = render_workflow_composition_guidance(decision, policy, None)

    assert answer is not None
    assert "**PANDA**" in answer
    assert "**LIONESS-PANDA**" in answer
    assert "Use LIONESS-PANDA directly" in answer
    assert "miRNA" not in answer
    assert "PUMA" not in answer


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

    policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()

    assert render_outcome_clarification(decision, policy) == (
        "I cannot select a workflow until the requested result is clear. "
        "Do you want measurement data or a regulatory network?\n\n"
        "No files were inspected and no analysis ran."
    )


def test_unique_mirna_hypothesis_explains_registry_composition_and_confirms():
    policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.9,
        reason="advisory hypothesis",
        capability_match_status="ambiguous",
        outcome_hypotheses=[
            OutcomeHypothesis(
                outcome=RequestedOutcome(
                    operation="infer",
                    artifact_type="regulatory_network",
                    entity_types=["mirna", "gene"],
                    display_entities=["miRNA", "gene"],
                    regulator_types=["mirna"],
                    target_types=["gene"],
                    granularity="sample_specific",
                    unresolved_dimensions=["confirm network interpretation"],
                ),
                confidence=0.9,
                evidence=[],
                assumptions=["network data means a regulatory-network result"],
            )
        ],
        hypothesis_actions=["run_lioness_puma"],
        clarification_question="Is that the network result you mean?",
    )

    answer = render_outcome_clarification(decision, policy)

    assert "It sounds like" in answer
    assert "PUMA" in answer
    assert "LIONESS-PUMA" in answer
    assert answer.index("PUMA") < answer.index("LIONESS-PUMA")
    assert "Is that the network result you mean?" in answer
    assert "I cannot select a workflow" not in answer


def test_tied_network_hypotheses_are_presented_without_priority():
    policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.9,
        reason="network family is ambiguous",
        capability_match_status="ambiguous",
        hypothesis_actions=[
            "run_lioness_puma",
            "run_lioness_panda",
            "run_lioness_coexpression",
        ],
        clarification_question="Which network relationship do you mean?",
    )

    answer = render_outcome_clarification(decision, policy)

    assert "TF-only regulatory" in answer
    assert "TF/miRNA regulatory" in answer
    assert "co-expression" in answer
    assert "Which network relationship" in answer
    for biased_word in ("best", "preferred", "recommended", "most likely"):
        assert biased_word not in answer.casefold()


def test_granularity_clarification_does_not_assume_a_sample_specific_result():
    policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.9,
        reason="granularity is ambiguous",
        capability_match_status="ambiguous",
        hypothesis_actions=["run_puma", "run_lioness_puma"],
        clarification_question="Should the result be aggregate or sample-specific?",
    )

    answer = render_outcome_clarification(decision, policy)

    assert "more than one compatible network result" in answer
    assert "sample-specific network family" not in answer
    assert "Should the result be aggregate or sample-specific?" in answer


def test_single_compatible_workflow_does_not_assume_an_unresolved_granularity():
    policy = ProjectPolicyLoader(Path(__file__).parents[1]).load()
    unknown = RequestedOutcome(
        operation="infer",
        artifact_type="regulatory_network",
        entity_types=["mirna", "gene"],
        display_entities=[],
        regulator_types=["mirna"],
        target_types=["gene"],
        granularity="unknown",
        unresolved_dimensions=["granularity"],
    )
    sample_specific = unknown.model_copy(
        update={"granularity": "sample_specific", "unresolved_dimensions": []}
    )
    question = "Should the result be aggregate or sample-specific?"
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.8,
        reason="granularity is unresolved",
        capability_match_status="ambiguous",
        requested_outcome=sample_specific,
        outcome_hypotheses=[
            OutcomeHypothesis(outcome=unknown, confidence=0.8),
            OutcomeHypothesis(outcome=sample_specific, confidence=0.7),
        ],
        hypothesis_actions=["run_lioness_puma"],
        clarification_question=question,
    )

    answer = render_outcome_clarification(decision, policy)
    leading_description = answer.split(question, maxsplit=1)[0]

    assert "miRNA/gene regulatory networks" in leading_description
    assert "sample-specific" not in leading_description
