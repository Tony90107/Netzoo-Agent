"""Widening the history vocabulary must not move any clause that already read right.

Clause scoping is a bounded lexical pass, shared between routing and input
detection, and within a clause a history hit overrides a current hit. So a
marker that is slightly too broad does not merely mislabel a sentence -- it
deletes a declared input from the request. `already` on its own is the clearest
example: "I already have an expression matrix" is a statement of possession, and
reading it as history leaves the right workflow with no input.

Every marker added in Log 123 is therefore bound to a completion verb rather
than to an adverb. What that buys is measured here rather than asserted: the
prompts carrying a historical clause are named, so any future widening that
reaches one more of them fails and says which.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.interpretation.request_integrity import (  # noqa: E402
    _scoped_clauses, input_mentions,
)

CORPUS = json.loads(
    (Path(__file__).parents[1] / "tests" / "routing_scenarios.json").read_text()
)

#: Every corpus prompt with at least one historical clause. Each is one a reader
#: can confirm by eye: all six report a method or an analysis as already done.
PROMPTS_WITH_HISTORY = {
    "mirna-current-goal",
    "mirna-current-goal-misspelled",
    "mutation-no-fallback-phrases",
    "original-q3",
    "reverse-history-expression",
    "run-named-tool-finished-then-new-goal",
    "unsupported-protein-acquisition",
}


def test_exactly_these_corpus_prompts_carry_a_historical_clause():
    found = {
        case["id"] for case in CORPUS
        if any(scope == "historical" for _, scope in _scoped_clauses(case["prompt"]))
    }

    assert found == PROMPTS_WITH_HISTORY


def test_owning_data_is_never_reported_as_history():
    """The specific hazard a bare adverb would have opened."""
    for text in (
        "I already have an expression matrix and motif priors.",
        "I have just the expression matrix, no PPI yet.",
        "We already hold RNA-Seq data for these patients.",
    ):
        scopes = {scope for clause, scope in _scoped_clauses(text) if clause.strip()}
        assert scopes == {"current"}, text


def test_a_declared_current_input_survives_the_wider_vocabulary():
    """Scoping decides which inputs count, so this is the consequence that matters."""
    mentions = input_mentions(
        "I already finished my PANDA run last month. Now I have a somatic "
        "mutation matrix for the same patients."
    )
    current = {item.artifact for item in mentions if item.status == "current"}

    assert "mutation_matrix" in current


def test_a_completed_run_is_history_and_a_bare_adverb_is_not():
    """The markers are verb-bound; these two sentences differ only in that."""
    finished = dict(
        (scope, clause) for clause, scope in _scoped_clauses(
            "I already finished my PANDA run last month."
        ) if clause.strip()
    )
    owned = dict(
        (scope, clause) for clause, scope in _scoped_clauses(
            "I already downloaded nothing yet and have my matrix."
        ) if clause.strip()
    )

    assert "historical" in finished
    assert "historical" not in owned
