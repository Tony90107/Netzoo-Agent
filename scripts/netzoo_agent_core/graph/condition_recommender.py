"""Advisory experimental-condition recommendation among tied workflows (Log 139).

When compatible workflows produce the same result and differ only in method,
the tag discriminator offers method jargon the user never writes. This stage
offers the study facts that separate the candidates instead -- sample count,
per-edge confidence, compute limits -- and asks the model which of them the
request states, with a quote. The deterministic part decides:

- every claim must be an offered condition with a quote grounded in the request;
- grounded study conditions take priority; otherwise the model may rank the
  offered philosophies using request quotes or stated conditional assumptions.
- conflicting study conditions are clarified rather than overridden by advice.

A recommendation is advice. It never changes ``action``, ``should_execute``,
``capability_match_status`` or ``matched_actions``; executing still requires
the user to choose.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Literal
from pydantic import ConfigDict, Field, create_model

from workflow_registry import ACTION_DEFINITIONS, OUTPUT_CAPABILITIES, REQUIRED_INPUTS, SELECTION_AXES

from ..contracts import AgentState, LLMUsage, TaskDecision
from ..contracts.outcomes import (
    AdvisoryCondition,
    AdvisoryRecommendation,
    ConditionClaim,
    MethodCapabilityGap,
    MethodPreference,
    SelectionConditionClaims,
)
from ..interpretation.outcome_validation import (
    _grounded_span,
    _hard_wrap_normalized,
    _normalized,
)
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.method_philosophy import method_philosophies_for
from ..presentation import _NON_ENGLISH
from ..interpretation.semantic_repair import semantic_payload
from ..llm import append_llm_usage, build_selection_condition_messages
from ..routing.clarification_planner import plan_clarification
from ..routing.clarification_planner import algorithmic_assumptions_for
from ..interpretation.input_bindings import request_input_bindings
from .context import _GraphContext, preflight_budget, record_event
from .input_inspection import _ROLE_LABELS, named_directories
from .structured_calls import _serialized_structured_input, _validation_issue_types

__all__ = [
    "ConditionOption",
    "condition_options",
    "invoke_condition_recommender",
    "is_divergent_reading_tie",
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


def is_divergent_reading_tie(decision: TaskDecision) -> bool:
    """Readings that differ in what is produced (Log 150), each leading to a workflow.

    Case 4 read "each patient's regulatory wiring ... per-TF regulatory strength"
    both as one TF-gene network per sample (LIONESS-PANDA) and as TF activity per
    sample (GIRAFFE). The inputs are the same, so the folder cannot separate
    them; the study fact that does is which per-sample quantity the user needs
    (Log 200). The readings' own question is kept when no fact is stated.
    """
    artifacts = {item.outcome.artifact_type for item in decision.outcome_hypotheses} - {"unknown"}
    return (
        decision.capability_match_status == "ambiguous"
        and len(decision.hypothesis_actions) >= 2
        and len(artifacts) >= 2
    )


def _same_subject_choice(decision: TaskDecision) -> bool:
    """Offer conditional advice on method/role choices, never unknown results."""
    outcome = decision.requested_outcome
    return bool(
        outcome is not None
        and outcome.artifact_type != "unknown"
        and outcome.granularity in {"aggregate", "sample_specific"}
        and decision.capability_match_status == "ambiguous"
        and len(decision.hypothesis_actions) >= 2
        and all(
            outcome.granularity in OUTPUT_CAPABILITIES[action].granularities
            and outcome.artifact_type in (
                OUTPUT_CAPABILITIES[action].produced_artifacts
                | {OUTPUT_CAPABILITIES[action].artifact_type}
            )
            for action in decision.hypothesis_actions
            if action in OUTPUT_CAPABILITIES
        )
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
        elif (witness := SELECTION_AXES[option.axis].get("witness")) and not re.search(witness, claim.text_span, re.I):
            # Log 300: a verbatim quote proves the words occurred, not that they
            # state this condition; an axis with a witness needs it in the request.
            rejected.append({"condition": claim.condition, "reason": "condition_not_in_request"})
        else:
            accepted.append((option, claim.text_span))
    if not accepted:
        return None, rejected
    remaining = set(candidates)
    for option, _ in accepted:
        remaining &= set(option.actions)
    # A base and its per-sample extensions are one method at two scales
    # (Log 269): start from the base; the extension stays a listed option.
    bases = [a for a in remaining
             if not set(OUTPUT_CAPABILITIES[a].guidance_predecessors) & remaining] if remaining else []
    if len(remaining) > 1 and len(bases) == 1 and all(
        bases[0] in OUTPUT_CAPABILITIES[a].guidance_predecessors for a in remaining - set(bases)
    ):
        remaining = set(bases)
    if len(remaining) != 1:
        return None, [*rejected, {"condition": None, "reason": "claims_do_not_select_one"}]
    action = next(iter(remaining))
    confirm = [SELECTION_AXES[option.axis].get("confirm", {}).get(option.value) for option, _ in accepted]
    return AdvisoryRecommendation(
        action=action,
        conditions=[
            AdvisoryCondition(axis=option.axis, value=option.value, text_span=span)
            for option, span in accepted
        ],
        assumptions=[text for text in dict.fromkeys(confirm) if text],
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


def _candidate_facts(candidates, context) -> list[dict]:
    """Compare the registry's philosophy and boundary, never inferred capabilities."""
    workflows = getattr(getattr(context, "project_policy", None), "workflows", {})
    facts = []
    for action in candidates:
        spec = workflows.get(action)
        definition = ACTION_DEFINITIONS.get(action)
        capability = (spec.output_capability if spec else OUTPUT_CAPABILITIES.get(action))
        if capability is None or definition is None:
            continue
        facts.append({
            "action": action, "workflow": _workflow_name(action),
            "description": getattr(spec, "description", ""),
            "artifact_type": capability.artifact_type,
            "granularities": sorted(capability.granularities),
            "selection_tags": sorted(capability.selection_tags),
            "regulator_types": sorted(capability.regulator_types),
            "method_premises": list(algorithmic_assumptions_for(capability.selection_tags)),
            "mathematical_interpretation": list(method_philosophies_for(capability.selection_tags)),
            "required_inputs": list(getattr(spec, "required_inputs", definition.required_inputs)),
            "guidance_notes": list(capability.guidance_notes),
            "boundary": capability.handoff_contract,
        })
    return facts


