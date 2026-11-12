"""A "which tool do I need" sentence is weighed by its result, and a confirmed result is never declined (2026-11-12)."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement  # noqa: E402
from netzoo_agent_core.graph.capability_check_call import confirmed_answers  # noqa: E402
from netzoo_agent_core.interpretation.asked_words import confirmed_links, result_words  # noqa: E402
from netzoo_agent_core.interpretation.core_decision import goal_unclear  # noqa: E402

GOAL = "if i want to get sample specific mi-rna regulator network,what tools do i need ?"


@pytest.mark.parametrize("quote, words", [
    (GOAL, "get sample specific mi-rna regulator network"),
    ("if i want to get sample specific mi-rna regulator network , what tools can i use ?",
     "get sample specific mi-rna regulator network"),
    ("What tools do I need to predict patient drug response from my expression data?",
     "predict patient drug response from my expression data"),
    ("which method should I use for per-sample TF networks", "per-sample TF networks"),
    ("Build a co-expression network per sample, which one should I use?", "Build a co-expression network per sample"),
    ("How can I find communities in my PANDA network?", "find communities in my PANDA network"),
    # The same frames around other workflows' results (the fix is not this one sentence's).
    ("What tools do I need to build a gene regulatory network for my cohort?", "build a gene regulatory network for my cohort"),
    ("Which tool should I use to find communities in my regulatory network?", "find communities in my regulatory network"),
    ("Is there a tool for per-sample co-expression networks?", "per-sample co-expression networks"),
    ("What can I use to get TF activity for each sample?", "get TF activity for each sample"),
    ("Which NetZoo workflow fits a two-omics partial correlation network?", "a two-omics partial correlation network"),
    ("Can NetZoo build single-cell regulatory networks for each cell type?",
     "build single-cell regulatory networks for each cell type"),
    ("I'd like per-sample TF-gene networks, which workflow is best?", "per-sample TF-gene networks"),
    ("What should I run to subtype tumors from somatic mutations?", "subtype tumors from somatic mutations"),
    ("Recommend a method for removing batch effects from co-expression.", "removing batch effects from co-expression"),
    ("If I want a cohort-level TF network with miRNAs, what do I need?", "a cohort-level TF network with miRNAs"),
    ("Which method fits if I want sample specific regulatory networks?", "sample specific regulatory networks"),
    ("What workflow gives me a TF-by-sample activity matrix?", "a TF-by-sample activity matrix"),
    ("Do you have a tool for bipartite community detection?", "bipartite community detection"),
    ("Is it possible to get a network for each patient?", "get a network for each patient"),
    ("What's the best way to compare networks between tumor and normal?", "compare networks between tumor and normal"),
    ("I need sample-specific networks; what are my options?", "sample-specific networks"),
    ("To get TF activity per sample, which tool do I need?", "get TF activity per sample"),
    ("Tell me which method gives single-cell networks per cluster.", "single-cell networks per cluster"),
])
def test_the_tool_question_is_trimmed_and_the_result_kept(quote, words):
    assert result_words(quote) == words


@pytest.mark.parametrize("quote", [
    "what tools do i need?",  # nothing but the tool question: kept whole
    "Run PANDA on data/official-toy, then CONDOR",
    "Compare the tumor and normal networks, then find communities",
    "Build PANDA networks and tell me which TFs are hubs",
])
def test_anything_else_is_left_as_it_was(quote):
    assert result_words(quote) == quote


def _state(value="yes", goal=GOAL):
    return {"task_state": {"goal": goal, "facts": [
        {"what": "jev_link:LIONESS-PUMA", "value": value, "answer_quote": "Yes, I mean LIONESS-PUMA's result."}]}}


def test_only_a_yes_to_a_result_confirm_is_a_confirmed_link():
    assert confirmed_links(_state()["task_state"]) == {"LIONESS-PUMA": GOAL}
    assert confirmed_links(_state("no")["task_state"]) == {}
    assert confirmed_links(None) == {}


def _context(events):
    return SimpleNamespace(recorder=SimpleNamespace(append=lambda run, kind, node, payload: events.append((kind, payload))))


def test_a_confirmed_result_is_credited_for_the_goal_it_was_asked_about():
    events = []
    pairs = [("get sample specific mi-rna regulator network", "LIONESS-PUMA", "per-sample networks"),
             ("get sample specific mi-rna regulator network", "PUMA", "cohort network"),
             ("predict drug response", "LIONESS-PUMA", "per-sample networks")]  # added later: not the confirmed goal
    answers = confirmed_answers(_context(events), _state(), pairs, ["part", "part", "none"],
                                confirmed_links(_state()["task_state"]))
    assert answers == ["all", "part", "none"]
    assert events == [("routing.capability_link_confirmed",
                       {"credited": [{"pair": 0, "workflow": "LIONESS-PUMA", "answer_before": "part"}]})]


def test_without_a_confirmed_link_or_answers_nothing_changes():
    pairs = [("get sample specific mi-rna regulator network", "LIONESS-PUMA", "per-sample networks")]
    assert confirmed_answers(_context([]), {}, pairs, ["part"], {}) == ["part"]
    assert confirmed_answers(_context([]), _state(), pairs, None, confirmed_links(_state()["task_state"])) is None


def _check(status, delivered):
    return CapabilityCheck(goal="purpose_only", goal_quote=GOAL, requirements=[
        CheckedRequirement(quote=GOAL, kind="result", status=status, delivered_by=delivered)])


def test_a_purpose_read_whose_result_is_credited_is_not_an_unclear_goal():
    assert goal_unclear(_check("available", ["lioness_puma.per_sample_networks"])) is False
    assert goal_unclear(_check("not_available", [])) is True
