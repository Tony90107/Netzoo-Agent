"""Positive, current mentions used by lexical capability boundaries."""

from __future__ import annotations

import re

from ..interpretation.request_integrity import _scoped_clauses


_DECLINED_PREFIX = re.compile(
    r"\b(?:do\s+not|don't|does\s+not|doesn't|not|never|without|avoid|exclude|no)\b"
    r"|不要|不用|避免|不需要|不想",
    re.IGNORECASE,
)


def has_current_positive_mention(task: str, pattern: str | re.Pattern[str]) -> bool:
    """Ignore a historical or explicitly declined mention of a boundary term."""
    compiled = re.compile(pattern, re.IGNORECASE) if isinstance(pattern, str) else pattern
    for clause, scope in _scoped_clauses(task):
        if scope == "historical":
            continue
        for match in compiled.finditer(clause):
            if not _DECLINED_PREFIX.search(clause[max(0, match.start() - 48):match.start()]):
                return True
    return False
