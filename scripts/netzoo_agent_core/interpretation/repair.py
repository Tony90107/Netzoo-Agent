"""Repair router decisions against deterministic workflow authority."""

from __future__ import annotations

import re

from workflow_registry import (
    ACTION_DEFINITIONS,
    LOCAL_WORKFLOW_ACTIONS,
    OUTPUT_CAPABILITIES,
    REQUIRED_INPUTS,
    registered_actions_for_family,
)

from ..contracts import (
    InputEvidence,
    LIONESS_MODE_QUESTION,
    RequestedOutcome,
    TaskDecision,
    WorkflowPlan,
    _ui_text,
)
from ..routing import (
    MIN_TOOL_CONFIDENCE,
    is_workflow_selection_request,
)
from ..routing.outcome_matching import (
    guidance_actions_for,
    match_outcome_hypotheses,
    named_workflow_action,
)
from .outcome_consistency import select_primary_hypothesis
from .extraction import _task_path

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
        _ui_text(
            f"{ACTION_DEFINITIONS[action].workflow} - "
            f"{ACTION_DEFINITIONS[action].memory_metadata.get('base_method', 'registered base method')}"
        )
        for action in registered_actions_for_family("lioness")
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
                    "The registered LIONESS variants require different inputs and "
                    "produce different network artifacts; choose the compatible variant."
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
    granularity = granularity_match.group(1).casefold() if granularity_match else None
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
    """Attach capability metadata without replacing the Router's selection.

    The only action override is a CLI-generated continuation marker. It represents
    an already approved pending plan, not a new interpretation of user language.
    """
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

    # Compatibility fallback for a legacy Router result with no typed outcome.
    # Evidence-bearing hypotheses take the registry-matcher path below instead.
    advisory_actions = [
        action
        for action in raw_decision.candidate_actions
        if action in LOCAL_WORKFLOW_ACTIONS
    ]
    if (
        is_workflow_selection_request(task)
        and not raw_decision.outcome_hypotheses
        and len(advisory_actions) > 1
    ):
        return raw_decision.model_copy(
            update={
                "action": "no_tool",
                "in_scope": True,
                "should_execute": False,
                "intent_type": "answer_question",
                "confidence": max(raw_decision.confidence, MIN_TOOL_CONFIDENCE),
                "reason": "The user asked which registered workflows are needed.",
                "capability_match_status": "exact",
                "matched_actions": [advisory_actions[-1]],
                "recommended_actions": advisory_actions,
                "alternative_actions": [],
                "mismatch_dimensions": [],
                "clarification_question": None,
                "missing_inputs": [],
            }
        )

    # A user-named executable workflow is stronger evidence than an incomplete
    # outcome hypothesis.  For example, PANDA is aggregate by definition;
    # do not turn an explicit "Run PANDA" request into a generic
    # aggregate/sample-specific question merely because the Router omitted
    # granularity.  Restrict this override to execution actions so conceptual
    # questions such as "What inputs does PANDA need?" remain informational.
    explicit_action = named_workflow_action(task)
    if (
        explicit_action is not None
        and explicit_action.startswith("run_")
        and (
            raw_decision.action.startswith("run_")
            or raw_decision.intent_type == "run_analysis"
        )
        and not re.search(r"PREVIOUS_ACTION=run_[a-z_]+", task, flags=re.IGNORECASE)
    ):
        return _ready_named_decision(
            raw_decision,
            explicit_action,
            should_execute=True,
            reason="The user explicitly named this executable NetZoo workflow.",
        )

    if raw_decision.outcome_hypotheses:
        match = match_outcome_hypotheses(raw_decision.outcome_hypotheses)
        primary = select_primary_hypothesis(raw_decision.outcome_hypotheses)
        decision = raw_decision.model_copy(
            update={
                "requested_outcome": primary.outcome if primary else None,
                "capability_match_status": match.status,
                "matched_actions": match.matched_actions,
                "hypothesis_actions": match.hypothesis_actions,
                "recommended_actions": (
                    guidance_actions_for(match.matched_actions[0])
                    if len(match.matched_actions) == 1
                    else []
                ),
                "alternative_actions": match.alternative_actions,
                "mismatch_dimensions": match.mismatch_dimensions,
                "clarification_question": match.clarification_question,
            }
        )
    else:
        decision = raw_decision.model_copy(deep=True)

    if is_workflow_selection_request(task) and decision.outcome_hypotheses:
        decision = decision.model_copy(
            update={
                "action": "no_tool",
                "in_scope": True,
                "should_execute": False,
                "intent_type": "answer_question",
                "missing_inputs": [],
            }
        )

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
            decision = TaskDecision.model_validate(repaired)
            return decision.model_copy(
                update={
                    "missing_inputs": [
                        field_name
                        for field_name in REQUIRED_INPUTS.get(action, ())
                        if field_name not in {"output_file", "lioness_output", "output_dir"}
                        and not getattr(decision, field_name, None)
                    ]
                }
            )

    if decision.clarification_question:
        return decision.model_copy(update={"action": "no_tool", "should_execute": False})
    return decision.model_copy(
        update={"should_execute": decision.action != "no_tool"}
    )
