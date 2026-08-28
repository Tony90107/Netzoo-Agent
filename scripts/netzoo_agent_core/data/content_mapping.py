"""Content-based input-role discovery for every registered NetZoo workflow."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..contracts import InputRoleAssignment, InputRoleMapping, PROJECT_ROOT
from ..data.paths import _resolve_user_path
from ..framework_compat import HumanMessage, SystemMessage

__all__ = ["infer_input_roles"]


_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])(?P<path>[A-Za-z0-9_./~\\-]+"
    r"\.(?:tsv|tab|txt|csv|npy|npz|bed|mtx|h5|hdf5)(?:\.gz)?)"
    r"[.。]?(?![A-Za-z0-9_.-])",
    flags=re.IGNORECASE,
)
_SUPPORTED_SUFFIXES = frozenset(
    {".tsv", ".tab", ".txt", ".csv", ".npy", ".npz", ".bed", ".mtx", ".h5", ".hdf5", ".gz"}
)
_MAX_CANDIDATES = 120
_MAX_PREVIEW_CHARS = 4_000
_ROLE_ALIASES = {
    "expression": "expression_file",
    "expr": "expression_file",
    "design": "design_file",
    "covariate": "design_file",
    "metadata": "design_file",
    "motif": "motif_file",
    "prior": "motif_file",
    "ppi": "ppi_file",
    "protein_interaction": "ppi_file",
    "interaction": "ppi_file",
    "mirna": "mirna_file",
    "microrna": "mirna_file",
    "coexpression": "coexpression_file",
    "co-expression": "coexpression_file",
    "network": "network_file",
    "bipartite": "network_file",
    "omics_layer_1": "omics_layer_1",
    "omics_layer_2": "omics_layer_2",
    "layer1": "omics_layer_1",
    "layer2": "omics_layer_2",
    "omics1": "omics_layer_1",
    "omics2": "omics_layer_2",
    "first_omics": "omics_layer_1",
    "second_omics": "omics_layer_2",
}
_ROLE_GUIDANCE = {
    "expression_file": "gene-by-sample numeric expression matrix; first column commonly contains gene IDs",
    "design_file": "sample-by-covariate numeric design matrix whose sample IDs align with expression columns",
    "motif_file": "regulator-to-gene prior edge list or BED-like motif prior",
    "ppi_file": "protein-protein or TF interaction edge list, normally with two node IDs",
    "mirna_file": "one-column miRNA identifier list, or a miRNA-containing prior list",
    "coexpression_file": "adjusted gene-by-gene numeric co-expression matrix",
    "network_file": "weighted source-target bipartite edge list for CONDOR",
    "omics_layer_1": "DRAGON layer 1; rows are samples and columns are continuous features",
    "omics_layer_2": "DRAGON layer 2; rows are the same samples and columns are continuous features",
}


def _path_candidates(task: str, nearby: Path) -> list[Path]:
    """Collect user-named files and nearby table files without broad filesystem reads."""
    paths: dict[Path, None] = {}
    directories: set[Path] = set()
    for match in _PATH_RE.finditer(task):
        candidate = _resolve_user_path(match.group("path")).resolve()
        if candidate.is_file() and not candidate.is_symlink():
            paths[candidate] = None
            directories.add(candidate.parent)
    anchor = nearby.expanduser().resolve()
    if anchor.is_file():
        anchor = anchor.parent
    if anchor.is_dir():
        directories.add(anchor)
    if not directories:
        data_root = (PROJECT_ROOT / "data").resolve()
        if data_root.is_dir():
            directories.add(data_root)
    for directory in sorted(directories, key=str):
        try:
            children = sorted(directory.iterdir(), key=lambda item: str(item))
        except OSError:
            continue
        for child in children:
            if (
                child.is_file()
                and not child.is_symlink()
                and any(child.name.casefold().endswith(suffix) for suffix in _SUPPORTED_SUFFIXES)
            ):
                paths[child.resolve()] = None
                if len(paths) >= _MAX_CANDIDATES:
                    return list(paths)
    return list(paths)


def _preview(path: Path) -> str:
    try:
        data = path.read_bytes()[:_MAX_PREVIEW_CHARS]
    except OSError as error:
        return f"<unreadable: {type(error).__name__}>"
    return data.decode("utf-8", errors="replace").replace("\x00", " ").strip()


def _prompt(action: str, fields: list[str], candidates: list[Path]) -> str:
    role_text = "\n".join(
        f"- {field}: {_ROLE_GUIDANCE.get(field, 'registered NetZoo input role')}"
        for field in fields
    )
    file_text = "\n\n".join(
        f"FILE: {path}\nCONTENT PREVIEW:\n{_preview(path)}"
        for path in candidates
    )
    return (
        "You are the NetZoo input-role resolver. Map candidate files to the unresolved "
        "input roles for the registered workflow. Use content structure, headers, "
        "column counts, identifier patterns, and the workflow contract; filenames are "
        "only weak evidence. Return only JSON matching the supplied schema. Include "
        "at most one best assignment per role, a confidence from 0 to 1, and a short "
        "rationale. Never invent a path and never map output files.\n\n"
        f"WORKFLOW ACTION: {action}\nUNRESOLVED ROLES:\n{role_text}\n\n"
        f"CANDIDATE FILES:\n{file_text}"
    )


def _payload(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return getattr(value, "content", value)


def _canonical_path(value: str, candidates: list[Path]) -> Path | None:
    try:
        resolved = _resolve_user_path(value).resolve()
    except (OSError, RuntimeError, TypeError):
        return None
    exact = {path: path for path in candidates}.get(resolved)
    if exact is not None:
        return exact
    basename_matches = [path for path in candidates if path.name == Path(value).name]
    return basename_matches[0] if len(basename_matches) == 1 else None


def infer_input_roles(
    action: str,
    task: str,
    fields: list[str],
    nearby: Path,
    mapper: Any | None = None,
) -> dict[str, InputRoleAssignment]:
    """Ask the configured LLM for bounded content mappings, or decline safely."""
    if mapper is None or not fields:
        return {}
    candidates = _path_candidates(task, nearby)
    if not candidates:
        return {}
    messages = [
        SystemMessage(
            content=(
                "NetZoo role mapping is advisory only. Select only from the listed "
                "candidate paths and unresolved roles."
            )
        ),
        HumanMessage(content=_prompt(action, fields, candidates)),
    ]
    try:
        structured_mapper = (
            mapper.with_structured_output(
                InputRoleMapping,
                method="function_calling",
                include_raw=False,
            )
            if hasattr(mapper, "with_structured_output")
            else mapper
        )
        response = structured_mapper.invoke(messages)
        mapping = InputRoleMapping.model_validate(_payload(response))
    except Exception:
        return {}

    candidate_by_path = {path: path for path in candidates}
    accepted: dict[str, InputRoleAssignment] = {}
    used_paths: set[Path] = set()
    for assignment in sorted(
        mapping.assignments,
        key=lambda item: (-item.confidence, item.role, item.path),
    ):
        role = _ROLE_ALIASES.get(assignment.role.casefold(), assignment.role.casefold())
        if role not in fields or role in accepted or assignment.confidence < 0.55:
            continue
        path = _canonical_path(assignment.path, candidates)
        if path is None or path in used_paths:
            continue
        accepted[role] = assignment.model_copy(
            update={"role": role, "path": str(candidate_by_path[path])}
        )
        used_paths.add(path)
    return accepted
