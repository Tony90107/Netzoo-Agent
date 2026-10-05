"""Code-enforced review of execution-ready workflow plans."""

from __future__ import annotations

import hashlib
import re

from workflow_registry import (
    ACTION_DEFINITIONS,
    CODE_VALIDATION_STEPS,
    LOCAL_EXECUTION_ACTIONS,
    REQUIRED_INPUTS,
    RUN_ACTIONS,
    workflow_name as _workflow_name,
    registered_handoff_consumers,
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
from ..data.cobra import cobra_input_output_collisions
from ..policy import ProjectPolicyLoader
from ..planning.step_decision import effective_step_decision
from ..contracts.requirements import RequestRequirements
from ..interpretation.request_requirements import stated_path
from ..routing.authorization import forbidding_reason, read_operation_authorization
from ..data.paths import _resolve_user_path
from ..string_download import requested_network_kind, requested_species
from .plan_rules import (
    _bundle_provenance_failures,
    _derived_evidence_contract_failures,
    _evidence_contract_failures,
    _expected_plan_steps,
    _path_hygiene_failures,
)

def _operation_authorization_item(
    plan: WorkflowPlan, decision: TaskDecision, user_task: str,
    requirements: RequestRequirements | None = None,
) -> PlanRubricItem:
    """Re-read operation authority from the request, not from the decision.

    ``should_execute`` is written by the stages being checked; a ban in the
    user's own words is independent evidence, so a plan for a forbidden
    operation fails here even if an upstream rule promoted it (F1/F2). The
    turn's requirements hold the same reading of the full message.
    """
    authorization = (
        requirements.operations if requirements is not None
        else read_operation_authorization(user_task)
    )
    refusals = [
        f"{action}: {reason}"
        for action in dict.fromkeys([decision.action, *(step.action for step in plan.steps)])
        if (reason := forbidding_reason(authorization, action))
    ]
    return PlanRubricItem(
        criterion="operation_authorization",
        result="fail" if refusals else "pass",
        detail=(
            "; ".join(refusals)
            if refusals
            else "The request does not forbid any planned operation."
        ),
    )


def _same_path(planned: object, stated: object) -> bool:
    if stated_path(str(planned)) == stated_path(str(stated)):
        return True
    return _resolve_user_path(stated_path(str(planned))) == _resolve_user_path(stated_path(str(stated)))


def _request_requirements_item(
    decision: TaskDecision, user_task: str, requirements: RequestRequirements | None,
) -> PlanRubricItem:
    """The plan answers the request routing read, and keeps what the user stated.

    Plan item 2: a stated input or output path, in this turn or in the request
    it continues, may not be replaced by a default or a discovered file.
    """
    if requirements is None:
        return PlanRubricItem(
            criterion="request_requirements", required=False, result="not_applicable",
            detail="No turn requirements were supplied to this evaluation.",
        )
    failures = []
    if hashlib.sha256(user_task.encode("utf-8")).hexdigest() != requirements.source_sha256:
        failures.append("the plan is evaluated against a different request than the one routed")
    for field in dict.fromkeys(item.field for item in requirements.stated):
        if field not in INPUT_ROLE_FIELDS | OUTPUT_ROLE_FIELDS:
            continue
        stated, planned = requirements.stated_value(field), getattr(decision, field, None)
        if planned is not None and not _same_path(planned, stated):
            failures.append(f"{field} is {planned}, but the user stated {stated}")
    return PlanRubricItem(
        criterion="request_requirements",
        result="fail" if failures else "pass",
        detail=(
            "; ".join(failures) if failures
            else "The plan answers the routed request and keeps every stated input and output."
        ),
    )


def evaluate_workflow_plan(
    plan: WorkflowPlan,
    user_task: str,
    project_policy: ProjectPolicySnapshot | dict | None = None,
    *,
    requirements: RequestRequirements | dict | None = None,
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
    policy_model = (
        ProjectPolicySnapshot.model_validate(project_policy)
        if project_policy is not None
        else None
    )
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
    if requirements is not None:
        requirements = RequestRequirements.model_validate(requirements)
    authority = _operation_authorization_item(plan, decision, user_task, requirements)
    stated = _request_requirements_item(decision, user_task, requirements)
    if action == "download_string":
        valid = (
            authority.result == "pass" and stated.result != "fail" and
            plan.workflow == "STRING-DOWNLOAD"
            and len(plan.steps) == 1
            and plan.steps[0].action == "download_string"
            and not plan.steps[0].arguments
            and decision.should_execute
            and not plan.missing_inputs
            and not decision.missing_inputs
            and bool(decision.taxon)
            and decision.taxon == requested_species(user_task)
            and decision.string_network_type in {"functional", "physical", "regulatory"}
            and decision.string_network_type == requested_network_kind(user_task)
            and decision.requested_outcome is not None
            and decision.requested_outcome.operation == "acquire"
            and bool(re.search(r"(?<![A-Za-z0-9])STRING(?:-DB)?(?![A-Za-z0-9])|string-db\.org", user_task, re.I))
            and all(
                any(item.field == field and item.value == getattr(decision, field) and item.status != "missing"
                    for item in plan.evidence)
                for field in ("taxon", "string_network_type")
            )
        )
        return PlanEvaluationResult(
            status="approved" if valid else "rejected",
            score=100 if valid else 0,
            summary="STRING acquisition plan is valid." if valid else "STRING acquisition plan is incomplete or inconsistent.",
            rubric=[authority, stated, PlanRubricItem(
                criterion="string_acquisition_contract",
                result="pass" if valid else "fail",
                detail="Species, network type, acquisition intent, and one official download step are required.",
            )],
        )
    handoff = plan.workflow_handoff or getattr(decision, "workflow_handoff", None)
    recognized_action = action in REQUIRED_INPUTS and action != "no_tool"
    expected_workflow = _workflow_name(action)
    if handoff is not None and handoff.status == "validated":
        expected_workflow = f"{expected_workflow} -> {handoff.consumer_workflow}"
    capability_ok = (
        recognized_action
        and plan.workflow == expected_workflow
    )
    rubric.append(authority)
    rubric.append(stated)
    rubric.append(
        PlanRubricItem(
            criterion="intent_and_capability_alignment",
            result="pass" if capability_ok else "fail",
            detail=(
                f"Action {action} is registered and matches workflow {plan.workflow}."
                if capability_ok
                else "The action is not registered or does not match the validated workflow."
            ),
        )
    )

    if handoff is None:
        handoff_ok = True
        handoff_detail = "No composed workflow handoff was requested."
    elif handoff.status != "validated":
        handoff_ok = False
        handoff_detail = (
            f"Handoff status is {handoff.status}; blocked handoffs cannot execute."
        )
    else:
        registry = policy_model.workflows if policy_model is not None else ACTION_DEFINITIONS
        consumers = registered_handoff_consumers(handoff.producer_action, registry)
        consumer = next(
            (item for item in consumers if item.action == handoff.consumer_action),
            None,
        )
        evidence_by_field = {item.field: item for item in plan.evidence}
        missing_priors = [
            field
            for field in handoff.required_prior_inputs
            if not getattr(decision, field, None)
            or evidence_by_field.get(field) is None
            or evidence_by_field[field].status == "missing"
        ]
        identities_ok = (
            bool(handoff.sample_ids and handoff.gene_ids and handoff.source_artifact_paths)
            and len(handoff.sample_ids) == len(set(handoff.sample_ids))
            and len(handoff.gene_ids) == len(set(handoff.gene_ids))
        )
        field_ok = (
            consumer is not None
            and handoff.consumer_input_field == consumer.input_field
        )
        handoff_ok = field_ok and identities_ok and not missing_priors
        handoff_detail = (
            "Registered consumer, exact artifact identity, sample IDs, gene order, and prior inputs are present."
            if handoff_ok
            else "Invalid handoff contract: "
            + "; ".join(
                item
                for item in [
                    "consumer is not registered or its handoff input field does not match"
                    if not field_ok
                    else "",
                    "sample IDs and gene order must be validated before execution"
                    if not identities_ok
                    else "",
                    "missing registered prior inputs: " + ", ".join(missing_priors)
                    if missing_priors
                    else "",
                ]
                if item
            )
        )
    rubric.append(
        PlanRubricItem(
            criterion="workflow_handoff_contract",
            result="pass" if handoff_ok else "fail",
            detail=handoff_detail,
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
            _evidence_contract_failures(
                plan.evidence, user_task,
                stated=(
                    {field: requirements.stated_value(field)
                     for field in dict.fromkeys(item.field for item in requirements.stated)}
                    if requirements is not None else None
                ),
            )
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
    if handoff is not None and handoff.status == "validated":
        consumer_spec = (
            policy_model.workflows.get(handoff.consumer_action)
            if policy_model is not None and handoff.consumer_action
            else None
        )
        if consumer_spec is not None:
            normal_steps.extend(
                [*consumer_spec.validation_steps, consumer_spec.execution_step]
            )
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

    step_argument_errors = []
    for index in range(len(plan.steps)):
        try:
            effective_step_decision(plan, index)
        except (ValueError, TypeError) as error:
            step_argument_errors.append(str(error))
    rubric.append(PlanRubricItem(
        criterion="step_argument_alignment",
        result="fail" if step_argument_errors else "pass",
        detail=(
            "; ".join(step_argument_errors) if step_argument_errors
            else "Every step uses the typed arguments reviewed in the plan."
        ),
    ))

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

    cobra_collisions = (
        cobra_input_output_collisions(
            decision.expression_file, decision.design_file, decision.output_dir,
        )
        if action == "run_cobra"
        and decision.expression_file
        and decision.design_file
        and decision.output_dir
        else ()
    )
    rubric.append(
        PlanRubricItem(
            criterion="cobra_derived_output_safety",
            required=action == "run_cobra",
            result=(
                "not_applicable" if action != "run_cobra"
                else "fail" if cobra_collisions else "pass"
            ),
            detail=(
                "This workflow does not derive COBRA output paths."
                if action != "run_cobra"
                else "COBRA output would overwrite an input: "
                + ", ".join(map(str, cobra_collisions))
                if cobra_collisions
                else "All COBRA derived outputs are distinct from its inputs."
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
