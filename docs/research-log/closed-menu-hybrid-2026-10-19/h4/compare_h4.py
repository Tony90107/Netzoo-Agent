"""Hybrid blind round h4 (hybrid spec 2026-10-19, section 5; ROUND.md): the live main path, and the same sessions with
the contract veto layer applied offline -- so the two arms differ only by the veto, never by live run-to-run variance.

Arms:
- main: the live netzoo-agent main path (`.worktrees/netzoo-core-p0-run`, 54d08ce7 = main 122936cc code), tag h4main
  (`run_live.py`, `collect.py` -> live/h4main/structure.json);
- hybrid: each h4main call; where it is DO, the veto layer's reads (gpt-4o-mini) and code (`contract_veto`,
  `vetoed_core`) on the live call's own workflows (`veto TAG` -> live/TAG/veto.json).

Primary metrics (`score_core.outcome`, unchanged from h1-h3): false accepts (dont: false_accept, partly_accept), false
refusals (do: false_refusal), missed asks (ask, vague: committed_without_asking, refused_without_asking). Adoption
(frozen): hybrid false accepts < main's, false refusals <= main's, missed asks <= main's, strict score >= main's.

Also: strict score per class; the deciding fact asked (blind labeller, fact-sheet.json, arms hidden); each veto's
reason and quotes (blind labeller, veto-sheet.json); runnable but with a scientific meaning different from what the
user asked (blind labeller, meaning-sheet.json, arms hidden); how often the core-data question fires, by class (on a
do item it is a needless question); disclosures and run confirmations shown.

Usage: compare_h4.py veto TAG | fact-sheet TAG | veto-sheet TAG | meaning-sheet TAG | score TAG
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from plan import CLASSES, HERE, SEED, load_items, session_id, write_json
from score_core import outcome

LOGS = HERE.parents[1]
sys.path.insert(0, str(LOGS / "closed-menu-phase1-2026-10-18"))
import p1common  # noqa: E402 -- puts this branch's scripts/ on the path

ARMS = ("main", "hybrid")
LIVE = "h4main"
ERRORS = {"false_accept": ("false_accept", "partly_accept"), "false_refusal": ("false_refusal",),
          "missed_ask": ("committed_without_asking", "refused_without_asking")}


def _live() -> dict:
    return {row["item"]: row for row in json.loads((HERE / "live" / LIVE / "structure.json").read_text()).values()}


def _reply(item_id: str) -> str:
    path = HERE / "live" / LIVE / session_id(LIVE, item_id, 1) / "t1" / "stdout.txt"
    return path.read_text(errors="replace").strip() if path.exists() else ""


def _veto_one(item: dict, core: dict, llm) -> dict:
    from netzoo_agent_core.contracts.core_decision import CoreDecision
    from netzoo_agent_core.graph.contract_veto_call import veto_reads
    from netzoo_agent_core.interpretation.contract_veto import contract_veto, veto_notes, vetoed_core
    from netzoo_agent_core.interpretation.semantic_repair import semantic_payload
    usages = []

    def call(role, messages, schema):
        try:
            adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
            payload, raw = semantic_payload(adapter.invoke(messages))
            usages.append(p1common.usage(raw))
            data = payload.model_dump(mode="json") if hasattr(payload, "model_dump") else dict(payload)
            schema.model_validate(data)
            return data
        except Exception as error:  # noqa: BLE001 -- a failed read leaves the live call (as on the live path)
            usages.append({"input_tokens": 0, "output_tokens": 0, "usd": 0.0, "error": str(error)[:300]})
            return None

    live = CoreDecision.model_validate(core)
    read = veto_reads(item["prompt"], live.workflows, call)
    row = {"id": item["id"], "class": item["class"], "core_before": core, "calls": len(usages),
           "usd": round(sum(u["usd"] for u in usages), 6), "errors": [u["error"] for u in usages if u.get("error")]}
    if read is None:
        return {**row, "status": "read_failed", "core_after": core}
    slim, pairs, payload = read
    verdict = contract_veto(slim, live.workflows, item["prompt"], payload, pairs)
    after = vetoed_core(live, verdict)
    return {**row, "status": "checked", "core_after": after.model_dump(mode="json"), "notes": veto_notes(after),
            "vetoes": [{"workflow": v.workflow, "kind": v.kind, "reason": v.reason, "user": v.user_quote,
                        "contract": v.contract_quote, "source": v.source}
                       for w in verdict.vetoed for v in verdict.violations[w]],
            "questions": [{"workflow": q.workflow, "dimension": q.dimension, "values": list(q.values),
                           "quote": q.quote} for q in verdict.questions],
            "unverified": verdict.unverified, "unconfirmed": verdict.unconfirmed,
            "disclosures": verdict.disclosures, "to_confirm": verdict.to_confirm, "nearest": verdict.nearest,
            "slim": slim.model_dump(mode="json", exclude_defaults=True)}


def veto(tag: str) -> None:
    out = HERE / "live" / tag / "veto.json"
    if out.exists():
        raise ValueError("veto.json exists; the veto is applied once")
    out.parent.mkdir(parents=True, exist_ok=True)
    items, live = load_items(), _live()
    jobs = [(items[key], row["core"]) for key, row in sorted(live.items()) if (row.get("core") or {}).get("kind") == "DO"]
    llm = p1common.build_reader_llm()
    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = list(pool.map(lambda job: _veto_one(*job, llm), jobs))
    write_json(out, {"commit": p1common.git_head(), "rows": rows})
    print(f"{len(rows)} DO sessions, {sum(r['calls'] for r in rows)} calls, US${sum(r['usd'] for r in rows):.4f}, "
          f"read failed {sum(r['status'] != 'checked' for r in rows)}")


def _vetoed(tag: str) -> dict:
    return {row["id"]: row for row in json.loads((HERE / "live" / tag / "veto.json").read_text())["rows"]}


def arm_call(arm: str, item_id: str, live: dict, vetoed: dict) -> dict:
    core = live[item_id].get("core") or {"kind": "NONE", "workflows": []}
    if arm == "hybrid" and item_id in vetoed:
        core = vetoed[item_id]["core_after"]
    texts = [f"{'States that the input check settles' if f.get('settled_by_input_check') else 'Asks'}: "
             f"{f.get('question', '')}" for f in core.get("facts") or []]
    if not texts and live[item_id].get("clarification_question") and core is live[item_id].get("core"):
        texts.append(f"Asks: {live[item_id]['clarification_question']}")
    return {"core": core, "questions": texts}


def fact_sheet(tag: str) -> None:
    items, live, vetoed = load_items(), _live(), _vetoed(tag)
    rng = random.Random(SEED + 4)
    entries, key, seen = {}, {}, {}
    for item_id in sorted(items):
        if items[item_id]["class"] != "ask":
            continue
        for arm in ARMS:
            call = arm_call(arm, item_id, live, vetoed)
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


def veto_sheet(tag: str) -> None:
    """Every veto, without the item's class: is the reason right -- does the request say it, and do the contract's
    words rule the workflow out for it?"""
    from netzoo_agent_core.interpretation.menu_reply import _reason
    items, vetoed = load_items(), _vetoed(tag)
    rng = random.Random(SEED + 5)
    entries, key = {}, {}
    for item_id, row in sorted(vetoed.items()):
        for n, v in enumerate(row.get("vetoes") or []):
            code = f"V{rng.randrange(100000, 999999)}"
            entries[code] = {"request": items[item_id]["prompt"], "workflow": v["workflow"],
                             "reason": _reason(v["reason"]), "user_words": v["user"],
                             "contract_words": v["contract"], "contract_source": v["source"]}
            key[code] = {"item": item_id, "n": n}
    order = list(entries)
    rng.shuffle(order)
    write_json(HERE / "live" / tag / "veto-sheet.json", {code: entries[code] for code in order})
    write_json(HERE / "live" / tag / "veto-key.json", key)
    print(f"{len(entries)} vetoes to label")


def meaning_sheet(tag: str) -> None:
    """Each arm's DO (not partial) on an item with interpretation-critical facts: what will run and what the user is
    told before it runs, arms hidden."""
    items, live, vetoed = load_items(), _live(), _vetoed(tag)
    rng = random.Random(SEED + 6)
    entries, key, seen = {}, {}, {}
    for item_id in sorted(items):
        facts = items[item_id].get("interpretation_facts") or []
        if not facts:
            continue
        for arm in ARMS:
            core = arm_call(arm, item_id, live, vetoed)["core"]
            if core.get("kind") != "DO" or core.get("partial"):
                continue
            told = _reply(item_id)
            if arm == "hybrid" and item_id in vetoed and vetoed[item_id].get("notes"):
                told = f"{told}\n\n{vetoed[item_id]['notes']}"
            text = json.dumps([item_id, core.get("workflows"), told])
            if text in seen:
                key[seen[text]]["arms"].append(arm)
                continue
            code = f"S{rng.randrange(100000, 999999)}"
            entries[code] = {"request": items[item_id]["prompt"], "interpretation_facts": facts,
                             "will_run": core.get("workflows"), "told_before_running": told[-4000:]}
            key[code] = {"item": item_id, "arms": [arm]}
            seen[text] = code
    order = list(entries)
    rng.shuffle(order)
    write_json(HERE / "live" / tag / "meaning-sheet.json", {code: entries[code] for code in order})
    write_json(HERE / "live" / tag / "meaning-key.json", key)
    print(f"{len(entries)} runs to label")


def _labels(tag: str, name: str) -> tuple[dict, dict]:
    labels = HERE / "live" / tag / f"{name}-labels.json"
    keys = HERE / "live" / tag / f"{name}-key.json"
    if not labels.exists():
        return {}, {}
    return json.loads(labels.read_text()), json.loads(keys.read_text())


def score(tag: str) -> None:
    items, live, vetoed = load_items(), _live(), _vetoed(tag)
    fact_labels, fact_key = _labels(tag, "fact")
    right_fact = {(v["item"], arm): fact_labels.get(code) is True for code, v in fact_key.items() for arm in v["arms"]}
    meaning_labels, meaning_key = _labels(tag, "meaning")
    different = {(v["item"], arm): meaning_labels.get(code) == "different_unflagged"
                 for code, v in meaning_key.items() for arm in v["arms"]}
    result = {}
    for arm in ARMS:
        strict, errors, fact, per_item = Counter(), {name: [] for name in ERRORS}, Counter(), {}
        for item_id, item in sorted(items.items()):
            core = arm_call(arm, item_id, live, vetoed)["core"]
            cls = item["class"]
            got, _cost = outcome(item, core, right_fact.get((item_id, arm)))
            strict[(cls, got == "correct")] += 1
            for name, bad in ERRORS.items():
                if got in bad:
                    errors[name].append(item_id)
            if cls == "ask":
                fact[right_fact.get((item_id, arm)) is True and core.get("kind") in ("ASK", "DO")] += 1
            per_item[item_id] = {"class": cls, "kind": core.get("kind"), "basis": core.get("basis"),
                                 "workflows": core.get("workflows"), "outcome": got}
        n_by = Counter(item["class"] for item in items.values())
        result[arm] = {
            **{name: [len(found), found] for name, found in errors.items()},
            "strict": {c: [strict[(c, True)], n_by[c]] for c in CLASSES},
            "strict_total": [sum(v for (c, ok), v in strict.items() if ok), len(items)],
            "deciding_fact_asked": [fact[True], n_by["ask"]],
            "meaning_different_unflagged": sorted(i for (i, a), bad in different.items() if a == arm and bad),
            "items": per_item}
    veto_labels, veto_key = _labels(tag, "veto")
    rows = list(vetoed.values())
    fired = {c: [r["id"] for r in rows if r.get("vetoes") and r["class"] == c] for c in CLASSES}
    core_data = {c: [r["id"] for r in rows if r["class"] == c and any(
        q["dimension"].startswith("data:") for q in r.get("questions") or [])] for c in CLASSES}
    result["veto"] = {
        "do_sessions": len(rows), "read_failed": [r["id"] for r in rows if r["status"] != "checked"],
        "vetoed_sessions_by_class": fired,
        "veto_labels": dict(Counter(veto_labels.values())) if veto_labels else "not labelled",
        "core_data_question_by_class": core_data,
        "core_data_needless_on_do": len(core_data["do"]),
        "questions_by_class": {c: [r["id"] for r in rows if r["class"] == c and r.get("questions")] for c in CLASSES},
        "disclosures_shown": sum(1 for r in rows if r.get("disclosures")),
        "confirmations_listed": sum(1 for r in rows if r.get("to_confirm")),
        "unverified": sum(len(r.get("unverified") or []) for r in rows),
        "cost_usd": round(sum(r["usd"] for r in rows), 4)}
    m, h = result["main"], result["hybrid"]
    result["adopt"] = {"false_accept": h["false_accept"][0] < m["false_accept"][0],
                       "false_refusal": h["false_refusal"][0] <= m["false_refusal"][0],
                       "missed_ask": h["missed_ask"][0] <= m["missed_ask"][0],
                       "strict": h["strict_total"][0] >= m["strict_total"][0]}
    result["adopt"]["all"] = all(result["adopt"].values())
    write_json(HERE / "live" / tag / "compare.json", result, exclusive=False)
    for arm in ARMS:
        print(arm, {k: v for k, v in result[arm].items() if k != "items"})
    print("veto", result["veto"])
    print("adopt", result["adopt"])


if __name__ == "__main__":
    command, tag = sys.argv[1], sys.argv[2]
    {"veto": veto, "fact-sheet": fact_sheet, "veto-sheet": veto_sheet, "meaning-sheet": meaning_sheet,
     "score": score}[command](tag)
