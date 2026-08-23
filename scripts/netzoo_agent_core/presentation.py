"""Deterministic user-visible text and compact progress rendering."""

from __future__ import annotations

from dataclasses import dataclass
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Literal

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
_PROGRESS_STATE: "ProgressState | None" = None
_PROGRESS_RENDERED_LINES = 0
_PROGRESS_LAST_TEXT: str | None = None
_COMMITTED_ACTIVITY_KEYS: set[str] = set()

_PROGRESS_STAGE_ORDER = ("understand", "match", "next_step")
_PROGRESS_STAGE_LABELS = {
    "understand": "Understand request",
    "match": "Match workflow capabilities",
    "next_step": "Choose next step",
}


@dataclass(slots=True)
class ProgressStage:
    """One code-owned, user-visible stage in the normal CLI progress view."""

    label: str
    status: Literal["pending", "active", "complete", "attention", "failed"]
    detail: str | None = None


@dataclass(slots=True)
class ProgressState:
    """Small task-level state machine for public CLI progress."""

    stages: dict[str, ProgressStage]
    activity: str | None = None

    @classmethod
    def initial(cls) -> "ProgressState":
        return cls(
            stages={
                name: ProgressStage(label=label, status="pending")
                for name, label in _PROGRESS_STAGE_LABELS.items()
            }
        )

    def activate(self, name: str, detail: str | None = None) -> None:
        index = _PROGRESS_STAGE_ORDER.index(name)
        for earlier in _PROGRESS_STAGE_ORDER[:index]:
            self.complete(earlier)
        for stage_name, stage in self.stages.items():
            if stage_name != name and stage.status == "active":
                stage.status = "pending"
                stage.detail = None
        stage = self.stages[name]
        stage.status = "active"
        stage.detail = detail

    def complete(self, name: str, detail: str | None = None) -> None:
        stage = self.stages[name]
        stage.status = "complete"
        if detail is not None:
            stage.detail = detail

    def attention(self, name: str, detail: str | None = None) -> None:
        index = _PROGRESS_STAGE_ORDER.index(name)
        for earlier in _PROGRESS_STAGE_ORDER[:index]:
            self.complete(earlier)
        self.stages[name].status = "attention"
        self.stages[name].detail = detail

    def fail(self, name: str, detail: str) -> None:
        index = _PROGRESS_STAGE_ORDER.index(name)
        for earlier in _PROGRESS_STAGE_ORDER[:index]:
            self.complete(earlier)
        self.stages[name].status = "failed"
        self.stages[name].detail = detail


def _render_progress_state(state: ProgressState) -> str:
    """Render only the one public activity currently in progress."""
    for name in _PROGRESS_STAGE_ORDER:
        stage = state.stages[name]
        if stage.status == "active":
            if name == "understand":
                text = "Refining outcome classification…" if "Refining" in (stage.detail or "") else "Classifying requested outcome…"
            elif name == "match":
                text = "Matching registered workflows…"
            else:
                text = "Preparing next step…"
            return _ui_text(_truncate_terminal_line(f"● {text}"))
        if stage.status == "attention":
            text = "? Clarification needed"
            if stage.detail:
                text += "\n  " + stage.detail
            return _ui_text(text)
        if stage.status == "failed":
            return _ui_text(_truncate_terminal_line(f"✗ {stage.detail or 'Operation failed'}"))
    return ""


def _terminal_columns() -> int:
    """Return a conservative terminal width for a one-row live status line."""
    return max(20, shutil.get_terminal_size(fallback=(100, 24)).columns)


def _truncate_terminal_line(text: str) -> str:
    """Prevent live status lines from wrapping and breaking ANSI redraw offsets."""
    columns = _terminal_columns()
    if len(text) <= columns:
        return text
    return text[: max(1, columns - 3)].rstrip() + "..."


def _commit_public_activity(key: str, text: str) -> None:
    """Keep one verified public activity visible above the live status block."""
    if key in _COMMITTED_ACTIVITY_KEYS:
        return
    _commit_live_progress_block()
    print(_truncate_terminal_line(_ui_text(text)), flush=True)
    _COMMITTED_ACTIVITY_KEYS.add(key)


