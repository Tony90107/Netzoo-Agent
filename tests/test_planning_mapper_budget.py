"""Planner advisory model calls share the task budget and usage ledger."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.contracts import (  # noqa: E402
    HumanMessage, InputRoleMapping, LLMUsage, TaskDecision, UserProfile, WorkflowPlan,
)
from netzoo_agent_core.graph.routing_planning import plan_task  # noqa: E402
from netzoo_agent_core.pricing import PriceCatalog  # noqa: E402


def _run_plan(*, consumed: int, response=None):
    decision = TaskDecision(
        action="run_panda", in_scope=True, should_execute=True,
        confidence=1.0, reason="Run PANDA.",
    )
    plan = WorkflowPlan(
        workflow="PANDA", objective="Run PANDA.", decision=decision.model_dump(),
        status="needs_input", question="Provide inputs.",
    )
    if response is None:
        response = InputRoleMapping(assignments=[])
    underlying = Mock()
    underlying.with_structured_output.return_value.invoke.return_value = response
    context = SimpleNamespace(
        input_content_mapper=underlying,
        profile_store=Mock(pending=Mock(return_value=[])),
        recorder=Mock(),
        task_token_budget=20_000,
        router_model_name="test-router",
        router_max_tokens=512,
        price_catalog=PriceCatalog.from_environment(),
    )
    state = {
        "messages": [HumanMessage(content="Run PANDA")],
        "decision": decision.model_dump(),
        "profile": UserProfile(profile_id="test").model_dump(),
        "token_usage": LLMUsage(total_tokens=consumed, budget_tokens=20_000).model_dump(),
        "run_id": "test-run",
    }

    def build(*args, content_mapper=None, **kwargs):
        try:
            content_mapper.with_structured_output(
                InputRoleMapping, method="function_calling", include_raw=False,
            ).invoke([HumanMessage(content="Map the listed input files.")])
        except Exception:
            pass  # Advisory mapping may decline when its budget is exhausted.
        return plan

    with patch("netzoo_agent_core.graph.routing_planning.build_workflow_plan", side_effect=build):
        update = plan_task(context, state)
    return update, underlying, context


def test_planning_mapper_call_is_in_the_task_usage_ledger():
    update, underlying, context = _run_plan(consumed=0)
    underlying.with_structured_output.return_value.invoke.assert_called_once()
    calls = update["token_usage"]["calls"]
    assert len(calls) == 1
    assert calls[0]["role"] == "input_content_mapper"
    assert update["token_usage"]["total_tokens"] > 0
    assert any(call.args[1] == "llm.completed" for call in context.recorder.append.call_args_list)


def test_planning_mapper_does_not_call_provider_after_budget_is_exhausted():
    update, underlying, context = _run_plan(consumed=19_999)
    underlying.with_structured_output.return_value.invoke.assert_not_called()
    assert update["token_usage"]["total_tokens"] == 19_999
    assert any(call.args[1] == "budget.blocked" for call in context.recorder.append.call_args_list)


def test_planning_mapper_records_structured_parse_failure():
    update, underlying, _ = _run_plan(
        consumed=0,
        response={"parsed": None, "raw": None, "parsing_error": "invalid structure"},
    )
    underlying.with_structured_output.return_value.invoke.assert_called_once()
    assert update["token_usage"]["calls"][0]["status"] == "failed"
