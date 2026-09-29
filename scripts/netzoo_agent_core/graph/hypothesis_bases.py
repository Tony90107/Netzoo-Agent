"""Preserve research alternatives before advisory ranking, across the registry.

One bounded advisory call examines the original question, independently of the
classifier's chosen endpoint. Its route labels are conditional guidance, never
execution authority. All method descriptions and input requirements come from
the registry. Practical concerns share this call. When it finds one goal, the
method stage may still make its own call (Log 257, `framing_yielded`).
"""

from __future__ import annotations

import re
import time

from pydantic import BaseModel
from workflow_registry import (
    ACTION_DEFINITIONS,
    OUTPUT_CAPABILITIES,
    GUIDANCE_COMPOSITIONS,
)

from ..contracts.outcomes import StatedHypothesis, StatedConcernClaims
from ..contracts.artifact_semantics import ARTIFACT_SEMANTICS
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..llm import append_llm_usage
from ..routing.capability_compatibility import _supported_artifacts
from .condition_recommender import _quote_grounded
from .context import preflight_budget, record_event
from .request_concerns import (
    addressed_from_claims,
    concern_options,
    selected_guidance_actions,
)
from .research_framing import framing_schema, framing_messages, framed_claims
from .structured_calls import _serialized_structured_input

ADVISORY_ROLES = frozenset(
    {"hypothesis_bases", "selection_conditions", "request_concerns"}
)

# Discourse cues only trigger a semantic review; they NEVER map words to a
# workflow. This also recovers alternatives that the endpoint classifier lost.
_OPEN_QUESTION = re.compile(
    r"\b(?:hypothes[ie]s|explanations|alternatives?|either|whether|or|versus|vs\.?|"
    r"unclear|uncertain|undecided|compare|comparing|not sure|cannot decide|"
    r"have not decided|don't know|do not know)\b|"
    r"假設|假说|假說|還是|还是|或者|或是|不確定|不确定|不清楚|不知道|尚未決定|尚未决定",
    re.IGNORECASE,
)


def needs_hypothesis_review(decision, task):
    return bool(
        decision.capability_match_status == "ambiguous"
        and len(decision.hypothesis_actions) > 1
        or len(decision.outcome_hypotheses) > 1
        or decision.requested_outcome is not None
        and decision.requested_outcome.artifact_type == "unknown"
        or _OPEN_QUESTION.search(task)
    )


def framing_yielded(decision, usage) -> bool:
    """A goal review that validated no comparison leaves the method choice open (Log 257).

    This stage asks which research question the request poses; the condition
    recommender asks which method answers one question. A successful review
    that found one goal changed nothing, so it must not use up the method
    stage's call: that is how the prior-reliability gap and every method-tie
    recommendation were lost after Log 255. A failed review still blocks it,
    so an explicit comparison never falls back to one recommended tool.
    """
    reviews = [call for call in usage.calls if call.role == "hypothesis_bases"]
    return not reviews or (
        all(call.status == "success" for call in reviews)
        and not decision.stated_hypotheses
        and decision.match_basis != "unverified_evidence"
    )


def explicit_research_choice(task):
    """Early review for explicit research alternatives, before outcome repair."""
    return bool(
        re.search(
            r"\b(?:hypothes[ie]s|explanations|undecided|cannot decide|not sure|"
            r"have not decided|unclear goal)\b|假設|假说|假說|還是|还是|不確定|不确定|"
            r"不知道|尚未決定|尚未决定",
            task,
            re.IGNORECASE,
        )
    )


