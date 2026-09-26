"""Form A for an advisory recommendation from a named folder's file names (Log 152)."""

from __future__ import annotations

from workflow_registry import OUTPUT_CAPABILITIES

from ..presentation import _ui_text

__all__ = ["render_inspected_recommendation"]


_INSPECTED_PRIOR_LABELS = {
    "motif_prior": "TF-motif prior",
    "ppi_prior": "protein-interaction prior",
    "mirna_prior": "miRNA list",
}


def render_inspected_recommendation(decision, policy, spec, details: list[str]) -> str:
    """Form A from a named folder's file names (Log 152); contents are never read."""
    recommendation = decision.advisory_recommendation
    folder = recommendation.conditions[0].text_span
    missing = [item.value.removeprefix("missing:") for item in recommendation.conditions]
    missing_text = " or ".join(_INSPECTED_PRIOR_LABELS.get(item, item) for item in missing)
    needs = OUTPUT_CAPABILITIES[recommendation.action].required_input_artifacts
    has_text = " and ".join(_INSPECTED_PRIOR_LABELS.get(item, item) for item in sorted(needs))
    lines = [
        f"The file names in `{folder}` look like a {has_text}, and none looks like a "
        f"{missing_text}, so **{spec.workflow}** fits: it needs no {missing_text}.",
        "\n".join(details),
    ]
    others = [
        f"- **{policy.workflows[action].workflow}** — would also need a "
        + " and ".join(
            _INSPECTED_PRIOR_LABELS.get(item, item)
            for item in sorted(OUTPUT_CAPABILITIES[action].required_input_artifacts - needs)
        ) + "."
        for action in decision.hypothesis_actions
        if action != recommendation.action and action in policy.workflows
        and action in OUTPUT_CAPABILITIES
        and OUTPUT_CAPABILITIES[action].required_input_artifacts - needs
    ]
    if others:
        lines.append("Other compatible option(s):\n" + "\n".join(others))
    if decision.clarification_question:
        lines.append(decision.clarification_question)
    lines.append(
        f"Only the file names in `{folder}` were listed; no file contents were read "
        "and no analysis ran."
    )
    return _ui_text("\n\n".join(lines))
