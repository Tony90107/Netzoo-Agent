"""D1/D2 (ROUND.md): the guard's existing data read and the new has-read for every j1-j8 gold item's opening prompt
(real Jev, cached here), and the guard's `ruled_out` for each gold workflow under each read and their union.

Usage: python3 measure.py read | score
"""
from __future__ import annotations

import glob
import hashlib
import json
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from netzoo_agent_core.graph.jev_guard_call import DATA_CRITERIA, DATA_INSTRUCTIONS, ruled_out  # noqa: E402
from netzoo_agent_core.interpretation.data_has import HAS_INSTRUCTIONS  # noqa: E402
from netzoo_agent_core.jev_client import decide  # noqa: E402

CACHE, CAP, LOCK = HERE / "jev-cache.json", 0.10, threading.Lock()
QUESTIONS = {"data": DATA_INSTRUCTIONS, "has": HAS_INSTRUCTIONS}


def items() -> list[tuple[str, dict]]:
    found = {}
    for path in sorted(glob.glob(str(LOGS / "**" / "items.json"), recursive=True)):
        name = Path(path).parent.name
        try:
            single = json.loads(Path(path).read_text()).get("single")
        except (ValueError, AttributeError):
            continue
        if re.fullmatch(r"j\d", name) and isinstance(single, list) and single and isinstance(single[0], dict):
            for item in single:
                if "expected_call" in item:
                    found[(name, item["id"])] = item
    return sorted(found.items())


def key(kind: str, prompt: str) -> str:
    return hashlib.sha256(f"{kind}\n{prompt}".encode()).hexdigest()[:20]


def read():
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    jobs = [(kind, item["prompt"]) for _k, item in items() for kind in QUESTIONS]
    jobs = [job for job in dict.fromkeys(jobs) if key(*job) not in cache]
    spent = [sum(v.get("cost", 0) for v in cache.values())]
    print(f"to read {len(jobs)}, spent US${spent[0]:.4f}")

    def one(job):
        kind, prompt = job
        if spent[0] > CAP:
            return
        try:
            out = decide(f"User request:\n{prompt}", {kind: {"type": "choice", "instructions": QUESTIONS[kind],
                                                             "criteria": DATA_CRITERIA}}, timeout=30)
            answer = out["answers"][kind]
            found = {"choice": answer["choice"], "confidence": answer["confidence"],
                     "cost": (out.get("usage") or {}).get("cost", 0)}
        except Exception as error:  # noqa: BLE001 -- recorded
            found = {"error": f"{type(error).__name__}: {error}"[:200], "cost": 0}
        with LOCK:
            cache[key(*job)] = found
            spent[0] += found["cost"]
            CACHE.write_text(json.dumps(cache, indent=1))

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(one, jobs))
    print(f"done, spent US${spent[0]:.4f}, errors {sum('error' in v for v in cache.values())}")


def score():
    cache = json.loads(CACHE.read_text())
    rows, lines = [], []
    for (name, item_id), item in items():
        reads = {kind: cache.get(key(kind, item["prompt"]), {}) for kind in QUESTIONS}
        if any("error" in r or not r for r in reads.values()):
            continue
        out = {}
        for kind, r in reads.items():
            out[kind] = {w: ruled_out(w, (r["choice"], r["confidence"]), None) for w in item.get("workflows") or []}
        union = {w: out["data"][w] or out["has"][w] for w in item.get("workflows") or []}
        rows.append({"set": name, "id": item_id, "gold": item["expected_call"], "category": item.get("category"),
                     "sub": item.get("sub"), "workflows": item.get("workflows"),
                     "data": [reads["data"]["choice"], reads["data"]["confidence"]],
                     "has": [reads["has"]["choice"], reads["has"]["confidence"]],
                     "ruled_data": out["data"], "ruled_has": out["has"], "ruled_union": union})
    (HERE / "measure.json").write_text(json.dumps(rows, indent=1))
    do = [r for r in rows if r["gold"] in ("DO", "PARTIAL")]
    hit = lambda r, k: any(r[k].values())  # noqa: E731
    lines.append(f"items {len(rows)}; gold DO/PARTIAL {len(do)}")
    lines.append(f"D1 gold-DO items with a gold workflow ruled out: existing {sum(hit(r, 'ruled_data') for r in do)}, "
                 f"new {sum(hit(r, 'ruled_has') for r in do)}, union {sum(hit(r, 'ruled_union') for r in do)}")
    for r in do:
        if hit(r, "ruled_union"):
            lines.append(f"   DO ruled out: {r['set']} {r['id']} {r['category']} data {r['data']} has {r['has']} "
                         f"{ {w: v for w, v in r['ruled_union'].items() if v} }")
    dtype = [r for r in rows if r["gold"] == "DECLINE" and (r["sub"] in ("incompatible", "not_accepted")
                                                            or r["category"] == "N")]
    lines.append(f"D2 gold-DECLINE data-type items {len(dtype)}: existing {sum(hit(r, 'ruled_data') for r in dtype)}, "
                 f"union {sum(hit(r, 'ruled_union') for r in dtype)}")
    q18 = next((r for r in rows if r["set"] == "j2" and r["id"] == "Q18"), None)
    lines.append(f"D2 j2 Q18: data {q18['data']} has {q18['has']} ruled_has {q18['ruled_has']}")
    for r in dtype:
        lines.append(f"   {r['set']} {r['id']} {r['sub']}: data {r['data']} has {r['has']} existing "
                     f"{hit(r, 'ruled_data')} union {hit(r, 'ruled_union')}")
    text = "\n".join(lines)
    (HERE / "SCORE.txt").write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    {"read": read, "score": score}[sys.argv[1]]()
