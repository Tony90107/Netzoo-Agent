"""couldn't-match-2026-11-18: labelled general background beside a refusal with no verified reason."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from netzoo_agent_core.contracts.core_decision import CoreDecision, DeclinedPart  # noqa: E402
from netzoo_agent_core.graph import general_background_call as call  # noqa: E402
from netzoo_agent_core.interpretation import general_background as gb  # noqa: E402
from netzoo_agent_core.interpretation.core_views import _with_background  # noqa: E402
from netzoo_agent_core.interpretation.reason_layers import UNMATCHED  # noqa: E402

QUOTE = "I need a directed network that shows which genes cause changes in which other genes."


def gap(basis="full_gap", line=None):
    return CoreDecision(kind="DECLINE", basis=basis,
                        declined=[DeclinedPart(quote=QUOTE, line=line if line is not None else f'"{QUOTE}" -- {UNMATCHED}')])


def test_only_a_refusal_without_a_verified_reason_wants_background():
    assert gb.wanted(gap()) and gb.wanted(gap("results_given"))
    assert not gb.wanted(gap("jev_answer", 'You answered "Yes". PANDA\'s contract lists x. So PANDA cannot do this.'))
    assert not gb.wanted(gap("contract_veto", "LIONESS-PANDA cannot, because its contract says ..."))
    assert not gb.wanted(CoreDecision(kind="DO", basis="run", workflows=["PANDA"]))
    assert not gb.wanted(None)


def test_sentences_naming_netzoo_or_a_workflow_are_dropped_and_at_most_four_kept():
    text = ("Causal gene networks are usually inferred from perturbation data such as knockouts or CRISPR screens. "
            "With observational expression alone, Bayesian networks or structural equation models are common. "
            "PANDA does this for TF networks. NetZoo cannot do it. LIONESS gives one network per sample. "
            "Time-series data help orient edges. Instrumental variables such as eQTLs are another route. "
            "A fifth plain sentence.")
    kept, dropped = gb.kept_sentences(text)
    assert "PANDA" not in kept and "NetZoo" not in kept and "LIONESS" not in kept
    assert kept.count(".") == 4 and len(dropped) == 4
    assert gb.kept_sentences("panda and sponge are names here.")[0] == ""  # case-insensitive


def test_the_paragraph_sits_under_its_label_before_the_closing_line():
    reply = "What I understood ...\n\nI couldn't match this ...\n\nNo files were inspected and no analysis ran."
    out = gb.with_background(reply, "Some background.")
    assert out.endswith(f"{gb.LABEL}\nSome background.\n\nNo files were inspected and no analysis ran.")
    assert gb.with_background(reply, "") == reply


def test_the_view_prints_only_a_recorded_background():
    def reply(content, kind):
        return {"messages": [type("M", (), {"content": content})()], "reply_kind": kind}

    plain = reply("Gap.\n\nNo files were inspected and no analysis ran.", "capability_check_gap")
    assert _with_background(plain, gap(), reply) is plain
    core = gap().model_copy(update={"evidence": {"general_background": {"text": "Background."}}})
    out = _with_background(plain, core, reply)
    assert gb.LABEL in out["messages"][-1].content and out["reply_kind"] == "capability_check_gap"


class _Usage:
    def model_dump(self):
        return {}


class _FakeLLM:
    def __init__(self, payload):
        self.payload, self.seen = payload, []

    def with_structured_output(self, *args, **kwargs):
        return self

    def invoke(self, messages):
        self.seen.append(messages)
        return {"parsed": self.payload, "raw": None}


@pytest.fixture
def wired(monkeypatch):
    events = []
    monkeypatch.setenv("NETZOO_GENERAL_BACKGROUND", "on")
    monkeypatch.setattr(call, "record_event", lambda *a: events.append(a[4]))
    monkeypatch.setattr(call, "preflight_budget", lambda *a, **k: (type("B", (), {"status": "ok"})(), []))
    monkeypatch.setattr(call, "with_reading_allowance", lambda *a: type("R", (), {"task_token_budget": 1})())
    monkeypatch.setattr(call, "spent", lambda usage: False)
    monkeypatch.setattr(call, "check_output_reserve", lambda *a: 100)
    monkeypatch.setattr(call, "append_llm_usage", lambda usage, **k: usage)
    monkeypatch.setattr(call, "semantic_payload", lambda response: (response["parsed"], None))
    context = type("C", (), {"price_catalog": None})()
    return events, context


def test_the_call_records_kept_sentences_and_never_changes_the_call(monkeypatch, wired):
    events, context = wired
    llm = _FakeLLM({"answerable": True, "background": "Causal networks need perturbations. PANDA is one tool."})
    monkeypatch.setattr(call, "fact_model", lambda c: ("mini", llm))
    core, _, _ = call.apply_general_background(context, {}, None, gap(), "task", _Usage(), [])
    assert (core.kind, core.basis) == ("DECLINE", "full_gap")
    assert core.evidence["general_background"]["text"] == "Causal networks need perturbations."
    assert events[-1]["status"] == "kept" and events[-1]["dropped"] == ["PANDA is one tool."]
    assert QUOTE in llm.seen[0][1].content


@pytest.mark.parametrize("payload", [{"answerable": False, "background": ""},
                                     {"answerable": True, "background": "NetZoo cannot do this."}])
def test_nothing_reliable_leaves_the_reply_as_it_was(monkeypatch, wired, payload):
    events, context = wired
    monkeypatch.setattr(call, "fact_model", lambda c: ("mini", _FakeLLM(payload)))
    core = gap()
    assert call.apply_general_background(context, {}, None, core, "task", _Usage(), [])[0] is core
    assert events[-1]["status"] == "none"


def test_off_by_default_and_not_on_a_verified_refusal(monkeypatch, wired):
    events, context = wired
    monkeypatch.setattr(call, "fact_model", lambda c: pytest.fail("model called"))
    verified = gap("jev_answer", "You answered x. So PANDA cannot do this as you asked.")
    assert call.apply_general_background(context, {}, None, verified, "t", _Usage(), [])[0] is verified
    monkeypatch.delenv("NETZOO_GENERAL_BACKGROUND")
    core = gap()
    assert call.apply_general_background(context, {}, None, core, "t", _Usage(), [])[0] is core
    assert events == []
