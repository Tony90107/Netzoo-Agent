"""The semantic pass gets two attempts. A third was tried, measured, reverted.

Log 22 established the mechanism correctly: correcting `artifact_type` from a
network to a cluster assignment makes an inherited `sample_specific` granularity
illegal, and that violation is first reported by the attempt with no successor.
Across 18 live trials it appeared only at the final attempt in 14 of them.

The remedy did not follow. A third, progress-gated attempt fired in 2 of 9 live
trials and made both worse: the extra review dropped the `mutation_matrix` input
it had already recovered and added ungrounded evidence, while the granularity
error survived. Overall passes were unchanged at 4/9, so it bought one more
provider call and nothing else.

These tests hold the bound at two so that a future change to it is deliberate,
and record why more attempts are not the answer to a self-inflicted violation.
"""
from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import IntentDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402
from netzoo_agent_core.graph.router_invocation import MAX_SEMANTIC_ATTEMPTS  # noqa: E402

from evaluate_routing import DEFAULT_SCENARIOS, evaluate, load_scenarios  # noqa: E402
from test_routing_evaluation import hypothesis  # noqa: E402


def q3():
    return next(case for case in load_scenarios(DEFAULT_SCENARIOS) if case.id == "original-q3")


def cluster_item():
    item = hypothesis()
    for evidence in item["evidence"]:
        evidence.update(source="inferred", text_span=None)
    return item


def network_item():
    """The first-pass shape Q3 produces: legal, but the wrong terminal goal."""
    return {
        "outcome": {"operation": "infer", "input_artifacts": [],
                    "artifact_type": "regulatory_network", "entity_types": ["gene"],
                    "regulator_types": ["tf"], "target_types": ["gene"],
                    "granularity": "sample_specific"},
        "confidence": 0.9,
        "evidence": [{"dimension": dimension, "value": value, "source": "inferred",
                      "rationale": "Entailed by the proposed method."}
                     for dimension, value in (
                         ("operation", "infer"), ("artifact_type", "regulatory_network"),
                         ("regulator_type", "tf"), ("target_type", "gene"),
                         ("entity_type", "gene"), ("granularity", "sample_specific"))],
    }


def half_corrected_item():
    """artifact_type is fixed; the inherited granularity is now illegal."""
    item = cluster_item()
    item["outcome"]["granularity"] = "sample_specific"
    for evidence in item["evidence"]:
        if evidence["dimension"] == "granularity":
            evidence["value"] = "sample_specific"
    return item


class SequencedProvider:
    """Return one scripted reply per semantic attempt, then the intent decision."""

    def __init__(self, *semantic_items):
        self.items = list(semantic_items)
        self.calls = []

    def with_structured_output(self, schema, **_kwargs):
        provider = self

        class Adapter:
            def invoke(self, messages):
                provider.calls.append(schema)
                if schema is IntentDecision:
                    return {"mode": "answer", "confidence": 0.95, "reason": "Guidance only."}
                index = min(len(provider.calls) - 1, len(provider.items) - 1)
                item = deepcopy(provider.items[index])
                body = {"request_mode": "guidance", "semantic_goal": "Subtype patients"}
                if schema is SemanticInterpretation:
                    return {**body, "outcome_hypotheses": [item]}
                return {**body, "outcome_hypothesis": item}

        return Adapter()

    @property
    def semantic_calls(self):
        return [item for item in self.calls if item is not IntentDecision]


def run_q3(provider):
    return evaluate([q3()], provider=provider, model_name="fixture")["results"][0]


def test_the_bound_is_two_semantic_attempts():
    assert MAX_SEMANTIC_ATTEMPTS == 2


def test_a_review_that_still_fails_ends_the_run_even_when_it_improved():
    """The measured reason: a further attempt regressed rather than converged."""
    provider = SequencedProvider(network_item(), half_corrected_item(), cluster_item())

    row = run_q3(provider)

    assert len(provider.semantic_calls) == 2
    assert row["status"] == "fallback"
    assert row["outcome"] == {}
    assert row["call_roles"] == ["semantic_interpreter", "semantic_reviewer"]


def test_a_first_pass_that_validates_still_costs_one_review():
    provider = SequencedProvider(cluster_item())

    row = run_q3(provider)

    assert len(provider.semantic_calls) == 2
    assert row["status"] == "exact"


@pytest.mark.parametrize("case_id", ["original-q1", "original-q2", "original-q3"])
def test_the_route_bound_stays_at_three_calls(case_id):
    case = next(item for item in load_scenarios(DEFAULT_SCENARIOS) if item.id == case_id)
    provider = SequencedProvider(network_item(), half_corrected_item(), cluster_item())

    row = evaluate([case], provider=provider, model_name="fixture")["results"][0]

    assert len(row["call_roles"]) <= 3
    assert "call_limit" not in " ".join(row["errors"])


def test_a_failed_run_still_delivers_registry_guidance():
    """Reverting the attempt must not cost the user the recommendation."""
    provider = SequencedProvider(network_item(), half_corrected_item())

    row = run_q3(provider)

    assert row["answer_evaluated"] and row["answer_passed"]
    assert "SAMBAR" in row["answer"]
    assert not row["next_step"]["allow_workflow_continuation"]
