"""An `unknown` reading with a recommended workflow renders from the compact catalog.

heldout12 b12 (Log 404), candidate MN3-3, "Why does OTTER need a PPI network as well as expression
data?": the semantic interpreter failed, the outcome stayed `unknown`, the registry intent still
recommended OTTER, and the reply crashed with KeyError 'accepted_input_modalities' -- the compact
catalog keeps only the capability keys a conceptual comparison needs.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evaluate_routing import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.graph.response_context import validated_workflow_context  # noqa: E402
from netzoo_agent_core.interpretation.verified_guidance import render_verified_guidance  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()


def test_a_recommended_workflow_renders_from_the_compact_catalog():
    task = "Why does OTTER need a PPI network as well as expression data?"
    decision = TaskDecision.model_validate({
        "action": "no_tool", "in_scope": True, "should_execute": False, "confidence": 0.9, "reason": "r",
        "recommended_actions": ["run_otter"], "matched_actions": ["run_otter"], "capability_match_status": "exact",
        "requested_outcome": {"operation": "explain", "artifact_type": "unknown", "granularity": "unknown"},
    })
    context = validated_workflow_context(decision, POLICY, task=task)
    otter = next(item for item in context["workflows"] if item["action"] == "run_otter")
    assert "accepted_input_modalities" not in otter["output_capability"]  # the compact catalog

    reply = render_verified_guidance(decision, context)

    assert reply is not None and "**OTTER**" in reply
