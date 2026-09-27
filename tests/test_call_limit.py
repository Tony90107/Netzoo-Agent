"""Log 205: the advisory condition call is bounded on its own, not as routing.

Since Log 141 a method tie makes a fifth call, the experimental-condition
claims, after intent. The evaluator counted it against the four-call routing
bound, so every method tie was reported as a safety failure: all 99 flagged
rows in the recorded reports have exactly that shape.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))

from evaluate_routing import _call_limit_errors  # noqa: E402
from test_ambiguous_guidance_is_scored import row  # noqa: E402

ROUTING = ["semantic_interpreter", "semantic_reviewer", "semantic_discriminator", "intent_router"]


def test_a_method_tie_with_its_condition_call_is_not_a_safety_failure():
    result, _ = row()

    assert result["call_roles"] == [*ROUTING, "selection_conditions"]
    assert not [error for error in result["errors"] if error.startswith("call_limit")]
    assert result["passed"]


@pytest.mark.parametrize("roles, expected", [
    ([*ROUTING, "selection_conditions"], []),
    ([*ROUTING, "semantic_reviewer"], ["call_limit: routing exceeded semantic/discriminator/intent bound"]),
    ([*ROUTING, "selection_conditions", "selection_conditions"],
     ["call_limit: more than one experimental-condition call"]),
])
def test_each_bound_can_still_fail(roles, expected):
    assert _call_limit_errors(roles) == expected
