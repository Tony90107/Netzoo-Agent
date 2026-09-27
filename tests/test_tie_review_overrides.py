"""Log 210: a tie review may not overturn a validated scalar without quoting the request.

Case 6 (Log 204): the first pass read aggregate co-expression and validated;
the only issue was a tie {COBRA, LIONESS-COEXPRESSION}. The review changed
aggregate to sample_specific on an inferred rationale, which swapped COBRA --
the right answer -- for BONOBO. The payloads below are that trial's, verbatim.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402
from netzoo_agent_core.contracts import LLMUsage  # noqa: E402
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation, SemanticPatch  # noqa: E402
from netzoo_agent_core.contracts.repair_scope import permitted_fields  # noqa: E402
from netzoo_agent_core.graph.router_invocation import _invoke_semantic_interpreter  # noqa: E402
from netzoo_agent_core.interpretation.semantic_patch import apply_semantic_patch  # noqa: E402
from netzoo_agent_core.llm import build_semantic_interpreter_prompt  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402

TASK = (
    "These samples were sequenced in two runs, recorded in data/blind-neutral/case-6/design.tsv; "
    "expression is in expression.tsv. I want to know which parts of the co-expression structure "
    "are driven by the batch and which are not."
)
FIRST = {
    "request_mode": "guidance",
    "semantic_goal": "Identify batch-driven and non-batch-driven components of the co-expression structure.",
    "outcome_hypotheses": [{
        "outcome": {"operation": "analyze", "input_artifacts": [], "artifact_type": "coexpression_network",
                    "entity_types": ["gene", "sample"], "display_entities": [], "regulator_types": [],
                    "target_types": [], "selection_tags": [], "granularity": "aggregate",
                    "unresolved_dimensions": []},
        "confidence": 0.9,
        "evidence": [
            {"dimension": "artifact_type", "value": "coexpression_network", "source": "explicit",
             "text_span": "I want to know which parts of the co-expression structure are driven by the batch and which are not.",
             "rationale": "The user is interested in the co-expression structure."},
            {"dimension": "granularity", "value": "aggregate", "source": "inferred", "text_span": None,
             "rationale": "The request implies a general analysis across all samples rather than per sample."},
        ],
        "assumptions": [],
    }],
}
PATCH = {
    "hypothesis_index": 0, "request_mode": "guidance",
    "outcome": {"operation": "analyze", "input_artifacts": ["expression_matrix"],
                "artifact_type": "coexpression_network", "entity_types": ["gene"], "regulator_types": [],
                "target_types": [], "selection_tags": [], "granularity": "sample_specific",
                "unresolved_dimensions": []},
    "evidence_removals": [{"dimension": "granularity", "value": "aggregate"}],
    "evidence_additions": [
        {"dimension": "input_artifact", "value": "expression_matrix", "source": "explicit",
         "rationale": "The user provided expression data in expression.tsv for the analysis.",
         "text_span": "expression is in expression.tsv."},
        {"dimension": "granularity", "value": "sample_specific", "source": "inferred",
         "rationale": "The request implies analysing co-expression separately for each sample.", "text_span": ""},
    ],
}
TIE = ("registry_ambiguity:the structured outcome does not uniquely identify a capability",)


def _merge(patch=PATCH, task=TASK, hold=True):
    return apply_semantic_patch(
        SemanticInterpretation.model_validate(FIRST), SemanticPatch.model_validate(patch),
        permitted_fields=permitted_fields(TIE), user_task=task, hold_validated=hold,
    )


def test_an_unquoted_change_of_a_validated_granularity_is_held():
    merged, retired = _merge()
    hypothesis = merged.outcome_hypotheses[0]

    assert hypothesis.outcome.granularity == "aggregate"
    assert ("granularity", "aggregate") in {(e.dimension, e.value) for e in hypothesis.evidence}
    assert ("granularity", "sample_specific") not in {(e.dimension, e.value) for e in hypothesis.evidence}
    assert {"dimension": "granularity", "value": "sample_specific", "field": "granularity", "kept": "aggregate",
            "reason": "override_of_validated_value_without_quote"} in retired
    # The rest of the review is applied as before.
    assert hypothesis.outcome.input_artifacts == ["expression_matrix"]


def test_a_quoted_change_is_applied():
    patch = copy.deepcopy(PATCH)
    patch["evidence_additions"][1] = {"dimension": "granularity", "value": "sample_specific", "source": "explicit",
                                      "text_span": "for each sample", "rationale": "Stated."}
    merged, _ = _merge(patch, task=TASK + " I need the result for each sample.")

    assert merged.outcome_hypotheses[0].outcome.granularity == "sample_specific"


def test_retreating_to_unknown_is_not_overturning():
    patch = copy.deepcopy(PATCH)
    patch["outcome"]["granularity"] = "unknown"
    patch["evidence_additions"] = patch["evidence_additions"][:1]

    assert _merge(patch)[0].outcome_hypotheses[0].outcome.granularity == "unknown"


def test_without_a_validated_first_pass_the_review_may_change_it():
    assert _merge(hold=False)[0].outcome_hypotheses[0].outcome.granularity == "sample_specific"


class Adapter:
    def __init__(self, reply):
        self.reply, self.calls = reply, 0

    def invoke(self, _messages):
        self.calls += 1
        return copy.deepcopy(self.reply)


class Recorder:
    def __init__(self):
        self.events = []

    def append(self, run_id, event, node, data):
        self.events.append((event, data))


def test_case_6_keeps_cobra_among_the_candidates():
    context = SimpleNamespace(
        semantic_claims=False, semantic_interpreter=Adapter(FIRST), semantic_patcher=Adapter(PATCH),
        semantic_reviewer=Adapter({}), semantic_discriminator=None,
        semantic_prompt=build_semantic_interpreter_prompt(), semantic_model_name="offline",
        router_max_tokens=2000, task_token_budget=100000, price_catalog=None, recorder=Recorder(),
        review_policy="when_needed",
        project_policy=SimpleNamespace(workflows={
            name: SimpleNamespace(output_capability=capability) for name, capability in OUTPUT_CAPABILITIES.items()
        }),
    )

    interpretation, _, _, error, _ = _invoke_semantic_interpreter(context, {}, TASK, LLMUsage(budget_tokens=100000))

    assert error is None and context.semantic_patcher.calls == 1
    assert interpretation.outcome_hypotheses[0].outcome.granularity == "aggregate"
    match = match_semantic_request(TASK, interpretation.outcome_hypotheses, request_mode="guidance")
    assert "run_cobra" in (match.matched_actions or match.hypothesis_actions)
    applied = [data for event, data in context.recorder.events if event == "routing.semantic_patch_applied"]
    assert applied[0]["overrides_held"][0]["kept"] == "aggregate"
