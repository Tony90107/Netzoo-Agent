"""User-facing rendering for plan reviews and execution outcomes."""

from __future__ import annotations

import re

from ..contracts import (
    EvaluationResult,
    PlanEvaluationResult,
    ToolExecutionResult,
    VERBOSE_OUTPUT,
    WorkflowPlan,
    _ui_text,
)
from ..outcomes import effective_results, terminal_failed
from ..validation import _resolve_user_path

def render_plan_evaluation(evaluation: PlanEvaluationResult) -> str:
    """Render the typed rubric as Markdown for audit; code never parses this table."""

    def cell(value: str) -> str:
        return value.replace("|", "\\|").replace("\n", " ")

    lines = [
        "| Criterion | Required | Result | Detail |",
        "|---|---:|---|---|",
    ]
    for item in evaluation.rubric:
        lines.append(
            f"| {cell(item.criterion)} | {'yes' if item.required else 'no'} | "
            f"{item.result} | {cell(item.detail)} |"
        )
    lines.extend(
        [
            "",
            f"Plan evaluation: **{evaluation.status}** ({evaluation.score}/100).",
            evaluation.summary,
        ]
    )
    return "\n".join(lines)


def render_plan_rejection_response(evaluation: PlanEvaluationResult) -> str:
    return (
        "No tool was executed because the pre-execution Plan Evaluator rejected "
        "the plan.\n\n" + render_plan_evaluation(evaluation)
    )


def render_verbose_execution_response(
    plan: WorkflowPlan,
    results: list[ToolExecutionResult],
    evaluation: EvaluationResult | None,
) -> str:
    """Render the full auditable execution report used by --verbose."""
    results = effective_results(results)
    has_failure = terminal_failed(results, evaluation)
    has_dry_run = any(item.status == "dry_run" for item in results)
    if has_failure:
        headline = "The workflow stopped because the Evaluator detected a validation or execution failure."
    elif has_dry_run:
        headline = "The command preview completed. This was a dry run; the analysis tool was not executed."
    else:
        headline = "The workflow completed, and the output artifacts passed the Executor existence checks."

    lines = [headline, "", f"Workflow: {plan.workflow}", "", "Step results:"]
    for index, item in enumerate(results, 1):
        marker = (
            "✓"
            if item.status == "success"
            else "◌"
            if item.status == "dry_run"
            else "✗"
        )
        lines.append(f"{index}. {marker} {item.action} — {item.status}")
        if item.metrics:
            useful_metrics = {
                key: value
                for key, value in item.metrics.items()
                if key not in {"raw_output_chars", "raw_output_truncated"}
            }
            if useful_metrics:
                lines.append(
                    "   metrics: "
                    + ", ".join(
                        f"{key}={value}" for key, value in useful_metrics.items()
                    )
                )
        for warning in item.warnings:
            lines.append(f"   warning: {warning}")
        for error in item.errors:
            lines.append(f"   error: {error}")
        if item.log_file:
            lines.append(f"   log: {item.log_file}")

    artifacts = []
    for item in results:
        if item.status != "success":
            continue
        for artifact in item.artifacts:
            if artifact not in artifacts:
                artifacts.append(artifact)
    if artifacts:
        lines.extend(["", "Output artifacts:"])
        for artifact in artifacts:
            path = _resolve_user_path(artifact)
            if path.is_file():
                lines.append(f"- {artifact} ({path.stat().st_size} bytes)")
            elif path.is_dir():
                lines.append(f"- {artifact}/ (directory)")
            else:
                lines.append(f"- {artifact} (not created)")

    inspection_results = [
        item
        for item in results
        if item.action.startswith("inspect_") and item.raw_output
    ]
    if inspection_results:
        lines.extend(["", "Validation summary:", inspection_results[-1].raw_output])
    if evaluation:
        lines.extend(["", f"Evaluator: {evaluation.status} — {evaluation.reason}"])
    return "\n".join(lines)


def _compact_field_label(field_name: str) -> str:
    return {
        "expression_file": "Expression",
        "motif_file": "Motif/prior",
        "ppi_file": "PPI",
        "mirna_file": "miRNA list",
        "network_file": "Network",
        "output_file": "Aggregate/network output",
        "lioness_output": "Sample-specific output",
        "output_dir": "Output directory",
    }.get(field_name, field_name.replace("_", " ").capitalize())


def _extract_command_preview(results: list[ToolExecutionResult]) -> str | None:
    for item in reversed(results):
        fenced = re.search(r"```bash\s*\n([^\n]+)", item.raw_output)
        if fenced:
            return fenced.group(1).strip()
        executed = re.search(r"^Command:\s*`([^`]+)`", item.raw_output, re.MULTILINE)
        if executed:
            return executed.group(1).strip()
    return None


