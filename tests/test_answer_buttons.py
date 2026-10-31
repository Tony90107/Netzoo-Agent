"""answer-buttons-2026-10-31: an ASK's single question gets Yes/No or option buttons (plus the own-answer row) when
NETZOO_ANSWER_BUTTONS=on; a clicked answer binds exactly the option it shows; typed answers bind as before; off
changes nothing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.core_decision import CoreDecision, FactQuestion  # noqa: E402
from netzoo_agent_core.engine.answer_buttons import buttons  # noqa: E402
from netzoo_agent_core.engine.task_updates import after_turn, bind_answers  # noqa: E402
from netzoo_agent_core.reply_cards.answer_buttons import ask_choices  # noqa: E402


def _ask(fact):
    return CoreDecision(kind="ASK", basis="needs_fact", facts=[fact], workflows=list(fact.workflows))


CONFIRM = FactQuestion(question="Before I go ahead, could you confirm this about your data? (yes or no)",
                       workflows=["DRAGON"], contract_quote="sample-ID set equality", depends_on="jev:condition")
GROUPS = FactQuestion(question="One group each, or several groups at once?", workflows=["CONDOR"],
                      outcomes={"one_group": ["CONDOR"], "several_groups": []}, depends_on="group_membership")


def _state(core):
    return after_turn(None, {"decision": {"core": core.model_dump(mode="json")}}, "request")


def test_off_shows_nothing_and_binds_as_before(monkeypatch):
    monkeypatch.delenv("NETZOO_ANSWER_BUTTONS", raising=False)
    assert ask_choices(_ask(CONFIRM)) is None
    _state_after, bound, _ = bind_answers(_state(_ask(CONFIRM)), "That's right, no shared tumours.")
    assert bound == []


def test_yes_no_buttons_round_trip(monkeypatch):
    monkeypatch.setenv("NETZOO_ANSWER_BUTTONS", "on")
    choices = ask_choices(_ask(CONFIRM))
    assert [o.label for o in choices.options] == ["Yes", "No"] and choices.allow_other
    for option, value in zip(choices.options, ("yes", "no")):
        _after, bound, _ = bind_answers(_state(_ask(CONFIRM)), option.answer)
        assert [b.value for b in bound] == [value]


def test_option_buttons_round_trip(monkeypatch):
    monkeypatch.setenv("NETZOO_ANSWER_BUTTONS", "on")
    choices = ask_choices(_ask(GROUPS))
    assert len(choices.options) == 2
    state = _state(_ask(GROUPS))
    for option, value in zip(choices.options, ("one_group", "several_groups")):
        _after, bound, _ = bind_answers(state, option.answer)
        assert [b.value for b in bound] == [value]


def test_typed_answers_bind_as_before(monkeypatch):
    monkeypatch.setenv("NETZOO_ANSWER_BUTTONS", "on")
    _after, bound, _ = bind_answers(_state(_ask(CONFIRM)), "Yes, they are different tumours.")
    assert [b.value for b in bound] == ["yes"]
    _after, bound, _ = bind_answers(_state(_ask(CONFIRM)), "Not sure, let me check.")
    assert bound == []


def test_open_question_has_no_buttons(monkeypatch):
    monkeypatch.setenv("NETZOO_ANSWER_BUTTONS", "on")
    open_count = FactQuestion(question="How many samples?", workflows=["LIONESS-PANDA"], depends_on="sample_count")
    assert ask_choices(_ask(open_count)) is None
    assert buttons(_state(_ask(open_count)).pending[0]) == []


def test_two_questions_get_no_buttons(monkeypatch):
    monkeypatch.setenv("NETZOO_ANSWER_BUTTONS", "on")
    core = CoreDecision(kind="ASK", basis="needs_fact", facts=[CONFIRM, GROUPS], workflows=["DRAGON"])
    assert ask_choices(core) is None
