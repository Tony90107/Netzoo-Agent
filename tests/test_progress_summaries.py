from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.progress_summaries import render_progress_summary  # noqa: E402
from netzoo_agent_core.interpretation.semantic_goal import (  # noqa: E402
    classification_progress_detail,
    next_step_progress_detail,
)
from netzoo_agent_core.cli.follow_up import (  # noqa: E402
    build_follow_up_context,
    build_next_turn_prompt,
    render_next_turn_prompt,
    resolve_next_turn_input,
)
from netzoo_agent_core.contracts import (  # noqa: E402
    ContextualReplyResolution,
    RequestedOutcome,
    TaskDecision,
    WorkflowPlan,
)
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402


def test_no_tool_summary_explains_source_and_safety():
    summary = render_progress_summary(
        "concept", {"source": "registered workflow specification"}
    )

    assert summary is not None
    assert "do not need to inspect files or run tools" in summary
    assert "registered workflow specification" in summary


def test_next_step_summary_explains_stable_guidance_without_tools():
    summary = render_progress_summary(
        "next_step",
        {"action": "no_tool", "in_scope": "true", "should_execute": "false"},
    )

    assert summary is not None
    assert "registered workflow information" in summary
    assert "without running an analysis" in summary


def test_next_step_summary_explains_analysis_preparation():
    summary = render_progress_summary(
        "next_step",
        {"action": "run_panda", "in_scope": "true", "should_execute": "true"},
    )

    assert summary is not None
    assert "prepare the matching registered workflow" in summary


def test_multiple_semantic_candidates_do_not_select_one_workflow():
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="guidance",
    )
    plan = WorkflowPlan(
        workflow="NO-TOOL",
        objective="guidance",
        decision=decision.model_dump(),
        status="respond_only",
    )

    prompt = build_next_turn_prompt(
        {
            "plan": plan.model_dump(),
            "semantic_goal": {
                "candidates": ["run_lioness_panda", "run_lioness_puma"],
                "relationship": "alternatives",
            },
        }
    )

    assert prompt.continuation_action is None
    assert (
        prompt.question
        == "Enter the requested clarification or describe another NetZoo goal."
    )


def test_workflow_composition_recommends_its_final_registered_action():
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="guidance",
        recommended_actions=["run_puma", "run_lioness_puma"],
    )
    plan = WorkflowPlan(
        workflow="NO-TOOL",
        objective="guidance",
        decision=decision.model_dump(),
        status="respond_only",
    )

    prompt = build_next_turn_prompt(
        {
            "plan": plan.model_dump(),
            "semantic_goal": {
                "candidates": ["run_puma", "run_lioness_puma"],
                "relationship": "composition",
            },
        }
    )

    assert prompt.continuation_action == "run_lioness_puma"
    assert "recommended LIONESS-PUMA workflow" in prompt.question
    rendered = render_next_turn_prompt(prompt)
    assert rendered.startswith("----------------------------------------\nNext step\n")
    assert "Enter a follow-up question" in rendered
    assert "Enter/back: start a new task | exit: close" in rendered
    assert "reply yes" not in rendered.casefold()

    context = build_follow_up_context(
        {
            "plan": plan.model_dump(),
            "semantic_goal": {
                "candidates": ["run_puma", "run_lioness_puma"],
                "relationship": "composition",
            },
        },
        prompt,
        "Which tools produce sample-specific miRNA networks?",
    )
    assert context.candidate_actions == ["run_puma", "run_lioness_puma"]
    assert context.prior_user_goal.startswith("Which tools")
    assert [item.workflow for item in context.candidate_workflows] == [
        "PUMA",
        "LIONESS-PUMA",
    ]
    assert "motif_file" in context.candidate_workflows[0].required_inputs
    assert context.candidate_workflows[0].granularities == ["aggregate"]
    assert context.candidate_workflows[1].granularities == [
        "aggregate",
        "sample_specific",
    ]


