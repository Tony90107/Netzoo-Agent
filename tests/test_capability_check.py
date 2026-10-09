"""Log 387: the capability sheet, the verified capability check, and how replies and cards use it."""

from __future__ import annotations

import sys
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


def _item(quote, delivered=(), not_by=(), **attrs):
    return {"quote": quote, "delivered_by": list(delivered), "not_by": list(not_by), "scale": "unstated",
            "omics_layers": 0, "data_unit": "not_stated", "regulator_kinds": [], "needs_sign": False,
            "input_network": "none", **attrs}


def _proposal(*sentences):
    """Each sentence as (text, items); an item is (quote, kind, delivered_by, not_by)."""
    def reading(items):
        kinds = {kind for _, kind, _, _ in items}
        role = ("background" if kinds == {"context"} else "methods_question" if kinds == {"about_methods"}
                else "asks" if kinds == {"result"} else "mixed")
        return {
            "role": role,
            "has": [quote for quote, kind, _, _ in items if kind == "context"],
            "about_methods": [_item(quote, delivered, not_by)
                              for quote, kind, delivered, not_by in items if kind == "about_methods"],
            "asks": [_item(quote, delivered, not_by) for quote, kind, delivered, not_by in items if kind == "result"],
        }
    return proposal_model(len(sentences)).model_validate(
        {f"s{index}": reading(items) for index, (_text, items) in enumerate(sentences, 1)})


def _splicing_proposal(delivered=()):
    return _proposal(
        ("s1", [("isoform-level quantifications from 80 brain samples", "context", (), ())]),
        ("s2", [("find which splicing factors control inclusion of each alternative exon", "result",
                 delivered, ("panda.no_motif_discovery",))]),
    )


def _splicing_check(delivered=()):
    return build_capability_check(SPLICING, _splicing_proposal(delivered))[0]


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


def test_sheet_fails_closed_on_a_produces_entry_without_a_granularity(tmp_path):
    bad = tmp_path / "sheet.yaml"
    bad.write_text(
        "workflows:\n  PANDA:\n    action: run_panda\n    produces:\n"
        "      - {id: p.x, result: A network., source: paper}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="granularity"):
        load_sheet(bad)


def test_sheet_fails_closed_on_a_run_action_without_produces(tmp_path):
    partial = tmp_path / "sheet.yaml"
    partial.write_text(
        "workflows:\n  PANDA:\n    action: run_panda\n    produces:\n"
        "      - {id: p.x, result: A network., source: paper, granularity: aggregate}\n", encoding="utf-8")
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


def test_an_ask_without_a_reason_says_it_was_not_matched():
    check = build_capability_check(SPLICING, _proposal(
        ("s1", [("isoform-level quantifications from 80 brain samples", "context", (), ())]),
        ("s2", [("find which splicing factors control inclusion of each alternative exon", "result", (), ())]),
    ))[0]
    assert '-- not matched to any registered workflow.' in understanding_paragraph(check)
    assert check.full_gap  # still nothing registered produces it


def test_an_unmatched_ask_in_a_background_sentence_is_read_as_background():
    proposal = proposal_model(2).model_validate({
        "s1": {"role": "background", "has": [], "about_methods": [],
               "asks": [{"quote": "isoform-level quantifications from 80 brain samples", "delivered_by": [],
                         "not_by": [], "scale": "unstated", "omics_layers": 0, "data_unit": "not_stated", "regulator_kinds": [], "needs_sign": False, "input_network": "none"}]},
        "s2": {"role": "asks", "has": [], "about_methods": [],
               "asks": [{"quote": "find which splicing factors control inclusion of each alternative exon",
                         "delivered_by": ["panda.tf_gene_network"], "not_by": [], "scale": "unstated",
                         "omics_layers": 0, "data_unit": "not_stated", "regulator_kinds": [], "needs_sign": False, "input_network": "none"}]},
    })
    check, _ = build_capability_check(SPLICING, proposal)
    assert [item.kind for item in check.requirements] == ["result", "context"]
    assert not check.unchecked
    matched = proposal_model(1).model_validate({"s1": {
        "role": "background", "has": [], "about_methods": [],
        "asks": [{"quote": "find which splicing factors control inclusion of each alternative exon",
                  "delivered_by": [], "not_by": ["panda.no_motif_discovery"], "scale": "unstated",
                  "omics_layers": 0, "data_unit": "not_stated", "regulator_kinds": [], "needs_sign": False, "input_network": "none"}]}})
    assert build_capability_check(SPLICING, matched)[0].results()[0].status == "not_available"


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
    assert sentence["required"] == ["role", "has", "about_methods", "asks"]
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


def _invocation(decision):
    return router_invocation._RouterInvocation(
        decision=decision, routing_state={}, usage=None, budget_warnings=[], reason_code=None)


def test_router_clears_every_candidate_on_a_full_gap(monkeypatch):
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                            capability_match_status="ambiguous",
                            hypothesis_actions=["run_panda", "run_otter"])
    monkeypatch.setattr(router_invocation, "record_event", lambda *args, **kwargs: None)
    updated = router_invocation._with_capability_check(
        None, {}, SPLICING, _invocation(decision), _splicing_proposal()).decision
    assert updated.hypothesis_actions == [] and updated.capability_match_status == "unsupported"
    assert updated.capability_check.full_gap


