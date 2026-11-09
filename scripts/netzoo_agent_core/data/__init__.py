"""Workflow input, output, preparation, and artifact behavior."""

from . import (
    artifacts,
    bonobo,
    bundles,
    cobra,
    coexpression,
    dragon,
    discovery,
    inspection,
    sambar,
    porcupine,
    scorpion,
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
    sambar,
    porcupine,
    scorpion,
    bundles,
    transforms,
    artifacts,
    cobra,
    coexpression,
    dragon,
    otter,
    bonobo,
)

__all__: list[str] = []
