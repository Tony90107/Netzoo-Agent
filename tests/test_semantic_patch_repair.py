"""The review repairs named fields; it no longer retypes the whole structure.

Across 83 attempt-1/attempt-2 pairs in the live record the review introduced an
issue absent from attempt 1 in 71 of them. Twenty-two of those new issues were
`schema_validation` -- a missing `evidence.N.rationale`, a non-literal in
`input_artifacts` -- against 2 such issues it fixed. A schema error can never be
the consequence of a correct semantic repair, only of re-emitting a structure
that was already well formed, and the repair message had already been given the
permitted literals and the item type without effect.

So the review is asked for a delta. What it omits is carried forward from the
first pass verbatim; what it names is changed. Nothing is invented, nothing is
relaxed, and the merged interpretation faces the identical validator.
"""
from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import IntentDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    SemanticInterpretation, SemanticPatch,
)
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    validate_outcome_hypotheses,
)
from netzoo_agent_core.interpretation.semantic_patch import apply_semantic_patch  # noqa: E402

from evaluate_routing import DEFAULT_SCENARIOS, evaluate, load_scenarios  # noqa: E402
from test_routing_evaluation import hypothesis  # noqa: E402


def q1():
    return next(case for case in load_scenarios(DEFAULT_SCENARIOS) if case.id == "original-q1")


def q3():
    return next(case for case in load_scenarios(DEFAULT_SCENARIOS) if case.id == "original-q3")


def grounded_item():
    item = hypothesis()
    for evidence in item["evidence"]:
        evidence.update(source="inferred", text_span=None)
    return item


def proposal_of(item) -> SemanticInterpretation:
    return SemanticInterpretation.model_validate({
        "request_mode": "guidance",
        "semantic_goal": "Subtype patients",
        "outcome_hypotheses": [deepcopy(item)],
    })


class PatchProvider:
    """Scripted transport whose second semantic reply is a patch, not a rewrite."""

    def __init__(self, first, patch):
        self.first, self.patch = first, patch
        self.schemas = []

    def with_structured_output(self, schema, **_kwargs):
        provider = self

        class Adapter:
            def invoke(self, _messages):
                provider.schemas.append(schema.__name__)
                if schema is IntentDecision:
                    return {"mode": "answer", "confidence": 0.95, "reason": "Guidance only."}
                if schema is SemanticInterpretation:
                    return {"request_mode": "guidance", "semantic_goal": "Subtype patients",
                            "outcome_hypotheses": [deepcopy(provider.first)]}
                return deepcopy(provider.patch)

        return Adapter()


def missing_input_item():
    """The most common live first-pass defect: the current input is not listed."""
    item = grounded_item()
    item["outcome"]["input_artifacts"] = []
    item["evidence"] = [e for e in item["evidence"] if e["dimension"] != "input_artifact"]
    return item


def test_the_second_semantic_call_asks_for_a_patch_when_the_first_pass_parsed():
    provider = PatchProvider(missing_input_item(), {"outcome": {"input_artifacts": ["mutation_matrix"]}})

    row = evaluate([q1()], provider=provider, model_name="fixture")["results"][0]

    assert provider.schemas == ["SemanticInterpretation", "SemanticPatch", "IntentDecision"]
    assert row["status"] == "exact"
    assert row["outcome"]["input_artifacts"] == ["mutation_matrix"]


def test_fields_the_patch_does_not_name_survive_verbatim():
    base = grounded_item()
    proposal = proposal_of(missing_input_item())
    patch = SemanticPatch.model_validate({"outcome": {"input_artifacts": ["mutation_matrix"]}})

    merged, retired = apply_semantic_patch(proposal, patch)
    outcome = merged.outcome_hypotheses[0].outcome

    assert outcome.input_artifacts == ["mutation_matrix"]
    assert outcome.artifact_type == base["outcome"]["artifact_type"]
    assert outcome.operation == base["outcome"]["operation"]
    assert outcome.granularity == base["outcome"]["granularity"]
    assert merged.semantic_goal == proposal.semantic_goal
    assert retired == []


def test_an_empty_patch_endorses_the_first_pass_and_is_still_judged_by_it():
    """Omission means "this was right", so a wrong first pass stays wrong."""
    proposal = proposal_of(missing_input_item())

    merged, _ = apply_semantic_patch(proposal, SemanticPatch())
    result = validate_outcome_hypotheses(q1().prompt, merged.outcome_hypotheses)

    assert merged.outcome_hypotheses[0].outcome == proposal.outcome_hypotheses[0].outcome
    assert not result.valid
    assert any("missing_current_input:mutation_matrix" in issue for issue in result.issues)


