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
from netzoo_agent_core.contracts.policy import WorkflowControlSpec  # noqa: E402
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
    task = "Previously used RNA-Seq PANDA. Now should I use PANDA and LIONESS on a sparse WES somatic mutation matrix to subtype patients?"
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
    assert "Gene-length normalization" in answer
    assert "patient-specific cancer-associated mutation rate" in answer
    assert "genes annotated to multiple pathways" in answer
    assert "Routing-level input modality: somatic mutation." in answer
    assert "Required workflow inputs:" in answer
    for field_name in (
        "mutation_file",
        "exon_size_file",
        "cancer_gene_file",
        "pathway_file",
    ):
        assert f"`{field_name}`" in answer
    assert "`output_dir`" not in answer
    assert "No files were inspected and no analysis ran." in answer


def test_response_blocks_unnamed_sample_specific_coexpression_handoff():
    task = (
        "先產生 S01 和 S07 的 sample-specific gene-gene co-expression，"
        "然後直接把這些矩陣交給 PANDA 作為 coexpression_file；"
        "不要做 aggregation 或 sample selection。"
    )
    policy = agent.ProjectPolicyLoader(agent.PROJECT_ROOT).load()
    decision = agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="The requested direct handoff is incompatible.",
        requested_outcome=agent.RequestedOutcome(
            operation="infer",
            input_artifacts=["expression_matrix"],
            artifact_type="coexpression_network",
            entity_types=["gene"],
            granularity="sample_specific",
        ),
        capability_match_status="unsupported",
        alternative_actions=["run_lioness_panda"],
    )
    plan = agent.WorkflowPlan(
        workflow="NO-TOOL",
        objective=decision.reason,
        decision=decision.model_dump(),
        status="respond_only",
    )

    class AdversarialResponse:
        def invoke(self, messages):
            pytest.fail("The deterministic handoff boundary must run first")

    result = respond(SimpleNamespace(
        project_policy=policy,
        response_llm=AdversarialResponse(),
    ), {
        "messages": [agent.HumanMessage(content=task)],
        "decision": decision.model_dump(),
        "plan": plan.model_dump(),
        "tool_results": [],
    })
    answer = result["messages"][0].content

    assert "PANDA" in answer
    assert "sample-specific gene-gene co-expression" in answer
    assert "aggregate" in answer
    assert "explicitly forbids aggregation or sample selection" in answer
    assert "LIONESS-PANDA can instead" not in answer
    assert "No execution is permitted" in answer


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


def test_dragon_guidance_states_modality_and_cross_layer_penalty_limit():
    outcome = agent.RequestedOutcome(
        operation="infer",
        artifact_type="multi_omic_network",
        entity_types=[],
        granularity="aggregate",
    )
    decision = agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        confidence=.95,
        reason="Guidance",
        requested_outcome=outcome,
        capability_match_status="exact",
        match_basis="registry_features",
        matched_actions=["run_dragon"],
        recommended_actions=["run_dragon"],
    )
    policy = agent.ProjectPolicyLoader(agent.PROJECT_ROOT).load()

    answer = render_verified_guidance(
        decision,
        guidance_contract(decision, policy, "Which workflow fits two continuous omics layers?"),
    )

    assert answer is not None
    assert "Selected path: **DRAGON**" in answer
    assert "Routing-level input modality: multi omic continuous." in answer
    assert "two layer-specific shrinkage parameters" in answer
    assert "does not expose a separately tunable third cross-layer penalty" in answer
    assert "three independently controlled intra/inter-omics penalties are outside" in answer
    assert "No files were inspected and no analysis ran." in answer


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


