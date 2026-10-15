"""The core decision (spec docs/superpowers/specs/2026-10-15-core-decision-design.md).

`decide_core` reads the turn's final `TaskDecision` -- the routing reading, the capability check and the run
verdict -- and makes the turn's four-way call: clarify the goal, ask a deciding fact, decline, or do. It makes no
model call; `classify_task` writes it on the decision and in the trace (`core.decision`), and `respond` records
which reply answered beside it (`core.view`). Phase 1 acts on CLARIFY (`with_core` holds the turn, and the CLARIFY
reply answers it); the other kinds still mirror today's replies (phase 0, shadow).

Rules, in the spec's order of precedence:

1. UNCHECKED -- routing failed closed with nothing routed (unless the check confirmed a full gap, which the reply
   still gives: round p0 C10, C22, C37, C49), the check could not confirm what it read, or the run was held because
   the check could not confirm or read it.
2. CLARIFY (phase 1, spec section 5) -- the check's confirmed reading says the request names no result
   (`purpose_only`), or the result it names is in no requirement the check read; a tool request is never held.
3. ASK -- a result waits on a fact the user said they do not know (`needs_fact`), or the run was held for it.
4. DECLINE -- every result read is not available (a full gap), a run was held on a gap, routing found the request
   unsupported with nothing read, or the request names a method combination no workflow implements.
5. CLARIFY (phase 0) -- no result was read, nothing is run and routing offered no workflow.
6. DO -- otherwise: a run, a workflow the check or routing gives, or several to choose from; `partial` when some
   results are declined, `run_allowed` only for a run the verdict approves.

Phase 0 mirrored the replies as they were; m3's labelled sessions were its offline check (research log).
"""

from __future__ import annotations

from workflow_registry import OUTPUT_CAPABILITIES, workflow_name

from ..capability_sheet import entry, produced_text
from ..contracts.capability_check import APPROVING_RUN_VERDICTS
from ..contracts.core_decision import ClarifyNeed, CoreDecision, DeclinedPart, FactQuestion
from .needed_facts import _question

__all__ = ["decide_core", "with_core"]

_FAILED_BASES = frozenset({"semantic_validation_recovery", "provider_unavailable"})
_TOOL_ACTIONS = frozenset({"download_string", "web_search", "query_context7"})
_READ = frozenset({"available", "with_step", "partial", "not_available", "needs_fact"})
_GIVEN = frozenset({"available", "with_step", "partial"})
_UNCHECKED_HOLDS = frozenset({"unread", "unconfirmed"})


def _workflow(key: str) -> str:
    try:
        found = entry(key)
    except KeyError:  # an action name, or a sheet key this sheet no longer has: its workflow prefix
        return workflow_name(key) if key.startswith("run_") else key.split(".")[0].replace("_", "-").upper()
    return found.workflow or (workflow_name(found.action) if found.action else key)


def _names(keys) -> list[str]:
    return list(dict.fromkeys(_workflow(key) for key in keys if key))


def _routed(decision) -> list[str]:
    actions = [*decision.matched_actions, *decision.hypothesis_actions, *decision.recommended_actions]
    if decision.action not in ("no_tool", "", None):
        actions.insert(0, decision.action)
    return list(dict.fromkeys(workflow_name(action) for action in actions if action and action != "no_tool"))


def _failed_closed(decision, reason_code: str) -> bool:
    return not _routed(decision) and decision.action == "no_tool" and (
        reason_code in ("semantic_fallback", "budget_fallback", "research_choices_unavailable")
        or decision.confidence <= 0.0 and decision.match_basis in _FAILED_BASES)


def _declined(rows) -> list[DeclinedPart]:
    return [DeclinedPart(quote=row.quote, reasons=[*row.limits, *row.violations],
                         alternatives=_names([*row.instead, *row.defaults]))
            for row in rows if row.status == "not_available"]


def _facts(check) -> list[FactQuestion]:
    rows = check.needed_facts() if check is not None else []
    return [FactQuestion(question=_question(row), user_quote=row.unknown_quote, depends_on=row.depends_on or "",
                         workflows=_names(key for keys in row.outcomes.values() for key in keys),
                         outcomes={value: _names(keys) for value, keys in row.outcomes.items()})
            for row in rows]


def _overlaps(a: str, b: str) -> bool:
    a, b = a.casefold().strip(), b.casefold().strip()
    return bool(a and b) and (a in b or b in a)


def _goal_unclear(check) -> bool:
    """Spec section 5: the request names no result, by the check's own confirmed reading and its verified words."""
    if check is None or check.unconfirmed() or not check.goal_quote:
        return False
    if check.goal == "purpose_only":
        return True
    asked = [row.quote for row in check.requirements if row.kind in ("result", "about_methods")]
    return check.goal == "result_named" and not any(_overlaps(check.goal_quote, quote) for quote in asked)


