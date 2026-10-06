"""The research purpose decides among the tools that fit (plan item 3, Log 379).

Log 378: the study purpose was read correctly in 27 of 27 baseline sessions and
used by the decision in none. These tests pin the chain the registry declares
-- conclusion -> each workflow's evidence -> the pick -- and the guards each
withdrawn round taught.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

sys.path[:0] = [str(Path(__file__).parents[1] / "scripts"), str(Path(__file__).parent)]

from workflow_registry import CLAIM_SUPPORT, OUTPUT_CAPABILITIES, PURPOSE_REASONS, purpose_reason  # noqa: E402
from netzoo_agent_core.contracts import HumanMessage, LLMUsage, TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.contracts.data_facts import DataFactsProposal  # noqa: E402
from netzoo_agent_core.graph import router_invocation  # noqa: E402
from netzoo_agent_core.graph import response as response_module  # noqa: E402
from netzoo_agent_core.graph.data_facts_call import verify_data_facts  # noqa: E402
from netzoo_agent_core.routing.purpose_selection import (  # noqa: E402
    needs_tf_priors, purpose_applies, select_by_purpose, with_purpose_selection,
)
from netzoo_agent_core.routing.study_purpose import StudyPurpose  # noqa: E402
from netzoo_agent_core.tracing import NullTraceRecorder  # noqa: E402
from test_reply_cards import POLICY, build_next_turn_prompt, build_reply_card  # noqa: E402

DECISIONS = json.loads((Path(__file__).parents[1] / "docs/research-log/minimal-pairs-2026-10-04/out/b0-decisions.json")
                       .read_text())
A1_QUOTE = "whether the regulatory network changes after treatment across the cohort"
B1_QUOTE = "whether gene co-expression differs between responders and non-responders"


def recorded(key: str) -> TaskDecision:
    """A live baseline decision (Log 378, `9f95e14`): the tie routing produced."""
    return TaskDecision.model_validate(DECISIONS[key]["decision"])


def purpose(design, *claims) -> StudyPurpose:
    return StudyPurpose(design, "", tuple(claims))


A1 = purpose("paired", ("group_difference", A1_QUOTE))
B1 = purpose("groups", ("group_difference", B1_QUOTE))


# --- the registry, typed ----------------------------------------------------

def test_every_cell_is_typed_consistently_with_its_level():
    for key, cell in CLAIM_SUPPORT.items():
        expected = {"direct": {"direct"}, "one_result": {"one_result"},
                    "with_step": {"tested", "descriptive"}}[cell.level]
        assert cell.evidence in expected, key
        for other in cell.stronger:
            assert other in OUTPUT_CAPABILITIES, key
            # A stronger workflow is one the registry declares testable for the same conclusion.
            assert any(CLAIM_SUPPORT.get((other, key[1], design)) and
                       CLAIM_SUPPORT[(other, key[1], design)].evidence == "tested"
                       for design in (key[2], "*", "paired", "groups")), key


def test_only_giraffe_measures_another_quantity():
    other = {key for key, cell in CLAIM_SUPPORT.items() if cell.quantity == "other"}
    assert other == {("run_giraffe", "group_difference", "*"), ("run_giraffe", "individual_change", "paired")}


def test_reasons_say_why_for_the_question_not_how_the_method_works():
    for reason in PURPOSE_REASONS.values():
        assert not any(word in reason.casefold() for word in ("lioness", "panda", "algorithm", "message passing"))
    assert purpose_reason("group_difference", "tested", "paired").endswith("keeping each individual's samples paired")
    assert purpose_reason("causal", "tested", "paired") == ""


# --- the pick -----------------------------------------------------------------

def test_a_paired_group_question_brings_in_the_per_sample_tool_its_cells_name():
    """A1 tied PANDA/OTTER/GIRAFFE/PUMA; LIONESS-PANDA keeps the pairing and allows a test."""
    decision = recorded("A1-1")
    selection = select_by_purpose(decision, A1, priors="stated")
    picked = with_purpose_selection(decision, selection)

    assert selection.recommended == "run_lioness_panda"
    assert picked.advisory_recommendation.action == "run_lioness_panda"
    assert picked.advisory_recommendation.conditions[0].text_span == A1_QUOTE
    # Nothing is removed; the pick is added to the options.
    assert set(decision.hypothesis_actions) < set(picked.hypothesis_actions)
    assert picked.hypothesis_actions[:len(decision.hypothesis_actions)] == decision.hypothesis_actions


@pytest.mark.parametrize("priors", ["unstated", "ruled_out", None])
def test_a_tool_needing_priors_is_never_picked_unless_the_priors_are_stated(priors):
    """Log 371 B4 and Log 377's bug: "unstated" must not count as having them."""
    selection = select_by_purpose(recorded("A1-1"), A1, priors=priors)

    assert selection.recommended is None
    assert selection.reason == "no workflow's needed inputs are stated"


