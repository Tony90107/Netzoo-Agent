"""Advisory choice among tied workflows from a folder the user named.

When a request names a local folder and the tied candidates differ in the
inputs they require, the folder's *contents* can say which candidate the user
is equipped to run: a folder whose files validate as an expression matrix, a
TF-motif prior and a PPI prior, but none as a miRNA list, fits LIONESS-PANDA
rather than LIONESS-PUMA.

Contents decide, not names (Log 154). Each tied candidate counts as equipped
only if some assignment of the folder's files to its input roles passes that
workflow's own content validator -- the same check preflight runs before
execution. A file called `mirna.txt` that is not a miRNA list does not count;
a miRNA list called `list_04.dat` does. Filename hints only order the search.

Bounds, all deliberate:

- Only a directory the request names, inside the project root; nothing is
  followed outside it and nothing is recursed into.
- At most 12 regular, non-hidden, non-symlink files of at most 20 MB, a 64 KB
  preview per file to shortlist roles, and at most 40 validator calls.
- A file that validates nowhere is not evidence the user lacks one. The
  open-world rule stands: no candidate is eliminated, and the result is an
  advisory recommendation with no execution authority.
"""

from __future__ import annotations

import itertools
import re
from pathlib import Path

from workflow_registry import ACTION_DEFINITIONS, REQUIRED_INPUTS

from ..contracts import TaskDecision
from ..contracts.outcomes import AdvisoryCondition, AdvisoryRecommendation
from ..data.inspection import expression_sample_count
from ..data.tables import _inspect_panda_inputs_impl
from ..interpretation.discovery import _unlabeled_input_bindings
from ..settings import INPUT_ROLE_FIELDS, PROJECT_ROOT
from .context import record_event

__all__ = [
    "INSPECTED_AXIS",
    "advise_from_inspected_inputs",
    "equipped_candidates",
    "invoke_input_inspection",
    "named_directories",
]

INSPECTED_AXIS = "inspected_inputs"
_PANDA_FAMILY = frozenset({"run_panda", "run_puma", "run_lioness_panda", "run_lioness_puma"})
_ROLE_SHAPES = {
    "expression_file": "matrix",
    "motif_file": "edges",
    "ppi_file": "edges",
    "mirna_file": "list",
}
_MAX_FILES = 12
_MAX_BYTES = 20 * 1024 * 1024
_PREVIEW_BYTES = 64 * 1024
_MAX_VALIDATIONS = 40
_PATH_TOKEN = re.compile(r"(?<![\w./~-])((?:\./)?[\w.-]+(?:/[\w.-]+)*/?)")
_NUMBER = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$")


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


def _shape(path: Path) -> str | None:
    """A cheap content shortlist: matrix, edges or list, from a bounded preview."""
    try:
        with path.open("r", encoding="utf-8", errors="strict") as handle:
            lines = [line.rstrip("\r\n") for line in handle.read(_PREVIEW_BYTES).splitlines()]
    except (OSError, UnicodeDecodeError):
        return None
    rows = [
        re.split(r"\t|,", line) for line in lines
        if line.strip() and not line.startswith("#")
    ][:50]
    if not rows:
        return None
    widths = [len(row) for row in rows]
    width = max(set(widths), key=widths.count)
    if width == 1:
        return "list"
    body = [row for row in rows[1:] if len(row) == width] or rows
    numeric = max(sum(bool(_NUMBER.match(cell.strip())) for cell in row[1:]) for row in body)
    if width >= 3 and numeric >= 2:
        return "matrix"
    return "edges" if width in (2, 3) else None


def _candidate_files(directory: Path) -> list[Path] | None:
    files = [
        entry for entry in sorted(directory.iterdir())
        if entry.is_file() and not entry.is_symlink() and not entry.name.startswith(".")
    ]
    if len(files) > _MAX_FILES:
        return None
    return [entry for entry in files if entry.stat().st_size <= _MAX_BYTES]


def _validates(action: str, values: dict[str, Path]) -> bool:
    try:
        _, valid, _ = _inspect_panda_inputs_impl(
            str(values["expression_file"]),
            str(values["motif_file"]),
            str(values["ppi_file"]),
            str(values["mirna_file"]) if "mirna_file" in values else "",
            check_gene_authority=False,
        )
        if valid and "lioness" in action:
            samples, _ = expression_sample_count(str(values["expression_file"]))
            valid = samples >= 3
    except Exception:
        return False
    return bool(valid)


