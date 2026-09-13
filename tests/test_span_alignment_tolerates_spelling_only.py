"""A quote may be spelled differently from the request. It may not say more.

A request with a transposed letter used to make a correct quote impossible: the
model writes `regulator`, the user typed `regualtor`, nothing matches, and a
reading that was right is discarded whole. Every misspelled trial of a live
round was lost that way.

What makes this hard is that the obvious fix does not work. `network` ->
`regulatory network` is at least as similar as `regualtor` -> `regulator`, so a
similarity threshold loose enough to rescue the typo also admits a qualifier the
user never wrote -- and that qualifier is what picks the capability. The two
axes have to be separated structurally, not by a number.

The separation rests on four things, and each has its own tests below because
losing any one of them turns this into the threshold it was written to avoid:
alignment is word-by-word against a contiguous run, the distance allowed shrinks
with the word, two domain words are never each other's typo, and non-ASCII words
get no tolerance at all.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeEvidence, OutcomeHypothesis, RequestedOutcome,
)
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    _grounded_span, _normalized, validate_outcome_hypotheses,
)
from netzoo_agent_core.interpretation.span_alignment import aligned_span  # noqa: E402


#: The reported hard failure, verbatim: `regualtor` and `toosl` are transposed.
PHENOMENON_A = "if i want to get sample specific mi-rna regualtor network, what toosl do i need?"


def grounds(span: str, task: str) -> bool:
    return _grounded_span(_normalized(span), _normalized(task))


# --- A1: the failure this exists to fix ---------------------------------------


@pytest.mark.parametrize("span", [
    "regulator network", "tools", "sample specific", "mi-RNA",
])
def test_a_quote_spelled_correctly_finds_the_misspelled_request(span):
    assert grounds(span, PHENOMENON_A)


def test_the_reported_hard_failure_now_validates_end_to_end():
    """The whole reading, not just one quote: this is what used to be lost."""
    item = OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="infer", artifact_type="regulatory_network",
            regulator_types=["mirna"], granularity="sample_specific",
        ),
        confidence=0.9,
        evidence=[
            OutcomeEvidence(
                dimension=dimension, value=value, source="explicit",
                text_span=span, rationale="Stated by the user.",
            )
            for dimension, value, span in (
                ("operation", "infer", "regulator network"),
                ("artifact_type", "regulatory_network", "regulator network"),
                ("regulator_type", "mirna", "mi-rna"),
                ("granularity", "sample_specific", "sample specific"),
            )
        ],
    )

    result = validate_outcome_hypotheses(PHENOMENON_A, [item])

    assert not [issue for issue in result.issues if "ungrounded_evidence" in issue]


def test_terminal_hard_wrap_inside_ascii_words_does_not_unground_a_quote():
    """The CLI may receive pasted display wrapping as literal newlines."""
    task = (
        "我想從 expression matrix 中產生兩張 s\n"
        "ample-specific gene-gene co-expression ma\n"
        "trix，並且在 sparsify 後輸出 p-value matrix。"
    )
    item = OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="infer",
            input_artifacts=["expression_matrix"],
            artifact_type="coexpression_network",
            entity_types=["gene"],
            granularity="sample_specific",
        ),
        confidence=0.9,
        evidence=[
            OutcomeEvidence(
                dimension=dimension,
                value=value,
                source="explicit",
                text_span=span,
                rationale="Stated by the user.",
            )
            for dimension, value, span in (
                (
                    "operation",
                    "infer",
                    "產生兩張 sample-specific gene-gene co-expression matrix",
                ),
                ("input_artifact", "expression_matrix", "expression matrix"),
                (
                    "artifact_type",
                    "coexpression_network",
                    "sample-specific gene-gene co-expression matrix",
                ),
                ("granularity", "sample_specific", "sample-specific"),
            )
        ],
    )

    result = validate_outcome_hypotheses(task, [item])

    assert not [issue for issue in result.issues if "ungrounded_evidence" in issue]


@pytest.mark.parametrize(("misspelled", "correct"), [
    ("regualtor", "regulator"), ("toosl", "tools"), ("expresion", "expression"),
    ("priros", "priors"), ("workflwo", "workflow"), ("seperate", "separate"),
    ("pateint", "patient"), ("cohrot", "cohort"), ("standrad", "standard"),
    ("recomend", "recommend"), ("subgropus", "subgroups"), ("mutaiton", "mutation"),
    ("acount", "account"), ("biolgical", "biological"), ("explan", "explain"),
])
def test_every_misspelling_the_corpus_contains_is_reachable(misspelled, correct):
    """Otherwise the corpus rows measure nothing and would say so too late."""
    assert aligned_span(correct, f"the {misspelled} thing")


# --- A2: the negative control, where relaxing could become blindness ----------


def test_a_quote_that_adds_a_word_the_request_lacks_is_still_rejected():
    """The request says `network`; the quote says `regulatory network`.

    One word the user never wrote, and the word that would decide the reading.
    Every similarity-threshold version of this change passes the test above and
    fails this one, which is why the threshold approach was rejected.
    """
    assert not grounds(
        "regulatory network", "I want a per-sample miRNA network. Which tool?",
    )


def test_a_quote_whose_words_are_not_adjacent_in_the_request_is_rejected():
    """Alignment is to a run of words, not to a bag of them."""
    assert not grounds("sample network", "a sample specific miRNA network")


def test_a_quote_longer_than_the_request_cannot_align():
    assert not grounds("a much longer quote than this", "short request")


# --- A3: alignment only ever adds ---------------------------------------------


def test_no_quote_that_grounded_verbatim_stops_grounding():
    """Checked against every contiguous phrase of every corpus prompt.

    This is the property that makes the change safe to reason about at all: the
    new branch is consulted only after the old test fails, so the set of
    grounded quotes can grow but never shrink. It is asserted over real prompts
    rather than a handful of examples because the first draft did lose one --
    a Chinese quote, since a script without word delimiters normalizes to a
    single token that word alignment cannot read.
    """
    prompts = [
        case["prompt"] for case in
        json.loads(Path(__file__).with_name("routing_scenarios.json").read_text("utf-8"))
    ]
    checked = 0
    for prompt in prompts:
        task = _normalized(prompt)
        words = task.split()
        for start in range(len(words)):
            for end in range(start + 1, min(start + 5, len(words)) + 1):
                span = " ".join(words[start:end])
                left = r"(?<![a-z0-9])" if span[0].isascii() and span[0].isalnum() else ""
                right = r"(?![a-z0-9])" if span[-1].isascii() and span[-1].isalnum() else ""
                if re.search(left + re.escape(span) + right, task):
                    checked += 1
                    assert _grounded_span(span, task), span
    assert checked > 500, "the corpus sweep did not actually exercise anything"


def test_a_quote_inside_an_undelimited_script_still_grounds():
    """The case the first draft broke, kept as its own row."""
    assert grounds("分組", "請對病人做分組，先不用執行。")


# --- A4: two domain words are never each other's typo -------------------------


@pytest.mark.parametrize(("quote", "request_word"), [
    # One edit apart, different molecules, and they select different workflows.
    ("mirna", "mrna"),
    # TF activity estimation is not TF regulation.
    ("tfa", "tf"),
    ("tf", "tfa"),
    # Two edits apart on a long word, where the length rule alone would allow it.
    ("coexpression", "expression"),
    ("expression", "coexpression"),
])
def test_two_words_that_both_mean_something_here_must_match_exactly(quote, request_word):
    assert not aligned_span(quote, f"i have {request_word} data")


def test_a_domain_word_still_finds_its_own_misspelling():
    """The guard is about two meanings, not about protecting domain words.

    `expresion` means nothing in the ontology, so it is a typo of `expression`
    and must align -- otherwise the guard would undo the fix for every corpus
    row whose misspelled word happens to be a registry term.
    """
    assert aligned_span("expression matrix", "a cohrot gene expresion matrix")


# --- A5: tolerance is a latin-script idea -------------------------------------


def test_a_non_ascii_word_gets_no_tolerance():
    """`分組` and `分類` are also one edit apart, and mean different things."""
    assert not aligned_span("分組", "請對病人做 分類")


# --- the length rule ----------------------------------------------------------


@pytest.mark.parametrize(("quote", "request_word"), [
    ("tf", "of"), ("gene", "gone"), ("puma", "pump"),
])
def test_a_short_word_must_match_exactly(quote, request_word):
    """At four characters almost every other word is one edit away.

    The bound is on the longer of the two, so `gene`/`genes` still aligns --
    a plural is not a different concept. `gene`/`gone` and `puma`/`pump` are
    the same length, and there the rule admits nothing but identity.
    """
    assert not aligned_span(quote, f"i said {request_word} here")