def _activity_duration(detail: dict) -> str:
    duration_ms = detail.get("duration_ms")
    if not isinstance(duration_ms, int):
        return ""
    return f" ({duration_ms / 1000:.2f}s)"


def _apply_public_progress_event(
    state: ProgressState,
    stage: str,
    message: str,
    detail: str | dict | None = None,
) -> bool:
    """Apply only recognized public graph events to the normal progress view."""
    if isinstance(detail, dict) and detail.get("kind") == "router_activity":
        operation = str(detail.get("operation") or "router")
        if detail.get("status") == "started":
            activity = (
                "Refining outcome classification"
                if operation == "router_repair"
                else "Calling Router to classify the requested outcome"
            )
            state.activate("understand", activity)
            return True
        if detail.get("status") == "completed":
            label = (
                "✓ Refined outcome classification"
                if operation == "router_repair"
                else "✓ Called Router — classified requested outcome"
            )
            _commit_public_activity(
                f"router:{operation}:completed:{detail.get('call_id', operation)}",
                label + _activity_duration(detail),
            )
            state.activate("understand", "Router response received")
            return True
        if detail.get("status") == "failed":
            error_type = str(detail.get("error_type") or "RouterError")
            _commit_public_activity(
                f"router:{operation}:failed:{detail.get('call_id', operation)}",
                f"✗ Router classification failed — {error_type}",
            )
            state.fail("understand", "Router call failed")
            return True
    if isinstance(detail, dict) and detail.get("kind") == "registry_activity":
        if detail.get("status") == "started":
            state.complete("understand", "Router response received")
            state.activate("match", "Comparing against registered workflows")
            return True
    event_names = {
        ("intent", "Interpreting the request and capability boundaries"): "understand",
        ("reasoning", "Checking registered workflow capabilities"): "match",
        ("reasoning", "Choosing the next safe step"): "next_step",
    }
    if (
        stage == "intent"
        and message.startswith("Classified as ")
        and isinstance(detail, dict)
        and detail.get("kind") == "classification"
    ):
        outcome = str(detail.get("outcome") or "Requested outcome classified")
        workflows = [str(item) for item in detail.get("workflows", [])]
        state.complete("understand", outcome)
        if workflows:
            state.complete("match", ", ".join(workflows))
            _commit_public_activity(
                f"workflow-match:{','.join(workflows)}",
                f"✓ Matched workflows — {', '.join(workflows)}",
            )
        return True
    state_name = event_names.get((stage, message))
    if stage == "input" and message == "The Planner requires additional input":
        state.attention("next_step", "Input required")
        return True
    if state_name is None:
        return False
    if isinstance(detail, dict) and detail.get("kind") == "next_step":
        question = str(detail.get("question") or "")
        tool_status = str(detail.get("tool_status") or "")
        if question:
            state.attention(state_name)
        else:
            state.activate(state_name)
        state.activity = tool_status or None
        return True
    rendered_detail = _bounded_timeline_detail(detail) if detail else None
    if state_name == "next_step" and rendered_detail and "clarification" in (
        rendered_detail.casefold()
    ):
        state.attention(state_name, rendered_detail)
        return True
    state.activate(state_name, rendered_detail)
    return True


def _render_or_update_progress_state(state: ProgressState) -> None:
    """Draw the current state block in place on TTYs and safely on streams."""
    global _PROGRESS_LAST_TEXT, _PROGRESS_RENDERED_LINES
    rendered = _render_progress_state(state)
    if rendered == _PROGRESS_LAST_TEXT:
        return
    if not rendered:
        if _PROGRESS_RENDERED_LINES and sys.stdout.isatty():
            print(f"\033[{_PROGRESS_RENDERED_LINES}A", end="", flush=True)
            for _ in range(_PROGRESS_RENDERED_LINES):
                print("\r\033[2K", flush=True)
            print(f"\033[{_PROGRESS_RENDERED_LINES}A", end="", flush=True)
        _PROGRESS_RENDERED_LINES = 0
        _PROGRESS_LAST_TEXT = rendered
        return
    if not sys.stdout.isatty():
        print(rendered, flush=True)
        _PROGRESS_LAST_TEXT = rendered
        return
    if _PROGRESS_RENDERED_LINES:
        print(f"\033[{_PROGRESS_RENDERED_LINES}A", end="", flush=True)
        for _ in range(_PROGRESS_RENDERED_LINES):
            print("\r\033[2K", flush=True)
        print(f"\033[{_PROGRESS_RENDERED_LINES}A", end="", flush=True)
    print(rendered, flush=True)
    _PROGRESS_RENDERED_LINES = rendered.count("\n") + 1
    _PROGRESS_LAST_TEXT = rendered


