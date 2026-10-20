"""The core decision (spec docs/superpowers/specs/2026-10-15-core-decision-design.md).

`decide_core` reads the turn's final `TaskDecision` -- the routing reading, the capability check and the run
verdict -- and makes the turn's four-way call: clarify the goal, ask a deciding fact, decline, or do. It makes no
model call; `classify_task` writes it on the decision and in the trace (`core.decision`), and `respond` records
which reply answered beside it (`core.view`). Phase 1 acts on CLARIFY and phase 2 on the fact agent's ASK (`with_core`
holds the turn; their replies answer it); the other kinds still mirror today's replies (phase 0, shadow).

Rules, in the spec's order of precedence:

1. UNCHECKED -- routing failed closed with nothing routed (unless the check confirmed a full gap, which the reply
   still gives: round p0 C10, C22, C37, C49; or, phase 5a, the check's confirmed reading says the goal is unclear),
   the check could not confirm what it read, or the run was held because the check could not confirm or read it.
2. CLARIFY (phase 1, spec section 5) -- the check's confirmed reading says the request names no result
   (`purpose_only`), or the result it names is in no requirement the check read, or its goal words name two
   registered methods as the choice and no result; one named method is never unclear; a tool request is never held.
   Phase 5c: also when the fact agent read a wanted result the user is unsure of with fewer than two options named
   (R7, `result_open`) -- before any ASK, so the turn's data facts wait for the goal.
3. ASK -- phase 2: the fact agent's kept questions (R1-R6, `interpretation.fact_check`); the fixed dimensions
   (`needs_fact`, or a run held for it) only when the agent did not run, and recorded as shadow when it did.
   Phase 5b: a count the user gave as candidates, each judged in code, is asked whether or not the agent ran
   (`count_fact`), before the agent's questions.
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
from ..method_names import workflows_in
from .count_alternatives import judged_count_words, splits_candidates
from .fact_check import MAX_ASKED
from .needed_facts import _question

__all__ = ["decide_core", "goal_unclear", "with_core"]

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


def _declined(rows, check=None) -> list[DeclinedPart]:
    from .capability_check import _status_line

    provisional = bool(check is not None and check.provisional)
    return [DeclinedPart(quote=row.quote, reasons=[*row.limits, *row.violations],
                         alternatives=_names([*row.instead, *row.defaults]), line=_status_line(row, provisional))
            for row in rows if row.status == "not_available"]


def _boundary(decision, task: str) -> tuple[str, str] | None:
    """Phase 3: the two text boundaries are evidence for DECLINE, no longer replies of their own."""
    from .concept_answers import render_cobra_expression_boundary, render_unsupported_algorithm_boundary

    if decision.stated_hypotheses or not task:
        return None
    if (text := render_unsupported_algorithm_boundary(task)) is not None:
        return "algorithm_boundary", text
    if (text := render_cobra_expression_boundary(task)) is not None:
        return "cobra_boundary", text
    return None


def _facts(check, by_code: bool | None = None, task: str = "") -> list[FactQuestion]:
    """The check's waits as questions: all, or only those code judged (phase 5b) or only the legacy dimensions'.

    One question per doubt (live attempt-04 T03): the first reading and the re-read each found a result, both waiting
    on "either 2 or 14 samples" / "2 or 14 samples", and "Which of these is right: 2 or 14?" was asked twice. Waits on
    the same dimension and candidate values, in overlapping words, are one question; its workflows and notes are
    both results' together."""
    rows = [row for row in (check.needed_facts() if check is not None else [])
            if by_code is None or row.by_code == by_code]
    found: list[FactQuestion] = []
    for row in rows:
        fact = FactQuestion(question=_question(row), user_quote=row.unknown_quote, depends_on=row.depends_on or "",
                            workflows=_names(key for keys in row.outcomes.values() for key in keys),
                            outcomes={value: _names(keys) for value, keys in row.outcomes.items()},
                            by_code=row.by_code, notes=dict(row.outcome_notes))
        same = next((index for index, known in enumerate(found)
                     if (known.depends_on, known.by_code, list(known.outcomes)) == (fact.depends_on, fact.by_code,
                                                                                    list(fact.outcomes))
                     and _same_words(task, known.user_quote, fact.user_quote)), None)
        if same is None:
            found.append(fact)
            continue
        known = found[same]
        found[same] = known.model_copy(update={
            "workflows": list(dict.fromkeys([*known.workflows, *fact.workflows])),
            "outcomes": {value: list(dict.fromkeys([*names, *fact.outcomes.get(value, [])]))
                         for value, names in known.outcomes.items()},
            "notes": {**fact.notes, **known.notes}})
    return found


