"""The Jev guard (jev-shadow-2026-10-27/PLAN-FRESH.md): off by default, only turns an action into a question."""

from __future__ import annotations

import sys
from concurrent.futures import Future
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from netzoo_agent_core.contracts.core_decision import ClarifyNeed, CoreDecision  # noqa: E402
from netzoo_agent_core.graph import jev_guard_call  # noqa: E402
from netzoo_agent_core.interpretation.ask_facts import ask_reply  # noqa: E402

TASK = ("Run PANDA on expr.tsv with motif.tsv and ppi.tsv. I can't remember whether expr.tsv is the filtered "
        "export or the raw counts. Save it to out.tsv.")


def do(kind="DO", basis="run"):
    return CoreDecision(kind=kind, basis=basis, workflows=["PANDA"])


def read(kind, confidence=0.9, **extra):
    return {"kind": kind, "confidence": confidence, **extra}


def clarify():
    return ClarifyNeed(question="Which result?")


def done(value):
    future = Future()
    future.set_result(value)
    return future


def failed(exc):
    future = Future()
    future.set_exception(exc)
    return future


@pytest.fixture
def events(monkeypatch):
    seen = []
    monkeypatch.setattr(jev_guard_call, "record_event", lambda *a: seen.append(a[4]))
    return seen


def test_the_guard_is_off_by_default(monkeypatch, events):
    monkeypatch.delenv("NETZOO_JEV_GUARD", raising=False)
    assert jev_guard_call.start_jev(TASK) is None
    core = do()
    assert jev_guard_call.apply_jev_guard(None, {}, None, core, TASK, done(read("ASK"))) is core
    assert events == []


@pytest.mark.parametrize("kind", ["DO", "DECLINE"])
def test_jev_never_makes_an_action(kind):
    for system in ("ASK", "CLARIFY", "UNCHECKED"):
        core = do(system, "fact_agent")
        assert jev_guard_call.guarded_core(core, read(kind, 1.0), clarify)[0] is core
    core = do("DO" if kind == "DECLINE" else "DECLINE")
    assert jev_guard_call.guarded_core(core, read(kind, 1.0), clarify)[0] is core


def test_a_question_from_the_system_is_never_changed():
    core = do("ASK", "fact_agent")
    assert jev_guard_call.guarded_core(core, read("CLARIFY"), clarify)[0] is core


def test_an_unsure_jev_changes_nothing():
    core = do()
    after, action = jev_guard_call.guarded_core(core, read("CLARIFY", 0.69), clarify)
    assert after is core and action == "agrees_or_unsure"


def test_a_confident_clarify_turns_an_action_into_the_clarify_view():
    after, action = jev_guard_call.guarded_core(do("DECLINE", "full_gap"), read("CLARIFY"), clarify)
    assert (after.kind, after.basis, action) == ("CLARIFY", "jev_goal", "clarify")
    assert after.clarify.question == "Which result?" and after.workflows == []
    assert after.evidence["jev_guard"]["kind_before"] == "DECLINE"


def test_a_clarify_view_that_cannot_be_built_leaves_the_call():
    core = do()
    after, action = jev_guard_call.guarded_core(core, read("CLARIFY"), lambda: 1 / 0)
    assert after is core and action == "clarify_failed"


def test_an_ask_quotes_the_users_own_sentence_and_claims_no_outcome():
    sentence = jev_guard_call.request_sentences(TASK)[1]
    after, action = jev_guard_call.guarded_core(
        do(), read("ASK", sentence=sentence, sentence_confidence=0.8, about="which_file"), clarify)
    assert (after.kind, after.basis, action) == ("ASK", "jev_fact", "ask")
    fact = after.facts[0]
    assert fact.user_quote == sentence and fact.user_quote in TASK
    assert fact.contract_quote == "" and fact.outcomes == {} and not fact.if_yes and not fact.if_no
    reply = ask_reply(after)
    assert sentence.rstrip(". ") in reply and "Which of the files do you have?" in reply


@pytest.mark.parametrize("extra", [{}, {"sentence": None, "sentence_confidence": 0.9},
                                   {"sentence": "x", "sentence_confidence": 0.5}])
def test_an_ask_without_a_confident_sentence_leaves_the_call(extra):
    core = do()
    after, action = jev_guard_call.guarded_core(core, read("ASK", **extra), clarify)
    assert after is core and action == "no_sentence"


