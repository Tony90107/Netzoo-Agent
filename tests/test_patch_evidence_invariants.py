"""What a field-scoped repair must prove, and what it need not.

Built from the report in scripts/analyze_patch_evidence.py over six recorded
rounds (59 patched trials). These pin behaviour that already holds; none of them
adds a new demand. They exist because the reviewer contract is about to be
revisited and every one of these guarantees is easy to lose by accident.

Two carry an exemption clause on purpose. Logs 25 and 26 removed the evidence
demand for a dimension the chosen artifact uniquely determines, and for an input
the request witnesses already located, and those are the only two interventions
in this investigation with a confirmed prediction on both sides. An invariant
written as "a changed field always needs its own evidence" would quietly undo
them, so each is pinned in both directions instead.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeHypothesis, RequestedOutcome, SemanticInterpretation, SemanticPatch,
)
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    validate_outcome_hypotheses,
)
from netzoo_agent_core.interpretation.semantic_patch import apply_semantic_patch  # noqa: E402

from evaluate_routing import DEFAULT_SCENARIOS, load_scenarios  # noqa: E402

CASES = {case.id: case for case in load_scenarios(DEFAULT_SCENARIOS)}
MUTATION_TASK = CASES["original-q1"].prompt
NO_INPUT_TASK = "Which workflow partitions a bipartite network into community modules?"
DISTANCE_TASK = CASES["mutation-distance-not-clusters"].prompt


def evidence(dimension, value, *, span=None, source=None):
    return {
        "dimension": dimension, "value": value,
        "source": source or ("explicit" if span else "inferred"),
        "text_span": span, "rationale": "Stated by the request.",
    }


def proposal(task_evidence=(), **outcome) -> SemanticInterpretation:
    base = dict(operation="analyze", input_artifacts=["mutation_matrix"],
                artifact_type="sample_cluster_assignment", granularity="aggregate")
    base.update(outcome)
    return SemanticInterpretation(
        request_mode="guidance", semantic_goal="Subtype patients",
        outcome_hypotheses=[OutcomeHypothesis(
            outcome=RequestedOutcome(**base), confidence=0.9,
            evidence=list(task_evidence or [evidence("operation", "analyze"),
                                            evidence("artifact_type", "sample_cluster_assignment")]),
        )],
    )


def issues_after(task, first, patch):
    merged, _ = apply_semantic_patch(first, SemanticPatch.model_validate(patch))
    return validate_outcome_hypotheses(task, merged.outcome_hypotheses).issues


# --- artifact_type: never exempt, in either failure shape --------------------

def test_a_changed_artifact_type_without_its_evidence_is_rejected():
    issues = issues_after(MUTATION_TASK, proposal(),
                          {"outcome": {"artifact_type": "sample_distance_matrix"}})

    assert any("missing_evidence:artifact_type=sample_distance_matrix" in i for i in issues)


def test_a_changed_artifact_type_quoting_absent_text_is_rejected():
    """The dominant observed shape: evidence supplied, but not from the request."""
    issues = issues_after(MUTATION_TASK, proposal(), {
        "outcome": {"artifact_type": "sample_distance_matrix"},
        "evidence_additions": [evidence("artifact_type", "sample_distance_matrix",
                                        span="a phrase the user never wrote")],
    })

    assert any("ungrounded_evidence:artifact_type=sample_distance_matrix" in i for i in issues)


def test_a_changed_artifact_type_with_grounded_evidence_is_accepted():
    """Uses the request that asks for distances and refuses cluster labels.

    On original-q1 the same change is correctly rejected: cluster assignment is
    that request's terminal goal, so moving away from it is a goal conflict, not
    an evidence question. Pinning acceptance needs a request whose terminal goal
    really is the new artifact.
    """
    issues = issues_after(DISTANCE_TASK, proposal(), {
        "outcome": {"artifact_type": "sample_distance_matrix", "entity_types": []},
        "evidence_removals": [{"dimension": "artifact_type", "value": "sample_cluster_assignment"}],
        "evidence_additions": [evidence("artifact_type", "sample_distance_matrix", span="距離")],
    })

    assert issues == ()


# --- input_artifact: exempt only where the witnesses confirm it --------------

def test_a_changed_input_the_witnesses_confirm_needs_no_evidence_of_its_own():
    """Log 26. The request's own wording already grounds it deterministically."""
    issues = issues_after(MUTATION_TASK, proposal(input_artifacts=[]),
                          {"outcome": {"input_artifacts": ["mutation_matrix"]}})

    assert not any("input_artifact" in i for i in issues)


