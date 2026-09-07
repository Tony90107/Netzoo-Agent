"""Regressions at semantic, recommendation and final-answer boundaries."""
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from typing import get_args

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

import netzoo_agent as agent  # noqa: E402
from netzoo_agent_core.graph.response import respond  # noqa: E402
from netzoo_agent_core.graph.response_context import validated_workflow_context  # noqa: E402
from netzoo_agent_core.interpretation.assembly import assemble_task_decision  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses  # noqa: E402
from netzoo_agent_core.contracts.decisions import IntentDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import (  # noqa: E402
    match_registry_guidance_features, match_semantic_request,
)
from netzoo_agent_core.contracts.artifact_semantics import ARTIFACT_SEMANTICS  # noqa: E402
from netzoo_agent_core.interpretation.verified_guidance import guidance_contract, render_verified_guidance  # noqa: E402
from workflow_registry import ArtifactType, OUTPUT_CAPABILITIES  # noqa: E402


def hypothesis(artifact="sample_cluster_assignment", entities=None, granularity="aggregate", **extra):
    outcome = agent.RequestedOutcome(
        operation="analyze", input_artifacts=["mutation_matrix"],
        artifact_type=artifact, entity_types=entities if entities is not None else ["sample"],
        granularity=granularity, **extra,
    )
    dimensions = [("operation", outcome.operation), ("input_artifact", "mutation_matrix"),
                  ("artifact_type", artifact), ("granularity", granularity)]
    dimensions.extend(("entity_type", entity) for entity in outcome.entity_types)
    return agent.OutcomeHypothesis(outcome=outcome, confidence=.9, evidence=[
        agent.OutcomeEvidence(dimension=key, value=value, source="inferred", rationale="Test inference")
        for key, value in dimensions
    ])


@pytest.mark.parametrize("item,issue", [
    (hypothesis(entities=["gene"]), "artifact_entity"),
    (hypothesis(granularity="sample_specific"), "artifact_granularity"),
    (hypothesis(unresolved_dimensions=["regulator_types", "target_types"]), "artifact_roles"),
    (hypothesis(artifact="sample_distance_matrix", entities=["pathway"]), "artifact_entity"),
    (hypothesis(artifact="pathway_mutation_matrix", entities=["gene"]), "artifact_entity"),
])
def test_cross_field_inconsistency_is_rejected_even_with_self_consistent_evidence(item, issue):
    result = validate_outcome_hypotheses("Subtype the mutation samples", [item])
    assert not result.valid
    assert any(issue in entry for entry in result.issues)
    assert match_semantic_request("Subtype mutation matrix with SAMBAR", [item], request_mode="execute").status != "exact"


def test_cohort_assignments_are_valid_and_not_individual_networks():
    assert validate_outcome_hypotheses("Subtype samples", [hypothesis()]).valid


def test_every_artifact_type_has_explicit_output_semantics():
    assert set(ARTIFACT_SEMANTICS) == set(get_args(ArtifactType))


@pytest.mark.parametrize("artifact,entities,granularity", [
    ("regulatory_network", ["tf", "gene"], "sample_specific"),
    ("coexpression_network", ["gene"], "aggregate"),
    # 2026-09-06: community_assignment now declares granularities={aggregate}.
    # The row is rewritten rather than dropped so the artifact keeps a
    # positive "this combination is valid" assertion under the new contract.
    ("community_assignment", ["tf", "gene"], "aggregate"),
    ("pathway_mutation_matrix", ["pathway", "sample"], "aggregate"),
    ("sample_distance_matrix", ["sample"], "aggregate"),
])
def test_valid_non_tool_specific_artifact_combinations(artifact, entities, granularity):
    assert validate_outcome_hypotheses("Guidance", [hypothesis(artifact, entities, granularity)]).valid


def test_feature_recommendation_is_not_exact_and_cannot_execute():
    task = "Subtype a sparse somatic mutation matrix using pathway aggregation"
    match = match_registry_guidance_features(task)
    assert match is None  # Tool selection requires interpreted scientific meaning.


