"""Round m3f (2026-10-15): the lean live check of the m3 fix, with round m3's own harness.

Usage: python docs/research-log/m3-method-fitting-2026-10-15/run_live_m3f.py m3f ITEM:1 ... --worktree <candidate> \
           --code-manifest docs/research-log/m3-method-fitting-2026-10-15/freeze-code.json --dotenv <main>/.env

`m3-clarification-2026-10-15/run_live.py` unchanged -- the same CLI bootstrap, per-turn evidence, code verification and
no-overwrite rules -- except that the jobs are written to this folder's `live/<tag>` and the dataset is round m3's
`heldout.json` (seen; used here as a development set).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
M3 = HERE.parent / "m3-clarification-2026-10-15"
sys.path.insert(0, str(M3))

import run_live  # noqa: E402

run_live.HERE = HERE
if "--dataset" not in sys.argv:
    sys.argv += ["--dataset", str(M3 / "heldout.json")]

if __name__ == "__main__":
    run_live.main()
