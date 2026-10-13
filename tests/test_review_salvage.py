"""C: a review reply that does not parse loses only its faulty parts, as the first pass does (Logs 213, 215).

122 traced interpretations were lost to an unparsable review reply. Replay: dropping out-of-vocabulary entities made
"all three layers in one network" an exact DRAGON match and a ceRNA network an exact PUMA one, so only case is fixed.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import SemanticReview  # noqa: E402
from netzoo_agent_core.graph.semantic_review_validation import _validated_review, salvage_review  # noqa: E402

F17 = {  # feasibility eval 10-13 F17: the operation evidence is marked explicit and quotes nothing
    "request_mode": "execute", "semantic_goal": "Train a survival prediction model.",
    "outcome_hypothesis": {"outcome": {
        "operation": "infer", "artifact_type": "unknown", "granularity": "not_applicable",
        "input_artifacts": ["expression_matrix"], "entity_types": ["sample", "gene"], "regulator_types": [],
        "target_types": []}, "confidence": 0.9, "evidence": [
        {"dimension": "operation", "value": "infer", "source": "explicit", "rationale": "Train a model."},
        {"dimension": "input_artifact", "value": "expression_matrix", "source": "explicit", "rationale": "Stated.",
         "text_span": "expression data"}], "assumptions": []}}


def _error(payload):
    with pytest.raises(ValidationError) as caught:
        SemanticReview.model_validate(payload)
    return caught.value


def test_an_explicit_entry_without_a_quote_is_dropped_and_the_reply_kept():
    cleaned, record = salvage_review(F17, _error(F17))
    assert [item["dimension"] for item in cleaned["outcome_hypothesis"]["evidence"]] == ["input_artifact"]
    assert record == [{"evidence": 0, "dimension": "operation", "dropped": True}]
    salvaged = []
    review = _validated_review(F17, patching=False, salvaged=salvaged)
    assert review.outcome_hypothesis.outcome.operation == "infer" and salvaged == record


def test_an_entity_in_another_case_is_matched_to_the_vocabulary():
    payload = copy.deepcopy(F17)
    payload["outcome_hypothesis"]["outcome"]["entity_types"] = ["miRNA", "gene"]
    payload["outcome_hypothesis"]["evidence"] = payload["outcome_hypothesis"]["evidence"][1:]
    cleaned, record = salvage_review(payload, _error(payload))
    assert cleaned["outcome_hypothesis"]["outcome"]["entity_types"] == ["mirna", "gene"]
    assert record == [{"field": "entity_types", "value": "miRNA", "kept_as": "mirna"}]


def test_an_entity_outside_the_vocabulary_leaves_the_reply_rejected():
    """Replay: dropping "lncRNA" turned a ceRNA network into an exact PUMA match."""
    payload = copy.deepcopy(F17)
    payload["outcome_hypothesis"]["outcome"]["entity_types"] = ["lncRNA", "gene"]
    assert salvage_review(payload, _error(payload)) is None
    with pytest.raises(ValidationError):
        _validated_review(payload, patching=False)
