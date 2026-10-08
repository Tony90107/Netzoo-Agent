"""Log 387 held-out round: heldout1.json through the local CLI, baseline and candidate interleaved.

Usage (main repository root, with the provider key in .env, never printed):
  set -a; . ./.env; set +a; python3 docs/research-log/capability-traps-2026-10-08/run_heldout.py <tag> <repeats> [arm:id:rep ...]

Arms run in clean detached worktrees: `base` = .worktrees/netzoo-trap-base (b61f660, before Log 386),
`cand` = .worktrees/netzoo-cc-cand (the frozen candidate). Jobs alternate arms; one fresh session per job
(`ce-<tag>-<arm>-<id>-<rep>`), five in parallel; a hung session is recorded as a timeout.
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREES = Path("/Users/chenzhonghan/Documents/LLM AGENT/.worktrees")
ARMS = {"base": WORKTREES / "netzoo-trap-base", "cand": WORKTREES / "netzoo-cc-cand"}
ITEMS = {item["id"]: item for item in json.loads((HERE / "heldout1.json").read_text())["items"]}


def run(tag, arm, key, rep):
    out = HERE / "heldout-live" / f"{tag}-{arm}-{key}-{rep}"
    with open(f"{out}.out", "w") as stdout, open(f"{out}.err", "w") as stderr:
        try:
            code = subprocess.call(
                [sys.executable, "scripts/netzoo_agent.py", "--session", f"ce-{tag}-{arm}-{key}-{rep}",
                 "--task", ITEMS[key]["prompt"]],
                cwd=ARMS[arm], stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL, timeout=600)
        except subprocess.TimeoutExpired:
            code = "timeout"
    return f"{arm}:{key}:{rep}", code


def main():
    tag, repeats = sys.argv[1], int(sys.argv[2])
    (HERE / "heldout-live").mkdir(exist_ok=True)
    if sys.argv[3:]:
        jobs = [(arm, key, int(rep)) for arm, key, rep in (job.split(":") for job in sys.argv[3:])]
    else:
        jobs = [(arm, key, rep) for rep in range(1, repeats + 1) for key in ITEMS for arm in ("base", "cand")]
    with ThreadPoolExecutor(5) as pool:
        for name, code in pool.map(lambda job: run(tag, *job), jobs):
            print(name, "exit", code, flush=True)


if __name__ == "__main__":
    main()
