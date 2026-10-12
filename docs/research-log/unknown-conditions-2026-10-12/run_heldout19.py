"""Log 414 round: heldout19.json through the local CLI, base and candidate interleaved.

Usage (main repository root, with the provider key in .env, never printed):
  set -a; . ./.env; set +a
  python3 docs/research-log/unknown-conditions-2026-10-12/run_heldout19.py <tag> <repeats> [arm:id:rep ...]

Arms run in clean detached worktrees: `base` = .worktrees/netzoo-uc-base (85a6397, the live code),
`cand` = .worktrees/netzoo-uc-cand (0f1b504, the frozen candidate).
One session per job
(`ve-<tag>-<arm>-<id>-<rep>`). Five jobs run in parallel; a hung turn is recorded as a timeout.

A multi-turn item's first turn starts the session with --session and every later turn continues it
with --resume (Log 404).
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREES = Path(__file__).resolve().parents[4] / ".worktrees"
ARMS = {"base": WORKTREES / "netzoo-uc-base", "cand": WORKTREES / "netzoo-uc-cand"}
ITEMS = {item["id"]: item for item in json.loads((HERE / "heldout19.json").read_text())["items"]}


def run(tag, arm, key, rep):
    item = ITEMS[key]
    turns = item.get("turns") or [item["prompt"]]
    (HERE / "live").mkdir(exist_ok=True)
    session = f"ve-{tag}-{arm}-{key}-{rep}"
    codes = []
    for number, text in enumerate(turns, 1):
        out = HERE / "live" / f"{tag}-{arm}-{key}-{rep}-t{number}"
        which = ["--session", session] if number == 1 else ["--resume", session]
        with open(f"{out}.out", "w") as stdout, open(f"{out}.err", "w") as stderr:
            try:
                code = subprocess.call(
                    [sys.executable, "scripts/netzoo_agent.py", *which, "--keep-session", "--task", text],
                    cwd=ARMS[arm], stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL, timeout=900,
                    env=dict(os.environ))
            except subprocess.TimeoutExpired:
                code = "timeout"
        codes.append(code)
    return f"{arm}:{key}:{rep}", codes


def main():
    tag, repeats = sys.argv[1], int(sys.argv[2])
    if sys.argv[3:]:
        jobs = [(arm, key, int(rep)) for arm, key, rep in (job.split(":") for job in sys.argv[3:])]
    else:
        jobs = [(arm, key, rep) for rep in range(1, repeats + 1) for key in ITEMS for arm in ARMS]
    with ThreadPoolExecutor(5) as pool:
        for name, codes in pool.map(lambda job: run(tag, *job), jobs):
            print(name, "exit", codes, flush=True)


if __name__ == "__main__":
    main()
