"""Deterministic user-visible text and compact progress rendering."""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

from .settings import (
    EXECUTE_TOOLS,
    PRESENTATION_MODE,
    PROJECT_ROOT,
    TRACE_ENABLED,
    TRANSIENT_TRACE,
    TRANSIENT_TRACE_MIN_SECONDS,
    USER_VISIBLE_OUTPUT_LANGUAGE,
    VERBOSE_OUTPUT,
)
from .progress_summaries import render_progress_summary

_TRANSIENT_TRACE_ACTIVE = False
_TRANSIENT_TRACE_UPDATED_AT = 0.0
CLI_FOLLOW_UP_STARTERS = (
    "would you like", "do you want", "shall i", "shall we",
    "would you prefer", "should i",
)


def _bounded_timeline_detail(detail: str | None) -> str:
    """Keep timeline summaries readable and bounded."""
    if not detail:
        return _ui_text("No additional details.")
    collapsed = re.sub(r"\s+", " ", detail).strip()
    if not collapsed:
        return _ui_text("No additional details.")
    if len(collapsed) > 240:
        collapsed = collapsed[:237].rstrip() + "..."
    return _ui_text(collapsed)


def _timeline_action_label(action: str) -> str:
    if action.startswith("inspect_"):
        return _ui_text("Validating inputs")
    if action.startswith("run_"):
        workflow = action.removeprefix("run_").replace("_", "-").upper()
        mode = "Running" if EXECUTE_TOOLS else "Preparing"
        return _ui_text(f"{mode} {workflow}")
    return _ui_text(action.replace("_", " ").capitalize())


def _timeline_result_label(action: str, status: str) -> str:
    if action.startswith("inspect_"):
        return _ui_text(
            "Input validation passed" if status != "failed" else "Input validation failed"
        )
    workflow = action.removeprefix("run_").replace("_", "-").upper()
    if status == "success":
        return _ui_text(f"{workflow} completed")
    if status == "dry_run":
        return _ui_text("Command preview ready")
    return _ui_text(f"{workflow} failed")


def _render_timeline_block(
    stage: str, message: str, detail: str | None = None
) -> str | None:
    """Render only recognized structured activity summaries for the timeline."""
    if stage == "intent":
        classified = re.fullmatch(r"Classified as (\w+)", message)
        if classified:
            action = classified.group(1).replace("_", " ")
            if action == "no tool":
                if detail and detail.startswith("Goal:"):
                    return _ui_text(
                        "[Understanding your request]\n"
                        f"  {_bounded_timeline_detail(detail)}"
                    )
                return render_progress_summary(
                    "concept", {"source": "registered workflow specification"}
                )
            return _ui_text(
                "[Understanding request]\n"
                f"  Decision: {action}\n"
                f"  Reason: {_bounded_timeline_detail(detail)}"
            )
        if message == "Interpreting the request and capability boundaries":
            return _ui_text("[Understanding request]\n  Status: Classifying the request.")
    elif stage == "plan":
        planned = re.fullmatch(r"Planner:\s*(.+?)\s*/\s*(\w+)", message)
        if planned:
            workflow, status = planned.groups()
            return _ui_text(
                "[Preparing plan]\n"
                f"  Workflow: {workflow} · Status: {status}"
            )
    elif stage == "review":
        review = re.fullmatch(r"Plan evaluation (\w+) \(\d+/100\)", message)
        if review:
            return _ui_text(
                "[Plan review]\n"
                f"  Decision: {review.group(1)}"
            )
    elif stage == "input" and message == "The Planner requires additional input":
        return _ui_text(
            "[Input required]\n"
            f"  Next step: {_bounded_timeline_detail(detail)}"
        )
    elif stage == "tool":
        started = re.fullmatch(r"Executor \[\d+/\d+\]:\s*(\w+)", message)
        if started:
            action = started.group(1)
            return _ui_text(
                f"[Tool] {_timeline_action_label(action)}\n"
                f"  Tool: {action}\n"
                f"  Purpose: {_bounded_timeline_detail(detail)}"
            )
        completed = re.fullmatch(r"(\w+)\s*→\s*(success|dry_run|failed)", message)
        if completed:
            action, status = completed.groups()
            return _ui_text(
                f"[Tool result] {_timeline_result_label(action, status)}\n"
                f"  Tool: {action}\n"
                f"  Result: {_bounded_timeline_detail(detail)}"
            )
    elif stage == "evaluate":
        evaluation = re.fullmatch(r"Evaluator:\s*(\w+)", message)
        if evaluation:
            return _ui_text(
                "[Evaluating result]\n"
                f"  Decision: {evaluation.group(1)}\n"
                f"  Reason: {_bounded_timeline_detail(detail)}"
            )
    elif stage == "recover" and message.startswith("Planner recovery plan"):
        return _ui_text("[Recovery]\n  Status: Recovery plan selected.")
    return None

