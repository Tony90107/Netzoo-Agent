"""Interpretation choices (user decision 2026-10-19; hybrid spec section 4): what keeps the workflow but changes what
its result means, read by code from `judgment_defaults.choices` -- never by the reader.

`disclosures_for` writes the default-and-disclose lines (and the draft-5 defaults and input checks an unstated B4
condition takes) for a run; `confirm_items` lists the must-confirm choices a run triggers, for its confirmation.
"""

from __future__ import annotations

from ..contracts.menu_reading import MenuReading
from ..judgment_defaults import JudgmentDefaults, judgment_defaults
from .menu_decision import _Context

__all__ = ["confirm_items", "disclosures_for"]


def _choice_applies(ctx: _Context, choice) -> bool:
    """Whether a must-confirm choice's trigger holds for what the reading says."""
    reading = ctx.reading
    if choice.trigger == "groups_mentioned":
        return bool(reading.groups)
    if choice.trigger == "batch_with_comparison":
        compared = bool(reading.groups) or any(w.compare.known() in ("describe", "test") for w in reading.wanted)
        return bool({"batch", "site"} & set(reading.covariates)) and compared
    if choice.trigger == "several_covariates":
        return len(reading.covariates) >= 2 or ("COBRA" in ctx.named and len(ctx.named) >= 2)
    if choice.trigger == "three_or_more_layers":
        return ctx.layers >= 3
    return False


_CHECKED = {"samples_matched": "Whether both layers come from the same samples is checked from your files (sample IDs) "
                               "before the run.",
            "input_network": "Whether your network file holds regulator-to-gene edges is checked before the run."}


def disclosures_for(reading: MenuReading, workflows, table: JudgmentDefaults | None = None) -> list[str]:
    """Code-written lines for a run (hybrid spec 4): the default interpretation choices of these workflows (unless
    the user set that control), the draft-5 defaults an unstated B4 condition takes, and the input checks that settle
    the others -- never a model's words (user decisions 2026-10-19)."""
    table = table or judgment_defaults()
    lines, workflows = [], list(workflows)
    stated = {s.control for s in reading.settings if not s.unsure}
    for choice in table.choices.values():
        if choice.policy == "default_disclose" and set(choice.workflows) & set(workflows) \
                and not stated & set(choice.unless_settings):
            lines.append(choice.disclose)
    for workflow in workflows:
        for name in table.b4_conditions.get(workflow, ()):
            if name in reading.conditions or name.startswith("setting:"):
                continue
            dimension = table.dimensions[name]
            if dimension.policy == "default":
                label = dimension.options.get(dimension.value, str(dimension.value))
                lines.append(f"Assumed for {workflow}: {label[0].lower()}{label[1:]} (the default; say so if not).")
            elif name in _CHECKED:
                lines.append(_CHECKED[name])
    return list(dict.fromkeys(lines))


def confirm_items(reading: MenuReading, workflows, task: str = "", table: JudgmentDefaults | None = None) -> list[str]:
    """The must-confirm interpretation choices a run of these workflows triggers, listed at run confirmation (hybrid
    spec 4): each one keeps the workflow but changes what the result means."""
    table = table or judgment_defaults()
    ctx = _Context(reading, table, task)
    return [choice.question for choice in table.choices.values()
            if choice.policy == "must_confirm" and set(choice.workflows) & set(workflows)
            and _choice_applies(ctx, choice)]
