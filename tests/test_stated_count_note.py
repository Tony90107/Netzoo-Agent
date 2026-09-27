"""Log 195: form B quotes a sample count the request gave, and maps it to nothing.

The user decided on 2026-09-26 that a count ("about 400 tumour samples") is
not converted to cohort_size:few/many; the agent asks. Form B then asked
"About how many samples do you have?" of a user who had just said.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis, RequestedOutcome  # noqa: E402
from netzoo_agent_core.graph.condition_recommender import condition_options, separating_question  # noqa: E402
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()
TIE = ["run_lioness_coexpression", "run_bonobo"]


def _form_b(candidates=TIE) -> TaskDecision:
    outcome = RequestedOutcome(operation="infer", artifact_type="coexpression_network",
                               granularity="sample_specific", entity_types=["gene"],
                               input_artifacts=["expression_matrix"])
    return TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question",
        confidence=0.9, reason="guidance", requested_outcome=outcome,
        outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=0.9)],
        hypothesis_actions=list(candidates), capability_match_status="ambiguous",
        clarification_question=separating_question(condition_options(list(candidates)), list(candidates)),
    )


def test_a_stated_count_is_quoted_and_not_mapped():
    task = "Our cohort has about 400 tumour samples with RNA-seq. I want each tumour's own co-expression network."

    answer = render_outcome_clarification(_form_b(), POLICY, task=task)

    assert 'You mentioned "about 400 tumour samples".' in answer
    assert "I do not map a sample count to these categories myself." in answer
    assert "About how many samples do you have?" in answer


def test_a_non_english_count_is_quoted_verbatim():
    answer = render_outcome_clarification(_form_b(), POLICY, task="我們有大約 400 個樣本的表現資料。")

    assert 'You mentioned "大約 400 個樣本".' in answer


def test_no_count_or_no_sample_question_adds_nothing():
    assert "You mentioned" not in render_outcome_clarification(
        _form_b(), POLICY, task="I want each tumour's own co-expression network.",
    )
    decision = _form_b().model_copy(update={"clarification_question": "Is memory a concern?"})
    assert "You mentioned" not in render_outcome_clarification(
        decision, POLICY, task="We have 400 samples.",
    )
