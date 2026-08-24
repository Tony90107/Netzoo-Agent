from __future__ import annotations

import json
from pathlib import Path

import sys

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.graph.prompts import build_graph_prompts  # noqa: E402
from netzoo_agent_core.llm import build_semantic_interpreter_prompt  # noqa: E402
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


def test_registered_capability_metadata_is_the_only_pipeline_source():
    policy = ProjectPolicyLoader().load()
    cobra = policy.workflows["run_cobra"].output_capability
    panda = policy.workflows["run_panda"].output_capability
    condor = policy.workflows["run_condor"].output_capability

    assert "hospital_effect_assessment" in cobra.selection_tags
    assert cobra.handoff_targets == ["run_panda"]
    assert panda.handoff_targets == ["run_condor"]
    assert condor.handoff_targets == []


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
        and "corrected gene-by-sample matrix" in item["handoff_contract"]
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

    assert preferred[0]["ordered_workflows"] == ["COBRA", "PANDA", "CONDOR"]
    assert {
        item["workflow"]
        for item in constraints["workflow_role_options"]
        if item["preferred_in_selected_composition"]
    } == {"COBRA", "PANDA", "CONDOR"}
    assert all(
        step["handoff_mode"] == expected
        for step, expected in zip(
            preferred[0]["handoff_steps"],
            ["independent_preparation", "registered_transformation"],
        )
    )
    assert "corrected gene-by-sample matrix" in preferred[0]["handoff_steps"][0]["handoff_contract"]


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
    assert cohort_match.status == "exact"
    assert cohort_match.matched_actions == ["run_panda"]
