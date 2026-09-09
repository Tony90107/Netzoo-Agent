"""Naming a registered method is a fact about the request, not a guess about it.

`Run PANDA using these three local files:` -- with three valid PANDA inputs
attached -- reached no workflow on every version measured: 6 of 6 trials on this
branch, 4 of 4 on `main`, and 4 of 4 on the 2026-09-07 commit that removed the
lexical fallback, most of those surfacing as the user-visible validation error
(Log 121).

The cause is that the outcome vocabulary has no dimension for a method name. The
interpreter's only self-consistent reading of a request that states a tool and
no scientific goal is every dimension `unknown` with `granularity` set to
`not_applicable` -- which is precisely how this system encodes "out of scope".
So `Run PANDA` was read as "NetZoo cannot do this", and it validated, because a
contract that checks whether asserted values are cited cannot object to a
reading that asserts nothing.

The narrow claim being pinned: **when the request asserts nothing else, an
explicitly written registered label is the only fact present, and it decides.**
That is a lookup, not the phrase-count guess removed in `15cbaad` -- the label
is matched on word boundaries against the registry after historical clauses are
stripped. The scope limits below are what keep the distinction real: a name in a
finished-work clause still loses, and a typed outcome that contradicts the name
still wins.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import (  # noqa: E402
    OutcomeEvidence, OutcomeHypothesis, RequestedOutcome,
)
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402

RUN_PANDA = (
    "Run PANDA using these three local files:\n"
    "/work/manual_tests/input_identification/random_names_valid/alpha_17.tsv\n"
    "/work/manual_tests/input_identification/random_names_valid/blue_note.csv\n"
    "/work/manual_tests/input_identification/random_names_valid/fragment_03.txt"
)


def nothing_interpreted() -> list[OutcomeHypothesis]:
    """The reading a live round actually returns for that request, verbatim.

    Recorded six times out of six: one hypothesis, every dimension unknown,
    `granularity` `not_applicable`, `unresolved_dimensions` empty, and a single
    explicit evidence entry citing the request in support of `operation` being
    unknown.
    """
    return [OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="unknown", input_artifacts=[], artifact_type="unknown",
            entity_types=[], display_entities=[], regulator_types=[],
            target_types=[], selection_tags=[], granularity="not_applicable",
            unresolved_dimensions=[],
        ),
        confidence=1.0,
        evidence=[OutcomeEvidence(
            dimension="operation", value="unknown", source="explicit",
            text_span="Run PANDA using these three local files",
            rationale="The user requests to run PANDA, which is an execution request.",
        )],
    )]


# --- N1: the defect ------------------------------------------------------------


def test_a_named_method_decides_when_the_reading_asserts_nothing():
    match = match_semantic_request(
        RUN_PANDA, nothing_interpreted(), request_mode="execute",
    )

    assert match.matched_actions == ["run_panda"], (
        "an explicitly named capability was discarded as out of scope"
    )
    assert match.status == "exact"
    assert match.match_basis == "workflow_name"


# --- N2: the name must still lose in a finished-work clause --------------------


def test_a_method_named_as_history_still_decides_nothing():
    """The guard that separates a lookup from a keyword grab.

    `_current_scope_text` drops historical clauses before the label is looked
    up, so a method the requester reports having already run is not a method
    they are asking for. A live round once recommended a forbidden PANDA to a
    request whose only mention of it was "Previously I used PANDA"; that is the
    failure this guard exists for.
    """
    task = (
        "Previously I used PANDA. Now I want to cluster patients by their "
        "somatic mutations."
    )

    match = match_semantic_request(task, nothing_interpreted(), request_mode="execute")

    assert match.matched_actions == []
    assert match.status == "not_applicable"


def test_a_finished_run_reported_without_the_old_markers_is_still_history():
    """The limit recorded in Log 122, now closed (Log 123/124).

    Clause scoping is a bounded lexical pass, and its history vocabulary was
    `previously`, `earlier`, `past`, `old` and their CJK equivalents. "I already
    finished my PANDA run last month" carried none of them, so a bare sentence
    reporting a finished run read as a live request to run it again. This test
    asserted that behaviour and said it would fail the day the vocabulary grew;
    it grew, and this is the reversed assertion.

    What the vocabulary gained is bound to a completion verb, never to a bare
    adverb, because a history hit overrides a current hit in the same clause and
    the same scoping decides which inputs count as present. `already` on its own
    would have read "I already have an expression matrix" as history and made a
    declared input disappear -- which the test below holds shut.
    """
    match = match_semantic_request(
        "I already finished my PANDA run last month.",
        nothing_interpreted(), request_mode="execute",
    )

    assert match.matched_actions == []
    assert match.status == "not_applicable"


def test_owning_something_already_is_not_reporting_it_finished():
    """The scope limit that makes the addition safe rather than merely wider."""
    match = match_semantic_request(
        "I already have an expression matrix and motif priors. Run PANDA.",
        nothing_interpreted(), request_mode="execute",
    )

    assert match.matched_actions == ["run_panda"]


def test_a_compound_label_is_not_two_labels():
    """`LIONESS-PANDA` contains `PANDA`; the inner span is an artefact."""
    match = match_semantic_request(
        "Run LIONESS-PANDA on these files", nothing_interpreted(),
        request_mode="execute",
    )

    assert match.matched_actions == ["run_lioness_panda"]


# --- N3: a stated outcome still outranks a name --------------------------------


def test_a_reading_that_asserts_something_is_not_overridden_by_the_name():
    """Unchanged behaviour, pinned because this change must not reach it.

    SAMBAR's output is a sample-by-pathway mutation summary, so a reading that
    asserts a per-sample regulatory network is incompatible with it. The name
    must not redefine what the request asked for.
    """
    stated = [OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="infer", input_artifacts=["expression_matrix"],
            artifact_type="regulatory_network", entity_types=["tf", "gene"],
            display_entities=["TF", "gene"], regulator_types=["tf"],
            target_types=["gene"], selection_tags=[], granularity="sample_specific",
            unresolved_dimensions=[],
        ),
        confidence=0.9,
        evidence=[OutcomeEvidence(
            dimension="artifact_type", value="regulatory_network", source="explicit",
            text_span="per-sample regulatory network",
            rationale="The request names the artifact.",
        )],
    )]

    match = match_semantic_request(
        "Run SAMBAR to get a per-sample regulatory network from my expression matrix",
        stated, request_mode="execute",
    )

    assert "run_sambar" not in match.matched_actions


def test_two_named_methods_decide_nothing():
    """One label is a fact; two are a question, and this must not answer it."""
    match = match_semantic_request(
        "Run PANDA and PUMA on these files", nothing_interpreted(),
        request_mode="execute",
    )

    assert match.matched_actions == []


def test_a_second_registered_label_of_any_kind_stops_the_lookup():
    """Counting only runnable labels was wrong, and this is how it showed.

    "Search the web with WEB-SEARCH for current PANDA references" names two
    registered labels. Only one of them is runnable, so a count restricted to
    runnable labels saw exactly one and ran PANDA -- turning a topic the
    requester wanted read about into a job, and taking the request away from the
    step they actually named.
    """
    match = match_semantic_request(
        "Search the web with WEB-SEARCH for current PANDA references.",
        nothing_interpreted(),
    )

    assert match.matched_actions == ["web_search"]
