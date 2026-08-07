"""Compatibility facade for workflow data preparation."""

from .data.preparation import convert_expression_to_coexpression, format_expression_for_netzoo

__all__ = ["format_expression_for_netzoo", "convert_expression_to_coexpression"]
