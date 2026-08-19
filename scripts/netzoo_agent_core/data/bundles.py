"""Coherent autonomous dataset discovery for multi-file NetZoo workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from workflow_registry import ACTION_DEFINITIONS, DISCOVERABLE_ACTIONS

from ..presentation import _display_path
from .paths import _resolve_user_path
from .resource_inventory import inventory_workspace_resources

__all__ = [
    "BundleDiscovery",
    "discover_coherent_bundle",
]


MULTI_FILE_ACTIONS = frozenset(
    action
    for action in DISCOVERABLE_ACTIONS
    if len(ACTION_DEFINITIONS[action].discovery.input_roles) > 1
)


@dataclass(frozen=True, slots=True)
class BundleDiscovery:
    values: dict[str, str]
    bundle_id: str
    reason: str
    candidates_by_field: dict[str, list[str]]


def discover_coherent_bundle(
    action: str,
    nearby: Path,
    explicit_inputs: dict[str, str],
) -> BundleDiscovery | None:
    """Select exactly one complete compatible bundle, or decline to guess."""
    if action not in MULTI_FILE_ACTIONS:
        return None
    inventory_root = nearby.expanduser()
    if inventory_root.is_file():
        inventory_root = inventory_root.parent
    normalized_inputs = {
        role: (
            value
            if Path(value).expanduser().is_absolute()
            else str(_resolve_user_path(value))
        )
        for role, value in explicit_inputs.items()
    }
    explicit_parents = {
        path.parent
        for value in normalized_inputs.values()
        if (path := Path(value).expanduser()).is_absolute()
    }
    if (
        len(explicit_parents) == 1
        and next(iter(explicit_parents)).resolve() == inventory_root.resolve()
    ):
        inventory_root = next(iter(explicit_parents))
    inventory = inventory_workspace_resources(
        inventory_root,
        [action],
        explicit_inputs=normalized_inputs,
    )
    compatible = [
        bundle
        for bundle in inventory.validated_bundles
        if action in bundle.compatible_actions
    ]
    if len(compatible) != 1:
        return None
    selected = compatible[0]
    root = inventory_root.resolve()
    values = {
        role: _display_path((root / relative_path).resolve())
        for role, relative_path in selected.inputs.items()
    }
    directory = (root / selected.directory).resolve()
    return BundleDiscovery(
        values=values,
        bundle_id=f"directory:{directory}",
        reason=selected.validation_reasons[0],
        candidates_by_field={key: [value] for key, value in values.items()},
    )
