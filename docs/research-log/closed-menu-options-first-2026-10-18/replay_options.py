"""Options-first decision: replay a recorded dev round with the current code (no model calls).

Each read is rebuilt from what the provider sent: the first read's payload through `to_menu_reading`, the focused
re-read's payload through `merge_focused`, and the requirement verdicts the round recorded (by quote and workflow).
Then `decide_menu` decides it, and the call is compared with the round's own. Dev rounds only -- the held-out and
bench sets are never replayed for tuning.

Usage: replay_options.py TAG   (../closed-menu-phase1-2026-10-18/live/TAG/dev.json)
"""
import json
import sys
from collections import Counter
from pathlib import Path

DEV = Path(__file__).resolve().parent.parent / "closed-menu-phase1-2026-10-18"
sys.path.insert(0, str(DEV))
import p1common  # noqa: E402,F401
from dev import outcome  # noqa: E402

from netzoo_agent_core.contracts.menu_reading import MenuReading  # noqa: E402
from netzoo_agent_core.interpretation.menu_decision import candidate_workflows, decide_menu  # noqa: E402
from netzoo_agent_core.interpretation.menu_focus import merge_focused  # noqa: E402
from netzoo_agent_core.interpretation.menu_reader import to_menu_reading  # noqa: E402


def rebuild(row: dict, task: str) -> MenuReading:
    if row["status"] == "failed" or not row.get("payload"):
        return MenuReading(status="failed")
    reading, _ = to_menu_reading(row["payload"], task)
    focus = row.get("focus") or {}
    if focus.get("ran") and focus.get("payload"):
        reading, _ = merge_focused(reading, focus["payload"], task, tuple(focus["candidates"]))
    recorded = MenuReading.model_validate(row["final"]["reading"])
    verdicts = {r.quote: r.verdicts for w in recorded.wanted for r in w.requirements}
    wanted = [w.model_copy(update={"requirements": [r.model_copy(update={"verdicts": verdicts.get(r.quote, {})})
                                                    for r in w.requirements]}) for w in reading.wanted]
    return reading.model_copy(update={"wanted": wanted})


def main(tag: str) -> None:
    rows = json.loads((DEV / "live" / tag / "dev.json").read_text())["rows"]
    items = {i["id"]: i for i in json.loads((DEV / "dev_items.json").read_text())["items"]}
    before, after, sizes, changed = Counter(), Counter(), Counter(), []
    for row in rows:
        item = items[row["id"]]
        old = outcome(item["class"], row["final"])
        decision = decide_menu(rebuild(row, item["prompt"]), item["prompt"])
        new = outcome(item["class"], {"status": "read", "kind": decision.kind, "partial": decision.partial})
        before[(item["class"], old)] += 1
        after[(item["class"], new)] += 1
        sizes[len(decision.options)] += 1
        if old != new:
            changed.append((row["id"], item["class"], f"{row['final']['kind']}->{decision.kind}", f"{old}->{new}"))
    print("before", dict(sorted(before.items())))
    print("after ", dict(sorted(after.items())))
    print("option-list sizes", dict(sorted(sizes.items())))
    for line in changed:
        print("  ", *line)


if __name__ == "__main__":
    main(sys.argv[1])
