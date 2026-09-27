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
from ..interpretation.input_bindings import request_input_bindings
from ..settings import INPUT_ROLE_FIELDS, PROJECT_ROOT
from .context import record_event
from .mixed_prior import mirna_capable_candidate, mixed_prior_conditions, tf_only_counterpart

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
    """Directories the request names that exist inside the project root.

    A named file names its folder too (Log 186): "my prior (data/x/prior.tsv)
    ... the files in the same folder" points at `data/x/`.
    """
    base = root.resolve()
    found: dict[Path, str] = {}
    for written in dict.fromkeys(_PATH_TOKEN.findall(task)):
        if "/" not in written:
            continue
        candidate = (base / written).resolve()
        if not candidate.exists() and written.endswith("."):
            # A path that ends a sentence carries its full stop (Log 188).
            written = written.rstrip(".")
            candidate = (base / written).resolve()
        if candidate.is_file() and not candidate.is_symlink():
            written, candidate = written.rstrip("/").rsplit("/", 1)[0] + "/", candidate.parent
        if candidate == base or not candidate.is_relative_to(base):
            continue
        if candidate.is_dir():
            found.setdefault(candidate, written)
    return [(written, candidate) for candidate, written in found.items()]


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
    exclude: frozenset[Path] = frozenset(),
    *,
    bindings: dict[str, Path] | None = None,
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
    files = [path for path in files if path not in exclude]
    bindings = bindings or {}
    shapes = {path: _shape(path) for path in files}
    hinted = _unlabeled_input_bindings(" ".join(path.name for path in files), tuple(_ROLE_SHAPES))
    budget = _MAX_VALIDATIONS
    equipped: dict[str, dict[str, Path]] = {}
    for action in candidates:
        fields = [f for f in REQUIRED_INPUTS[action] if f in INPUT_ROLE_FIELDS]
        pools = [
            ([bindings[field]] if bindings[field] in files else [])
            if field in bindings else sorted(
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


def _selected_files_elsewhere(
    directory: Path,
    action: str,
    bindings: dict[str, Path],
) -> dict[str, Path]:
    """Selected files that content-validate only in a role nobody selected (Log 238).

    Case 10 names `expression.tsv` as the expression matrix, but by content it
    is the TF-motif prior. A selected role is never given another file
    (b670faa); only where the user's own file belongs is reported.
    """
    content = (equipped_candidates(directory, [action]) or {}).get(action, {})
    selected = set(bindings.values())
    return {
        field: path for field, path in content.items()
        if path in selected and field not in bindings
    }


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
    ):
        return decision
    selections = request_input_bindings(task, root=root)
    if selections.issues:
        return decision.model_copy(update={"clarification_question": " ".join(selections.issues)})
    bindings = {
        field: (root / value).resolve()
        for field, value in selections.values.items()
    }
    fields_by_action = {
        action: {f for f in REQUIRED_INPUTS[action] if f in INPUT_ROLE_FIELDS}
        for action in candidates
    }
    by_equipment = (
        set(candidates) <= _PANDA_FAMILY
        and len({frozenset(value) for value in fields_by_action.values()}) >= 2
    )
    mirna_action = mirna_capable_candidate(candidates, _PANDA_FAMILY)
    # Any tie with a PANDA-family member may also report which files in the
    # named folder validate by content, without recommending (Log 188).
    family = sorted(
        (action for action in candidates if action in _PANDA_FAMILY),
        key=lambda action: (len(fields_by_action[action]), action),
    )
    if not by_equipment and mirna_action is None and not family:
        return decision
    inspected: list[str] = []
    discovered: list[str] = []
    for written, directory in named_directories(task, root):
        inspected.append(written)
        if mirna_action is not None:
            mixed = (equipped_candidates(directory, [mirna_action], bindings=bindings) or {}).get(mirna_action, {})
            conditions = mixed_prior_conditions(mixed, written)
            counterpart = tf_only_counterpart(mirna_action, _PANDA_FAMILY)
            clean = (
                equipped_candidates(directory, [counterpart], frozenset({mixed["motif_file"]}), bindings=bindings)
                if conditions and counterpart is not None else None
            )
            if conditions and ("motif_file" in bindings or clean == {}):
                return decision.model_copy(update={
                    "advisory_recommendation": AdvisoryRecommendation(
                        action=mirna_action, conditions=conditions,
                    ),
                    "clarification_question": (
                        f"Should I use {_workflow_name(mirna_action)}, or does another listed "
                        "option fit your study better?"
                    ),
                    "inspected_directories": inspected,
                })
        equipped = equipped_candidates(directory, candidates, bindings=bindings) if by_equipment else None
        action, values = next(iter(equipped.items())) if equipped and len(equipped) == 1 else (None, {})
        missing = sorted(
            set().union(*fields_by_action.values()) - fields_by_action[action]
        ) if action is not None else []
        if not missing:
            if family:
                probe = (equipped_candidates(directory, family[:1], bindings=bindings) or {}).get(family[0], {})
                if not probe and bindings:
                    probe = _selected_files_elsewhere(directory, family[0], bindings)
                discovered.extend(f"{field}={written}{path.name}" for field, path in probe.items())
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
        return decision.model_copy(update={
            "inspected_directories": inspected, "discovered_inputs": discovered,
        })
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
