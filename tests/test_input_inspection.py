"""Log 154: advice from the *contents* of a folder the user named, not its file names."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
TOY = ROOT / "data" / "lioness-toy"
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


def _folder(root: Path, files: dict[str, str]) -> str:
    """files maps the name to write -> the toy file whose content it gets."""
    folder = root / "data" / "study"
    folder.mkdir(parents=True)
    for name, source in files.items():
        shutil.copy(TOY / source, folder / name)
    return "data/study/"


def _task(written: str) -> str:
    return f"{written} has my data. I want per-patient TF networks."


PANDA_SET = {"expression.tsv": "expression.tsv", "motif.tsv": "motif-panda.tsv", "ppi.tsv": "ppi.tsv"}


def test_contents_without_a_mirna_list_recommend_the_panda_variant(tmp_path):
    written = _folder(tmp_path, PANDA_SET)
    decision = _decision()

    advised = advise_from_inspected_inputs(_task(written), decision, root=tmp_path)

    assert advised.advisory_recommendation.action == "run_lioness_panda"
    assert advised.inspected_directories == [written]
    for field in AUTHORITY:
        assert getattr(advised, field) == getattr(decision, field), field


def test_contents_decide_when_names_say_nothing(tmp_path):
    written = _folder(tmp_path, {
        "table_01.dat": "expression.tsv", "table_02.dat": "motif-panda.tsv", "table_03.dat": "ppi.tsv",
    })

    advised = advise_from_inspected_inputs(_task(written), _decision(), root=tmp_path)

    assert advised.advisory_recommendation.action == "run_lioness_panda"
    values = {c.value for c in advised.advisory_recommendation.conditions}
    assert "validated:motif_file=table_02.dat" in values
    assert "validated:ppi_file=table_03.dat" in values


def test_a_file_named_like_a_mirna_list_does_not_count_unless_its_content_is_one(tmp_path):
    written = _folder(tmp_path, {**PANDA_SET, "mirna.txt": "ppi.tsv"})

    advised = advise_from_inspected_inputs(_task(written), _decision(), root=tmp_path)

    assert advised.advisory_recommendation.action == "run_lioness_panda"


def test_a_mirna_list_with_an_uninformative_name_still_counts(tmp_path):
    written = _folder(tmp_path, {
        "expression.tsv": "expression.tsv", "prior.tsv": "prior-puma.tsv",
        "ppi.tsv": "ppi.tsv", "list_04.dat": "mirna.txt",
    })

    advised = advise_from_inspected_inputs(_task(written), _decision(), root=tmp_path)

    assert advised.advisory_recommendation is None
    assert advised.inspected_directories == [written]


def test_reading_without_recommending_still_says_files_were_read(tmp_path):
    written = _folder(tmp_path, {
        "expression.tsv": "expression.tsv", "prior.tsv": "prior-puma.tsv",
        "ppi.tsv": "ppi.tsv", "list_04.dat": "mirna.txt",
    })
    advised = advise_from_inspected_inputs(_task(written), _decision(), root=tmp_path)

    answer = render_outcome_clarification(advised, ProjectPolicyLoader(ROOT).load())

    assert "No files were inspected" not in answer
    assert f"I read the files in `{written}` only to check which inputs they contain" in answer


def test_form_a_reports_what_validated_by_content(tmp_path):
    written = _folder(tmp_path, PANDA_SET)
    advised = advise_from_inspected_inputs(_task(written), _decision(), root=tmp_path)

    answer = render_outcome_clarification(advised, ProjectPolicyLoader(ROOT).load())

    assert answer.startswith(f"By content, the files in `{written}` validate as a complete input set")
    assert "`motif.tsv` as the TF-motif prior" in answer
    assert "**LIONESS-PUMA** — would also need a miRNA list." in answer
    assert "No files were inspected" not in answer


@pytest.mark.parametrize("written", ["../outside/", "data/missing/"])
def test_folders_outside_the_root_or_missing_are_never_read(tmp_path, written):
    outside = tmp_path.parent / "outside"
    outside.mkdir(exist_ok=True)
    shutil.copy(TOY / "motif-panda.tsv", outside / "motif.tsv")

    assert named_directories(_task(written), root=tmp_path) == []
    decision = _decision()
    assert advise_from_inspected_inputs(_task(written), decision, root=tmp_path) is decision


def test_ties_outside_the_panda_family_are_not_read(tmp_path):
    written = _folder(tmp_path, PANDA_SET)
    decision = _decision(hypothesis_actions=["run_panda", "run_otter"])

    assert advise_from_inspected_inputs(_task(written), decision, root=tmp_path) is decision


def test_form_a_quotes_non_english_folder_and_file_names_verbatim(tmp_path):
    """Log 180: folder and file names are user data and may be in any language."""
    folder = tmp_path / "data" / "研究"
    folder.mkdir(parents=True)
    for name, source in {"表達.tsv": "expression.tsv", "基序.tsv": "motif-panda.tsv",
                         "蛋白.tsv": "ppi.tsv"}.items():
        shutil.copy(TOY / source, folder / name)
    written = "data/研究/"
    advised = advise_from_inspected_inputs(
        f"{written} 裡有我的資料。我想要每位病人的 TF 網路。", _decision(), root=tmp_path,
    )

    answer = render_outcome_clarification(advised, ProjectPolicyLoader(ROOT).load())

    assert answer.startswith(f"By content, the files in `{written}` validate as a complete input set")
    assert "`基序.tsv` as the TF-motif prior" in answer
