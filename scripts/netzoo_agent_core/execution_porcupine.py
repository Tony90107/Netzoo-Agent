"""PORCUPINE executors: pathway-level PCA over sample-specific networks (R package, run-porcupine)."""

from __future__ import annotations

from .command import _run_command
from .data.paths import _resolve_user_path
from .data.porcupine import inspect_porcupine_inputs_impl
from .contracts import tool

__all__ = ["PORCUPINE_ARTIFACTS", "inspect_porcupine_inputs", "run_porcupine"]


@tool
def inspect_porcupine_inputs(
    sample_network_file: str,
    pathway_file: str,
    min_pathway_size: int = 5,
    max_pathway_size: int = 150,
    scale_data: bool = True,
) -> str:
    """Inspect a sample-specific network table and GMT before a PORCUPINE run."""
    report, _ = inspect_porcupine_inputs_impl(
        sample_network_file, pathway_file,
        {"min_pathway_size": min_pathway_size, "max_pathway_size": max_pathway_size, "scale_data": scale_data},
    )
    return report


PORCUPINE_ARTIFACTS = (
    "porcupine_pathways.tsv",
    "porcupine_random_null.tsv",
    "porcupine_pc1_sample_scores.tsv",
    "porcupine_edge_loadings.tsv",
    "manifest.json",
)


@tool
def run_porcupine(
    sample_network_file: str,
    pathway_file: str,
    output_dir: str,
    min_pathway_size: int = 5,
    max_pathway_size: int = 150,
    n_permutations: int = 1000,
    n_cores: int = 1,
    scale_data: bool = True,
    fdr_threshold: float = 0.05,
    min_effect_size: float = 2.0,
    seed: int = 1,
) -> str:
    """Run PORCUPINE (R) using only declared, validated registry parameters."""
    params = {
        "min_pathway_size": min_pathway_size, "max_pathway_size": max_pathway_size,
        "n_permutations": n_permutations, "n_cores": n_cores, "scale_data": scale_data,
        "fdr_threshold": fdr_threshold,
        "min_effect_size": min_effect_size, "seed": seed,
    }
    inspection, ok = inspect_porcupine_inputs_impl(sample_network_file, pathway_file, params)
    if not ok:
        return "PORCUPINE input validation failed; no command was executed.\n\n" + inspection
    root = _resolve_user_path(output_dir)
    inputs = {_resolve_user_path(path) for path in (sample_network_file, pathway_file)}
    outputs = [root / name for name in PORCUPINE_ARTIFACTS]
    collision = next((path for path in outputs if path in inputs), None)
    if collision is not None:
        return "PORCUPINE input validation failed; no command was executed.\n\n  error: output would overwrite input: " + str(collision)
    command = [
        "run-porcupine", "-n", sample_network_file, "-p", pathway_file, "-o", str(root),
        "--min-pathway-size", str(min_pathway_size), "--max-pathway-size", str(max_pathway_size),
        "--n-permutations", str(n_permutations), "--n-cores", str(n_cores),
        "--scale-data", str(scale_data).lower(),
        "--fdr-threshold", str(fdr_threshold), "--min-effect-size", str(min_effect_size),
        "--seed", str(seed),
    ]
    return inspection + "\n\n" + _run_command(command, additional_output_files=[str(path) for path in outputs])
