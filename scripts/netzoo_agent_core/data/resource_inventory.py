"""Bounded, read-only inventory of workspace resources."""

from __future__ import annotations

import os
import stat
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from workflow_registry import (
    ACTION_DEFINITIONS,
    ActionDefinition,
    DiscoverySpec,
    RecommendedAction,
)

from ..contracts.resources import (
    PartialResourceCandidate,
    ValidatedResourceBundle,
    WorkspaceResourceInventory,
)
from .resource_validators import RESOURCE_VALIDATORS, ResourceValidator


@dataclass(frozen=True, slots=True)
class InventoryLimits:
    max_depth: int = 4
    max_visited_files: int = 2_000
    max_candidate_groups: int = 100
    max_returned_paths: int = 200
    max_file_bytes: int = 10_000_000
    max_duration_seconds: float = 5.0


def _contained(path: Path, root: Path) -> bool:
    return path.resolve().is_relative_to(root.resolve())


def _uses_symlink(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return path.is_symlink()
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            return True
    return False


def _best_matching_path(
    files: Sequence[Path],
    hints: tuple[str, ...],
    allowed_extensions: frozenset[str],
) -> Path | None:
    folded_hints = tuple(hint.casefold() for hint in hints)
    candidates = [
        path
        for path in files
        if path.suffix.casefold() in allowed_extensions
        and any(hint in path.name.casefold() for hint in folded_hints)
    ]
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda path: (
            -sum(hint in path.name.casefold() for hint in folded_hints),
            len(path.name),
            path.name.casefold(),
            str(path),
        ),
    )


def _relative(path: Path, root: Path) -> str:
    rendered = path.resolve().relative_to(root).as_posix()
    return rendered or "."


def _expired(started: float, limits: InventoryLimits) -> bool:
    return time.monotonic() - started >= limits.max_duration_seconds


