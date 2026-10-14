"""Item 6 (FREEZE.md): the accept24 round plan, shared by the runner, the collector and the analysis.

Every item runs once (rep 1); 30 items drawn with random.seed(24) run a second time (rep 2), for agreement only.
Sessions are `ve-a24-live-<id>-<rep>` in `.worktrees/netzoo-final-live`.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKTREE = Path(__file__).resolve().parents[4] / ".worktrees" / "netzoo-final-live"
ITEMS = {item["id"]: item for item in json.loads((HERE / "accept24.json").read_text())["items"]}


def repeated() -> list[str]:
    random.seed(24)
    return sorted(random.sample(sorted(ITEMS), 30))


def jobs() -> list[tuple[str, int]]:
    return [(key, 1) for key in ITEMS] + [(key, 2) for key in repeated()]


def session_id(tag: str, key: str, rep: int) -> str:
    return f"ve-{tag}-live-{key}-{rep}"
