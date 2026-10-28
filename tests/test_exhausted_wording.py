"""exhausted-wording-2026-10-28: an exhausted ASK says what is still missing and does not ask it again (j5 W18 t3)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.core_decision import CoreDecision, FactQuestion  # noqa: E402
from netzoo_agent_core.interpretation.ask_facts import ask_reply  # noqa: E402
from netzoo_agent_core.interpretation.task_answers import exhausted_body  # noqa: E402

CORE = CoreDecision(kind="ASK", basis="fact_agent", workflows=["OTTER"], facts=[FactQuestion(
    question="Were the libraries sequenced on one lane?", workflows=["OTTER"],
    user_quote="I'm not sure whether the libraries were sequenced on one lane or two.",
    contract_quote="OTTER consumes an OTTER seed/prior TF-by-gene edge list W.")])


def test_an_exhausted_ask_lists_what_is_missing_without_asking():
    body = exhausted_body(ask_reply(CORE))
    assert "please tell me" not in body and "before you answer" not in body
    assert body.startswith("Still missing:\n- Were the libraries sequenced on one lane?")
    assert "You wrote: \"I'm not sure whether the libraries were sequenced on one lane or two\"." in body
    assert "No workflow has been selected." in body


def test_text_without_the_asking_phrases_is_unchanged():
    text = "I can't tell yet which result you want, so I have not chosen a workflow."
    assert exhausted_body(text) == text


def test_an_exhausted_data_confirm_is_listed_as_missing_not_asked_again():
    """j4 S35: the guard's re-asked data confirm ("I need a yes or no to go on: ... (yes or no)") reaching the round
    cap must not ask for a yes or no under "I will not ask again"."""
    from netzoo_agent_core.graph import jev_guard_call
    from netzoo_agent_core.interpretation.ask_facts import CONFIRM_PLACED, CONFIRM_UNPLACED, REASK, YES_OR_NO

    typed = {"unplaced": "An aggregate COBRA adjusted co-expression artifact is not a direct LIONESS handoff",
             "workflow": "LIONESS-PANDA", "data": ["coexpression_network", 1.0]}
    do = CoreDecision(kind="DO", basis="run", workflows=["LIONESS-PANDA"])
    asked, _ = jev_guard_call.conditioned_core(do, typed)
    pending = {**asked.facts[0].model_dump(), "what": "jev:condition", "status": "asked",
               "labels": {"contract": typed["unplaced"], "workflow": "LIONESS-PANDA"}}
    reasked, _ = jev_guard_call.confirmed_core(do, pending, "I checked.", {"answer": "unread", "confidence": 0.0})
    assert reasked.facts[0].question.startswith(REASK)
    body = exhausted_body(ask_reply(reasked))
    for asking in (REASK.strip(), YES_OR_NO.strip(), CONFIRM_UNPLACED.strip(), "please tell me", "before you answer"):
        assert asking not in body
    assert body.startswith("Still missing:\n- A confirmation: is the data you will use a gene-by-gene co-expression")
    assert "LIONESS-PANDA's contract" in body and "No workflow has been selected." in body
    placed = exhausted_body(f"- {CONFIRM_PLACED}{YES_OR_NO}")
    assert placed == "- A confirmation about your data."
