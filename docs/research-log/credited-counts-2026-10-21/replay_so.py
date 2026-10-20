"""Offline replay of the second opinion with and without candidate weighing (no model calls).

Every recorded reading followed by a second opinion that answered: the check is rebuilt from the reading (and its
re-read) with this checkout, the recorded pairs and answers are applied by `apply_second_opinion` -- once without the
request's words (the code before this change: nothing weighed) and once with them -- then `wait_on_asked` and the
recorded session's `decide_core`, as count-scope-r09's replay_core does. A pair whose requirement quote differs from
the recorded check's is not applied (the rebuilt check is not the one the answers were for). Condition checks and the
ruled-out step after the second opinion are not replayed, so changes are read as direction.

Usage: python3 replay_so.py OUT.json
"""
from __future__ import annotations

import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parents[2]
sys.path.insert(0, str(WT / "scripts"))
sys.path.insert(0, str(WT / "docs/research-log/request-facts-round03-2026-10-20"))
sys.path.insert(0, str(WT / "docs/research-log/count-scope-r09-2026-10-20"))
ROOTS = [WT / "docs/research-log", WT.parents[1] / "netzoo_agent/docs/research-log"]


def _recorded():
    from replay import _fits
    for root in ROOTS:
        for path in sorted(glob.glob(str(root / "**" / "events.jsonl"), recursive=True)):
            session = Path(path).with_name("session.json")
            if not session.exists():
                continue
            users = [m["content"] for m in json.loads(session.read_text()).get("messages", []) if m["role"] == "user"]
            events = [json.loads(line) for line in open(path) if line.strip()]
            for index, event in enumerate(events):
                if event.get("event_type") != "routing.capability_checked" or not event["payload"].get("proposal"):
                    continue
                reread = opinion = None
                for later in events[index + 1:]:
                    kind = later.get("event_type")
                    if kind == "routing.capability_checked":
                        break
                    if kind == "routing.capability_reread" and reread is None:
                        reread = later["payload"]
                    if kind == "routing.capability_second_opinion":
                        opinion = later["payload"]
                        break
                if not opinion or not opinion.get("answers") or not opinion.get("pairs"):
                    continue
                proposal = event["payload"]["proposal"]
                task = next((t for t in reversed(users) if _fits(t, proposal)), None)
                if task is None:
                    continue
                yield Path(path).parent, task, proposal, reread, event["payload"].get("check") or {}, opinion


def main(out: str):
    from replay import _proposal
    from replay_core import _gold, KIND  # noqa: F401
    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.contracts.capability_check import reread_as_proposal, reread_model
    from netzoo_agent_core.graph.fact_check_call import without_legacy_waits
    from netzoo_agent_core.interpretation.capability_check import (
        apply_second_opinion, build_capability_check, wait_on_asked)
    from netzoo_agent_core.interpretation.core_decision import decide_core
    from netzoo_agent_core.interpretation.reread import merge_reread

    gold, core_items = _gold()
    rows, counts, seen = [], Counter(), set()
    for folder, task, payload, reread, recorded, opinion in _recorded():
        key = (str(folder), task, json.dumps(payload, sort_keys=True))
        if key in seen:
            continue
        seen.add(key)
        counts["second opinions"] += 1
        proposal = _proposal(payload)
        if proposal is None:
            counts["unparsable"] += 1
            continue
        try:
            check, _ = build_capability_check(task, proposal)
            if reread and reread.get("reread"):
                raw = reread["reread"]
                model = reread_model(sum(1 for name in raw if name[1:].isdigit()))
                again, unplaced = build_capability_check(
                    task, reread_as_proposal(model.model_validate(raw), getattr(proposal, "conditions", None)))
                check = merge_reread(task, check, again, reread.get("passages") or [], unplaced)
        except Exception as error:  # noqa: BLE001
            counts[f"error {type(error).__name__}"] += 1
            continue
        quotes = [item.get("quote") for item in recorded.get("requirements", [])]
        pairs, answers = [], []
        for (index, action, keys), answer in zip(opinion["pairs"], opinion["answers"]):
            if index < len(check.requirements) and index < len(quotes) and check.requirements[index].quote == quotes[index]:
                pairs.append((index, action, keys))
                answers.append(answer)
        if not pairs:
            counts["pairs not matching the rebuilt check"] += 1
            continue
        if check.count_alternatives:
            counts["with candidate counts"] += 1
        before = wait_on_asked(apply_second_opinion(check, pairs, answers), pairs)
        after = wait_on_asked(apply_second_opinion(check, pairs, answers, task), pairs)
        session = json.loads((folder / "session.json").read_text())
        try:
            decision = TaskDecision.model_validate(session["plan"]["decision"])
        except Exception:  # noqa: BLE001
            decision = None
        kinds = []
        for found in (before, after):
            if decision is None:
                kinds.append(None)
                continue
            if decision.fact_check is not None and decision.fact_check.status == "checked":
                found = without_legacy_waits(found)
            kinds.append(decide_core(decision.model_copy(update={"capability_check": found}), task).kind)
        sid = session.get("session_id", "")
        label = gold.get(sid)
        if label is None and (m := re.match(r"cj-[^-]+-(C\d+)-1", sid)):
            label = core_items.get(m.group(1))
        statuses = [[r.status for r in found.results()] for found in (before, after)]
        if statuses[0] != statuses[1] or kinds[0] != kinds[1]:
            counts["changed"] += 1
            rows.append({"where": str(folder).split("research-log/")[-1], "task": task, "gold": label,
                         "statuses": statuses, "kinds": kinds,
                         "candidates": [c["values"] for c in after.count_alternatives],
                         "limits": [r.limits for r in after.results()]})
        if label:
            counts["labelled"] += 1
            counts["right before"] += kinds[0] == label
            counts["right after"] += kinds[1] == label
    Path(out).write_text(json.dumps({"counts": counts, "changed": rows}, indent=1, ensure_ascii=False))
    for row in rows:
        print(f"{row['where'][:70]} gold={row['gold']} {row['kinds'][0]} -> {row['kinds'][1]} "
              f"statuses {row['statuses'][0]} -> {row['statuses'][1]} candidates {row['candidates']}")
    print(dict(counts))


if __name__ == "__main__":
    main(sys.argv[1])
