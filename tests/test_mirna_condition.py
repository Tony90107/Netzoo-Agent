"""Log 269 (user decision): a functional description may point to miRNA methods.

"Short non-coding molecules degrade the products post-transcription" never
names miRNA, so the regulator scope stays unresolved and the tie mixes TF-only
and TF/miRNA methods. A registered study condition lets the model claim it with
a verbatim quote; the result is an advisory PUMA recommendation the user must
confirm, never a typed regulator fact.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from netzoo_agent_core.contracts import LLMUsage, TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis, RequestedOutcome, SelectionConditionClaims  # noqa: E402
from netzoo_agent_core.graph.condition_recommender import (  # noqa: E402
    condition_options, invoke_condition_recommender, recommend_from_claims, separating_question,
)
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from test_condition_recommender import _context  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()
TIE = ["run_panda", "run_puma", "run_lioness_panda", "run_lioness_puma", "run_otter", "run_giraffe"]
TASK = ("Another type of 'short non-coding molecule' directly degraded the products post-transcription. "
        "Do you have a tool specifically for this class of molecules?")
QUOTE = "another type of 'short non-coding molecule' directly degraded the products post-transcription"


def _claims(*pairs):
    return SelectionConditionClaims.model_validate(
        {"claims": [{"condition": c, "text_span": s} for c, s in pairs]})


def test_the_condition_is_offered_only_when_the_tie_mixes_regulator_scopes():
    offered = {o.condition: o.actions for o in condition_options(TIE)}
    assert offered["regulator_class:mirna"] == ("run_puma", "run_lioness_puma")
    assert condition_options(TIE)[0].axis == "regulator_class"
    for tie in (["run_panda", "run_otter", "run_giraffe"], ["run_puma", "run_lioness_puma"]):
        assert not any(o.axis == "regulator_class" for o in condition_options(tie)), tie


def test_the_miRNA_question_comes_before_algorithm_questions():
    question = separating_question(condition_options(TIE), TIE)
    assert question.split("(1) ", 1)[1].startswith("Do the regulators include miRNAs")


def test_a_quoted_description_recommends_the_base_method_and_asks_for_confirmation():
    recommendation, rejected = recommend_from_claims(TASK, _claims(("regulator_class:mirna", QUOTE)),
                                                     condition_options(TIE), TIE)
    assert rejected == []
    assert recommendation.action == "run_puma"
    assert recommendation.conditions[0].text_span == QUOTE
    assert recommendation.assumptions[0].startswith("This reads the molecules you describe as miRNAs.")


def test_an_unquoted_claim_recommends_nothing():
    recommendation, rejected = recommend_from_claims(
        TASK, _claims(("regulator_class:mirna", "microRNAs degrade transcripts")), condition_options(TIE), TIE)
    assert recommendation is None and rejected[0]["reason"] == "quote_not_in_request"


def test_the_reply_names_puma_keeps_the_per_sample_option_and_asks_to_confirm(tmp_path):
    outcome = RequestedOutcome(operation="explain", artifact_type="regulatory_network", granularity="unknown")
    decision = TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question", confidence=0.9,
        reason="tie", capability_match_status="ambiguous", hypothesis_actions=list(TIE), requested_outcome=outcome,
        outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=0.9)],
    )
    ctx, state, _, _ = _context(tmp_path, {
        "claims": [{"condition": "regulator_class:mirna", "text_span": QUOTE}],
        "preference": {"action": "run_puma", "selection_tags": ["mirna_regulation"], "text_spans": [QUOTE],
                       "rationale": "PUMA models miRNA regulators.", "assumptions": ["A miRNA list is available."]},
    })
    updated, _, _ = invoke_condition_recommender(ctx, state, TASK, decision, LLMUsage(), [])

    assert updated.advisory_recommendation.action == "run_puma"
    assert updated.advisory_recommendation.assumptions[0].startswith("This reads the molecules you describe as miRNAs.")
    assert updated.action == "no_tool" and not updated.should_execute and updated.matched_actions == []
    answer = render_outcome_clarification(updated, POLICY, task=TASK)
    assert "**PUMA** fits better" in answer
    assert "Conditional assumptions to confirm" in answer and "miRNA-target prior" in answer
    assert "**LIONESS-PUMA**" in answer
    assert "keeps each miRNA's cooperativity" in answer


# -- Log 271: an offered condition id written as a philosophy --------------

def _tie_decision():
    outcome = RequestedOutcome(operation="explain", artifact_type="regulatory_network", granularity="unknown")
    return TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question", confidence=0.9,
        reason="tie", capability_match_status="ambiguous", hypothesis_actions=list(TIE), requested_outcome=outcome,
        outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=0.9)],
    )


def _misplaced(quote, philosophy=("regulator_class:mirna",)):
    # The recorded Log 270 shape: the condition id in requested_philosophy, claims empty.
    return {"requested_philosophy": list(philosophy), "requirement_quote": quote,
            "capability_gap": None, "preference": None, "claims": []}


def test_a_condition_written_as_a_philosophy_is_checked_as_the_claim_it_is(tmp_path):
    ctx, state, store, run_id = _context(tmp_path, _misplaced(QUOTE))
    updated, _, _ = invoke_condition_recommender(ctx, state, TASK, _tie_decision(), LLMUsage(), [])

    assert updated.advisory_recommendation.action == "run_puma"
    assert updated.advisory_recommendation.conditions[0].text_span == QUOTE
    assert "routing.selection_conditions_salvaged" in [e.event_type for e in store.read_events(run_id)]


def test_a_misplaced_condition_with_an_invented_quote_or_id_recommends_nothing(tmp_path):
    for parsed in (_misplaced("microRNAs degrade the transcripts"),
                   _misplaced(QUOTE, philosophy=("regulator_class:sirna",))):
        ctx, state, _, _ = _context(tmp_path, parsed)
        updated, _, _ = invoke_condition_recommender(ctx, state, TASK, _tie_decision(), LLMUsage(), [])
        assert updated.advisory_recommendation is None
