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
from .discovery import _UNLABELED_PATH_RE, _unlabeled_input_bindings
from .extraction import _task_path

# M2 (2026-10-14): where the words put a path as a result's destination ("write the networks to x.npy", "save it as
# y.csv", "Outputs can go to /z"), it is not an input; `_task_path` recognises only labelled outputs.
_OUTPUT_LEAD = re.compile(
    r"(?:\b(?:write|writes|writing|written|save|saved|saving|store|stored|export|exported|put|output|outputs|"
    r"call|name)\b[^.;!?\n]{0,48}\b(?:to|as|into|in|at|go\s+to)\s*|\boutputs?\s*[:=]?\s*)$",
    re.I)
_DIRECTORY_TOKEN = re.compile(r"(?<![\w.~/-])((?:~|\.{1,2})?/?[\w.~-]+(?:/[\w.~-]+)+)/?(?![\w.~/-])")


@dataclass(frozen=True)
class RequestInputBindings:
    values: dict[str, str]
    explicit_fields: frozenset[str]
    resolved_fields: frozenset[str]
    directory: Path | None
    issues: tuple[str, ...] = ()
    named_paths: tuple[str, ...] = ()
    """M2: every input file the request names, bound to a role or not, in the order named."""
    missing_directories: tuple[str, ...] = ()
    """M2: folders the request names that do not exist (a24b P33 "/proj/mac/priors")."""


def _named_paths(text: str) -> tuple[str, ...]:
    """The file paths the words name as inputs: not where a result is to be written."""
    found = []
    for match in _UNLABELED_PATH_RE.finditer(text):
        token = match.group(1).strip().rstrip(".。")
        if _OUTPUT_LEAD.search(text[max(0, match.start() - 80):match.start()]):
            continue
        if token not in found:
            found.append(token)
    return tuple(found)


def _missing_directories(text: str, root: Path) -> tuple[str, ...]:
    """Folders the words name (absolute, home- or dot-relative, or two levels deep) that do not exist."""
    found = []
    for match in _DIRECTORY_TOKEN.finditer(text):
        token = match.group(1).rstrip(".")  # a folder at the end of a sentence
        if Path(token).suffix or _OUTPUT_LEAD.search(text[max(0, match.start() - 80):match.start()]):
            continue
        if not (token.startswith(("/", "~", ".")) or token.count("/") >= 2):
            continue
        path = Path(token).expanduser()
        if not (path if path.is_absolute() else root / path).exists() and token not in found:
            found.append(token)
    return tuple(found)


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
    named, missing = _named_paths(input_text), _missing_directories(input_text, root)
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
            named, missing,
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
    return RequestInputBindings(values, frozenset(labelled).intersection(fields), frozenset(resolved), directory,
                                named_paths=named, missing_directories=missing)


def bound_expression_samples(task: str, root: Path = PROJECT_ROOT) -> tuple[int, str] | None:
    """ROUND-07 (G3): (samples, path) of the expression file the request names, counted as preflight counts them
    (`data.inspection.expression_sample_count`); None when no expression file is bound, the binding is in doubt, or
    the file is missing or does not read as an expression matrix. A doubt about the sample count that this file
    answers is checked here instead of being asked."""
    from ..data.inspection import expression_sample_count

    bindings = request_input_bindings(task, ("expression_file",), root)
    value = bindings.values.get("expression_file")
    if not value or bindings.issues:
        return None
    path = Path(value).expanduser()
    path = path if path.is_absolute() else root / path
    if not path.is_file():
        return None
    try:
        count, _header = expression_sample_count(str(path))
    except Exception:  # noqa: BLE001 -- an unreadable file is preflight's to report, never a count
        return None
    return (count, value) if count > 0 else None
