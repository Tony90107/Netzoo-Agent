from __future__ import annotations

import json
from pathlib import Path

import sys

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.graph.prompts import build_graph_prompts  # noqa: E402
from netzoo_agent_core.graph.router_invocation import _discriminator_context  # noqa: E402
from netzoo_agent_core.contracts.outcomes import SemanticDiscriminator  # noqa: E402
from netzoo_agent_core.llm import (  # noqa: E402
    build_semantic_interpreter_prompt,
    build_semantic_reviewer_messages,
)
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.contracts import RequestedOutcome, TaskDecision  # noqa: E402
from netzoo_agent_core.graph.response_context import (  # noqa: E402
    validated_workflow_context,
)
from netzoo_agent_core.routing.outcome_matching import match_requested_outcome  # noqa: E402


SCENARIOS = json.loads(
    (Path(__file__).with_name("workflow_reasoning_prompts.json")).read_text(
        encoding="utf-8"
    )
)

FULL_PIPELINE_PROMPT = (
    "我有一份來自不同醫院、不同定序梯次的 RNA-Seq 表現量矩陣，以及對應的 Metadata。"
    "我想要找出這群病患在基因調控上的社群模組。請幫我規劃一個最嚴謹的分析流水線 "
    "(Pipeline)：從一開始在共表現矩陣層次消除醫院和批次帶來的技術性干擾，接著整合先驗知識建立基因調控圖譜，"
    "最後對這個圖譜進行二分圖的模組化分群。請列出你的步驟和使用的演算法。"
)


def test_generated_reasoning_prompts_cover_implicit_workflow_intent():
    assert len(SCENARIOS) == 4
    assert all(item["prompt"] and item["expected"] for item in SCENARIOS)

    semantic_prompt = build_semantic_interpreter_prompt()
    response_prompt = build_graph_prompts(
        ProjectPolicyLoader().load()
    ).response

    for phrase in (
        "estimating each patient's network",
        "comparing networks across",
        "patient-level",
        "heterogeneity",
        "infer the result",
        "fixed keyword-to-tool table",
    ):
        assert phrase in semantic_prompt
    assert "registered workflow" in response_prompt
    assert "may be a LIONESS workflow" in response_prompt
    assert "registry_selection_constraints" in response_prompt
    assert "smallest additional-role set" in response_prompt
    assert "independent preparation step" in response_prompt
    assert "do not add a miRNA branch" not in response_prompt
    assert "For the COBRA handoff" not in response_prompt
    assert "Registered workflow execution mode" in response_prompt
    assert "without an explicit sample-specific request" not in response_prompt
    assert "selection_tags are registry-defined intent signals" in semantic_prompt
    assert "biologically_informed_matrix_factorization" in semantic_prompt
    assert "activity matrix is ONE compatible terminal goal" in semantic_prompt
    assert "artifact_type=regulatory_network_and_tf_activity" in semantic_prompt
    assert "artifact_type=signed_regulatory_effect_network" in semantic_prompt
    assert "signed partial regulatory effects" in semantic_prompt
    assert "linear-model coefficients" in semantic_prompt
    assert "leave_one_out_network_inference" in semantic_prompt
    assert "message_passing" in semantic_prompt
    assert "write or generate a script/template" in build_graph_prompts(
        ProjectPolicyLoader().load()
    ).intent
    assert "never call an artifact type a parameter name" in response_prompt.lower()
    assert "handoff_input_fields" in response_prompt
    assert "adjusted co-expression artifact" in response_prompt
    assert "not a corrected expression matrix" in response_prompt
    assert "If the user asks to write or generate a script" in response_prompt
    assert "output_files" in response_prompt


def test_semantic_prompt_defines_multi_omic_feature_entity_mapping():
    prompt = build_semantic_interpreter_prompt()

    assert "multi_omic_network" in prompt
    assert "omics_layer_1_feature, omics_layer_2_feature" in prompt
    assert "gene, mirna, protein, or metabolite" in prompt
    assert "not regulator_types or target_types" in prompt


def test_semantic_contract_separates_a_proposed_method_from_the_terminal_goal():
    """A method under evaluation is context, not a competing outcome."""
    prompt = build_semantic_interpreter_prompt()

    assert "historical context" in prompt
    assert "current input" in prompt
    assert "proposed method" in prompt
    assert "terminal scientific goal" in prompt
    assert "Do not create another hypothesis solely for the proposed method" in prompt


