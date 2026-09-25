"""Regression coverage for saved Legacy open-granularity traces."""

from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402
from netzoo_agent_core.contracts import LLMUsage  # noqa: E402
from netzoo_agent_core.contracts.decisions import IntentDecision  # noqa: E402
from netzoo_agent_core.graph.router_invocation import (  # noqa: E402
    _invoke_semantic_interpreter,
)
from netzoo_agent_core.interpretation.assembly import (  # noqa: E402
    assemble_task_decision,
)
from netzoo_agent_core.interpretation.outcome_validation import (  # noqa: E402
    validate_outcome_hypotheses,
)
from netzoo_agent_core.llm import build_semantic_interpreter_prompt  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import (  # noqa: E402
    match_semantic_request,
)


TASK = (
    "Which workflow infers a miRNA-to-gene regulatory network? I have not decided "
    "between one cohort network and separate per-patient networks, so please ask me."
)


class Adapter:
    def __init__(self, reply):
        self.reply = reply
        self.calls = 0

    def invoke(self, _messages):
        self.calls += 1
        return self.reply


class Recorder:
    def __init__(self):
        self.events = []

    def append(self, run_id, event, node, data):
        self.events.append((event, data))


def test_legacy_open_granularity_repair_keeps_both_candidates_and_unknown_outcome():
    # Minimal offline replies distilled from the saved Legacy trace. The first
    # pass over-selects aggregate without granularity evidence; the repair
    # correctly returns to unknown but does not itself enumerate alternatives.
    first = {
        "request_mode": "guidance",
        "semantic_goal": "Determine which workflow can infer a miRNA-to-gene regulatory network.",
        "outcome_hypotheses": [{
            "outcome": {
                "operation": "infer",
                "artifact_type": "regulatory_network",
                "regulator_types": ["mirna"],
                "target_types": ["gene"],
                "granularity": "aggregate",
            },
            "confidence": 0.9,
            "evidence": [
                {
                    "dimension": "operation",
                    "value": "infer",
                    "source": "explicit",
                    "text_span": "Which workflow infers a miRNA-to-gene regulatory network?",
                    "rationale": "The user asks for a workflow that infers a regulatory network.",
                },
                {
                    "dimension": "artifact_type",
                    "value": "regulatory_network",
                    "source": "explicit",
                    "text_span": "miRNA-to-gene regulatory network",
                    "rationale": "The user requests a miRNA-to-gene regulatory network.",
                },
                {
                    "dimension": "regulator_type",
                    "value": "mirna",
                    "source": "explicit",
                    "text_span": "miRNA-to-gene regulatory network",
                    "rationale": "The user specifies miRNA regulators.",
                },
                {
                    "dimension": "target_type",
                    "value": "gene",
                    "source": "explicit",
                    "text_span": "miRNA-to-gene regulatory network",
                    "rationale": "The user specifies gene targets.",
                },
            ],
        }],
    }
    patch = {
        "hypothesis_index": 0,
        "outcome": {"granularity": "unknown"},
        "evidence_additions": [{
            "dimension": "granularity",
            "value": "unknown",
            "source": "inferred",
            "rationale": (
                "The user has not decided between one cohort network and "
                "separate per-patient networks."
            ),
        }],
    }
    recorder = Recorder()
    context = SimpleNamespace(
        semantic_claims=False,
        semantic_interpreter=Adapter(first),
        semantic_patcher=Adapter(patch),
        semantic_reviewer=Adapter({}),
        semantic_discriminator=None,
        semantic_prompt=build_semantic_interpreter_prompt(),
        semantic_model_name="offline-trace-replay",
        router_max_tokens=2000,
        task_token_budget=100000,
        price_catalog=None,
        recorder=recorder,
        project_policy=SimpleNamespace(workflows={
            name: SimpleNamespace(output_capability=capability)
            for name, capability in OUTPUT_CAPABILITIES.items()
        }),
    )

    interpretation, _, _, error, _ = _invoke_semantic_interpreter(
        context, {}, TASK, LLMUsage(budget_tokens=100000)
    )

    assert error is None
    assert interpretation is not None
    assert context.semantic_interpreter.calls == 1
    assert context.semantic_patcher.calls == 1
    hypotheses = interpretation.outcome_hypotheses
    assert [item.outcome.granularity for item in hypotheses] == [
        "aggregate",
        "sample_specific",
    ]
    assert validate_outcome_hypotheses(TASK, hypotheses).valid

    match = match_semantic_request(TASK, hypotheses, request_mode="guidance")
    assert match.status == "ambiguous"
    assert match.clarification_question == (
        "Should the result be aggregate or sample-specific?"
    )
    decision = assemble_task_decision(
        interpretation,
        match,
        IntentDecision(mode="answer", confidence=0.9, reason="Guidance only."),
        task=TASK,
    )
    assert decision.requested_outcome is not None
    assert decision.requested_outcome.granularity == "unknown"
    assert any(
        event == "routing.granularity_alternatives_completed"
        for event, _ in recorder.events
    )
