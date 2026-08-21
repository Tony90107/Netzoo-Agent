"""Public Markdown audit logs for executed workflow steps."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .contracts.decisions import TaskDecision

__all__ = ["write_execution_markdown_log"]


# Containers commonly run in UTC. Logs are user-facing artifacts, so render
# their timestamps in Taiwan time instead of exposing an opaque UTC clock.
_LOG_TIMEZONE = ZoneInfo("Asia/Taipei")


def _log_directory(decision: TaskDecision) -> Path | None:
    if decision.output_dir:
        return Path(decision.output_dir)
    for value in (decision.output_file, decision.lioness_output):
        if value:
            return Path(value).parent
    return None


def _command(raw_output: str, action: str) -> str:
    match = re.search(r"^Command:\s*`(.+?)`\s*$", raw_output, re.MULTILINE)
    if match:
        return match.group(1)
    if action == "inspect_inputs":
        return "Not applicable — input inspection only."
    return "No command was started."


def _user_path(value: str) -> str:
    """Hide the container mount prefix from user-facing Markdown logs."""
    return value.replace("/work/", "")


def _structured_report(raw_output: str) -> tuple[list[str], list[str], list[str]]:
    """Turn the adapter's verbose stdout into concise public-log bullets."""
    preparation: list[str] = []
    execution: list[str] = []
    outputs: list[str] = []
    section = "preparation"
    for raw_line in raw_output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("Command:"):
            continue
        if line == "STDOUT:":
            section = "execution"
            continue
        if line == "STDERR:":
            section = "outputs"
            continue
        if line.startswith("Output file:"):
            # Output paths are represented by the artifact section, not as a
            # tool notice.
            continue
        if line.startswith("Exit code:"):
            execution.append(line)
            continue
        if line.startswith("step:") or line.startswith("Elapsed time:"):
            continue
        if line.startswith("NEW:"):
            outputs.append(line)
            continue
        if section == "preparation":
            preparation.append(_user_path(line.lstrip("- ")))
        elif section == "execution":
            # Keep meaningful milestones while omitting the algorithm's
            # progress stream, which is too noisy for a human-facing log.
            if not line.startswith("/opt/"):
                execution.append(line)
    return preparation, execution, outputs


def _runtime_warnings(raw_output: str) -> list[str]:
    """Collapse multiline Python warnings into one readable bullet."""
    warnings: list[str] = []
    for line in raw_output.splitlines():
        line = line.strip()
        if "UserWarning:" in line:
            warnings.append(line.split("UserWarning:", 1)[1].strip())
    return warnings


def _next_path(directory: Path, action: str, timestamp: str) -> Path:
    stem = f"{action.removeprefix('run_')}-execution-{timestamp}_TW"
    for index in range(1000):
        suffix = "" if index == 0 else f"-{index}"
        candidate = directory / f"{stem}{suffix}.md"
        if not candidate.exists():
            return candidate
    raise FileExistsError("Could not allocate a unique execution-log filename.")


def write_execution_markdown_log(
    decision: TaskDecision,
    *,
    action: str,
    raw_output: str,
    status: str,
    artifacts: list[str],
    warnings: list[str],
    errors: list[str],
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
) -> str | None:
    """Write one non-overwriting Markdown record beside a workflow output."""
    directory = _log_directory(decision)
    if directory is None:
        return None
    started_at = started_at or datetime.now().astimezone()
    finished_at = finished_at or datetime.now().astimezone()
    started_at = started_at.astimezone(_LOG_TIMEZONE)
    finished_at = finished_at.astimezone(_LOG_TIMEZONE)
    directory.mkdir(parents=True, exist_ok=True)
    path = _next_path(directory, action, started_at.strftime("%Y-%m-%d_%H-%M-%S"))
    preparation, execution, notices = _structured_report(raw_output)
    public_warnings = list(dict.fromkeys([*warnings, *_runtime_warnings(raw_output)]))
    summary_lines = [
        f"- Workflow: `{action.removeprefix('run_').upper()}`",
        f"- Status: `{status}`",
        f"- Started (Taiwan time): {started_at.isoformat(timespec='seconds')}",
        f"- Finished (Taiwan time): {finished_at.isoformat(timespec='seconds')}",
    ]
    if action == "inspect_inputs":
        summary_lines.append(
            f"- Validation result: {'passed' if status == 'success' else 'failed'}"
        )
    lines = [
        "# NetZoo execution summary",
        "",
        "## Summary",
        "",
        *summary_lines,
        "",
        "## Executed command",
        "",
        "```bash",
        _command(raw_output, action),
        "```",
    ]
    if preparation:
        lines.extend(["", "## Inputs and validation", "", *(f"- {item}" for item in preparation)])
    if execution:
        lines.extend(["", "## Execution", "", *(f"- {item}" for item in execution)])
    if artifacts:
        lines.extend(["", "## Output artifacts", "", *(f"- `{_user_path(path)}`" for path in artifacts)])
    if notices:
        lines.extend(["", "## Tool notices", "", *(f"- {item}" for item in notices)])
    if public_warnings:
        lines.extend(["", "## Warnings", "", *(f"- {item}" for item in public_warnings)])
    if errors:
        lines.extend(["", "## Errors", "", *(f"- {item}" for item in errors)])
    with path.open("x", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return str(path)
