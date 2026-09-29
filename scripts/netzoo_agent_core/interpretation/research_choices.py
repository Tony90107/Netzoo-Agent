"""Explain each distinct registered method once, and ask only real choices."""

from __future__ import annotations

from workflow_registry import GUIDANCE_COMPOSITIONS, OUTPUT_CAPABILITIES

from ..presentation import _ui_text_with_user_data, user_data_token
from .scientific_guidance import method_paragraphs, render_scientific_guidance
from .inspected_answers import with_inspection_footer


def render_research_choices(decision, policy, *, task):
    if decision.action != "no_tool" or decision.should_execute:
        return None
    from ..graph.condition_recommender import _quote_grounded

    items = [
        h
        for h in decision.stated_hypotheses
        if _quote_grounded(task, h.text_span)
        and (
            h.basis == "unsupported"
            or h.basis in policy.workflows
            and h.basis in OUTPUT_CAPABILITIES
        )
    ]
    if decision.stated_hypotheses and not items:
        return None  # Old quotes cannot become evidence for the next user turn.
    actions = list(dict.fromkeys(h.basis for h in items if h.basis != "unsupported"))
    if not items:
        outcome = decision.requested_outcome
        if decision.capability_match_status != "ambiguous" and not (
            outcome is not None and outcome.artifact_type == "unknown"
        ):
            return None
        actions = [
            a
            for a in dict.fromkeys(
                [*decision.hypothesis_actions, *decision.matched_actions]
            )
            if a in policy.workflows and a in OUTPUT_CAPABILITIES
        ]
        if not actions:
            actions = [a for a in policy.workflows if a in OUTPUT_CAPABILITIES]
    comparison = len(actions) >= 2
    gaps = list(dict.fromkeys(h.text_span for h in items if h.basis == "unsupported"))
    if len(actions) == 1 and not gaps:
        single = decision.model_copy(
            update={
                "matched_actions": actions,
                "capability_match_status": "exact",
                "clarification_question": None,
            }
        )
        if explanation := render_scientific_guidance(single, policy, task=task):
            return explanation
    sections, quotes, notes = [], [], []
    if comparison:
        sections.append(
            "There are different analyses to consider here. The useful distinction is "
            "what each method assumes and what you want to learn from the data."
        )
    # Candidate identity, not the number of quoted fragments, defines a choice.
    # A method shared by several scientific questions is explained only once.
    endpoints = set()
    for action in actions:
        attached = [h for h in items if h.basis == action]
        spans = list(dict.fromkeys(h.text_span for h in attached))
        if comparison and spans:
            labels = []
            for span in spans:
                quotes.append(span)
                labels.append("“" + user_data_token(len(quotes) - 1) + "”")
            sections.append("For " + " and ".join(labels) + ":")
        sections.extend(method_paragraphs(action, policy, task=task))
        targets = {h.target_artifact for h in attached}
        endpoints.update(targets)
        for (target, _), composition in GUIDANCE_COMPOSITIONS.items():
            if target in targets and action in dict(composition.sources):
                sections.append(
                    "To turn this into patient subtypes, use "
                    + dict(composition.sources)[action]
                    + ". "
                    + composition.outside_step
                )
                notes.extend(composition.notes)
    for span in gaps:
        quotes.append(span)
        sections.append(
            "For “" + user_data_token(len(quotes) - 1) + "”, no registered workflow "
            "meets the stated requirement. That part needs a clearer measurement or an external method."
        )
    sections.extend(dict.fromkeys(notes))
    if "sample_cluster_assignment" in endpoints:
        sections.append(
            "To use subtypes for chemotherapy resistance or another clinical outcome, "
            "you would also need outcome labels matched to the patients. Check cluster stability "
            "and confounding, then evaluate prediction on held-out patients. Fit feature selection "
            "and cohort-dependent network estimation within the training split to avoid information leakage."
        )
    sections.append("No files were inspected and no analysis ran.")
    if comparison:
        sections.append(
            "Which scientific question should we start with, and which of these inputs do you have? "
            "We can also investigate the hypotheses in parallel."
        )
    elif gaps:
        sections.append(
            "What measurement would let you distinguish the remaining explanation?"
        )
    return with_inspection_footer(
        _ui_text_with_user_data("\n\n".join(sections), quotes),
        decision.inspected_directories,
    )
