"""Registry-wide typed routing contracts; raw-model accuracy is tested separately."""

import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts import TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    MethodCapabilityGap, OutcomeEvidence, OutcomeHypothesis, RequestedOutcome,
)
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request, guidance_actions_for  # noqa: E402
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification  # noqa: E402
from netzoo_agent_core.interpretation.verified_guidance import render_verified_guidance  # noqa: E402
from netzoo_agent_core.cli.follow_up import build_next_turn_prompt  # noqa: E402
from netzoo_agent_core.graph.response_context import validated_workflow_context  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()
CASES = json.loads((ROOT / "manual_tests/all_workflow_routing_2026_09_28/cases.json").read_text())
SCIENTIFIC = [item for item in CASES if item.get("expected_artifact")]
METHODS = {
    "run_bonobo": ["bayesian"], "run_cobra": ["covariate_association"],
    "run_condor": ["bipartite_community_detection"], "run_dragon": ["partial_correlation"],
    "run_giraffe": ["biologically_informed_matrix_factorization"],
    "run_lioness_coexpression": ["leave_one_out_network_inference"],
    "run_lioness_panda": ["leave_one_out_network_inference", "message_passing"],
    "run_lioness_puma": ["leave_one_out_network_inference", "message_passing"],
    "run_otter": ["relaxed_graph_matching"], "run_panda": ["message_passing"],
    "run_puma": ["message_passing"], "run_sambar": ["somatic_mutation", "pathway_scores"],
}


def test_every_registered_workflow_has_bilingual_unnamed_method_cases():
    assert set(METHODS) == set(POLICY.workflows)
    for action, spec in POLICY.workflows.items():
        rows = [r for r in CASES if r.get("expected_action") == action and r.get("expected_artifact")]
        assert {r["language"] for r in rows} == {"en", "zh"}
        for row in rows:
            assert spec.workflow.casefold() not in row["prompt"].casefold()


@pytest.mark.parametrize("case", SCIENTIFIC, ids=lambda c: c["id"])
def test_all_scientific_subjects_match_their_registered_workflow(case):
    action = case["expected_action"]
    spec = POLICY.workflows[action]
    cap = spec.output_capability
    outcome = RequestedOutcome(operation="explain", artifact_type=case["expected_artifact"],
                               granularity=case["expected_granularity"],
                               regulator_types=cap.regulator_types, target_types=cap.target_types,
                               entity_types=["sample"] if action == "run_sambar" else cap.entity_types,
                               selection_tags=METHODS[action])
    hypothesis = OutcomeHypothesis(outcome=outcome, confidence=.9, evidence=[
        OutcomeEvidence(dimension="selection_tag", value=tag, source="inferred",
                        rationale="The independent scientific scenario requests this method's mathematical mechanism.")
        for tag in METHODS[action]
    ])
    match = match_semantic_request(case["prompt"], [hypothesis], request_mode="guidance")
    assert action in match.matched_actions + match.hypothesis_actions
    decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False,
                            confidence=.9, reason="Scientific workflow guidance", intent_type="answer_question",
                            requested_outcome=outcome, outcome_hypotheses=[hypothesis],
                            capability_match_status=match.status, matched_actions=match.matched_actions,
                            recommended_actions=guidance_actions_for(match.matched_actions[0]) if len(match.matched_actions) == 1 else [],
                            clarification_question=match.clarification_question,
                            hypothesis_actions=match.hypothesis_actions)
    answer = (render_outcome_clarification(decision, POLICY, task=case["prompt"])
              or render_verified_guidance(decision, validated_workflow_context(decision, POLICY, task=case["prompt"])))
    assert answer is not None and spec.workflow in answer


