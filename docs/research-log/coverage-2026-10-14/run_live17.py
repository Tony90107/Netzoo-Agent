"""Items 4-5 live check: live17.json through the local CLI, one session each (announced 2026-10-14, 17 sessions).

Usage (main repository root, provider key in .env, never printed):
  set -a; . ./.env; set +a
  python3 docs/research-log/coverage-2026-10-14/run_live17.py <tag> [items.json]

One arm: .worktrees/netzoo-cov-live (c1: f0a0536; c2: d806644, live13.json). Sessions `cv-<tag>-<id>`.
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = Path(__file__).resolve().parents[4] / ".worktrees" / "netzoo-cov-live"
ITEMS = json.loads((HERE / (sys.argv[2] if len(sys.argv) > 2 else "live17.json")).read_text())


def run(tag, item):
    (HERE / "live").mkdir(exist_ok=True)
    out = HERE / "live" / f"{tag}-{item['id']}"
    with open(f"{out}.out", "w") as stdout, open(f"{out}.err", "w") as stderr:
        try:
            code = subprocess.call(
                [sys.executable, "scripts/netzoo_agent.py", "--session", f"cv-{tag}-{item['id']}", "--keep-session",
                 "--task", item["prompt"]],
                cwd=TREE, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL, timeout=900)
        except subprocess.TimeoutExpired:
            code = "timeout"
    return item["id"], code


def main():
    tag = sys.argv[1]
    with ThreadPoolExecutor(5) as pool:
        for name, code in pool.map(lambda item: run(tag, item), ITEMS):
            print(name, "exit", code, flush=True)


if __name__ == "__main__":
    main()
