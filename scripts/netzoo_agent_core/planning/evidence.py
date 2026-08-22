"""Ordered workflow-input evidence construction."""

from __future__ import annotations

import re
from pathlib import Path

from .context import _PlanningContext
from ..data.bundles import MULTI_FILE_ACTIONS, discover_bundle_candidates
from ..contracts import InputEvidence, OUTPUT_ROLE_FIELDS, PROJECT_ROOT, _is_demo_request
from ..interpretation import (
    _candidate_keywords,
    _choose_unambiguous_candidate,
    _mentions_unspecified_data_directory,
    _task_path,
    discover_demo_bundle,
    reusable_episode_inputs,
)
from ..routing import (
    _default_lioness_outputs,
    _default_network_output,
    _find_candidate_files,
)
from ..data.paths import _resolve_user_path

__all__: list[str] = []


def _cobra_unlabeled_input_paths(task: str) -> tuple[str | None, str | None]:
    """Bind COBRA's two ordered table paths in natural-language requests."""
    if "cobra" not in task.casefold():
        return None, None
    paths = re.findall(
        r"(?<![A-Za-z0-9_.-])([A-Za-z0-9_./-]+\.(?:tsv|tab|csv|txt))(?![A-Za-z0-9_.-])",
        task,
        flags=re.IGNORECASE,
    )
    return (paths[0], paths[1]) if len(paths) >= 2 else (None, None)


