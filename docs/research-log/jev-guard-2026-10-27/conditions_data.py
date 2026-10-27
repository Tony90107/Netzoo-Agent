"""Step 1 offline data (CONDITIONS.md): every first-turn DO call with its workflows and gold, from the replay (757
labelled readings), j1 arm S, h10 and h9 live sessions. Writes conditions-data.json. No model calls."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parents[2].parent
MISREAD = WT / "netzoo-misread/docs/research-log/misread-detection-2026-10-25"


def core_of(folder: Path) -> dict:
    core = {}
    for trace in sorted(folder.glob("trace-*.jsonl")) + sorted(folder.glob("events.jsonl")):
        for line in trace.read_text().splitlines():
            if '"core.decision"' in line and (row := json.loads(line)).get("event_type") == "core.decision":
                core = row["payload"]
    return core


def main():
    rows = []
    signals = {r["key"]: r for r in json.loads((MISREAD / "signals-replay.json").read_text())}
    for key, r in json.loads((HERE / "replay-frozen.json").read_text()).items():
        s = signals.get(key)
        if not s or not r.get("gold") or r["kind"] != "DO" or r["recorded"] != "DO":
            continue
        core = core_of(Path(r["where"]))
        if core.get("kind") == "DO" and core.get("workflows"):
            rows.append({"set": "replay", "id": r["session"], "request": s["request"], "gold": r["gold"],
                         "workflows": core["workflows"]})
    items = {i["id"]: i for i in json.loads((HERE / "j1/items.json").read_text())["single"]}
    for folder in sorted((HERE / "live/j1").glob("hb-j1-*-1")):
        core, item = core_of(folder / "t1"), items[folder.name.split("-")[2]]
        if core.get("kind") == "DO" and core.get("workflows"):
            rows.append({"set": "j1", "id": item["id"], "request": item["prompt"],
                         "gold": "DO" if item["expected_call"] == "PARTIAL" else item["expected_call"],
                         "workflows": core["workflows"], "group": item["category"],
                         "dragon": bool(item.get("dragon_control"))})
    for tag in ("h10", "h9"):
        items = {i["id"]: i for i in json.loads((MISREAD / tag / "items.json").read_text())["single"]}
        for folder in sorted((MISREAD / "live" / tag).glob(f"hb-{tag}-*-1")):
            core, item = core_of(folder / "t1"), items[folder.name.split("-")[2]]
            if core.get("kind") == "DO" and core.get("workflows"):
                rows.append({"set": tag, "id": item["id"], "request": item["prompt"],
                             "gold": "DO" if item["expected_call"] == "PARTIAL" else item["expected_call"],
                             "workflows": core["workflows"], "group": item.get("category"),
                             "dragon": bool(item.get("dragon_control"))})
    unique = {}
    for r in rows:
        unique.setdefault((r["request"], tuple(r["workflows"])), r)
    out = list(unique.values())
    (HERE / "conditions-data.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(len(rows), "DO calls,", len(out), "unique (request, workflows)")
    print(Counter((r["set"], r["gold"]) for r in out))


if __name__ == "__main__":
    main()
