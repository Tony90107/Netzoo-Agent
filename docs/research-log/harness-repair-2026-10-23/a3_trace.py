"""ROUND-A gate for A3: on recorded live traces, the turns where a refused optional call kept a required read from
running, and whether that read passes its own preflight once the refusal no longer spends the turn. No model calls.

A turn's numbers are the recorded ones: tokens spent when the read was skipped (the refusal's `consumed_tokens`; the
`llm.completed` events are written at the end of a turn, so their order says nothing), and the read's
own input estimate -- the check's from a recorded preflight of the same item (`estimated_input_tokens`), the fact
check's from today's `fact_check_input` over the turn's text and its recorded candidates. The ceilings are the code's:
turn budget plus the reading allowance, less the 1.5k reserve.

Usage: python3 a3_trace.py [ROOT ...]   (default: p5/live live-check)
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))

from netzoo_agent_core.graph.required_check_budget import fact_check_input  # noqa: E402
from netzoo_agent_core.interpretation.menu_requirements import _policy  # noqa: E402
from netzoo_agent_core.llm import _estimated_tokens  # noqa: E402

TURN, ALLOWANCE, RESERVE, CHECK_OUT, FACT_OUT = 30000, 30000, 1500, 16000, 1000
# Refusals that do not flag the turn: the re-read and the condition check return without it; the study purpose and the
# data facts too when a fact read is reserved (their reservation then exceeds the plain output reserve).
NO_FLAG = {"capability_reread", "capability_condition_check"}


def _events(path: Path):
    for line in open(path):
        row = json.loads(line)
        yield row.get("event_type") or row.get("type"), row.get("payload", {})


def _flags(kind, payload) -> bool:
    role = payload.get("role")
    if kind != "budget.blocked" or role in NO_FLAG:
        return False
    if role in ("study_purpose", "data_facts") and payload.get("reserved_output_tokens", 0) > 1200:
        return False
    return True


def _turn_text(folder: Path) -> tuple[str, str]:
    session = json.load(open(folder / "session.json"))
    users = [m["content"] for m in session.get("messages", []) if m.get("role") == "user"]
    return (users[0] if users else ""), (users[-1] if users else "")


def scan(roots):
    check_inputs = defaultdict(list)  # item -> recorded check input estimates
    turns = []
    for root in roots:
        for path in sorted(Path(root).rglob("trace-*.jsonl")):
            events = list(_events(path))
            folder = path.parent
            session = folder.parent.name
            item = session.split("-")[2] if session.count("-") >= 3 else session
            for kind, payload in events:
                if payload.get("role") == "capability_check" and kind in ("budget.warning", "budget.blocked"):
                    check_inputs[item].append(payload["estimated_input_tokens"])
            turns.append((item, session, folder, events))
    rows = []
    for item, session, folder, events in turns:
        spent, flagged_by, check_ran = 0, None, False
        for kind, payload in events:
            if kind == "llm.completed":
                check_ran |= payload.get("role") == "capability_check"
            elif kind in ("budget.warning", "budget.blocked"):
                spent = max(spent, payload.get("consumed_tokens") or 0)
                if _flags(kind, payload) and flagged_by is None:
                    flagged_by = (payload.get("role"), spent)
            elif kind == "core.fact_check" and payload.get("status") == "blocked" and flagged_by:
                prompt, said = _turn_text(folder)
                actions = [a for a, spec in _policy().workflows.items() if spec.workflow in payload.get("candidates", [])]
                text = prompt if prompt == said else f"{prompt}\n{said}"
                estimate = _estimated_tokens(fact_check_input(text, actions, _policy())[1])
                limit = TURN + ALLOWANCE - RESERVE
                rows.append((session, folder.name, "fact check", flagged_by[0], spent,
                             spent >= TURN + ALLOWANCE, spent + estimate + FACT_OUT, limit))
        if flagged_by and not check_ran and not any(k == "routing.capability_checked" for k, _ in events):
            estimate = max(check_inputs.get(item) or [0])
            limit = TURN + ALLOWANCE - RESERVE
            rows.append((session, folder.name, "capability check", flagged_by[0], flagged_by[1],
                         flagged_by[1] >= TURN, flagged_by[1] + estimate + CHECK_OUT if estimate else None, limit))
    return rows


def main(roots):
    rows = scan(roots)
    print(f"{'session':28} {'turn':4} {'skipped read':16} {'refused call':26} {'spent':>6} {'A3 runs it':>10} "
          f"{'projected':>9} {'ceiling':>7}")
    for session, turn, read, refused, spent, was_spent, projected, ceiling in rows:
        runs = "no (spent)" if was_spent else ("?" if projected is None else
                                               "yes" if projected <= ceiling else "no (own preflight)")
        print(f"{session:28} {turn:4} {read:16} {refused:26} {spent:>6} {runs:>10} {projected or '-':>9} {ceiling:>7}")
    print(f"{len(rows)} skipped required reads")


if __name__ == "__main__":
    main(sys.argv[1:] or [str(HERE / "p5/live"), str(HERE / "live-check")])
