"""Slim reading blind round h3 (spec 2026-10-19, 6.2; ROUND.md): the live main path and the slim reading on the same
48 items, each once, scored the same way (no model calls except `read-slim`).

Arms:
- main: the live netzoo-agent main path (`.worktrees/netzoo-core-p0-run`, 54d08ce7 = main 122936cc code), tag h3main
  (`run_live.py`, `collect.py` -> live/h3main/structure.json);
- slim: this branch -- core read, the B fields step 2 chooses, the focused read, the requirement check, `decide_menu`
  (`read-slim`, reading calls only).

Primary metrics (the three scientific goals): false accepts (a dont item run, partly included), false refusals (a do
item refused, partly included), missed asks (an ask or vague item run or refused). Also: the strict score
(`score_core.outcome`), the deciding fact asked (ask items, blind labeller on fact-sheet.json, arms hidden), values
written per read and misfilled values (slim only; blind labeller on facts-to-label.json).
Adoption (frozen): slim's three error counts each <= main's, and slim's strict score >= main's.

Usage: compare_h3.py read-slim TAG | fact-sheet TAG | facts TAG | score TAG
"""
from __future__ import annotations

import json
import random
import statistics
import sys
from collections import Counter

from plan import CLASSES, HERE, SEED, load_items, write_json
from score_core import outcome

SLIM = HERE.parent
sys.path.insert(0, str(SLIM))
sys.path.insert(0, str(SLIM.parent / "closed-menu-phase1-2026-10-18"))
import p1common  # noqa: E402 -- puts this branch's scripts/ on the path

ARMS = ("main", "slim")
# The question labels the h1/h2 fact sheets used (closed-menu-phase1b-2026-10-18/heldout/compare.py), unchanged.
_DIMENSION = {"artifact": "which result they want", "artifact_group": "which kind of result they want",
              "granularity": "one result for all samples, one per group, or one per sample",
              "integration": "one joint network across layers or one per layer", "regulators": "which regulators",
              "layers": "which omics layers", "sample_count": "how many samples there are",
              "feature_count": "how many features there are", "file": "what the named file holds"}
LIVE = {"main": "h3main"}
ERRORS = {"false_accept": ("false_accept", "partly_accept"), "false_refusal": ("false_refusal",),
          "missed_ask": ("committed_without_asking", "refused_without_asking")}


def norm(names) -> list[str]:
    return [str(n).strip().upper().replace("LIONESS ", "LIONESS-") for n in names or []]


def read_slim(tag: str) -> None:
    import s2
    from netzoo_agent_core.interpretation.slim_reader import SLIM_SHAPE
    out = HERE / "live" / tag / "slim.json"
    if out.exists():
        raise ValueError("slim.json exists; the round is read once")
    out.parent.mkdir(parents=True, exist_ok=True)
    items = load_items()
    llm = p1common.build_reader_llm()
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(lambda key: s2.one(items[key], llm, keep_menu=True), sorted(items)))
    write_json(out, {"commit": p1common.git_head(), "shape": SLIM_SHAPE, "rows": rows})
    print(f"{len(rows)} items, {sum(r['calls'] for r in rows)} calls, US${sum(r['usd'] for r in rows):.4f}, "
          f"failed {sum(r['status'] == 'failed' for r in rows)}")


def _rows(tag: str) -> dict:
    found = {arm: {row["item"]: row for row in json.loads((HERE / "live" / live / "structure.json").read_text()).values()}
             for arm, live in LIVE.items()}
    found["slim"] = {row["id"]: row for row in json.loads((HERE / "live" / tag / "slim.json").read_text())["rows"]}
    return found


def _slim_decision(row: dict, prompt: str):
    from netzoo_agent_core.contracts.menu_reading import MenuReading
    from netzoo_agent_core.interpretation.menu_decision import decide_menu
    return decide_menu(MenuReading.model_validate(row["menu"]), prompt)


def arm_call(arm: str, row: dict, prompt: str) -> dict:
    """kind, workflows, partial, facts (settled by the input check) and the questions as text."""
    if arm in LIVE:
        core = row.get("core") or {"kind": "NONE", "workflows": []}
        texts = [f"{'States that the input check settles' if f.get('settled_by_input_check') else 'Asks'}: "
                 f"{f.get('question', '')}" for f in core.get("facts") or []]
        if not texts and row.get("clarification_question"):
            texts.append(f"Asks: {row['clarification_question']}")
        return {"core": core, "questions": texts}
    if row["status"] == "failed":
        return {"core": {"kind": "UNCHECKED", "workflows": []}, "questions": []}
    decision = _slim_decision(row, prompt)
    texts = []
    for question in decision.questions:
        name = question.dimension
        about = (f"the value of {name.split(':', 1)[1].replace('.', ' setting ')}" if name.startswith("setting:")
                 else "whether this requirement is a must" if name.startswith("requirement:")
                 else _DIMENSION.get(name, name.replace("_", " ")))
        texts.append(f"Asks {about}" + (f' (quoting "{question.quote}")' if question.quote else "") +
                     ". Options: " + " / ".join(label for _v, label in question.options))
    texts += [f"States that the input check will settle, before running: {q}" for q in decision.settled]
    core = {"kind": decision.kind, "workflows": decision.workflows, "partial": decision.partial,
            "facts": [{"settled_by_input_check": True}] if decision.settled else []}
    return {"core": core, "questions": texts}


