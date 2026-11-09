"""SPONGE executor: a human TF motif prior and a TF PPI prior (netzoopy-sponge, run-sponge)."""

from __future__ import annotations

import json
from typing import Any

from .command import _run_command
from .contracts import tool
from .data.paths import _resolve_user_path

__all__ = ["SPONGE_ARTIFACTS", "build_priors", "sponge_input_errors", "validate_sponge_output"]

SPONGE_ARTIFACTS = ("motif_prior.tsv", "ppi_prior.tsv", "manifest.json")
_HUMAN = {"", "human", "humans", "homo sapiens", "9606", "h. sapiens", "人類", "人类"}


def sponge_input_errors(decision: Any) -> list[str]:
    """What stops a SPONGE run before anything is downloaded (code-checked settings only)."""
    get = (lambda name: decision.get(name)) if isinstance(decision, dict) else (lambda name: getattr(decision, name, None))
    errors = []
    if str(get("taxon") or "").strip().casefold() not in _HUMAN:
        errors.append(f"SPONGE builds human priors only (hg38, hg19 or T2T-CHM13); the request names {get('taxon')}")
    upstream, downstream = get("promoter_upstream"), get("promoter_downstream")
    if upstream is not None and downstream is not None and upstream + downstream == 0:
        errors.append("the promoter window is empty (0 bp upstream and 0 bp downstream)")
    output_dir = get("output_dir")
    if output_dir and _resolve_user_path(output_dir).is_file():
        errors.append(f"output_dir is a file: {output_dir}")
    return errors


@tool
def build_priors(
    output_dir: str,
    sponge_tf_names: list[str] | None = None,
    jaspar_release: str = "",
    genome_assembly: str = "hg38",
    promoter_upstream: int = 750,
    promoter_downstream: int = 250,
    motif_score_threshold: int = 400,
    ppi_score_threshold: int = 400,
    n_cores: int = 1,
) -> str:
    """Run SPONGE with only declared settings; binding sites are downloaded one TF at a time."""
    errors = sponge_input_errors({"output_dir": output_dir, "promoter_upstream": promoter_upstream,
                                  "promoter_downstream": promoter_downstream})
    if errors:
        return "SPONGE input validation failed; no command was executed.\n\n" + "\n".join(f"  error: {e}" for e in errors)
    root = _resolve_user_path(output_dir)
    command = [
        "run-sponge", "-o", str(root), "--genome-assembly", genome_assembly,
        "--promoter-upstream", str(promoter_upstream), "--promoter-downstream", str(promoter_downstream),
        "--motif-score-threshold", str(motif_score_threshold), "--ppi-score-threshold", str(ppi_score_threshold),
        "--n-processes", str(n_cores),
    ]
    if sponge_tf_names:
        command += ["--tf-names", ",".join(sponge_tf_names)]
    if jaspar_release:
        command += ["--jaspar-release", jaspar_release]
    return _run_command(command, additional_output_files=[str(root / name) for name in SPONGE_ARTIFACTS])


def validate_sponge_output(output_dir: str) -> tuple[list[str], list[str], dict[str, Any]]:
    """The two priors exist, have three columns, and the manifest's counts."""
    root = _resolve_user_path(output_dir)
    errors: list[str] = []
    artifacts: list[str] = []
    metrics: dict[str, Any] = {}
    for name in ("motif_prior.tsv", "ppi_prior.tsv"):
        path = root / name
        if not path.is_file():
            errors.append(f"SPONGE output is missing: {path}")
            continue
        with path.open("r", encoding="utf-8") as handle:
            rows = [line.rstrip("\n").split("\t") for line in handle if line.strip()]
        if name == "motif_prior.tsv" and not rows:
            errors.append("SPONGE motif prior is empty")
        if any(len(row) != 3 for row in rows):
            errors.append(f"{name} must have three tab-separated columns")
        artifacts.append(str(path))
    try:
        summary = json.loads((root / "manifest.json").read_text(encoding="utf-8")).get("summary") or {}
        artifacts.append(str(root / "manifest.json"))
        metrics.update({f"sponge_{key}": value for key, value in summary.items()
                        if key in ("motif_edges", "motif_tfs", "target_genes", "ppi_edges")})
        if missing := summary.get("requested_tfs_without_motif_edges"):
            metrics["sponge_requested_tfs_without_motif_edges"] = missing
    except (OSError, ValueError) as error:
        errors.append(f"SPONGE manifest.json could not be read: {error}")
    return errors, artifacts, metrics
