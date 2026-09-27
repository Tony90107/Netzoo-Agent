"""Ask which reading the user means, in the readings' own terms (Log 188).

Divergent readings (Log 150) differ in *what* is produced, and the generic
question "What artifact should NetZoo produce?" named none of them. Case 4's
two readings were one TF-gene network per sample and TF activity per sample:
the choice the user is asked to make. Each reading is phrased from the
ontology's description of its artifact, its granularity when the artifact
permits more than one, and the registered workflows it leads to.
"""

from __future__ import annotations

from collections.abc import Sequence

from workflow_registry import ACTION_DEFINITIONS

from ..contracts.artifact_semantics import ARTIFACT_SEMANTICS

__all__ = ["reading_question"]

_GRANULARITY = {"aggregate": "one cohort-wide result", "sample_specific": "one result per sample"}
_LIMIT = 300


def _reading(outcome, actions: Sequence[str]) -> str:
    rule = ARTIFACT_SEMANTICS.get(outcome.artifact_type)
    text = (
        rule.description[:1].lower() + rule.description[1:] if rule is not None
        else outcome.artifact_type.replace("_", " ")
    )
    several = rule is None or rule.granularities is None or len(rule.granularities) > 1
    if several and outcome.granularity in _GRANULARITY:
        text += f", {_GRANULARITY[outcome.granularity]}"
    names = " or ".join(
        ACTION_DEFINITIONS[action].workflow if action in ACTION_DEFINITIONS else action
        for action in actions
    )
    return f"{text} ({names})"


def reading_question(readings: Sequence[tuple[object, Sequence[str]]]) -> str | None:
    """One question naming each (outcome, workflows) reading, or None if it does not fit."""
    parts = list(dict.fromkeys(_reading(outcome, actions) for outcome, actions in readings))
    if len(parts) < 2:
        return None
    question = "Which result do you mean: " + "; or ".join(parts) + "?"
    return question if len(question) <= _LIMIT else None
