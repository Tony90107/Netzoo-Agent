"""jev-links-first-2026-10-29 (phase C): Jev's confident link replaces the reading's when the flag is on; a low or
failed read keeps the reading's; shadow records and changes nothing; off makes no call."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from test_method_conditions import _ask  # noqa: E402

from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402
from netzoo_agent_core.graph import context as graph_context  # noqa: E402
from netzoo_agent_core.graph import jev_links_first_call as call  # noqa: E402
from netzoo_agent_core.interpretation.jev_links_first import linked, menu, pick  # noqa: E402

TASK = "We have 30 pigs. I want one TF-to-gene regulatory network per tissue, each built from all 30 samples."
QUOTE = "I want one TF-to-gene regulatory network per tissue, each built from all 30 samples."


def _option(entry_id):
    return next(option for option, found in menu()[1].items() if found == entry_id)


def _proposal(delivered=("lioness_panda.per_sample_networks",)):
    sentences = {"s1": {"role": "background", "has": ["30 pigs"], "about_methods": [], "asks": []},
                 "s2": {"role": "asks", "has": [], "about_methods": [], "asks": [_ask(QUOTE, delivered)]}}
    return proposal_model(2).model_validate(sentences)


def _links(proposal):
    return [ask.delivered_by for ask in proposal.s2.asks]


def test_the_rule():
    panda = {"choice": _option("panda.tf_gene_network"), "confidence": 0.9}
    assert pick(panda) == ["panda.tf_gene_network"]
    assert pick({**panda, "confidence": 0.69}) is None
    assert pick({"choice": "none", "confidence": 0.95}) == []
    assert pick({"error": "down"}) is None
    assert _links(linked(_proposal(), {QUOTE: panda})) == [["panda.tf_gene_network"]]
    assert _links(linked(_proposal(), {QUOTE: {**panda, "confidence": 0.5}})) == [["lioness_panda.per_sample_networks"]]
    assert linked(_proposal(), {}) is not None and _links(linked(_proposal(), {})) == [["lioness_panda.per_sample_networks"]]


@pytest.fixture
def calls(monkeypatch):
    found = {"decide": 0, "events": []}

    def decide(state, questions, timeout):
        found["decide"] += 1
        return {"answers": {"link": {"choice": _option("panda.tf_gene_network"), "confidence": 0.95}},
                "usage": {"cost": 1e-5}}

    monkeypatch.setattr(call, "decide", decide)
    monkeypatch.setattr(graph_context, "record_event", lambda c, s, name, node, payload: found["events"].append(
        (name, payload)))
    return found


def test_off_makes_no_call(monkeypatch, calls):
    monkeypatch.delenv("NETZOO_JEV_LINKS_FIRST", raising=False)
    proposal = _proposal()
    assert call.jev_linked(None, {}, TASK, proposal) is proposal and calls["decide"] == 0 and not calls["events"]


def test_shadow_records_and_changes_nothing(monkeypatch, calls):
    monkeypatch.setenv("NETZOO_JEV_LINKS_FIRST", "shadow")
    proposal = _proposal()
    assert call.jev_linked(None, {}, TASK, proposal) is proposal and calls["decide"] == 1
    (name, payload), = calls["events"]
    assert name == "core.jev_links_first" and payload["applied"] is False
    assert payload["reads"][0]["pick"] == ["panda.tf_gene_network"]


def test_on_applies_and_an_error_keeps_the_reading(monkeypatch, calls):
    monkeypatch.setenv("NETZOO_JEV_LINKS_FIRST", "on")
    assert _links(call.jev_linked(None, {}, TASK, _proposal())) == [["panda.tf_gene_network"]]
    monkeypatch.setattr(call, "decide", lambda *a, **k: (_ for _ in ()).throw(TimeoutError("slow")))
    proposal = _proposal()
    assert call.jev_linked(None, {}, TASK, proposal) is proposal
    assert "error" in calls["events"][-1][1]["reads"][0]
