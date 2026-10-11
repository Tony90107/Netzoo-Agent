"""Log 405: collect a heldout13 round, its code-read layers, and blinded labelling packets.

Usage (repository root): python docs/research-log/checked-match-2026-10-11/collect13.py <tag> <repeats>

Adapted from Log 404's collect12.py: heldout13 and the cm worktrees. Adds, per session, whether the
Log 405 rule adopted the check's workflow (trace `routing.check_match_adopted`), and a code check for
the conflict it targets: the understanding lines name the check's workflow while the body falls back,
selects nothing, or selects another workflow.

For each arm the recorded sessions (`ve-<tag>-<arm>-<id>-<rep>`) are re-rendered with that arm's own
code (`replay_sessions.py`), which gives the card the desktop showed; the replayed reply must equal the
recorded one. Then, per session and gold requirement:

- L1 (understood): the check requirement whose words the gold words share most, if any;
- L2 (checked): that requirement's status, or `unconfirmed` when the check confirmed nothing;
- CS (contradiction, code): a reading the check found deliverable answered "no registered workflow",
  or, with the check unconfirmed, a workflow presented as the answer.

Writes live/<tag>-structure.json, live/<tag>-packet-NN.md (blinded, both arms shuffled together)
and live/<tag>-blind-key.json. Nothing calls a model.
"""
from __future__ import annotations

import json
import os
import random
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORKTREES = ROOT.parent / ".worktrees"
REPLAY = ROOT / "docs" / "research-log" / "requirement-verdicts-2026-10-10" / "replay_sessions.py"
ARMS = {"base": "netzoo-cm-base", "cand": "netzoo-cm-cand"}
ITEMS = {item["id"]: item for item in json.loads((HERE / "heldout13.json").read_text())["items"]}
PACKET = 30
sys.path.insert(0, str(ROOT / "scripts"))
PROMISES = ("Selected path", "These all fit", "fits that result", "fits your goal", "is the registered workflow for",
            "The only registered workflow compatible")


def replay(tag: str, arm: str) -> dict[str, dict]:
    out = HERE / "live" / f"{tag}-{arm}-replay.jsonl"
    env = {**os.environ, "REPLAY_CODE_ROOT": str(WORKTREES / ARMS[arm]), "REPLAY_ARMS": ARMS[arm],
           "REPLAY_SESSION_PREFIX": "ve"}
    subprocess.run([sys.executable, str(REPLAY), str(out), tag], env=env, check=True,
                   cwd=ROOT, stdout=subprocess.DEVNULL)
    return {row["session"]: row for row in map(json.loads, out.read_text().splitlines())}


def span(task: str, words: str):
    words = (words or "").strip().rstrip(".,;:!?").strip()
    start = task.casefold().find(words.casefold()) if words else -1
    return None if start < 0 else (start, start + len(words))


def overlap(task: str, one: str, other: str) -> int:
    a, b = span(task, one), span(task, other)
    if a is None or b is None:
        return 0
    shared = min(a[1], b[1]) - max(a[0], b[0])
    return shared if shared > 0 and shared >= 0.5 * min(a[1] - a[0], b[1] - b[0]) else 0


def body_of(reply: str) -> str:
    return reply.split("\n\n", 1)[1] if reply.startswith("What I understood") and "\n\n" in reply else reply


_SECTION = re.compile(r"^\*\*(?:Reading|Step) \d+ -- \"(.+?)\"\*\*$", re.M)


def confirmed_nothing(check: dict) -> bool:
    """The check did not run, only the backup read it, or an owed second opinion failed."""
    return bool(check.get("unavailable") or check.get("provisional") or check.get("gap_unconfirmed"))


_UNDERSTOOD = re.compile(r"-- available from ([A-Z][A-Z-]+)")
_BODY_PICK = re.compile(r"(?:Selected path|Fallback recommendation): \*\*([A-Z][A-Z-]+)\*\*")


