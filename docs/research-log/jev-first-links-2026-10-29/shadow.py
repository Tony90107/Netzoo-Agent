"""jev-first-links phase A (ROUND.md): Jev's link for every recorded first-turn ask of the gold j/h sets, and the three
arms (M mini, J Jev, H hybrid) rebuilt with this checkout's pure-code capability check and scored.

Usage: python3 shadow.py read     (Jev calls, cached in jev-cache.json; stops at the cost cap)
       python3 shadow.py score    (no calls: rebuild the arms from the cache, write shadow.json and SCORE.txt)
"""
from __future__ import annotations

import copy
import glob
import hashlib
import json
import re
import sys
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
sys.path.insert(0, str(HERE))

from jev_link_menu import INSTRUCTIONS, menu, state  # noqa: E402

CACHE = HERE / "jev-cache.json"
CAP_USD = 0.30
THRESHOLD = 0.7
SESSION = re.compile(r"^hb-(?P<tag>[a-z]\d+)[a-z0-9]*-(?P<item>[A-Z]\d+)-(?P<rep>\d+)$")
_LOCK = threading.Lock()


def gold() -> dict:
    found = {}
    for path in glob.glob(str(LOGS / "**" / "items.json"), recursive=True):
        try:
            single = json.loads(Path(path).read_text()).get("single")
        except (ValueError, AttributeError):
            continue
        if not isinstance(single, list) or not single or not isinstance(single[0], dict):
            continue
        name = Path(path).parent.name
        for item in single:
            if "expected_call" in item and "workflows" in item and re.fullmatch(r"[jh]\d", name):
                found[(name, item["id"])] = item
    return found


def readings(golds: dict):
    for path in sorted(glob.glob(str(LOGS / "**" / "t1" / "*.jsonl"), recursive=True)):
        if not (Path(path).name.startswith("trace-") or Path(path).name == "events.jsonl"):
            continue
        folder = Path(path).parent
        match = SESSION.match(folder.parent.name)
        if not match or (match["tag"], match["item"]) not in golds:
            continue
        for line in open(path):
            event = json.loads(line)
            if event.get("event_type") == "routing.capability_checked" and event["payload"].get("proposal"):
                yield folder, (match["tag"], match["item"]), event["payload"]["proposal"]
                break


def asks(proposal: dict):
    for name, sentence in proposal.items():
        if re.fullmatch(r"s\d+", name) and isinstance(sentence, dict):
            for index, ask in enumerate(sentence.get("asks") or []):
                yield name, index, ask


def _key(task: str, quote: str) -> str:
    return hashlib.sha256(state(task, quote).encode()).hexdigest()[:20]


def _cache() -> dict:
    return json.loads(CACHE.read_text()) if CACHE.exists() else {}


def read():
    from netzoo_agent_core.jev_client import decide

    golds, (options, _ids) = gold(), menu()
    todo = {}
    for _folder, item, proposal in readings(golds):
        task = golds[item]["prompt"]
        for _name, _index, ask in asks(proposal):
            todo[_key(task, ask["quote"])] = (task, ask["quote"])
    cache = _cache()
    spent = [sum(found.get("cost", 0) for found in cache.values())]
    pending = [(key, value) for key, value in todo.items() if key not in cache]
    print(f"asks {len(todo)}, cached {len(todo) - len(pending)}, to read {len(pending)}, spent US${spent[0]:.4f}")

    def one(job):
        key, (task, quote) = job
        with _LOCK:
            if spent[0] > CAP_USD:
                return
        try:
            out = decide(state(task, quote), {"link": {"type": "choice", "instructions": INSTRUCTIONS,
                                                       "criteria": options}}, timeout=30)
            answer = out["answers"]["link"]
            found = {"choice": answer["choice"], "confidence": answer["confidence"],
                     "probabilities": answer.get("probabilities") or {}, "model": out.get("model"),
                     "cost": (out.get("usage") or {}).get("cost", 0)}
        except Exception as error:  # noqa: BLE001 -- recorded; the ask keeps mini's link in every arm
            found = {"error": f"{type(error).__name__}: {error}"[:200], "cost": 0}
        with _LOCK:
            cache[key] = found
            spent[0] += found["cost"] or 0
            CACHE.write_text(json.dumps(cache, indent=1))

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(one, pending))
    print(f"done; cached {len(cache)}, spent US${spent[0]:.4f}, errors {sum('error' in v for v in cache.values())}")


