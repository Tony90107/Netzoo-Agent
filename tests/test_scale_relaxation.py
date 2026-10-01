"""Log 281: an unstated scale must not rule out every workflow for a produced result.

Recorded blind case 7: "For the same individuals" (matched samples) was read
as a per-sample multi-omic network with an explicit but scale-free quote. No
workflow produces that, so the request got no workflow at all although DRAGON
produces a multi-omic network for the cohort. Replayed from the recorded replies.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))

from evaluate_routing import RoutingScenario, evaluate  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    CapabilityMatch, OutcomeHypothesis, RequestedOutcome, SemanticInterpretation,
)
from netzoo_agent_core.routing.scale_relaxation import relax_unstated_scale  # noqa: E402
from test_sibling_only_reduction import RecordedProvider  # noqa: E402

FIXTURE = json.loads((HERE / "log281_case7_calls.json").read_text(encoding="utf-8"))


def _replay():
    case = RoutingScenario.model_validate({
        "id": "log281-case7", "language": "en", "category": "positive", "prompt": FIXTURE["prompt"],
        "expected": {"status": "ambiguous", "actions": []},
    })
    return evaluate([case], provider=RecordedProvider(FIXTURE["calls"]), model_name="recorded")["results"][0]


def test_an_unstated_per_sample_reading_still_reaches_the_cohort_workflow_as_guidance():
    result = _replay()

    assert result["status"] == "fallback" and result["matched_actions"] == ["run_dragon"]
    assert result["action"] == "no_tool" and not result["should_execute"]
    # Log 290: LIONESS-DRAGON now gives the per-sample result; the unstated scale
    # still picks no workflow, and the note names both.
    assert ("No scale was stated; DRAGON gives one result for the whole cohort; "
            "LIONESS-DRAGON gives one result per sample.") in result["answer"]
    assert "per-sample" not in result["answer"].split("No scale was stated", 1)[0]


def _reading(granularity):
    outcome = RequestedOutcome(operation="infer", artifact_type="multi_omic_network", granularity=granularity)
    return SemanticInterpretation.model_construct(
        request_mode="guidance", semantic_goal="", outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=0.9)])


def test_a_stated_scale_or_a_recorded_mismatch_is_left_alone():
    empty = CapabilityMatch(status="ambiguous")
    stated = _reading("sample_specific")
    assert relax_unstated_scale("I need one per-sample network for each patient.", stated, empty)[0] is stated
    rejected = CapabilityMatch(status="unsupported", mismatch_dimensions=["input_artifacts"])
    assert relax_unstated_scale("Expression and methylation.", stated, rejected)[0] is stated


def _fallback_decision(granularity="sample_specific", actions=("run_dragon",)):
    from netzoo_agent_core.contracts import TaskDecision
    outcome = RequestedOutcome(operation="infer", artifact_type="multi_omic_network", granularity=granularity)
    return TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question", confidence=0.5,
        reason="fallback", capability_match_status="fallback", match_basis="unverified_evidence",
        matched_actions=list(actions), requested_outcome=outcome,
        outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=0.5)],
    )


def test_every_path_drops_an_unstated_scale_no_chosen_workflow_produces():
    from netzoo_agent_core.routing.scale_relaxation import note_unstated_scale
    decision = _fallback_decision()

    noted = note_unstated_scale(FIXTURE["prompt"], decision)
    assert noted.requested_outcome.granularity == "unknown"
    assert noted.outcome_hypotheses[0].assumptions == [
        "No scale was stated; DRAGON gives one result for the whole cohort."]
    assert note_unstated_scale("I need a per-sample network for each patient.", decision) is decision
    aggregate = _fallback_decision("aggregate")
    assert note_unstated_scale(FIXTURE["prompt"], aggregate) is aggregate
