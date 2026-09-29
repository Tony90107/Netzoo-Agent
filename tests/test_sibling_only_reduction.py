"""Log 279: a sibling repair keeps alternatives beside the primary reading, never replaces it.

Recorded blind case 6 (batch effect in co-expression): the patch left the
primary co-expression reading invalid, the sibling repair validated a stray
sample-distance reading with an unrelated quote, and dropping the invalid
primary left that sibling alone -- an exact SAMBAR match for a request that
never mentions mutations. Replayed offline from the recorded provider replies.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "scripts"))

from evaluate_routing import RoutingScenario, evaluate  # noqa: E402
from netzoo_agent_core.graph.partial_validity import issue_indices  # noqa: E402

FIXTURE = json.loads((HERE / "log279_case6_calls.json").read_text(encoding="utf-8"))


class RecordedProvider:
    def __init__(self, calls):
        self.calls, self.seen = list(calls), []

    def with_structured_output(self, schema, **kwargs):
        provider = self

        class Adapter:
            def invoke(self, messages):
                call = provider.calls.pop(0)
                assert call["schema"] == schema.__name__, (call["schema"], schema.__name__)
                provider.seen.append(schema.__name__)
                return schema.model_validate(call["args"]) if schema.__name__ == "IntentDecision" else call["args"]

        return Adapter()


def _replay():
    case = RoutingScenario.model_validate({
        "id": "log279-case6", "language": "en", "category": "positive", "prompt": FIXTURE["prompt"],
        "expected": {"status": "ambiguous", "actions": []},
    })
    return evaluate([case], provider=RecordedProvider(FIXTURE["calls"]), model_name="recorded")["results"][0]


def test_a_repaired_sibling_cannot_become_the_only_reading():
    result = _replay()

    assert "run_sambar" not in (result.get("matched_actions") or [])
    assert result["status"] != "exact"
    assert result["action"] == "no_tool" and not result["should_execute"]


def test_issue_positions_are_read_from_validation_messages():
    assert issue_indices(["hypothesis[0].missing_evidence:granularity=aggregate",
                          "hypothesis[1].missing_evidence:artifact_type=x", "request_mode"]) == {0, 1}
