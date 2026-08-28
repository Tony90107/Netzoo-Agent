"""Neutral file naming and candidate scoring rules."""

from __future__ import annotations

from pathlib import Path

from ..settings import PROJECT_ROOT

__all__: list[str] = []


def candidate_keywords(action: str, field_name: str) -> tuple[str, ...]:
    mode = "puma" if "puma" in action else "panda" if "panda" in action else ""
    if field_name == "expression_file":
        return ("expression", "expr")
    if field_name == "motif_file":
        extra = ("seed",) if action == "run_otter" else ()
        return tuple(part for part in (mode, "motif", "prior", *extra) if part)
    if field_name == "ppi_file":
        return ("ppi",)
    if field_name == "mirna_file":
        return ("mirna", "mir")
    if field_name == "network_file":
        return ("condor", "bipartite", "network")
    if action == "run_dragon" and field_name == "omics_layer_1":
        return ("layer1", "omics1", "transcript", "expression")
    if action == "run_dragon" and field_name == "omics_layer_2":
        return ("layer2", "omics2", "methyl", "chromatin")
    if action == "run_otter" and field_name == "coexpression_file":
        return ("coexpression", "co-expression", "correlation", "adjusted")
    if action == "run_otter" and field_name == "motif_file":
        return ("motif", "prior", "seed")
    if action == "run_otter" and field_name == "ppi_file":
        return ("ppi", "protein", "interaction")
    return ()


def score_candidate_file(
    path: Path,
    keywords: tuple[str, ...],
    nearby: Path,
) -> int:
    relative = (
        path.relative_to(PROJECT_ROOT) if path.is_relative_to(PROJECT_ROOT) else path
    )
    name = path.name.casefold()
    score = 0
    if path.parent == nearby:
        score += 50
    if str(relative.parent).startswith("data"):
        score += 10
    if path.suffix.casefold() in {".tsv", ".tab", ".txt", ".csv"}:
        score += 5
    for keyword in keywords:
        if keyword in name:
            score += 20
    if "puma" in name and "panda" in keywords:
        score -= 25
    if "panda" in name and "puma" in keywords:
        score -= 25
    return score


def best_named_file(
    directory: Path,
    keywords: tuple[str, ...],
) -> Path | None:
    if not directory.is_dir():
        return None
    candidates = [
        path
        for path in directory.iterdir()
        if path.is_file()
        and path.suffix.casefold() in {".tsv", ".tab", ".txt", ".csv"}
        and any(keyword in path.name.casefold() for keyword in keywords)
    ]
    if not candidates:
        return None
    candidates.sort(
        key=lambda path: (
            -score_candidate_file(path, keywords, directory),
            len(path.name),
            path.name,
        )
    )
    return candidates[0]
