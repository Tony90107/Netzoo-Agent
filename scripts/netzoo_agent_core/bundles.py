"""Coherent autonomous dataset discovery for multi-file NetZoo workflows."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from workflow_registry import REQUIRED_INPUTS

from .contracts import INPUT_ROLE_FIELDS, _display_path
from .execution import _expression_sample_count
from .interpretation import _best_named_file, _candidate_keywords
from .validation import _inspect_panda_inputs_impl, _resolve_user_path

__all__ = [
    "BundleDiscovery",
    "discover_coherent_bundle",
]


MULTI_FILE_ACTIONS = frozenset(
    {
        "run_panda",
        "run_puma",
        "run_lioness_panda",
        "run_lioness_puma",
    }
)
MAX_DIRECTORY_DEPTH = 4
MAX_VISITED_FILES = 2_000


@dataclass(frozen=True, slots=True)
class BundleDiscovery:
    values: dict[str, str]
    bundle_id: str
    reason: str
    candidates_by_field: dict[str, list[str]]


def _candidate_directories(action: str, nearby: Path) -> list[Path]:
    root = nearby.expanduser().resolve()
    if root.is_file():
        root = root.parent
    keywords = {
        keyword
        for field_name in REQUIRED_INPUTS[action]
        if field_name in INPUT_ROLE_FIELDS
        for keyword in _candidate_keywords(action, field_name)
    }
    directories: set[Path] = set()
    visited = 0
    if not root.is_dir():
        return []
    for directory, child_directories, filenames in os.walk(
        root,
        topdown=True,
        followlinks=False,
    ):
        directory_path = Path(directory)
        depth = len(directory_path.relative_to(root).parts)
        child_directories[:] = sorted(
            child
            for child in child_directories
            if not (directory_path / child).is_symlink()
        )
        if depth >= MAX_DIRECTORY_DEPTH:
            child_directories.clear()
        for filename in filenames:
            visited += 1
            if visited > MAX_VISITED_FILES:
                break
            path = directory_path / filename
            if (
                path.is_file()
                and not path.is_symlink()
                and path.suffix.casefold() in {".tsv", ".tab", ".txt", ".csv"}
                and any(keyword in filename.casefold() for keyword in keywords)
            ):
                directories.add(directory_path.resolve())
        if visited > MAX_VISITED_FILES:
            break
    return sorted(directories, key=str)


def _bundle_in_directory(
    action: str,
    directory: Path,
    explicit_inputs: dict[str, str],
) -> BundleDiscovery | None:
    input_fields = [
        field_name
        for field_name in REQUIRED_INPUTS[action]
        if field_name in INPUT_ROLE_FIELDS
    ]
    values = dict(explicit_inputs)
    candidates_by_field: dict[str, list[str]] = {}
    for field_name in input_fields:
        if field_name in values:
            candidates_by_field[field_name] = [values[field_name]]
            continue
        keywords = _candidate_keywords(action, field_name)
        candidate = _best_named_file(directory, keywords)
        if candidate is None:
            return None
        rendered = _display_path(candidate)
        values[field_name] = rendered
        candidates_by_field[field_name] = [rendered]

    if set(values) != set(input_fields):
        return None
    _, valid, _ = _inspect_panda_inputs_impl(
        values["expression_file"],
        values["motif_file"],
        values["ppi_file"],
        values.get("mirna_file", ""),
    )
    if not valid:
        return None
    if "lioness" in action:
        sample_count, _ = _expression_sample_count(values["expression_file"])
        if sample_count < 3:
            return None

    resolved_directory = directory.resolve()
    return BundleDiscovery(
        values=values,
        bundle_id=f"directory:{resolved_directory}",
        reason=(
            "Selected one complete validated dataset bundle from "
            f"{resolved_directory}."
        ),
        candidates_by_field=candidates_by_field,
    )


def discover_coherent_bundle(
    action: str,
    nearby: Path,
    explicit_inputs: dict[str, str],
) -> BundleDiscovery | None:
    """Select exactly one complete compatible bundle, or decline to guess."""
    if action not in MULTI_FILE_ACTIONS:
        return None
    anchor_parents = {
        _resolve_user_path(value).parent.resolve()
        for value in explicit_inputs.values()
    }
    if len(anchor_parents) > 1:
        return None
    directories = (
        sorted(anchor_parents, key=str)
        if anchor_parents
        else _candidate_directories(action, nearby)
    )
    valid = [
        bundle
        for directory in directories
        if (
            bundle := _bundle_in_directory(
                action,
                directory,
                explicit_inputs,
            )
        )
    ]
    return valid[0] if len(valid) == 1 else None
