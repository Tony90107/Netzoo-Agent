"""A method the requester named is a fact about the request, and it needs a home.

Measured before this existed (Log 127, six trials of one request): the repair
scope worked, five of six readings passed validation, and none of the six routed
to PANDA. The outcome vocabulary had no field for "the user named PANDA", so the
model translated that fact into the dimensions it did have -- `granularity` came
back `sample_specific` where PANDA is aggregate, `input_artifacts` came back
holding output network types -- and those translations are what left the match
unable to separate PANDA from LIONESS-PANDA and PUMA. The system then asked which
one, a question the requester had already answered.

More restriction could not fix that. The field is the fix, and it is split three
ways so that no part of it is a keyword rule: the model asserts that the request
names a method and quotes it, including the judgement of whether the mention is
current work or finished work; the contract checks only that the quote is in the
request and contains the label; the registry says what the method produces, so
the model never has to guess a dimension the request did not state.

The tests below are the checking half. What makes them a gate rather than a
lookup is that they can only ever reject: nothing here writes the field.
"""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import (  # noqa: E402
    OutcomeEvidence, OutcomeHypothesis, RequestedOutcome,
)
from netzoo_agent_core.contracts.repair_scope import permitted_fields  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    validate_outcome_hypotheses,
)
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402

TASK = (
    "Run PANDA using these local files:\n"
    "expression_file=/work/expression.tsv\n"
    "motif_file=/work/motif.tsv\n"
    "ppi_file=/work/ppi.tsv"
)


def reading(*, methods=("PANDA",), granularity="unknown", cite=True,
            source="explicit", span="Run PANDA",
            operation_span="Run PANDA using these local files"):
    evidence = [
        OutcomeEvidence(dimension="operation", value="infer", source="explicit",
                        text_span=operation_span,
                        rationale="The request asks for a network to be built."),
        OutcomeEvidence(dimension="artifact_type", value="regulatory_network",
                        source="inferred",
                        rationale="A regulatory network is the requested result."),
    ]
    if cite:
        evidence += [
            OutcomeEvidence(dimension="named_method", value=method, source=source,
                            text_span=span if source == "explicit" else None,
                            rationale="The request writes the method out.")
            for method in methods
        ]
    if granularity not in {"unknown", "not_applicable"}:
        evidence.append(OutcomeEvidence(
            dimension="granularity", value=granularity, source="inferred",
            rationale="Stated for the test.",
        ))
    return [OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="infer", artifact_type="regulatory_network",
            granularity=granularity, named_methods=list(methods),
        ),
        confidence=0.9, evidence=evidence,
    )]


def codes(hypotheses, task=TASK):
    return [str(issue) for issue in validate_outcome_hypotheses(task, hypotheses).issues]


# --- the claim has to be quoted ----------------------------------------------


def test_a_named_method_with_no_evidence_at_all_is_rejected():
    assert any("missing_evidence:named_method=PANDA" in c for c in codes(reading(cite=False)))


def test_an_inferred_named_method_is_rejected():
    """Reporting what the user wrote is not something that can be inferred."""
    assert any("unquoted_named_method:PANDA" in c for c in codes(reading(source="inferred")))


def test_a_quote_that_does_not_contain_the_label_is_rejected():
    """The span is in the request, and still does not support this claim."""
    assert any(
        "unquoted_named_method:PANDA" in c
        for c in codes(reading(span="these local files"))
    )


def test_a_method_the_request_never_mentions_cannot_be_claimed():
    """The two checks together: the quote must be in the request *and* name it."""
    for span in ("Run PUMA", "Run PANDA using these local files"):
        assert codes(reading(methods=("PUMA",), span=span)), span


def test_a_properly_quoted_claim_is_accepted():
    assert codes(reading()) == []


def test_a_compound_label_is_recognised_however_it_is_typed():
    task = "Please run lioness panda on my three files"
    assert codes(
        reading(methods=("LIONESS-PANDA",), span="run lioness panda",
                operation_span="run lioness panda on my three files"),
        task=task,
    ) == []


# --- the registry, not the model, answers for the method ---------------------


def test_asserting_what_the_named_method_cannot_produce_is_rejected():
    """PANDA infers one aggregate network; `sample_specific` is a guess."""
    issues = validate_outcome_hypotheses(
        TASK, reading(granularity="sample_specific")
    ).issues

    assert any("named_method_conflict:PANDA.granularity" in str(i) for i in issues)


def test_that_rejection_opens_the_contradicting_field_and_nothing_else():
    """The quote was checked, so the name is not the part in doubt."""
    issues = validate_outcome_hypotheses(
        TASK, reading(granularity="sample_specific")
    ).issues

    assert permitted_fields(issues) == {"granularity"}


def test_an_unknown_dimension_is_left_unknown_rather_than_filled_in():
    """The capability answers at match time; it is never written into the outcome."""
    hypotheses = reading(granularity="unknown")

    assert validate_outcome_hypotheses(TASK, hypotheses).valid
    assert hypotheses[0].outcome.granularity == "unknown"
    assert match_semantic_request(
        TASK, hypotheses, request_mode="execute"
    ).matched_actions == ["run_panda"]


# --- what the match does with it ---------------------------------------------


def test_one_named_method_decides_the_match():
    match = match_semantic_request(TASK, reading(), request_mode="execute")

    assert match.status == "exact"
    assert match.matched_actions == ["run_panda"]
    assert match.match_basis == "named_method"


def test_two_named_methods_are_a_question_and_stay_ambiguous():
    """Naming two is not a fact to act on, and this must not answer it."""
    match = match_semantic_request(
        "Run PANDA and PUMA on these files",
        reading(methods=("PANDA", "PUMA"), span="Run PANDA and PUMA"),
        request_mode="execute",
    )

    assert match.status == "ambiguous"
    assert match.matched_actions == []


def test_no_code_path_fills_the_field_in():
    """The architectural limit: this is a claim to check, never one to make.

    The request writes PANDA out plainly. Nothing may read that and populate the
    field on the model's behalf -- validation and matching only ever see what the
    reading asserted.
    """
    silent = [OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="infer", artifact_type="regulatory_network",
            granularity="unknown", named_methods=[],
        ),
        confidence=0.9,
        evidence=[OutcomeEvidence(
            dimension="operation", value="infer", source="explicit",
            text_span="Run PANDA using these local files", rationale="x",
        )],
    )]

    validate_outcome_hypotheses(TASK, silent)
    match_semantic_request(TASK, silent, request_mode="execute")

    assert silent[0].outcome.named_methods == []
    assert match_semantic_request(
        TASK, silent, request_mode="execute"
    ).match_basis != "named_method"
