"""Validated GIRAFFE toy-bundle discovery."""

from __future__ import annotations

from pathlib import Path

from ..data.giraffe import inspect_giraffe_inputs_impl
from ..contracts import _display_path


def discover_giraffe_demo_bundle(data_root: Path) -> tuple[dict[str, str], str] | None:
    paths = {
        key: data_root / "giraffe-toy" / filename
        for key, filename in (
            ("expression_file", "expression.tsv"),
            ("motif_file", "motif.tsv"),
            ("ppi_file", "ppi.tsv"),
        )
    }
    _, ok = inspect_giraffe_inputs_impl(*(str(path) for path in paths.values()))
    if not ok:
        return None
    return (
        {key: _display_path(path) for key, path in paths.items()},
        "Demo intent: selected the GIRAFFE toy expression, TF-gene prior, and TF-TF PPI bundle after exact labelled-matrix validation.",
    )


def validate_giraffe_episode_inputs(values: dict[str, str]) -> bool:
    _, ok = inspect_giraffe_inputs_impl(
        values["expression_file"], values["motif_file"], values["ppi_file"]
    )
    return ok
