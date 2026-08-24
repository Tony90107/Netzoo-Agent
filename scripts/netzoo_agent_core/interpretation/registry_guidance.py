"""Registry-derived constraints and compositions for guidance responses."""

from __future__ import annotations

from collections.abc import Sequence

from ..contracts import TaskDecision


def _capability(item: dict) -> dict:
    return item.get("output_capability") or {}


def _records_by_action(workflows: Sequence[dict]) -> dict[str, dict]:
    return {item["action"]: item for item in workflows if item.get("action")}


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
    return predecessors


def _paths_to_final(
    final_action: str,
    records: dict[str, dict],
) -> list[list[str]]:
    predecessors = _reverse_handoff_graph(records)

    def walk(action: str, seen: frozenset[str]) -> list[list[str]]:
        if action in seen:
            return []
        prior = predecessors.get(action) or []
        if not prior:
            return [[action]]
        paths: list[list[str]] = []
        for predecessor in prior:
            for path in walk(predecessor, seen | {action}):
                paths.append([*path, action])
        return paths

    return walk(final_action, frozenset())


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
                "handoff_contract": producer_capability.get("handoff_contract") or "",
            }
        )
    return steps


def _preferred_compositions(
    decision: TaskDecision,
    workflows: Sequence[dict],
) -> list[dict]:
    records = _records_by_action(workflows)
    finals = _final_actions(decision, records)
    if not finals:
        return []
    outcome = decision.requested_outcome
    requested_roles = (
        set(outcome.regulator_types) - {"unknown"} if outcome else set()
    )
    requested_tags = set(outcome.selection_tags) if outcome else set()
    candidates = []
    for final in finals:
        for path in _paths_to_final(final, records):
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