def test_evidence_the_patch_does_not_name_is_kept_as_written():
    proposal = proposal_of(grounded_item())
    patch = SemanticPatch.model_validate({"semantic_goal": "Cluster the cohort"})

    merged, _ = apply_semantic_patch(proposal, patch)

    assert merged.outcome_hypotheses[0].evidence == proposal.outcome_hypotheses[0].evidence
    assert merged.semantic_goal == "Cluster the cohort"


def test_a_withdrawn_evidence_entry_is_removed_and_a_replacement_is_added():
    proposal = proposal_of(grounded_item())
    original = proposal.outcome_hypotheses[0].evidence[0]
    patch = SemanticPatch.model_validate({
        "evidence_removals": [{"dimension": original.dimension, "value": original.value}],
        "evidence_additions": [{
            "dimension": original.dimension, "value": original.value,
            "source": "inferred", "rationale": "Restated from the scientific goal.",
        }],
    })

    merged, _ = apply_semantic_patch(proposal, patch)
    evidence = merged.outcome_hypotheses[0].evidence

    assert sum(item.dimension == original.dimension for item in evidence) == 1
    assert evidence[-1].rationale == "Restated from the scientific goal."


def test_evidence_the_patch_itself_made_stale_is_retired_and_reported():
    """A changed dimension retires only evidence naming the value it withdrew.

    That entry describes a claim the review just took back, so keeping it could
    only report a merge artifact. It is returned to the caller, never dropped in
    silence, and the required-evidence check still runs on what remains.
    """
    proposal = proposal_of(grounded_item())
    patch = SemanticPatch.model_validate({"outcome": {"artifact_type": "sample_distance_matrix"}})

    merged, retired = apply_semantic_patch(proposal, patch)
    evidence = merged.outcome_hypotheses[0].evidence

    assert retired == [{"dimension": "artifact_type", "value": "sample_cluster_assignment",
                        "field": "artifact_type"}]
    assert not any(item.dimension == "artifact_type" for item in evidence)
    result = validate_outcome_hypotheses(q1().prompt, merged.outcome_hypotheses)
    assert not result.valid
    assert any("missing_evidence:artifact_type=sample_distance_matrix" in issue
               for issue in result.issues)


def test_a_patch_cannot_relax_validation():
    """The merged result faces the same checks; a bad repair still fails."""
    proposal = proposal_of(missing_input_item())
    patch = SemanticPatch.model_validate({"outcome": {"granularity": "sample_specific"}})

    merged, _ = apply_semantic_patch(proposal, patch)
    result = validate_outcome_hypotheses(q1().prompt, merged.outcome_hypotheses)

    assert not result.valid
    assert any("artifact_granularity:sample_cluster_assignment" in issue for issue in result.issues)


