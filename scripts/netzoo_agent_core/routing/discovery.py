"""Bounded local file discovery and reversible output defaults."""

from __future__ import annotations

import os
import re
from pathlib import Path

from ..data.discovery import score_candidate_file as _score_candidate_file
from ..contracts import PROJECT_ROOT, _display_path

__all__ = [
    "FILE_DISCOVERY_MAX_DEPTH",
    "FILE_DISCOVERY_MAX_VISITED",
    "FILE_DISCOVERY_MAX_RESULTS",
    "_extract_named_path",
    "_extract_explicit_role_path",
    "_score_candidate_file",
    "_find_candidate_files",
    "_default_lioness_outputs",
    "_default_network_output",
]


FILE_DISCOVERY_MAX_DEPTH = 4


FILE_DISCOVERY_MAX_VISITED = 10_000


FILE_DISCOVERY_MAX_RESULTS = 200


def _extract_named_path(task: str, names: tuple[str, ...]) -> str | None:
    sorted_names = sorted(names, key=len, reverse=True)
    name_pattern = "|".join(re.escape(name) for name in sorted_names)
    pattern = re.compile(
        rf"(?<![A-Za-z0-9_])(?:{name_pattern})(?![A-Za-z0-9_])"
        r"\s*(?:是|為|=|:|：|at|as|is|to)?\s*"
        r"(?:(?P<quote>['\"])(?P<quoted>.*?)(?P=quote)|(?P<plain>[^\s，,。；;]+))",
        flags=re.IGNORECASE,
    )
    match = pattern.search(task)
    if not match:
        return None
    if match.group("quote"):
        return match.group("quoted")
    return match.group("plain").strip().rstrip(".。")


def _extract_explicit_role_path(task: str, role: str) -> str | None:
    match = re.search(
        rf"(?<![A-Za-z0-9_]){re.escape(role)}\s*=\s*"
        rf"(?:(?P<q>['\"])(?P<quoted>.*?)(?P=q)|(?P<plain>.*?))"
        r"(?=\s+[A-Za-z_]+\s*=|\s+[\u3400-\u9fff]|[，,；;]|$)",
        task,
        re.IGNORECASE,
    )
    if not match:
        return None
    return (match.group("quoted") if match.group("q") else match.group("plain")).strip().rstrip(".。")


def _find_candidate_files(
    keywords: tuple[str, ...],
    nearby: Path,
) -> list[str]:
    nearby = nearby.expanduser().resolve()
    roots = []
    for raw_root in (nearby, PROJECT_ROOT / "data"):
        root = raw_root.expanduser().resolve()
        if root not in roots:
            roots.append(root)
    candidates: list[tuple[int, Path]] = []
    seen: set[Path] = set()
    visited = 0
    for root in roots:
        if not root.is_dir():
            continue
        for directory, child_directories, filenames in os.walk(
            root,
            topdown=True,
            followlinks=False,
        ):
            directory_path = Path(directory)
            relative_depth = len(directory_path.relative_to(root).parts)
            child_directories[:] = sorted(
                child
                for child in child_directories
                if not (directory_path / child).is_symlink()
            )
            if relative_depth >= FILE_DISCOVERY_MAX_DEPTH:
                child_directories.clear()
            for filename in sorted(filenames):
                visited += 1
                if visited > FILE_DISCOVERY_MAX_VISITED:
                    break
                path = directory_path / filename
                if path in seen or path.is_symlink() or not path.is_file():
                    continue
                seen.add(path)
                name = path.name.casefold()
                if not any(keyword in name for keyword in keywords):
                    continue
                if path.suffix.casefold() not in {".tsv", ".tab", ".txt", ".csv", ".gmt"}:
                    continue
                candidates.append((_score_candidate_file(path, keywords, nearby), path))
                if len(candidates) >= FILE_DISCOVERY_MAX_RESULTS:
                    break
            if (
                visited > FILE_DISCOVERY_MAX_VISITED
                or len(candidates) >= FILE_DISCOVERY_MAX_RESULTS
            ):
                break
        if (
            visited > FILE_DISCOVERY_MAX_VISITED
            or len(candidates) >= FILE_DISCOVERY_MAX_RESULTS
        ):
            break
    if not candidates:
        return []
    candidates.sort(key=lambda item: (-item[0], len(str(item[1])), str(item[1])))
    return [_display_path(path) for _, path in candidates[:FILE_DISCOVERY_MAX_RESULTS]]


def _default_lioness_outputs(
    mode: str,
    expression_file: str,
    output_dir: str | Path = "outputs/demo",
) -> tuple[str, str]:
    stem = Path(expression_file).stem.replace("expression", "").strip("-_") or "lioness"
    prefix = f"{stem}-" if stem and stem != "lioness" else ""
    output_dir = Path(output_dir)
    aggregate = output_dir / f"{prefix}{mode}-aggregate.tsv"
    lioness = output_dir / f"{prefix}lioness-{mode}.tsv"
    return str(aggregate), str(lioness)


def _default_network_output(
    mode: str,
    expression_file: str,
    output_dir: str | Path = "outputs/demo",
) -> str:
    stem = Path(expression_file).stem.replace("expression", "").strip("-_") or mode
    prefix = f"{stem}-" if stem and stem != mode else ""
    return str(Path(output_dir) / f"{prefix}{mode}.tsv")
