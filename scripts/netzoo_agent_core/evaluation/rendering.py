"""User-facing rendering for plan reviews and execution outcomes."""

from __future__ import annotations

import json
import re
from urllib.parse import urlparse

from ..contracts import (
    EvaluationResult,
    PlanEvaluationResult,
    ToolExecutionResult,
    VERBOSE_OUTPUT,
    WorkflowPlan,
    _ui_text,
)
from ..outcomes import effective_results, terminal_failed
from ..data.paths import _resolve_user_path

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
        "coexpression_file": "Adjusted co-expression",
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
                "derived": "derived input",
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

    warnings = list(
        dict.fromkeys(warning for item in results for warning in item.warnings)
    )
    errors = [error for item in results for error in item.errors]
    for warning in warnings:
        # netZooPy reports its default TSV header behavior as a WARNING, but
        # this is informational and does not indicate a failed workflow.
        if "saved with the column names" in warning.casefold():
            lines.append("Notice: Output format: TSV with column headers.")
        else:
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


def render_retrieval_failure_response(
    decision, results: list[ToolExecutionResult]
) -> str | None:
    """Render retrieval failure without converting it into a negative hit."""
    if decision.action not in {"web_search", "query_context7"}:
        return None
    failed = [item for item in results if item.status == "failed"]
    if not failed:
        return None
    label = "Websearch" if decision.action == "web_search" else "Context7"
    lines = [
        f"{label} lookup failed before an authoritative result was retrieved.",
        "This is an unavailable/unknown result, not evidence that the requested record was not found.",
        "No local analysis workflow was executed.",
    ]
    details = list(dict.fromkeys(
        detail for item in failed for detail in (item.errors or [item.summary])
    ))
    if details:
        lines.extend(["", "Details:", *[f"- {detail}" for detail in details]])
    return "\n".join(lines)


def render_authority_search_response(
    task: str, decision, results: list[ToolExecutionResult]
) -> str | None:
    """Render exact NCBI/Ensembl discovery requests from trusted URLs only."""
    lowered = task.casefold()
    if not ("ncbi" in lowered or "ensembl" in lowered) or not any(
        item.status == "success" for item in results
    ):
        return None
    identifiers = list(dict.fromkeys(
        re.findall(r"\bENSG\d{5,}\b", task, re.IGNORECASE)
        + re.findall(r"(?:資料|data|gene)\s*[:：]\s*([A-Za-z][A-Za-z0-9_-]{1,20})", task, re.IGNORECASE)
    ))
    if not identifiers:
        identifiers = [
            token for token in re.findall(r"\b[A-Z][A-Z0-9_-]{2,20}\b", task)
            if token not in {"NCBI", "GENE", "ENSEMBL", "WEB", "SEARCH"}
        ]
    if not identifiers:
        return None

    def payload(raw: str) -> dict:
        _, separator, body = raw.partition("\n\n")
        if not separator:
            return {}
        try:
            value = json.loads(body)
        except json.JSONDecodeError:
            return {}
        return value if isinstance(value, dict) else {}

    def authority(url: str) -> str | None:
        host = (urlparse(url).hostname or "").casefold().lstrip("www.")
        if host == "ncbi.nlm.nih.gov" and re.search(r"/gene/\d+", url):
            return "NCBI Gene"
        if host == "ensembl.org" and urlparse(url).scheme in {"http", "https"}:
            return "Ensembl"
        return None

    matches: dict[str, list[dict[str, object]]] = {identifier: [] for identifier in identifiers}
    for item in results:
        for result in payload(item.raw_output).get("results", []):
            if not isinstance(result, dict):
                continue
            url = str(result.get("url") or "")
            source = authority(url)
            if source is None:
                continue
            title_url = " ".join(str(result.get(key) or "") for key in ("title", "url"))
            content = str(result.get("content") or "")
            for identifier in identifiers:
                pattern = rf"(?<![A-Za-z0-9]){re.escape(identifier)}(?![A-Za-z0-9])"
                if identifier.upper().startswith("ENSG"):
                    exact = re.search(pattern, title_url, re.IGNORECASE)
                else:
                    title = str(result.get("title") or "")
                    exact = re.match(
                        rf"\s*{re.escape(identifier)}(?![A-Za-z0-9])",
                        title,
                        re.IGNORECASE,
                    ) or re.search(
                        rf"Official Symbol\s+{re.escape(identifier)}(?![A-Za-z0-9])",
                        content,
                        re.IGNORECASE,
                    )
                if exact:
                    matches[identifier].append({"source": source, "url": url, "result": result})

    taxon_match = re.search(r"\b(Homo sapiens|Mus musculus)\b", task, re.IGNORECASE)
    taxon = taxon_match.group(1) if taxon_match else ""
    lines = ["Official NCBI/Ensembl Websearch exact-match report (discovery evidence):"]
    for identifier in identifiers:
        candidates = matches[identifier]
        if not candidates:
            lines.append(f"- {identifier}: Websearch 未找到 exact trusted result.")
            continue
        for candidate in candidates[:3]:
            result = candidate["result"]
            url = str(candidate["url"])
            gene_id = (re.search(r"/gene/(\d+)", url) or [None, ""])[1]
            ensembl = (re.search(r"\bENSG\d{5,}\b", " ".join(str(result.get(k) or "") for k in ("title", "content", "url")), re.IGNORECASE) or [""])[0].upper()
            symbol = identifier if not identifier.upper().startswith("ENSG") else ""
            symbol_match = re.search(r"Official Symbol\s+([A-Za-z0-9_-]+)", str(result.get("content") or ""), re.IGNORECASE)
            symbol = symbol_match.group(1) if symbol_match else symbol
            evidence = " ".join(str(result.get("content") or "").split())[:320]
            lines.extend([
                f"- {identifier}: exact trusted match",
                f"  authority={candidate['source']}; canonical_id={gene_id or ensembl or 'unparsed'}; symbol={symbol or 'unparsed'}; taxon={taxon or 'from source'}",
                f"  url={url}",
                f"  evidence={evidence}",
            ])
    lines.append("Websearch evidence alone does not authorize a workflow or prove authoritative absence.")
    return "\n".join(lines)


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


def render_input_confirmation_response(plan: WorkflowPlan) -> str:
    lines = [
        "No tool was executed because the local input selection needs confirmation.",
        "",
        plan.question or "Are these the files you want to use? [y/N]",
    ]
    return "\n".join(lines)
