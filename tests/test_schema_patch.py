"""Log 325: a first pass that failed the schema on confidence or artifact_type is patched.

The two faults that still sent a first pass to a whole review become
placeholders in a draft that only a patch can complete. A confidence nobody
wrote is never kept: a hypothesis still waiting after the last attempt is
dropped, and with none written the pass fails as the schema error did.
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
sys.path.insert(0, str(Path(__file__).parent))

from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402
from netzoo_agent_core.contracts import LLMUsage  # noqa: E402
from netzoo_agent_core.graph.first_pass_salvage import validate_first_pass  # noqa: E402
from netzoo_agent_core.graph.router_invocation import _invoke_semantic_interpreter  # noqa: E402
from netzoo_agent_core.graph.schema_placeholders import PLACEHOLDER_CONFIDENCE, SchemaPlaceholders  # noqa: E402
from netzoo_agent_core.llm import build_semantic_interpreter_prompt  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402
from test_first_pass_salvage import FIRST, TASK, Adapter, Recorder  # noqa: E402

QUOTES = ("separately in each patient", "transcription factors", "target genes")


def _valid_first():
    payload = copy.deepcopy(FIRST)
    for entry, quote in zip(payload["outcome_hypotheses"][0]["evidence"][1:], QUOTES):
        entry["text_span"] = quote
    payload["outcome_hypotheses"][0]["evidence"].append({
        "dimension": "artifact_type", "value": "regulatory_network", "source": "explicit",
        "text_span": "how transcription factors regulate their target genes",
        "rationale": "TF regulation of target genes is a regulatory network."})
    return payload


def _without_confidence():
    payload = _valid_first()
    del payload["outcome_hypotheses"][0]["confidence"]
    return payload


class Patcher(Adapter):
    def __init__(self, reply):
        super().__init__(reply)
        self.messages = []

    def invoke(self, messages):
        self.messages.append(messages)
        return super().invoke(messages)


def _context(first, patch, sibling=None):
    patcher, reviewer = Patcher(patch), Adapter({})
    sibling_llm = SimpleNamespace(with_structured_output=lambda schema, **_: Patcher(sibling or {}))
    context = SimpleNamespace(
        semantic_claims=False, semantic_interpreter=Adapter(first), semantic_patcher=patcher,
        semantic_reviewer=reviewer, selection_condition_llm=sibling_llm, semantic_discriminator=None,
        semantic_prompt=build_semantic_interpreter_prompt(), semantic_model_name="offline",
        router_max_tokens=2000, task_token_budget=100000, price_catalog=None, recorder=Recorder(),
        review_policy="when_needed",
        project_policy=SimpleNamespace(workflows={
            name: SimpleNamespace(output_capability=capability) for name, capability in OUTPUT_CAPABILITIES.items()
        }),
    )
    return context, patcher, reviewer


def _events(context, name):
    return [data for event, data in context.recorder.events if event == name]


def test_a_missing_confidence_becomes_a_placeholder_and_other_faults_still_fail():
    interpretation, salvage = validate_first_pass(_without_confidence())
    assert salvage["placeholders"] == {"confidence": [0], "artifact_type": {}}
    assert interpretation.outcome_hypotheses[0].confidence == PLACEHOLDER_CONFIDENCE
    malformed = _without_confidence()
    malformed["outcome_hypotheses"][0]["outcome"]["operation"] = "estimate"  # not a placeholder fault
    with pytest.raises(ValidationError):
        validate_first_pass(malformed)


def test_an_out_of_vocabulary_artifact_becomes_unknown_with_its_value_kept_for_the_patch():
    payload = _valid_first()
    payload["outcome_hypotheses"][0]["outcome"]["artifact_type"] = "sample_specific"
    interpretation, salvage = validate_first_pass(payload)
    assert salvage["placeholders"] == {"confidence": [], "artifact_type": {"0": "sample_specific"}}
    assert interpretation.outcome_hypotheses[0].outcome.artifact_type == "unknown"
    issues = SchemaPlaceholders.from_record(salvage["placeholders"]).issues()
    assert issues == ("hypothesis[0].schema_invalid_value:artifact_type=sample_specific",)
    assert issues[0].fields == frozenset({"artifact_type"})


def test_the_patch_is_asked_instead_of_a_whole_review_and_its_confidence_is_kept():
    context, patcher, reviewer = _context(_without_confidence(), {"hypothesis_index": 0, "confidence": 0.8})
    interpretation, _, _, error, _ = _invoke_semantic_interpreter(context, {}, TASK, LLMUsage(budget_tokens=100000))
    assert error is None and reviewer.calls == 0 and patcher.calls == 1
    assert interpretation.outcome_hypotheses[0].confidence == 0.8
    shown = str(patcher.messages[0][-1].content)
    assert "schema_missing:confidence" in shown and '"confidence": null' in shown
    assert match_semantic_request(TASK, interpretation.outcome_hypotheses,
                                  request_mode="guidance").matched_actions == ["run_lioness_panda"]


def test_a_confidence_no_model_wrote_is_never_kept():
    context, patcher, _ = _context(_without_confidence(), {"hypothesis_index": 0})
    interpretation, _, _, error, _ = _invoke_semantic_interpreter(context, {}, TASK, LLMUsage(budget_tokens=100000))
    assert interpretation is None and error is not None and patcher.calls == 1
    assert _events(context, "routing.schema_placeholders_unwritten")[0]["remaining"]["confidence"] == [0]


def test_the_patch_replaces_an_invalid_artifact():
    payload = _valid_first()
    payload["outcome_hypotheses"][0]["outcome"]["artifact_type"] = "sample_specific"
    patch = {"hypothesis_index": 0, "outcome": {"artifact_type": "regulatory_network"},
             "evidence_additions": [{"dimension": "artifact_type", "value": "regulatory_network", "source": "explicit",
                                     "text_span": "how transcription factors regulate their target genes",
                                     "rationale": "TF regulation of target genes is a regulatory network."}]}
    context, patcher, reviewer = _context(payload, patch)
    interpretation, _, _, error, _ = _invoke_semantic_interpreter(context, {}, TASK, LLMUsage(budget_tokens=100000))
    assert error is None and reviewer.calls == 0
    assert "schema_invalid_value:artifact_type=sample_specific" in str(patcher.messages[0][-1].content)
    assert interpretation.outcome_hypotheses[0].outcome.artifact_type == "regulatory_network"


def _two_without_confidence():
    payload = _without_confidence()
    second = copy.deepcopy(payload["outcome_hypotheses"][0])
    payload["outcome_hypotheses"].append(second)
    return payload


def test_a_sibling_gets_its_own_patch_for_its_confidence():
    context, _, _ = _context(_two_without_confidence(), {"hypothesis_index": 0, "confidence": 0.8},
                             sibling={"hypothesis_index": 1, "confidence": 0.4})
    interpretation, _, _, error, _ = _invoke_semantic_interpreter(context, {}, TASK, LLMUsage(budget_tokens=100000))
    assert error is None
    assert [h.confidence for h in interpretation.outcome_hypotheses] == [0.8, 0.4]


def test_a_sibling_whose_confidence_nobody_wrote_is_dropped():
    context, _, _ = _context(_two_without_confidence(), {"hypothesis_index": 0, "confidence": 0.8},
                             sibling={"hypothesis_index": 1})
    interpretation, _, _, error, _ = _invoke_semantic_interpreter(context, {}, TASK, LLMUsage(budget_tokens=100000))
    assert error is None and [h.confidence for h in interpretation.outcome_hypotheses] == [0.8]
    assert _events(context, "routing.schema_placeholders_unwritten")[0]["dropped"] == [1]