@pytest.mark.parametrize("artifact,granularity", sorted({
    (case["expected_artifact"], case["expected_granularity"]) for case in SCIENTIFIC
}))
@pytest.mark.parametrize("claims_contract", [False, True])
def test_subject_recovery_covers_every_registered_output_family(artifact, granularity, claims_contract):
    from types import SimpleNamespace
    from test_scientific_guidance_recovery import empty_reading
    from test_semantic_claims import Adapter, claim, context, legacy_context, run
    from netzoo_agent_core.interpretation.guidance_subject import GuidanceSubjectReview
    first = empty_reading()
    if claims_contract:
        first["outcome_hypotheses"][0] = {"confidence": .9, "outcome": {
            "operation": claim("explain"), "artifact_type": claim("unknown"),
            "granularity": claim("not_applicable"),
        }}
    ctx = context(first, AssertionError("Use the compact subject review")) if claims_contract else legacy_context(first, AssertionError("Use the compact subject review"))
    adapter = Adapter({"artifact_type": artifact, "granularity": granularity,
                       "artifact_rationale": "The scientific object is stated in the request.",
                       "granularity_rationale": "The requested unit determines this scale."})
    def bind(schema, **kwargs):
        assert schema is GuidanceSubjectReview
        return adapter
    ctx.selection_condition_llm = SimpleNamespace(with_structured_output=bind)
    # This isolates a schema-valid omitted subject. Prompts with other integrity
    # failures must retain the existing full field-repair path, not skip it.
    task = f"Explain the modeling philosophy for {artifact} at {granularity} scale."
    interpretation, usage, _, error, _ = run(ctx, task)
    assert error is None and interpretation is not None
    assert len(usage.calls) == 2
    outcome = interpretation.outcome_hypotheses[0].outcome
    assert (outcome.artifact_type, outcome.granularity) == (artifact, granularity)
    match = match_semantic_request(task, interpretation.outcome_hypotheses, request_mode="guidance")
    expected = {c["expected_action"] for c in SCIENTIFIC if c["expected_artifact"] == artifact
                and c["expected_granularity"] == granularity}
    assert expected <= set(match.matched_actions + match.hypothesis_actions)


@pytest.mark.parametrize("claims_contract", [False, True])
def test_subject_recovery_can_retain_model_reviewed_current_inputs(claims_contract):
    from types import SimpleNamespace
    from test_scientific_guidance_recovery import empty_reading
    from test_semantic_claims import Adapter, claim, context, legacy_context, run
    first = empty_reading()
    if claims_contract:
        first["outcome_hypotheses"][0] = {"confidence": .9, "outcome": {
            "operation": claim("explain"), "artifact_type": claim("unknown"),
            "granularity": claim("not_applicable"),
        }}
    ctx = context(first, AssertionError("Use focused review")) if claims_contract else legacy_context(first, AssertionError("Use focused review"))
    review = {"artifact_type": "coexpression_network", "granularity": "sample_specific",
              "artifact_rationale": "Gene associations are the scientific subject.",
              "granularity_rationale": "Separate patient networks are requested.",
              "current_inputs": [{"artifact_type": "expression_matrix", "text_span": "expression matrix",
                                  "rationale": "The user explicitly has this input now."}]}
    ctx.selection_condition_llm = SimpleNamespace(with_structured_output=lambda *a, **k: Adapter(review))
    task = "I have an expression matrix. Explain how to infer a gene-gene network for each patient."
    interpretation, usage, _, error, _ = run(ctx, task)
    assert error is None and interpretation is not None
    outcome = interpretation.outcome_hypotheses[0].outcome
    assert outcome.artifact_type == "coexpression_network"
    assert outcome.input_artifacts == ["expression_matrix"] and len(usage.calls) == 2
    evidence = next(e for e in interpretation.outcome_hypotheses[0].evidence if e.dimension == "input_artifact")
    assert evidence.source == "explicit" and evidence.text_span == "expression matrix"


@pytest.mark.parametrize("task", [
    "Previously I used an expression matrix. Explain patient-specific gene association networks.",
    "If I obtain an expression matrix, explain patient-specific gene association networks.",
    "I do not have an expression matrix. Explain patient-specific gene association networks.",
    "Explain patient-specific gene association networks.",
])
@pytest.mark.parametrize("claims_contract", [False, True])
def test_subject_review_cannot_turn_noncurrent_or_fabricated_inputs_into_facts(task, claims_contract):
    from types import SimpleNamespace
    from test_scientific_guidance_recovery import empty_reading
    from test_semantic_claims import Adapter, claim, context, legacy_context, run
    first = empty_reading()
    if claims_contract:
        first["outcome_hypotheses"][0] = {"confidence": .9, "outcome": {
            "operation": claim("explain"), "artifact_type": claim("unknown"),
            "granularity": claim("not_applicable"),
        }}
    ctx = context(first, AssertionError("Use focused review")) if claims_contract else legacy_context(first, AssertionError("Use focused review"))
    review = {"artifact_type": "coexpression_network", "granularity": "sample_specific",
              "artifact_rationale": "Gene associations are the subject.",
              "granularity_rationale": "Per-patient networks are discussed.",
              "current_inputs": [{"artifact_type": "expression_matrix", "text_span": "expression matrix",
                                  "rationale": "This is a deliberately unsupported input claim."}]}
    ctx.selection_condition_llm = SimpleNamespace(with_structured_output=lambda *a, **k: Adapter(review))
    interpretation, usage, _, _, _ = run(ctx, task)
    assert len(usage.calls) == 2
    assert interpretation is None or not interpretation.outcome_hypotheses[0].outcome.input_artifacts


