"""Log 267 (item 1, user decision): published methods this agent cannot run.

A capability-gap reply may name them for the missing principle and result.
They are never candidates, recommendations or prompt inputs.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from workflow_registry import EXTERNAL_REFERENCES, OUTPUT_CAPABILITIES, SELECTION_TAG_GLOSSARY  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import MethodCapabilityGap, RequestedOutcome  # noqa: E402
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()


def _gap(tags, artifact):
    return TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question",
        confidence=0.9, reason="gap", capability_match_status="ambiguous",
        hypothesis_actions=["run_panda", "run_otter"],
        requested_outcome=RequestedOutcome(operation="explain", artifact_type=artifact, granularity="unknown"),
        advisory_capability_gap=MethodCapabilityGap(selection_tags=tags, text_spans=["x"], rationale="No qualified workflow."),
    )


def test_entries_use_the_registry_vocabulary_and_cite_a_source():
    names = {spec.workflow for spec in POLICY.workflows.values()}
    for ref in EXTERNAL_REFERENCES:
        assert ref.selection_tags <= set(SELECTION_TAG_GLOSSARY), ref.name
        assert ref.name not in names and ref.source.strip() and ref.availability.strip()
    assert not {ref.name for ref in EXTERNAL_REFERENCES} & set(OUTPUT_CAPABILITIES)


def test_a_bayesian_regulatory_gap_names_the_references_without_recommending_them():
    answer = render_outcome_clarification(_gap(["bayesian"], "regulatory_network"), POLICY)

    section = answer.split("Outside this agent (reference only; it cannot run these):", 1)[1].split("\n\n", 1)[0]
    assert "**TIGER** (netZooR, R)" in section and "doi:10.1038/s41540-024-00386-w" in section
    assert "**Werhli & Husmeier (2007)**" in section and "PMID 17542777" in section
    assert "(recommend)" not in section
    assert answer.index("No qualified registered workflow") < answer.index("Outside this agent")


def test_a_reference_is_named_only_for_its_own_principle_and_result():
    assert "Outside this agent" not in render_outcome_clarification(_gap(["partial_correlation"], "regulatory_network"), POLICY)
    coexpression = render_outcome_clarification(_gap(["bayesian"], "coexpression_network"), POLICY)
    assert "TIGER" not in coexpression and "Werhli" not in coexpression
