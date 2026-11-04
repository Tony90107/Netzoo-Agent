"""Allow-listed normalization adapter: checks inputs here, runs the method in its own process.

SNAIL runs with PySNAIL (``run-pysnail``); RLE, TMM, quantile and FPKM run with DESeq2, edgeR and preprocessCore
in the image's separate R environment (``run-normalize-r``).
"""

from __future__ import annotations

from .command import _run_command
from .contracts import tool
from .data.normalization import METHOD_LABELS, normalization_input_report, normalization_record_path

__all__ = ["normalize_expression"]


@tool
def normalize_expression(
    expression_file: str,
    output_file: str,
    groups_file: str = "",
    snail_aggregation: str = "median",
    normalization_method: str = "snail",
    gene_lengths_file: str = "",
) -> str:
    """Normalize a count-scale gene-by-sample matrix: SNAIL, RLE (DESeq2), TMM (edgeR), quantile or FPKM (edgeR)."""
    report, inputs_ok, inputs = normalization_input_report(
        expression_file, output_file, groups_file, snail_aggregation, normalization_method, gene_lengths_file,
    )
    if not inputs_ok:
        label = METHOD_LABELS.get(normalization_method, "Normalization")
        return f"{label} normalization input validation failed; no command was executed.\n\n" + report
    output_path = inputs.output_path
    if normalization_method == "snail":
        command = ["run-pysnail", "-e", str(inputs.expression_path), "-o", str(output_path), "-m", snail_aggregation]
        if inputs.groups_path is not None:
            command.extend(["-g", str(inputs.groups_path)])
    else:
        command = ["run-normalize-r", "-m", normalization_method, "-e", str(inputs.expression_path), "-o", str(output_path)]
        if inputs.lengths_path is not None:
            command.extend(["-l", str(inputs.lengths_path)])
    return report + "\n\n" + _run_command(
        command,
        output_file=str(output_path),
        additional_output_files=[str(normalization_record_path(output_path))],
    )
