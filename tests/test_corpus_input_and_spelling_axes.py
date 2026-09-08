"""The corpus must contain requests a real user would actually send.

The twenty original prompts share two properties no real request has: every
content word is spelled correctly, and every one of them states which inputs the
user already holds. A condition the corpus never contains is a condition the
corpus can never fail on, so both were invisible -- while a reported hard failure
(`Semantic routing unavailable`) turned on a single transposed letter, and the
deterministic input witnesses turn out to be just as spelling-brittle.

These tests keep the two axes present and readable. They do not assert that any
case passes: what a live round scores on them is the measurement, not a contract.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from evaluate_routing import DEFAULT_SCENARIOS, load_scenarios  # noqa: E402
from netzoo_agent_core.interpretation.request_integrity import (  # noqa: E402
    confirmed_current_inputs,
)

# Each pair is one prompt and its misspelled twin. Nothing but spelling differs,
# so a difference in outcome between the two rows is attributable to spelling.
MISSPELLED_PAIRS = (
    ("mirna-current-goal", "mirna-current-goal-misspelled"),
    ("aggregate-tf-baseline", "aggregate-tf-baseline-misspelled"),
    ("mutation-paraphrase-en", "mutation-paraphrase-misspelled"),
)


def corpus():
    return {case.id: case for case in load_scenarios(DEFAULT_SCENARIOS)}


def test_both_real_user_conditions_are_present_in_the_corpus():
    categories = {case.category for case in corpus().values()}

    assert {"misspelling", "terse"} <= categories


def test_the_reported_hard_failure_is_in_the_corpus_verbatim():
    """`regualtor` and `toosl`: the transposition the whole finding rests on."""
    prompt = corpus()["mirna-misspelled-no-inputs"].prompt

    assert "regualtor" in prompt and "toosl" in prompt


def test_a_typo_never_changes_the_answer_key():
    """Both rows of a pair ask for the same result; only the typing differs.

    If a misspelled row were allowed its own expectation, the pair would stop
    measuring spelling and start measuring two different questions.
    """
    cases = corpus()

    for base, misspelled in MISSPELLED_PAIRS:
        assert cases[misspelled].expected == cases[base].expected, base
        assert cases[misspelled].prompt != cases[base].prompt, base
        assert cases[misspelled].language == cases[base].language, base


def test_each_misspelled_prompt_actually_defeats_a_deterministic_witness():
    """Otherwise the pair is a spelling change the pipeline never notices.

    `confirmed_current_inputs` matches on surface form, so a typo in the word
    naming the input silences it -- and a silenced witness is what forces the
    model to ground that input by quotation instead. This is the mechanism the
    misspelling rows exist to exercise; a pair that does not reach it would
    quietly measure nothing.
    """
    cases = corpus()

    for base, misspelled in MISSPELLED_PAIRS:
        assert confirmed_current_inputs(cases[base].prompt), base
        assert not confirmed_current_inputs(cases[misspelled].prompt), misspelled


def test_no_terse_case_states_what_the_user_already_has():
    """The property that makes the row terse, checked by the production witness."""
    terse = [case for case in corpus().values() if case.category == "terse"]

    assert terse
    for case in terse:
        assert not confirmed_current_inputs(case.prompt), case.id
        assert case.expected.input_artifacts == [], case.id
        assert len(case.prompt) <= 120, case.id


def test_a_terse_request_that_really_is_underdetermined_expects_a_question():
    """Without it, "the terse rows improved" cannot be told from "the system

    became readier to guess". A cohort TF network fits four capabilities and the
    short form names nothing that separates them.
    """
    control = corpus()["terse-tf-cohort"]

    assert control.expected.status == "ambiguous"
    assert control.expected.require_clarification
    assert control.expected.actions == []
