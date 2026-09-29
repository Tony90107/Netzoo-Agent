"""Present advisory algorithm choices without granting execution authority."""

from __future__ import annotations

from collections import Counter

from workflow_registry import EXTERNAL_REFERENCES, OUTPUT_CAPABILITIES, SELECTION_AXES, SELECTION_TAG_GLOSSARY

from ..contracts import ProjectPolicySnapshot, TaskDecision
from ..presentation import _ui_text, _ui_text_with_user_data, user_data_token
from .inspected_answers import render_inspected_recommendation
from .method_philosophy import method_philosophies_for, question_fit_for, requested_framework_for
from .tie_guidance import _inputs, concern_section
from ..contracts.artifact_semantics import ARTIFACT_SEMANTICS
from ..routing.clarification_planner import algorithmic_assumptions_for
from ..routing.capability_compatibility import _supported_artifacts


def _condition_label(condition: str) -> str:
    axis, _, value = condition.partition(":")
    return SELECTION_AXES.get(axis, {}).get("values", {}).get(value, condition)


def _least_shared_tags(capability, shared: Counter) -> list[str]:
    tags = [tag for tag in capability.selection_tags if method_philosophies_for([tag])]
    if not tags:
        return []
    fewest = min(shared[tag] for tag in tags)
    return sorted(tag for tag in tags if shared[tag] == fewest)


def _recommended_block(action, policy, shared: Counter) -> str:
    """The recommended method in prose: what sets it apart, needs, produces (Log 273)."""
    spec = policy.workflows[action]
    capability = spec.output_capability
    notes = (method_philosophies_for(_least_shared_tags(capability, shared))
             or method_philosophies_for(capability.selection_tags) or (spec.description,))
    artifacts = sorted(capability.produced_artifacts or {capability.artifact_type})
    results = [ARTIFACT_SEMANTICS[a].description for a in artifacts if a in ARTIFACT_SEMANTICS]
    scale = {frozenset({"aggregate"}): " (one cohort-level result)",
             frozenset({"sample_specific"}): " (one result per sample)"}.get(frozenset(capability.granularities), "")
    produces = ("Produces " + "; ".join(r[0].lower() + r[1:] for r in results) + scale + ".") if results else ""
    return f"**{spec.workflow}** (recommend) — " + " ".join(
        part for part in (" ".join(notes), _inputs(spec), produces) if part)


def _alternative_line(action, policy, shared: Counter) -> str:
    capability = policy.workflows[action].output_capability
    preferred = "; ".join(_condition_label(item) for item in capability.prefer_when)
    approach = next((SELECTION_TAG_GLOSSARY[t] for t in _least_shared_tags(capability, shared)
                     if t in SELECTION_TAG_GLOSSARY), "")
    parts = ([f"preferred when: {preferred}"] if preferred else []) + ([f"approach: {approach}"] if approach else [])
    return f"- **{policy.workflows[action].workflow}**" + (" — " + "; ".join(parts) + "." if parts else ".")


