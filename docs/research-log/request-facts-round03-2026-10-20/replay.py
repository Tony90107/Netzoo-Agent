"""ROUND-03 offline replay (collab/ROUND-03-PLAN.md section 3): no model calls.

Every distinct recorded capability reading (event `routing.capability_checked`, with the re-read that followed it when
there was one) is checked again by `build_capability_check` -- once by the code before ROUND-03 (a checkout given by
--scripts) and once by this checkout -- and the two checks are compared with the ROUND-03 fields left out. This
checkout also reports the shared record: reads per fact, conflicts, and how many of the reading's values the result
fields repeat.

Usage:
  python3 -I replay.py checks OUT.json [--scripts DIR]   rebuild every check with that code
  python3 -I replay.py compare OLD.json NEW.json        list every check that differs (ROUND-03 fields left out)
  python3 -I replay.py metrics NEW.json                 the record's numbers (NEW from this checkout)
"""
from __future__ import annotations

import glob
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREE = HERE.parents[2]
ROOTS = [WORKTREE / "docs" / "research-log",
         WORKTREE.parents[1] / "netzoo_agent" / "docs" / "research-log"]  # the main checkout's recorded rounds
ROUND03 = ("facts", "fact_conflicts")


def _readings():
    """(key, task, proposal payload, re-read payload or None, passages) for each distinct recorded reading."""
    seen = set()
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
                proposal = event["payload"]["proposal"]
                reread = None
                for later in events[index + 1:]:  # the re-read of this reading, before any next reading
                    if later.get("event_type") == "routing.capability_checked":
                        break
                    if later.get("event_type") == "routing.capability_reread":
                        reread = later["payload"]
                        break
                for task in reversed(users):
                    key = hashlib.sha256(json.dumps([task, proposal, reread], sort_keys=True).encode()).hexdigest()[:16]
                    if _fits(task, proposal):
                        break
                if key in seen:
                    continue
                seen.add(key)
                yield key, str(Path(path).parent.relative_to(root.parent.parent)), task, proposal, reread


def _fits(task, proposal) -> bool:
    from netzoo_agent_core.interpretation.request_spans import _span
    quotes = [ask["quote"] for name, sentence in proposal.items() if name[1:].isdigit() for ask in sentence["asks"]]
    return all(_span(task, quote) is not None for quote in quotes)


def _proposal(payload):
    from netzoo_agent_core.contracts.capability_check import proposal_model
    count = sum(1 for name in payload if name[1:].isdigit())
    for compact in (False, True):
        try:
            return proposal_model(count, compact).model_validate(payload)
        except Exception:  # noqa: BLE001 -- a recording of an older schema
            continue
    return None


def checks(out: str):
    from netzoo_agent_core.contracts.capability_check import reread_as_proposal, reread_model
    from netzoo_agent_core.interpretation.capability_check import build_capability_check
    from netzoo_agent_core.interpretation.reread import merge_reread

    found, skipped = {}, Counter()
    for key, where, task, payload, reread in _readings():
        proposal = _proposal(payload)
        if proposal is None:
            skipped["unparsable"] += 1
            continue
        try:
            check, _rejected = build_capability_check(task, proposal)
            if reread and reread.get("reread"):
                raw = reread["reread"]
                model = reread_model(sum(1 for name in raw if name[1:].isdigit()))
                again, unplaced = build_capability_check(
                    task, reread_as_proposal(model.model_validate(raw), getattr(proposal, "conditions", None)))
                check = merge_reread(task, check, again, reread.get("passages") or [], unplaced)
        except Exception as error:  # noqa: BLE001
            skipped[f"error: {type(error).__name__}"] += 1
            continue
        found[key] = {"where": where, "task": task, "proposal": payload, "check": check.model_dump(mode="json")}
    Path(out).write_text(json.dumps(found, indent=1))
    print(f"{len(found)} checks -> {out}; skipped {dict(skipped)}")


def _without_round03(check: dict) -> dict:
    check = {k: v for k, v in check.items() if k not in ROUND03}
    check["requirements"] = [{k: v for k, v in item.items() if k != "fact_ids"} for item in check["requirements"]]
    return check


