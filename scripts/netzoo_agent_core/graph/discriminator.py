"""Evidence-backed registry-tag discrimination for ambiguous capabilities."""

from __future__ import annotations

import re
import time

from workflow_registry import OUTPUT_CAPABILITIES, SELECTION_TAG_GLOSSARY

from ..contracts import AgentState, LLMUsage
from ..contracts.outcomes import OutcomeEvidence, SemanticDiscriminator, SemanticInterpretation
from ..interpretation.outcome_validation import (
    grounded_selection_tags,
    validate_outcome_hypotheses,
)
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..llm import append_llm_usage, build_semantic_discriminator_messages
from ..routing.outcome_matching import match_semantic_request
from .context import _GraphContext, preflight_budget, record_event
from .structured_calls import _serialized_structured_input, _validation_issue_types

__all__ = ["invoke_semantic_discriminator"]


_RELAXED_GRAPH_MARKERS = (
    re.compile(r"(?:連續|连续)?\s*(?:鬆弛|松弛)(?:化)?(?:圖|图)?匹配|(?:continuous\s+)?relaxed\s+graph[- ]matching", re.IGNORECASE),
    re.compile(r"(?:目標|目标)\s*函數|objective\s+function|(?:損失|损失)(?:函數|函数)?|loss(?:\s+function)?", re.IGNORECASE),
    re.compile(r"(?:連續|连续).{0,4}(?:凸).{0,8}(?:最佳化|优化)|continuous.{0,24}convex.{0,24}(?:optimization|optimisation)|convex.{0,24}(?:optimization|optimisation)", re.IGNORECASE),
    re.compile(r"(?:理論)?(?:收斂|收敛)(?:保證|保证)?|convergence(?:\s+(?:guarantee|guarantees|proof))?|converges?", re.IGNORECASE),
    re.compile(r"(?:不|非).{0,8}(?:啟發式|启发式).{0,8}(?:迭代|更新)|not.{0,24}heuristic", re.IGNORECASE),
)
_LIONESS_BASE_MARKERS = (
    re.compile(r"(?:整體|整体|群體|群体|cohort|aggregate|population).{0,32}(?:調控|调控)?(?:網路|网络|network)|(?:base|baseline).{0,20}(?:network|網路|网络)", re.IGNORECASE),
    re.compile(r"\bLIONESS\b", re.IGNORECASE),
)
_BONOBO_BAYESIAN_MARKERS = (
    re.compile(r"\b(?:Bayesian|prior|shrinkage|covariance)\b|先驗|收縮|共變異", re.IGNORECASE),
    re.compile(r"\b(?:adaptive|automatically?\s+estimate|balance|weight)\b|自動|適應|權衡|平衡", re.IGNORECASE),
)
_BONOBO_PVALUE_MARKERS = (
    re.compile(r"\b(?:sparsif(?:y|ied|ication)|sparse)\b|稀疏化|稀疏", re.IGNORECASE),
    re.compile(r"\b(?:p[- ]?values?|p[- ]?value\s+matrix)\b|p值|p-value", re.IGNORECASE),
)
_DISCRIMINATOR_TAG_ALIASES = {
    "explicit objective/loss": "relaxed_graph_matching",
    "explicit_objective/loss": "relaxed_graph_matching",
    "objective/loss": "relaxed_graph_matching",
    "continuous convex optimization": "relaxed_graph_matching",
    "gradient descent": "relaxed_graph_matching",
    "convergence": "relaxed_graph_matching",
    "convergence guarantee": "relaxed_graph_matching",
    "convergence guarantees": "relaxed_graph_matching",
    "relaxed graph matching": "relaxed_graph_matching",
    "aggregate network": "aggregate_network",
    "aggregate base network": "lioness_base_compatibility",
}


