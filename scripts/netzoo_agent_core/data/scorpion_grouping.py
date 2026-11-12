"""SCORPION groups and comparison read from a request's own words against its cell metadata (2026-11-10).

"Build one network per donor and region ..., then compare tumour (region T) against normal (region N)" built a single
`all_cells` network: only `group_by=` assignments were read, so the stated grouping was dropped without a word (live
2026-11-10). Nothing here is guessed: a word becomes `group_by` only when it names a column of the request's metadata
table, and a side of the comparison only when it names one value of one column. Anything ambiguous is left unset,
as before, and the run's own checks still decide.
"""

from __future__ import annotations

import re
from typing import Any

from scorpion_io import read_cell_metadata

from .paths import _resolve_user_path

__all__ = ["scorpion_plan_lines", "stated_grouping"]

_ANCHOR = re.compile(r"\b(?:per|for\s+(?:each|every)|split\s+by|grouped\s+by|stratified\s+by)\s+", re.I)
_JOIN = re.compile(r"\s*(?:,\s*(?:and\s+)?|\band\b|&|\bx\b|×)\s*", re.I)
_COMPARE = re.compile(
    r"\bcompar\w*\s+(?P<one>[^.;!?]{1,80}?)\s+(?:against|versus|vs\.?|with|to)\s+(?P<two>[^.;!?]{1,80})", re.I)


def _column_patterns(columns: list[str]) -> list[tuple[str, re.Pattern]]:
    """Each column with the words that name it ("cell_type" -> cell type / cell types / cell_type)."""
    found = []
    for column in sorted(columns, key=len, reverse=True):
        words = r"[\s_-]+".join(re.escape(part) for part in re.split(r"[\s_-]+", column) if part)
        found.append((column, re.compile(rf"(?:the\s+)?{words}(?:e?s)?(?![A-Za-z0-9])", re.I)))
    return found


def _grouping_columns(task: str, patterns) -> list[str]:
    for anchor in _ANCHOR.finditer(task):
        position, named = anchor.end(), []
        while True:
            hit = next(((column, m) for column, pattern in patterns if (m := pattern.match(task, position))), None)
            if hit is None:
                break
            named.append(hit[0])
            position = hit[1].end()
            joined = _JOIN.match(task, position)
            if joined is None:
                break
            position = joined.end()
        if named:
            return list(dict.fromkeys(named))
    return []


def _side(text: str, values: dict[str, set[str]], patterns, prefer: list[str]) -> set[tuple[str, str]]:
    """(column, value) pairs one side of the comparison names: "region T" first, else a bare value token."""
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_.+-]*", text)
    named = set()
    for column, pattern in patterns:  # "region T", "(region N)"
        for found in pattern.finditer(text):
            after = re.match(r"\s*[=:]?\s*([A-Za-z0-9][A-Za-z0-9_.+-]*)", text[found.end():])
            if after and after.group(1) in values[column]:
                named.add((column, after.group(1)))
    if named:
        return named
    hits = {(column, token) for token in tokens for column in values if token in values[column]}
    preferred = {hit for hit in hits if hit[0] in prefer}
    return preferred or hits


def stated_grouping(task: str, metadata_file: str | None) -> dict[str, Any]:
    """group_by / compare_by / group1 / group2 the request states in words, checked against its metadata table."""
    if not metadata_file:
        return {}
    frame, id_column, errors = read_cell_metadata(_resolve_user_path(metadata_file))
    if frame is None or errors:
        return {}
    columns = [str(column) for column in frame.columns if column != id_column]
    patterns = _column_patterns(columns)
    found: dict[str, Any] = {}
    if group_by := _grouping_columns(task, patterns):
        found["group_by"] = group_by
    compared = _COMPARE.search(task)
    if compared:
        values = {column: {str(v) for v in frame[column].dropna().unique() if str(v)} for column in columns}
        one = _side(compared.group("one"), values, patterns, group_by)
        two = _side(compared.group("two"), values, patterns, group_by)
        if len(one) == 1 and len(two) == 1:
            (column, first), (other, second) = next(iter(one)), next(iter(two))
            if column == other and first != second:
                found.update(compare_by=column, group1=first, group2=second)
                found["group_by"] = list(dict.fromkeys([*found.get("group_by", []), column]))
    return found


def scorpion_plan_lines(decision: dict) -> list[str]:
    """Which networks the plan builds and what it compares, so a grouping read from words can be checked."""
    group_by = decision.get("group_by") or []
    if isinstance(group_by, str):
        group_by = [part.strip() for part in group_by.split(",") if part.strip()]
    lines = [f"- One network per {' x '.join(group_by)} (cell metadata columns)" if group_by
             else "- One network from all cells (no grouping column set)"]
    if decision.get("compare_by") and decision.get("group1") and decision.get("group2"):
        lines.append(f"- Compared: {decision['compare_by']} {decision['group1']} vs {decision['group2']} "
                     "(testEdges; log2 fold change is the first minus the second)")
    return lines
