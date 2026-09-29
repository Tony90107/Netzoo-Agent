"""Log 261: a tie is explained by what separates its candidates, for every workflow.

The spec sheet printed every registered field of every candidate. The user
asked for method notes only where they matter; a post-transcriptional
degradation question should point at PUMA's miRNA design, not repeat six
mathematical interpretations.
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import MethodCapabilityGap, RequestedOutcome  # noqa: E402
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification  # noqa: E402
from netzoo_agent_core.interpretation.method_philosophy import method_philosophies_for  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()
SHEET_LABELS = ("Registered purpose", "Method premise", "Mathematical interpretation", "Declared output")


def _tie(actions, artifact="regulatory_network", question="Which fits your study?", **outcome):
    return TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question",
        confidence=0.9, reason="tie", capability_match_status="ambiguous",
        hypothesis_actions=list(actions), clarification_question=question,
        requested_outcome=RequestedOutcome(operation="explain", artifact_type=artifact,
                                           granularity="unknown", **outcome),
    )


def _same_result_ties():
    by_artifact = {}
    for action, cap in OUTPUT_CAPABILITIES.items():
        for artifact in {cap.artifact_type} | set(cap.produced_artifacts):
            by_artifact.setdefault(artifact, []).append(action)
    for artifact, actions in sorted(by_artifact.items()):
        for size in range(2, len(actions) + 1):
            for combo in itertools.combinations(sorted(actions), size):
                yield artifact, combo


@pytest.mark.parametrize("artifact, actions", list(_same_result_ties()))
def test_every_registered_tie_names_each_method_once_without_a_spec_sheet(artifact, actions):
    answer = render_outcome_clarification(_tie(actions, artifact), POLICY)

    for action in actions:
        assert f"**{POLICY.workflows[action].workflow}**" in answer
    assert not [label for label in SHEET_LABELS if label in answer]
    for line in answer.splitlines():
        if line.startswith("- **"):
            assert " — " in line and len(line.split(" — ", 1)[1]) > 20, line
    assert answer.endswith("No files were inspected and no analysis ran.")


def test_a_degradation_question_points_at_puma_design_and_keeps_tf_methods_short():
    tie = ["run_panda", "run_puma", "run_lioness_panda", "run_lioness_puma", "run_otter", "run_giraffe"]
    answer = render_outcome_clarification(_tie(tie), POLICY)

    puma = next(line for line in answer.splitlines() if line.startswith("- **PUMA**"))
    assert "TargetScan or miRanda" in puma
    assert "keeps each miRNA's cooperativity with other regulators at its initial value" in puma
    assert "Per-sample version: **LIONESS-PUMA**" in puma
    assert answer.index("**TF/miRNA regulatory network**") < answer.index("- **PUMA**")
    panda = next(line for line in answer.splitlines() if line.startswith("- **PANDA**"))
    assert "Per-sample version: **LIONESS-PANDA**" in panda
    assert "not calibrated posterior probabilities" not in panda
    assert "W_q = N*W_all" not in answer
    assert len(answer) < 2600


def test_the_puma_note_states_what_the_code_does_not_do():
    (note,) = [n for n in method_philosophies_for(["mirna_regulation"])]
    assert "miRNA's own expression is not used" in note
    assert "anti-correlation receives no special weight for repression" in note


def test_a_pure_method_tie_is_described_by_assumptions_without_family_headings():
    answer = render_outcome_clarification(_tie(["run_panda", "run_otter"], regulator_types=["tf"]), POLICY)

    assert answer.startswith("Several registered methods fit this result; they differ in their modeling assumptions:")
    assert "**TF-only regulatory network**" not in answer


def test_shared_mechanism_is_said_once():
    answer = render_outcome_clarification(_tie(["run_lioness_panda", "run_lioness_puma"]), POLICY)

    assert answer.count("derive each sample network from all-sample and leave-one-out networks") == 1
    assert "W_q = N*W_all" not in answer
    assert "keeps each miRNA's cooperativity" in answer


def test_a_missing_estimator_is_explained_as_a_principle():
    decision = _tie(["run_panda", "run_otter"]).model_copy(update={
        "advisory_capability_gap": MethodCapabilityGap(
            selection_tags=["partial_correlation"], text_spans=["x"], rationale="No qualified workflow."),
    })
    answer = render_outcome_clarification(decision, POLICY)

    assert answer.startswith("Partial correlation asks whether two features stay associated")
    assert "Requested modeling principle" not in answer