def compare(old_path: str, new_path: str):
    old, new = json.loads(Path(old_path).read_text()), json.loads(Path(new_path).read_text())
    keys = sorted(set(old) & set(new))
    differ = [key for key in keys if _without_round03(old[key]["check"]) != _without_round03(new[key]["check"])]
    print(f"compared {len(keys)} (old only {len(set(old) - set(new))}, new only {len(set(new) - set(old))}); "
          f"different: {len(differ)}")
    for key in differ[:20]:
        print("  ", key, new[key]["where"])


def _leaves(value) -> tuple[int, int]:
    """(filled, empty) leaf values; a non-empty list counts its elements, an empty one counts once as empty."""
    if isinstance(value, dict):
        counts = [_leaves(v) for v in value.values()]
        return sum(c[0] for c in counts), sum(c[1] for c in counts)
    if isinstance(value, list):
        if not value:
            return 0, 1
        counts = [_leaves(v) for v in value]
        return sum(c[0] for c in counts), sum(c[1] for c in counts)
    return (0, 1) if value in (None, "", "none", "not_stated") else (1, 0)


METHOD_FIELDS = ("named_method", "named_method_quote", "settings", "sample_count", "sample_count_quote",
                 "feature_counts")


def metrics(new_path: str):
    data = json.loads(Path(new_path).read_text())
    totals = Counter()
    reads_by_reader = Counter()
    conflicts = []
    for key, row in data.items():
        check, proposal = row["check"], row["proposal"]
        totals["checks"] += 1
        facts = check.get("facts", [])
        totals["facts"] += len(facts)
        for fact in facts:
            if fact["origin"] == "derived":
                totals["derived"] += 1
                continue
            totals[f"facts:{fact['property']}"] += 1
            totals["reads"] += len(fact["evidence"])
            if len(fact["evidence"]) > 1:
                totals["facts read more than once"] += 1
            for evidence in fact["evidence"]:
                reads_by_reader[evidence["reader"]] += 1
            readers = {evidence["reader"] for evidence in fact["evidence"]}
            if "result" in readers:
                totals["facts read by a result: also by the request" if "request" in readers
                       else "facts read by a result only"] += 1
                if "request" not in readers:
                    totals[f"result-only {fact['property']}"] += 1
            if fact["state"] == "unsure":
                totals["unsure"] += 1
                if {e["reader"] for e in fact["evidence"]} >= {"count_alternatives", "unknown_facts"}:
                    totals["unsure read by both candidate fields"] += 1
        for found in check.get("fact_conflicts", []):
            conflicts.append((row["where"], found["property"], found["result"][:50], found["used"], found["set_aside"]))
        cited = [item for item in check["requirements"] if item.get("fact_ids")]
        totals["results citing facts"] += len(cited)
        totals["results"] += sum(1 for item in check["requirements"] if item["kind"] == "result")
        # the reading's own output: method fields at request level vs inside each ask (and each open-choice option)
        conditions = proposal.get("conditions") or {}
        filled, empty = _leaves({name: conditions.get(name) for name in METHOD_FIELDS if name in conditions})
        totals["request method leaves filled"] += filled
        totals["request method leaves empty"] += empty
        asks = [ask for name, sentence in proposal.items() if name[1:].isdigit() for ask in sentence["asks"]]
        asks += [option for choice in conditions.get("open_choices") or [] for option in choice.get("options", [])]
        for ask in asks:
            filled, empty = _leaves({name: ask.get(name) for name in METHOD_FIELDS if name in ask})
            totals["result method leaves filled"] += filled
            totals["result method leaves empty"] += empty
            totals["asks"] += 1
    print(json.dumps({**totals, "reads by reader": dict(reads_by_reader)}, indent=1))
    print(f"conflicts: {len(conflicts)}")
    for found in conflicts:
        print("  ", found)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[0] == "checks":
        sys.path.insert(0, args[args.index("--scripts") + 1] if "--scripts" in args else str(WORKTREE / "scripts"))
        checks(args[1])
    elif args[0] == "compare":
        compare(args[1], args[2])
    elif args[0] == "metrics":
        metrics(args[1])
