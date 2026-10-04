"""Log 342 live round: the held-out set through the local CLI, baseline and candidate interleaved.

Usage (candidate repository root, with the provider key in .env, never printed):
  set -a; . ./.env; set +a; python3 docs/research-log/purpose-contract-2026-10-04/run_live.py <tag> <repeats> [job ...]

Arms: `base` runs in the baseline worktree (the declaration commit), `cand` in
this tree. Jobs alternate arms (base, cand, base, ...) so neither runs as its
own batch. One fresh session per job: `hp-<tag>-<arm>-<id>-<rep>`, five in
parallel; a hung session is recorded as a timeout and the rest continue.
A job argument `cand:F1-a:2` reruns only that one.
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ARMS = {"base": Path("/Users/chenzhonghan/Documents/LLM AGENT/.worktrees/netzoo-purpose-baseline"), "cand": ROOT}
ITEMS = {item["id"]: item for item in json.loads((HERE / "heldout" / "heldout.json").read_text())["items"]}


def run(tag, arm, key, rep):
    out = HERE / "live" / f"{tag}-{arm}-{key}-{rep}"
    with open(f"{out}.out", "w") as stdout, open(f"{out}.err", "w") as stderr:
        try:
            code = subprocess.call(
                [sys.executable, "scripts/netzoo_agent.py", "--session", f"hp-{tag}-{arm}-{key}-{rep}",
                 "--task", ITEMS[key]["prompt"]],
                cwd=ARMS[arm], stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL, timeout=600)
        except subprocess.TimeoutExpired:
            code = "timeout"
    return f"{arm}:{key}:{rep}", code


def main():
    tag, repeats = sys.argv[1], int(sys.argv[2])
    (HERE / "live").mkdir(exist_ok=True)
    if sys.argv[3:]:
        jobs = [(arm, key, int(rep)) for arm, key, rep in (job.split(":") for job in sys.argv[3:])]
    else:
        jobs = [(arm, key, rep) for rep in range(1, repeats + 1) for key in ITEMS for arm in ("base", "cand")]
    with ThreadPoolExecutor(5) as pool:
        for name, code in pool.map(lambda job: run(tag, *job), jobs):
            print(name, "exit", code, flush=True)


if __name__ == "__main__":
    main()
