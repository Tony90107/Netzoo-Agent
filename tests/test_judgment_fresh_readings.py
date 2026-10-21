"""Regressions from new model readings, including failed evidence and modifier ownership."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import TaskDecision
from netzoo_agent_core.contracts.capability_check import proposal_model
from netzoo_agent_core.contracts.fact_check import FactProposals
from netzoo_agent_core.interpretation.capability_check import build_capability_check
from netzoo_agent_core.interpretation.checked_match import checked_match
from netzoo_agent_core.interpretation.core_decision import decide_core
from netzoo_agent_core.interpretation.fact_check import kept_facts
from netzoo_agent_core.interpretation.method_conditions import verified_controls
from netzoo_agent_core.policy import ProjectPolicyLoader

CASES = json.loads((Path(__file__).parent / "fixtures/judgment_repairs/fresh_readings.json").read_text())


def build(case):
    row = CASES[case]
    raw = row["proposal"]
    proposal = proposal_model(sum(k[1:].isdigit() for k in raw)).model_validate(raw)
    check, rejected = build_capability_check(row["task"], proposal)
    return row, check, rejected


def _without_split_fields(raw):
    """The live readings were taken with the withdrawn requirement_role/parent_quote fields (Claude split)."""
    if isinstance(raw, dict):
        return {k: _without_split_fields(v) for k, v in raw.items() if k not in ("requirement_role", "parent_quote")}
    if isinstance(raw, list):
        return [_without_split_fields(v) for v in raw]
    return raw


# J17's live reading credited nothing; only the withdrawn command recovery made it a run (Claude split).
@pytest.mark.parametrize("case,expected", [("J29", "CLARIFY")])
def test_second_live_reading_keeps_an_open_method_choice_and_full_setting_phrase(case, expected):
    rows = json.loads((Path(__file__).parent / "fixtures/judgment_repairs/verification_02.json").read_text())
    row = rows[case]
    raw = _without_split_fields(row["proposal"])
    check, _ = build_capability_check(row["task"], proposal_model(sum(k[1:].isdigit() for k in raw)).model_validate(raw))
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9,
                            reason="read", capability_check=check)
    core = decide_core(decision, row["task"])
    assert core.kind == expected
    if case == "J29":
        assert core.clarify.candidates == ["DRAGON", "LIONESS-DRAGON"]
    else:
        values = verified_controls(check, "run_sambar")
        assert values["norm_patient"] is True and values["gmt_msigdb"] is False


@pytest.mark.parametrize("task,expected", [
    ("Run DRAGON or LIONESS-DRAGON, your call.", ["DRAGON", "LIONESS-DRAGON"]),
    ("Run DRAGON or LIONESS-DRAGON for a network per sample, your call.", []),
    ("Run DRAGON or LIONESS-DRAGON on whole-cohort expression matrices, your call.", ["DRAGON", "LIONESS-DRAGON"]),
    ("Previously we used DRAGON or LIONESS-DRAGON, your call. Now run CONDOR.", []),
    ("Run DRAGON or LIONESS-DRAGON, your call.\nUser follow-up: Run DRAGON.", []),
])
def test_raw_choice_witness_requires_current_requested_methods_and_no_chosen_output_scale(task, expected):
    from netzoo_agent_core.interpretation.goal_evidence import source_granularity_choice

    assert source_granularity_choice(task) == expected




def test_methods_named_only_as_an_input_source_are_not_a_choice():
    """Claude split (2026-10-21): the raw choice counts only between workflows this turn weighs for the request."""
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck, CheckedRequirement
    from netzoo_agent_core.interpretation.goal_evidence import method_choice

    task = "Our inputs came from DRAGON or LIONESS-DRAGON. Run CONDOR on edges.tsv."
    check = CapabilityCheck(goal="method_named", goal_quote="Run CONDOR", requirements=[CheckedRequirement(
        quote="Run CONDOR on edges.tsv", kind="result", status="available", delivered_by=["condor.communities"])])
    condor = TaskDecision(action="run_condor", in_scope=True, should_execute=True, confidence=0.9, reason="read",
                          matched_actions=["run_condor"], capability_check=check)
    assert method_choice(check, condor, task) == []
    both = condor.model_copy(update={"action": "no_tool", "hypothesis_actions": ["run_dragon", "run_lioness_dragon"]})
    assert method_choice(check, both, "Run DRAGON or LIONESS-DRAGON on these layers.") == ["DRAGON", "LIONESS-DRAGON"]
