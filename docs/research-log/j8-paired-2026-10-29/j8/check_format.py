"""j8 sealing check (adapted from j4) (jev-shadow PLAN-FRESH.md): counts and format only -- never a prompt, reason or deciding fact.

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
    print("names_workflow:", dict(Counter((i["category"], bool(i.get("names_workflow"))) for i in single)))
    print("dragon_control:", dict(Counter((i["category"], bool(i.get("dragon_control"))) for i in single)))
    print("reply fields:", {f: sum(bool(i.get(f)) for i in single) for f in ("reply_restate", "reply_fact", "fact_keywords",
                                                                          "final_after_fact", "reply_result", "final_after_result", "reply_confirm", "reply_form")})
    print("final calls:", dict(Counter((f, (i.get(f) or {}).get("call")) for i in single
                                       for f in ("final_after_fact", "final_after_result") if i.get(f))))
    ids = [i["id"] for i in single]
    print("ids Z01-Z48:", sorted(ids) == [f"Z{n:02d}" for n in range(1, 49)])
    print("non-ASCII prompts:", [i["id"] for i in single if not i["prompt"].isascii()] or "none",
          "| unknown workflow names:", [i["id"] for i in single if not set(i.get("workflows", [])) <= WORKFLOWS] or "none")
    def all_evidence(item):
        return " ; ".join([item.get("evidence", "") or ""] + [(item.get(f) or {}).get("evidence", "") or ""
                                                           for f in ("final_after_fact", "final_after_result")])

    missing = sorted({i["id"] for i in single for source, quote in QUOTE.findall(all_evidence(i))
                      if " ".join(quote.split()) not in " ".join(sources(source).split())})
    print("evidence quotes not found verbatim:", missing or "none")
    named = Counter(w for i in single for w in WORKFLOWS if re.search(rf"(?<![\w-]){re.escape(w)}(?![\w-])", i["prompt"]))
    listed = Counter(w for i in single for w in set(i.get("workflows", [])))
    print("workflows (listed in gold / named in a prompt):",
          {w: (listed[w], named[w]) for w in sorted(WORKFLOWS)})


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "items.json")
