"""Validator contracts for specification-driven workspace resource discovery."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TypeAlias

from workflow_registry import DiscoverySpec


ResourceValidator: TypeAlias = Callable[
    [Mapping[str, str], DiscoverySpec], tuple[bool, str]
]
ValidatorMap: TypeAlias = Mapping[str, ResourceValidator]

# Production adapters are installed by the workflow-integration layer. Keeping the
# engine's default map here avoids coupling traversal to any workflow implementation.
RESOURCE_VALIDATORS: ValidatorMap = {}

__all__ = ["RESOURCE_VALIDATORS", "ResourceValidator", "ValidatorMap"]