def test_router_keeps_candidates_when_something_is_available(monkeypatch):
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                            hypothesis_actions=["run_panda"])
    monkeypatch.setattr(router_invocation, "record_event", lambda *args, **kwargs: None)
    updated = router_invocation._with_capability_check(
        None, {}, SPLICING, _invocation(decision), _splicing_proposal(("panda.tf_gene_network",))).decision
    assert updated.hypothesis_actions == ["run_panda"]
    assert updated.capability_check.results()[0].status == "available"


def test_router_skips_a_run_request_and_a_turn_nothing_read():
    run = _invocation(TaskDecision(action="run_panda", in_scope=True, should_execute=True, confidence=0.9,
                                   reason="r"))
    assert router_invocation._with_capability_check(None, {}, SPLICING, run, _splicing_proposal()) is run
    guidance = _invocation(TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9,
                                        reason="r"))
    assert router_invocation._with_capability_check(None, {}, SPLICING, guidance, None) is guidance


def test_full_gap_card_lists_each_unavailable_result_and_offers_no_workflow():
    from netzoo_agent_core.reply_cards import builder

    decision = TaskDecision.model_validate(_state(_splicing_check())["decision"])
    card = builder._core_card("capability_check_gap", decision, None, SPLICING)
    assert card.kind == "capability_gap" and card.choices is None
    assert card.headline.startswith("No registered workflow produces what you asked for")
    assert [row.available for row in card.unavailable] == [False]
    assert "motif prior is an input" in card.unavailable[0].reason


def _ask(task, quote, delivered=(), not_by=(), scale="unstated", layers=0, unit="not_stated", kinds=(),
         sign=False, network="none"):
    return proposal_model(1).model_validate({"s1": {"role": "asks", "has": [], "about_methods": [], "asks": [
        {"quote": quote, "delivered_by": list(delivered), "not_by": list(not_by), "scale": scale,
         "omics_layers": layers, "data_unit": unit, "regulator_kinds": list(kinds), "needs_sign": sign, "input_network": network}]}})


SIGNS = "With liver expression and priors, we want to know whether each TF activates or represses its targets."


def test_a_cited_near_miss_never_credits_its_alternative():
    """Log 389: with gpt-4o the alternative rule only let single-cell networks and protein abundance through."""
    proposal = _ask(SIGNS, "whether each TF activates or represses its targets", not_by=("panda.no_sign",))
    check, _ = build_capability_check(SIGNS, proposal)
    assert check.full_gap and check.results()[0].delivered_by == []


def test_a_scale_narrows_the_workflows_but_never_empties_them():
    task = "We want a TF-gene network for each patient."
    quote = "a TF-gene network for each patient"
    both = ("lioness_panda.per_sample_networks", "otter.tf_gene_network")
    check, _ = build_capability_check(task, _ask(task, quote, both, scale="per_sample"))
    assert check.results()[0].delivered_by == ["lioness_panda.per_sample_networks"]
    only_aggregate, _ = build_capability_check(task, _ask(task, quote, ("otter.tf_gene_network",), scale="per_sample"))
    assert only_aggregate.results()[0].status == "available"  # a misread scale never makes a gap


