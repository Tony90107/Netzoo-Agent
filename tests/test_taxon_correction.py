"""Answering a preflight that asked for the organism.

A gene-symbol axis cannot be validated without a species, so preflight stops
and asks for one. Two things had to be true for that to be answerable and
neither was: the message had to give the spelling that is actually parsed,
and the correction prompt had to accept it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core import TaskDecision, build_workflow_plan  # noqa: E402
from netzoo_agent_core.contracts import ClarificationInputError  # noqa: E402
from netzoo_agent_core.cli.clarification import (  # noqa: E402
    input_confirmation_continuation,
)

TASK = (
    "Run PANDA using data/official-toy/ToyExpressionData.txt, "
    "data/official-toy/ToyMotifData.txt, and "
    "data/official-toy/ToyPPIData.txt"
)


def _plan():
    return build_workflow_plan(
        TaskDecision(
            action="run_panda",
            in_scope=True,
            should_execute=True,
            confidence=1.0,
            reason="Run PANDA.",
        ),
        TASK,
    )


class TestTheCorrectionPromptAcceptsAnOrganism:
    @pytest.mark.parametrize(
        "answer, expected",
        [
            ("taxon=human", "human"),
            ("taxon=Homo sapiens", "Homo sapiens"),
            ("species=mouse", "mouse"),
            ("taxon=9606", "9606"),
        ],
    )
    def test_an_organism_alone_is_a_complete_answer(self, answer, expected):
        """The one correction the error asks for used to be the one refused."""
        continuation = input_confirmation_continuation(
            _plan(), answer, approved=False
        )

        assert f"taxon={expected};" in continuation

    def test_an_answer_naming_neither_is_still_refused(self):
        with pytest.raises(ClarificationInputError) as caught:
            input_confirmation_continuation(_plan(), "ok thanks", approved=False)

        # The refusal has to name both ways out, or it repeats the old trap.
        assert "field=path" in str(caught.value)
        assert "taxon=" in str(caught.value)

    def test_a_corrected_path_still_works_without_an_organism(self):
        continuation = input_confirmation_continuation(
            _plan(), "expression_file=data/other.tsv", approved=False
        )

        assert "CORRECTED_INPUT_expression_file=data/other.tsv;" in continuation

    def test_a_path_and_an_organism_can_be_given_together(self):
        continuation = input_confirmation_continuation(
            _plan(), "expression_file=data/other.tsv, taxon=human", approved=False
        )

        assert "CORRECTED_INPUT_expression_file=data/other.tsv;" in continuation
        assert "taxon=human;" in continuation

    def test_an_approved_answer_does_not_read_a_taxon_out_of_it(self):
        """Approval confirms the roles found; it is not a place to set controls."""
        continuation = input_confirmation_continuation(
            _plan(), "taxon=human", approved=True
        )

        assert "taxon=human;" not in continuation


def test_the_preflight_message_gives_the_spelling_that_is_parsed():
    """Saying "set taxon" invited prose, and prose is deliberately not read."""
    from netzoo_agent_core.interpretation.request_parameters import (
        extract_explicit_taxon,
    )
    from netzoo_agent_core.data import preflight

    source = Path(preflight.__file__).read_text(encoding="utf-8")
    start = source.index("cannot be verified without a species")
    message = source[start : start + 400]

    assert "taxon=human" in message
    # The advice must be advice the parser honours.
    assert extract_explicit_taxon("taxon=human") == "human"
    assert extract_explicit_taxon("taxon=Homo sapiens") == "Homo sapiens"
    assert extract_explicit_taxon("taxon=9606") == "9606"
