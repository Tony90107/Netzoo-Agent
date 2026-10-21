"""ROUND-20 step 4 (collab/ROUND-20-PLAN.md), no model calls: ROUND-19's `replies.py` with this checkout's code --
every labelled reading decided by B2, its reply rendered by `respond`, and for each reply saying something cannot be
done, each reason it states, tagged by its source. The tagging mirrors `capability_check._why_not`, which now reads the
row through `stated_reasons.stated` first (ROUND-20: only reasons code can verify; none -> "not matched ...").
  R1 limits   R3 a near miss's why_not   R4 a result-form reason   R5 a registry-wide entry
  ALT the offer of a workflow with its own settings or method instead   R0 no reason ("not matched ...")
R2 (the condition check's answer) is never said any more; it is kept as a type so a regression would show.

Usage: python3 replies.py OUT.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
sys.path.insert(0, str(LOGS / "stability-round13-2026-10-21"))
import harness  # noqa: E402  (sets the import paths)

replay_full = harness.replay_full
SESSION = re.compile(r"^cj-[^-]+-(C\d+)-\d+$")


def tagged(item, check) -> list[tuple[str, str]]:
    """(type, text) of the reasons the reply states for one result, as `_why_not` chooses them."""
    from netzoo_agent_core.capability_sheet import entry
    from netzoo_agent_core.interpretation.capability_check import _form_reasons, _lower_first, _workflows
    from netzoo_agent_core.interpretation.stated_reasons import stated

    if (item := stated(item, check)) is None:
        return []
    cited = []
    for key in item.not_by:
        found = entry(key)
        cited.append(("R5", found.why_not) if found.kind == "registry_wide"
                     else ("R3", f"{found.workflow} does not give it: {_lower_first(found.why_not)}"))
    forms = [("R4", text) for text in _form_reasons(item)] if item.status == "not_available" else []
    reasons = [*(("R2", f"{reason}.") for reason in item.violations[:1]), *forms, *cited[:1]]
    if item.limits and item.status == "not_available":
        named = item.method.get("named_quote")
        alternative = ([("ALT", f"{_workflows(item.defaults)} itself can still run, with its own settings instead -- "
                                "an alternative, not the setting you asked for.")] if item.defaults else
                       [("ALT", f'{_workflows(item.instead)} gives this result with its own method instead -- an '
                                f'alternative, not "{named}".')] if item.instead and named else [])
        reasons = [(_limit_type(item.limits[0]), f"{item.limits[0]}."), *alternative,
                   *((_limit_type(reason), f"{reason}.") for reason in item.limits[1:]), *reasons]
    seen, out = set(), []
    for kind, text in reasons:
        if text not in seen:
            seen.add(text)
            out.append((kind, text))
    return out[:2]


def _limit_type(reason: str) -> str:
    """R2 for a limit the own-sentence condition check wrote (`requirement_split.apply_own_sentence_answers`: the model's
    answer, as 'W does not meet "..."'); R1 for one code derived from the contract."""
    return "R2" if re.match(r'^\S+ does not meet "', reason) else "R1"


def gold_reasons() -> dict[str, dict]:
    audit = json.loads((LOGS / "strictness-audit-2026-10-20/audit.json").read_text())["items"]
    by_session = {item["trace"]["session"]: {"id": key, "reason": item.get("gold_reason", ""), "evidence": ""}
                  for key, item in audit.items()}
    core = {item["id"]: {"id": item["id"], "reason": item.get("reason", ""), "evidence": str(item.get("evidence", ""))}
            for item in json.loads((LOGS / "core-judgment-2026-10-15/items.json").read_text())["items"]}
    return {"session": by_session, "core": core}


def main(out: str):
    import netzoo_agent_core.interpretation.core_decision as core_decision
    from netzoo_agent_core.graph.response import respond

    from types import SimpleNamespace

    from netzoo_agent_core.policy import ProjectPolicyLoader

    golds, (by_session, core) = gold_reasons(), harness._gold()
    context = SimpleNamespace(project_policy=ProjectPolicyLoader(LOGS.parents[1]).load())
    original, seen = core_decision.decide_core, {}

    def spy(decision, task="", **kwargs):
        seen["decision"], seen["core"] = decision, original(decision, task, **kwargs)
        return seen["core"]

    rows = []
    for key, folder, sid, task, payload, reread, found, _n in harness.readings():
        label = harness._label(sid, by_session, core)
        if not label:
            continue
        core_decision.decide_core = spy
        try:
            replay_full.replay(folder, task, payload, reread, found)
        except Exception:  # noqa: BLE001 -- the three 10-20 T01 readings of a withdrawn shape (unlabelled)
            continue
        finally:
            core_decision.decide_core = original
        call = seen["core"]
        if not (call.kind == "DECLINE" or (call.kind == "DO" and call.partial)):
            continue
        final = core_decision.with_core(seen["decision"], call)
        try:
            reply = respond(context, {"decision": final.model_dump(mode="json"), "messages": []})["messages"][-1].content
        except KeyError:  # a partial run's body needs the run plan B2 does not rebuild; its reasons are this paragraph
            from netzoo_agent_core.interpretation.capability_check import understanding_paragraph
            reply = "[paragraph only] " + (understanding_paragraph(final.capability_check) or "")
        lines, missing = [], []
        for item in (final.capability_check.results() if final.capability_check else []):
            if item.status not in ("not_available", "partial"):
                continue
            reasons = tagged(item, final.capability_check) or [("R0", "")]
            for kind, text in reasons:
                if text and text not in reply:
                    missing.append(text)
                lines.append({"quote": item.quote, "status": item.status, "type": kind, "text": text})
        if not lines:  # a decline with no result rows: the plain "not something a registered workflow produces"
            lines.append({"quote": task, "status": "not_available", "type": "R0", "text": ""})
        match = SESSION.match(sid)
        gold = golds["core"].get(match.group(1)) if match else golds["session"].get(sid)
        rows.append({"key": key, "session": sid, "item": (gold or {}).get("id"), "task": task, "gold": label,
                     "gold_reason": (gold or {}).get("reason", ""), "gold_evidence": (gold or {}).get("evidence", ""),
                     "kind": call.kind, "basis": call.basis, "partial": call.partial, "lines": lines,
                     "missing_from_reply": missing, "reply": reply})
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    from collections import Counter
    print(f"{len(rows)} replies; gold {dict(Counter(r['gold'] for r in rows))}; "
          f"line types {dict(Counter(line['type'] for r in rows for line in r['lines']))}; "
          f"replies with a tagged text not in the reply: {sum(bool(r['missing_from_reply']) for r in rows)}")


if __name__ == "__main__":
    main(sys.argv[1])
