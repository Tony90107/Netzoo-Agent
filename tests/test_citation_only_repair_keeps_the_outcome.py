"""Being asked for a citation is not permission to change the value.

`missing_evidence` says a dimension's value has no supporting entry. It does not
say the value is wrong -- other codes say that, and say which dimension:
`conflicting_evidence`, `artifact_granularity`, `role_entity`,
`terminal_goal_conflict`. Asked only for citations, the review rewrote the whole
outcome in 14 of 24 recorded patches and added `entity_types=["sample"]` on the
way, which raised `role_entity` 38 times across 36 trials and is this study's
only recorded cause of a wrong tool recommendation.

Measured on a matched control that fixes the model's first pass and varies only
this code: repair rate 2/36 -> 22/36, one-sided Fisher exact p = 3.1e-7, with
`role_entity` going 38 -> 0 and no new issue family appearing.

The model's behaviour did not change -- 18 of 25 candidate patches still rewrite
nine or more fields. What changed is that those overrides are no longer applied.
The tests below pin that boundary, and the scope limit that keeps it from
blocking a correction the rejection actually asked for.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    SemanticInterpretation, SemanticPatch,
)
from netzoo_agent_core.interpretation.semantic_patch import (  # noqa: E402
    apply_semantic_patch, evidence_only_repair,
)


def proposal() -> SemanticInterpretation:
    """A reading whose roles carry no evidence -- the class under measurement."""
    return SemanticInterpretation.model_validate({
        "request_mode": "guidance",
        "semantic_goal": "Infer a per-sample miRNA regulatory network",
        "outcome_hypotheses": [{
            "outcome": {
                "operation": "infer", "input_artifacts": ["expression_matrix"],
                "artifact_type": "regulatory_network", "entity_types": [],
                "regulator_types": ["mirna"], "target_types": ["gene"],
                "granularity": "sample_specific",
            },
            "confidence": 0.9,
            "evidence": [
                {"dimension": "operation", "value": "infer", "source": "inferred",
                 "rationale": "The request asks for a network to be built."},
            ],
        }],
    })


def rewriting_patch() -> SemanticPatch:
    """What the review actually returns: the citations, plus a whole new outcome.

    `entity_types=["sample"]` is the part that matters. It is what the review
    added unprompted, and what `role_entity` then rejects for a regulatory
    network, whose entities are its regulator and target roles.
    """
    return SemanticPatch.model_validate({
        "request_mode": "guidance",
        "semantic_goal": "Infer a per-sample miRNA regulatory network",
        "hypothesis_index": 0,
        "outcome": {
            "entity_types": ["sample"],
            "granularity": "aggregate",
            "artifact_type": "coexpression_network",
        },
        "evidence_additions": [
            {"dimension": "regulator_type", "value": "mirna", "source": "inferred",
             "rationale": "The request names miRNA regulators."},
            {"dimension": "target_type", "value": "gene", "source": "inferred",
             "rationale": "Regulatory networks in this registry target genes."},
        ],
        "evidence_removals": [],
    })


# --- which rejections count as citation-only ---------------------------------


def test_a_rejection_naming_only_missing_evidence_is_citation_only():
    assert evidence_only_repair((
        "hypothesis[0].missing_evidence:regulator_type=mirna",
        "hypothesis[0].missing_evidence:target_type=gene",
    ))


def test_any_other_code_alongside_it_is_not():
    """Those codes do say a value is wrong, so the review must stay free to fix it."""
    for other in (
        "hypothesis[0].role_entity:regulatory_network",
        "hypothesis[0].artifact_granularity:coexpression_network",
        "hypothesis[0].conflicting_evidence:granularity=aggregate",
        "hypothesis[0].terminal_goal_conflict:sample_cluster_assignment",
    ):
        assert not evidence_only_repair((
            "hypothesis[0].missing_evidence:regulator_type=mirna", other,
        )), other


def test_an_empty_rejection_is_not_citation_only():
    """Nothing was asked, so nothing licenses suppressing anything."""
    assert not evidence_only_repair(())


# --- what the merge does with it ---------------------------------------------


def test_the_citations_are_applied_and_the_rewrite_is_not():
    merged, _ = apply_semantic_patch(proposal(), rewriting_patch(), evidence_only=True)
    outcome = merged.outcome_hypotheses[0].outcome

    # The reading the first pass gave, untouched.
    assert outcome.entity_types == []
    assert outcome.granularity == "sample_specific"
    assert outcome.artifact_type == "regulatory_network"
    # And the entries it was actually asked for.
    assert {(item.dimension, item.value) for item in merged.outcome_hypotheses[0].evidence} == {
        ("operation", "infer"), ("regulator_type", "mirna"), ("target_type", "gene"),
    }


def test_the_same_patch_still_changes_the_outcome_when_the_rejection_was_not_citation_only():
    """The scope limit. Without it this would block corrections that were asked for."""
    merged, _ = apply_semantic_patch(proposal(), rewriting_patch(), evidence_only=False)
    outcome = merged.outcome_hypotheses[0].outcome

    assert outcome.entity_types == ["sample"]
    assert outcome.granularity == "aggregate"
    assert outcome.artifact_type == "coexpression_network"


def test_suppressing_the_rewrite_is_what_removes_the_role_entity_rejection():
    """The mechanism the live result attributes its effect to, checked directly.

    `role_entity` fires because a regulatory network's entities must be its
    roles, and the review added `sample`. Dropping the override is what makes
    the merged reading valid; keeping it is what made 38 of 36 trials' attempt-2
    rejections that code.
    """
    from netzoo_agent_core.contracts.artifact_semantics import outcome_consistency_issues

    rewritten, _ = apply_semantic_patch(proposal(), rewriting_patch(), evidence_only=False)
    citations, _ = apply_semantic_patch(proposal(), rewriting_patch(), evidence_only=True)

    assert outcome_consistency_issues(rewritten.outcome_hypotheses[0].outcome)
    assert not outcome_consistency_issues(citations.outcome_hypotheses[0].outcome)


def test_a_citation_only_repair_ignores_withdrawals_too():
    """Nothing can have gone stale, so a withdrawal can only undo the repair.

    The outcome is untouched on this path, so every evidence entry still
    supports a value the outcome asserts. Applying a withdrawal there recreates
    the `missing_evidence` being repaired -- measured in 8 of 11 residual
    failures, where the review withdrew exactly the entries attempt 2 then
    reported missing while adding only the two roles it was asked for.
    """
    item = proposal()
    item.outcome_hypotheses[0].evidence.append(
        type(item.outcome_hypotheses[0].evidence[0]).model_validate({
            "dimension": "artifact_type", "value": "regulatory_network",
            "source": "inferred", "rationale": "The request describes a network.",
        })
    )
    patch = SemanticPatch.model_validate({
        "hypothesis_index": 0,
        "evidence_additions": [
            {"dimension": "regulator_type", "value": "mirna", "source": "inferred",
             "rationale": "The request names miRNA regulators."},
        ],
        # Exactly the shape observed: withdraw the first pass's own valid
        # entries while adding the roles.
        "evidence_removals": [
            {"dimension": "operation", "value": "infer"},
            {"dimension": "artifact_type", "value": "regulatory_network"},
        ],
    })

    kept, _ = apply_semantic_patch(item, patch, evidence_only=True)
    dropped, _ = apply_semantic_patch(item, patch, evidence_only=False)

    kept_pairs = {(e.dimension, e.value) for e in kept.outcome_hypotheses[0].evidence}
    dropped_pairs = {(e.dimension, e.value) for e in dropped.outcome_hypotheses[0].evidence}

    # Citation-only: the first pass's entries survive and the role is added.
    assert ("operation", "infer") in kept_pairs
    assert ("artifact_type", "regulatory_network") in kept_pairs
    assert ("regulator_type", "mirna") in kept_pairs
    # The scope guard: elsewhere a withdrawal still withdraws.
    assert ("operation", "infer") not in dropped_pairs
    assert ("artifact_type", "regulatory_network") not in dropped_pairs
