"""ROUND-13 regression harness: ROUND-12's B2 replay (`replay_full.replay`) over every recorded reading in this
checkout's and the main tree's research logs, scored against the gold calls. No model calls.

A reading is the first `routing.capability_checked` (with a proposal) of a turn's events.jsonl; turns holding more
than one are replayed on their first and counted. The same session turn found in both trees is replayed once. Gold:
the h1-h4 strictness audit (by session id) and the core-judgment items (cj-<round>-<item>-<rep>), as every replay
since ROUND-09 labels them (count-scope-r09 `replay_core._gold`).

Usage:
  python3 harness.py run OUT.json [--scripts DIR]    B2 on every reading with this (or another) checkout's code
  python3 harness.py compare OLD.json NEW.json       every changed call beside its gold; right counts; stability
"""
from __future__ import annotations

import glob
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
sys.path.insert(0, str(LOGS / "false-accept-replay-2026-10-21"))
import replay_full  # noqa: E402  (sets the import paths; honours --scripts)

sys.path.insert(0, str(LOGS / "count-scope-r09-2026-10-20"))
ROOTS = [LOGS, replay_full.units.MAIN / "docs/research-log"]
SESSION = re.compile(r"^(?:cj-(?P<round>[^-]+)-(?P<item>C\d+)|hb-(?P<set>[^-]+)-(?P<hitem>[A-Z]\d+))-(?P<rep>\d+)$")


def _gold():
    from replay_core import _gold as gold
    by_session, core = gold()
    return by_session, core


def _label(session: str, by_session: dict, core: dict) -> str | None:
    if session in by_session:
        return by_session[session]
    found = SESSION.match(session)
    return core.get(found.group("item")) if found and found.group("item") else None


def _item(session: str) -> tuple[str, str] | None:
    """(set, item) a session reads -- a round of the 56 core items, or an h set's item."""
    found = SESSION.match(session)
    if not found:
        return None
    return ("core", found.group("item")) if found.group("item") else (found.group("set"), found.group("hitem"))


def readings():
    from replay import _fits
    seen = set()
    for root in ROOTS:
        for path in sorted(glob.glob(str(root / "**" / "events.jsonl"), recursive=True)):
            folder = Path(path).parent
            if not (folder / "session.json").exists():
                continue
            session = json.loads((folder / "session.json").read_text())
            found = [json.loads(line) for line in open(path) if line.strip()]
            checks = [i for i, e in enumerate(found)
                      if e.get("event_type") == "routing.capability_checked" and e["payload"].get("proposal")]
            if not checks:
                continue
            payload = found[checks[0]]["payload"]["proposal"]
            reread = None
            for later in found[checks[0] + 1:]:
                if later.get("event_type") == "routing.capability_checked":
                    break
                if later.get("event_type") == "routing.capability_reread":
                    reread = later["payload"]
                    break
            users = [m["content"] for m in session.get("messages", []) if m["role"] == "user"]
            task = next((t for t in reversed(users) if _fits(t, payload)), None)
            if task is None:
                continue
            sid = session.get("session_id", "")
            key = hashlib.sha256(json.dumps([sid, folder.name, task, payload], sort_keys=True).encode()).hexdigest()[:16]
            if key in seen:
                continue
            seen.add(key)
            yield key, folder, sid, task, payload, reread, found, len(checks)


def run(out: str):
    by_session, core = _gold()
    rows, counts = {}, Counter()
    for key, folder, sid, task, payload, reread, found, checks in readings():
        counts["readings"] += 1
        counts["turns with more than one reading"] += checks > 1
        recorded = next((e["payload"] for e in reversed(found) if e.get("event_type") == "core.decision"), {})
        try:
            call = replay_full.replay(folder, task, payload, reread, found)
        except Exception as error:  # noqa: BLE001 -- reported, never hidden
            call = {"kind": "error", "error": f"{type(error).__name__}: {error}"[:300]}
            counts["errors"] += 1
        rows[key] = {"session": sid, "turn": folder.name, "where": str(folder), "gold": _label(sid, by_session, core),
                     "recorded": recorded.get("kind"), "kind": call["kind"], "basis": call.get("basis"),
                     "partial": call.get("partial"), "unrecorded": call.get("unrecorded", {}),
                     "error": call.get("error")}
        counts["unrecorded"] += bool(sum(call.get("unrecorded", {}).values()))
    Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    labelled = [r for r in rows.values() if r["gold"]]
    print(f"{dict(counts)}; labelled {len(labelled)}, right {sum(r['kind'] == r['gold'] for r in labelled)}; "
          f"B2 = recorded {sum(r['kind'] == r['recorded'] for r in rows.values())}/{len(rows)}")


def stability(rows: dict) -> dict:
    """Per item read more than once (first turns only): every read right (pass^k), some right, none right."""
    by_item = defaultdict(list)
    for row in rows.values():
        if row["gold"] and row["turn"] == "t1" and (item := _item(row["session"])):
            by_item[item].append(row["kind"] == row["gold"])
    found = Counter()
    for reads in by_item.values():
        if len(reads) > 1:
            found["items"] += 1
            found["all right" if all(reads) else "none right" if not any(reads) else "mixed"] += 1
    return dict(found)


def compare(old_path: str, new_path: str):
    old, new = json.loads(Path(old_path).read_text()), json.loads(Path(new_path).read_text())
    shared = sorted(set(old) & set(new))
    changed = [k for k in shared if (old[k]["kind"], old[k]["partial"]) != (new[k]["kind"], new[k]["partial"])]
    labelled = [k for k in shared if new[k]["gold"]]
    right = (sum(old[k]["kind"] == old[k]["gold"] for k in labelled), sum(new[k]["kind"] == new[k]["gold"] for k in labelled))
    for k in changed:
        o, n = old[k], new[k]
        verdict = ("" if not n["gold"] else "FIX" if n["kind"] == n["gold"] != o["kind"]
                   else "BREAK" if o["kind"] == o["gold"] != n["kind"] else "other")
        print(f"{verdict:5} {n['session']}/{n['turn']} gold {n['gold']}: {o['kind']}{'(p)' if o['partial'] else ''}/"
              f"{o['basis']} -> {n['kind']}{'(p)' if n['partial'] else ''}/{n['basis']}")
    print(f"{len(changed)} of {len(shared)} calls changed; right on {len(labelled)} labelled: {right[0]} -> {right[1]}")
    print(f"stability (items read more than once, first turns): before {stability(old)}, after {stability(new)}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--scripts" and not (sys.argv.index(a) > 0
                                                              and sys.argv[sys.argv.index(a) - 1] == "--scripts")]
    {"run": lambda: run(args[1]), "compare": lambda: compare(args[1], args[2])}[args[0]]()
