"""Deterministic extraction used only to echo explicit request parameters."""

from __future__ import annotations

import re

from ..contracts import PROSE_PATH_TERMINATORS
from .discovery import _unlabeled_input_bindings
from .extraction import _task_path

__all__: list[str] = []

# Roles whose file a request may name without saying which role it is.
_INPUT_ROLE_FIELDS = tuple(
    field_name for field_name in (
        "expression_file", "design_file", "motif_file", "ppi_file",
        "mirna_file", "coexpression_file", "network_file", "mutation_file",
        "exon_size_file", "cancer_gene_file", "pathway_file",
    )
)
_FILE_SUFFIXES = (
    ".tsv", ".tab", ".txt", ".csv", ".gmt", ".npy", ".npz", ".bed", ".mtx",
    ".h5", ".hdf5", ".gz",
)

_PATH_FIELDS = (
    "expression_file",
    "design_file",
    "motif_file",
    "ppi_file",
    "mirna_file",
    "coexpression_file",
    "network_file",
    "mutation_file",
    "exon_size_file",
    "cancer_gene_file",
    "pathway_file",
    "output_file",
    "output_dir",
)
_BOOLEAN_FIELDS = (
    "sparsify",
    "save_pvals",
    "keep_in_memory",
    "log_transformed",
    "centered",
)

_TAXON_NEXT_FIELD = (
    r"expression_file|motif_file|ppi_file|output_file|output_dir|taxon|species|organism"
)


def extract_explicit_taxon(task: str) -> str | None:
    """Return an explicitly labelled organism without interpreting free prose."""
    match = re.search(
        rf"(?:(?<![A-Za-z0-9_])(?:taxon|species|organism)(?![A-Za-z0-9_])|物種)"
        rf"\s*(?:=|:|：|is\b|是|為)\s*"
        rf"(?P<taxon>[A-Za-z0-9_-]+"
        rf"(?:\s+(?!(?:{_TAXON_NEXT_FIELD})\b)[A-Za-z][A-Za-z0-9_-]+)?)"
        rf"(?=\s*(?:$|[,，;；。!?！？\n]|[^A-Za-z0-9_\s]|(?:{_TAXON_NEXT_FIELD})\b))",
        task,
        flags=re.IGNORECASE,
    )
    return match.group("taxon").strip() if match else None


def _sample_names(task: str) -> list[str]:
    assignment = re.search(
        r"(?:sample_names?|sample_ids?)\s*=\s*([^;\n。]+)",
        task,
        flags=re.IGNORECASE,
    )
    if assignment:
        raw = assignment.group(1).strip().split()[0].rstrip(",，")
        names = [item.strip() for item in re.split(r"[,，]", raw) if item.strip()]
        if names:
            return list(dict.fromkeys(names))

    # Keep this an echo-only witness. It does not decide whether the identifiers
    # exist or which workflow should consume them; BONOBO preflight owns that.
    if not re.search(r"sample|樣本|病患|病人|個案", task, flags=re.IGNORECASE):
        return []
    names = re.findall(
        r"(?<![A-Za-z0-9])S\d+(?![A-Za-z0-9])",
        task,
        flags=re.IGNORECASE,
    )
    unique: dict[str, str] = {}
    for name in names:
        unique.setdefault(name.casefold(), name)
    return list(unique.values())


def _explicit_path(task: str, field_name: str) -> str | None:
    assignment = re.search(
        rf"\b{field_name}\s*=\s*(?:'([^']+)'|\"([^\"]+)\"|([^{PROSE_PATH_TERMINATORS}]+))",
        task,
        flags=re.IGNORECASE,
    )
    if assignment:
        return next(value for value in assignment.groups() if value is not None)
    return _task_path(task, field_name)


def _looks_like_file(value: object) -> bool:
    return str(value).casefold().endswith(_FILE_SUFFIXES)


