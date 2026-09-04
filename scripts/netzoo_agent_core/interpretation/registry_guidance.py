"""Registry-derived constraints and compositions for guidance responses."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import re

from ..contracts import TaskDecision


_PIPELINE_GUIDANCE_PATTERN = re.compile(
    r"\b(?:pipeline|workflow|end[-\s]?to[-\s]?end|multi[-\s]?stage|"
    r"sequence|steps?|stages?|first|then|finally)\b"
    r"|(?:完整流程|多階段|步驟|先|接著|然後|最後)",
    flags=re.IGNORECASE,
)
_TAG_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def should_expand_guidance_catalog(decision: TaskDecision, task: str) -> bool:
    """Expand the registry only for an explicitly requested pipeline map."""
    return (
        decision.capability_match_status == "unsupported"
        and not decision.matched_actions
        and bool(_PIPELINE_GUIDANCE_PATTERN.search(task))
    )


def _capability(item: dict) -> dict:
    return item.get("output_capability") or {}


def _records_by_action(workflows: Sequence[dict]) -> dict[str, dict]:
    return {item["action"]: item for item in workflows if item.get("action")}


def _normalized_tokens(value: str) -> set[str]:
    value = re.sub(r"(?i)(?:mi|micro)[-_ ]rna", "mirna", value)
    tokens = _TAG_TOKEN_PATTERN.findall(value.casefold())
    return {token[:-1] if token.endswith("s") and len(token) > 3 else token for token in tokens}


def _task_supported_selection_tags(
    task: str,
    workflows: Mapping[str, object],
) -> set[str]:
    task_tokens = _normalized_tokens(task)
    tags = {
        tag
        for spec in workflows.values()
        if getattr(spec, "output_capability", None) is not None
        for tag in spec.output_capability.selection_tags
    }
    supported = set()
    for tag in tags:
        tag_tokens = _normalized_tokens(tag.replace("_", " "))
        required = max(1, (len(tag_tokens) + 1) // 2)
        if len(tag_tokens & task_tokens) >= required:
            supported.add(tag)
    return supported


def decision_with_registry_signals(
    decision: TaskDecision,
    task: str,
    workflows: Mapping[str, object],
) -> TaskDecision:
    """Add only registry tags with direct lexical support in the user request."""
    outcome = decision.requested_outcome
    if outcome is None:
        return decision
    inferred = _task_supported_selection_tags(task, workflows)
    tags = list(dict.fromkeys([*outcome.selection_tags, *inferred]))
    if tags == outcome.selection_tags:
        return decision
    return decision.model_copy(
        deep=True,
        update={
            "requested_outcome": outcome.model_copy(update={"selection_tags": tags})
        },
    )


def _workflow_records(workflows: Mapping[str, object]) -> list[dict]:
    """Adapt typed workflow definitions to the generic path-selection records."""
    records = []
    for action, spec in workflows.items():
        capability = getattr(spec, "output_capability", None)
        workflow = getattr(spec, "workflow", None)
        if capability is None or not workflow:
            continue
        records.append(
            {
                "action": action,
                "workflow": workflow,
                "output_capability": {
                    "operation": capability.operation,
                    "artifact_type": capability.artifact_type,
                    "entity_types": sorted(capability.entity_types),
                    "granularities": sorted(capability.granularities),
                    "regulator_types": sorted(capability.regulator_types),
                    "target_types": sorted(capability.target_types),
                    "guidance_predecessors": list(capability.guidance_predecessors),
                    "input_artifacts": sorted(capability.input_artifacts),
                    "handoff_targets": list(capability.handoff_targets),
                    "selection_tags": sorted(capability.selection_tags),
                    "handoff_contract": capability.handoff_contract,
                },
            }
        )
    return records


def preferred_registry_composition_actions(
    task: str,
    decision: TaskDecision,
    workflows: Mapping[str, object],
) -> list[str]:
    """Return one registry-selected composition without naming workflow pairs.

    An already selected multi-stage composition is preserved. Otherwise, lexical
    signals are mapped to declared selection tags, then the registered artifact
    graph chooses the lowest-scoring legal path to the matched final action.
    """
    existing = list(dict.fromkeys(decision.recommended_actions))
    if len(existing) > 1:
        return existing
    if decision.requested_outcome is None:
        # Candidate composition may use lexical signals without fabricating a
        # requested artifact, role or granularity from the selected capability.
        preferred = _preferred_compositions(decision, _workflow_records(workflows),
                                            selection_tags=_task_supported_selection_tags(task, workflows))
        return list(preferred[0]["ordered_actions"]) if len(preferred) == 1 else existing
    enriched = decision_with_registry_signals(decision, task, workflows)
    preferred = build_registry_selection_constraints(
        enriched,
        _workflow_records(workflows),
    )["preferred_compositions"]
    if len(preferred) == 1:
        return list(preferred[0]["ordered_actions"])
    return existing


def related_registry_actions(
    seed_actions: Sequence[str],
    workflows: Mapping[str, object],
) -> list[str]:
    """Expand selected actions through declared guidance and artifact handoffs."""
    queue = list(seed_actions)
    related = []
    seen: set[str] = set()
    while queue:
        action = queue.pop(0)
        if action in seen:
            continue
        seen.add(action)
        spec = workflows.get(action)
        if spec is None:
            continue
        related.append(action)
        capability = spec.output_capability
        queue.extend(capability.guidance_predecessors)
        accepted_artifacts = set(capability.input_artifacts)
        queue.extend(
            producer_action
            for producer_action, producer in workflows.items()
            if action in producer.output_capability.handoff_targets
            and producer.output_capability.artifact_type in accepted_artifacts
        )
    return related


def handoff_input_fields(producer_contract: str, consumer_spec) -> list[str]:
    """Find consumer parameters explicitly named by the producer contract."""
    fields = [*consumer_spec.required_inputs, *consumer_spec.optional_inputs]
    return [
        field
        for field in fields
        if re.search(
            rf"(?<![A-Za-z0-9_]){re.escape(field)}(?![A-Za-z0-9_])",
            producer_contract,
        )
    ]


def _final_actions(
    decision: TaskDecision,
    records: dict[str, dict],
) -> list[str]:
    """Find final-result candidates without choosing a workflow by name."""
    for actions in (decision.matched_actions,):
        available = [action for action in actions if action in records]
        if available:
            return available
    for actions in (
        decision.recommended_actions,
        decision.hypothesis_actions,
        decision.alternative_actions,
    ):
        available = [action for action in actions if action in records]
        if available:
            # A registered composition stores predecessors first and its final
            # action last.
            return [available[-1]] if actions == decision.recommended_actions else available

    outcome = decision.requested_outcome
    if outcome is None:
        return []
    compatible = []
    for action, item in records.items():
        capability = _capability(item)
        if (
            capability.get("operation") == outcome.operation
            and capability.get("artifact_type") == outcome.artifact_type
            and outcome.granularity in (capability.get("granularities") or ())
        ):
            compatible.append(action)
    return compatible


def _reverse_handoff_graph(records: dict[str, dict]) -> dict[str, list[str]]:
    predecessors = {action: [] for action in records}
    for producer, item in records.items():
        for target in _capability(item).get("handoff_targets") or ():
            if target in records:
                predecessors[target].append(producer)
    for action, items in predecessors.items():
        predecessors[action] = list(dict.fromkeys(items))
    return predecessors


def _guidance_predecessors(action: str, records: dict[str, dict]) -> list[str]:
    return [
        predecessor
        for predecessor in _capability(records[action]).get("guidance_predecessors")
        or ()
        if predecessor in records
    ]


def _paths_to_final(
    final_action: str,
    records: dict[str, dict],
) -> list[list[str]]:
    predecessors = _reverse_handoff_graph(records)

    def walk(action: str, seen: frozenset[str]) -> list[list[str]]:
        if action in seen:
            return []
        guidance_prior = _guidance_predecessors(action, records)
        if guidance_prior:
            paths = [[]]
            for predecessor in guidance_prior:
                prior_paths = walk(predecessor, seen | {action})
                paths = [
                    [*prefix, *path]
                    for prefix in paths
                    for path in prior_paths
                ]
            return [
                [*path, action]
                for path in paths
                if path and path[-1] != action
            ]

        paths = [[action]]
        for predecessor in predecessors.get(action) or []:
            for path in walk(predecessor, seen | {action}):
                paths.append([*path, action])
        return paths

    paths = []
    for path in walk(final_action, frozenset()):
        if path not in paths:
            paths.append(path)
    return paths


def _path_score(
    path: list[str],
    records: dict[str, dict],
    requested_roles: set[str],
    requested_tags: set[str],
) -> tuple[int, int, int, int]:
    capabilities = [_capability(records[action]) for action in path]
    supported_roles = set().union(
        *(set(item.get("regulator_types") or ()) for item in capabilities)
    )
    supported_tags = set().union(
        *(set(item.get("selection_tags") or ()) for item in capabilities)
    )
    missing_tags = len(requested_tags - supported_tags)
    missing_roles = len(requested_roles - supported_roles)
    # Extra biological roles are penalized even when the user left the role
    # unspecified. This gives an under-specified request the least-assumptive
    # registered composition while still allowing an explicit miRNA signal.
    extra_roles = sum(
        len(set(item.get("regulator_types") or ()) - requested_roles)
        for item in capabilities
    )
    return missing_tags, missing_roles, extra_roles, len(path)


def _handoff_steps(path: list[str], records: dict[str, dict]) -> list[dict]:
    steps = []
    for producer, consumer in zip(path, path[1:]):
        producer_capability = _capability(records[producer])
        consumer_capability = _capability(records[consumer])
        producer_output = producer_capability.get("artifact_type")
        consumer_inputs = sorted(consumer_capability.get("input_artifacts") or ())
        direct_artifact_match = producer_output in consumer_inputs
        is_guidance_predecessor = (
            producer in (consumer_capability.get("guidance_predecessors") or ())
            and consumer not in (producer_capability.get("handoff_targets") or ())
        )
        steps.append(
            {
                "from_action": producer,
                "from_workflow": records[producer]["workflow"],
                "from_output": producer_output,
                "to_action": consumer,
                "to_workflow": records[consumer]["workflow"],
                "to_inputs": consumer_inputs,
                "handoff_mode": (
                    "independent_preparation"
                    if not direct_artifact_match
                    else "registered_transformation"
                ),
                "handoff_contract": (
                    consumer_capability.get("handoff_contract")
                    if is_guidance_predecessor
                    else producer_capability.get("handoff_contract")
                ) or "",
            }
        )
    return steps


def _preferred_compositions(
    decision: TaskDecision,
    workflows: Sequence[dict],
    *, selection_tags: set[str] | None = None,
) -> list[dict]:
    records = _records_by_action(workflows)
    finals = _final_actions(decision, records)
    if not finals:
        return []
    outcome = decision.requested_outcome
    requested_roles = (
        set(outcome.regulator_types) - {"unknown"} if outcome else set()
    )
    requested_tags = set(outcome.selection_tags) if outcome else set(selection_tags or ())
    candidates = []
    for final in finals:
        paths = _paths_to_final(final, records)
        if len(decision.recommended_actions) > 1 and decision.recommended_actions in paths:
            paths = [decision.recommended_actions]
        for path in paths:
            candidates.append(
                (
                    _path_score(path, records, requested_roles, requested_tags),
                    path,
                )
            )
    if not candidates:
        return []
    candidates.sort(key=lambda item: (item[0], item[1]))
    selected_score, selected_path = candidates[0]
    selected = []
    for action in selected_path:
        item = records[action]
        capability = _capability(item)
        selected.append(
            {
                "action": action,
                "workflow": item["workflow"],
                "input_artifacts": sorted(capability.get("input_artifacts") or ()),
                "output_artifact": capability.get("artifact_type"),
                "selection_tags": capability.get("selection_tags") or [],
                "handoff_contract": capability.get("handoff_contract") or "",
            }
        )
    return [
        {
            "ordered_actions": selected_path,
            "ordered_workflows": [item["workflow"] for item in selected],
            "final_action": selected_path[-1],
            "selection_basis": {
                "requested_regulator_types": sorted(requested_roles),
                "requested_selection_tags": sorted(requested_tags),
                "score": list(selected_score),
            },
            "stages": selected,
            "handoff_steps": _handoff_steps(selected_path, records),
            "non_selected_paths": [
                {
                    "ordered_actions": path,
                    "ordered_workflows": [records[action]["workflow"] for action in path],
                    "score": list(score),
                }
                for score, path in candidates[1:]
            ],
        }
    ]


def build_registry_selection_constraints(
    decision: TaskDecision,
    workflows: Sequence[dict],
) -> dict:
    """Expose registry-derived role constraints and the preferred graph path."""
    outcome = decision.requested_outcome
    requested_regulators = (
        set(outcome.regulator_types) - {"unknown"} if outcome else set()
    )
    requested_targets = set(outcome.target_types) - {"unknown"} if outcome else set()
    requested_tags = set(outcome.selection_tags) if outcome else set()
    preferred = _preferred_compositions(decision, workflows)
    preferred_actions = {
        action
        for composition in preferred
        for action in composition["ordered_actions"]
    }
    options = []
    for item in workflows:
        capability = _capability(item)
        regulators = set(capability.get("regulator_types") or ())
        targets = set(capability.get("target_types") or ())
        tags = set(capability.get("selection_tags") or ())
        options.append(
            {
                "action": item["action"],
                "workflow": item["workflow"],
                "regulator_types": sorted(regulators),
                "target_types": sorted(targets),
                "additional_regulator_types": sorted(regulators - requested_regulators),
                "additional_target_types": sorted(targets - requested_targets),
                "selection_tags": sorted(tags),
                "matched_selection_tags": sorted(tags & requested_tags),
                "handoff_targets": capability.get("handoff_targets") or [],
                "preferred_in_selected_composition": item["action"] in preferred_actions,
            }
        )
    return {
        "requested_regulator_types": sorted(requested_regulators),
        "requested_target_types": sorted(requested_targets),
        "requested_selection_tags": sorted(requested_tags),
        "role_selection_rule": (
            "Do not introduce biological roles absent from the validated request. "
            "When a role is unspecified, prefer the compatible option with the "
            "smallest additional-role set and mention alternatives only when the "
            "user asks or the uncertainty is material."
        ),
        "composition_selection_rule": (
            "Select the lowest-scoring registry handoff path that covers the "
            "validated roles and selection signals. For a resolved request, explain "
            "only the preferred path; do not present non-selected paths as equal "
            "options."
        ),
        "preferred_compositions": preferred,
        "workflow_role_options": options,
    }