def _build_evidence_ledger(context: _PlanningContext) -> list[InputEvidence]:
    decision = context.decision
    task = context.task
    profile_model = context.profile
    episode_models = context.episodes
    action = context.action
    required = context.required
    input_fields = [
        field_name
        for field_name in required
        if field_name not in {"output_file", "lioness_output", "output_dir"}
    ]
    explicit_input_values: dict[str, str] = {}
    selected_fields = set(
        re.findall(r"SELECTED_FIELD=([a-z_]+)", task, flags=re.IGNORECASE)
    )
    carried_discovered_fields = set(
        re.findall(
            r"CARRIED_DISCOVERED_FIELD=([a-z_]+)",
            task,
            flags=re.IGNORECASE,
        )
    )
    cobra_expression, cobra_design = _cobra_unlabeled_input_paths(task)
    for field_name in input_fields:
        parsed = _task_path(task, field_name) or (
            cobra_expression
            if action == "run_cobra" and field_name == "expression_file"
            else cobra_design
            if action == "run_cobra" and field_name == "design_file"
            else None
        )
        routed = getattr(decision, field_name, None)
        if parsed:
            setattr(decision, field_name, parsed)
            if field_name not in carried_discovered_fields:
                explicit_input_values[field_name] = parsed
        elif routed and str(routed) in task:
            explicit_input_values[field_name] = str(routed)
        elif routed:
            # Router-produced paths are untrusted unless the literal path appears
            # in the user's request. Otherwise the Planner would present a guessed
            # workspace file as "provided".
            setattr(decision, field_name, None)

    for field_name in required:
        if field_name not in OUTPUT_ROLE_FIELDS:
            continue
        routed = getattr(decision, field_name, None)
        parsed = _task_path(task, field_name)
        if parsed:
            setattr(decision, field_name, parsed)
        elif routed and str(routed) not in task:
            setattr(decision, field_name, None)

    autonomous_values: dict[str, str] = {}
    autonomous_reasons: dict[str, str] = {}
    autonomous_sources: dict[str, str] = {}
    autonomous_bundle_ids: dict[str, str] = {}
    bundle_choices_by_field: dict[str, list[str]] = {}
    bundle_choice_ids: list[str] = []
    partial_bundle_selected = False
    for field_name in carried_discovered_fields:
        value = _task_path(task, field_name)
        if not value:
            continue
        setattr(decision, field_name, value)
        autonomous_values[field_name] = value
        autonomous_reasons[field_name] = (
            "Carried forward from the coherent bundle shown in the prior clarification."
        )
        autonomous_sources[field_name] = "discovered"
        autonomous_bundle_ids[field_name] = (
            f"directory:{_resolve_user_path(value).parent.resolve()}"
        )
    if profile_model.preferences.get("reuse_last_inputs") is True:
        reused = reusable_episode_inputs(action, episode_models)
        if reused:
            reused_values, reason = reused
            for field_name, value in reused_values.items():
                if field_name not in explicit_input_values:
                    setattr(decision, field_name, value)
                    autonomous_values[field_name] = value
                    autonomous_reasons[field_name] = reason
                    autonomous_sources[field_name] = "discovered"
                    autonomous_bundle_ids[field_name] = f"reused:{reason}"
    if (
        _is_demo_request(task)
        and not _mentions_unspecified_data_directory(task)
        and profile_model.preferences.get("allow_demo_autofill", True) is not False
        and not explicit_input_values
        and not autonomous_values
    ):
        bundle = discover_demo_bundle(action)
        if bundle:
            bundle_values, reason = bundle
            for field_name, value in bundle_values.items():
                # A validated coherent bundle outranks ungrounded paths proposed by
                # the language-model router. Literal user paths were handled above.
                setattr(decision, field_name, value)
                autonomous_values[field_name] = value
                autonomous_reasons[field_name] = reason
                autonomous_sources[field_name] = "demo_bundle"
    # Outputs are safe and reversible defaults; input datasets require evidence.
    expression_hint = decision.expression_file or _task_path(task, "expression_file")
    if expression_hint:
        nearby = _resolve_user_path(expression_hint).parent
    else:
        nearby = PROJECT_ROOT / "data"

    if action in MULTI_FILE_ACTIONS and not autonomous_values:
        candidates = discover_bundle_candidates(action, nearby, explicit_input_values)
        bundles = [item for item in candidates if not item.missing_fields]
        bundle = bundles[0] if len(bundles) == 1 else None
        if bundle is not None:
            for field_name, value in bundle.values.items():
                if field_name in explicit_input_values:
                    continue
                setattr(decision, field_name, value)
                autonomous_values[field_name] = value
                autonomous_reasons[field_name] = bundle.reason
                autonomous_sources[field_name] = "discovered"
                autonomous_bundle_ids[field_name] = bundle.bundle_id
        elif len(bundles) > 1:
            bundle_choice_ids = [item.bundle_id for item in bundles]
            bundle_choices_by_field = {
                field_name: [
                    item.values[field_name]
                    for item in bundles
                    if item.values.get(field_name)
                ]
                for field_name in input_fields
            }
        elif candidates:
            most_complete = max(len(item.values) for item in candidates)
            best_partials = [
                item for item in candidates if len(item.values) == most_complete
            ]
            if len(best_partials) == 1:
                partial = best_partials[0]
                partial_bundle_selected = True
                for field_name, value in partial.values.items():
                    if field_name in explicit_input_values:
                        continue
                    setattr(decision, field_name, value)
                    autonomous_values[field_name] = value
                    autonomous_reasons[field_name] = partial.reason
                    autonomous_sources[field_name] = "discovered"
                    autonomous_bundle_ids[field_name] = partial.bundle_id

    default_output_dir = str(
        profile_model.preferences.get("default_output_dir", "outputs/demo")
    )
    evidence: list[InputEvidence] = []
    for field_name in required:
        value = getattr(decision, field_name) or _task_path(task, field_name)
        if value:
            setattr(decision, field_name, value)
            status = (
                autonomous_sources[field_name]
                if field_name in autonomous_values
                else "selected"
                if field_name in selected_fields
                else "provided"
            )
            evidence.append(
                InputEvidence(
                    field=field_name,
                    status=status,
                    value=value,
                    reason=(
                        autonomous_reasons[field_name]
                        if field_name in autonomous_values
                        else "Explicitly provided by the user or the intent parser."
                    ),
                    bundle_id=autonomous_bundle_ids.get(field_name),
                )
            )
            continue

        if field_name in {"output_file", "lioness_output"}:
            seed = decision.expression_file or "expression.tsv"
            if "lioness" in action:
                aggregate, sample_specific = _default_lioness_outputs(
                    (
                        "puma"
                        if "puma" in action
                        else "panda"
                        if "panda" in action
                        else "coexpression"
                    ),
                    seed,
                    default_output_dir,
                )
                value = aggregate if field_name == "output_file" else sample_specific
            else:
                value = _default_network_output(
                    "puma" if "puma" in action else "panda",
                    seed,
                    default_output_dir,
                )
            setattr(decision, field_name, value)
            evidence.append(
                InputEvidence(
                    field=field_name,
                    status="defaulted",
                    value=value,
                    reason="The output location is reversible and does not overwrite an input, so the Planner used the project default.",
                )
            )
            continue
        if field_name == "output_dir" and action in {"run_condor", "run_cobra"}:
            value = default_output_dir
            decision.output_dir = value
            evidence.append(
                InputEvidence(
                    field=field_name,
                    status="defaulted",
                    value=value,
                    reason=f"The Planner used the default {action.removeprefix('run_').upper()} output directory.",
                )
            )
            continue

        keywords = _candidate_keywords(action, field_name)
        candidates = _find_candidate_files(keywords, nearby) if keywords else []
        if partial_bundle_selected:
            candidates = []
        if bundle_choices_by_field.get(field_name):
            candidates = bundle_choices_by_field[field_name]
        if action in MULTI_FILE_ACTIONS:
            selected = None
            reason = (
                "Multiple complete validated input bundles are available; "
                "choose one before execution."
                if bundle_choices_by_field
                else "No single complete validated dataset bundle contains every "
                "remaining required input."
            )
        else:
            selected, reason = _choose_unambiguous_candidate(
                candidates,
                keywords,
                nearby,
            )
        if selected:
            setattr(decision, field_name, selected)
            evidence.append(
                InputEvidence(
                    field=field_name,
                    status="discovered",
                    value=selected,
                    reason=reason,
                    candidates=candidates[:5],
                )
            )
        else:
            evidence.append(
                InputEvidence(
                    field=field_name,
                    status="missing",
                    reason=reason,
                    candidates=candidates[:5],
                    candidate_bundle_ids=(
                        bundle_choice_ids[:5]
                        if bundle_choices_by_field.get(field_name)
                        else []
                    ),
                )
            )

    return evidence