def conflicts(reply: str) -> list[str]:
    """The understanding lines credit a workflow the body does not select (Log 405's target)."""
    credited = set(_UNDERSTOOD.findall(reply))
    if not credited:
        return []
    body = body_of(reply)
    picked = set(_BODY_PICK.findall(body))
    if "no workflow was selected" in body:
        return [f"understood {sorted(credited)}, body selected no workflow"]
    if picked and not picked & credited:
        return [f"understood {sorted(credited)}, body selected {sorted(picked)}"]
    return []


def contradictions(task: str, reply: str, card: dict | None, check: dict) -> list[str]:
    found = conflicts(reply)
    deliverable = [item for item in check.get("requirements") or []
                   if item.get("kind") == "result" and item.get("status") in ("available", "with_step", "partial")]
    body = body_of(reply)
    heads = list(_SECTION.finditer(body))
    for index, head in enumerate(heads):
        end = heads[index + 1].start() if index + 1 < len(heads) else len(body)
        section = body[head.start():end]
        if "No registered workflow produces this result" in section and any(
                overlap(task, head.group(1), item["quote"]) for item in deliverable):
            found.append(f"reading said no workflow for a deliverable result: {head.group(1)}")
    if confirmed_nothing(check) and not check.get("full_gap"):
        promised = [phrase for phrase in PROMISES if phrase in body]
        options = ((card or {}).get("choices") or {}).get("options") or []
        badges = [option["badge"] for option in options if option.get("badge")]
        if promised or badges or "fits your goal" in str((card or {}).get("headline")):
            found.append(f"unconfirmed check, answer presented: {promised + badges}")
    return found


def adopted(worktree: str, run_id: str | None) -> str | None:
    """The workflow the Log 405 rule adopted in this run, if it fired."""
    path = WORKTREES / worktree / ".netzoo" / "traces" / str(run_id) / "events.jsonl"
    if not run_id or not path.exists():
        return None
    for line in path.read_text().splitlines():
        event = json.loads(line) if line.strip() else {}
        if event.get("event_type") == "routing.check_match_adopted":
            return event["payload"]["action"]
    return None


def blank_second_opinion(worktree: str, run_id: str | None) -> list | None:
    """Part 2's answers when it fired in this run: a second opinion asked although the check was no full gap."""
    path = WORKTREES / worktree / ".netzoo" / "traces" / str(run_id) / "events.jsonl"
    if not run_id or not path.exists():
        return None
    events = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    checked = [e for e in events if e.get("event_type") == "routing.capability_checked"]
    opinions = [e for e in events if e.get("event_type") == "routing.capability_second_opinion"]
    if not checked or not opinions or (checked[-1].get("payload") or {}).get("check", {}).get("full_gap"):
        return None
    return [(pair[1], answer) for pair, answer in zip(opinions[-1]["payload"].get("pairs") or [],
                                                     opinions[-1]["payload"].get("answers") or [])]


def layers(task: str, gold: list[dict], check: dict) -> list[dict]:
    results = [item for item in check.get("requirements") or [] if item.get("kind") == "result"]
    unconfirmed = confirmed_nothing(check)
    rows = []
    for requirement in gold:
        best = max(results, key=lambda item: overlap(task, requirement["words"], item["quote"]), default=None)
        if best is not None and not overlap(task, requirement["words"], best["quote"]):
            best = None
        status = None if best is None else ("unconfirmed" if unconfirmed else best["status"])
        rows.append({"words": requirement["words"], "expect": requirement["expect"], "understood": best is not None,
                     "checked": status, "asked_as": None if best is None else best.get("asked_as")})
    return rows


def card_text(card: dict | None) -> list[str]:
    if not card:
        return ["(no card)"]
    lines = [f"- headline: {card.get('headline')}"]
    lines += [f"- point: {point}" for point in card.get("points") or []]
    choices = card.get("choices") or {}
    if choices:
        lines.append(f"- question: {choices.get('question')}")
        lines += [f"- option: {o['label']} — {o.get('description', '')}" + (f" [{o['badge']}]" if o.get("badge") else "")
                  for o in choices.get("options") or []]
    lines += [f"- not available: {o['label']} — {o.get('reason', '')}" for o in card.get("unavailable") or []]
    lines += [f"- next step: {o['label']}" for o in card.get("next_steps") or []]
    return lines


