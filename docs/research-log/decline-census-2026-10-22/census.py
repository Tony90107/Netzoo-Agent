"""ROUND-26 phase 0 (`collab/ROUND-26-PLAN.md` 1.3): what each "cannot be done" rests on. No model calls.

Every labelled reading (the 757 dev readings and h5's 94 main-round readings) is B2-replayed (`replay_full`) with each
step spied on. For every call that says something cannot be done -- DECLINE, or DO with a part not available -- each
not-available result row gets the step that first made it not available and a ground:

  build:            delivery / condition_requirement / setting_apart / open_choice (the row is that kind of
                    requirement), else contract_limit:number (a contract limit whose numbers the user wrote),
                    contract_limit:link (a contract limit on settings the reading linked), typed_attr (the reading
                    credited a workflow and its typed attributes removed every credit), near_miss (no credit, a near
                    miss cited), no_credit (no credit, nothing cited)
  later steps:      condition_model (the condition check's answer), second_opinion, ruled_out:explicit /
                    ruled_out:inference (ROUND-20 D), unbuilt_network:user_words / unbuilt_network:typed,
                    settings_read:number, same_run, goal_read, merge_reread

Declared before running (the plan's two classes):
- anchored: the user's own words checked by code against the contract -- contract_limit:number, ruled_out:explicit,
  unbuilt_network:user_words, settings_read:number; same_run when the call holds an anchored row; a call's text
  boundary (no rows).
- reading-derived: every other ground.
A call would be confirmed under proposal 1 when every not-available row in it has only reading-derived grounds.

Corrected after the first run (a bug in the declaration, not a change of rule): a call with no not-available rows was
taken to be a text boundary, but every such call was routing_unsupported -- routing's model reading, so
reading-derived. Only a call whose basis is a text boundary (`algorithm_boundary`, `cobra_boundary`) is anchored.

Usage: python3 census.py OUT.json
"""
from __future__ import annotations

import importlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
sys.path.insert(0, str(LOGS / "stability-round13-2026-10-21"))
import harness  # noqa: E402  (sets the import paths to this checkout's scripts)

H5 = re.compile(r"^hb-h5main-(Q\d+)-(\d)$")
ANCHORED = {"contract_limit:number", "ruled_out:explicit", "unbuilt_network:user_words", "settings_read:number"}
STEPS = {  # module: names -> step label (the check is in the return value)
    "netzoo_agent_core.interpretation.capability_check": {
        "build_capability_check": "build", "apply_condition_answers": "condition_model",
        "apply_redirect_answers": "condition_model", "apply_second_opinion": "second_opinion",
        "wait_on_asked": "wait_on_asked"},
    "netzoo_agent_core.interpretation.requirement_split": {"apply_own_sentence_answers": "condition_model"},
    "netzoo_agent_core.graph.router_invocation": {"_not_checked": "condition_model"},
    "netzoo_agent_core.interpretation.ruled_out": {"without_ruled_out": "ruled_out",
                                                   "without_unbuilt_network": "unbuilt_network"},
    "netzoo_agent_core.interpretation.settings_read": {"with_settings_read": "settings_read"},
    "netzoo_agent_core.interpretation.same_run": {"same_run_holds": "same_run"},
    "netzoo_agent_core.interpretation.goal_read": {"with_goal_read": "goal_read"},
}
MAKERS = {  # functions inside build that make a requirement of their own kind
    "delivery_requirements": "delivery", "condition_requirements": "condition_requirement",
    "settings_apart": "setting_apart", "_open_choices": "open_choice"}


def _check_of(value):
    from netzoo_agent_core.contracts.capability_check import CapabilityCheck
    if isinstance(value, CapabilityCheck):
        return value
    if isinstance(value, tuple):
        return next((item for item in value if isinstance(item, CapabilityCheck)), None)
    return None


class Spy:
    def __init__(self):
        self.trace, self.made, self.patched = [], {}, []

    def reset(self):
        self.trace, self.made = [], {}

    def install(self):
        for module_name, names in STEPS.items():
            module = importlib.import_module(module_name)
            for name, label in names.items():
                self._wrap(module, name, label)
        self._wrap(harness.replay_full, "merge_reread_", "merge_reread")
        cc = importlib.import_module("netzoo_agent_core.interpretation.capability_check")
        for name, kind in MAKERS.items():
            original = getattr(cc, name)

            def maker(*args, _original=original, _kind=kind, **kwargs):
                out = _original(*args, **kwargs)
                rows = out if isinstance(out, list) else out[1] if _kind == "setting_apart" else out[0]
                self.made.setdefault(_kind, set()).update(getattr(row, "quote", "") for row in rows or [])
                return out
            setattr(cc, name, maker)
            self.patched.append((cc, name, original))

    def _wrap(self, module, name, label):
        original = getattr(module, name)

        def step(*args, _original=original, _label=label, **kwargs):
            out = _original(*args, **kwargs)
            if (check := _check_of(out)) is not None:
                self.trace.append((_label, args, check))
            return out
        setattr(module, name, step)
        self.patched.append((module, name, original))