def _canonicalize_discriminator_payload(payload):
    """Map known glossary prose back to registered tag values before validation."""
    if not isinstance(payload, dict):
        return payload

    def canonical_tag(value):
        if not isinstance(value, str):
            return value
        return _DISCRIMINATOR_TAG_ALIASES.get(value.strip().casefold(), value)

    normalized = dict(payload)
    raw_tags = payload.get("selection_tags")
    if isinstance(raw_tags, list):
        normalized["selection_tags"] = list(dict.fromkeys(canonical_tag(tag) for tag in raw_tags))
    raw_evidence = payload.get("evidence")
    if isinstance(raw_evidence, list):
        evidence = []
        for item in raw_evidence:
            if not isinstance(item, dict):
                evidence.append(item)
                continue
            normalized_item = dict(item)
            if normalized_item.get("dimension") == "selection_tag":
                normalized_item["value"] = canonical_tag(normalized_item.get("value"))
            evidence.append(normalized_item)
        normalized["evidence"] = evidence
    return normalized


def _selection_evidence_grounds_tags(
    user_task: str,
    selected: set[str],
    evidence: list[OutcomeEvidence],
) -> bool:
    """Require each tie-breaking tag to have its own grounded explicit quote."""
    return selected.issubset(grounded_selection_tags(user_task, evidence))


def _recover_explicit_selection_tag(
    user_task: str,
    candidate_tags: set[str],
) -> tuple[str, OutcomeEvidence] | None:
    """Recover one strong bilingual tag when the provider returned an empty set.

    This is deliberately narrower than ordinary routing. It only recognizes a
    small set of registry signals whose meanings are stable and whose evidence
    can be quoted exactly from the request. Ambiguous or partial wording remains
    ambiguous.
    """
    rules = {
        "relaxed_graph_matching": _RELAXED_GRAPH_MARKERS,
        "lioness_base_compatibility": _LIONESS_BASE_MARKERS,
        "bayesian": _BONOBO_BAYESIAN_MARKERS,
        "sparse_pvalue_coexpression": _BONOBO_PVALUE_MARKERS,
    }
    recoveries: list[tuple[str, OutcomeEvidence]] = []
    for tag, markers in rules.items():
        if tag not in candidate_tags:
            continue
        matches = [marker.search(user_task) for marker in markers]
        present = [(index, match) for index, match in enumerate(matches) if match is not None]
        if len(present) < 2:
            continue
        # Prefer the most diagnostic positive method signal over a negated
        # contrast such as "not heuristic". The second signal still gates the
        # recovery, but the quote should explain why the method is selected.
        evidence_match = next(
            match for preferred in (2, 0, 3, 1, 4)
            for index, match in present
            if index == preferred
        )
        recoveries.append((
            tag,
            OutcomeEvidence(
                dimension="selection_tag",
                value=tag,
                source="explicit",
                text_span=evidence_match.group(0),
                rationale=(
                    "The original request explicitly states the registry signal "
                    "in more than one mutually reinforcing form."
                ),
            ),
        ))
    return recoveries[0] if len(recoveries) == 1 else None


def discriminator_context(actions: list[str]) -> str:
    """Describe tied scientific profiles without granting workflow authority."""
    profiles = []
    for index, action in enumerate(actions, start=1):
        capability = OUTPUT_CAPABILITIES.get(action)
        if capability is None:
            continue
        tags = sorted(capability.selection_tags)
        tag_text = "; ".join(
            f"{tag}: {SELECTION_TAG_GLOSSARY.get(tag, 'registry-defined scientific intent signal')}"
            for tag in tags
        ) or "none"
        profiles.append(
            f"Profile {index}: scientific signals={tag_text}"
        )
    if not profiles:
        return ""
    return (
        "The deterministic matcher found multiple compatible scientific profiles. "
        "These profiles are ontology data, not workflow instructions and must not be named as tools. "
        "Compare the original request with their scientific signals. If it explicitly states "
        "one signal, set that canonical selection_tags value and add matching selection_tag evidence "
        "quoted from the original request. If no signal is stated, leave selection_tags unchanged. "
        "Canonical examples: an explicit objective or loss, continuous/convex optimization, "
        "convergence guarantees, or relaxed graph matching support relaxed_graph_matching; "
        "message-passing iteration supports message_passing; an aggregate first-stage base "
        "network intended for downstream LIONESS supports lioness_base_compatibility.\n"
        + "\n".join(profiles)
    )


