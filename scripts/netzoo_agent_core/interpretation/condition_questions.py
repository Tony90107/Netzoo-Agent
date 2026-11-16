"""The study conditions that separate candidate workflows, and the question that asks them.

Moved out of ``graph.condition_recommender`` (2026-11-16) so the core decision can ask the same question of methods a
request names, without the interpretation layer importing the graph layer. Everything here reads the registry alone.
"""

from __future__ import annotations

from dataclasses import dataclass

from workflow_registry import ACTION_DEFINITIONS, OUTPUT_CAPABILITIES, SELECTION_AXES

__all__ = ["ConditionOption", "condition_options", "separating_question"]

_MAX_QUESTIONS = 2
_DEFAULT_LINE = " If none of these applies: "

@dataclass(frozen=True, slots=True)
class ConditionOption:
    axis: str
    value: str
    label: str
    actions: tuple[str, ...]

    @property
    def condition(self) -> str:
        return f"{self.axis}:{self.value}"


def _workflow_name(action: str) -> str:
    definition = ACTION_DEFINITIONS.get(action)
    return definition.workflow if definition is not None else action


def condition_options(candidates: list[str]) -> list[ConditionOption]:
    """Conditions that separate the candidates, in axis order.

    A single-valued axis ("the network is large") separates when some but not
    all candidates are preferred under it. A multi-valued axis separates only
    when every candidate declares a value on it: a candidate silent on the axis
    is equally suitable under any value, so "no covariates" does not favour
    LIONESS over BONOBO even though LIONESS declares it.
    """
    preferring: dict[str, list[str]] = {}
    declared_axes: dict[str, set[str]] = {}
    for action in candidates:
        capability = OUTPUT_CAPABILITIES.get(action)
        for condition in (capability.prefer_when if capability else ()):
            preferring.setdefault(condition, []).append(action)
            declared_axes.setdefault(condition.partition(":")[0], set()).add(action)
    options = []
    for axis, spec in SELECTION_AXES.items():
        multi_valued = len(spec["values"]) > 1
        if multi_valued and declared_axes.get(axis, set()) != set(candidates):
            continue
        for value, label in spec["values"].items():
            actions = preferring.get(f"{axis}:{value}", [])
            if 0 < len(actions) < len(candidates):
                options.append(ConditionOption(axis, value, label, tuple(actions)))
    return options


def separating_question(
    options: list[ConditionOption],
    candidates: list[str] | None = None,
) -> str:
    """Form B: ask the study facts that separate the candidates, not method names."""
    questions = []
    covered: set[str] = set()
    for axis in dict.fromkeys(option.axis for option in options):
        axis_options = [option for option in options if option.axis == axis]
        single_valued = len(SELECTION_AXES[axis]["values"]) == 1
        answers = "; ".join(
            ("yes" if single_valued else option.label)
            + " → " + ", ".join(_workflow_name(a) for a in option.actions)
            for option in axis_options
        )
        covered.update(a for option in axis_options for a in option.actions)
        questions.append(f"{SELECTION_AXES[axis]['question']} ({answers})")
        if len(questions) == _MAX_QUESTIONS:
            break
    numbered = " ".join(f"({index}) {text}" for index, text in enumerate(questions, 1))
    lead = "Both fit" if candidates is not None and len(candidates) == 2 else "These all fit"
    text = f"{lead}; to choose, tell me: {numbered}"
    uncovered = [a for a in (candidates or []) if a not in covered]
    if uncovered:
        text += _DEFAULT_LINE + ", ".join(_workflow_name(a) for a in uncovered) + "."
    return text
