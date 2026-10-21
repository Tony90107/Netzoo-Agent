"""Codex's 2026-10-21 repairs on the same requests in other words (no model calls).

Each targeted item's recorded reading is rebuilt with one sentence replaced by a same-meaning paraphrase -- in the
request and in the reading alike, as if the reader had quoted the new words -- and decided as count-scope-r09's
replay_core does. A repair that reads the meaning keeps the call; one that matches the item's wording loses it.

Usage: python3 paraphrase.py [--scripts DIR]   (DIR: the code under test; default this checkout)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parents[2]
sys.path.insert(0, sys.argv[sys.argv.index("--scripts") + 1] if "--scripts" in sys.argv else str(WT / "scripts"))
sys.path.insert(0, str(WT / "docs/research-log/request-facts-round03-2026-10-20"))
MAIN = WT.parents[1] / "netzoo_agent"

CASES = {  # item: (gold, original words, [paraphrases])
    "H34": ("DECLINE", "sparsify at confidence 0.05",
            ["sparsify with a confidence of 0.05", "sparsify (confidence 0.05)"]),
    "M25": ("DECLINE", "trying anywhere from 2 to 8 subtypes",
            ["testing between 2 and 8 clusters", "with kmin 2 and kmax 8"]),
    "J17": ("DO", "keep the normalization by each patient's mutation burden",
            ["normalize by each patient's mutation burden", "leave the per-patient burden normalization on"]),
    "H18": ("DECLINE", "Can you set it up that way?",
            ["Is that configuration possible?", "Would that work?"]),
    "J29": ("CLARIFY", "DRAGON or LIONESS-DRAGON, your call",
            ["DRAGON or LIONESS-DRAGON, you pick", "DRAGON or LIONESS-DRAGON, I don't mind which"]),
    "H21": ("DO", "Start PANDA with", ["Please do a PANDA run with", "Go ahead with PANDA using"]),
    "J06": ("CLARIFY", "Run PANDA or GIRAFFE on them now, whichever",
            ["Run PANDA or GIRAFFE on them now, either is fine", "Run PANDA or GIRAFFE on them now, I don't mind"]),
}
SETS = ("closed-menu-phase1b-2026-10-18/heldout/live/h1/", "closed-menu-options-first-2026-10-18/h2/live/h2main/",
        "closed-menu-slim-2026-10-19/h3/live/h3main/", "closed-menu-hybrid-2026-10-19/h4/live/h4main/")


def main():
    from replay import _proposal, _readings
    from netzoo_agent_core.contracts import TaskDecision
    from netzoo_agent_core.contracts.capability_check import reread_as_proposal, reread_model
    from netzoo_agent_core.graph.fact_check_call import without_legacy_waits
    from netzoo_agent_core.interpretation.capability_check import build_capability_check
    from netzoo_agent_core.interpretation.core_decision import decide_core
    from netzoo_agent_core.interpretation.reread import merge_reread

    for _key, where, task, payload, reread in _readings():
        item = next((i for i in CASES if f"-{i}-1/" in where + "/" and any(s in where for s in SETS)), None)
        if item is None:
            continue
        gold, words, paraphrases = CASES[item]
        if words not in task:
            continue
        folder = next(p for root in (WT, MAIN) if (p := root / where).joinpath("session.json").exists())
        decision = TaskDecision.model_validate(json.loads((folder / "session.json").read_text())["plan"]["decision"])
        for variant in [words, *paraphrases]:
            def swap(value):
                return json.loads(json.dumps(value).replace(words, variant))
            new_task = task.replace(words, variant)
            proposal = _proposal(swap(payload))
            try:
                check, _ = build_capability_check(new_task, proposal)
                if reread and reread.get("reread"):
                    raw = swap(reread["reread"])
                    model = reread_model(sum(1 for name in raw if name[1:].isdigit()))
                    again, unplaced = build_capability_check(
                        new_task, reread_as_proposal(model.model_validate(raw), getattr(proposal, "conditions", None)))
                    check = merge_reread(new_task, check, again, swap(reread.get("passages") or []), unplaced)
                if decision.fact_check is not None and decision.fact_check.status == "checked":
                    check = without_legacy_waits(check)
                kind = decide_core(decision.model_copy(update={"capability_check": check}), new_task).kind
            except Exception as error:  # noqa: BLE001
                kind = f"error {type(error).__name__}"
            mark = "ok " if kind == gold else "MISS"
            print(f"{item} gold={gold:8} {mark} {kind:9} {'(original)' if variant == words else variant}")


if __name__ == "__main__":
    main()