def hypothesis_options(decision, task: str) -> list[tuple[str, str]]:
    """Offer every scientific method, not only the classifier's winning route.

    Do not gate on modalities or method-specific vocabulary: missing data is
    precisely one of the things the comparison should explain.
    """
    if decision.action != "no_tool" or decision.should_execute:
        return []
    outcomes = [h.outcome for h in decision.outcome_hypotheses]
    if decision.requested_outcome is not None:
        outcomes.append(decision.requested_outcome)
    if not decision.in_scope and not any(
        o.artifact_type != "unknown" for o in outcomes
    ):
        return []
    return [
        (action, spec.workflow)
        for action, spec in ACTION_DEFINITIONS.items()
        if action in OUTPUT_CAPABILITIES
    ] + [("unsupported", "No registered method fits this hypothesis")]


def hypotheses_from_claims(task, claims, options):
    offered = {basis for basis, _ in options}
    accepted, rejected, seen = [], [], set()
    if claims.question_mode == "single_goal":
        return accepted, rejected
    for claim in claims.claims:
        key = (claim.basis, claim.text_span.strip())
        if claim.basis not in offered:
            rejected.append({"basis": claim.basis, "reason": "not_offered"})
        elif not _quote_grounded(task, claim.text_span):
            rejected.append({"basis": claim.basis, "reason": "quote_not_in_request"})
        elif key not in seen:
            seen.add(key)
            bases = compatible_bases(claim)
            if not bases:
                rejected.append(
                    {"basis": claim.basis, "reason": "result_not_supported"}
                )
            for basis in bases or ["unsupported"]:
                accepted.append(
                    StatedHypothesis(
                        axis=claims.question_mode,
                        basis=basis,
                        text_span=claim.text_span.strip(),
                        target_artifact=claim.target_artifact,
                        target_granularity=claim.target_granularity,
                    )
                )
    if any(
        item["reason"] in {"not_offered", "quote_not_in_request"} for item in rejected
    ):
        # Never silently lose the third alternative just because two survived.
        return [], rejected
    accepted = list(
        {
            (h.basis, h.text_span, h.target_artifact, h.target_granularity): h
            for h in accepted
        }.values()
    )
    # Multiple methods for one quotation are alternatives within ONE hypothesis.
    if (
        claims.question_mode == "multiple_hypotheses"
        and len({h.text_span for h in accepted}) < 2
    ):
        return [], [*rejected, {"reason": "fewer_than_two_grounded_hypotheses"}]
    return accepted, rejected


def compatible_bases(claim):
    """Check actual output/scale and declared compositions, never a name alone.

    An aggregate predecessor can be expanded to a declared sample-specific
    composition when the desired endpoint requires per-sample features. An
    unrelated output becomes a visible capability gap, not a recommendation.
    """
    if claim.basis == "unsupported":
        return [claim.basis]
    cap = OUTPUT_CAPABILITIES[claim.basis]
    output_matches = (
        claim.target_artifact == "unknown"
        or claim.target_artifact in _supported_artifacts(cap)
    )
    semantics = ARTIFACT_SEMANTICS[claim.target_artifact]
    # A TF-by-sample matrix and a sample partition are cohort artifacts in the
    # existing ontology, even though their columns/labels describe patients.
    scales = semantics.granularities
    scale = (
        next(iter(scales)) if scales and len(scales) == 1 else claim.target_granularity
    )
    scale_matches = scale == "unknown" or scale in cap.granularities
    if output_matches and scale_matches:
        return [claim.basis]
    composed = set()
    for (target, _), composition in GUIDANCE_COMPOSITIONS.items():
        if target == claim.target_artifact:
            sources = dict(composition.sources)
            if claim.basis in sources:
                return [claim.basis]
            composed.update(
                a
                for a in sources
                if claim.basis in OUTPUT_CAPABILITIES[a].guidance_predecessors
            )
    if composed:
        return sorted(composed)
    return [
        a
        for a, c in OUTPUT_CAPABILITIES.items()
        if claim.basis in c.guidance_predecessors
        and claim.target_artifact in _supported_artifacts(c)
        and scale in c.granularities
    ]


