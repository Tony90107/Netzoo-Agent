"""SCORPION executors: single-cell PANDA networks per group of cells (R package, run-scorpion)."""

from __future__ import annotations

from .command import _run_command
from .contracts import tool
from .data.paths import _resolve_user_path
from .data.scorpion import (
    SCORPION_CELLS, SCORPION_DIFFERENTIAL, SCORPION_NETWORKS, inspect_scorpion_inputs_impl,
)

__all__ = ["inspect_scorpion_inputs", "run_scorpion"]


@tool
def inspect_scorpion_inputs(
    cell_expression_file: str,
    motif_file: str,
    ppi_file: str,
    cell_metadata_file: str = "",
    group_by: list[str] | None = None,
    compare_by: str = "",
    group1: str = "",
    group2: str = "",
    paired: bool = False,
    min_cells: int = 30,
) -> str:
    """Inspect single-cell expression, priors and cell metadata before a SCORPION run."""
    report, _ = inspect_scorpion_inputs_impl(cell_expression_file, motif_file, ppi_file, {
        "cell_metadata_file": cell_metadata_file, "group_by": group_by or [], "compare_by": compare_by,
        "group1": group1, "group2": group2, "paired": paired, "min_cells": min_cells,
    })
    return report


@tool
def run_scorpion(
    cell_expression_file: str,
    motif_file: str,
    ppi_file: str,
    output_dir: str,
    cell_metadata_file: str = "",
    group_by: list[str] | None = None,
    compare_by: str = "",
    group1: str = "",
    group2: str = "",
    paired: bool = False,
    normalize_data: bool = True,
    gamma_value: float = 10.0,
    n_pc: int = 25,
    assoc_method: str = "pearson",
    alpha_value: float = 0.1,
    min_cells: int = 30,
    z_scaling: bool = True,
    n_cores: int = 1,
    seed: int = 1,
) -> str:
    """Run SCORPION (R) using only declared, validated registry parameters."""
    group_by = list(group_by or [])
    params = {
        "cell_metadata_file": cell_metadata_file, "group_by": group_by, "compare_by": compare_by,
        "group1": group1, "group2": group2, "paired": paired, "normalize_data": normalize_data,
        "gamma_value": gamma_value, "n_pc": n_pc, "assoc_method": assoc_method, "alpha_value": alpha_value,
        "min_cells": min_cells, "z_scaling": z_scaling, "n_cores": n_cores,
    }
    inspection, ok = inspect_scorpion_inputs_impl(cell_expression_file, motif_file, ppi_file, params)
    if not ok:
        return "SCORPION input validation failed; no command was executed.\n\n" + inspection
    root = _resolve_user_path(output_dir)
    names = [SCORPION_NETWORKS, SCORPION_CELLS, *([SCORPION_DIFFERENTIAL] if compare_by else []), "manifest.json"]
    outputs = [root / name for name in names]
    inputs = {_resolve_user_path(path) for path in (cell_expression_file, motif_file, ppi_file, cell_metadata_file)
              if path}
    collision = next((path for path in outputs if path in inputs), None)
    if collision is not None:
        return ("SCORPION input validation failed; no command was executed.\n\n  error: output would overwrite input: "
                + str(collision))
    command = [
        "run-scorpion", "-e", cell_expression_file, "-m", motif_file, "-p", ppi_file, "-o", str(root),
        "--normalize-data", str(normalize_data).lower(), "--gamma-value", str(gamma_value), "--n-pc", str(n_pc),
        "--assoc-method", assoc_method, "--alpha-value", str(alpha_value), "--min-cells", str(min_cells),
        "--z-scaling", str(z_scaling).lower(), "--n-cores", str(n_cores), "--seed", str(seed),
    ]
    if group_by:
        command += ["--cell-metadata", cell_metadata_file, "--group-by", ",".join(group_by)]
    if compare_by:
        command += ["--compare-by", compare_by, "--group1", group1, "--group2", group2,
                    "--paired", str(paired).lower()]
    return inspection + "\n\n" + _run_command(command, additional_output_files=[str(path) for path in outputs])
