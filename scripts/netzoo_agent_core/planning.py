"""Evidence-ledger construction and deterministic workflow planning."""

from __future__ import annotations

import re
from pathlib import Path


from workflow_registry import (
    CODE_VALIDATION_STEPS,
    LOCAL_WORKFLOW_ACTIONS,
    REQUIRED_INPUTS,
    workflow_name as _workflow_name,
)

from .contracts import (
    Episode,
    InputEvidence,
    OUTPUT_ROLE_FIELDS,
    PROJECT_ROOT,
    ProjectPolicySnapshot,
    TaskDecision,
    UserProfile,
    WorkflowPlan,
    WorkflowStep,
    _is_demo_request,
)

from .validation import (
    _resolve_user_path,
)

from .routing import (
    MIN_TOOL_CONFIDENCE,
    _default_lioness_outputs,
    _default_network_output,
    _find_candidate_files,
    enforce_capability_gate,
    validate_task_text,
)

from .policy import (
    ProjectPolicyLoader,
)

from .interpretation import (
    _candidate_keywords,
    _choose_unambiguous_candidate,
    _lioness_mode_plan,
    _mentions_unspecified_data_directory,
    _needs_lioness_mode_choice,
    _task_path,
    discover_demo_bundle,
    reusable_episode_inputs,
)

__all__ = [
    "build_workflow_plan",
    "render_plan",
]