def test_too_many_omics_layers_rule_dragon_out():
    task = "We want one joint network over expression, methylation and proteomics."
    quote = "one joint network over expression, methylation and proteomics"
    check, _ = build_capability_check(task, _ask(task, quote, ("dragon.two_layer_network",), layers=3))
    assert check.results()[0].status == "not_available" and check.full_gap
    two, _ = build_capability_check(task, _ask(task, quote, ("dragon.two_layer_network",), layers=2))
    assert two.results()[0].status == "available"


def test_single_cells_lncrna_regulators_and_signs_rule_entries_out():
    """Log 388: per-cell networks went to LIONESS, lncRNA regulators to PUMA, signs to PANDA."""
    task = "We want a separate network for every single cell with lncRNA regulators and their signs."
    quote = "a separate network for every single cell"
    cells, _ = build_capability_check(task, _ask(task, quote, ("lioness_panda.per_sample_networks",),
                                                 scale="per_sample", unit="single_cells"))
    assert cells.results()[0].status == "not_available"
    lnc, _ = build_capability_check(task, _ask(task, quote, ("puma.regulator_gene_network",), kinds=("lncrna",)))
    assert lnc.results()[0].status == "not_available"
    mirna, _ = build_capability_check(task, _ask(task, quote, ("puma.regulator_gene_network",), kinds=("tf", "mirna")))
    assert mirna.results()[0].status == "available"
    signs, _ = build_capability_check(task, _ask(
        task, quote, ("panda.tf_gene_network", "giraffe.signed_regulation"), sign=True))
    assert signs.results()[0].delivered_by == ["giraffe.signed_regulation"]
    coexp, _ = build_capability_check(task, _ask(task, quote, ("bonobo.per_sample_networks",), kinds=("tf",)))
    assert coexp.results()[0].status == "not_available"


