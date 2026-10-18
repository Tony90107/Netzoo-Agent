"""Hybrid hard gates on the live path's DO (the user's options-first decision, 2026-10-18, step 7).

The live system's main failure on the fresh blind set h1 was committing, in part, to what a workflow's contract rules
out (H18 an unregistered DRAGON penalty, H27 CONDOR with no network, H40 GIRAFFE settings). The closed-menu reader's
hard-condition components judge them better. Before anything the live call offers is treated as runnable, these
gates read the request once more against only the offered workflows' limits (`menu_focus.gate_model`), check the
user's requirements against those workflows' contracts with verified contract clauses (`menu_requirements`), and judge
each workflow's hard conditions in code (`menu_decision.workflow_gate`):

- a workflow some condition rules out is no longer offered; with none left the call is DECLINE (basis `hybrid_gate`),
  each part saying "NetZoo cannot run X for this because ..." with the contract's words;
- a requirement no offered workflow's contract addresses, while fewer than 9 in 10 are met, is asked as a must
  (ASK, basis `hybrid_requirement`); the live path's own questions are never replaced.

Pure code here; the calls are `graph.hybrid_gate_call`.
"""

from __future__ import annotations

from ..contracts.core_decision import CoreDecision, DeclinedPart, FactQuestion
from ..contracts.menu_reading import MenuReading, Requirement, Wanted
from .menu_decision import GateVerdict
from .menu_focus import gate_requirements, merge_focused
from .menu_reply import _reason

__all__ = ["gate_reading", "gated_core"]


def gate_reading(payload, task: str, workflows: tuple[str, ...]) -> MenuReading:
    """The gate read as a `MenuReading`: limits, data, conditions, unsupported settings and requirements."""
    reading, _report = merge_focused(MenuReading(wanted=[Wanted(quote="")]), payload, task, workflows)
    requirements = [Requirement(quote=quote) for quote in gate_requirements(payload, task)]
    return reading.model_copy(update={"wanted": [reading.wanted[0].model_copy(update={"requirements": requirements})]})


def _line(verdict: GateVerdict) -> str:
    line = f"NetZoo cannot run {verdict.workflow} for this because {'; '.join(_reason(r) for r in verdict.reasons)}."
    return " ".join([line, *(f'The contract says: "{words}"' for words in verdict.contract)])


def gated_core(core: CoreDecision, verdicts: dict[str, GateVerdict]) -> CoreDecision:
    """The live call after the gates (only a DO is ever changed)."""
    if core.kind != "DO" or not verdicts:
        return core
    blocked = {name: v for name, v in verdicts.items() if v.reasons}
    kept = [name for name in core.workflows if name not in blocked]
    evidence = {**core.evidence, "hybrid_gate": {
        "judged": sorted(verdicts), "blocked": {name: v.reasons for name, v in blocked.items()},
        "must_ask": {name: v.must_ask for name, v in verdicts.items() if v.must_ask},
        "unconfirmed": {name: v.unconfirmed for name, v in verdicts.items() if v.unconfirmed}}}
    parts = [DeclinedPart(quote="", reasons=v.reasons, line=_line(v)) for v in blocked.values()]
    if not kept:
        return CoreDecision(kind="DECLINE", basis="hybrid_gate", workflows=sorted(blocked), declined=parts,
                            evidence=evidence)
    asks = [name for name in kept if name in verdicts and verdicts[name].must_ask]
    if asks and len(asks) == len([name for name in kept if name in verdicts]):
        quotes = list(dict.fromkeys(q for name in asks for q in verdicts[name].must_ask))
        facts = [FactQuestion(question=f'Is this a must for your analysis: "{quote}"? The contract of '
                                       f'{", ".join(name for name in asks if quote in verdicts[name].must_ask)} '
                                       f"does not say it meets it.",
                              user_quote=quote, workflows=[name for name in asks if quote in verdicts[name].must_ask])
                 for quote in quotes]
        return CoreDecision(kind="ASK", basis="hybrid_requirement", workflows=kept, facts=facts,
                            declined=[*core.declined, *parts], evidence=evidence)
    return core.model_copy(update={"workflows": kept, "declined": [*core.declined, *parts],
                                   "run_allowed": core.run_allowed and not blocked, "evidence": evidence})
