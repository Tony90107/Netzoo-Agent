"""h7 sealing check (ROUND-P5.md): counts and format only -- never a prompt, reply, reason or deciding fact.

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


def texts(item: dict) -> list[str]:
    found = [item.get("prompt", "")]
    fact = item.get("deciding_fact")
    if isinstance(fact, dict):
        found.append(fact.get("answer", ""))
    found += [item.get(key, "") for key in ("correction", "new_request")] + list(item.get("unknown_replies") or [])
    return [text for text in found if text]


def main(name: str):
    data = json.loads((HERE / name).read_text())
    single, multi = data["single"], data["multi"]
    print(f"{name}: {len(single)} single, {len(multi)} multi")
    print("class x form:", dict(sorted(Counter((i["class"], i["form"]) for i in single).items())))
    print("expected_call:", dict(Counter(i["expected_call"] for i in single)))
    print("uncertainty:", dict(Counter(i.get("uncertainty") for i in single)))
    groups = Counter(i["group"] for i in single if i["group"] != i["id"])
    print("pairs:", {g: n for g, n in sorted(groups.items())})
    print("multi type:", dict(Counter(i["type"] for i in multi)), "t1_call:", dict(Counter(i["t1_call"] for i in multi)),
          "answer_form:", dict(Counter((i.get("deciding_fact") or {}).get("answer_form", "") for i in multi)))
    ids = [i["id"] for i in single + multi]
    print("ids unique:", len(ids) == len(set(ids)), "| S01-S36 and M01-M14:",
          sorted(ids) == sorted([f"S{n:02d}" for n in range(1, 37)] + [f"M{n:02d}" for n in range(1, 15)]))
    non_ascii = [i["id"] for i in single + multi if any(not t.isascii() for t in texts(i))]
    names = [i["id"] for i in single + multi
             if not set(i.get("workflows", []) + i.get("final_workflows", []) + i.get("new_request_workflows", []))
             <= WORKFLOWS]
    print("non-ASCII text:", non_ascii or "none", "| unknown workflow names:", names or "none")
    missing = []
    for item in single + multi:
        for field in ("evidence", "final_reason"):  # each field on its own: joined, a match runs across the boundary
            for source, quote in QUOTE.findall(item.get(field, "") or ""):
                if " ".join(quote.split()) not in " ".join(sources(source).split()):
                    missing.append(item["id"])
    print("evidence quotes not found verbatim:", sorted(set(missing)) or "none")
    coverage = Counter(w for i in single + multi for w in set(i.get("workflows", []) + i.get("final_workflows", [])))
    print("workflow coverage:", dict(sorted(coverage.items())))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "items.json")
