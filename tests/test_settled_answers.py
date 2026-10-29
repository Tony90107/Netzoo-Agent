"""settled-answers-2026-10-29: a reply already bound to a form or count answer is no new stated condition for the
model condition check (j6 X06)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.task_state import TaskFact, TaskState  # noqa: E402
from netzoo_agent_core.interpretation.task_answers import without_settled  # noqa: E402

REPLY = "Every TF and every gene should end up in exactly one module, no sharing between modules."


def _state(source="dimension"):
    return TaskState(task_id="t", facts=[TaskFact(
        question_id="dimension:group_membership:x", source=source, what="group_membership",
        question="Should each gene, regulator or sample belong to one group only?", value="one_group",
        answer_quote=REPLY, turn=1)])


def test_a_condition_repeating_a_bound_form_answer_is_left_out():
    other = "Please save the communities as a CSV file."
    assert without_settled([REPLY, other], _state()) == [other]
    assert without_settled([REPLY.rstrip(".")], _state("count")) == []


def test_without_a_settled_answer_nothing_changes():
    assert without_settled([REPLY], None) == [REPLY]
    assert without_settled([REPLY], _state("agent")) == [REPLY]  # an agent yes/no is not settled in code
