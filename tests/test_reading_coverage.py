"""A copied data description is not a checked count or a requested output."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from netzoo_agent_core.contracts import TaskDecision, HumanMessage
from netzoo_agent_core.contracts.capability_check import proposal_model
from netzoo_agent_core.contracts.capability_check import CapabilityCheck
from netzoo_agent_core.graph.response import respond
from netzoo_agent_core.interpretation.capability_check import (
    apply_second_opinion, build_capability_check, second_opinion_pairs, understanding_paragraph,
)
from netzoo_agent_core.interpretation.core_decision import decide_core, with_core


def _record(key):
    return json.loads((Path(__file__).parent / "fixtures/reading_coverage" / f"{key}.json").read_text())


def _build(raw):
    payload = raw["proposal"]
    n = sum(name[1:].isdigit() for name in payload)
    return build_capability_check(raw["task"], proposal_model(n).model_validate(payload))


def test_misplaced_background_cannot_be_promoted_by_the_second_opinion():
    raw = _record("T01")
    original = copy.deepcopy(raw)
    check, rejected = _build(raw)
    assert [r.quote for r in check.results()] == [raw["proposal"]["s1"]["asks"][0]["quote"]]
    pairs = second_opinion_pairs(check, ["run_lioness_panda"])
    check = apply_second_opinion(check, pairs, ["all"] * len(pairs))
    text = understanding_paragraph(check)
    assert '" -- available' not in text.split("1.")[0]
    assert "post-QC" not in text and "We have the TF motif" not in text
    assert sum(r["reason"] == "ask_in_other_background_sentence" for r in rejected) == 2
    assert raw == original


def test_a_misplaced_real_result_is_still_a_result():
    raw = _record("T01")
    raw["proposal"]["s2"]["role"] = "asks"
    check, _ = _build(raw)
    assert any("post-QC" in r.quote for r in check.results())
    assert not any("We have the TF motif" in r.quote for r in check.results())


@pytest.mark.parametrize("field, key", [("not_by", "outcome_prediction"),
                                      ("delivered_by", "lioness_panda.per_sample_networks")])
def test_sentence_roles_cannot_erase_a_credited_or_refused_result(field, key):
    raw = _record("T01")
    item = raw["proposal"]["s1"]["asks"][1]
    item[field] = [key]
    check, _ = _build(raw)
    assert item["quote"] in [row.quote for row in check.results()]


def test_unread_data_quantity_cannot_approve_a_sample_limited_workflow():
    raw = _record("T02")
    decision = TaskDecision.model_validate(raw["decision"])
    core = decide_core(decision, raw["task"])
    assert (core.kind, core.basis, core.run_allowed) == ("ASK", "count_fact", False)
    assert len(core.facts) == 1
    fact = core.facts[0]
    assert fact.depends_on == "sample_count" and fact.uncertainty == "unread"
    assert fact.user_quote == raw["proposal"]["s1"]["has"][0]
    assert "at least 3" in fact.question
    assert not fact.contract_quote  # computed minimum is not misrepresented as a verbatim clause
    assert not fact.by_code and not fact.outcomes  # no invented interpretation of the background numbers
    assert core.evidence["unread_sample_conditions"]


def test_unread_count_ask_holds_runs_and_has_a_complete_reply():
    raw = _record("T02")
    decision = TaskDecision.model_validate(raw["decision"]).model_copy(update={
        "action": "run_lioness_panda", "should_execute": True, "execution_requested": True})
    held = with_core(decision, decide_core(decision, raw["task"]))
    assert held.action == "no_tool"
    assert not held.should_execute and not held.execution_requested
    result = respond(None, {"decision": held.model_dump(mode="json"),
                            "messages": [HumanMessage(content=raw["task"])]})
    assert result["reply_kind"] == "ask_facts"
    assert "biological samples" in result["messages"][-1].content
    assert "No workflow has been selected" in result["messages"][-1].content


@pytest.mark.parametrize("count, expected", [(2, "DECLINE"), (14, "DO")])
def test_a_verified_answer_releases_the_unread_guard(count, expected):
    raw = _record("T02")
    answer = f"There are {count} biological samples."
    raw["task"] += " " + answer
    raw["proposal"]["conditions"].update(sample_count=count, sample_count_quote=answer)
    check, _ = _build(raw)
    decision = TaskDecision.model_validate(raw["decision"]).model_copy(update={"capability_check": check})
    assert decide_core(decision, raw["task"]).kind == expected


def test_the_guard_uses_the_preflight_sample_minimum(monkeypatch):
    from netzoo_agent_core.data import inspection

    raw = _record("T02")
    monkeypatch.setattr(inspection, "LIONESS_MIN_SAMPLES", 7)
    core = decide_core(TaskDecision.model_validate(raw["decision"]), raw["task"])
    assert core.kind == "ASK" and "at least 7" in core.facts[0].question


def test_generic_method_questions_and_workflows_without_a_sample_limit_are_not_held():
    raw = _record("T02")
    decision = TaskDecision.model_validate(raw["decision"])
    check = decision.capability_check
    only_result = check.model_copy(update={"requirements": check.results()})
    assert decide_core(decision.model_copy(update={"capability_check": only_result}), raw["task"]).kind == "DO"
    row = check.results()[0].model_copy(update={"delivered_by": ["panda.tf_gene_network"]})
    panda = check.model_copy(update={"requirements": [row, *[r for r in check.requirements if r.kind == "context"]]})
    assert decide_core(decision.model_copy(update={"capability_check": panda}), raw["task"]).kind == "DO"


def test_provider_failure_keeps_its_own_status():
    raw = _record("T02")
    decision = TaskDecision.model_validate(raw["decision"])
    check = decision.capability_check.model_copy(update={"provisional": True})
    assert decide_core(decision.model_copy(update={"capability_check": check}), raw["task"]).kind == "UNCHECKED"


def test_known_samples_are_not_asked_again_because_a_batch_count_was_unread():
    raw = _record("known_samples_and_batches")
    check = CapabilityCheck.model_validate(raw["check"])
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9,
                            reason="adjusted coexpression", capability_check=check)
    # The compiler retained the shared 140 sample fact but did not copy it to
    # either result's method. The three sequencing runs are a different count.
    assert all("samples" not in row.method for row in check.results())
    assert decide_core(decision, raw["task"]).kind == "DO"


@pytest.mark.parametrize("kind, scope", [("sample_count", []), ("feature_count", None)])
def test_an_unrelated_or_wrong_kind_count_cannot_clear_the_missing_sample_condition(kind, scope):
    raw = _record("known_samples_and_batches")
    check = CapabilityCheck.model_validate(raw["check"])
    check = check.model_copy(update={"facts": [fact.model_copy(update={"property": kind, "applies_to": scope})
                                              if fact.property == "sample_count" else fact
                                              for fact in check.facts]})
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9,
                            reason="r", capability_check=check)
    core = decide_core(decision, raw["task"])
    assert core.kind == "ASK" and core.facts[0].depends_on == "sample_count"


def test_a_known_count_cannot_settle_a_different_data_description():
    raw = _record("known_samples_and_batches")
    check = CapabilityCheck.model_validate(raw["check"])
    extra = "The other cohort contains either one or two samples."
    task = raw["task"] + " " + extra
    context = check.requirements[-1].model_copy(update={"quote": extra, "kind": "context", "method": {}})
    check = check.model_copy(update={"requirements": [*check.requirements, context]})
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9,
                            reason="r", capability_check=check)
    core = decide_core(decision, task)
    assert core.kind == "ASK" and core.facts[0].user_quote == extra


def test_verified_candidate_counts_still_follow_the_same_threshold_rules():
    for candidates, expected in [([1, 2], "DECLINE"), ([9, 17], "DO"), ([2, 14], "ASK")]:
        raw = _record("T02")
        quote = raw["proposal"]["s1"]["has"][0]
        text = "The cohort has either " + " or ".join(map(str, candidates)) + " samples"
        raw["task"] = raw["task"].replace(quote, text)
        raw["proposal"]["s1"]["has"][0] = text
        raw["proposal"]["conditions"]["unknown_facts"] = [{
            "about": "sample_count", "quote": text, "applies_to": None,
            "count_kind": "choices", "count_values": candidates}]
        check, _ = _build(raw)
        decision = TaskDecision.model_validate(raw["decision"]).model_copy(update={"capability_check": check})
        core = decide_core(decision, raw["task"])
        assert core.kind == expected
        assert "unread_sample_conditions" not in core.evidence


def test_ambiguous_sentence_ownership_is_not_guessed():
    from types import SimpleNamespace
    from netzoo_agent_core.interpretation.sentence_ownership import background_owner, request_sentences

    task = "Copy this phrase. Copy this phrase."
    sentences = [SimpleNamespace(role="background"), SimpleNamespace(role="asks")]
    assert background_owner(task, "Copy this phrase", 1, sentences, request_sentences(task)) is None
    assert background_owner(task, task, 1, sentences, request_sentences(task)) is None


def test_a_complete_numeric_read_scoped_to_another_result_cannot_clear_the_guard():
    from netzoo_agent_core.contracts.request_facts import FactEvidence, RequestFact

    raw = _record("T02")
    decision = TaskDecision.model_validate(raw["decision"])
    quote = raw["proposal"]["s1"]["has"][0]
    fact = RequestFact(id="other-count", property="sample_count", state="unsure", values=["1", "2"],
                       quote=quote, applies_to=["a different result"], evidence=[FactEvidence(
                           reader="result", quote=quote, span=[0, len(quote)], result="a different result")])
    check = decision.capability_check.model_copy(update={"facts": [fact]})
    assert decide_core(decision.model_copy(update={"capability_check": check}), raw["task"]).kind == "ASK"
