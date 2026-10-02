"""Log 321: Test 6 (TF and miRNA regulation) must not end as GIRAFFE.

Two rules, each needed: a regulator role the request calls insufficient ("A
TF-gene network alone misses the post-transcriptional layer") is not the role
asked for (RA); and a TF-only result the request never states (TF activity,
signed effects) yields to the reading's own miRNA regulators instead of
clearing them (TA, Log 321 supplement 3).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis, SemanticInterpretation  # noqa: E402
from netzoo_agent_core.interpretation.request_integrity import regulatory_role_mentions  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402
from netzoo_agent_core.interpretation.stated_field_restoration import restore_stated_fields  # noqa: E402

TEST6 = json.loads((ROOT / "docs" / "research-log" / "test10-2026-10-03" / "prompts.json").read_text())["test6"]


def _reading(artifact, regulators, entities=("gene", "tf", "sample"), granularity="aggregate"):
    return OutcomeHypothesis.model_validate({"outcome": {
        "operation": "infer", "input_artifacts": ["expression_matrix"], "artifact_type": artifact,
        "entity_types": list(entities), "regulator_types": list(regulators), "target_types": ["gene"],
        "granularity": granularity}, "confidence": 0.9, "evidence": []})


def _restore(task, hypotheses):
    reading = SemanticInterpretation.model_construct(request_mode="guidance", semantic_goal="",
                                                     outcome_hypotheses=hypotheses)
    restored, record = restore_stated_fields(task, reading)
    return restored.outcome_hypotheses[0].outcome, [item["source"] for item in record]


def test_a_role_the_request_calls_insufficient_is_not_a_stated_role():
    assert regulatory_role_mentions(TEST6) == ()
    assert regulatory_role_mentions("A TF-gene network is not enough for us.") == ()
    assert [m.regulator_type for m in regulatory_role_mentions("We want a TF-to-gene network per patient.")] == ["tf"]


def test_an_unstated_tf_activity_yields_to_the_readings_mirna_regulators():
    outcome, sources = _restore(TEST6, [_reading("regulatory_network_and_tf_activity", ["tf", "mirna"])])
    assert "unstated_tf_only_artifact" in sources
    assert outcome.artifact_type == "regulatory_network" and set(outcome.regulator_types) == {"tf", "mirna"}
    assert "sample" not in outcome.entity_types and "mirna" in outcome.entity_types
    match = match_semantic_request(TEST6, [_reading("regulatory_network", ["tf", "mirna"], outcome.entity_types)],
                                   request_mode="guidance")
    assert match.matched_actions == ["run_puma"]
    # Live supplement 4: the corrected artifact keeps an artifact evidence entry.
    from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses

    reading = SemanticInterpretation.model_construct(request_mode="guidance", semantic_goal="", outcome_hypotheses=[
        _reading("regulatory_network_and_tf_activity", ["tf", "mirna"])])
    restored, _ = restore_stated_fields(TEST6, reading)
    issues = validate_outcome_hypotheses(TEST6, restored.outcome_hypotheses, "guidance").issues
    assert not any("artifact_type" in issue for issue in issues)


def test_a_tf_only_activity_reading_is_kept():
    # Case 4's per-TF reading has no miRNA: nothing contradicts it.
    task = "Each person's per-TF regulatory strength over its targets, related to survival."
    outcome, sources = _restore(task, [_reading("regulatory_network_and_tf_activity", ["tf"])])
    assert outcome.artifact_type == "regulatory_network_and_tf_activity" and "unstated_tf_only_artifact" not in sources


def test_a_stated_activity_is_never_dropped():
    task = TEST6 + " We also want each TF's activity in every sample."
    outcome, sources = _restore(task, [_reading("regulatory_network_and_tf_activity", ["tf", "mirna"])])
    assert "unstated_tf_only_artifact" not in sources
