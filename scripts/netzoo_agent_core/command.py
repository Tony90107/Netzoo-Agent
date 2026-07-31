"""Bounded local process execution and dry-run command rendering."""

from __future__ import annotations

import shlex
import subprocess
import tempfile
from pathlib import Path


from .contracts import (
    EXECUTE_TOOLS,
    TOOL_RAW_MAX_CHARS,
    TOOL_TIMEOUT_SECONDS,
)

__all__ = [
    "_quote_command",
    "_read_bounded_process_output",
    "_run_command",
]


def _quote_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def _read_bounded_process_output(handle, label: str) -> str:
    """Read bounded UTF-8 process output from a disk-backed temporary stream."""
    handle.flush()
    handle.seek(0, 2)
    size = handle.tell()
    handle.seek(0)
    if size <= TOOL_RAW_MAX_CHARS:
        return handle.read().decode("utf-8", errors="replace").strip()

    head_size = TOOL_RAW_MAX_CHARS * 2 // 3
    tail_size = TOOL_RAW_MAX_CHARS - head_size
    head = handle.read(head_size)
    handle.seek(-tail_size, 2)
    tail = handle.read(tail_size)
    return (
        head.decode("utf-8", errors="replace").strip()
        + f"\n[{label} truncated; {size} bytes total]\n"
        + tail.decode("utf-8", errors="replace").strip()
    )


def _run_command(
    command: list[str],
    output_file: str | None = None,
    additional_output_files: list[str] | None = None,
) -> str:
    if not command:
        return "- error: local command is empty."
    rendered = _quote_command(command)
    if not EXECUTE_TOOLS:
        return (
            "Dry run only. The agent selected this command but did not execute it.\n\n"
            f"```bash\n{rendered}\n```\n\n"
            "Add `--execute` if you want the script to actually run the tool."
        )

    expected_outputs = [
        path for path in [output_file, *(additional_output_files or [])] if path
    ]
    output_state_before: dict[str, tuple[int, int] | None] = {}
    for expected_output in expected_outputs:
        expected_path = Path(expected_output)
        expected_path.parent.mkdir(parents=True, exist_ok=True)
        if expected_path.exists():
            stat = expected_path.stat()
            output_state_before[expected_output] = (stat.st_mtime_ns, stat.st_size)
        else:
            output_state_before[expected_output] = None

    timeout = TOOL_TIMEOUT_SECONDS if TOOL_TIMEOUT_SECONDS > 0 else None
    with (
        tempfile.TemporaryFile() as stdout_handle,
        tempfile.TemporaryFile() as stderr_handle,
    ):
        try:
            completed = subprocess.run(
                command,
                check=False,
                stdout=stdout_handle,
                stderr=stderr_handle,
                timeout=timeout,
            )
        except FileNotFoundError:
            return (
                f"Command: `{rendered}`\n"
                f"- error: local executable was not found: {command[0]}"
            )
        except PermissionError:
            return (
                f"Command: `{rendered}`\n"
                f"- error: local executable is not permitted: {command[0]}"
            )
        except subprocess.TimeoutExpired:
            rendered_timeout = f"{timeout:g}" if timeout is not None else "unknown"
            result = [
                f"Command: `{rendered}`",
                f"- error: local command timed out after {rendered_timeout} seconds.",
            ]
            stdout = _read_bounded_process_output(stdout_handle, "STDOUT")
            stderr = _read_bounded_process_output(stderr_handle, "STDERR")
            if stdout:
                result.append("\nSTDOUT before timeout:\n" + stdout)
            if stderr:
                result.append("\nSTDERR before timeout:\n" + stderr)
            return "\n".join(result)
        except OSError as error:
            return (
                f"Command: `{rendered}`\n"
                "- error: local command could not be started: "
                f"{type(error).__name__}: {error}"
            )
        stdout = _read_bounded_process_output(stdout_handle, "STDOUT")
        stderr = _read_bounded_process_output(stderr_handle, "STDERR")

    result = [
        f"Command: `{rendered}`",
        f"Exit code: {completed.returncode}",
    ]
    if stdout:
        result.append("\nSTDOUT:\n" + stdout)
    if stderr:
        result.append("\nSTDERR:\n" + stderr)
    if completed.returncode == 0:
        missing_or_stale_outputs = []
        for path in expected_outputs:
            current_path = Path(path)
            if not current_path.exists():
                missing_or_stale_outputs.append(path)
                continue
            stat = current_path.stat()
            current_state = (stat.st_mtime_ns, stat.st_size)
            if output_state_before[path] == current_state:
                missing_or_stale_outputs.append(path)
        if missing_or_stale_outputs:
            result.append(
                "\nERROR: command exited successfully but did not create or update "
                "expected output(s): "
                + ", ".join(f"`{path}`" for path in missing_or_stale_outputs)
            )
        for expected_output in expected_outputs:
            if Path(expected_output).exists():
                result.append(f"\nOutput file: `{expected_output}`")
    return "\n".join(result)
