"""The requirement contract check (closed-menu phase 1b, step 1; spec section 3.10, draft 5).

A requirement is how a result must be computed or what it must contain, in the user's words ("with most edges
exactly zero", "a p-value for every edge"). `decide_menu` keeps the candidates meeting at least
`soft_requirements_met` of them and asks whether the ones the contract does not address are musts; it needs a
verdict per candidate workflow -- met, contradicted or not_addressed. Phase 1 had no check, so every requirement was
asked about (7 of 38 wrong bench calls).

One call reads every (requirement, candidate workflow) pair against that workflow's contract: its YAML policy text
(`contract_text`: description, conventions, settings, guidance notes, handoff contract) and its capability-sheet
lines (what each result is and how to read it; what it does not give and why). For each pair the model first copies
the contract clause that speaks to the requirement, then gives the verdict. Code keeps met or contradicted only when
that clause is verbatim in that workflow's text; anything else is not_addressed, which is asked, never assumed.

Phase 1b: offline only; nothing in the live path calls it.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, create_model

from ..capability_sheet import sheet_entries
from ..contract_text import contract_text, normalized
from ..contracts.menu_reading import MenuReading
from ..method_names import registered_workflows
from .menu_reader import ReadReport, _strict

__all__ = ["MAX_PAIRS", "RequirementPair", "apply_verdicts", "requirement_model", "requirement_pairs",
           "requirement_text", "workflow_contract"]

MAX_PAIRS = 18
_FORBID = ConfigDict(extra="forbid")
Verdict = Literal["met", "contradicted", "not_addressed"]


@dataclass(frozen=True, slots=True)
class RequirementPair:
    item: int
    index: int
    quote: str
    workflow: str


@lru_cache(maxsize=1)
def _policy():
    from ..policy import ProjectPolicyLoader
    return ProjectPolicyLoader().load()


@lru_cache(maxsize=32)
def workflow_contract(workflow: str) -> str:
    """The words a verdict's clause must come from: the workflow's policy contract and its sheet lines."""
    lines = [contract_text(_policy().workflows[registered_workflows()[workflow]])]
    for key, entry in sheet_entries().items():
        if entry.workflow != workflow:
            continue
        if entry.kind == "produces":
            lines.append(f"- gives: {entry.text}" + (f" {entry.reading}" if entry.reading else ""))
        else:
            lines.append(f"- does not give: {entry.text}" + (f" {entry.why_not}" if entry.why_not else ""))
    return "\n".join(lines)


def requirement_pairs(reading: MenuReading, candidates) -> list[RequirementPair]:
    """Every requirement of a thing asked, with every candidate workflow (at most `MAX_PAIRS`)."""
    known = registered_workflows()
    pairs = [RequirementPair(item, index, requirement.quote, workflow)
             for item, wanted in enumerate(reading.wanted) if wanted.form == "deliverable"
             for index, requirement in enumerate(wanted.requirements)
             for workflow in candidates if workflow in known]
    return pairs[:MAX_PAIRS]


def requirement_text(task: str, pairs: list[RequirementPair]) -> str:
    workflows = list(dict.fromkeys(pair.workflow for pair in pairs))
    contracts = "\n\n".join(workflow_contract(workflow) for workflow in workflows)
    numbered = "\n".join(f'p{n}. requirement "{pair.quote}" -- workflow {pair.workflow}'
                         for n, pair in enumerate(pairs, 1))
    return f"REQUEST:\n{task}\n\nCONTRACTS:\n{contracts}\n\nPAIRS:\n{numbered}"


@lru_cache(maxsize=32)
def requirement_model(pairs: int) -> type[BaseModel]:
    pair = create_model(
        "RequirementVerdict", __config__=_FORBID,
        clause=(str, Field(description="The exact words of that workflow's contract that speak to the requirement; "
                                       "empty when none does.")),
        verdict=(Verdict, Field(description="met: the clause says the workflow's result meets the requirement; "
                                            "contradicted: the clause says it cannot; not_addressed: the contract "
                                            "does not say.")),
    )
    fields = {f"p{n}": (pair, Field(description=f"Pair {n}.")) for n in range(1, pairs + 1)}
    return _strict(create_model("RequirementVerdicts", __config__=_FORBID, **fields))


def apply_verdicts(reading: MenuReading, pairs: list[RequirementPair], payload) -> tuple[MenuReading, ReadReport]:
    """The reading with each pair's verdict; met or contradicted without its clause in the contract is not_addressed."""
    raw = payload.model_dump(mode="json") if isinstance(payload, BaseModel) else dict(payload)
    report = ReadReport()
    wanted = [item.model_copy(deep=True) for item in reading.wanted]
    for n, pair in enumerate(pairs, 1):
        answer = raw.get(f"p{n}") or {}
        verdict, clause = answer.get("verdict", "not_addressed"), answer.get("clause") or ""
        if verdict in ("met", "contradicted") and (
                not normalized(clause) or normalized(clause) not in normalized(workflow_contract(pair.workflow))):
            report.dropped.append(f"p{n}: {verdict} for {pair.workflow} without a clause of its contract "
                                  f"({clause[:60]!r}) -> not_addressed")
            verdict = "not_addressed"
        requirement = wanted[pair.item].requirements[pair.index]
        requirement.verdicts[pair.workflow] = verdict
        if verdict != "not_addressed":
            report.filled.append(f"p{n}: \"{pair.quote[:50]}\" {verdict} by {pair.workflow}")
    return reading.model_copy(update={"wanted": wanted}), report
