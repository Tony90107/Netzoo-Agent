"""An ambiguous match is the commonest outcome, and nothing was watching it.

Across two rounds `ambiguous` was 69 of 162 trials, and 63 of those left the
evaluation with `answer_evaluated: false` -- no report said anything about what
the user is shown in the case that happens most often. Replaying those trials'
own recorded outcomes showed the answer layer already naming the real candidates
in 56 of them, in exactly the shape the handoff described as missing. A solved
problem stayed written down as unsolved across several documents because no
report could see it, and a regression would have been just as invisible.

What is pinned here is therefore mostly behaviour that already worked. That is
the point: an unwatched correct behaviour and an unwatched broken one look
identical from the outside.

The part that genuinely cannot be scored here is separated rather than hidden.
An ambiguous decision with nothing to ask hands off to the response model, which
this evaluator deliberately does not pay for; those rows now say so.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from evaluate_routing import RoutingScenario, evaluate  # noqa: E402
from test_routing_evaluation import FixtureProvider, hypothesis  # noqa: E402


TASK = "I have an expression matrix and TF motif priors. Which workflow should I use?"

#: The outcome leaves granularity open, so four registered capabilities remain
#: compatible and the registry says so rather than choosing.
AMBIGUOUS_OUTCOME = {
    "operation": "infer", "input_artifacts": ["expression_matrix"],
    "artifact_type": "regulatory_network", "entity_types": [],
    "regulator_types": ["tf"], "target_types": ["gene"], "granularity": "unknown",
}
EXPECTED_CANDIDATES = ("PANDA", "LIONESS-PANDA", "OTTER", "GIRAFFE")


def ambiguous_hypothesis():
    item = hypothesis()
    item["outcome"] = dict(AMBIGUOUS_OUTCOME)
    item["evidence"] = [
        {"dimension": dimension, "value": value, "source": "explicit",
         "text_span": span, "rationale": "Stated by the user."}
        for dimension, value, span in (
            ("operation", "infer", "Which workflow"),
            ("artifact_type", "regulatory_network", "TF motif priors"),
            ("input_artifact", "expression_matrix", "expression matrix"),
            ("regulator_type", "tf", "TF"),
            ("target_type", "gene", "expression matrix"),
        )
    ]
    return item


def case(prompt: str = TASK) -> RoutingScenario:
    return RoutingScenario.model_validate({
        "id": "ambiguous-case", "language": "en", "category": "negative",
        "prompt": prompt,
        "expected": {"status": "ambiguous", "actions": [], "require_clarification": True},
    })


def row(item=None, prompt: str = TASK):
    item = item or ambiguous_hypothesis()
    provider = FixtureProvider(
        first={"request_mode": "guidance", "semantic_goal": "Network guidance",
               "outcome_hypotheses": [item]},
        review={"request_mode": "guidance", "semantic_goal": "Network guidance",
                "outcome_hypothesis": item},
    )
    report = evaluate([case(prompt)], provider=provider, model_name="fixture")
    return report["results"][0], provider


def test_the_commonest_outcome_is_no_longer_left_unscored():
    result, _ = row()

    assert result["status"] == "ambiguous"
    assert result["answer_evaluated"], "ambiguous guidance left the evaluator silent"
    assert result["answer_scope"] == "deterministic"


def test_the_report_records_which_candidates_the_decision_was_holding():
    """Without them, "underdetermined between four" reads the same as

    "resolved nothing", and those call for opposite responses.
    """
    result, _ = row()

    assert set(result["hypothesis_actions"]) == {
        "run_panda", "run_lioness_panda", "run_otter", "run_giraffe",
    }
    assert result["clarification_question_asked"]


def test_every_candidate_the_decision_holds_is_named_to_the_user():
    result, _ = row()

    for name in EXPECTED_CANDIDATES:
        assert name in result["answer"], f"{name} was never shown to the user"
    assert not [error for error in result["answer_errors"]
                if error.startswith("candidate_unnamed")]


def test_a_candidate_left_out_of_the_answer_is_reported():
    """The check has to be able to fail, or it pins nothing."""
    import evaluate_routing

    real = evaluate_routing.respond

    def stripped(context, state):
        response = real(context, state)
        text = str(response["messages"][0].content)
        for name in ("LIONESS-PANDA", "GIRAFFE"):
            text = text.replace(name, "a workflow")
        response["messages"][0].content = text
        return response

    evaluate_routing.respond = stripped
    try:
        result, _ = row()
    finally:
        evaluate_routing.respond = real

    assert {error.split(": ")[1] for error in result["answer_errors"]
            if error.startswith("candidate_unnamed")} == {
        "run_lioness_panda", "run_giraffe",
    }


def test_scoring_the_ambiguous_answer_costs_no_provider_call():
    """It is produced deterministically; paying for it would be the reason to skip it."""
    result, provider = row()

    assert result["provider_calls"] == len(provider.calls)
    # Interpreter, one field-scoped review, intent. Nothing for the answer.
    assert [schema.__name__ for schema, _ in provider.calls] == [
        "SemanticInterpretation", "SemanticPatch", "IntentDecision",
    ]


def test_an_ambiguity_with_nothing_to_ask_says_it_went_to_the_response_model():
    """Not every ambiguous decision can be scored here, and the difference matters.

    A single surviving candidate carries no question, so there is no
    deterministic answer and the response model -- which this evaluator does not
    pay for -- writes the reply. That row is genuinely out of scope, but it must
    not be recorded the way a row nobody looked at was recorded.

    Reachability is asserted first. An invented outcome for this branch turned
    out to be unreachable and the assertion silently never ran, so the shape
    here is one a live round actually produced: `two-layer-network`, whose only
    candidate is DRAGON.
    """
    from types import SimpleNamespace

    from evaluate_routing import _score_answer
    from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis
    from netzoo_agent_core.routing.outcome_matching import match_semantic_request

    match = match_semantic_request("", [OutcomeHypothesis.model_validate({
        "outcome": {
            "operation": "explain", "artifact_type": "multi_omic_network",
            "granularity": "unknown",
        },
        "confidence": 0.9, "evidence": [],
    })], request_mode="guidance")

    assert match.status == "ambiguous"
    assert match.hypothesis_actions == ["run_dragon"]
    assert match.clarification_question is None, "the branch under test is gone"

    scored = _score_answer(
        case(),
        SimpleNamespace(decision=SimpleNamespace(
            action="no_tool", should_execute=False,
            capability_match_status=match.status,
            matched_actions=[], rejected_methods=[], match_basis="semantic",
            clarification_question=match.clarification_question,
        )),
        SimpleNamespace(project_policy=SimpleNamespace(workflows={})),
    )

    assert not scored["answer_evaluated"]
    assert scored["answer_scope"] == "response_model"
