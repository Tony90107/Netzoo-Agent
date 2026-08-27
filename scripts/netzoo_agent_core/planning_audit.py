"""Human-readable audit reports for planning-mode runs.

The append-only JSON trace remains the source of truth. This module renders a
separate Markdown view for planning runs so the execute log and execute
directory stay unchanged. It intentionally records context boundaries and
provenance, not raw prompts or unrestricted model state.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .settings import PLANNING_AUDIT_ROOT
from .trace_redaction import sanitize_text
from .trace_store import LocalTraceStore

__all__ = ["write_planning_audit"]


_LOG_TIMEZONE = ZoneInfo("Asia/Taipei")
_MAX_TASK_CHARS = 12_000
_MAX_DETAIL_CHARS = 600


def _safe_text(value: object, *, limit: int = _MAX_DETAIL_CHARS) -> str:
    text, _redactions = sanitize_text(str(value))
    text = text.replace("\x00", "")
    if len(text) > limit:
        return text[: limit - 20].rstrip() + " …[truncated]"
    return text


def _markdown_cell(value: object) -> str:
    return _safe_text(value, limit=240).replace("|", "\\|").replace("\n", " ")


def _load_events(trace_store: LocalTraceStore, run_id: str) -> list[dict[str, Any]]:
    events_path = trace_store.run_path(run_id) / "events.jsonl"
    events: list[dict[str, Any]] = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if isinstance(value, dict):
                events.append(value)
    return events


def _event_payload(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload")
    return payload if isinstance(payload, dict) else {}


def _event_label(event: dict[str, Any]) -> str:
    event_type = str(event.get("event_type") or "event")
    node = str(event.get("node") or "unknown")
    payload = _event_payload(event)
    if event_type == "llm.completed":
        role = payload.get("role", node)
        status = payload.get("status", "unknown")
        return f"LLM `{role}` → {status}"
    if event_type == "decision.recorded":
        return f"Decision: {payload.get('action', 'unknown')}"
    if event_type == "plan.created":
        return f"Plan: {payload.get('workflow', 'unknown')} / {payload.get('status', 'unknown')}"
    if event_type == "memory.retrieved":
        return f"Memory retrieved ({payload.get('episode_count', 0)} episodes)"
    if event_type == "policy.loaded":
        return f"Policy loaded (v{payload.get('policy_version', '?')})"
    if event_type == "node.finished":
        duration = payload.get("duration_ms")
        return f"`{node}` finished" + (f" ({duration} ms)" if duration is not None else "")
    if event_type == "node.started":
        return f"`{node}` started"
    return f"{event_type} ({node})"


def _phase_order(events: list[dict[str, Any]]) -> list[str]:
    phases: list[str] = []
    for event in events:
        node = str(event.get("node") or "").strip()
        if node and node not in phases:
            phases.append(node)
    return phases


def _llm_calls(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        _event_payload(event)
        for event in events
        if event.get("event_type") == "llm.completed"
    ]


def _executor_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        event
        for event in events
        if str(event.get("event_type", "")).startswith("tool.")
        or str(event.get("node", "")) in {"executor", "execute_tool"}
    ]


def _result_value(result: dict[str, Any] | None, *keys: str) -> Any:
    value: Any = result
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _context_boundary_lines(
    events: list[dict[str, Any]],
    result: dict[str, Any] | None,
) -> list[str]:
    observed_roles = [str(call.get("role")) for call in _llm_calls(events)]
    role_set = set(observed_roles)
    lines = [
        "- This is an envelope-level audit. The provider does not expose which "
        "individual tokens the model used internally.",
        "- Raw prompts, hidden reasoning, and unrestricted model state are not "
        "duplicated in this Markdown report.",
    ]
    envelopes = {
        "semantic_interpreter": "latest user turn + ontology/policy prompt; no tool execution authority",
        "semantic_reviewer": "latest user turn + prior semantic proposal + validation issues",
        "intent_router": "latest user turn + validated semantic/capability facts; no workflow-selection authority",
        "response": "latest user turn + validated plan/workflow context + typed tool-result metadata",
    }
    for role, envelope in envelopes.items():
        if role in role_set:
            lines.append(f"- `{role}` context envelope: {envelope}.")
        else:
            lines.append(f"- `{role}` was not called in this run.")

    memory_events = [event for event in events if event.get("event_type") == "memory.retrieved"]
    if memory_events:
        count = _event_payload(memory_events[-1]).get("episode_count", 0)
        lines.append(
            f"- Memory retrieval occurred ({count} episode record(s)); raw memory payloads "
            "are not treated as response or executor authority."
        )
    else:
        lines.append("- No memory retrieval event was observed.")

    plan = _result_value(result, "plan") or {}
    missing = plan.get("missing_inputs", []) if isinstance(plan, dict) else []
    if missing:
        lines.append(
            "- Inputs still missing at planning time: "
            + ", ".join(f"`{_markdown_cell(item)}`" for item in missing)
            + "."
        )
    else:
        lines.append("- No missing input fields were reported by the planner.")

    executor_events = _executor_events(events)
    if executor_events:
        lines.append(
            "- Executor/tool activity was observed; inspect the sequence table before "
            "treating this as a planning-only run."
        )
    else:
        lines.append("- No executor/tool event was observed; no command or file input was sent to an executor.")

    lines.extend(
        [
            "- Do not pass API keys, credentials, raw external instructions, unvalidated "
            "workflow arguments, or router rationale as executor authority.",
            "- Router interpretation is advisory; validated workflow specifications and "
            "typed input roles are the authority boundary.",
            "- Raw tool output is excluded from the trusted response metadata path when "
            "the response node builds its context.",
        ]
    )
    return lines


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def write_planning_audit(
    run_id: str,
    trace_store: LocalTraceStore,
    *,
    task: str,
    result: dict[str, Any] | None = None,
    root: Path = PLANNING_AUDIT_ROOT,
) -> str | None:
    """Render one planning run from the safe append-only trace and final state."""
    try:
        manifest = trace_store.load_manifest(run_id)
        events = _load_events(trace_store, run_id)
    except (OSError, TypeError, ValueError):
        return None

    started_at = manifest.created_at.astimezone(_LOG_TIMEZONE)
    finished_at = (
        manifest.finished_at.astimezone(_LOG_TIMEZONE)
        if manifest.finished_at is not None
        else datetime.now(timezone.utc).astimezone(_LOG_TIMEZONE)
    )
    calls = _llm_calls(events)
    executor_events = _executor_events(events)
    phases = _phase_order(events)
    decision = _result_value(result, "decision") or {}
    plan = _result_value(result, "plan") or {}
    task_text = _safe_text(task, limit=_MAX_TASK_CHARS)
    total_input = sum(int(call.get("input_tokens", 0) or 0) for call in calls)
    total_output = sum(int(call.get("output_tokens", 0) or 0) for call in calls)
    total_tokens = sum(int(call.get("total_tokens", 0) or 0) for call in calls)
    total_cache_read = sum(int(call.get("cache_read_tokens", 0) or 0) for call in calls)

    lines = [
        "# NetZoo planning audit",
        "",
        "> This report is generated for planning mode. It summarizes safe trace metadata; it is not a dump of prompts, hidden reasoning, or provider internals.",
        "",
        "## Run summary",
        "",
        f"- Run ID: `{manifest.run_id}`",
        f"- Session ID: `{_markdown_cell(manifest.session_id)}`",
        "- Mode: `planning`",
        f"- Trace status: `{_markdown_cell(manifest.status)}`",
        f"- Started (Taiwan time): `{started_at.isoformat(timespec='seconds')}`",
        f"- Last observed (Taiwan time): `{finished_at.isoformat(timespec='seconds')}`",
        f"- Workflow: `{_markdown_cell(plan.get('workflow', 'unknown'))}`",
        f"- Plan status: `{_markdown_cell(plan.get('status', 'unknown'))}`",
        f"- Decision: `{_markdown_cell(decision.get('action', 'unknown'))}`",
        f"- Executor/tool events observed: `{len(executor_events)}`",
        "",
        "## User task (secrets redacted)",
        "",
        task_text or "_(empty)_",
        "",
        "## Execution order",
        "",
        "`"
        + " → ".join(_markdown_cell(phase) for phase in phases)
        + "`",
        "",
        "| Seq | Time (TW) | Event | Node | Detail |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for event in events:
        occurred_at = str(event.get("occurred_at", ""))
        try:
            event_time = datetime.fromisoformat(occurred_at.replace("Z", "+00:00")).astimezone(_LOG_TIMEZONE)
            time_text = event_time.strftime("%H:%M:%S")
        except ValueError:
            time_text = "?"
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_cell(event.get("sequence", "?")),
                    time_text,
                    _markdown_cell(event.get("event_type", "event")),
                    _markdown_cell(event.get("node", "unknown")),
                    _markdown_cell(_event_label(event)),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## LLM and token usage",
            "",
            "| Step | Role | Model | Status | Input | Output | Total | Cache read | Duration | Cost (USD) |",
            "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for index, call in enumerate(calls, start=1):
        cost = call.get("cost_micro_usd")
        cost_text = "—" if cost is None else f"${int(cost) / 1_000_000:.6f}"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    _markdown_cell(call.get("role", "unknown")),
                    _markdown_cell(call.get("model", "unknown")),
                    _markdown_cell(call.get("status", "unknown")),
                    _markdown_cell(call.get("input_tokens", 0)),
                    _markdown_cell(call.get("output_tokens", 0)),
                    _markdown_cell(call.get("total_tokens", 0)),
                    _markdown_cell(call.get("cache_read_tokens", 0)),
                    _markdown_cell(f"{call.get('duration_ms', 0)} ms"),
                    cost_text,
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            f"- Total observed tokens: `{total_tokens}` (`{total_input}` input + `{total_output}` output).",
            f"- Total cache-read tokens: `{total_cache_read}`.",
            "- Token provenance is taken from provider usage when available; estimated calls remain marked in the source trace.",
            "",
            "## Context usage and boundaries",
            "",
            *_context_boundary_lines(events, result),
            "",
            "## What this audit cannot prove",
            "",
            "- It cannot prove which individual prompt tokens affected a model decision; that information is not exposed by the LLM API.",
            "- A context envelope being sent does not mean every field was semantically used.",
            "- Absence of a tool event means no tool activity was observed in this run, not that a future `/execute` run will use the same inputs.",
            "",
            "## Source of truth",
            "",
            f"- Structured event trace: `.netzoo/traces/{manifest.run_id}/events.jsonl`",
            "- This Markdown is a derived, redacted view and can be regenerated from the trace.",
            "",
        ]
    )

    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(root, 0o700)
    path = root / f"planning-{started_at.strftime('%Y-%m-%d_%H-%M-%S')}_TW-{manifest.run_id}.md"
    _write_atomic(path, "\n".join(lines))
    return str(path)
