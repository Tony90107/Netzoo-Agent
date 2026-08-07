"""Framework-neutral dataset facts and CONDOR input inspection."""

from __future__ import annotations

from netzoo_table_io import read_condor_edges

from .table_validation import (
    _drop_common_header,
    _read_checked_table,
    _validate_expression,
)

__all__: list[str] = []

def expression_sample_count(expression_file: str) -> tuple[int, bool]:
    expression = _validate_expression(
        _read_checked_table("expression", expression_file)
    )
    if expression.frame is None or expression.errors:
        return 0, expression.has_header
    frame, has_header = _drop_common_header(expression.frame)
    return max(frame.shape[1] - 1, 0), has_header

def inspect_condor_inputs_impl(network_file: str) -> tuple[str, bool]:
    check = _read_checked_table("CONDOR network", network_file)
    location = str(check.resolved_path) if check.resolved_path else network_file
    lines = [
        "CONDOR input inspection:",
        f"- input: {location}",
        "  required format: bipartite edge list",
        "  required columns: source, target",
        "  optional column: numeric weight",
        f"  delimiter: {check.delimiter_name}",
    ]
    if check.skipped_annotation_rows:
        lines.append(
            f"  annotation: skipped {check.skipped_annotation_rows} leading row(s)"
        )
    for note in check.notes:
        lines.append(f"  note: {note}")
    for warning in check.warnings:
        lines.append(f"  warning: {warning}")
    for error in check.errors:
        lines.append(f"  error: {error}")
    if check.frame is None or check.errors:
        return "\n".join(lines), False

    raw_frame, has_header = _drop_common_header(check.frame)
    try:
        frame, _ = read_condor_edges(location)
    except (OSError, ValueError) as error:
        lines.append(f"  error: {error}")
        return "\n".join(lines), False

    source_ids = frame["source"]
    target_ids = frame["target"]
    if raw_frame.shape[1] < 3:
        lines.append(
            "  note: no weight column detected; CONDOR wrapper will use weight=1."
        )

    duplicate_edges = frame[["source", "target"]].duplicated()
    if duplicate_edges.any():
        lines.append(
            f"  warning: duplicate source-target pairs: {int(duplicate_edges.sum())}"
        )

    overlap = set(source_ids) & set(target_ids)
    if overlap:
        preview = ", ".join(sorted(overlap)[:5])
        lines.append(
            "  warning: source and target node IDs overlap. CONDOR expects a bipartite "
            f"network with two node types; overlapping examples: {preview}"
        )

    lines.extend(
        [
            f"  header: {'detected' if has_header else 'not detected'}",
            f"  shape: {frame.shape[0]} rows x {frame.shape[1]} columns",
            f"  edges: {len(frame)}",
            f"  source nodes: {source_ids.nunique()}",
            f"  target nodes: {target_ids.nunique()}",
        ]
    )
    has_errors = any("  error:" in line for line in lines)
    return "\n".join(lines), not has_errors