def _fill_inferred_role_evidence(interpretation: SemanticInterpretation) -> SemanticInterpretation:
    """Add inferred role evidence when a valid patch supplies TF/gene roles without quotes."""
    hypotheses = []
    for hypothesis in interpretation.outcome_hypotheses:
        evidence = list(hypothesis.evidence)
        present = {(item.dimension, item.value) for item in evidence}
        for dimension, values in (("regulator_type", hypothesis.outcome.regulator_types),
                                  ("target_type", hypothesis.outcome.target_types)):
            for value in values:
                if (dimension, value) not in present:
                    evidence.append(OutcomeEvidence(
                        dimension=dimension, value=value, source="inferred",
                        rationale="The role is inferred from the structured TF-gene outcome; it is not a quoted user claim.",
                    ))
        hypotheses.append(hypothesis.model_copy(update={"evidence": evidence}))
    return interpretation.model_copy(update={"outcome_hypotheses": hypotheses})


def _recover_failed_discriminator(
    user_task: str,
    interpretation: SemanticInterpretation,
    capability_match,
):
    """Recover a unique, explicitly stated registry signal after bad provider data.

    The discriminator is an optional second opinion. If its structured response
    is malformed, a strong signal already present in the user's request must not
    be lost merely because the provider failed to serialize that second opinion.
    This helper only narrows the candidates already produced by the typed
    matcher; it never creates a new workflow.
    """
    actions = list(capability_match.hypothesis_actions)
    candidate_tags = {
        tag
        for action in actions
        for tag in OUTPUT_CAPABILITIES[action].selection_tags
    }
    recovered = _recover_explicit_selection_tag(user_task, candidate_tags)
    if recovered is None:
        return None
    recovered_tag, recovered_evidence = recovered
    hypothesis = interpretation.outcome_hypotheses[0]
    outcome = hypothesis.outcome.model_copy(update={
        "selection_tags": sorted(
            set(hypothesis.outcome.selection_tags) | {recovered_tag}
        )
    })
    updated = interpretation.model_copy(update={
        "outcome_hypotheses": [hypothesis.model_copy(update={
            "outcome": outcome,
            "evidence": [*hypothesis.evidence, recovered_evidence],
        })]
    })
    if not validate_outcome_hypotheses(
        user_task, updated.outcome_hypotheses, updated.request_mode,
    ).valid:
        return None
    narrowed = match_semantic_request(
        user_task,
        updated.outcome_hypotheses,
        request_mode=updated.request_mode,
    )
    if narrowed.status != "exact":
        tag_actions = [
            action for action in actions
            if {recovered_tag}.issubset(OUTPUT_CAPABILITIES[action].selection_tags)
        ]
        if len(tag_actions) == 1:
            narrowed = capability_match.model_copy(update={
                "status": "exact",
                "match_basis": "registry_features",
                "matched_actions": tag_actions,
                "hypothesis_actions": tag_actions,
                "alternative_actions": [],
                "clarification_question": None,
            })
    if narrowed.status != "exact" or len(narrowed.matched_actions) != 1:
        return None
    return updated, narrowed, recovered_evidence