def test_terminal_cluster_artifact_recovers_its_entailed_operation_and_granularity():
    """Replay the live q3 failure through the production routing seam.

    The first pass correctly identifies the terminal cluster labels, but carries
    `infer` and `sample_specific` over from the proposed patient-network means.
    The review fixes the input/evidence and attempts `analyze`, while repeating
    the invalid granularity.  Artifact ontology, not task keywords, must settle
    the dependent fields before registry matching.
    """
    first = {
        "outcome": {
            "operation": "infer",
            "input_artifacts": [],
            "artifact_type": "sample_cluster_assignment",
            "entity_types": ["sample"],
            "granularity": "sample_specific",
        },
        "confidence": 0.9,
        "evidence": [
            {
                "dimension": "operation",
                "value": "infer",
                "source": "explicit",
                "text_span": "找出病患的特異性突變網路",
                "rationale": "The proposed intermediate is a patient-specific network.",
            },
            {
                "dimension": "artifact_type",
                "value": "mutation_matrix",
                "source": "explicit",
                "text_span": "全外顯子定序 (WES) 體細胞突變矩陣",
                "rationale": "The model confused the current input with the result.",
            },
            {
                "dimension": "entity_type",
                "value": "sample",
                "source": "inferred",
                "rationale": "The requested labels assign patients to subtypes.",
            },
            {
                "dimension": "granularity",
                "value": "sample_specific",
                "source": "inferred",
                "rationale": "The model copied granularity from the proposed network.",
            },
        ],
    }
    patch = {
        "outcome": {
            "operation": "analyze",
            "input_artifacts": ["mutation_matrix"],
            "artifact_type": "sample_cluster_assignment",
            "entity_types": ["sample"],
            "display_entities": [],
            "regulator_types": [],
            "target_types": [],
            "selection_tags": [],
            # This is the one defect the live reviewer left behind.
            "granularity": "sample_specific",
            "unresolved_dimensions": [],
        },
        "evidence_removals": [
            {"dimension": "artifact_type", "value": "mutation_matrix"},
        ],
        "evidence_additions": [
            {
                "dimension": "input_artifact",
                "value": "mutation_matrix",
                "source": "explicit",
                "text_span": "全外顯子定序 (WES) 體細胞突變矩陣",
                "rationale": "This is the current dataset.",
            },
            {
                "dimension": "artifact_type",
                "value": "sample_cluster_assignment",
                "source": "inferred",
                "rationale": "Patient subtyping asks for cohort cluster labels.",
            },
        ],
    }
    provider = PatchProvider(first, patch)

    row = evaluate([q3()], provider=provider, model_name="fixture")["results"][0]

    assert row["status"] == "exact"
    assert row["matched_actions"] == ["run_sambar"]
    assert row["outcome"] == {
        "operation": "analyze",
        "input_artifacts": ["mutation_matrix"],
        "artifact_type": "sample_cluster_assignment",
        "entity_types": ["sample"],
        "display_entities": [],
        "regulator_types": [],
        "target_types": [],
        "selection_tags": [],
        "granularity": "aggregate",
        "unresolved_dimensions": [],
    }
    assert row["should_execute"] is False
    assert "Do not use **PANDA**" in row["answer"]
    assert "Do not use **LIONESS-PANDA**" in row["answer"]
    assert "SAMBAR" in row["answer"]
    assert "Pathway aggregation turns gene mutation scores" in row["answer"]


def test_review_unknown_is_resolved_when_its_evidence_names_the_artifact_entailment():
    """Replay d0ebe7b1: the field says unknown while its evidence says aggregate."""
    first = grounded_item()
    first["outcome"]["granularity"] = "sample_specific"
    for item in first["evidence"]:
        if item["dimension"] == "granularity":
            item["value"] = "sample_specific"
    patch = {
        "outcome": {"granularity": "unknown"},
        "evidence_removals": [
            {"dimension": "granularity", "value": "sample_specific"},
        ],
        "evidence_additions": [
            {
                "dimension": "granularity",
                "value": "aggregate",
                "source": "inferred",
                "rationale": (
                    "Sample cluster assignments are one cohort-level artifact."
                ),
            },
        ],
    }

    row = evaluate(
        [q3()],
        provider=PatchProvider(first, patch),
        model_name="fixture",
    )["results"][0]

    assert row["status"] == "exact"
    assert row["matched_actions"] == ["run_sambar"]
    assert row["outcome"]["granularity"] == "aggregate"


def test_review_unknown_is_resolved_from_a_uniquely_entailed_artifact():
    """The artifact contract is sufficient when granularity evidence is absent."""
    first = grounded_item()
    first["outcome"]["granularity"] = "sample_specific"
    for item in first["evidence"]:
        if item["dimension"] == "granularity":
            item["value"] = "sample_specific"
    patch = {
        "outcome": {"granularity": "unknown"},
        "evidence_removals": [
            {"dimension": "granularity", "value": "sample_specific"},
        ],
    }

    row = evaluate(
        [q3()],
        provider=PatchProvider(first, patch),
        model_name="fixture",
    )["results"][0]

    assert row["status"] == "exact"
    assert row["matched_actions"] == ["run_sambar"]
    assert row["outcome"]["granularity"] == "aggregate"


@pytest.mark.parametrize("index,expected", [(0, "sample_cluster_assignment"), (1, "sample_distance_matrix")])
def test_the_patch_names_which_hypothesis_it_adjudicates(index, expected):
    second = grounded_item()
    second["outcome"]["artifact_type"] = "sample_distance_matrix"
    for evidence in second["evidence"]:
        if evidence["dimension"] == "artifact_type":
            evidence["value"] = "sample_distance_matrix"
    proposal = SemanticInterpretation.model_validate({
        "request_mode": "guidance", "semantic_goal": "Subtype patients",
        "outcome_hypotheses": [grounded_item(), second],
    })

    merged, _ = apply_semantic_patch(
        proposal,
        SemanticPatch(hypothesis_index=index, outcome={"granularity": "aggregate"}),
    )

    # Log 150: the patch replaces the hypothesis it names and carries the
    # untouched ones forward; it used to discard them.
    assert len(merged.outcome_hypotheses) == 2
    assert merged.outcome_hypotheses[index].outcome.artifact_type == expected
    other = 1 - index
    assert merged.outcome_hypotheses[other] == proposal.outcome_hypotheses[other]


