"""Shared path validation for outputs derived by NetZoo workflows."""

from __future__ import annotations

import re
from pathlib import Path

from ..contracts import OUTPUT_ROLE_FIELDS, PROJECT_ROOT, TaskDecision

def _resolve_user_path(path: str) -> Path:
    raw = Path(path).expanduser()
    candidates = [raw] if raw.is_absolute() else [Path.cwd() / raw, PROJECT_ROOT / raw]
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.exists():
            return resolved
    return candidates[0].resolve()

__all__ = [
    "condor_artifact_paths",
    "resolved_output_collisions",
    "validate_output_basename",
]


SAFE_OUTPUT_BASENAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")


def validate_output_basename(value: str, label: str) -> str:
    """Return a safe filename component or reject directory/path syntax."""
    if (
        not value
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
        or SAFE_OUTPUT_BASENAME.fullmatch(value) is None
    ):
        raise ValueError(
            f"{label} must be a simple filename prefix containing only letters, "
            "digits, dots, underscores, and hyphens"
        )
    return value


def condor_artifact_paths(
    output_dir: str | Path,
    prefix: str,
) -> dict[str, Path]:
    """Resolve every required CONDOR artifact beneath one output directory."""
    root = _resolve_user_path(str(output_dir))
    safe_prefix = validate_output_basename(prefix or "condor", "prefix")
    suffixes = ("edges.tsv", "reg_memb.tsv", "tar_memb.tsv", "summary.txt")
    paths = {
        suffix: (root / f"{safe_prefix}-{suffix}").resolve() for suffix in suffixes
    }
    if any(not path.is_relative_to(root) for path in paths.values()):
        raise ValueError("CONDOR output path escapes output_dir")
    return paths


def resolved_output_collisions(decision: TaskDecision) -> list[str]:
    """Describe populated output roles that resolve to the same path."""
    roles_by_path: dict[Path, list[str]] = {}
    for field_name in sorted(OUTPUT_ROLE_FIELDS):
        value = getattr(decision, field_name, None)
        if value:
            roles_by_path.setdefault(_resolve_user_path(value), []).append(field_name)
    return [
        f"{', '.join(roles)} resolve to {path}"
        for path, roles in roles_by_path.items()
        if len(roles) > 1
    ]
