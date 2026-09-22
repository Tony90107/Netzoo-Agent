"""Candidate selection, coherent demo bundles, and reusable episode inputs."""

from __future__ import annotations
import json
import re
from pathlib import Path

from ..contracts import PROJECT_ROOT, _display_path
from ..data.discovery import (
    best_named_file as _best_named_file,
    candidate_keywords as _candidate_keywords,  # noqa: F401 -- package facade
    score_candidate_file as _score_candidate_file,
)
from ..data.inspection import (
    expression_sample_count as _expression_sample_count,
    inspect_condor_inputs_impl as _inspect_condor_inputs_impl,
)
from ..data.cobra import inspect_cobra_inputs_impl
from ..data.sambar import inspect_sambar_inputs_impl
from ..data.dragon import inspect_dragon_inputs_impl
from ..data.otter import inspect_otter_inputs_impl
from . import bonobo_demo, giraffe_demo
from .episode_reuse import reusable_episode_inputs as reusable_episode_inputs
from ..data.paths import _resolve_user_path
from ..data.panda_preflight import inspect_panda_inputs_with_provenance
__all__: list[str] = []

_UNLABELED_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])([A-Za-z0-9_./~-]+\.(?:tsv|tab|txt|csv|gmt|npy))"
    r"[.。]?(?![A-Za-z0-9_.-])",
    flags=re.IGNORECASE,
)


def _unlabeled_input_bindings(
    task: str,
    fields: tuple[str, ...] | list[str],
) -> dict[str, str]:
    """Infer roles from stable filename hints; content validation remains authoritative."""
    available = set(fields)
    role_hints = {
        "expression_file": ("expression", "expr"),
        "design_file": ("design", "covariate", "metadata"),
        "motif_file": ("motif", "prior"),
        "ppi_file": ("ppi", "protein", "interaction"),
        "mirna_file": ("mirna", "microrna"),
        "coexpression_file": ("coexpression", "co-expression"),
        "network_file": ("network", "bipartite"),
        "mutation_file": ("mutation", "mut", "maf"),
        "exon_size_file": ("exon", "length", "esize"),
        "cancer_gene_file": ("cancer", "cangenes"),
        "pathway_file": ("pathway", "gmt", "signature"),
    }
    bindings: dict[str, str] = {}
    for raw_path in _UNLABELED_PATH_RE.findall(task):
        path = raw_path.strip().rstrip(".。")
        name = path.rsplit("/", 1)[-1].casefold()
        matches = [
            field_name
            for field_name in available
            if field_name not in bindings
            and any(hint in name for hint in role_hints.get(field_name, ()))
        ]
        if len(matches) == 1:
            bindings[matches[0]] = path
    return bindings


def _choose_unambiguous_candidate(
    candidates: list[str], keywords: tuple[str, ...], nearby: Path
) -> tuple[str | None, str]:
    """Choose autonomously only when the best workspace candidate is defensible."""
    if not candidates:
        return None, "No matching file was found in the workspace."
    if len(candidates) == 1:
        return candidates[0], "The workspace contains exactly one matching candidate."

    scored = []
    for candidate in candidates:
        path = _resolve_user_path(candidate)
        scored.append((_score_candidate_file(path, keywords, nearby), candidate))
    scored.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
    best_score, best = scored[0]
    second_score = scored[1][0]
    if best_score >= second_score + 15:
        return (
            best,
            f"The best candidate score ({best_score}) clearly exceeds the runner-up ({second_score}).",
        )
    return (
        None,
        f"The top candidate scores are too close ({best_score} vs {second_score}) for safe automatic selection.",
    )