def test_the_check_uses_its_own_model_when_configured(monkeypatch):
    """Log 389: OPENROUTER_CAPABILITY_MODEL replaces the semantic model for this call only."""
    from types import SimpleNamespace

    from netzoo_agent_core.contracts import LLMUsage
    from netzoo_agent_core.graph import capability_check_call as call

    seen = []

    class Fake:
        def __init__(self, name):
            self.name = name

        def with_structured_output(self, schema, **kwargs):
            seen.append(self.name)
            raise RuntimeError("no provider in tests")

    monkeypatch.setattr(call, "_own_llm", lambda model, max_tokens: Fake(model))
    monkeypatch.setattr(call, "preflight_budget", lambda *args, **kwargs: (SimpleNamespace(status="ok"), []))
    monkeypatch.setattr(call, "record_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(call, "append_llm_usage", lambda usage, **kwargs: seen.append(kwargs["model"]) or usage)
    context = SimpleNamespace(study_purpose_llm=Fake("semantic"), semantic_model_name="openai/gpt-4o-mini",
                              router_max_tokens=1000, task_token_budget=30000, price_catalog=None)
    monkeypatch.delenv("OPENROUTER_CAPABILITY_MODEL", raising=False)
    call.request_capability_check(context, {}, SPLICING, LLMUsage(budget_tokens=30000), [])
    monkeypatch.setenv("OPENROUTER_CAPABILITY_MODEL", "openai/gpt-4o")
    call.request_capability_check(context, {}, SPLICING, LLMUsage(budget_tokens=30000), [])
    # Log 399: a failed own model is followed by one attempt with the semantic model.
    assert seen == ["semantic", "openai/gpt-4o-mini", "openai/gpt-4o", "openai/gpt-4o", "semantic", "openai/gpt-4o-mini"]


DRAGON_ASK = "We want one network of direct associations between the two layers, with significance for each edge."


def test_second_opinion_pairs_only_fitting_entries_of_the_exact_workflows():
    from netzoo_agent_core.interpretation.capability_check import second_opinion_pairs

    quote = "one network of direct associations between the two layers, with significance for each edge"
    check, _ = build_capability_check(DRAGON_ASK, _ask(DRAGON_ASK, quote, layers=2, scale="whole_cohort"))
    assert check.full_gap
    pairs = second_opinion_pairs(check, ["run_dragon"])
    assert pairs == [(0, "run_dragon", ["dragon.two_layer_network", "dragon.edge_pvalues", "dragon.group_comparison"])]
    three, _ = build_capability_check(DRAGON_ASK, _ask(DRAGON_ASK, quote, layers=3))
    assert second_opinion_pairs(three, ["run_dragon"]) == []  # too many layers: nothing to ask


def test_a_yes_rescues_the_result_and_a_no_keeps_the_gap():
    from netzoo_agent_core.interpretation.capability_check import apply_second_opinion, second_opinion_pairs

    quote = "one network of direct associations between the two layers, with significance for each edge"
    check, _ = build_capability_check(DRAGON_ASK, _ask(DRAGON_ASK, quote, layers=2))
    pairs = second_opinion_pairs(check, ["run_dragon"])
    rescued = apply_second_opinion(check, pairs, [True])
    assert not rescued.full_gap and rescued.results()[0].status == "available"
    assert rescued.results()[0].second_opinion
    assert apply_second_opinion(check, pairs, [False]).full_gap


def test_router_asks_a_second_opinion_only_when_a_gap_clears_an_exact_match(monkeypatch):
    quote = "one network of direct associations between the two layers, with significance for each edge"
    asked = []
    monkeypatch.setattr(router_invocation, "record_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(router_invocation, "request_second_opinion",
                        lambda context, state, pairs, usage, warnings, situation=(): (asked.append(pairs) or [True] * len(pairs),
                                                                        usage, warnings))
    exact = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                         capability_match_status="exact", matched_actions=["run_dragon"])
    kept = router_invocation._with_capability_check(
        None, {}, DRAGON_ASK, _invocation(exact), _ask(DRAGON_ASK, quote, layers=2)).decision
    assert asked and kept.matched_actions == ["run_dragon"] and not kept.capability_check.full_gap
    asked.clear()
    ambiguous = exact.model_copy(update={"capability_match_status": "ambiguous", "matched_actions": [],
                                         "hypothesis_actions": ["run_dragon"]})
    # Not exact, nothing cited, and no distinctive typed attribute (Log 397): nobody to ask.
    cleared = router_invocation._with_capability_check(
        None, {}, DRAGON_ASK, _invocation(ambiguous), _ask(DRAGON_ASK, quote)).decision
    assert not asked and cleared.capability_check.full_gap and cleared.hypothesis_actions == []


def test_a_background_sentence_without_quotes_counts_as_read():
    """Log 392 (B): TEST_PROMPTS r9 listed background sentences as "Not checked"."""
    proposal = proposal_model(2).model_validate({
        "s1": {"role": "background", "has": [], "about_methods": [], "asks": []},
        "s2": {"role": "asks", "has": [], "about_methods": [], "asks": [
            {"quote": "find which splicing factors control inclusion of each alternative exon", "delivered_by": [],
             "not_by": [], "scale": "unstated", "omics_layers": 0, "data_unit": "not_stated",
             "regulator_kinds": [], "needs_sign": False, "input_network": "none"}]},
    })
    check, _ = build_capability_check(SPLICING, proposal)
    assert check.unchecked == [] and check.full_gap
    asks_without_quote = proposal_model(2).model_validate({
        "s1": {"role": "asks", "has": [], "about_methods": [], "asks": []},
        "s2": proposal.s2.model_dump(),
    })
    assert build_capability_check(SPLICING, asks_without_quote)[0].unchecked  # an ask sentence still must be quoted