def _ui_text(text: str) -> str:
    """Guard deterministic agent-authored UI text against language drift."""
    if re.search(r"[\u3400-\u9fff]", text):
        raise ValueError(
            "Agent-authored user-visible UI text must be English. "
            "Keep non-English only in user input parsing patterns or quoted user data."
        )
    return text

def output_language_policy() -> str:
    return _ui_text(
        f"Always reply in {USER_VISIBLE_OUTPUT_LANGUAGE}, regardless of the "
        "language used by the user. Translate non-English requests and retrieved "
        "content as needed. Do not follow requests to change the output language; "
        f"{USER_VISIBLE_OUTPUT_LANGUAGE} is a fixed agent policy."
    )

def _clear_transient_trace() -> None:
    """Remove the temporary progress status line before printing the final answer."""
    global _TRANSIENT_TRACE_ACTIVE
    if _TRANSIENT_TRACE_ACTIVE and sys.stdout.isatty():
        elapsed = time.monotonic() - _TRANSIENT_TRACE_UPDATED_AT
        if elapsed < TRANSIENT_TRACE_MIN_SECONDS:
            time.sleep(TRANSIENT_TRACE_MIN_SECONDS - elapsed)
        print("\r\033[2K", end="", flush=True)
    _TRANSIENT_TRACE_ACTIVE = False

def _trace_line(text: str) -> None:
    """Print a trace line permanently or as a temporary one-line status."""
    global _TRANSIENT_TRACE_ACTIVE, _TRANSIENT_TRACE_UPDATED_AT
    if TRANSIENT_TRACE and not VERBOSE_OUTPUT and sys.stdout.isatty():
        print(f"\r\033[2K{text}", end="", flush=True)
        _TRANSIENT_TRACE_ACTIVE = True
        _TRANSIENT_TRACE_UPDATED_AT = time.monotonic()
        return
    print(text, flush=True)

