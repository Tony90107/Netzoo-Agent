"""Public Markdown audit logs for executed workflow steps."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from .contracts.decisions import TaskDecision

__all__ = ["write_execution_markdown_log"]


def _log_directory(decision: TaskDecision) -> Path | None:
    if decision.output_dir:
        return Path(decision.output_dir)
    for value in (decision.output_file, decision.lioness_output):
        if value:
            return Path(value).parent
    return None


def _command(raw_output: str) -> str:
    match = re.search(r"^Command:\s*`(.+?)`\s*$", raw_output, re.MULTILINE)
    return match.group(1) if match else "No command was started."


def _next_path(directory: Path, action: str, timestamp: str) -> Path:
    stem = f"{action.removeprefix('run_')}-execution-{timestamp}"
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
    directory.mkdir(parents=True, exist_ok=True)
    path = _next_path(directory, action, started_at.strftime("%Y%m%d-%H%M%S"))
    lines = [
        "# NetZoo execution record",
        "",
        f"- Started: {started_at.isoformat(timespec='seconds')}",
        f"- Finished: {finished_at.isoformat(timespec='seconds')}",
        f"- Action: `{action}`",
        f"- Status: `{status}`",
        "",
        "## Executed command",
        "",
        "```bash",
        _command(raw_output),
        "```",
        "",
        "## Preparation and execution report",
        "",
        raw_output or "No adapter report was returned.",
    ]
    if artifacts:
        lines.extend(["", "## Output artifacts", "", *(f"- `{path}`" for path in artifacts)])
    if warnings:
        lines.extend(["", "## Warnings", "", *(f"- {item}" for item in warnings)])
    if errors:
        lines.extend(["", "## Errors", "", *(f"- {item}" for item in errors)])
    with path.open("x", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return str(path)
