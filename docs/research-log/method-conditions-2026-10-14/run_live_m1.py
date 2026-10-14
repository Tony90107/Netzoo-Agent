"""M1 step 4.3: live_m1.json through the local CLI on the candidate code, one session per item.

Usage (main repository root, provider key in .env, never printed):
  set -a; . ./.env; set +a
  python3 <this worktree>/docs/research-log/method-conditions-2026-10-14/run_live_m1.py <tag> [id ...]

Runs in this file's own checkout (the candidate worktree), five at a time; sessions `mc-<tag>-<id>`. A two-turn item's
first turn starts the session with --session and the second continues it with --resume (Log 404). The checkout must
import before any session starts (a24's void run).
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parents[2]
ITEMS = {item["id"]: item for item in json.loads((HERE / "live_m1.json").read_text())["items"]}


def run(tag, key):
    item = ITEMS[key]
    turns = item.get("turns") or [item["prompt"]]
    (HERE / "live").mkdir(exist_ok=True)
    session = f"mc-{tag}-{key}"
    codes = []
    for number, text in enumerate(turns, 1):
        out = HERE / "live" / f"{tag}-{key}-t{number}"
        which = ["--session", session] if number == 1 else ["--resume", session]
        with open(f"{out}.out", "w") as stdout, open(f"{out}.err", "w") as stderr:
            try:
                code = subprocess.call(
                    [sys.executable, "scripts/netzoo_agent.py", *which, "--keep-session", "--task", text],
                    cwd=TREE, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL, timeout=900,
                    env=dict(os.environ))
            except subprocess.TimeoutExpired:
                code = "timeout"
        codes.append(code)
    return key, codes


def main():
    tag = sys.argv[1]
    subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, 'scripts'); import netzoo_agent_core"],
                   cwd=TREE, check=True)
    todo = sys.argv[2:] or list(ITEMS)
    with ThreadPoolExecutor(5) as pool:
        for name, codes in pool.map(lambda key: run(tag, key), todo):
            print(name, "exit", codes, flush=True)


if __name__ == "__main__":
    main()
