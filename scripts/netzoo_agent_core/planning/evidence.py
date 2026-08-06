"""Ordered workflow-input evidence construction."""

from __future__ import annotations

import re
from pathlib import Path

from .context import _PlanningContext
from ..bundles import MULTI_FILE_ACTIONS, discover_coherent_bundle
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
from ..validation import _resolve_user_path

__all__: list[str] = []


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
    for field_name in input_fields:
        parsed = _task_path(task, field_name)
        routed = getattr(decision, field_name, None)
        if parsed:
            explicit_input_values[field_name] = parsed
            setattr(decision, field_name, parsed)
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
        bundle = discover_coherent_bundle(action, nearby, explicit_input_values)
        if bundle is not None:
            for field_name, value in bundle.values.items():
                if field_name in explicit_input_values:
                    continue
                setattr(decision, field_name, value)
                autonomous_values[field_name] = value
                autonomous_reasons[field_name] = bundle.reason
                autonomous_sources[field_name] = "discovered"
                autonomous_bundle_ids[field_name] = bundle.bundle_id

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
        if field_name == "output_dir" and action == "run_condor":
            value = (
                "outputs/condor"
                if default_output_dir == "outputs/demo"
                else str(Path(default_output_dir) / "condor")
            )
            decision.output_dir = value
            evidence.append(
                InputEvidence(
                    field=field_name,
                    status="defaulted",
                    value=value,
                    reason="The Planner used the default CONDOR output directory.",
                )
            )
            continue

        keywords = _candidate_keywords(action, field_name)
        candidates = _find_candidate_files(keywords, nearby) if keywords else []
        if action in MULTI_FILE_ACTIONS:
            selected = None
            reason = (
                "No single complete validated dataset bundle contains every "
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
                )
            )

    return evidence
