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
