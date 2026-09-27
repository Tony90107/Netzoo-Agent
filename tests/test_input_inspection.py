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

    # Log 186: this prior lists a regulator from the list, so the list now
    # recommends LIONESS-PUMA; before, both candidates were equipped and
    # nothing was recommended. Either way it counts by content, not name.
    assert advised.advisory_recommendation.action == "run_lioness_puma"
    values = {c.value for c in advised.advisory_recommendation.conditions}
    assert "validated:mirna_file=list_04.dat" in values
    assert "mixed_prior:1" in values
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


def test_ties_outside_the_panda_family_only_report_what_validated(tmp_path):
    """Log 188 (was: such ties are not read). Reading now reports, never recommends."""
    written = _folder(tmp_path, PANDA_SET)
    decision = _decision(hypothesis_actions=["run_panda", "run_otter"])

    advised = advise_from_inspected_inputs(_task(written), decision, root=tmp_path)

    assert advised.advisory_recommendation is None
    assert advised.inspected_directories == [written]
    assert f"motif_file={written}motif.tsv" in advised.discovered_inputs
    for field in AUTHORITY:
        assert getattr(advised, field) == getattr(decision, field), field


def test_ties_without_a_panda_family_member_are_not_read(tmp_path):
    written = _folder(tmp_path, PANDA_SET)
    decision = _decision(hypothesis_actions=["run_otter", "run_giraffe"])

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


CASE_5 = {"expression.tsv": "expression.tsv", "prior.tsv": "prior-puma.tsv",
          "ppi.tsv": "ppi.tsv", "mirna.txt": "mirna.txt"}
MIXED_TIE = ["run_panda", "run_puma", "run_otter", "run_giraffe"]


def _case_5_task(written: str) -> str:
    return (f"My prior regulatory table ({written}prior.tsv) also has small RNAs, listed in "
            "mirna.txt. Use the expression and PPI files in the same folder.")


def test_a_named_file_names_its_folder(tmp_path):
    """Log 186: the request names only data/study/prior.tsv."""
    written = _folder(tmp_path, CASE_5)

    assert named_directories(_case_5_task(written), tmp_path) == [
        (written, (tmp_path / "data" / "study").resolve()),
    ]


def test_a_prior_that_uses_its_mirna_list_recommends_puma_over_tf_only_candidates(tmp_path):
    written = _folder(tmp_path, CASE_5)
    decision = _decision(hypothesis_actions=list(MIXED_TIE))

    advised = advise_from_inspected_inputs(_case_5_task(written), decision, root=tmp_path)

    assert advised.advisory_recommendation.action == "run_puma"
    assert "mixed_prior:1" in {c.value for c in advised.advisory_recommendation.conditions}
    for field in AUTHORITY:
        assert getattr(advised, field) == getattr(decision, field), field

    answer = render_outcome_clarification(advised, ProjectPolicyLoader(ROOT).load())

    assert "`prior.tsv` lists 1 regulator(s) that `mirna.txt` validates as miRNAs" in answer
    assert "**OTTER** — would read every regulator in the prior as a transcription factor." in answer


def test_a_mirna_list_the_prior_never_uses_recommends_nothing(tmp_path):
    written = _folder(tmp_path, {**CASE_5, "prior.tsv": "motif-panda.tsv"})
    decision = _decision(hypothesis_actions=list(MIXED_TIE))

    advised = advise_from_inspected_inputs(_case_5_task(written), decision, root=tmp_path)

    assert advised.advisory_recommendation is None
    assert advised.inspected_directories == [written]


def test_a_named_prior_outranks_an_unselected_clean_tf_prior(tmp_path):
    """An extra file does not undo the user's choice of this analysis's prior."""
    written = _folder(tmp_path, {**CASE_5, "motif.tsv": "motif-panda.tsv"})
    decision = _decision(hypothesis_actions=list(MIXED_TIE))

    advised = advise_from_inspected_inputs(_case_5_task(written), decision, root=tmp_path)

    assert advised.advisory_recommendation.action == "run_puma"
    assert "validated:motif_file=prior.tsv" in {
        condition.value for condition in advised.advisory_recommendation.conditions
    }


def test_a_folder_without_a_selected_prior_keeps_both_readings(tmp_path):
    written = _folder(tmp_path, {**CASE_5, "motif.tsv": "motif-panda.tsv"})
    decision = _decision(hypothesis_actions=list(MIXED_TIE))

    advised = advise_from_inspected_inputs(
        f"My files are in {written}. I want one overall regulatory network.",
        decision, root=tmp_path,
    )

    assert advised.advisory_recommendation is None


@pytest.mark.parametrize("source", [None, "ppi.tsv"])
def test_an_explicit_missing_or_invalid_prior_is_never_replaced(tmp_path, source):
    files = {**PANDA_SET, "mirna.txt": "mirna.txt"}
    if source is not None:
        files["chosen.tsv"] = source
    written = _folder(tmp_path, files)
    task = f"Use motif_file={written}chosen.tsv. The other inputs are in the same folder."

    advised = advise_from_inspected_inputs(
        task, _decision(hypothesis_actions=list(MIXED_TIE)), root=tmp_path,
    )

    assert advised.advisory_recommendation is None
    assert not any("motif_file=" in value for value in advised.discovered_inputs)


def test_a_path_that_ends_a_sentence_still_names_its_folder(tmp_path):
    written = _folder(tmp_path, PANDA_SET)

    assert named_directories(f"All I have is {written}expression.tsv. Build a network.", tmp_path) == [
        (written, (tmp_path / "data" / "study").resolve()),
    ]


@pytest.mark.parametrize("actions", [MIXED_TIE, ["run_lioness_panda", "run_lioness_puma"]])
def test_selected_mixed_prior_with_decoys_recommends_the_matching_granularity(tmp_path, actions):
    written = _folder(tmp_path, {**CASE_5, "motif-panda.tsv": "motif-panda.tsv"})
    task = (f"My prior regulatory table ({written}prior.tsv) contains not only transcription "
            "factors but also predicted targets of some small RNAs; those small RNAs are "
            "listed in mirna.txt. Use the expression and PPI files in the same folder.")
    decision = _decision(hypothesis_actions=actions)

    advised = advise_from_inspected_inputs(task, decision, root=tmp_path)

    expected = "run_lioness_puma" if "run_lioness_puma" in actions else "run_puma"
    assert advised.advisory_recommendation.action == expected
    for field in AUTHORITY:
        assert getattr(advised, field) == getattr(decision, field), field
