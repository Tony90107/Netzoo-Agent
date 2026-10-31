"""clarify-menu-2026-11-01: every capability-sheet produce entry is in exactly one result family; at most eight
families; a CLARIFY card shows them all as buttons (with the own-answer row) when NETZOO_CLARIFY_MENU=on, and nothing
otherwise."""

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.capability_sheet import sheet_entries  # noqa: E402
from netzoo_agent_core.contracts.core_decision import ClarifyNeed, CoreDecision  # noqa: E402
from netzoo_agent_core.capability_sheet import result_families  # noqa: E402
from netzoo_agent_core.interpretation.result_families import families  # noqa: E402
from netzoo_agent_core.reply_cards.answer_buttons import family_choices  # noqa: E402
from netzoo_agent_core.reply_cards.contracts import MAX_OPTIONS  # noqa: E402

CLARIFY = CoreDecision(kind="CLARIFY", basis="goal_unclear", clarify=ClarifyNeed(question="Which result?"))


def test_every_produce_entry_in_exactly_one_family():
    produced = {e.id for e in sheet_entries().values() if e.kind == "produces"}
    listed = Counter(entry for item in families() for entry in item["entries"])
    assert set(listed) == produced and set(listed.values()) == {1}
    assert len(result_families()) <= MAX_OPTIONS and all(item["entries"] for item in families())
    workflows = {w for item in families() for w in item["workflows"]}
    assert workflows == {e.workflow for e in sheet_entries().values() if e.kind == "produces"}


def test_card(monkeypatch):
    monkeypatch.delenv("NETZOO_CLARIFY_MENU", raising=False)
    assert family_choices(CLARIFY) is None
    monkeypatch.setenv("NETZOO_CLARIFY_MENU", "on")
    choices = family_choices(CLARIFY)
    assert len(choices.options) == len(result_families()) and choices.allow_other
    assert choices.options[-1].answer == "I want patient subtypes from somatic mutations."
    assert family_choices(CoreDecision(kind="DO", basis="results_given", workflows=["PANDA"])) is None
