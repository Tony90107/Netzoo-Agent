"""The recorded live T01 readings with their candidates swapped (no model calls): "nine or seventeen" becomes "one or
two" (every candidate below LIONESS-PANDA's minimum of three) or "2 or 14" (the candidates split), in the request and
in the reading alike. Each perturbed reading is rebuilt, given its recorded second opinion with and without the
request's words, and decided by `decide_core`. The recordings have no second-opinion case whose candidates matter,
so this shows the effect on real readings of the one shape that has one."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import replay_so  # noqa: E402  (sets the import paths)


def main():
    from replay import _proposal
    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.graph.fact_check_call import without_legacy_waits
    from netzoo_agent_core.interpretation.capability_check import (
        apply_second_opinion, build_capability_check, wait_on_asked)
    from netzoo_agent_core.interpretation.core_decision import decide_core

    seen = set()
    for folder, task, payload, _reread, recorded, opinion in replay_so._recorded():
        if "nine or seventeen" not in task or (str(folder), task) in seen:
            continue
        seen.add((str(folder), task))
        decision = TaskDecision.model_validate(json.loads((folder / "session.json").read_text())["plan"]["decision"])
        for words in ("nine or seventeen", "one or two", "2 or 14"):
            new_task = task.replace("nine or seventeen", words)
            proposal = _proposal(json.loads(json.dumps(payload).replace("nine or seventeen", words)))
            check, _ = build_capability_check(new_task, proposal)
            quotes = [item.get("quote", "").replace("nine or seventeen", words) for item in recorded["requirements"]]
            pairs = [(i, a, k) for i, a, k in opinion["pairs"] if i < len(check.requirements)
                     and check.requirements[i].quote == quotes[i]]
            answers = [ans for (i, _a, _k), ans in zip(opinion["pairs"], opinion["answers"])
                       if (i, _a, _k) in pairs]
            kinds = []
            for given in ("", new_task):
                found = wait_on_asked(apply_second_opinion(check, pairs, answers, given), pairs)
                if decision.fact_check is not None and decision.fact_check.status == "checked":
                    found = without_legacy_waits(found)
                core = decide_core(decision.model_copy(update={"capability_check": found}), new_task)
                kinds.append(f"{core.kind}{[f.question for f in core.facts] if core.facts else ''}")
            print(f"{str(folder).split('judgment-live-2026-10-20/')[-1][:10]} {words:18} before {kinds[0]:45} after {kinds[1]}")


if __name__ == "__main__":
    main()
