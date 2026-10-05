"""Log 376: what a request says about its TF priors, read by its own small call.

The provider is a fake. The decisions are recorded ones from earlier live
rounds (already read), so only the call, its hook and the tie reply are under
test.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from netzoo_agent_core.contracts import LLMUsage, TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.data_facts import DataFactsProposal  # noqa: E402
from netzoo_agent_core.graph.data_facts_call import invoke_data_facts, verify_data_facts  # noqa: E402
from netzoo_agent_core.graph.router_invocation import _tie_with_question  # noqa: E402
from test_study_purpose_call import _context, _recorded  # noqa: E402

LIVE = ROOT / "docs" / "research-log" / "purpose-contract-2026-10-04" / "live"
TASK = ("Whole blood from 28 children was RNA-sequenced before and after a year of oral immunotherapy; the "
        "resulting gene count table is the whole of our data.")


def test_a_reading_stands_when_its_quote_is_in_the_request_and_nothing_more_is_checked():
    entry, rejected = verify_data_facts(TASK, DataFactsProposal(
        priors="ruled_out", priors_span="the resulting gene count table is the whole of our data"))
    assert entry == {"source": "model", "priors": "ruled_out",
                     "priors_quote": "the resulting gene count table is the whole of our data"} and rejected == []
    entry, rejected = verify_data_facts(TASK, DataFactsProposal(priors="stated", priors_span="a motif prior"))
    assert entry["priors"] == "unstated" and rejected == [
        {"field": "priors", "value": "stated", "reason": "quote_not_in_request"}]
    entry, _ = verify_data_facts(TASK, DataFactsProposal(priors="unstated", priors_span=""))
    assert entry == {"source": "model", "priors": "unstated", "priors_quote": ""}


def test_the_call_is_strict_records_its_reading_and_its_own_role():
    reply = DataFactsProposal(priors="ruled_out", priors_span="the resulting gene count table is the whole of our data")
    context, events = _context(reply)
    entry, usage, _ = invoke_data_facts(context, {}, TASK, LLMUsage(), [])
    assert context.study_purpose_llm.options[0][1] == {
        "method": "function_calling", "include_raw": True, "strict": True}
    assert entry["priors"] == "ruled_out"
    assert [call.role for call in usage.calls] == ["data_facts"]
    assert dict(events)["routing.data_facts_detected"]["priors"] == "ruled_out"


def test_nothing_is_read_when_the_call_is_missing_or_fails():
    context, _ = _context(None)
    context.study_purpose_llm = None
    entry, usage, _ = invoke_data_facts(context, {}, TASK, LLMUsage(), [])
    assert entry is None and usage.calls == []
    context, events = _context(RuntimeError("provider down"))
    entry, usage, _ = invoke_data_facts(context, {}, TASK, LLMUsage(), [])
    assert entry is None and dict(events)["routing.data_facts_failed"]["error_type"] == "RuntimeError"
    assert [call.status for call in usage.calls] == ["failed"]


def _decision(tag, key):
    return TaskDecision.model_validate(json.loads((LIVE / f"{tag}-decisions.json").read_text())[key]["decision"])


@pytest.mark.parametrize("claims, expected", [
    ([["regulator_change", "which TFs differ"]], True),
    ([], False),  # no stated question: the tie reply does not rank, so nothing is read
    ([["causal", "show it causes"], ["group_difference", "differ"]], False),  # a gap reply instead
])
def test_the_call_is_asked_only_on_a_tie_with_a_stated_question(claims, expected):
    tie = _decision("s13", "cand-B4-1")
    assert _tie_with_question(tie, {"claims": claims}) is expected
    exact = tie.model_copy(update={"capability_match_status": "exact"})
    assert _tie_with_question(exact, {"claims": [["regulator_change", "which TFs differ"]]}) is False


PURPOSE = {"source": "model", "design": "groups", "design_quote": "x", "claims": [[
    "regulator_change",
    "which transcription factors differ most between the lakes in how strongly they regulate their target genes"]]}


def _reply_with(facts):
    from langchain_core.messages import HumanMessage
    from netzoo_agent_core.contracts import WorkflowPlan
    from netzoo_agent_core.graph import response
    from test_reply_cards import POLICY
    from types import SimpleNamespace

    item = json.loads((LIVE / "s13-decisions.json").read_text())["cand-B4-1"]
    decision = TaskDecision.model_validate(item["decision"])
    plan = WorkflowPlan(workflow="NO-TOOL", objective=item["prompt"][:200], decision=decision.model_dump(),
                        status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(), "tool_results": [], "evaluation": None,
             "messages": [HumanMessage(content=item["prompt"])], "study_purpose": PURPOSE, "data_facts": facts}
    return response.respond(SimpleNamespace(project_policy=POLICY), state)["messages"][-1].content


def test_the_tie_reply_uses_the_calls_reading_and_shows_it_in_the_users_words():
    # s13 B4 names no prior. Nothing read: the word lists, which ask.
    assert "depends on whether you have a TF motif prior" in _reply_with(None)
    # Read as stated (here wrongly): the reply recommends the prior-based workflows and quotes what it rests on.
    text = _reply_with({"source": "model", "priors": "stated", "priors_quote": "We sequenced head-kidney transcriptomes"})
    assert ('with the TF motif prior and PPI network you mentioned ("We sequenced head-kidney transcriptomes"), these '
            "fit best") in text
    # Read as ruled out: every candidate needs them, and the reply says so in the user's words.
    text = _reply_with({"source": "model", "priors": "ruled_out", "priors_quote": "We sequenced head-kidney transcriptomes"})
    assert ("none of the workflows suggested for this result works without a TF motif prior and a PPI network, which "
            'you said you do not have ("We sequenced head-kidney transcriptomes").') in text


def test_the_study_purpose_prompt_is_untouched():
    from netzoo_agent_core.llm import DATA_FACTS_SYSTEM, STUDY_PURPOSE_SYSTEM

    assert "priors" not in STUDY_PURPOSE_SYSTEM and "priors" in DATA_FACTS_SYSTEM