def invoke_hypothesis_matcher(context, state, task, decision, usage, budget_warnings):
    llm = getattr(context, "selection_condition_llm", None)
    options = hypothesis_options(decision, task)
    if (
        llm is None
        or not options
        or not needs_hypothesis_review(decision, task)
        or any(c.role in ADVISORY_ROLES for c in usage.calls)
    ):
        return decision, usage, budget_warnings
    # A tie selects no workflow; offer its candidates' concerns (Log 263).
    actions = selected_guidance_actions(decision) or list(decision.hypothesis_actions)
    schema = framing_schema()
    messages = framing_messages(task, concern_options(actions))
    input_text = _serialized_structured_input(messages, schema)
    budget, budget_warnings = preflight_budget(
        context,
        dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings),
        role="hypothesis_bases",
        model=context.semantic_model_name,
        input_text=input_text,
        reserved_output_tokens=context.router_max_tokens,
        allow_reserve=False,
    )
    if budget.status == "blocked":
        usage.budget_exhausted = True
        return decision, usage, budget_warnings
    started, raw, output, status = time.monotonic_ns(), None, "", "failed"
    result = decision
    try:
        record_event(context, state, "routing.hypothesis_bases_started", "classify", {})
        payload, raw = semantic_payload(
            llm.with_structured_output(
                schema,
                method="function_calling",
                include_raw=True,
                strict=True,
            ).invoke(messages)
        )
        framing = schema.model_validate(
            payload.model_dump() if isinstance(payload, BaseModel) else payload
        )
        claims = framed_claims(framing, task)
        accepted, rejected = hypotheses_from_claims(task, claims, options)
        addressed, concern_rejections = addressed_from_claims(
            task,
            StatedConcernClaims(claims=claims.concerns),
            actions,
        )
        output, status = framing.model_dump_json(), "success"
        updates = {}
        if accepted:
            actions = list(dict.fromkeys(h.basis for h in accepted if h.basis != "unsupported"))
            comparison = len(actions) >= 2
            gaps = any(h.basis == "unsupported" for h in accepted)
            updates.update(
                stated_hypotheses=accepted, advisory_recommendation=None,
                matched_actions=actions if len(actions) == 1 else [],
                recommended_actions=[], hypothesis_actions=actions if comparison else [],
                capability_match_status=("ambiguous" if comparison else "unsupported" if gaps else "exact"),
                clarification_question=("Which scientific question should we start with?" if comparison else None),
            )
        elif claims.question_mode != "single_goal":
            # An invalid comparison is not evidence for the classifier's one
            # surviving method. Keep it out of single-path recommendation.
            updates.update(
                matched_actions=[],
                recommended_actions=[],
                hypothesis_actions=[],
                advisory_recommendation=None,
                requested_outcome=None,
                capability_match_status="ambiguous",
                match_basis="unverified_evidence",
                confidence=0.0,
                clarification_question=(
                    "I could not validate every research alternative. Please state each "
                    "hypothesis and the result you want from it before selecting a workflow."
                ),
            )
        if addressed:
            updates["addressed_concerns"] = addressed
        result = decision.model_copy(update=updates) if updates else decision
        record_event(
            context,
            state,
            "routing.hypothesis_bases_matched",
            "classify",
            {
                "question_mode": claims.question_mode,
                "scientific_hypotheses": [h.model_dump() for h in framing.hypotheses],
                "accepted": [h.model_dump() for h in accepted],
                "rejected": rejected,
                "concern_rejections": concern_rejections,
            },
        )
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        record_event(
            context,
            state,
            "routing.hypothesis_bases_failed",
            "classify",
            {"error_type": type(error).__name__},
        )
    finally:
        usage = append_llm_usage(
            usage,
            role="hypothesis_bases",
            model=context.semantic_model_name,
            response=raw,
            input_text=input_text,
            output_text=output,
            budget_tokens=context.task_token_budget,
            duration_ms=max(0, (time.monotonic_ns() - started) // 1_000_000),
            status=status,
            price_catalog=context.price_catalog,
        )
    return result, usage, budget_warnings
