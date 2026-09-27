"""Find and load recorded routing reports, plain or gzip-compressed.

A report is the JSON written by `scripts/evaluate_routing.py --json` or by the
traced harness (`live-semantic-trace-2026-09-23-harness.py`): a dict with
`metadata`, `summary` and `results`; harness rows also carry `_trace` with the
prompt, every provider call, every routing event and the final decision.

Reports live in two places: `docs/research-log/live-*.json` (plain) and
`docs/research-log/archive/<session>/` (moved out of per-session /tmp
scratchpads on 2026-09-27; files over 200 kB are gzip-compressed).
"""

from __future__ import annotations

import gzip
import json
from collections.abc import Iterator
from pathlib import Path

RESEARCH = Path(__file__).resolve().parents[1]
ROOT = RESEARCH.parents[1]

__all__ = ["RESEARCH", "ROOT", "load_report", "report_paths", "traced_rows"]


def load_report(path: str | Path):
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def report_paths(include_archive: bool = True) -> list[Path]:
    """Every recorded file that parses as a report with results."""
    candidates = sorted(RESEARCH.glob("live-*.json"))
    if include_archive:
        candidates += sorted(RESEARCH.glob("archive/*/*.json")) + sorted(RESEARCH.glob("archive/*/*.json.gz"))
    paths = []
    for path in candidates:
        try:
            report = load_report(path)
        except (OSError, ValueError):
            continue
        if isinstance(report, dict) and isinstance(report.get("results"), list):
            paths.append(path)
    return paths


def traced_rows(paths=None) -> Iterator[tuple[Path, int, dict]]:
    """(path, row index, row) for every harness row that carries a `_trace`."""
    for path in paths if paths is not None else report_paths():
        for index, row in enumerate(load_report(path).get("results", [])):
            if row.get("_trace"):
                yield Path(path), index, row
