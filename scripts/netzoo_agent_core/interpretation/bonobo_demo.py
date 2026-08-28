"""Validated BONOBO toy-bundle discovery."""

from __future__ import annotations

from pathlib import Path

from ..contracts import _display_path
from ..data.bonobo import inspect_bonobo_inputs_impl

__all__ = ["discover_bonobo_demo_bundle"]


def discover_bonobo_demo_bundle(data_root: Path) -> tuple[dict[str, str], str] | None:
    expression = data_root / "bonobo-toy" / "expression.tsv"
    _, ok = inspect_bonobo_inputs_impl(
        str(expression), log_transformed=True, centered=True
    )
    if not ok:
        return None
    return (
        {"expression_file": _display_path(expression)},
        "Demo intent: selected the BONOBO toy expression matrix after gene-by-sample, preprocessing, and sample-count validation.",
    )
