"""Candidate selection, coherent demo bundles, and reusable episode inputs."""

from __future__ import annotations

import json
from pathlib import Path

from workflow_registry import REQUIRED_INPUTS, workflow_name as _workflow_name

from ..contracts import Episode, PROJECT_ROOT, _display_path
from ..data.discovery import (
    best_named_file as _best_named_file,
    candidate_keywords as _candidate_keywords,  # noqa: F401 -- compatibility export
    score_candidate_file as _score_candidate_file,
)
from ..data.inspection import (
    expression_sample_count as _expression_sample_count,
    inspect_condor_inputs_impl as _inspect_condor_inputs_impl,
)
from ..data.paths import _resolve_user_path
from ..data.tables import _inspect_panda_inputs_impl

__all__: list[str] = []


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
        _, ok, _ = _inspect_panda_inputs_impl(
            str(expression), str(motif), str(ppi), str(mirna or "")
        )
        sample_count, _ = _expression_sample_count(str(expression))
        if not ok or ("lioness" in action and sample_count < 3):
            continue
        bundle = {
            "expression_file": _display_path(expression),
            "motif_file": _display_path(motif),
            "ppi_file": _display_path(ppi),
        }
        if mirna:
            bundle["mirna_file"] = _display_path(mirna)
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


def reusable_episode_inputs(
    action: str, episodes: list[Episode]
) -> tuple[dict[str, str], str] | None:
    expected_workflow = _workflow_name(action)
    for episode in episodes:
        if episode.status != "completed" or episode.workflow != expected_workflow:
            continue
        required_fields = [
            field_name
            for field_name in REQUIRED_INPUTS.get(action, ())
            if field_name not in {"output_file", "lioness_output", "output_dir"}
        ]
        if any(field_name not in episode.inputs for field_name in required_fields):
            continue
        values = {
            field_name: episode.inputs[field_name] for field_name in required_fields
        }
        if any(not _resolve_user_path(path).exists() for path in values.values()):
            continue
        if action == "run_condor":
            _, ok = _inspect_condor_inputs_impl(values["network_file"])
        elif action in {
            "run_panda",
            "run_puma",
            "run_lioness_panda",
            "run_lioness_puma",
        }:
            _, ok, _ = _inspect_panda_inputs_impl(
                values["expression_file"],
                values["motif_file"],
                values["ppi_file"],
                values.get("mirna_file", ""),
            )
            if ok and "lioness" in action:
                sample_count, _ = _expression_sample_count(values["expression_file"])
                ok = sample_count >= 3
        else:
            ok = True
        if ok:
            return (
                values,
                f"Reused validated inputs from successful episode {episode.episode_id[:8]} under the confirmed reuse_last_inputs preference.",
            )
    return None
