"""The narrow, authorized case where the deterministic layer writes a field.

`missing_current_input` was the largest single issue in the live record on both
models -- 28 occurrences on one round, 27 on another -- and it names an artifact
the request's own witnesses located and scoped as current while the outcome
omitted it. The model usually knows: it cites the same artifact in evidence and
leaves the field empty, which then also raises `conflicting_evidence`.

The value restored here comes from those witnesses, not from the model's free
text. The validator already trusts them enough to waive the evidence
requirement for a confirmed input, and it is the same call that raises the issue
being removed. Everything else is unchanged: no role field is written, nothing
is removed, and the merged outcome faces the identical strict validation.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402
from netzoo_agent_core.interpretation.stated_field_restoration import (  # noqa: E402
    restore_stated_fields,
)
from netzoo_agent_core.interpretation.request_integrity import (  # noqa: E402
    request_integrity_issues,
)

CURRENT = "Now I have a gene expression matrix, TF motif priors and PPI data. Which workflow infers a per-patient regulatory network?"
HISTORICAL = "Previously I used a somatic mutation matrix. That analysis is finished. Which workflow infers a per-patient regulatory network?"


def interpretation(*, cites="expression_matrix", **outcome):
    """A hypothesis that cites an input in evidence but may omit the field."""
    body = {
        "operation": "infer",
        "input_artifacts": [],
        "artifact_type": "regulatory_network",
        "granularity": "sample_specific",
        **outcome,
    }
    evidence = [
        {
            "dimension": "input_artifact",
            "value": cites,
            "source": "inferred",
            "rationale": "The request supplies this dataset.",
        }
    ] if cites else []
    return SemanticInterpretation.model_validate({
        "request_mode": "guidance",
        "semantic_goal": "Infer per-patient networks",
        "outcome_hypotheses": [
            {"outcome": body, "confidence": 0.9, "evidence": evidence}
        ],
    })


def test_a_witnessed_current_input_is_restored_and_reported():
    result, restored = restore_stated_fields(CURRENT, interpretation())

    assert result.outcome_hypotheses[0].outcome.input_artifacts == ["expression_matrix"]
    assert [item["value"] for item in restored] == ["expression_matrix"]
    assert restored[0]["field"] == "input_artifacts"
    # The witness's own span is carried, so the record says what it read.
    assert restored[0]["witnessed_span"]


def test_restoring_removes_the_issue_it_was_written_for():
    before = request_integrity_issues(CURRENT, interpretation().outcome_hypotheses[0].outcome)
    result, _ = restore_stated_fields(CURRENT, interpretation())
    after = request_integrity_issues(CURRENT, result.outcome_hypotheses[0].outcome)

    assert "missing_current_input:expression_matrix" in before
    assert not [issue for issue in after if issue.startswith("missing_current_input")]


def test_a_hypothesis_that_never_cited_the_input_is_not_repaired():
    """The invariant this must not remove: omitting a stated input still fails.

    Two independent sources have to agree. The witness alone is not enough, or a
    model that never read the request would be handed the answer, and fifteen
    tests written to guard exactly that would be silently rewritten.
    """
    result, restored = restore_stated_fields(CURRENT, interpretation(cites=None))

    assert result.outcome_hypotheses[0].outcome.input_artifacts == []
    assert restored == []
    assert "missing_current_input:expression_matrix" in request_integrity_issues(
        CURRENT, result.outcome_hypotheses[0].outcome,
    )


def test_a_cited_input_the_request_does_not_witness_is_not_restored():
    """The other direction: the model's word alone is not enough either."""
    result, restored = restore_stated_fields(
        HISTORICAL, interpretation(cites="expression_matrix"),
    )

    assert result.outcome_hypotheses[0].outcome.input_artifacts == []
    assert restored == []


def test_a_historical_mention_is_never_restored():
    """Log 41's failure class cannot arrive here: past clauses are not current."""
    result, restored = restore_stated_fields(
        HISTORICAL, interpretation(cites="mutation_matrix"),
    )

    assert result.outcome_hypotheses[0].outcome.input_artifacts == []
    assert restored == []


def test_an_artifact_the_outcome_already_names_is_not_duplicated():
    source = interpretation(input_artifacts=["expression_matrix"])

    result, restored = restore_stated_fields(CURRENT, source)

    assert result.outcome_hypotheses[0].outcome.input_artifacts == ["expression_matrix"]
    assert restored == []


def test_unknown_is_never_added():
    result, _ = restore_stated_fields(
        "Which workflow should I use?", interpretation(cites="unknown"),
    )

    assert result.outcome_hypotheses[0].outcome.input_artifacts == []


def test_artifact_alignment_resolves_a_uniquely_entailed_unknown():
    source = SemanticInterpretation.model_validate({
        "request_mode": "guidance",
        "semantic_goal": "Subtype patients",
        "outcome_hypotheses": [{
            "outcome": {
                "operation": "analyze",
                "input_artifacts": ["mutation_matrix"],
                "artifact_type": "sample_cluster_assignment",
                "entity_types": ["sample"],
                "granularity": "unknown",
                "unresolved_dimensions": ["granularity"],
            },
            "confidence": 0.9,
            "evidence": [{
                "dimension": "artifact_type",
                "value": "sample_cluster_assignment",
                "source": "inferred",
                "rationale": "The requested result is a patient subtype assignment.",
            }],
        }],
    })

    result, restored = restore_stated_fields(
        "Subtype patients from a mutation matrix.",
        source,
        align_artifact_constraints=True,
    )

    outcome = result.outcome_hypotheses[0].outcome
    assert outcome.granularity == "aggregate"
    assert outcome.unresolved_dimensions == []
    assert [(item["field"], item["source"]) for item in restored] == [
        ("granularity", "artifact_ontology"),
    ]


