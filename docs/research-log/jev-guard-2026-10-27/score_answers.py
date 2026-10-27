"""ANSWERS.md live check: L1 and the reported counts, from the j1u sessions. No model calls.

Usage: python3 score_answers.py > RESULTS-ANSWERS.txt
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MISREAD = HERE.parents[2].parent / "netzoo-misread/docs/research-log/misread-detection-2026-10-25"


def events(turn: Path, kind: str) -> list[dict]:
    return [json.loads(line)["payload"] for trace in sorted(turn.glob("trace-*.jsonl"))
            for line in trace.read_text().splitlines() if f'"{kind}"' in line
            and json.loads(line).get("event_type") == kind]


def main():
    items = {i["id"]: i for path in (HERE / "j1/items.json", MISREAD / "h10/items.json")
             for i in json.loads(path.read_text())["single"]}
    rows = []
    for folder in sorted((HERE / "live/j1u").glob("hb-j1u-*-1")):
        item, job = items[folder.name.split("-")[2]], json.loads((folder / "job.json").read_text())
        turns = sorted(folder.glob("t*"))
        cores = [(events(t, "core.decision") or [{}])[-1] for t in turns]
        guard1 = (events(turns[0], "core.jev_guard") or [{}])[-1]
        answer = (events(turns[1], "core.jev_answer") or [{}])[-1] if len(turns) > 1 else {}
        final_gold = item["final_after_fact"]["call"] if "fact" in job["sent"] else item["expected_call"]
        final = cores[-1].get("kind")
        without = answer.get("kind_before") or final
        rows.append({"id": item["id"], "sent": job["sent"], "t1": f"{cores[0].get('kind')}/{cores[0].get('basis')}",
                     "guard1": guard1.get("action"), "line": bool(guard1.get("jev", {}).get("pick_contract")),
                     "answer": (answer.get("judged") or {}).get("answer"), "action": answer.get("action"),
                     "final": f"{final}/{cores[-1].get('basis')}", "without": without, "gold": final_gold,
                     "right": final == final_gold, "right_without": without == final_gold})
    wrong = [r["id"] for r in rows if r["action"] == "declined" and r["gold"] == "DO"]
    caught = [r["id"] for r in rows if r["action"] == "declined" and r["gold"] == "DECLINE"]
    print(f"sessions {len(rows)}; turn-1 Jev asks {sum(r['guard1'] == 'ask' for r in rows)} "
          f"(with a contract line {sum(r['guard1'] == 'ask' and r['line'] for r in rows)}); "
          f"answer reads {sum(bool(r['answer']) for r in rows)}")
    print(f"L1 wrong jev_answer declines: {wrong or 'none'} -> {'PASS' if not wrong else 'FAIL'}")
    print(f"declines caught: {caught}")
    print(f"final right with the step {sum(r['right'] for r in rows)}/{len(rows)}; "
          f"without (kind_before) {sum(r['right_without'] for r in rows)}/{len(rows)}")
    print("\nid | sent | turn 1 | guard t1 | answer read -> action | final | without | gold final")
    for r in rows:
        print(f"  {r['id']} | {'+'.join(r['sent'])} | {r['t1']} | {r['guard1']}{'+line' if r['line'] else ''} | "
              f"{r['answer']} -> {r['action']} | {r['final']} | {r['without']} | {r['gold']}")


if __name__ == "__main__":
    main()
