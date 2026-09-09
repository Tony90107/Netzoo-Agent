"""A narrow rejection is not a licence to rewrite the outcome.

A request that named PANDA and three files was interpreted almost correctly --
`operation` infer and `artifact_type` regulatory_network, both with evidence --
and rejected on one field: `granularity` was `not_applicable`, which the ontology
refuses for a regulatory network. The review, asked to fix that, rewrote the
whole outcome and introduced failures the first pass did not have, including
`input_artifact=regulatory_network`. Both attempts failed and the user saw a
validation error. Reproduced 4 of 4 (Log 125).

The scope of a repair is now collected from the rules that fired rather than
parsed out of their codes. That distinction is the point: a table from code to
field list is read far from the check it describes and drifts from what the
check actually examines, and it makes the system act on the spelling of a code
instead of on the rule behind it. Each rule declares its scope beside the fields
it reads, and two parts are derived rather than declared -- the field behind an
evidence dimension, and the fields an ontology opens when `artifact_type`
legitimately changes.
"""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import (  # noqa: E402
    OutcomeEvidence, OutcomeHypothesis, RequestedOutcome,
)
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    SemanticInterpretation, SemanticPatch,
)
from netzoo_agent_core.contracts.repair_scope import (  # noqa: E402
    OUTCOME_FIELDS, permitted_fields,
)
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    validate_outcome_hypotheses,
)
from netzoo_agent_core.interpretation.semantic_patch import (  # noqa: E402
    apply_semantic_patch,
)

TASK = (
    "Run PANDA using these local files:\n"
    "expression_file=/work/expression.tsv\n"
    "motif_file=/work/motif.tsv\n"
    "ppi_file=/work/ppi.tsv"
)


def first_pass() -> SemanticInterpretation:
    """The reading a live round returns for that request, field for field."""
    return SemanticInterpretation.model_validate({
        "request_mode": "execute",
        "semantic_goal": "Run PANDA with specified local files.",
        "outcome_hypotheses": [{
            "outcome": {
                "operation": "infer", "input_artifacts": [],
                "artifact_type": "regulatory_network", "entity_types": [],
                "regulator_types": [], "target_types": [],
                "granularity": "not_applicable", "unresolved_dimensions": [],
            },
            "confidence": 0.9,
            "evidence": [
                {"dimension": "operation", "value": "infer", "source": "explicit",
                 "text_span": "Run PANDA using these local files",
                 "rationale": "The request asks for PANDA to be run."},
                {"dimension": "artifact_type", "value": "regulatory_network",
                 "source": "inferred",
                 "rationale": "PANDA produces a regulatory network."},
            ],
        }],
    })


def sprawling_patch() -> SemanticPatch:
    """What the review returns: the one field, plus a rewrite of everything else.

    `input_artifacts` holding output artifact names is the shape that actually
    appeared at attempt 2 and is what turned a one-field rejection into a failed
    round.
    """
    return SemanticPatch.model_validate({
        "hypothesis_index": 0,
        "outcome": {
            "granularity": "aggregate",
            "input_artifacts": ["regulatory_network", "multi_omic_network"],
            "entity_types": ["tf"],
            "regulator_types": ["tf"],
            "target_types": ["gene"],
        },
        "evidence_additions": [],
        "evidence_removals": [],
    })


# --- what the rejection licenses ---------------------------------------------


def test_the_ontology_rejection_licenses_only_the_pair_it_compared():
    issues = validate_outcome_hypotheses(TASK, first_pass().outcome_hypotheses).issues

    assert any(".artifact_granularity:" in issue for issue in issues)
    assert permitted_fields(issues) == {"granularity", "artifact_type"}


def test_every_issue_the_validator_raises_declares_a_scope():
    """Without this an added rule silently reverts to permitting everything."""
    readings = [
        first_pass().outcome_hypotheses,
        [OutcomeHypothesis(
            outcome=RequestedOutcome(
                operation="infer", artifact_type="regulatory_network",
                entity_types=["sample"], regulator_types=["tf"],
                target_types=["gene"], granularity="sample_specific",
            ),
            confidence=0.9,
            evidence=[OutcomeEvidence(
                dimension="granularity", value="sample_specific", source="explicit",
                text_span="nowhere in the request", rationale="x",
            )],
        )],
    ]
    for hypotheses in readings:
        issues = validate_outcome_hypotheses(TASK, hypotheses).issues
        assert issues
        for issue in issues:
            assert getattr(issue, "fields", None) is not None, issue


# --- what the merge does with it ---------------------------------------------


def test_the_licensed_field_is_applied_and_the_rest_of_the_rewrite_is_not():
    issues = validate_outcome_hypotheses(TASK, first_pass().outcome_hypotheses).issues

    merged, _ = apply_semantic_patch(
        first_pass(), sprawling_patch(), permitted_fields=permitted_fields(issues),
    )
    outcome = merged.outcome_hypotheses[0].outcome

    assert outcome.granularity == "aggregate"          # the field that was wrong
    assert outcome.input_artifacts == []               # never questioned
    assert outcome.entity_types == []
    assert outcome.regulator_types == []
    assert outcome.target_types == []


def test_an_unscoped_rejection_still_permits_the_whole_outcome():
    """The default, unchanged: nothing declared means nothing is withheld."""
    merged, _ = apply_semantic_patch(first_pass(), sprawling_patch())

    assert merged.outcome_hypotheses[0].outcome.entity_types == ["tf"]
    assert permitted_fields(("a bare string with no declaration",)) == OUTCOME_FIELDS


# --- the ontology opens what a corrected artifact governs ---------------------


def test_correcting_the_artifact_opens_the_fields_that_artifact_governs():
    """Derived from `ARTIFACT_SEMANTICS`, not from a list beside the issue code.

    `terminal_goal_conflict` reads `artifact_type` alone. If the review may only
    change that one field, the corrected artifact is left beside a granularity
    its own ontology forbids -- a rejection answered into a fresh rejection.
    """
    patch = SemanticPatch.model_validate({
        "hypothesis_index": 0,
        "outcome": {
            "artifact_type": "sample_cluster_assignment",
            "granularity": "aggregate",
            "entity_types": ["sample"],
            "regulator_types": ["tf"],
        },
        "evidence_additions": [], "evidence_removals": [],
    })

    merged, _ = apply_semantic_patch(
        first_pass(), patch, permitted_fields=frozenset({"artifact_type"}),
    )
    outcome = merged.outcome_hypotheses[0].outcome

    assert outcome.artifact_type == "sample_cluster_assignment"
    assert outcome.granularity == "aggregate"       # opened by the new ontology
    assert outcome.entity_types == ["sample"]       # opened by the new ontology
    assert outcome.regulator_types == []            # governed by neither, so shut


def test_a_withdrawal_outside_the_licence_does_not_take_effect():
    """Withdrawals follow the same scope; otherwise the licence has a back door."""
    patch = SemanticPatch.model_validate({
        "hypothesis_index": 0,
        "outcome": {"granularity": "aggregate"},
        "evidence_additions": [],
        "evidence_removals": [{"dimension": "operation", "value": "infer"}],
    })

    merged, _ = apply_semantic_patch(
        first_pass(), patch, permitted_fields=frozenset({"granularity", "artifact_type"}),
    )
    kept = {(e.dimension, e.value) for e in merged.outcome_hypotheses[0].evidence}

    assert ("operation", "infer") in kept