def _finalize_progress_state() -> None:
    """Keep the final state visible while releasing its live redraw position."""
    global _PROGRESS_LAST_TEXT, _PROGRESS_RENDERED_LINES, _PROGRESS_STATE
    _PROGRESS_RENDERED_LINES = 0
    _PROGRESS_LAST_TEXT = None
    _PROGRESS_STATE = None
    _COMMITTED_ACTIVITY_KEYS.clear()


def _commit_live_progress_block() -> None:
    """Turn the live state block into terminal history before a tool record."""
    global _PROGRESS_RENDERED_LINES
    if not (_PROGRESS_LAST_TEXT and sys.stdout.isatty() and _PROGRESS_RENDERED_LINES):
        return
    print(f"\033[{_PROGRESS_RENDERED_LINES}A", end="", flush=True)
    for _ in range(_PROGRESS_RENDERED_LINES):
        print("\r\033[2K", flush=True)
    print(f"\033[{_PROGRESS_RENDERED_LINES}A", end="", flush=True)
    print(_PROGRESS_LAST_TEXT, flush=True)
    _PROGRESS_RENDERED_LINES = 0


CLI_FOLLOW_UP_STARTERS = (
    "would you like", "do you want", "shall i", "shall we",
    "would you prefer", "should i",
)


def _bounded_timeline_detail(detail: str | dict | None) -> str:
    """Keep timeline summaries readable and bounded."""
    if not detail:
        return _ui_text("No additional details.")
    text = detail.get("text", "") if isinstance(detail, dict) else detail
    collapsed = re.sub(r"\s+", " ", text).strip()
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


def _state_machine_tool_label(action: str) -> str:
    """Return the code-owned task label for one verified tool action."""
    if action.startswith("run_"):
        workflow = action.removeprefix("run_").replace("_", "-").upper()
        return _ui_text(f"Run {workflow}")
    return _timeline_action_label(action)


def _render_tool_activity(
    action: str,
    status: str | None,
    detail: str | dict | None,
) -> str:
    """Render a permanent record from an already-emitted tool event only."""
    purpose = (
        _bounded_timeline_detail(detail.get("purpose"))
        if isinstance(detail, dict) and detail.get("kind") == "tool_activity"
        else _bounded_timeline_detail(detail)
    )
    label = _state_machine_tool_label(action)
    if status is None:
        lines = [
            f"● {label}",
            f"  Tool: {action}",
            f"  Purpose: {purpose}",
        ]
        if isinstance(detail, dict) and detail.get("kind") == "tool_activity":
            inputs = [str(item) for item in detail.get("inputs", [])]
            if inputs:
                lines.append(f"  Inputs: {', '.join(inputs)}")
        return _ui_text("\n".join(lines))
    marker = "✓" if status in {"success", "dry_run"} else "✗"
    result_label = label if action.startswith("run_") else _timeline_result_label(action, status)
    return _ui_text(
        f"{marker} {result_label}\n"
        f"  Tool: {action}\n"
        f"  Result: {purpose}"
    )


