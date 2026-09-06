"""A workflow the user reports having already run is not the one being asked about.

Live full-corpus round 3 recommended PANDA -- a forbidden action for that case --
to a request whose only mention of it was "Previously I used PANDA" and which
said in the same breath that it did not want inferred networks. The semantic pass
had failed, so `recover_registry_guidance` fell back to the written name.

`_match_semantic_request` already refuses to let a historical mention override a
compatible typed outcome; its comment says so. But that guard needs an outcome to
protect, and after validation fails there is none. The name resolver itself now
reads only the request's non-historical clauses, using the same deterministic
clause scoping `input_mentions` applies to input artifacts.

This is the standing prohibition on treating historical data as current input,
applied to the one place that still ignored it.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.interpretation.provider_fallback import (  # noqa: E402
    recover_registry_guidance,
)
from netzoo_agent_core.policy import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.routing.outcome_matching import named_workflow_action  # noqa: E402

from evaluate_routing import DEFAULT_SCENARIOS, load_scenarios  # noqa: E402

CASES = {case.id: case for case in load_scenarios(DEFAULT_SCENARIOS)}


@pytest.mark.parametrize("task", [
    "Previously I used PANDA. Now I want advice on acquiring protein abundance measurements.",
    "I used PANDA earlier. Which workflow finds bipartite communities?",
    "我之前做過 PANDA；現在以突變資料對病人做分組。",
])
def test_a_name_only_in_a_historical_clause_is_not_resolved(task):
    assert named_workflow_action(task) is None


@pytest.mark.parametrize("task,expected", [
    ("Use OTTER for an aggregate TF-to-gene network.", "run_otter"),
    ("Previously I used SAMBAR. Now run PANDA on this expression matrix.", "run_panda"),
    ("If I obtain a mutation matrix, could SAMBAR help?", "run_sambar"),
])
def test_a_name_outside_the_history_still_resolves(task, expected):
    """History scoping must not swallow the clause the user is actually asking about."""
    assert named_workflow_action(task) == expected


def test_the_harness_continuation_marker_still_resolves():
    """Injected markers are not natural-language history and must keep working."""
    assert named_workflow_action("PREVIOUS_ACTION=run_panda") == "run_panda"


def test_the_negative_control_no_longer_gets_a_forbidden_recommendation():
    case = CASES["unsupported-protein-acquisition"]
    forbidden = set(case.expected.forbidden_actions)

    decision = recover_registry_guidance(
        case.prompt, ProjectPolicyLoader().load().workflows, ValueError()
    )

    assert forbidden
    assert decision is None or not forbidden.intersection(decision.matched_actions)


def test_a_proposed_method_is_still_a_current_mention():
    """Q3 proposes PANDA rather than reporting it, so the input contract must
    still get the chance to reject it. Scoping history away must not hide that."""
    assert named_workflow_action(CASES["original-q3"].prompt) == "run_panda"
