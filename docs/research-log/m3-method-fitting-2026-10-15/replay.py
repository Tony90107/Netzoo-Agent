"""Rebuild every recorded round-m3 capability check with one checkout's code, using the recorded model answers.

Usage (from any checkout):
  REPLAY_CODE_ROOT=<checkout> python docs/research-log/m3-method-fitting-2026-10-15/replay.py <out.json> \
      [--recordings <live/m3 folder>] [--inject <counts.json>]

No model is called. For each recorded turn with a `routing.capability_checked` event, the model's proposal is rebuilt
with `build_capability_check` of REPLAY_CODE_ROOT, and the rest of `graph.router_invocation._with_capability_check`
is mirrored with the model's recorded answers: the re-read (recorded passages), the condition check (looked up by
asked result, workflow and stated words), the second opinion (by asked result and workflow) and, for a run, the run
verdict with `unbound_settings`. A model answer the new code would need and the recording does not hold is reported in
`needs_live` and treated as a failed call (unanswered), as the live code treats one.

`--inject` (counterfactual, new code only): {"<session>/t<n>": {"sample_count": int, "sample_count_quote": str,
"feature_counts": [{"count": int, "quote": str}]}} adds the request-level count fields the new contract asks the model
for. The recordings predate those fields, so without it they are empty.

The raw traces (session.json, events.jsonl) are kept only in the main checkout, not in git; by default they are read
from this checkout's `live/m3`, else from the main checkout beside `.claude/worktrees`.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CODE_ROOT = Path(os.environ.get("REPLAY_CODE_ROOT") or REPO)
sys.path.insert(0, str(CODE_ROOT / "scripts"))

from netzoo_agent_core.capability_sheet import entry  # noqa: E402
from netzoo_agent_core.contracts.capability_check import (  # noqa: E402
    MAX_SENTENCES, proposal_model, reread_as_proposal, reread_model,
)
from netzoo_agent_core.interpretation.capability_check import (  # noqa: E402
    apply_condition_answers, apply_redirect_answers, apply_second_opinion, blank_requirement_pairs,
    build_capability_check, condition_pairs, redirect_pairs, second_opinion_pairs, stated_requirements,
    understanding_paragraph, wait_on_asked,
)
from netzoo_agent_core.interpretation.method_conditions import unbound_settings  # noqa: E402
from netzoo_agent_core.interpretation.reread import merge_reread  # noqa: E402
from netzoo_agent_core.interpretation.requirement_split import apply_own_sentence_answers  # noqa: E402
from netzoo_agent_core.interpretation.run_check import run_check_verdict  # noqa: E402

LIVE = Path("docs/research-log/m3-clarification-2026-10-15/live/m3")


def _recordings_root(given: str | None) -> Path:
    if given:
        return Path(given)
    for root in (REPO, REPO.parents[2]):  # this checkout, or the main checkout of a .claude/worktrees/<name> one
        if any((root / LIVE).glob("ve-m3-live-*/t1/session.json")):
            return root / LIVE
    raise SystemExit("no raw m3 traces found; pass --recordings")


def _not_checked(check, pairs):
    quotes = [quote for _index, _action, _keys, quote in pairs]
    return check.model_copy(update={"unchecked": list(dict.fromkeys([*check.unchecked, *quotes])), "full_gap": False})


def _proposal(payload):
    count = sum(1 for name in payload if re.fullmatch(r"s\d+", name))
    try:
        return proposal_model(count).model_validate(payload)
    except Exception:  # noqa: BLE001 -- the backup model's compact schema
        return proposal_model(count, compact=True).model_validate(payload)


class Answers:
    """The model's recorded answers, looked up by what was asked rather than by position."""

    def __init__(self):
        self.found: dict[tuple, object] = {}
        self.missing: list[str] = []

    def add(self, keys: list[tuple], answers):
        for key, answer in zip(keys, answers or [None] * len(keys)):
            self.found.setdefault(key, answer)

    def get(self, kind: str, keys: list[tuple]):
        """The answers for these keys, or None (a failed call): when the recorded call failed, or -- reported in
        `missing` -- when the recording never asked one of them."""
        if not keys:
            return []
        self.missing += [f"{kind}: {key}" for key in keys if key not in self.found]
        if all(self.found.get(key) is not None for key in keys):
            return [self.found[key] for key in keys]
        return None


