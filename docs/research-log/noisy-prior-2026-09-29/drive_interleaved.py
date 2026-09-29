"""Interleave traced live rounds of the Log 257 fix and unmodified HEAD (gpt-4o-mini).

Usage: python drive_interleaved.py <head_worktree> <rounds>
Loads .env into this process only (values are never printed), then runs the
2026-09-23 traced harness from each tree in turn, so same-day provider drift is
shared by both arms (Log 119-120). Reports land next to this file.
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE.parents[2]
HEAD = Path(sys.argv[1]).resolve()
ROUNDS = int(sys.argv[2])
CORPORA = {"blind": FIX / "docs/research-log/blind/blind_en.json", "noisy": HERE / "corpus.json"}

from dotenv import dotenv_values  # noqa: E402

env = {**os.environ, **{k: v for k, v in dotenv_values(FIX / ".env").items() if v is not None}}
for round_ in range(1, ROUNDS + 1):
    for arm, tree in (("fix", FIX), ("head", HEAD)):
        for name, corpus in CORPORA.items():
            out = HERE / f"live-{arm}-r{round_}-{name}.json"
            if out.exists():
                continue
            harness = tree / "docs/research-log/live-semantic-trace-2026-09-23-harness.py"
            done = subprocess.run([sys.executable, str(harness), "legacy", "1", str(out), str(corpus)],
                                  env=env, cwd=tree, capture_output=True, text=True)
            print(arm, round_, name, done.returncode, done.stdout.strip()[-200:], done.stderr.strip()[-300:], flush=True)