def render_advisory_recommendation(
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
    *, candidate_details, downstream_section,
) -> str | None:
    """Form A (Log 139): recommend from quoted study facts; list the others."""
    recommendation = decision.advisory_recommendation
    spec = policy.workflows.get(recommendation.action)
    if spec is None:
        return None
    if recommendation.conditions and all(item.axis == "inspected_inputs" for item in recommendation.conditions):
        return render_inspected_recommendation(
            decision, policy, spec, candidate_details(recommendation.action, spec, policy, recommended=True),
            downstream_section(recommendation.action),
        )
    # Quotes remain in the validated decision for audit. Echoing a Chinese
    # excerpt in the answer breaks the project's fixed English output policy.
    evidence = [item.text_span for item in recommendation.conditions] or recommendation.supporting_spans
    spans = [span for span in evidence if span.isascii()]
    quotes = "; ".join(f'"{user_data_token(index)}"' for index in range(len(spans)))
    reasons = "; ".join(
        _condition_label(f"{item.axis}:{item.value}") for item in recommendation.conditions
    )
    lead = (
        (f"Based on what you said — {quotes} — **{spec.workflow}** fits better: {reasons}."
         if quotes else f"Based on the stated study conditions, **{spec.workflow}** fits better: {reasons}.")
        if recommendation.conditions else
        f"My recommended starting method is **{spec.workflow}**: {recommendation.rationale}"
    )
    fit = question_fit_for(
        decision.requested_outcome, spec.workflow, spec.output_capability,
        stated_conditions=[_condition_label(f"{item.axis}:{item.value}")
                           for item in recommendation.conditions],
    )
    lines = [lead]
    if recommendation.conditions and recommendation.rationale:
        lines.append("Why it addresses this question: " + recommendation.rationale)
    if fit:
        lines.append(fit)
    listed = [a for a in dict.fromkeys([recommendation.action, *decision.hypothesis_actions]) if a in policy.workflows]
    shared = Counter(tag for a in listed for tag in policy.workflows[a].output_capability.selection_tags)
    lines.append(_recommended_block(recommendation.action, policy, shared))
    if not recommendation.conditions and spans:
        lines.append(f"Request evidence: {quotes}.")
    if recommendation.assumptions:
        lines.append("Conditional assumptions to confirm:\n" + "\n".join(
            f"- {item}" for item in recommendation.assumptions
        ))
    others = [_alternative_line(action, policy, shared) for action in listed if action != recommendation.action]
    if others:
        lines.append("Other compatible option(s):\n" + "\n".join(others))
    if downstream := downstream_section(recommendation.action):
        lines.append(downstream.rstrip("\n"))
    if decision.clarification_question:
        lines.append(decision.clarification_question)
    lines.append("No files were inspected and no analysis ran.")
    return _ui_text_with_user_data("\n\n".join(lines), spans)


def _related_gap_actions(decision, policy):
    """Group related methods by typed fit; preserve ties rather than invent a winner."""
    actions = [a for a in dict.fromkeys(decision.hypothesis_actions) if a in policy.workflows]
    outcome = decision.requested_outcome
    subject = outcome.artifact_type if outcome else "unknown"
    requested_roles = set(outcome.regulator_types) - {"unknown"} if outcome else set()
    requested_scale = outcome.granularity if outcome else "unknown"
    compatible = [a for a in actions
                  if requested_roles <= set(policy.workflows[a].output_capability.regulator_types)
                  # An added regulator class is a different scientific question.
                  # Do not suggest miRNA methods without typed miRNA intent.
                  and ("mirna" not in policy.workflows[a].output_capability.regulator_types
                       or "mirna" in requested_roles)
                  and (requested_scale == "unknown" or requested_scale in policy.workflows[a].output_capability.granularities)]
    bases = [a for a in compatible if not set(policy.workflows[a].output_capability.guidance_predecessors) & set(compatible)]
    direct = [a for a in bases if subject in _supported_artifacts(OUTPUT_CAPABILITIES[a])]
    primary = [a for a in direct if OUTPUT_CAPABILITIES[a].artifact_type == subject]
    choices = primary or direct or bases
    def fit(action):
        spec = policy.workflows[action]
        return (
            spec.output_capability.artifact_type != subject,
            len(set(spec.output_capability.regulator_types) - requested_roles),
        )
    # Extra outputs or input burden are not study preferences unless the user
    # stated them. Equal typed fit remains a tie across algorithm philosophies.
    # Stable sort may retain catalog order, never evidence of a better method.
    return [(action, fit(action)) for action in sorted(choices, key=fit)[:3]]


