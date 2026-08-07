"""Code-enforced review of execution-ready workflow plans."""

from __future__ import annotations

import re

from workflow_registry import (
    CODE_VALIDATION_STEPS,
    LOCAL_EXECUTION_ACTIONS,
    REQUIRED_INPUTS,
    RUN_ACTIONS,
    workflow_name as _workflow_name,
)

from ..contracts import (
    INPUT_ROLE_FIELDS,
    OUTPUT_ROLE_FIELDS,
    PlanEvaluationResult,
    PlanRubricItem,
    ProjectPolicySnapshot,
    TaskDecision,
    WorkflowPlan,
)
from ..data.paths import condor_artifact_paths, resolved_output_collisions
from ..policy import ProjectPolicyLoader
from ..routing import validate_task_text
from ..data.paths import _resolve_user_path
from .plan_rules import (
    _bundle_provenance_failures,
    _derived_evidence_contract_failures,
    _evidence_contract_failures,
    _expected_plan_steps,
    _path_hygiene_failures,
)

def evaluate_workflow_plan(
    plan: WorkflowPlan,
    user_task: str,
    project_policy: ProjectPolicySnapshot | dict | None = None,
) -> PlanEvaluationResult:
    """Evaluate a structured plan before Executor receives any tool authority."""
    if plan.status != "ready":
        return PlanEvaluationResult(
            status="deferred",
            score=0,
            summary=(
                "Plan evaluation is deferred because the plan is not execution-ready."
            ),
            rubric=[
                PlanRubricItem(
                    criterion="execution_readiness",
                    required=True,
                    result="not_applicable",
                    detail=f"Plan status is {plan.status}; no execution is permitted.",
                )
            ],
        )

    rubric: list[PlanRubricItem] = []
    try:
        decision = TaskDecision.model_validate(plan.decision)
    except Exception as error:
        return PlanEvaluationResult(
            status="rejected",
            score=0,
            summary="The plan decision does not satisfy the TaskDecision schema.",
            rubric=[
                PlanRubricItem(
                    criterion="decision_schema",
                    result="fail",
                    detail=f"Schema validation failed: {type(error).__name__}.",
                )
            ],
        )

    action = decision.action
    recognized_action = action in REQUIRED_INPUTS and action != "no_tool"
    action_rejection = (
        validate_task_text(user_task, action) if recognized_action else None
    )
    continuation_authorized = bool(
        re.search(
            rf"PREVIOUS_ACTION={re.escape(action)}\b",
            user_task,
            flags=re.IGNORECASE,
        )
    )
    preference_authorized = "confirmed preferred workflow" in decision.reason.casefold()
    capability_ok = (
        recognized_action
        and (not action_rejection or continuation_authorized or preference_authorized)
        and plan.workflow == _workflow_name(action)
        and decision.intent_type != "answer_question"
    )
    rubric.append(
        PlanRubricItem(
            criterion="intent_and_capability_alignment",
            result="pass" if capability_ok else "fail",
            detail=(
                f"Action {action} matches the authorized deliverable and workflow {plan.workflow}."
                if capability_ok
                else action_rejection
                or "The action, workflow, or user intent is not execution-authorized."
            ),
        )
    )

    local_data_action = action in LOCAL_EXECUTION_ACTIONS
    if local_data_action:
        evidence_by_field = {item.field: item for item in plan.evidence}
        missing_evidence = []
        for field_name in REQUIRED_INPUTS[action]:
            value = getattr(decision, field_name, None)
            item = evidence_by_field.get(field_name)
            if (
                not value
                or item is None
                or item.status == "missing"
                or item.value != value
            ):
                missing_evidence.append(field_name)
        evidence_ok = not missing_evidence
        rubric.append(
            PlanRubricItem(
                criterion="required_input_evidence",
                result="pass" if evidence_ok else "fail",
                detail=(
                    "Every required input/output has a non-missing evidence entry."
                    if evidence_ok
                    else "Missing or inconsistent evidence: "
                    + ", ".join(missing_evidence)
                ),
            )
        )
    else:
        rubric.append(
            PlanRubricItem(
                criterion="required_input_evidence",
                required=False,
                result="not_applicable",
                detail="This read-only retrieval action does not use local dataset evidence.",
            )
        )

    provenance_failures = []
    if local_data_action:
        provenance_failures.extend(
            _evidence_contract_failures(plan.evidence, user_task)
        )
        provenance_failures.extend(
            _derived_evidence_contract_failures(plan, decision)
        )
    rubric.append(
        PlanRubricItem(
            criterion="evidence_provenance_contract",
            result="pass" if not provenance_failures else "fail",
            detail=(
                "Every evidence status is grounded by its declared source contract."
                if not provenance_failures
                else "; ".join(provenance_failures)
            ),
        )
    )

    bundle_failures = (
        _bundle_provenance_failures(plan, decision) if local_data_action else []
    )
    rubric.append(
        PlanRubricItem(
            criterion="dataset_bundle_provenance",
            result="pass" if not bundle_failures else "fail",
            detail=(
                "Autonomously discovered multi-file inputs share one dataset bundle."
                if not bundle_failures
                else "; ".join(bundle_failures)
            ),
        )
    )

    path_failures = _path_hygiene_failures(plan, decision) if local_data_action else []
    rubric.append(
        PlanRubricItem(
            criterion="path_hygiene",
            result="pass" if not path_failures else "fail",
            detail=(
                "Planned paths are free of sentence punctuation artifacts."
                if not path_failures
                else "; ".join(path_failures)
            ),
        )
    )

    allowed_step_actions = set(REQUIRED_INPUTS)
    unapproved_steps = [
        step.action for step in plan.steps if step.action not in allowed_step_actions
    ]
    rubric.append(
        PlanRubricItem(
            criterion="step_allowlist",
            result="pass" if not unapproved_steps else "fail",
            detail=(
                "Every planned step is in the code-enforced action allowlist."
                if not unapproved_steps
                else "Unapproved steps: " + ", ".join(unapproved_steps)
            ),
        )
    )

    policy_model = (
        ProjectPolicySnapshot.model_validate(project_policy)
        if project_policy is not None
        else None
    )
    workflow_spec = (
        policy_model.workflows.get(action)
        if policy_model is not None and action in policy_model.workflows
        else None
    )
    if workflow_spec is not None:
        normal_steps = [
            *workflow_spec.validation_steps,
            workflow_spec.execution_step,
        ]
    elif action in RUN_ACTIONS:
        normal_steps = [*CODE_VALIDATION_STEPS[action], action]
    elif recognized_action:
        normal_steps = [action]
    else:
        normal_steps = []
    expected_steps, recovery_ok, recovery_detail = _expected_plan_steps(
        plan,
        decision,
        normal_steps,
    )
    rubric.append(
        PlanRubricItem(
            criterion="recovery_authorization",
            result="pass" if recovery_ok else "fail",
            detail=recovery_detail,
        )
    )
    actual_steps = [step.action for step in plan.steps]
    sequence_ok = bool(actual_steps) and actual_steps == expected_steps
    rubric.append(
        PlanRubricItem(
            criterion="validation_and_execution_order",
            result="pass" if sequence_ok else "fail",
            detail=(
                "Step order matches the validated workflow specification: "
                + " -> ".join(actual_steps)
                if sequence_ok
                else (
                    "Expected "
                    + (" -> ".join(expected_steps) or "no executable steps")
                    + "; received "
                    + (" -> ".join(actual_steps) or "no steps")
                    + "."
                )
            ),
        )
    )

    inputs = [
        getattr(decision, field_name, None)
        for field_name in INPUT_ROLE_FIELDS
        if getattr(decision, field_name, None)
    ]
    outputs = [
        getattr(decision, field_name, None)
        for field_name in OUTPUT_ROLE_FIELDS
        if getattr(decision, field_name, None)
    ]
    collisions = []
    resolved_inputs = {_resolve_user_path(value) for value in inputs}
    for value in outputs:
        if _resolve_user_path(value) in resolved_inputs:
            collisions.append(value)
    output_safe = not collisions
    rubric.append(
        PlanRubricItem(
            criterion="output_non_overwrite",
            result="pass" if output_safe else "fail",
            detail=(
                "No planned output path overwrites a declared input path."
                if output_safe
                else "Output/input path collisions: " + ", ".join(collisions)
            ),
        )
    )

    output_role_collisions = resolved_output_collisions(decision)
    rubric.append(
        PlanRubricItem(
            criterion="output_role_uniqueness",
            result="pass" if not output_role_collisions else "fail",
            detail=(
                "Every populated output role resolves to a distinct path."
                if not output_role_collisions
                else "Output role collisions: " + "; ".join(output_role_collisions)
            ),
        )
    )

    condor_path_error = None
    if action == "run_condor" and decision.output_dir:
        try:
            condor_artifact_paths(decision.output_dir, decision.prefix or "condor")
        except ValueError as error:
            condor_path_error = str(error)
    rubric.append(
        PlanRubricItem(
            criterion="condor_derived_output_safety",
            required=action == "run_condor",
            result=(
                "not_applicable"
                if action != "run_condor"
                else "pass"
                if condor_path_error is None
                else "fail"
            ),
            detail=(
                "This workflow does not derive CONDOR output paths."
                if action != "run_condor"
                else "All CONDOR artifacts stay beneath output_dir."
                if condor_path_error is None
                else condor_path_error
            ),
        )
    )

    state_ok = (
        decision.should_execute
        and not decision.missing_inputs
        and not plan.missing_inputs
        and bool(plan.steps)
    )
    rubric.append(
        PlanRubricItem(
            criterion="planner_state_consistency",
            result="pass" if state_ok else "fail",
            detail=(
                "The ready plan has execution authorization, no missing inputs, and at least one step."
                if state_ok
                else "Ready status conflicts with authorization, missing-input, or step state."
            ),
        )
    )

    if policy_model is None:
        rubric.append(
            PlanRubricItem(
                criterion="project_policy_binding",
                required=False,
                result="not_applicable",
                detail="No project policy snapshot was supplied to this evaluation.",
            )
        )
    else:
        try:
            ProjectPolicyLoader._validate_against_code(policy_model.workflows)
            policy_ok = plan.policy_hash == policy_model.policy_hash
            policy_detail = (
                "Plan policy hash matches the validated project policy."
                if policy_ok
                else "Plan policy hash does not match the active project policy."
            )
        except Exception as error:
            policy_ok = False
            policy_detail = f"Project policy validation failed: {type(error).__name__}."
        rubric.append(
            PlanRubricItem(
                criterion="project_policy_binding",
                result="pass" if policy_ok else "fail",
                detail=policy_detail,
            )
        )

    applicable = [item for item in rubric if item.result != "not_applicable"]
    passed = sum(item.result == "pass" for item in applicable)
    score = round(100 * passed / len(applicable)) if applicable else 0
    rejected = any(item.required and item.result == "fail" for item in rubric)
    return PlanEvaluationResult(
        status="rejected" if rejected else "approved",
        score=score,
        summary=(
            "The plan failed one or more required pre-execution criteria."
            if rejected
            else "The plan passed every required pre-execution criterion."
        ),
        rubric=rubric,
    )
