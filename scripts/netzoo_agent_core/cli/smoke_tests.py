"""Safe, deterministic preflight smoke tests for the interactive CLI."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from ..data.tables import _inspect_panda_inputs_impl
from ..settings import PROJECT_ROOT

__all__ = ["run_smoke_tests"]


@dataclass(frozen=True, slots=True)
class _SmokeCase:
    name: str
    directory: str
    expected_valid: bool
    expected_identifier: str


@dataclass(frozen=True, slots=True)
class _CaseResult:
    status: str
    expected: str
    actual: str
    cache_hits: int = 0
    online_queries: int = 0
    statuses: tuple[str, ...] = ()
    authorities: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()
    detail: str = ""


_CASES = (
    _SmokeCase(
        name="valid fixtures",
        directory="data/auto-check-valid",
        expected_valid=True,
        expected_identifier="",
    ),
    _SmokeCase(
        name="invalid fixtures",
        directory="data/auto-check-invalid",
        expected_valid=False,
        expected_identifier="ENSG00000999999",
    ),
)
_RECORD_LINE = re.compile(r"^\s+- id: (?P<id>[^;]+); (?P<body>.*)$")
_FIELD = re.compile(r"(?:^|; )(?P<name>status|authority|source): (?P<value>[^;]+)")
_CACHE_HITS = re.compile(r"(\d+) cache hit\(s\)")
_ONLINE_QUERIES = re.compile(r"(\d+) online lookup batch\(es\)")


def _fixture_paths(case: _SmokeCase) -> tuple[Path, Path, Path]:
    root = PROJECT_ROOT / case.directory
    return root / "expression.tsv", root / "motif.tsv", root / "ppi.tsv"


def _parse_report(report: str) -> tuple[dict[str, str], set[str], set[str], int, int]:
    statuses: dict[str, str] = {}
    authorities: set[str] = set()
    sources: set[str] = set()
    for line in report.splitlines():
        match = _RECORD_LINE.match(line)
        if not match:
            continue
        identifier = match.group("id").strip()
        fields = {
            field.group("name"): field.group("value").strip()
            for field in _FIELD.finditer(match.group("body"))
        }
        if identifier:
            statuses[identifier.casefold()] = fields.get("status", "unknown")
        if fields.get("authority"):
            authorities.add(fields["authority"])
        if fields.get("source"):
            sources.add(fields["source"])
    cache_hits = sum(int(value) for value in _CACHE_HITS.findall(report))
    online_queries = sum(int(value) for value in _ONLINE_QUERIES.findall(report))
    return statuses, authorities, sources, cache_hits, online_queries


def _first_reason(report: str) -> str:
    for line in report.splitlines():
        stripped = line.strip()
        if stripped.startswith("error:") or stripped.startswith("warning:"):
            return stripped
    return ""


def _run_case(case: _SmokeCase) -> _CaseResult:
    expression, motif, ppi = _fixture_paths(case)
    missing = [str(path.relative_to(PROJECT_ROOT)) for path in (expression, motif, ppi) if not path.exists()]
    if missing:
        return _CaseResult(
            status="FAIL",
            expected="fixture files are present",
            actual="missing " + ", ".join(missing),
            detail="Create or restore the bundled smoke-test fixtures.",
        )

    try:
        report, preflight_passed, _ = _inspect_panda_inputs_impl(
            expression_file=str(expression),
            motif_file=str(motif),
            ppi_file=str(ppi),
            taxon="Homo sapiens",
        )
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        return _CaseResult(
            status="FAIL",
            expected="preflight completes without an exception",
            actual=f"{type(exc).__name__}: {exc}",
            detail="The smoke test could not inspect the fixture files.",
        )

    statuses, authorities, sources, cache_hits, online_queries = _parse_report(report)
    status_values = tuple(sorted(set(statuses.values())))
    expected = "preflight passes with authoritative labels" if case.expected_valid else "preflight blocks the unknown label"
    target_status = statuses.get(case.expected_identifier.casefold())

    if case.expected_valid:
        if preflight_passed and statuses and set(status_values) == {"valid"}:
            result_status = "PASS"
            actual = "preflight passed; all labels are authoritative"
        elif any(status in {"unverified", "remote_error"} for status in status_values):
            result_status = "INCONCLUSIVE"
            actual = "authority lookup was unresolved"
        else:
            result_status = "FAIL"
            actual = "preflight did not produce the expected valid result"
    else:
        blocked_for_label = (
            case.expected_identifier.casefold() in statuses
            and not preflight_passed
            and (
                "not recognized by the configured gene authority" in report
                or "could not be authoritatively verified" in report
            )
        )
        if blocked_for_label and target_status == "invalid":
            result_status = "PASS"
            actual = "preflight blocked the unknown label authoritatively"
        elif blocked_for_label and target_status in {"unverified", "remote_error"}:
            result_status = "PASS"
            actual = "preflight blocked the unresolved label safely"
        elif target_status in {"unverified", "remote_error"}:
            result_status = "INCONCLUSIVE"
            actual = "offline lookup did not produce an authoritative block"
        else:
            result_status = "FAIL"
            actual = "the unknown label was not blocked for the expected reason"

    return _CaseResult(
        status=result_status,
        expected=expected,
        actual=actual,
        cache_hits=cache_hits,
        online_queries=online_queries,
        statuses=status_values,
        authorities=tuple(sorted(authorities)),
        sources=tuple(sorted(sources)),
        detail=_first_reason(report),
    )


def _render_case(case: _SmokeCase, result: _CaseResult) -> list[str]:
    lines = [
        f"- {case.name}: {result.status}",
        f"  expected: {result.expected}",
        f"  actual: {result.actual}",
        f"  cache_hits: {result.cache_hits}; online_queries: {result.online_queries}",
        "  statuses: " + (", ".join(result.statuses) if result.statuses else "(none)"),
        "  authorities: " + (", ".join(result.authorities) if result.authorities else "(none)"),
        "  sources: " + (", ".join(result.sources) if result.sources else "(none)"),
    ]
    if result.detail:
        lines.append(f"  detail: {result.detail}")
    return lines


def run_smoke_tests() -> str:
    """Run bundled preflight checks without invoking a workflow executor."""
    results = [(case, _run_case(case)) for case in _CASES]
    statuses = [result.status for _, result in results]
    if "FAIL" in statuses:
        overall = "FAIL"
    elif "INCONCLUSIVE" in statuses:
        overall = "INCONCLUSIVE"
    else:
        overall = "PASS"

    online_setting = os.environ.get("NETZOO_GENE_ONLINE_LOOKUP", "auto")
    lines = [
        "NetZoo smoke tests (preflight only; no workflow executed)",
        f"Configuration: NETZOO_GENE_ONLINE_LOOKUP={online_setting}",
    ]
    for case, result in results:
        lines.extend(_render_case(case, result))
    lines.extend(
        [
            f"Overall: {overall}",
            "Websearch is never treated as authoritative; unresolved labels remain blocked or inconclusive.",
        ]
    )
    return "\n".join(lines)