def test_a_full_gap_keeps_the_outside_step_notes_of_cleared_candidates():
    """Log 392 (A): TEST_PROMPTS r9 tests 4 and 8 lost SCORPION's and ALPACA's notes."""
    from netzoo_agent_core.contracts import HumanMessage
    from netzoo_agent_core.interpretation.capability_check import full_gap_result

    task = ("We built networks for controls and patients. How can we directly quantify the differential modular "
            "structure between the two networks?")
    quote = "directly quantify the differential modular structure between the two networks"
    check, _ = build_capability_check(task, proposal_model(2).model_validate({
        "s1": {"role": "background", "has": [], "about_methods": [], "asks": []},
        "s2": {"role": "asks", "has": [], "about_methods": [], "asks": [
            {"quote": quote, "delivered_by": [], "not_by": ["condor.no_two_network_comparison"],
             "scale": "unstated", "omics_layers": 0, "data_unit": "not_stated", "regulator_kinds": [],
             "needs_sign": False, "input_network": "none"}]}}))
    assert check.full_gap
    state = _state(check.model_copy(update={"cleared": ["run_condor"]}))
    state["messages"] = [HumanMessage(content=task)]
    text = full_gap_result(state, lambda content, kind: {"messages": [AIMessage(content=content)],
                                                         "reply_kind": kind})["messages"][-1].content
    assert "ALPACA" in text and text.rstrip().endswith("No files were inspected and no analysis ran.")
    # Log 393: the closing sentence points to the note instead of reading against its route.
    assert "so none is offered for it as asked. The note below describes the closest route." in text
    state = _state(check)
    state["messages"] = [HumanMessage(content=task)]
    without = full_gap_result(state, lambda content, kind: {"messages": [AIMessage(content=content)],
                                                            "reply_kind": kind})["messages"][-1].content
    assert "ALPACA" not in without  # the ALPACA note is tied to CONDOR being a candidate
    assert "so none is offered as the way to get it." in without


def test_a_gene_gene_network_rules_condor_out():
    """Log 394 (Log 390 LN8): communities of a co-expression network went to CONDOR."""
    task = "We built a gene-gene co-expression network. We want to partition it into communities of genes."
    quote = "partition it into communities of genes"
    check, _ = build_capability_check(task, _ask(task, quote, ("condor.communities",), network="gene_gene"))
    assert check.results()[0].status == "not_available"
    tf, _ = build_capability_check(task, _ask(task, quote, ("condor.communities",), network="regulator_gene"))
    assert tf.results()[0].status == "available"
    from netzoo_agent_core.interpretation.capability_check import second_opinion_pairs
    assert second_opinion_pairs(check, ["run_condor"]) == []  # nothing left for the second opinion to credit


def test_the_check_has_its_own_allowance_but_never_reopens_a_spent_turn(monkeypatch):
    """Log 394: heldout3 KU9 x2 -- routing spent 26.6k of 30k and the budget skipped the check."""
    from types import SimpleNamespace

    from netzoo_agent_core.contracts import LLMUsage
    from netzoo_agent_core.graph import capability_check_call as call

    budgets = []

    def fake_preflight(context, state, **kwargs):
        budgets.append(context.task_token_budget)
        return SimpleNamespace(status="ok"), []

    class Undecodable:
        def with_structured_output(self, schema, **kwargs):
            return self

        def invoke(self, messages):
            raise ValueError("Semantic structured output could not be decoded")

    monkeypatch.delenv("OPENROUTER_CAPABILITY_MODEL", raising=False)
    monkeypatch.setattr(call, "preflight_budget", fake_preflight)
    monkeypatch.setattr(call, "record_event", lambda *args, **kwargs: None)
    context = SimpleNamespace(study_purpose_llm=Undecodable(), semantic_model_name="openai/gpt-4o-mini",
                              router_max_tokens=1000, task_token_budget=30000, price_catalog=None)
    proposal, usage, _, status = call.request_capability_check(context, {}, SPLICING, LLMUsage(budget_tokens=30000), [])
    assert proposal is None and status == "failed"
    assert budgets == [38000, 38000]  # the allowance, and one retry after an undecodable reply
    spent = LLMUsage(budget_tokens=30000)
    spent.budget_exhausted = True
    assert call.request_capability_check(context, {}, SPLICING, spent, [])[3] == "blocked"


def test_a_turn_the_check_could_not_read_says_so():
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck

    result = {"messages": [AIMessage(content="PANDA builds the network.")], "reply_kind": "verified_guidance"}
    updated = with_capability_check_reply(result, _state(CapabilityCheck(unavailable=True)), lambda text, kind: {
        "messages": [AIMessage(content=text)], "reply_kind": kind})
    assert updated["messages"][-1].content.startswith("This turn could not be checked")


