"""ROUND-27 phase 0: the C1 content-labelling batch, from the ROUND-26 field gold's `has` units.

Usage: python3 make_batch.py  ->  content-batch.json (request text and has quotes/slots only; no other labels).
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOLD = HERE.parent / "field-gold-2026-10-22"
SETS = ("core", "h1", "h2", "h3", "h4", "h5")


def main() -> None:
    items = []
    for name in SETS:
        prompts = {i["id"]: i["prompt"] for i in json.loads((GOLD / f"batch-{name}.json").read_text())["items"]}
        for label in json.loads((GOLD / f"labels-{name}.json").read_text())["items"]:
            if not label["has"]:
                continue
            items.append({"set": name, "id": label["id"], "prompt": prompts[label["id"]],
                          "has": [{"n": n, "quote": h["quote"], "slot": h["slot"]} for n, h in enumerate(label["has"])]})
    ids = [i["id"] for i in items]
    assert len(ids) == len(set(ids)), "request ids repeat across sets"
    (HERE / "content-batch.json").write_text(json.dumps({"items": items}, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(items)} requests, {sum(len(i['has']) for i in items)} has units")


if __name__ == "__main__":
    main()
