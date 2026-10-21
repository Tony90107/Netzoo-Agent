"""ROUND-12 (collab/ROUND-12-PLAN.md): B2 -- a recorded 56-item reading decided again by this checkout with the steps
after the capability reading that ROUND-11's replay (B) left out. Every model answer comes from the recording; no
model calls.

The order is `_with_capability_check`'s (graph/router_invocation.py:467-640):
  1 build_capability_check with the recorded study-purpose claims and the file-counted samples
  2 the recorded re-read, merged
  3 the condition check -- this checkout's pairs (stated and own-sentence), each answered by the recorded answer for
    the same (row quote, workflow action, stated quote); redirect pairs likewise
  4 the recorded second opinion, each pair moved to the rebuilt row with the same quote (as ROUND-11)
  5 the condition check after the second opinion, as step 3
  6 a provisional reading is never a full gap
  7 without_ruled_out (code only)
  8 the recorded fact check: its waits lifted when it ran
  9 waiting_decision when a fact is needed; the full-gap update of the decision; decide_core
A pair this checkout asks that the recording never answered is "unrecorded" and handled as live handles an
unanswered call: the condition check's quote is unchecked (`_not_checked`), a redirect changes nothing. Routing before
the check and the run verdict stay as recorded; `run_verdict` is only recomputed on the replayed check as a flag.

Usage: python3 replay_full.py OUT.json [--scripts DIR]
  every reading of p4b p4c p5r g4o1 g4o2, B2 next to the recorded call; --scripts decides them with another
  checkout's code (older code: no file-counted samples, second opinion without the request's words)
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
sys.path.insert(0, str(LOGS / "unit-typing-d1-2026-10-21"))
import units  # noqa: E402  (sets the import path to this checkout's scripts)

sys.path.insert(0, str(LOGS / "request-facts-round03-2026-10-20"))
if "--scripts" in sys.argv:  # another checkout's code (the fidelity check at a round's frozen commit)
    sys.path.insert(0, sys.argv[sys.argv.index("--scripts") + 1])


def _takes(function, count: int) -> bool:
    """Whether the function takes `count` positional arguments (older checkouts take fewer)."""
    import inspect
    return len(inspect.signature(function).parameters) >= count


def events(folder: Path) -> list[dict]:
    return [json.loads(line) for line in (folder / "events.jsonl").read_text().splitlines() if line.strip()]


def _first(found: list[dict], kind: str, **where) -> dict | None:
    return next((e["payload"] for e in found if e["event_type"] == kind
                 and all(bool(e["payload"].get(k)) == v for k, v in where.items())), None)


def _row_quotes(found: list[dict]) -> list[str]:
    """The rows the recorded condition check's indices point to: the check after the re-read, else the first one."""
    quotes = []
    for event in found:
        if event["event_type"] in ("routing.capability_checked", "routing.capability_reread"):
            quotes = [row.get("quote") for row in (event["payload"].get("check") or {}).get("requirements", [])] or quotes
        if event["event_type"] == "routing.capability_condition_check":
            break
    return quotes


def _recorded_answers(payload: dict | None, quotes: list[str]) -> dict:
    """{(row quote, action, stated quote): answer} for a recorded condition-check event's pairs and own pairs."""
    found = {}
    if not payload:
        return found
    for pairs, answers in ((payload.get("pairs") or [], payload.get("answers")),
                           (payload.get("own_sentence") or [], payload.get("own_answers")),
                           (payload.get("redirect") or [], payload.get("redirected"))):
        for (index, action, _keys, stated), answer in zip(pairs, answers or []):
            if index < len(quotes):
                found[(quotes[index], action, stated)] = answer
    return found


def _answer(check, pairs, recorded: dict):
    """(answered pairs, their answers, unanswered pairs) for this checkout's pairs."""
    try:  # ROUND-14: answers code gives before asking (absent from older checkouts)
        from netzoo_agent_core.capability_sheet import entry
        from netzoo_agent_core.interpretation.expects import code_answer
    except ImportError:
        code_answer = None
    done, answers, missing = [], [], []
    for pair in pairs:
        index, action, keys, stated = pair
        key = (check.requirements[index].quote, action, stated)
        if code_answer is not None and (by_code := code_answer(entry(keys[0]).workflow, stated)):
            done.append(pair)
            answers.append(by_code)
        elif key in recorded:
            done.append(pair)
            answers.append(recorded[key])
        else:
            missing.append(pair)
    return done, answers, missing