def _overlaps(a: str, b: str) -> bool:
    a, b = a.casefold().strip(), b.casefold().strip()
    return bool(a and b) and (a in b or b in a)


def _same_words(task: str, a: str, b: str) -> bool:
    """Whether two quotes are, in the request, overlapping words (by containment when they cannot be placed)."""
    from .request_spans import _span

    if task and (first := _span(task, a)) is not None and (second := _span(task, b)) is not None:
        return first[0] < second[1] and second[0] < first[1]
    return _overlaps(a, b)


def goal_unclear(check) -> bool:
    """Spec section 5: the request names no result, by the check's own confirmed reading and its verified words.

    The methods the goal's words name are the registry's to count (`workflows_in`): one named method is the goal --
    a question about it (p1 C32, p2-p3 C51, p4b-p4c C39 were read purpose_only); two named as the choice with no
    result read is no goal ("Should I use COBRA or CONDOR?", p4b C10 was read method_named).
    """
    if check is None or check.unconfirmed() or not check.goal_quote:
        return False
    named = workflows_in(check.goal_quote)
    if len(named) == 1:
        return False
    if len(named) > 1 and check.goal == "method_named" and not any(row.kind == "result" for row in check.requirements):
        return True
    if check.goal == "purpose_only":
        return True
    asked = [row.quote for row in check.requirements if row.kind in ("result", "about_methods")]
    return check.goal == "result_named" and not any(_overlaps(check.goal_quote, quote) for quote in asked)


def _clarify_need(decision, check, goal_quote: str = "") -> ClarifyNeed:
    """The results the request's stated data can give -- listed as possible, never as fitting. `goal_quote`: the
    user's words for the open result (phase 5c), else the check's goal words."""
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
                       inputs=sorted(stated), question=question,
                       goal_quote=goal_quote or (check.goal_quote if check else ""))


