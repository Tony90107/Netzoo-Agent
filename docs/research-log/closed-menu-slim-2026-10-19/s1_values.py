"""Slim reading S1, offline: how many values a read writes, old shape vs slim (spec 2026-10-19, 0 and 6.1).

Old: the recorded wire payloads of phase 1 -- bench p1 (56 items x 2 reads, v7, with the focused re-read's payload)
and dev d9 (85 reads, v8). Slim: the same readings re-expressed as the two slim payloads (`wire_payloads`: the core
read, and the focused read when step 2 runs it) -- what a slim read would write for the same content. Also the
phase-0 gold readings in the slim shape: what a correct slim read writes. One counter for all (`wire_values`: every
leaf, an empty list once; content = leaves that are not empty, null, false or "not stated"); it gives phase 1's
208/25 on the bench payloads.

No model calls. Usage: python3 s1_values.py
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
P1 = ROOT / "docs/research-log/closed-menu-phase1-2026-10-18"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "docs/research-log/closed-menu-phase0-2026-10-18"))

from phase0_gate import ITEMS, reading as gold_reading  # noqa: E402

from netzoo_agent_core.contracts.menu_reading import MenuReading  # noqa: E402
from netzoo_agent_core.interpretation.slim_reader import (  # noqa: E402
    slim_needs, split_b, to_slim,
)
from netzoo_agent_core.interpretation.slim_values import (  # noqa: E402
    wire_payloads, wire_values,
)
from netzoo_agent_core.method_names import workflows_in  # noqa: E402

DEV = {item["id"]: item for item in json.loads((P1 / "dev_items.json").read_text())["items"]}


def slim_count(menu: MenuReading, prompt: str) -> tuple[int, int, int, int, bool]:
    """(written, content) of the core payload, (written, content) of core + focus, and whether step 3 runs."""
    slim = to_slim(menu)
    core, _b = split_b(slim)
    needs = slim_needs(core, prompt)
    core_payload, focus_payload = wire_payloads(slim, needs, tuple(workflows_in(prompt)))
    a, b = wire_values(core_payload)
    c, d = wire_values(focus_payload) if focus_payload is not None else (0, 0)
    return a, b, a + c, b + d, focus_payload is not None


def summary(values: list[int]) -> str:
    return f"median {statistics.median(values):g}, max {max(values)}" if values else "-"


def main() -> None:
    report = {}
    for name, path, items in (("bench p1 (v7)", P1 / "live/p1/bench.json", ITEMS),
                              ("dev d9 (v8)", P1 / "live/d9/dev.json", DEV)):
        rows = [r for r in json.loads(path.read_text())["rows"] if r.get("payload")]
        old_first, old_first_c, old_all, old_all_c = [], [], [], []
        slim_core, slim_core_c, slim_all, slim_all_c, runs = [], [], [], [], 0
        for row in rows:
            a, b = wire_values(row["payload"])
            focus = row.get("focus") or {}
            c, d = wire_values(focus.get("payload")) if focus.get("payload") else (0, 0)
            old_first.append(a), old_first_c.append(b), old_all.append(a + c), old_all_c.append(b + d)
            menu = (row.get("final") or {}).get("reading") or focus.get("reading") or row["reading"]
            sa, sb, sc, sd, ran = slim_count(MenuReading.model_validate(menu), items[row["id"]]["prompt"])
            slim_core.append(sa), slim_core_c.append(sb), slim_all.append(sc), slim_all_c.append(sd)
            runs += ran
        report[name] = {
            "reads": len(rows),
            "old first read: written": summary(old_first), "old first read: content": summary(old_first_c),
            "old with focused re-read: written": summary(old_all), "old with focused re-read: content": summary(old_all_c),
            "slim core: written": summary(slim_core), "slim core: content": summary(slim_core_c),
            "slim core + focus: written": summary(slim_all), "slim core + focus: content": summary(slim_all_c),
            "slim step 3 runs": f"{runs}/{len(rows)}",
        }
    gold = yaml.safe_load((ROOT / "docs/research-log/closed-menu-phase0-2026-10-18/gold_readings.yaml").read_text())
    counts = [slim_count(gold_reading(raw), ITEMS[key]["prompt"]) for key, raw in sorted(gold.items())]
    report["gold (56, slim shape)"] = {
        "slim core: written": summary([c[0] for c in counts]), "slim core: content": summary([c[1] for c in counts]),
        "slim core + focus: written": summary([c[2] for c in counts]),
        "slim core + focus: content": summary([c[3] for c in counts]),
        "slim step 3 runs": f"{sum(c[4] for c in counts)}/{len(counts)}"}
    for name, lines in report.items():
        print(name)
        for key, value in lines.items():
            print(f"  {key}: {value}")
    (HERE / "s1-values.json").write_text(json.dumps(report, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
