"""Log 406: words the capability check left unread are read once more, asks only.

heldout11 VN5q ("Is there a method that models how each TF-gene edge at one time point depends on the
edges at the previous time point?") was filed as a question about methods 3 of 3 times and four
workflows were said to "all fit"; heldout13 P1's "uploaded automatically to a public database" was
never quoted. Nothing here calls a model.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import (  # noqa: E402
    CapabilityCheck, CheckedRequirement, proposal_model, reread_as_proposal, reread_model,
)
from netzoo_agent_core.interpretation.capability_check import build_capability_check  # noqa: E402
from netzoo_agent_core.interpretation.reread import merge_reread, reread_passages  # noqa: E402

VN5Q = ("We measured expression every 2 hours for 48 hours after heat shock, with motifs and PPI. Is there a method "
        "that models how each TF-gene edge at one time point depends on the edges at the previous time point?")
QUESTION = VN5Q.split(". ", 1)[1]
P1 = "We want the communities of our bipartite TF-gene network, uploaded automatically to a public database when they are done."
PLAIN = {"scale": "unstated", "omics_layers": 0, "data_unit": "not_stated", "regulator_kinds": [], "needs_sign": False,
         "input_network": "none", "group_membership": "not_about_groups", "time_model": "not_dynamic",
         "spatial": "not_spatial", "asked_as": "request"}


def _req(quote, kind, status="not_checked", keys=()):
    return CheckedRequirement(quote=quote, kind=kind, status=status, delivered_by=list(keys))


def _decision(check, **extra):
    return TaskDecision.model_validate({"action": "no_tool", "in_scope": True, "should_execute": False,
                                        "confidence": 0.5, "reason": "r", "capability_check": check.model_dump(),
                                        "capability_match_status": "ambiguous",
                                        "hypothesis_actions": ["run_panda", "run_otter"], **extra})


def test_a_request_with_no_result_read_is_read_again_when_routing_offered_workflows():
    check = CapabilityCheck(requirements=[_req(VN5Q.split(". ")[0] + ".", "context"), _req(QUESTION, "about_methods")])
    assert reread_passages(VN5Q, _decision(check)) == [VN5Q.split(". ")[0] + ".", QUESTION]
    # nothing offered, a named workflow asked about, or a check that did not run: nothing to read
    assert reread_passages(VN5Q, _decision(check, hypothesis_actions=[], capability_match_status=None)) == []
    named = CapabilityCheck(requirements=[_req("How does PANDA use the PPI network?", "about_methods")])
    assert reread_passages("How does PANDA use the PPI network?", _decision(named)) == []
    assert reread_passages(VN5Q, _decision(check.model_copy(update={"provisional": True}))) == []


def test_a_long_unquoted_stretch_beside_a_quoted_result_is_read_again():
    found = CapabilityCheck(requirements=[_req("the communities of our bipartite TF-gene network", "result", "available",
                                               ["condor.communities"])])
    # Item 4: only the words no quote covers are given, not the sentence whose result was already read.
    assert reread_passages(P1, _decision(found, capability_match_status="exact", matched_actions=["run_condor"])) == [
        "uploaded automatically to a public database when they are done"]
    framing = "We have RNA-seq from 64 kidney biopsies plus motifs. We want one TF-gene network for the cohort."
    plain = CapabilityCheck(requirements=[_req("RNA-seq from 64 kidney biopsies plus motifs", "context"),
                                          _req("one TF-gene network for the cohort", "result", "available",
                                               ["panda.tf_gene_network"])])
    assert reread_passages(framing, _decision(plain)) == []


def _reread_check(task, quote, delivered=(), **attrs):
    reread = reread_model(1).model_validate({"s1": {"asks": [{**PLAIN, "quote": quote, "delivered_by": list(delivered),
                                                              "not_by": [], **attrs}]}})
    return build_capability_check(task, reread_as_proposal(reread))[0]


def test_a_new_result_replaces_the_methods_quote_and_can_make_a_full_gap():
    check = CapabilityCheck(requirements=[_req(VN5Q.split(". ")[0] + ".", "context"), _req(QUESTION, "about_methods")])
    merged = merge_reread(VN5Q, check, _reread_check(VN5Q, QUESTION, time_model="dynamic", asked_as="question"))
    assert [(item.kind, item.status) for item in merged.requirements] == [("context", "not_checked"),
                                                                          ("result", "not_available")]
    assert merged.full_gap


def test_a_reread_result_overlapping_one_already_found_is_dropped():
    task = ("Which method gives each TF's activity per sample from our expression, motifs and PPI, "
            "and also aligns our raw reads to the genome first?")
    found = CapabilityCheck(requirements=[_req("each TF's activity per sample", "result", "available",
                                               ["giraffe.tf_activity"])])
    assert merge_reread(task, found, _reread_check(task, task.rstrip("?"))) is found


def test_a_new_result_beside_a_found_one_is_added_without_a_full_gap():
    found = CapabilityCheck(requirements=[_req("the communities of our bipartite TF-gene network", "result", "available",
                                               ["condor.communities"])])
    merged = merge_reread(P1, found, _reread_check(P1, "uploaded automatically to a public database"))
    assert [(item.quote, item.status) for item in merged.results()] == [
        ("the communities of our bipartite TF-gene network", "available"),
        ("uploaded automatically to a public database", "not_available")]
    assert not merged.full_gap


def test_the_router_reads_again_before_the_second_opinion(monkeypatch):
    from netzoo_agent_core.graph import router_invocation

    calls = []
    monkeypatch.setattr(router_invocation, "record_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(router_invocation, "request_capability_reread",
                        lambda context, state, task, passages, usage, warnings: (
                            calls.append(passages) or reread_model(len(passages)).model_validate({
                                "s1": {"asks": []},
                                "s2": {"asks": [{**PLAIN, "quote": QUESTION, "delivered_by": [], "not_by": [],
                                                 "time_model": "dynamic", "asked_as": "question"}]}}),
                            usage, warnings))
    monkeypatch.setattr(router_invocation, "request_second_opinion",
                        lambda *args, **kwargs: (["none"] * len(args[2]), args[3], args[4]))
    proposal = proposal_model(2).model_validate({
        "s1": {"role": "background", "has": [VN5Q.split(". ")[0] + "."], "about_methods": [], "asks": []},
        "s2": {"role": "methods_question", "has": [], "about_methods": [QUESTION], "asks": []}})
    tied = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9, reason="r",
                        capability_match_status="ambiguous", hypothesis_actions=["run_panda", "run_otter"])
    invocation = router_invocation._RouterInvocation(decision=tied, routing_state={}, usage=None,
                                                     budget_warnings=[], reason_code=None)

    decision = router_invocation._with_capability_check(None, {}, VN5Q, invocation, proposal).decision

    assert len(calls) == 1 and decision.capability_check.full_gap
    assert decision.capability_match_status == "unsupported" and not decision.hypothesis_actions


EMAILED = ("We want each patient's TF-gene network from expression, motifs and PPI of 50 patients, emailed to each "
           "patient's doctor automatically.")


def test_a_short_tail_in_any_script_is_read_again_and_framing_is_not():
    """Item 4 (2026-10-14): the English 4-letter-word count missed short tails and every unspaced script."""
    from netzoo_agent_core.interpretation.reread import letter_runs

    task = "We want one TF-gene network per sample and upload them."
    found = CapabilityCheck(requirements=[_req("one TF-gene network per sample", "result", "available",
                                               ["lioness_panda.per_sample_networks"])])
    assert reread_passages(task, _decision(found)) == ["and upload them"]
    framing = "Which method gives one TF-gene network per sample?"
    plain = CapabilityCheck(requirements=[_req("one TF-gene network per sample", "result", "available",
                                               ["lioness_panda.per_sample_networks"])])
    assert reread_passages(framing, _decision(plain)) == []
    assert letter_runs("and upload them") == 3 and letter_runs("並上傳到公開資料庫") == 5


def test_the_reread_quotes_only_the_words_it_was_given():
    """heldout14 P1 (rr-cand): given the whole sentence, the re-read quoted the network again and the e-mail stayed
    unread; a result quoted outside the given words is the first reading's."""
    found = CapabilityCheck(requirements=[_req("each patient's TF-gene network", "result", "available",
                                               ["lioness_panda.per_sample_networks"]),
                                          _req("expression, motifs and PPI of 50 patients", "context")])
    passages = reread_passages(EMAILED, _decision(found))
    assert passages == ["from expression, motifs and PPI of 50 patients, emailed to each patient's doctor automatically"]
    elsewhere = _reread_check(EMAILED, "expression, motifs and PPI of 50 patients", ["panda.tf_gene_network"])
    assert merge_reread(EMAILED, found, elsewhere, passages) is found
    tail = merge_reread(EMAILED, found, _reread_check(EMAILED, "emailed to each patient's doctor automatically"),
                        passages)
    assert [(item.quote, item.status) for item in tail.results()][-1] == (
        "emailed to each patient's doctor automatically", "not_available")


