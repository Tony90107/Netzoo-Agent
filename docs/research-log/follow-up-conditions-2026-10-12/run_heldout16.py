"""Log 410 round: heldout16 two-turn conversations, base through the interactive loop, cand through --resume.

Usage (main repository root, with the provider key in .env, never printed):
  set -a; . ./.env; set +a
  python3 docs/research-log/follow-up-conditions-2026-10-12/run_heldout16.py <tag> [arm:id:rep ...]

`base` (.worktrees/netzoo-mt-base, bc49ba3, the live code) runs once per item through the interactive CLI:
both turns are sent on stdin, as a user types them, so the second goes through the reply resolver.
`cand` (.worktrees/netzoo-mt-cand) runs twice per item: `--session --task <turn 1>`, then
`--resume --task <turn 2>`, the path Log 410's part 2a sends through the same resolver. Session
`ve-<tag>-<arm>-<id>-<rep>`; stdout of each process in live/. Four jobs run in parallel.
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREES = Path(__file__).resolve().parents[4] / ".worktrees"
ARMS = {"base": WORKTREES / "netzoo-mt-base", "cand": WORKTREES / "netzoo-mt-cand"}
REPEATS = {"base": 1, "cand": 2}
ITEMS = {item["id"]: item for item in json.loads((HERE / "heldout16.json").read_text())["items"]}
AGENT = "scripts/netzoo_agent.py"


def _call(arm, args, out, stdin_text=None):
    with open(out, "w") as stdout:
        try:
            return subprocess.run([sys.executable, AGENT, *args], cwd=ARMS[arm], stdout=stdout,
                                  stderr=subprocess.STDOUT, input=stdin_text, text=True, timeout=1200,
                                  env=dict(os.environ)).returncode
        except subprocess.TimeoutExpired:
            return "timeout"


def run(tag, arm, key, rep):
    turns = ITEMS[key]["turns"]
    (HERE / "live").mkdir(exist_ok=True)
    session = f"ve-{tag}-{arm}-{key}-{rep}"
    stem = HERE / "live" / f"{tag}-{arm}-{key}-{rep}"
    if arm == "base":
        codes = [_call(arm, ["--session", session, "--keep-session"], f"{stem}.out", "\n".join([*turns, "exit"]) + "\n")]
    else:
        codes = [_call(arm, ["--session", session, "--keep-session", "--task", turns[0]], f"{stem}-t1.out", ""),
                 _call(arm, ["--resume", session, "--keep-session", "--task", turns[1]], f"{stem}-t2.out", "")]
    return f"{arm}:{key}:{rep}", codes


def main():
    tag = sys.argv[1]
    if sys.argv[2:]:
        jobs = [(arm, key, int(rep)) for arm, key, rep in (job.split(":") for job in sys.argv[2:])]
    else:
        jobs = [(arm, key, rep) for key in ITEMS for arm in ("base", "cand") for rep in range(1, REPEATS[arm] + 1)]
    with ThreadPoolExecutor(4) as pool:
        for name, codes in pool.map(lambda job: run(tag, *job), jobs):
            print(name, "exit", codes, flush=True)


if __name__ == "__main__":
    main()
