"""Bounded live guidance check; no Planner, Executor, input files or session writes.

Loads the project's configured API credential without printing it. Each case
uses the production router and response node, with their usual call budgets.
"""
from __future__ import annotations
# ruff: noqa: E402 -- local package imports follow the workspace path setup.

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from dotenv import load_dotenv
from netzoo_agent_core.contracts import HumanMessage, WorkflowPlan
from netzoo_agent_core.contracts.outcomes import (
    SemanticDiscriminator, SemanticInterpretation, SemanticPatch, SemanticReview,
)
from netzoo_agent_core.contracts import IntentDecision
from netzoo_agent_core.graph.context import _GraphContext
from netzoo_agent_core.graph.prompts import build_graph_prompts
from netzoo_agent_core.graph.response import respond
from netzoo_agent_core.graph.router_invocation import invoke_router
from netzoo_agent_core.llm import build_llm
from netzoo_agent_core.policy import ProjectPolicyLoader
from netzoo_agent_core.pricing import PriceCatalog


class Events:
    def __init__(self):
        self.events = []

    def append(self, run_id, event_type, node, payload):
        self.events.append({"event_type": event_type, "node": node, "payload": payload})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", action="append")
    parser.add_argument("--output", default="live_report.json")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env", override=False)
    model = "openai/gpt-4o-mini"
    provider = build_llm(model, 0.0, max_output_tokens=1200, timeout_seconds=45)
    policy = ProjectPolicyLoader(ROOT).load()
    prompts = build_graph_prompts(policy)
    events = Events()
    def bind(schema, **kwargs):
        return provider.with_structured_output(
            schema, method="function_calling", include_raw=True, **kwargs,
        )
    context = _GraphContext(
        profile_id="guidance-acceptance", profile_store=None, episode_store=None,
        project_policy=policy, recorder=events, price_catalog=PriceCatalog.from_environment(),
        semantic_interpreter=bind(SemanticInterpretation),
        semantic_reviewer=bind(SemanticReview),
        semantic_patcher=bind(SemanticPatch, strict=True),
        semantic_discriminator=bind(SemanticDiscriminator),
        selection_condition_llm=provider,
        intent_router=provider.with_structured_output(
            IntentDecision, method="function_calling", include_raw=False),
        input_content_mapper=None, response_llm=provider,
        semantic_model_name=model, router_model_name=model, response_model_name=model,
        semantic_prompt=prompts.semantic, intent_prompt=prompts.intent,
        response_prompt=prompts.response, router_max_tokens=1200,
        response_max_tokens=800,
        task_token_budget=int(os.environ.get("NETZOO_MAX_TASK_TOKENS", "20000")),
        review_policy="when_needed",
    )
    rows = []
    cases = json.loads((Path(__file__).parent / "cases.json").read_text())
    for case in cases:
        if args.case and case["id"] not in args.case:
            continue
        events.events.clear()
        result = invoke_router(context, {}, case["prompt"])
        decision = result.decision
        state = {"messages": [HumanMessage(content=case["prompt"])],
                 "decision": decision.model_dump(), "tool_results": [],
                 "plan": WorkflowPlan(workflow="NO-TOOL", objective="Guidance acceptance",
                                      decision=decision.model_dump(), status="respond_only").model_dump(),
                 **result.routing_state, "token_usage": result.usage.model_dump(),
                 "budget_warnings": result.budget_warnings}
        answer = respond(context, state)
        row = {"id": case["id"], "decision": decision.model_dump(),
               "answer": str(answer["messages"][0].content),
               "usage": answer.get("token_usage", result.usage.model_dump()),
               "events": list(events.events)}
        rows.append(row)
        (Path(__file__).parent / args.output).write_text(json.dumps({
            "model": model, "scope": "live_production_guidance_no_analysis_execution",
            "results": rows,
        }, ensure_ascii=False, indent=2, default=str)+"\n")
        print(json.dumps({"id":case["id"],"status":decision.capability_match_status,
                          "matched":decision.matched_actions,"candidates":decision.hypothesis_actions,
                          "recommendation":decision.advisory_recommendation.action
                          if decision.advisory_recommendation else None,
                          "should_execute":decision.should_execute,
                          "answer":row["answer"]},ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
