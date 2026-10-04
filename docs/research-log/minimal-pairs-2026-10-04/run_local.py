"""Log 340: run each minimal-pair prompt through the local CLI, as a user would.

Usage (repository root, with the provider key in .env, never printed):
  set -a; . ./.env; set +a; python3 docs/research-log/minimal-pairs-2026-10-04/run_local.py <tag> <repeats> [prompt ids or id-rep...]

One fresh session per prompt and repeat (`mp-<tag>-<id>-<rep>`), five in parallel.
The CLI's non-tty output (the full reply) goes to out/<tag>-<id>-<rep>.out;
collect.py then reads each session's decision and card from .netzoo/.
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROMPTS = json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))


def run(tag, key, rep):
    out = HERE / "out" / f"{tag}-{key}-{rep}"
    with open(f"{out}.out", "w") as stdout, open(f"{out}.err", "w") as stderr:
        try:
            code = subprocess.call(
                [sys.executable, "scripts/netzoo_agent.py", "--session", f"mp-{tag}-{key}-{rep}", "--task", PROMPTS[key]],
                cwd=ROOT, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL, timeout=600)
        except subprocess.TimeoutExpired:
            # One hung session must not cancel the jobs still queued (s1 lost 8 that way).
            code = "timeout"
    return f"{key}-{rep}", code


def main():
    tag, repeats, keys = sys.argv[1], int(sys.argv[2]), sys.argv[3:] or list(PROMPTS)
    (HERE / "out").mkdir(exist_ok=True)
    # "A0" runs every repeat of that prompt; "A0-3" runs only repeat 3.
    jobs = [tuple(key.split("-")) if "-" in key else (key, str(rep))
            for rep in range(1, repeats + 1) for key in keys
            if "-" not in key or rep == 1]
    with ThreadPoolExecutor(5) as pool:
        for name, code in pool.map(lambda job: run(tag, *job), jobs):
            print(name, "exit", code, flush=True)


if __name__ == "__main__":
    main()
