"""NetZoo table parsing and biological input compatibility checks."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .. import settings
from netzoo_table_io import (
    read_table as _read_table,
    table_read_info as _table_read_info,
)

from .gene_validation import (
    TAXON_REQUIRED_SOURCE,
    UNRECOGNIZED_PHRASE,
    GeneValidationSummary,
    _identifier_preview,
    validate_gene_identifiers,
)

from .paths import _resolve_user_path

__all__ = [
    "TableCheck",
    "_resolve_user_path",
    "_read_expression_source",
    "_looks_numeric",
    "_drop_common_header",
    "_read_checked_table",
    "_validate_expression",
    "_validate_edge_or_bed",
    "_validate_mirna_list",
    "validate_gene_identifiers",
    "_identifier_overlap_report",
    "_inspect_panda_inputs_impl",
    "inspect_netzoo_inputs_report",
]


@dataclass
class TableCheck:
    label: str
    path: str
    resolved_path: Path | None = None
    frame: pd.DataFrame | None = None
    identifiers: set[str] = field(default_factory=set)
    secondary_identifiers: set[str] = field(default_factory=set)
    format_name: str = "unknown"
    has_header: bool = False
    header_label: str | None = None
    header_role: str = "unknown"
    identifier_namespace: str = "unknown"
    secondary_identifier_namespace: str = "unknown"
    # Shape after expression header/ID-axis normalization. ``frame`` remains
    # the raw parsed table so the report can show both views without ambiguity.
    data_rows: int | None = None
    data_columns: int | None = None
    canonical_identifiers: dict[str, str] = field(default_factory=dict)
    regulator_canonical_identifiers: dict[str, str] = field(default_factory=dict)
    node_canonical_identifiers: dict[str, str] = field(default_factory=dict)
    gene_validation: GeneValidationSummary | None = None
    delimiter_name: str = "unknown"
    skipped_annotation_rows: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _read_expression_source(path: Path) -> pd.DataFrame:
    """Read a TSV or CSV expression table without assuming its orientation."""
    return _read_table(path, min_fields=2)


def _looks_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").notna()


def _normalise_header_label(value: object) -> str:
    """Return a stable comparison token for a first-cell axis label."""
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().casefold()).strip("_")


def _header_role(value: object) -> str:
    """Classify a first-cell label without claiming that IDs are biologically valid."""
    token = _normalise_header_label(value)
    if token in {
        "gene",
        "genes",
        "gene_id",
        "geneid",
        "gene_symbol",
        "genesymbol",
        "symbol",
        "feature",
        "feature_id",
    }:
        return "gene"
    if token in {
        "sample",
        "samples",
        "sample_id",
        "sampleid",
        "subject",
        "subject_id",
        "patient",
        "patient_id",
        "cell",
        "cell_id",
    }:
        return "sample"
    return "unknown"


_ENSEMBL_GENE = re.compile(r"^ENS[A-Z0-9]*G[0-9]+(?:\.[0-9]+)?$", re.IGNORECASE)
_ENSEMBL_TRANSCRIPT = re.compile(r"^ENS[A-Z0-9]*T[0-9]+(?:\.[0-9]+)?$", re.IGNORECASE)
_SYMBOL_LIKE = re.compile(r"^[A-Za-z][A-Za-z0-9-]*$")
# High enough that a genuinely mixed file stays opaque, low enough that a
# handful of spreadsheet-mangled labels do not disable the whole axis.
_DOMINANT_NAMESPACE_RATIO = 0.9
_DOMINANT_NAMESPACE_MIN_IDENTIFIERS = 10


def _identifier_namespace(values: object) -> str:
    """Infer a conservative identifier namespace from observed values.

    This is intentionally a namespace observation, not an online gene database
    lookup. Numeric IDs may be Entrez IDs, and symbol-like IDs may belong to a
    non-human organism or a project-local namespace.
    """
    identifiers = [str(value).strip() for value in values if str(value).strip()]
    if not identifiers:
        return "unknown"
    if all(_ENSEMBL_GENE.fullmatch(value) for value in identifiers):
        return "ensembl_gene"
    if all(_ENSEMBL_TRANSCRIPT.fullmatch(value) for value in identifiers):
        return "ensembl_transcript"
    if all(value.isdigit() for value in identifiers):
        return "numeric_identifier"
    if all(_SYMBOL_LIKE.fullmatch(value) for value in identifiers):
        return "symbol_like"
    if any(
        _ENSEMBL_GENE.fullmatch(value) or _ENSEMBL_TRANSCRIPT.fullmatch(value)
        for value in identifiers
    ):
        return "mixed_ensembl"
    # A real expression matrix routinely carries a few corrupted labels -- the
    # classic case is a spreadsheet rewriting MARCH7 or SEPT9 as a date serial.
    # Treating the whole axis as unresolvable because of them means the other
    # thousand genes go unverified and the corrupted ones are never named. Keep
    # the dominant namespace so each outlier is reported on its own merits.
    symbol_like = sum(
        1 for value in identifiers if _SYMBOL_LIKE.fullmatch(value)
    )
    if (
        len(identifiers) >= _DOMINANT_NAMESPACE_MIN_IDENTIFIERS
        and symbol_like / len(identifiers) >= _DOMINANT_NAMESPACE_RATIO
    ):
        return "symbol_like"
    return "opaque"


def _namespace_union(*namespaces: str) -> str:
    values = {value for value in namespaces if value and value != "unknown"}
    if not values:
        return "unknown"
    return next(iter(values)) if len(values) == 1 else "mixed"


def _drop_common_header(frame: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    if frame.empty:
        return frame, False

    first_value = str(frame.iloc[0, 0]).strip().lower()
    if first_value == "" or _header_role(first_value) in {"gene", "sample"}:
        return frame.iloc[1:, :].reset_index(drop=True), True

    edge_header_first_cells = {
        "tf",
        "regulator",
        "source",
        "tf1",
        "protein1",
        "chrom",
        "chromosome",
        "#chrom",
    }
    if first_value in edge_header_first_cells and frame.shape[1] >= 3:
        if not _looks_numeric(frame.iloc[0, 2:3]).all():
            return frame.iloc[1:, :].reset_index(drop=True), True

    if frame.shape[0] >= 2 and frame.shape[1] >= 2:
        first_row_after_id = frame.iloc[0, 1:]
        second_row_after_id = frame.iloc[1, 1:]
        if (
            not _looks_numeric(first_row_after_id).any()
            and _looks_numeric(second_row_after_id).mean() >= 0.8
        ):
            return frame.iloc[1:, :].reset_index(drop=True), True
    return frame, False


def _read_checked_table(label: str, path: str) -> TableCheck:
    check = TableCheck(label=label, path=path)
    if not path:
        check.errors.append(f"{label} path is empty.")
        return check

    resolved = _resolve_user_path(path)
    check.resolved_path = resolved
    if not resolved.exists():
        check.errors.append(f"{label} file does not exist: {resolved}")
        return check
    if not resolved.is_file():
        check.errors.append(f"{label} path is not a regular file: {resolved}")
        return check
    try:
        with resolved.open("r", encoding="utf-8"):
            pass
    except OSError as error:
        check.errors.append(f"{label} file is not readable: {error}")
        return check

    try:
        min_fields = 1 if label.casefold() == "mirna" else 2
        read_info = _table_read_info(resolved, min_fields=min_fields)
        check.delimiter_name = read_info.delimiter_name
        check.skipped_annotation_rows = len(read_info.skiprows)
    except Exception as error:
        check.errors.append(f"{label} delimiter could not be detected: {error}")
        return check

    try:
        check.frame = _read_table(resolved, min_fields=min_fields)
    except Exception as error:
        check.errors.append(
            f"{label} could not be parsed as a delimited table: {error}"
        )
        return check

    if check.delimiter_name == "CSV":
        check.notes.append(
            f"{label} was read as CSV; PANDA/PUMA runtime outputs will be written as TSV."
        )
    elif check.delimiter_name == "whitespace":
        check.warnings.append(
            f"{label} was read as whitespace-delimited text; TSV is safer for PANDA/PUMA."
        )
    if check.skipped_annotation_rows:
        check.notes.append(
            f"skipped {check.skipped_annotation_rows} leading annotation/comment row(s)."
        )

    if check.frame.empty:
        check.errors.append(f"{label} table is empty.")
    return check


def _validate_expression(check: TableCheck) -> TableCheck:
    if check.frame is None or check.errors:
        return check

    frame, has_header = _drop_common_header(check.frame)
    check.has_header = has_header
    if has_header and check.frame is not None:
        raw_label = str(check.frame.iloc[0, 0]).strip()
        check.header_label = raw_label or None
        check.header_role = _header_role(raw_label)
        if check.header_role == "sample":
            check.errors.append(
                f"expression first header cell {raw_label!r} labels a sample axis; "
                "gene IDs must be in the first column."
            )
        elif check.header_role == "gene":
            check.notes.append(
                f"gene-axis header label observed: {raw_label!r}."
            )
        else:
            check.warnings.append(
                f"expression first header cell {raw_label!r} has unknown axis semantics; "
                "the first column is treated as gene IDs by position."
            )
    if frame.empty:
        check.errors.append("expression table has no data rows.")
        return check

    numeric_block = frame.iloc[:, 1:] if frame.shape[1] > 1 else pd.DataFrame()
    numeric_ratio = (
        _looks_numeric(numeric_block.stack()).mean() if not numeric_block.empty else 0.0
    )
    row_ids = frame.iloc[:, 0].dropna().astype(str).str.strip()
    check.data_rows = len(row_ids)
    check.data_columns = max(frame.shape[1] - 1, 0)
    check.identifier_namespace = _identifier_namespace(row_ids)
    check.notes.append(
        f"gene ID namespace observed: {check.identifier_namespace}."
    )

    header_ids = (
        set(check.frame.iloc[0, 1:].dropna().astype(str).str.strip())
        if has_header and check.frame is not None and check.frame.shape[1] > 1
        else set()
    )
    row_id_overlap = (
        len(header_ids & set(row_ids)) / max(len(set(row_ids)), 1)
        if header_ids and len(row_ids) > 0
        else 0.0
    )
    possible_square_with_header = (
        has_header
        and check.frame.shape[0] == check.frame.shape[1]
        and row_id_overlap >= 0.8
    )
    possible_square_no_header = (
        not has_header
        and check.frame.shape[0] == check.frame.shape[1]
        and _looks_numeric(check.frame.stack()).mean() >= 0.95
    )

    if possible_square_with_header or possible_square_no_header:
        check.format_name = "co-expression matrix"
        check.errors.append(
            "expression_file looks like a square co-expression matrix. The current run-panda wrapper expects a gene-by-sample expression matrix; convert only if using a PANDA API/CLI mode that accepts precomputed co-expression."
        )
        if possible_square_with_header:
            check.identifiers = set(row_ids)
        return check

    check.format_name = "expression matrix"
    check.identifiers = set(row_ids)
    if frame.shape[1] < 2:
        check.errors.append(
            "expression matrix must have a gene ID column plus at least one sample column."
        )
    if numeric_ratio < 0.95:
        check.errors.append(
            f"expression values must be numeric; numeric cell ratio is {numeric_ratio:.1%}."
        )
    numeric_values = pd.to_numeric(numeric_block.stack(), errors="coerce").dropna()
    if (
        len(numeric_values) >= 100
        and set(numeric_values.unique()).issubset({0, 1})
        and (numeric_values == 0).mean() >= 0.98
    ):
        check.errors.append(
            "expression_file looks like a highly sparse binary somatic mutation "
            "incidence matrix. The expression input contract requires gene-expression "
            "measurements, not mutation incidence. Confirm the data modality and "
            "choose a compatible workflow before correlation-based inference."
        )
    if row_ids.empty:
        check.errors.append("expression matrix has no gene IDs in the first column.")
    duplicated = row_ids[row_ids.duplicated()].unique()
    if len(duplicated):
        preview = ", ".join(duplicated[:5])
        check.warnings.append(
            f"expression matrix contains duplicate gene IDs: {preview}"
        )
    if frame.shape[1] < 3:
        check.warnings.append(
            "expression matrix has fewer than two sample columns; co-expression/correlation is not meaningful."
        )
    elif frame.shape[1] >= 3:
        check.notes.append(
            "expression matrix can be used to derive gene co-expression/correlation for PANDA."
        )
    if has_header:
        check.notes.append(
            "expression header row detected; pass --with_header when running netZooPy PANDA."
        )
    return check


def _validate_edge_or_bed(check: TableCheck, label: str) -> TableCheck:
    if check.frame is None or check.errors:
        return check

    frame, has_header = _drop_common_header(check.frame)
    check.has_header = has_header
    if frame.empty:
        check.errors.append(f"{label} table has no data rows.")
        return check

    first_col = frame.iloc[:, 0].astype(str).str.strip()
    second_col = (
        frame.iloc[:, 1].astype(str).str.strip()
        if frame.shape[1] > 1
        else pd.Series(dtype=str)
    )
    third_col = (
        frame.iloc[:, 2].astype(str).str.strip()
        if frame.shape[1] > 2
        else pd.Series(dtype=str)
    )

    bed_like = (
        frame.shape[1] >= 3
        and first_col.str.match(r"^(chr)?[A-Za-z0-9_.-]+$").mean() >= 0.95
        and pd.to_numeric(second_col, errors="coerce").notna().mean() >= 0.95
        and pd.to_numeric(third_col, errors="coerce").notna().mean() >= 0.95
    )

    if bed_like:
        starts = pd.to_numeric(second_col, errors="coerce")
        ends = pd.to_numeric(third_col, errors="coerce")
        check.format_name = "BED-like intervals"
        if not (starts < ends).all():
            check.errors.append(f"{label} BED intervals must have start < end.")
        check.errors.append(
            f"{label} looks like BED intervals. PANDA run-panda expects a TF-gene-weight edge list here, so this BED file must be converted to a motif/prior edge list before execution."
        )
        return check

    check.format_name = "edge list"
    if frame.shape[1] < 3:
        check.errors.append(f"{label} edge list must have at least 3 columns.")
        return check

    weight_numeric = pd.to_numeric(frame.iloc[:, 2], errors="coerce").notna().mean()
    if weight_numeric < 0.95:
        check.errors.append(
            f"{label} weight column must be numeric; numeric ratio is {weight_numeric:.1%}."
        )

    invalid_id_values = {"", "nan", "none", "null"}
    left_ids = first_col[~first_col.str.casefold().isin(invalid_id_values)]
    right_ids = second_col[~second_col.str.casefold().isin(invalid_id_values)]
    if left_ids.empty or right_ids.empty:
        check.errors.append(
            f"{label} edge list must have non-empty IDs in the first two columns."
        )
    check.identifiers = set(left_ids)
    check.secondary_identifiers = set(right_ids)
    check.identifier_namespace = _identifier_namespace(left_ids)
    check.secondary_identifier_namespace = _identifier_namespace(right_ids)
    check.notes.append(
        f"{label} first-column ID namespace observed: {check.identifier_namespace}."
    )
    check.notes.append(
        f"{label} second-column ID namespace observed: {check.secondary_identifier_namespace}."
    )
    duplicated = frame.iloc[:, :2].astype(str).duplicated()
    if duplicated.any():
        check.warnings.append(
            f"{label} contains duplicate ID pairs: {int(duplicated.sum())}"
        )
    return check


def _validate_mirna_list(check: TableCheck) -> TableCheck:
    """Validate the exact one-regulator-per-line format consumed by netZooPy PUMA."""
    check.format_name = "one-regulator-per-line list"
    if check.resolved_path is None or check.errors:
        return check

    try:
        raw_lines = check.resolved_path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as error:
        check.errors.append(f"miRNA file is not readable: {error}")
        return check

    if not raw_lines:
        check.errors.append("miRNA list is empty.")
        return check

    blank_lines = [
        index + 1 for index, value in enumerate(raw_lines) if not value.strip()
    ]
    if blank_lines:
        check.errors.append(
            "miRNA list contains blank lines: "
            + ", ".join(str(index) for index in blank_lines[:5])
        )

    entries: list[str] = []
    for index, raw_value in enumerate(raw_lines, start=1):
        value = raw_value.strip()
        if not value:
            continue
        if "\t" in raw_value or "," in raw_value:
            check.errors.append(
                f"miRNA line {index} has multiple fields; expected exactly one regulator ID."
            )
            continue
        if re.search(r"\s", value):
            check.errors.append(
                f"miRNA line {index} contains whitespace inside the regulator ID: {value!r}."
            )
            continue
        entries.append(value)

    if entries and entries[0].casefold() in {
        "mirna",
        "mir",
        "mirna_id",
        "regulator",
    }:
        check.errors.append(
            "miRNA list must not have a header; the first line must be a regulator ID."
        )

    duplicated = sorted({entry for entry in entries if entries.count(entry) > 1})
    if duplicated:
        check.errors.append(
            "miRNA list contains duplicate regulator IDs: " + ", ".join(duplicated[:5])
        )

    check.identifiers = set(entries)
    if not check.identifiers:
        check.errors.append("miRNA list has no usable regulator IDs.")
    return check


def _identifier_overlap_report(
    label: str,
    source_ids: set[str],
    reference_ids: set[str],
    source_name: str,
    reference_name: str,
    source_namespace: str = "unknown",
    reference_namespace: str = "unknown",
    source_canonical_ids: dict[str, str] | None = None,
    reference_canonical_ids: dict[str, str] | None = None,
) -> tuple[list[str], bool]:
    """Report exact cross-file ID compatibility and return whether it is invalid."""
    overlap = source_ids & reference_ids
    source_count = len(source_ids)
    coverage = len(overlap) / source_count if source_count else 0.0
    lines = [f"- {label}: {len(overlap)}/{source_count} ({coverage:.1%})"]

    if not source_ids:
        lines.append(f"  error: {source_name} contains no usable IDs.")
        return lines, True

    unmatched = sorted(source_ids - reference_ids)
    if not overlap:
        canonical_source = set((source_canonical_ids or {}).values())
        canonical_reference = set((reference_canonical_ids or {}).values())
        canonical_overlap = canonical_source & canonical_reference
        if canonical_overlap:
            lines.append(
                "  status: canonical gene matches found after identifier mapping "
                f"({len(canonical_overlap)} unique gene(s))."
            )
            if source_canonical_ids and reference_canonical_ids:
                lines[0] = (
                    f"- {label}: {len(canonical_overlap)}/{source_count} "
                    f"({len(canonical_overlap) / source_count:.1%} canonical coverage)"
                )
            return lines, False
        lines.append(
            f"  error: no exact ID overlap between {source_name} and {reference_name}."
        )
        if (
            source_namespace not in {"unknown", "mixed"}
            and reference_namespace not in {"unknown", "mixed"}
            and source_namespace != reference_namespace
        ):
            lines.append(
                "  observation: identifier namespaces differ "
                f"({source_namespace} vs {reference_namespace}); map both files "
                "to one namespace before relying on overlap."
            )

        casefold_overlap = {identifier.casefold() for identifier in source_ids} & {
            identifier.casefold() for identifier in reference_ids
        }
        if casefold_overlap:
            lines.append(
                "  hint: IDs overlap only when letter case is ignored; normalize capitalization."
            )

        def without_version(identifier: str) -> str:
            return re.sub(r"\.\d+$", "", identifier)

        versionless_overlap = {
            without_version(identifier) for identifier in source_ids
        } & {without_version(identifier) for identifier in reference_ids}
        if versionless_overlap:
            lines.append(
                "  hint: IDs overlap after removing numeric version suffixes such as '.1'."
            )
        return lines, True

    if unmatched:
        preview = ", ".join(unmatched[:5])
        lines.append(
            f"  warning: unmatched {source_name} IDs: {len(unmatched)}"
            f" (examples: {preview})"
        )
    else:
        lines.append(f"  status: all {source_name} IDs match {reference_name}.")
    return lines, False


def _gene_authority_report_lines(
    role: str,
    summary: GeneValidationSummary | None,
) -> list[str]:
    """Render the per-identifier authority evidence used by input preflight.

    The aggregate status note above is useful for large tables, but it is not
    enough to diagnose one bad label or to explain whether a result came from
    the local cache, NCBI/Ensembl, or the non-authoritative Websearch fallback.
    Keep the complete records in the inspection report so the CLI can show the
    same evidence that the execution gate used.
    """
    if summary is None or not summary.records:
        return []
    lines = [f"  gene authority records ({role}):"]
    for _, record in sorted(
        summary.records.items(), key=lambda item: item[1].identifier.casefold()
    ):
        identifier = record.identifier
        canonical_id = record.canonical_id or "(none)"
        authority = record.authority or "(none)"
        source = record.source or "(none)"
        taxon = record.taxon or "(none)"
        symbol = record.symbol or "(none)"
        display_status = record.status
        if settings.TEST_DATA_MODE and record.status != "valid":
            display_status = "test_only"
        lines.append(
            "    - "
            f"id: {identifier}; "
            f"status: {display_status}; "
            f"canonical_id: {canonical_id}; "
            f"authority: {authority}; "
            f"source: {source}; "
            f"taxon: {taxon}; "
            f"symbol: {symbol}"
        )
    return lines


def _inspect_panda_inputs_impl(
    expression_file: str,
    motif_file: str,
    ppi_file: str,
    mirna_file: str = "",
    taxon: str = "",
    check_gene_authority: bool = True,
) -> tuple[str, bool, bool]:
    expression = _validate_expression(
        _read_checked_table("expression", expression_file)
    )
    motif = _validate_edge_or_bed(_read_checked_table("motif", motif_file), "motif")
    ppi = _validate_edge_or_bed(_read_checked_table("PPI", ppi_file), "PPI")
    motif_regulator_validation: GeneValidationSummary | None = None
    ppi_node_validation: GeneValidationSummary | None = None

    # Validate the gene axis and motif target axis independently before
    # comparing them.  The validator is cache-first; a configured Websearch
    # MCP is consulted only for cache misses.  Unverified results remain
    # warnings, while authoritative invalid results become preflight errors.
    if check_gene_authority and expression.identifiers:
        expression.gene_validation = validate_gene_identifiers(
            expression.identifiers,
            expression.identifier_namespace,
            taxon,
        )
        expression.canonical_identifiers = expression.gene_validation.canonical_map
    if check_gene_authority and motif.format_name == "edge list" and motif.secondary_identifiers:
        motif.gene_validation = validate_gene_identifiers(
            motif.secondary_identifiers,
            motif.secondary_identifier_namespace,
            taxon,
        )
        motif.canonical_identifiers = motif.gene_validation.canonical_map
    if check_gene_authority and motif.format_name == "edge list" and motif.identifiers:
        motif_regulator_validation = validate_gene_identifiers(
            motif.identifiers,
            motif.identifier_namespace,
            taxon,
        )
        motif.regulator_canonical_identifiers = motif_regulator_validation.canonical_map
    if check_gene_authority and ppi.format_name == "edge list":
        ppi_nodes = ppi.identifiers | ppi.secondary_identifiers
        if ppi_nodes:
            ppi_node_validation = validate_gene_identifiers(
                ppi_nodes,
                _namespace_union(
                    ppi.identifier_namespace,
                    ppi.secondary_identifier_namespace,
                ),
                taxon,
            )
            ppi.node_canonical_identifiers = ppi_node_validation.canonical_map

    for check, summary, role in (
        (expression, expression.gene_validation, "expression genes"),
        (motif, motif.gene_validation, "motif target genes"),
        (motif, motif_regulator_validation, "motif regulator genes"),
        (ppi, ppi_node_validation, "PPI regulator genes"),
    ):
        if summary is None:
            continue
        counts = summary.status_counts()
        display_counts: dict[str, int] = {}
        for status, count in counts.items():
            display_status = (
                "test_only"
                if settings.TEST_DATA_MODE and status != "valid"
                else status
            )
            display_counts[display_status] = display_counts.get(display_status, 0) + count
        parts = [
            f"{count} {status}"
            for status, count in sorted(display_counts.items())
        ]
        lookup_parts = [f"{summary.cache_hits} cache hit(s)"]
        if summary.online_queries:
            lookup_parts.append(f"{summary.online_queries} online lookup batch(es)")
        scope = f" for taxon {taxon!r}" if taxon else ""
        check.notes.append(
            f"{role} authority validation{scope}: {', '.join(parts)} "
            f"({', '.join(lookup_parts)})."
        )
        if summary.stale_cache_hits:
            check.warnings.append(
                f"{role} used {summary.stale_cache_hits} stale cache fallback(s); "
                "refresh the gene authority cache when online lookup is available."
            )
        invalid_ids = sorted(
            record.identifier
            for record in summary.records.values()
            if record.status == "invalid"
        )
        if invalid_ids:
            message = (
                f"{role} {UNRECOGNIZED_PHRASE}" + _identifier_preview(invalid_ids)
            )
            if settings.TEST_DATA_MODE:
                check.warnings.append(
                    message
                    + "; accepted as test-only identifiers because Synthetic Test mode is enabled."
                )
            else:
                check.errors.append(message)
        taxon_required_ids = sorted(
            record.identifier
            for record in summary.records.values()
            if record.source == TAXON_REQUIRED_SOURCE
        )
        if taxon_required_ids:
            message = (
                f"{role} are gene symbols and cannot be verified without a "
                "species; set taxon (for example 'human', 'Homo sapiens', or "
                "'9606'), or supply NCBI/Ensembl gene IDs instead: "
                + ", ".join(taxon_required_ids[:5])
            )
            if settings.TEST_DATA_MODE:
                check.warnings.append(
                    message
                    + "; accepted as test-only identifiers because Synthetic Test mode is enabled."
                )
            else:
                check.errors.append(message)
        ambiguous_ids = sorted(
            record.identifier
            for record in summary.records.values()
            if record.status == "ambiguous"
            and record.source != TAXON_REQUIRED_SOURCE
        )
        if ambiguous_ids:
            message = (
                f"{role} have multiple authority matches; taxon may be required: "
                + ", ".join(ambiguous_ids[:5])
            )
            check.warnings.append(
                message
                + (
                    "; accepted as test-only identifiers because Synthetic Test mode is enabled."
                    if settings.TEST_DATA_MODE
                    else ""
                )
            )
        unverified_ids = sorted(
            record.identifier
            for record in summary.records.values()
            if record.status == "unverified"
        )
        if unverified_ids:
            online_unverified = sorted(
                record.identifier
                for record in summary.records.values()
                if record.status == "unverified"
                and record.source not in {"offline", "stale_cache"}
            )
            if online_unverified:
                message = (
                    f"{role} could not be authoritatively verified because the "
                    "structured NCBI/Ensembl lookup was unavailable; Websearch "
                    "cannot authorize execution: "
                    + ", ".join(online_unverified[:5])
                )
                if settings.TEST_DATA_MODE:
                    check.warnings.append(
                        message
                        + "; accepted as test-only identifiers because Synthetic Test mode is enabled."
                    )
                else:
                    check.errors.append(message)
            else:
                message = (
                    f"{role} could not be authority-verified in offline mode; exact "
                    "schema and cross-file matching will still be used: "
                    + ", ".join(unverified_ids[:5])
                )
                if settings.TEST_DATA_MODE:
                    check.warnings.append(
                        message
                        + "; accepted as test-only identifiers because Synthetic Test mode is enabled."
                    )
                else:
                    check.errors.append(
                        message
                        + "; production validation requires authoritative confirmation."
                    )

    all_checks = [expression, motif, ppi]
    authority_summaries = {
        "expression": [("expression genes", expression.gene_validation)],
        "motif": [
            ("motif target genes", motif.gene_validation),
            ("motif regulator genes", motif_regulator_validation),
        ],
        "PPI": [("PPI regulator genes", ppi_node_validation)],
    }

    lines = ["Input inspection:"]
    for check in all_checks:
        location = str(check.resolved_path) if check.resolved_path else check.path
        shape = (
            f"{check.frame.shape[0]} rows x {check.frame.shape[1]} columns"
            if check.frame is not None
            else "unreadable"
        )
        lines.extend(
            [
                f"- {check.label}: {location}",
                f"  format: {check.format_name}",
                f"  delimiter: {check.delimiter_name}",
                f"  shape: {shape}",
            ]
        )
        if (
            check.label.casefold() == "expression"
            and check.format_name == "expression matrix"
            and check.data_rows is not None
            and check.data_columns is not None
        ):
            lines.append(
                f"  data shape: {check.data_rows} genes x "
                f"{check.data_columns} samples"
            )
        if check.has_header:
            lines.append("  header: detected")
        for note in check.notes:
            lines.append(f"  note: {note}")
        for warning in check.warnings:
            lines.append(f"  warning: {warning}")
        for error in check.errors:
            lines.append(f"  error: {error}")
        for role, summary in authority_summaries.get(check.label, ()):
            lines.extend(_gene_authority_report_lines(role, summary))

    cross_id_error = False
    if motif.format_name == "edge list" and expression.identifiers:
        id_lines, invalid = _identifier_overlap_report(
            "motif target genes overlapping expression genes",
            motif.secondary_identifiers,
            expression.identifiers,
            "motif target gene",
            "expression gene IDs",
            motif.secondary_identifier_namespace,
            expression.identifier_namespace,
            motif.canonical_identifiers,
            expression.canonical_identifiers,
        )
        lines.extend(id_lines)
        cross_id_error = cross_id_error or invalid
    mirna: TableCheck | None = None
    if mirna_file:
        mirna = _validate_mirna_list(_read_checked_table("miRNA", mirna_file))
        all_checks.append(mirna)
        location = str(mirna.resolved_path) if mirna.resolved_path else mirna.path
        lines.extend(
            [
                f"- miRNA: {location}",
                f"  format: {mirna.format_name}",
                f"  entries: {len(mirna.identifiers)}",
            ]
        )
        for warning in mirna.warnings:
            lines.append(f"  warning: {warning}")
        for error in mirna.errors:
            lines.append(f"  error: {error}")

        if motif.format_name == "edge list" and mirna.identifiers:
            missing_mirnas = sorted(mirna.identifiers - motif.identifiers)
            overlap = mirna.identifiers & motif.identifiers
            lines.append(
                "- miRNA names overlapping motif/prior regulators: "
                f"{len(overlap)}/{len(mirna.identifiers)} "
                f"({len(overlap) / len(mirna.identifiers):.1%})"
            )
            if missing_mirnas:
                lines.append(
                    "  error: every miRNA list ID must occur in motif/prior column 1; "
                    f"missing {len(missing_mirnas)} (examples: "
                    + ", ".join(missing_mirnas[:5])
                    + ")"
                )
                cross_id_error = True

    if motif.format_name == "edge list" and ppi.format_name == "edge list":
        motif_tfs = motif.identifiers
        if mirna is not None:
            motif_tfs = motif_tfs - mirna.identifiers
        if len(motif_tfs) < 2:
            lines.append(
                "  error: PANDA/PUMA normalization needs at least two TF regulators; "
                f"found {len(motif_tfs)} after excluding miRNAs."
            )
            cross_id_error = True
        id_lines, invalid = _identifier_overlap_report(
            "motif TFs overlapping PPI TFs",
            motif_tfs,
            ppi.identifiers | ppi.secondary_identifiers,
            "motif TF",
            "PPI TF IDs",
            motif.identifier_namespace,
            _namespace_union(ppi.identifier_namespace, ppi.secondary_identifier_namespace),
            motif.regulator_canonical_identifiers,
            ppi.node_canonical_identifiers,
        )
        lines.extend(id_lines)
        cross_id_error = cross_id_error or invalid

    has_errors = any(check.errors for check in all_checks) or cross_id_error
    with_header = (
        expression.has_header and expression.format_name == "expression matrix"
    )
    return "\n".join(lines), not has_errors, with_header


def inspect_netzoo_inputs_report(
    expression_file: str,
    motif_file: str,
    ppi_file: str,
    mirna_file: str = "",
    taxon: str = "",
) -> str:
    """Inspect PANDA/PUMA input files and report format, readability, and ID overlaps."""
    report, _, _ = _inspect_panda_inputs_impl(
        expression_file=expression_file,
        motif_file=motif_file,
        ppi_file=ppi_file,
        mirna_file=mirna_file,
        taxon=taxon,
    )
    return report
