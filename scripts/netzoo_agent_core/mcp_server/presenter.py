"""A ``TurnResult`` as text a model reads.

The terminal renders the machine's state as a prompt; the window renders it as
components. This renders it as a short document for the model on the other end
of an MCP call, with two parts kept visibly apart: what NetZoo said, unchanged,
and what this server adds about which tool to call next. The second part never
states anything about the analysis itself.
"""

from __future__ import annotations

import re

from .contracts import TurnResult

__all__ = ["render_turn"]

_STATUS = {
    "waiting_for_user": "waiting for the user",
    "running": "turn still running",
    "stopped": "session ended",
    "error": "error",
}

_QUESTION_FOR_USER = (
    "This question is for the user. Show it to them and send their answer with netzoo_ask. "
    "Answer it yourself only with something the user has already said in this conversation."
)

_RULE = "-" * 40


_MODE_PREFIX = re.compile(r"^\[(?:Planning|Execute|Test)\]\s*")


def _question(text: str) -> str:
    """The terminal's prompt without its rule lines, mode prefix and input marker.

    The mode is in the result's first line already; the rule and the ``>`` are
    how a terminal frames a prompt, not part of what is asked.
    """
    kept = []
    for line in text.strip().splitlines():
        line = _MODE_PREFIX.sub("", line.rstrip())
        if line.strip() and set(line.strip()) != {"-"} and line.strip() != ">":
            kept.append(line)
    return "\n".join(kept)


def _options(result: TurnResult) -> list[str]:
    lines = []
    for index, option in enumerate(result.options, start=1):
        head = f"{index}. {option.label}"
        if option.recommended:
            head += " (recommended by NetZoo)"
        if option.description:
            head += f": {option.description}"
        if option.via == "none":
            how = f"not available{': ' + option.reason if option.reason else ''}"
        elif option.via == "netzoo_ask":
            how = f'netzoo_ask with message "{option.answer}"'
        elif option.via == "netzoo_execute":
            how = "netzoo_execute with this plan_hash, after the user agrees"
        elif option.via == "netzoo_set_mode":
            how = f'netzoo_set_mode with mode "{option.answer.lstrip("/")}"'
        else:
            how = "netzoo_preview_output for a file, netzoo_list_outputs for a folder"
            if option.paths:
                how += f": {', '.join(option.paths)}"
        lines.append(f"{head}\n   -> {how}")
    return lines


def _plan(result: TurnResult) -> list[str]:
    plan = result.plan
    lines = [f"Plan: {plan.workflow} (status: {plan.status})"]
    if plan.objective:
        lines.append(f"Objective: {plan.objective}")
    if plan.missing_inputs:
        lines.append("Missing inputs: " + ", ".join(plan.missing_inputs))
    if plan.evidence:
        lines.append("Inputs:")
        for row in plan.evidence:
            value = row.value if row.value not in (None, "") else "(none)"
            lines.append(f"  - {row.field} = {value} [{row.status}]")
    if plan.steps:
        lines.append("Steps:")
        lines.extend(f"  {index}. {step.action}: {step.purpose}" for index, step in enumerate(plan.steps, start=1))
    if result.previewed and result.plan_hash:
        # Only a previewed plan can be approved, so only then is its hash worth quoting.
        lines.append(f"plan_hash: {result.plan_hash}")
    return lines


def _next(result: TurnResult) -> list[str]:
    notes = []
    if result.status == "running":
        notes.append(
            f'The turn has not finished. Call netzoo_wait with session_id "{result.session_id}" '
            "to read the rest, or netzoo_cancel to stop it."
        )
        return notes
    if result.status == "stopped":
        notes.append("This session has ended. Call netzoo_ask without a session_id to start another.")
        return notes
    if result.status == "error":
        return notes
    if result.can_execute:
        notes.append(
            "A previewed plan is ready. Show the user the plan and the commands NetZoo listed, and "
            "call netzoo_execute with this session_id and plan_hash only after they agree to run it."
        )
    elif result.previewed:
        notes.append(
            "A previewed plan is ready, but this server was started with execution turned off. The "
            "user can set NETZOO_MCP_EXECUTE=on in the project's .env and restart the server, or "
            f'continue session "{result.session_id}" in the NetZoo desktop app and run it there.'
        )
    if result.prompt_kind and result.prompt_kind != "main":
        notes.append(_QUESTION_FOR_USER)
    elif result.options:
        notes.append(
            "The options are NetZoo's. Let the user choose; choose for them only when they have "
            "already said which they want."
        )
    return notes


def render_turn(result: TurnResult, *, path_note: str = "") -> str:
    mode = f" | {result.mode} mode" if result.mode else ""
    sections = [f"NetZoo session {result.session_id or '(none)'}{mode} | {_STATUS[result.status]}"]

    if result.errors:
        sections.append("\n".join(f"Not done ({error.error_type}): {error.message}" for error in result.errors))
    if result.reply:
        sections.append(f"NetZoo's reply (its own words, unchanged):\n{_RULE}\n{result.reply}\n{_RULE}")
    if result.notices:
        sections.append("NetZoo notices:\n" + "\n".join(f"- {notice.strip()}" for notice in result.notices))
    if result.progress and result.status == "running":
        sections.append("Progress so far:\n" + "\n".join(f"- {line}" for line in result.progress))
    if result.plan is not None:
        sections.append("\n".join(_plan(result)))
    if result.question and (question := _question(result.question)):
        sections.append(f"NetZoo is now asking:\n{question}")
    if result.options:
        sections.append("Options NetZoo offered:\n" + "\n".join(_options(result)))
    if result.outputs:
        sections.append(
            "Output files:\n" + "\n".join(f"- {ref.path} (on this computer: {ref.host_path})" for ref in result.outputs)
        )
    if result.usage and (tokens := result.usage.get("total_tokens")) is not None:
        budget = result.usage.get("budget_tokens")
        line = f"NetZoo model usage for this task: {tokens} tokens"
        if budget:
            line += f" of a {budget}-token budget"
        if result.usage.get("budget_exhausted"):
            line += " (budget exhausted)"
        sections.append(line)

    notes = []
    if result.resumed:
        notes.append(
            "This session was reopened from its saved state in a new worker. The conversation and "
            f"the plan were kept; the mode was not, and it is now {result.mode or 'Planning'} mode. If the "
            "earlier work was in test mode, tell the user and switch back with netzoo_set_mode before "
            "continuing."
        )
    notes.extend(_next(result))
    if path_note and (result.plan is not None or result.outputs):
        notes.append(path_note)
    if notes:
        sections.append("Notes from the NetZoo MCP server (not part of NetZoo's reply):\n" + "\n".join(f"- {note}" for note in notes))
    return "\n\n".join(sections)