def gap_decision():
    return TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=.9,
                        reason="Required prior-uncertainty philosophy is unavailable", intent_type="answer_question",
                        capability_match_status="ambiguous",
                        requested_outcome=RequestedOutcome(operation="explain", artifact_type="regulatory_network",
                                                           granularity="unknown"),
                        hypothesis_actions=["run_panda", "run_puma", "run_lioness_panda",
                                            "run_lioness_puma", "run_otter", "run_giraffe"],
                        advisory_capability_gap=MethodCapabilityGap(selection_tags=["bayesian"],
                          text_spans=["以機率量化先驗可靠度"], rationale="No qualified workflow estimates posterior motif reliability."),
                        clarification_question="Would you accept a different modeling philosophy, or do you need probabilistic prior reliability?")


def test_missing_philosophy_answers_the_question_before_listing_short_related_methods():
    decision = gap_decision()
    answer = render_outcome_clarification(decision, POLICY)
    assert answer.startswith("Yes, in principle, data can weaken an unreliable TF-binding prior")
    assert "latent TF-gene edges" in answer and "source-reliability parameter" in answer
    assert "Conflicting evidence can lower posterior edge support" in answer
    assert "independent binding evidence or multiple priors" in answer
    assert "registered" in answer
    assert "LIONESS" not in answer
    assert "(recommend)" not in answer
    assert "PANDA and OTTER tie only on the stated output and scope" in answer
    assert "equally robust to a noisy motif prior" in answer
    assert "PUMA" not in answer
    assert "GIRAFFE" not in answer
    assert answer.index("PANDA") < answer.index("OTTER")
    assert "Iterative message passing reconciles the motif seed" in answer
    assert "W W-transpose" in answer and "W-transpose W" in answer
    assert "lambda balances" in answer and "gamma regularizes W" in answer
    assert "PPI-transformed motif matrix initializes W" in answer
    assert "rather than contributing a motif-fidelity term" in answer
    assert "Neither parameter estimates motif-prior reliability" in answer
    assert "The edge weights summarize integrated evidence, not a posterior probability" in answer
    assert "the hierarchical model above remains the recommendation" in answer
    assert "perturb or replace the motif prior" in answer
    assert "which better fits your study" not in answer
    assert "Use this if the intended result" not in answer
    assert "讓數據自己去權衡" not in answer
    assert len(answer) < 2900
    assert decision.action == "no_tool" and not decision.should_execute


def test_tied_alternatives_do_not_gain_recommendation_from_candidate_order():
    decision = gap_decision()
    reversed_decision = decision.model_copy(update={
        "hypothesis_actions": list(reversed(decision.hypothesis_actions)),
    })
    for item in (decision, reversed_decision):
        answer = render_outcome_clarification(item, POLICY)
        assert "PANDA" in answer and "OTTER" in answer
        assert "tie only on the stated output and scope" in answer
        assert "(recommend)" not in answer
        assert "PUMA" not in answer


def test_unstated_input_burden_does_not_break_a_method_philosophy_tie():
    decision = gap_decision()
    workflows = dict(POLICY.workflows)
    otter = workflows["run_otter"]
    workflows["run_otter"] = otter.model_copy(update={
        "required_inputs": [*otter.required_inputs, "extra_unstated_input"],
    })
    policy = POLICY.model_copy(update={"workflows": workflows})

    answer = render_outcome_clarification(decision, policy)

    assert "PANDA and OTTER tie only on the stated output and scope" in answer
    assert "(recommend)" not in answer


def test_conditional_gap_ranking_respects_explicit_mirna_scope():
    decision = gap_decision()
    decision = decision.model_copy(update={"requested_outcome": decision.requested_outcome.model_copy(
        update={"regulator_types": ["mirna"]})})
    answer = render_outcome_clarification(decision, POLICY)
    assert answer.count("(recommend)") == 1
    assert "**PUMA** (recommend)" in answer
    assert "**PANDA**" not in answer and "**OTTER**" not in answer
    assert "does not" in answer and "probabilistic" in answer.lower()


