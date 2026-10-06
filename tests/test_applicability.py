"""Each listed workflow judged against the request's data (plan item 4, Log 380).

The registry says what a workflow needs; the request's side is the data-facts
reading (a model call whose quotes are verified). Where it has read a kind,
no word list may overrule it: Log 373 read "no transcription factor motifs"
as having them, and Log 378 B3-1 asked about priors after "no other data".
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

sys.path[:0] = [str(Path(__file__).parents[1] / "scripts"), str(Path(__file__).parent)]

from netzoo_agent_core.contracts import LLMUsage  # noqa: E402
from netzoo_agent_core.contracts.data_facts import DataFactsProposal  # noqa: E402
from netzoo_agent_core.graph import router_invocation  # noqa: E402
from netzoo_agent_core.graph.data_facts_call import verify_data_facts  # noqa: E402
from netzoo_agent_core.interpretation.applicability import (  # noqa: E402
    assess_applicability, merge_inputs, needs_data_facts,
)
from netzoo_agent_core.reply_cards.method_notes import missing_input_labels  # noqa: E402
from netzoo_agent_core.routing.capability_compatibility import input_availability  # noqa: E402
from test_reply_cards import HEART_FAILURE, _heart_failure_tie, decision, reading, respond_and_card  # noqa: E402

NO_MOTIFS = ("We profiled 72 maize inbred lines by RNA-seq, but no transcription factor motifs or protein "
             "interaction network exist for this species. We want one TF network per line.")
NO_OTHER = ("We have bulk RNA-seq from 60 tumors, 30 responders and 30 non-responders, and no other data. "
            "We want each tumor's regulatory network.")
F3 = ("We have nasal brushing RNA-seq from 40 asthmatic and 40 healthy children. We want to know which "
      "transcription factors change their regulatory activity between the groups.")
DATABASES = ("We have lung RNA-seq from 35 patients plus JASPAR binding-site scans of promoters and the STRING "
             "database for human proteins. We want each patient's TF-gene network.")


def facts(priors, mirna="unstated", priors_quote="", mirna_quote=""):
    return {"source": "model", "priors": priors, "priors_quote": priors_quote,
            "mirna": mirna, "mirna_quote": mirna_quote}


def judged(made, task, reading_):
    listed = [*made.matched_actions, *made.hypothesis_actions, *made.recommended_actions]
    present = set(input_availability(task).present) | {
        v for h in made.outcome_hypotheses for v in h.outcome.input_artifacts if v != "unknown"}
    return made.model_copy(update={
        "data_facts": reading_, "applicability": assess_applicability(listed, merge_inputs(present, reading_), task),
    })


def lioness_panda():
    return decision([reading("regulatory_network", ["expression_matrix"], ["tf"], granularity="sample_specific")],
                    capability_match_status="exact", matched_actions=["run_lioness_panda"],
                    recommended_actions=["run_lioness_panda"])


def giraffe():
    return decision([reading("tf_activity_matrix", ["expression_matrix"], ["tf"], granularity="sample_specific")],
                    capability_match_status="exact", matched_actions=["run_giraffe"], recommended_actions=["run_giraffe"])


def statuses(made):
    return {item.action: item.status for item in made.applicability}


# --- the reading replaces the wording, for the kinds it read ---------------------

def test_a_ruled_out_reading_is_not_overruled_by_the_words_it_contains():
    """Log 373 C: "no transcription factor motifs" matched the motif word list."""
    present = merge_inputs(input_availability(NO_MOTIFS).present, facts("ruled_out"))

    assert "motif_prior" not in present and {"motif_prior", "ppi_prior"} <= present.absent
    assert missing_input_labels("run_lioness_panda", present, NO_MOTIFS) == ["motif prior", "PPI network"]
    # Without the reading, the loose wording rescues both roles, as before.
    assert missing_input_labels("run_lioness_panda", frozenset({"expression_matrix"}), NO_MOTIFS) == []


def test_a_stated_reading_counts_data_the_word_list_misses():
    present = merge_inputs({"expression_matrix"}, facts("stated", priors_quote="JASPAR binding-site scans"))

    assert {"motif_prior", "ppi_prior"} <= present
    assert missing_input_labels("run_lioness_panda", present, DATABASES) == []


@pytest.mark.parametrize(("reading_", "expected"), [
    (facts("stated"), "applicable"),
    (facts("ruled_out"), "not_applicable"),
    (facts("unstated"), "insufficient_information"),
])
def test_each_workflow_gets_a_status_from_the_reading(reading_, expected):
    made = judged(lioness_panda(), NO_OTHER, reading_)

    assert statuses(made) == {"run_lioness_panda": expected}
    basis = made.applicability[0].basis
    assert [(fact.kind, fact.source) for fact in basis] == [("tf_priors", "model")]


def test_mirna_is_judged_separately_from_tf_priors():
    tie = _heart_failure_tie()
    made = judged(tie, HEART_FAILURE, facts("stated", mirna="ruled_out", mirna_quote="we did not profile microRNAs"))

    assert statuses(made) == {"run_lioness_panda": "applicable", "run_lioness_puma": "not_applicable"}


def test_the_reading_is_asked_only_when_a_listed_workflow_needs_unbound_priors_or_mirna():
    assert needs_data_facts(["run_lioness_panda"], bound=())
    assert needs_data_facts(["run_puma"], bound=("motif_file", "ppi_file"))  # still needs miRNA
    assert not needs_data_facts(["run_lioness_panda"], bound=("motif_file", "ppi_file"))
    assert not needs_data_facts(["run_cobra", "run_bonobo", "run_lioness_coexpression"], bound=())


def test_a_reading_whose_quote_is_not_in_the_request_is_unstated():
    proposal = DataFactsProposal(priors="ruled_out", priors_span="does not have them, or that it has only other data",
                                 mirna="ruled_out", mirna_span="")
    entry, rejected = verify_data_facts(NO_OTHER, proposal)

    assert (entry["priors"], entry["mirna"]) == ("unstated", "unstated")
    assert {item["field"] for item in rejected} == {"priors", "mirna"}


# --- what the user sees ----------------------------------------------------------

def _paragraph(text):
    return next((p for p in text.split("\n\n") if p.startswith("**What your data allows.**")), None)


def test_missing_data_with_no_alternative_is_asked_about_not_assumed():
    """Log 379 F3: priors never mentioned, GIRAFFE given as the answer."""
    text, _, card = respond_and_card(F3, judged(giraffe(), F3, facts("unstated")))

    assert _paragraph(text) == (
        "**What your data allows.** Your request names only expression data. GIRAFFE also needs a motif prior "
        "and a PPI network. Do you also have a motif prior and a PPI network?")
    assert card.choices.question == "Do you also have a motif prior and a PPI network?"
    # Nothing is claimed about every registered workflow: that would rest on routing's reading.
    assert "No registered workflow" not in text
    assert card.choices.options[0].description == "Ask what the data you named can give instead"


@pytest.mark.parametrize(("task", "quote"), [
    (NO_OTHER, "no other data"),
    (NO_MOTIFS, "no transcription factor motifs or protein interaction network exist for this species"),
])
def test_ruled_out_data_is_said_with_the_users_words_and_never_asked_about(task, quote):
    text, _, card = respond_and_card(task, judged(lioness_panda(), task, facts("ruled_out", priors_quote=quote)))

    paragraph = _paragraph(text)
    assert f'LIONESS-PANDA needs a motif prior and a PPI network, which you said you do not have ("{quote}").' \
        in paragraph
    assert "Do you also have" not in text
    assert card.choices is None or card.choices.header != "Inputs"
    assert "Needs a motif prior and a PPI network, which you said you do not have." in card.points
    assert not any(point.startswith("Not mentioned") for point in card.points)


def test_stated_data_needs_no_paragraph_and_no_note():
    text, _, card = respond_and_card(DATABASES, judged(lioness_panda(), DATABASES, facts("stated", priors_quote="JASPAR")))

    assert _paragraph(text) is None
    assert not any("Not mentioned" in point for point in card.points)


def test_with_unstated_priors_and_an_alternative_the_reply_is_unchanged():
    """Log 312's Test 2 text and card, now from the reading instead of the wording."""
    before = respond_and_card(HEART_FAILURE, _heart_failure_tie())
    after = respond_and_card(HEART_FAILURE, judged(_heart_failure_tie(), HEART_FAILURE, facts("unstated")))

    assert _paragraph(after[0]) == _paragraph(before[0])
    assert after[2].choices.question == before[2].choices.question


