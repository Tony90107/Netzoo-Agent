"""answered-counts-2026-10-29: a count the user answered is applied even when the turn's re-reading drops the doubt
(ad1 j6 X22); a wait still settles as before; several credited results are left alone."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from test_count_alternatives import KEY  # noqa: E402
from test_request_facts import _check  # noqa: E402
from test_method_conditions import _ask  # noqa: E402

from netzoo_agent_core.contracts.task_state import TaskFact, TaskState  # noqa: E402
from netzoo_agent_core.interpretation.task_answers import answered_check  # noqa: E402

TASK = ("We have 100 breast tumors with 400 transcript features and a metabolite panel measured on the same tumors, "
        "and we want LIONESS-DRAGON networks for every tumor. I don't know yet whether the metabolomics core used "
        "their 150-metabolite panel or their 400-metabolite panel.")
DOUBT = "I don't know yet whether the metabolomics core used their 150-metabolite panel or their 400-metabolite panel."


def _reread():  # turn 2's reading: the doubt is gone, the row is available on the 400 transcripts alone
    return _check(TASK, _ask("we want LIONESS-DRAGON networks for every tumor", [KEY], samples=100,
                             samples_quote="100 breast tumors", omics_layers=2, scale="per_sample",
                             features=[(400, "400 transcript features")]))


def _state(value, what="feature_count"):
    return TaskState(task_id="t", facts=[TaskFact(
        question_id=f"count:{what}:x", source="count", what=what, question="Which of these is right: 150 or 400?",
        user_quote=DOUBT, options={"150": [KEY], "400": []}, value=value,
        answer_quote=f"It was the {value}-metabolite panel.", turn=1)])


def test_an_answered_feature_count_reaches_the_size_check_without_the_doubt():
    (before,) = _reread().results()
    assert before.status == "available"
    (row,) = answered_check(_reread(), _state("400"), TASK).results()
    assert row.status == "not_available" and row.method["features"] == 800
    assert any("31,960,000" in limit for limit in row.limits)
    assert any('You answered "It was the 400-metabolite panel."' in limit for limit in row.limits)
    (fits,) = answered_check(_reread(), _state("150"), TASK).results()
    assert fits.status == "available" and fits.method["features"] == 550


def test_a_waiting_row_still_settles_and_several_results_are_left_alone():
    from test_feature_count_doubts import _doubt

    waiting = _check(TASK, _ask("we want LIONESS-DRAGON networks for every tumor", [KEY], samples=100,
                                samples_quote="100 breast tumors", omics_layers=2, scale="per_sample",
                                features=[(400, "400 transcript features")]),
                     unknown_facts=[_doubt(DOUBT.rstrip("."), (150, 400), about="omics_layers")])
    (row,) = answered_check(waiting, _state("400").model_copy(update={"facts": [
        _state("400").facts[0].model_copy(update={"question_id": "count:feature_count:y"})]}), TASK).results()
    assert row.status == "not_available"
    two = _check(TASK, _ask("we want LIONESS-DRAGON networks for every tumor", [KEY], samples=100,
                            samples_quote="100 breast tumors", omics_layers=2, scale="per_sample",
                            features=[(400, "400 transcript features")]),
                 _ask("We have 100 breast tumors", ["dragon.two_layer_network"], samples=100,
                      samples_quote="100 breast tumors", omics_layers=2))
    assert len([r for r in two.results() if r.delivered_by]) == 2
    assert answered_check(two, _state("400"), TASK) is two


def test_a_corrected_answer_is_used_never_the_superseded_one():
    """jev-guard review: P3 keeps a corrected answer as superseded; only the known one refits."""
    old = _state("400").facts[0].model_copy(update={"status": "superseded"})
    new = _state("150").facts[0]
    (row,) = answered_check(_reread(), TaskState(task_id="t", facts=[old, new]), TASK).results()
    assert row.status == "available" and row.method["features"] == 550


def test_the_refusal_line_is_the_code_limit_with_both_numbers_and_the_answer():
    (row,) = answered_check(_reread(), _state("400"), TASK).results()
    limit = next(line for line in row.limits if "LIONESS-DRAGON writes at most" in line)
    assert "20,000,000" in limit and "31,960,000" in limit
    assert row.limits[-1] == 'You answered "It was the 400-metabolite panel." to "Which of these is right: 150 or 400?".'
