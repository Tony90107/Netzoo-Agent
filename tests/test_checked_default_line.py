"""checked-default-line-2026-10-28: the tie question's default line keeps only check-credited workflows."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.graph.condition_recommender import checked_default_line  # noqa: E402

QUESTION = ("These all fit; to choose, tell me: (1) Is the network large enough that memory or runtime is a concern? "
            "(yes → OTTER) If none of these applies: PANDA, LIONESS-PANDA.")


def test_an_uncredited_workflow_leaves_the_line():
    assert checked_default_line(QUESTION, {"PANDA", "OTTER", "GIRAFFE"}).endswith("If none of these applies: PANDA.")
    assert checked_default_line(QUESTION, {"LIONESS-PANDA"}).endswith("If none of these applies: LIONESS-PANDA.")


def test_the_line_is_dropped_when_nothing_on_it_is_credited():
    assert checked_default_line(QUESTION, {"OTTER"}) == QUESTION.split(" If none")[0]


def test_unchanged_without_credited_results_or_without_the_line():
    assert checked_default_line(QUESTION, set()) == QUESTION
    assert checked_default_line("Which of the listed options fits your study?", {"PANDA"}) == \
        "Which of the listed options fits your study?"
    assert checked_default_line(QUESTION, {"PANDA", "LIONESS-PANDA"}) == QUESTION
