"""jev-confirm-2026-10-28 ROUND.md gates L1-L3: Jev's read of replies to the data confirm. Jev calls only.

Usage: OPENROUTER_API_KEY=... python3 confirm_offline.py > CONFIRM-OFFLINE.txt   (also writes confirm-offline.json)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from netzoo_agent_core.graph import jev_guard_call as g  # noqa: E402

W = HERE.parents[3]
SETS = {"j2": W / "netzoo-jev-guard/docs/research-log/jev-guard-2026-10-27/j2/items.json",
        "j3": W / "netzoo-jev-combined/docs/research-log/jev-j3-2026-10-27/j3/items.json",
        "j4": HERE.parent / "jev-j4-2026-10-27/j4/items.json"}
PLACED = "Before I go ahead, could you confirm this about your data? (yes or no)"
FIXED_Q = g.condition_question({"data": ["mutation_matrix", 1.0]}, "x")
FIXED_LINE = "PANDA incompatible_input_artifacts: mutation_matrix"
UNSURE = ("No idea, sorry.", "I'm not sure yet.", "I'd have to check with my student.")
DENIAL = "No, that's not what we have; it's a different kind of table."
YES_WORD = re.compile(r"^(yes|yeah|yep|right|correct|exactly|true)\b[\s,.!:;-]*", re.I)


def contract_of(item) -> str:
    found = re.findall(r'"(.+?)"', item.get("evidence") or "")
    return found[0] if found else (item.get("reason") or "")


def cases():
    out = []
    for name, path in SETS.items():
        for item in json.loads(path.read_text())["single"]:
            key = f"{name}:{item['id']}"
            if item["category"] == "T" and item.get("reply_confirm"):
                q = (PLACED, item["prompt"], contract_of(item))
                stripped = YES_WORD.sub("", item["reply_confirm"]).strip()
                out.append(("pos", key, stripped[:1].upper() + stripped[1:], *q))
                out += [("neg-unsure", key, text, *q) for text in UNSURE]
                out.append(("neg-denial", key, DENIAL, *q))
                out.append(("neg-restate", key, item["reply_restate"], *q))
            elif name == "j4" and item["id"] == "S35":
                out.append(("pos", key, item["reply_fact"], g.condition_question(
                    {"data": ["coexpression_network", 1.0]}, "x"), "",
                    "An aggregate COBRA adjusted co-expression artifact is not a direct LIONESS handoff"))
            else:
                for field in ("reply_restate", "reply_fact"):
                    if item.get(field):
                        out.append((f"neg-{field[6:]}", key, item[field], FIXED_Q, "", FIXED_LINE))
    return out


def main():
    rows = []
    for kind, key, reply, question, quote, line in cases():
        read = g.judge_confirm(question, quote, line, reply)
        rows.append({"kind": kind, "key": key, "reply": reply, "question": question, "quote": quote, "line": line,
                     "answer": read["answer"], "confidence": read["confidence"], "cost": read["cost"]})
    yes = lambda r: r["answer"] == "yes" and r["confidence"] >= g.THRESHOLD  # noqa: E731
    pos = [r for r in rows if r["kind"] == "pos"]
    neg = [r for r in rows if r["kind"] != "pos"]
    wrong = [f"{r['kind']} {r['key']}: {r['reply'][:60]} ({r['confidence']:.2f})" for r in neg if yes(r)]
    l1 = sum(yes(r) for r in pos) * 4 >= len(pos) * 3
    print(f"positives {len(pos)}: yes>=0.7 {sum(yes(r) for r in pos)} -> L1 {'PASS' if l1 else 'fail'}")
    for r in pos:
        if not yes(r):
            print(f"   missed {r['key']}: {r['answer']} {r['confidence']:.2f} | {r['reply'][:90]}")
    by = {}
    for r in neg:
        by.setdefault(r["kind"], [0, 0])
        by[r["kind"]][0] += 1
        by[r["kind"]][1] += yes(r)
    print(f"negatives {len(neg)} (kind: n, read yes>=0.7): {by} -> L2 {'PASS' if not wrong else 'FAIL'} {wrong}")

    # L3 stability: S35 and three negatives, 10 reads each
    picks = [next(r for r in pos if r["key"] == "j4:S35"), next(r for r in neg if r["kind"] == "neg-denial"),
             next(r for r in neg if r["reply"] == "No idea, sorry."), next(r for r in neg if r["kind"] == "neg-restate")]
    stable = True
    for r in picks:
        reads = [g.judge_confirm(r["question"], r["quote"], r["line"], r["reply"]) for _ in range(10)]
        sides = {(x["answer"] == "yes" and x["confidence"] >= g.THRESHOLD) for x in reads}
        stable &= len(sides) == 1
        print(f"   L3 {r['kind']} {r['key']}: sides {sides}; answers {[x['answer'] for x in reads]}; "
              f"conf {min(x['confidence'] for x in reads):.2f}-{max(x['confidence'] for x in reads):.2f}")
    print(f"L3 {'PASS' if stable else 'fail'}")
    print(f"-> {'ALL PASS' if l1 and not wrong and stable else 'NOT PASSED'}; cost US${sum(r['cost'] for r in rows):.4f}"
          " (+40 L3 reads)")
    (HERE / "confirm-offline.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
