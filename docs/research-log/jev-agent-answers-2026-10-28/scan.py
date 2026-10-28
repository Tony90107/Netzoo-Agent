"""Population scan (ROUND.md): every recorded conversation whose turn N was ASK `fact_agent` with accepted fact-agent
questions carrying a contract quote, and that has a turn N+1 (the answer turn). One row per (session, turn N+1);
copies of a session under several logs kept once.

Usage: python3 scan.py OUT.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE.parent


def events(folder: Path, kind: str):
    for name in ("events.jsonl", "trace-*.jsonl"):
        for trace in sorted(folder.glob(name)):
            for line in open(trace, errors="replace"):
                if f'"{kind}"' in line:
                    event = json.loads(line)
                    if event.get("event_type") == kind:
                        yield event["payload"]


rows, seen = [], set()
for folder in sorted({p.parent for p in LOGS.rglob("session.json")}):
    if HERE in folder.parents or not (folder.name[:1] == "t" and folder.name[1:].isdigit()):
        continue
    after = folder.parent / f"t{int(folder.name[1:]) + 1}"
    if not (after / "session.json").exists():
        continue
    decision = next(events(folder, "core.decision"), {})
    if decision.get("kind") != "ASK" or decision.get("basis") != "fact_agent":
        continue
    asked = [f for f in decision.get("facts") or [] if f.get("contract_quote") and not f.get("depends_on")
             and not f.get("by_code")]
    if not asked:
        continue
    key = (folder.parent.name, after.name)
    if key in seen:
        continue
    seen.add(key)
    then = next(events(after, "core.decision"), {})
    bound = [fact for payload in events(after, "task.answers_bound") for fact in payload.get("facts", [])]
    users = [m["content"] for m in json.loads((after / "session.json").read_text())["messages"] if m["role"] == "user"]
    rows.append({"session": folder.parent.name, "turn": after.name, "where": str(after.relative_to(LOGS)),
                 "asked": [{k: f.get(k) for k in ("question", "user_quote", "contract_quote", "workflows", "if_yes",
                                                  "if_no")} for f in asked],
                 "reply": users[-1].split("User follow-up:")[-1].strip() if users else "",
                 "bound": bound, "after": {"kind": then.get("kind"), "basis": then.get("basis"),
                                           "workflows": then.get("workflows")}})
Path(sys.argv[1]).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
print(len(rows), "answer turns;", len({r["session"].rsplit("-", 1)[0] for r in rows}), "items")
for r in rows:
    print(r["session"], r["turn"], r["after"]["kind"], r["after"]["basis"], "|", r["asked"][0]["question"][:70], "|",
          r["reply"][:70], "| bound", r["bound"])
