"""Public summaries derived from validated transient semantic-goal facts."""

from __future__ import annotations

from ..contracts import TaskDecision
from ..routing.outcome_matching import guidance_actions_for
from workflow_registry import workflow_name


def classification_progress_detail(semantic_goal: dict, decision: TaskDecision) -> dict:
    """Return compact, fact-grounded classification facts for the live CLI."""
    outcome = decision.requested_outcome
    if outcome is None:
        outcome_label = "Requested outcome classified"
    elif outcome.artifact_type == "regulatory_network" and outcome.regulator_types:
        regulator_labels = {"tf": "TF", "mirna": "miRNA"}
        regulators = "/".join(
            regulator_labels.get(item, item) for item in outcome.regulator_types
        )
        outcome_label = f"{regulators} regulatory network"
    else:
        outcome_label = outcome.artifact_type.replace("_", " ")
    workflows = [
        workflow_name(action) for action in semantic_goal.get("candidates") or []
    ]
    return {
        "kind": "classification",
        "outcome": outcome_label,
        "workflows": list(dict.fromkeys(workflows)),
        "workflow_scope": (
            "final_result"
            if decision.action == "no_tool"
            and semantic_goal.get("request_mode") == "guidance"
            and workflows
            else "composition"
            if semantic_goal.get("relationship") == "composition"
            else "match"
        ),
    }


def next_step_progress_detail(decision: TaskDecision) -> dict:
    """Return public next-step facts without exposing private route reasoning."""
    if decision.clarification_question:
        return {
            "kind": "next_step",
            "status": "clarification_required",
            "question": decision.clarification_question,
            "tool_status": "No local tool has run yet.",
        }
    return {
        "kind": "next_step",
        "status": "execution_pending" if decision.should_execute else "guidance",
        "tool_status": (
            "Local tool execution is pending input validation."
            if decision.should_execute
            else "No local tool has run yet."
        ),
    }


def public_semantic_summary(semantic_goal: dict, decision: TaskDecision) -> str:
    candidates = semantic_goal.get("candidates") or []
    unresolved = semantic_goal.get("unresolved_dimensions") or []
    relationship = semantic_goal.get("relationship")
    match_status = semantic_goal.get("match_status")
    display_candidates = [workflow_name(action) for action in candidates]
    goal = semantic_goal.get("goal") or ""
    if match_status == "unsupported":
        return (
            "The requested outcome does not exactly match a registered workflow; "
            "related capabilities remain alternatives only."
        )
    if match_status == "ambiguous":
        return (
            "The requested outcome needs one clarification before workflow selection."
        )
    if match_status == "exact" and display_candidates:
        if relationship == "composition":
            return (
                "I found a registered workflow composition for this goal: "
                f"{' → '.join(display_candidates)}."
            )
        return (
            "I found an exact registered workflow for this goal: "
            f"{display_candidates[-1]}."
        )
    if candidates and unresolved:
        prefix = (
            f"Goal: {goal} "
            if goal
            else "I found multiple registered approaches for this goal. "
        )
        return f"{prefix}Candidates: {', '.join(display_candidates)}. I still need: {', '.join(unresolved)}."
    if candidates:
        if relationship == "composition":
            return f"I found a registered workflow composition for this goal: {' → '.join(display_candidates)}."
        prefix = (
            f"Goal: {goal} "
            if goal
            else "I found registered approaches that fit this goal. "
        )
        return f"{prefix}Candidates: {', '.join(display_candidates)}."
    if decision.action == "no_tool":
        return "This request does not need files or tool execution."
    return "I selected a registered workflow before proceeding."


def semantic_summary_detail(semantic_goal: dict, decision: TaskDecision) -> dict:
    return {
        "kind": "semantic_goal",
        "text": public_semantic_summary(semantic_goal, decision),
    }


def outcome_routing_state(
    decision: TaskDecision,
    goal: str = "",
    request_mode: str = "unknown",
) -> dict:
    """Build graph state from the deterministic capability-match decision."""
    if decision.recommended_actions:
        candidates = list(decision.recommended_actions)
        relationship = "composition" if len(candidates) > 1 else "single"
    elif len(decision.hypothesis_actions) == 1:
        candidates = guidance_actions_for(decision.hypothesis_actions[0])
        relationship = "composition" if len(candidates) > 1 else "single"
    else:
        candidates = list(decision.hypothesis_actions)
        relationship = "alternatives" if len(candidates) > 1 else "single"
    semantic_goal = {
        "goal": goal,
        "candidates": candidates,
        "unresolved_dimensions": (
            list(decision.requested_outcome.unresolved_dimensions)
            if decision.requested_outcome
            else []
        ),
        "relationship": relationship,
        "match_status": decision.capability_match_status,
        "request_mode": request_mode,
    }
    return {
        "semantic_goal": semantic_goal,
        "requested_outcome": (
            decision.requested_outcome.model_dump()
            if decision.requested_outcome
            else None
        ),
        "outcome_hypotheses": [
            item.model_dump() for item in decision.outcome_hypotheses
        ],
        "capability_match": {
            "status": decision.capability_match_status,
            "matched_actions": decision.matched_actions,
            "hypothesis_actions": decision.hypothesis_actions,
            "alternative_actions": decision.alternative_actions,
            "mismatch_dimensions": decision.mismatch_dimensions,
            "clarification_question": decision.clarification_question,
        },
    }