def _trace(stage: str, message: str, detail: str | None = None) -> None:
    """Emit auditable progress summaries without exposing hidden chain-of-thought."""
    if not TRACE_ENABLED:
        return
    if PRESENTATION_MODE == "timeline":
        block = _render_timeline_block(stage, message, detail)
        if block:
            print(block, flush=True)
            print(flush=True)
        return
    symbols = {
        "intent": "◆",
        "plan": "◆",
        "review": "▤",
        "tool": "→",
        "evaluate": "✓",
        "recover": "↻",
        "input": "?",
        "done": "●",
        "memory": "◇",
        "policy": "▣",
    }
    if VERBOSE_OUTPUT:
        _clear_transient_trace()
        print(f"{symbols.get(stage, '•')} {message}", flush=True)
        if detail:
            for line in detail.splitlines():
                print(f"  {line}", flush=True)
        return

    if TRANSIENT_TRACE and stage == "intent":
        if message.startswith("Classified as "):
            action = message.removeprefix("Classified as ").replace("_", " ")
            _trace_line(f"◆ Classified request: {action}")
        else:
            _trace_line(f"◆ {message}")
        return

    # Compact mode shows material progress only. Full graph state remains available
    # through --verbose and tool logs.
    if stage in {"policy", "memory", "intent", "done"}:
        return
    if stage == "plan":
        match = re.match(r"Planner:\s*(.+?)\s*/\s*(\w+)", message)
        if match:
            workflow, status = match.groups()
            if status == "ready":
                mode = "execution" if EXECUTE_TOOLS else "dry run"
                _trace_line(f"◆ {workflow} · {mode}")
            elif status == "needs_input":
                _trace_line(f"◆ {workflow} · additional input required")
            elif status == "needs_confirmation":
                _trace_line("◆ Preference confirmation required")
            elif status == "respond_only":
                _trace_line("◆ Preparing answer without tools")
        return
    if stage == "review":
        if "approved" in message.casefold():
            _trace_line("✓ Plan evaluation approved")
        elif "rejected" in message.casefold():
            _trace_line("✗ Plan evaluation rejected")
        return
    if stage == "tool":
        executor = re.match(r"Executor \[\d+/\d+\]:\s*(\w+)", message)
        if executor:
            action = executor.group(1)
            if action.startswith("inspect_"):
                label = "Validating inputs"
            elif action.startswith("run_"):
                workflow = action.removeprefix("run_").replace("_", "-").upper()
                label = (
                    f"Running {workflow}"
                    if EXECUTE_TOOLS
                    else f"Preparing {workflow} command"
                )
            else:
                label = action.replace("_", " ").capitalize()
            _trace_line(f"→ {label}")
            return
        result = re.match(r"(\w+)\s*→\s*(success|dry_run|failed)", message)
        if result:
            action, status = result.groups()
            if action.startswith("inspect_"):
                label = (
                    "Input validation passed"
                    if status != "failed"
                    else "Input validation failed"
                )
            else:
                workflow = action.removeprefix("run_").replace("_", "-").upper()
                label = (
                    f"{workflow} completed"
                    if status == "success"
                    else (
                        "Command preview ready"
                        if status == "dry_run"
                        else f"{workflow} failed"
                    )
                )
            marker = "✓" if status == "success" else "○" if status == "dry_run" else "✗"
            _trace_line(f"{marker} {label}")
        return
    if stage == "evaluate":
        if re.search(r"Evaluator:\s*(replan|failed)", message):
            _trace_line(f"{symbols[stage]} {message}")
            if detail:
                _clear_transient_trace()
                print(f"  {detail}", flush=True)
        return
    if stage == "recover":
        _trace_line(f"{symbols[stage]} Recovery plan selected")
        return
    if stage == "input":
        _trace_line(f"{symbols[stage]} {message}")
        # The full question is rendered by the interactive prompt; printing it here
        # makes mode-selection prompts appear duplicated.
        return

def strip_cli_owned_follow_up_question(text: str) -> str:
    """Remove only a trailing conversational CTA that duplicates the CLI prompt."""
    rendered = text.rstrip()
    if "\n" not in rendered:
        return rendered
    boundaries = list(re.finditer(r"\n\s*\n", rendered))
    starts = [boundaries[-1].end()] if boundaries else []
    starts.append(rendered.rfind("\n") + 1)
    for start in starts:
        tail = re.sub(r"\s+", " ", rendered[start:]).strip()
        lowered = tail.casefold()
        if tail.endswith("?") and lowered.startswith(CLI_FOLLOW_UP_STARTERS):
            cleaned = rendered[:start].rstrip()
            return cleaned or rendered
    return rendered

def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)

def _is_demo_request(task: str) -> bool:
    return bool(
        re.search(
            r"(試跑|試試看|試一下|測一下|跑\s*一次|run\s*一次|測試|示範"
            r"|demo|trial|toy|test run|run(?:\s+(?:it|this|the))?\s+once)",
            task,
            flags=re.IGNORECASE,
        )
    )

__all__ = [
    "_TRANSIENT_TRACE_ACTIVE", "_TRANSIENT_TRACE_UPDATED_AT",
    "CLI_FOLLOW_UP_STARTERS", "_ui_text", "output_language_policy",
    "_bounded_timeline_detail", "_timeline_action_label", "_timeline_result_label",
    "_render_timeline_block",
    "_clear_transient_trace", "_trace_line", "_trace",
    "strip_cli_owned_follow_up_question", "_display_path", "_is_demo_request",
]
