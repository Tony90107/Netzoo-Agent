"""Rebuild the frozen 999 readings with archived routing/agent answers. No API calls."""
from __future__ import annotations

from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WT = HERE.parents[2]
sys.path.insert(0, str(WT / "scripts"))

from netzoo_agent_core.contracts import TaskDecision
from netzoo_agent_core.contracts.capability_check import proposal_model, reread_as_proposal, reread_model
try:  # harness repair P1 (2026-10-23) removed the lift: no wait is lifted when the fact agent runs
    from netzoo_agent_core.graph.fact_check_call import without_legacy_waits
except ImportError:
    def without_legacy_waits(check):
        return check
from netzoo_agent_core.interpretation.capability_check import (
    apply_second_opinion, build_capability_check, understanding_paragraph,
)
from netzoo_agent_core.interpretation.core_decision import decide_core, with_core
from netzoo_agent_core.interpretation.reread import merge_reread


def write(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def parse(payload):
    count = sum(name[1:].isdigit() for name in payload)
    for compact in (False, True):
        try:
            return proposal_model(count, compact).model_validate(payload)
        except ValueError:
            pass
    raise ValueError("Frozen proposal no longer parses")


def rebuild(row):
    proposal = parse(row["proposal"])
    check, rejected = build_capability_check(row["task"], proposal)
    reread = row["reread"]
    if reread and reread.get("reread"):
        raw = reread["reread"]
        again = reread_model(sum(name[1:].isdigit() for name in raw)).model_validate(raw)
        extra, unplaced = build_capability_check(row["task"], reread_as_proposal(again, proposal.conditions))
        check = merge_reread(row["task"], check, extra, reread.get("passages") or [], unplaced)
    return check, rejected


def main():
    inputs = json.loads(gzip.decompress((HERE / "inputs.json.gz").read_bytes()))
    changes, ownership, transitions = [], [], Counter()
    correct_before = correct_after = labelled = 0
    for key, row in inputs.items():
        check, rejected = rebuild(row)
        for item in rejected:
            if item.get("reason") == "ask_in_other_background_sentence":
                ownership.append({"key": key, "where": row["where"], **item})
        decision = TaskDecision.model_validate(row["decision"])
        if decision.fact_check is not None and decision.fact_check.status == "checked":
            check = without_legacy_waits(check)
        core = decide_core(decision.model_copy(update={"capability_check": check}), row["task"],
                           reason_code=row["reason"] or "")
        before = row["before_core"]
        transitions[before["kind"] + "->" + core.kind] += 1
        label = row["gold"]
        if label:
            labelled += 1
            correct_before += before["kind"] == label
            correct_after += core.kind == label
            assert not (before["kind"] == label and core.kind != label), (key, label)
        if before["kind"] != core.kind or before["asked"] != [f.question for f in core.facts]:
            held = with_core(decision, core)
            assert core.kind == "ASK" and held.action == "no_tool"
            assert not held.should_execute and not held.execution_requested
            changes.append({"key": key, "where": row["where"], "task": row["task"], "gold": label,
                            "before": before, "after": core.model_dump(mode="json")})
    write("changed-calls.json", changes)
    write("sentence-ownership.json", ownership)
    summary = {"readings": len(inputs), "skipped": 0, "transitions": dict(sorted(transitions.items())),
               "changed_calls": len(changes), "ownership_corrections": len(ownership),
               "labelled": labelled, "correct_before": correct_before, "correct_after": correct_after,
               "previously_correct_regressions": 0,
               "limits": "Archived routing, fact-agent answers and run verdicts; no new model reading, "
                         "second opinion or condition calls. Not end-to-end accuracy."}
    write("replay-summary.json", summary)

    # T01 presentation check: reuse only the archived second-opinion answers
    # whose result quote survived. No answer is regenerated or reassigned to a
    # different quote after the background rows have been removed.
    live = WT / "docs/research-log/judgment-live-2026-10-20/attempt-05/live"
    evidence = []
    for name in ("T01", "T02"):
        folder = live / f"hb-judgment20261020e-{name}-1/t1"
        task = json.loads((folder / "manifest.json").read_text())["request"]
        events = [json.loads(line) for line in (folder / "events.jsonl").read_text().splitlines()]
        reading = next(e["payload"] for e in events if e["event_type"] == "routing.capability_checked")
        check, rejected = build_capability_check(task, parse(reading["proposal"]))
        for event in events:
            if event["event_type"] != "routing.capability_second_opinion":
                continue
            pairs, answers = [], []
            for (old_index, action, keys), answer in zip(event["payload"]["pairs"], event["payload"]["answers"]):
                quote = reading["check"]["requirements"][old_index]["quote"]
                for index, result in enumerate(check.requirements):
                    if result.kind == "result" and result.quote == quote:
                        pairs.append((index, action, keys))
                        answers.append(answer)
            check = apply_second_opinion(check, pairs, answers)
        saved = json.loads((folder / "session.json").read_text())
        decision = TaskDecision.model_validate(saved["plan"]["decision"]).model_copy(update={"capability_check": check})
        core = decide_core(decision, task)
        evidence.append({"item": name, "kind": core.kind, "understanding": understanding_paragraph(check),
                         "core": core.model_dump(mode="json"), "rejected": rejected})
    assert [row["kind"] for row in evidence] == ["DO", "ASK"]
    assert "post-QC" not in evidence[0]["understanding"]
    write("targeted-replay.json", evidence)
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
