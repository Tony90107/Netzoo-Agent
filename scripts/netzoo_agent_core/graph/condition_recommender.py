"""Advisory experimental-condition recommendation among tied workflows (Log 139).

When compatible workflows produce the same result and differ only in method,
the tag discriminator offers method jargon the user never writes. This stage
offers the study facts that separate the candidates instead -- sample count,
per-edge confidence, compute limits -- and asks the model which of them the
request states, with a quote. The deterministic part decides:

- every claim must be an offered condition with a quote grounded in the request;
- the grounded claims must point to exactly one candidate, or nothing is
  recommended and the user is asked the separating questions instead.

A recommendation is advice. It never changes ``action``, ``should_execute``,
``capability_match_status`` or ``matched_actions``; executing still requires
the user to choose.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from workflow_registry import ACTION_DEFINITIONS, OUTPUT_CAPABILITIES, SELECTION_AXES

from ..contracts import AgentState, LLMUsage, TaskDecision
from ..contracts.outcomes import (
    AdvisoryCondition,
    AdvisoryRecommendation,
    SelectionConditionClaims,
)
from ..interpretation.concept_answers import _TWO_GROUP_COMPARISON_PATTERN
from ..interpretation.outcome_validation import (
    _grounded_span,
    _hard_wrap_normalized,
    _normalized,
)
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..llm import append_llm_usage, build_selection_condition_messages
from ..routing.clarification_planner import plan_clarification
from .context import _GraphContext, preflight_budget, record_event
from .structured_calls import _serialized_structured_input, _validation_issue_types

__all__ = [
    "ConditionOption",
    "condition_options",
    "invoke_condition_recommender",
    "is_method_tie",
    "recommend_from_claims",
    "separating_question",
]

_MAX_QUESTIONS = 2


@dataclass(frozen=True, slots=True)
class ConditionOption:
    axis: str
    value: str
    label: str
    actions: tuple[str, ...]

    @property
    def condition(self) -> str:
        return f"{self.axis}:{self.value}"


def _workflow_name(action: str) -> str:
    definition = ACTION_DEFINITIONS.get(action)
    return definition.workflow if definition is not None else action


def condition_options(candidates: list[str]) -> list[ConditionOption]:
    """Conditions that separate the candidates, in axis order.

    A single-valued axis ("the network is large") separates when some but not
    all candidates are preferred under it. A multi-valued axis separates only
    when every candidate declares a value on it: a candidate silent on the axis
    is equally suitable under any value, so "no covariates" does not favour
    LIONESS over BONOBO even though LIONESS declares it.
    """
    preferring: dict[str, list[str]] = {}
    declared_axes: dict[str, set[str]] = {}
    for action in candidates:
        capability = OUTPUT_CAPABILITIES.get(action)
        for condition in (capability.prefer_when if capability else ()):
            preferring.setdefault(condition, []).append(action)
            declared_axes.setdefault(condition.partition(":")[0], set()).add(action)
    options = []
    for axis, spec in SELECTION_AXES.items():
        multi_valued = len(spec["values"]) > 1
        if multi_valued and declared_axes.get(axis, set()) != set(candidates):
            continue
        for value, label in spec["values"].items():
            actions = preferring.get(f"{axis}:{value}", [])
            if 0 < len(actions) < len(candidates):
                options.append(ConditionOption(axis, value, label, tuple(actions)))
    return options


def is_method_tie(decision: TaskDecision) -> bool:
    """Same result, different method: the planner can only ask about the algorithm."""
    candidates = list(decision.hypothesis_actions)
    if decision.capability_match_status != "ambiguous" or len(candidates) < 2:
        return False
    plan = plan_clarification(
        candidates,
        outcomes=[item.outcome for item in decision.outcome_hypotheses],
    )
    return plan is not None and plan.dimension == "algorithm"


def _beginner_group_guidance_applies(task: str, decision: TaskDecision) -> bool:
    """Leave the existing two-group comparison guidance untouched."""
    outcome = decision.requested_outcome
    return bool(
        outcome is not None
        and outcome.artifact_type == "regulatory_network"
        and "run_panda" in decision.hypothesis_actions
        and _TWO_GROUP_COMPARISON_PATTERN.search(task)
    )


def _quote_grounded(task: str, span: str) -> bool:
    normalized = _normalized(span or "")
    if not normalized:
        return False
    variants = tuple(dict.fromkeys((_normalized(task), _hard_wrap_normalized(task))))
    return any(_grounded_span(normalized, variant) for variant in variants)


def recommend_from_claims(
    user_task: str,
    claims: SelectionConditionClaims,
    options: list[ConditionOption],
    candidates: list[str],
) -> tuple[AdvisoryRecommendation | None, list[dict]]:
    """Return the recommendation, if any, and every rejected claim with its reason."""
    offered = {option.condition: option for option in options}
    accepted: list[tuple[ConditionOption, str]] = []
    rejected: list[dict] = []
    for claim in claims.claims:
        option = offered.get(claim.condition)
        if option is None:
            rejected.append({"condition": claim.condition, "reason": "not_offered"})
        elif not _quote_grounded(user_task, claim.text_span):
            rejected.append({"condition": claim.condition, "reason": "quote_not_in_request"})
        else:
            accepted.append((option, claim.text_span))
    if not accepted:
        return None, rejected
    remaining = set(candidates)
    for option, _ in accepted:
        remaining &= set(option.actions)
    if len(remaining) != 1:
        return None, [*rejected, {"condition": None, "reason": "claims_do_not_select_one"}]
    action = next(iter(remaining))
    return AdvisoryRecommendation(
        action=action,
        conditions=[
            AdvisoryCondition(axis=option.axis, value=option.value, text_span=span)
            for option, span in accepted
        ],
    ), rejected


def separating_question(
    options: list[ConditionOption],
    candidates: list[str] | None = None,
) -> str:
    """Form B: ask the study facts that separate the candidates, not method names."""
    questions = []
    covered: set[str] = set()
    for axis in dict.fromkeys(option.axis for option in options):
        axis_options = [option for option in options if option.axis == axis]
        single_valued = len(SELECTION_AXES[axis]["values"]) == 1
        answers = "; ".join(
            ("yes" if single_valued else option.label)
            + " → " + ", ".join(_workflow_name(a) for a in option.actions)
            for option in axis_options
        )
        covered.update(a for option in axis_options for a in option.actions)
        questions.append(f"{SELECTION_AXES[axis]['question']} ({answers})")
        if len(questions) == _MAX_QUESTIONS:
            break
    numbered = " ".join(f"({index}) {text}" for index, text in enumerate(questions, 1))
    lead = "Both fit" if candidates is not None and len(candidates) == 2 else "These all fit"
    text = f"{lead}; to choose, tell me: {numbered}"
    uncovered = [a for a in (candidates or []) if a not in covered]
    if uncovered:
        text += " If none of these applies: " + ", ".join(_workflow_name(a) for a in uncovered) + "."
    return text


def recommendation_question(recommendation: AdvisoryRecommendation) -> str:
    return (
        f"Should I use {_workflow_name(recommendation.action)}, or does another "
        "listed option fit your study better?"
    )


def invoke_condition_recommender(
    context: _GraphContext,
    state: AgentState,
    user_task: str,
    decision: TaskDecision,
    usage: LLMUsage,
    budget_warnings: list[str],
):
    """Attach an advisory recommendation or a separating question to a method tie."""
    llm = getattr(context, "selection_condition_llm", None)
    if (
        llm is None
        or getattr(context, "semantic_claims", False)
        or not is_method_tie(decision)
        or _beginner_group_guidance_applies(user_task, decision)
    ):
        return decision, usage, budget_warnings
    candidates = list(decision.hypothesis_actions)
    options = condition_options(candidates)
    if not options:
        return decision, usage, budget_warnings
    messages = build_selection_condition_messages(
        user_task, [(option.condition, option.label) for option in options],
    )
    input_text = _serialized_structured_input(messages, SelectionConditionClaims)
    semantic_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
    budget, budget_warnings = preflight_budget(
        context, semantic_state, role="selection_conditions",
        model=context.semantic_model_name, input_text=input_text,
        reserved_output_tokens=context.router_max_tokens, allow_reserve=False,
    )
    if budget.status == "blocked":
        usage.budget_exhausted = True
        return decision, usage, budget_warnings
    fallback = decision.model_copy(update={
        "clarification_question": separating_question(options, candidates),
    })
    started_ns = time.monotonic_ns()
    raw = None
    payload = None
    output_text = ""
    call_status = "failed"
    try:
        record_event(context, state, "routing.selection_conditions_started", "classify", {
            "candidate_actions": candidates,
            "offered_conditions": [option.condition for option in options],
        })
        adapter = llm.with_structured_output(
            SelectionConditionClaims, method="function_calling", include_raw=True,
        )
        payload, raw = semantic_payload(adapter.invoke(messages))
        claims = SelectionConditionClaims.model_validate(payload)
        output_text = claims.model_dump_json()
        call_status = "success"
        recommendation, rejected = recommend_from_claims(
            user_task, claims, options, candidates,
        )
        if recommendation is None:
            record_event(context, state, "routing.selection_conditions_unresolved", "classify", {
                "claims": [item.model_dump() for item in claims.claims],
                "rejected": rejected,
                "candidate_actions": candidates,
            })
            return fallback, usage, budget_warnings
        record_event(context, state, "routing.selection_conditions_recommended", "classify", {
            "recommended_action": recommendation.action,
            "conditions": [item.model_dump() for item in recommendation.conditions],
            "rejected": rejected,
            "candidate_actions": candidates,
        })
        return decision.model_copy(update={
            "advisory_recommendation": recommendation,
            "clarification_question": recommendation_question(recommendation),
        }), usage, budget_warnings
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        record_event(context, state, "routing.selection_conditions_failed", "classify", {
            "error_type": type(error).__name__,
            "error_message": str(error)[:2000],
            "validation_issues": _validation_issue_types(error),
            "provider_payload": payload,
            "candidate_actions": candidates,
        })
        return fallback, usage, budget_warnings
    finally:
        usage = append_llm_usage(
            usage, role="selection_conditions", model=context.semantic_model_name,
            response=raw, input_text=input_text, output_text=output_text,
            budget_tokens=context.task_token_budget,
            duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000),
            status=call_status, price_catalog=context.price_catalog,
        )