def test_sentences_are_verbatim():
    assert all(part in TASK for part in jev_guard_call.request_sentences(TASK))
    assert len(jev_guard_call.request_sentences(TASK)) == 3


def test_shadow_records_and_keeps_the_call(monkeypatch, events):
    monkeypatch.setenv("NETZOO_JEV_GUARD", "shadow")
    core = do()
    after = jev_guard_call.apply_jev_guard(None, {}, None, core, TASK, done(read("CLARIFY")))
    assert after is core
    monkeypatch.setattr(jev_guard_call, "guarded_core", lambda c, r, f, a=(): (do("CLARIFY", "jev_goal"), "clarify"))
    jev_guard_call.apply_jev_guard(None, {}, None, core, TASK, done(read("CLARIFY")))
    assert events[-1]["would_have"]["kind"] == "CLARIFY" and events[-1]["mode"] == "shadow"


def test_on_applies_the_guard(monkeypatch, events):
    monkeypatch.setenv("NETZOO_JEV_GUARD", "on")
    monkeypatch.setattr(jev_guard_call, "guarded_core", lambda c, r, f, a=(): (do("CLARIFY", "jev_goal"), "clarify"))
    assert jev_guard_call.apply_jev_guard(None, {}, None, do(), TASK, done(read("CLARIFY"))).kind == "CLARIFY"


@pytest.mark.parametrize("mode", ["shadow", "on"])
def test_a_failed_jev_call_leaves_the_call_and_says_so(monkeypatch, events, mode):
    monkeypatch.setenv("NETZOO_JEV_GUARD", mode)
    core = do()
    assert jev_guard_call.apply_jev_guard(None, {}, None, core, TASK, failed(TimeoutError())) is core
    assert events[-1]["status"] == "not_run:TimeoutError"


