"""Log 283: role paths, folded alternatives, stated-only downstream notes, compact card."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.outcomes import (  # noqa: E402
    AdvisoryCondition, AdvisoryRecommendation, OutcomeHypothesis, RequestedOutcome,
)
from netzoo_agent_core.graph.response_context import validated_workflow_context  # noqa: E402
from netzoo_agent_core.interpretation.concept_answers import render_outcome_clarification  # noqa: E402
from netzoo_agent_core.interpretation.input_bindings import request_input_bindings  # noqa: E402
from netzoo_agent_core.interpretation.verified_guidance import render_verified_guidance  # noqa: E402
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()
BLIND = {c["id"]: c["prompt"] for c in json.loads((ROOT / "docs/research-log/blind/blind_en.json").read_text())}


def test_a_role_name_inside_a_file_name_is_not_a_role_keyword():
    case7 = dict(request_input_bindings(BLIND["case7-en"]).values)
    assert case7 == {"expression_file": "data/blind-neutral/case-7/layer1.tsv"}
    assert dict(request_input_bindings(BLIND["case9-en"]).values) == {
        "network_file": "data/blind-neutral/case-9/bipartite.tsv"}
    assert dict(request_input_bindings("omics layers: layer2 = data/x/meth.tsv").values)["omics_layer_2"] == "data/x/meth.tsv"


def _puma_recommendation():
    outcome = RequestedOutcome(operation="explain", artifact_type="regulatory_network", granularity="unknown")
    return TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question", confidence=0.9,
        reason="tie", capability_match_status="ambiguous", requested_outcome=outcome,
        outcome_hypotheses=[OutcomeHypothesis(outcome=outcome, confidence=0.9)],
        hypothesis_actions=["run_panda", "run_puma", "run_lioness_panda", "run_lioness_puma", "run_otter", "run_giraffe"],
        advisory_recommendation=AdvisoryRecommendation(action="run_puma", conditions=[
            AdvisoryCondition(axis="regulator_class", value="mirna", text_span="short non-coding molecule")]),
        clarification_question="Should I use PUMA, or does another listed option fit your study better?",
    )


def test_another_family_with_several_methods_is_named_once():
    answer = render_outcome_clarification(_puma_recommendation(), POLICY)
    options = answer.split("Other compatible option(s):\n", 1)[1].split("\n\n", 1)[0].splitlines()

    assert "- If you need a tF-only regulatory network instead" not in answer
    assert "- If you need a TF-only regulatory network instead: **PANDA**, **LIONESS-PANDA**, **OTTER**." in options
    assert any(line.startswith("- **LIONESS-PUMA** — preferred when") for line in options)
    assert any(line.startswith("- **GIRAFFE** — preferred when") for line in options)
    assert len(options) == 3


def test_downstream_notes_wait_for_a_stated_concern():
    answer = render_outcome_clarification(_puma_recommendation(), POLICY)
    assert "Downstream use" not in answer and "Targeting scores" not in answer


def test_a_conceptual_card_is_prose_and_an_operational_one_lists_controls():
    decision = TaskDecision(
        action="no_tool", in_scope=True, should_execute=False, intent_type="answer_question", confidence=1.0,
        reason="guidance", capability_match_status="exact", matched_actions=["run_otter"], recommended_actions=["run_otter"],
    )
    from netzoo_agent_core.interpretation.verified_guidance import guidance_contract
    compact = render_verified_guidance(decision, guidance_contract(decision, POLICY, "How does OTTER work?"))
    assert "Routing-level input modality" not in compact and "Other declared controls" not in compact
    assert "Required alternative (provide one):" in compact and "Outputs:" in compact
    # The production facts builder carries the input groups too.
    production = render_verified_guidance(decision, validated_workflow_context(decision, POLICY, task="How does OTTER work?"))
    assert "Required alternative (provide one):" in production and "`coexpression_file`" in production
    detailed = render_verified_guidance(decision, guidance_contract(decision, POLICY, "What are OTTER's parameters and defaults?"))
    assert "Other declared controls" in detailed