def test_reviewer_recovers_scientific_goal_after_not_applicable_placeholder():
    messages = build_semantic_reviewer_messages(
        build_semantic_interpreter_prompt(),
        "請問哪個演算法能以損失函數、正則化與鬆弛化推論基因調控網路？",
        {"request_mode": "guidance"},
        ("hypothesis[0].inconsistent_not_applicable_outcome",),
    )
    reviewer_prompt = messages[0].content

    assert "reconstruct the goal" in reviewer_prompt
    assert "regulatory_network" in reviewer_prompt
    assert "relaxed_graph_matching" in reviewer_prompt


def test_registered_capability_metadata_is_the_only_pipeline_source():
    policy = ProjectPolicyLoader().load()
    cobra = policy.workflows["run_cobra"].output_capability
    panda = policy.workflows["run_panda"].output_capability
    condor = policy.workflows["run_condor"].output_capability
    giraffe = policy.workflows["run_giraffe"].output_capability

    assert "hospital_effect_assessment" in cobra.selection_tags
    assert cobra.handoff_targets == ["run_panda", "run_puma", "run_otter"]
    assert panda.handoff_targets == ["run_condor"]
    assert condor.handoff_targets == []
    assert "biologically_informed_matrix_factorization" in giraffe.selection_tags
    assert "joint_grn_tfa_inference" in giraffe.selection_tags
    assert "signed_partial_regulatory_effects" in giraffe.selection_tags
    assert "linear_model_coefficients" in giraffe.selection_tags
    assert "tfa_covariate_regression" in giraffe.selection_tags
    assert giraffe.artifact_type == "signed_regulatory_effect_network"
    assert "biologically informed matrix factorization" in giraffe.handoff_contract
    assert "Y approximately R times absolute TFA" in giraffe.handoff_contract


def test_every_registered_selection_tag_has_a_scientific_gloss():
    from workflow_registry import OUTPUT_CAPABILITIES, SELECTION_TAG_GLOSSARY

    registered = set().union(
        *(capability.selection_tags for capability in OUTPUT_CAPABILITIES.values())
    )

    assert registered <= SELECTION_TAG_GLOSSARY.keys()


def test_ambiguous_reviewer_context_exposes_scientific_otter_discriminator_without_tool_names():
    context = _discriminator_context(["run_panda", "run_otter"])

    assert "continuous relaxed graph-matching" in context
    assert "gradient descent" in context
    assert "selection_tags value" in context
    assert "run_panda" not in context
    assert "run_otter" not in context
    assert "PANDA" not in context
    assert "OTTER" not in context


def test_semantic_discriminator_is_closed_and_evidence_backed():
    schema = SemanticDiscriminator.model_json_schema()

    assert set(schema["properties"]) == {"selection_tags", "evidence"}
    valid = SemanticDiscriminator.model_validate({
        "selection_tags": ["relaxed_graph_matching"],
        "evidence": [{
            "dimension": "selection_tag",
            "value": "relaxed_graph_matching",
            "source": "explicit",
            "text_span": "連續鬆弛化",
            "rationale": "The request explicitly asks for continuous relaxation.",
        }],
    })
    assert valid.selection_tags == ["relaxed_graph_matching"]


def test_provider_schema_keeps_selection_signals_optional():
    from netzoo_agent_core.contracts import RequestedOutcome

    schema = RequestedOutcome.model_json_schema()

    assert "selection_tags" in schema["properties"]
    assert "selection_tags" not in schema["required"]
    assert all("selection_tags" not in branch["required"] for branch in schema["anyOf"])


def test_lioness_panda_contract_describes_internal_inference_inputs():
    policy = ProjectPolicyLoader().load()
    lioness = policy.workflows["run_lioness_panda"]
    contract = lioness.output_capability.handoff_contract

    assert lioness.required_inputs == [
        "expression_file",
        "motif_file",
        "ppi_file",
        "output_file",
        "lioness_output",
    ]
    assert "motif and PPI priors" in contract
    assert "internally" in contract
    assert "not a direct file handoff" in contract

    puma_contract = policy.workflows["run_lioness_puma"].output_capability.handoff_contract
    assert "motif, PPI, and miRNA priors" in puma_contract
    assert "internally" in puma_contract
    assert "not a direct file handoff" in puma_contract


def test_expression_network_workflows_reject_somatic_mutation_matrices():
    policy = ProjectPolicyLoader().load()

    for action in (
        "run_panda",
        "run_puma",
        "run_lioness_panda",
        "run_lioness_puma",
        "run_lioness_coexpression",
    ):
        capability = policy.workflows[action].output_capability
        assert "gene_expression" in capability.accepted_input_modalities
        assert capability.incompatible_input_artifacts == ["mutation_matrix"]


