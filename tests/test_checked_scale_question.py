"""checked-scale-question-2026-10-28: routing's scale question is dropped when the check read a scale for every
result it credited."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.graph.condition_recommender import SCALE_QUESTION, checked_scale_question  # noqa: E402


def test_dropped_when_every_credited_result_states_a_scale():
    assert checked_scale_question(SCALE_QUESTION, ["whole_cohort", "whole_cohort"]) is None
    assert checked_scale_question(f"Which priors do you have? {SCALE_QUESTION}", ["per_sample"]) == \
        "Which priors do you have?"


def test_kept_when_a_scale_is_unstated_or_nothing_is_credited():
    assert checked_scale_question(SCALE_QUESTION, ["whole_cohort", "unstated"]) == SCALE_QUESTION
    assert checked_scale_question(SCALE_QUESTION, []) == SCALE_QUESTION
    assert checked_scale_question("Which priors do you have?", ["per_sample"]) == "Which priors do you have?"
    assert checked_scale_question(None, ["per_sample"]) is None