def unestablished_inputs(task, action, requested_outcome=None) -> list[str]:
    """Input roles the workflow requires that the request does not establish (Log 259).

    Established means a file the request binds to that role, or the typed
    current input `expression_matrix`. Priors are executor prerequisites, not
    ontology values, so only a bound file establishes them.
    """
    bound = set(request_input_bindings(task).values)
    if requested_outcome is not None and "expression_matrix" in requested_outcome.input_artifacts:
        bound.add("expression_file")
    return [role for role in REQUIRED_INPUTS.get(action, ()) if role in _ROLE_LABELS and role not in bound]


def _defers_to_named_inputs(task, recommendation, requested_outcome) -> bool:
    """Quoted facts > folder contents > a bare model preference (Log 259).

    A preference whose workflow needs inputs the request has not established
    must not pre-empt the content check of a file or folder the request names.
    """
    return bool(unestablished_inputs(task, recommendation.action, requested_outcome)
                and named_directories(task))


def _recommend_from_preference(task, preference, candidate_facts, requested_outcome=None):
    """Advisory only: reject added actions, invented method signals and false quotes."""
    if preference is None:
        return None
    facts = {item["action"]: item for item in candidate_facts}
    selected = facts.get(preference.action)
    if selected is None or not set(preference.selection_tags) <= set(selected["selection_tags"]):
        return None
    if any(not _quote_grounded(task, span) for span in preference.text_spans):
        return None
    # Model prose may copy Chinese evidence into English explanations. Preserve
    # original quotes only in supporting_spans; never crash deterministic UI.
    rationale = preference.rationale
    assumptions = list(preference.assumptions)
    if _NON_ENGLISH.search(rationale):
        rationale = "A conditional starting method based on its registered premises, inputs and output."
    if any(_NON_ENGLISH.search(item) for item in assumptions):
        assumptions = [
            item for item in assumptions if not _NON_ENGLISH.search(item)
        ] + ["Confirm that the biological scope and required inputs listed below match your study."]
    roles = selected.get("regulator_types", [])
    if roles and requested_outcome and not (set(requested_outcome.regulator_types) - {"unknown"}):
        labels = {"tf": "transcription factors", "mirna": "miRNA regulators"}
        assumptions.insert(0, "This starting choice assumes a regulator scope of "
                           + ", ".join(labels.get(role, role) for role in roles)
                           + "; confirm this scope before analysis.")
    if missing := unestablished_inputs(task, preference.action, requested_outcome):
        # Never let model prose imply the inputs are in hand (Log 259).
        needed = " and ".join(_ROLE_LABELS[role] for role in missing)
        article = "an" if needed[0] in "aeiou" else "a"
        assumptions.insert(1 if roles and assumptions and assumptions[0].startswith("This starting choice")
                           else 0, f"It also needs {article} {needed}, which the request does not mention.")
    return AdvisoryRecommendation(
        action=preference.action, rationale=rationale,
        supporting_spans=preference.text_spans, assumptions=assumptions[:4],
    )


