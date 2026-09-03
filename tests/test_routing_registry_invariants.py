"""Registry-derived invariants: new workflows inherit these tests automatically.

These check deterministic contracts, not natural-language model performance.
No graph engine, provider credentials, scientific packages or Docker required.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import OutcomeHypothesis, RequestedOutcome  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402
from workflow_registry import ACTION_DEFINITIONS, OUTPUT_CAPABILITIES  # noqa: E402
from netzoo_agent_core.contracts.artifact_semantics import ARTIFACT_SEMANTICS  # noqa: E402


def requested(capability, input_artifact):
    granularity = next(value for value in ("sample_specific", "aggregate", "not_applicable")
                       if value in capability.granularities)
    return RequestedOutcome(
        operation=capability.operation, input_artifacts=[input_artifact],
        artifact_type=capability.artifact_type, entity_types=sorted(capability.entity_types & (
            ARTIFACT_SEMANTICS[capability.artifact_type].entities or capability.entity_types
        )),
        regulator_types=sorted(capability.regulator_types),
        target_types=sorted(capability.target_types), granularity=granularity,
    )


@pytest.mark.parametrize("action,artifact", [
    (action, artifact) for action, capability in OUTPUT_CAPABILITIES.items()
    for artifact in sorted(capability.input_artifacts)
])
def test_compatible_named_workflow_preserves_its_registry_contract(action, artifact):
    capability = OUTPUT_CAPABILITIES[action]
    result = match_semantic_request(
        f"Use {ACTION_DEFINITIONS[action].workflow} for this scientific result.",
        [OutcomeHypothesis(outcome=requested(capability, artifact), confidence=1)],
        request_mode="execute",
    )

    assert result.status == "exact"
    assert result.matched_actions == [action]


@pytest.mark.parametrize("mode", ["guidance", "execute"])
@pytest.mark.parametrize("action,artifact", [
    (action, artifact) for action, capability in OUTPUT_CAPABILITIES.items()
    for artifact in sorted(capability.incompatible_input_artifacts)
])
def test_tool_name_never_bypasses_declared_incompatible_input(action, artifact, mode):
    result = match_semantic_request(
        f"Use {ACTION_DEFINITIONS[action].workflow} for this scientific result.",
        [OutcomeHypothesis(outcome=requested(OUTPUT_CAPABILITIES[action], artifact), confidence=1)],
        request_mode=mode,
    )

    assert action not in result.matched_actions


def test_every_registered_workflow_has_a_testable_input_and_output_contract():
    for action, capability in OUTPUT_CAPABILITIES.items():
        assert capability.input_artifacts, action
        assert capability.granularities, action
        assert not capability.input_artifacts & capability.incompatible_input_artifacts, action
        assert capability.artifact_type != "unknown", action
