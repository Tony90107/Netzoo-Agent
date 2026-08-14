"""Normalize legacy tool output into the typed executor contract."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Literal

from ..data.artifacts import ARTIFACT_WRITE_ACTIONS, validate_output_artifacts
from ..contracts import (
    TOOL_LOG_ROOT,
    TOOL_RAW_MAX_CHARS,
    TaskDecision,
    ToolExecutionResult,
    _display_path,
)
from ..memory import _ensure_private_directory, _write_private_text
from ..execution_log import write_execution_markdown_log
from .error_adapters import (
    ToolErrorContext,
    adapt_tool_error,
    extract_reported_error_codes,
)

__all__ = [
    "_expected_artifacts",
    "_diagnostic_messages",
    "structure_tool_result",
]


def _expected_artifacts(decision: TaskDecision, action: str) -> list[str]:
    if action in {"format_expression", "convert_expression", "run_panda", "run_puma"}:
        return [decision.output_file] if decision.output_file else []
    if action.startswith("run_lioness_"):
        return [
            path for path in (decision.output_file, decision.lioness_output) if path
        ]
    if action == "run_condor" and decision.output_dir:
        return [decision.output_dir]
    return []


def _diagnostic_messages(
    raw_output: str, label: Literal["error", "warning"]
) -> list[str]:
    """Extract line-leading diagnostics without coupling to one Markdown bullet style."""
    pattern = re.compile(
        rf"^\s*(?:[-*•]\s*)?{label}\s*:\s*(.+?)\s*$",
        flags=re.IGNORECASE,
    )
    messages = []
    for line in raw_output.splitlines():
        match = pattern.match(line)
        if match:
            messages.append(match.group(1).strip())
    return messages


def structure_tool_result(
    action: str,
    decision: TaskDecision,
    raw_output: str,
    persist_log: bool = False,
    persist_execution_log: bool = False,
    attempt_id: int = 0,
    execution_started_at: datetime | None = None,
) -> ToolExecutionResult:
    """Normalize legacy text-returning tools into a stable executor contract."""
    lowered = raw_output.casefold()
    error_lines = _diagnostic_messages(raw_output, "error")
    warning_lines = _diagnostic_messages(raw_output, "warning")
    exit_match = re.search(r"Exit code:\s*(\d+)", raw_output, flags=re.IGNORECASE)
    exit_code = int(exit_match.group(1)) if exit_match else None
    hard_failure_markers = (
        "validation failed",
        "traceback",
        "lookup failed",
        "did not create or update expected output",
    )
    failed = (
        bool(error_lines)
        or (exit_code is not None and exit_code != 0)
        or any(marker in lowered for marker in hard_failure_markers)
    )
    diagnosis = adapt_tool_error(
        ToolErrorContext(
            action=action,
            reported_error_codes=extract_reported_error_codes(raw_output),
            errors=error_lines,
            exit_code=exit_code,
        )
    )
    if diagnosis is not None:
        failed = True
    dry_run = "dry run only" in lowered or "dry-run" in lowered
    artifacts = _expected_artifacts(decision, action)
    metrics: dict[str, int | float | str | bool] = {}
    if exit_code is not None:
        metrics["exit_code"] = exit_code
    if not failed and not dry_run and action in ARTIFACT_WRITE_ACTIONS:
        artifact_check = validate_output_artifacts(action, decision)
        metrics.update(artifact_check.metrics)
        warning_lines.extend(artifact_check.warnings)
        if artifact_check.ok:
            artifacts = artifact_check.artifacts
        else:
            failed = True
            error_lines.extend(artifact_check.errors)

    status: Literal["success", "dry_run", "failed"]
    status = "failed" if failed else "dry_run" if dry_run else "success"

    summary = {
        "success": "The tool completed and passed structured result checks.",
        "dry_run": "The dry run completed; the analysis command was not executed.",
        "failed": "The tool or its validation failed.",
    }[status]
    if failed and not error_lines:
        error_lines = [summary]
    log_file = None
    if persist_log:
        _ensure_private_directory(TOOL_LOG_ROOT)
        log_path = TOOL_LOG_ROOT / f"{action}-{uuid.uuid4().hex[:12]}.log"
        _write_private_text(log_path, raw_output)
        log_file = _display_path(log_path)
    bounded_output = raw_output
    if len(raw_output) > TOOL_RAW_MAX_CHARS:
        head = TOOL_RAW_MAX_CHARS * 2 // 3
        tail = TOOL_RAW_MAX_CHARS - head
        bounded_output = (
            raw_output[:head]
            + f"\n\n[tool output truncated; full log: {log_file or '(not persisted)'}]\n\n"
            + raw_output[-tail:]
        )
        metrics["raw_output_truncated"] = True
    else:
        metrics["raw_output_truncated"] = False
    metrics["raw_output_chars"] = len(raw_output)
    if persist_execution_log and status != "dry_run":
        try:
            execution_log = write_execution_markdown_log(
                decision,
                action=action,
                raw_output=raw_output,
                status=status,
                artifacts=artifacts,
                warnings=warning_lines,
                errors=error_lines,
                started_at=execution_started_at,
            )
            if execution_log:
                metrics["execution_markdown_log"] = execution_log
        except OSError as error:
            warning_lines.append(f"Execution Markdown log could not be written: {error}")
    return ToolExecutionResult(
        action=action,
        status=status,
        summary=summary,
        attempt_id=attempt_id,
        artifacts=artifacts,
        metrics=metrics,
        warnings=warning_lines,
        errors=error_lines,
        error_code=diagnosis.error_code if diagnosis else None,
        retryable=diagnosis.retryable if diagnosis else False,
        recovery_hint=diagnosis.recovery_action if diagnosis else None,
        log_file=log_file,
        raw_output=bounded_output,
    )
