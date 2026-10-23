"""Harness repair P4 (spec 9, ROUND-P4.md): which input files a run used, by content, and whether they are still
the same.

A fingerprint is taken at the execute gate, for the files the step is about to use. It names the content (sha256,
streamed), and the rules the files were checked against: the input-check code, the workflow's contract and the
project policy. A file is the same only when its sha256 is; size and mtime can only say it changed.

What it cannot guarantee: subprocess workflows re-open their paths after the gate, and nothing is copied, so a file
changed after the gate is not seen (TOCTOU is narrowed to the gate, not removed).
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Literal

from workflow_registry import ACTION_DEFINITIONS, REQUIRED_INPUTS

from ..contracts.memory import InputRevision
from .paths import _resolve_user_path

__all__ = ["Freshness", "freshness", "input_files", "preview_check", "revision", "step_revisions",
           "validator_hash"]

Freshness = Literal["unchanged", "changed", "rules_changed", "missing", "unverified"]

_OUTPUTS = frozenset({"output_file", "lioness_output", "output_dir"})
_FILE_FIELDS = frozenset({
    "expression_file", "design_file", "motif_file", "ppi_file", "mirna_file", "coexpression_file", "network_file",
    "mutation_file", "exon_size_file", "cancer_gene_file", "pathway_file", "omics_layer_1", "omics_layer_2"})
_CHUNK = 1 << 20


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


@lru_cache(maxsize=1)
def validator_hash() -> str:
    """sha256 of the input-check code (this package's modules): any change there makes an earlier check stale.

    Coarse on purpose (spec 9: invalidate conservatively); helper code outside the package is not covered."""
    digest = hashlib.sha256()
    for module in sorted(Path(__file__).parent.glob("*.py")):
        digest.update(module.name.encode())
        digest.update(module.read_bytes())
    return digest.hexdigest()


def contract_hash(policy, action: str) -> str | None:
    """sha256 of the workflow's parsed contract, or None when the policy has none for the action."""
    spec = (getattr(policy, "workflows", None) or {}).get(action)
    return hashlib.sha256(spec.model_dump_json().encode()).hexdigest() if spec is not None else None


def input_files(action: str, decision) -> dict[str, Path]:
    """The step's input files that exist: its required inputs and its optional input files, by field."""
    definition = ACTION_DEFINITIONS.get(action)
    required = [field for field in REQUIRED_INPUTS.get(action, ()) if field not in _OUTPUTS]
    optional = [field for field in (definition.optional_inputs if definition else ()) if field in _FILE_FIELDS]
    found = {}
    for field in dict.fromkeys([*required, *optional]):
        value = getattr(decision, field, None)
        path = _resolve_user_path(str(value)) if value else None
        if path is not None and path.is_file():
            found[field] = path
    return found


def revision(path: Path, action: str, policy=None) -> InputRevision:
    stat = path.stat()
    return InputRevision(path=str(path), size=stat.st_size, mtime_ns=stat.st_mtime_ns, sha256=_sha256(path),
                         validator=action, validator_hash=validator_hash(), contract_hash=contract_hash(policy, action),
                         policy_hash=getattr(policy, "policy_hash", None))


def step_revisions(action: str, decision, policy=None) -> dict[str, InputRevision]:
    """The fingerprints of a step's input files, by field."""
    return {field: revision(path, action, policy) for field, path in input_files(action, decision).items()}


def freshness(old: InputRevision | None, path: str, action: str, policy=None) -> tuple[Freshness, str]:
    """Whether a file is still the one an earlier run checked, and in words what differs."""
    if old is None:
        return "unverified", "no fingerprint was recorded for it then"
    current = _resolve_user_path(path)
    if not current.is_file():
        return "missing", "the file is no longer there"
    stat = current.stat()
    if stat.st_size != old.size or _sha256(current) != old.sha256:
        return "changed", "its content changed since"
    rules = [name for name, before, now in (
        ("the input checks", old.validator_hash, validator_hash()),
        ("the workflow contract", old.contract_hash, contract_hash(policy, action)),
        ("the project policy", old.policy_hash, getattr(policy, "policy_hash", None)),
    ) if before != now]
    if rules:
        return "rules_changed", f"the content is the same, but {', '.join(rules)} changed since"
    return "unchanged", "the content is the same (sha256) and the rules are unchanged"


def preview_check(action: str, decision, policy, previewed: dict | None) -> tuple[dict, str | None]:
    """The step's input files by canonical path, and why a confirmed preview's run may not start (A17): a file
    changed (sha256), gone, or never shown in the preview. `previewed` is given only for an executed step after a
    confirmed preview; without it nothing is compared. The guarantee ends at the execute gate (module docstring)."""
    try:
        found = {item.path: item.model_dump(mode="json") for item in step_revisions(action, decision, policy).values()}
    except OSError as error:
        return {}, (f"an input file could not be read to compare it with the preview ({error}); no analysis was "
                    "started." if previewed else None)
    if not previewed:
        return found, None
    present = input_files(action, decision)
    problems = [f"the input file {getattr(decision, field)} ({field}) is no longer there"
                for field in REQUIRED_INPUTS.get(action, ())
                if field not in _OUTPUTS and getattr(decision, field, None) and field not in present]
    for path, item in found.items():
        before = previewed.get(path)
        if before is None:
            problems.append(f"the plan now uses {path}, which the preview did not show")
        elif before.get("sha256") != item["sha256"]:
            problems.append(f"the input file {path} changed after the preview (sha256 {before.get('sha256', '')[:12]} "
                            f"-> {item['sha256'][:12]})")
    if not problems:
        return found, None
    return found, ("; ".join(problems) + "; no analysis was started. Ask for the preview again to check the current "
                   "files, then confirm the new one.")
