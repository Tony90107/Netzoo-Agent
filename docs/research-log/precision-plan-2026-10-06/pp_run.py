"""Log 384 live round: heldout23 through the local CLI, baseline and candidate interleaved.

Usage (main repository root, with the provider key in .env, never printed):
  set -a; . ./.env; set +a; python3 docs/research-log/precision-plan-2026-10-06/pp_run.py <tag> <repeats> [arm:id:rep ...]

Arms run in their own clean worktrees: `base` = `.worktrees/netzoo-item3-base` (9f95e14, code
identical to 161f33d: no applicability judgement), `cand` = `.worktrees/netzoo-dp-cand` (the
implementation commit). Jobs alternate arms; one fresh session per job (`hp-<tag>-<arm>-<id>-<rep>`),
five in parallel; a hung session is recorded as a timeout and the rest continue.
HELDOUT=<path relative to this folder> selects another labelled set (the analyzer self-test).
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREES = Path("/Users/chenzhonghan/Documents/LLM AGENT/.worktrees")
ARMS = {"base": WORKTREES / "netzoo-item3-base", "cand": WORKTREES / "netzoo-dp-cand"}
ITEMS = {item["id"]: item for item in json.loads((HERE / os.environ.get("HELDOUT", "heldout23/heldout.json")).read_text())["items"]}


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
