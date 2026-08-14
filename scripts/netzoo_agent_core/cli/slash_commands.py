"""CLI-owned slash commands for interactive execution authority."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .. import settings
from ..runtime import configure_runtime

__all__ = [
    "SlashCommandResult",
    "current_mode_label",
    "handle_slash_command",
    "render_mode_prompt",
]

_COMMAND_TOKEN = re.compile(r"^/[A-Za-z][A-Za-z0-9_-]*(?:\s+.*)?$")
_KNOWN_COMMANDS = frozenset({"/planning", "/execute", "/status", "/help"})


@dataclass(frozen=True, slots=True)
class SlashCommandResult:
    handled: bool
    message: str = ""


def current_mode_label() -> str:
    return "Execute" if settings.EXECUTE_TOOLS else "Planning"


def render_mode_prompt(prompt: str) -> str:
    return f"[Execute] {prompt}" if settings.EXECUTE_TOOLS else prompt


def handle_slash_command(
    user_input: str,
    *,
    allow_path_answer: bool = False,
) -> SlashCommandResult:
    stripped = user_input.strip()
    if not _COMMAND_TOKEN.fullmatch(stripped):
        return SlashCommandResult(handled=False)

    command, *arguments = stripped.split(maxsplit=1)
    normalized = command.casefold()
    if normalized not in _KNOWN_COMMANDS:
        if allow_path_answer and not arguments:
            return SlashCommandResult(handled=False)
        return SlashCommandResult(
            handled=True,
            message=(
                f"Unknown slash command: {command}. "
                "Enter /help to list available commands."
            ),
        )
    if arguments:
        return SlashCommandResult(
            handled=True,
            message=f"Slash commands do not accept arguments. Enter {normalized} by itself.",
        )
    if normalized == "/execute":
        configure_runtime(EXECUTE_TOOLS=True)
        return SlashCommandResult(
            handled=True,
            message="Execution mode enabled. Future workflow tasks will run commands.",
        )
    if normalized == "/planning":
        configure_runtime(EXECUTE_TOOLS=False)
        return SlashCommandResult(
            handled=True,
            message="Planning mode enabled. Future workflow tasks will only create previews.",
        )
    if normalized == "/status":
        return SlashCommandResult(
            handled=True,
            message=f"Current mode: {current_mode_label()}",
        )
    return SlashCommandResult(
        handled=True,
        message=(
            "Press / at an empty prompt, then Enter, to use /execute.\n"
            "Type after / to enter another slash command.\n"
            "Slash commands:\n"
            "  /planning Return future workflow tasks to preview-only Planning.\n"
            "  /execute  Run validated workflow commands for future tasks.\n"
            "  /status   Show the current execution mode.\n"
            "  /help     Show this help."
        ),
    )