def main(tag: str, repeats: int) -> None:
    (HERE / "live").mkdir(exist_ok=True)
    rows, blocks = {}, []
    for arm, worktree in ARMS.items():
        rendered = replay(tag, arm)
        for key, item in ITEMS.items():
            for rep in range(1, repeats + 1):
                sid = f"ve-{tag}-{arm}-{key}-{rep}"
                path = WORKTREES / worktree / ".netzoo" / "sessions" / f"{sid}.json"
                if not path.exists():
                    rows[sid] = {"arm": arm, "item": key, "missing": True}
                    continue
                session = json.loads(path.read_text())
                decision = (session.get("plan") or {}).get("decision") or {}
                users = [m["content"] for m in session.get("messages", []) if m.get("role") == "user"]
                reply = next((m["content"] for m in reversed(session.get("messages", []))
                              if m.get("role") == "assistant"), "")
                calls = (session.get("token_usage") or {}).get("calls", [])
                check = decision.get("capability_check") or {}
                again = rendered.get(sid) or {}
                task = users[-1] if users else ""
                rows[sid] = {
                    "arm": arm, "item": key, "rep": rep, "family": item["family"], "form": item.get("form"),
                    "twin": item.get("twin"), "turns": len(users), "action": decision.get("action"),
                    "status": decision.get("capability_match_status"),
                    "candidates": [*decision.get("matched_actions", []), *decision.get("hypothesis_actions", [])],
                    "reply_kind": again.get("reply_kind"), "replay_equal": again.get("reply") == reply,
                    "card_error": again.get("card_error"),
                    "consult": item.get("consult"),
                    "check": {k: check.get(k) for k in ("full_gap", "unavailable", "provisional", "gap_unconfirmed",
                                                         "unchecked")},
                    "check_kinds": [r.get("kind") for r in check.get("requirements") or []],
                    "so2": blank_second_opinion(worktree, session.get("run_id")),
                    "adopted": adopted(worktree, session.get("run_id")),
                    "conflicts": conflicts(reply),
                    "check_calls": [(c.get("model"), c.get("status")) for c in calls if c.get("role") == "capability_check"],
                    "second_opinion": [(c.get("model"), c.get("status")) for c in calls
                                       if c.get("role") == "capability_second_opinion"],
                    "errors": [c.get("exception") for c in calls if c.get("exception")],
                    "budget_exhausted": (session.get("token_usage") or {}).get("budget_exhausted"),
                    "layers": layers(task, item["requirements"], check),
                    "contradictions": contradictions(task, reply, again.get("card"), check) if decision else [],
                    "cost": sum((c.get("cost_micro_usd") or 0) for c in calls) / 1e6,
                }
                requests = "\n".join(f"Request (turn {n}): {text}" for n, text in enumerate(users, 1))
                judged = "\n".join(f"R{n}: \"{r['words']}\"" for n, r in enumerate(item["requirements"], 1))
                extra = ""
                if item["family"] == "M":
                    judged, extra = "(none: this request asks about methods; give `R: []`)", "\nJudge `consult` for this session."
                blocks.append((sid, "\n".join([
                    requests, "", "Requirements to judge (in the user's words):", judged + extra, "",
                    "Reply:", "", "````", reply.strip(), "````", "", "Card shown with the reply:",
                    *card_text(again.get("card")), ""])))
    random.seed(405)
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
    missing = sum(1 for row in rows.values() if row.get("missing"))
    unequal = [sid for sid, row in rows.items() if not row.get("missing") and not row["replay_equal"]]
    print(f"sessions {len(rows)}, missing {missing}, packets {(len(blocks) + PACKET - 1) // PACKET}, "
          f"replay differs from record: {len(unequal)} {unequal[:5]}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
