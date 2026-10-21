"""ROUND-17 (user decision, 2026-10-21): when the registered workflows cannot put a feasible result together, the
turn is declined, and the reply says why -- never a run of what is left.

The h1-h3 gold judged a run whose own setting, size or stated requirement cannot be met as not doable (J44 "set
computing to gpu", L21 GIRAFFE "change the optimizer: learning rate 0.0005", H40, H27 CONDOR "directly on
rnaseq_tpm.tsv ... without building any network first", L13 LIONESS-DRAGON past its size cap), but the check kept a
row of the same run doable beside the row that could not be met -- the run itself once its setting was set apart, an
attached sentence ("Can you set it up that way?", "Per-sample edges to lioness_dragon/edges.tsv ..."), or a
background phrase ("TF activity matrix") -- so the turn ran in part. The a24b gold's opposite reading (MX04, MX05: the
run supported, the setting not) is superseded.

Only a reason code derives from the contract blocks: a not-available row blocks the workflows `blocks` records -- those
`method_fitting` removed for a setting they cannot take or a run limit (sample count, size), or that a setting was set
apart from (`settings_apart`) -- never one removed because the request named another method (`instead`). A doable row
resting on blocked workflows alone is held with those reasons; a row another workflow can still give stays (separate
results stay separate).

Not blocking: a stated requirement the condition check answered violates. gpt-4o-mini answers it wrongly and
consistently on words describing the data (four reads each: M47 "both built on the same genes and the same motif and
PPI priors", C58 "use cobra_out/adjusted_coexpression.tsv", C35, C32 "complete continuous values with no NAs" for
DRAGON), so it keeps M2's own row and never holds the run (H27 stays partial). Nor words naming no allowed choice
(C40 genes_axis, `UNCLEAR_CHOICE`): unsettled, not impossible.
"""

from __future__ import annotations

from ..capability_sheet import entry
from ..contracts.capability_check import CapabilityCheck, CheckedRequirement

__all__ = ["blocked_workflows", "same_run_holds"]

_DOABLE = ("available", "with_step", "partial")


def _hard(row: CheckedRequirement) -> list[str]:
    from ..workflow_conditions import UNCLEAR_CHOICE

    return [reason for reason in row.limits if not reason.endswith(UNCLEAR_CHOICE)]


def blocked_workflows(row: CheckedRequirement) -> list[str]:
    """The workflows a not-available row shows, by a code-derived reason, cannot run as asked."""
    if row.kind != "result" or row.status != "not_available" or not _hard(row):
        return []
    return list(dict.fromkeys(row.blocks))


def same_run_holds(check: CapabilityCheck | None) -> CapabilityCheck | None:
    """The check with every doable row that rests only on blocked workflows held, citing why they cannot run."""
    if check is None:
        return check
    reasons: dict[str, list[str]] = {}
    for row in check.results():
        for workflow in blocked_workflows(row):
            reasons.setdefault(workflow, []).extend(_hard(row))
    if not reasons:
        return check
    requirements, held = [], False
    for row in check.requirements:
        credited = {entry(key).workflow for key in row.delivered_by if entry(key).workflow}
        if row.kind == "result" and row.status in _DOABLE and credited and credited <= reasons.keys():
            why = [reason for workflow in sorted(credited) for reason in dict.fromkeys(reasons[workflow])]
            row = row.model_copy(update={"status": "not_available", "delivered_by": [],
                                         "limits": list(dict.fromkeys([*row.limits, *why])), "blocks": sorted(credited)})
            held = True
        requirements.append(row)
    return check.model_copy(update={"requirements": requirements}) if held else check
