"""Log 188: a tie's reply says what was assumed, and what a read folder holds."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
)
from netzoo_agent_core.interpretation.concept_answers import (  # noqa: E402
    render_outcome_clarification,
)
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_outcome_hypotheses  # noqa: E402

TIE = ["run_panda", "run_otter", "run_giraffe"]


def _decision(artifact_source: str = "inferred", **update) -> TaskDecision:
    outcome = RequestedOutcome(operation="infer", artifact_type="regulatory_network",
                               granularity="aggregate", regulator_types=["tf"],
                               target_types=["gene"], input_artifacts=["expression_matrix"])
    evidence = [OutcomeEvidence(
        dimension="artifact_type", value="regulatory_network", source=artifact_source,
        text_span="regulatory network" if artifact_source == "explicit" else None, rationale="t",
    )]
    fields = dict(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question",
        confidence=1.0, reason="guidance", requested_outcome=outcome,
        outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=0.9, evidence=evidence)],
        hypothesis_actions=list(TIE), capability_match_status="ambiguous",
        clarification_question="Is memory or runtime a concern?",
    )
    fields.update(update)
    return TaskDecision(**fields)


def _answer(decision: TaskDecision) -> str:
    return render_outcome_clarification(decision, ProjectPolicyLoader(ROOT).load())


def test_an_assumed_network_kind_is_said_with_what_it_costs_and_the_alternative():
    answer = _answer(_decision())

    assert "the options above assume regulator-to-target associations." in answer
    assert "Every option above also needs a TF-motif prior and a protein-interaction prior." in answer
    assert "**BONOBO** and **LIONESS-COEXPRESSION** need only the input you named." in answer


def test_a_quoted_network_kind_adds_no_assumption_note():
    assert "options above assume" not in _answer(_decision(artifact_source="explicit"))


def test_files_found_by_content_are_reported_and_not_used():
    decision = _decision(
        inspected_directories=["data/研究/"],
        discovered_inputs=["motif_file=data/研究/基序.tsv", "ppi_file=data/研究/ppi.tsv"],
    )

    answer = _answer(decision)

    assert ("in `data/研究/`, `基序.tsv` as the TF-motif prior, `ppi.tsv` as the "
            "protein-interaction prior. I have not used them") in answer
    assert decision.motif_file is None


def test_divergent_readings_are_asked_in_their_own_terms():
    network = RequestedOutcome(operation="infer", artifact_type="regulatory_network",
                               granularity="sample_specific", regulator_types=["tf"],
                               target_types=["gene"], input_artifacts=["expression_matrix"])
    activity = RequestedOutcome(operation="infer", artifact_type="tf_activity_matrix",
                                granularity="aggregate", input_artifacts=["expression_matrix"])

    match = match_outcome_hypotheses([
        OutcomeHypothesis(outcome=network, confidence=0.9),
        OutcomeHypothesis(outcome=activity, confidence=0.8),
    ])

    assert match.status == "ambiguous"
    assert match.clarification_question.startswith(
        "Which result do you mean: inferred regulator-to-target associations, one result per sample ("
    )
    assert "; or inferred transcription-factor-by-sample activity values (GIRAFFE)?" in match.clarification_question
