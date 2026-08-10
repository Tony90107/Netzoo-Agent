"""Repair router decisions against deterministic workflow authority."""

from __future__ import annotations

import re

from workflow_registry import (
    LOCAL_WORKFLOW_ACTIONS,
    OUTPUT_CAPABILITIES,
    REQUIRED_INPUTS,
)

from ..contracts import (
    InputEvidence,
    LIONESS_MODE_QUESTION,
    RequestedOutcome,
    TaskDecision,
    WorkflowPlan,
    _is_demo_request,
    _ui_text,
)
from ..routing import (
    MIN_TOOL_CONFIDENCE,
    has_direct_execution_intent,
    is_workflow_information_request,
)
from ..routing.outcome_matching import (
    apply_outcome_match,
    guidance_actions_for,
    named_workflow_action,
)
from .extraction import (
    _task_path,
    documentation_library_for_task,
    is_versioned_documentation_request,
)

__all__: list[str] = []


def _lioness_mode_plan(
    decision: TaskDecision,
    task: str,
    *,
    memory_notes: list[str],
    policy_hash: str | None,
) -> WorkflowPlan:
    """Build a resumable mode-selection step without guessing the LIONESS method."""
    candidates = [
        _ui_text("LIONESS PANDA - expression + motif/prior + PPI"),
        _ui_text("LIONESS PUMA - expression + TF/miRNA prior + PPI + miRNA list"),
        _ui_text("LIONESS co-expression - expression only"),
    ]
    question = _ui_text(LIONESS_MODE_QUESTION)
    mode_decision = decision.model_copy(
        update={
            "action": "no_tool",
            "in_scope": True,
            "should_execute": False,
            "confidence": max(decision.confidence, MIN_TOOL_CONFIDENCE),
            "reason": "A LIONESS run was requested, but its base method is ambiguous.",
            "missing_inputs": ["lioness_mode"],
        }
    )
    return WorkflowPlan(
        workflow="LIONESS",
        objective=f"Choose a LIONESS base method before continuing: {task}",
        decision=mode_decision.model_dump(),
        evidence=[
            InputEvidence(
                field="lioness_mode",
                status="missing",
                reason=_ui_text(
                    "LIONESS needs an explicit base method because PANDA, PUMA, and "
                    "co-expression require different inputs and produce different networks."
                ),
                candidates=candidates,
            )
        ],
        missing_inputs=["lioness_mode"],
        status="needs_input",
        question=question,
        memory_notes=memory_notes,
        policy_hash=policy_hash,
    )


def _ready_named_decision(
    decision: TaskDecision,
    action: str,
    *,
    should_execute: bool,
    reason: str,
) -> TaskDecision:
    updates = {
        "action": action if should_execute else "no_tool",
        "in_scope": True,
        "should_execute": should_execute,
        "confidence": max(decision.confidence, MIN_TOOL_CONFIDENCE),
        "reason": reason,
        "capability_match_status": "exact",
        "matched_actions": [action],
        "recommended_actions": guidance_actions_for(action),
        "alternative_actions": [],
        "mismatch_dimensions": [],
        "clarification_question": None,
    }
    return decision.model_copy(update=updates)


def _confirmed_outcome(task: str, action: str) -> RequestedOutcome:
    capability = OUTPUT_CAPABILITIES[action]
    granularity_match = re.search(
        r"CONFIRMED_GRANULARITY=([a-z_]+)",
        task,
        flags=re.IGNORECASE,
    )
    granularity = (
        granularity_match.group(1).casefold() if granularity_match else None
    )
    if granularity not in capability.granularities:
        granularity = (
            next(iter(capability.granularities))
            if len(capability.granularities) == 1
            else "unknown"
        )
    display_labels = {"tf": "TF", "mirna": "miRNA", "gene": "gene"}
    return RequestedOutcome(
        operation=capability.operation,
        artifact_type=capability.artifact_type,
        entity_types=sorted(capability.entity_types),
        display_entities=[
            display_labels.get(item, item) for item in sorted(capability.entity_types)
        ],
        regulator_types=sorted(capability.regulator_types),
        target_types=sorted(capability.target_types),
        granularity=granularity,
        unresolved_dimensions=([] if granularity != "unknown" else ["granularity"]),
    )


