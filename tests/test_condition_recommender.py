"""Log 139: experimental-condition claims recommend among method ties, advisory only."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts import LLMUsage, TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeHypothesis,
    RequestedOutcome,
    SelectionConditionClaims,
)
from netzoo_agent_core.graph.condition_recommender import (  # noqa: E402
    condition_options,
    invoke_condition_recommender,
    is_method_tie,
    recommend_from_claims,
)
from netzoo_agent_core.interpretation.concept_answers import (  # noqa: E402
    render_outcome_clarification,
)
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.pricing import PriceCatalog  # noqa: E402
from netzoo_agent_core.routing.clarification_planner import plan_clarification  # noqa: E402
from netzoo_agent_core.trace_store import LocalTraceStore  # noqa: E402
from netzoo_agent_core.tracing import TraceRecorder  # noqa: E402
from workflow_registry import OUTPUT_CAPABILITIES, SELECTION_AXES  # noqa: E402

TASK = (
    "I only have expression data from a handful of patients "
    "(data/blind-neutral/case-3/expression.tsv) and no prior files. I want to see how "
    "each patient's own gene co-expression structure differs, and ideally know which "
    "connections are trustworthy in that particular patient."
)
TIE = ["run_lioness_coexpression", "run_bonobo"]
AUTHORITY_FIELDS = ("action", "should_execute", "capability_match_status", "matched_actions")


def _outcome() -> RequestedOutcome:
    return RequestedOutcome(
        operation="infer", input_artifacts=["expression_matrix"],
        artifact_type="coexpression_network", entity_types=["gene", "sample"],
        granularity="sample_specific",
    )


def _decision(**update) -> TaskDecision:
    outcome = _outcome()
    fields = dict(
        action="no_tool", in_scope=True, should_execute=False,
        intent_type="answer_question", confidence=1.0, reason="guidance",
        requested_outcome=outcome,
        outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=0.9)],
        hypothesis_actions=list(TIE), capability_match_status="ambiguous",
        clarification_question="Which modeling assumption best matches your experiment?",
    )
    fields.update(update)
    return TaskDecision(**fields)


def _context(tmp_path, parsed):
    store = LocalTraceStore(tmp_path / "traces")
    recorder = TraceRecorder(store)
    run_id = recorder.start_run(session_id="log139", profile_id="default")
    adapter = SimpleNamespace(invoke=lambda _messages: {"parsed": parsed, "raw": object()})
    llm = SimpleNamespace(with_structured_output=lambda schema, **_: adapter)
    context = SimpleNamespace(
        selection_condition_llm=llm, semantic_claims=False,
        semantic_model_name="fixture", router_max_tokens=200, task_token_budget=10_000,
        recorder=recorder, price_catalog=PriceCatalog(),
    )
    return context, {"run_id": str(run_id)}, store, run_id


def _claims(*pairs) -> SelectionConditionClaims:
    return SelectionConditionClaims.model_validate(
        {"claims": [{"condition": c, "text_span": q} for c, q in pairs]}
    )


# R-b: every algorithm-dimension tie in the Log 137 grid can be asked about.
def test_every_method_tie_in_the_grid_has_a_separating_condition():
    sys.path.insert(0, str(ROOT / "docs" / "research-log"))
    import log136_outcome_grid as grid

    uncovered = set()
    seen = set()
    for key, row in grid.build().items():
        status, _, candidates, _ = row["hyp"]
        if status != "ambiguous" or len(candidates) < 2:
            continue
        outcome = RequestedOutcome(**json.loads(key))
        plan = plan_clarification(candidates, outcomes=[outcome])
        if plan is None or plan.dimension != "algorithm":
            continue
        tie = tuple(sorted(candidates))
        seen.add(tie)
        if not condition_options(list(tie)):
            uncovered.add(tie)

    assert seen, "the grid must contain method ties"
    assert uncovered == set()


def test_prefer_when_conditions_are_registered_axes():
    for capability in OUTPUT_CAPABILITIES.values():
        for condition in capability.prefer_when:
            axis, _, value = condition.partition(":")
            assert value in SELECTION_AXES[axis]["values"], condition


def test_prefer_when_never_reaches_a_model_context_dump():
    """Every capability dump that can reach a model context excludes the field."""
    import re

    offenders = []
    for path in (ROOT / "scripts" / "netzoo_agent_core").rglob("*.py"):
        for match in re.finditer(r"output_capability\.model_dump\(([^)]*)\)", path.read_text()):
            if "prefer_when" not in match.group(1):
                offenders.append(f"{path.name}: {match.group(0)}")
    assert offenders == []
    assert ProjectPolicyLoader(ROOT).load().workflows["run_bonobo"].output_capability.prefer_when


def test_multi_valued_axis_needs_every_candidate_to_declare_it():
    offered = {option.condition for option in condition_options(TIE)}
    assert "covariates:no" not in offered
    assert {"cohort_size:few", "cohort_size:many", "per_edge_confidence:needed"} <= offered


# R-c: deterministic claim handling.
def test_grounded_claims_recommend_the_single_supported_candidate():
    recommendation, rejected = recommend_from_claims(
        TASK,
        _claims(("cohort_size:few", "a handful of patients"),
                ("per_edge_confidence:needed", "which connections are trustworthy")),
        condition_options(TIE), TIE,
    )
    assert recommendation is not None and recommendation.action == "run_bonobo"
    assert rejected == []


def test_ungrounded_quote_is_rejected_and_nothing_is_recommended():
    recommendation, rejected = recommend_from_claims(
        TASK, _claims(("cohort_size:few", "only three samples")), condition_options(TIE), TIE,
    )
    assert recommendation is None
    assert rejected == [{"condition": "cohort_size:few", "reason": "quote_not_in_request"}]


def test_condition_outside_the_offer_is_rejected():
    recommendation, rejected = recommend_from_claims(
        TASK, _claims(("compute_constraints:constrained", "a handful of patients")),
        condition_options(TIE), TIE,
    )
    assert recommendation is None
    assert rejected[0]["reason"] == "not_offered"


def test_conflicting_claims_recommend_nothing():
    task = TASK + " We have dozens of samples overall."
    recommendation, rejected = recommend_from_claims(
        task,
        _claims(("cohort_size:few", "a handful of patients"),
                ("cohort_size:many", "dozens of samples")),
        condition_options(TIE), TIE,
    )
    assert recommendation is None
    assert rejected[-1]["reason"] == "claims_do_not_select_one"


def test_philosophy_preference_cannot_override_conflicting_study_facts(tmp_path):
    task = TASK + " We have dozens of samples overall."
    parsed = _philosophy_preference()
    parsed["claims"] = [
        {"condition": "cohort_size:few", "text_span": "a handful of patients"},
        {"condition": "cohort_size:many", "text_span": "dozens of samples"},
    ]
    context, state, _, _ = _context(tmp_path, parsed)
    updated, _, _ = invoke_condition_recommender(context, state, task, _decision(), LLMUsage(), [])
    assert updated.advisory_recommendation is None
    assert not updated.should_execute


def test_non_english_model_prose_does_not_crash_advisory_rendering(tmp_path):
    task = "We need probabilistic uncertainty，病患個別共表現網路。"
    parsed = _philosophy_preference()
    parsed["preference"].update(
        rationale="Bayesian shrinkage addresses 病患個別共表現網路.",
        assumptions=["The goal is 病患個別共表現網路."],
    )
    context, state, _, _ = _context(tmp_path, parsed)
    updated, _, _ = invoke_condition_recommender(context, state, task, _decision(), LLMUsage(), [])
    assert updated.advisory_recommendation is not None
    answer = render_outcome_clarification(updated, ProjectPolicyLoader(ROOT).load())
    assert "BONOBO" in answer and answer.count("(recommend)") == 1
    assert "Confirm that the biological scope" in answer


def test_chinese_evidence_is_kept_for_grounding_but_not_echoed_in_english_advice(tmp_path):
    task = "我需要每位病患各自的共表現網路，並希望量化連線可信度。"
    parsed = {"claims": [], "preference": {
        "action": "run_bonobo", "selection_tags": ["bayesian"],
        "text_spans": ["量化連線可信度"],
        "rationale": "Conditional Bayesian co-expression starting method.",
        "assumptions": [],
    }}
    context, state, _, _ = _context(tmp_path, parsed)
    updated, _, _ = invoke_condition_recommender(context, state, task, _decision(), LLMUsage(), [])
    assert updated.advisory_recommendation.supporting_spans == ["量化連線可信度"]
    answer = render_outcome_clarification(updated, ProjectPolicyLoader(ROOT).load())
    assert "BONOBO" in answer and answer.count("(recommend)") == 1
    assert "量化連線可信度" not in answer
    assert all(not ("\u3400" <= ch <= "\u9fff") for ch in answer)


def test_same_network_subject_can_receive_conditional_regulator_advice(tmp_path):
    task = "Each patient has one blood expression measurement. We need individual regulatory wiring."
    parsed = {"claims": [], "preference": {
        "action": "run_lioness_panda", "selection_tags": ["leave_one_out_network_inference"],
        "text_spans": ["individual regulatory wiring"],
        "rationale": "LIONESS estimates individual wiring from cohort and leave-one-out networks.",
        "assumptions": ["The requested regulators are transcription factors; use LIONESS-PUMA if miRNAs must be included."],
    }}
    context, state, _, _ = _context(tmp_path, parsed)
    outcome = RequestedOutcome(operation="explain", artifact_type="regulatory_network",
                               granularity="sample_specific")
    decision = _decision(requested_outcome=outcome,
                         outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=.9)],
                         hypothesis_actions=["run_lioness_panda", "run_lioness_puma"])
    updated, _, _ = invoke_condition_recommender(context, state, task, decision, LLMUsage(), [])
    assert updated.advisory_recommendation.action == "run_lioness_panda"
    assert updated.matched_actions == [] and not updated.should_execute
    answer = render_outcome_clarification(updated, ProjectPolicyLoader(ROOT).load())
    assert answer.count("(recommend)") == 1
    assert "W_q = N*W_all - (N-1)*W_without_q" in answer
    assert "LIONESS-PUMA" in answer and "Conditional assumptions" in answer


@pytest.mark.parametrize("parsed, expect_recommendation", [
    ({"claims": [{"condition": "cohort_size:few", "text_span": "a handful of patients"}]}, True),
    ({"claims": [{"condition": "cohort_size:few", "text_span": "invented quote"}]}, False),
    ({"claims": []}, False),
    ({"claims": "not a list"}, False),
])
def test_stage_never_changes_execution_authority(tmp_path, parsed, expect_recommendation):
    context, state, _, _ = _context(tmp_path, parsed)
    decision = _decision()

    updated, _, _ = invoke_condition_recommender(context, state, TASK, decision, LLMUsage(), [])

    for field in AUTHORITY_FIELDS:
        assert getattr(updated, field) == getattr(decision, field), field
    assert (updated.advisory_recommendation is not None) is expect_recommendation
    if expect_recommendation:
        assert updated.clarification_question.startswith("Should I use BONOBO")
    else:
        assert updated.clarification_question.startswith("Both fit; to choose, tell me:")


def test_stage_skips_non_method_ties(tmp_path):
    context, state, _, _ = _context(tmp_path, {"claims": []})
    decision = _decision(clarification_question="Should the result be aggregate or sample-specific?")
    outcome = _outcome().model_copy(update={"granularity": "unknown", "entity_types": ["gene"]})
    decision = decision.model_copy(update={
        "hypothesis_actions": ["run_lioness_coexpression", "run_cobra"],
        "outcome_hypotheses": [OutcomeHypothesis(outcome=outcome, confidence=0.9)],
        "requested_outcome": outcome,
    })
    assert not is_method_tie(decision)

    updated, _, _ = invoke_condition_recommender(context, state, TASK, decision, LLMUsage(), [])

    assert updated == decision


def test_form_a_renders_the_quote_and_the_alternative():
    policy = ProjectPolicyLoader(ROOT).load()
    recommendation, _ = recommend_from_claims(
        TASK, _claims(("cohort_size:few", "a handful of patients")), condition_options(TIE), TIE,
    )
    decision = _decision(
        advisory_recommendation=recommendation,
        clarification_question="Should I use BONOBO, or does another listed option fit your study better?",
    )

    answer = render_outcome_clarification(decision, policy)

    assert answer.startswith('Based on what you said — "a handful of patients" — **BONOBO** fits better')
    assert "Your question asks for per-sample coexpression network" in answer
    assert "BONOBO applies Bayesian estimation and shrinkage" in answer
    assert "**LIONESS-COEXPRESSION** — preferred when: dozens of samples or more" in answer
    assert "No files were inspected and no analysis ran." in answer


def test_grounded_method_reason_explains_question_without_changing_claim_choice(tmp_path):
    parsed = {
        "claims": [{"condition": "cohort_size:few", "text_span": "a handful of patients"}],
        "preference": {
            "action": "run_bonobo", "selection_tags": ["bayesian"],
            "text_spans": ["each patient's own gene co-expression structure"],
            "rationale": (
                "Bayesian shrinkage borrows cohort information to temper noisy "
                "per-patient co-expression estimates from this small study."
            ),
            "assumptions": [],
        },
    }
    context, state, _, _ = _context(tmp_path, parsed)
    updated, _, _ = invoke_condition_recommender(context, state, TASK, _decision(), LLMUsage(), [])
    assert updated.advisory_recommendation.action == "run_bonobo"
    answer = render_outcome_clarification(updated, ProjectPolicyLoader(ROOT).load())
    assert "Why it addresses this question: Bayesian shrinkage borrows cohort information" in answer

    parsed["preference"]["action"] = "run_lioness_coexpression"
    parsed["preference"]["selection_tags"] = ["leave_one_out_network_inference"]
    parsed["preference"]["rationale"] = "A conflicting model preference must not override the quoted condition."
    context, state, _, _ = _context(tmp_path, parsed)
    updated, _, _ = invoke_condition_recommender(context, state, TASK, _decision(), LLMUsage(), [])
    assert updated.advisory_recommendation.action == "run_bonobo"
    answer = render_outcome_clarification(updated, ProjectPolicyLoader(ROOT).load())
    assert "conflicting model preference" not in answer


def test_form_a_keeps_chinese_evidence_in_decision_but_replies_in_english():
    """Ground the recommendation without echoing a non-English excerpt."""
    task = "我手上只有少數幾位病人的表現量資料，想看每位病人自己的基因共表現結構。"
    policy = ProjectPolicyLoader(ROOT).load()
    recommendation, _ = recommend_from_claims(
        task, _claims(("cohort_size:few", "少數幾位病人")), condition_options(TIE), TIE,
    )
    decision = _decision(
        advisory_recommendation=recommendation,
        clarification_question="Should I use BONOBO, or does another listed option fit your study better?",
    )

    answer = render_outcome_clarification(decision, policy)

    assert recommendation.conditions[0].text_span == "少數幾位病人"
    assert answer.startswith("Based on the stated study conditions, **BONOBO** fits better")
    assert "少數幾位病人" not in answer


def _philosophy_preference(**overrides):
    preference = {
        "action": "run_bonobo", "selection_tags": ["bayesian"],
        "text_spans": ["probabilistic uncertainty"],
        "rationale": "Bayesian shrinkage matches the requested probabilistic uncertainty.",
        "assumptions": [],
    }
    return {"claims": [], "preference": {**preference, **overrides}}


@pytest.mark.parametrize("claim_contract", [False, True])
def test_algorithm_philosophy_recommends_one_candidate_and_keeps_user_choice(tmp_path, claim_contract):
    task = "Which method estimates each patient's gene coexpression with probabilistic uncertainty?"
    context, state, _, _ = _context(tmp_path, _philosophy_preference())
    context.semantic_claims = claim_contract
    decision = _decision()

    updated, _, _ = invoke_condition_recommender(context, state, task, decision, LLMUsage(), [])

    assert updated.advisory_recommendation is not None
    assert updated.advisory_recommendation.action == "run_bonobo"
    for field in AUTHORITY_FIELDS:
        assert getattr(updated, field) == getattr(decision, field)
    answer = render_outcome_clarification(updated, ProjectPolicyLoader(ROOT).load())
    assert answer.count("(recommend)") == 1
    assert "BONOBO" in answer and "LIONESS-COEXPRESSION" in answer
    assert "Bayesian" in answer and "Method premise:" in answer
    assert "Should I use BONOBO" in answer


@pytest.mark.parametrize("overrides", [
    {"action": "run_panda"},
    {"selection_tags": ["relaxed_graph_matching"]},
    {"text_spans": ["a fabricated request quote"]},
])
def test_preference_cannot_add_a_candidate_or_invent_its_philosophy(tmp_path, overrides):
    context, state, _, _ = _context(tmp_path, _philosophy_preference(**overrides))
    decision = _decision()
    updated, _, _ = invoke_condition_recommender(
        context, state, "I want probabilistic uncertainty", decision, LLMUsage(), [],
    )
    assert updated.advisory_recommendation is None
    assert updated.hypothesis_actions == decision.hypothesis_actions
    assert updated.action == "no_tool" and not updated.should_execute


def _regulatory_decision(granularity="aggregate"):
    outcome = RequestedOutcome(operation="explain", artifact_type="regulatory_network",
                               granularity=granularity)
    candidates = ["run_panda", "run_otter"] if granularity == "aggregate" else ["run_lioness_panda", "run_lioness_puma"]
    return _decision(requested_outcome=outcome, hypothesis_actions=candidates,
                     outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=.9)])


def test_unavailable_prior_uncertainty_is_a_gap_not_a_false_recommendation(tmp_path):
    task = "How can Bayesian probabilities quantify uncertain binding-site priors?"
    parsed = {"claims": [], "rationale": "", "capability_gap": {
        "selection_tags": ["bayesian"], "text_spans": ["Bayesian probabilities"],
        "rationale": "The qualified regulatory methods do not quantify posterior motif reliability.",
    }}
    ctx, state, _, _ = _context(tmp_path, parsed)
    decision = _regulatory_decision()
    updated, _, _ = invoke_condition_recommender(ctx, state, task, decision, LLMUsage(), [])
    assert updated.advisory_capability_gap is not None
    assert updated.advisory_recommendation is None
    for field in AUTHORITY_FIELDS:
        assert getattr(updated, field) == getattr(decision, field)
    answer = render_outcome_clarification(updated, ProjectPolicyLoader(ROOT).load())
    assert "PANDA" in answer and "OTTER" in answer
    assert "(recommend)" not in answer
    # Log 259 (user decision): the Bayesian workflow is named only as a method
    # with the same philosophy and a different result, never as an alternative.
    different, _, alternatives = answer.partition("If you relax that requirement")
    assert "A registered method with that philosophy estimates a different result:\n- **BONOBO**" in different
    assert "does not model uncertain TF-binding/motif priors" in different
    assert "BONOBO" not in alternatives
    assert "PANDA and OTTER tie only on the stated output and scope" in answer
    assert "PUMA" not in answer
    assert "these registered approaches can infer the requested network through different assumptions" in answer
    assert "the hierarchical model above remains the recommendation" in answer
    assert "No qualified registered workflow" in answer


def test_nonempty_unknown_model_field_still_fails_structured_review(tmp_path):
    task = "How can Bayesian probabilities quantify uncertain binding-site priors?"
    parsed = {"claims": [], "rationale": "An unregistered claim", "capability_gap": {
        "selection_tags": ["bayesian"], "text_spans": ["Bayesian probabilities"],
        "rationale": "No qualified regulatory workflow estimates prior reliability.",
    }}
    ctx, state, _, _ = _context(tmp_path, parsed)
    updated, _, _ = invoke_condition_recommender(ctx, state, task, _regulatory_decision(), LLMUsage(), [])
    assert updated.advisory_capability_gap is None
    assert updated.action == "no_tool" and not updated.should_execute


@pytest.mark.parametrize("tags,quote", [
    (["invented_bayesian_prior"], "Bayesian probabilities"),
    (["message_passing"], "Bayesian probabilities"),
    (["bayesian"], "fabricated quote"),
])
def test_gap_requires_registered_missing_philosophy_and_grounded_quote(tmp_path, tags, quote):
    ctx, state, _, _ = _context(tmp_path, {"claims": [], "capability_gap": {
        "selection_tags": tags, "text_spans": [quote], "rationale": "A missing philosophy.",
    }})
    updated, _, _ = invoke_condition_recommender(ctx, state, "Bayesian probabilities", _regulatory_decision(), LLMUsage(), [])
    assert updated.advisory_capability_gap is None
    assert updated.action == "no_tool" and not updated.should_execute


def test_same_subject_role_choice_marks_conditional_start_and_keeps_alternative(tmp_path):
    task = "Estimate each patient's regulatory wiring."
    ctx, state, _, _ = _context(tmp_path, _philosophy_preference(
        action="run_lioness_panda", selection_tags=["leave_one_out_network_inference"],
        text_spans=["each patient's regulatory wiring"],
        rationale="Cohort contributions yield the requested patient-specific edge estimates.",
    ))
    decision = _regulatory_decision("sample_specific")
    updated, _, _ = invoke_condition_recommender(ctx, state, task, decision, LLMUsage(), [])
    assert updated.advisory_recommendation.action == "run_lioness_panda"
    answer = render_outcome_clarification(updated, ProjectPolicyLoader(ROOT).load())
    assert answer.count("(recommend)") == 1 and "LIONESS-PUMA" in answer
    assert "assumes a regulator scope" in answer and "W_q = N*W_all" in answer
    assert updated.action == "no_tool" and not updated.should_execute


def test_unoffered_algorithm_tag_cannot_become_a_study_condition(tmp_path):
    ctx, state, _, _ = _context(tmp_path, {"claims": [{
        "condition": "leave_one_out_network_inference", "text_span": "patient wiring",
    }]})
    updated, _, _ = invoke_condition_recommender(ctx, state, "patient wiring", _regulatory_decision("sample_specific"), LLMUsage(), [])
    assert updated.advisory_recommendation is None
    assert updated.action == "no_tool" and not updated.should_execute


def test_required_unavailable_philosophy_takes_priority_over_unrelated_conditions(tmp_path):
    ctx, state, _, _ = _context(tmp_path, {
        "requested_philosophy": ["bayesian"], "requirement_quote": "probabilistic prior uncertainty",
        "claims": [{"condition": "compute_constraints:constrained", "text_span": "prior uncertainty"}],
        "preference": None, "capability_gap": None,
    })
    decision = _regulatory_decision()
    updated, _, _ = invoke_condition_recommender(ctx, state, "quantify probabilistic prior uncertainty", decision, LLMUsage(), [])
    assert updated.advisory_capability_gap.selection_tags == ["bayesian"]
    assert updated.advisory_recommendation is None
    for field in AUTHORITY_FIELDS:
        assert getattr(updated, field) == getattr(decision, field)