def test_patch_rejects_a_hypothesis_index_the_proposal_does_not_have():
    proposal = SemanticInterpretation.model_validate({
        "request_mode": "guidance",
        "semantic_goal": "Subtype patients",
        "outcome_hypotheses": [grounded_item()],
    })

    with pytest.raises(ValueError, match="existing hypothesis index"):
        apply_semantic_patch(proposal, SemanticPatch(hypothesis_index=2))


def test_a_first_pass_that_did_not_parse_still_gets_the_whole_review():
    """There is nothing to carry forward, so the review owns the structure."""
    provider = PatchProvider(
        {"outcome": {"artifact_type": "sample_cluster_assignment"}},
        {"request_mode": "guidance", "semantic_goal": "Subtype patients",
         "outcome_hypothesis": grounded_item()},
    )

    row = evaluate([q1()], provider=provider, model_name="fixture")["results"][0]

    assert provider.schemas == ["SemanticInterpretation", "SemanticReview", "IntentDecision"]
    assert row["status"] == "exact"


def test_a_reply_that_is_neither_shape_is_reported_against_the_patch_contract():
    """Observed live: a patch reply was reported as `outcome_hypothesis:missing`.

    That names the whole-review contract, which the call never asked for, and
    would send the next round chasing the wrong defect.
    """
    provider = PatchProvider(
        missing_input_item(),
        {"hypothesis_index": 0, "outcome": {"granularity": "not-an-ontology-value"}},
    )

    row = evaluate([q1()], provider=provider, model_name="fixture")["results"][0]
    issues = [issue for entry in row["diagnostic_details"] for issue in entry["issues"]]

    assert any("outcome.granularity" in issue for issue in issues), issues
    assert not any("outcome_hypothesis:missing" in issue for issue in issues), issues


def nested_patch(**root):
    """The shape a live round returned 5/5 for one request: lists inside outcome."""
    return {
        "outcome": {
            "input_artifacts": ["mutation_matrix"],
            "evidence_additions": [{
                "dimension": "input_artifact", "value": "mutation_matrix",
                "source": "explicit", "text_span": "DNA 突變資料",
                "rationale": "The request supplies the mutation matrix.",
            }],
        },
        **root,
    }


def test_evidence_lists_nested_inside_outcome_are_lifted_to_the_root():
    patch = SemanticPatch.model_validate(nested_patch())

    assert patch.outcome.input_artifacts == ["mutation_matrix"]
    assert [item.dimension for item in patch.evidence_additions] == ["input_artifact"]


def test_the_lifted_shape_routes_exactly_like_the_flat_one():
    provider = PatchProvider(missing_input_item(), nested_patch())

    row = evaluate([q1()], provider=provider, model_name="fixture")["results"][0]

    assert row["status"] == "exact"
    assert row["matched_actions"] == ["run_sambar"]
    assert row["review_patch"]["evidence_added"] == 1


def test_a_conflicting_pair_is_rejected_rather_than_merged_or_guessed():
    """Two different lists under one name is not an equivalent nesting."""
    with pytest.raises(ValueError, match="Conflicting patch evidence list"):
        SemanticPatch.model_validate(nested_patch(evidence_additions=[]))


def test_an_identical_pair_is_accepted_because_nothing_is_ambiguous():
    payload = nested_patch()
    payload["evidence_additions"] = list(payload["outcome"]["evidence_additions"])

    patch = SemanticPatch.model_validate(payload)

    assert len(patch.evidence_additions) == 1


@pytest.mark.parametrize("outcome", ["not-a-mapping", ["granularity"], 7])
def test_an_unexpected_outcome_shape_is_left_for_strict_validation_to_report(outcome):
    """Never turn a repairable schema failure into a TypeError from this hook."""
    with pytest.raises(Exception) as caught:
        SemanticPatch.model_validate({"outcome": outcome})

    assert not isinstance(caught.value, TypeError)
