"""NETZOO_REGULATOR_SCOPE: a miRNA extension tied with its TF-only base is not offered when the request states
TF priors and no miRNA data (app session 07a68476, 2026-11-02: "a TF motif prior and a PPI network ... a regulatory
network for each patient" asked "Which regulator type ...?" in 5 of 13 runs). Nothing calls a model.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_routing import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.cli.follow_up import build_next_turn_prompt  # noqa: E402
from netzoo_agent_core.contracts import HumanMessage, TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.graph.response import respond  # noqa: E402
from netzoo_agent_core.interpretation.regulator_scope import (  # noqa: E402
    applied, enabled, mirna_extensions, narrow_regulator_scope)
from netzoo_agent_core.reply_cards import build_reply_card  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()
TASK = ("I have RNA-seq from 50 tumors, a TF motif prior and a PPI network. "
        "I want a regulatory network for each patient.")
FACTS = {"source": "model", "priors": "stated", "priors_quote": "a TF motif prior and a PPI network",
         "mirna": "unstated", "mirna_quote": ""}


def _outcome(regulators=(), granularity="sample_specific"):
    return {"operation": "infer", "artifact_type": "regulatory_network", "granularity": granularity,
            "regulator_types": list(regulators)}


def _decision(candidates=("run_lioness_panda", "run_lioness_puma"), facts=FACTS, **extra) -> TaskDecision:
    return TaskDecision.model_validate({
        "action": "no_tool", "in_scope": True, "should_execute": False, "confidence": 0.5, "reason": "r",
        "capability_match_status": "ambiguous", "hypothesis_actions": list(candidates),
        "requested_outcome": _outcome(), "clarification_question": (
            "Which regulator type should the network model: transcription factors, miRNA regulators, or both?"),
        "data_facts": facts, **extra})


def _replay(task: str, decision: TaskDecision):
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task, decision=decision.model_dump(), status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=task)],
             "tool_results": [], "evaluation": None}
    out = respond(SimpleNamespace(project_policy=POLICY), state)
    result = {**state, "messages": [HumanMessage(content=task), out["messages"][-1]], "reply_kind": out["reply_kind"]}
    return str(out["messages"][-1].content), build_reply_card(result, build_next_turn_prompt(result), POLICY, task=task)


def test_off_unless_the_flag_is_on(monkeypatch):
    monkeypatch.delenv("NETZOO_REGULATOR_SCOPE", raising=False)
    assert not enabled()
    monkeypatch.setenv("NETZOO_REGULATOR_SCOPE", "on")
    assert enabled()


def test_extensions_come_from_the_registry():
    assert mirna_extensions(["run_lioness_panda", "run_lioness_puma"]) == {"run_lioness_puma": "run_lioness_panda"}
    assert mirna_extensions(["run_panda", "run_puma", "run_otter"]) == {"run_puma": "run_panda"}
    # a base at another scale is not the extension's base
    assert mirna_extensions(["run_panda", "run_lioness_puma"]) == {}
    assert mirna_extensions(["run_puma"]) == {}


def test_the_recorded_tie_becomes_lioness_panda_and_the_reply_stops_asking():
    stored = _decision()
    before, _ = _replay(TASK, stored)
    assert "Which regulator type" in before  # the recorded question

    decision, dropped = narrow_regulator_scope(stored, TASK)
    assert dropped == ["run_lioness_puma"]
    assert decision.matched_actions == ["run_lioness_panda"] and decision.capability_match_status == "exact"
    assert decision.hypothesis_actions == [] and decision.clarification_question is None
    reply, card = _replay(TASK, decision)
    assert "Which regulator type" not in reply and "LIONESS-PUMA" not in reply
    assert "LIONESS-PANDA" in reply and "LIONESS-PANDA" in card.headline


def test_a_larger_tie_keeps_its_other_candidates_and_a_question():
    decision, dropped = narrow_regulator_scope(
        _decision(("run_panda", "run_puma", "run_otter", "run_giraffe")), TASK)
    assert dropped == ["run_puma"]
    assert decision.hypothesis_actions == ["run_panda", "run_otter", "run_giraffe"]
    assert decision.matched_actions == [] and decision.clarification_question
    assert "miRNA" not in decision.clarification_question


@pytest.mark.parametrize("why,decision,task", [
    ("miRNA data stated", _decision(facts={**FACTS, "mirna": "stated", "mirna_quote": "a miRNA list"}), TASK),
    ("priors not stated", _decision(facts={**FACTS, "priors": "unstated", "priors_quote": ""}), TASK),
    ("no data facts read", _decision(facts=None), TASK),
    ("miRNA words in the request", _decision(), TASK + " Small non-coding RNAs may matter too."),
    ("a reading names miRNA regulators", _decision(requested_outcome=_outcome(("tf", "mirna"))), TASK),
    ("the user named the workflow", _decision(match_basis="workflow_name"), TASK),
    ("no extension in the tie", _decision(("run_lioness_panda", "run_giraffe")), TASK),
])
def test_left_alone(why, decision, task):
    assert narrow_regulator_scope(decision, task) == (decision, []), why


def test_applied_records_only_when_it_drops(monkeypatch):
    seen = []
    monkeypatch.delenv("NETZOO_REGULATOR_SCOPE", raising=False)
    stored = _decision()
    assert applied(stored, TASK, seen.append) is stored and seen == []
    monkeypatch.setenv("NETZOO_REGULATOR_SCOPE", "on")
    assert applied(stored, TASK, seen.append).matched_actions == ["run_lioness_panda"]
    assert seen == [{"dropped": ["run_lioness_puma"], "kept": ["run_lioness_panda"], "data_facts": FACTS}]