def test_a_full_input_list_is_left_alone_rather_than_overflowed():
    """The field is bounded at four; re-validation refuses, nothing raises."""
    full = interpretation(input_artifacts=[
        "regulatory_network", "coexpression_network", "multi_omic_network",
        "community_assignment",
    ])

    result, restored = restore_stated_fields(CURRENT, full)

    assert len(result.outcome_hypotheses[0].outcome.input_artifacts) == 4
    assert restored == []


def test_nothing_else_about_the_outcome_changes():
    result, _ = restore_stated_fields(CURRENT, interpretation())
    before = interpretation().outcome_hypotheses[0].outcome.model_dump()
    after = result.outcome_hypotheses[0].outcome.model_dump()

    assert {k: v for k, v in after.items() if k != "input_artifacts"} == {
        k: v for k, v in before.items() if k != "input_artifacts"
    }


def role_interpretation(evidence, **outcome):
    body = {
        "operation": "infer",
        "input_artifacts": ["expression_matrix"],
        "artifact_type": "regulatory_network",
        "granularity": "sample_specific",
        **outcome,
    }
    return SemanticInterpretation.model_validate({
        "request_mode": "guidance",
        "semantic_goal": "Infer per-patient networks",
        "outcome_hypotheses": [{
            "outcome": body,
            "confidence": 0.9,
            "evidence": [
                {"dimension": d, "value": v, "source": "inferred",
                 "rationale": "Stated by the request."}
                for d, v in evidence
            ],
        }],
    })


def test_a_role_stated_in_evidence_is_moved_into_its_field():
    """The gpt-4o shape: 22 occurrences of a role cited but not carried."""
    source = role_interpretation(
        [("regulator_type", "mirna"), ("target_type", "gene")],
        entity_types=["mirna", "gene"],
    )

    result, restored = restore_stated_fields(CURRENT, source)
    outcome = result.outcome_hypotheses[0].outcome

    assert outcome.regulator_types == ["mirna"]
    assert outcome.target_types == ["gene"]
    assert {item["field"] for item in restored} == {"regulator_types", "target_types"}
    # Roles have no independent witness, so none is claimed for them.
    assert all(item["witnessed_span"] is None for item in restored)


def test_a_role_no_evidence_states_is_never_invented():
    source = role_interpretation([("target_type", "gene")], entity_types=["gene"])

    result, _ = restore_stated_fields(CURRENT, source)

    assert result.outcome_hypotheses[0].outcome.regulator_types == []


def test_a_move_that_would_create_a_new_consistency_issue_is_reverted():
    """`role_entity` fires when a role is not among the declared entity types.

    Trading `conflicting_evidence` for `role_entity` repairs nothing, so the
    move is dropped rather than applied.
    """
    source = role_interpretation(
        [("regulator_type", "tf")], entity_types=["gene"],
    )

    result, restored = restore_stated_fields(CURRENT, source)

    assert result.outcome_hypotheses[0].outcome.regulator_types == []
    assert restored == []


def test_a_value_outside_the_closed_vocabulary_cannot_be_written():
    """Re-validation, not model_copy: an invalid literal is refused structurally."""
    source = role_interpretation(
        [("regulator_type", "protein")], entity_types=["gene", "protein"],
    )

    result, restored = restore_stated_fields(CURRENT, source)

    assert result.outcome_hypotheses[0].outcome.regulator_types == []
    assert restored == []


def test_unknown_is_never_moved_into_a_role_field():
    source = role_interpretation([("regulator_type", "unknown")])

    result, _ = restore_stated_fields(CURRENT, source)

    assert result.outcome_hypotheses[0].outcome.regulator_types == []


def test_a_selection_tag_stated_in_evidence_is_moved_and_reported_as_such():
    """The largest remaining conflict family, and the one with a coupling.

    The report has to name the moved tag so the caller can keep it out of
    capability selection.
    """
    source = role_interpretation([("selection_tag", "mirna_regulation")])

    result, restored = restore_stated_fields(CURRENT, source)

    assert result.outcome_hypotheses[0].outcome.selection_tags == ["mirna_regulation"]
    assert [(item["field"], item["value"]) for item in restored] == [
        ("selection_tags", "mirna_regulation"),
    ]


def test_roles_made_illegal_by_the_artifact_are_cleared():
    """The deletion half: a non-regulatory artifact has no legal role.

    `artifact_roles` was 28 occurrences on the cheaper model. Clearing cannot
    invent anything -- there is no legal value here to preserve -- which is why
    it is the safest of the three authorized acts.
    """
    source = role_interpretation(
        [], artifact_type="sample_cluster_assignment", granularity="aggregate",
        regulator_types=["tf"], target_types=["gene"], entity_types=["sample"],
        input_artifacts=["mutation_matrix"], operation="analyze",
    )

    result, restored = restore_stated_fields(CURRENT, source)
    outcome = result.outcome_hypotheses[0].outcome

    assert outcome.regulator_types == [] and outcome.target_types == []
    assert [(item["field"], item["source"]) for item in restored] == [
        ("roles", "stale_under_artifact"),
    ]


def test_roles_on_a_regulatory_artifact_are_left_alone():
    source = role_interpretation(
        [("regulator_type", "mirna")], entity_types=["mirna", "gene"],
        regulator_types=["mirna"],
    )

    result, restored = restore_stated_fields(CURRENT, source)

    assert result.outcome_hypotheses[0].outcome.regulator_types == ["mirna"]
    assert restored == []
