"""Public Markdown audit logs for executed workflow steps."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .contracts.decisions import TaskDecision

__all__ = ["write_execution_markdown_log"]


# Containers commonly run in UTC. Logs are user-facing artifacts, so render
# their timestamps in Taiwan time instead of exposing an opaque UTC clock.
_LOG_TIMEZONE = ZoneInfo("Asia/Taipei")


@dataclass
class _ReportBlock:
    """A titled block with optional child facts from adapter output."""

    title: str
    details: list[str] = field(default_factory=list)


@dataclass
class _StructuredReport:
    """Normalized facts used to render the human-facing execution report."""

    input_blocks: list[_ReportBlock] = field(default_factory=list)
    validation_blocks: list[_ReportBlock] = field(default_factory=list)
    validation_lines: list[str] = field(default_factory=list)
    execution: list[_ReportBlock] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)
    exit_code: str | None = None
    compute_duration_seconds: float | None = None
    compute_device: str | None = None


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


def _split_key_value(value: str) -> tuple[str, str] | None:
    if ":" not in value:
        return None
    key, detail = value.split(":", 1)
    key = key.strip()
    detail = detail.strip()
    if not key or not detail:
        return None
    return key, detail


def _append_preparation_block(
    report: _StructuredReport,
    block: _ReportBlock,
) -> None:
    """Keep input facts and cross-input checks as separate titled blocks."""
    if not block.details:
        report.validation_lines.append(_user_path(block.title))
        return
    input_labels = {
        "expression",
        "motif",
        "ppi",
        "mirna",
        "coexpression",
        "network",
    }
    key_value = _split_key_value(block.title)
    key = key_value[0].casefold() if key_value else ""
    if key in input_labels:
        if key_value:
            block.title = key_value[0]
            block.details.insert(0, f"path: {key_value[1]}")
        report.input_blocks.append(block)
    else:
        report.validation_blocks.append(block)


def _parse_preparation(lines: list[str], report: _StructuredReport) -> None:
    pending: _ReportBlock | None = None
    for raw_line in lines:
        raw = raw_line.rstrip()
        line = raw.strip()
        if not line or line.casefold() in {"preparation:", "input inspection:"}:
            continue
        indent = len(raw) - len(raw.lstrip())
        if indent == 0 and line.startswith("- "):
            if pending is not None:
                _append_preparation_block(report, pending)
            pending = _ReportBlock(line[2:].strip())
            continue
        if pending is not None and indent > 0:
            pending.details.append(_user_path(line.lstrip("- ")))
            continue
        if pending is not None:
            _append_preparation_block(report, pending)
            pending = None
        report.validation_lines.append(_user_path(line.lstrip("- ")))
    if pending is not None:
        _append_preparation_block(report, pending)


def _append_execution_step(
    report: _StructuredReport,
    title: str,
    details: list[str] | None = None,
) -> None:
    title = _user_path(title.rstrip(".! "))
    if not title:
        return
    report.execution.append(_ReportBlock(title, details or []))


def _parse_execution(lines: list[str], report: _StructuredReport) -> None:
    pending: _ReportBlock | None = None
    for raw_line in lines:
        raw = raw_line.rstrip()
        line = raw.strip()
        if not line:
            continue
        if line.startswith("Exit code:"):
            report.exit_code = line.split(":", 1)[1].strip()
            continue
        if line.startswith("step:") or line.startswith("Elapsed time:"):
            continue
        if line.startswith("Output file:"):
            continue
        if line.startswith("NEW:"):
            report.notices.append(line)
            continue
        if line.startswith("Use old_compatible="):
            report.notices.append(line)
            continue
        if line.startswith("WARNING:") or "UserWarning:" in line:
            continue
        if line.startswith("/opt/") or line.startswith("union "):
            continue
        compute_duration = re.search(
            r"running\s+panda\s+took:\s*"
            r"([0-9]+(?:\.[0-9]+)?)\s*seconds",
            line,
            flags=re.IGNORECASE,
        )
        if compute_duration:
            report.compute_duration_seconds = float(compute_duration.group(1))
        compute_device = re.match(
            r"computing\s+panda\s+on\s+(.+)", line, flags=re.IGNORECASE
        )
        if compute_device:
            report.compute_device = compute_device.group(1).strip().rstrip(".! ")
        indent = len(raw) - len(raw.lstrip())
        if pending is not None and indent > 0:
            pending.details.append(_user_path(line.lstrip("- ")))
            continue
        if pending is not None:
            report.execution.append(pending)
            pending = None

        # The adapter emits a small input manifest before the actual
        # milestones. Keep it together instead of presenting every path as a
        # separate execution step.
        if line == "Input data:":
            pending = _ReportBlock(line)
            continue
        if pending is None and report.execution:
            previous = report.execution[-1]
            if previous.title == "Input data:" and _split_key_value(line):
                previous.details.append(_user_path(line))
                continue
        _append_execution_step(report, line)
    if pending is not None:
        report.execution.append(pending)


def _structured_report(raw_output: str) -> _StructuredReport:
    """Turn adapter output into structured, human-facing report sections."""
    report = _StructuredReport()
    preparation: list[str] = []
    execution: list[str] = []
    section = "preparation"
    for raw_line in raw_output.splitlines():
        line = raw_line.strip()
        if line.startswith("Exit code:"):
            report.exit_code = line.split(":", 1)[1].strip()
            continue
        if line.startswith("NEW:"):
            report.notices.append(line)
            continue
        if line.startswith("Use old_compatible="):
            report.notices.append(line)
            continue
        if line.startswith("WARNING:") or "UserWarning:" in line:
            continue
        if line == "STDOUT:":
            section = "execution"
            continue
        if line == "STDERR:":
            section = "stderr"
            continue
        if section == "preparation":
            if not line.startswith("Command:"):
                preparation.append(raw_line)
        elif section == "execution":
            execution.append(raw_line)
    _parse_preparation(preparation, report)
    _parse_execution(execution, report)
    return report


def _runtime_warnings(raw_output: str) -> list[str]:
    """Collapse multiline Python warnings into one readable bullet."""
    warnings: list[str] = []
    for line in raw_output.splitlines():
        line = line.strip()
        if line.startswith("WARNING:"):
            warnings.append(line.split(":", 1)[1].strip())
        elif "UserWarning:" in line:
            warnings.append(line.split("UserWarning:", 1)[1].strip())
    return warnings


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _format_notice(value: str) -> str:
    """Translate adapter compatibility chatter into a user-facing notice."""
    normalized = value.strip()
    lowered = normalized.casefold()
    if "save_tmp" in lowered:
        return "Temporary files are not saved by default."
    if "old_compatible" in lowered:
        return "Legacy headerless output is available with `old_compatible=True`."
    if "saved with the column names" in lowered or "column headers" in lowered:
        return "PANDA output includes column headers by default."
    return normalized.removeprefix("NEW:").strip()


def _classify_messages(
    report: _StructuredReport,
    warnings: list[str],
    raw_output: str,
) -> tuple[list[str], list[str]]:
    notices = [_format_notice(value) for value in report.notices]
    public_warnings: list[str] = []
    for value in [*warnings, *_runtime_warnings(raw_output)]:
        if "saved with the column names" in value.casefold():
            notices.append(_format_notice(value))
        else:
            public_warnings.append(value)
    return _dedupe(notices), _dedupe(public_warnings)


def _display_label(value: str) -> str:
    words = value.replace("_", " ").strip().split()
    if not words:
        return ""
    replacements = {
        "cobra": "COBRA",
        "lioness": "LIONESS",
        "mirna": "miRNA",
        "panda": "PANDA",
        "ppi": "PPI",
        "ppis": "PPIs",
        "puma": "PUMA",
        "tf": "TF",
        "tfs": "TFs",
    }
    return " ".join(
        replacements.get(word.casefold(), word.capitalize()) for word in words
    )


def _normalize_execution_text(value: str) -> str:
    """Normalize workflow names without changing paths embedded in a step."""
    prefix = value
    suffix = ""
    for separator in (" to ", " from "):
        if separator in value:
            prefix, suffix = value.split(separator, 1)
            suffix = separator + suffix
            break
    for pattern, replacement in (
        (r"\bpanda\b", "PANDA"),
        (r"\bppi\b", "PPI"),
        (r"\bppis\b", "PPIs"),
        (r"\btfs\b", "TFs"),
    ):
        prefix = re.sub(pattern, replacement, prefix, flags=re.IGNORECASE)
    return prefix + suffix


def _render_block_details(
    lines: list[str],
    block: _ReportBlock,
    *,
    heading_level: int = 3,
) -> None:
    key_value = _split_key_value(block.title)
    title = key_value[0] if key_value else block.title
    if key_value:
        block.details.insert(0, f"result: {key_value[1]}")
    heading = "#" * heading_level
    lines.extend([f"{heading} {_display_label(title)}", ""])
    for index, detail in enumerate(block.details):
        detail_key_value = _split_key_value(detail)
        if detail_key_value:
            key, value = detail_key_value
            label = _display_label(key)
            if index == 0 and key.casefold() in {"path", "file", "location"}:
                lines.append(f"- {label}: `{_user_path(value)}`")
            else:
                lines.append(f"- {label}: {_user_path(value)}")
        else:
            lines.append(f"- {_user_path(detail)}")
    if not block.details:
        lines.append("- No details reported.")
    lines.append("")


def _render_execution(lines: list[str], report: _StructuredReport) -> None:
    lines.extend(["## Execution timeline", ""])
    if not report.execution:
        lines.append("- No execution milestones were reported.")
        return

    phase_order = (
        "Prepare inputs",
        "Build networks",
        "Run PANDA",
        "Save result",
        "Execution details",
    )
    phase_by_title = {title: _ReportBlock(title) for title in phase_order}
    for block in report.execution:
        lower_title = block.title.casefold()
        if (
            lower_title.startswith("input data")
            or lower_title.startswith("loading")
            or "input" in lower_title
        ):
            phase_title = "Prepare inputs"
        elif "saving" in lower_title or "output" in lower_title:
            phase_title = "Save result"
        elif any(
            marker in lower_title
            for marker in (
                "coexpression",
                "motif network",
                "ppi network",
                "number of ppis",
                "normalizing",
            )
        ):
            phase_title = "Build networks"
        elif any(marker in lower_title for marker in ("panda", "computing")):
            phase_title = "Run PANDA"
        else:
            phase_title = "Execution details"

        phase = phase_by_title[phase_title]
        phase.details.append(block.title)
        phase.details.extend(f"  {detail}" for detail in block.details)

    phases = [phase_by_title[title] for title in phase_order]
    phases = [phase for phase in phases if phase.details]
    for index, phase in enumerate(phases, 1):
        lines.append(f"{index}. {phase.title}")
        for detail in phase.details:
            detail = detail.strip()
            if phase.title == "Run PANDA" and (
                detail.casefold().startswith("start panda run")
                or detail.casefold().startswith("running panda algorithm")
                or detail.casefold().startswith("computing panda on")
                or detail.casefold().startswith("running panda took:")
            ):
                continue
            detail_key_value = _split_key_value(detail)
            if detail_key_value:
                key, value = detail_key_value
                lines.append(
                    f"   - {_normalize_execution_text(key)}: {_user_path(value)}"
                )
            else:
                title = _normalize_execution_text(detail)
                lines.append(f"   - {_user_path(title)}")
        if phase.title == "Run PANDA":
            if report.compute_device:
                lines.append(f"   - Device: {report.compute_device}")
            if report.compute_duration_seconds is not None:
                lines.append(
                    f"   - Compute duration: "
                    f"{report.compute_duration_seconds:.2f} seconds"
                )
            lines.append("   - Result: completed")
    lines.append("")


def _artifact_report_lines(artifact: str) -> list[str]:
    display_path = _user_path(artifact)
    path = Path(display_path)
    lines = [f"- Path: `{display_path}`"]
    if path.exists():
        lines.append("  - Exists: `yes`")
        if path.is_file():
            size = path.stat().st_size
            if size >= 1_000_000:
                size_text = f"{size / 1_000_000:.2f} MB ({size:,} bytes)"
            elif size >= 1_000:
                size_text = f"{size / 1_000:.2f} KB ({size:,} bytes)"
            else:
                size_text = f"{size:,} bytes"
            lines.append(f"  - Size: `{size_text}`")
        else:
            lines.append("  - Type: `directory`")
        lines.append("  - Validation: `passed`")
    else:
        lines.append("  - Exists: `no`")
        lines.append("  - Validation: `not found`")
    return lines


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
    report = _structured_report(raw_output)
    notices, public_warnings = _classify_messages(report, warnings, raw_output)
    duration_seconds = max((finished_at - started_at).total_seconds(), 0.0)
    summary_lines = [
        f"- Workflow: `{action.removeprefix('run_').upper()}`",
        f"- Status: `{status}`",
        f"- Started (Taiwan time): {started_at.isoformat(timespec='milliseconds')}",
        f"- Finished (Taiwan time): {finished_at.isoformat(timespec='milliseconds')}",
        f"- Duration: `{duration_seconds:.2f} seconds`",
    ]
    if report.compute_duration_seconds is not None:
        summary_lines.extend(
            [
                "- PANDA compute duration: "
                f"`{report.compute_duration_seconds:.2f} seconds`",
                "- Execution overhead: "
                f"`{max(duration_seconds - report.compute_duration_seconds, 0.0):.2f} seconds`",
            ]
        )
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
    if report.input_blocks or report.validation_blocks or report.validation_lines:
        lines.extend(["", "## Inputs and validation", ""])
        for block in report.input_blocks:
            _render_block_details(lines, block)
        if report.validation_blocks:
            lines.extend(["### Compatibility checks", ""])
            for block in report.validation_blocks:
                _render_block_details(lines, block, heading_level=4)
        if report.validation_lines:
            lines.append("### Additional checks")
            lines.append("")
            lines.extend(f"- {item}" for item in report.validation_lines)
            lines.append("")
        validation_status = {
            "success": "passed",
            "dry_run": "not executed",
        }.get(status, "failed")
        lines.extend([f"- Overall validation: `{validation_status}`", ""])
    if report.execution:
        lines.extend([""])
        _render_execution(lines, report)
    lines.extend([
        "",
        "## Result",
        "",
        f"- Outcome: `{status}`",
    ])
    if report.exit_code is not None:
        lines.append(f"- Exit code: `{report.exit_code}`")
    lines.append("")
    if artifacts:
        lines.extend(["", "## Output artifacts", ""])
        for artifact in artifacts:
            lines.extend(_artifact_report_lines(artifact))
    if notices:
        lines.extend(["", "## Tool notices", "", *(f"- {item}" for item in notices)])
    if public_warnings:
        lines.extend(["", "## Warnings", "", *(f"- {item}" for item in public_warnings)])
    if errors:
        lines.extend(["", "## Errors", "", *(f"- {item}" for item in errors)])
    lines.extend(["", "## Conclusion", ""])
    if status == "success":
        lines.append("The workflow completed successfully and passed the available result checks.")
    elif status == "dry_run":
        lines.append("This was a dry run; no analysis command was executed.")
    else:
        lines.append("The workflow did not complete successfully. See the errors above for details.")
    with path.open("x", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return str(path)