def test_cobra_panda_handoff_prompt_requires_the_complete_bundle_before_execute():
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="COBRA-to-PANDA guidance",
        recommended_actions=["run_cobra", "run_panda"],
    )
    plan = WorkflowPlan(
        workflow="NO-TOOL",
        objective="COBRA-to-PANDA guidance",
        decision=decision.model_dump(),
        status="respond_only",
    )

    prompt = build_next_turn_prompt({"plan": plan.model_dump()})

    assert prompt.continuation_action == "run_cobra"
    assert prompt.expected_field is None
    assert prompt.required_fields == [
        "expression_file",
        "design_file",
        "motif_file",
        "ppi_file",
    ]
    assert "COBRA → PANDA" in prompt.question
    assert "`expression_file`" in prompt.question
    assert "`design_file`" in prompt.question
    assert "`motif_file`" in prompt.question
    assert "`ppi_file`" in prompt.question
    assert "inspect the complete input bundle" in prompt.question
    assert "separate ready plan and /execute authorization" in prompt.question

    continuation = resolve_next_turn_input(
        prompt,
        ContextualReplyResolution(
            kind="accept_workflow",
            reason="The user supplied the requested bundle.",
            selected_action="run_cobra",
        ),
        "expression_file=data/expression.tsv design_file=data/design.tsv "
        "motif_file=data/motif.tsv ppi_file=data/ppi.tsv",
    )
    assert continuation is not None
    assert "PREVIOUS_ACTION=run_cobra" in continuation
    assert "design_file=data/design.tsv" in continuation
    assert "motif_file=data/motif.tsv" in continuation


def test_direct_retrieval_action_does_not_enter_workflow_follow_up_contract():
    decision = TaskDecision(
        action="web_search",
        in_scope=True,
        should_execute=True,
        intent_type="answer_question",
        confidence=1.0,
        reason="direct retrieval",
        matched_actions=["web_search"],
    )
    plan = WorkflowPlan(
        workflow="WEB-SEARCH",
        objective="retrieve official gene records",
        decision=decision.model_dump(),
        status="ready",
    )

    prompt = build_next_turn_prompt(
        {
            "plan": plan.model_dump(),
            "tool_results": [
                {
                    "action": "web_search",
                    "status": "failed",
                    "summary": "The tool or its validation failed.",
                    "errors": ["ImportError: MCP adapter is unavailable"],
                }
            ],
            "evaluation": {"status": "failed"},
        }
    )
    context = build_follow_up_context(
        {"plan": plan.model_dump()},
        prompt,
        "Search NCBI Gene for TP53.",
    )

    assert context.candidate_actions == []
    assert context.candidate_workflows == []


def test_guidance_classification_labels_condor_as_final_result_boundary():
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="guidance",
        capability_match_status="exact",
        matched_actions=["run_condor"],
        recommended_actions=["run_condor"],
    )

    detail = classification_progress_detail(
        {
            "goal": "gene regulatory community modules",
            "candidates": ["run_condor"],
            "relationship": "single",
            "request_mode": "guidance",
        },
        decision,
    )

    assert detail["workflow_scope"] == "final_result"


def test_guidance_ambiguity_is_not_presented_as_cli_clarification():
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="guidance",
        capability_match_status="ambiguous",
        clarification_question="Should the result be aggregate or sample-specific?",
    )

    detail = next_step_progress_detail(
        decision,
        {"request_mode": "guidance"},
    )

    assert detail["status"] == "guidance"
    assert "question" not in detail


def test_unknown_nonexecuting_mode_is_not_presented_as_cli_clarification():
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.8,
        reason="The request is conceptual.",
        capability_match_status="ambiguous",
        clarification_question="Should the result be aggregate or sample-specific?",
    )

    detail = next_step_progress_detail(
        decision,
        {"request_mode": "unknown"},
    )

    assert detail["status"] == "guidance"
    assert "question" not in detail


