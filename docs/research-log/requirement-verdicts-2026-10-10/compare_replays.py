"""List the sessions whose re-rendered reply or card differs between two replays (Log 403).

Usage: python docs/research-log/requirement-verdicts-2026-10-10/compare_replays.py <base.jsonl> <cand.jsonl> [--show N]
"""
import difflib
import json
import sys
from collections import Counter


def load(path):
    return {row["session"]: row for row in map(json.loads, open(path))}


def main():
    base, cand = load(sys.argv[1]), load(sys.argv[2])
    show = int(sys.argv[sys.argv.index("--show") + 1]) if "--show" in sys.argv else 0
    reply, card, errors = [], [], Counter()
    for key, row in cand.items():
        old = base[key]
        if "error" in row or "error" in old:
            errors[("base" if "error" in old else "") + ("cand" if "error" in row else "")] += 1
            continue
        if row["reply"] != old["reply"]:
            reply.append(key)
        if row["card"] != old["card"]:
            card.append(key)
    print(f"sessions {len(cand)}; reply changed {len(reply)}; card changed {len(card)}; errors {dict(errors)}")
    print("reply changed by item:", Counter("-".join(key.split("-")[1:2] + key.split("-")[3:4]) for key in reply))
    print("card only:", sorted(set(card) - set(reply)))
    for key in reply[:show]:
        print("=" * 20, key)
        for line in difflib.unified_diff(base[key]["reply"].splitlines(), cand[key]["reply"].splitlines(),
                                         lineterm="", n=0):
            print("  " + line[:240])


if __name__ == "__main__":
    main()
