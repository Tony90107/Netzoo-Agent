"""Reply cards and Markdown for an interactive terminal.

Only an interactive terminal gets these: a pipe, a test recorder and a
redirected log keep the plain full text they always had. Colour follows the
`NO_COLOR` convention. Nothing here changes what the agent said -- the full
reply is one `/details` away -- it changes how much of it is shown first.
"""

from __future__ import annotations

import os
import re
import shutil
import textwrap

__all__ = ["DETAILS_COMMAND", "color_enabled", "option_prompt", "render_card", "render_markdown", "render_options"]

DETAILS_COMMAND = "/details"

_BOLD, _DIM, _ACCENT, _CYAN, _YELLOW, _RESET = "\x1b[1m", "\x1b[2m", "\x1b[38;5;173m", "\x1b[36m", "\x1b[33m", "\x1b[0m"


def color_enabled() -> bool:
    return not os.environ.get("NO_COLOR") and os.environ.get("TERM", "") != "dumb"


def _style(text: str, code: str, color: bool) -> str:
    return f"{code}{text}{_RESET}" if color and text else text


def _width() -> int:
    return max(40, min(shutil.get_terminal_size((100, 24)).columns, 110))


def _inline(text: str, color: bool) -> str:
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r"\1 (\2)", text)
    text = re.sub(r"\*\*(.+?)\*\*", lambda m: _style(m.group(1), _BOLD, color), text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\1", text)
    return re.sub(r"`([^`]+)`", lambda m: _style(m.group(1), _CYAN, color), text)


def render_markdown(text: str, *, color: bool | None = None) -> str:
    """A light Markdown pass: headings, emphasis, code, bullets and rules.

    Tables and code blocks are left as written: their layout is already the
    terminal's, and re-wrapping them would only break it.
    """
    color = color_enabled() if color is None else color
    lines, fenced = [], False
    for line in text.split("\n"):
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if fenced or line.lstrip().startswith("|"):
            lines.append(_style(line, _DIM, color) if fenced else line)
            continue
        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            lines.append(_style(_inline(heading.group(2), False), _BOLD, color))
            continue
        if re.fullmatch(r"\s*(-{3,}|\*{3,}|_{3,})\s*", line):
            lines.append(_style("─" * min(_width(), 60), _DIM, color))
            continue
        bullet = re.match(r"^(\s*)[-*+]\s+(.*)$", line)
        if bullet:
            depth = len(bullet.group(1)) // 2
            marker = "•" if depth == 0 else "◦"
            lines.append("  " * depth + f"{marker} " + _inline(bullet.group(2), color))
            continue
        lines.append(_inline(line, color))
    return "\n".join(lines)


def _wrap(text: str, indent: str) -> list[str]:
    return textwrap.wrap(text, width=_width() - len(indent), initial_indent=indent,
                         subsequent_indent=indent) or [indent]


def render_card(card: dict, *, color: bool | None = None) -> str:
    """The brief reply: headline, key points, and what cannot run here."""
    color = color_enabled() if color is None else color
    lines = [_style(line, _BOLD, color) for line in _wrap(card.get("headline", ""), "")]
    for point in card.get("points") or []:
        lines.extend(_wrap(point, "  • "))
    unavailable = card.get("unavailable") or []
    if unavailable:
        lines.append(_style("  Related, but not available in this agent:", _YELLOW, color))
        for item in unavailable:
            text = item["label"] + (f" — {item['reason']}" if item.get("reason") else "")
            lines.extend(_wrap(text, "    ✕ "))
    lines.append(_style(f"  Full explanation: {DETAILS_COMMAND}", _DIM, color))
    return "\n".join(lines)


def render_options(card: dict, *, active: int | None = None, color: bool | None = None) -> list[str]:
    """The question and every selectable option, numbered as the machine numbers them."""
    color = color_enabled() if color is None else color
    lines: list[str] = []
    number = 0
    choices = card.get("choices") or {}
    options = [o for o in choices.get("options") or [] if o.get("available", True) and o.get("resolution") != "none"]
    if options:
        header = _style(f"[{choices.get('header', 'Choice')}]", _ACCENT, color)
        lines.append(f"{header} {_style(choices.get('question', ''), _BOLD, color)}")
        if choices.get("ordering"):
            lines.append(_style("  " + choices["ordering"], _DIM, color))
        for option in options:
            number += 1
            pointer = "›" if active == number - 1 else " "
            badge = f"  ({option['badge']})" if option.get("badge") else ""
            label = f"{pointer} {number}) {option['label']}{badge}"
            lines.append(_style(label, _ACCENT if active == number - 1 else _BOLD, color))
            if option.get("description"):
                lines.extend(_style(line, _DIM, color) for line in _wrap(option["description"], "      "))
        for item in card.get("unavailable") or []:
            lines.append(_style(f"  ✕  {item['label']} — not available here", _DIM, color))
    steps = [s for s in card.get("next_steps") or [] if s.get("available", True) and s.get("resolution") != "none"]
    if steps:
        entries = []
        for step in steps:
            number += 1
            entries.append(f"{number}) {step['label']}")
        pointer = "›" if active is not None and active >= len(options) else " "
        lines.append(_style(f"{pointer} Next: " + "   ".join(entries), _DIM if active is None or active < len(options) else _ACCENT, color))
    return lines


def option_prompt(prompt: str) -> str:
    """The prompt text to show beside an option menu: the question is the menu's.

    The machine's own "Next step" block restates the question the menu already
    asks; only its navigation hint and any mode label are kept.
    """
    question, _, prefix = prompt.rpartition("\n")
    kept = [line for line in question.split("\n")
            if line.startswith(("Enter/back", "[Execute]", "[Test]", "[Planning]"))]
    return ("\n".join(kept) + "\n" if kept else "") + prefix
