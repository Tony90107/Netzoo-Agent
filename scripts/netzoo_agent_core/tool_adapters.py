"""LangChain adapters for pure workflow data operations."""

from __future__ import annotations

from . import settings
from .data.tables import inspect_netzoo_inputs_report
from .data.cobra import inspect_cobra_inputs_impl
from .data.dragon import inspect_dragon_inputs_impl
from .data.transforms import (
    convert_expression_to_coexpression_impl,
    format_expression_for_netzoo_impl,
)
from .framework_compat import tool


@tool
def inspect_netzoo_inputs(
    expression_file: str,
    motif_file: str,
    ppi_file: str,
    mirna_file: str = "",
) -> str:
    """Inspect PANDA/PUMA input readability, formats, and identifier overlaps."""
    return inspect_netzoo_inputs_report(
        expression_file,
        motif_file,
        ppi_file,
        mirna_file,
    )


@tool
def inspect_cobra_inputs(expression_file: str, design_file: str) -> str:
    """Inspect labelled expression and sample-covariate inputs for COBRA."""
    report, _ = inspect_cobra_inputs_impl(expression_file, design_file)
    return report


@tool
def inspect_dragon_inputs(omics_layer_1: str, omics_layer_2: str) -> str:
    """Inspect exactly two DRAGON sample-by-feature continuous data tables."""
    report, _ = inspect_dragon_inputs_impl(omics_layer_1, omics_layer_2)
    return report


@tool
def format_expression_for_netzoo(
    expression_file: str,
    output_file: str,
    genes_axis: str = "auto",
    with_header: bool = False,
) -> str:
    """Arrange expression as gene rows and sample columns for PANDA/PUMA."""
    return format_expression_for_netzoo_impl(
        expression_file,
        output_file,
        genes_axis,
        with_header,
        execute=settings.EXECUTE_TOOLS,
    )


@tool
def convert_expression_to_coexpression(
    expression_file: str,
    output_file: str,
) -> str:
    """Convert expression to a gene-by-gene Pearson correlation matrix."""
    return convert_expression_to_coexpression_impl(
        expression_file,
        output_file,
        execute=settings.EXECUTE_TOOLS,
    )


__all__ = [
    "inspect_netzoo_inputs",
    "inspect_cobra_inputs",
    "inspect_dragon_inputs",
    "format_expression_for_netzoo",
    "convert_expression_to_coexpression",
]
