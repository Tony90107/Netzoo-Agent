"""Options-first blind round h2: three arms on the same items, scored the same way (no model calls here).

Arms (each item once):
- main: the live netzoo-agent main path (`.worktrees/netzoo-core-p0-run`, 54d08ce7 = main 122936cc code), tag h2main;
- hybrid: the live path with the hybrid hard gates (`.worktrees/netzoo-hybrid-run`), tag h2hyb;
- options: the options-first path on this branch -- first read, focused re-read, requirement check, `decide_menu`
  (`read-options`, reading calls only).

What each arm offers: live DO and ASK -> `core.workflows`, CLARIFY -> `core.clarify.candidates`, DECLINE -> the
alternatives after the denial; options-first -> `MenuDecision.options` (DECLINE -> `nearest`).

Metrics (ROUND.md, frozen before running):
  a. the right workflow among the offered feasible options (do, ask, vague items; any position and the first 3);
  b. safety -- nothing infeasible offered as runnable: a DO on a dont item (also reported: a DO on an ask item, run
     before the deciding fact);
  c. option-list length (median, share with at most 3);
  d. the deciding fact asked when needed (ask items; blind labeller on `fact-sheet.json`);
  and the old strict score (score_core.outcome) for reference.

Usage: compare_h2.py read-options TAG     -> live/TAG/options.json (announce first)
       compare_h2.py fact-sheet TAG       -> live/TAG/fact-sheet.json, fact-key.json
       compare_h2.py score TAG            -> live/TAG/compare.json (needs fact-labels.json)
"""
from __future__ import annotations

import json
import random
import statistics
import sys
from collections import Counter

from plan import CLASSES, HERE, SEED, load_items, write_json
from score_core import outcome

sys.path.insert(0, str(HERE.parents[1] / "closed-menu-phase1-2026-10-18"))
sys.path.insert(0, str(HERE.parents[1] / "closed-menu-phase1b-2026-10-18" / "heldout"))
import p1common  # noqa: E402,F401 -- puts this branch's scripts/ on the path

LIVE_ARMS = {"main": "h2main", "hybrid": "h2hyb"}
ARMS = ("main", "hybrid", "options")


def norm(names) -> list[str]:
    return [str(n).strip().upper().replace("LIONESS ", "LIONESS-") for n in names or []]


def read_options(tag: str) -> None:
    from p1common import git_head, read_many
    from netzoo_agent_core.interpretation.menu_reader import READER_SHAPE
    items = load_items()
    out = HERE / "live" / tag / "options.json"
    if out.exists():
        raise ValueError("options.json exists; the round is read once")
    rows = read_many([(items[key], 1) for key in sorted(items)], focus=True, requirements=True)
    write_json(out, {"commit": git_head(), "shape": READER_SHAPE, "rows": rows})


def _live_rows(tag: str) -> dict:
    return {row["item"]: row for row in json.loads((HERE / "live" / tag / "structure.json").read_text()).values()}


def _options_rows(tag: str) -> dict:
    return {row["id"]: row for row in json.loads((HERE / "live" / tag / "options.json").read_text())["rows"]}


def arm_call(arm: str, row: dict) -> dict:
    """kind, workflows (scored), offered (the options shown), partial, facts, questions text."""
    if arm in LIVE_ARMS:
        core = row.get("core") or {"kind": "NONE", "workflows": []}
        kind = core.get("kind")
        if kind == "CLARIFY":
            offered = (core.get("clarify") or {}).get("candidates") or []
        elif kind == "DECLINE":
            offered = [w for part in core.get("declined") or [] for w in part.get("alternatives") or []]
        else:
            offered = core.get("workflows") or []
        texts = [f"{'States that the input check settles' if f.get('settled_by_input_check') else 'Asks'}: "
                 f"{f.get('question', '')}" for f in core.get("facts") or []]
        if not texts and row.get("clarification_question"):
            texts.append(f"Asks: {row['clarification_question']}")
        return {"core": core, "offered": norm(offered), "questions": texts}
    final = row["final"]
    kind = final["kind"] if final.get("status") != "failed" else "UNCHECKED"
    offered = final.get("nearest") if kind == "DECLINE" else final.get("options")
    core = {"kind": kind, "workflows": final["workflows"], "partial": final["partial"],
            "facts": [{"settled_by_input_check": True}] if final.get("settled") else []}
    return {"core": core, "offered": norm(offered or []), "questions": _option_questions(row)}


