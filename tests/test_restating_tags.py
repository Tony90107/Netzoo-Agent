"""Log 174: a tag that restates a fixed typed dimension cannot pick a workflow."""

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
from netzoo_agent_core.routing.outcome_matching import restated_tags  # noqa: E402

TASK = "Which workflow gives one cohort-level gene co-expression network from my expression matrix?"


class _Recorder:
    def append(self, *args, **kwargs):
        pass


def _hypothesis(granularity="aggregate") -> OutcomeHypothesis:
    return OutcomeHypothesis(
        outcome=RequestedOutcome(operation="infer", input_artifacts=["expression_matrix"],
                                 artifact_type="coexpression_network", entity_types=["gene"],
                                 granularity=granularity),
        confidence=0.9,
        evidence=[OutcomeEvidence(dimension="artifact_type", value="coexpression_network",
                                  source="explicit", text_span="gene co-expression network",
                                  rationale="t")],
    )


def _discriminate(tags, spans, candidates, hypothesis):
    payload = {"selection_tags": tags, "evidence": [
        {"dimension": "selection_tag", "value": tag, "source": "explicit",
         "text_span": span, "rationale": "t"} for tag, span in zip(tags, spans)
    ]}
    context = SimpleNamespace(
        semantic_discriminator=SimpleNamespace(invoke=lambda _m: {"parsed": payload, "raw": object()}),
        semantic_claims=False, semantic_model_name="fixture", router_max_tokens=200,
        task_token_budget=10_000, recorder=_Recorder(), price_catalog=PriceCatalog(),
    )
    interpretation = SemanticInterpretation(request_mode="guidance", semantic_goal="g",
                                            outcome_hypotheses=[hypothesis])
    match = CapabilityMatch(status="ambiguous", hypothesis_actions=list(candidates))
    return invoke_semantic_discriminator(context, {"run_id": "x"}, TASK, interpretation,
                                         match, LLMUsage(), [])[1]


def test_topic_tag_no_longer_decides_the_cobra_lioness_tie():
    """The recorded Log 172 T2-none shape."""
    match = _discriminate(["coexpression"], ["gene co-expression network"],
                          ["run_lioness_coexpression", "run_cobra"], _hypothesis())

    assert match.status == "ambiguous"
    assert set(match.hypothesis_actions) == {"run_lioness_coexpression", "run_cobra"}


def test_a_method_tag_still_decides():
    match = _discriminate(["bayesian"], ["gene co-expression network"],
                          ["run_lioness_coexpression", "run_bonobo"],
                          _hypothesis(granularity="sample_specific"))

    assert match.status == "exact"
    assert match.matched_actions == ["run_bonobo"]


@pytest.mark.parametrize("field, value, tag", [
    ("artifact_type", "unknown", "coexpression"),
    ("granularity", "unknown", "sample_specific"),
])
def test_a_restating_tag_still_counts_while_its_dimension_is_open(field, value, tag):
    outcome = _hypothesis().outcome.model_copy(update={field: value})

    assert tag not in restated_tags(outcome)
