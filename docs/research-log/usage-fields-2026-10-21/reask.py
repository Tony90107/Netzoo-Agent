"""ROUND-14 re-ask: every recorded condition-check and second-opinion call, asked again of the check's model twice --
arm A with the text these calls read before ROUND-14, arm C with the contract's usage lines added (`expects` for the
condition check, near misses for the second opinion) -- then every reading decided by B2 with each arm's answers in
place of the recorded ones, scored against the gold calls. Same system prompts, schemas and parsing as the live calls.

Usage:
  python3 reask.py ask OUT.json [--limit N]    ask both arms (model calls; announce first)
  python3 reask.py score ASKED.json OUT.json   B2 with the recorded answers, arm A's and arm C's
"""
from __future__ import annotations

import copy
import json
import os
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
sys.path.insert(0, str(LOGS / "stability-round13-2026-10-21"))
import harness  # noqa: E402  (sets the import paths)

replay_full = harness.replay_full
PRICE = {"input": 0.15e-6, "output": 0.60e-6}  # gpt-4o-mini per token


def _env():
    for line in (replay_full.units.MAIN / ".env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            name, value = line.split("=", 1)
            os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


def _quotes_before(found: list[dict], index: int) -> list[str]:
    quotes = []
    for event in found[:index]:
        if event.get("event_type") in ("routing.capability_checked", "routing.capability_reread"):
            quotes = [row.get("quote") for row in (event["payload"].get("check") or {}).get("requirements", [])] or quotes
    return quotes


def expects_text(action: str) -> str:
    """Arm C's addition to the condition check: the workflow's `expects` lines."""
    from netzoo_agent_core.interpretation.expects import expectations
    found = expectations(action)
    return f" It expects: {' '.join(item.state for item in found)}" if found else ""


def not_given_text(action: str) -> str:
    """Arm C's addition to the second opinion: the workflow's near misses."""
    from netzoo_agent_core.capability_sheet import sheet_entries
    asked = [entry.text.rstrip(".") for entry in sheet_entries().values()
             if entry.kind == "near_miss" and entry.action == action]
    return f" It does not give: {'; '.join(asked)}." if asked else ""


def jobs():
    """One job per (reading, recorded call, arm): what that call is shown."""
    from netzoo_agent_core.capability_sheet import entry
    from netzoo_agent_core.interpretation.capability_check import workflow_description

    by_session, core = harness._gold()
    for key, folder, sid, task, payload, reread, found, _n in harness.readings():
        gold = harness._label(sid, by_session, core)
        condition_quotes = replay_full._row_quotes(found)
        for at, event in enumerate(found):
            kind, raw = event.get("event_type"), event.get("payload") or {}
            if kind == "routing.capability_condition_check":
                for part, pairs, redirect in (("check", (raw.get("pairs") or []) + (raw.get("own_sentence") or []), False),
                                              ("redirect", raw.get("redirect") or [], True)):
                    if not pairs or any(index >= len(condition_quotes) for index, *_ in pairs):
                        continue
                    for arm in ("A", "C"):
                        shown = [(condition_quotes[index], stated, entry(keys[0]).workflow,
                                  workflow_description(keys) + (expects_text(action) if arm == "C" else ""))
                                 for index, action, keys, stated in pairs]
                        yield {"key": key, "at": at, "call": f"condition-{part}", "arm": arm, "gold": gold,
                               "session": sid, "shown": shown, "redirect": redirect}
            if kind == "routing.capability_second_opinion" and raw.get("pairs"):
                quotes = _quotes_before(found, at)
                if any(index >= len(quotes) for index, *_ in raw["pairs"]):
                    continue
                for arm in ("A", "C"):
                    shown = [(quotes[index], entry(keys[0]).workflow,
                              " ".join(entry(k).text for k in keys) + (not_given_text(action) if arm == "C" else ""))
                             for index, action, keys in raw["pairs"]]
                    yield {"key": key, "at": at, "call": "second-opinion", "arm": arm, "gold": gold, "session": sid,
                           "shown": shown, "situation": [task]}


def ask_one(llm, job: dict) -> dict:
    from netzoo_agent_core.contracts import HumanMessage, SystemMessage
    from netzoo_agent_core.contracts.capability_check import condition_check_model, second_opinion_model
    from netzoo_agent_core.graph import capability_check_call as calls
    from netzoo_agent_core.interpretation.semantic_repair import semantic_payload

    pairs = job["shown"]
    if job["call"].startswith("condition"):
        schema = condition_check_model(len(pairs))
        listed = "\n".join(f'{i}. Asked result: "{asked}" | Stated requirement: "{stated}" | {workflow} produces: '
                           f"{produced}" for i, (asked, stated, workflow, produced) in enumerate(pairs, 1))
        system = calls._CONDITION_REDIRECT if job["redirect"] else calls._CONDITION_CHECK
        shown = listed
    else:
        schema = second_opinion_model(len(pairs))
        listed = "\n".join(f'{i}. Request words: "{quote}" | {workflow} produces: {result}'
                           for i, (quote, workflow, result) in enumerate(pairs, 1))
        system, shown = calls._SECOND_OPINION, f"The user has: {'; '.join(job['situation'])}.\n{listed}"
    messages = [SystemMessage(content=system), HumanMessage(content=shown)]
    started = time.time()
    try:
        adapter = llm.with_structured_output(schema, method="function_calling", include_raw=True, strict=True)
        payload, raw = semantic_payload(adapter.invoke(messages))
        if hasattr(payload, "model_dump"):
            payload = payload.model_dump()
        parsed = schema.model_validate(payload)
        answers = [getattr(parsed, f"a{index}") for index in range(1, len(pairs) + 1)]
        usage = getattr(raw, "usage_metadata", None) or {}
        return {**job, "answers": answers, "seconds": round(time.time() - started, 1),
                "tokens": [usage.get("input_tokens", 0), usage.get("output_tokens", 0)]}
    except Exception as error:  # noqa: BLE001 -- a failed call is recorded, as live records it
        return {**job, "answers": None, "error": f"{type(error).__name__}: {error}"[:300]}


def ask(out: str, limit: int | None):
    _env()
    from netzoo_agent_core.graph.capability_check_call import _own_llm

    model = os.environ["OPENROUTER_CAPABILITY_MODEL"]
    llm = _own_llm(model, int(os.environ.get("OPENROUTER_CAPABILITY_MAX_TOKENS", "16000")))
    todo = list(jobs())[: limit or None]
    print(f"model {model}; {len(todo)} calls")
    with ThreadPoolExecutor(6) as pool:
        done = list(pool.map(lambda job: ask_one(llm, job), todo))
    tokens = [sum(row.get("tokens", [0, 0])[i] for row in done) for i in (0, 1)]
    cost = tokens[0] * PRICE["input"] + tokens[1] * PRICE["output"]
    Path(out).write_text(json.dumps({"model": model, "tokens": tokens, "usd": round(cost, 4), "calls": done},
                                    indent=1, ensure_ascii=False))
    print(f"done: {sum(r['answers'] is not None for r in done)}/{len(done)} answered; tokens {tokens}; US${cost:.4f}")


def _with_answers(found: list[dict], calls: list[dict]) -> list[dict]:
    found = copy.deepcopy(found)
    for call in calls:
        payload = found[call["at"]]["payload"]
        answers = call["answers"]
        if call["call"] == "condition-check":
            size = len(payload.get("pairs") or [])
            payload["answers"] = None if answers is None else answers[:size]
            payload["own_answers"] = None if answers is None else answers[size:]
        elif call["call"] == "condition-redirect":
            payload["redirected"] = answers
        else:
            payload["answers"] = answers
    return found


def score(asked_path: str, out: str):
    asked = json.loads(Path(asked_path).read_text())["calls"]
    by_key = {}
    for call in asked:
        by_key.setdefault(call["key"], []).append(call)
    rows = []
    for key, folder, sid, task, payload, reread, found, _n in harness.readings():
        if key not in by_key:
            continue
        row = {"session": sid, "gold": by_key[key][0]["gold"], "calls": {}}
        for arm in ("recorded", "A", "C"):
            events = found if arm == "recorded" else _with_answers(found, [c for c in by_key[key] if c["arm"] == arm])
            try:
                call = replay_full.replay(folder, task, payload, reread, events)
            except Exception as error:  # noqa: BLE001 -- the three 10-20 T01 readings of a withdrawn shape (harness)
                call = {"kind": "error", "basis": f"{type(error).__name__}"}
            row["calls"][arm] = {"kind": call["kind"], "basis": call.get("basis"), "partial": call.get("partial")}
        row["answers"] = {arm: [c["answers"] for c in by_key[key] if c["arm"] == arm] for arm in ("A", "C")}
        rows.append(row)
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    labelled = [r for r in rows if r["gold"]]
    right = {arm: sum(r["calls"][arm]["kind"] == r["gold"] for r in labelled) for arm in ("recorded", "A", "C")}
    print(f"{len(rows)} readings with a re-asked call, {len(labelled)} labelled; right {right}")
    for a, b in (("recorded", "A"), ("A", "C")):
        moved = Counter()
        for r in labelled:
            x, y = r["calls"][a]["kind"] == r["gold"], r["calls"][b]["kind"] == r["gold"]
            moved["wrong->right" if y and not x else "right->wrong" if x and not y else "same"] += 1
        print(f"{a} -> {b}: {dict(moved)}")
        for r in labelled:
            if r["calls"][a]["kind"] != r["calls"][b]["kind"]:
                print(f"   {r['session']} gold {r['gold']}: {a} {r['calls'][a]['kind']}/{r['calls'][a]['basis']} -> "
                      f"{b} {r['calls'][b]['kind']}/{r['calls'][b]['basis']}")
    changed = sum(a != c for r in rows for a, c in zip(r["answers"]["A"], r["answers"]["C"]))
    print(f"calls whose answers differ between A and C: {changed}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[0] == "ask":
        ask(args[1], int(args[args.index("--limit") + 1]) if "--limit" in args else None)
    else:
        score(args[1], args[2])
