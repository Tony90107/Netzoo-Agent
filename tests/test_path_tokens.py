"""Log 191: a folder called `bonobo-toy` does not name BONOBO."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeHypothesis,
    RequestedOutcome,
)
from netzoo_agent_core.interpretation.extraction import _needs_lioness_mode_choice  # noqa: E402
from netzoo_agent_core.routing.method_rejections import rejected_methods_for  # noqa: E402
from netzoo_agent_core.routing.named_labels import (  # noqa: E402
    named_registered_action,
    named_workflow_action,
    solely_named_run_action,
)
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402
from netzoo_agent_core.routing.path_tokens import is_path_token, without_path_tokens  # noqa: E402


@pytest.mark.parametrize("token", [
    "data/bonobo-toy/", "data/bonobo-toy/expression.tsv", "./panda/", "../otter-run/x",
    "/abs/giraffe", "~/cobra/", "prior-puma.tsv", "data/lioness-toy", "results/dragon.tsv.",
])
def test_paths_are_recognised(token):
    assert is_path_token(token)


@pytest.mark.parametrize("token", ["PANDA/PUMA", "TF/gene", "tumor/normal", "and/or", "LIONESS-PANDA", "BONOBO"])
def test_words_joined_by_a_slash_are_not_paths(token):
    assert not is_path_token(token)


def test_path_tokens_are_blanked_and_words_kept():
    text = "Run PANDA/PUMA on (data/bonobo-toy/expression.tsv) and `data/giraffe-toy/`."

    assert without_path_tokens(text) == "Run PANDA/PUMA on ( ) and ` `."


def test_a_path_alone_names_no_workflow():
    task = "I only have expression data (data/bonobo-toy/expression.tsv) and no prior files."

    assert named_registered_action(task) is None
    assert named_workflow_action(task) is None
    assert solely_named_run_action(task) is None


def test_a_name_written_outside_the_path_still_counts():
    task = "Run BONOBO on data/bonobo-toy/expression.tsv."

    assert named_registered_action(task) == "run_bonobo"
    assert solely_named_run_action(task) == "run_bonobo"


def test_an_empty_reading_is_not_answered_by_a_folder_name():
    unknown = RequestedOutcome(operation="unknown", artifact_type="unknown", granularity="unknown")
    task = "Run it on data/bonobo-toy/expression.tsv"

    match = match_semantic_request(
        task, [OutcomeHypothesis(outcome=unknown, confidence=0.5)], request_mode="execute",
    )

    assert match.match_basis != "workflow_name"
    assert "run_bonobo" not in match.matched_actions


def test_a_folder_name_is_not_a_mention_of_a_rejected_method():
    task = "Use the co-expression network in data/sambar-run/network.tsv."

    assert rejected_methods_for(task, ["coexpression_network"]) == []
    assert [item.action for item in rejected_methods_for(
        "Can SAMBAR use data/x/network.tsv?", ["coexpression_network"],
    )] == ["run_sambar"]


def test_a_lioness_folder_does_not_ask_which_lioness_mode():
    assert not _needs_lioness_mode_choice(
        "Use data/lioness-toy/ to build a regulatory network for each sample, then run a t-test."
    )
    assert _needs_lioness_mode_choice("Run LIONESS on data/study/.")
