"""Bounded paths attached to explicit input-role descriptions."""

import re


def _alias_pattern(aliases: tuple[str, ...]) -> str:
    return "|".join(re.escape(alias) for alias in sorted(aliases, key=len, reverse=True))


def _parenthesized_role_path(task: str, aliases: tuple[str, ...]) -> str | None:
    """Bind a role description to its adjacent parenthesized location."""
    names = _alias_pattern(aliases)
    descriptor = (
        r"(?:regulatory|sample|covariate|adjusted|somatic|protein|interaction|"
        r"target|prediction|pathway|design|numeric|data|table|matrix|file|list|"
        r"prior|network|dataset)"
    )
    match = re.search(
        rf"(?<![A-Za-z0-9_])(?:{names})(?![A-Za-z0-9_])"
        rf"(?:\s+{descriptor}){{0,4}}\s*(?:檔案|清單|矩陣|資料|表)?\s*"
        r"[（(]\s*(?P<path>[^)）\n]+?)\s*[）)]",
        task, flags=re.IGNORECASE,
    )
    return match.group("path").strip().strip("'\"`") if match else None