def test_bound_prior_files_count_as_stated():
    selection = select_by_purpose(recorded("A1-1"), A1, priors=None,
                                  stated={"motif_file": "m.tsv", "ppi_file": "p.tsv"})

    assert selection.recommended == "run_lioness_panda"


def test_a_two_group_coexpression_question_picks_the_tool_whose_output_answers_it():
    """B1 tied COBRA/LIONESS-COEXPRESSION with no other data; COBRA's group component answers it."""
    selection = select_by_purpose(recorded("B1-1"), B1, priors="ruled_out")

    assert selection.recommended == "run_cobra"


def test_cobra_needs_a_verified_two_group_design_for_its_design_matrix():
    selection = select_by_purpose(recorded("B1-1"), purpose(None, ("group_difference", B1_QUOTE)),
                                  priors="ruled_out")

    assert selection is None or selection.recommended != "run_cobra"


def test_equal_best_tools_are_not_separated():
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=1, reason="tie",
                            capability_match_status="ambiguous",
                            hypothesis_actions=["run_lioness_coexpression", "run_bonobo"])
    selection = select_by_purpose(decision, purpose("paired", ("individual_change", "which donors change most")),
                                  priors="ruled_out")

    assert selection.recommended is None
    assert selection.reason == "more than one workflow fits the conclusion best"


def test_an_undeclared_candidate_is_unknown_not_worse():
    """CC1: a missing declaration is never a gap, so nothing is compared."""
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=1, reason="tie",
                            capability_match_status="ambiguous",
                            hypothesis_actions=["run_lioness_coexpression", "run_cobra"])
    selection = select_by_purpose(decision, purpose("paired", ("group_difference", "does it change")),
                                  priors="ruled_out")

    assert selection.recommended is None
    assert selection.reason == "a candidate has no declared cell for this conclusion"


def test_mirna_tools_need_a_quoted_mirna_reading():
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=1, reason="tie",
                            capability_match_status="ambiguous",
                            hypothesis_actions=["run_puma", "run_lioness_puma"])
    claim = purpose("paired", ("individual_change", "which patients change most"))

    assert select_by_purpose(decision, claim, priors="stated").recommended is None


@pytest.mark.parametrize(("key", "study"), [
    ("A0-1", purpose("paired")),                                        # no conclusion: control
    ("A4-1", purpose("paired", ("causal", "the treatment itself causes changes"))),
    ("B3-2", purpose("groups", ("prediction", "predicts whether a new patient will respond"))),
    ("A3-1", purpose("paired", ("regulator_change", "which transcription factors change"))),  # exact
])
def test_no_pick_without_a_supported_conclusion_on_a_tie(key, study):
    decision = recorded(key)

    assert purpose_applies(decision, study) is None
    assert select_by_purpose(decision, study, priors="stated") is None


def test_the_prior_reading_is_asked_only_when_a_prior_tool_could_be_picked():
    assert needs_tf_priors(recorded("A1-1"), A1)
    assert not needs_tf_priors(recorded("B1-1"), B1)
    assert not needs_tf_priors(recorded("A0-1"), purpose("paired"))


def test_a_prior_quote_absent_from_the_request_reads_as_unstated():
    proposal = DataFactsProposal(priors="stated", priors_span="we have JASPAR motifs")

    assert verify_data_facts("RNA-seq from 24 patients.", proposal)[0]["priors"] == "unstated"
    assert verify_data_facts("RNA-seq plus we have JASPAR motifs.", proposal)[0]["priors"] == "stated"


# --- routing reads the purpose first ----------------------------------------