def _conditional_fit(
    capability, *, include_preference: bool = True, include_scope: bool = True,
) -> str:
    """Explain a related method's scope, actual mechanism, and decision tradeoff."""
    tags = capability.selection_tags
    roles = capability.regulator_types
    if "mirna" in roles:
        scope = "Use this only if miRNA-to-gene regulation and a miRNA-target prior are part of the study"
    elif "tf" in roles:
        scope = "Use this if the intended result is TF-to-gene regulation"
    else:
        scope = "Use this if its registered scientific output is the intended result"
    if "leave_one_out_network_inference" in tags:
        scope += " for each sample, using a cohort"
        method = " ".join(method_philosophies_for(tags))
        preference = "Choose it when per-sample network contributions are the scientific target"
    elif "relaxed_graph_matching" in tags:
        method = " ".join(method_philosophies_for(tags))
        preference = "Choose it when an explicit projection-matching loss and tunable regularization matter"
    elif "message_passing" in tags:
        if "mirna" in roles:
            method = (
                "Iterative message passing combines miRNA-target predictions with "
                "target-gene co-expression and TF motif/PPI evidence; other layers "
                "can revise the starting edge support."
            )
            preference = "Choose it when the miRNA layer is part of the biological question"
        else:
            method = (
                "Iterative message passing reconciles the motif seed with TF-TF "
                "interactions and gene co-expression, repeatedly revising TF-gene "
                "edge support across those networks. The edge weights summarize "
                "integrated evidence, not a posterior probability that the motif "
                "prior is reliable."
            )
            preference = "Choose it when consistency across the biological evidence networks matters"
    else:
        method = " ".join(method_philosophies_for(tags))
        if not method:
            premises = algorithmic_assumptions_for(tags)
            method = "; ".join(premises) if premises else "Its registered assumptions must fit the study."
        preference = "Choose it when that mechanism and its stated output match the question"
    opening = f"{scope}. " if include_scope else ""
    return opening + method + (f" {preference}." if include_preference else "")


def _choice_criterion(capability) -> str:
    """Name the meaningful assumption that separates tied methods."""
    tags = capability.selection_tags
    if "leave_one_out_network_inference" in tags:
        return "cohort-derived per-sample network contributions"
    if "relaxed_graph_matching" in tags:
        return "an explicit projection-matching objective and regularization"
    if "message_passing" in tags:
        if "mirna" in capability.regulator_types:
            return "iterative integration that includes miRNA-target predictions"
        return "iterative reconciliation of motif, PPI, and co-expression evidence"
    premises = algorithmic_assumptions_for(tags)
    return premises[0] if premises else "the registered mathematical assumption"


def _tie_explanation(ranked, policy, gap, outcome) -> str:
    leading = [policy.workflows[action].workflow for action, score in ranked
               if score == ranked[0][1]]
    names = " and ".join((", ".join(leading[:-1]), leading[-1])) if len(leading) > 2 else " and ".join(leading)
    if "bayesian" in gap.selection_tags and outcome and outcome.artifact_type == "regulatory_network":
        return (
            f"{names} tie only on the stated output and scope. This does not show "
            "that they are equally robust to a noisy motif prior; neither estimates "
            "its reliability as a posterior probability."
        )
    return (
        f"{names} tie on the stated output and scope. This does not establish "
        "equal accuracy or interchangeable mathematical assumptions."
    )


def _same_philosophy_other_result(decision, policy, gap, ranked, artifact_label) -> str:
    """Registered methods that declare the required philosophy for another result (Log 257).

    Someone asking for a Bayesian treatment of a motif prior will ask about the
    Bayesian workflow next, so say what it estimates instead of omitting it.
    Derived from registry tags and outputs only; it never adds a candidate.
    """
    shown = set(decision.hypothesis_actions) | {action for action, _ in ranked}
    required = set(gap.selection_tags)
    lines = []
    for action, capability in OUTPUT_CAPABILITIES.items():
        shared = required & set(capability.selection_tags)
        if action in shown or action not in policy.workflows or not shared:
            continue
        outputs = " and ".join(
            artifact_label(item)
            for item in sorted(capability.produced_artifacts or {capability.artifact_type})
        )
        scale = " (one per sample)" if set(capability.granularities) == {"sample_specific"} else ""
        notes = method_philosophies_for(shared) or algorithmic_assumptions_for(shared)
        lines.append(f"- **{policy.workflows[action].workflow}** — declared output: {outputs}{scale}."
                     + (" " + " ".join(notes) if notes else ""))
    if not lines:
        return ""
    lead = ("A registered method with that philosophy estimates a different result:"
            if len(lines) == 1 else
            "Registered methods with that philosophy estimate different results:")
    return lead + "\n" + "\n".join(lines)


