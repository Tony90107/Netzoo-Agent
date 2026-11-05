"""Strict, side-effect-free PORCUPINE input inspection."""

from __future__ import annotations

from typing import Any

from porcupine_io import DEFAULTS, MIN_SAMPLES, parameter_errors, read_gmt, read_sample_network, scan_sample_network

from .paths import _resolve_user_path

__all__ = ["inspect_porcupine_inputs_impl", "porcupine_gene_axes", "porcupine_parameters", "validate_porcupine_output"]


def porcupine_parameters(decision: Any | None) -> dict[str, Any]:
    """Declared PORCUPINE controls from a decision or dict; unset values take the verified defaults."""
    params = dict(DEFAULTS)
    if decision is None:
        return params
    for name in DEFAULTS:
        value = decision.get(name) if isinstance(decision, dict) else getattr(decision, name, None)
        if value is not None:
            params[name] = value
    return params


def porcupine_gene_axes(sample_network_file: str, pathway_file: str) -> list[tuple[list[str], str]]:
    """Identifier axes for the shared gene-namespace check (targets and GMT genes).

    Regulators are not checked: PORCUPINE matches pathways on target genes only, and a LIONESS-PUMA network's
    regulators include miRNAs (hsa-miR-21-5p), which a gene authority does not recognize.
    Only GMT genes that are network targets are checked: the others are dropped before any PCA, and a full
    Reactome or MSigDB file carries withdrawn or renamed symbols that would otherwise refuse the run. With no
    shared gene the whole GMT is checked, so a namespace mismatch is still named.
    """
    network = scan_sample_network(_resolve_user_path(sample_network_file))
    pathways, _ = read_gmt(_resolve_user_path(pathway_file))
    targets = set(network.targets)
    gmt_genes = {gene for genes in pathways.values() for gene in genes}
    return [
        (sorted(targets), "PORCUPINE network target genes"),
        (sorted(gmt_genes & targets or gmt_genes), "PORCUPINE pathway genes"),
    ]


def inspect_porcupine_inputs_impl(
    sample_network_file: str,
    pathway_file: str,
    decision: Any | None = None,
) -> tuple[str, bool]:
    """Validate the PORCUPINE network/GMT contract without writing files."""
    network_path = _resolve_user_path(sample_network_file)
    gmt_path = _resolve_user_path(pathway_file)
    params = porcupine_parameters(decision)
    lines = [
        "PORCUPINE input inspection:",
        f"- sample-specific network: {network_path}",
        f"- pathways: {gmt_path}",
        "  required network format: header tf/regulator, gene/target, [prior], <one column per sample>;"
        " rows are unique regulator->target edges (edges x samples)",
        "  required pathway format: GMT (pathway name, description, gene IDs; tab separated)",
    ]
    network = scan_sample_network(network_path)
    pathways, gmt_errors = read_gmt(gmt_path)
    errors = [*network.errors, *gmt_errors, *parameter_errors(params)]
    if not network.errors:
        samples = len(network.samples)
        lines.append(f"  network shape: {network.n_edges} edges x {samples} samples")
        lines.append(
            f"  regulators: {network.regulators.nunique()}, target genes: {network.targets.nunique()}"
        )
        if network.prior_column:
            lines.append(f"  prior column '{network.prior_column}' is an edge annotation and is not used as a sample")
        if samples < MIN_SAMPLES:
            errors.append(f"PORCUPINE needs at least {MIN_SAMPLES} samples for a stable PCA; got {samples}")
        if params["scale_data"] is True:
            constant = network.constant_edges
            if constant:
                lines.append(f"  {constant} edges are constant across samples and will be dropped before scaling")
    if not network.errors and not gmt_errors:
        targets = set(network.targets)
        overlap = {name: [gene for gene in genes if gene in targets] for name, genes in pathways.items()}
        low, high = params["min_pathway_size"], params["max_pathway_size"]
        testable = sum(1 for genes in overlap.values() if isinstance(low, int) and isinstance(high, int) and low <= len(genes) <= high)
        shared = {gene for genes in overlap.values() for gene in genes}
        lines.extend([
            f"  GMT pathways: {len(pathways)}",
            f"  GMT genes found among network targets: {len(shared)}",
            f"  pathways testable with {low} <= size <= {high}: {testable}",
        ])
        if not shared:
            errors.append(
                "no GMT gene is a network target gene; the GMT and network must use the same gene "
                "identifier namespace (e.g. both HGNC symbols or both Ensembl IDs)"
            )
        elif testable == 0:
            errors.append("no GMT pathway falls within min_pathway_size..max_pathway_size after matching network targets")
        else:
            # The null gene sets are drawn from the genes of every GMT pathway found in the network
            # (porcupine_run.R, as upstream pca_random). A pathway holding all of them makes every random
            # set equal to it, and PORCUPINE's t-test then stops ("data are essentially constant").
            whole = sorted(
                name for name, genes in overlap.items()
                if low <= len(genes) <= high and len(set(genes)) >= len(shared)
            )
            if whole:
                errors.append(
                    f"pathway {whole[0]} contains all {len(shared)} GMT genes found in the network, and PORCUPINE "
                    "draws its random comparison gene sets from those genes, so every random set would equal "
                    "this pathway and the test cannot run; give a GMT with more pathways (for example a full "
                    "Reactome or KEGG file)"
                )
    for error in dict.fromkeys(errors):
        lines.append(f"  error: {error}")
    return "\n".join(lines), not errors


