"""Log 300: a condition the request never states (II-B), stated modules (II-C).

Each is replayed from the recorded replies of Log 299 (II-A was withdrawn, Log 301):
- "Which workflow finds gene modules within each patient?" was quoted as
  stating that the regulators include miRNAs, and LIONESS-PUMA was recommended;
- the same request read as an unknown result tied the per-sample networks.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))

import evaluate_routing  # noqa: E402
from evaluate_routing import RoutingScenario, evaluate  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    ConditionClaim, OutcomeHypothesis, RequestedOutcome, SelectionConditionClaims,
    SemanticInterpretation,
)
from netzoo_agent_core.graph.condition_recommender import condition_options, recommend_from_claims  # noqa: E402
from netzoo_agent_core.interpretation.concept_answers import render_capability_gap  # noqa: E402
from netzoo_agent_core.interpretation.stated_field_restoration import (  # noqa: E402
    _stated_partition, restore_stated_fields,
)
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from test_sibling_only_reduction import RecordedProvider  # noqa: E402

POLICY = ProjectPolicyLoader(HERE.parent).load()
MODULES = "Which workflow finds gene modules within each patient? Advice only."


def _replay(fixture, monkeypatch):
    recorded = json.loads((HERE / fixture).read_text(encoding="utf-8"))
    decisions = []
    original = evaluate_routing.invoke_router

    def recording(context, state, prompt):
        result = original(context, state, prompt)
        decisions.append(result.decision)
        return result

    monkeypatch.setattr(evaluate_routing, "invoke_router", recording)
    case = RoutingScenario.model_validate({
        "id": "log300", "language": "en", "category": "positive", "prompt": recorded["prompt"],
        "expected": {"status": "ambiguous", "actions": []},
    })
    evaluate([case], provider=RecordedProvider(recorded["calls"]), model_name="recorded")
    return decisions[0]


# --- II-B: a regulator condition the request never states ---------------------

def _claims(task):
    claims = SelectionConditionClaims(claims=[ConditionClaim(condition="regulator_class:mirna", text_span=task)])
    candidates = ["run_lioness_panda", "run_lioness_puma"]
    return recommend_from_claims(task, claims, condition_options(candidates), candidates)


def test_a_quote_that_names_no_such_molecule_states_no_regulator_condition():
    recommendation, rejected = _claims(MODULES)
    assert recommendation is None
    assert rejected == [{"condition": "regulator_class:mirna", "reason": "condition_not_in_request"}]


@pytest.mark.parametrize("task", [
    "Another type of 'short non-coding molecule' directly degraded the products post-transcription.",
    "My prior lists predicted targets of some small RNAs; they are listed in mirna.txt.",
])
def test_a_request_describing_the_molecules_keeps_the_condition(task):
    recommendation, _ = _claims(task)
    assert recommendation is not None and recommendation.action == "run_lioness_puma"


MIRNA_DEGRADATION = (
    "We found a set of genes heavily suppressed in the cells, but this isn't because upstream "
    "regulatory proteins failed to bind. Instead, another type of 'short non-coding molecule' "
    "directly degraded the products post-transcription. Do you have a tool specifically for "
    "this class of molecules?"
)


def test_the_evidence_words_may_sit_outside_the_quote():
    """Log 269 / Log 300: a functional description elsewhere in the request states the class.

    The recorded quote of mirna-degradation-en names no molecule; the request
    around it does. Checking only the quote rejected it (restored after Log 303).
    """
    quote = "Do you have a tool specifically for this class of molecules?"
    claims = SelectionConditionClaims(claims=[ConditionClaim(condition="regulator_class:mirna", text_span=quote)])
    candidates = ["run_lioness_panda", "run_lioness_puma"]
    recommendation, rejected = recommend_from_claims(
        MIRNA_DEGRADATION, claims, condition_options(candidates), candidates,
    )
    assert recommendation is not None and recommendation.action == "run_lioness_puma"
    assert rejected == []


def test_the_recorded_modules_tie_no_longer_recommends_lioness_puma(monkeypatch):
    # With II-C the first pass is already the community gap; either way no
    # LIONESS-PUMA recommendation rests on an unstated miRNA premise.
    decision = _replay("log300_modules_tie_calls.json", monkeypatch)
    assert decision.advisory_recommendation is None


# --- II-C: stated modules are the community result ----------------------------

def test_a_stated_module_result_is_found_but_held_modules_are_not():
    assert _stated_partition(MODULES) == "gene modules"
    assert _stated_partition(
        "We already have gene modules from an earlier analysis. Which tool infers a TF-gene network?") is None


def test_an_unknown_result_named_as_modules_becomes_a_community_assignment():
    unknown = RequestedOutcome(operation="infer", artifact_type="unknown", granularity="sample_specific")
    interpretation = SemanticInterpretation(request_mode="guidance", semantic_goal="modules", outcome_hypotheses=[
        OutcomeHypothesis(outcome=unknown, confidence=0.9)])
    restored, record = restore_stated_fields(MODULES, interpretation)
    assert restored.outcome_hypotheses[0].outcome.artifact_type == "community_assignment"
    assert any(item["source"] == "stated_partition_entailment" for item in record)


def test_the_recorded_modules_first_pass_gets_the_community_gap(monkeypatch):
    decision = _replay("log300_modules_first_pass_calls.json", monkeypatch)
    assert decision.capability_match_status == "unsupported"
    assert decision.mismatch_dimensions == ["granularity"] and decision.alternative_actions == ["run_condor"]
    reply = render_capability_gap(decision, POLICY)
    assert "do not produce sample-specific community assignments" in reply
