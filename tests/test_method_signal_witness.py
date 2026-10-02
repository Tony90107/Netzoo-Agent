"""Log 302 (MS1): a tag breaks a PANDA/OTTER/GIRAFFE tie only when its quote states the method."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import LLMUsage  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    CapabilityMatch,
    OutcomeEvidence,
    OutcomeHypothesis,
    RequestedOutcome,
    SemanticInterpretation,
)
from netzoo_agent_core.graph.discriminator import invoke_semantic_discriminator  # noqa: E402
from netzoo_agent_core.pricing import PriceCatalog  # noqa: E402
from netzoo_agent_core.trace_store import LocalTraceStore  # noqa: E402
from netzoo_agent_core.tracing import TraceRecorder  # noqa: E402
from workflow_registry import OUTPUT_CAPABILITIES, SELECTION_TAG_WITNESSES  # noqa: E402

TRIO = ["run_panda", "run_otter", "run_giraffe"]
# The 2026-10-02 11:19 request (session 60bf4978); the discriminator quoted its
# goal clause for matrix factorization and the card picked GIRAFFE.
LUNG = (
    "We just finished sequencing lung cancer tissue transcriptomes and have standard "
    "transcription factor motif binding sites alongside known protein-protein interaction "
    "maps. We want to estimate genome-wide regulatory strengths, capturing both the "
    "regulatory communication between TFs and target genes as well as cooperative "
    "complexes among TFs. What framework should we use to build this network?"
)
GOAL_QUOTE = (
    "regulatory communication between TFs and target genes as well as cooperative "
    "complexes among TFs"
)
CASE2 = (
    "I need one consensus regulatory network for a tissue. I'd prefer the result to "
    "correspond to a well-defined optimization objective rather than a pile of "
    "iterative update rules."
)


def tf_aggregate() -> OutcomeHypothesis:
    evidence = [
        OutcomeEvidence(dimension=dimension, value=value, source="inferred",
                        rationale=f"Fixture supplies the validated {dimension}.")
        for dimension, value in (
            ("operation", "infer"), ("artifact_type", "regulatory_network"),
            ("input_artifact", "expression_matrix"), ("granularity", "aggregate"),
            ("regulator_type", "tf"), ("target_type", "gene"),
        )
    ]
    return OutcomeHypothesis(
        outcome=RequestedOutcome(
            operation="infer", input_artifacts=["expression_matrix"],
            artifact_type="regulatory_network", entity_types=["tf", "gene"],
            regulator_types=["tf"], target_types=["gene"], granularity="aggregate",
        ),
        confidence=0.95, evidence=evidence,
    )


def discriminate(tmp_path, task, tag, span, *, source="explicit"):
    recorder = TraceRecorder(LocalTraceStore(tmp_path / "traces"))
    run_id = recorder.start_run(session_id="ms1", profile_id="default")
    payload = {"selection_tags": [tag], "evidence": [{
        "dimension": "selection_tag", "value": tag, "source": source,
        "text_span": span, "rationale": "Recorded discriminator answer.",
    }]}
    context = SimpleNamespace(
        semantic_discriminator=SimpleNamespace(invoke=lambda _messages: {"parsed": payload, "raw": object()}),
        semantic_claims=False, semantic_model_name="fixture", router_max_tokens=200,
        task_token_budget=10_000, recorder=recorder, price_catalog=PriceCatalog(),
    )
    interpretation = SemanticInterpretation(
        request_mode="guidance", semantic_goal="Choose a regulatory-network method",
        outcome_hypotheses=[tf_aggregate()],
    )
    _, match, _, _ = invoke_semantic_discriminator(
        context, {"run_id": str(run_id)}, task, interpretation,
        CapabilityMatch(status="ambiguous", hypothesis_actions=list(TRIO)), LLMUsage(), [],
    )
    events = [event for event in recorder.store.read_events(run_id)]
    return match, events


@pytest.mark.parametrize("tag", sorted(SELECTION_TAG_WITNESSES))
def test_the_recorded_goal_quote_states_no_method(tmp_path, tag):
    match, events = discriminate(tmp_path, LUNG, tag, GOAL_QUOTE)

    assert match.status == "ambiguous"
    assert match.hypothesis_actions == TRIO
    unstated = [event for event in events if event.event_type == "routing.semantic_discriminator_unstated_tags"]
    assert unstated and unstated[0].payload["selection_tags"] == [tag]


@pytest.mark.parametrize("task,tag,span,action", [
    (CASE2, "relaxed_graph_matching", "well-defined optimization objective", "run_otter"),
    ("Infer it with OTTER-style relaxed graph matching.", "relaxed_graph_matching",
     "relaxed graph matching", "run_otter"),
    ("我需要明確的最佳化目標，而不是一堆迭代更新規則。", "relaxed_graph_matching",
     "明確的最佳化目標，而不是一堆迭代更新規則", "run_otter"),
    ("Estimate the network by message passing between motif, PPI and co-expression.",
     "message_passing", "message passing between motif, PPI and co-expression", "run_panda"),
    ("Factorize gene expression using the motif and PPI priors.",
     "biologically_informed_matrix_factorization", "Factorize gene expression", "run_giraffe"),
    ("I want which regulators are more active in each sample.", "tfa",
     "which regulators are more active in each sample", "run_giraffe"),
])
def test_a_quote_that_states_the_method_still_breaks_the_tie(tmp_path, task, tag, span, action):
    match, _ = discriminate(tmp_path, task, tag, span)

    assert match.status == "exact"
    assert match.matched_actions == [action]


def test_an_unquoted_inference_cannot_break_the_tie(tmp_path):
    """The one recorded acceptance MS1 changes (Log 230, case 2): source inferred, no quote."""
    match, _ = discriminate(tmp_path, CASE2, "relaxed_graph_matching", None, source="inferred")

    assert match.status == "ambiguous"
    assert match.hypothesis_actions == TRIO


def test_witnesses_cover_only_the_tags_that_separate_the_trio():
    tags = [OUTPUT_CAPABILITIES[action].selection_tags for action in TRIO]
    separating = set().union(*tags) - set.intersection(*map(set, tags))
    assert set(SELECTION_TAG_WITNESSES) == separating