def test_unstated_mirna_scope_never_promotes_an_extra_regulator_class():
    from netzoo_agent_core.interpretation.advisory_answers import _related_gap_actions
    decision = gap_decision()
    assert "run_puma" in decision.hypothesis_actions
    assert "run_puma" not in [action for action, _ in _related_gap_actions(decision, POLICY)]
    assert "run_lioness_puma" not in [action for action, _ in _related_gap_actions(decision, POLICY)]


def test_conditional_gap_ranking_respects_sample_specific_scope_before_base_deduplication():
    decision = gap_decision()
    decision = decision.model_copy(update={"requested_outcome": decision.requested_outcome.model_copy(
        update={"granularity": "sample_specific", "regulator_types": ["tf"]})})
    answer = render_outcome_clarification(decision, POLICY)
    assert "**LIONESS-PANDA** (recommend)" in answer
    assert "**PANDA**" not in answer and "**OTTER**" not in answer
    assert decision.action == "no_tool" and not decision.should_execute


def test_gap_renders_registered_mechanism_for_every_workflow_family():
    from netzoo_agent_core.interpretation.advisory_answers import _conditional_fit
    from netzoo_agent_core.interpretation.method_philosophy import (
        method_philosophies_for, question_fit_for,
    )
    mechanism_evidence = {
        "run_bonobo": "Bayesian estimation and shrinkage",
        "run_cobra": "conditional covariance estimation",
        "run_condor": "bipartite modularity and BRIM",
        "run_dragon": "two-layer Gaussian graphical model",
        "run_giraffe": "jointly factors expression",
        "run_lioness_coexpression": "W_q = N*W_all",
        "run_lioness_panda": "W_q = N*W_all",
        "run_lioness_puma": "W_q = N*W_all",
        "run_otter": "W W-transpose",
        "run_panda": "motif seed with TF-TF interactions",
        "run_puma": "miRNA-target predictions with",
        "run_sambar": "gene-length",
    }
    assert set(mechanism_evidence) == set(POLICY.workflows)
    for action, expected in mechanism_evidence.items():
        spec = POLICY.workflows[action]
        capability = spec.output_capability
        explanation = _conditional_fit(capability)
        assert expected in explanation, action
        outcome = RequestedOutcome(
            operation="explain", artifact_type=capability.artifact_type,
            granularity=sorted(capability.granularities)[0],
        )
        fit = question_fit_for(outcome, spec.workflow, capability)
        assert fit.startswith("Your question asks for "), action
        assert spec.workflow in fit, action
        assert method_philosophies_for(capability.selection_tags)[0].split(". ", 1)[0] in fit, action


@pytest.mark.parametrize("case", [c for c in SCIENTIFIC if c["language"] == "en"], ids=lambda c: c["id"])
def test_shared_gap_ranking_can_include_every_registered_workflow(case):
    from netzoo_agent_core.interpretation.advisory_answers import _related_gap_actions
    cap = POLICY.workflows[case["expected_action"]].output_capability
    decision = TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, confidence=.9,
        reason="Shared alternative ranking", intent_type="answer_question",
        capability_match_status="ambiguous", hypothesis_actions=list(POLICY.workflows),
        requested_outcome=RequestedOutcome(
            operation="explain", artifact_type=case["expected_artifact"],
            granularity=case["expected_granularity"],
            regulator_types=cap.regulator_types, target_types=cap.target_types,
        ),
        advisory_capability_gap=MethodCapabilityGap(
            selection_tags=["bayesian", "partial_correlation"],
            text_spans=["unsupported combined philosophy"],
            rationale="No registered workflow implements the required combination.",
        ),
    )
    ranked = [action for action, _ in _related_gap_actions(decision, POLICY)]
    assert case["expected_action"] in ranked
    answer = render_outcome_clarification(decision, POLICY)
    assert POLICY.workflows[case["expected_action"]].workflow in answer
    assert answer.count("(recommend)") <= 1
    assert decision.action == "no_tool" and not decision.should_execute


def test_next_step_does_not_refer_to_a_question_missing_from_gap_answer():
    decision = gap_decision()
    plan = WorkflowPlan(workflow="NO-TOOL", objective="Conceptual guidance",
                        decision=decision.model_dump(), status="respond_only")
    prompt = build_next_turn_prompt({"plan":plan.model_dump(),"decision":decision.model_dump()})
    answer = render_outcome_clarification(decision, POLICY)
    assert decision.clarification_question not in answer
    assert decision.clarification_question not in prompt.question
    assert "above" not in prompt.question
    assert prompt.kind == "completed"
    assert "follow-up" in prompt.question
    assert not prompt.allow_workflow_continuation and prompt.continuation_action is None
