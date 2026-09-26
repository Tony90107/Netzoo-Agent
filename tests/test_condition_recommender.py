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
    assert "**LIONESS-COEXPRESSION** — preferred when: dozens of samples or more" in answer
    assert "No files were inspected and no analysis ran." in answer


def test_form_a_quotes_a_non_english_request_verbatim():
    """Log 180: a Chinese quote is user data, not agent-authored text."""
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

    assert answer.startswith('Based on what you said — "少數幾位病人" — **BONOBO** fits better')