def test_the_purpose_is_read_before_routing_and_reaches_the_decision():
    order = []
    purpose_state = {"source": "model", "design": "paired", "design_quote": "", "claims": [["group_difference", A1_QUOTE]]}

    def study(context, state, task, usage, warnings):
        order.append("study_purpose")
        return purpose_state, usage, warnings

    def route(context, state, task, purpose=None):
        order.append("route")
        assert purpose == purpose_state
        return router_invocation._RouterInvocation(
            decision=recorded("A0-1"), routing_state={}, usage=LLMUsage(budget_tokens=1000),
            budget_warnings=[], reason_code="semantic_registry_intent")

    context = SimpleNamespace(task_token_budget=1000, recorder=NullTraceRecorder())
    with patch.object(router_invocation, "invoke_study_purpose", side_effect=study), \
         patch.object(router_invocation, "_route_request", side_effect=route):
        result = router_invocation.invoke_router(context, {}, DECISIONS["A0-1"]["prompt"])

    assert order == ["study_purpose", "route"]
    assert result.routing_state["study_purpose"] == purpose_state


def test_a_pick_skips_nothing_but_the_condition_question_and_is_recorded():
    events = []
    context = SimpleNamespace(recorder=SimpleNamespace(append=lambda run, kind, node, payload: events.append((kind, payload))))
    purpose_state = {"source": "model", "design": "paired", "design_quote": "", "claims": [["group_difference", A1_QUOTE]]}
    usage = LLMUsage(budget_tokens=1000)
    with patch.object(router_invocation, "invoke_data_facts",
                      return_value=({"source": "model", "priors": "stated", "priors_quote": "TF motif"}, usage, [])) as facts:
        decision, _, _, record, data = router_invocation._select_by_purpose(
            context, {}, DECISIONS["A1-1"]["prompt"], recorded("A1-1"), purpose_state, usage, [])

    facts.assert_called_once()
    assert decision.advisory_recommendation.action == "run_lioness_panda"
    assert decision.clarification_question.startswith("Should I use LIONESS-PANDA")
    assert record["recommended"] == "run_lioness_panda" and data["priors"] == "stated"
    assert [kind for kind, _ in events] == ["routing.purpose_selection"]


# --- what the user sees ---------------------------------------------------------

def _reply_and_card(key, study, priors):
    task = DECISIONS[key]["prompt"]
    decision = with_purpose_selection(recorded(key), select_by_purpose(recorded(key), study, priors=priors))
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task, decision=decision.model_dump(), status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=task)],
             "tool_results": [], "evaluation": None,
             "study_purpose": {"source": "model", "design": study.design, "design_quote": "",
                               "claims": [list(c) for c in study.claims]}}
    out = response_module.respond(SimpleNamespace(project_policy=POLICY), state)
    result = {**state, "messages": [HumanMessage(content=task), out["messages"][-1]], "reply_kind": out["reply_kind"]}
    return out["messages"][-1].content, build_reply_card(result, build_next_turn_prompt(result), POLICY, task=task)


def test_the_reply_says_why_the_pick_fits_the_question_without_method_text():
    text, card = _reply_and_card("A1-1", A1, "stated")

    assert text.startswith(f'Based on what you said — "{A1_QUOTE}" — **LIONESS-PANDA** fits better: '
                           "it gives a result for each sample, so the difference you ask about can be tested, "
                           "keeping each individual's samples paired.")
    assert "approach:" not in text and "W_q" not in text
    assert f'For your question ("{A1_QUOTE}")' in text  # every listed workflow, in the question's terms
    option = card.choices.options[0]
    assert (option.label, option.badge) == ("LIONESS-PANDA", "Recommended")
    assert option.description.startswith("Fits what you said: it gives a result for each sample")
    assert {o.label for o in card.choices.options} >= {"PANDA", "OTTER", "GIRAFFE", "PUMA"}


def test_without_a_pick_the_reply_is_the_baseline_reply():
    """Log 378's live A1 decision rendered as is: the purpose reading alone changes nothing."""
    task = DECISIONS["A1-1"]["prompt"]
    decision = recorded("A1-1")
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task, decision=decision.model_dump(), status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=task)],
             "tool_results": [], "evaluation": None,
             "study_purpose": {"source": "model", "design": "paired", "design_quote": "",
                               "claims": [["group_difference", A1_QUOTE]]}}
    text = response_module.respond(SimpleNamespace(project_policy=POLICY), state)["messages"][-1].content

    assert not text.startswith("Based on what you said")
    assert "**LIONESS-PANDA** fits better" not in text
