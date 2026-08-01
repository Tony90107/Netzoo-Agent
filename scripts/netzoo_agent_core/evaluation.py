"""Pre-execution plan review, result evaluation, rendering, and recovery."""

from __future__ import annotations

import re
from pathlib import Path


from workflow_registry import (
    CODE_VALIDATION_STEPS,
    LOCAL_EXECUTION_ACTIONS,
    REQUIRED_INPUTS,
    RUN_ACTIONS,
    workflow_name as _workflow_name,
)

from .contracts import (
    EXECUTE_TOOLS,
    EvaluationResult,
    INPUT_ROLE_FIELDS,
    InputEvidence,
    MAX_RECOVERY_ATTEMPTS,
    OUTPUT_ROLE_FIELDS,
    PlanEvaluationResult,
    PlanRubricItem,
    ProjectPolicySnapshot,
    TaskDecision,
    ToolExecutionResult,
    VERBOSE_OUTPUT,
    WorkflowPlan,
    WorkflowStep,
    _is_demo_request,
    _ui_text,
)

from .validation import (
    _resolve_user_path,
)

from .routing import (
    structure_tool_result,
    validate_task_text,
)

from .policy import (
    ProjectPolicyLoader,
)

from .interpretation import (
    _mentions_unspecified_data_directory,
)
from .outcomes import effective_results, terminal_failed
from .bundles import MULTI_FILE_ACTIONS
from .path_safety import condor_artifact_paths, resolved_output_collisions