def _external_references(decision, gap) -> str:
    """Published methods for the missing principle that this agent cannot run (Log 267)."""
    artifact = decision.requested_outcome.artifact_type if decision.requested_outcome else "unknown"
    matches = [ref for ref in EXTERNAL_REFERENCES
               if ref.selection_tags & set(gap.selection_tags)
               and (artifact == "unknown" or artifact in ref.artifact_types)]
    if not matches:
        return ""
    return ("Outside this agent (reference only; it cannot run these):\n"
            + "\n".join(f"- **{ref.name}** ({ref.availability}) — {ref.summary} {ref.source}."
                         for ref in matches))


def render_method_capability_gap(decision, policy, *, artifact_label):
    gap = decision.advisory_capability_gap
    lines = [
        requested_framework_for(
            gap.selection_tags,
            artifact_type=decision.requested_outcome.artifact_type if decision.requested_outcome else "unknown",
        ),
        "No qualified registered workflow fully matches the requested modeling philosophy."
        + (" " + gap.rationale if not gap.rationale.startswith("No qualified") else ""),
    ]
    ranked = _related_gap_actions(decision, policy)
    if external := _external_references(decision, gap):
        lines.append(external)
    if near_miss := _same_philosophy_other_result(decision, policy, gap, ranked, artifact_label):
        lines.append(near_miss)
    tied_first = bool(ranked and len([score for _, score in ranked if score == ranked[0][1]]) > 1)
    probabilistic_regulatory_gap = bool(
        "bayesian" in gap.selection_tags and decision.requested_outcome
        and decision.requested_outcome.artifact_type == "regulatory_network"
    )
    if ranked:
        lines.append(
            "If you relax that requirement, these registered approaches can infer the "
            "requested network through different assumptions:"
            if probabilistic_regulatory_gap else
            "Conditional alternatives, ordered by the stated output and scope if you relax that requirement:"
        )
    if tied_first:
        lines.append(_tie_explanation(ranked, policy, gap, decision.requested_outcome))
    for index, (action, _) in enumerate(ranked):
        spec = policy.workflows[action]
        marker = " (recommend)" if index == 0 and not tied_first else ""
        lines.append(f"{index + 1}. **{spec.workflow}**{marker} — "
                     f"{_conditional_fit(spec.output_capability, include_preference=not tied_first, include_scope=not tied_first)}")
    if ranked:
        if probabilistic_regulatory_gap:
            lines.append(
                "For the probabilistic reliability estimate you asked for, the "
                "hierarchical model above remains the recommendation. If stable "
                "network scores would suffice instead, perturb or replace the motif "
                "prior and compare inferred edges against independent evidence. "
                "Neither algorithm is known from the stated facts to be more robust "
                "for your study."
            )
        else:
            lines.append("These alternatives do not fulfill the requested modeling requirement.")
        if concerns := concern_section(decision, policy, [action for action, _ in ranked]):
            lines.append(concerns)
    if tied_first:
        if not probabilistic_regulatory_gap:
            choices = [
                f"{policy.workflows[action].workflow} for {_choice_criterion(policy.workflows[action].output_capability)}"
                for action, score in ranked if score == ranked[0][1]
            ]
            lines.append("If you can relax the unavailable requirement, which better fits your study: "
                         + "; or ".join(choices) + "?")
    elif decision.clarification_question and not probabilistic_regulatory_gap:
        lines.append(decision.clarification_question)
    lines.append("No files were inspected and no analysis ran.")
    return _ui_text("\n\n".join(lines))
