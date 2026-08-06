"""Repair router decisions against deterministic workflow authority."""

from __future__ import annotations

import re

from workflow_registry import LOCAL_WORKFLOW_ACTIONS, REQUIRED_INPUTS

from ..contracts import (
    InputEvidence,
    LIONESS_MODE_QUESTION,
    TaskDecision,
    WorkflowPlan,
    _is_demo_request,
    _ui_text,
)
from ..routing import (
    MIN_TOOL_CONFIDENCE,
    has_direct_execution_intent,
    infer_advisory_capabilities,
    infer_goal_capabilities,
    inferred_execution_action,
    is_workflow_information_request,
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


def repair_router_decision(raw_decision: TaskDecision, task: str) -> TaskDecision:
    """Repair under-routing while keeping execution tied to a recognized user goal."""
    normalized = task.casefold()
    inferred_recommendations = infer_goal_capabilities(task)
    recommendations = inferred_recommendations or raw_decision.recommended_actions
    if recommendations != raw_decision.recommended_actions:
        raw_decision = raw_decision.model_copy(
            update={"recommended_actions": recommendations}
        )

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
            recommended_actions=recommendations,
            preference_updates=raw_decision.preference_updates,
        )

    if is_workflow_information_request(task):
        named_recommendations = infer_advisory_capabilities(task)
        if not named_recommendations:
            named_recommendations = list(recommendations)
        if not named_recommendations:
            if "lioness" in normalized and "puma" in normalized:
                named_recommendations = ["run_puma", "run_lioness_puma"]
            elif "lioness" in normalized and "panda" in normalized:
                named_recommendations = ["run_panda", "run_lioness_panda"]
            elif "lioness" in normalized and re.search(
                r"(co[- _]?expression|coexpression|共表現|共同表現)", normalized
            ):
                named_recommendations = ["run_lioness_coexpression"]
            elif "puma" in normalized:
                named_recommendations = ["run_puma"]
            elif "panda" in normalized:
                named_recommendations = ["run_panda"]
            elif "condor" in normalized:
                named_recommendations = ["run_condor"]
        return TaskDecision(
            action="no_tool",
            in_scope=True,
            should_execute=False,
            intent_type="answer_question",
            confidence=max(raw_decision.confidence, MIN_TOOL_CONFIDENCE),
            reason="The request asks for stable workflow requirements or usage guidance.",
            recommended_actions=named_recommendations,
            preference_updates=raw_decision.preference_updates,
        )

    continuation_match = re.search(
        r"PREVIOUS_ACTION=(run_[a-z_]+)", task, flags=re.IGNORECASE
    )
    if continuation_match:
        action = continuation_match.group(1).casefold()
        if action in LOCAL_WORKFLOW_ACTIONS:
            repaired = raw_decision.model_dump()
            repaired.update(
                {
                    "action": action,
                    "in_scope": True,
                    "should_execute": True,
                    "confidence": max(raw_decision.confidence, MIN_TOOL_CONFIDENCE),
                    "reason": (
                        "Continuing a pending workflow; the previous action marker "
                        "overrides any router reclassification."
                    ),
                }
            )
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

    inferred_action = inferred_execution_action(task)
    if (
        inferred_action
        and has_direct_execution_intent(task)
        and raw_decision.action != inferred_action
        and (raw_decision.action == "no_tool" or raw_decision.action in recommendations)
    ):
        repaired = raw_decision.model_dump()
        repaired.update(
            {
                "action": inferred_action,
                "in_scope": True,
                "should_execute": True,
                "intent_type": "demo_run" if _is_demo_request(task) else "run_analysis",
                "confidence": max(raw_decision.confidence, MIN_TOOL_CONFIDENCE),
                "reason": (
                    "The requested deliverable maps to an allow-listed local workflow; "
                    "the user does not need to know or name the tool in advance."
                ),
                "recommended_actions": recommendations,
            }
        )
        repaired["missing_inputs"] = [
            field_name
            for field_name in REQUIRED_INPUTS[inferred_action]
            if not repaired.get(field_name)
        ]
        return TaskDecision.model_validate(repaired)

    if raw_decision.action != "no_tool":
        return raw_decision

    if is_workflow_information_request(task):
        return raw_decision.model_copy(
            update={
                "intent_type": "answer_question",
                "should_execute": False,
            }
        )

    run_intent = re.search(
        r"(run|execute|trial|test|demo|試跑|執行|跑|跑一次|測試|做測試|示範|分析)",
        normalized,
        flags=re.IGNORECASE,
    )
    lioness_action = None
    if "lioness" in normalized and run_intent:
        if "panda" in normalized:
            lioness_action = "run_lioness_panda"
        elif "puma" in normalized:
            lioness_action = "run_lioness_puma"
        elif re.search(
            r"(co[- _]?expression|coexpression|共表現|共同表現)",
            normalized,
            flags=re.IGNORECASE,
        ):
            lioness_action = "run_lioness_coexpression"
    if lioness_action:
        repaired = raw_decision.model_dump()
        repaired.update(
            {
                "action": lioness_action,
                "in_scope": True,
                "should_execute": True,
                "confidence": max(raw_decision.confidence, MIN_TOOL_CONFIDENCE),
                "reason": (
                    "Explicit LIONESS mode and run/test request; the Planner will "
                    "resolve inputs or ask for missing data."
                ),
            }
        )
        repaired["missing_inputs"] = [
            field_name
            for field_name in REQUIRED_INPUTS[lioness_action]
            if not repaired.get(field_name)
        ]
        return TaskDecision.model_validate(repaired)

    condor_run_intent = "condor" in normalized and re.search(
        r"(run|execute|trial|test|試跑|執行|跑|跑一次|測試|做測試|分析|community|module|社群|模組)",
        normalized,
        flags=re.IGNORECASE,
    )
    if not condor_run_intent:
        return raw_decision

    return TaskDecision(
        action="run_condor",
        in_scope=True,
        should_execute=True,
        confidence=max(raw_decision.confidence, MIN_TOOL_CONFIDENCE),
        reason=(
            "Explicit CONDOR run/test request; the Planner will resolve demo inputs "
            "or ask for missing paths."
        ),
        network_file=_task_path(task, "network_file"),
        output_dir=_task_path(task, "output_dir"),
        prefix=raw_decision.prefix,
        missing_inputs=["network_file", "output_dir"],
        recommended_actions=recommendations,
        preference_updates=raw_decision.preference_updates,
    )
