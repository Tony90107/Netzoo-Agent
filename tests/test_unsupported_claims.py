"""A reading whose only faults are claims without evidence keeps the claims that have it.

Across 6,275 traced runs, 668 semantic interpretations were discarded; 171 for missing evidence alone and 94 for an
unknown result of not_applicable scale (feasibility eval F36). Offline replay of the recorded rejections: 169 of 240
such readings validate once the unsupported claims are taken out.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses  # noqa: E402
from netzoo_agent_core.interpretation.unsupported_claims import without_unsupported_claims  # noqa: E402

F36 = "幫我分析這些資料，看看有沒有生物意義。"
F36_READING = {
    "request_mode": "guidance", "semantic_goal": "Analyze the data for biological significance.",
    "outcome_hypotheses": [{"outcome": {
        "operation": "analyze", "input_artifacts": [], "artifact_type": "unknown", "entity_types": [],
        "display_entities": [], "regulator_types": [], "target_types": [], "selection_tags": [],
        "granularity": "not_applicable", "unresolved_dimensions": []}, "confidence": 0.8, "evidence": [
        {"dimension": "operation", "value": "analyze", "source": "explicit", "text_span": "幫我分析這些資料，看看有沒有生物意義",
         "rationale": "The user requests to analyze the data."},
        {"dimension": "artifact_type", "value": "unknown", "source": "inferred", "text_span": None,
         "rationale": "Not defined."},
        {"dimension": "granularity", "value": "not_applicable", "source": "inferred", "text_span": None,
         "rationale": "Not specified."}], "assumptions": []}]}


def _reading(payload=F36_READING):
    return SemanticInterpretation.model_validate(payload)


def test_an_unknown_result_of_not_applicable_scale_is_kept_as_unknown_scale():
    reading = _reading()
    issues = validate_outcome_hypotheses(F36, reading.outcome_hypotheses, reading.request_mode).issues
    assert issues == ("hypothesis[0].inconsistent_not_applicable_outcome",)
    kept = without_unsupported_claims(F36, reading, issues)
    assert kept is not None and kept.outcome_hypotheses[0].outcome.granularity == "unknown"
    assert validate_outcome_hypotheses(F36, kept.outcome_hypotheses, kept.request_mode).valid


def test_a_scale_claimed_without_evidence_is_taken_out_and_the_rest_kept():
    task = "We have expression, motifs and PPI for 60 lung samples. We want a TF-gene regulatory network."
    outcome = {"operation": "infer", "input_artifacts": [], "artifact_type": "regulatory_network",
               "entity_types": ["tf", "gene"], "display_entities": [], "regulator_types": ["tf"],
               "target_types": ["gene"], "selection_tags": [], "granularity": "sample_specific",
               "unresolved_dimensions": []}
    evidence = [{"dimension": "artifact_type", "value": "regulatory_network", "source": "explicit",
                 "text_span": "a TF-gene regulatory network", "rationale": "Stated."}]
    reading = _reading({"request_mode": "guidance", "semantic_goal": "TF network",
                        "outcome_hypotheses": [{"outcome": outcome, "confidence": 0.9, "evidence": evidence,
                                                "assumptions": []}]})
    issues = validate_outcome_hypotheses(task, reading.outcome_hypotheses, reading.request_mode).issues
    assert "hypothesis[0].missing_evidence:granularity=sample_specific" in issues
    kept = without_unsupported_claims(task, reading, issues)
    assert kept is not None
    assert kept.outcome_hypotheses[0].outcome.granularity == "unknown"
    assert kept.outcome_hypotheses[0].outcome.artifact_type == "regulatory_network"


def test_any_other_fault_discards_the_reading_as_before():
    reading = _reading()
    assert without_unsupported_claims(F36, reading, ["hypothesis[0].ungrounded_evidence:operation=analyze"]) is None
    assert without_unsupported_claims(F36, reading, [
        "hypothesis[0].inconsistent_not_applicable_outcome", "hypothesis[0].artifact_granularity"]) is None
    assert without_unsupported_claims(F36, reading, []) is None
