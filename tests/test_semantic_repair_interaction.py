"""Observed failure patterns, replayed offline; not live-model accuracy claims."""
import json

import pytest

from test_routing_evaluation import FixtureProvider, hypothesis, run
from netzoo_agent_core.contracts import RequestedOutcome
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation


def test_generation_schema_constrains_output_dependent_fields():
    schema = RequestedOutcome.model_json_schema()
    variants = {v["properties"]["artifact_type"]["const"]: v["properties"] for v in schema["anyOf"]}
    for artifact in ("sample_cluster_assignment", "sample_distance_matrix"):
        assert variants[artifact]["granularity"]["enum"] == ["aggregate", "unknown"]
        assert variants[artifact]["entity_types"]["items"]["enum"] == ["sample", "unknown"]
        assert variants[artifact]["regulator_types"]["maxItems"] == 0
        assert variants[artifact]["target_types"]["maxItems"] == 0
    assert "regulator_types" not in variants["regulatory_network"]


@pytest.mark.parametrize("artifact,changes,missing", [
    ("sample_distance_matrix", {"granularity": "sample_specific", "regulator_types": ["tf"]}, None),
    ("sample_cluster_assignment", {"granularity": "sample_specific"}, "operation"),
    ("multi_omic_network", {"target_types": ["gene"]}, None),
])
def test_observed_cross_field_errors_receive_actionable_repair(artifact, changes, missing):
    item = hypothesis()
    item["outcome"].update(artifact_type=artifact, **changes)
    if missing:
        item["evidence"] = [e for e in item["evidence"] if e["dimension"] != missing]
    provider = FixtureProvider(first={"request_mode": "guidance", "semantic_goal": "Grouping",
                                      "outcome_hypotheses": [item]})
    row = run(provider)["results"][0]
    message = provider.calls[1][1][-1].content
    assert "repair_feedback" in message
    assert '"expected"' in message and '"actual"' in message
    assert artifact in message
    if missing:
        assert "operation=analyze" in message
    assert row["review_repair_attempted"] and row["review_repair_validated"]
    assert row["review_repair_correct"] and row["passed"]


def test_schema_invalid_proposal_is_retained_for_repair_without_relaxing_validation():
    first = {"request_mode": "guidance", "semantic_goal": "Grouping",
             "outcome_hypotheses": [hypothesis()], "assumptions": ["Wrong nesting"]}
    provider = FixtureProvider(first=first)
    row = run(provider)["results"][0]
    message = provider.calls[1][1][-1].content
    assert '"assumptions": ["Wrong nesting"]' in message
    assert "outcome_hypothesis.assumptions" in message
    assert row["review_repair_correct"]
    with pytest.raises(ValueError):
        SemanticInterpretation.model_validate(first)


def test_failed_repair_has_no_fabricated_goal_or_execution_shortcut():
    provider = FixtureProvider(first=ValueError("invalid"))
    report = run(provider)
    row = report["results"][0]
    assert row["status"] == "fallback" and row["outcome"] == {}
    assert row["interaction_passed"]
    assert "Clarification needed" not in row["progress"]
    assert "confirmation before planning" not in row["answer"]
    assert "to start the recommended" not in row["next_step"]["question"]
    assert row["next_step"].get("continuation_action") is None
    assert report["summary"]["review_repair_rate"] is None
    assert "invalid" not in json.dumps(row.get("repair_feedback", {}))


def _review_for_original_questions():
    item = hypothesis()
    for evidence in item["evidence"]:
        evidence.update(source="inferred", text_span=None)
    return {"request_mode": "guidance", "semantic_goal": "Subtype patients", "outcome_hypothesis": item}


def test_three_original_questions_have_distinct_complete_surfaces_and_repair_metrics():
    from evaluate_routing import DEFAULT_SCENARIOS, evaluate, load_scenarios
    from routing_repair_replay import RepairReplayProvider

    cases = [case for case in load_scenarios(DEFAULT_SCENARIOS) if case.id.startswith("original-")]
    report = evaluate(cases, provider=RepairReplayProvider(FixtureProvider(review=_review_for_original_questions())),
                      model_name="fixture")
    assert report["metadata"]["source"] == "fixture"
    assert report["metadata"]["first_pass_source"] == "observed_error_reconstruction_not_raw_capture"
    assert report["summary"]["review_repair_attempts"] == 3
    assert report["summary"]["review_repair_rate"] == 1
    assert report["summary"]["provider_calls"] == 6
    assert report["summary"]["passed"] == 3
    q1, q2, q3 = report["results"]
    assert "longer genes" in q1["answer"] and "overall mutation burden" in q1["answer"]
    assert "different genes within the same biological pathway" in q2["answer"]
    assert "does not guarantee" in q2["answer"]
    assert "Changing a file's format" in q3["answer"] and q3["answer"].startswith("Do not use")
    for row in report["results"]:
        assert row["interaction_passed"]
        assert "✓ Workflow — SAMBAR" in row["progress"]
        assert "Next step" in row["next_step_text"]
        assert "Enter/back" in row["next_step_text"]


