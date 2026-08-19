"""LangChain adapters for pure workflow data operations."""

from __future__ import annotations

from pathlib import Path

from . import settings
from .data.resource_inventory import inventory_workspace_resources
from .data.tables import inspect_netzoo_inputs_report
from .data.transforms import (
    convert_expression_to_coexpression_impl,
    format_expression_for_netzoo_impl,
)
from .framework_compat import tool
from .settings import PROJECT_ROOT


@tool
def discover_workspace_resources(
    workspace_root: str,
    resource_subpath: str | None = None,
    resource_actions: list[str] | None = None,
) -> str:
    """Inventory compatible input resources inside the NetZoo workspace read-only."""
    project_root = PROJECT_ROOT.resolve()
    requested_root = Path(workspace_root).expanduser().resolve()
    if not requested_root.is_relative_to(project_root):
        raise ValueError("workspace_root must remain inside the NetZoo workspace")
    search_root = requested_root
    if resource_subpath:
        search_root = (requested_root / resource_subpath).resolve()
    if not search_root.is_relative_to(requested_root) or not search_root.is_relative_to(
        project_root
    ):
        raise ValueError("resource_subpath must remain beneath workspace_root")
    inventory = inventory_workspace_resources(
        search_root,
        resource_actions or [],
    )
    return inventory.model_dump_json()


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
    "discover_workspace_resources",
    "inspect_netzoo_inputs",
    "format_expression_for_netzoo",
    "convert_expression_to_coexpression",
]
