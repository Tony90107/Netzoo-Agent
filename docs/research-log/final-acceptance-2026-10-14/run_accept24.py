"""Item 6 round: accept24.json through the local CLI on the live code (FREEZE.md).

Usage (main repository root, provider key in .env, never printed):
  set -a; . ./.env; set +a
  python3 docs/research-log/final-acceptance-2026-10-14/run_accept24.py <tag> [key:rep ...]

Runs `plan24.jobs()` (or the given jobs) five at a time in `.worktrees/netzoo-final-live`. A two-turn item's first turn
starts the session with --session and the second continues it with --resume (Log 404). A hung turn is a timeout.
"""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from plan24 import HERE, ITEMS, WORKTREE, jobs, session_id


def run(tag, key, rep):
    item = ITEMS[key]
    turns = item.get("turns") or [item["prompt"]]
    (HERE / "live").mkdir(exist_ok=True)
    session = session_id(tag, key, rep)
    codes = []
    for number, text in enumerate(turns, 1):
        out = HERE / "live" / f"{tag}-{key}-{rep}-t{number}"
        which = ["--session", session] if number == 1 else ["--resume", session]
        with open(f"{out}.out", "w") as stdout, open(f"{out}.err", "w") as stderr:
            try:
                code = subprocess.call(
                    [sys.executable, "scripts/netzoo_agent.py", *which, "--keep-session", "--task", text],
                    cwd=WORKTREE, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL, timeout=900,
                    env=dict(os.environ))
            except subprocess.TimeoutExpired:
                code = "timeout"
        codes.append(code)
    return f"{key}:{rep}", codes


def main():
    tag = sys.argv[1]
    todo = [(key, int(rep)) for key, rep in (job.split(":") for job in sys.argv[2:])] or jobs()
    with ThreadPoolExecutor(5) as pool:
        for name, codes in pool.map(lambda job: run(tag, *job), todo):
            print(name, "exit", codes, flush=True)


if __name__ == "__main__":
    main()
