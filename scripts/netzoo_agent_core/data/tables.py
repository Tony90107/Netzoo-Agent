"""NetZoo table parsing and biological input compatibility checks."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from netzoo_table_io import (
    read_table as _read_table,
    table_read_info as _table_read_info,
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


def _drop_common_header(frame: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    if frame.empty:
        return frame, False

    first_value = str(frame.iloc[0, 0]).strip().lower()
    if first_value in {"", "gene", "genes", "gene_id", "geneid", "symbol"}:
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
    if frame.empty:
        check.errors.append("expression table has no data rows.")
        return check

    numeric_block = frame.iloc[:, 1:] if frame.shape[1] > 1 else pd.DataFrame()
    numeric_ratio = (
        _looks_numeric(numeric_block.stack()).mean() if not numeric_block.empty else 0.0
    )
    row_ids = frame.iloc[:, 0].dropna().astype(str).str.strip()

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
        lines.append(
            f"  error: no exact ID overlap between {source_name} and {reference_name}."
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


def _inspect_panda_inputs_impl(
    expression_file: str,
    motif_file: str,
    ppi_file: str,
    mirna_file: str = "",
) -> tuple[str, bool, bool]:
    expression = _validate_expression(
        _read_checked_table("expression", expression_file)
    )
    motif = _validate_edge_or_bed(_read_checked_table("motif", motif_file), "motif")
    ppi = _validate_edge_or_bed(_read_checked_table("PPI", ppi_file), "PPI")

    all_checks = [expression, motif, ppi]

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
        if check.has_header:
            lines.append("  header: detected")
        for note in check.notes:
            lines.append(f"  note: {note}")
        for warning in check.warnings:
            lines.append(f"  warning: {warning}")
        for error in check.errors:
            lines.append(f"  error: {error}")

    cross_id_error = False
    if motif.format_name == "edge list" and expression.identifiers:
        id_lines, invalid = _identifier_overlap_report(
            "motif target genes overlapping expression genes",
            motif.secondary_identifiers,
            expression.identifiers,
            "motif target gene",
            "expression gene IDs",
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
) -> str:
    """Inspect PANDA/PUMA input files and report format, readability, and ID overlaps."""
    report, _, _ = _inspect_panda_inputs_impl(
        expression_file=expression_file,
        motif_file=motif_file,
        ppi_file=ppi_file,
        mirna_file=mirna_file,
    )
    return report