def test_an_unchecked_sentence_is_read_again_and_an_empty_answer_reads_it():
    """10-13 noise: "Not checked against the registered workflows: 'Opinions welcome.'" under every reply."""
    task = "We want one TF-gene network for the cohort. Opinions welcome."
    found = CapabilityCheck(requirements=[_req("one TF-gene network for the cohort", "result", "available",
                                               ["panda.tf_gene_network"])], unchecked=["Opinions welcome."])
    passages = reread_passages(task, _decision(found))
    assert passages == ["Opinions welcome."]
    nothing = build_capability_check(task, reread_as_proposal(reread_model(1).model_validate({"s1": {"asks": []}})))[0]
    assert merge_reread(task, found, nothing, passages).unchecked == []
    # A quote the re-read made up leaves the sentence unchecked.
    assert merge_reread(task, found, nothing, passages, [{"quote": "x", "reason": "quote_not_in_request"}]) is found


VP5Q = ("Which method gives each TF's activity per sample from our expression, motifs and PPI, and also aligns our raw "
        "reads to the genome first?")


def test_stretches_a_context_quote_separates_are_read_as_one_passage():
    """Live check VP5q: "and also aligns" and "to the genome first" around the context quote "our raw reads"."""
    found = CapabilityCheck(requirements=[
        _req("each TF's activity per sample", "result", "available", ["giraffe.tf_activity"]),
        _req("our expression, motifs and PPI", "context"), _req("our raw reads", "context")])
    assert reread_passages(VP5Q, _decision(found)) == [
        "from our expression, motifs and PPI, and also aligns our raw reads to the genome first"]
    # A data clause alone after the result is one unread word: not read again.
    plain = "We want each patient's TF-gene network from expression, motifs and PPI of 50 patients."
    data = CapabilityCheck(requirements=[_req("each patient's TF-gene network", "result", "available",
                                              ["lioness_panda.per_sample_networks"]),
                                         _req("expression, motifs and PPI of 50 patients", "context")])
    assert reread_passages(plain, _decision(data)) == []
