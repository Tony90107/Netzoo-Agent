"""Request-scoped input selections shared by routing and planning.

Selection is independent of workflow names and content validity. A missing or
invalid selected file stays selected so preflight can report it; it never gives
discovery permission to substitute another dataset.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from collections.abc import Iterable

from ..settings import INPUT_ROLE_FIELDS, OUTPUT_ROLE_FIELDS, PROJECT_ROOT
from .discovery import _unlabeled_input_bindings
from .extraction import _task_path


@dataclass(frozen=True)
class RequestInputBindings:
    values: dict[str, str]
    explicit_fields: frozenset[str]
    resolved_fields: frozenset[str]
    directory: Path | None
    issues: tuple[str, ...] = ()


def request_input_bindings(
    task: str,
    fields: Iterable[str] = INPUT_ROLE_FIELDS,
    root: Path = PROJECT_ROOT,
) -> RequestInputBindings:
    """Preserve labelled paths before filename hints, and scope sibling names.

    Resolving a bare filename against a uniquely named input directory is a
    location inference, recorded separately from literal provided evidence.
    Existence is deliberately not required for the selected file.
    """
    fields = tuple(sorted(set(fields) & INPUT_ROLE_FIELDS))
    labelled = {field: value for field in INPUT_ROLE_FIELDS if (value := _task_path(task, field))}
    input_text = task
    for field in OUTPUT_ROLE_FIELDS:
        if output := _task_path(task, field):
            input_text = input_text.replace(output, " ")
    # A file already labelled as an input cannot simultaneously establish a
    # different role just because its filename happens to suggest one.
    hint_text = input_text
    for value in labelled.values():
        hint_text = hint_text.replace(value, " ")
    values = {
        **_unlabeled_input_bindings(hint_text, fields),
        **{field: value for field, value in labelled.items() if field in fields},
    }
    directories: set[Path] = set()
    for value in values.values():
        path = Path(value).expanduser()
        if path.is_absolute() or path.parent != Path("."):
            directories.add((path if path.is_absolute() else root / path).resolve().parent)
    # A folder-only request is also a valid anchor. Never use output locations.
    for token in re.findall(r"(?<![\w./~-])([\w./~-]+/)", input_text):
        candidate = (root / token).resolve()
        if candidate.is_dir() and not candidate.is_symlink():
            directories.add(candidate)
    directory = next(iter(directories)) if len(directories) == 1 else None
    resolved = set()
    same_folder = re.search(
        r"\bsame\s+(?:folder|directory)\b|同(?:一個|一|個)?(?:資料夾|目錄)", task, re.I,
    )
    sibling_fields = {
        field for field, value in values.items()
        if not Path(value).is_absolute() and Path(value).parent == Path(".")
    }
    if same_folder and len(directories) > 1 and sibling_fields:
        return RequestInputBindings(
            values, frozenset(labelled).intersection(fields), frozenset(), None,
            ("Multiple input directories were named. Please specify which directory "
             "contains these same-folder inputs: " + ", ".join(sorted(sibling_fields)) + ".",),
        )
    if directory is not None and same_folder:
        for field, value in values.items():
            path = Path(value)
            if not path.is_absolute() and path.parent == Path("."):
                selected = directory / path
                values[field] = (
                    str(selected.relative_to(root.resolve()))
                    if selected.is_relative_to(root.resolve()) else str(selected)
                )
                resolved.add(field)
    return RequestInputBindings(values, frozenset(labelled).intersection(fields), frozenset(resolved), directory)