def fact_sheet(tag: str) -> None:
    items, rows = load_items(), _rows(tag)
    rng = random.Random(SEED + 3)
    entries, key, seen = {}, {}, {}
    for item_id in sorted(items):
        if items[item_id]["class"] != "ask":
            continue
        for arm in ARMS:
            call = arm_call(arm, rows[arm][item_id], items[item_id]["prompt"])
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


def facts(tag: str) -> None:
    """The slim reading's written values, for the blind misfill labeller (as s2.py facts)."""
    import s2
    items = load_items()
    rows = json.loads((HERE / "live" / tag / "slim.json").read_text())["rows"]
    s2.ITEMS = [{"id": key, "prompt": item["prompt"]} for key, item in items.items()]
    tmp = SLIM / "live" / f"h3-{tag}"
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "dev.json").write_text(json.dumps({"rows": rows}), encoding="utf-8")
    s2.HERE = SLIM
    s2.facts(f"h3-{tag}")


def score(tag: str) -> None:
    items, rows = load_items(), _rows(tag)
    labels = json.loads((HERE / "live" / tag / "fact-labels.json").read_text())
    key = json.loads((HERE / "live" / tag / "fact-key.json").read_text())
    right_fact = {(v["item"], arm): labels[code] is True for code, v in key.items() for arm in v["arms"]}
    result = {}
    for arm in ARMS:
        strict, errors, fact, per_item = Counter(), {name: [] for name in ERRORS}, Counter(), {}
        for item_id, item in sorted(items.items()):
            call = arm_call(arm, rows[arm][item_id], item["prompt"])
            core, cls = call["core"], item["class"]
            got, _cost = outcome(item, core, right_fact.get((item_id, arm)))
            strict[(cls, got == "correct")] += 1
            for name, bad in ERRORS.items():
                if got in bad:
                    errors[name].append(item_id)
            if cls == "ask":
                fact[right_fact.get((item_id, arm)) is True and core.get("kind") in ("ASK", "DO")] += 1
            per_item[item_id] = {"class": cls, "kind": core.get("kind"), "workflows": norm(core.get("workflows")),
                                 "outcome": got, "questions": call["questions"]}
        n_by = Counter(item["class"] for item in items.values())
        result[arm] = {
            **{name: [len(found), found] for name, found in errors.items()},
            "strict": {c: [strict[(c, True)], n_by[c]] for c in CLASSES},
            "strict_total": [sum(v for (c, ok), v in strict.items() if ok), len(items)],
            "deciding_fact_asked": [fact[True], n_by["ask"]], "items": per_item}
    slim_rows = json.loads((HERE / "live" / tag / "slim.json").read_text())["rows"]
    written = [r["values"]["written"] for r in slim_rows if r["status"] == "read"]
    content = [r["values"]["content"] for r in slim_rows if r["status"] == "read"]
    result["slim"]["values_per_read"] = {"written_median": statistics.median(written), "written_max": max(written),
                                         "content_median": statistics.median(content)}
    misfill_path = SLIM / "live" / f"h3-{tag}" / "fact-labels.json"
    if misfill_path.exists():
        import s2
        result["slim"]["misfills"] = {k: v for k, v in s2.misfills(json.loads(misfill_path.read_text())).items()
                                      if k != "items"}
    m, s = result["main"], result["slim"]
    result["adopt"] = {name: s[name][0] <= m[name][0] for name in ERRORS}
    result["adopt"]["strict"] = s["strict_total"][0] >= m["strict_total"][0]
    result["adopt"]["all"] = all(result["adopt"].values())
    write_json(HERE / "live" / tag / "compare.json", result, exclusive=False)
    for arm in ARMS:
        print(arm, {k: v for k, v in result[arm].items() if k != "items"})
    print("adopt", result["adopt"])


if __name__ == "__main__":
    command, tag = sys.argv[1], sys.argv[2]
    {"read-slim": read_slim, "fact-sheet": fact_sheet, "facts": facts, "score": score}[command](tag)
