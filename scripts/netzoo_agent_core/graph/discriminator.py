"""Evidence-backed registry-tag discrimination for ambiguous capabilities."""

from __future__ import annotations

import time

from workflow_registry import OUTPUT_CAPABILITIES, SELECTION_TAG_GLOSSARY

from ..contracts import AgentState, LLMUsage
from ..contracts.outcomes import OutcomeEvidence, SemanticDiscriminator, SemanticInterpretation
from ..interpretation.outcome_validation import validate_outcome_hypotheses
from ..interpretation.provider_fallback import _is_fatal_exception
from ..interpretation.semantic_repair import semantic_payload
from ..llm import append_llm_usage, build_semantic_discriminator_messages
from ..routing.outcome_matching import match_semantic_request
from .context import _GraphContext, preflight_budget, record_event
from .structured_calls import _serialized_structured_input

__all__ = ["invoke_semantic_discriminator"]


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
            f"Profile {index}: artifact={capability.artifact_type}; "
            f"entities={sorted(capability.entity_types)}; regulators={sorted(capability.regulator_types)}; "
            f"targets={sorted(capability.target_types)}; granularities={sorted(capability.granularities or ())}; "
            f"scientific signals={tag_text}"
        )
    if not profiles:
        return ""
    return (
        "The deterministic matcher found multiple compatible scientific capability profiles. "
        "These profiles are ontology data, not workflow instructions and must not be named as tools. "
        "Compare the original request with their scientific signals. If the request explicitly states "
        "one signal, set that canonical selection_tags value and add matching selection_tag evidence "
        "quoted from the original request. If no signal is stated, leave selection_tags unchanged. "
        "Canonical examples: continuous relaxation, relaxed graph matching, or gradient-based graph "
        "optimization support relaxed_graph_matching; message-passing iteration supports message_passing.\n"
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
    started_ns = time.monotonic_ns(); raw = None; output_text = ""; call_status = "failed"
    try:
        record_event(context, state, "routing.semantic_discriminator_started", "classify", {"candidate_count": len(actions)})
        payload, raw = semantic_payload(adapter.invoke(messages))
        result = SemanticDiscriminator.model_validate(payload)
        output_text = result.model_dump_json(); call_status = "success"
        candidate_tags = {tag for action in actions for tag in OUTPUT_CAPABILITIES[action].selection_tags}
        selected = set(result.selection_tags)
        if not selected or not selected.issubset(candidate_tags):
            record_event(context, state, "routing.semantic_discriminator_rejected", "classify",
                         {"reason": "empty_or_non_candidate_tags", "selection_tags": sorted(selected)})
            return interpretation, capability_match, usage, budget_warnings
        hypothesis = interpretation.outcome_hypotheses[0]
        updated = interpretation.model_copy(update={"outcome_hypotheses": [hypothesis.model_copy(update={
            "outcome": hypothesis.outcome.model_copy(update={"selection_tags": sorted(set(hypothesis.outcome.selection_tags) | selected)}),
            "evidence": [*hypothesis.evidence, *result.evidence],
        })]})
        if not validate_outcome_hypotheses(user_task, updated.outcome_hypotheses).valid:
            record_event(context, state, "routing.semantic_discriminator_rejected", "classify", {"reason": "evidence_validation"})
            return interpretation, capability_match, usage, budget_warnings
        narrowed = match_semantic_request(user_task, updated.outcome_hypotheses, request_mode=updated.request_mode)
        if narrowed.status != "exact":
            tag_actions = [action for action in actions if selected.issubset(OUTPUT_CAPABILITIES[action].selection_tags)]
            if len(tag_actions) == 1:
                narrowed = capability_match.model_copy(update={"status": "exact", "match_basis": "registry_features",
                    "matched_actions": tag_actions, "hypothesis_actions": tag_actions, "alternative_actions": [], "clarification_question": None})
        if narrowed.status != "exact" or len(narrowed.matched_actions) != 1:
            record_event(context, state, "routing.semantic_discriminator_rejected", "classify",
                         {"reason": "tags_did_not_resolve_tie", "selection_tags": sorted(selected)})
            return interpretation, capability_match, usage, budget_warnings
        record_event(context, state, "routing.semantic_discriminator_accepted", "classify",
                     {"selection_tags": sorted(selected), "matched_actions": narrowed.matched_actions})
        return updated, narrowed, usage, budget_warnings
    except BaseException as error:
        if _is_fatal_exception(error):
            raise
        record_event(context, state, "routing.semantic_discriminator_failed", "classify", {"error_type": type(error).__name__})
    finally:
        usage = append_llm_usage(usage, role="semantic_discriminator", model=context.semantic_model_name,
            response=raw, input_text=input_text, output_text=output_text, budget_tokens=context.task_token_budget,
            duration_ms=max(0, (time.monotonic_ns() - started_ns) // 1_000_000), status=call_status,
            price_catalog=context.price_catalog)
    return interpretation, capability_match, usage, budget_warnings
