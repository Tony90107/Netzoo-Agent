"""Log 409: a blinded labelling packet of every reply the candidate changed, both versions shuffled together.

Usage (repository root): python docs/research-log/verdict-architecture-2026-10-12/packet409.py

Reads replay/base.jsonl and replay/cand.jsonl (replay409.py), keeps the sessions whose reply or card differs,
and writes replay/packet.md (each version as its own session code, shuffled) and replay/key.json. The
requirements to judge are the gold requirement words of each session's held-out item, as in its round.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = HERE.parent
sys.path.insert(0, str(LOG / "reread-2026-10-11"))
sys.path.insert(0, str(HERE))

from attribute import ROUNDS, SETS  # noqa: E402
from collect14 import card_text  # noqa: E402

WORKTREES = LOG.parents[1].parent / ".worktrees"


def main() -> None:
    base = {row["session"] + "|" + row["tree"]: row for row in map(json.loads, open(HERE / "replay" / "base.jsonl"))}
    cand = {row["session"] + "|" + row["tree"]: row for row in map(json.loads, open(HERE / "replay" / "cand.jsonl"))}
    changed = sorted(k for k in base if (base[k]["reply"], base[k]["card"]) != (cand[k]["reply"], cand[k]["card"]))
    blocks = []
    for key in changed:
        session, tree = key.split("|")
        tag, item = session.split("-")[1], session.split("-")[3]
        gold = {i["id"]: i for i in json.loads((LOG / SETS[tag]).read_text())["items"]}[item]["requirements"]
        data = json.loads((WORKTREES / tree / ".netzoo" / "sessions" / f"{session}.json").read_text())
        users = [m["content"] for m in data.get("messages", []) if m.get("role") == "user"]
        for version, rows in (("base", base), ("cand", cand)):
            row = rows[key]
            blocks.append((f"{key}|{version}", "\n".join([
                "\n".join(f"Request (turn {n}): {text}" for n, text in enumerate(users, 1)), "",
                "Requirements to judge (in the user's words):",
                "\n".join(f'R{n}: "{r["words"]}"' for n, r in enumerate(gold, 1)), "",
                "Reply:", "", "````", row["reply"].strip(), "````", "", "Card shown with the reply:",
                *card_text(row["card"] if "error" not in row["card"] else None), ""])))
    random.seed(409)
    random.shuffle(blocks)
    key_map, out = {}, []
    for index, (key, body) in enumerate(blocks, 1):
        code = f"S{index:03d}"
        key_map[code] = key
        out += [f"## {code}", "", body]
    (HERE / "replay" / "packet.md").write_text("\n".join(out), encoding="utf-8")
    (HERE / "replay" / "key.json").write_text(json.dumps(key_map, indent=1))
    print(f"changed sessions {len(changed)}, packet blocks {len(blocks)}")


if __name__ == "__main__":
    main()