def replay(folder: Path, task: str, payload: dict, reread: dict | None, found: list[dict]) -> dict:
    from replay import _proposal
    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.contracts.capability_check import reread_as_proposal, reread_model
    from netzoo_agent_core.graph.fact_check_call import without_legacy_waits
    from netzoo_agent_core.graph.router_invocation import _not_checked
    from netzoo_agent_core.interpretation.capability_check import (
        apply_condition_answers, apply_redirect_answers, apply_second_opinion, build_capability_check,
        condition_pairs, redirect_pairs, stated_requirements, wait_on_asked)
    from netzoo_agent_core.interpretation.core_decision import decide_core
    from netzoo_agent_core.interpretation.needed_facts import waiting_decision
    from netzoo_agent_core.interpretation.requirement_split import apply_own_sentence_answers
    from netzoo_agent_core.interpretation.ruled_out import without_ruled_out
    from netzoo_agent_core.interpretation.run_check import run_verdict

    steps, unrecorded = [], Counter()
    proposal = _proposal(payload)
    if proposal is None:
        return {"kind": "unparsable"}
    study = _first(found, "routing.study_purpose_detected") or {}
    claims = {claim: quote for claim, quote in study.get("claims") or ()}  # ROUND-20: with their words
    try:
        from netzoo_agent_core.interpretation.input_bindings import bound_expression_samples
        counted = bound_expression_samples(task)
    except ImportError:  # before ROUND-07 nothing counted a named file's samples
        counted = None
        steps.append("no file count (older code)")
    extra = (counted,) if _takes(build_capability_check, 4) else ()
    check, _ = build_capability_check(task, proposal, claims, *extra)
    if reread and reread.get("reread"):
        raw = reread["reread"]
        model = reread_model(sum(1 for name in raw if name[1:].isdigit()))
        again, unplaced = build_capability_check(
            task, reread_as_proposal(model.model_validate(raw), getattr(proposal, "conditions", None)), claims, *extra)
        check = merge_reread_(task, check, again, reread.get("passages") or [], unplaced)
        steps.append("reread")
    session = json.loads((folder / "session.json").read_text())
    decision = TaskDecision.model_validate(session["plan"]["decision"])

    # 3: the condition check, this checkout's pairs answered from the recording
    quotes = _row_quotes(found)
    first = _first(found, "routing.capability_condition_check", after_second_opinion=False)
    recorded = _recorded_answers(first, quotes)
    stated = stated_requirements(task, proposal, check)
    own = stated_requirements(task, proposal, check, own_sentence=True)
    pairs, own_pairs = condition_pairs(check, stated), condition_pairs(check, own)
    if pairs or own_pairs:
        done, answers, missing = _answer(check, pairs, recorded)
        own_done, own_answers, own_missing = _answer(check, own_pairs, recorded)
        check = apply_condition_answers(check, done, answers) if done else check
        check = apply_own_sentence_answers(check, own_done, own_answers) if own_done else check
        if missing or own_missing:
            check = _not_checked(check, missing + own_missing)
            unrecorded["condition pairs"] += len(missing) + len(own_missing)
        offered = [*decision.matched_actions, *decision.hypothesis_actions, *decision.recommended_actions]
        redirect = redirect_pairs(check, list(dict.fromkeys(offered))[:4]) if done else []
        if redirect:
            r_done, r_answers, r_missing = _answer(check, redirect, recorded)
            check = apply_redirect_answers(check, r_done, r_answers) if r_done else check
            unrecorded["redirect pairs"] += len(r_missing)
        steps.append(f"condition {len(done)}+{len(own_done)} answered, {len(missing) + len(own_missing)} unrecorded")
    elif first:
        steps.append("condition check recorded, none asked now")

    # 4: the recorded second opinion
    opinion = _first(found, "routing.capability_second_opinion")
    if opinion and opinion.get("pairs"):
        rebuilt = [row.quote for row in check.requirements]
        before = [row.get("quote") for row in (
            next((e["payload"].get("check") for e in reversed(found[:_index(found, "routing.capability_second_opinion")])
                  if e["event_type"] in ("routing.capability_checked", "routing.capability_reread")), None)
            or {}).get("requirements", [])]
        if opinion.get("answers"):
            moved_pairs, answers = [], []
            for (index, action, keys), answer in zip(opinion["pairs"], opinion["answers"]):
                quote = before[index] if index < len(before) else None
                if quote in rebuilt:
                    moved_pairs.append((rebuilt.index(quote), action, keys))
                    answers.append(answer)
                else:
                    unrecorded["second-opinion pairs"] += 1
            if moved_pairs:
                given = (task,) if _takes(apply_second_opinion, 4) else ()
                check = wait_on_asked(apply_second_opinion(check, moved_pairs, answers, *given), moved_pairs)
                steps.append(f"second opinion {len(moved_pairs)}")
                # 5: workflows the second opinion credited, held to the stated requirements
                late = [p for p in condition_pairs(check, stated) if check.requirements[p[0]].second_opinion]
                late_own = [p for p in condition_pairs(check, own) if check.requirements[p[0]].second_opinion]
                if late or late_own:
                    later = _recorded_answers(
                        _first(found, "routing.capability_condition_check", after_second_opinion=True), quotes)
                    done, answers, missing = _answer(check, late, later)
                    own_done, own_answers, own_missing = _answer(check, late_own, later)
                    check = apply_condition_answers(check, done, answers) if done else check
                    check = apply_own_sentence_answers(check, own_done, own_answers) if own_done else check
                    if missing or own_missing:
                        check = _not_checked(check, missing + own_missing)
                        unrecorded["late condition pairs"] += len(missing) + len(own_missing)
                    steps.append(f"late condition {len(done)}+{len(own_done)}")
        elif check.full_gap:
            check = check.model_copy(update={"full_gap": False, "gap_unconfirmed": True})
            steps.append("second opinion unanswered: gap unconfirmed")

    # 6: a provisional reading
    if _first(found, "routing.capability_check_provisional") is not None:
        check = check.model_copy(update={"full_gap": False, "provisional": True})
        steps.append("provisional")

    # 7: the user's ruled-out inputs
    stated_inputs = frozenset(value for item in decision.outcome_hypotheses for value in item.outcome.input_artifacts
                              if value != "unknown") | frozenset(decision.guidance_input_artifacts)
    if (lifted := without_ruled_out(check, stated_inputs)) is not check:
        check = lifted
        steps.append("ruled out")
    try:  # ROUND-17: rows resting only on a workflow another row blocks are held (absent from older checkouts)
        from netzoo_agent_core.interpretation.same_run import same_run_holds
    except ImportError:
        same_run_holds = None
    if same_run_holds is not None and (held := same_run_holds(check)) is not check:
        check = held
        steps.append("same run held")

    # 8-9: the recorded fact check, waits, the full-gap update, the call
    if decision.fact_check is not None and decision.fact_check.status == "checked":
        check = without_legacy_waits(check)
    if check.needed_facts():
        decision = waiting_decision(decision, check)
    update = {"capability_check": check}
    if check.full_gap:
        update.update({"matched_actions": [], "hypothesis_actions": [], "recommended_actions": [],
                       "alternative_actions": [], "advisory_recommendation": None, "clarification_question": None,
                       "capability_match_status": "unsupported"})
    decision = decision.model_copy(update=update)
    recorded_core = next((e["payload"] for e in reversed(found) if e["event_type"] == "core.decision"), {})
    reason = recorded_core.get("evidence", {}).get("reason_code", "") or ""
    core = decide_core(decision, task, reason_code=reason)
    held = _first(found, "routing.run_held")
    verdict = None
    if held:
        verdict = run_verdict(check, held["action"], check_status=held.get("check_status") or "ok",
                              named=bool(held.get("named"))).verdict
    return {"kind": core.kind, "basis": core.basis, "partial": core.partial, "steps": steps,
            "unrecorded": dict(unrecorded), "run_verdict_recorded": held and held.get("verdict"),
            "run_verdict_replayed": verdict,
            "rows": [{"kind": row.kind, "status": row.status, "quote": row.quote[:80], "limits": row.limits,
                      "violations": row.violations, "delivered_by": row.delivered_by} for row in check.requirements],
            "ruled_out": check.ruled_out, "full_gap": check.full_gap, "unchecked": check.unchecked}