def with_core(decision, core: CoreDecision):
    """The decision a call leaves: CLARIFY (phase 1) and an agent's ASK (phase 2) select, refuse and run nothing;
    the other kinds change nothing yet."""
    if core.kind == "ASK" and core.basis in ("fact_agent", "count_fact", "hybrid_requirement", "contract_veto_fact"):
        asked = [fact.question for fact in core.facts if not fact.settled_by_input_check]
        return decision.model_copy(update={
            "core": core, "action": "no_tool", "should_execute": False, "execution_requested": False,
            "intent_type": "answer_question", "matched_actions": [], "recommended_actions": [],
            "hypothesis_actions": [], "alternative_actions": [], "capability_match_status": "ambiguous",
            "clarification_question": " ".join(asked)[:300],
            "reason": "A fact the user is unsure of decides the request; it is asked before any workflow is chosen."})
    if core.kind == "DECLINE" and core.basis in ("hybrid_gate", "contract_veto"):  # a contract rules it out
        return decision.model_copy(update={
            "core": core, "action": "no_tool", "should_execute": False, "execution_requested": False,
            "intent_type": "answer_question", "matched_actions": [], "recommended_actions": [],
            "hypothesis_actions": [], "alternative_actions": [], "capability_match_status": "unsupported",
            "reason": "A contract condition rules out every workflow offered; the reply says why."})
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
    # p0: a confirmed gap is still answered. Phase 5a (spec 13.2): so is a confirmed unclear goal -- p2-p4c C10 ran
    # no failed call; the hypothesis reader read unclear_goal and routing was labelled research_choices_unavailable.
    if _failed_closed(decision, reason_code) and not confirmed_gap and not goal_unclear(check):
        return call("UNCHECKED", "routing_failed")
    if verdict is not None and verdict.held and verdict.verdict in _UNCHECKED_HOLDS:
        return call("UNCHECKED", f"run_held_{verdict.verdict}", workflows=_routed(decision))
    if decision.action in _TOOL_ACTIONS:
        return call("DO", "tool", workflows=[workflow_name(decision.action)])
    if goal_unclear(check):
        return call("CLARIFY", "goal_unclear", clarify=_clarify_need(decision, check))
    agent = getattr(decision, "fact_check", None)
    if agent is not None and agent.status == "checked" and agent.open_results:  # phase 5c R7: before any ASK
        return call("CLARIFY", "result_open", clarify=_clarify_need(decision, check, agent.open_results[0]))
    if agent is not None and agent.status == "checked":
        evidence["legacy_facts"] = [fact.question for fact in agent.legacy]  # phase 2: shadow
        # Phase 5b (spec 13.3): a count code judged is asked first, beside the agent's (the code's on the same words).
        counted = _facts(check, by_code=True, task=task)
        # ROUND-09 (R8): a question on candidates code weighed must be able to tell them apart, or it is not asked.
        owned = [fact for fact in agent.accepted if not fact.settled_by_input_check and any(
            _same_words(task, fact.user_quote, words) and not splits_candidates(fact.question, values)
            for words, values in judged_count_words(check))]
        if owned:
            evidence["count_owned"] = [fact.question for fact in owned]
        asked = [*counted, *(fact for fact in agent.accepted if not fact.settled_by_input_check and fact not in owned
                             and not any(_same_words(task, fact.user_quote, count.user_quote)
                                         for count in counted))][:MAX_ASKED]
        if asked:
            settled = [fact for fact in agent.accepted if fact.settled_by_input_check]
            return call("ASK", "count_fact" if counted else "fact_agent", facts=[*asked, *settled],
                        workflows=list(dict.fromkeys(name for fact in asked for name in fact.workflows)))
    elif (facts := _facts(check, task=task)) or verdict is not None and verdict.held and verdict.verdict == "needs_fact":
        return call("ASK", "needs_fact", facts=facts, workflows=_names(k for f in facts for k in f.workflows))
    running = decision.action.startswith("run_")
    if check is not None and check.unconfirmed() and (read or not running):  # p3: an unconfirmed guidance turn too
        return call("UNCHECKED", "check_unconfirmed", workflows=_routed(decision))
    if (boundary := _boundary(decision, task)) is not None:
        return call("DECLINE", boundary[0], declined=[DeclinedPart(quote="", line=boundary[1])])
    if check is not None and check.full_gap or verdict is not None and verdict.held and verdict.verdict == "gap":
        return call("DECLINE", "full_gap", declined=_declined(results, check))
    if not read and not running and decision.capability_match_status == "unsupported":
        return call("DECLINE", "routing_unsupported")
    if not read and not running and not _routed(decision):
        return call("CLARIFY", "no_result_read", clarify=_clarify_need(decision, check))  # p1 C41, C48: one view
    shadow = agent is not None and agent.status == "checked"  # phase 2: a legacy wait gives what it could give
    given = [row for row in read if row.status in _GIVEN or shadow and row.status == "needs_fact"]
    if read and not given:
        return call("DECLINE", "all_results_not_available", declined=_declined(results, check))
    # p4b/p4c C59: a run is the workflow it runs, never routing's other picks beside it
    workflows = ([workflow_name(decision.action)] if running
                 else _names(key for row in given for key in row.delivered_by) or _routed(decision))
    declined = _declined(results, check)
    approved = (running and verdict is not None and not verdict.held and verdict.verdict in APPROVING_RUN_VERDICTS)
    held = verdict is not None and verdict.held
    basis = "run_held" if held else "run" if running else "results_given" if given else "routed"
    settled = [fact for fact in agent.accepted if fact.settled_by_input_check] if agent is not None else []
    return call("DO", basis, workflows=workflows, partial=bool(declined and given), declined=declined,
                run_allowed=approved, facts=settled)
