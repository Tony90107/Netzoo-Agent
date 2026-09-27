"""Log 194: a one-candidate tie is answered deterministically, so the evaluator scores it.

Before Log 194 such a row said `answer_scope: response_model`: the reply was the
response model's, which this evaluator does not pay for. The registry now
supplies the question, and the row is scored like any other deterministic reply.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from test_ambiguous_guidance_is_scored import row  # noqa: E402
from test_routing_evaluation import hypothesis  # noqa: E402

TASK = (
    "I have a regulator-gene link table. I'd like to know whether groups of regulators "
    "jointly control groups of genes, and who the most central members of each group are."
)


def test_the_case_9_shape_is_scored_as_a_deterministic_reply():
    item = hypothesis()
    item["outcome"] = {
        "operation": "infer", "input_artifacts": [], "artifact_type": "community_assignment",
        "entity_types": [], "regulator_types": [], "target_types": [], "granularity": "aggregate",
    }
    item["evidence"] = [
        {"dimension": "artifact_type", "value": "community_assignment", "source": "inferred",
         "rationale": "Groups of regulators and genes are communities."},
        {"dimension": "granularity", "value": "aggregate", "source": "inferred",
         "rationale": "One partition of one network."},
    ]

    result, _ = row(item, TASK)

    assert result["status"] == "ambiguous"
    assert result["hypothesis_actions"] == ["run_condor"]
    assert result["answer_evaluated"] and result["answer_scope"] == "deterministic"
    assert "The only registered workflow compatible with this request is **CONDOR**" in result["answer"]