def test_review_validator_success_is_not_the_same_as_correct_repair():
    item = hypothesis()
    # Terminal distances now conflict with this explicit clustering request.
    # Use unresolved granularity to retain the distinction between an accepted
    # partial interpretation and the complete gold meaning, without requiring
    # the validator to accept a known contradiction.
    item["outcome"]["granularity"] = "unknown"
    item["outcome"]["unresolved_dimensions"] = ["granularity"]
    item["evidence"] = [e for e in item["evidence"] if e["dimension"] != "granularity"]
    provider = FixtureProvider(first={"outcome_hypotheses": []}, review={
        "request_mode": "guidance", "semantic_goal": "Grouping", "outcome_hypothesis": item,
    })
    report = run(provider)
    assert report["summary"]["review_repair_validation_rate"] == 1
    assert report["summary"]["review_repair_rate"] == 0


def test_unrepaired_observed_errors_remain_failures_in_replay():
    from evaluate_routing import DEFAULT_SCENARIOS, evaluate, load_scenarios
    from routing_repair_replay import RepairReplayProvider, reconstructed_proposal

    case = next(c for c in load_scenarios(DEFAULT_SCENARIOS) if c.id == "original-q2")
    bad_review = {"request_mode": "guidance", "semantic_goal": "Grouping",
                  "outcome_hypothesis": reconstructed_proposal(case.id)["outcome_hypotheses"][0]}
    report = evaluate([case], provider=RepairReplayProvider(FixtureProvider(review=bad_review)), model_name="fixture")
    assert report["summary"]["review_repair_attempts"] == 1
    assert report["summary"]["review_repair_validation_rate"] == 0
    assert report["summary"]["review_repair_rate"] == 0
    assert report["results"][0]["status"] == "fallback"
    assert report["results"][0]["interaction_passed"]
    assert report["results"][0]["outcome"] == {}


def test_provider_outage_is_not_reported_as_user_ambiguity():
    row = run(FixtureProvider(first=TimeoutError("private message")))["results"][0]
    assert row["match_basis"] == "provider_unavailable"
    assert row["interaction_passed"]
    assert "Semantic routing unavailable" in row["progress"]
    assert "Clarification needed" not in row["progress"]
    assert "Guidance prepared" not in row["progress"]
    assert "not evidence that your question is unclear" in row["answer"]
    assert not row["next_step"]["allow_workflow_continuation"]