def _credited(task: str, proposal: dict) -> list[str] | None:
    from netzoo_agent_core.capability_sheet import entry
    from netzoo_agent_core.contracts.capability_check import proposal_model
    from netzoo_agent_core.interpretation.capability_check import build_capability_check

    count = sum(1 for name in proposal if re.fullmatch(r"s\d+", name))
    try:
        check, _ = build_capability_check(task, proposal_model(count).model_validate(proposal))
    except Exception:  # noqa: BLE001 -- an old reading today's schema cannot take: excluded from every arm
        return None
    return sorted({entry(key).workflow for row in check.results()
                   if row.status in ("available", "with_step", "partial") for key in row.delivered_by})


def score():
    golds, (_options, ids) = gold(), menu()
    cache = _cache()
    rows = []
    for folder, item, proposal in readings(golds):
        task, want = golds[item]["prompt"], golds[item]
        arms, picks = {"M": proposal, "J": copy.deepcopy(proposal), "H": copy.deepcopy(proposal)}, []
        for name, index, ask in asks(proposal):
            found = cache.get(_key(task, ask["quote"]))
            if not found or "error" in found:
                picks.append(None)
                continue
            pick = [ids[found["choice"]]] if found["choice"] in ids else []
            picks.append({"quote": ask["quote"], "mini": ask.get("delivered_by"), "jev": pick,
                          "confidence": found["confidence"]})
            arms["J"][name]["asks"][index]["delivered_by"] = pick
            if found["confidence"] >= THRESHOLD:
                arms["H"][name]["asks"][index]["delivered_by"] = pick
        credited = {arm: _credited(task, value) for arm, value in arms.items()}
        if any(value is None for value in credited.values()):
            rows.append({"where": str(folder), "item": item, "excluded": True})
            continue
        rows.append({"where": str(folder.relative_to(LOGS)), "item": list(item), "gold": want["expected_call"],
                     "workflows": want["workflows"], "also": want.get("also_acceptable") or [],
                     "credited": credited, "picks": picks})
    (HERE / "shadow.json").write_text(json.dumps(rows, indent=1))
    report(rows)


def _right(row, arm) -> bool:
    found = row["credited"][arm]
    return bool(found) and set(found) <= set(row["workflows"]) | set(row["also"])


def report(rows):
    lines, kept = [], [row for row in rows if not row.get("excluded")]
    lines.append(f"readings {len(rows)}, excluded (schema) {len(rows) - len(kept)}, items "
                 f"{len({tuple(row['item']) for row in kept})}")
    do = [row for row in kept if row["gold"] == "DO"]
    lines.append(f"gold DO readings {len(do)}")
    for arm in "MJH":
        right = sum(_right(row, arm) for row in do)
        up = sum(_right(row, arm) and not _right(row, "M") for row in do)
        down = sum(_right(row, "M") and not _right(row, arm) for row in do)
        lines.append(f"  {arm}: right {right}  (vs M: wrong->right {up}, right->wrong {down})")
    decline = [row for row in kept if row["gold"] == "DECLINE"]
    lines.append(f"gold DECLINE readings {len(decline)}")
    for arm in "MJH":
        lines.append(f"  {arm}: check-level false accepts {sum(bool(row['credited'][arm]) for row in decline)}")
    confident = [(pick, row) for row in do for pick in row["picks"] if pick and pick["confidence"] >= THRESHOLD]
    good = sum(bool(pick["jev"]) and set(_workflows(pick["jev"])) <= set(row["workflows"]) | set(row["also"])
               for pick, row in confident)
    lines.append(f"A3: Jev picks with confidence >= {THRESHOLD} on gold-DO asks: {good}/{len(confident)} name a gold "
                 f"workflow")
    other = Counter(row["gold"] for row in kept if row["gold"] not in ("DO", "DECLINE"))
    lines.append(f"other gold (reported only): {dict(other)}")
    text = "\n".join(lines)
    (HERE / "SCORE.txt").write_text(text + "\n")
    print(text)


def _workflows(keys):
    from netzoo_agent_core.capability_sheet import entry

    return [entry(key).workflow for key in keys]


if __name__ == "__main__":
    {"read": read, "score": score}[sys.argv[1]]()
