"""A registry tag may break a tie the scientific dimensions left standing.

`selection_tags` is defined by the contract, asked for by the prompt and checked
by the evidence validator, and the matcher never read it: `grep` found the name
nowhere under routing/. On a stronger model that became visible as a stable
failure -- one prompt expressed its only discriminator as a tag rather than as a
regulator role, and two equally compatible capabilities stayed tied with no
action at all, three trials out of three.

The contract also says tags "do not select or authorize a workflow by
themselves". So the rule tested here only chooses among candidates the stated
dimensions have already qualified, and can only shrink that set.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402

MIRNA_TASK = (
    "PANDA worked for our old aggregate TF analysis. With the current expression "
    "matrix and miRNA, motif and PPI priors, which workflow would estimate a "
    "separate miRNA-to-gene regulatory network for every patient? Please explain "
    "the choice only."
)
TF_TASK = (
    "Previously I used SAMBAR for somatic mutations. That analysis is finished. "
    "Now I have a gene expression matrix, TF motif priors and PPI data. Which "
    "workflow can infer a separate TF-to-gene regulatory network for each "
    "patient? Advice only."
)


def match(task, *, tags=(), artifact_type="regulatory_network", **overrides):
    outcome = {
        "operation": "infer",
        "input_artifacts": ["expression_matrix"],
        "artifact_type": artifact_type,
        "entity_types": [],
        "regulator_types": [],
        "target_types": [],
        "selection_tags": list(tags),
        "granularity": "sample_specific",
        **overrides,
    }
    hypothesis = OutcomeHypothesis.model_validate(
        {"outcome": outcome, "confidence": 0.9, "evidence": []}
    )
    return match_semantic_request(task, [hypothesis], request_mode="guidance")


def test_a_tag_carried_by_one_tied_candidate_selects_it():
    """The observed failure: roles empty, both LIONESS variants compatible."""
    result = match(MIRNA_TASK, tags=["mirna_regulation"])

    assert result.status == "exact"
    assert result.matched_actions == ["run_lioness_puma"]
    # Not "semantic": the registry catalogue resolved this, not the ontology.
    assert result.match_basis == "registry_features"


def test_the_same_outcome_without_a_tag_still_asks():
    result = match(MIRNA_TASK)

    assert result.status == "ambiguous"
    assert result.matched_actions == []


def test_a_tag_no_candidate_carries_changes_nothing():
    result = match(MIRNA_TASK, tags=["batch_correction"])

    assert result.status == "ambiguous"
    assert result.matched_actions == []


def test_a_tag_several_survivors_carry_changes_nothing():
    """`sample_specific` is on both LIONESS variants, so it settles nothing."""
    result = match(MIRNA_TASK, tags=["sample_specific"])

    assert result.status == "ambiguous"
    assert result.matched_actions == []


def test_a_tag_never_rescues_a_candidate_whose_stated_dimensions_differ():
    """The tag narrows an already-qualified set; it does not widen one.

    `mirna_regulation` belongs to capabilities producing a regulatory_network.
    An outcome that states a different artifact must not reach them through it.
    """
    result = match(MIRNA_TASK, tags=["mirna_regulation"],
                   artifact_type="coexpression_network")

    assert result.matched_actions != ["run_lioness_puma"]


@pytest.mark.xfail(
    reason=(
        "Accepted, recorded limitation: tags need no evidence, so a tag the "
        "request does not support still discriminates. Pinned so it cannot be "
        "forgotten. Sixteen of sixteen tags in the live record were catalogue "
        "entries naming the expected tool, and the live criterion vetoes on any "
        "wrong recommendation. See research log Log 58 and Log 60."
    ),
    strict=True,
)
def test_an_unsupported_tag_does_not_discriminate():
    """A TF-to-gene request carrying an invented miRNA tag should not pick PUMA."""
    result = match(TF_TASK, tags=["mirna_regulation"])

    assert result.matched_actions != ["run_lioness_puma"]
