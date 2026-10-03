"""Replies for advice drawn from a named folder's file contents (Log 154)."""

from __future__ import annotations

from ..presentation import _ui_text_with_user_data, user_data_token

__all__ = ["above_closing", "inspection_footer", "render_inspected_recommendation", "with_inspection_footer"]

_ROLE_LABELS = {
    "expression_file": "expression matrix",
    "motif_file": "TF-motif prior",
    "ppi_file": "protein-interaction prior",
    "mirna_file": "miRNA list",
}
_NOT_INSPECTED = "No files were inspected and no analysis ran."


def above_closing(text: str, block: str) -> str:
    """`block` as its own paragraph above the closing one.

    The closing paragraph may begin with another closing sentence ("This is
    workflow guidance only; ..."); splitting it put an added paragraph
    between the two (Test 6, 2026-10-03).
    """
    paragraphs = text.split("\n\n")
    closing = next((i for i, part in enumerate(paragraphs) if _NOT_INSPECTED in part), None)
    if closing is None:
        return text + "\n\n" + block
    return "\n\n".join([*paragraphs[:closing], block, *paragraphs[closing:]])


def inspection_footer(directories: list[str]) -> str:
    folders = ", ".join(f"`{item}`" for item in directories)
    return (
        f"I read the files in {folders} only to check which inputs they contain; "
        "no analysis ran."
    )


def with_inspection_footer(text: str | None, directories: list[str]) -> str | None:
    """Replace the 'no files were inspected' footer once routing read a folder."""
    if text is None or not directories:
        return text
    return text.replace(_NOT_INSPECTED, inspection_footer(directories))


def render_inspected_recommendation(
    decision, policy, spec, details: list[str], downstream: str = "",
) -> str:
    """Form A: which files validated for which roles, and what nothing validated as.

    The folder path and file names are the user's own data and may be in any
    language, so they enter through placeholders after the template is checked.
    """
    recommendation = decision.advisory_recommendation
    user_data: list[str] = []

    def quoted(value: str) -> str:
        user_data.append(value)
        return user_data_token(len(user_data) - 1)

    folder = recommendation.conditions[0].text_span
    validated = [
        item.value.removeprefix("validated:").split("=", 1)
        for item in recommendation.conditions if item.value.startswith("validated:")
    ]
    missing = [
        item.value.removeprefix("missing:")
        for item in recommendation.conditions if item.value.startswith("missing:")
    ]
    found = ", ".join(
        f"`{quoted(name)}` as the {_ROLE_LABELS.get(field, field)}" for field, name in validated
    )
    missing_text = " or ".join(_ROLE_LABELS.get(field, field) for field in missing)
    names = dict(validated)
    mixed = [
        item.value.split(":", 1)[1] for item in recommendation.conditions
        if item.value.startswith("mixed_prior:")
    ]
    if mixed:
        reason = (
            f"`{quoted(names.get('motif_file', ''))}` lists {mixed[0]} regulator(s) that "
            f"`{quoted(names.get('mirna_file', ''))}` validates as miRNAs, so the prior mixes "
            f"TF and miRNA regulators and **{spec.workflow}** models both."
        )
        other_text = "would read every regulator in the prior as a transcription factor."
    else:
        reason = f"No file there validates as a {missing_text}, so **{spec.workflow}** fits."
        other_text = f"would also need a {missing_text}."
    lines = [
        f"By content, the files in `{quoted(folder)}` validate as a complete input set for "
        f"**{spec.workflow}**: {found}. {reason}",
        "\n".join(details),
    ]
    others = [
        f"- **{policy.workflows[action].workflow}** — {other_text}"
        for action in decision.hypothesis_actions
        if action != recommendation.action and action in policy.workflows
    ]
    if others:
        lines.append("Other compatible option(s):\n" + "\n".join(others))
    if downstream:
        lines.append(downstream.rstrip("\n"))
    if decision.clarification_question:
        lines.append(decision.clarification_question)
    lines.append(inspection_footer(
        [quoted(item) for item in (decision.inspected_directories or [folder])]
    ))
    return _ui_text_with_user_data("\n\n".join(lines), user_data)
