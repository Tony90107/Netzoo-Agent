"""The one deliberate relaxation in the pipeline, and the fence around it.

A reading whose quotes cannot be found in the request used to be discarded
whole. That cost 148 of 188 such entries their entire run, and every one of a
round's twelve misspelled trials, while the reading itself was usually right --
a transposed letter makes a matching quote impossible, not the meaning unclear.

The reading is kept now. Everything that would let it pass for a verified one is
not: it can never be an exact match, never authorize an action, and never claim
to have been checked. It also cannot tell a typo from an invention, since both
are simply a quote the request does not contain, so those bounds are the whole
of the safety argument and each is pinned here.

Equally pinned is what did NOT change: a quote that adds a qualifier the request
never contained is still caught, and a reading with any other kind of problem is
still discarded entirely.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from evaluate_routing import RoutingScenario, evaluate  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeEvidence, OutcomeHypothesis, RequestedOutcome,
)
from netzoo_agent_core.interpretation.guidance_interaction import (  # noqa: E402
    guidance_interaction,
)
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    validate_outcome_hypotheses,
)
from test_routing_evaluation import FixtureProvider, hypothesis  # noqa: E402


TASK = "Which tool groups patients from somatic mutations using gene length normalization?"


def case() -> RoutingScenario:
    return RoutingScenario.model_validate({
        "id": "unverified-case", "language": "en", "category": "positive",
        "prompt": TASK,
        "expected": {
            "status": "exact", "actions": ["run_sambar"],
            "input_artifacts": ["mutation_matrix"],
            "artifact_type": "sample_cluster_assignment", "granularity": "aggregate",
        },
    })


def report_for(item):
    return evaluate(
        [case()],
        provider=FixtureProvider(
            first={"request_mode": "guidance", "semantic_goal": "Grouping",
                   "outcome_hypotheses": [item]},
            review={"request_mode": "guidance", "semantic_goal": "Grouping",
                    "outcome_hypothesis": item},
        ),
        model_name="fixture",
    )["results"][0]


def unquoted():
    """A reading whose only fault is quotes the request does not contain."""
    item = hypothesis()
    for entry in item["evidence"]:
        if entry["source"] == "explicit":
            entry["text_span"] = "wording that is not in the request"
    return item


# --- R1: which readings this applies to --------------------------------------


def test_a_reading_faulted_only_on_its_quotes_is_kept():
    row = report_for(unquoted())

    assert row["outcome"], "the reading was discarded, which is what this replaced"
    assert row["matched_actions"] == ["run_sambar"]


def test_a_reading_with_any_other_fault_is_still_discarded_whole():
    """The relaxation is for unlocatable quotes, not for incomplete readings.

    Here one dimension carries no evidence at all, so `missing_evidence` joins
    the ungrounded ones. That is not a citation the request happens to lack; it
    is a claim with nothing behind it, and it still costs the whole reading.
    """
    item = unquoted()
    item["evidence"] = [
        entry for entry in item["evidence"] if entry["dimension"] != "artifact_type"
    ]

    row = report_for(item)

    assert not row["outcome"]
    assert row["matched_actions"] == []


# --- R2: the bounds -----------------------------------------------------------


def test_a_kept_reading_can_never_present_itself_as_an_exact_match():
    row = report_for(unquoted())

    assert row["status"] == "fallback"
    assert row["match_basis"] == "unverified_evidence"


def test_a_kept_reading_can_never_authorize_an_action():
    row = report_for(unquoted())

    assert row["should_execute"] is False
    assert row["action"] == "no_tool"


def test_a_kept_reading_is_never_recorded_as_a_validated_interpretation():
    """The evaluation's semantic metric must not soften with the disposition."""
    row = report_for(unquoted())

    assert not row["semantic_passed"]
    assert "evidence_validation" in row["diagnostics"]


# --- R3: the negative control, which is where relaxing could become blindness --


def test_a_quote_that_adds_a_qualifier_the_request_lacks_is_still_caught():
    """The request says `network`; the quote says `regulatory network`.

    One word the user never wrote, and it is the word that would decide the
    reading. If this stops being reported, the change has stopped detecting the
    problem rather than responding to it differently -- and nothing else in this
    file would notice.
    """
    outcome = RequestedOutcome(
        operation="infer", artifact_type="regulatory_network",
        regulator_types=["mirna"], granularity="sample_specific",
    )
    item = OutcomeHypothesis(
        outcome=outcome, confidence=0.9,
        evidence=[
            OutcomeEvidence(
                dimension="artifact_type", value="regulatory_network",
                source="explicit", text_span="regulatory network",
                rationale="The user asked for a regulatory network.",
            ),
        ],
    )

    result = validate_outcome_hypotheses(
        "I want a per-sample miRNA network. Which tool?", [item],
    )

    assert any(
        "ungrounded_evidence:artifact_type=regulatory_network" in issue
        for issue in result.issues
    )


# --- R4: what the user is told ------------------------------------------------


def test_the_user_is_told_the_quotes_did_not_match_and_not_told_to_retry():
    """The message this replaces said routing was "unavailable" and advised

    retrying "when available", while routing had run twice and the wording it
    could not match was still in the request -- so an unchanged retry was
    certain to fail the same way.
    """
    row = report_for(unquoted())
    from netzoo_agent_core.contracts import TaskDecision

    interaction = guidance_interaction(TaskDecision.model_validate({
        **{key: row[key] for key in ("action", "should_execute", "match_basis")},
        "capability_match_status": row["status"],
        "in_scope": True, "confidence": 0.5, "reason": "unverified reading",
    }))

    assert interaction is not None
    text = interaction.explanation + " " + interaction.next_step
    assert "quote" in text.lower()
    assert "unavailable" not in text.lower()
    assert "retry" not in text.lower()