__all__ = [
    "_path_literal_in_task",
    "_evidence_contract_failures",
    "_path_hygiene_failures",
    "_expected_plan_steps",
    "evaluate_workflow_plan",
    "render_plan_evaluation",
    "render_plan_rejection_response",
    "render_verbose_execution_response",
    "_compact_field_label",
    "_extract_command_preview",
    "_compact_validation_highlights",
    "render_compact_execution_response",
    "render_execution_response",
    "render_needs_input_response",
    "render_preference_confirmation_response",
    "evaluate_step_result",
    "recover_workflow_plan",
]


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
        elif item.status == "defaulted":
            if item.field not in OUTPUT_ROLE_FIELDS or not item.value:
                failures.append(
                    f"{item.field} is marked defaulted but is not a reversible output field"
                )
        elif item.status == "missing" and item.value:
            failures.append(f"{item.field} is missing but still carries a value")
    return failures


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
        or plan.recovery_step_index is not None
        or plan.recovery_attempt != 0
    )
    if not recovery_metadata_present:
        return normal_steps, True, "This is an initial plan with no recovery mutation."

    index = plan.recovery_step_index
    metadata_ok = (
        plan.recovery_action == "format_expression_headerless"
        and decision.action == "run_puma"
        and index is not None
        and 1 <= plan.recovery_attempt <= MAX_RECOVERY_ATTEMPTS
        and 0 <= index < len(normal_steps)
        and normal_steps[index] == "run_puma"
    )
    if not metadata_ok:
        return (
            normal_steps,
            False,
            "Recovery metadata does not identify an allow-listed, bounded PUMA repair.",
        )

    expected = [
        *normal_steps[:index],
        "format_expression",
        "inspect_inputs",
        "run_puma",
    ]
    sequence_ok = [step.action for step in plan.steps] == expected
    return (
        expected,
        sequence_ok,
        (
            "Recovery metadata and steps match the allow-listed header-removal repair."
            if sequence_ok
            else "Recovery steps do not match the allow-listed header-removal repair."
        ),
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

    provenance_failures = (
        _evidence_contract_failures(plan.evidence, user_task)
        if local_data_action
        else []
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


def render_plan_evaluation(evaluation: PlanEvaluationResult) -> str:
    """Render the typed rubric as Markdown for audit; code never parses this table."""

    def cell(value: str) -> str:
        return value.replace("|", "\\|").replace("\n", " ")

    lines = [
        "| Criterion | Required | Result | Detail |",
        "|---|---:|---|---|",
    ]
    for item in evaluation.rubric:
        lines.append(
            f"| {cell(item.criterion)} | {'yes' if item.required else 'no'} | "
            f"{item.result} | {cell(item.detail)} |"
        )
    lines.extend(
        [
            "",
            f"Plan evaluation: **{evaluation.status}** ({evaluation.score}/100).",
            evaluation.summary,
        ]
    )
    return "\n".join(lines)


def render_plan_rejection_response(evaluation: PlanEvaluationResult) -> str:
    return (
        "No tool was executed because the pre-execution Plan Evaluator rejected "
        "the plan.\n\n" + render_plan_evaluation(evaluation)
    )


def render_verbose_execution_response(
    plan: WorkflowPlan,
    results: list[ToolExecutionResult],
    evaluation: EvaluationResult | None,
) -> str:
    """Render the full auditable execution report used by --verbose."""
    results = effective_results(results)
    has_failure = terminal_failed(results, evaluation)
    has_dry_run = any(item.status == "dry_run" for item in results)
    if has_failure:
        headline = "The workflow stopped because the Evaluator detected a validation or execution failure."
    elif has_dry_run:
        headline = "The command preview completed. This was a dry run; the analysis tool was not executed."
    else:
        headline = "The workflow completed, and the output artifacts passed the Executor existence checks."

    lines = [headline, "", f"Workflow: {plan.workflow}", "", "Step results:"]
    for index, item in enumerate(results, 1):
        marker = (
            "✓"
            if item.status == "success"
            else "◌"
            if item.status == "dry_run"
            else "✗"
        )
        lines.append(f"{index}. {marker} {item.action} — {item.status}")
        if item.metrics:
            useful_metrics = {
                key: value
                for key, value in item.metrics.items()
                if key not in {"raw_output_chars", "raw_output_truncated"}
            }
            if useful_metrics:
                lines.append(
                    "   metrics: "
                    + ", ".join(
                        f"{key}={value}" for key, value in useful_metrics.items()
                    )
                )
        for warning in item.warnings:
            lines.append(f"   warning: {warning}")
        for error in item.errors:
            lines.append(f"   error: {error}")
        if item.log_file:
            lines.append(f"   log: {item.log_file}")

    artifacts = []
    for item in results:
        if item.status != "success":
            continue
        for artifact in item.artifacts:
            if artifact not in artifacts:
                artifacts.append(artifact)
    if artifacts:
        lines.extend(["", "Output artifacts:"])
        for artifact in artifacts:
            path = _resolve_user_path(artifact)
            if path.is_file():
                lines.append(f"- {artifact} ({path.stat().st_size} bytes)")
            elif path.is_dir():
                lines.append(f"- {artifact}/ (directory)")
            else:
                lines.append(f"- {artifact} (not created)")

    inspection_results = [
        item
        for item in results
        if item.action.startswith("inspect_") and item.raw_output
    ]
    if inspection_results:
        lines.extend(["", "Validation summary:", inspection_results[-1].raw_output])
    if evaluation:
        lines.extend(["", f"Evaluator: {evaluation.status} — {evaluation.reason}"])
    return "\n".join(lines)


def _compact_field_label(field_name: str) -> str:
    return {
        "expression_file": "Expression",
        "motif_file": "Motif/prior",
        "ppi_file": "PPI",
        "mirna_file": "miRNA list",
        "network_file": "Network",
        "output_file": "Aggregate/network output",
        "lioness_output": "Sample-specific output",
        "output_dir": "Output directory",
    }.get(field_name, field_name.replace("_", " ").capitalize())


def _extract_command_preview(results: list[ToolExecutionResult]) -> str | None:
    for item in reversed(results):
        fenced = re.search(r"```bash\s*\n([^\n]+)", item.raw_output)
        if fenced:
            return fenced.group(1).strip()
        executed = re.search(r"^Command:\s*`([^`]+)`", item.raw_output, re.MULTILINE)
        if executed:
            return executed.group(1).strip()
    return None


def _compact_validation_highlights(results: list[ToolExecutionResult]) -> list[str]:
    inspection = next(
        (
            item
            for item in reversed(results)
            if item.action.startswith("inspect_") and item.status == "success"
        ),
        None,
    )
    if not inspection:
        return []
    highlights = []
    expression_section = re.search(
        r"- expression:.*?\n(?:.*\n){0,5}?\s*shape:\s*([^\n]+)",
        inspection.raw_output,
        flags=re.IGNORECASE,
    )
    if expression_section:
        highlights.append(f"Expression shape: {expression_section.group(1).strip()}")
    labels = {
        "motif target genes overlapping expression genes": "Motif targets ↔ expression genes",
        "motif tfs overlapping ppi tfs": "Motif TFs ↔ PPI TFs",
        "mirna names overlapping motif/prior regulators": "miRNAs ↔ motif/prior regulators",
    }
    for raw_line in inspection.raw_output.splitlines():
        line = raw_line.strip().removeprefix("- ")
        lowered = line.casefold()
        for prefix, label in labels.items():
            if lowered.startswith(prefix + ":"):
                highlights.append(f"{label}: {line.split(':', 1)[1].strip()}")
                break
    return highlights[:4]


def render_compact_execution_response(
    plan: WorkflowPlan,
    results: list[ToolExecutionResult],
    evaluation: EvaluationResult | None,
) -> str:
    """Render the default user-facing result with progressive disclosure."""
    results = effective_results(results)
    has_failure = terminal_failed(results, evaluation)
    has_dry_run = any(item.status == "dry_run" for item in results)
    status = "FAILED" if has_failure else "DRY RUN" if has_dry_run else "COMPLETED"
    lines = [f"{plan.workflow} · {status}"]

    input_evidence = [
        item
        for item in plan.evidence
        if item.value
        and item.field not in {"output_file", "lioness_output", "output_dir"}
    ]
    if input_evidence:
        lines.extend(["", "Inputs"])
        for item in input_evidence:
            source = {
                "provided": "provided",
                "selected": "selected",
                "discovered": "auto-discovered",
                "demo_bundle": "demo bundle",
                "defaulted": "default",
            }.get(item.status, item.status)
            lines.append(
                f"- {_compact_field_label(item.field)}: {item.value} [{source}]"
            )

    inspection = next(
        (item for item in results if item.action.startswith("inspect_")), None
    )
    if inspection:
        lines.extend(["", "Validation"])
        marker = "✓" if inspection.status == "success" else "✗"
        verdict = (
            "Input formats and identifier compatibility passed."
            if inspection.status == "success"
            else "Input validation failed."
        )
        lines.append(f"{marker} {verdict}")
        for highlight in _compact_validation_highlights(results):
            lines.append(f"- {highlight}")

    lines.extend(["", "Result"])
    if has_failure:
        lines.append("✗ The workflow stopped before successful completion.")
    elif has_dry_run:
        lines.append("○ Command preview ready; no analysis was executed.")
    else:
        lines.append("✓ The workflow completed successfully.")

    warnings = [warning for item in results for warning in item.warnings]
    errors = [error for item in results for error in item.errors]
    for warning in warnings:
        lines.append(f"Warning: {warning}")
    for error in errors:
        lines.append(f"Error: {error}")

    command = _extract_command_preview(results)
    if has_dry_run and command:
        lines.extend(["", "Command", command])

    output_evidence = [
        item
        for item in plan.evidence
        if item.value and item.field in {"output_file", "lioness_output", "output_dir"}
    ]
    if output_evidence:
        heading = "Planned outputs" if has_dry_run else "Outputs"
        lines.extend(["", heading])
        for item in output_evidence:
            path = _resolve_user_path(item.value)
            suffix = ""
            if not has_dry_run and path.is_file():
                suffix = f" ({path.stat().st_size} bytes)"
            elif not has_dry_run and not path.exists():
                suffix = " (not created)"
            lines.append(f"- {_compact_field_label(item.field)}: {item.value}{suffix}")

    if has_failure:
        log_files = [item.log_file for item in results if item.log_file]
        if log_files:
            lines.extend(["", "Diagnostic logs"])
            lines.extend(f"- {path}" for path in log_files)
        if evaluation:
            lines.extend(["", f"Next: {evaluation.reason}"])
    elif has_dry_run:
        lines.extend(["", "Next: rerun with --execute to perform the analysis."])
    return "\n".join(lines)


def render_execution_response(
    plan: WorkflowPlan,
    results: list[ToolExecutionResult],
    evaluation: EvaluationResult | None,
    verbose: bool | None = None,
) -> str:
    """Select the compact default or the full --verbose execution report."""
    use_verbose = VERBOSE_OUTPUT if verbose is None else verbose
    renderer = (
        render_verbose_execution_response
        if use_verbose
        else render_compact_execution_response
    )
    return renderer(plan, results, evaluation)


def render_needs_input_response(plan: WorkflowPlan) -> str:
    if "lioness_mode" in plan.missing_inputs:
        return _ui_text(
            "No tool was executed because the LIONESS base method is ambiguous. "
            "Choose one of the listed modes to continue."
        )
    lines = [
        _ui_text("No tool was executed because the Planner requires additional input."),
        "",
    ]
    lines.append(plan.question or _ui_text("Please provide the missing input paths."))
    return "\n".join(lines)


def render_preference_confirmation_response(plan: WorkflowPlan) -> str:
    lines = [
        _ui_text(
            "No preference has been saved yet. Explicit confirmation is required."
        ),
        "",
        _ui_text("Proposed long-term preferences:"),
    ]
    for proposal in plan.preference_proposals:
        lines.append(f"- {proposal.key} = {proposal.value}")
        lines.append(_ui_text("  Reason: ") + proposal.reason)
    return "\n".join(lines)


def evaluate_step_result(
    plan: WorkflowPlan,
    step_index: int,
    result: ToolExecutionResult | dict | str,
    replan_count: int = 0,
) -> EvaluationResult:
    if isinstance(result, str):
        action = plan.steps[step_index].action
        try:
            decision = TaskDecision.model_validate(plan.decision)
        except Exception:
            decision = TaskDecision(
                action=action,
                in_scope=True,
                should_execute=True,
                confidence=1.0,
                reason="legacy evaluator input",
            )
        structured = structure_tool_result(action, decision, result)
    else:
        structured = ToolExecutionResult.model_validate(result)
    if structured.status == "failed":
        if (
            structured.retryable
            and structured.recovery_hint
            and replan_count < MAX_RECOVERY_ATTEMPTS
            and EXECUTE_TOOLS
        ):
            return EvaluationResult(
                status="replan",
                reason="The failure is recoverable; return to the Planner to insert an approved repair step.",
                recovery_action=structured.recovery_hint,
            )
        return EvaluationResult(
            status="failed",
            reason="The structured tool result reports a validation or execution failure.",
        )
    if step_index + 1 < len(plan.steps):
        return EvaluationResult(
            status="continue",
            reason="This step passed; continue to the next planned step.",
        )
    return EvaluationResult(
        status="completed", reason="All planned steps completed successfully."
    )


def recover_workflow_plan(
    plan: WorkflowPlan,
    step_index: int,
    evaluation: EvaluationResult,
) -> tuple[WorkflowPlan, int]:
    """Apply allow-listed, bounded repairs; never let the LLM invent shell actions."""
    if evaluation.recovery_action != "format_expression_headerless":
        return plan, step_index

    decision = TaskDecision.model_validate(plan.decision)
    if not decision.expression_file or not decision.output_file:
        return plan, step_index
    source = Path(decision.expression_file)
    output_parent = Path(decision.output_file).parent
    derived = str(output_parent / f"{source.stem}.puma-expression.tsv")
    original_run_action = plan.steps[step_index].action
    decision.expression_file = derived
    plan.decision = decision.model_dump()
    expression_evidence = next(
        (item for item in plan.evidence if item.field == "expression_file"),
        None,
    )
    recovery_reason = (
        "The prior PUMA attempt rejected the expression header, so the bounded "
        "recovery derived a headerless expression file."
    )
    if expression_evidence is None:
        plan.evidence.append(
            InputEvidence(
                field="expression_file",
                status="discovered",
                value=derived,
                reason=recovery_reason,
            )
        )
    else:
        expression_evidence.status = "discovered"
        expression_evidence.value = derived
        expression_evidence.reason = recovery_reason
        expression_evidence.candidates = []
    recovery_steps = [
        WorkflowStep(
            action="format_expression",
            purpose="Remove the expression header rejected by PUMA and create a derived input file.",
            arguments={
                "expression_file": str(source),
                "output_file": derived,
                "genes_axis": "auto",
                "with_header": False,
            },
        ),
        WorkflowStep(
            action="inspect_inputs",
            purpose="Revalidate the repaired expression file against the prior and PPI inputs.",
        ),
        WorkflowStep(
            action=original_run_action,
            purpose="Retry the PUMA workflow with the repaired input.",
        ),
    ]
    plan.steps = [*plan.steps[:step_index], *recovery_steps]
    plan.recovery_action = "format_expression_headerless"
    plan.recovery_step_index = step_index
    plan.recovery_attempt = min(
        plan.recovery_attempt + 1,
        MAX_RECOVERY_ATTEMPTS,
    )
    return plan, step_index