def test_final_answer_rejects_wrong_method_and_separates_artifacts():
    task = "Previously used RNA-Seq PANDA. Now should I use PANDA and LIONESS on a WES somatic mutation matrix to subtype patients?"
    item = hypothesis()
    match = match_semantic_request(task, [item], request_mode="guidance")
    decision = assemble_task_decision(
        SemanticInterpretation(request_mode="guidance", semantic_goal="Subtype patients", outcome_hypotheses=[item]),
        match, IntentDecision(mode="answer", confidence=.9, reason="Explain"), task=task,
    )
    policy = agent.ProjectPolicyLoader(agent.PROJECT_ROOT).load()
    facts = validated_workflow_context(decision, policy, task=task)
    rejected = {entry["action"]: entry for entry in facts["rejected_methods"]}
    assert rejected["run_panda"]["reason_code"] == "incompatible_input"
    assert rejected["run_panda"]["input_artifacts"] == ["mutation_matrix"]
    assert rejected["run_lioness_panda"]["reason_code"] == "incompatible_input"

    class AdversarialResponse:
        def invoke(self, messages):
            pytest.fail("Free-form prose must not override verified workflow guidance")

    result = respond(SimpleNamespace(project_policy=policy, response_llm=AdversarialResponse()), {
        "messages": [agent.HumanMessage(content=task)], "decision": decision.model_dump(),
        "plan": agent.WorkflowPlan(workflow="NO-TOOL", objective="Guidance", decision=decision.model_dump(), status="respond_only").model_dump(),
        "tool_results": [],
    })
    answer = result["messages"][0].content
    assert answer.startswith("Do not use")
    assert "PANDA" in answer and "LIONESS" in answer
    assert "SAMBAR" in answer
    assert "valid approach" not in answer
    assert "`pathway_mutation_matrix`: Pathway-by-sample mutation scores" in answer
    assert "`sample_cluster_assignment`: Sample-to-cluster labels" in answer
    assert "not cluster labels" in answer
    assert "No files were inspected and no analysis ran." in answer


@pytest.mark.parametrize("action", sorted(OUTPUT_CAPABILITIES))
def test_all_registered_workflows_inherit_artifact_separation(action):
    policy = agent.ProjectPolicyLoader(agent.PROJECT_ROOT).load()
    decision = agent.TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, confidence=.9,
        reason="A pathway score matrix contains cluster labels. Valid approach!",
        capability_match_status="exact", matched_actions=[action], recommended_actions=[action],
    )
    facts = guidance_contract(decision, policy, "Explain this workflow")
    answer = render_verified_guidance(decision, facts)
    assert "Valid approach!" not in answer  # Never copy untrusted decision prose.
    capability = OUTPUT_CAPABILITIES[action]
    for artifact in capability.produced_artifacts or {capability.artifact_type}:
        assert f"`{artifact}`: {ARTIFACT_SEMANTICS[artifact].description}." in answer


def test_reverse_history_does_not_reject_compatible_expression_workflows():
    task = "Previously used SAMBAR for mutations; now use PANDA with expression data."
    decision = agent.TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, confidence=.9, reason="Guidance",
        capability_match_status="exact", matched_actions=["run_panda"],
        requested_outcome=agent.RequestedOutcome(
            operation="infer", input_artifacts=["expression_matrix"], artifact_type="regulatory_network",
            entity_types=["tf", "gene"], granularity="aggregate",
        ),
    )
    policy = agent.ProjectPolicyLoader(agent.PROJECT_ROOT).load()
    facts = validated_workflow_context(decision, policy, task=task)
    assert {item["action"] for item in facts["rejected_methods"]} == {"run_sambar"}
    assert all(item["input_artifacts"] == ["expression_matrix"] for item in facts["rejected_methods"])
    answer = render_verified_guidance(decision, facts)
    assert "Selected path: **PANDA**" in answer
    assert "not every possible use of the method" in answer


def test_fallback_public_progress_is_not_an_exact_workflow_signal():
    from netzoo_agent_core.interpretation.semantic_goal import classification_progress_detail, outcome_routing_state, public_semantic_summary
    decision = agent.TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, confidence=.35, reason="Guidance",
        capability_match_status="fallback", match_basis="registry_features",
        matched_actions=["run_sambar"], recommended_actions=["run_sambar"],
    )
    state = outcome_routing_state(decision, request_mode="guidance")
    detail = classification_progress_detail(state["semantic_goal"], decision)
    assert detail["match_status"] == "fallback"
    assert detail["workflow_path"] == []
    assert "not an exact semantic match" in public_semantic_summary(state["semantic_goal"], decision)
