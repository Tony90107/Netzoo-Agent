"""Neutral file naming and candidate scoring rules."""

from __future__ import annotations

from pathlib import Path

from ..settings import PROJECT_ROOT

__all__: list[str] = ["SHIPPED_DATA_DIRECTORIES", "is_shipped_data"]

#: The demonstration, test and fixture datasets the repository ships under `data/` (M2, 2026-10-14). AGENTS.md: a
#: real analysis never takes toy data because it is in the workspace; final acceptance a24b offered or filled them in
#: 18 of 24 runs that reached the input gate. `tests/test_input_files.py` keeps this equal to the tracked folders.
SHIPPED_DATA_DIRECTORIES = frozenset({
    "auto-check-invalid", "auto-check-valid", "blind-neutral", "blind-tests", "bonobo-toy", "cobra-toy",
    "condor-toy", "dragon-toy", "format-demo", "giraffe-toy", "lioness-toy", "manual-tests", "official-toy",
    "otter-toy", "role-mapping-fixtures", "sambar-official-toy", "sambar-toy", "teacher-demo",
})


def is_shipped_data(path: str | Path) -> bool:
    """Whether a path lies in one of the shipped demonstration or fixture datasets."""
    candidate = Path(path).expanduser()
    candidate = (candidate if candidate.is_absolute() else PROJECT_ROOT / candidate).resolve()
    try:
        parts = candidate.relative_to((PROJECT_ROOT / "data").resolve()).parts
    except ValueError:
        return False
    return bool(parts) and parts[0] in SHIPPED_DATA_DIRECTORIES


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
    if field_name == "mutation_file":
        return ("mutation", "mut", "maf")
    if field_name == "exon_size_file":
        return ("exon", "length", "esize")
    if field_name == "cancer_gene_file":
        return ("cancer", "gene", "cangenes")
    if field_name == "pathway_file":
        return ("pathway", "gmt", "signature")
    if action in {"run_dragon", "run_lioness_dragon"} and field_name == "omics_layer_1":
        return ("layer1", "omics1", "transcript", "expression")
    if action in {"run_dragon", "run_lioness_dragon"} and field_name == "omics_layer_2":
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
    if path.suffix.casefold() in {".tsv", ".tab", ".txt", ".csv", ".gmt"}:
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
        and path.suffix.casefold() in {".tsv", ".tab", ".txt", ".csv", ".gmt"}
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
