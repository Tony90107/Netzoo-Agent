"""Historical facade for table validation and the decorated inspection tool."""

from ..tool_adapters import inspect_netzoo_inputs
from .tables import (
    TableCheck,
    _drop_common_header,
    _identifier_overlap_report,
    _inspect_panda_inputs_impl,
    _looks_numeric,
    _read_checked_table,
    _read_expression_source,
    _resolve_user_path,
    _validate_edge_or_bed,
    _validate_expression,
    _validate_mirna_list,
)

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
    "inspect_netzoo_inputs",
]
