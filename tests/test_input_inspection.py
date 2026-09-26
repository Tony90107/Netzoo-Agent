"""Log 152: advice from the file names in a folder the user named."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis, RequestedOutcome  # noqa: E402
from netzoo_agent_core.graph.input_inspection import (  # noqa: E402
    advise_from_inspected_inputs,
    named_directories,
)
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

TIE = ["run_lioness_panda", "run_lioness_puma"]
AUTHORITY = ("action", "should_execute", "capability_match_status", "matched_actions")


def _decision(**update) -> TaskDecision:
    outcome = RequestedOutcome(operation="infer", artifact_type="regulatory_network",
                               granularity="sample_specific")
    fields = dict(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question",
        confidence=1.0, reason="guidance", requested_outcome=outcome,
        outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=0.9)],
        hypothesis_actions=list(TIE), capability_match_status="ambiguous",
        clarification_question="Which regulator type should the network model?",
    )
    fields.update(update)
    return TaskDecision(**fields)


def _folder(root: Path, *names: str) -> str:
    folder = root / "data" / "study"
    folder.mkdir(parents=True)
    for name in names:
        (folder / name).write_text("x\n")
    return "data/study/"


def _task(written: str) -> str:
    return f"{written} has expression, motif and PPI files. I want per-patient TF networks."


def test_folder_without_a_mirna_list_recommends_the_panda_variant(tmp_path):
    written = _folder(tmp_path, "expression.tsv", "motif.tsv", "ppi.tsv")
    decision = _decision()

    advised = advise_from_inspected_inputs(_task(written), decision, root=tmp_path)

    assert advised.advisory_recommendation.action == "run_lioness_panda"
    assert [c.value for c in advised.advisory_recommendation.conditions] == ["missing:mirna_prior"]
    for field in AUTHORITY:
        assert getattr(advised, field) == getattr(decision, field), field


def test_folder_with_every_prior_recommends_nothing(tmp_path):
    written = _folder(tmp_path, "expression.tsv", "motif.tsv", "ppi.tsv", "mirna.txt")
    decision = _decision()

    assert advise_from_inspected_inputs(_task(written), decision, root=tmp_path) is decision


@pytest.mark.parametrize("written", ["../outside/", "data/missing/"])
def test_folders_outside_the_root_or_missing_are_ignored(tmp_path, written):
    (tmp_path.parent / "outside").mkdir(exist_ok=True)
    (tmp_path.parent / "outside" / "motif.tsv").write_text("x\n")
    (tmp_path.parent / "outside" / "ppi.tsv").write_text("x\n")

    assert named_directories(_task(written), root=tmp_path) == []
    decision = _decision()
    assert advise_from_inspected_inputs(_task(written), decision, root=tmp_path) is decision


def test_candidates_with_the_same_required_priors_are_left_alone(tmp_path):
    written = _folder(tmp_path, "expression.tsv", "motif.tsv", "ppi.tsv")
    decision = _decision(hypothesis_actions=["run_panda", "run_otter"])

    assert advise_from_inspected_inputs(_task(written), decision, root=tmp_path) is decision


def test_form_a_names_the_folder_and_says_contents_were_not_read(tmp_path):
    written = _folder(tmp_path, "expression.tsv", "motif.tsv", "ppi.tsv")
    advised = advise_from_inspected_inputs(_task(written), _decision(), root=tmp_path)

    answer = render_outcome_clarification(advised, ProjectPolicyLoader(ROOT).load())

    assert answer.startswith("The file names in `data/study/` look like a")
    assert "**LIONESS-PANDA** fits" in answer
    assert "**LIONESS-PUMA** — would also need a miRNA list." in answer
    assert "no file contents were read" in answer
    assert "No files were inspected" not in answer