def test_tfa_factorization_guidance_is_model_routed_and_explicit_about_giraffe():
    task = (
        "Use biologically informed matrix factorization to jointly infer a "
        "TF-gene network and a TF-by-sample TFA matrix."
    )
    # Raw request text is never a deterministic workflow-selection shortcut.
    assert match_registry_guidance_features(task) is None

    requested = agent.RequestedOutcome(
        operation="infer",
        input_artifacts=["expression_matrix"],
        artifact_type="regulatory_network_and_tf_activity",
        entity_types=["tf", "gene", "sample"],
        regulator_types=["tf"],
        target_types=["gene"],
        selection_tags=[
            "tfa",
            "biologically_informed_matrix_factorization",
            "joint_grn_tfa_inference",
        ],
        granularity="aggregate",
    )
    match = match_semantic_request(
        task,
        [agent.OutcomeHypothesis(outcome=requested, confidence=.95, evidence=[])],
        request_mode="guidance",
    )
    assert match.status == "exact" and match.matched_actions == ["run_giraffe"]

    decision = agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        confidence=.95,
        reason="Guidance",
        requested_outcome=requested,
        capability_match_status=match.status,
        match_basis=match.match_basis,
        matched_actions=match.matched_actions,
        recommended_actions=match.matched_actions,
    )
    policy = agent.ProjectPolicyLoader(agent.PROJECT_ROOT).load()
    answer = render_verified_guidance(decision, guidance_contract(decision, policy, task))

    assert answer is not None
    assert "Selected path: **GIRAFFE**" in answer
    assert "biologically informed matrix factorization" in answer.lower()
    assert "jointly infer" in answer.lower()
    assert "`regulatory_network`" in answer
    assert "`tf_activity_matrix`" in answer


def test_otter_guidance_declares_expression_or_coexpression_source_and_optimization():
    outcome = agent.RequestedOutcome(
        operation="infer",
        input_artifacts=["expression_matrix"],
        artifact_type="regulatory_network",
        entity_types=["tf", "gene"],
        regulator_types=["tf"],
        target_types=["gene"],
        selection_tags=["relaxed_graph_matching"],
        granularity="aggregate",
    )
    decision = agent.TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, confidence=.95,
        reason="Guidance", requested_outcome=outcome,
        capability_match_status="exact", match_basis="registry_features",
        matched_actions=["run_otter"], recommended_actions=["run_otter"],
    )
    policy = agent.ProjectPolicyLoader(agent.PROJECT_ROOT).load()
    answer = render_verified_guidance(decision, guidance_contract(
        decision, policy,
        "Infer an aggregate TF-gene regulatory network with continuous relaxed graph matching.",
    ))
    assert answer is not None
    assert "continuous-relaxation" in answer
    assert "Required alternative (provide one):" in answer
    assert "`expression_file`" in answer and "`coexpression_file`" in answer


def test_bonobo_guidance_exposes_sample_and_pvalue_controls_without_claiming_thresholding():
    outcome = agent.RequestedOutcome(
        operation="infer",
        input_artifacts=["expression_matrix"],
        artifact_type="coexpression_network",
        entity_types=["gene"],
        selection_tags=["sample_specific", "sparse_pvalue_coexpression"],
        granularity="sample_specific",
    )
    decision = agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        confidence=.95,
        reason="Guidance",
        requested_outcome=outcome,
        capability_match_status="exact",
        match_basis="registry_features",
        matched_actions=["run_bonobo"],
        recommended_actions=["run_bonobo"],
    )
    policy = agent.ProjectPolicyLoader(agent.PROJECT_ROOT).load()

    answer = render_verified_guidance(
        decision,
        guidance_contract(
            decision,
            policy,
            "Select two samples and save sparsification p-values.",
        ),
    )

    assert answer is not None
    assert "Selected path: **BONOBO**" in answer
    assert "`sample_names`" in answer
    assert "`sparsify`" in answer
    assert "`save_pvals`" in answer
    assert "retains the full co-expression matrix" in answer
    assert "does not also emit an already-thresholded network" in answer


