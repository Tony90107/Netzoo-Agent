"""Reading named paths stays linear in the length of the message.

"X as the expression matrix" was searched from every offset inside a long
token, and every quote mark re-scanned the rest of its line for a closing mark.
Hydration reads paths ~51 times per turn, so a 6,000-character message spent
~15 s of one graph turn in regex.
"""

import random
import re
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import PROSE_PATH_TERMINATORS, TaskDecision  # noqa: E402
from netzoo_agent_core.interpretation.extraction import (  # noqa: E402
    _looks_like_path,
    _reverse_named_path,
    _task_path,
)
from netzoo_agent_core.interpretation.hydration import hydrate_router_decision  # noqa: E402
from netzoo_agent_core.routing.role_paths import _alias_pattern  # noqa: E402

_SIZE = 20_000
_FILLERS = {
    "one long token": "x" * _SIZE,
    "prose on one line": ("it's the gene's role, don't skip it " * 600)[:_SIZE],
    "minified JSON": ('{"gene": "TP53", "score": 1}, ' * 700)[:_SIZE],
}


@pytest.mark.parametrize("filler", _FILLERS.values(), ids=_FILLERS)
def test_hydrating_a_20_kb_message_takes_under_a_second(filler):
    task = f"Do not run anything.\n{filler}\nPlease search."
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False,
                            confidence=1, reason="test")

    start = time.perf_counter()
    hydrate_router_decision(decision, task)

    assert time.perf_counter() - start < 1.0


@pytest.mark.parametrize("filler", _FILLERS.values(), ids=_FILLERS)
def test_a_reverse_named_path_after_a_long_message_is_still_read(filler):
    task = (f"{filler}\nUse 'my data/expr.tsv' as the expression matrix "
            "and data/study/motif.tsv for the motif prior.")

    assert _task_path(task, "expression_file") == "my data/expr.tsv"
    assert _task_path(task, "motif_file") == "data/study/motif.tsv"


def _single_regex(task: str, aliases: tuple[str, ...]) -> str | None:
    """The search before the fix, kept as the oracle for what it returns."""
    match = re.search(
        rf"(?:(?P<quote>['\"])(?P<quoted>.*?)(?P=quote)|"
        rf"(?P<plain>[^{PROSE_PATH_TERMINATORS}]+))\s+(?:as|for)\s+(?:the\s+)?(?:{_alias_pattern(aliases)})",
        task,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    if match.group("quote"):
        return match.group("quoted").strip().rstrip(".。")
    cleaned = match.group("plain").strip().rstrip(".。")
    return cleaned if _looks_like_path(cleaned) else None


_PIECES = (" ", "  ", "\n", "\t", "，", ",", "、", "；", "。", "?", "'", '"', "''", "(", ")",
           "x", "a.tsv", "data/", "./b.csv", ".", "use", "the", "as", "for", "AS", "x y",
           "expression", "Expression", "motif", "prior", "表現矩陣", "先驗")


@pytest.mark.parametrize("aliases", [
    ("expression_file", "expression", "表現矩陣", "表現資料"),
    ("motif_file", "motif", "prior", "先驗", "調控先驗"),
])
def test_reverse_named_path_matches_the_single_regex_it_replaced(aliases):
    rng = random.Random(20261005)
    noise = lambda limit: "".join(rng.choice(_PIECES) for _ in range(rng.randint(0, limit)))
    for _ in range(4_000):
        task = "".join(
            noise(8) + rng.choice(("", " ", "\n", "'", '"')) + noise(4)
            + rng.choice((" ", "\n", "'", '"')) + rng.choice(("as", "for", "fo"))
            + rng.choice((" ", "\n", "")) + rng.choice(("", "the ")) + rng.choice(aliases + ("xx",))
            for _ in range(rng.randint(1, 3))
        ) + noise(6)

        assert _reverse_named_path(task, aliases) == _single_regex(task, aliases), task
