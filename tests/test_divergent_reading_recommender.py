"""Log 200: divergent readings get a study-fact recommendation, advisory only.

Case 4 ("each patient's regulatory wiring is different ... each person's per-TF
regulatory strength over its targets") was read both as one TF-gene network per
sample (LIONESS-PANDA) and as TF activity per sample (GIRAFFE). Their inputs are
the same, so no folder content separates them (Log 187). What does is the
per-sample quantity the user needs: wiring to targets, or regulator activity.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts import LLMUsage, TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis, RequestedOutcome  # noqa: E402
from netzoo_agent_core.graph.condition_recommender import (  # noqa: E402
    condition_options,
    invoke_condition_recommender,
    is_divergent_reading_tie,
    is_method_tie,
)
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.pricing import PriceCatalog  # noqa: E402
from netzoo_agent_core.trace_store import LocalTraceStore  # noqa: E402
from netzoo_agent_core.tracing import TraceRecorder  # noqa: E402

CASE_4 = (
    "data/blind-neutral/case-4/ has expression, motif and PPI files. I believe each patient's "
    "regulatory wiring is different, and later I want to relate each person's per-TF regulatory "
    "strength over its targets to survival time."
)
READING_QUESTION = (
    "Which result do you mean: inferred regulator-to-target associations, one result per sample "
    "(LIONESS-PANDA); or inferred transcription-factor-by-sample activity values (GIRAFFE)?"
)
AUTHORITY = ("action", "should_execute", "capability_match_status", "matched_actions")


def _divergent(actions=("run_lioness_panda", "run_giraffe")) -> TaskDecision:
    network = RequestedOutcome(operation="infer", artifact_type="regulatory_network",
                               granularity="sample_specific", regulator_types=["tf"],
                               target_types=["gene"], input_artifacts=["expression_matrix"])
    activity = RequestedOutcome(operation="infer", artifact_type="tf_activity_matrix",
                                granularity="aggregate", input_artifacts=["expression_matrix"])
    return TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question",
        confidence=0.9, reason="guidance", requested_outcome=network,
        outcome_hypotheses=[OutcomeHypothesis(outcome=network, confidence=0.9),
                            OutcomeHypothesis(outcome=activity, confidence=0.8)],
        hypothesis_actions=list(actions), capability_match_status="ambiguous",
        clarification_question=READING_QUESTION,
    )


def _context(tmp_path, parsed):
    recorder = TraceRecorder(LocalTraceStore(tmp_path / "traces"))
    run_id = recorder.start_run(session_id="log200", profile_id="default")
    calls = []

    def bind(schema, **_):
        calls.append(schema.__name__)
        return SimpleNamespace(invoke=lambda _messages: {"parsed": parsed, "raw": object()})

    context = SimpleNamespace(
        selection_condition_llm=SimpleNamespace(with_structured_output=bind), semantic_claims=False,
        semantic_model_name="fixture", router_max_tokens=200, task_token_budget=10_000,
        recorder=recorder, price_catalog=PriceCatalog(),
    )
    return context, {"run_id": str(run_id)}, calls


def test_the_quantity_axis_separates_wiring_from_activity():
    offered = {option.condition: option.actions for option in condition_options(["run_lioness_panda", "run_giraffe"])}

    assert offered["per_sample_quantity:wiring"] == ("run_lioness_panda",)
    assert offered["per_sample_quantity:activity"] == ("run_giraffe",)
    three = {option.condition: option.actions
             for option in condition_options(["run_lioness_panda", "run_lioness_puma", "run_giraffe"])}
    assert three["per_sample_quantity:wiring"] == ("run_lioness_panda", "run_lioness_puma")


def test_existing_method_ties_are_offered_nothing_new():
    for tie in (["run_panda", "run_otter", "run_giraffe"], ["run_lioness_panda", "run_lioness_puma"],
                ["run_bonobo", "run_lioness_coexpression"]):
        assert not any(option.axis == "per_sample_quantity" for option in condition_options(tie)), tie


def test_divergent_readings_are_recognised_and_are_not_a_method_tie():
    assert is_divergent_reading_tie(_divergent())
    assert not is_method_tie(_divergent())


def test_a_quoted_wiring_fact_recommends_lioness_panda_and_changes_no_authority(tmp_path):
    parsed = {"claims": [{"condition": "per_sample_quantity:wiring",
                          "text_span": "each patient's regulatory wiring is different"}]}
    context, state, calls = _context(tmp_path, parsed)
    decision = _divergent()

    updated, _, _ = invoke_condition_recommender(context, state, CASE_4, decision, LLMUsage(), [])

    assert calls == ["SelectionConditionClaims"]
    assert updated.advisory_recommendation.action == "run_lioness_panda"
    assert updated.clarification_question.startswith("Should I use LIONESS-PANDA")
    for field in AUTHORITY:
        assert getattr(updated, field) == getattr(decision, field), field
    answer = render_outcome_clarification(updated, ProjectPolicyLoader(ROOT).load(), task=CASE_4)
    assert "each patient's regulatory wiring is different" in answer
    assert "**GIRAFFE** — preferred when:" in answer


def test_no_stated_fact_keeps_the_readings_own_question(tmp_path):
    context, state, _ = _context(tmp_path, {"claims": []})
    decision = _divergent()

    updated, _, _ = invoke_condition_recommender(context, state, CASE_4, decision, LLMUsage(), [])

    assert updated.advisory_recommendation is None
    assert updated.clarification_question == READING_QUESTION
