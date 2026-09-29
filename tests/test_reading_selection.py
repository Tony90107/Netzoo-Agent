"""Log 285: which readings of one request can stand as its result, and whose quote a gap may use.

Blind case 4 ("each patient's regulatory wiring is different ... relate each
person's per-TF regulatory strength over its targets to survival time") was
PARTIAL in three recorded shapes; two were structural, not wording:

- B. A second reading's result was the expression matrix, which no workflow
  produces, so a one-candidate tie stayed open.
- G. The method stage's Bayesian requirement quoted the words that ask for the
  per-patient network, so the reply answered a prior-reliability question
  nobody asked.
- H. A folder-based recommendation did not name the other per-sample reading
  (GIRAFFE's activity), which every other path names (Log 283).

The third shape, a tie between the per-sample network and the TF activity
readings, is the question Logs 150 and 200 keep open and is left as it is.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "scripts"))
sys.path.insert(0, str(HERE))

from evaluate_routing import RoutingScenario, evaluate  # noqa: E402

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    MethodCapabilityGap, OutcomeEvidence, OutcomeHypothesis, RequestedOutcome, SemanticInterpretation,
)
from netzoo_agent_core.graph.condition_recommender import _quotes_the_result  # noqa: E402
from netzoo_agent_core.routing.reading_selection import INPUT_ONLY, drop_input_only_readings  # noqa: E402
from test_sibling_only_reduction import RecordedProvider  # noqa: E402

TASK = ("data/blind-neutral/case-4/ has expression, motif and PPI files. I believe each patient's regulatory "
        "wiring is different, and later I want to relate each person's per-TF regulatory strength over its "
        "targets to survival time.")
WIRING = "each patient's regulatory wiring is different"
STRENGTH = "relate each person's per-TF regulatory strength over its targets to survival time"


def _evidence(dimension, value, span=None):
    return OutcomeEvidence(dimension=dimension, value=value, source="explicit" if span else "inferred", text_span=span,
                           rationale="recorded case 4")


NETWORK = OutcomeHypothesis(
    outcome=RequestedOutcome(operation="infer", artifact_type="regulatory_network", granularity="sample_specific",
                             entity_types=["tf", "gene"], regulator_types=["tf"], target_types=["gene"]),
    confidence=0.8,
    evidence=[_evidence("artifact_type", "regulatory_network", WIRING), _evidence("granularity", "sample_specific", WIRING),
              _evidence("regulator_type", "tf", STRENGTH), _evidence("target_type", "gene", STRENGTH)],
)
ACTIVITY = OutcomeHypothesis(
    outcome=RequestedOutcome(operation="infer", artifact_type="tf_activity_matrix", granularity="aggregate",
                             entity_types=["tf", "sample"]),
    confidence=0.5,
    evidence=[_evidence("artifact_type", "tf_activity_matrix", STRENGTH), _evidence("operation", "infer")],
)
EXPRESSION = OutcomeHypothesis(
    outcome=RequestedOutcome(operation="infer", artifact_type="expression_matrix", granularity="sample_specific"),
    confidence=0.4,
    evidence=[_evidence("artifact_type", "expression_matrix", "expression"), _evidence("operation", "infer")],
)


def _interpretation(*readings):
    return SemanticInterpretation(request_mode="guidance", semantic_goal="case 4", outcome_hypotheses=list(readings))


def test_the_input_only_results_are_derived_from_the_registry():
    assert INPUT_ONLY == {"expression_matrix", "measurement_dataset", "mutation_matrix"}


def test_a_reading_whose_result_is_only_an_input_is_dropped_beside_a_produced_one():
    kept, dropped = drop_input_only_readings(TASK, _interpretation(NETWORK, EXPRESSION))
    assert dropped == ["expression_matrix"] and kept.outcome_hypotheses == [NETWORK]

    alone = _interpretation(EXPRESSION)
    assert drop_input_only_readings(TASK, alone) == (alone, [])


def test_a_gap_may_not_quote_the_words_that_ground_the_result():
    gap = MethodCapabilityGap(selection_tags=["bayesian"], rationale="No qualified workflow.",
                              text_spans=["I believe each patient's regulatory wiring is different"])
    assert _quotes_the_result(gap, [NETWORK, ACTIVITY])

    stated = gap.model_copy(update={"text_spans": ["how much to trust the borrowed mouse prior"]})
    assert not _quotes_the_result(stated, [NETWORK, ACTIVITY])
    assert not _quotes_the_result(gap, [])


# Replayed from recorded gpt-4o-mini case 4 trials (tests/log285_case4_calls.json).
FIXTURE = json.loads((HERE / "log285_case4_calls.json").read_text(encoding="utf-8"))


def _replay(name):
    case = RoutingScenario.model_validate({
        "id": "log285-" + name.replace("_", "-"), "language": "en", "category": "positive", "prompt": FIXTURE["prompt"],
        "expected": {"status": "ambiguous", "actions": []},
    })
    return evaluate([case], provider=RecordedProvider(FIXTURE[name]["calls"]), model_name="recorded")["results"][0]


def test_an_expression_matrix_reading_no_longer_holds_the_one_candidate_open():
    result = _replay("input_only")

    assert result["status"] == "exact" and result["matched_actions"] == ["run_lioness_panda"]
    assert result["action"] == "no_tool" and not result["should_execute"]
    assert "GIRAFFE" in result["answer"] and "activity" in result["answer"]


def test_the_per_patient_wording_no_longer_gets_a_prior_reliability_answer():
    result = _replay("gap_quote")

    assert result["status"] == "ambiguous"
    assert set(result["hypothesis_actions"]) >= {"run_lioness_panda", "run_giraffe"}
    assert "unreliable TF-binding prior" not in result["answer"] and "Bayesian" not in result["answer"]
    assert "No qualified registered workflow" not in result["answer"]


def test_a_folder_recommendation_still_names_the_other_reading():
    result = _replay("inspected")

    assert "validate as a complete input set for **LIONESS-PANDA**" in result["answer"]
    assert "GIRAFFE's TF-by-sample activity matrix is the other reading" in result["answer"]
