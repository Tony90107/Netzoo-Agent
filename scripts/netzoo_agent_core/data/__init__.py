"""Workflow input, output, preparation, and artifact behavior."""

from . import (
    artifacts,
    bundles,
    cobra,
    coexpression,
    dragon,
    discovery,
    inspection,
    otter,
    paths,
    tables,
    transforms,
)

_DATA_IMPLEMENTATION_MODULES = (
    paths,
    discovery,
    tables,
    inspection,
    bundles,
    transforms,
    artifacts,
    cobra,
    coexpression,
    dragon,
    otter,
)

__all__: list[str] = []