def _compact_validation_highlights(results: list[ToolExecutionResult]) -> list[str]:
    inspection = next(
        (
            item
            for item in reversed(results)
            if item.action.startswith("inspect_") and item.status == "success"
        ),
        None,
    )
    if not inspection:
        return []
    highlights = []
    expression_section = re.search(
        r"- expression:.*?\n(?:.*\n){0,5}?\s*shape:\s*([^\n]+)",
        inspection.raw_output,
        flags=re.IGNORECASE,
    )
    if expression_section:
        highlights.append(f"Expression shape: {expression_section.group(1).strip()}")
    labels = {
        "motif target genes overlapping expression genes": "Motif targets ↔ expression genes",
        "motif tfs overlapping ppi tfs": "Motif TFs ↔ PPI TFs",
        "mirna names overlapping motif/prior regulators": "miRNAs ↔ motif/prior regulators",
    }
    for raw_line in inspection.raw_output.splitlines():
        line = raw_line.strip().removeprefix("- ")
        lowered = line.casefold()
        for prefix, label in labels.items():
            if lowered.startswith(prefix + ":"):
                highlights.append(f"{label}: {line.split(':', 1)[1].strip()}")
                break
    return highlights[:4]


def render_compact_execution_response(
    plan: WorkflowPlan,
    results: list[ToolExecutionResult],
    evaluation: EvaluationResult | None,
) -> str:
    """Render the default user-facing result with progressive disclosure."""
    results = effective_results(results)
    has_failure = terminal_failed(results, evaluation)
    has_dry_run = any(item.status == "dry_run" for item in results)
    status = "FAILED" if has_failure else "DRY RUN" if has_dry_run else "COMPLETED"
    lines = [f"{plan.workflow} · {status}"]

    input_evidence = [
        item
        for item in plan.evidence
        if item.value
        and item.field not in {"output_file", "lioness_output", "output_dir"}
    ]
    if input_evidence:
        lines.extend(["", "Inputs"])
        for item in input_evidence:
            source = {
                "provided": "provided",
                "selected": "selected",
                "discovered": "auto-discovered",
                "demo_bundle": "demo bundle",
                "defaulted": "default",
            }.get(item.status, item.status)
            lines.append(
                f"- {_compact_field_label(item.field)}: {item.value} [{source}]"
            )

    inspection = next(
        (item for item in results if item.action.startswith("inspect_")), None
    )
    if inspection:
        lines.extend(["", "Validation"])
        marker = "✓" if inspection.status == "success" else "✗"
        verdict = (
            "Input formats and identifier compatibility passed."
            if inspection.status == "success"
            else "Input validation failed."
        )
        lines.append(f"{marker} {verdict}")
        for highlight in _compact_validation_highlights(results):
            lines.append(f"- {highlight}")

    lines.extend(["", "Result"])
    if has_failure:
        lines.append("✗ The workflow stopped before successful completion.")
    elif has_dry_run:
        lines.append("○ Command preview ready; no analysis was executed.")
    else:
        lines.append("✓ The workflow completed successfully.")

    warnings = [warning for item in results for warning in item.warnings]
    errors = [error for item in results for error in item.errors]
    for warning in warnings:
        lines.append(f"Warning: {warning}")
    for error in errors:
        lines.append(f"Error: {error}")

    command = _extract_command_preview(results)
    if has_dry_run and command:
        lines.extend(["", "Command", command])

    output_evidence = [
        item
        for item in plan.evidence
        if item.value and item.field in {"output_file", "lioness_output", "output_dir"}
    ]
    if output_evidence:
        heading = "Planned outputs" if has_dry_run else "Outputs"
        lines.extend(["", heading])
        for item in output_evidence:
            path = _resolve_user_path(item.value)
            suffix = ""
            if not has_dry_run and path.is_file():
                suffix = f" ({path.stat().st_size} bytes)"
            elif not has_dry_run and not path.exists():
                suffix = " (not created)"
            lines.append(f"- {_compact_field_label(item.field)}: {item.value}{suffix}")

    if has_failure:
        log_files = [item.log_file for item in results if item.log_file]
        if log_files:
            lines.extend(["", "Diagnostic logs"])
            lines.extend(f"- {path}" for path in log_files)
        if evaluation:
            lines.extend(["", f"Next: {evaluation.reason}"])
    elif has_dry_run:
        lines.extend(["", "Next: rerun with --execute to perform the analysis."])
    return "\n".join(lines)


def render_execution_response(
    plan: WorkflowPlan,
    results: list[ToolExecutionResult],
    evaluation: EvaluationResult | None,
    verbose: bool | None = None,
) -> str:
    """Select the compact default or the full --verbose execution report."""
    use_verbose = VERBOSE_OUTPUT if verbose is None else verbose
    renderer = (
        render_verbose_execution_response
        if use_verbose
        else render_compact_execution_response
    )
    return renderer(plan, results, evaluation)


def render_needs_input_response(plan: WorkflowPlan) -> str:
    if "lioness_mode" in plan.missing_inputs:
        return _ui_text(
            "No tool was executed because the LIONESS base method is ambiguous. "
            "Choose one of the listed modes to continue."
        )
    lines = [
        _ui_text("No tool was executed because the Planner requires additional input."),
        "",
    ]
    lines.append(plan.question or _ui_text("Please provide the missing input paths."))
    return "\n".join(lines)


def render_preference_confirmation_response(plan: WorkflowPlan) -> str:
    lines = [
        _ui_text(
            "No preference has been saved yet. Explicit confirmation is required."
        ),
        "",
        _ui_text("Proposed long-term preferences:"),
    ]
    for proposal in plan.preference_proposals:
        lines.append(f"- {proposal.key} = {proposal.value}")
        lines.append(_ui_text("  Reason: ") + proposal.reason)
    return "\n".join(lines)
