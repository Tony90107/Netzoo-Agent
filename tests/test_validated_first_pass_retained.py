"""A failed review must not discard an interpretation that already validated.

Live full-corpus run: `bipartite-communities` produced a first pass that passed
every evidence, consistency and request-integrity check, and the review that
followed did not. The run then fell back with no workflow at all, so a validated
reading was replaced by a registry guess that named nothing.

The reviewer is a second opinion, not a precondition. When it fails, the first
opinion still satisfies the same validator, and keeping it is strictly better
than discarding both. Nothing is filled in: the retained outcome is the one the
model produced and the validator accepted.
"""
from copy import deepcopy
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import IntentDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402

from evaluate_routing import DEFAULT_SCENARIOS, evaluate, load_scenarios  # noqa: E402
from test_routing_evaluation import hypothesis  # noqa: E402


def q1():
    return next(case for case in load_scenarios(DEFAULT_SCENARIOS) if case.id == "original-q1")


def good_item():
    item = hypothesis()
    for evidence in item["evidence"]:
        evidence.update(source="inferred", text_span=None)
    return item


def broken_item():
    """Internally inconsistent: a cluster assignment cannot be sample-specific."""
    item = good_item()
    item["outcome"]["granularity"] = "sample_specific"
    for evidence in item["evidence"]:
        if evidence["dimension"] == "granularity":
            evidence["value"] = "sample_specific"
    return item


class ScriptedProvider:
    def __init__(self, first, review):
        self.first, self.review = first, review
        self.calls = []

    def with_structured_output(self, schema, **_kwargs):
        provider = self

        class Adapter:
            def invoke(self, messages):
                provider.calls.append(schema)
                if schema is IntentDecision:
                    return {"mode": "answer", "confidence": 0.95, "reason": "Guidance only."}
                body = {"request_mode": "guidance", "semantic_goal": "Subtype patients"}
                if schema is SemanticInterpretation:
                    return {**body, "outcome_hypotheses": [deepcopy(provider.first)]}
                return {**body, "outcome_hypothesis": deepcopy(provider.review)}

        return Adapter()


def run(first, review):
    return evaluate([q1()], provider=ScriptedProvider(first, review),
                    model_name="fixture")["results"][0]


def test_a_validated_first_pass_survives_a_failed_review():
    row = run(good_item(), broken_item())

    assert row["status"] == "exact"
    assert row["matched_actions"] == ["run_sambar"]
    assert row["outcome"]["artifact_type"] == "sample_cluster_assignment"
    assert row["outcome"]["granularity"] == "aggregate"
    assert "intent_router" in row["call_roles"]


def test_the_discarded_review_is_still_reported():
    row = run(good_item(), broken_item())

    issues = [issue for entry in row["diagnostic_details"] for issue in entry["issues"]]
    assert any("artifact_granularity" in issue for issue in issues)


def test_a_successful_review_is_still_preferred():
    """The review remains the adjudicated result whenever it validates.

    The change has to be one the validator accepts; swapping the artifact for a
    distance matrix would conflict with the request's stated clustering goal and
    would therefore be discarded for the right reason, not this one.
    """
    reviewed = good_item()
    reviewed["outcome"]["display_entities"] = ["patient"]

    row = run(good_item(), reviewed)

    assert row["outcome"]["display_entities"] == ["patient"]
    assert row["status"] == "exact"


def test_two_failed_attempts_still_fall_back():
    row = run(broken_item(), broken_item())

    assert row["status"] == "fallback"
    assert row["outcome"] == {}
