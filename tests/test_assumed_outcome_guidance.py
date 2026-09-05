"""A hypothesis kept advisory by its assumptions still deserves guidance.

`match_semantic_request` refuses `exact` for any hypothesis carrying an
assumption, because an assumption marks an unconfirmed interpretation of the
request. Repeated live measurement showed the cost of the resulting
`ambiguous`: the only trials that produced the gold outcome asked the user a
clarification question and returned no recommendation at all -- a worse result
than the fallback the same request gets when interpretation fails outright.

Option C keeps the guard exactly as it is. When a single candidate is the sole
reason for the demotion, the match is reported as a fallback recommendation, on
its own `assumed_outcome` basis, so the user receives the registry guidance
without any claim that the goal was exactly matched.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402

from evaluate_routing import DEFAULT_SCENARIOS, evaluate, load_scenarios  # noqa: E402
from test_routing_evaluation import FixtureProvider  # noqa: E402


GOLD = {
    "outcome": {"operation": "analyze", "input_artifacts": ["mutation_matrix"],
                "artifact_type": "sample_cluster_assignment",
                "entity_types": ["sample"], "granularity": "aggregate"},
    "confidence": 0.95,
    "evidence": [{"dimension": dimension, "value": value, "source": "inferred",
                  "rationale": "Entailed by the stated goal."}
                 for dimension, value in (
                     ("operation", "analyze"), ("input_artifact", "mutation_matrix"),
                     ("artifact_type", "sample_cluster_assignment"),
                     ("entity_type", "sample"), ("granularity", "aggregate"))],
}
NETWORK = {
    "outcome": {"operation": "infer", "artifact_type": "regulatory_network",
                "entity_types": ["tf", "gene"], "regulator_types": ["tf"],
                "target_types": ["gene"], "granularity": "sample_specific"},
    "confidence": 0.9,
    "evidence": [{"dimension": dimension, "value": value, "source": "inferred",
                  "rationale": "Entailed by the stated goal."}
                 for dimension, value in (
                     ("operation", "infer"), ("artifact_type", "regulatory_network"),
                     ("regulator_type", "tf"), ("target_type", "gene"),
                     ("entity_type", "tf"), ("entity_type", "gene"),
                     ("granularity", "sample_specific"))],
}


def q1():
    return next(case for case in load_scenarios(DEFAULT_SCENARIOS) if case.id == "original-q1")


def hypothesis_with(assumptions, body=None):
    return OutcomeHypothesis.model_validate({**(body or GOLD), "assumptions": assumptions})


def test_the_guard_still_refuses_an_exact_match():
    match = match_semantic_request(
        q1().prompt, [hypothesis_with(["Clustering follows aggregation."])],
        request_mode="unknown",
    )

    assert match.status != "exact"
    assert match.match_basis == "assumed_outcome"


def test_a_single_assumed_candidate_becomes_registry_guidance():
    match = match_semantic_request(
        q1().prompt, [hypothesis_with(["Clustering follows aggregation."])],
        request_mode="unknown",
    )

    assert match.status == "fallback"
    assert match.matched_actions == ["run_sambar"]
    assert match.clarification_question is None


def test_an_assumption_free_hypothesis_is_unaffected():
    match = match_semantic_request(q1().prompt, [hypothesis_with([])], request_mode="unknown")

    assert match.status == "exact" and match.match_basis == "semantic"


def test_competing_assumed_candidates_still_raise_a_question_instead():
    """Two candidates are a real choice; guidance must not pick one silently."""
    match = match_semantic_request(
        q1().prompt,
        [hypothesis_with(["one"]), hypothesis_with(["two"], NETWORK)],
        request_mode="unknown",
    )

    assert match.status == "ambiguous"
    assert match.matched_actions == []


def test_an_assumed_fallback_is_never_promoted_back_to_exact():
    """The guidance-mode promotion path applies to partial evidence only."""
    match = match_semantic_request(
        q1().prompt, [hypothesis_with(["Clustering follows aggregation."])],
        request_mode="unknown",
    )

    assert match.match_basis == "assumed_outcome"
    assert match.status == "fallback"


def declarative_case():
    """A request that states a goal without asking which method fits.

    `request_mode` is validated now, and every corpus prompt asks about methods,
    so `unknown` is corrected there rather than reaching this path. The path
    still applies to a request that takes no position on performing the work.
    """
    from evaluate_routing import RoutingScenario

    return RoutingScenario.model_validate({
        "id": "declarative-case", "language": "en", "category": "positive",
        "prompt": "I have a somatic mutation matrix for cancer patients "
                  "and I want cohort subtype labels for them.",
        "expected": {"status": "exact", "actions": ["run_sambar"],
                     "input_artifacts": ["mutation_matrix"],
                     "artifact_type": "sample_cluster_assignment",
                     "granularity": "aggregate"},
    })


def routing_row():
    """Reproduces the observed live shape: a reviewed outcome with request_mode unknown."""
    item = {**GOLD, "assumptions": ["Clustering follows pathway aggregation."]}
    provider = FixtureProvider(
        first={"request_mode": "unknown", "semantic_goal": "Cluster patients",
               "outcome_hypotheses": [item]},
        review={"request_mode": "unknown", "semantic_goal": "Cluster patients",
                "outcome_hypothesis": item},
    )
    return evaluate([declarative_case()], provider=provider, model_name="fixture")["results"][0]


def test_production_routing_gives_the_user_guidance_and_no_continuation():
    row = routing_row()

    assert row["status"] == "fallback"
    assert row["match_basis"] == "assumed_outcome"
    assert row["assumption_count"] == 1
    assert row["answer_evaluated"] and row["answer_passed"]
    assert "SAMBAR" in row["answer"]
    assert "not an exact semantic match" in row["answer"]
    assert not row["next_step"]["allow_workflow_continuation"]
    assert row["interaction_passed"]
    # A demoted match is still not the expected exact route.
    assert not row["route_passed"]


def test_the_recorded_outcome_survives_the_demotion():
    """The reviewed dimensions are kept; only the match claim is weaker."""
    row = routing_row()

    assert row["outcome"]["input_artifacts"] == ["mutation_matrix"]
    assert row["outcome"]["artifact_type"] == "sample_cluster_assignment"
    assert row["outcome"]["granularity"] == "aggregate"
    assert row["outcome"]["entity_types"] == ["sample"]


def test_guidance_mode_completeness_promotion_is_left_unchanged():
    """A guidance request reaches `exact` through its own completeness path.

    The assumptions guard only applies where a strict match was found, which a
    guidance request avoids by design: it may omit the operation because it is
    asking which workflow to use. This records that boundary rather than
    changing it.
    """
    match = match_semantic_request(
        q1().prompt, [hypothesis_with(["Clustering follows aggregation."])],
        request_mode="guidance",
    )

    assert match.status == "exact"


def test_an_assumed_candidate_is_not_asked_what_result_the_user_wants():
    """Intent may read the request as execution; the outcome is still determined.

    Observed live: an assumed_outcome fallback still received the generic
    "what result do you want" question, because that question fires whenever
    intent says execute and no exact action exists. Here the outcome is complete
    and a single candidate is named, so the question has no answer to collect.
    """
    from netzoo_agent_core.contracts import IntentDecision
    from netzoo_agent_core.contracts.outcomes import CapabilityMatch, SemanticInterpretation
    from netzoo_agent_core.interpretation.assembly import assemble_task_decision

    interpretation = SemanticInterpretation.model_validate({
        "request_mode": "unknown", "semantic_goal": "Cluster patients",
        "outcome_hypotheses": [{**GOLD, "assumptions": ["Clustering follows aggregation."]}],
    })
    match = CapabilityMatch(
        status="fallback", match_basis="assumed_outcome",
        matched_actions=["run_sambar"], hypothesis_actions=["run_sambar"],
    )

    decision = assemble_task_decision(
        interpretation, match,
        IntentDecision(mode="execute", confidence=0.9, reason="reads as a work request"),
        task=q1().prompt,
    )

    assert decision.clarification_question is None
    assert decision.should_execute is False
    assert decision.action == "no_tool"


def test_a_recovery_fallback_without_an_outcome_still_asks():
    from netzoo_agent_core.contracts import IntentDecision
    from netzoo_agent_core.contracts.outcomes import CapabilityMatch, SemanticInterpretation
    from netzoo_agent_core.interpretation.assembly import assemble_task_decision

    interpretation = SemanticInterpretation.model_validate({
        "request_mode": "unknown", "semantic_goal": "Cluster patients",
        "outcome_hypotheses": [{**GOLD, "assumptions": []}],
    })
    match = CapabilityMatch(status="fallback", match_basis="registry_features")

    decision = assemble_task_decision(
        interpretation, match,
        IntentDecision(mode="execute", confidence=0.9, reason="reads as a work request"),
        task=q1().prompt,
    )

    assert decision.clarification_question
