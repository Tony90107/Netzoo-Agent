"""`request_mode` decided every live outcome and was the one field never checked.

Across 63 live trials, a case passed exactly when its request_mode came back as
`guidance`: 5/21 for Q1, 10/21 for Q2, 0/21 for Q3, with the pass count equal to
the guidance count every time. Every other semantic dimension has deterministic
validation and therefore a repair opportunity; this one was taken on trust.

The history case is the only prompt in the corpus that asks whether a *named*
method suits its data rather than which tool produces a result, and it has never
once been classified as guidance. It also opens by reporting a completed past
run, which must not read as an instruction to execute now.

These witnesses raise an issue for the reviewer. They never set the field.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import OutcomeHypothesis  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses  # noqa: E402
from netzoo_agent_core.interpretation.semantic_repair import repair_feedback  # noqa: E402

from evaluate_routing import DEFAULT_SCENARIOS, load_scenarios  # noqa: E402
from test_routing_evaluation import hypothesis  # noqa: E402


CORPUS = load_scenarios(DEFAULT_SCENARIOS)


def item():
    entry = hypothesis()
    for evidence in entry["evidence"]:
        evidence.update(source="inferred", text_span=None)
    return OutcomeHypothesis.model_validate(entry)


def issues(task, request_mode):
    return validate_outcome_hypotheses(task, [item()], request_mode=request_mode).issues


@pytest.mark.parametrize("case", CORPUS, ids=lambda case: case.id)
def test_every_corpus_prompt_is_a_guidance_request(case):
    """The corpus is guidance-only by construction, so none may claim otherwise."""
    assert "request_mode_conflict:guidance" in issues(case.prompt, "unknown")
    assert "request_mode_conflict:guidance" not in issues(case.prompt, "guidance")


@pytest.mark.parametrize("task", [
    "Please run SAMBAR on my mutation matrix now.",
    "幫我跑 PANDA，檔案都準備好了。",
    "Execute the LIONESS-PANDA pipeline on these files.",
    "現在請執行分群分析。",
])
def test_an_explicit_instruction_to_work_now_is_never_called_guidance(task):
    """The safety-relevant direction: never argue a work order into guidance."""
    assert "request_mode_conflict:guidance" not in issues(task, "execute")
    assert "request_mode_conflict:guidance" not in issues(task, "unknown")


@pytest.mark.parametrize("task", [
    "我剛剛成功用 RNA-Seq 資料跑完了 PANDA，效果很好！那我是不是也應該把突變矩陣丟進 PANDA？",
    "I already ran PANDA on the expression matrix. Should I feed it the mutation matrix too?",
])
def test_a_completed_past_run_is_not_an_instruction_to_execute(task):
    """The history case opens with a finished run; that is background, not an order."""
    assert "request_mode_conflict:guidance" in issues(task, "unknown")


@pytest.mark.parametrize("task", [
    "The weather is fine today.",
    "今天天氣不錯。",
    "Thanks, that was helpful.",
])
def test_a_request_with_no_scientific_question_is_left_alone(task):
    assert "request_mode_conflict:guidance" not in issues(task, "unknown")


def test_the_reviewer_is_told_where_and_why_to_correct_it():
    expected = repair_feedback(
        {"outcome_hypotheses": [hypothesis()]},
        ("request_mode_conflict:guidance",),
        next(case for case in CORPUS if case.id == "original-q3").prompt,
    )[0]["expected"]

    assert expected["action"] == "restore_request_mode"
    assert expected["review_path"] == "request_mode"
    assert expected["request_mode"] == "guidance"
    instruction = expected["instruction"].casefold()
    assert "explicit" in instruction
    assert "unknown" in instruction