def test_guidance_hypotheses_are_not_shown_as_final_workflow_matches():
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.9,
        reason="guidance",
        capability_match_status="ambiguous",
        hypothesis_actions=[
            "run_panda",
            "run_puma",
            "run_lioness_panda",
            "run_lioness_puma",
        ],
    )

    detail = classification_progress_detail(
        {
            "candidates": [
                "run_panda",
                "run_puma",
                "run_lioness_panda",
                "run_lioness_puma",
            ],
            "request_mode": "guidance",
            "relationship": "alternatives",
        },
        decision,
    )

    assert detail["workflows"] == []
    assert detail["workflow_scope"] == "match"


def test_exact_guidance_exposes_registry_derived_workflow_path():
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="guidance",
        capability_match_status="exact",
        matched_actions=["run_lioness_panda"],
        recommended_actions=["run_panda", "run_lioness_panda"],
    )

    detail = classification_progress_detail(
        {
            "candidates": ["run_panda", "run_lioness_panda"],
            "request_mode": "guidance",
            "relationship": "composition",
            "match_status": "exact",
        },
        decision,
    )

    assert detail["workflow_path"] == ["PANDA", "LIONESS-PANDA"]


def test_exact_guidance_uses_conditional_handoff_path_for_batch_effects():
    policy = ProjectPolicyLoader().load()
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="guidance",
        capability_match_status="exact",
        matched_actions=["run_panda"],
        recommended_actions=["run_panda"],
        requested_outcome=RequestedOutcome(
            operation="explain",
            artifact_type="expression_matrix",
            entity_types=["gene", "sample"],
            selection_tags=["sequencing_batch_effect_assessment"],
            granularity="aggregate",
        ),
    )

    detail = classification_progress_detail(
        {
            "candidates": ["run_panda"],
            "request_mode": "guidance",
            "relationship": "single",
            "match_status": "exact",
        },
        decision,
        policy,
    )

    assert detail["workflow_path"] == ["COBRA", "PANDA"]
    assert detail["workflow_scope"] == "composition"


def test_exact_guidance_recovers_registry_tags_from_task_text():
    policy = ProjectPolicyLoader().load()
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="guidance",
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

    detail = classification_progress_detail(
        {"candidates": ["run_panda"], "request_mode": "guidance"},
        decision,
        policy,
        "Remove hospital and sequencing batch effects before PANDA.",
    )

    assert detail["workflow_path"] == ["PANDA"]
    assert detail["workflow_scope"] == "final_result"


def test_normal_panda_guidance_does_not_force_optional_cobra_handoff():
    policy = ProjectPolicyLoader().load()
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="guidance",
        capability_match_status="exact",
        matched_actions=["run_panda"],
        recommended_actions=["run_panda"],
        requested_outcome=RequestedOutcome(
            operation="infer",
            artifact_type="regulatory_network",
            entity_types=["tf", "gene"],
            regulator_types=["tf"],
            target_types=["gene"],
            selection_tags=["tf_gene_regulation", "aggregate_network"],
            granularity="aggregate",
        ),
    )

    detail = classification_progress_detail(
        {
            "candidates": ["run_panda"],
            "request_mode": "guidance",
            "relationship": "single",
            "match_status": "exact",
        },
        decision,
        policy,
    )

    assert detail["workflow_path"] == ["PANDA"]
    assert detail["workflow_scope"] == "final_result"


def test_guidance_next_step_does_not_offer_only_condor_input_path():
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="guidance",
        recommended_actions=["run_condor"],
    )
    plan = WorkflowPlan(
        workflow="NO-TOOL",
        objective="pipeline guidance",
        decision=decision.model_dump(),
        status="respond_only",
    )

    prompt = build_next_turn_prompt(
        {
            "plan": plan.model_dump(),
            "semantic_goal": {
                "candidates": ["run_condor"],
                "relationship": "single",
                "request_mode": "guidance",
            },
        }
    )

    assert prompt.continuation_action is None
    assert "CONDOR" not in prompt.question
    assert "complete recommended pipeline" in prompt.question


