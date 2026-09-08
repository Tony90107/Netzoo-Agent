"""One instruction that could never have worked should not cost the whole repair.

A patch reply carries evidence additions -- the repair -- alongside removals.
Two malformed shapes rejected the entire reply, additions included, and together
they were the whole schema-level residual of a matched-control round: 5 trials
whose removal named a dimension outside the closed vocabulary, and 6 whose
evidence list appeared both at the root and nested inside `outcome` with
different contents, out of 14 failures in 36.

Neither instruction could have had an effect. A removal names one
(dimension, value) to withdraw; naming a dimension that does not exist matches
nothing, so honouring it and ignoring it are the same act. And the nested copy
is an accommodation for providers that put it there, not a second source of
truth, so when the two disagree the field the contract declares is the one it
meant.

What must not follow from that is a general tolerance. A malformed *addition* is
the repair itself failing and stays strict; a well-formed removal still takes
effect; and nothing is dropped without being recorded. Each of those is pinned
below, because they are what separate this from relaxing the contract.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.graph.router_invocation import _as_semantic_patch  # noqa: E402


def payload(**overrides) -> dict:
    base = {
        "hypothesis_index": 0,
        "request_mode": "guidance",
        "semantic_goal": "Infer a per-sample miRNA regulatory network",
        "outcome": {},
        "evidence_additions": [
            {"dimension": "regulator_type", "value": "mirna", "source": "inferred",
             "rationale": "The request names miRNA regulators."},
        ],
        "evidence_removals": [],
    }
    base.update(overrides)
    return base


# --- a removal that names nothing ---------------------------------------------


def test_a_removal_naming_no_dimension_is_set_aside_and_the_repair_survives():
    patch, ignored = _as_semantic_patch(payload(evidence_removals=[
        {"dimension": "regulator types", "value": "mirna"},
    ]))

    assert patch is not None, "the addition was lost to an inert instruction"
    assert [item.value for item in patch.evidence_additions] == ["mirna"]
    assert patch.evidence_removals == []
    assert ignored == [{"reason": "removal_names_no_dimension",
                        "field": "evidence_removals"}]


def test_a_well_formed_removal_still_takes_effect():
    """The scope guard. Without it this would be a licence to ignore removals."""
    patch, ignored = _as_semantic_patch(payload(evidence_removals=[
        {"dimension": "granularity", "value": "aggregate"},
    ]))

    assert patch is not None
    assert [(item.dimension, item.value) for item in patch.evidence_removals] == [
        ("granularity", "aggregate"),
    ]
    assert ignored == []


def test_a_malformed_addition_still_rejects_the_patch():
    """An addition that names no dimension is the repair failing, not an inert
    instruction, and must not be quietly discarded.
    """
    patch, _ = _as_semantic_patch(payload(evidence_additions=[
        {"dimension": "regulator types", "value": "mirna", "source": "inferred",
         "rationale": "The request names miRNA regulators."},
    ]))

    assert patch is None


# --- the same list in two places, disagreeing ---------------------------------


def test_a_nested_list_that_disagrees_is_set_aside_for_the_declared_field():
    patch, ignored = _as_semantic_patch(payload(
        evidence_removals=[{"dimension": "granularity", "value": "aggregate"}],
        outcome={"evidence_removals": [
            {"dimension": "operation", "value": "infer"},
        ]},
    ))

    assert patch is not None, "the whole reply was rejected over a duplicate list"
    assert [(item.dimension, item.value) for item in patch.evidence_removals] == [
        ("granularity", "aggregate"),
    ]
    assert ignored == [{"reason": "nested_list_disagreed",
                        "field": "evidence_removals"}]


def test_a_nested_list_that_agrees_is_still_accepted_silently():
    """It was already accepted, and it is not a disagreement to report."""
    removals = [{"dimension": "granularity", "value": "aggregate"}]
    patch, ignored = _as_semantic_patch(payload(
        evidence_removals=removals, outcome={"evidence_removals": list(removals)},
    ))

    assert patch is not None
    assert len(patch.evidence_removals) == 1
    assert ignored == []


def test_a_nested_list_with_no_root_counterpart_is_still_lifted():
    """The existing accommodation, unchanged: nesting alone is not a conflict."""
    patch, ignored = _as_semantic_patch({
        "hypothesis_index": 0, "request_mode": "guidance",
        "semantic_goal": "Infer a per-sample miRNA regulatory network",
        "outcome": {
            "evidence_removals": [{"dimension": "granularity", "value": "aggregate"}],
        },
    })

    assert patch is not None
    assert [(item.dimension, item.value) for item in patch.evidence_removals] == [
        ("granularity", "aggregate"),
    ]
    assert ignored == []
