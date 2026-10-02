"""Log 259: quoted study facts > folder contents > a bare model preference.

Blind case 10 ("All I have is this expression matrix, <path>. Build me a
network") received a PANDA recommendation from the condition call's free
preference alone: its only quote was the generic request and its rationale
said the user already had PANDA's inputs, but PANDA also needs a motif and a
PPI prior. That preference also pre-empted the content check of the named
folder, whose discovery note the case requires. A preference whose workflow
needs inputs the request has not established now yields to a named folder,
and otherwise states the missing inputs.

The same log restores, at the user's request, the note that names a
registered method sharing a required philosophy but estimating another result.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from netzoo_agent_core.contracts import LLMUsage  # noqa: E402
from netzoo_agent_core.contracts.outcomes import MethodCapabilityGap, OutcomeHypothesis, RequestedOutcome  # noqa: E402
from netzoo_agent_core.graph.condition_recommender import (  # noqa: E402
    invoke_condition_recommender, unestablished_inputs,
)
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from test_condition_recommender import _context, _decision  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()
NAMED = "All I have is this expression matrix, data/blind-tests/case-1/expression.tsv. Build me a network."
UNNAMED = "All I have is an expression matrix. Build me a network."
TIE = ["run_panda", "run_puma", "run_otter", "run_giraffe"]


def _network_decision():
    outcome = RequestedOutcome(operation="infer", input_artifacts=["expression_matrix"],
                               artifact_type="regulatory_network", granularity="aggregate")
    return _decision(requested_outcome=outcome, hypothesis_actions=list(TIE),
                     outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=.9)])


def _panda_preference(task_quote):
    return {"claims": [], "preference": {
        "action": "run_panda", "selection_tags": ["message_passing"], "text_spans": [task_quote],
        "rationale": "PANDA needs only the expression file, which you have.", "assumptions": [],
    }}


def _events(store, run_id):
    return [event.event_type for event in store.read_events(run_id)]


def test_the_required_inputs_are_read_from_the_registry_and_the_request():
    outcome = _network_decision().requested_outcome
    assert unestablished_inputs(NAMED, "run_panda", outcome) == ["motif_file", "ppi_file"]
    assert unestablished_inputs(UNNAMED, "run_panda", outcome) == ["motif_file", "ppi_file"]
    assert unestablished_inputs(NAMED, "run_bonobo", outcome) == []
    assert unestablished_inputs("Build me a network.", "run_bonobo") == ["expression_file"]


def test_a_bare_preference_yields_to_the_folder_the_request_names(tmp_path):
    ctx, state, store, run_id = _context(tmp_path, _panda_preference("Build me a network."))
    updated, _, _ = invoke_condition_recommender(ctx, state, NAMED, _network_decision(), LLMUsage(), [])

    assert updated.advisory_recommendation is None
    assert "routing.preference_deferred_to_inputs" in _events(store, run_id)
    assert updated.action == "no_tool" and not updated.should_execute


def test_a_generic_request_gets_no_preference_at_all(tmp_path):
    # Log 318: "Build me a network" states nothing that separates PANDA.
    ctx, state, _, _ = _context(tmp_path, _panda_preference("Build me a network."))
    updated, _, _ = invoke_condition_recommender(ctx, state, UNNAMED, _network_decision(), LLMUsage(), [])
    assert updated.advisory_recommendation is None


def test_without_a_named_folder_the_preference_states_what_is_missing(tmp_path):
    task = UNNAMED + " I would like iterative message passing."
    ctx, state, _, _ = _context(tmp_path, _panda_preference("iterative message passing"))
    updated, _, _ = invoke_condition_recommender(ctx, state, task, _network_decision(), LLMUsage(), [])

    recommendation = updated.advisory_recommendation
    assert recommendation.action == "run_panda"
    assert recommendation.assumptions[0].startswith("This starting choice assumes a regulator scope")
    assert recommendation.assumptions[1] == (
        "It also needs a TF-motif prior and protein-interaction prior, which the request does not mention."
    )


def test_a_preference_whose_inputs_are_bound_is_kept(tmp_path):
    task = ("I only have expression data (data/blind-neutral/case-3/expression.tsv) and want "
            "probabilistic uncertainty for each patient's co-expression.")
    ctx, state, store, run_id = _context(tmp_path, {"claims": [], "preference": {
        "action": "run_bonobo", "selection_tags": ["bayesian"], "text_spans": ["probabilistic uncertainty"],
        "rationale": "Bayesian shrinkage matches the requested probabilistic uncertainty.", "assumptions": [],
    }})
    updated, _, _ = invoke_condition_recommender(ctx, state, task, _decision(), LLMUsage(), [])

    assert updated.advisory_recommendation.action == "run_bonobo"
    assert "routing.preference_deferred_to_inputs" not in _events(store, run_id)
    assert not any("does not mention" in item for item in updated.advisory_recommendation.assumptions)


def test_an_unmentioned_expression_matrix_is_named_as_missing(tmp_path):
    task = "Gene co-expression seems to change across our tumours; we want probabilistic uncertainty. Which workflow fits?"
    outcome = RequestedOutcome(operation="explain", artifact_type="coexpression_network",
                               granularity="sample_specific")
    ctx, state, _, _ = _context(tmp_path, {"claims": [], "preference": {
        "action": "run_bonobo", "selection_tags": ["bayesian"], "text_spans": ["probabilistic uncertainty"],
        "rationale": "Bayesian shrinkage of per-sample co-expression.", "assumptions": [],
    }})
    decision = _decision(requested_outcome=outcome,
                         outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=.9)])
    updated, _, _ = invoke_condition_recommender(ctx, state, task, decision, LLMUsage(), [])

    assert updated.advisory_recommendation.assumptions == [
        "It also needs an expression matrix, which the request does not mention.",
    ]


def test_a_quoted_study_fact_still_outranks_the_folder(tmp_path):
    task = ("I only have expression data from a handful of patients "
            "(data/blind-neutral/case-3/expression.tsv) and want each patient's co-expression.")
    ctx, state, _, _ = _context(tmp_path, {"claims": [
        {"condition": "cohort_size:few", "text_span": "a handful of patients"},
    ]})
    updated, _, _ = invoke_condition_recommender(ctx, state, task, _decision(), LLMUsage(), [])

    assert updated.advisory_recommendation.action == "run_bonobo"
    assert updated.advisory_recommendation.conditions[0].text_span == "a handful of patients"


def _gap_answer(tags, candidates, artifact="regulatory_network"):
    decision = _decision(
        requested_outcome=RequestedOutcome(operation="explain", artifact_type=artifact, granularity="unknown"),
        hypothesis_actions=candidates,
        advisory_capability_gap=MethodCapabilityGap(selection_tags=tags, text_spans=["x"], rationale="No qualified workflow."),
    )
    return render_outcome_clarification(decision, POLICY)


def test_a_method_with_the_required_philosophy_but_another_result_is_named_not_offered():
    answer = _gap_answer(["partial_correlation"], ["run_panda", "run_otter"])

    different, _, alternatives = answer.partition("Conditional alternatives")
    # Log 290: LIONESS-DRAGON shares DRAGON's philosophy and result type.
    assert "Registered methods with that philosophy estimate different results:\n- **DRAGON**" in different
    assert "- **LIONESS-DRAGON** — declared output: multi omic network (one per sample)" in different
    assert "declared output: multi omic network" in different
    assert "DRAGON" not in alternatives and "(recommend)" not in different


def test_a_candidate_that_already_carries_the_tag_is_not_repeated():
    answer = _gap_answer(["bayesian"], ["run_panda", "run_otter", "run_bonobo"])

    assert "estimates a different result" not in answer
