"""Log 160: sample-specific composition guidance says what the networks are for next."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import AddressedConcern, OutcomeHypothesis, RequestedOutcome  # noqa: E402
from netzoo_agent_core.interpretation.concept_answers import (  # noqa: E402
    render_workflow_composition_guidance,
)
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402


def _decision(final: str, aggregate: str, regulators: list[str]) -> TaskDecision:
    outcome = RequestedOutcome(
        operation="infer", artifact_type="regulatory_network", granularity="sample_specific",
        regulator_types=regulators, target_types=["gene"], entity_types=[*regulators, "gene"],
    )
    return TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question",
        confidence=1.0, reason="guidance", requested_outcome=outcome,
        outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=0.9)],
        capability_match_status="exact", matched_actions=[final],
        recommended_actions=[aggregate, final],
    )


@pytest.mark.parametrize("final, aggregate, regulators", [
    ("run_lioness_panda", "run_panda", ["tf"]),
    ("run_lioness_puma", "run_puma", ["tf", "mirna"]),
])
def test_sample_specific_guidance_explains_targeting_clinical_data_and_dependence(final, aggregate, regulators):
    policy = ProjectPolicyLoader(ROOT).load()
    # Log 283 (user decision): the notes answer a stated downstream concern only.
    silent = render_workflow_composition_guidance(_decision(final, aggregate, regulators), policy)
    assert "clinical table" not in silent and "not statistically independent" not in silent
    asked = _decision(final, aggregate, regulators).model_copy(update={"addressed_concerns": [
        AddressedConcern(action=final, concern="downstream_use", text_span="relate it to survival")]})
    answer = render_workflow_composition_guidance(asked, policy)

    assert "About your concern that what to do with the result afterwards" in answer
    assert "outdegree" in answer and "indegree" in answer
    assert "clinical table" in answer
    assert "not statistically independent" in answer
    assert answer.rstrip().endswith("No files were inspected and no analysis ran.")


# Log 162: the advisory (form A) replies carry the same notes for the recommended workflow.
import shutil  # noqa: E402

from netzoo_agent_core.graph.input_inspection import advise_from_inspected_inputs  # noqa: E402
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification  # noqa: E402


def _tie() -> TaskDecision:
    outcome = RequestedOutcome(operation="infer", artifact_type="regulatory_network",
                               granularity="sample_specific")
    return TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question",
        confidence=1.0, reason="guidance", requested_outcome=outcome,
        outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=0.9)],
        hypothesis_actions=["run_lioness_panda", "run_lioness_puma"],
        capability_match_status="ambiguous",
        clarification_question="Which regulator type should the network model?",
    )


def test_folder_based_recommendation_includes_the_downstream_notes(tmp_path):
    folder = tmp_path / "data" / "study"
    folder.mkdir(parents=True)
    toy = ROOT / "data" / "lioness-toy"
    for name, source in (("expression.tsv", "expression.tsv"), ("motif.tsv", "motif-panda.tsv"),
                         ("ppi.tsv", "ppi.tsv")):
        shutil.copy(toy / source, folder / name)
    advised = advise_from_inspected_inputs("data/study/ has my data.", _tie(), root=tmp_path)
    policy = ProjectPolicyLoader(ROOT).load()
    # Log 283 (user decision): shown only for a stated downstream concern.
    assert "clinical table" not in render_outcome_clarification(advised, policy)
    asked = advised.model_copy(update={"addressed_concerns": [
        AddressedConcern(action="run_lioness_panda", concern="downstream_use", text_span="relate it to survival")]})

    answer = render_outcome_clarification(asked, policy)

    assert "About your concern that what to do with the result afterwards" in answer
    assert answer.index("About your concern") < answer.index("Should I use LIONESS-PANDA")
    assert "clinical table" in answer


# Log 166: every registered workflow says what its output is for next.
from workflow_registry import DOWNSTREAM_ANALYSES, OTHER_READING_NOTES, OUTPUT_CAPABILITIES  # noqa: E402

from netzoo_agent_core.graph.response_context import validated_workflow_context  # noqa: E402
from netzoo_agent_core.interpretation.verified_guidance import render_verified_guidance  # noqa: E402


def test_every_registered_workflow_has_downstream_notes():
    assert set(OUTPUT_CAPABILITIES) <= set(DOWNSTREAM_ANALYSES)
    for heading, notes in DOWNSTREAM_ANALYSES.values():
        assert heading.startswith("Downstream use of the") and heading.endswith(":")
        assert notes


@pytest.mark.parametrize("action", sorted(OUTPUT_CAPABILITIES))
def test_verified_guidance_renders_each_workflows_notes(action):
    policy = ProjectPolicyLoader(ROOT).load()
    decision = TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question",
        confidence=1.0, reason="guidance", capability_match_status="exact",
        matched_actions=[action], recommended_actions=[action],
    )

    heading, notes = DOWNSTREAM_ANALYSES[action]
    # Log 283 (user decision): the notes answer a stated downstream concern only.
    silent = render_verified_guidance(decision, validated_workflow_context(decision, policy))
    assert heading not in silent
    asked = decision.model_copy(update={"addressed_concerns": [
        AddressedConcern(action=action, concern="downstream_use", text_span="what next")]})
    answer = render_verified_guidance(asked, validated_workflow_context(asked, policy))

    shown = [note for note in notes if note != OTHER_READING_NOTES.get(action)]
    assert all(note in answer for note in shown)
    assert answer.index("What you asked about") < answer.index("This is workflow guidance only")