def inventory_workspace_resources(
    root: Path,
    actions: Sequence[RecommendedAction],
    *,
    definitions: Mapping[str, ActionDefinition] = ACTION_DEFINITIONS,
    validators: Mapping[str, ResourceValidator] = RESOURCE_VALIDATORS,
    explicit_inputs: Mapping[str, str] | None = None,
    limits: InventoryLimits = InventoryLimits(),
) -> WorkspaceResourceInventory:
    """Inventory complete and partial resource groups below ``root`` only."""
    search_root = root.expanduser().resolve()
    errors: list[str] = []
    rejected: Counter[str] = Counter()
    if not search_root.is_dir():
        return WorkspaceResourceInventory(
            scope_root=".",
            visited_file_count=0,
            rejected_summary={},
            errors=["workspace root is not a readable directory"],
        )

    action_specs: list[tuple[int, RecommendedAction, DiscoverySpec]] = []
    for order, action in enumerate(actions):
        definition = definitions.get(action)
        if definition is not None and definition.discovery is not None:
            action_specs.append((order, action, definition.discovery))

    active_extensions = {
        suffix.casefold()
        for _, _, spec in action_specs
        for suffix in spec.allowed_extensions
    }
    active_hints = {
        hint.casefold()
        for _, _, spec in action_specs
        for hints in spec.filename_hints.values()
        for hint in hints
    }
    started = time.monotonic()
    visited = 0
    truncated = False
    candidate_files: dict[Path, list[Path]] = {}
    stop = False

    for directory, child_names, filenames in os.walk(
        search_root, topdown=True, followlinks=False
    ):
        if _expired(started, limits):
            truncated = True
            break
        directory_path = Path(directory)
        if not _contained(directory_path, search_root):
            child_names.clear()
            rejected["outside_root"] += 1
            continue
        depth = len(directory_path.relative_to(search_root).parts)
        child_names[:] = sorted(
            child
            for child in child_names
            if not (directory_path / child).is_symlink()
        )
        if depth >= limits.max_depth:
            if child_names:
                truncated = True
            child_names.clear()

        files: list[Path] = []
        for filename in sorted(filenames):
            if _expired(started, limits):
                truncated = True
                stop = True
                break
            if visited >= limits.max_visited_files:
                truncated = True
                stop = True
                break
            visited += 1
            path = directory_path / filename
            if path.is_symlink():
                rejected["symlink"] += 1
                continue
            if not _contained(path, search_root):
                rejected["outside_root"] += 1
                continue
            if path.suffix.casefold() not in active_extensions:
                continue
            if not any(hint in filename.casefold() for hint in active_hints):
                continue
            try:
                metadata = path.stat()
            except OSError:
                rejected["unreadable"] += 1
                continue
            if not stat.S_ISREG(metadata.st_mode):
                rejected["not_regular_file"] += 1
                continue
            size = metadata.st_size
            if size > limits.max_file_bytes:
                rejected["too_large"] += 1
                truncated = True
                stop = True
                break
            try:
                with path.open("rb") as handle:
                    handle.read(1)
            except OSError:
                rejected["unreadable"] += 1
                continue
            files.append(path)
        if files:
            candidate_files[directory_path.resolve()] = files
        if stop:
            break

    explicit_paths: dict[str, Path] = {}
    explicit_parents: set[Path] = set()
    explicit_invalid = False
    for role, rendered in (explicit_inputs or {}).items():
        if _expired(started, limits):
            truncated = True
            explicit_invalid = True
            break
        path = Path(rendered).expanduser()
        if not path.is_absolute():
            path = search_root / path
        if _uses_symlink(path, search_root):
            rejected["symlink"] += 1
            explicit_invalid = True
            continue
        if not _contained(path, search_root):
            rejected["outside_root"] += 1
            explicit_invalid = True
            continue
        if path.suffix.casefold() not in active_extensions:
            rejected["disallowed_extension"] += 1
            explicit_invalid = True
            continue
        try:
            resolved = path.resolve(strict=True)
            metadata = resolved.stat()
            if not stat.S_ISREG(metadata.st_mode):
                rejected["not_regular_file"] += 1
                explicit_invalid = True
                continue
            size = metadata.st_size
            if size > limits.max_file_bytes:
                rejected["too_large"] += 1
                truncated = True
                explicit_invalid = True
                continue
            with resolved.open("rb") as handle:
                handle.read(1)
        except OSError:
            rejected["unreadable"] += 1
            explicit_invalid = True
            continue
        explicit_paths[role] = resolved
        explicit_parents.add(resolved.parent)

    if explicit_invalid:
        candidate_files.clear()
    elif len(explicit_parents) > 1:
        rejected["incoherent_explicit_inputs"] += 1
        candidate_files.clear()
    elif explicit_parents:
        anchor = next(iter(explicit_parents))
        candidate_files = {anchor: candidate_files.get(anchor, [])}

    complete: dict[
        tuple[tuple[str, str], ...],
        tuple[int, Path, dict[str, str], list[RecommendedAction], list[str]],
    ] = {}
    partials: list[tuple[int, PartialResourceCandidate]] = []
    group_count = 0
    returned_path_count = 0

    for directory in sorted(candidate_files, key=lambda item: _relative(item, search_root)):
        if _expired(started, limits):
            truncated = True
            break
        files = candidate_files[directory]
        for order, action, spec in action_specs:
            if _expired(started, limits):
                truncated = True
                stop = True
                break
            if group_count >= limits.max_candidate_groups:
                truncated = True
                stop = True
                break
            matched = {
                role: (
                    explicit_paths.get(role)
                    if explicit_paths.get(role) is not None
                    and explicit_paths[role].suffix.casefold()
                    in spec.allowed_extensions
                    else None
                )
                or _best_matching_path(
                    files,
                    spec.filename_hints[role],
                    spec.allowed_extensions,
                )
                for role in spec.input_roles
            }
            present = {role: path for role, path in matched.items() if path is not None}
            if not present:
                continue
            group_count += 1
            missing = [role for role in spec.input_roles if role not in present]
            rendered_inputs = {
                role: _relative(path, search_root) for role, path in present.items()
            }
            if missing:
                if (
                    returned_path_count + len(rendered_inputs)
                    > limits.max_returned_paths
                ):
                    truncated = True
                    stop = True
                    break
                partials.append(
                    (
                        order,
                        PartialResourceCandidate(
                            directory=_relative(directory, search_root),
                            action=action,
                            matched_inputs=rendered_inputs,
                            missing_inputs=missing,
                        ),
                    )
                )
                returned_path_count += len(rendered_inputs)
                continue

            absolute_values = {role: str(path) for role, path in present.items()}
            reasons: list[str] = []
            valid = True
            for validator_id in spec.validator_ids:
                if _expired(started, limits):
                    truncated = True
                    valid = False
                    stop = True
                    break
                validator = validators.get(validator_id)
                if validator is None:
                    rejected["validator_unavailable"] += 1
                    valid = False
                    break
                try:
                    accepted, reason = validator(absolute_values, spec)
                except Exception as exc:  # Validator adapters are a failure boundary.
                    rejected["validation_error"] += 1
                    if len(errors) < 20:
                        errors.append(f"validation failed: {type(exc).__name__}")
                    valid = False
                    break
                if _expired(started, limits):
                    truncated = True
                    valid = False
                    stop = True
                    break
                if not accepted:
                    rejected[reason or "validation_failed"] += 1
                    valid = False
                    break
                reasons.append(reason)
            if not valid:
                continue
            if not reasons:
                reasons.append("all declared validators passed")
            key = tuple(sorted(rendered_inputs.items()))
            existing = complete.get(key)
            if existing is None:
                if (
                    returned_path_count + len(rendered_inputs)
                    > limits.max_returned_paths
                ):
                    truncated = True
                    stop = True
                    break
                complete[key] = (
                    order,
                    directory,
                    rendered_inputs,
                    [action],
                    reasons,
                )
                returned_path_count += len(rendered_inputs)
            else:
                existing[3].append(action)
                for reason in reasons:
                    if reason not in existing[4]:
                        existing[4].append(reason)
        if stop:
            break

    bundles = [
        ValidatedResourceBundle(
            directory=_relative(directory, search_root),
            compatible_actions=compatible_actions,
            inputs=inputs,
            validation_reasons=reasons,
        )
        for _, directory, inputs, compatible_actions, reasons in sorted(
            complete.values(), key=lambda value: (value[0], _relative(value[1], search_root))
        )
    ]
    ordered_partials = [
        candidate
        for _, candidate in sorted(
            partials,
            key=lambda item: (
                item[0],
                item[1].directory,
                tuple(item[1].missing_inputs),
                tuple(item[1].matched_inputs.values()),
            ),
        )
    ]
    return WorkspaceResourceInventory(
        scope_root=".",
        visited_file_count=visited,
        truncated=truncated,
        validated_bundles=bundles,
        partial_candidates=ordered_partials,
        rejected_summary=dict(sorted(rejected.items())),
        errors=errors,
    )


__all__ = ["InventoryLimits", "inventory_workspace_resources"]
