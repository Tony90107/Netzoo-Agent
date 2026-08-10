"""Pure rules used by pre-execution plan review."""

from __future__ import annotations

import re

from ..data.bundles import MULTI_FILE_ACTIONS
from ..contracts import (
    INPUT_ROLE_FIELDS,
    OUTPUT_ROLE_FIELDS,
    InputEvidence,
    TaskDecision,
    WorkflowPlan,
    _is_demo_request,
)
from ..interpretation import _mentions_unspecified_data_directory
from .recovery_registry import get_recovery_strategy

def _path_literal_in_task(value: str | None, user_task: str) -> bool:
    """Return whether a planned path is grounded in literal user-visible text."""
    if not value:
        return False
    normalized_value = str(value).strip().strip("'\"")
    if not normalized_value:
        return False
    return normalized_value in user_task


def _evidence_contract_failures(
    evidence: list[InputEvidence],
    user_task: str,
) -> list[str]:
    failures: list[str] = []
    selected_fields = set(
        re.findall(r"SELECTED_FIELD=([a-z_]+)", user_task, flags=re.IGNORECASE)
    )
    demo_allowed = _is_demo_request(
        user_task
    ) and not _mentions_unspecified_data_directory(user_task)
    for item in evidence:
        if item.status != "derived" and item.derived_from is not None:
            failures.append(
                f"{item.field} carries a derived source without derived status"
            )
        if item.status == "provided":
            if not _path_literal_in_task(item.value, user_task):
                failures.append(
                    f"{item.field} is marked provided but its value is not in the user request"
                )
        elif item.status == "selected":
            if item.field not in selected_fields or not _path_literal_in_task(
                item.value,
                user_task,
            ):
                failures.append(
                    f"{item.field} is marked selected without a matching selection marker"
                )
        elif item.status == "demo_bundle":
            if not item.value or not demo_allowed:
                failures.append(
                    f"{item.field} uses a demo bundle outside an unambiguous demo request"
                )
        elif item.status == "discovered":
            if not item.value or not item.reason:
                failures.append(
                    f"{item.field} is marked discovered without value and discovery reason"
                )
        elif item.status == "derived":
            if (
                not item.value
                or not item.reason
                or not isinstance(item.derived_from, str)
                or not item.derived_from.strip()
                or item.bundle_id is not None
                or item.candidates
            ):
                failures.append(
                    f"{item.field} has malformed derived-input provenance"
                )
        elif item.status == "defaulted":
            if item.field not in OUTPUT_ROLE_FIELDS or not item.value:
                failures.append(
                    f"{item.field} is marked defaulted but is not a reversible output field"
                )
        elif item.status == "missing" and item.value:
            failures.append(f"{item.field} is missing but still carries a value")
    return failures


def _derived_evidence_contract_failures(
    plan: WorkflowPlan,
    decision: TaskDecision,
) -> list[str]:
    derived = [item for item in plan.evidence if item.status == "derived"]
    strategy = get_recovery_strategy(plan.recovery_action)
    if strategy is not None:
        return strategy.validate_evidence(plan, decision)
    if derived:
        return ["derived input is not authorized by a registered recovery strategy"]
    return []


def _path_hygiene_failures(plan: WorkflowPlan, decision: TaskDecision) -> list[str]:
    failures: list[str] = []
    values_by_field: dict[str, str] = {}
    for field_name in INPUT_ROLE_FIELDS | OUTPUT_ROLE_FIELDS:
        value = getattr(decision, field_name, None)
        if value:
            values_by_field[field_name] = str(value)
    for item in plan.evidence:
        if item.value:
            values_by_field[item.field] = str(item.value)
    for field_name, value in values_by_field.items():
        if value.endswith((".", "。")):
            failures.append(f"{field_name} has trailing sentence punctuation: {value}")
    return failures


def _bundle_provenance_failures(
    plan: WorkflowPlan,
    decision: TaskDecision,
) -> list[str]:
    """Reject autonomous multi-file evidence that does not name one bundle."""
    if decision.action not in MULTI_FILE_ACTIONS:
        return []
    discovered = [
        item
        for item in plan.evidence
        if item.status == "discovered" and item.field in INPUT_ROLE_FIELDS
    ]
    if not discovered:
        return []
    if any(not item.bundle_id for item in discovered):
        return ["autonomously discovered inputs are missing a dataset bundle id"]
    bundle_ids = {item.bundle_id for item in discovered}
    if len(bundle_ids) != 1:
        return [
            "autonomously discovered inputs mix dataset bundles: "
            + ", ".join(sorted(bundle_ids))
        ]
    return []


def _expected_plan_steps(
    plan: WorkflowPlan,
    decision: TaskDecision,
    normal_steps: list[str],
) -> tuple[list[str], bool, str]:
    """Return the exact authorized step sequence for an initial or recovery plan."""
    recovery_metadata_present = (
        plan.recovery_action is not None
        or plan.recovery_error_code is not None
        or plan.recovery_step_index is not None
        or plan.recovery_attempt != 0
    )
    if not recovery_metadata_present:
        return normal_steps, True, "This is an initial plan with no recovery mutation."

    strategy = get_recovery_strategy(plan.recovery_action)
    if strategy is None:
        return (
            normal_steps,
            False,
            "Recovery metadata does not identify a registered recovery strategy.",
        )
    validation = strategy.validate(plan, decision, normal_steps)
    return validation.expected_steps, validation.ok, validation.detail