def test_bonobo_guidance_echoes_explicit_request_parameters():
    task = (
        "請對 expression_file=data/toy/expression.tsv 的 S01 與 S07 執行 "
        "sample-specific gene-gene co-expression 分析，sparsify=true，"
        "save_pvals=true，output_dir=outputs/pvalues，log_transformed=true，"
        "centered=true。"
    )
    outcome = agent.RequestedOutcome(
        operation="infer",
        input_artifacts=["expression_matrix"],
        artifact_type="coexpression_network",
        entity_types=["gene"],
        selection_tags=["sample_specific", "sparse_pvalue_coexpression"],
        granularity="sample_specific",
    )
    decision = agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        confidence=.95,
        reason="Guidance",
        requested_outcome=outcome,
        capability_match_status="exact",
        match_basis="registry_features",
        matched_actions=["run_bonobo"],
        recommended_actions=["run_bonobo"],
    )
    policy = agent.ProjectPolicyLoader(agent.PROJECT_ROOT).load()

    answer = render_verified_guidance(decision, guidance_contract(decision, policy, task))

    assert answer is not None
    assert "Captured request parameters:" in answer
    assert "`expression_file`: data/toy/expression.tsv" in answer
    assert "`expression_file`: data/toy/expression.tsv 的" not in answer
    assert "Sample IDs (`sample_names`): S01, S07" in answer
    assert "`output_dir`: outputs/pvalues" in answer
    assert "`sparsify`: true" in answer
    assert "`save_pvals`: true" in answer
    assert "`log_transformed`: true" in answer
    assert "`centered`: true" in answer


def test_guidance_renders_an_injected_registry_control_without_renderer_changes():
    policy = agent.ProjectPolicyLoader(agent.PROJECT_ROOT).load()
    custom_control = WorkflowControlSpec(
        name="fixture_control",
        type="string",
        default="fixture-default",
        executor_argument="fixture_control",
        description="A test-only registry control.",
    )
    bonobo = policy.workflows["run_bonobo"].model_copy(
        update={
            "controls": [*policy.workflows["run_bonobo"].controls, custom_control]
        }
    )
    injected_policy = policy.model_copy(
        update={"workflows": {**policy.workflows, "run_bonobo": bonobo}}
    )
    decision = agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        confidence=.95,
        reason="Guidance",
        capability_match_status="exact",
        matched_actions=["run_bonobo"],
        recommended_actions=["run_bonobo"],
    )

    answer = render_verified_guidance(
        decision,
        guidance_contract(decision, injected_policy, "Explain BONOBO controls"),
    )

    assert answer is not None
    assert "fixture_control" in answer
    assert "fixture-default" in answer


def test_signed_linear_effect_guidance_is_typed_and_explains_tfa_regression():
    task = (
        "I need signed partial regulatory effects whose positive and negative "
        "weights are coefficients of a linear model."
    )
    assert match_registry_guidance_features(task) is None

    requested = agent.RequestedOutcome(
        operation="infer",
        artifact_type="signed_regulatory_effect_network",
        entity_types=["tf", "gene"],
        regulator_types=["tf"],
        target_types=["gene"],
        granularity="aggregate",
    )
    match = match_semantic_request(
        task,
        [agent.OutcomeHypothesis(outcome=requested, confidence=.95, evidence=[])],
        request_mode="guidance",
    )
    assert match.status == "exact" and match.matched_actions == ["run_giraffe"]

    decision = agent.TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        confidence=.95,
        reason="Guidance",
        requested_outcome=requested,
        capability_match_status=match.status,
        match_basis=match.match_basis,
        matched_actions=match.matched_actions,
        recommended_actions=match.matched_actions,
    )
    policy = agent.ProjectPolicyLoader(agent.PROJECT_ROOT).load()
    answer = render_verified_guidance(
        decision, guidance_contract(decision, policy, task)
    )

    assert answer is not None
    assert "Selected path: **GIRAFFE**" in answer
    assert "signed partial regulatory effects" in answer.lower()
    assert "linear-model coefficients" in answer.lower()
    assert "positive" in answer.lower() and "negative" in answer.lower()
    assert "tfa" in answer.lower() and "predictor" in answer.lower()


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