def test_registry_generates_role_constraints_and_preserves_handoff_contracts():
    policy = ProjectPolicyLoader().load()
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="guidance",
        requested_outcome=RequestedOutcome(
            operation="analyze",
            artifact_type="community_assignment",
            entity_types=["gene"],
            regulator_types=[],
            target_types=[],
            selection_tags=[
                "hospital_effect_assessment",
                "sequencing_batch_effect_assessment",
                "tf_gene_regulation",
                "bipartite_community_detection",
            ],
            granularity="not_applicable",
            unresolved_dimensions=[],
        ),
    )

    context = validated_workflow_context(
        decision,
        policy,
        include_all=True,
    )
    constraints = context["selection_constraints"]
    options = {item["workflow"]: item for item in constraints["workflow_role_options"]}

    assert constraints["requested_regulator_types"] == []
    assert "role_selection_rule" in constraints
    assert options["PANDA"]["regulator_types"] == ["tf"]
    assert options["PUMA"]["regulator_types"] == ["mirna", "tf"]
    assert any(
        item["from_workflow"] == "COBRA"
        and item["to_workflow"] == "PANDA"
        and "adjusted gene-by-gene co-expression artifact" in item["handoff_contract"]
        for item in context["handoffs"]
    )


def test_same_pipeline_prompt_gets_one_registry_derived_path_and_explicit_handoffs():
    policy = ProjectPolicyLoader().load()
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="guidance",
        capability_match_status="exact",
        matched_actions=["run_condor"],
        requested_outcome=RequestedOutcome(
            operation="analyze",
            artifact_type="community_assignment",
            entity_types=["gene"],
            regulator_types=[],
            target_types=[],
            selection_tags=[
                "hospital_effect_assessment",
                "sequencing_batch_effect_assessment",
                "tf_gene_regulation",
                "bipartite_community_detection",
            ],
            granularity="not_applicable",
        ),
    )

    context = validated_workflow_context(
        decision,
        policy,
        include_all=True,
        task=FULL_PIPELINE_PROMPT,
    )
    constraints = context["selection_constraints"]
    preferred = constraints["preferred_compositions"]

    assert preferred[0]["ordered_workflows"] == ["COBRA", "OTTER", "CONDOR"]
    assert context["compositions"][0]["ordered_workflows"] == [
        "COBRA",
        "OTTER",
        "CONDOR",
    ]
    assert {
        item["workflow"]
        for item in constraints["workflow_role_options"]
        if item["preferred_in_selected_composition"]
    } == {"COBRA", "OTTER", "CONDOR"}
    assert all(
        step["handoff_mode"] == expected
        for step, expected in zip(
            preferred[0]["handoff_steps"],
            ["registered_transformation", "registered_transformation"],
        )
    )
    assert "adjusted gene-by-gene co-expression artifact" in preferred[0]["handoff_steps"][0]["handoff_contract"]


def test_lioness_guidance_predecessor_is_in_the_shared_selected_path():
    policy = ProjectPolicyLoader().load()
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="guidance",
        capability_match_status="exact",
        matched_actions=["run_lioness_puma"],
        recommended_actions=["run_puma", "run_lioness_puma"],
        requested_outcome=RequestedOutcome(
            operation="infer",
            artifact_type="regulatory_network",
            entity_types=["tf", "mirna", "gene"],
            regulator_types=["tf", "mirna"],
            target_types=["gene"],
            selection_tags=["sample_specific", "mirna_regulation"],
            granularity="sample_specific",
        ),
    )

    context = validated_workflow_context(
        decision,
        policy,
        include_all=True,
    )
    preferred = context["selection_constraints"]["preferred_compositions"]

    assert preferred[0]["ordered_workflows"] == ["PUMA", "LIONESS-PUMA"]
    assert context["compositions"][0]["ordered_workflows"] == [
        "PUMA",
        "LIONESS-PUMA",
    ]
    assert "not a direct file handoff" in preferred[0]["handoff_steps"][0]["handoff_contract"]


def test_semantic_purpose_inference_routes_implicit_patient_goal_to_lioness():
    implicit_patient_goal = RequestedOutcome(
        operation="infer",
        artifact_type="regulatory_network",
        entity_types=["tf", "gene"],
        regulator_types=["tf"],
        target_types=["gene"],
        granularity="sample_specific",
    )
    cohort_goal = implicit_patient_goal.model_copy(
        update={"granularity": "aggregate"}
    )

    patient_match = match_requested_outcome(implicit_patient_goal)
    cohort_match = match_requested_outcome(cohort_goal)

    assert patient_match.status == "exact"
    assert patient_match.matched_actions == ["run_lioness_panda"]
    assert cohort_match.status == "ambiguous"
    assert cohort_match.matched_actions == []
