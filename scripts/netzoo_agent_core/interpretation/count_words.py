"""ROUND-07 (collab/ROUND-07-PLAN.md, G1): a count whose words give it more than one way. Pure code.

A count is stated only when its words give that one number. "They may contain two or ten paired samples" gives two
candidates, and "8-15 tumours" a range; reading either as one number (2, or 8) would settle a doubt the user left
open (h4 M38: "either 8 or 15" read as 8). Two numbers are side by side -- candidates for one count -- when nothing
but punctuation stands between them ("8-15", "8/15", "8, 15"), or one word with only spaces around it ("8 or 15",
"8 to 15"). Two quantities of different things keep their own words and punctuation between them: "88 donors: 44
AD" and "6 tumours x 900 genes" are not candidates. No list of connecting words is used.
"""

from __future__ import annotations

import re

from ..workflow_conditions import _NUMBER, _WORDS

__all__ = ["candidate_runs", "number_spans", "side_by_side", "side_by_side_values"]

_IDENTIFIER = re.compile(r"\b\w+\.[A-Za-z][A-Za-z0-9]{1,4}\b|\b[a-z0-9]+_[a-z0-9_]+\b")
"""A file name or identifier (rna_85.csv): the numbers inside it count nothing (as `menu_reader._IDENTIFIER`)."""
_ONE_WORD = re.compile(r"\s+[^\W\d_]+\s+")
_NO_WORD = re.compile(r"[^\w]*")


def number_spans(text: str) -> list[tuple[float, int, int]]:
    """(value, start, end) of each number the words state -- digits and number words, as `stated_numbers` reads
    them -- in order, less those inside a file name or identifier."""
    text = text or ""
    inside = [(m.start(), m.end()) for m in _IDENTIFIER.finditer(text)]
    found = []
    for match in _NUMBER.finditer(text):
        raw = match.group().replace(",", "").replace(" ", "")
        if not any(ch.isdigit() for ch in raw):
            continue
        try:
            value = float(raw.rstrip("kK")) * (1000 if raw[-1:] in "kK" else 1)
        except ValueError:
            continue
        found.append((abs(value) if raw[:1] in "-+" else value, match.start(), match.end()))
    for match in re.finditer(r"[A-Za-z]+", text):
        if (word := match.group().casefold()) in _WORDS:
            found.append((float(_WORDS[word]), match.start(), match.end()))
    return sorted((item for item in found if not any(s <= item[1] < e for s, e in inside)), key=lambda item: item[1])


def _beside(gap: str) -> bool:
    return bool(_NO_WORD.fullmatch(gap) or _ONE_WORD.fullmatch(gap))


def side_by_side_values(text: str, value: float, numbers=None) -> list[float]:
    """Every number standing in one run of side-by-side numbers with this one, in order ([] when it stands alone).

    `numbers`: the (value, start, end) to read, when the caller parses numbers its own way (`veto_evidence`)."""
    numbers = number_spans(text) if numbers is None else sorted(numbers, key=lambda item: item[1])
    runs, run = [], []
    for item in numbers:
        if run and not _beside(text[run[-1][2]:item[1]]):
            runs.append(run)
            run = []
        run.append(item)
    if run:
        runs.append(run)
    for run in runs:
        values = list(dict.fromkeys(found for found, _start, _end in run))
        if value in values and len(values) >= 2:
            return values
    return []


def side_by_side(text: str, value: float, numbers=None) -> bool:
    """Whether another number stands beside this one as a candidate for the same count."""
    return bool(side_by_side_values(text, value, numbers))


def candidate_runs(text: str) -> list[tuple[list[float], int, int]]:
    """(values, start, end) of each run of side-by-side whole numbers in the words -- two or more different ones, each
    at least 1 ("either one or two", "8-15"): the user's candidates for one count, when no reading wrote them.

    A number glued to a letter ("10x", "3D", "2nd") is a unit, a dimension or an order, never a count (CELLS
    "a single 10x run" is not "1 or 10"); a fraction counts nothing ("delta is 0.2 or 0.5")."""
    text = text or ""
    numbers = [item for item in number_spans(text) if not text[item[2]:item[2] + 1].isalpha()]
    runs, run = [], []
    for item in numbers:
        if run and not _beside(text[run[-1][2]:item[1]]):
            runs.append(run)
            run = []
        run.append(item)
    runs.append(run)
    found = []
    for run in runs:
        values = sorted({value for value, _start, _end in run})
        if len(values) >= 2 and all(value >= 1 and value == int(value) for value in values):
            found.append((values, run[0][1], run[-1][2]))
    return found