def discover_demo_bundle(action: str) -> tuple[dict[str, str], str] | None:
    """Find a coherent toy dataset as a bundle, then validate cross-file compatibility."""
    data_root = PROJECT_ROOT / "data"
    if action == "run_dragon":
        layer1 = data_root / "dragon-toy" / "layer1.tsv"
        layer2 = data_root / "dragon-toy" / "layer2.tsv"
        _, ok = inspect_dragon_inputs_impl(str(layer1), str(layer2))
        if not ok:
            return None
        return (
            {"omics_layer_1": _display_path(layer1), "omics_layer_2": _display_path(layer2)},
            "Demo intent: selected the DRAGON two-layer toy bundle with exact sample-ID alignment.",
        )
    if action == "run_cobra":
        expression = data_root / "cobra-toy" / "expression.tsv"
        design = data_root / "cobra-toy" / "design.tsv"
        _, ok = inspect_cobra_inputs_impl(str(expression), str(design))
        if not ok:
            return None
        return (
            {"expression_file": _display_path(expression), "design_file": _display_path(design)},
            "Demo intent: selected the COBRA toy expression/design bundle with aligned sample IDs.",
        )
    if action == "run_otter":
        expression = data_root / "otter-toy" / "expression.tsv"
        motif = data_root / "otter-toy" / "motif.tsv"
        ppi = data_root / "otter-toy" / "ppi.tsv"
        _, ok = inspect_otter_inputs_impl(str(expression), "", str(motif), str(ppi))
        if not ok:
            return None
        return (
            {
                "expression_file": _display_path(expression),
                "motif_file": _display_path(motif),
                "ppi_file": _display_path(ppi),
            },
            "Demo intent: selected the OTTER toy expression, TF-gene seed, and TF-TF PPI bundle after exact W/P/C validation.",
        )
    if action == "run_giraffe":
        return giraffe_demo.discover_giraffe_demo_bundle(data_root)
    if action == "run_bonobo":
        return bonobo_demo.discover_bonobo_demo_bundle(data_root)
    if action == "run_condor":
        candidates: list[tuple[int, Path]] = []
        for path in data_root.rglob("*"):
            if not path.is_file() or path.suffix.casefold() not in {
                ".tsv",
                ".txt",
                ".csv",
            }:
                continue
            name = path.name.casefold()
            if "condor" not in name and "bipartite" not in name:
                continue
            _, ok = _inspect_condor_inputs_impl(str(path))
            if ok:
                score = 100 if "condor-toy" in str(path.parent).casefold() else 20
                candidates.append((score, path))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (-item[0], str(item[1])))
        best_score, best = candidates[0]
        if len(candidates) > 1 and best_score < candidates[1][0] + 15:
            return None
        return (
            {"network_file": _display_path(best)},
            "Demo intent: selected a complete CONDOR toy bundle that passed format validation.",
        )

    if action == "run_sambar":
        directory = data_root / "sambar-toy"
        bundle = {
            "mutation_file": _display_path(directory / "mutation.csv"),
            "exon_size_file": _display_path(directory / "exon_size.csv"),
            "cancer_gene_file": _display_path(directory / "cancer_genes.txt"),
            "pathway_file": _display_path(directory / "pathways.gmt"),
        }
        _, ok = inspect_sambar_inputs_impl(*bundle.values())
        return (bundle, "Demo intent: selected the complete SAMBAR toy mutation/pathway bundle.") if ok else None

    if action == "run_lioness_coexpression":
        candidates: list[tuple[int, Path]] = []
        for expression in data_root.rglob("*"):
            if (
                not expression.is_file()
                or "expression" not in expression.name.casefold()
            ):
                continue
            sample_count, error = _expression_sample_count(str(expression))
            if error or sample_count < 3:
                continue
            location = str(expression.parent).casefold()
            score = 0
            if "lioness" in location:
                score += 100
            if "toy" in location:
                score += 20
            if "manual" in location:
                score -= 30
            candidates.append((score, expression))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (-item[0], str(item[1])))
        best_score, best = candidates[0]
        if len(candidates) > 1 and best_score < candidates[1][0] + 15:
            return None
        return (
            {"expression_file": _display_path(best)},
            "Demo intent: selected a LIONESS expression dataset with at least three samples.",
        )

    if action not in {
        "run_panda",
        "run_puma",
        "run_lioness_panda",
        "run_lioness_puma",
    }:
        return None
    mode = "puma" if "puma" in action else "panda"
    candidates: list[tuple[int, dict[str, str]]] = []
    for expression in data_root.rglob("*"):
        if not expression.is_file() or "expression" not in expression.name.casefold():
            continue
        directory = expression.parent
        motif = _best_named_file(directory, (mode, "motif", "prior"))
        ppi = _best_named_file(directory, ("ppi",))
        mirna = (
            _best_named_file(directory, ("mirna", "mir")) if mode == "puma" else None
        )
        if not motif or not ppi or (mode == "puma" and not mirna):
            continue
        bundle = {
            "expression_file": _display_path(expression),
            "motif_file": _display_path(motif),
            "ppi_file": _display_path(ppi),
        }
        if mirna:
            bundle["mirna_file"] = _display_path(mirna)
        _, ok, _, _ = inspect_panda_inputs_with_provenance(
            action, str(expression), str(motif), str(ppi), str(mirna or "")
        )
        sample_count, _ = _expression_sample_count(str(expression))
        if not ok or ("lioness" in action and sample_count < 3):
            continue
        location = str(directory).casefold()
        score = 0
        if "lioness" in action and "lioness" in location:
            score += 100
        if action in {"run_panda", "run_puma"} and "official-toy" in location:
            score += 100
        if mode in location or mode in motif.name.casefold():
            score += 30
        if "toy" in location:
            score += 20
        if "manual" in location:
            score -= 30
        candidates.append((score, bundle))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item[0], json.dumps(item[1], sort_keys=True)))
    best_score, best_bundle = candidates[0]
    if len(candidates) > 1 and best_score < candidates[1][0] + 15:
        return None
    return (
        best_bundle,
        (
            "Demo intent: files are complete in one dataset directory and expression/prior/PPI"
            + ("/miRNA" if mode == "puma" else "")
            + " identifier validation passed."
        ),
    )
