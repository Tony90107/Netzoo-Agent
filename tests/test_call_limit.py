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

    assert result["call_roles"] == [*ROUTING, "hypothesis_bases"]
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


# Log 217: the pre-run `--max-calls` check assumed three calls per trial
# (two in a repair replay) after the discriminator and the condition call had
# made it five; 35 of 369 recorded legacy live trials made five.

def test_the_pre_run_cap_is_the_scored_bound():
    from evaluate_routing import worst_case_calls

    result, _ = row()

    # Log 244: two sibling repairs (Log 242) are bounded apart from routing;
    # this method tie makes none, so it reaches the bound without them.
    assert len(result["call_roles"]) == 5
    assert worst_case_calls(1, 1) == 5 + 2
    assert worst_case_calls(1, 1, repair_replay=True) == 6
    assert worst_case_calls(39, 3) == 819


@pytest.mark.parametrize("args, cap, reaches_provider", [
    (["--case", "original-q1"], 6, False),
    (["--case", "original-q1"], 7, True),
    (["--repair-replay"], 17, False),
    (["--repair-replay"], 18, True),
])
def test_a_run_is_admitted_only_under_its_worst_case(monkeypatch, capsys, args, cap, reaches_provider):
    import evaluate_routing

    built = []

    def stop(*_args, **_kwargs):
        built.append(True)
        raise ValueError("stop before any provider call")

    monkeypatch.setenv("OPENROUTER_API_KEY", "offline-placeholder")
    monkeypatch.setattr(evaluate_routing, "build_llm", stop)

    assert evaluate_routing.main(["--live", *args, "--max-calls", str(cap), "--json"]) == 2
    assert bool(built) is reaches_provider
    assert ("Run needs a cap" in capsys.readouterr().err) is not reaches_provider
