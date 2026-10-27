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
    monkeypatch.setattr(jev_guard_call, "guarded_core", lambda c, r, f: (do("CLARIFY", "jev_goal"), "clarify"))
    jev_guard_call.apply_jev_guard(None, {}, None, core, TASK, done(read("CLARIFY")))
    assert events[-1]["would_have"]["kind"] == "CLARIFY" and events[-1]["mode"] == "shadow"


def test_on_applies_the_guard(monkeypatch, events):
    monkeypatch.setenv("NETZOO_JEV_GUARD", "on")
    monkeypatch.setattr(jev_guard_call, "guarded_core", lambda c, r, f: (do("CLARIFY", "jev_goal"), "clarify"))
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
