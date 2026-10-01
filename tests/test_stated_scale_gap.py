"""Log 294: a stated scale the ontology gives a result no other way is a gap, not a failure.

"Which tool finds gene communities separately for each patient, with
individual-specific networks split into modules per patient?" was read as a
per-patient community assignment. The ontology gives communities one scale, so
the reading was rejected; its repair to aggregate contradicted the stated scale;
both attempts failed and the reply was "Semantic routing output failed
validation". Replayed from the recorded replies (Log 293).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))

import evaluate_routing  # noqa: E402
from evaluate_routing import RoutingScenario, evaluate  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeEvidence, OutcomeHypothesis, RequestedOutcome,
)
from netzoo_agent_core.interpretation.concept_answers import render_capability_gap  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses  # noqa: E402
from netzoo_agent_core.interpretation.request_integrity import stated_scale_gap  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.routing.requested_outcome_matching import match_requested_outcome  # noqa: E402
from test_sibling_only_reduction import RecordedProvider  # noqa: E402

FIXTURE = json.loads((HERE / "log294_communities_calls.json").read_text(encoding="utf-8"))
TASK = FIXTURE["prompt"]
PER_SAMPLE = RequestedOutcome(operation="infer", artifact_type="community_assignment", granularity="sample_specific")


def _reading(outcome=PER_SAMPLE):
    # As validation sees it after restoration, which quotes the stated scale.
    return OutcomeHypothesis(outcome=outcome, confidence=0.9, evidence=[
        OutcomeEvidence(dimension="artifact_type", value="community_assignment", source="explicit",
                        text_span="finds gene communities separately for each patient", rationale="communities"),
        OutcomeEvidence(dimension="granularity", value="sample_specific", source="explicit",
                        text_span="individual-specific networks", rationale="stated scale"),
    ])


def test_only_a_stated_scale_the_result_cannot_have_is_a_gap():
    assert stated_scale_gap(TASK, PER_SAMPLE) == "artifact_granularity:community_assignment"
    # Unstated, or both scales stated: the reading's scale is still the model's.
    assert stated_scale_gap("Which tool finds gene communities for each patient?", PER_SAMPLE) is None
    both = "I want one cohort network and individual-specific networks split into modules."
    assert stated_scale_gap(both, PER_SAMPLE) is None
    # A scale the ontology gives the result is no gap.
    aggregate = PER_SAMPLE.model_copy(update={"granularity": "aggregate"})
    assert stated_scale_gap("I want one cohort network split into modules.", aggregate) is None


def test_validation_keeps_the_reading_only_when_the_gap_is_its_one_fault():
    assert validate_outcome_hypotheses(TASK, [_reading()], "guidance").valid
    # Two readings: unchanged, the gap is still repaired.
    two = validate_outcome_hypotheses(TASK, [_reading(), _reading()], "guidance")
    assert not two.valid and any("artifact_granularity:community_assignment" in issue for issue in two.issues)
    # Any other fault keeps the repair, and the repair still sees the gap; the
    # TF+miRNA per-patient reading as GIRAFFE's network-and-activity is this case.
    roles = RequestedOutcome(operation="infer", artifact_type="regulatory_network_and_tf_activity",
                             granularity="sample_specific", regulator_types=["tf", "mirna"], target_types=["gene"])
    task = "I want per-patient networks that capture both TF and miRNA regulation of genes."
    mixed = validate_outcome_hypotheses(task, [_reading(roles)], "guidance")
    assert not mixed.valid
    assert any("artifact_granularity:regulatory_network_and_tf_activity" in issue for issue in mixed.issues)


def test_matching_names_the_workflow_that_gives_the_result_at_its_scale():
    match = match_requested_outcome(PER_SAMPLE)
    assert (match.status, match.mismatch_dimensions, match.alternative_actions) == (
        "unsupported", ["granularity"], ["run_condor"])


def test_a_gap_is_about_producing_the_result():
    # Log 296 (GG3): "Which workflow finds X?" read as `explain` said "do not explain X".
    from netzoo_agent_core.contracts import TaskDecision
    outcome = PER_SAMPLE.model_copy(update={"operation": "explain"})
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question",
                            confidence=0.9, reason="gap", capability_match_status="unsupported",
                            requested_outcome=outcome, mismatch_dimensions=["granularity"],
                            alternative_actions=["run_condor"])
    reply = render_capability_gap(decision, ProjectPolicyLoader(HERE.parent).load())
    assert "do not produce sample-specific community assignments" in reply and "do not explain" not in reply


def test_the_recorded_request_gets_the_gap_instead_of_a_validation_failure(monkeypatch):
    decisions = []
    original = evaluate_routing.invoke_router

    def recording(context, state, prompt):
        result = original(context, state, prompt)
        decisions.append(result.decision)
        return result

    monkeypatch.setattr(evaluate_routing, "invoke_router", recording)
    case = RoutingScenario.model_validate({
        "id": "log294-communities", "language": "en", "category": "positive", "prompt": TASK,
        "expected": {"status": "unsupported", "actions": []},
    })
    evaluate([case], provider=RecordedProvider(FIXTURE["calls"]), model_name="recorded")
    decision = decisions[0]
    # The recorded review set the scale to not_applicable; that contradicts the
    # stated scale, so the validated first pass is kept.
    assert decision.capability_match_status == "unsupported"
    assert (decision.requested_outcome.artifact_type, decision.requested_outcome.granularity) == (
        "community_assignment", "sample_specific")
    assert decision.mismatch_dimensions == ["granularity"] and decision.alternative_actions == ["run_condor"]
    reply = render_capability_gap(decision, ProjectPolicyLoader(HERE.parent).load())
    assert "do not infer sample-specific community assignments" in reply
    assert "CONDOR can instead analyze aggregate community assignments" in reply
    assert "failed validation" not in reply