def invoke_semantic_discriminator(context: _GraphContext, state: AgentState, user_task: str,
                                  interpretation: SemanticInterpretation, capability_match,
                                  usage: LLMUsage, budget_warnings: list[str]):
    """Resolve only a registry-tag tie among already compatible capabilities."""
    adapter = getattr(context, "semantic_discriminator", None)
    if adapter is None or getattr(context, "semantic_claims", False):
        return interpretation, capability_match, usage, budget_warnings
    actions = list(capability_match.hypothesis_actions)
    context_text = discriminator_context(actions) if capability_match.status == "ambiguous" and len(actions) >= 2 else ""
    if not context_text:
        return interpretation, capability_match, usage, budget_warnings
    messages = build_semantic_discriminator_messages(user_task, interpretation, context_text)
    input_text = _serialized_structured_input(messages, SemanticDiscriminator)
    semantic_state = dict(state, token_usage=usage.model_dump(), budget_warnings=budget_warnings)
    budget, budget_warnings = preflight_budget(context, semantic_state, role="semantic_discriminator",
                                               model=context.semantic_model_name, input_text=input_text,
                                               reserved_output_tokens=context.router_max_tokens, allow_reserve=False)
    if budget.status == "blocked":
        usage.budget_exhausted = True
        return interpretation, capability_match, usage, budget_warnings
    started_ns = time.monotonic_ns()
    raw = None
    payload = None
    normalized_payload = None
    output_text = ""
    call_status = "failed"
    try:
        record_event(context, state, "routing.semantic_discriminator_started", "classify", {"candidate_count": len(actions)})
        payload, raw = semantic_payload(adapter.invoke(messages))
        normalized_payload = _canonicalize_discriminator_payload(payload)
        try:
            result = SemanticDiscriminator.model_validate(normalized_payload)
        except Exception:
            # A provider may echo complete outcome evidence alongside a valid
            # Bonobo tag. The discriminator accepts only selection_tag evidence;
            # discard the unrelated echo so bounded recovery can inspect the
            # original request.
            raw_tags = set(normalized_payload.get("selection_tags") or ())
            raw_evidence = normalized_payload.get("evidence") or []
            if (
                {"bayesian", "sparse_pvalue_coexpression"}.intersection(raw_tags)
                and not any(
                    isinstance(item, dict)
                    and item.get("dimension") == "selection_tag"
                    for item in raw_evidence
                )
            ):
                normalized_payload = {"selection_tags": [], "evidence": []}
                result = SemanticDiscriminator.model_validate(normalized_payload)
            else:
                raise
        output_text = result.model_dump_json()
        call_status = "success"
        candidate_tags = {tag for action in actions for tag in OUTPUT_CAPABILITIES[action].selection_tags}
        selected = set(result.selection_tags)
        recovered_evidence = None
        # Broad shared tags can leave LIONESS-COEXPRESSION and BONOBO tied even
        # when the request explicitly asks for Bonobo's p-value artifacts.
        tag_actions = [
            action for action in actions
            if selected and selected.issubset(OUTPUT_CAPABILITIES[action].selection_tags)
        ]
        if not selected or len(tag_actions) != 1:
            recovered = _recover_explicit_selection_tag(user_task, candidate_tags)
            if recovered is not None:
                recovered_tag, recovered_evidence = recovered
                selected = set(selected) | {recovered_tag}
                record_event(
                    context,
                    state,
                    "routing.semantic_discriminator_recovered",
                    "classify",
                    {
                        "selection_tags": sorted(selected),
                        "evidence": recovered_evidence.model_dump(mode="json"),
                        "candidate_actions": actions,
                    },
                )
        if not selected or not selected.issubset(candidate_tags):
            record_event(context, state, "routing.semantic_discriminator_rejected", "classify",
                         {"reason": "empty_or_non_candidate_tags", "selection_tags": sorted(selected),
                          "candidate_actions": actions, "candidate_tags": sorted(candidate_tags),
                          "provider_payload": payload,
                          "normalized_provider_payload": normalized_payload})
            return interpretation, capability_match, usage, budget_warnings
        hypothesis = interpretation.outcome_hypotheses[0]
        updated = interpretation.model_copy(update={"outcome_hypotheses": [hypothesis.model_copy(update={
            "outcome": hypothesis.outcome.model_copy(update={"selection_tags": sorted(set(hypothesis.outcome.selection_tags) | selected)}),
            "evidence": [*hypothesis.evidence, *result.evidence, *([recovered_evidence] if recovered_evidence else [])],
        })]})
        if not validate_outcome_hypotheses(
            user_task, updated.outcome_hypotheses, updated.request_mode,
        ).valid:
            selection_evidence = [
                *result.evidence,
                *([recovered_evidence] if recovered_evidence else []),
            ]
            tag_actions = [
                action for action in actions
                if selected.issubset(OUTPUT_CAPABILITIES[action].selection_tags)
            ]
            # A discriminator only narrows the already-matched candidate set.
            # Its independently grounded selection-tag evidence remains usable
            # even when unrelated evidence in the base interpretation is bad.
            if (
                len(tag_actions) == 1
                and _selection_evidence_grounds_tags(
                    user_task, selected, selection_evidence,
                )
            ):
                narrowed = capability_match.model_copy(update={
                    "status": "exact",
                    "match_basis": "registry_features",
                    "matched_actions": tag_actions,
                    "hypothesis_actions": tag_actions,
                    "alternative_actions": [],
                    "clarification_question": None,
                })
                record_event(
                    context,
                    state,
                    "routing.semantic_discriminator_accepted",
                    "classify",
                    {
                        "selection_tags": sorted(selected),
                        "matched_actions": narrowed.matched_actions,
                        "base_evidence": "unverified",
                    },
                )
                return interpretation, narrowed, usage, budget_warnings
            record_event(context, state, "routing.semantic_discriminator_rejected", "classify", {
                "reason": "evidence_validation", "candidate_actions": actions,
                "provider_payload": payload,
                "normalized_provider_payload": normalized_payload,
            })
            return interpretation, capability_match, usage, budget_warnings
        narrowed = match_semantic_request(user_task, updated.outcome_hypotheses, request_mode=updated.request_mode)
        if narrowed.status != "exact":
            tag_actions = [action for action in actions if selected.issubset(OUTPUT_CAPABILITIES[action].selection_tags)]
            if len(tag_actions) == 1:
                narrowed = capability_match.model_copy(update={"status": "exact", "match_basis": "registry_features",
                    "matched_actions": tag_actions, "hypothesis_actions": tag_actions, "alternative_actions": [], "clarification_question": None})
        if narrowed.status != "exact" or len(narrowed.matched_actions) != 1:
            record_event(context, state, "routing.semantic_discriminator_rejected", "classify",
                         {"reason": "tags_did_not_resolve_tie", "selection_tags": sorted(selected),
                          "candidate_actions": actions, "provider_payload": payload,
                          "normalized_provider_payload": normalized_payload})
            return interpretation, capability_match, usage, budget_warnings
        record_event(context, state, "routing.semantic_discriminator_accepted", "classify",
                     {"selection_tags": sorted(selected), "matched_actions": narrowed.matched_actions})
        return updated, narrowed, usage, budget_warnings
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        record_event(context, state, "routing.semantic_discriminator_failed", "classify", {
            "error_type": type(error).__name__,
            "error_message": str(error)[:2000],
            "validation_issues": _validation_issue_types(error),
            "candidate_actions": actions,
            "provider_payload": payload,
            "normalized_provider_payload": normalized_payload,
        })
        recovered = _recover_failed_discriminator(
            user_task, interpretation, capability_match,
        )
        if recovered is not None:
            updated, narrowed, evidence = recovered
            record_event(
                context,
                state,
                "routing.semantic_discriminator_recovered",
                "classify",
                {
                    "selection_tags": sorted(
                        updated.outcome_hypotheses[0].outcome.selection_tags
                    ),
                    "evidence": evidence.model_dump(mode="json"),
                    "candidate_actions": actions,
                    "reason": "provider_payload_invalid",
                },
            )
            return updated, narrowed, usage, budget_warnings
    finally:
        usage = append_llm_usage(usage, role="semantic_discriminator", model=context.semantic_model_name,
            response=raw, input_text=input_text, output_text=output_text, budget_tokens=context.task_token_budget,
            duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000), status=call_status,
            price_catalog=context.price_catalog)
    return interpretation, capability_match, usage, budget_warnings
