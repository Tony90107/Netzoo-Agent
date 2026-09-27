"""Logs 196/198: a first pass that gave no evidence is asked for exactly that evidence.

Case 7 T2 (Log 183): the first pass named multi_omic_network and aggregate with
no evidence; the patch then added evidence for other fields and never for the
named pairs. The second call is now answered in a strict schema holding one
`Support` per named pair (Log 198; required fields in a non-strict patch schema
were ignored 12 of 12 times, Log 197), and the reply becomes a patch of those
additions. Validation is unchanged, so an ungrounded quote still fails, and a
granularity that contradicts the request's own granularity witness is rejected
however it is justified.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402
from netzoo_agent_core.contracts import LLMUsage  # noqa: E402
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402
from netzoo_agent_core.graph.evidence_supply import supplied_pairs  # noqa: E402
from netzoo_agent_core.graph.router_invocation import _invoke_semantic_interpreter  # noqa: E402
from netzoo_agent_core.interpretation.outcome_validation import validate_outcome_hypotheses  # noqa: E402
from netzoo_agent_core.llm import build_semantic_interpreter_prompt  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402

CASE_7 = (
    "For the same individuals I have gene expression (data/blind-neutral/case-7/layer1.tsv) and "
    "methylation (layer2.tsv). I want to know which methylation sites and genes are directly "
    "associated, not linked indirectly through other variables."
)
FIRST = {
    "request_mode": "guidance",
    "semantic_goal": "Identify direct associations between methylation sites and genes.",
    "outcome_hypotheses": [{
        "outcome": {"operation": "infer", "artifact_type": "multi_omic_network",
                    "target_types": [], "granularity": "aggregate"},
        "confidence": 0.9,
        "evidence": [{
            "dimension": "operation", "value": "infer", "source": "explicit",
            "text_span": "I want to know which methylation sites and genes are directly associated",
            "rationale": "Direct associations are inferred from the data.",
        }],
    }],
}


class Adapter:
    def __init__(self, reply):
        self.reply = reply
        self.calls = 0

    def invoke(self, _messages):
        self.calls += 1
        return self.reply


class Provider:
    """The raw semantic model: records which schema each call was bound to."""

    def __init__(self, reply):
        self.reply = reply
        self.schemas = []
        self.options = []

    def with_structured_output(self, schema, **options):
        self.schemas.append(schema)
        self.options.append(options)
        return Adapter(self.reply)


class Recorder:
    def __init__(self):
        self.events = []

    def append(self, run_id, event, node, data):
        self.events.append((event, data))


def _context(first, supply_reply, patch_reply=None):
    return SimpleNamespace(
        semantic_claims=False,
        semantic_interpreter=Adapter(first),
        semantic_patcher=Adapter(patch_reply or {"hypothesis_index": 0}),
        semantic_reviewer=Adapter({}),
        semantic_discriminator=None,
        selection_condition_llm=Provider(supply_reply),
        semantic_prompt=build_semantic_interpreter_prompt(),
        semantic_model_name="offline",
        router_max_tokens=2000, task_token_budget=100000, price_catalog=None,
        recorder=Recorder(),
        project_policy=SimpleNamespace(workflows={
            name: SimpleNamespace(output_capability=capability)
            for name, capability in OUTPUT_CAPABILITIES.items()
        }),
    )


def _run(context, task=CASE_7):
    interpretation, _, _, error, _ = _invoke_semantic_interpreter(
        context, {}, task, LLMUsage(budget_tokens=100000),
    )
    return interpretation, error


def test_case_7_t2_is_answered_with_the_named_evidence():
    supply = {
        "evidence_0": {"source": "explicit", "text_span": "gene expression", "rationale": "Two omics layers."},
        "evidence_1": {"source": "inferred", "rationale": "One set of associations for the whole cohort."},
    }
    context = _context(FIRST, supply)

    interpretation, error = _run(context)

    assert error is None and interpretation is not None
    assert context.semantic_patcher.calls == 0
    (schema,) = context.selection_condition_llm.schemas
    assert context.selection_condition_llm.options[0]["strict"] is True
    required = {name for name, field in schema.model_fields.items() if field.is_required()}
    assert required == set(schema.model_fields) == {"evidence_0", "evidence_1"}
    assert validate_outcome_hypotheses(CASE_7, interpretation.outcome_hypotheses, "guidance").valid
    match = match_semantic_request(CASE_7, interpretation.outcome_hypotheses, request_mode="guidance")
    assert (match.status, match.matched_actions) == ("exact", ["run_dragon"])
    assert ("routing.semantic_evidence_supplied", {
        "attempt": 2,
        "requested": ["hypothesis[0].artifact_type=multi_omic_network", "hypothesis[0].granularity=aggregate"],
        "sources": ["explicit", "inferred"],
    }) in context.recorder.events


def test_a_supplied_quote_the_request_does_not_contain_still_fails():
    supply = {
        "evidence_0": {"source": "explicit", "text_span": "a multi-omic network", "rationale": "r"},
        "evidence_1": {"source": "inferred", "rationale": "r"},
    }

    interpretation, _ = _run(_context(FIRST, supply))

    assert interpretation is None or not validate_outcome_hypotheses(
        CASE_7, interpretation.outcome_hypotheses, "guidance",
    ).valid


def test_other_issues_keep_the_patch_path():
    first = SemanticInterpretation.model_validate(FIRST)

    assert supplied_pairs(("hypothesis[0].missing_evidence:granularity=aggregate",), first) == [
        (0, "granularity", "aggregate"),
    ]
    assert supplied_pairs((
        "hypothesis[0].missing_evidence:granularity=aggregate",
        "hypothesis[0].ungrounded_evidence:operation=infer",
    ), first) is None
    # A pair the proposal did not write is not asked for.
    assert supplied_pairs(("hypothesis[0].missing_evidence:granularity=sample_specific",), first) is None


PER_PATIENT = "I want per-patient networks that capture both TF and miRNA regulation of genes. Which workflow? Advice only."


@pytest.mark.parametrize("span", [None, "per-patient networks"])
def test_a_granularity_against_the_requests_own_witness_is_rejected(span):
    """role-both-ss-en: an aggregate reading passed as exact PUMA once any evidence was added."""
    first = SemanticInterpretation.model_validate({
        "request_mode": "guidance", "semantic_goal": "g",
        "outcome_hypotheses": [{
            "outcome": {"operation": "infer", "artifact_type": "regulatory_network",
                        "regulator_types": ["tf", "mirna"], "target_types": ["gene"],
                        "granularity": "aggregate"},
            "confidence": 0.9,
            "evidence": [
                {"dimension": "artifact_type", "value": "regulatory_network", "source": "explicit",
                 "text_span": "networks that capture both TF and miRNA regulation of genes", "rationale": "r"},
                {"dimension": "regulator_type", "value": "tf", "source": "explicit",
                 "text_span": "TF and miRNA regulation", "rationale": "r"},
                {"dimension": "regulator_type", "value": "mirna", "source": "explicit",
                 "text_span": "TF and miRNA regulation", "rationale": "r"},
                {"dimension": "target_type", "value": "gene", "source": "explicit",
                 "text_span": "regulation of genes", "rationale": "r"},
                {"dimension": "granularity", "value": "aggregate",
                 "source": "explicit" if span else "inferred", "text_span": span, "rationale": "r"},
            ],
        }],
    })

    validation = validate_outcome_hypotheses(PER_PATIENT, first.outcome_hypotheses, "guidance")

    assert not validation.valid
    assert "hypothesis[0].granularity_contradicts_request:aggregate" in validation.issues