# --- routing asks once, after routing, and only when it can matter ---------------

def _result(made):
    return router_invocation._RouterInvocation(decision=made, routing_state={}, usage=LLMUsage(budget_tokens=1000),
                                               budget_warnings=[], reason_code="semantic_registry_intent")


def test_routing_reads_the_data_facts_and_records_each_workflows_status():
    events = []
    context = SimpleNamespace(recorder=SimpleNamespace(append=lambda run, kind, node, payload: events.append(kind)))
    with patch.object(router_invocation, "invoke_data_facts",
                      return_value=(facts("ruled_out", priors_quote="no other data"), LLMUsage(budget_tokens=1000), [])) as call:
        result = router_invocation._with_applicability(context, {}, NO_OTHER, _result(lioness_panda()))

    call.assert_called_once()
    assert result.decision.data_facts["priors"] == "ruled_out"
    assert statuses(result.decision) == {"run_lioness_panda": "not_applicable"}
    assert result.routing_state["data_facts"]["priors"] == "ruled_out"
    assert events == ["routing.applicability_assessed"]


@pytest.mark.parametrize("task", [
    "Run nothing. Explain LIONESS-PANDA with motif_file=m.tsv ppi_file=p.tsv expression_file=e.tsv.",
])
def test_bound_files_need_no_reading(task):
    with patch.object(router_invocation, "invoke_data_facts") as call:
        result = router_invocation._with_applicability(SimpleNamespace(), {}, task, _result(lioness_panda()))

    call.assert_not_called()
    assert result.decision.data_facts is None


