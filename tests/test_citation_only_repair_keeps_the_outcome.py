"""Being asked for a citation is not permission to change the value.

`missing_evidence` says a dimension's value has no supporting entry. It does not
say the value is wrong -- other codes say that, and say which dimension:
`conflicting_evidence`, `artifact_granularity`, `role_entity`,
`terminal_goal_conflict`. Asked only for citations, the review rewrote the whole
outcome in 14 of 24 recorded patches and added `entity_types=["sample"]` on the
way, which raised `role_entity` 38 times across 36 trials and is this study's
only recorded cause of a wrong tool recommendation.

Measured on a matched control that fixes the model's first pass and varies only
this code: repair rate 2/36 -> 22/36, with `role_entity` going 38 -> 0 and no new
issue family appearing. The 38 -> 0 is what this file pins, because it is a
consequence of the code rather than of sampling. The score is not: a same-code
replicate of the final state later returned 24/36 against a recorded 35/36
(Log 120), which showed that three consecutive rounds share a drifting provider
state and are not independent samples, and every Fisher p value this design had
reported was withdrawn.

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
from netzoo_agent_core.contracts.repair_scope import permitted_fields  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    validate_outcome_hypotheses,
)
from netzoo_agent_core.interpretation.semantic_patch import (  # noqa: E402
    apply_semantic_patch,
)

TASK = "Infer a per-sample miRNA regulatory network from my expression matrix"


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


# --- which rejections license nothing in the outcome -------------------------
#
# There is no test here for a code's spelling any more. The scope comes from the
# rules that fired, which is why `missing_evidence` licenses an empty set: the
# rule that raises it examined the evidence list and no outcome field at all.


def test_a_rejection_naming_only_missing_evidence_licenses_no_outcome_field():
    issues = validate_outcome_hypotheses(TASK, proposal().outcome_hypotheses).issues

    assert issues and all(".missing_evidence:" in issue for issue in issues)
    assert permitted_fields(issues) == frozenset()


def test_a_rejection_about_the_outcome_licenses_the_fields_its_rule_read():
    """Those rules do say a value is wrong, so the review must stay free to fix it."""
    item = proposal()
    item.outcome_hypotheses[0].outcome.granularity = "not_applicable"

    issues = validate_outcome_hypotheses(TASK, item.outcome_hypotheses).issues

    assert any(".artifact_granularity:" in issue for issue in issues)
    assert permitted_fields(issues) >= {"granularity", "artifact_type"}


def test_an_empty_rejection_licenses_nothing_either():
    """Nothing was asked, so nothing licenses suppressing anything."""
    assert permitted_fields(()) == frozenset()


# --- what the merge does with it ---------------------------------------------


def test_the_citations_are_applied_and_the_rewrite_is_not():
    merged, _ = apply_semantic_patch(proposal(), rewriting_patch(), permitted_fields=frozenset())
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
    merged, _ = apply_semantic_patch(proposal(), rewriting_patch())
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

    rewritten, _ = apply_semantic_patch(proposal(), rewriting_patch())
    citations, _ = apply_semantic_patch(proposal(), rewriting_patch(), permitted_fields=frozenset())

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

    kept, _ = apply_semantic_patch(item, patch, permitted_fields=frozenset())
    dropped, _ = apply_semantic_patch(item, patch)

    kept_pairs = {(e.dimension, e.value) for e in kept.outcome_hypotheses[0].evidence}
    dropped_pairs = {(e.dimension, e.value) for e in dropped.outcome_hypotheses[0].evidence}

    # Citation-only: the first pass's entries survive and the role is added.
    assert ("operation", "infer") in kept_pairs
    assert ("artifact_type", "regulatory_network") in kept_pairs
    assert ("regulator_type", "mirna") in kept_pairs
    # The scope guard: elsewhere a withdrawal still withdraws.
    assert ("operation", "infer") not in dropped_pairs
    assert ("artifact_type", "regulatory_network") not in dropped_pairs
