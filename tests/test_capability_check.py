"""Log 387: the capability sheet, the verified capability check, and how replies and cards use it."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.capability_sheet import load_sheet, sheet_entries  # noqa: E402
from netzoo_agent_core.contracts import AIMessage, TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import proposal_model  # noqa: E402
from netzoo_agent_core.graph import router_invocation  # noqa: E402
from netzoo_agent_core.graph.response import respond  # noqa: E402
from netzoo_agent_core.interpretation.capability_check import (  # noqa: E402
    build_capability_check, full_gap_reply, request_sentences, understanding_paragraph,
    with_capability_check_reply,
)
from workflow_registry import RUN_ACTIONS  # noqa: E402

SPLICING = ("We have isoform-level quantifications from 80 brain samples. We want to find which splicing "
            "factors control inclusion of each alternative exon.")
PER_TUMOR = ("We have RNA-seq from 90 ovarian tumors plus TF motif and protein interaction data. We want a "
             "separate TF-gene regulatory network for every tumor so we can relate it to survival.")


def _proposal(*sentences):
    """Each sentence as (text, items); an item is (quote, kind, delivered_by, not_by)."""
    def reading(items):
        return {
            "has": [quote for quote, kind, _, _ in items if kind == "context"],
            "about_methods": [quote for quote, kind, _, _ in items if kind == "about_methods"],
            "asks": [{"quote": quote, "delivered_by": list(delivered), "not_by": list(not_by)}
                     for quote, kind, delivered, not_by in items if kind == "result"],
        }
    return proposal_model(len(sentences)).model_validate(
        {f"s{index}": reading(items) for index, (_text, items) in enumerate(sentences, 1)})


def _splicing_check(delivered=()):
    return build_capability_check(SPLICING, _proposal(
        ("s1", [("isoform-level quantifications from 80 brain samples", "context", (), ())]),
        ("s2", [("find which splicing factors control inclusion of each alternative exon", "result",
                 delivered, ("panda.no_motif_discovery",))]),
    ))[0]


def test_sheet_covers_every_run_action_and_resolves_references():
    entries = sheet_entries()
    assert {item.action for item in entries.values() if item.kind == "produces"} >= set(RUN_ACTIONS)
    shared = entries["otter.no_complexes"]
    assert shared.workflow == "OTTER" and shared.text == entries["panda.no_complexes"].text
    assert entries["lioness_puma.per_sample_targeting"].level == "with_step"
    assert entries["dragon.edge_pvalues"].kind == "produces"  # Log 386
    assert entries["condor.core_scores"].kind == "produces"  # Log 386


def test_sheet_fails_closed_on_a_produces_entry_without_a_source(tmp_path):
    bad = tmp_path / "sheet.yaml"
    bad.write_text(
        "workflows:\n  PANDA:\n    action: run_panda\n    produces:\n"
        "      - {id: p.x, result: A network.}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="source"):
        load_sheet(bad)


def test_sheet_fails_closed_on_a_run_action_without_produces(tmp_path):
    partial = tmp_path / "sheet.yaml"
    partial.write_text(
        "workflows:\n  PANDA:\n    action: run_panda\n    produces:\n"
        "      - {id: p.x, result: A network., source: paper}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="without a produces entry"):
        load_sheet(partial)


def test_proposal_ids_are_enums_of_the_sheet():
    with pytest.raises(Exception):
        _proposal(("s", [("x", "result", ("panda.invented_capability",), ())]))


def test_no_produces_entry_is_a_full_gap_with_the_near_miss_reason():
    check = _splicing_check()
    assert check.full_gap and not check.unchecked
    text = full_gap_reply(check)
    assert "not available here: no registered workflow produces this" in text
    assert "PANDA does not give it: the motif prior is an input" in text
    assert "none is offered" in text


def test_registry_wide_reasons_need_the_verified_claim():
    proposal = _proposal(("s1", [("isoform-level quantifications from 80 brain samples", "context", (), ())]),
                         ("s2", [("find which splicing factors control inclusion of each alternative exon",
                                  "result", (), ("causal_proof",))]))
    unverified, _ = build_capability_check(SPLICING, proposal)
    assert unverified.results()[0].not_by == []
    verified, _ = build_capability_check(SPLICING, proposal, frozenset({"causal"}))
    assert verified.results()[0].not_by == ["causal_proof"]


def test_a_near_verbatim_quote_stands_for_the_request_words():
    task = "We want a regulatory network for each patient, then a classifier to predict survival."
    check, rejected = build_capability_check(task, _proposal(
        ("s1", [("We want a classifier to predict survival.", "result", (), ())])))
    assert not rejected
    assert check.results()[0].quote == "a classifier to predict survival"


def test_one_passage_read_as_two_asks_with_and_without_an_entry_is_partial():
    task = "We want an integrated network for each patient and then a forecast of each network."
    quote = "an integrated network for each patient and then a forecast of each network"
    check, _ = build_capability_check(task, _proposal(("s1", [
        (quote, "result", ("lioness_dragon.per_sample_networks",), ()), (quote, "result", (), ())])))
    assert [item.status for item in check.results()] == ["partial"]
    assert "partly available: LIONESS-DRAGON gives part of it" in understanding_paragraph(check)
    assert not check.full_gap


def test_near_misses_never_decide_support():
    """A produces entry delivers it even when a near miss is also named."""
    check = _splicing_check(delivered=("panda.tf_gene_network",))
    assert check.results()[0].status == "available"
    assert not check.full_gap


def test_a_quote_not_in_the_request_is_dropped_and_its_sentence_is_unchecked():
    check, rejected = build_capability_check(SPLICING, _proposal(
        ("s1", [("isoform-level quantifications from 80 brain samples", "context", (), ())]),
        ("s2", [("discover splicing regulators genome-wide", "result", (), ())]),
    ))
    assert rejected == [{"quote": "discover splicing regulators genome-wide", "reason": "quote_not_in_request"}]
    assert check.unchecked == ["We want to find which splicing factors control inclusion of each alternative exon."]
    assert not check.full_gap  # an unchecked sentence may hold something that is available


def test_with_step_and_unchecked_sentence_are_said():
    check, _ = build_capability_check(PER_TUMOR, _proposal(
        ("s2", [("a separate TF-gene regulatory network for every tumor", "result",
                 ("lioness_panda.per_sample_networks", "lioness_puma.per_sample_networks"), ()),
                ("relate it to survival", "result", ("lioness_panda.association_tests",), ())]),
    ))
    assert [item.status for item in check.results()] == ["available", "with_step"]
    text = understanding_paragraph(check)
    assert "available from LIONESS-PANDA or LIONESS-PUMA." in text
    assert "plus a step you run outside NetZoo" in text
    assert 'Not checked against the registered workflows: "We have RNA-seq from 90 ovarian tumors' in text
    assert not check.full_gap


def test_methods_questions_and_context_are_not_checked():
    task = "We have RNA-seq. Which method should we use?"
    check, _ = build_capability_check(task, _proposal(
        ("s", [("We have RNA-seq", "context", (), ()), ("Which method should we use?", "about_methods", (), ())]),
    ))
    assert check.results() == [] and not check.full_gap
    assert understanding_paragraph(check) is None


def test_schema_requires_one_field_per_sentence():
    schema = proposal_model(3).model_json_schema()
    assert schema["required"] == ["s1", "s2", "s3"] and schema["additionalProperties"] is False
    sentence = schema["$defs"]["SentenceReading"]
    assert sentence["required"] == ["has", "about_methods", "asks"]
    assert "not_by" not in str(sentence["properties"]["has"])  # only an ask can name entries


def test_messages_number_the_sentences_the_schema_names():
    from netzoo_agent_core.graph.capability_check_call import build_capability_check_messages

    messages, count = build_capability_check_messages(SPLICING)
    assert count == 2
    assert messages[1].content.endswith(
        "Sentences:\n1. We have isoform-level quantifications from 80 brain samples.\n"
        "2. We want to find which splicing factors control inclusion of each alternative exon.")


def test_request_sentences_split_on_end_marks_and_lines():
    assert [SPLICING[s:e] for s, e in request_sentences(SPLICING)] == [
        "We have isoform-level quantifications from 80 brain samples.",
        "We want to find which splicing factors control inclusion of each alternative exon.",
    ]


def _state(check, **decision):
    payload = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                           capability_check=check, **decision).model_dump()
    return {"decision": payload, "messages": []}


def test_respond_answers_a_full_gap_without_any_renderer():
    result = respond(None, _state(_splicing_check()))
    assert result["reply_kind"] == "capability_check_gap"
    assert "none is offered" in result["messages"][-1].content


def test_other_replies_open_with_what_was_understood():
    check = _splicing_check(delivered=("panda.tf_gene_network",))
    result = {"messages": [AIMessage(content="PANDA builds the network.")], "reply_kind": "verified_guidance"}
    updated = with_capability_check_reply(result, _state(check), lambda text, kind: {
        "messages": [AIMessage(content=text)], "reply_kind": kind})
    content = updated["messages"][-1].content
    assert content.startswith("What I understood you are asking for:")
    assert content.endswith("PANDA builds the network.")


def test_router_clears_every_candidate_on_a_full_gap(monkeypatch):
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                            capability_match_status="ambiguous",
                            hypothesis_actions=["run_panda", "run_otter"])
    monkeypatch.setattr(router_invocation, "invoke_capability_check",
                        lambda context, state, task, usage, warnings, claims: (_splicing_check(), usage, warnings))
    monkeypatch.setattr(router_invocation, "record_event", lambda *args, **kwargs: None)
    invocation = router_invocation._RouterInvocation(
        decision=decision, routing_state={}, usage=None, budget_warnings=[], reason_code=None)
    updated = router_invocation._with_capability_check(None, {}, SPLICING, invocation).decision
    assert updated.hypothesis_actions == [] and updated.capability_match_status == "unsupported"
    assert updated.capability_check.full_gap


def test_router_keeps_candidates_when_something_is_available(monkeypatch):
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                            hypothesis_actions=["run_panda"])
    check = _splicing_check(delivered=("panda.tf_gene_network",))
    monkeypatch.setattr(router_invocation, "invoke_capability_check",
                        lambda context, state, task, usage, warnings, claims: (check, usage, warnings))
    invocation = router_invocation._RouterInvocation(
        decision=decision, routing_state={}, usage=None, budget_warnings=[], reason_code=None)
    updated = router_invocation._with_capability_check(None, {}, SPLICING, invocation).decision
    assert updated.hypothesis_actions == ["run_panda"] and updated.capability_check is check


def test_router_skips_a_run_request(monkeypatch):
    monkeypatch.setattr(router_invocation, "invoke_capability_check",
                        lambda *args: pytest.fail("a run request is not checked"))
    decision = TaskDecision(action="run_panda", in_scope=True, should_execute=True, confidence=0.9, reason="r")
    invocation = router_invocation._RouterInvocation(
        decision=decision, routing_state={}, usage=None, budget_warnings=[], reason_code=None)
    assert router_invocation._with_capability_check(None, {}, SPLICING, invocation) is invocation
    assert replace  # dataclasses.replace stays importable for the module under test


def test_full_gap_card_lists_each_unavailable_result_and_offers_no_workflow():
    from netzoo_agent_core.reply_cards import builder

    decision = TaskDecision.model_validate(_state(_splicing_check())["decision"])
    card = builder._core_card("capability_check_gap", decision, None, SPLICING)
    assert card.kind == "capability_gap" and card.choices is None
    assert card.headline.startswith("No registered workflow produces what you asked for")
    assert [row.available for row in card.unavailable] == [False]
    assert "motif prior is an input" in card.unavailable[0].reason