def build_workflow_plan(
    raw_decision: TaskDecision,
    task: str,
    profile: UserProfile | dict | None = None,
    retrieved_episodes: list[Episode | dict] | None = None,
    project_policy: ProjectPolicySnapshot | dict | None = None,
) -> WorkflowPlan:
    """Turn intent into an evidence-backed, multi-step NetZoo workflow."""
    decision = raw_decision.model_copy(deep=True)
    profile_model = (
        UserProfile.model_validate(profile)
        if profile is not None
        else UserProfile(profile_id="default")
    )
    episode_models = [
        Episode.model_validate(item) for item in (retrieved_episodes or [])
    ]
    memory_notes = [
        f"Retrieved {episode.status} episode {episode.episode_id[:8]} for {episode.workflow}."
        for episode in episode_models
    ]
    policy_model = (
        ProjectPolicySnapshot.model_validate(project_policy)
        if project_policy is not None
        else None
    )
    if policy_model is not None:
        ProjectPolicyLoader._validate_against_code(policy_model.workflows)
    policy_hash = policy_model.policy_hash if policy_model else None
    policy_notes = []
    workflow_spec = None
    preferred_workflow_authorized = False
    preferred_workflow = profile_model.preferences.get("preferred_workflow")
    if (
        decision.action == "no_tool"
        and isinstance(preferred_workflow, str)
        and re.search(
            r"(preferred|default).{0,16}workflow|workflow.{0,16}(preferred|default)"
            r"|偏好.{0,8}(工作流|流程)|預設.{0,8}(工作流|流程)",
            task,
            flags=re.IGNORECASE,
        )
        and re.search(r"(run|execute|start|執行|開始|跑)", task, flags=re.IGNORECASE)
    ):
        decision.action = f"run_{preferred_workflow}"
        decision.in_scope = True
        decision.should_execute = True
        decision.confidence = max(decision.confidence, MIN_TOOL_CONFIDENCE)
        decision.reason = (
            f"The user explicitly requested the confirmed preferred workflow: "
            f"{preferred_workflow}."
        )
        preferred_workflow_authorized = True
        memory_notes.append(
            f"Applied confirmed preferred_workflow={preferred_workflow}."
        )
    if _needs_lioness_mode_choice(task):
        return _lioness_mode_plan(
            decision,
            task,
            memory_notes=memory_notes,
            policy_hash=policy_hash,
        )
    action = decision.action
    workflow = _workflow_name(action)
    if action in {"query_context7", "web_search"}:
        decision = enforce_capability_gate(decision, user_task=task)
        action = decision.action
        workflow = _workflow_name(action)
    elif action != "no_tool":
        rejection = (
            None if preferred_workflow_authorized else validate_task_text(task, action)
        )
        reasons = []
        if rejection:
            reasons.append(rejection)
        if (
            action in LOCAL_WORKFLOW_ACTIONS
            and decision.intent_type == "answer_question"
        ):
            reasons.append(
                "The request was classified as an information question, not an execution request."
            )
        if not decision.in_scope:
            reasons.append("The task is outside the NetZoo agent capability scope.")
        if decision.confidence < MIN_TOOL_CONFIDENCE:
            reasons.append(
                f"Tool-selection confidence is too low ({decision.confidence:.2f})."
            )
        if reasons:
            decision = TaskDecision(
                action="no_tool",
                in_scope=decision.in_scope,
                should_execute=False,
                confidence=decision.confidence,
                reason="；".join(reasons),
                recommended_actions=decision.recommended_actions,
            )
            action = "no_tool"
            workflow = "NO-TOOL"

    if policy_model and action in policy_model.workflows:
        workflow_spec = policy_model.workflows[action]
        policy_notes = [
            f"Validated workflow specification {workflow_spec.workflow} under project policy {policy_hash[:12]}.",
            *workflow_spec.conventions,
        ]

    if action == "no_tool" or action in {"query_context7", "web_search"}:
        steps = (
            []
            if action == "no_tool"
            else [
                WorkflowStep(
                    action=action,
                    purpose="Retrieve reference material required for the answer.",
                )
            ]
        )
        return WorkflowPlan(
            workflow=workflow,
            objective=decision.reason,
            decision=decision.model_dump(),
            steps=steps,
            status="respond_only" if action == "no_tool" else "ready",
            memory_notes=memory_notes,
            policy_hash=policy_hash,
            policy_notes=policy_notes,
        )

    required = (
        list(workflow_spec.required_inputs)
        if workflow_spec is not None
        else list(REQUIRED_INPUTS[action])
    )
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
        selected, reason = _choose_unambiguous_candidate(candidates, keywords, nearby)
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

    missing = [item.field for item in evidence if item.status == "missing"]
    decision.missing_inputs = missing
    decision.should_execute = not missing
    if missing:
        question = (
            "Please provide the next missing input. The CLI wizard will ask for "
            "each unresolved field one at a time; advanced users may still enter "
            "field=value pairs for all remaining inputs."
        )
        return WorkflowPlan(
            workflow=workflow,
            objective=decision.reason,
            decision=decision.model_dump(),
            evidence=evidence,
            missing_inputs=missing,
            status="needs_input",
            question=question,
            memory_notes=memory_notes,
            policy_hash=policy_hash,
            policy_notes=policy_notes,
        )

    steps = []
    validation_actions = (
        list(workflow_spec.validation_steps)
        if workflow_spec is not None
        else CODE_VALIDATION_STEPS.get(action, [])
    )
    for validation_action in validation_actions:
        steps.append(
            WorkflowStep(
                action=validation_action,
                purpose="Validate input formats and identifier compatibility before execution.",
            )
        )
    execution_action = (
        workflow_spec.execution_step if workflow_spec is not None else action
    )
    steps.append(
        WorkflowStep(
            action=execution_action,
            purpose="Execute the requested NetZoo workflow.",
        )
    )
    return WorkflowPlan(
        workflow=workflow,
        objective=decision.reason,
        decision=decision.model_dump(),
        evidence=evidence,
        steps=steps,
        status="ready",
        memory_notes=memory_notes,
        policy_hash=policy_hash,
        policy_notes=policy_notes,
    )


def render_plan(plan: WorkflowPlan) -> str:
    lines = [f"Workflow: {plan.workflow}", "Evidence ledger:"]
    if not plan.evidence:
        lines.append("- This task does not require local data files.")
    for item in plan.evidence:
        value = f" → {item.value}" if item.value else ""
        lines.append(f"- {item.field}: {item.status}{value} ({item.reason})")
        if item.status == "missing" and item.candidates:
            lines.append("  Candidates: " + ", ".join(item.candidates))
    if plan.steps:
        lines.append("Execution plan:")
        for index, step in enumerate(plan.steps, 1):
            lines.append(f"{index}. {step.action}: {step.purpose}")
    if plan.memory_notes:
        lines.append("Retrieved memory:")
        lines.extend(f"- {note}" for note in plan.memory_notes)
    if plan.policy_notes:
        lines.append(f"Project policy ({(plan.policy_hash or 'unknown')[:12]}):")
        lines.extend(f"- {note}" for note in plan.policy_notes)
    if plan.preference_proposals:
        lines.append("Preference changes awaiting confirmation:")
        lines.extend(
            f"- {proposal.key} = {proposal.value} ({proposal.reason})"
            for proposal in plan.preference_proposals
        )
    if plan.question:
        lines.append("User input required: " + plan.question)
    return "\n".join(lines)