def _misplaced_condition_claims(task, review, options, claims) -> list[ConditionClaim]:
    """Offered condition ids the model wrote as a philosophy, with their quote (Log 271).

    The model's own claim and quote, moved to the field that is checked: it
    still passes every check of `recommend_from_claims`. Nothing is added that
    the model did not write.
    """
    offered = {option.condition for option in options}
    claimed = {claim.condition for claim in claims.claims}
    quote = review.requirement_quote or ""
    if not quote or not _quote_grounded(task, quote):
        return []
    return [ConditionClaim(condition=item, text_span=quote)
            for item in dict.fromkeys(review.requested_philosophy)
            if item in offered and item not in claimed][:max(0, 6 - len(claims.claims))]


_RESULT_DIMENSIONS = frozenset({"artifact_type", "entity_type", "regulator_type", "target_type", "granularity"})


def _quotes_the_result(gap, readings) -> bool:
    """A required philosophy is stated apart from the result it qualifies (Log 285).

    The words that ask for a per-patient network are not a request for Bayesian
    inference, so a gap whose only quote grounds the typed result is unsupported.
    """
    spans = {_normalized(item.text_span) for reading in readings for item in reading.evidence
             if item.text_span and item.dimension in _RESULT_DIMENSIONS}
    quotes = {_normalized(span) for span in gap.text_spans}
    return any(q and s and (q in s or s in q) for q in quotes for s in spans)


def _validated_capability_gap(task, gap, candidate_facts, readings=()):
    if gap is None or not candidate_facts:
        return None
    registered = set().union(*(item.selection_tags for item in OUTPUT_CAPABILITIES.values()))
    required = set(gap.selection_tags)
    if not required <= registered or any(
        required <= set(item["selection_tags"]) for item in candidate_facts
    ) or any(not _quote_grounded(task, span) for span in gap.text_spans) or _quotes_the_result(gap, readings):
        return None
    if _NON_ENGLISH.search(gap.rationale):
        gap = gap.model_copy(update={"rationale":
            "No qualified registered workflow declares the requested combination of method signals."})
    return gap


