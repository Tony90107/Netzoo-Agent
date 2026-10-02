"""Log 320: run each English TEST_PROMPTS scenario once through the local CLI, as a user would.

Usage (repository root, with the provider key in .env, never printed):
  set -a; . ./.env; set +a; python3 docs/research-log/test10-2026-10-03/run_local.py <tag> [test ids...]

One fresh session per prompt (`t10-<tag>-<id>`), five in parallel. The CLI's
non-tty output (the full reply) goes to out/<tag>-<id>.out; collect.py then
reads each session's decision and card from .netzoo/.
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROMPTS = json.loads((HERE / "prompts.json").read_text(encoding="utf-8"))


def run(tag, key):
    out = HERE / "out" / f"{tag}-{key}"
    with open(f"{out}.out", "w") as stdout, open(f"{out}.err", "w") as stderr:
        code = subprocess.call(
            [sys.executable, "scripts/netzoo_agent.py", "--session", f"t10-{tag}-{key}", "--task", PROMPTS[key]],
            cwd=ROOT, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL, timeout=600)
    return key, code


def main():
    tag, keys = sys.argv[1], sys.argv[2:] or list(PROMPTS)
    (HERE / "out").mkdir(exist_ok=True)
    with ThreadPoolExecutor(5) as pool:
        for key, code in pool.map(lambda k: run(tag, k), keys):
            print(key, "exit", code, flush=True)


if __name__ == "__main__":
    main()