def replay_turn(task: str, events: list[dict], final_action: str, inject: dict | None):
    by_type: dict[str, list[dict]] = {}
    for event in events:
        by_type.setdefault(event["event_type"], []).append(event["payload"])
    checked = by_type["routing.capability_checked"][0]
    payload = dict(checked["proposal"])
    if inject:
        payload["conditions"] = {**payload.get("conditions", {}), **inject}
    proposal = _proposal(payload)
    claims = frozenset(claim for claim, *_ in (by_type.get("routing.study_purpose_detected", [{}])[0].get("claims")
                                               or ()))
    check, _rejected = build_capability_check(task, proposal, claims)
    first = check
    reread = (by_type.get("routing.capability_reread") or [None])[0]
    if reread and reread.get("reread") is not None:
        passages = reread["passages"]
        model = reread_model(min(len(passages), MAX_SENTENCES)).model_validate(reread["reread"])
        reread_check, unplaced = build_capability_check(
            task, reread_as_proposal(model, getattr(proposal, "conditions", None)), claims)
        check = merge_reread(task, check, reread_check, passages, unplaced)
    provisional = bool(by_type.get("routing.capability_check_provisional"))
    recorded_check = (reread or checked)["check"]
    quote_at = {index: item["quote"] for index, item in enumerate(recorded_check["requirements"])}

    answers = Answers()
    for event in by_type.get("routing.capability_condition_check", []):
        for name, said in (("pairs", "answers"), ("own_sentence", "own_answers"), ("redirect", "redirected")):
            pairs = event.get(name) or []
            given = event.get(said)
            if name == "pairs" and event.get("after_second_opinion"):
                own = event.get("own_sentence") or []
                given = (event.get("answers") or [None] * (len(pairs) + len(own)))
                answers.add([("cond", quote_at.get(i), a, q) for i, a, _k, q in pairs], given[:len(pairs)])
                answers.add([("cond", quote_at.get(i), a, q) for i, a, _k, q in own], given[len(pairs):])
                break
            answers.add([("cond", quote_at.get(i), a, q) for i, a, _k, q in pairs], given)
    seconds = by_type.get("routing.capability_second_opinion", [])
    for event in seconds:
        answers.add([("second", quote_at.get(i), a) for i, a, _k in event.get("pairs") or []], event.get("answers"))
    # The workflows a second opinion weighs: those it was asked about, and routing's exact match (a full gap that
    # would clear it is asked about; one the recording never needed is then reported in `needs_live`).
    match = (by_type.get("routing.registry_match_completed") or [{}])[0]
    exact = list(match.get("matched_actions") or []) if match.get("status") == "exact" else []
    asked = list(dict.fromkeys([*exact, *(a for event in seconds for _i, a, _k in event.get("pairs") or [])]))

    def ask(kind, pairs):
        return answers.get(kind, [("cond", check.requirements[i].quote, a, q) for i, a, _k, q in pairs])

    stated = [] if provisional else stated_requirements(task, proposal, check)
    own = [] if provisional else stated_requirements(task, proposal, check, own_sentence=True)
    pairs_to_check, own_pairs = condition_pairs(check, stated), condition_pairs(check, own)
    sent = {"pairs": [[check.requirements[i].quote, a, q] for i, a, _k, q in pairs_to_check],
            "own": [[check.requirements[i].quote, a, q] for i, a, _k, q in own_pairs]}
    if pairs_to_check or own_pairs:
        got = ask("cond", pairs_to_check + own_pairs)
        main, mine = (got[:len(pairs_to_check)], got[len(pairs_to_check):]) if got is not None else (None, None)
        check = apply_condition_answers(check, pairs_to_check, main) if main is not None else _not_checked(
            check, pairs_to_check)
        check = apply_own_sentence_answers(check, own_pairs, mine) if mine is not None else _not_checked(
            check, own_pairs)
        if main is not None:
            offered = list(dict.fromkeys(a for event in by_type.get("routing.capability_condition_check", [])
                                         for _i, a, _k, _q in event.get("redirect") or []))
            redirect = redirect_pairs(check, offered[:4]) if offered else []
            if redirect:
                back = ask("cond", redirect)
                if back is not None:
                    check = apply_redirect_answers(check, redirect, back)
    blank = [] if provisional or check.full_gap else blank_requirement_pairs(check)
    if (check.full_gap and asked) or blank:
        pairs = second_opinion_pairs(check, asked) if check.full_gap else blank
        got = answers.get("second", [("second", check.requirements[i].quote, a) for i, a, _k in pairs]) if pairs else None
        if got is not None:
            check = wait_on_asked(apply_second_opinion(check, pairs, got), pairs)
            late = [p for p in condition_pairs(check, stated) if check.requirements[p[0]].second_opinion]
            late_own = [p for p in condition_pairs(check, own) if check.requirements[p[0]].second_opinion]
            if late or late_own:
                back = ask("cond", late + late_own)
                check = (apply_condition_answers(check, late, back[:len(late)]) if back is not None
                         else _not_checked(check, late))
                check = (apply_own_sentence_answers(check, late_own, back[len(late):]) if back is not None
                         else _not_checked(check, late_own))
        elif pairs and check.full_gap:
            check = check.model_copy(update={"full_gap": False, "gap_unconfirmed": True})
    elif check.full_gap and not asked and not seconds:
        pass  # nothing was weighed in the recording either; a gap that clears a routing match is reported
    if provisional:
        check = check.model_copy(update={"full_gap": False, "provisional": True})
    run = None
    action = next((e["action"] for e in by_type.get("routing.run_check_shadow", [])), None)
    if action and not check.needed_facts() and not check.full_gap:
        unbound = unbound_settings(check, action)
        verdict_check = check.model_copy(update={"unchecked": list(dict.fromkeys([*check.unchecked, *unbound]))}) \
            if unbound else check
        run = {"action": action, "unbound": unbound, **run_check_verdict(verdict_check, action)}
    elif action:
        run = {"action": action, "verdict": "needs_fact" if check.needed_facts() else "full_gap"}
    return first, check, {"sent": sent, "needs_live": answers.missing, "run": run, "final_action": final_action}


