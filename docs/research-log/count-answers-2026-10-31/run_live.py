"""count-answers live F1/F2 (ROUND.md): the four LIVE-PROMPTS.json prompts x 3 runs (2 "below", 1 "meets") on this
checkout, the app `.env` plus NETZOO_ANSWER_BUTTONS=on and NETZOO_COUNT_ANSWERS=on, up to 3 turns. On a turn whose
card shows Yes/No or number buttons for a question that names a number, the scripted user clicks: below -> "No" or
the smallest number; meets -> "Yes" or the largest. Any other turn ends the conversation. Cap US$0.12.

Usage: python3 run_live.py      (live/, jobs.json, LIVE.md via score)
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[2]
WORKTREES = CHECKOUT.parent
DOTENV = WORKTREES.parent / "netzoo_agent/.env"
HARNESS = WORKTREES / "netzoo-ab/docs/research-log/closed-menu-hybrid-2026-10-19/h4/run_live.py"
PROMPTS = json.loads((HERE / "LIVE-PROMPTS.json").read_text())["prompts"]
RUNS = [(pid, rep, mode) for pid in PROMPTS for rep, mode in ((1, "below"), (2, "below"), (3, "meets"))]
CAP_USD, RESERVE = 0.12, 0.012
NUMBER_WORDS = {"two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"}
LOCK = threading.Lock()


def spent() -> float:
    calls, jev = {}, 0.0
    for path in HERE.glob("live/*/t*/session.json"):
        for call in (json.loads(path.read_text()).get("token_usage") or {}).get("calls", []):
            calls[call.get("call_id") or id(call)] = call.get("cost_micro_usd") or 0
    for trace in HERE.glob("live/*/t*/trace-*.jsonl"):
        for line in trace.read_text().splitlines():
            if '"core.jev_' in line:
                payload = json.loads(line).get("payload") or {}
                for key in ("jev", "pick", "typed", "judged", "read"):
                    found = payload.get(key)
                    if isinstance(found, dict):
                        jev += found.get("cost") or 0
    return sum(calls.values()) / 1e6 + jev


def setup():
    spec = importlib.util.spec_from_file_location("h4", HARNESS)
    live = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(HARNESS.parent))
    spec.loader.exec_module(live)
    env = live.environment(DOTENV)
    if env.get("OPENROUTER_CAPABILITY_MODEL") != "openai/gpt-4o-mini-2024-07-18" or not env.get("OPENROUTER_API_KEY"):
        raise RuntimeError("unexpected model configuration")
    env.pop("OPENROUTER_CAPABILITY_EXTRA_TOKENS", None)
    env.update({"NETZOO_ANSWER_BUTTONS": "on", "NETZOO_COUNT_ANSWERS": "on", "NETZOO_MAX_TASK_TOKENS": "30000",
                "PYTHONUNBUFFERED": "1"})
    dirty = [line for line in subprocess.check_output(["git", "status", "--porcelain"], cwd=CHECKOUT, text=True).splitlines()
             if "docs/research-log/" not in line]
    if dirty:
        raise RuntimeError(f"code not committed: {dirty[:3]}")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=CHECKOUT, text=True).strip()
    return live, env, head


def click(turn: Path, mode: str) -> str | None:
    cards = json.loads((turn / "cards.json").read_text()) if (turn / "cards.json").exists() else []
    for card in cards:
        choices = card.get("choices") or {}
        options = choices.get("options") or []
        words = set(re.findall(r"[a-z]+|\d+", (choices.get("question") or "").casefold()))
        if not options or not (words & NUMBER_WORDS or any(w.isdigit() for w in words)):
            continue
        labels = [o["label"] for o in options]
        if set(labels) == {"Yes", "No"}:
            return next(o["answer"] for o in options if o["label"] == ("No" if mode == "below" else "Yes"))
        if all(label.replace(",", "").isdigit() for label in labels):
            pick = (min if mode == "below" else max)(options, key=lambda o: int(o["label"].replace(",", "")))
            return pick["answer"]
    return None


def conversation(live, env, pid: str, rep: int, mode: str) -> dict:
    sid = f"ca-{pid}-{rep}"
    folder = HERE / "live" / sid
    folder.mkdir(parents=True)
    record = {"prompt": pid, "rep": rep, "mode": mode, "session": sid, "sent": [], "codes": []}
    text = PROMPTS[pid]
    for n in range(1, 4):
        with LOCK:
            if spent() + RESERVE > CAP_USD:
                record["end"] = "cap"
                break
        turn = folder / f"t{n}"
        turn.mkdir()
        args = ["--session" if n == 1 else "--resume", sid, "--keep-session", "--task", text]
        with (turn / "stdout.txt").open("w") as out, (turn / "stderr.txt").open("w") as err:
            code = subprocess.call([live.PYTHON, "-c", live.BOOTSTRAP, *args], cwd=CHECKOUT, stdin=subprocess.DEVNULL,
                                   env={**env, "NETZOO_PROFILE": sid, "CJ_CARD_CAPTURE": str(turn / "cards.json")},
                                   stdout=out, stderr=err, timeout=600)
        record["codes"].append(code)
        record["sent"].append("prompt" if n == 1 else text)
        source = CHECKOUT / ".netzoo" / "sessions" / f"{sid}.json"
        if source.exists():
            (turn / "session.json").write_text(source.read_text())
        for events in (CHECKOUT / ".netzoo" / "traces").glob("*/events.jsonl"):
            first = json.loads(events.read_text().splitlines()[0] or "{}")
            if (first.get("payload") or {}).get("session_id") == sid and not (turn / f"trace-{events.parent.name}.jsonl").exists() \
                    and not any((folder / f"t{m}" / f"trace-{events.parent.name}.jsonl").exists() for m in range(1, n)):
                (turn / f"trace-{events.parent.name}.jsonl").write_text(events.read_text())
        text = click(turn, mode)
        if text is None or code not in (0, 2):
            record["end"] = "no click" if code in (0, 2) else "failed"
            break
    else:
        record["end"] = "turns_done"
    (folder / "job.json").write_text(json.dumps(record, indent=1))
    return record


def main():
    live, env, head = setup()
    (HERE / "round.json").write_text(json.dumps({"head": head, "runs": RUNS, "cap_usd": CAP_USD,
                                                 "spent_before": spent()}, indent=1))
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs = list(pool.map(lambda r: conversation(live, env, *r), RUNS))
    (HERE / "jobs.json").write_text(json.dumps(jobs, indent=1))
    print(json.dumps(jobs, indent=1)[:3000], f"\nspent US${spent():.4f}")


if __name__ == "__main__":
    main()