def merge_reread_(task, check, again, passages, unplaced):
    from netzoo_agent_core.interpretation.reread import merge_reread
    return merge_reread(task, check, again, passages, unplaced)


def _index(found: list[dict], kind: str) -> int:
    return next((i for i, e in enumerate(found) if e["event_type"] == kind), len(found))


def run(out: str):
    truth, tasks = units.gold(), units.items()
    rows = []
    for name, model in units.ROUNDS.items():
        for item, folder, task, payload, reread, _failed in units.recorded(name):
            if item not in truth or payload is None:
                continue
            found = events(folder)
            recorded = next((e["payload"] for e in reversed(found) if e["event_type"] == "core.decision"), {})
            row = {"round": name, "model": model, "item": item, "gold": tasks[item]["gold"],
                   "recorded": recorded.get("kind"), "recorded_basis": recorded.get("basis"),
                   "recorded_partial": recorded.get("partial"), "where": str(folder.relative_to(units.MAIN))}
            try:
                row["b2"] = replay(folder, task, payload, reread, found)
            except Exception as error:  # noqa: BLE001 -- reported, never hidden
                row["b2"] = {"kind": "error", "error": f"{type(error).__name__}: {error}"[:300]}
            rows.append(row)
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    for group, names in (("mini", ("p4b", "p4c", "p5r")), ("gpt-4o", ("g4o1", "g4o2"))):
        mine = [r for r in rows if r["round"] in names]
        print(f"{group}: {len(mine)} readings; errors {sum(r['b2']['kind'] in ('error', 'unparsable') for r in mine)}; "
              f"B2 = recorded {sum(r['b2']['kind'] == r['recorded'] for r in mine)}; "
              f"recorded right {sum(r['recorded'] == r['gold'] for r in mine)}; "
              f"B2 right {sum(r['b2']['kind'] == r['gold'] for r in mine)}; "
              f"unrecorded {sum(sum(r['b2'].get('unrecorded', {}).values()) > 0 for r in mine)} readings")


if __name__ == "__main__":
    run(sys.argv[1])