def test_a_cited_near_miss_asks_its_workflow_even_when_routing_failed(monkeypatch):
    """Log 396: TEST_PROMPTS r12 test9 refused "infer a network" over OTTER's convexity near miss."""
    task = "We want to infer a gene regulatory network for a rare tissue, with a convex guarantee."
    quote = "infer a gene regulatory network for a rare tissue"
    asked = []
    monkeypatch.setattr(router_invocation, "record_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(router_invocation, "request_second_opinion",
                        lambda context, state, pairs, usage, warnings, situation=(): (asked.append(pairs) or [True] * len(pairs),
                                                                        usage, warnings))
    failed = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.0, reason="r",
                          capability_match_status="fallback")
    proposal = _ask(task, quote, not_by=("otter.no_global_optimum",), kinds=("tf",))
    decision = router_invocation._with_capability_check(None, {}, task, _invocation(failed), proposal).decision
    assert [workflow for _, workflow, _ in asked[0]] == ["OTTER"]
    assert not decision.capability_check.full_gap
    assert decision.capability_check.results()[0].delivered_by[0] == "otter.tf_gene_network"
    asked.clear()
    lnc = _ask(task, quote, not_by=("puma.no_lncrna_cerna",), kinds=("lncrna",))
    gap = router_invocation._with_capability_check(None, {}, task, _invocation(failed), lnc).decision
    assert asked == [] and gap.capability_check.full_gap  # typed attributes leave PUMA nothing to be asked


def test_a_blank_verdict_asks_the_workflows_its_typed_attributes_point_to(monkeypatch):
    """Log 397 (heldout6 NC6): routing failed and the check named nothing for a two-layer network."""
    from netzoo_agent_core.interpretation.capability_check import implied_actions

    task = "We want one network of direct associations between metabolites and lipids with edge p-values."
    quote = "one network of direct associations between metabolites and lipids with edge p-values"
    check, _ = build_capability_check(task, _ask(task, quote, layers=2, scale="whole_cohort"))
    # LIONESS-DRAGON writes the aggregate network too, so a cohort-level ask fits both.
    assert check.results()[0].blank and implied_actions(check.results()[0]) == ["run_dragon", "run_lioness_dragon"]
    asked = []
    monkeypatch.setattr(router_invocation, "record_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(router_invocation, "request_second_opinion",
                        lambda context, state, pairs, usage, warnings, situation=(): (
                            asked.append(pairs) or [True] * len(pairs), usage, warnings))
    failed = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.0, reason="r",
                          capability_match_status="fallback")
    decision = router_invocation._with_capability_check(
        None, {}, task, _invocation(failed), _ask(task, quote, layers=2, scale="whole_cohort")).decision
    assert [workflow for _, workflow, _ in asked[0]] == ["DRAGON", "LIONESS-DRAGON"]
    assert not decision.capability_check.full_gap


def test_a_blank_verdict_without_a_distinctive_attribute_implies_nothing():
    from netzoo_agent_core.interpretation.capability_check import implied_actions

    task = "We want copy-number segments for each tumor."
    plain, _ = build_capability_check(task, _ask(task, "copy-number segments for each tumor", kinds=("tf",)))
    assert implied_actions(plain.results()[0]) == []
    three, _ = build_capability_check(task, _ask(task, "copy-number segments for each tumor", layers=3))
    assert implied_actions(three.results()[0]) == []  # too many layers: the DRAGON family does not fit
    reasoned, _ = build_capability_check(task, _ask(task, "copy-number segments for each tumor", layers=2,
                                                    not_by=("dragon.no_more_layers",)))
    assert implied_actions(reasoned.results()[0]) == []  # a verdict with a reason is not blank


MIRNA_QUESTION = ("We also have miRNA expression data. Is there a method that incorporates miRNA target predictions "
                  "into regulatory network inference?")
MIRNA_QUOTE = "Is there a method that incorporates miRNA target predictions into regulatory network inference?"


