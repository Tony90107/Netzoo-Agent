"""Expression formatting and co-expression data preparation."""

from __future__ import annotations


import pandas as pd

from netzoo_table_io import (
    table_read_info as _table_read_info,
)

from .tables import (
    _drop_common_header,
    _looks_numeric,
    _read_checked_table,
    _read_expression_source,
    _resolve_user_path,
    _validate_expression,
)

__all__: list[str] = []


def format_expression_for_netzoo_impl(
    expression_file: str,
    output_file: str,
    genes_axis: str = "auto",
    with_header: bool = False,
    *,
    execute: bool,
) -> str:
    """Arrange expression as gene rows and sample columns for PANDA/PUMA."""
    lines = ["Expression formatting for PANDA/PUMA:"]
    source_path = _resolve_user_path(expression_file)
    output_path = _resolve_user_path(output_file)
    lines.extend([f"- input: {source_path}", f"- output: {output_path}"])

    if genes_axis not in {"auto", "rows", "columns"}:
        lines.append("- error: genes_axis must be auto, rows, or columns.")
        return "\n".join(lines)
    if not source_path.exists() or not source_path.is_file():
        lines.append("- error: expression input does not exist or is not a file.")
        return "\n".join(lines)
    if source_path == output_path:
        lines.append(
            "- error: output path must be different from the expression input."
        )
        return "\n".join(lines)

    try:
        read_info = _table_read_info(source_path, min_fields=2)
        raw = _read_expression_source(source_path)
    except Exception as error:
        lines.append(f"- error: expression input could not be parsed: {error}")
        return "\n".join(lines)
    if raw.empty or raw.shape[1] < 2:
        lines.append("- error: expression table needs an ID column/row plus values.")
        return "\n".join(lines)
    lines.append(f"- detected input delimiter: {read_info.delimiter_name}")
    if read_info.skiprows:
        lines.append(
            f"- skipped leading annotation/comment rows: {len(read_info.skiprows)}"
        )

    first_cell = str(raw.iloc[0, 0]).strip().casefold()
    gene_labels = {"gene", "genes", "gene_id", "geneid", "symbol"}
    sample_labels = {"sample", "samples", "sample_id", "sampleid"}
    lower_right = raw.iloc[1:, 1:]
    lower_right_numeric = (
        pd.to_numeric(lower_right.stack(), errors="coerce").notna().mean()
        if not lower_right.empty
        else 0.0
    )
    has_header = lower_right_numeric >= 0.95 and (
        first_cell in gene_labels | sample_labels
        or not _looks_numeric(raw.iloc[0, 1:]).any()
    )

    orientation = genes_axis
    if orientation == "auto":
        if first_cell in gene_labels:
            orientation = "rows"
        elif first_cell in sample_labels:
            orientation = "columns"
        elif has_header and raw.shape[0] != raw.shape[1]:
            data_rows = raw.shape[0] - 1
            data_columns = raw.shape[1] - 1
            orientation = "rows" if data_rows > data_columns else "columns"
        else:
            lines.append(
                "- error: gene orientation is ambiguous; set genes_axis to rows or columns."
            )
            return "\n".join(lines)

    if orientation == "columns" and not has_header:
        lines.append(
            "- error: genes in columns require a header row containing gene IDs."
        )
        return "\n".join(lines)

    if orientation == "rows":
        data = raw.iloc[1:, :].copy() if has_header else raw.copy()
        gene_ids = data.iloc[:, 0].astype(str).str.strip()
        values = data.iloc[:, 1:].copy()
        if has_header:
            sample_ids = raw.iloc[0, 1:].astype(str).str.strip().tolist()
        else:
            sample_ids = [f"Sample{index + 1}" for index in range(values.shape[1])]
    else:
        gene_ids = raw.iloc[0, 1:].astype(str).str.strip()
        sample_ids = raw.iloc[1:, 0].astype(str).str.strip().tolist()
        values = raw.iloc[1:, 1:].transpose().reset_index(drop=True)

    numeric_values = values.apply(pd.to_numeric, errors="coerce")
    invalid_cells = int(numeric_values.isna().sum().sum())
    if invalid_cells:
        lines.append(
            f"- error: expression matrix contains {invalid_cells} non-numeric or missing values."
        )
    invalid_ids = gene_ids.eq("") | gene_ids.str.casefold().isin(
        {"nan", "none", "null"}
    )
    if invalid_ids.any():
        lines.append("- error: gene IDs must be non-empty.")
    duplicate_ids = gene_ids[gene_ids.duplicated()].unique()
    if len(duplicate_ids):
        lines.append(
            "- error: gene IDs must be unique: " + ", ".join(duplicate_ids[:5])
        )
    if numeric_values.shape[1] < 3:
        lines.append(
            "- warning: fewer than three samples cannot be used for LIONESS "
            "leave-one-out correlation."
        )
    if any(line.startswith("- error:") for line in lines):
        lines.append("- no output file was written.")
        return "\n".join(lines)

    formatted = pd.concat(
        [
            gene_ids.reset_index(drop=True).rename("gene"),
            numeric_values.reset_index(drop=True),
        ],
        axis=1,
    )
    formatted.columns = ["gene", *sample_ids]
    lines.extend(
        [
            f"- detected genes axis: {orientation}",
            f"- genes: {len(gene_ids)}",
            f"- samples: {numeric_values.shape[1]}",
            "- output delimiter: TSV",
            f"- header in output: {'yes' if with_header else 'no'}",
        ]
    )
    if not execute:
        lines.append(
            "- dry run only; validation passed but no output file was written."
        )
        return "\n".join(lines)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    formatted.to_csv(
        output_path,
        sep="\t",
        index=False,
        header=with_header,
        float_format="%.10g",
    )
    lines.append("- status: success")
    return "\n".join(lines)


