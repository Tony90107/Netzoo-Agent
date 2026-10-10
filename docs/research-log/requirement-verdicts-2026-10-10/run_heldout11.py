"""Log 403 round: heldout11.json through the local CLI, base and candidate interleaved.

Usage (main repository root, with the provider key in .env, never printed):
  set -a; . ./.env; set +a
  [OUTAGE=1] python3 docs/research-log/requirement-verdicts-2026-10-10/run_heldout11.py <tag> <repeats> [arm:id:rep ...]

Arms run in clean detached worktrees: `base` = .worktrees/netzoo-verdict-base (the live code),
`cand` = .worktrees/netzoo-verdict-cand (the frozen candidate). One fresh session per job
(`ve-<tag>-<arm>-<id>-<rep>`); a multi-turn item sends its turns one after the other into that
session. Five jobs run in parallel; a hung turn is recorded as a timeout.

OUTAGE=1 simulates the check's own model failing (Log 401): a model id that does not exist is
put in the allowlist and set as OPENROUTER_CAPABILITY_MODEL, so the provider errors every time and
no free-model quota is used.
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREES = Path(__file__).resolve().parents[4] / ".worktrees"
ARMS = {"base": WORKTREES / "netzoo-verdict-base", "cand": WORKTREES / "netzoo-verdict-cand"}
OUTAGE_MODEL = "nvidia/netzoo-outage-simulation:free"
ITEMS = {item["id"]: item for item in json.loads((HERE / "heldout11.json").read_text())["items"]}


def environment() -> dict:
    env = dict(os.environ)
    if os.environ.get("OUTAGE") == "1":
        env["OPENROUTER_CAPABILITY_MODEL"] = OUTAGE_MODEL
        allow = [model for model in env.get("NETZOO_ROUTER_MODEL_ALLOWLIST", "").split(",") if model]
        env["NETZOO_ROUTER_MODEL_ALLOWLIST"] = ",".join([*allow, OUTAGE_MODEL])
    return env


def run(tag, arm, key, rep):
    item = ITEMS[key]
    turns = item.get("turns") or [item["prompt"]]
    (HERE / "live").mkdir(exist_ok=True)
    codes = []
    for number, text in enumerate(turns, 1):
        out = HERE / "live" / f"{tag}-{arm}-{key}-{rep}-t{number}"
        with open(f"{out}.out", "w") as stdout, open(f"{out}.err", "w") as stderr:
            try:
                code = subprocess.call(
                    [sys.executable, "scripts/netzoo_agent.py", "--session", f"ve-{tag}-{arm}-{key}-{rep}",
                     "--task", text],
                    cwd=ARMS[arm], stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL, timeout=900,
                    env=environment())
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