def _render_timeline_block(
    stage: str, message: str, detail: str | dict | None = None
) -> str | None:
    """Render only recognized structured activity summaries for the timeline."""
    if stage == "intent":
        classified = re.fullmatch(r"Classified as (\w+)", message)
        if classified:
            action = classified.group(1).replace("_", " ")
            if action == "no tool":
                if isinstance(detail, dict) and detail.get("kind") == "semantic_goal":
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
    elif stage == "reasoning":
        titles = {
            "Checking registered workflow capabilities": "[Checking available workflows]",
            "Choosing the next safe step": "[Choosing next step]",
        }
        if message in titles:
            return _ui_text(f"{titles[message]}\n  {_bounded_timeline_detail(detail)}")
    elif stage == "plan":
        planned = re.fullmatch(r"Planner:\s*(.+?)\s*/\s*(\w+)", message)
        if planned:
            workflow, status = planned.groups()
            if workflow == "NO-TOOL" and status == "respond_only":
                return None
            return _ui_text(
                "[Preparing plan]\n"
                f"  Workflow: {workflow} · Status: {status}"
            )
    elif stage == "review":
        review = re.fullmatch(r"Plan evaluation (\w+) \(\d+/100\)", message)
        if review:
            if review.group(1) == "deferred":
                return None
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
    if PRESENTATION_MODE == "state_machine":
        _finalize_progress_state()
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

def _trace(stage: str, message: str, detail: str | dict | None = None) -> None:
    """Emit auditable progress summaries without exposing hidden chain-of-thought."""
    if not TRACE_ENABLED:
        return
    if PRESENTATION_MODE == "state_machine" and not TRANSIENT_TRACE:
        global _PROGRESS_STATE
        if _PROGRESS_STATE is None:
            _PROGRESS_STATE = ProgressState.initial()
        if _apply_public_progress_event(_PROGRESS_STATE, stage, message, detail):
            _render_or_update_progress_state(_PROGRESS_STATE)
            return
        started = re.fullmatch(r"Executor \[\d+/\d+\]:\s*(\w+)", message)
        completed = re.fullmatch(r"(\w+)\s*→\s*(success|dry_run|failed)", message)
        if stage == "tool" and (started or completed):
            action = started.group(1) if started else completed.group(1)
            status = None if started else completed.group(2)
            if status == "failed":
                _PROGRESS_STATE.fail("next_step", "Tool failed")
            elif status is None:
                _PROGRESS_STATE.activate("next_step", _state_machine_tool_label(action))
            else:
                _PROGRESS_STATE.complete("next_step")
            _commit_live_progress_block()
            print(_render_tool_activity(action, status, detail), flush=True)
            _render_or_update_progress_state(_PROGRESS_STATE)
            return
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
            rendered_detail = detail.get("text", "") if isinstance(detail, dict) else detail
            for line in rendered_detail.splitlines():
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

def _is_cli_owned_guidance_paragraph(paragraph: str) -> bool:
    collapsed = re.sub(r"\s+", " ", paragraph).strip()
    lowered = collapsed.casefold()
    operational_status = bool(
        re.search(
            r"\bno (?:tools?|commands?) (?:were )?(?:executed|run)\b"
            r"|\bno files? (?:were )?(?:inspected|read)\b"
            r"|\bno analysis (?:was )?(?:run|performed)\b",
            lowered,
        )
    )
    conversational_cta = (
        collapsed.endswith("?") and lowered.startswith(CLI_FOLLOW_UP_STARTERS)
    ) or lowered.startswith(
        (
            "if you need to start",
            "if you want to start",
            "to start the workflow",
        )
    )
    return operational_status or conversational_cta


def strip_cli_owned_guidance_tail(text: str) -> str:
    """Remove trailing operational status or navigation owned by the CLI."""
    paragraphs = re.split(r"\n\s*\n", text.rstrip())
    while paragraphs and _is_cli_owned_guidance_paragraph(paragraphs[-1]):
        paragraphs.pop()
    return "\n\n".join(paragraph.rstrip() for paragraph in paragraphs).rstrip()


def strip_cli_owned_follow_up_question(text: str) -> str:
    """Compatibility alias for the broader CLI-owned tail normalizer."""
    return strip_cli_owned_guidance_tail(text)

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
    "strip_cli_owned_follow_up_question", "strip_cli_owned_guidance_tail",
    "_display_path", "_is_demo_request",
]
