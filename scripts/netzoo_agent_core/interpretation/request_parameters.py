"""Deterministic extraction used only to echo explicit request parameters."""

from __future__ import annotations

import re

from .extraction import _task_path

__all__: list[str] = []

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
        rf"\b{field_name}\s*=\s*(?:'([^']+)'|\"([^\"]+)\"|([^\s,，;；。!?！？]+))",
        task,
        flags=re.IGNORECASE,
    )
    if assignment:
        return next(value for value in assignment.groups() if value is not None)
    return _task_path(task, field_name)


def extract_explicit_request_parameters(task: str) -> dict[str, object]:
    """Return only values explicitly present in the latest user request."""
    parameters: dict[str, object] = {}
    for field_name in _PATH_FIELDS:
        value = _explicit_path(task, field_name)
        if value:
            parameters[field_name] = value
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
    return render_request_parameters(parameters) if parameters else None
