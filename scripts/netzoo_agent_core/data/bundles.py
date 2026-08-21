"""Coherent autonomous dataset discovery for multi-file NetZoo workflows."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from workflow_registry import REQUIRED_INPUTS

from ..presentation import _display_path
from ..settings import INPUT_ROLE_FIELDS
from .discovery import best_named_file, candidate_keywords
from .inspection import expression_sample_count as _expression_sample_count
from .paths import _resolve_user_path
from .tables import _inspect_panda_inputs_impl

__all__ = [
    "BundleDiscovery",
    "discover_bundle_candidates",
    "discover_coherent_bundles",
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
    missing_fields: tuple[str, ...] = ()


def _candidate_directories(action: str, nearby: Path) -> list[Path]:
    root = nearby.expanduser().resolve()
    if root.is_file():
        root = root.parent
    keywords = {
        keyword
        for field_name in REQUIRED_INPUTS[action]
        if field_name in INPUT_ROLE_FIELDS
        for keyword in candidate_keywords(action, field_name)
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
        keywords = candidate_keywords(action, field_name)
        candidate = best_named_file(directory, keywords)
        if candidate is None:
            continue
        rendered = _display_path(candidate)
        values[field_name] = rendered
        candidates_by_field[field_name] = [rendered]

    missing_fields = tuple(
        field_name for field_name in input_fields if field_name not in values
    )
    resolved_directory = directory.resolve()
    if missing_fields:
        if "lioness" in action and values.get("expression_file"):
            sample_count, _ = _expression_sample_count(values["expression_file"])
            if sample_count < 3:
                return None
        return BundleDiscovery(
            values=values,
            bundle_id=f"directory:{resolved_directory}",
            reason=(
                f"Found a partial input bundle in {resolved_directory}; missing "
                + ", ".join(missing_fields)
                + "."
            ),
            candidates_by_field=candidates_by_field,
            missing_fields=missing_fields,
        )
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

    return BundleDiscovery(
        values=values,
        bundle_id=f"directory:{resolved_directory}",
        reason=(
            f"Selected one complete validated dataset bundle from {resolved_directory}."
        ),
        candidates_by_field=candidates_by_field,
    )


def discover_coherent_bundle(
    action: str,
    nearby: Path,
    explicit_inputs: dict[str, str],
) -> BundleDiscovery | None:
    """Select exactly one complete compatible bundle, or decline to guess."""
    valid = discover_coherent_bundles(action, nearby, explicit_inputs)
    return valid[0] if len(valid) == 1 else None


def discover_coherent_bundles(
    action: str,
    nearby: Path,
    explicit_inputs: dict[str, str],
) -> list[BundleDiscovery]:
    """Return all complete compatible bundles for an interactive choice list."""
    return [
        bundle
        for bundle in discover_bundle_candidates(action, nearby, explicit_inputs)
        if not bundle.missing_fields
    ]


def discover_bundle_candidates(
    action: str,
    nearby: Path,
    explicit_inputs: dict[str, str],
) -> list[BundleDiscovery]:
    """Return coherent complete and partial bundles without mixing directories."""
    if action not in MULTI_FILE_ACTIONS:
        return []
    anchor_parents = {
        _resolve_user_path(value).parent.resolve() for value in explicit_inputs.values()
    }
    if len(anchor_parents) > 1:
        return []
    directories = (
        sorted(anchor_parents, key=str)
        if anchor_parents
        else _candidate_directories(action, nearby)
    )
    candidates = [
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
    return sorted(
        candidates,
        key=lambda item: (len(item.missing_fields), item.bundle_id),
    )
