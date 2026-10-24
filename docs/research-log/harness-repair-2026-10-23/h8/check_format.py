"""h8 sealing check (ROUND-A1C.md): counts and format only -- never a prompt, reason or deciding fact.

Usage: python3 check_format.py [items.json]
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
WORKFLOWS = {"PANDA", "PUMA", "LIONESS-PANDA", "LIONESS-PUMA", "LIONESS-COEXPRESSION", "LIONESS-DRAGON", "DRAGON",
             "BONOBO", "CONDOR", "COBRA", "OTTER", "GIRAFFE", "SAMBAR"}
QUOTE = re.compile(r"([\w.-]+\.(?:yaml|py)): \"(.+?)\"(?=\s*(?:;|$|,|\n| [\w.-]+\.(?:yaml|py):))", re.S)


def sources(name: str) -> str:
    path = ROOT / "workflows" / name if name.endswith(".yaml") else ROOT / "scripts" / name
    return path.read_text() if path.exists() else ""


def main(name: str):
    single = json.loads((HERE / name).read_text())["single"]
    print(f"{name}: {len(single)} items")
    print("category x sub:", dict(sorted(Counter((i["category"], i["sub"]) for i in single).items())))
    print("category x expected_call:", dict(sorted(Counter((i["category"], i["expected_call"]) for i in single).items())))
    print("uncertainty:", dict(Counter(i.get("uncertainty") for i in single)))
    ids = [i["id"] for i in single]
    print("ids Y01-Y24:", sorted(ids) == [f"Y{n:02d}" for n in range(1, 25)])
    print("non-ASCII prompts:", [i["id"] for i in single if not i["prompt"].isascii()] or "none",
          "| unknown workflow names:", [i["id"] for i in single if not set(i.get("workflows", [])) <= WORKFLOWS] or "none")
    missing = sorted({i["id"] for i in single for source, quote in QUOTE.findall(i.get("evidence", "") or "")
                      if " ".join(quote.split()) not in " ".join(sources(source).split())})
    print("evidence quotes not found verbatim:", missing or "none")
    named = Counter(w for i in single for w in WORKFLOWS if re.search(rf"(?<![\w-]){re.escape(w)}(?![\w-])", i["prompt"]))
    listed = Counter(w for i in single for w in set(i.get("workflows", [])))
    print("workflows (listed in gold / named in a prompt):",
          {w: (listed[w], named[w]) for w in sorted(WORKFLOWS)})


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "items.json")
