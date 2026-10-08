"""Log 385 baseline: the capability-trap set through the local CLI, in a clean worktree.

Usage (main repository root, with the provider key in .env, never printed):
  set -a; . ./.env; set +a; python3 docs/research-log/capability-traps-2026-10-08/run_traps.py <tag> <repeats> [id:rep ...]

The arm is `.worktrees/netzoo-trap-base` (b61f660, detached, no uncommitted change). One fresh
session per job (`ct-<tag>-<id>-<rep>`), repeats interleaved, five in parallel; a hung session is
recorded as a timeout and the rest continue. Output goes to live/<tag>-<id>-<rep>.out/.err.
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARM = Path(os.environ.get("ARM", "/Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-trap-base"))
ITEMS = {item["id"]: item for item in json.loads((HERE / "traps.json").read_text())["items"]}


def run(tag, key, rep):
    out = HERE / "live" / f"{tag}-{key}-{rep}"
    with open(f"{out}.out", "w") as stdout, open(f"{out}.err", "w") as stderr:
        try:
            code = subprocess.call(
                [sys.executable, "scripts/netzoo_agent.py", "--session", f"ct-{tag}-{key}-{rep}",
                 "--task", ITEMS[key]["prompt"]],
                cwd=ARM, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL, timeout=600)
        except subprocess.TimeoutExpired:
            code = "timeout"
    return f"{key}:{rep}", code


def main():
    tag, repeats = sys.argv[1], int(sys.argv[2])
    (HERE / "live").mkdir(exist_ok=True)
    if sys.argv[3:]:
        jobs = [(key, int(rep)) for key, rep in (job.split(":") for job in sys.argv[3:])]
    else:
        jobs = [(key, rep) for rep in range(1, repeats + 1) for key in ITEMS]
    with ThreadPoolExecutor(5) as pool:
        for name, code in pool.map(lambda job: run(tag, *job), jobs):
            print(name, "exit", code, flush=True)


if __name__ == "__main__":
    main()