def _methods_question(task, quote, delivered=(), **attrs):
    return proposal_model(2).model_validate({
        "s1": {"role": "background", "has": [], "about_methods": [], "asks": []},
        "s2": {"role": "methods_question", "has": [], "asks": [],
               "about_methods": [_item(quote, delivered, **attrs)]}})


def test_a_methods_question_naming_what_it_needs_is_checked():
    """Log 399 (TEST_PROMPTS r15 test6): the miRNA question was a bare methods quote, so nothing checked GIRAFFE."""
    check, _ = build_capability_check(MIRNA_QUESTION, _methods_question(
        MIRNA_QUESTION, MIRNA_QUOTE, regulator_kinds=["tf", "mirna"]))
    assert [(item.kind, item.status, item.blank) for item in check.results()] == [("result", "not_available", True)]
    credited, _ = build_capability_check(MIRNA_QUESTION, _methods_question(
        MIRNA_QUESTION, MIRNA_QUOTE, ("puma.regulator_gene_network", "giraffe.signed_regulation"),
        regulator_kinds=["tf", "mirna"]))
    assert credited.results()[0].delivered_by == ["puma.regulator_gene_network"]
    bare, _ = build_capability_check(MIRNA_QUESTION, _methods_question(MIRNA_QUESTION, MIRNA_QUOTE))
    assert bare.results() == [] and [item.kind for item in bare.requirements] == ["about_methods"]
    # An entry alone does not make it an ask (dev run test7: a "how to set it up" question credited to PANDA).
    entry_only, _ = build_capability_check(MIRNA_QUESTION, _methods_question(
        MIRNA_QUESTION, MIRNA_QUOTE, ("panda.tf_gene_network",)))
    assert entry_only.results() == []
    near_miss, _ = build_capability_check(MIRNA_QUESTION, proposal_model(2).model_validate({
        "s1": {"role": "background", "has": [], "about_methods": [], "asks": []},
        "s2": {"role": "methods_question", "has": [], "asks": [],
               "about_methods": [_item(MIRNA_QUOTE, (), ("panda.no_sign",))]}}))
    assert [item.status for item in near_miss.results()] == ["not_available"]


def test_routing_offers_ruled_out_by_the_check_are_redirected():
    from netzoo_agent_core.interpretation.capability_check import redirected_actions

    check, _ = build_capability_check(MIRNA_QUESTION, _methods_question(
        MIRNA_QUESTION, MIRNA_QUOTE, ("puma.regulator_gene_network",), regulator_kinds=["tf", "mirna"]))
    assert redirected_actions(check, ["run_giraffe"]) == ["run_puma"]
    assert redirected_actions(check, ["run_giraffe", "run_puma"]) == []  # one offer fits: routing stands
    blank, _ = build_capability_check(MIRNA_QUESTION, _methods_question(
        MIRNA_QUESTION, MIRNA_QUOTE, regulator_kinds=["mirna"]))
    assert redirected_actions(blank, ["run_giraffe"]) == ["run_puma", "run_lioness_puma"]
    cohort, _ = build_capability_check(MIRNA_QUESTION, _methods_question(
        MIRNA_QUESTION, MIRNA_QUOTE, regulator_kinds=["mirna"], scale="per_sample"))
    assert redirected_actions(cohort, ["run_giraffe"]) == ["run_lioness_puma"]
    plain, _ = build_capability_check(MIRNA_QUESTION, _methods_question(
        MIRNA_QUESTION, MIRNA_QUOTE, ("panda.tf_gene_network",)))
    assert redirected_actions(plain, ["run_giraffe"]) == []  # nothing distinctive rules GIRAFFE out
    cells, _ = build_capability_check(MIRNA_QUESTION, _methods_question(
        MIRNA_QUESTION, MIRNA_QUOTE, data_unit="single_cells"))
    assert redirected_actions(cells, ["run_panda"]) == []  # nothing meets it: the gap logic decides


