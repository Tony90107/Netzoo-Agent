"""Final clarification or executable plan assembly."""

from __future__ import annotations

from pathlib import Path

from workflow_registry import CODE_VALIDATION_STEPS, workflow_name

from .context import _PlanningContext
from ..contracts import InputBundleOption, InputEvidence, WorkflowPlan, WorkflowStep

__all__: list[str] = []


def _assemble_workflow_plan(
    context: _PlanningContext,
    evidence: list[InputEvidence],
) -> WorkflowPlan:
    decision = context.decision
    action = context.action
    workflow = context.workflow
    workflow_spec = context.workflow_spec
    memory_notes = context.memory_notes
    policy_hash = context.policy_hash
    policy_notes = context.policy_notes
    workflow_handoff = context.workflow_handoff
    missing = [item.field for item in evidence if item.status == "missing"]
    decision.missing_inputs = missing
    decision.should_execute = not missing
    if missing:
        input_bundle_options: list[InputBundleOption] = []
        discovered_bundle = [
            item
            for item in evidence
            if item.status == "discovered" and item.bundle_id
        ]
        bundle_choice = next(
            (
                item
                for item in evidence
                if item.status == "missing"
                and item.candidate_bundle_ids
            ),
            None,
        )
        if bundle_choice and bundle_choice.candidates:
            input_evidence = [
                item
                for item in evidence
                if item.field not in {"output_file", "lioness_output", "output_dir"}
            ]
            choice_lines: list[str] = []
            for index, value in enumerate(bundle_choice.candidates, 1):
                inputs = {
                    item.field: item.candidates[index - 1]
                    for item in input_evidence
                    if index <= len(item.candidates)
                }
                directory = str(Path(value).parent)
                input_bundle_options.append(
                    InputBundleOption(
                        bundle_id=bundle_choice.candidate_bundle_ids[index - 1],
                        directory=directory,
                        inputs=inputs,
                    )
                )
                choice_lines.append(f"{index}. {directory}/")
                for item in input_evidence:
                    if index <= len(item.candidates):
                        choice_lines.append(
                            f"   - {Path(item.candidates[index - 1]).name}"
                        )
            question = (
                "Choose one complete input bundle before the workflow continues, "
                "or enter custom to select files individually:\n"
                + "\n".join(choice_lines)
            )
        elif discovered_bundle:
            actions = decision.recommended_actions or [action]
            workflow_sequence = " -> ".join(workflow_name(item) for item in actions)
            directory = str(Path(discovered_bundle[0].value).parent)
            files = "\n".join(
                f"   - {Path(item.value).name}"
                for item in discovered_bundle
                if item.value
            )
            question = (
                f"I can prepare the {workflow_sequence} workflow.\n\n"
                "I found this partial input bundle:\n\n"
                f"1. {directory}/\n{files}\n\n"
                "Please provide the remaining required input"
                + ("s" if len(missing) != 1 else "")
                + ": "
                + ", ".join(missing)
                + ". The wizard will ask only for these missing fields."
            )
        else:
            question = (
                "Please provide the next missing input. The CLI wizard will ask for "
                "each unresolved field one at a time."
            )
        return WorkflowPlan(
            workflow=workflow,
            objective=decision.reason,
            decision=decision.model_dump(),
            workflow_handoff=workflow_handoff,
            evidence=evidence,
            input_bundle_options=input_bundle_options,
            missing_inputs=missing,
            status="needs_input",
            question=question,
            memory_notes=memory_notes,
            policy_hash=policy_hash,
            policy_notes=policy_notes,
        )

    if context.preflight_errors:
        decision.should_execute = False
        errors = "\n".join(f"- {error}" for error in context.preflight_errors)
        if context.role_mismatch_hints:
            hints = "\n".join(f"- {hint}" for hint in context.role_mismatch_hints)
            remedy = (
                "\nThe file contents suggest the input roles are crossed:\n\n"
                f"{hints}\n\n"
                "Confirm the corrected assignment, or supply the intended paths, "
                "and I will re-check them."
            )
        else:
            remedy = (
                "\nPlease provide corrected files or fix the file contents, then "
                "I will re-check them."
            )
        return WorkflowPlan(
            workflow=workflow,
            objective=decision.reason,
            decision=decision.model_dump(),
            workflow_handoff=workflow_handoff,
            evidence=evidence,
            missing_inputs=[],
            status="needs_input",
            question=(
                "Input preflight failed, so the Work Plan is not ready:\n\n"
                f"{errors}\n{remedy}"
            ),
            memory_notes=memory_notes,
            policy_hash=policy_hash,
            policy_notes=policy_notes,
        )

    # Discovery and inference are evidence, not execution authority. Every
    # discovered or demo-selected local input must be deliberately confirmed.
    confirmation_evidence = [
        item
        for item in evidence
        if (
            (
                item.reason.startswith("Role inferred from file contents by the LLM")
                or item.status in {"discovered", "demo_bundle"}
            )
        )
        and item.value
        and item.field not in {"output_file", "lioness_output", "output_dir"}
    ]
    if confirmation_evidence:
        lines = [
            f"I identified these local inputs for the {workflow} workflow:",
            "",
        ]
        for item in confirmation_evidence:
            lines.append(f"- {item.field}: {item.value}")
            lines.append(f"  Evidence: {item.reason}")
        lines.extend(
            [
                "",
                "Are these the files you want to use? [y/N]",
                "If not, answer no and provide the correct path(s).",
            ]
        )
        decision.should_execute = False
        return WorkflowPlan(
            workflow=workflow,
            objective=decision.reason,
            decision=decision.model_dump(),
            workflow_handoff=workflow_handoff,
            evidence=evidence,
            missing_inputs=[],
            status="needs_confirmation",
            question="\n".join(lines),
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
    if workflow_handoff is not None and workflow_handoff.status == "validated":
        consumer_spec = (
            context.policy.workflows.get(workflow_handoff.consumer_action)
            if context.policy is not None and workflow_handoff.consumer_action
            else None
        )
        if consumer_spec is not None:
            for validation_action in consumer_spec.validation_steps:
                steps.append(
                    WorkflowStep(
                        action=validation_action,
                        purpose=(
                            "Validate the registered BONOBO handoff artifact, preserving "
                            "sample identity and gene order before downstream execution."
                        ),
                    )
                )
            steps.append(
                WorkflowStep(
                    action=consumer_spec.execution_step,
                    purpose=(
                        "Execute the registered downstream consumer using the validated "
                        "BONOBO artifact and declared prior inputs."
                    ),
                )
            )
        workflow = f"{workflow} -> {workflow_handoff.consumer_workflow}"
    return WorkflowPlan(
        workflow=workflow,
        objective=decision.reason,
        decision=decision.model_dump(),
        workflow_handoff=workflow_handoff,
        evidence=evidence,
        steps=steps,
        status="ready",
        memory_notes=memory_notes,
        policy_hash=policy_hash,
        policy_notes=policy_notes,
    )