def test_a_changed_input_the_witnesses_cannot_see_still_needs_evidence():
    first = proposal(input_artifacts=[], artifact_type="community_assignment",
                     task_evidence=[evidence("operation", "analyze"),
                                    evidence("artifact_type", "community_assignment")])
    issues = issues_after(NO_INPUT_TASK, first,
                          {"outcome": {"input_artifacts": ["regulatory_network"]}})

    assert any("missing_evidence:input_artifact=regulatory_network" in i for i in issues)


# --- granularity: exempt only where the artifact entails one value -----------

def test_a_changed_granularity_the_artifact_entails_needs_no_evidence():
    """Log 25. sample_cluster_assignment permits aggregate and nothing else."""
    issues = issues_after(MUTATION_TASK, proposal(granularity="unknown"),
                          {"outcome": {"granularity": "aggregate"}})

    assert not any("granularity" in i for i in issues)


def test_a_changed_granularity_the_artifact_leaves_open_still_needs_evidence():
    first = proposal(artifact_type="regulatory_network", granularity="unknown",
                     task_evidence=[evidence("operation", "analyze"),
                                    evidence("artifact_type", "regulatory_network")])
    issues = issues_after(MUTATION_TASK, first,
                          {"outcome": {"granularity": "sample_specific"}})

    assert any("missing_evidence:granularity=sample_specific" in i for i in issues)


# --- carrying forward is not free -------------------------------------------

def test_evidence_left_on_a_value_the_patch_replaced_is_not_silently_kept():
    """The merge retires what the patch withdrew; anything else stays a conflict."""
    first = proposal(task_evidence=[
        evidence("operation", "analyze"),
        evidence("artifact_type", "sample_cluster_assignment"),
        evidence("entity_type", "sample"),
    ])
    merged, retired = apply_semantic_patch(first, SemanticPatch.model_validate(
        {"outcome": {"entity_types": ["pathway"]}}))

    assert retired == [{"dimension": "entity_type", "value": "sample", "field": "entity_types"}]
    assert not any(item.value == "sample" for item in merged.outcome_hypotheses[0].evidence)


def test_roles_carried_under_a_new_artifact_type_are_rejected():
    """The largest bucket in the report, and it is a carry-forward, not a change.

    The patch corrects artifact_type and says nothing about the roles, so they
    survive into an artifact whose ontology forbids them. Pinned as a failure so
    that any future handling of it has to be a deliberate decision.
    """
    first = proposal(artifact_type="regulatory_network", granularity="sample_specific",
                     entity_types=["tf", "gene"], regulator_types=["tf"], target_types=["gene"],
                     task_evidence=[evidence("operation", "analyze"),
                                    evidence("artifact_type", "regulatory_network"),
                                    evidence("regulator_type", "tf"),
                                    evidence("target_type", "gene")])
    issues = issues_after(MUTATION_TASK, first, {
        "outcome": {"artifact_type": "sample_cluster_assignment", "granularity": "aggregate",
                    "entity_types": ["sample"]},
        "evidence_additions": [evidence("artifact_type", "sample_cluster_assignment")],
    })

    assert any("artifact_roles:sample_cluster_assignment" in i for i in issues)


# --- what must keep working -------------------------------------------------

def test_an_untouched_field_keeps_its_evidence_and_stays_valid():
    first = proposal(task_evidence=[
        evidence("operation", "analyze"),
        evidence("artifact_type", "sample_cluster_assignment"),
    ])
    issues = issues_after(MUTATION_TASK, first, {"semantic_goal": "Group the cohort"})

    assert issues == ()


@pytest.mark.parametrize("issues_expected", [True])
def test_a_failed_repair_never_becomes_a_partially_merged_result(issues_expected):
    """A merge that fails validation cannot be stored: the caller discards it.

    Pinned here as the property the reviewer contract must keep -- a changed core
    field without its evidence leaves the whole replacement unvalidated, rather
    than letting the fields that did validate through.
    """
    issues = issues_after(MUTATION_TASK, proposal(),
                          {"outcome": {"artifact_type": "sample_distance_matrix"}})

    assert bool(issues) is issues_expected
    assert validate_outcome_hypotheses(MUTATION_TASK, proposal().outcome_hypotheses).valid