def _numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+(?:\.\d+)?", text))


def _raw_credits(proposal, quote: str) -> list[str]:
    """The produces credits the reading itself gave the asks whose quote overlaps this row's."""
    credits = []
    for name, value in proposal:
        for ask in (getattr(value, "asks", None) or []):
            if ask.quote and (ask.quote in quote or quote in ask.quote):
                credits += list(ask.delivered_by)
    return credits


def ground(row, origin, snapshot, spy, proposal, task, check) -> str:
    from netzoo_agent_core.interpretation.ruled_out import rests_on_inference
    if origin == "build":
        for kind in ("delivery", "condition_requirement", "setting_apart", "open_choice"):
            if row.quote in spy.made.get(kind, ()):
                return kind
        if snapshot.limits:
            stated = _numbers(task)
            return ("contract_limit:number" if any(_numbers(limit) & stated for limit in snapshot.limits)
                    else "contract_limit:link")
        if _raw_credits(proposal, row.quote):
            return "typed_attr"
        return "near_miss" if row.not_by else "no_credit"
    if origin == "ruled_out":
        return ("ruled_out:inference" if any(rests_on_inference(check, reason) for reason in row.limits)
                else "ruled_out:explicit")
    if origin == "unbuilt_network":
        return ("unbuilt_network:user_words" if any(limit.startswith("You said") for limit in row.limits)
                else "unbuilt_network:typed")
    if origin == "settings_read":
        return "settings_read:number"
    return origin


def main(out: str):
    import netzoo_agent_core.interpretation.core_decision as core_decision
    from replay import _proposal

    spy = Spy()
    spy.install()
    original, seen = core_decision.decide_core, {}

    def decide(decision, task="", **kwargs):
        seen["decision"], seen["core"] = decision, original(decision, task, **kwargs)
        return seen["core"]

    by_session, core = harness._gold()
    h5 = {item["id"]: item["class"] for item in json.loads(
        (LOGS / "heldout-h5-2026-10-21/items.json").read_text())["items"]}
    kind_of = {"do": "DO", "dont": "DECLINE", "ask": "ASK", "vague": "CLARIFY"}
    rows_out, counts = [], Counter()
    for key, folder, sid, task, payload, reread, found, _n in harness.readings():
        if match := H5.match(sid):
            gold, where = kind_of[h5[match.group(1)]], "h5"
        else:
            gold, where = harness._label(sid, by_session, core), "dev"
        if not gold:
            continue
        spy.reset()
        seen.clear()
        core_decision.decide_core = decide
        try:
            harness.replay_full.replay(folder, task, payload, reread, found)
        finally:
            core_decision.decide_core = original
        call = seen.get("core")
        if call is None:
            counts["no call"] += 1
            continue
        counts[where] += 1
        if not (call.kind == "DECLINE" or (call.kind == "DO" and call.partial)):
            continue
        final = seen["decision"].capability_check
        proposal = list(_proposal(payload) or [])
        declined = []
        for row in (final.results() if final is not None else []):
            if row.status != "not_available":
                continue
            origin, snapshot = "unknown", row
            for label, _args, check in spy.trace:
                match_row = next((r for r in check.requirements if r.kind == "result" and r.quote == row.quote), None)
                if match_row is not None and match_row.status == "not_available":
                    origin, snapshot = label, match_row
                    break
            declined.append({"quote": row.quote, "origin": origin,
                             "ground": ground(row, origin, snapshot, spy, proposal, task, final),
                             "limits": row.limits, "violations": row.violations, "not_by": row.not_by,
                             "attrs": {k: v for k, v in row.attrs.items() if v not in ("none", "not_stated", 0, [],
                                                                                       False, "unstated")}})
        grounds = [item["ground"] for item in declined]
        boundary = call.basis in ("algorithm_boundary", "cobra_boundary")
        anchored = any(g in ANCHORED for g in grounds) or boundary
        for item in declined:
            if item["ground"] == "same_run":
                item["anchored"] = anchored
            else:
                item["anchored"] = item["ground"] in ANCHORED
        rows_out.append({"key": key, "session": sid, "where": where, "gold": gold, "kind": call.kind,
                         "basis": call.basis, "partial": call.partial, "task": task, "declined": declined,
                         "would_confirm": not anchored})
    Path(out).write_text(json.dumps(rows_out, indent=1, ensure_ascii=False))
    print(dict(counts), f"{len(rows_out)} calls say something cannot be done")
    print("grounds (rows):", Counter(item["ground"] for row in rows_out for item in row["declined"]).most_common())
    table = Counter((row["where"], row["gold"], row["would_confirm"]) for row in rows_out)
    for where in ("dev", "h5"):
        print(where, {f"gold {g} / {'confirm' if c else 'keep'}": n for (w, g, c), n in sorted(table.items())
                      if w == where})


if __name__ == "__main__":
    main(sys.argv[1])
