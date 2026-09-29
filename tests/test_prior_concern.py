"""Log 265 (item 2, user decision A): how each prior-using method treats its prior.

In PANDA, PUMA, OTTER and GIRAFFE the motif prior is only the starting point;
no term of the update or loss pulls the result back to it. A request that says
its prior is noisy or borrowed gets that registry answer, per listed method,
also on ties and in capability-gap replies.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from workflow_registry import ACTION_DEFINITIONS, REQUEST_CONCERNS  # noqa: E402
from netzoo_agent_core.contracts import LLMUsage, TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import AddressedConcern, MethodCapabilityGap, RequestedOutcome  # noqa: E402
from netzoo_agent_core.graph import hypothesis_bases  # noqa: E402
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()
PRIOR_USERS = ("run_panda", "run_puma", "run_lioness_panda", "run_lioness_puma", "run_otter", "run_giraffe")
TIE = ["run_panda", "run_otter", "run_giraffe"]


def _declared(action):
    return next(c for c in REQUEST_CONCERNS[action] if c.concern == "unreliable_prior")


def test_every_prior_using_method_answers_the_concern_without_an_unexposed_knob():
    for action in PRIOR_USERS:
        concern = _declared(action)
        exposed = {control.name for control in ACTION_DEFINITIONS[action].controls}
        assert set(concern.controls) <= exposed, action
        if not concern.controls:
            assert "this agent sets" in concern.note or "inherits" in concern.note, action
    assert set(_declared("run_otter").controls) == {"iterations", "eta", "lam", "gamma"}
    assert "no motif term" in _declared("run_otter").note
    assert "only the starting network" in _declared("run_panda").note


def _decision(**update):
    fields = dict(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question",
        confidence=0.9, reason="tie", capability_match_status="ambiguous",
        hypothesis_actions=list(TIE), clarification_question="Which fits your study?",
        requested_outcome=RequestedOutcome(operation="explain", artifact_type="regulatory_network",
                                           granularity="unknown"),
        addressed_concerns=[AddressedConcern(action=a, concern="unreliable_prior",
                                             text_span="the prior is borrowed") for a in ("run_panda", "run_otter")],
    )
    fields.update(update)
    return TaskDecision(**fields)


def test_a_tie_answers_a_stated_prior_concern_for_the_listed_methods():
    answer = render_outcome_clarification(_decision(), POLICY)

    section = answer.split("About your concern that the prior network is noisy", 1)[1]
    assert "- **PANDA** — The motif prior is only the starting network" in section
    assert "- **OTTER** — OTTER's objective has no motif term" in section
    assert "**GIRAFFE** —" not in section


def test_a_capability_gap_answers_it_for_the_relaxed_alternatives():
    decision = _decision(hypothesis_actions=["run_panda", "run_otter"], advisory_capability_gap=MethodCapabilityGap(
        selection_tags=["bayesian"], text_spans=["x"], rationale="No qualified workflow."))
    answer = render_outcome_clarification(decision, POLICY)

    assert answer.index("If you relax that requirement") < answer.index("About your concern that the prior")
    assert "`iterations` (default 60)" in answer


def test_the_goal_review_offers_the_tie_candidates_concerns(monkeypatch):
    seen = {}

    class Adapter:
        def invoke(self, messages):
            seen["system"] = messages[0].content
            return {"question_mode": "single_goal", "hypotheses": [], "concerns": []}

    llm = SimpleNamespace(with_structured_output=lambda schema, **_: Adapter())
    context = SimpleNamespace(selection_condition_llm=llm, semantic_model_name="fixture", router_max_tokens=200,
                              task_token_budget=20_000, recorder=None, price_catalog=None)
    monkeypatch.setattr(hypothesis_bases, "preflight_budget",
                        lambda *a, **k: (SimpleNamespace(status="ok"), []))
    monkeypatch.setattr(hypothesis_bases, "record_event", lambda *a, **k: None)
    monkeypatch.setattr(hypothesis_bases, "append_llm_usage", lambda usage, **k: usage)
    hypothesis_bases.invoke_hypothesis_matcher(context, {}, "Which of these fits?", _decision(addressed_concerns=[]),
                                               LLMUsage(), [])

    system = seen["system"]
    offered, _ = json.JSONDecoder().raw_decode(system[system.index('{"estimator_constraints"'):])
    assert "unreliable_prior" in dict(offered["offered_concerns"])


def test_a_named_workflow_card_answers_the_concern_by_id():
    from netzoo_agent_core.interpretation.concept_answers import render_registered_workflow_contract_answer
    task = ("I want to build one PANDA network for my tissue from expression, motif and PPI files, but the "
            "motif prior is borrowed from mouse and probably noisy. Does PANDA trust that prior rigidly?")
    decision = _decision(hypothesis_actions=["run_lioness_panda", "run_lioness_puma"], addressed_concerns=[
        AddressedConcern(action="run_lioness_panda", concern="unreliable_prior", text_span="the motif prior is borrowed from mouse")])
    card = render_registered_workflow_contract_answer(task, decision, POLICY)

    assert card.startswith("PANDA:")
    assert "About your concern that the prior network is noisy" in card
    assert "- **PANDA** — The motif prior is only the starting network" in card