def _option_questions(row: dict) -> list[str]:
    from netzoo_agent_core.contracts.menu_reading import MenuReading
    from netzoo_agent_core.interpretation.menu_decision import decide_menu
    from compare import _DIMENSION
    items = load_items()
    decision = decide_menu(MenuReading.model_validate(row["final"]["reading"]), items[row["id"]]["prompt"])
    texts = []
    for question in decision.questions:
        name = question.dimension
        about = (f"the value of {name.split(':', 1)[1].replace('.', ' setting ')}" if name.startswith("setting:")
                 else "whether this requirement is a must" if name.startswith("requirement:")
                 else _DIMENSION.get(name, name.replace("_", " ")))
        texts.append(f"Asks {about}" + (f' (quoting "{question.quote}")' if question.quote else "") +
                     ". Options: " + " / ".join(label for _v, label in question.options))
    texts += [f"States that the input check will settle, before running: {q}" for q in decision.settled]
    return texts


def _arms(tag: str) -> dict:
    found = {arm: _live_rows(live) for arm, live in LIVE_ARMS.items()}
    found["options"] = _options_rows(tag)
    return found


def fact_sheet(tag: str) -> None:
    items, rows = load_items(), _arms(tag)
    rng = random.Random(SEED + 2)
    entries, key, seen = {}, {}, {}
    for item_id in sorted(items):
        if items[item_id]["class"] != "ask":
            continue
        for arm in ARMS:
            call = arm_call(arm, rows[arm][item_id])
            core = call["core"]
            asked = core.get("kind") == "ASK" or (core.get("kind") == "DO" and any(
                f.get("settled_by_input_check") for f in core.get("facts") or []))
            if not asked:
                continue
            text = json.dumps([item_id, call["questions"]])
            if text in seen:
                key[seen[text]]["arms"].append(arm)
                continue
            code = f"Q{rng.randrange(100000, 999999)}"
            entries[code] = {"request": items[item_id]["prompt"], "deciding_fact": items[item_id]["deciding_fact"],
                             "answer": call["questions"]}
            key[code] = {"item": item_id, "arms": [arm]}
            seen[text] = code
    order = list(entries)
    rng.shuffle(order)
    write_json(HERE / "live" / tag / "fact-sheet.json", {code: entries[code] for code in order})
    write_json(HERE / "live" / tag / "fact-key.json", key)
    print(f"{len(entries)} answers to label")


def score(tag: str) -> None:
    items, rows = load_items(), _arms(tag)
    labels = json.loads((HERE / "live" / tag / "fact-labels.json").read_text())
    key = json.loads((HERE / "live" / tag / "fact-key.json").read_text())
    right_fact = {(v["item"], arm): labels[code] is True for code, v in key.items() for arm in v["arms"]}
    result = {}
    for arm in ARMS:
        strict, hits, hits3, lengths, unsafe, early, fact = Counter(), Counter(), Counter(), [], [], [], Counter()
        per_item = {}
        for item_id, item in sorted(items.items()):
            call = arm_call(arm, rows[arm][item_id])
            core, offered, cls = call["core"], call["offered"], item["class"]
            got, _cost = outcome(item, core, right_fact.get((item_id, arm)))
            strict[(cls, got == "correct")] += 1
            gold = set(norm(item["workflows"]))
            if cls != "dont":
                hits[(cls, bool(gold & set(offered)))] += 1
                hits3[(cls, bool(gold & set(offered[:3])))] += 1
            lengths.append(len(offered))
            if cls == "dont" and core.get("kind") == "DO":
                unsafe.append(item_id)
            if cls == "ask" and core.get("kind") == "DO":
                early.append(item_id)
            if cls == "ask":
                fact[right_fact.get((item_id, arm)) is True and core.get("kind") in ("ASK", "DO")] += 1
            per_item[item_id] = {"class": cls, "kind": core.get("kind"), "offered": offered, "outcome": got}
        n_by = Counter(item["class"] for item in items.values())
        result[arm] = {
            "a_right_in_options": {c: [hits[(c, True)], n_by[c]] for c in ("do", "ask", "vague")},
            "a_right_in_first_3": {c: [hits3[(c, True)], n_by[c]] for c in ("do", "ask", "vague")},
            "b_dont_offered_as_runnable": [len(unsafe), n_by["dont"], unsafe],
            "b_ask_run_before_the_fact": [len(early), n_by["ask"], early],
            "c_options_median": statistics.median(lengths), "c_options_at_most_3": [sum(l <= 3 for l in lengths),
                                                                                  len(lengths)],
            "d_fact_asked": [fact[True], n_by["ask"]],
            "strict": {c: [strict[(c, True)], n_by[c]] for c in CLASSES},
            "strict_total": [sum(v for (c, ok), v in strict.items() if ok), len(items)],
            "items": per_item,
        }
    write_json(HERE / "live" / tag / "compare.json", result, exclusive=False)
    for arm, r in result.items():
        print(arm, {k: v for k, v in r.items() if k != "items"})


if __name__ == "__main__":
    command, tag = sys.argv[1], sys.argv[2]
    {"read-options": read_options, "fact-sheet": fact_sheet, "score": score}[command](tag)