def _clarify_need(decision, check) -> ClarifyNeed:
    """The results the request's stated data can give -- listed as possible, never as fitting."""
    stated = {*decision.guidance_input_artifacts,
              *(artifact for hypothesis in decision.outcome_hypotheses
                for artifact in hypothesis.outcome.input_artifacts)} - {"unknown"}
    actions = [action for action, capability in OUTPUT_CAPABILITIES.items()
               if not stated or capability.input_artifacts & stated]
    actions = [action for action in actions if produced_text(action)] or list(OUTPUT_CAPABILITIES)
    question = "Which of these results do you want, or what question should the analysis answer?"
    if not stated:
        question += (" And what data do you have (for example expression, motif and PPI priors, miRNAs, mutations, "
                     "or a second omics layer)?")
    return ClarifyNeed(missing="result" if stated else "both", candidates=[workflow_name(a) for a in actions],
                       inputs=sorted(stated), question=question, goal_quote=check.goal_quote if check else "")


def with_core(decision, core: CoreDecision):
    """The decision a phase-1 call leaves: CLARIFY selects, refuses and runs nothing; the other kinds change nothing."""
    if core.kind != "CLARIFY":
        return decision.model_copy(update={"core": core})
    return decision.model_copy(update={
        "core": core, "action": "no_tool", "should_execute": False, "execution_requested": False,
        "intent_type": "answer_question", "matched_actions": [], "recommended_actions": [],
        "hypothesis_actions": [], "alternative_actions": [], "capability_match_status": "ambiguous",
        "clarification_question": core.clarify.question if core.clarify else None,
        "reason": "The request names no result yet; the goal is asked before any workflow is chosen."})


def decide_core(decision, task: str = "", *, reason_code: str = "") -> CoreDecision:
    """The turn's four-way call, read from its final decision."""
    from ..routing.method_rejections import unsupported_algorithm_request

    check = decision.capability_check
    verdict = decision.run_verdict
    results = check.results() if check is not None else []
    read = [row for row in results if row.status in _READ]
    outcome = decision.requested_outcome
    evidence = {
        "action": decision.action, "match_status": decision.capability_match_status,
        "artifact_type": getattr(outcome, "artifact_type", None), "reason_code": reason_code,
        "rows": [[row.kind, row.status] for row in (check.requirements if check is not None else [])],
        "check_unconfirmed": bool(check is not None and check.unconfirmed()),
        "goal": [check.goal, check.goal_quote] if check is not None else None,
        "run_verdict": None if verdict is None else {"verdict": verdict.verdict, "held": verdict.held},
    }

    def call(kind, basis, **fields) -> CoreDecision:
        return CoreDecision(kind=kind, basis=basis, evidence=evidence, **fields)

    confirmed_gap = check is not None and check.full_gap and not check.unconfirmed()
    if _failed_closed(decision, reason_code) and not confirmed_gap:  # p0: a confirmed gap is still answered
        return call("UNCHECKED", "routing_failed")
    if verdict is not None and verdict.held and verdict.verdict in _UNCHECKED_HOLDS:
        return call("UNCHECKED", f"run_held_{verdict.verdict}", workflows=_routed(decision))
    if decision.action in _TOOL_ACTIONS:
        return call("DO", "tool", workflows=[workflow_name(decision.action)])
    if _goal_unclear(check):
        return call("CLARIFY", "goal_unclear", clarify=_clarify_need(decision, check))
    if not decision.stated_hypotheses and unsupported_algorithm_request(task):
        return call("DECLINE", "algorithm_boundary")
    if (facts := _facts(check)) or verdict is not None and verdict.held and verdict.verdict == "needs_fact":
        return call("ASK", "needs_fact", facts=facts, workflows=_names(k for f in facts for k in f.workflows))
    if read and check.unconfirmed():
        return call("UNCHECKED", "check_unconfirmed", workflows=_routed(decision))
    if check is not None and check.full_gap or verdict is not None and verdict.held and verdict.verdict == "gap":
        return call("DECLINE", "full_gap", declined=_declined(results))
    running = decision.action.startswith("run_")
    if not read and not running and decision.capability_match_status == "unsupported":
        return call("DECLINE", "routing_unsupported")
    if not read and not running and not _routed(decision):
        return call("CLARIFY", "no_result_read", clarify=_clarify_need(decision, check))  # p1 C41, C48: one view
    given = [row for row in read if row.status in _GIVEN]
    if read and not given:
        return call("DECLINE", "all_results_not_available", declined=_declined(results))
    workflows = _names(key for row in given for key in row.delivered_by) or _routed(decision)
    declined = _declined(results)
    approved = (running and verdict is not None and not verdict.held and verdict.verdict in APPROVING_RUN_VERDICTS)
    held = verdict is not None and verdict.held
    basis = "run_held" if held else "run" if running else "results_given" if given else "routed"
    return call("DO", basis, workflows=workflows, partial=bool(declined and given), declined=declined,
                run_allowed=approved)
