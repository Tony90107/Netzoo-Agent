"""Log 257: the goal review and the method stage resolve different ambiguities.

After Log 255 the goal review (`hypothesis_bases`) ran on every tie and on any
discourse cue, including 不確定 inside the noun 不確定性 ("uncertainty"). When it
found a single goal it changed nothing, yet it still used up the turn's one
advisory call, so the condition recommender -- the only stage that reports a
missing mathematical philosophy and recommends from quoted study facts --
never ran. The prior-reliability question then got a six-candidate list and a
granularity question. A review that validates no comparison now yields.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from evaluate_routing import RoutingScenario, evaluate  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.graph.hypothesis_bases import explicit_research_choice, framing_yielded  # noqa: E402
from test_ambiguous_guidance_is_scored import ambiguous_hypothesis  # noqa: E402
from test_routing_evaluation import FixtureProvider  # noqa: E402

ROUTING = ["semantic_interpreter", "semantic_reviewer", "semantic_discriminator", "intent_router"]
SINGLE_GOAL = {"question_mode": "single_goal", "hypotheses": [], "concerns": []}

EN = ("I have an expression matrix and TF motif priors borrowed from a related species, so "
      "the priors are noisy. Which workflow lets the data weigh how unreliable the prior is, "
      "probabilistically?")
EN_REQUIREMENT = "how unreliable the prior is, probabilistically"
ZH = ("我有 expression matrix 和 TF motif priors，但先驗借自近緣物種，充滿雜訊和不確定性。"
      "Which workflow 能用機率量化先驗不可靠的程度？")
ZH_REQUIREMENT = "用機率量化先驗不可靠的程度"


class StagedProvider(FixtureProvider):
    """FixtureProvider plus scripted goal-review and method-comparison replies."""

    def __init__(self, framing=SINGLE_GOAL, comparison=None):
        item = ambiguous_hypothesis()
        super().__init__(
            first={"request_mode": "guidance", "semantic_goal": "Network guidance",
                   "outcome_hypotheses": [item]},
            review={"request_mode": "guidance", "semantic_goal": "Network guidance",
                    "outcome_hypothesis": item},
        )
        self.framing, self.comparison = framing, comparison

    def with_structured_output(self, schema, **kwargs):
        scripted = {"ResearchFraming": self.framing, "MethodComparisonReview": self.comparison}
        if schema.__name__ not in scripted:
            return super().with_structured_output(schema, **kwargs)
        provider, result = self, scripted[schema.__name__]

        class Adapter:
            def invoke(self, messages):
                provider.calls.append((schema, messages))
                if isinstance(result, BaseException):
                    raise result
                return result

        return Adapter()


def gap_reply(quote):
    return {"requested_philosophy": ["bayesian"], "requirement_quote": quote,
            "claims": [], "preference": None, "capability_gap": None}


def run(prompt, provider, language="en"):
    scenario = RoutingScenario.model_validate({
        "id": "stage-composition", "language": language, "category": "positive",
        "prompt": prompt, "expected": {"status": "ambiguous", "actions": []},
    })
    return evaluate([scenario], provider=provider, model_name="fixture")["results"][0]


def _usage(*calls):
    return SimpleNamespace(calls=[SimpleNamespace(role=role, status=status) for role, status in calls])


def _decision(**update):
    return TaskDecision(action="no_tool", in_scope=True, should_execute=False,
                        intent_type="answer_question", confidence=0.9, reason="guidance", **update)


@pytest.mark.parametrize("calls, update, yielded", [
    ((), {}, True),
    ((("hypothesis_bases", "success"),), {}, True),
    ((("hypothesis_bases", "failed"),), {}, False),
    ((("hypothesis_bases", "success"),), {"match_basis": "unverified_evidence"}, False),
])
def test_only_a_successful_review_without_a_comparison_yields(calls, update, yielded):
    assert framing_yielded(_decision(**update), _usage(*calls)) is yielded


def test_a_validated_comparison_keeps_the_method_stage_out():
    from netzoo_agent_core.contracts.outcomes import StatedHypothesis
    decision = _decision(stated_hypotheses=[StatedHypothesis(
        axis="multiple_hypotheses", basis="run_giraffe", text_span="TF activity",
        target_artifact="tf_activity_matrix", target_granularity="aggregate",
    )])
    assert not framing_yielded(decision, _usage(("hypothesis_bases", "success")))


@pytest.mark.parametrize("prompt, quote, language, roles", [
    (EN, EN_REQUIREMENT, "en", [*ROUTING, "hypothesis_bases", "selection_conditions"]),
    # 不確定性 is the topic ("uncertainty"), not an undecided user; it still
    # triggers the early review, which must not cost the gap.
    (ZH, ZH_REQUIREMENT, "mixed", ["hypothesis_bases", *ROUTING, "selection_conditions"]),
])
def test_a_single_goal_review_still_reports_the_missing_philosophy(prompt, quote, language, roles):
    assert explicit_research_choice(prompt) is (language == "mixed")
    result = run(prompt, StagedProvider(comparison=gap_reply(quote)), language)

    assert result["call_roles"] == roles
    assert not [error for error in result["errors"] if error.startswith("call_limit")]
    answer = result["answer"]
    assert answer.startswith("Yes, in principle, data can weaken an unreliable TF-binding prior")
    assert "No qualified registered workflow fully matches" in answer
    assert "aggregate or sample-specific" not in answer
    assert "(recommend)" not in answer
    assert result["action"] == "no_tool" and not result["should_execute"]


def test_a_validated_comparison_is_not_followed_by_a_condition_call():
    prompt = ("I have an expression matrix and TF motif priors. Which workflow should I use: "
              "per-sample TF activity levels or one cohort TF-gene wiring network?")
    framing = {"question_mode": "multiple_hypotheses", "concerns": [], "hypotheses": [
        {"text_span": "per-sample TF activity levels", "profile": "tf_activity_matrix"},
        {"text_span": "one cohort TF-gene wiring network", "profile": "regulatory_network",
         "granularity": "aggregate", "regulators": ["tf"]},
    ]}
    result = run(prompt, StagedProvider(framing=framing, comparison=gap_reply("TF activity")))

    assert result["call_roles"][-1] == "hypothesis_bases"
    assert "selection_conditions" not in result["call_roles"]
    assert len({h["text_span"] for h in result["stated_hypotheses"]}) == 2


def test_a_failed_review_does_not_fall_back_to_the_method_stage():
    result = run(EN, StagedProvider(framing=RuntimeError("provider down"),
                                    comparison=gap_reply(EN_REQUIREMENT)))

    assert result["call_roles"] == [*ROUTING, "hypothesis_bases"]
    assert "No qualified registered workflow" not in result["answer"]
