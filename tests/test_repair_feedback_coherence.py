"""Repair feedback must describe the corrected outcome, never the rejected one.

A live gpt-4o run returned byte-identical output on both attempts. Its feedback
told it to set artifact_type to the terminal goal and, in the same message,
pinned `artifact_type` to `{"const": "unknown"}` -- because field constraints were
derived from the artifact that validation had just rejected. One issue in that
run, `inconsistent_not_applicable_outcome`, also had no repair branch at all.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.interpretation.semantic_repair import repair_feedback  # noqa: E402

from evaluate_routing import DEFAULT_SCENARIOS, load_scenarios  # noqa: E402
from test_routing_evaluation import FixtureProvider, hypothesis, run  # noqa: E402


GPT4O_ISSUES = (
    "hypothesis[0].missing_current_input:mutation_matrix",
    "hypothesis[0].terminal_goal_conflict:sample_cluster_assignment",
    "hypothesis[0].inconsistent_not_applicable_outcome",
    "hypothesis[0].conflicting_evidence:input_artifact=mutation_matrix",
)


def hedged_proposal(count=1):
    return {"outcome_hypotheses": [{
        "outcome": {"operation": "unknown", "artifact_type": "unknown",
                    "granularity": "not_applicable"},
        "confidence": 0.6, "evidence": [],
    } for _ in range(count)]}


def q1():
    return next(case for case in load_scenarios(DEFAULT_SCENARIOS) if case.id == "original-q1")


def test_no_entry_pins_the_artifact_that_validation_rejected():
    entries = repair_feedback(hedged_proposal(), GPT4O_ISSUES, q1().prompt)

    for entry in entries:
        constraints = entry["expected"].get("field_constraints", {})
        assert constraints.get("artifact_type") != {"const": "unknown"}, entry["issue"]


def test_every_entry_describes_the_corrected_terminal_artifact():
    entries = repair_feedback(hedged_proposal(), GPT4O_ISSUES, q1().prompt)

    for entry in entries:
        assert entry["expected"]["field_constraints"]["artifact_type"] == {
            "const": "sample_cluster_assignment"
        }, entry["issue"]


def test_an_unresolvable_artifact_supplies_no_constraints_at_all():
    """Nothing to constrain toward is better than pinning the rejected value."""
    entries = repair_feedback(
        hedged_proposal(),
        ("hypothesis[0].inconsistent_not_applicable_outcome",),
        q1().prompt,
    )

    assert "field_constraints" not in entries[0]["expected"]


def test_a_corrected_artifact_applies_only_to_its_own_hypothesis():
    entries = repair_feedback(
        hedged_proposal(2),
        ("hypothesis[1].terminal_goal_conflict:sample_cluster_assignment",
         "hypothesis[0].inconsistent_not_applicable_outcome"),
        q1().prompt,
    )

    by_issue = {entry["issue"]: entry["expected"] for entry in entries}
    assert "field_constraints" not in by_issue["hypothesis[0].inconsistent_not_applicable_outcome"]
    assert by_issue["hypothesis[1].terminal_goal_conflict:sample_cluster_assignment"][
        "field_constraints"]["artifact_type"] == {"const": "sample_cluster_assignment"}


def test_a_hedged_outcome_is_told_the_request_does_describe_a_result():
    expected = repair_feedback(
        hedged_proposal(),
        ("hypothesis[0].inconsistent_not_applicable_outcome",),
        q1().prompt,
    )[0]["expected"]

    assert expected["action"] == "replace_not_applicable_outcome"
    assert expected["review_path"] == "outcome_hypothesis.outcome"
    instruction = expected["instruction"].casefold()
    assert "no scientific result at all" in instruction
    assert "guidance" in instruction


@pytest.mark.parametrize("case_id", ["original-q1", "original-q2", "original-q3"])
def test_production_routing_never_sends_a_contradictory_constraint(case_id):
    item = hypothesis()
    item["outcome"].update(operation="unknown", artifact_type="unknown", granularity="not_applicable")
    item["outcome"]["input_artifacts"] = []
    # entity_types stays filled, so this is not the canonical empty outcome:
    # a hedged not_applicable is exactly what the live gpt-4o run returned.
    provider = FixtureProvider(
        first={"request_mode": "guidance", "semantic_goal": "Cluster patients",
               "outcome_hypotheses": [item]},
    )

    run(provider, next(c for c in load_scenarios(DEFAULT_SCENARIOS) if c.id == case_id))
    message = provider.calls[1][1][-1].content

    assert '"const": "unknown"' not in message
    assert "replace_not_applicable_outcome" in message


def test_repair_never_directs_content_into_a_field_that_voids_the_match():
    """`match_semantic_request` treats any assumption as an interpretive guess.

    A live run produced the gold Q1 outcome and still lost its exact match. The
    terminal-goal instruction had told the reviewer to record the intermediate
    artifact's relationship in `assumptions`, and one assumption is enough to
    disqualify an exact match. Related artifacts are already rendered from the
    registry in the final answer, so the instruction must not ask for them here.
    """
    expected = repair_feedback(
        hedged_proposal(),
        ("hypothesis[0].terminal_goal_conflict:sample_cluster_assignment",),
        q1().prompt,
    )[0]["expected"]

    instruction = expected["instruction"].casefold()
    assert "retain their relationship in assumptions" not in instruction
    assert "do not add assumptions" in instruction
    assert expected["artifact_type"] == "sample_cluster_assignment"


def test_the_report_counts_assumptions_so_a_voided_match_is_visible():
    from evaluate_routing import evaluate

    item = hypothesis()
    item["assumptions"] = ["Clustering follows pathway aggregation."]
    for evidence in item["evidence"]:
        evidence.update(source="inferred", text_span=None)
    provider = FixtureProvider(
        first={"request_mode": "guidance", "semantic_goal": "g", "outcome_hypotheses": [item]},
        review={"request_mode": "guidance", "semantic_goal": "g", "outcome_hypothesis": item},
    )

    row = evaluate([q1()], provider=provider, model_name="fixture")["results"][0]

    assert row["assumption_count"] == 1


def test_one_assumption_turns_the_gold_outcome_into_an_advisory_candidate():
    """Directly reproduces the live Q1 result and pins the coupling being avoided."""
    from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis
    from netzoo_agent_core.routing.outcome_matching import match_semantic_request

    gold = {
        "outcome": {"operation": "analyze", "input_artifacts": ["mutation_matrix"],
                    "artifact_type": "sample_cluster_assignment",
                    "entity_types": ["sample"], "granularity": "aggregate"},
        "confidence": 0.95,
        "evidence": [{"dimension": dimension, "value": value, "source": "inferred",
                      "rationale": "Entailed by the stated goal."}
                     for dimension, value in (
                         ("operation", "analyze"), ("input_artifact", "mutation_matrix"),
                         ("artifact_type", "sample_cluster_assignment"),
                         ("entity_type", "sample"), ("granularity", "aggregate"))],
    }
    task = q1().prompt

    without = match_semantic_request(
        task, [OutcomeHypothesis.model_validate({**gold, "assumptions": []})],
        request_mode="unknown",
    )
    with_one = match_semantic_request(
        task,
        [OutcomeHypothesis.model_validate({**gold, "assumptions": ["Clustering follows aggregation."]})],
        request_mode="unknown",
    )

    # The guard still refuses `exact`. Since option C, a single assumed candidate
    # is surfaced as registry guidance instead of an unanswerable question; see
    # tests/test_assumed_outcome_guidance.py.
    assert without.status == "exact" and without.matched_actions == ["run_sambar"]
    assert with_one.status == "fallback" and with_one.match_basis == "assumed_outcome"
    assert with_one.matched_actions == ["run_sambar"]


# Observed at 3 of 3 Q3 trials once the transport defect was gone: the second
# attempt kept a granularity the chosen artifact does not allow. Like
# `inconsistent_not_applicable_outcome` before it, the issue reached the reviewer
# with constraints but no stated action.
ARTIFACT_CONSISTENCY = {
    "artifact_granularity": ("granularity", ["aggregate", "unknown"]),
    "artifact_entity": ("entity_types", ["sample", "unknown"]),
}


@pytest.mark.parametrize("issue_code", sorted(ARTIFACT_CONSISTENCY), ids=sorted(ARTIFACT_CONSISTENCY))
def test_an_artifact_consistency_issue_states_its_action_and_allowed_values(issue_code):
    field, allowed = ARTIFACT_CONSISTENCY[issue_code]
    proposal = {"outcome_hypotheses": [{
        "outcome": {"operation": "analyze", "artifact_type": "sample_cluster_assignment",
                    "granularity": "sample_specific"},
        "confidence": 0.9, "evidence": [],
    }]}

    expected = repair_feedback(
        proposal, (f"hypothesis[0].{issue_code}:sample_cluster_assignment",), q1().prompt,
    )[0]["expected"]

    assert expected["action"] == "align_with_artifact_ontology"
    assert expected["review_path"] == f"outcome_hypothesis.outcome.{field}"
    assert expected["allowed_values"] == allowed
    instruction = expected["instruction"].casefold()
    assert "artifact_type" in instruction
    assert "evidence" in instruction


def test_the_named_artifact_owns_the_allowed_values_not_the_rejected_one():
    """The correction target decides what is allowed, as for field constraints."""
    proposal = {"outcome_hypotheses": [{
        "outcome": {"operation": "infer", "artifact_type": "multi_omic_network",
                    "granularity": "sample_specific"},
        "confidence": 0.9, "evidence": [],
    }]}

    expected = repair_feedback(
        proposal,
        ("hypothesis[0].terminal_goal_conflict:sample_cluster_assignment",
         "hypothesis[0].artifact_granularity:sample_cluster_assignment"),
        q1().prompt,
    )[1]["expected"]

    assert expected["allowed_values"] == ["aggregate", "unknown"]


def test_an_artifact_without_a_declared_restriction_states_no_allowed_values():
    proposal = {"outcome_hypotheses": [{
        "outcome": {"operation": "infer", "artifact_type": "regulatory_network",
                    "granularity": "aggregate"},
        "confidence": 0.9, "evidence": [],
    }]}

    expected = repair_feedback(
        proposal, ("hypothesis[0].artifact_entity:regulatory_network",), q1().prompt,
    )[0]["expected"]

    assert "allowed_values" not in expected
    assert expected["action"] == "align_with_artifact_ontology"