def convert_expression_to_coexpression_impl(
    expression_file: str,
    output_file: str,
    *,
    execute: bool,
) -> str:
    """Convert a gene-by-sample expression TSV to a gene-by-gene Pearson correlation matrix."""
    expression = _validate_expression(
        _read_checked_table("expression", expression_file)
    )
    lines = ["Expression to co-expression conversion:"]
    location = (
        str(expression.resolved_path)
        if expression.resolved_path is not None
        else expression_file
    )
    lines.append(f"- input: {location}")

    if expression.format_name == "co-expression matrix":
        lines.append(
            "- error: input is already a co-expression matrix; expected a gene-by-sample expression matrix."
        )
    for warning in expression.warnings:
        lines.append(f"- warning: {warning}")
    for error in expression.errors:
        lines.append(f"- error: {error}")
    if expression.errors:
        lines.append("- no output file was written.")
        return "\n".join(lines)

    frame, _ = _drop_common_header(expression.frame)
    gene_ids = frame.iloc[:, 0].astype(str).str.strip()
    duplicate_ids = gene_ids[gene_ids.duplicated()].unique()
    if len(duplicate_ids):
        lines.append(
            "- error: gene IDs must be unique before conversion: "
            + ", ".join(duplicate_ids[:5])
        )
    if frame.shape[1] < 3:
        lines.append(
            "- error: at least two sample columns are required to calculate correlation."
        )

    values = frame.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")
    zero_variance = gene_ids[values.nunique(axis=1, dropna=True) <= 1].tolist()
    if zero_variance:
        lines.append(
            "- error: correlation is undefined for zero-variance genes: "
            + ", ".join(zero_variance[:5])
        )

    output_path = _resolve_user_path(output_file)
    lines.append(f"- output: {output_path}")
    if expression.resolved_path == output_path:
        lines.append(
            "- error: output path must be different from the expression input."
        )

    if any(line.startswith("- error:") for line in lines):
        lines.append("- no output file was written.")
        return "\n".join(lines)

    lines.extend(
        [
            f"- genes: {len(gene_ids)}",
            f"- samples: {values.shape[1]}",
            "- method: Pearson correlation across samples",
        ]
    )
    if not execute:
        lines.append(
            "- dry run only; validation passed but no output file was written. Add --execute to write it."
        )
        return "\n".join(lines)

    values.index = gene_ids
    coexpression = values.transpose().corr(method="pearson")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    coexpression.to_csv(
        output_path,
        sep="\t",
        index=True,
        index_label="gene",
        float_format="%.10g",
    )
    lines.extend(
        [
            f"- result: wrote {coexpression.shape[0]} x {coexpression.shape[1]} co-expression matrix",
            "- status: success",
        ]
    )
    return "\n".join(lines)