def test_guidance_does_not_offer_unsupported_alternative_as_next_step():
    decision = TaskDecision(
        action="no_tool",
        in_scope=False,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="guidance",
        capability_match_status="unsupported",
        alternative_actions=["run_condor"],
    )
    plan = WorkflowPlan(
        workflow="NO-TOOL",
        objective="pipeline guidance",
        decision=decision.model_dump(),
        status="respond_only",
    )

    prompt = build_next_turn_prompt(
        {
            "plan": plan.model_dump(),
            "semantic_goal": {
                "relationship": "single",
                "request_mode": "guidance",
            },
        }
    )

    assert prompt.kind == "completed"
    assert "supported alternative above" not in prompt.question
    assert "complete recommended pipeline" in prompt.question


def test_unsupported_outcome_offers_alternative_without_execution_continuation():
    outcome = RequestedOutcome(
        operation="acquire",
        artifact_type="measurement_dataset",
        entity_types=["mirna"],
        display_entities=["miRNA"],
        regulator_types=[],
        target_types=[],
        granularity="sample_specific",
        unresolved_dimensions=[],
    )
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="unsupported",
        requested_outcome=outcome,
        capability_match_status="unsupported",
        alternative_actions=["run_lioness_puma"],
    )
    plan = WorkflowPlan(
        workflow="NO-TOOL",
        objective="unsupported",
        decision=decision.model_dump(),
        status="respond_only",
    )

    prompt = build_next_turn_prompt({"plan": plan.model_dump()})

    assert prompt.kind == "alternative_outcome"
    assert prompt.continuation_action is None
    assert prompt.alternative_action == "run_lioness_puma"
    assert "LIONESS-PUMA" in prompt.question
    assert "supported alternative above" not in prompt.question
    continuation = resolve_next_turn_input(
        prompt,
        ContextualReplyResolution(
            kind="accept_workflow",
            reason="Accepted the supported alternative.",
        ),
        "sounds good",
    )
    assert continuation.startswith("CONFIRMED_OUTCOME_ACTION=run_lioness_puma")
    assert "CONFIRMED_GRANULARITY=sample_specific" in continuation
    assert "PREVIOUS_ACTION" not in continuation


def test_ambiguous_outcome_asks_for_clarification_without_continuation():
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=1.0,
        reason="ambiguous",
        capability_match_status="ambiguous",
        clarification_question="Which result do you want?",
    )
    plan = WorkflowPlan(
        workflow="NO-TOOL",
        objective="ambiguous",
        decision=decision.model_dump(),
        status="respond_only",
    )

    prompt = build_next_turn_prompt({"plan": plan.model_dump()})

    assert prompt.kind == "clarify_outcome"
    assert prompt.continuation_action is None


def test_ranked_advisory_outcome_does_not_force_a_clarification_prompt():
    decision = TaskDecision(
        action="no_tool",
        in_scope=True,
        should_execute=False,
        intent_type="answer_question",
        confidence=0.9,
        reason="One advisory workflow remains after Router ranking.",
        capability_match_status="ambiguous",
        hypothesis_actions=["run_lioness_puma"],
        clarification_question=None,
    )
    plan = WorkflowPlan(
        workflow="NO-TOOL",
        objective="answer guidance",
        decision=decision.model_dump(),
        status="respond_only",
    )

    prompt = build_next_turn_prompt({"plan": plan.model_dump()})

    assert prompt.kind == "completed"


def test_ambiguous_hypotheses_progress_preserves_candidate_context():
    text = render_progress_summary(
        "next_step",
        {
            "action": "no_tool",
            "in_scope": "true",
            "should_execute": "false",
            "capability_match_status": "ambiguous",
            "hypothesis_count": "3",
        },
    )

    assert "compatible workflow" in text
    assert "clarification" in text
    assert "requested result is ambiguous" not in text