def test_router_redirects_an_exact_match_the_check_rules_out(monkeypatch):
    events = []
    monkeypatch.setattr(router_invocation, "record_event", lambda context, state, kind, node, payload: events.append(kind))
    monkeypatch.setattr(router_invocation, "_with_applicability", lambda context, state, task, result: result)
    exact = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                         capability_match_status="exact", matched_actions=["run_giraffe"],
                         recommended_actions=["run_giraffe"])
    proposal = _methods_question(MIRNA_QUESTION, MIRNA_QUOTE, ("puma.regulator_gene_network",),
                                 regulator_kinds=["tf", "mirna"])
    decision = router_invocation._with_capability_check(
        None, {}, MIRNA_QUESTION, _invocation(exact), proposal).decision
    assert decision.capability_match_status == "exact" and decision.matched_actions == ["run_puma"]
    assert decision.requested_outcome.regulator_types == ["mirna", "tf"]
    assert decision.capability_check.results()[0].status == "available"
    assert "routing.capability_redirected" in events


def test_a_failed_own_model_is_followed_by_the_semantic_model(monkeypatch):
    """Log 399 (TEST_PROMPTS r15 test9): nemotron answered nothing twice; mini is asked instead."""
    from types import SimpleNamespace

    from netzoo_agent_core.contracts import LLMUsage
    from netzoo_agent_core.graph import capability_check_call as call

    asked = []

    class Model:
        def __init__(self, name, answer):
            self.name, self.answer = name, answer

        def with_structured_output(self, schema, **kwargs):
            self.schema = schema
            return self

        def invoke(self, messages):
            asked.append(self.name)
            if self.answer is None:
                raise ValueError("Semantic structured output could not be decoded")
            return {"parsed": self.schema.model_validate(self.answer), "raw": None, "parsing_error": None}

    answer = {f"s{i}": {"role": "background", "has": [], "about_methods": [], "asks": []} for i in (1, 2)}
    monkeypatch.setenv("OPENROUTER_CAPABILITY_MODEL", "nvidia/nemotron")
    monkeypatch.setattr(call, "_own_llm", lambda model, max_tokens: Model("own", None))
    monkeypatch.setattr(call, "preflight_budget", lambda *args, **kwargs: (SimpleNamespace(status="ok"), []))
    monkeypatch.setattr(call, "record_event", lambda *args, **kwargs: None)
    context = SimpleNamespace(study_purpose_llm=Model("mini", answer), semantic_model_name="openai/gpt-4o-mini",
                              router_max_tokens=1000, task_token_budget=30000, price_catalog=None)
    proposal, usage, _, status = call.request_capability_check(context, {}, SPLICING, LLMUsage(budget_tokens=30000), [])
    assert status == "ok" and proposal is not None and asked == ["own", "mini"]
    assert [call.model for call in usage.calls] == ["nvidia/nemotron", "openai/gpt-4o-mini"]


def test_a_failed_own_second_opinion_is_followed_by_the_semantic_model(monkeypatch):
    """Log 399: when the own model fails the check's turn, the second opinion must not fail with it."""
    from types import SimpleNamespace

    from netzoo_agent_core.contracts import LLMUsage
    from netzoo_agent_core.graph import capability_check_call as call

    asked = []

    class Model:
        def __init__(self, name, answer):
            self.name, self.answer = name, answer

        def with_structured_output(self, schema, **kwargs):
            self.schema = schema
            return self

        def invoke(self, messages):
            asked.append(self.name)
            if self.answer is None:
                raise TimeoutError("no answer")
            return {"parsed": self.schema.model_validate(self.answer), "raw": None, "parsing_error": None}

    monkeypatch.setenv("OPENROUTER_CAPABILITY_MODEL", "nvidia/nemotron")
    monkeypatch.setattr(call, "_own_llm", lambda model, max_tokens: Model("own", None))
    monkeypatch.setattr(call, "preflight_budget", lambda *args, **kwargs: (SimpleNamespace(status="ok"), []))
    monkeypatch.setattr(call, "record_event", lambda *args, **kwargs: None)
    context = SimpleNamespace(study_purpose_llm=Model("mini", {"a1": True}), semantic_model_name="openai/gpt-4o-mini",
                              router_max_tokens=1000, task_token_budget=30000, price_catalog=None)
    answers, _, _ = call.request_second_opinion(context, {}, [("q", "DRAGON", "r")], LLMUsage(budget_tokens=30000), [])
    assert answers == [True] and asked == ["own", "mini"]
