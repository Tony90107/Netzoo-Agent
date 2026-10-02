"""Log 306: first-pass method tags need a quote stating them (WT1); a miRNA preference needs miRNA words (WT2)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    MethodPreference, OutcomeEvidence, OutcomeHypothesis, RequestedOutcome,
)
from netzoo_agent_core.graph.condition_recommender import _candidate_facts, _recommend_from_preference  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402

TRIO = {"run_panda", "run_otter", "run_giraffe"}
T1 = ("I need one cohort-wide TF-to-gene regulatory network from my expression matrix, TF motif prior "
      "and PPI data (data/blind-neutral/case-2/). ")
T1_OTTER = T1 + "The real network will be very large, so memory and runtime are a concern."


def reading(task, tag, span):
    """The final reading recorded for t1-otter (Log 305, candidate s1): the review patch added the tag."""
    goal = task.split(". ")[0] + "."
    return OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="infer", input_artifacts=["expression_matrix"], artifact_type="regulatory_network",
            entity_types=["tf", "gene"], regulator_types=["tf"], target_types=["gene"], granularity="aggregate",
            selection_tags=["tf_gene_regulation", "aggregate_network", tag],
        ),
        confidence=0.9,
        evidence=[
            OutcomeEvidence(dimension="operation", value="infer", source="explicit", text_span=goal,
                            rationale="recorded"),
            OutcomeEvidence(dimension="artifact_type", value="regulatory_network", source="explicit",
                            text_span="one cohort-wide TF-to-gene regulatory network", rationale="recorded"),
            OutcomeEvidence(dimension="regulator_type", value="tf", source="explicit", text_span="TF-to-gene",
                            rationale="recorded"),
            OutcomeEvidence(dimension="target_type", value="gene", source="explicit", text_span="TF-to-gene",
                            rationale="recorded"),
            OutcomeEvidence(dimension="selection_tag", value=tag, source="explicit", text_span=span,
                            rationale="recorded"),
        ],
    )


def test_the_recorded_t1_otter_reading_no_longer_picks_panda():
    match = match_semantic_request(
        T1_OTTER,
        [reading(T1_OTTER, "lioness_base_compatibility",
                 "The real network will be very large, so memory and runtime are a concern.")],
        request_mode="guidance",
    )

    assert match.status == "ambiguous"
    assert set(match.hypothesis_actions) == TRIO


@pytest.mark.parametrize("sentence,tag,span,action", [
    ("Later I will run LIONESS on this base network.", "lioness_base_compatibility",
     "Later I will run LIONESS on this base network.", "run_panda"),
    ("It should be solved as a relaxed graph matching problem.", "relaxed_graph_matching",
     "solved as a relaxed graph matching problem", "run_otter"),
    ("Estimate it by message passing between the networks.", "message_passing",
     "by message passing between the networks", "run_panda"),
])
def test_a_quote_that_states_the_method_still_decides(sentence, tag, span, action):
    task = T1 + sentence
    match = match_semantic_request(task, [reading(task, tag, span)], request_mode="guidance")

    assert match.status == "exact"
    assert match.matched_actions == [action]


POLICY = ProjectPolicyLoader(Path(__file__).parents[1]).load()
CONTEXT = SimpleNamespace(project_policy=POLICY)
COMMUNICATION = ("Our tumor RNA-seq comes with TF motif priors and a protein interaction map. We want to capture "
                 "how TFs communicate with their target genes and how TFs cooperate in complexes. Which framework "
                 "builds this network? Advice only.")
SMALL_RNAS = ("My prior regulatory table contains not only transcription factors but also predicted targets of some "
              "small RNAs; those small RNAs are listed in mirna.txt. I want one overall regulatory network.")
DEGRADATION = ("Instead, another type of 'short non-coding molecule' directly degraded the products "
               "post-transcription. Do you have a tool specifically for this class of molecules?")


def prefer(task, action, tags, span, candidates):
    preference = MethodPreference(action=action, selection_tags=tags, text_spans=[span],
                                  rationale="Recorded model preference.")
    return _recommend_from_preference(task, preference, _candidate_facts(candidates, CONTEXT))


def test_the_recorded_puma_preference_for_a_tf_only_request_is_dropped():
    """ms-generic-communication, Log 305 candidate s1: PUMA for a request that names no miRNA."""
    quote = "We want to capture how TFs communicate with their target genes and how TFs cooperate in complexes."
    recommendation = prefer(COMMUNICATION, "run_puma", ["aggregate_network", "message_passing", "mirna_regulation"],
                            quote, ["run_panda", "run_puma", "run_otter", "run_giraffe"])
    assert recommendation is None


@pytest.mark.parametrize("task,action,span", [
    (SMALL_RNAS, "run_puma", "I want one overall regulatory network."),
    (DEGRADATION, "run_puma", "Do you have a tool specifically for this class of molecules?"),
])
def test_a_request_describing_mirnas_keeps_a_mirna_preference(task, action, span):
    recommendation = prefer(task, action, ["aggregate_network", "message_passing", "mirna_regulation"], span,
                            ["run_panda", "run_puma"])
    assert recommendation is not None and recommendation.action == action


def test_a_tf_preference_is_unaffected():
    span = "We want to capture how TFs communicate with their target genes and how TFs cooperate in complexes."
    recommendation = prefer(COMMUNICATION, "run_panda", ["aggregate_network", "message_passing"], span,
                            ["run_panda", "run_otter", "run_giraffe"])
    assert recommendation is not None and recommendation.action == "run_panda"