PATHWAY_COLUMNS = (
    "pathway", "pathway_size", "n_edges", "pc1_variance_pct", "null_mean_pc1_variance_pct",
    "pvalue", "padj", "effect_size", "significant",
)
LOADING_COLUMNS = ("pathway", "regulator", "target", "pc1_loading", "pc2_loading")
NULL_COLUMNS = ("pathway_size", "n_edges", "pc1_variance_pct")


def validate_porcupine_output(
    output_dir: str, sample_network_file: str | None
) -> tuple[bool, list[str], list[str], dict[str, Any]]:
    """Check every PORCUPINE artifact's orientation, identifiers and values."""
    import json

    import numpy as np
    import pandas as pd

    root = _resolve_user_path(output_dir)
    names = {
        "pathways": root / "porcupine_pathways.tsv",
        "null": root / "porcupine_random_null.tsv",
        "scores": root / "porcupine_pc1_sample_scores.tsv",
        "loadings": root / "porcupine_edge_loadings.tsv",
        "manifest": root / "manifest.json",
    }
    artifacts = [str(path) for path in names.values()]
    errors: list[str] = []
    metrics: dict[str, Any] = {}
    frames: dict[str, pd.DataFrame] = {}
    for key, path in names.items():
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"PORCUPINE artifact is missing or empty: {path}")
            continue
        if key == "manifest":
            try:
                if json.loads(path.read_text(encoding="utf-8")).get("method") != "PORCUPINE":
                    errors.append("PORCUPINE manifest method must be PORCUPINE")
            except (OSError, ValueError) as error:
                errors.append(f"PORCUPINE manifest is malformed: {error}")
            continue
        try:
            frames[key] = pd.read_csv(path, sep="\t", dtype={"pathway": str, "regulator": str, "target": str})
        except (OSError, ValueError, pd.errors.ParserError) as error:
            errors.append(f"PORCUPINE {key} table could not be parsed as TSV: {error}")
    if errors:
        return False, errors, artifacts, metrics

    def numeric(frame: pd.DataFrame, columns: tuple[str, ...], label: str) -> None:
        values = frame[list(columns)].apply(pd.to_numeric, errors="coerce")
        if values.isna().any().any() or not np.isfinite(values.to_numpy(dtype=float)).all():
            errors.append(f"PORCUPINE {label} values must be finite numbers: {', '.join(columns)}")

    stats = frames["pathways"]
    if tuple(stats.columns) != PATHWAY_COLUMNS:
        errors.append("PORCUPINE pathway table columns must be: " + ", ".join(PATHWAY_COLUMNS))
    else:
        if stats.empty or stats["pathway"].duplicated().any():
            errors.append("PORCUPINE pathway table must have one row per unique tested pathway")
        numeric(stats, PATHWAY_COLUMNS[1:8], "pathway statistics")
        for column in ("pvalue", "padj"):
            values = pd.to_numeric(stats[column], errors="coerce")
            if ((values < 0) | (values > 1)).any():
                errors.append(f"PORCUPINE {column} must lie in [0, 1]")
        flags = stats["significant"].astype(str).str.upper()
        if not flags.isin({"TRUE", "FALSE"}).all():
            errors.append("PORCUPINE significant column must be TRUE or FALSE")
        metrics["porcupine_pathways_tested"] = int(stats.shape[0])
        metrics["porcupine_significant_pathways"] = int((flags == "TRUE").sum())
    null = frames["null"]
    if tuple(null.columns) != NULL_COLUMNS or null.empty:
        errors.append("PORCUPINE random null table columns must be: " + ", ".join(NULL_COLUMNS))
    else:
        numeric(null, NULL_COLUMNS, "random null")
        metrics["porcupine_random_sets"] = int(null.shape[0])
    scores = frames["scores"]
    if scores.columns[0] != "pathway" or scores.shape[1] < 2:
        errors.append("PORCUPINE PC1 sample scores must have a pathway column followed by one column per sample")
    else:
        numeric(scores, tuple(scores.columns[1:]), "PC1 sample scores")
        if "pathway" in stats and set(scores["pathway"]) != set(stats["pathway"]):
            errors.append("PORCUPINE PC1 score rows must be exactly the tested pathways")
        if sample_network_file:
            expected = read_sample_network(_resolve_user_path(sample_network_file), nrows=1).samples
            if expected and [str(name) for name in scores.columns[1:]] != expected:
                errors.append("PORCUPINE PC1 score columns must be the input network's samples in the same order")
        metrics["porcupine_score_samples"] = int(scores.shape[1] - 1)
    loadings = frames["loadings"]
    if tuple(loadings.columns) != LOADING_COLUMNS:
        errors.append("PORCUPINE edge loadings columns must be: " + ", ".join(LOADING_COLUMNS))
    elif not loadings.empty:
        numeric(loadings, ("pc1_loading", "pc2_loading"), "edge loadings")
        if "significant" in stats:
            significant = set(stats.loc[stats["significant"].astype(str).str.upper() == "TRUE", "pathway"])
            if not set(loadings["pathway"]) <= significant:
                errors.append("PORCUPINE edge loadings may only cover significant pathways")
        metrics["porcupine_loading_rows"] = int(loadings.shape[0])
    return not errors, errors, artifacts, metrics