def _place_output_by_shape(parameters: dict[str, object]) -> None:
    """Let the value decide whether an output is a file or a directory.

    "輸出到 X" and "output to X" mean the same thing, but the first matches an
    output_dir alias and the second an output_file alias, so the same request
    echoed a path as a directory in one language and a file in the other. A
    value ending in a table suffix is a file whichever phrase introduced it.
    """
    directory = parameters.get("output_dir")
    if directory is not None and _looks_like_file(directory):
        parameters.pop("output_dir")
        parameters.setdefault("output_file", directory)


def extract_recognized_input_files(task: str) -> dict[str, str]:
    """Return input files the request names without naming their role.

    The echo exists to show the user what survived a routing failure. Listing
    only role-labelled paths meant a request that simply listed its files
    reported nothing at all, under a sentence promising those inputs would be
    carried forward.
    """
    return _unlabeled_input_bindings(task, _INPUT_ROLE_FIELDS)


def extract_explicit_request_parameters(task: str) -> dict[str, object]:
    """Return only values explicitly present in the latest user request."""
    parameters: dict[str, object] = {}
    for field_name in _PATH_FIELDS:
        value = _explicit_path(task, field_name)
        if value:
            parameters[field_name] = value
    _place_output_by_shape(parameters)
    taxon = extract_explicit_taxon(task)
    if taxon:
        parameters["taxon"] = taxon
    names = _sample_names(task)
    if names:
        parameters["sample_names"] = names
    for field_name in _BOOLEAN_FIELDS:
        match = re.search(
            rf"\b{field_name}\s*=\s*(true|false)\b",
            task,
            flags=re.IGNORECASE,
        )
        if match:
            parameters[field_name] = match.group(1).casefold() == "true"
    for field_name, aliases in (
        ("precision", r"single|double"),
        ("bonobo_output_format", r"\.?h5|\.?hdf|\.?txt|\.?csv"),
    ):
        match = re.search(
            rf"\b{field_name}\s*=\s*({aliases})\b",
            task,
            flags=re.IGNORECASE,
        )
        if match:
            value = match.group(1).casefold()
            if field_name == "bonobo_output_format" and not value.startswith("."):
                value = "." + value
            parameters[field_name] = value
    for field_name in ("bonobo_confidence", "confidence", "delta"):
        match = re.search(
            rf"\b{field_name}\s*=\s*([0-9]*\.?[0-9]+)\b",
            task,
            flags=re.IGNORECASE,
        )
        if match:
            parameters[field_name] = match.group(1)
    return parameters


def has_explicit_request_parameters(task: str) -> bool:
    return bool(extract_explicit_request_parameters(task))


def render_request_parameters(parameters: dict[str, object]) -> str:
    """Render a compact, stable parameter echo for guidance and fallback text."""
    labels = {
        "sample_names": "Sample IDs (`sample_names`)",
    }
    lines = []
    for field_name, value in parameters.items():
        label = labels.get(field_name, f"`{field_name}`")
        if isinstance(value, list):
            rendered = ", ".join(str(item) for item in value)
        elif isinstance(value, bool):
            rendered = str(value).lower()
        else:
            rendered = str(value)
        lines.append(f"- {label}: {rendered}")
    return "Captured request parameters:\n\n" + "\n".join(lines)


def render_explicit_request_parameters(task: str) -> str | None:
    parameters = extract_explicit_request_parameters(task)
    recognized = {
        field_name: value
        for field_name, value in extract_recognized_input_files(task).items()
        if field_name not in parameters
    }
    if not parameters and not recognized:
        return None
    sections = []
    if parameters:
        sections.append(render_request_parameters(parameters))
    if recognized:
        lines = "\n".join(
            f"- `{field_name}`: {value}" for field_name, value in recognized.items()
        )
        sections.append(
            "Input files recognized by filename (role not stated in the "
            f"request, so it is still to be confirmed):\n\n{lines}"
        )
    return "\n\n".join(sections)