def equipped_candidates(
    directory: Path,
    candidates: list[str],
) -> dict[str, dict[str, Path]] | None:
    """Candidates whose inputs some file assignment content-validates, with that assignment.

    Returns None when the folder is outside the bounds or a candidate is not a
    PANDA-family workflow, so nothing can be concluded.
    """
    if not set(candidates) <= _PANDA_FAMILY:
        return None
    files = _candidate_files(directory)
    if not files:
        return None
    shapes = {path: _shape(path) for path in files}
    hinted = _unlabeled_input_bindings(" ".join(path.name for path in files), tuple(_ROLE_SHAPES))
    budget = _MAX_VALIDATIONS
    equipped: dict[str, dict[str, Path]] = {}
    for action in candidates:
        fields = [f for f in REQUIRED_INPUTS[action] if f in INPUT_ROLE_FIELDS]
        pools = [
            sorted(
                (path for path in files if shapes[path] == _ROLE_SHAPES[field]),
                # Names only order the search: a hinted file is tried first.
                key=lambda path, field=field: (hinted.get(field) != path.name, path.name),
            )
            for field in fields
        ]
        for assignment in itertools.product(*pools):
            if len(set(assignment)) != len(assignment):
                continue
            if budget <= 0:
                return None
            budget -= 1
            values = dict(zip(fields, assignment))
            if _validates(action, values):
                equipped[action] = values
                break
    return equipped


def _workflow_name(action: str) -> str:
    definition = ACTION_DEFINITIONS.get(action)
    return definition.workflow if definition is not None else action


def advise_from_inspected_inputs(
    task: str,
    decision: TaskDecision,
    root: Path = PROJECT_ROOT,
) -> TaskDecision:
    """Recommend the one tied candidate whose inputs the named folder content-validates."""
    candidates = list(decision.hypothesis_actions)
    if (
        decision.capability_match_status != "ambiguous"
        or len(candidates) < 2
        or decision.advisory_recommendation is not None
        or not set(candidates) <= _PANDA_FAMILY
    ):
        return decision
    fields_by_action = {
        action: {f for f in REQUIRED_INPUTS[action] if f in INPUT_ROLE_FIELDS}
        for action in candidates
    }
    if len({frozenset(value) for value in fields_by_action.values()}) < 2:
        return decision
    inspected: list[str] = []
    for written, directory in named_directories(task, root):
        inspected.append(written)
        equipped = equipped_candidates(directory, candidates)
        if not equipped or len(equipped) != 1:
            continue
        action, values = next(iter(equipped.items()))
        missing = sorted(
            set().union(*fields_by_action.values()) - fields_by_action[action]
        )
        if not missing:
            continue
        conditions = [
            AdvisoryCondition(axis=INSPECTED_AXIS, value=f"validated:{field}={path.name}", text_span=written)
            for field, path in values.items()
        ] + [
            AdvisoryCondition(axis=INSPECTED_AXIS, value=f"missing:{field}", text_span=written)
            for field in missing
        ]
        missing_labels = " or ".join(_ROLE_LABELS.get(field, field) for field in missing)
        return decision.model_copy(update={
            "advisory_recommendation": AdvisoryRecommendation(action=action, conditions=conditions),
            "clarification_question": (
                f"Should I use {_workflow_name(action)}, or do you also have a "
                f"{missing_labels} elsewhere?"
            ),
            "inspected_directories": inspected,
        })
    if inspected:
        return decision.model_copy(update={"inspected_directories": inspected})
    return decision


_ROLE_LABELS = {
    "expression_file": "expression matrix",
    "motif_file": "TF-motif prior",
    "ppi_file": "protein-interaction prior",
    "mirna_file": "miRNA list",
}


def invoke_input_inspection(context, state, user_task: str, decision: TaskDecision) -> TaskDecision:
    """Graph entry point: advise from a named folder and record what was read."""
    advised = advise_from_inspected_inputs(user_task, decision)
    if advised.inspected_directories:
        record_event(context, state, "routing.inspected_inputs_read", "classify", {
            "directories": list(advised.inspected_directories),
            "recommended_action": (
                advised.advisory_recommendation.action
                if advised.advisory_recommendation is not None
                and advised.advisory_recommendation is not decision.advisory_recommendation
                else None
            ),
            "conditions": (
                [item.model_dump() for item in advised.advisory_recommendation.conditions]
                if advised.advisory_recommendation is not None
                and advised.advisory_recommendation is not decision.advisory_recommendation
                else []
            ),
            "candidate_actions": list(decision.hypothesis_actions),
        })
    return advised
