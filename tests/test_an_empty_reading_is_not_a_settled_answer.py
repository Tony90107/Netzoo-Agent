"""An interpretation that asserts nothing has not settled anything.

Since 2026-09-07 the second semantic call is conditional: a first pass that
matches the registry cleanly is accepted without review. The guard that keeps a
reading with `operation == "unknown"` out of that shortcut was attached only to
the `exact` branch. On the `not_applicable` branch there is no guard at all, so
a reading with every dimension unknown -- the shape that encodes "out of scope"
-- ends routing on the first attempt with no review.

That conflates two different things. "Out of scope" is a finding about the
request; "everything unknown" is a description of the interpreter's output, and
the interpreter produces it whenever the request states something the outcome
vocabulary has no dimension for. The review is the only step that can tell those
apart, and it was exactly the step being skipped (Log 121).

The cost is stated rather than hidden: a genuinely out-of-scope request now
spends one more call before saying so.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402
from netzoo_agent_core.contracts import LLMUsage  # noqa: E402
from netzoo_agent_core.graph.router_invocation import (  # noqa: E402
    _invoke_semantic_interpreter,
)
from netzoo_agent_core.llm import build_semantic_interpreter_prompt  # noqa: E402

# Out of scope, and naming no registered capability, so the named-capability
# lookup cannot be what decides this case.
TASK = "Please book me a table for two at eight tonight."


class Adapter:
    def __init__(self, reply):
        self.reply, self.calls = reply, []

    def invoke(self, messages):
        self.calls.append(messages)
        if isinstance(self.reply, Exception):
            raise self.reply
        return deepcopy(self.reply)


class Recorder:
    def __init__(self):
        self.events = []

    def append(self, run_id, event, node, data):
        self.events.append((event, data))


def context(first, second):
    return SimpleNamespace(
        semantic_claims=False,
        review_policy="when_needed",
        semantic_prompt=build_semantic_interpreter_prompt(),
        semantic_interpreter=Adapter(first),
        semantic_reviewer=Adapter(second),
        semantic_patcher=Adapter(second),
        recorder=Recorder(),
        project_policy=SimpleNamespace(workflows={
            k: SimpleNamespace(output_capability=v)
            for k, v in OUTPUT_CAPABILITIES.items()
        }),
        semantic_model_name="offline",
        task_token_budget=100000,
        router_max_tokens=2000,
        price_catalog=None,
    )


def empty_reading() -> dict:
    return {
        "request_mode": "execute",
        "semantic_goal": "Book a restaurant table.",
        "outcome_hypotheses": [{
            "confidence": 1.0,
            "outcome": {
                "operation": "unknown", "input_artifacts": [],
                "artifact_type": "unknown", "entity_types": [],
                "display_entities": [], "regulator_types": [], "target_types": [],
                "selection_tags": [], "granularity": "not_applicable",
                "unresolved_dimensions": [],
            },
            "evidence": [],
        }],
    }


def settled_reading() -> dict:
    """A first pass that does resolve a capability, which must keep its shortcut."""
    return {
        "request_mode": "execute",
        "semantic_goal": "Infer a per-sample miRNA regulatory network.",
        "outcome_hypotheses": [{
            "confidence": 0.9,
            "outcome": {
                "operation": "infer", "input_artifacts": ["expression_matrix"],
                "artifact_type": "regulatory_network", "entity_types": [],
                "display_entities": [], "regulator_types": ["mirna"],
                "target_types": ["gene"], "selection_tags": [],
                "granularity": "sample_specific", "unresolved_dimensions": [],
            },
            "evidence": [
                {"dimension": "operation", "value": "infer", "source": "inferred",
                 "rationale": "The request asks for a network to be built."},
                {"dimension": "artifact_type", "value": "regulatory_network",
                 "source": "explicit", "text_span": "regulatory network",
                 "rationale": "The request names the artifact."},
                {"dimension": "regulator_type", "value": "mirna", "source": "explicit",
                 "text_span": "miRNA", "rationale": "The request names the regulator."},
                {"dimension": "target_type", "value": "gene", "source": "explicit",
                 "text_span": "gene", "rationale": "The request names the target."},
                {"dimension": "granularity", "value": "sample_specific",
                 "source": "explicit", "text_span": "per-sample",
                 "rationale": "The request names the granularity."},
                {"dimension": "input_artifact", "value": "expression_matrix",
                 "source": "explicit", "text_span": "expression matrix",
                 "rationale": "The request names the input."},
            ],
        }],
    }


def skipped(recorder) -> bool:
    return any(
        data.get("review_skipped") == "validated_complete_match"
        for _, data in recorder.events
    )


def test_a_reading_that_asserts_nothing_does_not_skip_the_review():
    ctx = context(empty_reading(), empty_reading())

    _invoke_semantic_interpreter(ctx, {}, TASK, LLMUsage(budget_tokens=100000))

    assert not skipped(ctx.recorder), (
        "an empty reading ended routing on the first attempt, unreviewed"
    )
    assert ctx.semantic_reviewer.calls or ctx.semantic_patcher.calls, (
        "no second call was made"
    )


def test_a_reading_that_resolves_a_capability_still_skips_it():
    """The scope limit. Without it this would undo the conditional review."""
    task = (
        "Infer a per-sample regulatory network of miRNA regulators on gene targets "
        "from my expression matrix."
    )
    ctx = context(settled_reading(), AssertionError("no review should be needed"))

    result, usage, _, error, _ = _invoke_semantic_interpreter(
        ctx, {}, task, LLMUsage(budget_tokens=100000)
    )

    assert result is not None and error is None
    assert skipped(ctx.recorder)
    assert [call.role for call in usage.calls] == ["semantic_interpreter"]