def repair_router_decision(raw_decision: TaskDecision, task: str) -> TaskDecision:
    """Repair under-routing while keeping execution tied to a typed exact match."""
    documentation_library = documentation_library_for_task(task)
    if is_versioned_documentation_request(task) and documentation_library:
        return TaskDecision(
            action="query_context7",
            in_scope=True,
            should_execute=True,
            intent_type="answer_question",
            confidence=max(raw_decision.confidence, MIN_TOOL_CONFIDENCE),
            reason="The request requires current or version-specific package documentation.",
            library_name=documentation_library,
            docs_query=task[:2_000],
            preference_updates=raw_decision.preference_updates,
        )

    confirmed_match = re.search(
        r"CONFIRMED_OUTCOME_ACTION=(run_[a-z_]+)",
        task,
        flags=re.IGNORECASE,
    )
    if confirmed_match:
        action = confirmed_match.group(1).casefold()
        if action in OUTPUT_CAPABILITIES:
            confirmed = raw_decision.model_copy(
                update={"requested_outcome": _confirmed_outcome(task, action)}
            )
            return _ready_named_decision(
                confirmed,
                action,
                should_execute=False,
                reason="The user confirmed a supported alternative outcome.",
            ).model_copy(update={"intent_type": "answer_question"})

    decision = apply_outcome_match(raw_decision)

    continuation_match = re.search(
        r"PREVIOUS_ACTION=(run_[a-z_]+)", task, flags=re.IGNORECASE
    )
    if continuation_match:
        action = continuation_match.group(1).casefold()
        if action in LOCAL_WORKFLOW_ACTIONS:
            decision = _ready_named_decision(
                decision,
                action,
                should_execute=True,
                reason=(
                    "Continuing a pending workflow; the previous action marker "
                    "overrides any router reclassification."
                ),
            )
            repaired = decision.model_dump()
            for field_name in REQUIRED_INPUTS.get(action, ()):
                parsed = _task_path(task, field_name)
                if parsed:
                    repaired[field_name] = parsed
            repaired["missing_inputs"] = [
                field_name
                for field_name in REQUIRED_INPUTS.get(action, ())
                if field_name not in {"output_file", "lioness_output", "output_dir"}
                and not repaired.get(field_name)
            ]
            return TaskDecision.model_validate(repaired)

    if decision.capability_match_status in {"ambiguous", "unsupported"}:
        return decision.model_copy(
            update={"action": "no_tool", "should_execute": False}
        )

    named_action = named_workflow_action(task)
    if decision.requested_outcome is None and named_action:
        decision = _ready_named_decision(
            decision,
            named_action,
            should_execute=False,
            reason="The user explicitly named a registered workflow.",
        )

    if is_workflow_information_request(task):
        return decision.model_copy(
            update={
                "action": "no_tool",
                "in_scope": True,
                "should_execute": False,
                "intent_type": "answer_question",
                "confidence": max(decision.confidence, MIN_TOOL_CONFIDENCE),
                "reason": (
                    "The request asks for stable workflow requirements or usage "
                    "guidance."
                ),
            }
        )

    if has_direct_execution_intent(task) and len(decision.matched_actions) == 1:
        action = decision.matched_actions[0]
        repaired = decision.model_dump()
        repaired.update(
            {
                "action": action,
                "in_scope": True,
                "should_execute": True,
                "intent_type": "demo_run" if _is_demo_request(task) else "run_analysis",
                "confidence": max(decision.confidence, MIN_TOOL_CONFIDENCE),
                "reason": "The requested outcome exactly matches a registered workflow.",
            }
        )
        repaired["missing_inputs"] = [
            field_name
            for field_name in REQUIRED_INPUTS[action]
            if not repaired.get(field_name)
        ]
        return TaskDecision.model_validate(repaired)

    normalized = task.casefold()
    run_intent = bool(
        re.search(
            r"(run|execute|trial|test|demo|試跑|執行|跑|跑一次|測試|做測試|示範|分析)",
            normalized,
            flags=re.IGNORECASE,
        )
    )
    if named_action and run_intent:
        decision = _ready_named_decision(
            decision,
            named_action,
            should_execute=True,
            reason="The user explicitly named a registered workflow.",
        )
        repaired = decision.model_dump()
        repaired["intent_type"] = (
            "demo_run" if _is_demo_request(task) else "run_analysis"
        )
        repaired["missing_inputs"] = [
            field_name
            for field_name in REQUIRED_INPUTS[named_action]
            if not repaired.get(field_name)
        ]
        return TaskDecision.model_validate(repaired)

    if raw_decision.action not in LOCAL_WORKFLOW_ACTIONS:
        return decision
    return decision.model_copy(update={"action": "no_tool", "should_execute": False})
