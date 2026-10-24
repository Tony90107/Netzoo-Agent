"""ROUND-A gate for A2' (withdrawn; needs a2-withdrawn.patch applied to run): on the recorded P5 (h7) traces, every proposal R1 dropped for want of the check's witness that
`declaration_doubt` now witnesses, re-judged by today's `kept_facts` against the turn's recorded check. No model calls.

Usage: python3 a2_h7.py [ROOT ...]   (default: p5/live live-check)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.capability_check import CapabilityCheck  # noqa: E402
from netzoo_agent_core.contracts.fact_check import FactProposal, FactProposals  # noqa: E402
from netzoo_agent_core.interpretation.fact_check import declaration_doubt, kept_facts  # noqa: E402
from netzoo_agent_core.interpretation.menu_requirements import _policy  # noqa: E402
from netzoo_agent_core.method_names import registered_workflows  # noqa: E402


def _task(folder: Path) -> str:
    session = json.load(open(folder / "session.json"))
    users = [m["content"] for m in session.get("messages", []) if m.get("role") == "user"]
    return users[-1] if users else ""


def scan(roots):
    rows, rejected_r1 = [], 0
    for root in roots:
        for path in sorted(Path(root).rglob("trace-*.jsonl")):
            events = [json.loads(line) for line in open(path)]
            kind = lambda e: e.get("event_type") or e.get("type")  # noqa: E731
            checked = next((e["payload"]["check"] for e in events if kind(e) == "routing.capability_checked"), None)
            for event in events:
                if kind(event) != "core.fact_check":
                    continue
                agent = event["payload"]
                drops = [r["proposal"] for r in agent.get("rejected", [])
                         if r["rule"].startswith("R1 the check did not read")]
                rejected_r1 += len(drops)
                task = _task(path.parent)
                proposals = []
                for raw in drops:
                    try:
                        proposal = FactProposal.model_validate(raw)
                    except ValueError:
                        continue
                    if declaration_doubt(task, proposal):
                        proposals.append(proposal)
                if not proposals:
                    continue
                known = registered_workflows()
                actions = [known[name] for name in agent.get("candidates", []) if name in known]
                check = CapabilityCheck.model_validate(checked) if checked else CapabilityCheck()
                decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.9,
                                        reason="replay", matched_actions=actions, capability_check=check)
                again = kept_facts(task, FactProposals(facts=proposals), decision, _policy())
                for proposal in proposals:
                    kept = any(f.question == proposal.question for f in [*again.accepted, *again.queued])
                    why = next((r.rule for r in again.rejected if r.proposal["question"] == proposal.question), "")
                    rows.append((path.parents[1].name, path.parent.name, proposal.question, proposal.user_quote,
                                 "kept" if kept else why))
    return rows, rejected_r1


def main(roots):
    rows, rejected_r1 = scan(roots)
    for session, turn, question, words, verdict in rows:
        print(f"{session:24} {turn:3} {verdict:40} {question!r}  <- {words!r}")
    print(f"{rejected_r1} proposals R1 dropped for want of the check's witness; "
          f"{len(rows)} witnessed by declaration_doubt, {sum(r[-1] == 'kept' for r in rows)} kept")


if __name__ == "__main__":
    main(sys.argv[1:] or [str(HERE / "p5/live"), str(HERE / "live-check")])