def test_a_failed_reading_changes_nothing():
    with patch.object(router_invocation, "invoke_data_facts", return_value=(None, LLMUsage(budget_tokens=1000), [])):
        result = router_invocation._with_applicability(SimpleNamespace(), {}, NO_OTHER, _result(lioness_panda()))

    assert result.decision.data_facts is None and result.decision.applicability == []


# --- the pick follows the data, not just the input format ------------------------

def test_a_ruled_out_workflow_is_not_presented_as_the_selected_path():
    text, _, card = respond_and_card(NO_OTHER, judged(lioness_panda(), NO_OTHER, facts("ruled_out", priors_quote="no other data")))

    assert text.startswith("**LIONESS-PANDA** fits the result you describe, but it needs a motif prior and a PPI "
                           "network, which you said you do not have.")
    assert "Selected path" not in text
    assert card.headline == "LIONESS-PANDA needs a motif prior and a PPI network, which you said you do not have."


def test_a_workflow_short_of_unstated_data_is_offered_on_that_condition():
    text, _, card = respond_and_card(F3, judged(giraffe(), F3, facts("unstated")))

    assert text.startswith("**GIRAFFE** fits the result you describe if you have a motif prior and a PPI network.")
    assert card.headline == "GIRAFFE fits your goal if you have a motif prior and a PPI network."


def test_stated_data_keeps_the_selected_path():
    text, _, card = respond_and_card(DATABASES, judged(lioness_panda(), DATABASES, facts("stated", priors_quote="JASPAR")))

    assert text.startswith("Selected path: **LIONESS-PANDA**.")
    assert card.headline.startswith("LIONESS-PANDA fits your goal:")


def test_a_recommendation_needing_ruled_out_data_is_dropped():
    from netzoo_agent_core.contracts.outcomes import AdvisoryCondition, AdvisoryRecommendation

    tie = decision([reading("regulatory_network", ["expression_matrix"], ["tf"], granularity="sample_specific")],
                   capability_match_status="ambiguous",
                   hypothesis_actions=["run_lioness_panda", "run_lioness_coexpression"],
                   advisory_recommendation=AdvisoryRecommendation(
                       action="run_lioness_panda",
                       conditions=[AdvisoryCondition(axis="sample_size", value="many", text_span="60 tumors")]),
                   clarification_question="Should I use LIONESS-PANDA, or does another listed option fit your study better?")
    with patch.object(router_invocation, "invoke_data_facts",
                      return_value=(facts("ruled_out", priors_quote="no other data"), LLMUsage(budget_tokens=1000), [])):
        result = router_invocation._with_applicability(
            SimpleNamespace(recorder=SimpleNamespace(append=lambda *a: None)), {}, NO_OTHER, _result(tie))

    assert result.decision.advisory_recommendation is None
    assert result.decision.clarification_question is None
    assert statuses(result.decision)["run_lioness_coexpression"] == "applicable"
