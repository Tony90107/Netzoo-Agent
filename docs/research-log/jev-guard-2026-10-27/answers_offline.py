"""Step 3 offline feasibility (ANSWERS.md): can Jev pick the contract line a U item's unsure sentence depends on, and
read the user's answer against it? Jev calls only (no LLM, no agent run).

For each U item of j1 (12) and h10 (8): Jev picks the unsure sentence (the guard's own call) and the contract line
among the gold workflows' lines (live, the call's workflows; gold here, said in ANSWERS.md); then judges
`reply_fact` (gold: final DO -> meets, DECLINE -> fails) and `reply_restate` (gold: unclear; never fails).

Usage: OPENROUTER_API_KEY=... python3 answers_offline.py > ANSWERS-OFFLINE.txt
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from netzoo_agent_core.graph import jev_guard_call as g  # noqa: E402

MISREAD = HERE.parents[2].parent / "netzoo-misread/docs/research-log/misread-detection-2026-10-25"
TAU = g.THRESHOLD


def items():
    for name, path in (("j1", HERE / "j1/items.json"), ("h10", MISREAD / "h10/items.json")):
        for item in json.loads(path.read_text())["single"]:
            if item["category"] == "U":
                yield name, item


def sentence_of(prompt: str) -> tuple[str | None, float]:
    sentences = g.request_sentences(prompt)
    options = {f"s{i}": t for i, t in enumerate(sentences, 1)} | {"none": "no sentence says this"}
    state = f"Registered workflows:\n{g.registry_text()}\n\nUser request (first turn):\n{prompt}"
    out = g._decide(state, {"sentence": {"type": "choice", "instructions": g.SENTENCE_INSTRUCTIONS,
                                         "criteria": options}})
    answer = out["answers"]["sentence"]
    return (options.get(answer["choice"]) if answer["choice"] != "none" else None), answer["confidence"]


def main():
    rows = []
    for name, item in items():
        sentence, s_conf = sentence_of(item["prompt"])
        row = {"set": name, "id": item["id"], "sentence_found": bool(sentence and s_conf >= TAU),
               "final": item["final_after_fact"]["call"]}
        if row["sentence_found"]:
            pick = g.pick_contract(item["prompt"], sentence, item["workflows"])
            row["contract"] = pick["contract"]
            row["contract_conf"] = pick["contract_confidence"]
            if pick["contract"]:
                question = "Before I go ahead, could you settle this point you mentioned?"
                for reply in ("reply_fact", "reply_restate"):
                    judged = g.judge_answer(pick["contract"], sentence, question, item[reply])
                    row[reply] = [judged["answer"], round(judged["confidence"], 2)]
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    found = [r for r in rows if r.get("contract")]

    def acted(r, reply):  # the decision the guard would take: fails only at >= TAU
        choice, conf = r[reply]
        return choice if conf >= TAU else "unsure"

    fact = Counter((r["final"], acted(r, "reply_fact")) for r in found)
    restate = Counter(acted(r, "reply_restate") for r in found)
    wrong_fails = [r["id"] for r in found if acted(r, "reply_fact") == "fails" and r["final"] != "DECLINE"]
    wrong_fails += [r["id"] + "(restate)" for r in found if acted(r, "reply_restate") == "fails"]
    caught = [r["id"] for r in found if acted(r, "reply_fact") == "fails" and r["final"] == "DECLINE"]
    print(f"\nU items {len(rows)}; sentence found {sum(r['sentence_found'] for r in rows)}; contract line {len(found)}")
    print(f"reply_fact: (gold final, guard) {dict(fact)}")
    print(f"reply_restate: {dict(restate)}")
    print(f"declines caught {len(caught)}/{sum(r['final'] == 'DECLINE' for r in rows)} {caught}; "
          f"wrong declines {wrong_fails}")
    print("gates: A1 wrong declines == 0:", not wrong_fails, "| A2 caught >= half of gold DECLINE finals:",
          len(caught) * 2 >= sum(r["final"] == "DECLINE" for r in rows))
    (HERE / "answers-offline.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
