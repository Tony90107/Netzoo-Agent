"""SAMBAR executors (moved verbatim from execution.py to keep that module reviewable)."""

from __future__ import annotations

from .command import _run_command
from .data.paths import _resolve_user_path
from .data.sambar import inspect_sambar_inputs_impl
from .contracts import tool

__all__ = ["inspect_sambar_inputs", "run_sambar"]


@tool
def inspect_sambar_inputs(
    mutation_file: str,
    exon_size_file: str,
    cancer_gene_file: str,
    pathway_file: str,
    kmin: int = 2,
    kmax: int = 4,
    cluster: bool = True,
) -> str:
    """Inspect SAMBAR files before a subtype-analysis run."""
    report, _ = inspect_sambar_inputs_impl(
        mutation_file, exon_size_file, cancer_gene_file, pathway_file,
        {"kmin": kmin, "kmax": kmax, "cluster": cluster},
    )
    return report


@tool
def run_sambar(
    mutation_file: str,
    exon_size_file: str,
    cancer_gene_file: str,
    pathway_file: str,
    output_dir: str,
    norm_patient: bool = True,
    kmin: int = 2,
    kmax: int = 4,
    gmt_msigdb: bool = True,
    subset_cancer_genes: bool = True,
    distance: str = "binomial",
    linkage: str = "complete",
    cluster: bool = True,
) -> str:
    """Run SAMBAR using only declared, validated registry parameters."""
    inspection, ok = inspect_sambar_inputs_impl(
        mutation_file, exon_size_file, cancer_gene_file, pathway_file,
        {"norm_patient": norm_patient, "kmin": kmin, "kmax": kmax,
         "gmt_msigdb": gmt_msigdb, "subset_cancer_genes": subset_cancer_genes,
         "distance": distance, "linkage": linkage, "cluster": cluster},
    )
    if not ok:
        return "SAMBAR input validation failed; no command was executed.\n\n" + inspection
    root = _resolve_user_path(output_dir)
    inputs = {_resolve_user_path(path) for path in (mutation_file, exon_size_file, cancer_gene_file, pathway_file)}
    outputs = [root / "mt_out.csv", root / "pt_out.csv", root / "manifest.json"]
    if cluster:
        outputs.extend([root / "clustergroups.csv", root / "dist_matrix.csv"])
    collision = next((path for path in outputs if path in inputs), None)
    if collision is not None:
        return "SAMBAR input validation failed; no command was executed.\n\n  error: output would overwrite input: " + str(collision)
    command = [
        "run-sambar", "-m", mutation_file, "-e", exon_size_file, "-g", cancer_gene_file,
        "-p", pathway_file, "-o", str(root), "--kmin", str(kmin), "--kmax", str(kmax),
        "--distance", distance, "--linkage", linkage,
    ]
    if not norm_patient:
        command.append("--no-norm-patient")
    if not gmt_msigdb:
        command.append("--no-gmt-msigdb")
    if not subset_cancer_genes:
        command.append("--no-subset-cancer-genes")
    if not cluster:
        command.append("--no-cluster")
    return inspection + "\n\n" + _run_command(command, additional_output_files=[str(path) for path in outputs])
