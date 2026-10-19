"""Closed-menu phase 1b variant: the focused intent probe (the user's decision, 2026-10-18).

No model calls: which intents are probed (only those that change the call), the closed questions, and `merge_intent`
-- agreement keeps, disagreement or missing words make the intent unclear (asked), an explicit verified value fills
an intent the first read did not state.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.menu_reading import MenuReading, Said, Wanted  # noqa: E402
from netzoo_agent_core.graph.menu_reading_call import read_intent  # noqa: E402
from netzoo_agent_core.interpretation.menu_decision import PROBED_INTENTS, decide_menu  # noqa: E402
from netzoo_agent_core.interpretation.menu_intent import (  # noqa: E402
    CHOICE, NOT_SAID, intent_model, intent_questions, intent_text, merge_intent,
)

TASK = "We want one TF-gene regulatory network for each of our 40 patients; expression, motifs and PPI are ready."
DATA = ["expression", "motif_prior", "ppi"]


def said(value: str, quote: str) -> Said:
    return Said(status="stated", value=value, basis="explicit", quotes=[quote])


def reading(**fields) -> MenuReading:
    wanted = Wanted(quote="one TF-gene regulatory network for each of our 40 patients",
                    artifact=fields.pop("artifact", said("regulatory_network", "TF-gene regulatory network")), **fields)
    return MenuReading(wanted=[wanted], data=DATA)


def answers(*pairs) -> dict:
    return {f"q{n}": {"quote": quote, "answer": value} for n, (value, quote) in enumerate(pairs, 1)}


def probe(first: MenuReading, *pairs):
    questions = intent_questions(first, TASK)
    return questions, merge_intent(first, questions, answers(*pairs), TASK)


def test_only_intents_that_change_the_call_are_probed():
    questions = intent_questions(reading(), TASK)
    # regulators decide too: TF only (PANDA) or TF and miRNA (PUMA) leave different options
    assert [(q.item, q.dimension) for q in questions] == [(0, "artifact"), (0, "granularity"), (0, "regulators")]
    assert all(q.dimension in PROBED_INTENTS for q in questions)
    unsure = reading(granularity=Said(status="unsure", values=["per_group", "per_sample"], quotes=["?"]))
    assert "granularity" not in [q.dimension for q in intent_questions(unsure, TASK)]  # asked anyway, never probed
    run = MenuReading(wanted=[Wanted(quote="Run PANDA on expr.tsv")], data=DATA)
    assert [q.dimension for q in intent_questions(run, "Run PANDA on expr.tsv")] == ["artifact"]


def test_questions_offer_the_menu_values_and_not_said():
    questions = intent_questions(reading(), TASK)
    text = intent_text(TASK, questions)
    assert "- per_sample: A separate result for each sample" in text and f"- {NOT_SAID}: " in text
    assert f"- {CHOICE}: " in text
    schema = intent_model(tuple((q.dimension, q.values) for q in questions)).model_json_schema()
    first = schema["$defs"]["IntentAnswer1"]
    assert first["required"] == ["quote", "answer"] and NOT_SAID in first["properties"]["answer"]["enum"]


def test_agreement_keeps_the_first_reading():
    first = reading(granularity=said("per_sample", "for each of our 40 patients"))
    questions, (merged, report) = probe(first, ("regulatory_network", "TF-gene regulatory network"),
                                        ("per_sample", "for each of our 40 patients"), (NOT_SAID, ""))
    assert [q.dimension for q in questions] == ["artifact", "granularity", "regulators"]  # per sample: PANDA or PUMA
    assert merged == first
    assert [line.split(":")[0] for line in report.filled] == ["agree", "agree", "kept not stated"]


def test_disagreement_makes_the_intent_unclear_and_it_is_asked():
    first = reading(granularity=said("whole_cohort", "one TF-gene regulatory network"))
    _q, (merged, report) = probe(first, ("regulatory_network", "TF-gene regulatory network"),
                                 ("per_sample", "for each of our 40 patients"))
    granularity = merged.wanted[0].granularity
    assert granularity.status == "conflicting" and granularity.values == ["whole_cohort", "per_sample"]
    decision = decide_menu(merged, TASK)
    assert decision.kind == "ASK" and decision.questions[0].dimension == "granularity"
    assert any(line.startswith("unclear") for line in report.filled)


def test_not_said_or_unverified_words_against_a_stated_value_is_unclear():
    first = reading(granularity=said("per_sample", "for each of our 40 patients"))
    _q, (merged, _r) = probe(first, ("regulatory_network", "TF-gene regulatory network"), (NOT_SAID, ""))
    assert merged.wanted[0].granularity.status == "conflicting"
    assert set(merged.wanted[0].granularity.values) == {"whole_cohort", "per_group", "per_sample"}
    assert decide_menu(merged, TASK).kind == "ASK"
    _q, (merged, _r) = probe(first, ("tf_activity", "TF activity per patient"), ("per_sample", "for each patient"))
    assert merged.wanted[0].artifact.status == "unsure" and merged.wanted[0].artifact.values == []
    decision = decide_menu(merged, TASK)
    assert decision.kind == "ASK" and decision.questions[0].dimension in ("artifact", "artifact_group")  # asked


def test_a_verified_value_fills_an_intent_the_first_read_did_not_state():
    first = reading()
    _q, (merged, report) = probe(first, ("regulatory_network", "TF-gene regulatory network"),
                                 ("per_sample", "for each of our 40 patients"))
    assert merged.wanted[0].granularity == Said(status="stated", value="per_sample", basis="explicit",
                                                quotes=["for each of our 40 patients"])
    assert decide_menu(merged, TASK).workflows == ["LIONESS-PANDA"]
    _q, (kept, _r) = probe(first, ("regulatory_network", "TF-gene regulatory network"),
                           ("per_sample", "one network per donor"))  # words not in the request
    assert kept == first


def test_a_result_the_request_left_unnamed_is_filled_only_by_verified_words():
    task = "Can you help with our 40 patients? We want TF activity per patient."
    first = MenuReading(wanted=[Wanted(quote="Can you help with our 40 patients?", form="question_to_us")],
                        data=DATA)
    questions = intent_questions(first, task)
    assert questions[0].item == 1 and questions[0].dimension == "artifact"
    merged, _ = merge_intent(first, questions, answers(("tf_activity", "TF activity per patient")), task)
    assert merged.wanted[1].artifact.value == "tf_activity" and merged.wanted[1].form == "deliverable"
    unchanged, _ = merge_intent(first, questions, answers((NOT_SAID, "")), task)
    assert unchanged == first


def test_a_choice_between_workflows_is_asked_as_the_goal():
    task = "Should I be using COBRA or CONDOR on our lupus cohort?"
    first = MenuReading(wanted=[Wanted(quote=task, artifact=said("communities", "CONDOR"))])
    questions = intent_questions(first, task)
    merged, _ = merge_intent(first, questions, answers((CHOICE, "COBRA or CONDOR")), task)
    assert merged.wanted[0].method_choice == ["COBRA or CONDOR"] and decide_menu(merged, task).kind == "CLARIFY"


def test_no_call_without_a_deciding_intent_and_a_failed_call_keeps_the_reading():
    class Broken:
        def with_structured_output(self, *args, **kwargs):
            raise RuntimeError("provider down")

    first = reading()
    read, questions = read_intent(TASK, first, Broken())
    assert questions and read.reading == first and "provider down" in read.error
    assert read_intent(TASK, MenuReading(status="failed"), Broken()) == (None, [])
