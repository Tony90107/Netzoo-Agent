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
from workflow_registry import OUTPUT_CAPABILITIES


def score(case, decision, answer):
    """Independent expected results never enter provider messages or routing."""
    errors = []
    if decision.action != "no_tool" or decision.should_execute:
        errors.append("guidance_authorized_execution")
    actions = set(decision.matched_actions + decision.hypothesis_actions)
    recommendation = decision.advisory_recommendation
    selected = recommendation.action if recommendation else next(iter(actions)) if len(actions) == 1 else None
    expected = case.get("expected_action")
    if expected and selected != expected:
        errors.append(f"expected_choice:{expected};actual:{selected};candidates:{sorted(actions)}")
    if expected and expected not in actions:
        errors.append("expected_method_missing")
    outcome = decision.requested_outcome
    if case.get("expected_artifact") and (not outcome or outcome.artifact_type != case["expected_artifact"]):
        errors.append("wrong_scientific_output")
    if case.get("expected_granularity") and (not outcome or outcome.granularity != case["expected_granularity"]):
        errors.append("wrong_scale")
    if expected:
        from netzoo_agent_core.policy import ProjectPolicyLoader
        name = ProjectPolicyLoader(ROOT).load().workflows[expected].workflow
        if name not in answer:
            errors.append("method_unnamed_in_answer")
    if case.get("expect_gap") and not decision.advisory_capability_gap:
        errors.append("missing_capability_gap")
    if case.get("expect_gap") and (recommendation or decision.matched_actions):
        errors.append("unsupported_philosophy_endorsed")
    if case.get("expect_gap") and answer.count("(recommend)") > 1:
        errors.append("conditional_alternative_multiple_recommendations")
    if case.get("expect_no_recommendation") and (actions or recommendation):
        errors.append("definition_routed_to_method")
    if case.get("expected_choices") and not set(case["expected_choices"]) <= actions:
        errors.append("comparison_lost_alternative")
    if case.get("expect_recommendation") and not recommendation:
        errors.append("comparison_has_no_recommendation")
    if recommendation and answer.count("(recommend)") != 1:
        errors.append("recommendation_marker_not_unique")
    if any("\u3400" <= char <= "\u9fff" for char in answer):
        errors.append("non_english_answer")
    return errors


class Events:
    def __init__(self):
        self.events = []

    def append(self, run_id, event_type, node, payload):
        self.events.append({"event_type": event_type, "node": node, "payload": payload})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", action="append")
    parser.add_argument("--output", default="baseline.json")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    cases = json.loads((Path(__file__).parent / "cases.json").read_text())
    if {c.get("expected_action") for c in cases} - {None} != set(OUTPUT_CAPABILITIES):
        raise ValueError("Every registered scientific workflow needs a corpus case")
    if not args.live:
        print(json.dumps({"source":"corpus_only_no_model_calls", "cases":len(cases), "workflows":len(OUTPUT_CAPABILITIES)}))
        return
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
        row["errors"] = score(case, decision, row["answer"])
        row["passed"] = not row["errors"]
        rows.append(row)
        (Path(__file__).parent / args.output).write_text(json.dumps({
            "model": model, "scope": "live_production_guidance_no_analysis_execution",
            "results": rows,
        }, ensure_ascii=False, indent=2, default=str)+"\n")
        print(json.dumps({"id":case["id"],"passed":row["passed"],"errors":row["errors"],"status":decision.capability_match_status,
                          "matched":decision.matched_actions,"candidates":decision.hypothesis_actions,
                          "recommendation":decision.advisory_recommendation.action
                          if decision.advisory_recommendation else None,
                          "should_execute":decision.should_execute},ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
