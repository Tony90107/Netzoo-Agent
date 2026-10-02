"""Log 313: a multi-omic reading needs a second omics layer named in the request.

Test 2 ("microarray expression profiles ... a separate regulatory network for
each patient") was read twice: the quoted regulatory network and, with no
quote, a multi-omic network that brought LIONESS-DRAGON into the tie.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "scripts"))

from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis, RequestedOutcome, SemanticInterpretation  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402
from netzoo_agent_core.routing.reading_selection import drop_unwitnessed_readings  # noqa: E402

FIXTURE = json.loads((HERE / "log313_t2_readings.json").read_text(encoding="utf-8"))


def _interpretation(readings):
    return SemanticInterpretation.model_construct(request_mode="guidance", semantic_goal="", outcome_hypotheses=readings)


def _recorded():
    return [OutcomeHypothesis.model_validate(item) for item in FIXTURE["readings"]]


def test_the_recorded_test_2_multi_omic_reading_is_dropped_and_lioness_dragon_leaves_the_tie():
    task, readings = FIXTURE["prompt"], _recorded()
    assert [r.outcome.artifact_type for r in readings] == ["regulatory_network", "multi_omic_network"]
    before = match_semantic_request(task, readings, request_mode="guidance")
    assert "run_lioness_dragon" in before.hypothesis_actions
    kept, dropped = drop_unwitnessed_readings(task, _interpretation(readings))
    assert dropped == ["multi_omic_network"]
    after = match_semantic_request(task, kept.outcome_hypotheses, request_mode="guidance")
    assert set(after.hypothesis_actions) == {"run_lioness_panda", "run_lioness_puma"}


def test_a_request_naming_a_second_layer_keeps_the_reading():
    readings = _recorded()
    task = FIXTURE["prompt"] + " We also measured DNA methylation on the same biopsies."
    interpretation = _interpretation(readings)
    assert drop_unwitnessed_readings(task, interpretation) == (interpretation, [])


def test_an_only_reading_is_never_dropped():
    only = _interpretation(_recorded()[1:])
    assert drop_unwitnessed_readings(FIXTURE["prompt"], only) == (only, [])


def test_a_protein_interaction_prior_is_not_a_second_layer():
    readings = _recorded()
    task = FIXTURE["prompt"] + " We also have a protein interaction map."
    assert drop_unwitnessed_readings(task, _interpretation(readings))[1] == ["multi_omic_network"]


def test_the_rest_must_still_validate_on_its_own():
    # Rule B's guard: an unquoted, unsupported remaining reading keeps the pair.
    bare = OutcomeHypothesis(outcome=RequestedOutcome(operation="infer", artifact_type="regulatory_network",
                                                      granularity="sample_specific"), confidence=0.5)
    interpretation = _interpretation([bare, _recorded()[1]])
    assert drop_unwitnessed_readings(FIXTURE["prompt"], interpretation) == (interpretation, [])
