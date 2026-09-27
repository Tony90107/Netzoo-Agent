"""Log 215: root-level assumptions of a one-hypothesis first pass are nested into it.

`gran-mirna-unstated-control` (Log 208 strict round): the first pass wrote its
one assumption beside `outcome_hypotheses` instead of inside the hypothesis.
The draft failed the schema and went to a whole review. The payload below is
that trial's first pass, verbatim. The rule is `SemanticReview`'s: accept only
an equivalent nesting, never conflicts.
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
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402
from netzoo_agent_core.graph.first_pass_salvage import validate_first_pass  # noqa: E402
from netzoo_agent_core.graph.router_invocation import _invoke_semantic_interpreter  # noqa: E402
from netzoo_agent_core.llm import build_semantic_interpreter_prompt  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402

TASK = (
    "Which workflow infers a miRNA-to-gene regulatory network? I have not decided between one cohort "
    "network and separate per-patient networks, so please ask me."
)
ASSUMPTION = "The user is considering both cohort-wide and patient-specific networks for the analysis."
FIRST = {
    "request_mode": "guidance",
    "semantic_goal": "Determine which workflow can infer a miRNA-to-gene regulatory network.",
    "outcome_hypotheses": [{
        "outcome": {"operation": "infer", "artifact_type": "regulatory_network", "granularity": "aggregate",
                    "regulator_types": ["mirna"], "target_types": ["gene"]},
        "confidence": 0.9,
        "evidence": [
            {"dimension": "operation", "value": "infer", "source": "explicit",
             "rationale": "The user is asking for a workflow that infers a regulatory network.",
             "text_span": "Which workflow infers a miRNA-to-gene regulatory network?"},
            {"dimension": "artifact_type", "value": "regulatory_network", "source": "explicit",
             "rationale": "The user specifically requests a miRNA-to-gene regulatory network.",
             "text_span": "miRNA-to-gene regulatory network"},
            {"dimension": "regulator_type", "value": "mirna", "source": "explicit",
             "rationale": "The user specifies that the regulatory network should involve miRNAs.",
             "text_span": "miRNA-to-gene regulatory network"},
            {"dimension": "target_type", "value": "gene", "source": "explicit",
             "rationale": "The user specifies that the targets of the regulatory network should be genes.",
             "text_span": "miRNA-to-gene regulatory network"},
        ],
    }],
    "assumptions": [ASSUMPTION],
}


def test_the_contract_itself_still_rejects_the_nesting():
    with pytest.raises(ValidationError):
        SemanticInterpretation.model_validate(FIRST)


def test_root_assumptions_move_into_the_only_hypothesis():
    interpretation, salvage = validate_first_pass(FIRST)

    assert salvage == {"nested": ["assumptions"]}
    assert interpretation.outcome_hypotheses[0].assumptions == [ASSUMPTION]
    assert interpretation.outcome_hypotheses[0].outcome.granularity == "aggregate"


def test_the_same_assumptions_on_both_levels_are_accepted():
    payload = copy.deepcopy(FIRST)
    payload["outcome_hypotheses"][0]["assumptions"] = [ASSUMPTION]

    assert validate_first_pass(payload)[1] == {"nested": ["assumptions"]}


@pytest.mark.parametrize("shape", ["conflicting_nested_assumptions", "two_hypotheses"])
def test_an_ambiguous_nesting_keeps_the_schema_failure(shape):
    payload = copy.deepcopy(FIRST)
    if shape == "conflicting_nested_assumptions":
        payload["outcome_hypotheses"][0]["assumptions"] = ["Something else."]
    else:
        payload["outcome_hypotheses"].append(copy.deepcopy(payload["outcome_hypotheses"][0]))

    with pytest.raises(ValidationError):
        validate_first_pass(payload)


def test_nesting_and_evidence_repairs_combine():
    payload = copy.deepcopy(FIRST)
    del payload["outcome_hypotheses"][0]["evidence"][3]["text_span"]

    interpretation, salvage = validate_first_pass(payload)

    assert salvage["nested"] == ["assumptions"]
    assert [d["dimension"] for d in salvage["dropped_evidence"]] == ["target_type"]
    assert interpretation.outcome_hypotheses[0].assumptions == [ASSUMPTION]


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


def test_the_nested_draft_asks_which_granularity_without_a_whole_review():
    reviewer, patcher = Adapter({}), Adapter({})
    context = SimpleNamespace(
        semantic_claims=False, semantic_interpreter=Adapter(FIRST), semantic_patcher=patcher,
        semantic_reviewer=reviewer, selection_condition_llm=None, semantic_discriminator=None,
        semantic_prompt=build_semantic_interpreter_prompt(), semantic_model_name="offline",
        router_max_tokens=2000, task_token_budget=100000, price_catalog=None, recorder=Recorder(),
        review_policy="when_needed",
        project_policy=SimpleNamespace(workflows={
            name: SimpleNamespace(output_capability=capability) for name, capability in OUTPUT_CAPABILITIES.items()
        }),
    )

    interpretation, _, _, error, _ = _invoke_semantic_interpreter(context, {}, TASK, LLMUsage(budget_tokens=100000))

    # The undecided-granularity witnesses split the draft; an empty tie review
    # is discarded and the validated draft kept.
    assert error is None and reviewer.calls == 0
    assert {h.outcome.granularity for h in interpretation.outcome_hypotheses} == {"aggregate", "sample_specific"}
    match = match_semantic_request(TASK, interpretation.outcome_hypotheses, request_mode="guidance")
    assert match.status == "ambiguous"
    assert set(match.hypothesis_actions) == {"run_puma", "run_lioness_puma"}
