"""Harness repair P3 (ROUND-P3.md, spec 7.2): answers bound in code, answered waits settled, two rounds at most."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import AIMessage, HumanMessage, TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement  # noqa: E402
from netzoo_agent_core.contracts.core_decision import CoreDecision, FactQuestion  # noqa: E402
from netzoo_agent_core.contracts.task_state import PendingQuestion, TaskFact, TaskState  # noqa: E402
from netzoo_agent_core.engine.task_updates import bind_answers, opened_goal  # noqa: E402
from netzoo_agent_core.interpretation.core_decision import with_core  # noqa: E402
from netzoo_agent_core.interpretation.task_answers import (  # noqa: E402
    EXHAUSTED_NOTE, answered_check, clarification_rounds,
)

UNSURE = "I can't tell whether those are somatic calls or germline variants"


def _origin(**extra) -> PendingQuestion:
    return PendingQuestion(question_id="dimension:mutation_origin:x", source="dimension", what="mutation_origin",
                           question="Are these acquired somatic mutations, or inherited germline variants?",
                           user_quote=UNSURE, options={"somatic": ["SAMBAR"], "germline": []},
                           labels={"somatic": "somatic mutations", "germline": "germline variants"}, **extra)


def _task(*pending, **extra) -> TaskState:
    return TaskState(task_id="t", pending=list(pending), **extra)


def test_the_goal_is_the_request_without_the_follow_up_wrapping():
    wrapped = "Previous NetZoo goal: Previous NetZoo goal: Run SAMBAR.\nUser follow-up: a\nUser follow-up: b"
    assert opened_goal(wrapped) == "Run SAMBAR."


def test_a_reply_naming_one_option_binds_it_by_value_or_label():
    for reply, value in (("They are germline variants.", "germline"), ("somatic, from tumour vs normal", "somatic")):
        state, [fact], corrected = bind_answers(_task(_origin()), reply)
        assert (fact.value, fact.answer_quote, corrected, state.pending) == (value, reply, False, [])


def test_a_reply_naming_both_options_or_neither_binds_nothing():
    for reply in ("Either somatic or germline, I really don't know.", "Not sure, the README is silent."):
        state, bound, _ = bind_answers(_task(_origin()), reply)
        assert bound == [] and len(state.pending) == 1


def test_a_count_is_bound_by_its_candidate_with_thousands_commas_set_aside():
    panel = PendingQuestion(question_id="count:feature_count:x", source="count", what="feature_count",
                            question="Which of these is right: 200 or 2,000?", user_quote="200 or 2,000 proteins",
                            options={"200": ["LIONESS-DRAGON"], "2000": []})
    _, [fact], _ = bind_answers(_task(panel), "It is the 2,000-protein discovery panel.")
    assert fact.value == "2000"
    _, bound, _ = bind_answers(_task(panel), "Use a threshold of 0.200 on it.")  # part of a decimal names nothing
    assert bound == []


def test_one_word_naming_options_of_two_questions_binds_neither():
    matched = PendingQuestion(question_id="dimension:samples_matched:x", source="dimension", what="samples_matched",
                              question="Were the different omics tables measured on the same samples?",
                              user_quote="same mice", options={"same_samples": ["DRAGON"], "different_samples": []})
    aligned = matched.model_copy(update={"question_id": "dimension:sample_alignment:x", "what": "sample_alignment",
                                         "user_quote": "same IDs"})
    state, bound, _ = bind_answers(_task(matched, aligned), "the same samples")
    assert bound == [] and len(state.pending) == 2


def test_yes_or_no_binds_only_the_one_open_agent_question():
    agent = PendingQuestion(question_id="agent:SAMBAR:x", source="agent", what="SAMBAR", yes_no=True,
                            question="Are the calls somatic?", user_quote="somatic calls")
    for reply, value in (("Yes, they are.", "yes"), ("No. They are germline.", "no")):
        _, [fact], _ = bind_answers(_task(agent), reply)
        assert fact.value == value
    other = agent.model_copy(update={"question_id": "agent:SAMBAR:y", "question": "Are all 80 tumours in it?"})
    _, bound, _ = bind_answers(_task(agent, other), "yes")
    assert bound == []


def test_a_correction_supersedes_the_known_answer():
    known = TaskFact(question_id="dimension:mutation_origin:x", source="dimension", what="mutation_origin",
                     question="q", user_quote=UNSURE, options={"somatic": ["SAMBAR"], "germline": []},
                     labels={}, value="somatic", answer_quote="somatic", turn=1)
    state, [fact], corrected = bind_answers(_task(facts=[known]), "Sorry, they are germline.")
    assert corrected and [f.status for f in state.facts] == ["superseded", "known"] and fact.value == "germline"


def _waiting(task: str) -> CapabilityCheck:
    return CapabilityCheck(requirements=[CheckedRequirement(
        quote="Run SAMBAR on brca_variant_matrix.csv", kind="result", status="needs_fact", depends_on="mutation_origin",
        unknown_quote=task, outcomes={"somatic": ["sambar.subtypes"], "germline": []},
        delivered_by=["sambar.subtypes"])])


def _known(value: str) -> TaskState:
    return _task(facts=[TaskFact(question_id="dimension:mutation_origin:x", source="dimension", what="mutation_origin",
                                 question="Are these acquired somatic mutations, or inherited germline variants?",
                                 user_quote=UNSURE, options={"somatic": ["SAMBAR"], "germline": []},
                                 labels={"germline": "germline variants"}, value=value,
                                 answer_quote=f"They are {value}.", turn=1)])


def test_an_answered_wait_is_settled_by_its_own_outcome_never_asked_again():
    check = answered_check(_waiting(UNSURE), _known("somatic"))
    (row,) = check.results()
    assert (row.status, row.delivered_by, check.needed_facts()) == ("available", ["sambar.subtypes"], [])
    check = answered_check(_waiting(UNSURE), _known("germline").model_dump(mode="json"))
    (row,) = check.results()
    assert row.status == "not_available" and check.full_gap
    assert row.limits == ['You answered "They are germline." to "Are these acquired somatic mutations, or inherited '
                          'germline variants?": with germline variants, none of the workflows matched to this result '
                          '(SAMBAR) gives it']


def test_a_wait_on_other_words_or_without_the_answer_as_an_outcome_still_waits():
    other = answered_check(_waiting("the tumour cohort is mixed"), _known("somatic"))
    assert other.results()[0].status == "needs_fact"
    unknown = _known("somatic").model_copy(update={"facts": [_known("somatic").facts[0].model_copy(
        update={"value": "mosaic"})]})
    assert answered_check(_waiting(UNSURE), unknown).results()[0].status == "needs_fact"


def test_a_third_round_is_not_asked():
    ask = CoreDecision(kind="ASK", basis="fact_agent", facts=[FactQuestion(question="Are the calls somatic?")])
    assert "clarification" not in clarification_rounds(ask, _task(rounds=1)).evidence
    assert clarification_rounds(ask, _task(rounds=2)).evidence["clarification"] == {"rounds": 2, "status": "exhausted"}
    assert "clarification" not in clarification_rounds(ask, _task(rounds=2, status="closed")).evidence
    do = CoreDecision(kind="DO", basis="results_given")
    assert "clarification" not in clarification_rounds(do, _task(rounds=5)).evidence


def test_an_exhausted_ask_says_so_before_what_is_still_missing():
    from netzoo_agent_core.interpretation.core_views import core_view

    ask = clarification_rounds(CoreDecision(kind="ASK", basis="fact_agent", workflows=["SAMBAR"], facts=[FactQuestion(
        question="Are the calls somatic?", user_quote="somatic calls", workflows=["SAMBAR"])]), _task(rounds=2))
    decision = with_core(TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9,
                                      reason="r"), ask)
    state = {"decision": decision.model_dump(), "messages": [HumanMessage(content="Run SAMBAR on somatic calls.")]}
    result = core_view(None, state, lambda content, kind: {"messages": [AIMessage(content=content)],
                                                           "reply_kind": kind})
    text = result["messages"][-1].content
    assert text.startswith(EXHAUSTED_NOTE) and "Are the calls somatic?" in text
    assert result["reply_kind"] == "ask_facts"