def test_repair_replay_requires_explicit_live_opt_in(monkeypatch, capsys):
    from evaluate_routing import main
    monkeypatch.setattr("evaluate_routing.build_llm", lambda *_a, **_kw: pytest.fail("Unexpected provider call"))
    assert main(["--repair-replay", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "corpus_validation_only" and report["cases"] == 3
    assert main(["--repair-replay", "--case", "mutation-paraphrase-en"]) == 2


def test_explanations_depend_on_capabilities_not_tool_name():
    from netzoo_agent_core.interpretation.scientific_explanations import scientific_explanations
    task = "A sparse mutation matrix has 99% zero entries"
    assert scientific_explanations(task, [{"transformations": ["coexpression"]}], []) == []
    explanations = scientific_explanations(task, [{"transformations": ["pathway_aggregation"]}], [])
    assert len(explanations) == 1 and "different genes" in explanations[0]


def test_all_registered_fallback_candidates_share_non_executing_interaction():
    from workflow_registry import OUTPUT_CAPABILITIES
    from netzoo_agent_core.cli.follow_up import build_next_turn_prompt
    from netzoo_agent_core.contracts import TaskDecision, WorkflowPlan
    for action in OUTPUT_CAPABILITIES:
        decision = TaskDecision(action="no_tool", should_execute=False, in_scope=True, confidence=.35,
                                reason="Candidate only", capability_match_status="fallback", recommended_actions=[action])
        prompt = build_next_turn_prompt({"plan": WorkflowPlan(workflow="NO-TOOL", objective="Guidance",
                                                              decision=decision.model_dump(), status="respond_only").model_dump()})
        assert not prompt.allow_workflow_continuation and prompt.continuation_action is None
        assert "clarification" not in prompt.question.casefold()


def test_raw_schema_failure_keeps_arguments_available_to_reviewer():
    from types import SimpleNamespace
    first = {"request_mode": "guidance", "semantic_goal": "Grouping",
             "outcome_hypotheses": [hypothesis()], "assumptions": ["Wrong nesting"]}
    provider = FixtureProvider(first={"parsed": None,
                                      "raw": SimpleNamespace(tool_calls=[{"args": first}]),
                                      "parsing_error": ValueError("private error")})
    row = run(provider)["results"][0]
    assert row["review_repair_correct"]
    assert "Wrong nesting" in provider.calls[1][1][-1].content
    assert "private error" not in json.dumps(row)


def test_fallback_acknowledgement_cannot_bypass_semantic_validation():
    from netzoo_agent_core.cli.follow_up import (
        build_follow_up_context, build_workflow_continuation, resolve_next_turn_input,
    )
    from netzoo_agent_core.cli.reply_resolution import _validated_resolution
    from netzoo_agent_core.contracts import ContextualReplyResolution, NextTurnPrompt, ReplyIntentDecision, TaskDecision, WorkflowPlan

    row = run(FixtureProvider(first=ValueError("invalid")))["results"][0]
    prompt = NextTurnPrompt.model_validate(row["next_step"])
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=.35,
                            reason="Fallback", recommended_actions=["run_sambar"], capability_match_status="fallback")
    state = {"plan": WorkflowPlan(workflow="NO-TOOL", objective="Guidance", decision=decision.model_dump(), status="respond_only").model_dump()}
    context = build_follow_up_context(state, prompt, "Compare patients from mutations")
    reply = "Use SAMBAR with /data/mutations.csv"
    resolution = _validated_resolution(ReplyIntentDecision(kind="accept_workflow", selected_action="run_sambar",
                                                           confidence=.99, reason="User accepts"), context, reply)
    assert resolution.kind == "follow_up" and resolution.selected_action is None
    assert "Compare patients from mutations" in resolution.resolved_task
    forged = ContextualReplyResolution(kind="accept_workflow", selected_action="run_sambar", reason="Unsafe shortcut")
    assert build_workflow_continuation(prompt, context, forged, reply) is None
    assert "PREVIOUS_ACTION" not in resolve_next_turn_input(prompt, forged, reply)


def test_genuine_fallback_clarification_is_consistent_on_all_surfaces():
    from netzoo_agent_core.contracts import TaskDecision, WorkflowPlan
    from netzoo_agent_core.interpretation.provider_fallback import recover_registry_guidance
    from netzoo_agent_core.interpretation.semantic_goal import publish_routing_progress
    from netzoo_agent_core.interpretation.verified_guidance import guidance_contract, render_verified_guidance
    from netzoo_agent_core.evaluation.guidance_surface import capture_progress, score_surface
    from netzoo_agent_core.policy import ProjectPolicyLoader

    policy = ProjectPolicyLoader().load()
    decision = recover_registry_guidance("Sparse somatic mutation matrix subtyping", policy.workflows, ValueError())
    decision = TaskDecision.model_validate({**decision.model_dump(), "clarification_question": "Do you want distances only or cluster labels?"})
    with capture_progress() as progress:
        publish_routing_progress(decision, {}, policy, "Sparse somatic mutation matrix subtyping")
    answer = render_verified_guidance(decision, guidance_contract(decision, policy, "Sparse somatic mutation matrix subtyping"))
    state = {"plan": WorkflowPlan(workflow="NO-TOOL", objective="Guidance", decision=decision.model_dump(), status="respond_only").model_dump()}
    score = score_surface(decision, state, progress.getvalue(), answer)
    assert score["interaction_passed"]
    assert "Clarification needed" in score["progress"]
    assert decision.clarification_question in answer


@pytest.mark.parametrize("corruption", ["progress", "continuation", "next_step"])
def test_evaluator_detects_inconsistent_terminal_surfaces(monkeypatch, corruption):
    import netzoo_agent_core.evaluation.guidance_surface as surface
    from netzoo_agent_core.contracts import NextTurnPrompt

    if corruption == "progress":
        original = surface.score_surface
        monkeypatch.setattr("evaluate_routing.score_surface", lambda d, s, p, a: original(d, s, p + "\n? Clarification needed", a))
    else:
        original = surface.build_next_turn_prompt
        def bad_next(state):
            prompt = original(state).model_dump()
            if corruption == "continuation":
                prompt.update(allow_workflow_continuation=True, continuation_action="run_sambar")
            else:
                prompt["question"] = "Provide a path to start the recommended SAMBAR workflow."
            return NextTurnPrompt.model_validate(prompt)
        monkeypatch.setattr(surface, "build_next_turn_prompt", bad_next)
    row = run(FixtureProvider(first=ValueError("invalid")))["results"][0]
    assert not row["interaction_passed"] and not row["passed"]
