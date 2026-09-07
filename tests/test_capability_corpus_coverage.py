"""Every registered capability must be reachable, and the corpus must reach it.

Two defects this file exists to stop recurring.

A capability can be unreachable by construction: an earlier round found CONDOR
selectable only through a value the prompt reserves for something else, and the
corpus had no case for it, so nothing failed and nobody noticed. PANDA is the
same shape today -- its selection tags are a proper subset of OTTER's and
GIRAFFE's, so no outcome can single it out -- and it is listed below rather than
hidden.

And an expectation can be impossible: adding a corpus case for an unreachable
capability would depress the score forever for a reason that has nothing to do
with the model. So the corpus is checked against reachability, not just parsed.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from evaluate_routing import DEFAULT_SCENARIOS, load_scenarios  # noqa: E402
from netzoo_agent_core.contracts.outcomes import OutcomeHypothesis  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import match_semantic_request  # noqa: E402
from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402

# Reachability is a registry property, not a model one: a capability whose
# selection tags are a subset of another's cannot be singled out by any outcome.
KNOWN_UNREACHABLE = {"run_panda"}

TASK = "Which registered workflow should I use? Advice only."


def _best_outcome(action):
    """The outcome that capability's own definition implies, at its own values."""
    capability = OUTPUT_CAPABILITIES[action]
    granularities = capability.granularities or {"aggregate"}
    granularity = "aggregate" if "aggregate" in granularities else sorted(granularities)[0]
    return {
        "operation": capability.operation,
        "input_artifacts": sorted(capability.input_artifacts)[:1],
        "artifact_type": capability.artifact_type,
        "entity_types": [],
        "regulator_types": sorted(capability.regulator_types),
        "target_types": sorted(capability.target_types),
        "selection_tags": sorted(capability.selection_tags),
        "granularity": granularity,
    }


def _match(action):
    hypothesis = OutcomeHypothesis.model_validate(
        {"outcome": _best_outcome(action), "confidence": 0.9, "evidence": []}
    )
    return match_semantic_request(TASK, [hypothesis], request_mode="guidance")


@pytest.mark.parametrize("action", sorted(OUTPUT_CAPABILITIES))
def test_each_capability_is_reachable_or_listed_as_not(action):
    result = _match(action)
    reachable = result.status == "exact" and result.matched_actions == [action]

    if action in KNOWN_UNREACHABLE:
        assert not reachable, (
            f"{action} is now reachable; remove it from KNOWN_UNREACHABLE and "
            "add a corpus case for it."
        )
        return
    assert reachable, (
        f"{action} cannot be singled out by its own definition "
        f"(got {result.status} {result.matched_actions or result.hypothesis_actions}). "
        "Give it a distinguishing selection tag or add it to KNOWN_UNREACHABLE "
        "with the reason."
    )


def test_the_corpus_never_expects_an_unreachable_capability():
    expected = {
        action for case in load_scenarios(DEFAULT_SCENARIOS)
        for action in (case.expected.actions or [])
    }

    assert not expected & KNOWN_UNREACHABLE


def test_the_corpus_covers_every_reachable_capability():
    """Half the registry had no case at all when this was written."""
    expected = {
        action for case in load_scenarios(DEFAULT_SCENARIOS)
        for action in (case.expected.actions or [])
    }
    uncovered = set(OUTPUT_CAPABILITIES) - expected - KNOWN_UNREACHABLE

    assert not uncovered, f"reachable capabilities with no corpus case: {sorted(uncovered)}"
