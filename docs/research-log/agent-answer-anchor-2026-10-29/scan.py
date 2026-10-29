"""Population (ROUND.md): every recorded answer turn after an ASK whose asked fact-agent or Jev-agent questions carry a
contract quote (R01's scan, widened from basis fact_agent to jev_agent too). One row per (session, answer turn); a
session copied under several logs is kept once. Labels: R01's own labels (`jev-agent-answers-2026-10-28/population.json`)
where it labelled the row, else from the item file when the reply sent is the item's own scripted reply.

Usage: python3 scan.py   (writes population.json; no model calls)
"""
from __future__ import annotations

import glob
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent
R01 = {(r["session"], r["turn"]): r["label"]
       for r in json.loads((LOGS / "jev-agent-answers-2026-10-28" / "population.json").read_text())}
SESSION = re.compile(r"^hb-(?P<tag>[a-z]\d+)[a-z0-9]*-(?P<item>[A-Z]\d+)-\d+$")


def events(folder: Path, kind: str):
    for name in ("events.jsonl", "trace-*.jsonl"):
        for trace in sorted(folder.glob(name)):
            for line in open(trace, errors="replace"):
                if f'"{kind}"' in line:
                    event = json.loads(line)
                    if event.get("event_type") == kind:
                        yield event["payload"]


def items() -> dict:
    found = {}
    for path in glob.glob(str(LOGS / "**" / "items.json"), recursive=True):
        try:
            single = json.loads(Path(path).read_text()).get("single")
        except (ValueError, AttributeError):
            continue
        if isinstance(single, list) and single and isinstance(single[0], dict) and re.fullmatch(r"[jh]\d",
                                                                                                  Path(path).parent.name):
            found.update({(Path(path).parent.name, item["id"]): item for item in single})
    return found


def label(session: str, reply: str, golds: dict) -> str | None:
    match = SESSION.match(session)
    item = golds.get((match["tag"], match["item"])) if match else None
    if item is None:
        return None
    if reply == item.get("reply_fact") and item.get("final_after_fact"):
        return "fails" if item["final_after_fact"]["call"] == "DECLINE" else "meets"
    if reply in (item.get("reply_restate"), item.get("reply_form"), item.get("reply_confirm")):
        return "meets" if item["expected_call"] in ("DO", "PARTIAL") else "not_do"
    return None


golds, rows, seen = items(), [], set()
for folder in sorted({p.parent for p in LOGS.rglob("session.json")}):
    if HERE in folder.parents or not (folder.name[:1] == "t" and folder.name[1:].isdigit()):
        continue
    after = folder.parent / f"t{int(folder.name[1:]) + 1}"
    if not (after / "session.json").exists():
        continue
    decision = next(events(folder, "core.decision"), {})
    if decision.get("kind") != "ASK" or decision.get("basis") not in ("fact_agent", "jev_agent"):
        continue
    asked = [f for f in decision.get("facts") or [] if f.get("contract_quote") and not f.get("depends_on")
             and not f.get("by_code")]
    if not asked or (folder.parent.name, after.name) in seen:
        continue
    seen.add((folder.parent.name, after.name))
    then = next(events(after, "core.decision"), {})
    users = [m["content"] for m in json.loads((after / "session.json").read_text())["messages"] if m["role"] == "user"]
    reply = users[-1].split("User follow-up:")[-1].strip() if users else ""
    rows.append({"session": folder.parent.name, "turn": after.name, "where": str(after.relative_to(LOGS)),
                 "basis": decision.get("basis"),
                 "asked": [{k: f.get(k) for k in ("question", "user_quote", "contract_quote", "workflows")}
                           for f in asked],
                 "reply": reply, "label": R01.get((folder.parent.name, after.name)) or label(folder.parent.name, reply,
                                                                                           golds),
                 "after": {"kind": then.get("kind"), "basis": then.get("basis"), "workflows": then.get("workflows")}})
(HERE / "population.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
do = [r for r in rows if r["after"]["kind"] == "DO"]
print(f"{len(rows)} answer turns; DO after {len(do)}; labels on DO turns:",
      {lab: sum(r["label"] == lab for r in do) for lab in sorted({str(r["label"]) for r in do})})
