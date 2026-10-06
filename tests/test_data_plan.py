"""The turn's data-needs plan (plan item 5, Log 383).

Log 382 traced the reply failures of Logs 379-381 to whether-to-ask being
decided by each renderer under its own preconditions, and to the question's
data needs being inferred from the workflows routing listed. The plan reads
the need from the question, decides once, and every reply shows it.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path[:0] = [str(Path(__file__).parents[1] / "scripts"), str(Path(__file__).parent)]

from netzoo_agent_core.contracts import AIMessage, HumanMessage, LLMUsage  # noqa: E402
from netzoo_agent_core.graph import router_invocation  # noqa: E402
from netzoo_agent_core.interpretation.data_plan import (  # noqa: E402
    build_data_plan, plan_needs, render_plan_block, with_data_plan_reply,
)
from test_reply_cards import decision, reading  # noqa: E402

DATA_SENTENCE = ("We have RNA-seq from 48 airway cultures, plus maps of where transcription factors bind and of which "
                 "proteins physically contact each other.")


def facts(priors="unstated", mirna="unstated", priors_quote="", mirna_quote=""):
    return {"source": "model", "priors": priors, "priors_quote": priors_quote, "mirna": mirna, "mirna_quote": mirna_quote}


def coexpression():
    return decision([reading("coexpression_network", ["expression_matrix"])], capability_match_status="exact",
                    matched_actions=["run_cobra"], recommended_actions=["run_cobra"])


def tf_tie():
    return decision([reading("regulatory_network", ["expression_matrix"], ["tf"])], capability_match_status="ambiguous",
                    hypothesis_actions=["run_panda", "run_otter"])


# --- the need is read from the question, not from the workflows routing listed ----

def test_a_tf_question_needs_the_priors_and_a_coexpression_question_does_not():
    assert plan_needs([("regulator_change", "Which transcription factors steer the program?")], tf_tie()) == (
        True, "claims", ("tf_priors",))
    # Routing listed TF workflows; the question asks about co-expression (Log 382: R2).
    assert plan_needs([("group_difference", "Which genes are co-expressed?")], tf_tie()) == (True, "claims", ())


def test_a_data_sentence_naming_tfs_is_not_a_tf_question():
    task = f"{DATA_SENTENCE} How does co-expression among matrix genes differ between groups?"
    assert plan_needs((), coexpression(), task) == (True, "question", ())


def test_a_mirna_question_needs_mirna_and_the_priors():
    assert plan_needs([("regulator_change", "Are microRNAs part of the regulation?")], tf_tie())[2] == (
        "tf_priors", "mirna")


def test_a_question_no_workflow_answers_needs_nothing():
    assert plan_needs([("prediction", "Could these profiles predict relapse?")], tf_tie()) == (False, "unanswerable", ())


def test_without_a_quoted_question_the_requests_own_question_decides_then_the_routing_reading():
    assert plan_needs((), coexpression(), "We have RNA-seq. Which transcription factors drive the genes?")[2] == (
        "tf_priors",)
    assert plan_needs((), tf_tie(), "We have RNA-seq from 30 livers.") == (True, "reading", ("tf_priors",))
    assert plan_needs((), decision([]), "We have RNA-seq.") == (True, "none", ())


def test_a_quoted_question_from_someone_else_is_not_the_users():
    task = 'A reviewer asked "Did you use a TF motif prior?" Which genes are co-expressed in our samples?'
    assert plan_needs((), coexpression(), task)[2] == ()


# --- what the plan does with each need ---------------------------------------------

def test_each_need_gets_one_action_from_the_reading():
    claims = [("regulator_change", "Which transcription factors steer the program?")]
    assert build_data_plan(claims, tf_tie(), facts("unstated"), set()).asks() == ["tf_priors"]
    plan = build_data_plan(claims, tf_tie(), facts("ruled_out", priors_quote="no binding-site data"), set())
    assert plan.asks() == [] and plan.ruled_out()[0].quote == "no binding-site data"
    assert build_data_plan(claims, tf_tie(), facts("stated", priors_quote="JASPAR"), set()).asks() == []


def test_without_a_reading_the_words_decide_and_bound_files_count_as_stated():
    claims = [("regulator_change", "Which transcription factors steer the program?")]
    assert build_data_plan(claims, tf_tie(), None, {"motif_prior", "ppi_prior"}).needs[0].source == "words"
    assert build_data_plan(claims, tf_tie(), None, set()).asks() == ["tf_priors"]
    bound = build_data_plan(claims, tf_tie(), None, set(), bound={"motif_file", "ppi_file"})
    assert bound.needs[0].source == "binding" and bound.asks() == []


def test_mirna_is_not_asked_once_the_priors_are_ruled_out():
    claims = [("regulator_change", "Are microRNAs part of the regulation?")]
    plan = build_data_plan(claims, tf_tie(), facts("ruled_out", priors_quote="no binding-site data"), set())
    assert plan.asks() == [] and [need.kind for need in plan.ruled_out()] == ["tf_priors"]


# --- every reply shows the plan ------------------------------------------------------

def _plan(state="unstated", quote=""):
    return build_data_plan([("regulator_change", "Which transcription factors steer the program?")], tf_tie(),
                           facts(state, priors_quote=quote), set())


def test_a_reply_missing_the_plans_question_gets_it_named():
    block = render_plan_block(_plan(), "PANDA fits.")
    assert block.endswith("Do you have a motif prior and a PPI network?")


def test_a_reply_that_already_asks_or_says_it_gets_nothing():
    assert render_plan_block(_plan(), "PANDA fits. Do you also have a motif prior and a PPI network?") is None
    said = "PANDA needs a motif prior and a PPI network, which you said you do not have."
    assert render_plan_block(_plan("ruled_out", "no binding-site data"), said) is None


def _respond(kind, made, text="PANDA and OTTER fit.\n\nNo files were inspected and no analysis ran."):
    state = {"decision": made.model_dump(), "messages": [HumanMessage(content="task")]}
    result = {"messages": [AIMessage(content=text)], "reply_kind": kind}
    out = with_data_plan_reply(result, state, lambda new, k: {"messages": [AIMessage(content=new)], "reply_kind": k})
    return str(out["messages"][-1].content)


def test_the_plan_is_shown_whichever_guidance_renderer_answered():
    made = tf_tie().model_copy(update={"data_plan": _plan()})
    for kind in ("verified_guidance", "hypothesis_routes", "outcome_clarification", "unresolved"):
        text = _respond(kind, made)
        assert "Do you have a motif prior and a PPI network?" in text
        assert text.endswith("No files were inspected and no analysis ran.")
    # Not an execution report, and nothing without a plan.
    assert "Do you have" not in _respond("execution", made)
    assert "Do you have" not in _respond("verified_guidance", tf_tie())


def test_routing_builds_the_plan_and_reads_the_data_for_a_tf_question_routing_did_not_list():
    # Log 382 C: routing listed only COBRA; the question is about TFs.
    task = "We ran RNA-seq on 30 sheep. Which transcription factors regulate different targets on each diet?"
    result = router_invocation._RouterInvocation(
        decision=coexpression(), routing_state={"study_purpose": {"claims": [
            ["regulator_change", "Which transcription factors regulate different targets on each diet?"]]}},
        usage=LLMUsage(budget_tokens=1000), budget_warnings=[], reason_code="semantic_registry_intent")
    events = []
    context = SimpleNamespace(recorder=SimpleNamespace(append=lambda run, kind, node, payload: events.append(kind)))
    with patch.object(router_invocation, "invoke_data_facts",
                      return_value=(facts("unstated"), LLMUsage(budget_tokens=1000), [])) as call:
        made = router_invocation._with_applicability(context, {}, task, result).decision

    call.assert_called_once()
    assert made.data_plan.asks() == ["tf_priors"] and events == ["routing.data_plan_built"]
