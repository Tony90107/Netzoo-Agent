"""Verdict layer step 1 measurement: run17.json (heldout17 rewritten as run commands) through the local CLI.

Usage (main repository root, provider key in .env, never printed):
  set -a; . ./.env; set +a
  python3 docs/research-log/run-path-2026-10-12/run_run17.py <tag> <repeats>

One arm: .worktrees/netzoo-rp-shadow (dc00b58 = live code + shadow hook) with NETZOO_SHADOW_RUN_CHECK=1, so each
session records what the live run path did and what the check would say. Sessions `ve-<tag>-shadow-<id>-<rep>`.
Before a round, check the free check model's daily quota (1000 requests; about 1-3 check calls a session).
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = Path(__file__).resolve().parents[4] / ".worktrees" / "netzoo-rp-shadow"
ITEMS = json.loads((HERE / "run17.json").read_text())


def run(tag, item, rep):
    (HERE / "live").mkdir(exist_ok=True)
    out = HERE / "live" / f"{tag}-{item['id']}-{rep}"
    with open(f"{out}.out", "w") as stdout, open(f"{out}.err", "w") as stderr:
        try:
            code = subprocess.call(
                [sys.executable, "scripts/netzoo_agent.py", "--session", f"ve-{tag}-shadow-{item['id']}-{rep}",
                 "--keep-session", "--task", item["prompt"]],
                cwd=TREE, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL, timeout=900,
                env={**os.environ, "NETZOO_SHADOW_RUN_CHECK": "1"})
        except subprocess.TimeoutExpired:
            code = "timeout"
    return f"{item['id']}:{rep}", code


def main():
    tag, repeats = sys.argv[1], int(sys.argv[2])
    jobs = [(item, rep) for rep in range(1, repeats + 1) for item in ITEMS]
    with ThreadPoolExecutor(5) as pool:
        for name, code in pool.map(lambda job: run(tag, *job), jobs):
            print(name, "exit", code, flush=True)


if __name__ == "__main__":
    main()
