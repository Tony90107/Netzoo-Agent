"""Budgeted, metered adapter for advisory planner model calls."""

from __future__ import annotations

import time
from typing import Any

from ..contracts import LLMUsage
from ..llm import append_llm_usage
from .context import preflight_budget, record_event
from .structured_calls import _serialized_structured_input


class PlanningMapper:
    def __init__(self, mapper: Any, context: Any, state: dict, schema=None):
        self._mapper = mapper
        self._context = context
        self._state = state
        self._schema = schema
        self.usage = LLMUsage.model_validate(
            state.get("token_usage") or {"budget_tokens": context.task_token_budget}
        )
        self.budget_warnings = list(state.get("budget_warnings", []))

    def with_structured_output(self, schema, **kwargs):
        bound = (
            self._mapper.with_structured_output(
                schema, **{**kwargs, "include_raw": True},
            )
            if hasattr(self._mapper, "with_structured_output")
            else self._mapper
        )
        child = PlanningMapper(bound, self._context, self._state, schema)
        child.usage = self.usage
        child.budget_warnings = self.budget_warnings
        # Both the parent and its bound instance must expose the same ledger.
        child._parent = self
        return child

    def invoke(self, messages):
        input_text = (
            _serialized_structured_input(messages, self._schema)
            if self._schema is not None
            else "\n".join(str(message.content) for message in messages)
        )
        budget_state = {**self._state, "token_usage": self.usage.model_dump(),
                        "budget_warnings": self.budget_warnings}
        budget, warnings = preflight_budget(
            self._context, budget_state,
            role="input_content_mapper",
            model=self._context.router_model_name,
            input_text=input_text,
            reserved_output_tokens=min(512, self._context.router_max_tokens),
            allow_reserve=False,
        )
        self.budget_warnings[:] = warnings
        if budget.status == "blocked":
            raise RuntimeError("The planner model call exceeds the task token budget.")

        started = time.monotonic()
        response = None
        status = "success"
        try:
            result = self._mapper.invoke(messages)
            if isinstance(result, dict) and "parsed" in result:
                response = result.get("raw")
                parsed = result["parsed"]
                if parsed is None:
                    raise ValueError("Planner structured output failed to parse.")
            else:
                response = result
                parsed = result
            return parsed
        except Exception:
            status = "failed"
            raise
        finally:
            self.usage = append_llm_usage(
                self.usage,
                role="input_content_mapper",
                model=self._context.router_model_name,
                response=response,
                input_text=input_text,
                output_text=str(response) if response is not None else "",
                budget_tokens=self._context.task_token_budget,
                duration_ms=int((time.monotonic() - started) * 1000),
                status=status,
                price_catalog=self._context.price_catalog,
            )
            record_event(
                self._context, self._state, "llm.completed", "plan",
                self.usage.calls[-1].model_dump(mode="json"),
            )
            if hasattr(self, "_parent"):
                self._parent.usage = self.usage
