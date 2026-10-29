"""jev-first-fields phase B (ROUND.md): Jev's five typed fields for every recorded first-turn ask, the arms H, HB and
the five one-field ablations rebuilt with the pure-code check, scored as phase A.

Usage: python3 shadow_b.py read | score
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
A = HERE.parent / "jev-first-links-2026-10-29"
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
sys.path.insert(0, str(A))
sys.path.insert(0, str(HERE))

import shadow as phase_a  # noqa: E402
from jev_field_questions import GROUPING, QUESTIONS, VALUES  # noqa: E402

CACHE = HERE / "jev-cache.json"
CAP_USD = 0.30
THRESHOLD = 0.7
FIELDS = tuple(QUESTIONS)
_LOCK = threading.Lock()


def _state(task: str, quote: str) -> str:
    return f"User request:\n{task}\n\nThe quoted part that asks for the result:\n{quote}"


def _key(task: str, quote: str) -> str:
    return hashlib.sha256(_state(task, quote).encode()).hexdigest()[:20]


def _cache() -> dict:
    return json.loads(CACHE.read_text()) if CACHE.exists() else {}


def read():
    from netzoo_agent_core.jev_client import decide

    golds = phase_a.gold()
    todo = {}
    for _folder, item, proposal in phase_a.readings(golds):
        task = golds[item]["prompt"]
        for _name, _index, ask in phase_a.asks(proposal):
            todo[_key(task, ask["quote"])] = (task, ask["quote"])
    cache = _cache()
    spent = [sum(found.get("cost", 0) for found in cache.values())]
    pending = [(key, value) for key, value in todo.items() if key not in cache]
    print(f"asks {len(todo)}, to read {len(pending)}, spent US${spent[0]:.4f}")
    questions = {name: {"type": "choice", **spec} for name, spec in QUESTIONS.items()}

    def one(job):
        key, (task, quote) = job
        with _LOCK:
            if spent[0] > CAP_USD:
                return
        try:
            out = decide(_state(task, quote), questions, timeout=40)
            found = {name: {"choice": answer["choice"], "confidence": answer["confidence"],
                            "probabilities": answer.get("probabilities") or {}}
                     for name, answer in out["answers"].items()}
            found |= {"model": out.get("model"), "cost": (out.get("usage") or {}).get("cost", 0)}
        except Exception as error:  # noqa: BLE001 -- recorded; the ask keeps mini's fields
            found = {"error": f"{type(error).__name__}: {error}"[:200], "cost": 0}
        with _LOCK:
            cache[key] = found
            spent[0] += found["cost"] or 0
            CACHE.write_text(json.dumps(cache, indent=1))

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(one, pending))
    print(f"done; cached {len(cache)}, spent US${spent[0]:.4f}, errors {sum('error' in v for v in cache.values())}")


def _with_fields(ask: dict, read: dict | None, fields) -> dict:
    if not read or "error" in read:
        return ask
    for name in fields:
        answer = read.get(name)
        if not answer or answer["confidence"] < THRESHOLD or answer["choice"] not in VALUES[name]:
            continue
        if name == "group_membership" and ask.get("group_membership") not in GROUPING:
            continue
        ask[name] = copy.deepcopy(VALUES[name][answer["choice"]])
    return ask


def score():
    golds, (_options, ids) = phase_a.gold(), phase_a.menu()
    links, fields = phase_a._cache(), _cache()
    arms = {"H": (), "HB": FIELDS, **{f"H+{name}": (name,) for name in FIELDS}}
    rows = []
    for folder, item, proposal in phase_a.readings(golds):
        task, want = golds[item]["prompt"], golds[item]
        base = copy.deepcopy(proposal)
        for name, index, ask in phase_a.asks(proposal):
            found = links.get(phase_a._key(task, ask["quote"]))
            if found and "error" not in found and found["confidence"] >= THRESHOLD:
                base[name]["asks"][index]["delivered_by"] = [ids[found["choice"]]] if found["choice"] in ids else []
        credited = {}
        for arm, chosen in arms.items():
            built = copy.deepcopy(base)
            for name, index, ask in phase_a.asks(proposal):
                _with_fields(built[name]["asks"][index], fields.get(_key(task, ask["quote"])), chosen)
            credited[arm] = phase_a._credited(task, built)
        if any(value is None for value in credited.values()):
            rows.append({"where": str(folder), "excluded": True})
            continue
        rows.append({"where": str(folder.relative_to(phase_a.LOGS)), "item": list(item), "gold": want["expected_call"],
                     "workflows": want["workflows"], "also": want.get("also_acceptable") or [], "credited": credited})
    (HERE / "shadow_b.json").write_text(json.dumps(rows, indent=1))
    report(rows, list(arms))


def report(rows, arms):
    right = lambda row, arm: bool(row["credited"][arm]) and set(row["credited"][arm]) <= (  # noqa: E731
        set(row["workflows"]) | set(row["also"]))
    kept = [row for row in rows if not row.get("excluded")]
    do = [row for row in kept if row["gold"] == "DO"]
    decline = [row for row in kept if row["gold"] == "DECLINE"]
    lines = [f"readings {len(rows)}, excluded {len(rows) - len(kept)}; gold DO {len(do)}, gold DECLINE {len(decline)}"]
    for arm in arms:
        up = sum(right(row, arm) and not right(row, "H") for row in do)
        down = sum(right(row, "H") and not right(row, arm) for row in do)
        accepts = sum(bool(row["credited"][arm]) for row in decline)
        new = sum(bool(row["credited"][arm]) and not row["credited"]["H"] for row in decline)
        lines.append(f"  {arm:20s} DO right {sum(right(row, arm) for row in do):3d} (vs H +{up} / -{down}); "
                     f"DECLINE false accepts {accepts} (new vs H {new})")
    text = "\n".join(lines)
    (HERE / "SCORE.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    {"read": read, "score": score}[sys.argv[1]]()