def summary(check) -> dict:
    return {"full_gap": check.full_gap, "unchecked": check.unchecked,
            "rows": [{"kind": item.kind, "quote": item.quote, "status": item.status,
                      "workflows": sorted({entry(k).workflow for k in item.delivered_by if entry(k).workflow}),
                      "limits": item.limits, "defaults": sorted({entry(k).workflow for k in item.defaults}),
                      "violations": item.violations}
                     for item in check.requirements if item.kind == "result"],
            "paragraph": understanding_paragraph(check)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("out")
    parser.add_argument("--recordings")
    parser.add_argument("--inject")
    args = parser.parse_args()
    root = _recordings_root(args.recordings)
    inject = json.loads(Path(args.inject).read_text()) if args.inject else {}
    rows = {}
    for turn in sorted(root.glob("ve-m3-live-*/t*")):
        if not (turn / "events.jsonl").exists():
            continue
        session = json.loads((turn / "session.json").read_text())
        events = [json.loads(line) for line in (turn / "events.jsonl").read_text().splitlines() if line.strip()]
        if not any(e["event_type"] == "routing.capability_checked" for e in events):
            continue
        task = [m["content"] for m in session["messages"] if m["role"] == "user"][-1]
        decision = (session.get("plan") or {}).get("decision") or {}
        key = f"{turn.parent.name}/{turn.name}"
        first, check, info = replay_turn(task, events, decision.get("action", ""), inject.get(key))
        recorded = decision.get("capability_check")
        rows[key] = {"task": task, "first": summary(first), "final": summary(check), **info,
                     "recorded_final": None if recorded is None else {
                         "full_gap": recorded.get("full_gap"), "unchecked": recorded.get("unchecked"),
                         "rows": [{"quote": r["quote"], "status": r["status"]} for r in recorded["requirements"]
                                  if r["kind"] == "result"]}}
    Path(args.out).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    print(f"{CODE_ROOT}: {len(rows)} recorded checks rebuilt from {root}")


if __name__ == "__main__":
    main()
