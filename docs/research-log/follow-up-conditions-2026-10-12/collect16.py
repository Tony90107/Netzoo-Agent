"""Log 410: collect a heldout16 round, its code-read layers, and blinded labelling packets.

Usage (repository root): python docs/research-log/follow-up-conditions-2026-10-12/collect16.py <tag>

Per session, the second turn's reply:
- a turn that ran: the last assistant message, re-rendered with the arm's own code (`replay409.render`, the
  card the desktop showed; the replay must equal the recording);
- a turn that did not run (the reply resolver asked for detail, or navigation): the prompt the CLI printed
  instead, from the process output.

The packet shows the user's own words for both turns (from heldout16, never the composed task) and the gold
requirement words of the second turn. Writes live/<tag>-structure.json, live/<tag>-packet-NN.md (both arms
shuffled together) and live/<tag>-blind-key.json. Nothing calls a model.
"""
from __future__ import annotations

import json
import os
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOG = HERE.parent
ROOT = LOG.parents[1]
WORKTREES = ROOT.parent / ".worktrees"
sys.path.insert(0, str(LOG / "reread-2026-10-11"))
from collect14 import card_text, contradictions, layers  # noqa: E402

TREES = {"base": "netzoo-mt-base", "cand": "netzoo-mt-cand"}
REPEATS = {"base": 1, "cand": 2}
ITEMS = {item["id"]: item for item in json.loads((HERE / "heldout16.json").read_text())["items"]}
RETRY = "Please enter a concrete follow-up question"
PACKET = 30

_RENDER = r'''
import json, sys
sys.path.insert(0, sys.argv[1])
import replay409 as r
from netzoo_agent_core.contracts import TaskDecision
for line in sys.stdin:
    job = json.loads(line)
    data = json.loads(open(job["path"]).read())
    plan = data.get("plan") or {}
    decision = TaskDecision.model_validate(plan["decision"])
    out = r.render(job["task"], decision, plan, r.study_purpose(job["tree"], data.get("run_id")))
    print(json.dumps({"session": job["session"], **out}))
'''


def rendered(arm: str, jobs: list[dict]) -> dict:
    env = {**os.environ, "REPLAY_CODE_ROOT": str(WORKTREES / TREES[arm])}
    done = subprocess.run([sys.executable, "-c", _RENDER, str(LOG / "verdict-architecture-2026-10-12")],
                          input="\n".join(json.dumps(job) for job in jobs), text=True, capture_output=True,
                          env=env, cwd=ROOT, check=True)
    return {row["session"]: row for row in map(json.loads, done.stdout.splitlines())}


def stdout_of(tag: str, arm: str, key: str, rep: int) -> str:
    stem = HERE / "live" / f"{tag}-{arm}-{key}-{rep}"
    path = Path(f"{stem}.out") if arm == "base" else Path(f"{stem}-t2.out")
    return path.read_text(errors="replace") if path.exists() else ""


def main(tag: str) -> None:
    rows, sessions, jobs = {}, {}, {"base": [], "cand": []}
    for arm, tree in TREES.items():
        for key in ITEMS:
            for rep in range(1, REPEATS[arm] + 1):
                sid = f"ve-{tag}-{arm}-{key}-{rep}"
                path = WORKTREES / tree / ".netzoo" / "sessions" / f"{sid}.json"
                if not path.exists():
                    rows[sid] = {"arm": arm, "item": key, "rep": rep, "missing": True}
                    continue
                data = json.loads(path.read_text())
                users = [m["content"] for m in data.get("messages", []) if m.get("role") == "user"]
                sessions[sid] = (arm, key, rep, path, data, users)
                if len(users) >= 2:
                    jobs[arm].append({"session": sid, "path": str(path), "tree": tree, "task": users[-1]})
    again = {**rendered("base", jobs["base"]), **rendered("cand", jobs["cand"])}
    blocks = []
    for sid, (arm, key, rep, path, data, users) in sessions.items():
        item = ITEMS[key]
        ran = len(users) >= 2
        decision = ((data.get("plan") or {}).get("decision") or {}) if ran else {}
        check = decision.get("capability_check") or {}
        calls = (data.get("token_usage") or {}).get("calls", [])
        printed = stdout_of(tag, arm, key, rep)
        if ran:
            reply = next(m["content"] for m in reversed(data["messages"]) if m.get("role") == "assistant")
            card = again[sid]["card"]
            kind = again[sid]["reply_kind"]
            equal = again[sid]["reply"] == reply
        else:
            reply = (RETRY + ", provide the requested input path, or describe another NetZoo goal."
                     if RETRY in printed else "(no reply to the second turn)")
            card, kind, equal = None, "needs_detail" if RETRY in printed else "none", True
        rows[sid] = {
            "arm": arm, "item": key, "rep": rep, "family": item["family"], "ran_turn_2": ran,
            "turn_2_task": users[1] if ran else None,
            "composed": bool(ran and users[1].startswith("Previous NetZoo goal:")),
            "reply_kind": kind, "replay_equal": equal, "action": decision.get("action"),
            "status": decision.get("capability_match_status"),
            "candidates": [*decision.get("matched_actions", []), *decision.get("hypothesis_actions", [])],
            "check": {k: check.get(k) for k in ("full_gap", "unavailable", "provisional", "gap_unconfirmed")},
            "check_calls": [(c.get("model"), c.get("status")) for c in calls if c.get("role") == "capability_check"],
            "errors": [c.get("exception") for c in calls if c.get("exception")],
            "layers": layers(users[1] if ran else item["turns"][1], item["requirements"], check),
            "contradictions": contradictions(users[1], reply, card, check) if ran and decision else [],
        }
        requests = "\n".join(f"Request (turn {n}): {text}" for n, text in enumerate(item["turns"], 1))
        judged = "\n".join(f"R{n}: \"{r['words']}\"" for n, r in enumerate(item["requirements"], 1)) or \
            "(none: the second turn asks for nothing; give `R: []`)"
        blocks.append((sid, "\n".join([
            requests, "", "Requirements to judge (in the user's words, from the last turn):", judged, "",
            "Reply to the last turn:", "", "````", reply.strip(), "````", "", "Card shown with the reply:",
            *card_text(card), ""])))
    random.seed(410)
    random.shuffle(blocks)
    key_map = {}
    for start in range(0, len(blocks), PACKET):
        out = []
        for index, (sid, body) in enumerate(blocks[start:start + PACKET], start + 1):
            code = f"S{index:03d}"
            key_map[code] = sid
            out += [f"## {code}", "", body]
        (HERE / "live" / f"{tag}-packet-{start // PACKET + 1:02d}.md").write_text("\n".join(out), encoding="utf-8")
    (HERE / "live" / f"{tag}-structure.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    (HERE / "live" / f"{tag}-blind-key.json").write_text(json.dumps(key_map, indent=1))
    missing = [sid for sid, row in rows.items() if row.get("missing")]
    unequal = [sid for sid, row in rows.items() if not row.get("missing") and not row["replay_equal"]]
    print(f"sessions {len(rows)}, missing {len(missing)} {missing[:4]}, "
          f"packets {(len(blocks) + PACKET - 1) // PACKET}, replay differs: {len(unequal)} {unequal[:4]}")


if __name__ == "__main__":
    main(sys.argv[1])