def test_no_key_fails_inside_the_future(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        jev_guard_call._read(TASK)


def test_the_registry_lists_every_workflow():
    text = jev_guard_call.registry_text()
    assert sum(line.startswith("- ") for line in text.splitlines()) == 13 and "LIONESS-DRAGON" in text


def test_an_unreachable_jev_fails_inside_the_future(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "x")
    monkeypatch.setenv("NETZOO_JEV_URL", "http://127.0.0.1:9/decisions")
    with pytest.raises(OSError):
        jev_guard_call._read(TASK)


def test_a_sentence_already_asked_in_the_task_is_not_asked_again():
    sentence = jev_guard_call.request_sentences(TASK)[1]
    state = {"pending": [{"what": "jev:which_file", "user_quote": sentence}], "facts": []}
    core = do()
    ask = read("ASK", sentence=sentence, sentence_confidence=0.9, about="which_file")
    after, action = jev_guard_call.guarded_core(core, ask, clarify, jev_guard_call.asked_sentences(state))
    assert after is core and action == "already_asked"
    other = {"pending": [{"what": "dimension:count", "user_quote": sentence}]}  # not Jev's question: still asked
    assert jev_guard_call.guarded_core(core, ask, clarify, jev_guard_call.asked_sentences(other))[1] == "ask"
    assert jev_guard_call.asked_sentences(None) == set()


# ANSWERS.md: the contract line a Jev question quotes, and the user's answer read against it.

def _question(contract="An aggregate COBRA adjusted co-expression artifact is not a direct LIONESS handoff"):
    return {"what": "jev:data_property", "status": "asked", "question": "Before I go ahead ...",
            "user_quote": "I can't remember whether it is the raw matrix or the COBRA matrix.",
            "workflows": ["LIONESS-PANDA"], "labels": {"contract": contract}}


def test_contract_lines_are_verbatim_contract_text():
    lines = jev_guard_call.contract_lines(("LIONESS-PANDA",))
    text = " ".join((jev_guard_call.WORKFLOWS / "lioness-panda.yaml").read_text().split())
    assert lines and all(name == "LIONESS-PANDA" and " ".join(line.split()) in text for name, line in lines)


def test_a_failed_answer_declines_with_both_verbatim_quotes_and_says_nothing_of_other_workflows():
    from netzoo_agent_core.interpretation.core_views import decline_reply

    answer = "It's the COBRA adjusted co-expression matrix."
    after, action = jev_guard_call.answered_core(do(), _question(), answer, {"answer": "fails", "confidence": 0.9})
    assert (after.kind, after.basis, action) == ("DECLINE", "jev_answer", "declined")
    reply = decline_reply(after, "options line")
    assert answer.rstrip(".") in reply and "not a direct LIONESS handoff" in reply
    assert "No registered workflow" not in reply and "options line" not in reply


@pytest.mark.parametrize("judged", [{"answer": "meets", "confidence": 1.0}, {"answer": "unclear", "confidence": 1.0},
                                    {"answer": "fails", "confidence": 0.69}, {"answer": "not_run:X", "confidence": 0}])
def test_anything_but_a_confident_fail_leaves_the_call(judged):
    core = do()
    assert jev_guard_call.answered_core(core, _question(), "yes", judged)[0] is core


def test_only_a_do_is_declined_by_an_answer():
    for kind in ("ASK", "CLARIFY", "DECLINE", "UNCHECKED"):
        core = do(kind, "fact_agent")
        assert jev_guard_call.answered_core(core, _question(), "no", {"answer": "fails", "confidence": 1})[0] is core


def test_the_waiting_question_is_found_only_with_its_line():
    assert jev_guard_call.asked_contract_question({"pending": [_question()]})["what"] == "jev:data_property"
    assert jev_guard_call.asked_contract_question({"pending": [_question(contract="")]}) is None
    assert jev_guard_call.asked_contract_question({"pending": [{**_question(), "what": "dimension:x"}]}) is None
    assert jev_guard_call.asked_contract_question(None) is None


def test_the_pending_question_keeps_the_contract_line():
    from netzoo_agent_core.engine.task_updates import _pending

    core = {"kind": "ASK", "facts": [{"question": "q", "user_quote": "u", "workflows": ["PANDA"],
                                      "depends_on": "jev:input_exists", "contract_quote": "PANDA consumes ..."}]}
    assert _pending(core)[0].labels == {"contract": "PANDA consumes ..."}
    core["facts"][0]["depends_on"] = "jev:count"
    core["facts"][0]["contract_quote"] = ""
    assert _pending(core)[0].labels == {}


# LINKS.md step 4: a CLARIFY whose request names one workflow's result becomes a confirm of that result.

def test_a_confident_result_pick_turns_a_clarify_into_a_confirm_in_contract_words():
    from netzoo_agent_core.interpretation.ask_facts import ask_reply

    core = do("CLARIFY", "goal_unclear")
    after, action = jev_guard_call.linked_core(core, {"result": "PUMA", "confidence": 0.85})
    assert (after.kind, after.basis, action) == ("ASK", "jev_link", "link")
    text = (jev_guard_call.WORKFLOWS / "puma.yaml").read_text()
    assert after.facts[0].contract_quote in text and "Did you mean PUMA's result?" in ask_reply(after)


@pytest.mark.parametrize("pick", [{"result": "not_named", "confidence": 1.0}, {"result": "none_registered", "confidence": 1},
                                  {"result": "PUMA", "confidence": 0.69}, {"result": "not_run:X", "confidence": 0}])
def test_no_confident_workflow_pick_leaves_the_clarify(pick):
    core = do("CLARIFY", "goal_unclear")
    assert jev_guard_call.linked_core(core, pick)[0] is core


def test_only_a_clarify_is_linked_and_only_once_per_task():
    for kind in ("DO", "ASK", "DECLINE"):
        core = do(kind, "x")
        assert jev_guard_call.linked_core(core, {"result": "PUMA", "confidence": 1})[0] is core
    assert jev_guard_call.linked_already({"pending": [{"what": "jev_link:PUMA"}]})
    assert not jev_guard_call.linked_already({"pending": [{"what": "jev:count"}]}) and not jev_guard_call.linked_already(None)


def test_a_link_question_is_never_judged_as_an_answer_to_a_contract_line():
    from netzoo_agent_core.engine.task_updates import _pending

    core = {"kind": "ASK", "facts": [{"question": "Did you mean PUMA's result?", "workflows": ["PUMA"],
                                      "depends_on": "jev_link:PUMA", "contract_quote": "Infer ..."}]}
    pending = _pending(core)[0].model_dump()
    assert pending["labels"] == {} and jev_guard_call.asked_contract_question({"pending": [pending]}) is None


def test_the_result_menu_is_generated_for_every_workflow():
    menu = jev_guard_call.result_menu()
    assert len(menu) == 15 and set(jev_guard_call.RESULT_NONE) <= set(menu) and "Result: " in menu["DRAGON"]
