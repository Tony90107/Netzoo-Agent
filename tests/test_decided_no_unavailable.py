"""decided-no-unavailable-2026-10-29: a decided core call is never shown as "Semantic routing unavailable"."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.contracts.core_decision import CoreDecision  # noqa: E402
from netzoo_agent_core.interpretation.guidance_interaction import guidance_interaction  # noqa: E402


def _fallback(core=None):
    return TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=0.0, reason="r",
                        capability_match_status="fallback", core=core)


def test_a_decided_call_has_no_unavailable_notice():
    assert guidance_interaction(_fallback(CoreDecision(kind="DECLINE", basis="full_gap"))) is None
    assert guidance_interaction(_fallback(CoreDecision(kind="DO", basis="results_given"))) is None


def test_an_unchecked_or_missing_core_keeps_the_notice():
    for core in (CoreDecision(kind="UNCHECKED", basis="routing_failed"), None):
        found = guidance_interaction(_fallback(core))
        assert found is not None and found.status == "routing_unavailable"
