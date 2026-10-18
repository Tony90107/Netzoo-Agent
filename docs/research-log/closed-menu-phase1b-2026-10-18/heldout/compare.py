"""Phase 1b step 6: the live system and the closed-menu reader on the same blind held-out items, scored the same way.

Arms:
- live: the current netzoo-agent main path (code 54d08ce7 = netzoo-agent/main 122936cc for scripts and workflows), one
  CLI session per item through run_live.py; its call is the trace's `core.decision` (collect.py -> structure.json).
- menu: the closed-menu reader on this branch -- first read, focused re-read, requirement check -- then `decide_menu`,
  one pass per item (no session runs; reading calls only).
- first: the same pass's first read alone; probe: the same pass with the focused intent probe after the re-read (the
  user's decision, 2026-10-18; its own measured variant). The three reader arms share the first read.

Both are scored by score_core.outcome (copied unchanged from core-judgment-2026-10-15). Whether an ASK targets the
gold deciding fact is judged by one blind labeller (a subagent) from `fact-sheet.json`: the gold fact and each
arm's question text, the arms hidden behind random codes. Reported side by side: accuracy, per class, the
wrong-commitment rate (a DO or DECLINE that is not correct), and a secondary view where any clarifying question on a
vague item counts as right.

Usage: compare.py read-menu TAG          -> live/TAG/menu.json   (announce first)
       compare.py fact-sheet TAG         -> live/TAG/fact-sheet.json, fact-key.json (needs structure.json and menu.json)
       compare.py score TAG              -> live/TAG/compare.json (needs fact-labels.json from the labeller)
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

from plan import CLASSES, HERE, SEED, load_items, write_json
from score_core import EXPECTED, outcome

sys.path.insert(0, str(HERE.parents[1] / "closed-menu-phase1-2026-10-18"))
import p1common  # noqa: E402,F401 -- puts this branch's scripts/ on the path for the reader arms


def read_menu_arm(tag: str) -> None:
    from p1common import git_head, read_many
    from netzoo_agent_core.interpretation.menu_reader import READER_SHAPE
    items = load_items()
    out = HERE / "live" / tag / "menu.json"
    if out.exists():
        raise ValueError("menu.json exists; the round is read once")
    rows = read_many([(items[key], 1) for key in sorted(items)], focus=True, requirements=True, probe=True)
    write_json(out, {"commit": git_head(), "shape": READER_SHAPE, "rows": rows})


_DIMENSION = {"artifact": "which result they want", "artifact_group": "which kind of result they want",
              "granularity": "one result for all samples, one per group, or one per sample",
              "integration": "one joint network across layers or one per layer", "regulators": "which regulators",
              "layers": "which omics layers", "sample_count": "how many samples there are",
              "feature_count": "how many features there are", "file": "what the named file holds"}


_ARM_KEY = {"first": None, "menu": "final", "probe": "final_probe"}
READER_ARMS = tuple(_ARM_KEY)


def _source(row: dict, arm: str) -> dict:
    key = _ARM_KEY[arm]
    return {**row, "status": row["status"]} if key is None else row[key]


def _menu_questions(row: dict, arm: str = "menu") -> list[str]:
    from netzoo_agent_core.contracts.menu_reading import MenuReading
    from netzoo_agent_core.interpretation.menu_decision import decide_menu
    items = load_items()
    final = _source(row, arm)
    decision = decide_menu(MenuReading.model_validate(final["reading"]), items[row["id"]]["prompt"])
    texts = []
    for question in decision.questions:
        name = question.dimension
        if name.startswith("setting:"):
            about = f"the value of {name.split(':', 1)[1].replace('.', ' setting ')}"
        elif name.startswith("requirement:"):
            about = "whether this requirement is a must"
        else:
            about = _DIMENSION.get(name, name.replace("_", " "))
        options = " / ".join(label for _value, label in question.options)
        texts.append(f"Asks {about}" + (f' (quoting "{question.quote}")' if question.quote else "") +
                     f". Options: {options}")
    if decision.settled:
        texts += [f"States that the input check will settle, before running: {quote}" for quote in decision.settled]
    return texts


def _live_questions(row: dict) -> list[str]:
    core = row.get("core") or {}
    texts = [f"{'States that the input check settles' if f.get('settled_by_input_check') else 'Asks'}: "
             f"{f.get('question', '')}" for f in core.get("facts") or []]
    if not texts and row.get("clarification_question"):
        texts.append(f"Asks: {row['clarification_question']}")
    return texts


def _arms(tag: str):
    live_dir = HERE / "live" / tag
    live = {row["item"]: row for row in json.loads((live_dir / "structure.json").read_text()).values()}
    menu = {row["id"]: row for row in json.loads((live_dir / "menu.json").read_text())["rows"]}
    return live, menu


def _menu_core(row: dict, arm: str = "menu") -> dict:
    final = _source(row, arm)
    return {"kind": final["kind"] if final.get("status") != "failed" else "UNCHECKED",
            "workflows": final["workflows"], "partial": final["partial"],
            "facts": [{"settled_by_input_check": True}] if final.get("settled") else []}


def fact_sheet(tag: str) -> None:
    items, (live, menu) = load_items(), _arms(tag)
    rng = random.Random(SEED + 18)
    entries, key = {}, {}
    for item_id in sorted(items):
        item = items[item_id]
        if item["class"] != "ask":
            continue
        arms = [("live", live[item_id].get("core") or {}, _live_questions(live[item_id]))] + [
            (arm, _menu_core(menu[item_id], arm), _menu_questions(menu[item_id], arm)) for arm in READER_ARMS]
        seen = {}
        for arm, core, questions in arms:
            asked = core.get("kind") == "ASK" or (core.get("kind") == "DO" and any(
                f.get("settled_by_input_check") for f in core.get("facts") or []))
            if not asked:
                continue
            text = json.dumps(questions)
            if text in seen:  # the same questions from two reader arms are labelled once
                key[seen[text]]["arms"].append(arm)
                continue
            code = f"Q{rng.randrange(100000, 999999)}"
            entries[code] = {"request": item["prompt"], "deciding_fact": item["deciding_fact"], "answer": questions}
            key[code] = {"item": item_id, "arms": [arm]}
            seen[text] = code
    order = list(entries)
    rng.shuffle(order)
    write_json(HERE / "live" / tag / "fact-sheet.json", {code: entries[code] for code in order})
    write_json(HERE / "live" / tag / "fact-key.json", key)
    print(f"{len(entries)} answers to label in fact-sheet.json")


def score(tag: str) -> None:
    items, (live, menu) = load_items(), _arms(tag)
    labels = json.loads((HERE / "live" / tag / "fact-labels.json").read_text())
    key = json.loads((HERE / "live" / tag / "fact-key.json").read_text())
    right_fact = {(v["item"], arm): labels[code] is True for code, v in key.items() for arm in v["arms"]}
    result = {}
    for arm in ("live", *READER_ARMS):
        per_class, per_item, wrong_commit, vague_lenient = Counter(), {}, 0, 0
        for item_id, item in sorted(items.items()):
            core = (live[item_id].get("core") or {"kind": "NONE", "workflows": []}) if arm == "live" \
                else _menu_core(menu[item_id], arm)
            result_, _cost = outcome(item, core, right_fact.get((item_id, arm)))
            right = result_ == "correct"
            per_class[(item["class"], right)] += 1
            if core.get("kind") in ("DO", "DECLINE") and not right:
                wrong_commit += 1
            if item["class"] == "vague" and core.get("kind") in ("ASK", "CLARIFY"):
                vague_lenient += 1
            per_item[item_id] = {"class": item["class"], "kind": core.get("kind") + (
                "(partial)" if core.get("partial") else ""), "workflows": core.get("workflows"), "outcome": result_}
        n = len(items)
        correct = sum(v for (c, ok), v in per_class.items() if ok)
        vague_strict = per_class[("vague", True)]
        result[arm] = {
            "correct": [correct, n],
            "per_class": {c: [per_class[(c, True)], per_class[(c, True)] + per_class[(c, False)]] for c in CLASSES},
            "wrong_commitments": [wrong_commit, n],
            "lenient_vague": {"vague_right": vague_lenient, "correct": [correct - vague_strict + vague_lenient, n]},
            "items": per_item,
        }
    write_json(HERE / "live" / tag / "compare.json", result, exclusive=False)
    for arm, r in result.items():
        print(f"{arm:5} correct {r['correct']} per class {r['per_class']} wrong commitments {r['wrong_commitments']} "
              f"lenient vague {r['lenient_vague']}")


if __name__ == "__main__":
    command, tag = sys.argv[1], sys.argv[2]
    {"read-menu": read_menu_arm, "fact-sheet": fact_sheet, "score": score}[command](tag)
