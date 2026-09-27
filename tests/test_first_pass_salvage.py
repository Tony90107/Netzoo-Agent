"""Log 213: a first pass whose only schema faults are evidence entries is kept.

`role-tf-ss-en` (Log 198 round): the first pass read the request correctly --
infer a sample-specific TF-to-gene regulatory network -- but three explicit
evidence entries carried no quote. The whole payload failed the schema, the
second call became a whole review and the trial ended in `semantic_fallback`.
The payload below is that trial's first pass, verbatim.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402
from netzoo_agent_core.contracts import LLMUsage  # noqa: E402
from netzoo_agent_core.graph.first_pass_salvage import validate_first_pass  # noqa: E402
from netzoo_agent_core.graph.router_invocation import _invoke_semantic_interpreter  # noqa: E402
from netzoo_agent_core.llm import build_semantic_interpreter_prompt  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402

TASK = "Which method estimates how transcription factors regulate their target genes separately in each patient? Advice only."
FIRST = {
    "request_mode": "guidance",
    "semantic_goal": "Identify a method for estimating transcription factor regulation of target genes on a per-patient basis.",
    "outcome_hypotheses": [{
        "outcome": {"operation": "infer", "artifact_type": "regulatory_network", "granularity": "sample_specific",
                    "regulator_types": ["tf"], "target_types": ["gene"]},
        "confidence": 0.9,
        "evidence": [
            {"dimension": "operation", "value": "infer", "source": "explicit",
             "rationale": "The user is asking for a method to estimate regulation, which implies a need for inference.",
             "text_span": "Which method estimates how transcription factors regulate their target genes separately in each patient?"},
            {"dimension": "granularity", "value": "sample_specific", "source": "explicit",
             "rationale": "The request specifies regulation separately in each patient, indicating a sample-specific approach."},
            {"dimension": "regulator_type", "value": "tf", "source": "explicit",
             "rationale": "The user specifically mentions transcription factors as the regulators."},
            {"dimension": "target_type", "value": "gene", "source": "explicit",
             "rationale": "The user refers to target genes in the context of regulation."},
        ],
    }],
}


def test_unquoted_explicit_entries_are_dropped_and_the_outcome_kept():
    interpretation, dropped = validate_first_pass(FIRST)
    hypothesis = interpretation.outcome_hypotheses[0]

    assert [(e.dimension, e.value) for e in hypothesis.evidence] == [("operation", "infer")]
    assert hypothesis.outcome.granularity == "sample_specific"
    assert hypothesis.outcome.regulator_types == ["tf"]
    assert [(d["dimension"], d["value"], d["errors"]) for d in dropped] == [
        ("granularity", "sample_specific", ["value_error"]),
        ("regulator_type", "tf", ["value_error"]),
        ("target_type", "gene", ["value_error"]),
    ]


def test_a_valid_first_pass_is_returned_unchanged():
    payload = copy.deepcopy(FIRST)
    for entry, quote in zip(payload["outcome_hypotheses"][0]["evidence"][1:],
                            ("separately in each patient", "transcription factors", "target genes")):
        entry["text_span"] = quote

    interpretation, dropped = validate_first_pass(payload)

    assert dropped == [] and len(interpretation.outcome_hypotheses[0].evidence) == 4


@pytest.mark.parametrize("fault", ["quote_too_long", "quote_empty"])
def test_a_quote_of_the_wrong_length_is_dropped(fault):
    payload = copy.deepcopy(FIRST)
    payload["outcome_hypotheses"][0]["evidence"][1]["text_span"] = "x" * 400 if fault == "quote_too_long" else ""
    del payload["outcome_hypotheses"][0]["evidence"][2:]

    _, dropped = validate_first_pass(payload)

    assert [d["dimension"] for d in dropped] == ["granularity"]


@pytest.mark.parametrize("change", ["dimension_not_a_string", "value_outside_vocabulary", "extra_root_field"])
def test_any_other_fault_keeps_the_schema_failure(change):
    payload = copy.deepcopy(FIRST)
    entry = payload["outcome_hypotheses"][0]["evidence"][0]
    if change == "dimension_not_a_string":
        entry["dimension"] = {"dimension": "operation"}
    elif change == "value_outside_vocabulary":
        entry["dimension"] = "input_artifacts"
    else:
        payload["assumptions"] = []

    with pytest.raises(ValidationError):
        validate_first_pass(payload)


class Adapter:
    def __init__(self, reply):
        self.reply, self.calls = reply, 0

    def invoke(self, _messages):
        self.calls += 1
        return copy.deepcopy(self.reply)


class Supply:
    def __init__(self, reply):
        self.adapter, self.schemas = Adapter(reply), []

    def with_structured_output(self, schema, **options):
        self.schemas.append((sorted(schema.model_fields), options.get("strict")))
        return self.adapter


class Recorder:
    def __init__(self):
        self.events = []

    def append(self, run_id, event, node, data):
        self.events.append((event, data))


def test_the_salvaged_draft_goes_to_the_strict_evidence_supply_and_routes():
    supply = Supply({"evidence_0": {"source": "explicit", "text_span": "how transcription factors regulate their target genes",
                                    "rationale": "Regulation of target genes by TFs is a regulatory network."}})
    reviewer = Adapter({})
    context = SimpleNamespace(
        semantic_claims=False, semantic_interpreter=Adapter(FIRST), semantic_patcher=Adapter({}),
        semantic_reviewer=reviewer, selection_condition_llm=supply, semantic_discriminator=None,
        semantic_prompt=build_semantic_interpreter_prompt(), semantic_model_name="offline",
        router_max_tokens=2000, task_token_budget=100000, price_catalog=None, recorder=Recorder(),
        review_policy="when_needed",
        project_policy=SimpleNamespace(workflows={
            name: SimpleNamespace(output_capability=capability) for name, capability in OUTPUT_CAPABILITIES.items()
        }),
    )

    interpretation, _, _, error, _ = _invoke_semantic_interpreter(context, {}, TASK, LLMUsage(budget_tokens=100000))

    assert error is None and reviewer.calls == 0
    assert supply.schemas == [(["evidence_0"], True)]
    salvaged = [data for event, data in context.recorder.events if event == "routing.semantic_first_pass_salvaged"]
    assert [d["dimension"] for d in salvaged[0]["dropped_evidence"]] == ["granularity", "regulator_type", "target_type"]
    match = match_semantic_request(TASK, interpretation.outcome_hypotheses, request_mode="guidance")
    assert match.matched_actions == ["run_lioness_panda"]
