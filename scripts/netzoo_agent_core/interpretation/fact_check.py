"""Core decision spec, phase 2 (section 6): the fact agent's proposals, held to rules R1-R6 in code.

Round p0/p1 (2026-10-15): asking was 3/15 and 2/15. Every deciding fact that was asked was one of the 11 fixed
`needed_facts.DIMENSIONS`; the rest (which file this is, a log transform, a feature count, a panel size, which of two
readings) could not be asked at all. The agent may propose any fact, but code keeps one only when:

- R1 the user's words for it are in the request, and the capability check -- a second, independent reading --
  read the same words as the user not knowing or not having decided something (`CapabilityCheck.uncertain_quotes`;
  dev set m3: the agent alone asked on 10-20 of 27 supported requests);
- R2 the contract words that make it decide are in that candidate workflow's contract;
- R3 a yes and a no lead to different outcomes;
- R4 the reading did not type it as stated (its words are not inside a definite condition, method or setting);
- R5 when the workflow's own input check covers it and the turn runs on named files, it is said, not asked;
- R6 at most two are asked, in the request's order.

A fact is never asked because a contract field exists (spec boundary 1): only what the user shows they are unsure of.
"""

from __future__ import annotations

from workflow_registry import OUTPUT_CAPABILITIES, workflow_name

from ..capability_sheet import entry
from ..contract_text import contract_text, normalized
from ..contracts.core_decision import FactQuestion
from ..contracts.fact_check import FactCheck, RejectedFact
from .request_spans import _span

__all__ = ["FACT_INSTRUCTIONS", "fact_candidates", "fact_messages_text", "kept_facts"]

MAX_CANDIDATES = 4
MAX_ASKED = 2

FACT_INSTRUCTIONS = (
    "Return only the FactProposals structure. You are given a user's request and the contracts of the registered "
    "workflows that may answer it.\n\n"
    "List each fact about the user's data or the wanted result that BOTH (1) the request itself shows the user is "
    "unsure of -- they say they do not know it or have not decided it, give two incompatible versions of it, or use "
    "words that can be read two ways -- AND (2) decides, by a listed contract, whether the request can be done or "
    "which workflow does it.\n\n"
    "For each fact: copy the user's words exactly; name the workflow; copy the contract words that make the fact "
    "decide it exactly as listed; ask one short question whose yes answer leads to the yes outcome; give both "
    "outcomes. Do not list a fact the request states, a fact the user does not show they are unsure of, a missing "
    "file, or a fact whose answer would not change the outcome. An empty list is a normal answer."
)


def _workflow_actions(policy) -> dict[str, str]:
    return {spec.workflow.upper(): action for action, spec in policy.workflows.items()}


def fact_candidates(decision, policy) -> list[str]:
    """The run actions that may answer the request: the check's credited ones, then routing's (at most four)."""
    check = decision.capability_check
    keys = [key for row in (check.requirements if check is not None else [])
            for key in [*row.delivered_by, *(k for found in row.outcomes.values() for k in found)]]
    actions = []
    for key in keys:
        try:
            actions.append(entry(key).action)
        except KeyError:
            continue
    actions += [*decision.matched_actions, *decision.hypothesis_actions, *decision.recommended_actions]
    if decision.action.startswith("run_"):
        actions.insert(0, decision.action)
    return [a for a in dict.fromkeys(actions) if a and a in policy.workflows and a in OUTPUT_CAPABILITIES][:MAX_CANDIDATES]


def fact_messages_text(task: str, actions: list[str], policy) -> str:
    contracts = "\n\n".join(contract_text(policy.workflows[action]) for action in actions)
    return f"REQUEST:\n{task}\n\nCONTRACTS OF THE WORKFLOWS THAT MAY ANSWER IT:\n{contracts}"


def _outcome(kind: str, other: str, names: set[str], own: str) -> str | None:
    if kind == "other_workflow":  # R3: a legal value names another listed workflow (round p2 C31: "GIRAFFE instead of GIRAFFE")
        name = other.strip().upper()
        return f"other_workflow:{name}" if name in names and name != own.strip().upper() else None
    return kind


def _overlaps(a: str, b: str) -> bool:
    a, b = normalized(a), normalized(b)
    return bool(a and b) and (a in b or b in a)


def _inside(quote: str, outer: list[str]) -> bool:
    q = normalized(quote)
    return any(q and q in normalized(item) for item in outer)


def kept_facts(task: str, proposals, decision, policy, *, model: str = "") -> FactCheck:
    """R1-R6 over the agent's proposals; what is kept is what the turn may ask (or say, R5)."""
    actions = fact_candidates(decision, policy)
    by_name = _workflow_actions(policy)
    names = set(by_name)
    check = decision.capability_check
    stated = list(getattr(check, "stated_quotes", []) or [])
    uncertain = list(getattr(check, "uncertain_quotes", []) or [])
    running = decision.action.startswith("run_") or bool(getattr(decision, "execution_requested", False))
    kept, rejected, seen = [], [], set()
    for proposal in getattr(proposals, "facts", None) or []:
        raw = proposal.model_dump()

        def reject(rule):
            rejected.append(RejectedFact(rule=rule, proposal=raw))

        span = _span(task, proposal.user_quote) if proposal.user_quote.strip() else None
        if span is None:
            reject("R1 user words not in the request")
            continue
        if not any(_overlaps(proposal.user_quote, quote) for quote in uncertain):
            reject("R1 the check did not read these words as the user being unsure")
            continue
        action = by_name.get(proposal.workflow.strip().upper())
        if action not in actions:
            reject("R2 not a candidate workflow")
            continue
        spec = policy.workflows[action]
        if not proposal.contract_quote.strip() or normalized(proposal.contract_quote) not in normalized(contract_text(spec)):
            reject("R2 contract words not in its contract")
            continue
        yes = _outcome(proposal.yes_outcome, proposal.yes_workflow, names, spec.workflow)
        no = _outcome(proposal.no_outcome, proposal.no_workflow, names, spec.workflow)
        if yes is None or no is None or yes == no:
            reject("R3 yes and no do not lead to different outcomes")
            continue
        if _inside(proposal.user_quote, stated):
            reject("R4 the reading typed it as stated")
            continue
        if span in seen:
            reject("R6 the same words already ask a fact")
            continue
        seen.add(span)
        settled = running and any(normalized(item) in normalized(proposal.contract_quote)
                                  or normalized(proposal.contract_quote) in normalized(item)
                                  for item in spec.input_checks)
        workflows = [spec.workflow, *(o.split(":", 1)[1] for o in (yes, no) if o.startswith("other_workflow:"))]
        kept.append((span[0], FactQuestion(
            question=proposal.question.strip(), user_quote=task[span[0]:span[1]], workflows=list(dict.fromkeys(workflows)),
            contract_quote=proposal.contract_quote.strip(), uncertainty=proposal.uncertainty, if_yes=yes, if_no=no,
            settled_by_input_check=settled)))
    kept.sort(key=lambda item: item[0])
    asked = [fact for _, fact in kept if not fact.settled_by_input_check]
    said = [fact for _, fact in kept if fact.settled_by_input_check]
    for fact in asked[MAX_ASKED:]:
        rejected.append(RejectedFact(rule="R6 more than two questions", proposal=fact.model_dump()))
    return FactCheck(status="checked", model=model, candidates=[workflow_name(a) for a in actions],
                     accepted=[*asked[:MAX_ASKED], *said], rejected=rejected)
