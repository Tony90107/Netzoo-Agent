"""Log 298: "Which tool finds gene communities for each patient?" states a per-patient scale.

The witness knew per-sample scales only beside a network noun, so this request
stated none: its per-patient community reading was repaired to aggregate and
answered "a cohort-level community assignment" beside an assumption saying
per-patient (Log 295). With the scale stated, the reading is the capability
gap of Log 294. Replayed from the recorded replies.
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
from netzoo_agent_core.interpretation.concept_answers import render_capability_gap  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from test_sibling_only_reduction import RecordedProvider  # noqa: E402

FIXTURE = json.loads((HERE / "log298_communities_each_patient_calls.json").read_text(encoding="utf-8"))


def test_per_patient_communities_get_the_gap_not_a_cohort_answer(monkeypatch):
    decisions = []
    original = evaluate_routing.invoke_router

    def recording(context, state, prompt):
        result = original(context, state, prompt)
        decisions.append(result.decision)
        return result

    monkeypatch.setattr(evaluate_routing, "invoke_router", recording)
    case = RoutingScenario.model_validate({
        "id": "log298", "language": "en", "category": "positive", "prompt": FIXTURE["prompt"],
        "expected": {"status": "unsupported", "actions": []},
    })
    evaluate([case], provider=RecordedProvider(FIXTURE["calls"]), model_name="recorded")
    decision = decisions[0]
    # The recorded review set the scale back to aggregate; that contradicts
    # the stated scale, so the validated first pass is kept.
    assert decision.capability_match_status == "unsupported"
    assert (decision.requested_outcome.artifact_type, decision.requested_outcome.granularity) == (
        "community_assignment", "sample_specific")
    assert decision.mismatch_dimensions == ["granularity"] and decision.alternative_actions == ["run_condor"]
    reply = render_capability_gap(decision, ProjectPolicyLoader(HERE.parent).load())
    assert "do not produce sample-specific community assignments" in reply
    assert "CONDOR can instead analyze aggregate community assignments" in reply
    assert "cohort-level" not in reply
