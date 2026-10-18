"""Offline what-ifs on the p1 bench readings (no model calls): the same readings re-decided with one part of the
reading set aside, to size each cause of wrong calls. Analysis only -- the frozen design is not changed by it.

Usage: whatif.py TAG
"""
import json
import sys
from collections import Counter

from bench import GOLD, ITEMS, gate_score
from p1common import HERE


def run(tag: str) -> None:
    from netzoo_agent_core.contracts.menu_reading import MenuReading
    from netzoo_agent_core.interpretation.menu_decision import decide_menu
    rows = json.loads((HERE / "live" / tag / "bench.json").read_text())["rows"]
    cases = {
        "as read": lambda r: r,
        "requirements set aside": lambda r: r.model_copy(update={"wanted": [
            w.model_copy(update={"requirements": []}) for w in r.wanted]}),
        "gold context_mentions": None,
    }
    for arm in ("first", "focused"):
        for name, change in cases.items():
            right = Counter()
            for row in rows:
                source = row["focus"] if arm == "focused" and row.get("focus", {}).get("ran") else row
                item = ITEMS[row["id"]]
                reading = MenuReading.model_validate(source["reading"])
                if change is None:
                    reading = reading.model_copy(update={"context_mentions": GOLD[row["id"]].get("context_mentions")
                                                         or []})
                else:
                    reading = change(reading)
                outcome = gate_score(item, decide_menu(reading, item["prompt"]), GOLD[row["id"]].get("fact"))
                right[item["class"]] += outcome == "correct"
            print(f"{arm:8} {name:26} {dict(sorted(right.items()))} total {sum(right.values())}/112")


if __name__ == "__main__":
    run(sys.argv[1])
