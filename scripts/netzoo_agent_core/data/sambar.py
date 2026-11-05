"""Strict, side-effect-free SAMBAR input inspection."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .paths import _resolve_user_path

__all__ = ["inspect_sambar_inputs_impl"]


def _read_csv(path: str, label: str) -> tuple[pd.DataFrame | None, list[str]]:
    resolved = _resolve_user_path(path)
    if not resolved.is_file():
        return None, [f"{label} must be an existing regular file: {resolved}"]
    try:
        frame = pd.read_csv(resolved, index_col=0)
    except (OSError, ValueError, pd.errors.ParserError) as error:
        return None, [f"{label} must be a readable CSV with a first-column identifier: {error}"]
    if frame.empty or frame.shape[1] == 0:
        return None, [f"{label} must contain a first-column identifier and at least one data column"]
    if (frame.index.astype(str).str.strip() == "").any() or frame.index.duplicated().any():
        return None, [f"{label} first-column identifiers must be non-empty and unique"]
    return frame, []


def _read_cancer_genes(path: str) -> tuple[set[str], list[str]]:
    resolved = _resolve_user_path(path)
    if not resolved.is_file():
        return set(), [f"cancer_gene_file must be an existing regular file: {resolved}"]
    try:
        lines = [line.strip() for line in resolved.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError as error:
        return set(), [f"cancer_gene_file could not be read: {error}"]
    if len(lines) != 1:
        return set(), ["cancer_gene_file must contain exactly one non-empty tab-delimited line, matching the installed SAMBAR reader"]
    genes = {value.strip() for value in lines[0].split("\t") if value.strip()}
    return genes, [] if genes else ["cancer_gene_file contains no gene identifiers"]


def _read_gmt(path: str) -> tuple[set[str], int, list[str]]:
    resolved = _resolve_user_path(path)
    if not resolved.is_file():
        return set(), 0, [f"pathway_file must be an existing regular file: {resolved}"]
    genes: set[str] = set()
    pathways = 0
    errors: list[str] = []
    try:
        lines = resolved.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        return set(), 0, [f"pathway_file could not be read: {error}"]
    for line_number, raw in enumerate(lines, 1):
        if not raw.strip():
            continue
        fields = [value.strip() for value in raw.split("\t")]
        if len(fields) < 3 or not fields[0] or not any(fields[2:]):
            errors.append(f"pathway_file line {line_number} must be GMT: pathway name, description, and at least one gene")
            continue
        pathways += 1
        genes.update(value for value in fields[2:] if value)
    if pathways == 0 and not errors:
        errors.append("pathway_file contains no GMT pathways")
    return genes, pathways, errors


def kmax_sample_error(kmax, samples: int) -> str | None:
    """Clustering tries up to kmax subtypes, so it needs at least kmax samples (M2: shared with the check)."""
    if isinstance(kmax, int) and not isinstance(kmax, bool) and samples < kmax:
        return "kmax cannot exceed the number of mutation samples when clustering is enabled"
    return None


def _parameter_errors(decision: Any) -> list[str]:
    def value(name: str, default: Any) -> Any:
        return (
            decision.get(name, default)
            if isinstance(decision, dict)
            else getattr(decision, name, default)
        )

    kmin, kmax = value("kmin", 2), value("kmax", 4)
    errors: list[str] = []
    if not isinstance(kmin, int) or isinstance(kmin, bool) or kmin < 2:
        errors.append("kmin must be an integer of at least 2")
    if not isinstance(kmax, int) or isinstance(kmax, bool) or kmax < 2:
        errors.append("kmax must be an integer of at least 2")
    if not errors and kmax < kmin:
        errors.append("kmax must be greater than or equal to kmin")
    for name, default in (("distance", "binomial"), ("linkage", "complete")):
        item = value(name, default)
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{name} must be a non-empty scipy distance/linkage name")
    return errors


#: Below either bound the four-way gene overlap is reported as small (a warning, not an error).
SAMBAR_MIN_OVERLAP_GENES = 50
SAMBAR_MIN_OVERLAP_FRACTION = 0.10


def _decision_value(decision: Any, name: str, default: Any) -> Any:
    if decision is None:
        return default
    return decision.get(name, default) if isinstance(decision, dict) else getattr(decision, name, default)


def _dropped_samples_warning(mutation: pd.DataFrame, genes: list[str], reason: str) -> str | None:
    """A warning naming the samples netZooPy SAMBAR drops because they have no mutation in `genes`, or None.

    Upstream ``corgenelength`` drops samples with no mutation in the scored genes (mutation genes with an exon size,
    restricted to cancer genes unless ``subcangenes`` is off) before any per-patient normalization, and
    ``desparsify`` drops samples whose pathway scores are all zero. Both happen without notice, so the samples are
    named here.
    """
    columns = [column for column in mutation.columns if str(column).strip() in set(genes)]
    numeric = mutation[columns].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    zero = [str(sample) for sample in numeric.index[(numeric == 0).all(axis=1)]]
    if not zero:
        return None
    return (
        f"  warning: {len(zero)} of {mutation.shape[0]} samples have no mutations in {reason}: "
        + ", ".join(zero[:5])
        + (f" (and {len(zero) - 5} more)" if len(zero) > 5 else "")
        + "; netZooPy SAMBAR drops them, so they will be missing from every output"
    )


def inspect_sambar_inputs_impl(
    mutation_file: str,
    exon_size_file: str,
    cancer_gene_file: str,
    pathway_file: str,
    decision: Any | None = None,
) -> tuple[str, bool]:
    """Validate the installed netZooPy SAMBAR file contract without writing files."""
    lines = [
        "SAMBAR input inspection:",
        f"- mutation: {_resolve_user_path(mutation_file)}",
        f"- exon size: {_resolve_user_path(exon_size_file)}",
        f"- cancer genes: {_resolve_user_path(cancer_gene_file)}",
        f"- pathways: {_resolve_user_path(pathway_file)}",
        "  required mutation format: CSV with samples as rows and genes as columns",
    ]
    mutation, mutation_errors = _read_csv(mutation_file, "mutation_file")
    lengths, length_errors = _read_csv(exon_size_file, "exon_size_file")
    cancer_genes, cancer_errors = _read_cancer_genes(cancer_gene_file)
    pathway_genes, pathway_count, pathway_errors = _read_gmt(pathway_file)
    errors = [*mutation_errors, *length_errors, *cancer_errors, *pathway_errors]
    if mutation is not None:
        numeric = mutation.apply(pd.to_numeric, errors="coerce")
        if numeric.isna().any().any() or (numeric < 0).any().any():
            errors.append("mutation_file values must all be non-negative numeric mutation values")
        if (mutation.columns.astype(str).str.strip() == "").any() or mutation.columns.duplicated().any():
            errors.append("mutation_file gene columns must be non-empty and unique")
    if lengths is not None:
        # The pinned implementation uses ``esize.iloc[0]`` and intersects genes
        # with ``esize.columns``. Its actual contract is therefore a one-row CSV
        # with gene IDs as columns, despite the higher-level API wording.
        if lengths.shape[0] != 1:
            errors.append("exon_size_file must have exactly one data row with gene IDs as CSV columns, matching the installed SAMBAR implementation")
        values = lengths.iloc[0].apply(pd.to_numeric, errors="coerce")
        if values.isna().any() or (values <= 0).any():
            errors.append("exon_size_file lengths must all be positive numeric values")
        if (lengths.columns.astype(str).str.strip() == "").any() or lengths.columns.duplicated().any():
            errors.append("exon_size_file gene columns must be non-empty and unique")
    if mutation is not None and lengths is not None:
        mutation_genes = set(mutation.columns.astype(str).str.strip())
        length_genes = set(lengths.columns.astype(str).str.strip())
        common = mutation_genes & length_genes & cancer_genes & pathway_genes
        if not common:
            errors.append("no identifier is shared by mutation genes, exon sizes, cancer-gene list, and GMT pathways")
        lines.extend([
            f"  mutation shape: {mutation.shape[0]} samples x {mutation.shape[1]} genes",
            f"  exon-size genes: {len(length_genes)}",
            f"  cancer genes: {len(cancer_genes)}",
            f"  GMT pathways: {pathway_count}",
            f"  four-way identifier overlap: {len(common)} genes",
        ])
        subset = bool(_decision_value(decision, "subset_cancer_genes", True))
        candidates = mutation_genes & cancer_genes if subset else mutation_genes
        # Whole-exome mutations against a cancer-gene list overlap little by design, so the share is taken of the
        # mutation genes SAMBAR can score at all, not of every mutation gene.
        if common and candidates and (
            len(common) < SAMBAR_MIN_OVERLAP_GENES or len(common) < SAMBAR_MIN_OVERLAP_FRACTION * len(candidates)
        ):
            lines.append(
                f"  warning: only {len(common)} genes are shared by all four inputs, out of "
                f"{len(candidates)} {'mutation genes in the cancer-gene list' if subset else 'mutation genes'} "
                f"(fewer than {SAMBAR_MIN_OVERLAP_GENES} genes or {SAMBAR_MIN_OVERLAP_FRACTION:.0%}); pathway scores "
                "rest on few genes"
                + (
                    ", so check that every file uses the same gene identifier type (for example HGNC symbols)"
                    if len(common) < SAMBAR_MIN_OVERLAP_FRACTION * len(candidates) else
                    "; every candidate gene is shared, so the input itself is small"
                )
            )
        if not errors:
            # A sample with no mutation in a scored gene of some pathway ends with all-zero pathway scores (or none
            # at all), and upstream drops it; this covers both of upstream's drops.
            scored = mutation_genes & length_genes & (cancer_genes if subset else mutation_genes) & pathway_genes
            scope = "cancer genes with an exon size" if subset else "genes with an exon size"
            if warning := _dropped_samples_warning(
                mutation, sorted(scored), f"the {len(scored)} pathway {scope} that SAMBAR scores"
            ):
                lines.append(warning)
        if decision is not None and bool(decision.get("cluster", True) if isinstance(decision, dict) else getattr(decision, "cluster", True)):
            kmax = decision.get("kmax", 4) if isinstance(decision, dict) else getattr(decision, "kmax", 4)
            if error := kmax_sample_error(kmax, mutation.shape[0]):
                errors.append(error)
    if decision is not None:
        errors.extend(_parameter_errors(decision))
    for error in dict.fromkeys(errors):
        lines.append(f"  error: {error}")
    return "\n".join(lines), not errors
