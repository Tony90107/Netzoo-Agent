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


# -- Log 332: a sample-clustering reading needs words asking to group something --

TEST4 = json.loads((HERE.parent / "docs" / "research-log" / "test10-2026-10-03" / "out"
                    / "r5-decisions.json").read_text())["test4"]


def _test4_readings():
    return [OutcomeHypothesis.model_validate(item) for item in TEST4["decision"]["outcome_hypotheses"]]


def test_the_recorded_test_4_annotation_read_as_clustering_is_dropped():
    task, readings = TEST4["prompt"], _test4_readings()
    assert [r.outcome.artifact_type for r in readings] == ["regulatory_network", "sample_cluster_assignment"]
    kept, dropped = drop_unwitnessed_readings(task, _interpretation(readings))
    assert dropped == ["sample_cluster_assignment"]
    after = match_semantic_request(task, kept.outcome_hypotheses, request_mode="guidance")
    assert "run_sambar" not in after.hypothesis_actions and "run_panda" in after.hypothesis_actions


def test_a_request_asking_to_cluster_keeps_the_clustering_reading():
    readings = _test4_readings()
    for words in (" We also want to cluster the cells within each state.",
                  " We also want to group the rare-state cells into subgroups."):
        interpretation = _interpretation(readings)
        assert drop_unwitnessed_readings(TEST4["prompt"] + words, interpretation) == (interpretation, [])


def test_an_only_clustering_reading_is_never_dropped():
    only = _interpretation(_test4_readings()[1:])
    assert drop_unwitnessed_readings("I need per-patient gene modules. Which workflow fits?", only) == (only, [])
