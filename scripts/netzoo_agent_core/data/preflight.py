"""Side-effect-free input validation shared by Planning and /execute."""

from __future__ import annotations

from typing import Any

from .cobra import inspect_cobra_inputs_impl
from .dragon import inspect_dragon_inputs_impl
from .coexpression import read_coexpression_matrix
from .inspection import inspect_condor_inputs_impl
from .tables import _inspect_panda_inputs_impl, _read_checked_table, _validate_expression
from .transforms import (
    convert_expression_to_coexpression_impl,
    format_expression_for_netzoo_impl,
)

__all__ = ["validate_workflow_inputs"]


def _value(decision: Any, field_name: str) -> str:
    if isinstance(decision, dict):
        return str(decision.get(field_name) or "")
    return str(getattr(decision, field_name, None) or "")


def _report_errors(label: str, report: str, ok: bool) -> list[str]:
    if ok:
        return []
    errors = [
        line.strip()
        for line in report.splitlines()
        if "error:" in line.casefold()
    ]
    return [f"{label}: {error}" for error in errors] or [
        f"{label}: validation failed."
    ]


def _validate_expression_file(path: str, label: str = "expression") -> list[str]:
    check = _validate_expression(_read_checked_table(label, path))
    return [f"{label}: {error}" for error in check.errors]


def _validate_lioness_sample_count(path: str) -> list[str]:
    check = _validate_expression(_read_checked_table("expression", path))
    if check.errors or check.frame is None:
        return []
    sample_count = max(check.frame.shape[1] - 1, 0)
    if sample_count < 3:
        return [
            "expression: LIONESS requires at least three samples so each "
            "leave-one-out correlation still has at least two samples."
        ]
    return []


def validate_workflow_inputs(action: str, decision: Any) -> list[str]:
    """Return actionable content/format errors without writing any files.

    The same function is called after Planning resolves inputs and immediately
    before ``/execute`` grants one-shot execution authority. Runtime executors
    still validate again as the final defense at the tool boundary.
    """

    errors: list[str] = []
    expression = _value(decision, "expression_file")
    motif = _value(decision, "motif_file")
    ppi = _value(decision, "ppi_file")
    mirna = _value(decision, "mirna_file")

    if action in {"inspect_inputs", "run_panda", "run_puma", "run_lioness_panda", "run_lioness_puma"}:
        report, ok, inferred_header = _inspect_panda_inputs_impl(
            expression,
            motif,
            ppi,
            mirna
            if action in {"inspect_inputs", "run_puma", "run_lioness_puma"}
            else "",
        )
        errors.extend(_report_errors("PANDA/PUMA inputs", report, ok))
        if action == "run_puma" and inferred_header:
            errors.append(
                "expression: PUMA requires a headerless expression matrix; "
                "run format_expression with with_header=false first."
            )
        if action in {"run_lioness_panda", "run_lioness_puma"}:
            errors.extend(_validate_lioness_sample_count(expression))
    elif action in {"inspect_condor_inputs", "run_condor"}:
        report, ok = inspect_condor_inputs_impl(_value(decision, "network_file"))
        errors.extend(_report_errors("CONDOR network", report, ok))
    elif action in {"inspect_cobra_inputs", "run_cobra"}:
        report, ok = inspect_cobra_inputs_impl(expression, _value(decision, "design_file"))
        errors.extend(_report_errors("COBRA inputs", report, ok))
    elif action in {"inspect_dragon_inputs", "run_dragon"}:
        report, ok = inspect_dragon_inputs_impl(
            _value(decision, "omics_layer_1"),
            _value(decision, "omics_layer_2"),
        )
        errors.extend(_report_errors("DRAGON inputs", report, ok))
    elif action == "run_lioness_coexpression":
        errors.extend(_validate_expression_file(expression))
        errors.extend(_validate_lioness_sample_count(expression))
    elif action == "format_expression":
        report = format_expression_for_netzoo_impl(
            expression,
            _value(decision, "output_file"),
            _value(decision, "genes_axis") or "auto",
            bool(decision.get("with_header", False))
            if isinstance(decision, dict)
            else bool(getattr(decision, "with_header", False)),
            execute=False,
        )
        errors.extend(_report_errors("Expression formatting", report, "- error:" not in report))
    elif action == "convert_expression":
        report = convert_expression_to_coexpression_impl(
            expression,
            _value(decision, "output_file"),
            execute=False,
        )
        errors.extend(_report_errors("Expression conversion", report, "- error:" not in report))

    coexpression = _value(decision, "coexpression_file")
    if action in {"run_panda", "run_puma"} and coexpression:
        try:
            read_coexpression_matrix(coexpression)
        except (OSError, ValueError) as error:
            errors.append(f"coexpression_file: {error}")

    return list(dict.fromkeys(errors))
