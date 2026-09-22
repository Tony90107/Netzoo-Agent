"""Validation of reusable inputs from completed workflow episodes."""

from __future__ import annotations

from workflow_registry import (
    REQUIRED_INPUT_GROUPS,
    REQUIRED_INPUTS,
    workflow_name as _workflow_name,
)

from ..contracts import Episode
from ..data.inspection import (
    expression_sample_count as _expression_sample_count,
    inspect_condor_inputs_impl as _inspect_condor_inputs_impl,
)
from ..data.panda_preflight import inspect_panda_inputs_with_provenance
from ..data.paths import _resolve_user_path
from ..data.sambar import inspect_sambar_inputs_impl
from .giraffe_demo import validate_giraffe_episode_inputs

__all__: list[str] = []


def reusable_episode_inputs(
    action: str,
    episodes: list[Episode],
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
        missing_required = any(
            field_name not in episode.inputs for field_name in required_fields
        )
        missing_group = any(
            not any(field_name in episode.inputs for field_name in group)
            for group in REQUIRED_INPUT_GROUPS.get(action, ())
        )
        if missing_required or missing_group:
            continue
        values = {
            field_name: episode.inputs[field_name] for field_name in required_fields
        }
        if any(not _resolve_user_path(path).exists() for path in values.values()):
            continue
        if action == "run_condor":
            _, ok = _inspect_condor_inputs_impl(values["network_file"])
        elif action == "run_sambar":
            _, ok = inspect_sambar_inputs_impl(
                values["mutation_file"],
                values["exon_size_file"],
                values["cancer_gene_file"],
                values["pathway_file"],
            )
        elif action == "run_giraffe":
            ok = validate_giraffe_episode_inputs(values)
        elif action in {
            "run_panda",
            "run_puma",
            "run_lioness_panda",
            "run_lioness_puma",
        }:
            _, ok, _, _ = inspect_panda_inputs_with_provenance(
                action,
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
                "Reused validated inputs from successful episode "
                f"{episode.episode_id[:8]} under the confirmed "
                "reuse_last_inputs preference.",
            )
    return None
