"""Advisory choice among tied workflows from a folder the user named (Log 152).

When a request names a local folder and the tied candidates differ in the
priors they require, the folder's file names can say which candidate the user
is equipped to run: a folder with a TF-motif and a PPI prior but no miRNA list
fits LIONESS-PANDA rather than LIONESS-PUMA.

Bounds, all deliberate:

- Only a directory the request names, inside the project root, is listed;
  nothing is followed outside it and nothing is recursed into.
- Only file names are read, never contents; roles come from the same filename
  hints the request parser already uses, and content validation stays
  authoritative at planning time.
- A missing file is not evidence the user lacks it. The open-world rule stands:
  no candidate is eliminated, and the result is an advisory recommendation
  with no execution authority, which the user confirms or overrides.
"""

from __future__ import annotations

import re
from pathlib import Path

from workflow_registry import ACTION_DEFINITIONS, OUTPUT_CAPABILITIES

from ..contracts import TaskDecision
from ..contracts.outcomes import AdvisoryCondition, AdvisoryRecommendation
from ..interpretation.discovery import _unlabeled_input_bindings
from ..settings import PROJECT_ROOT
from .context import record_event

__all__ = [
    "INSPECTED_AXIS",
    "PRIOR_LABELS",
    "advise_from_inspected_inputs",
    "invoke_input_inspection",
    "named_directories",
    "present_priors",
]

INSPECTED_AXIS = "inspected_inputs"
PRIOR_LABELS = {
    "motif_prior": "TF-motif prior",
    "ppi_prior": "protein-interaction prior",
    "mirna_prior": "miRNA list",
}
_PRIOR_BY_FIELD = {
    "motif_file": "motif_prior",
    "ppi_file": "ppi_prior",
    "mirna_file": "mirna_prior",
}
_MAX_ENTRIES = 200
_PATH_TOKEN = re.compile(r"(?<![\w./~-])((?:\./)?[\w.-]+(?:/[\w.-]+)*/?)")


def named_directories(task: str, root: Path = PROJECT_ROOT) -> list[tuple[str, Path]]:
    """Directories the request names that exist inside the project root."""
    base = root.resolve()
    found: list[tuple[str, Path]] = []
    for written in dict.fromkeys(_PATH_TOKEN.findall(task)):
        if "/" not in written:
            continue
        candidate = (base / written).resolve()
        if candidate == base or not candidate.is_relative_to(base):
            continue
        if candidate.is_dir():
            found.append((written, candidate))
    return found


def present_priors(directory: Path) -> set[str]:
    """Registry prior names whose filename hint appears in the directory listing."""
    names = sorted(
        entry.name for entry in directory.iterdir() if entry.is_file()
    )[:_MAX_ENTRIES]
    bindings = _unlabeled_input_bindings(" ".join(names), tuple(_PRIOR_BY_FIELD))
    return {_PRIOR_BY_FIELD[field] for field in bindings}


def _workflow_name(action: str) -> str:
    definition = ACTION_DEFINITIONS.get(action)
    return definition.workflow if definition is not None else action


def advise_from_inspected_inputs(
    task: str,
    decision: TaskDecision,
    root: Path = PROJECT_ROOT,
) -> TaskDecision:
    """Recommend the one tied candidate whose required priors the folder holds."""
    candidates = list(decision.hypothesis_actions)
    if (
        decision.capability_match_status != "ambiguous"
        or len(candidates) < 2
        or decision.advisory_recommendation is not None
    ):
        return decision
    required = {
        action: set(OUTPUT_CAPABILITIES[action].required_input_artifacts)
        for action in candidates if action in OUTPUT_CAPABILITIES
    }
    if len({frozenset(value) for value in required.values()}) < 2:
        return decision
    for written, directory in named_directories(task, root):
        present = present_priors(directory)
        satisfied = [action for action, needs in required.items() if needs <= present]
        if len(satisfied) != 1:
            continue
        action = satisfied[0]
        missing = sorted(
            {need for needs in required.values() for need in needs} - present
        )
        if not missing:
            continue
        recommendation = AdvisoryRecommendation(
            action=action,
            conditions=[
                AdvisoryCondition(axis=INSPECTED_AXIS, value=f"missing:{need}", text_span=written)
                for need in missing
            ],
        )
        missing_labels = " or ".join(PRIOR_LABELS.get(need, need) for need in missing)
        return decision.model_copy(update={
            "advisory_recommendation": recommendation,
            "clarification_question": (
                f"Should I use {_workflow_name(action)}, or do you also have a "
                f"{missing_labels} elsewhere?"
            ),
        })
    return decision


def invoke_input_inspection(context, state, user_task: str, decision: TaskDecision) -> TaskDecision:
    """Graph entry point: advise from a named folder and record what was advised."""
    advised = advise_from_inspected_inputs(user_task, decision)
    if advised is not decision:
        record_event(context, state, "routing.inspected_inputs_recommended", "classify", {
            "recommended_action": advised.advisory_recommendation.action,
            "conditions": [item.model_dump() for item in advised.advisory_recommendation.conditions],
            "candidate_actions": list(decision.hypothesis_actions),
        })
    return advised