def _condition_schema(options):
    """Constrain extraction to offered study facts, including an empty offer."""
    offered_claim = create_model(
        "OfferedConditionClaim", __base__=ConditionClaim,
        condition=(Literal[tuple(option.condition for option in options)], ...),
    ) if options else ConditionClaim
    return create_model(
        "MethodComparisonReview", __config__=ConfigDict(extra="forbid"),
        requested_philosophy=(list[str], Field(default_factory=list, max_length=8, description=(
            "Registered method signals the user REQUIRES, before picking candidates. "
            "Probabilistic quantification of uncertainty is bayesian, even for motif priors. "
            "Do not restrict requirements to tags present in candidate methods. "
            "Use [] when no mathematical philosophy is required."
        ))),
        requirement_quote=(str | None, Field(default=None, max_length=300, description=(
            "Exact user quote requiring that philosophy; null if none is required."
        ))),
        capability_gap=(MethodCapabilityGap | None, Field(default=None, description=(
            "Missing required mathematical philosophy. Regulatory message passing/optimization "
            "cannot quantify Bayesian motif-prior reliability; report that gap if requested."
        ))),
        preference=(MethodPreference | None, Field(default=None, description=(
            "One best qualified starting method with English rationale and conditional assumptions. "
            "Null when the required philosophy is unavailable."
        ))),
        claims=(list[offered_claim], Field(default_factory=list, max_length=6 if options else 0)),
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
    method_tie = is_method_tie(decision)
    divergent = not method_tie and is_divergent_reading_tie(decision)
    same_subject = _same_subject_choice(decision)
    if (
        llm is None
        or not (method_tie or divergent or same_subject)
    ):
        return decision, usage, budget_warnings
    candidates = list(decision.hypothesis_actions)
    options = condition_options(candidates)
    candidate_facts = _candidate_facts(candidates, context)
    if not options and not candidate_facts:
        return decision, usage, budget_warnings
    messages = build_selection_condition_messages(
        user_task, [(option.condition, option.label) for option in options],
        candidate_facts,
    )
    schema = _condition_schema(options)
    input_text = _serialized_structured_input(messages, schema)
    semantic_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
    budget, budget_warnings = preflight_budget(
        context, semantic_state, role="selection_conditions",
        model=context.semantic_model_name, input_text=input_text,
        reserved_output_tokens=context.router_max_tokens, allow_reserve=False,
    )
    if budget.status == "blocked":
        usage.budget_exhausted = True
        return decision, usage, budget_warnings
    # Divergent readings keep their own question (Log 188) when nothing is stated.
    fallback = decision if not method_tie or not options else decision.model_copy(update={
        "clarification_question": separating_question(options, candidates),
    })
    started_ns = time.monotonic_ns()
    raw = None
    payload = None
    output_text = ""
    call_status = "failed"
    try:
        record_event(context, state, "routing.selection_conditions_started", "classify", {
            "tie": "divergent_readings" if divergent else "method",
            "candidate_actions": candidates,
            "offered_conditions": [option.condition for option in options],
        })
        adapter = llm.with_structured_output(
            schema, method="function_calling", include_raw=True,
        )
        payload, raw = semantic_payload(adapter.invoke(messages))
        if isinstance(payload, dict):
            # Some providers echo an unused empty top-level field from a nested
            # schema. It adds no claim. Keep nonempty unknown fields forbidden.
            payload = {
                key: value for key, value in payload.items()
                if key in schema.model_fields or value not in (None, "", [], {})
            }
        review = schema.model_validate(payload)
        claims = SelectionConditionClaims.model_validate(review.model_dump(exclude={
            "requested_philosophy", "requirement_quote",
        }))
        output_text = claims.model_dump_json()
        call_status = "success"
        if misplaced := _misplaced_condition_claims(user_task, review, options, claims):
            claims = claims.model_copy(update={"claims": [*claims.claims, *misplaced]})
            record_event(context, state, "routing.selection_conditions_salvaged", "classify", {
                "claims": [item.model_dump() for item in misplaced],
            })
        required_gap = None
        if review.requested_philosophy and review.requirement_quote:
            required_gap = MethodCapabilityGap(
                selection_tags=review.requested_philosophy,
                text_spans=[review.requirement_quote],
                rationale="No qualified registered workflow declares the requested mathematical philosophy for this scientific result.",
            )
        readings = decision.outcome_hypotheses
        gap = (_validated_capability_gap(user_task, required_gap, candidate_facts, readings)
               or _validated_capability_gap(user_task, claims.capability_gap, candidate_facts, readings))
        # Recorded only where the result quote is what rejects an otherwise valid gap.
        if quoted := [item.model_dump() for item in (required_gap, claims.capability_gap)
                      if _validated_capability_gap(user_task, item, candidate_facts) is not None
                      and _quotes_the_result(item, readings)]:
            record_event(context, state, "routing.capability_gap_quotes_result", "classify", {"gaps": quoted})
        if gap is not None:
            record_event(context, state, "routing.method_capability_gap", "classify", gap.model_dump())
            return decision.model_copy(update={
                "advisory_capability_gap": gap,
                "clarification_question": "Would you accept a different modeling philosophy among these related methods, or do you need the unavailable method?",
            }), usage, budget_warnings
        recommendation, rejected = recommend_from_claims(
            user_task, claims, options, candidates,
        )
        if recommendation is not None and claims.preference is not None:
            explained = _recommend_from_preference(
                user_task, claims.preference, candidate_facts, decision.requested_outcome,
            )
            if explained is not None and explained.action == recommendation.action:
                # The quoted condition chooses the method. A separately grounded
                # model explanation may explain *why* it addresses this question,
                # but cannot change that choice or authorize execution.
                recommendation = recommendation.model_copy(update={
                    "rationale": explained.rationale,
                    # An axis's confirmation (Log 269) is never replaced by model prose.
                    "assumptions": list(dict.fromkeys(
                        [*recommendation.assumptions, *explained.assumptions]))[:4],
                    "supporting_spans": explained.supporting_spans,
                })
        if recommendation is None and not rejected:
            recommendation = _recommend_from_preference(
                user_task, claims.preference, candidate_facts, decision.requested_outcome,
            )
            if recommendation is not None and _defers_to_named_inputs(
                user_task, recommendation, decision.requested_outcome,
            ):
                record_event(context, state, "routing.preference_deferred_to_inputs", "classify", {
                    "preferred_action": recommendation.action,
                    "unestablished_inputs": unestablished_inputs(
                        user_task, recommendation.action, decision.requested_outcome,
                    ),
                    "candidate_actions": candidates,
                })
                return fallback, usage, budget_warnings
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
            "rationale": recommendation.rationale,
            "assumptions": recommendation.assumptions,
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
