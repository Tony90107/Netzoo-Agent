"""Log 404 round: heldout12.json through the local CLI, base and candidate interleaved.

Usage (main repository root, with the provider key in .env, never printed):
  set -a; . ./.env; set +a
  python3 docs/research-log/checked-no-result-2026-10-11/run_heldout12.py <tag> <repeats> [arm:id:rep ...]

Arms run in clean detached worktrees: `base` = .worktrees/netzoo-p1-base (2eee5e3, the live code, plus the 332af36 resume fix),
`cand` = .worktrees/netzoo-p1-cand (332af36: the 7d9b023 candidate plus the resume fix). One session per job
(`ve-<tag>-<arm>-<id>-<rep>`). Five jobs run in parallel; a hung turn is recorded as a timeout.

A multi-turn item's first turn starts the session with --session and every later turn continues it
with --resume. The Log 403 runner passed --session on every turn, which only names the session: each
turn started a new conversation under the same id, so heldout11's T items measured the last
sentence alone.
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREES = Path(__file__).resolve().parents[4] / ".worktrees"
ARMS = {"base": WORKTREES / "netzoo-p1-base", "cand": WORKTREES / "netzoo-p1-cand"}
ITEMS = {item["id"]: item for item in json.loads((HERE / "heldout12.json").read_text())["items"]}


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
        jobs = [(arm, key, rep) for rep in range(1, repeats + 1) for key in ITEMS for arm in ("base", "cand")]
    with ThreadPoolExecutor(5) as pool:
        for name, codes in pool.map(lambda job: run(tag, *job), jobs):
            print(name, "exit", codes, flush=True)


if __name__ == "__main__":
    main()
