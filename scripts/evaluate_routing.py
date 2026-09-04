#!/usr/bin/env python3
"""Opt-in raw-prompt routing evaluation; never invokes planning or execution.

Default: validate the corpus only. Live: call the same structured adapters and
invoke_router boundary as the app. Injectable providers are for offline contract
tests, and their reports are explicitly labelled fixture, not model accuracy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from netzoo_agent_core.contracts import (
    DEFAULT_ROUTER_MAX_TOKENS, DEFAULT_ROUTER_MODEL, DEFAULT_TASK_TOKEN_BUDGET,
    HumanMessage, IntentDecision, ROUTER_CONTEXT_MAX_CHARS, WorkflowPlan,
)
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation, SemanticReview
from netzoo_agent_core.graph.context import _GraphContext
from netzoo_agent_core.graph.prompts import build_graph_prompts
from netzoo_agent_core.graph.router_invocation import invoke_router
from netzoo_agent_core.graph.response import respond
from netzoo_agent_core.evaluation.guidance_surface import capture_progress, score_surface
from netzoo_agent_core.interpretation.semantic_goal import publish_routing_progress
from netzoo_agent_core.presentation import _trace
from netzoo_agent_core.llm import build_llm, build_semantic_reviewer_messages, validate_router_model
from netzoo_agent_core.policy import ProjectPolicyLoader
from netzoo_agent_core.pricing import PriceCatalog
from workflow_registry import ArtifactType, EntityType, Granularity, RecommendedAction
from routing_repair_replay import OBSERVED_ISSUES, RepairReplayProvider

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = PROJECT_ROOT / "tests" / "routing_scenarios.json"


class _ConfigurationError(ValueError):
    """Safe, evaluator-owned error text (not a provider response)."""


class RoutingExpectation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["exact", "fallback", "ambiguous", "unsupported", "not_applicable"]
    actions: list[RecommendedAction]
    forbidden_actions: list[RecommendedAction] = Field(default_factory=list)
    input_artifacts: list[ArtifactType] | None = None
    artifact_type: ArtifactType | None = None
    granularity: Granularity | None = None
    entity_types: list[EntityType] | None = None
    answer_required: list[str] = Field(default_factory=list)
    answer_forbidden: list[str] = Field(default_factory=list)
    require_clarification: bool = False

    @model_validator(mode="after")
    def consistent(self):
        if (self.status in {"exact", "fallback"}) != bool(self.actions):
            raise ValueError("Only exact or fallback expectations may select actions, and must select at least one.")
        if set(self.actions) & set(self.forbidden_actions):
            raise ValueError("Expected actions cannot also be forbidden.")
        if len(self.actions) != len(set(self.actions)):
            raise ValueError("Expected actions must be unique.")
        return self


class RoutingScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    language: Literal["en", "zh", "mixed"]
    category: Literal["positive", "negative", "history", "paraphrase"]
    prompt: str = Field(min_length=1, max_length=ROUTER_CONTEXT_MAX_CHARS)
    expected: RoutingExpectation


def load_scenarios(path: Path) -> list[RoutingScenario]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not raw:
        raise ValueError("Routing corpus must be a non-empty list.")
    cases = [RoutingScenario.model_validate(item) for item in raw]
    if len({case.id for case in cases}) != len(cases):
        raise ValueError("Routing case IDs must be unique.")
    return cases


class _EventRecorder:
    """Capture only in-memory route diagnostics, without persistent user state."""

    def __init__(self):
        self.events: list[dict] = []

    def append(self, _run_id, event_type, _node, payload):
        self.events.append({"type": event_type, "payload": payload})


def _fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _breakdown(results, field):
    return {
        key: {
            "trials": len(items),
            "passed": sum(item["passed"] for item in items),
            "pass_rate": sum(item["passed"] for item in items) / len(items),
        }
        for key in sorted({item[field] for item in results})
        if (items := [item for item in results if item[field] == key])
    }


def _diagnostics(events, reason_code):
    codes = set()
    for event in events:
        kind, payload = event["type"], event["payload"]
        if kind == "routing.semantic_interpretation_rejected":
            issues = payload.get("issues", [])
            codes.add("schema_validation" if any(str(item).startswith("schema_validation:") for item in issues)
                      else "evidence_validation")
        if kind == "routing.semantic_interpreter_failed":
            issues = payload.get("validation_issues", [])
            codes.add(("schema_validation" if isinstance(issues[0], dict) else "evidence_validation")
                      if issues else "provider")
        if kind == "budget.blocked":
            codes.add("budget")
    if reason_code == "intent_fallback":
        codes.add("intent")
    return sorted(codes)


def _score(case, result, events):
    decision, expected = result.decision, case.expected
    event_types = {event["type"] for event in events}
    accepted = "routing.semantic_interpretation_accepted" in event_types
    recovered = "routing.semantic_guidance_recovered" in event_types
    route_errors = []
    if decision.capability_match_status != expected.status:
        route_errors.append(f"status: expected {expected.status}, got {decision.capability_match_status}")
    if set(decision.matched_actions) != set(expected.actions):
        route_errors.append(f"actions: expected {expected.actions}, got {decision.matched_actions}")
    forbidden = set(expected.forbidden_actions) & set(decision.matched_actions + decision.recommended_actions)
    if forbidden:
        route_errors.append(f"forbidden_actions: {sorted(forbidden)}")
    if expected.require_clarification and not decision.clarification_question:
        route_errors.append("clarification: a real missing scientific choice must be surfaced")
    if expected.status == "exact" and decision.clarification_question:
        route_errors.append("clarification: unnecessary question for a complete scientific goal")

    semantic_errors = []
    if not accepted:
        semantic_errors.append("semantic_acceptance: no validated review; fallback is not semantic success")
    actual_outcome = decision.requested_outcome.model_dump() if decision.requested_outcome else {}
    for dimension in ("input_artifacts", "artifact_type", "granularity", "entity_types"):
        wanted = getattr(expected, dimension)
        actual = actual_outcome.get(dimension)
        if wanted is not None and (set(actual or []) != set(wanted) if isinstance(wanted, list) else actual != wanted):
            semantic_errors.append(f"{dimension}: expected {wanted}, got {actual}")
    request_mode = result.routing_state.get("semantic_goal", {}).get("request_mode")
    if request_mode != "guidance":
        semantic_errors.append(f"request_mode: expected guidance, got {request_mode}")

    safety_errors = []
    if decision.should_execute or decision.action != "no_tool":
        safety_errors.append("execution: a guidance case must never authorize an action")
    roles = [call.role for call in result.usage.calls]
    if len(roles) > 3:
        safety_errors.append("call_limit: routing exceeded interpreter/reviewer/intent bound")
    pipeline_errors = [] if result.reason_code == "semantic_registry_intent" else [
        f"pipeline: {result.reason_code}",
    ]
    errors = route_errors + semantic_errors + safety_errors + pipeline_errors
    repair_attempted = any(event["type"] == "routing.semantic_interpretation_rejected"
                           and event["payload"].get("attempt") == 1 for event in events)
    return {
        "review_repair_attempted": repair_attempted,
        "review_repair_validated": repair_attempted and accepted,
        "review_repair_correct": repair_attempted and not semantic_errors and not route_errors,
        "id": case.id, "language": case.language, "category": case.category,
        "passed": not errors, "route_passed": not route_errors,
        "semantic_passed": not semantic_errors, "errors": errors,
        "path": "registry_recovery" if recovered else result.reason_code,
        "diagnostics": _diagnostics(events, result.reason_code),
        "status": decision.capability_match_status, "matched_actions": decision.matched_actions,
        "match_basis": decision.match_basis,
        "rejected_methods": [item.model_dump() for item in decision.rejected_methods],
        "outcome": actual_outcome, "request_mode": request_mode,
        "action": decision.action, "should_execute": decision.should_execute,
        "call_roles": roles,
        "call_statuses": [call.status for call in result.usage.calls],
        "total_tokens": result.usage.total_tokens,
    }


def _score_answer(case, result, context, progress=""):
    """Exercise the production final guidance node without extra provider calls.

    Unselected/general free-prose answers are outside this bounded evaluator;
    explicitly requiring an answer for such a case fails instead of fabricating a pass.
    """
    decision = result.decision
    if decision.action != "no_tool" or decision.should_execute or not (
        decision.capability_match_status in {"exact", "fallback"}
        and any(action in context.project_policy.workflows for action in decision.matched_actions)
        or decision.rejected_methods or decision.match_basis in {"semantic_validation_recovery", "provider_unavailable"}
    ):
        return {"answer_evaluated": False, "answer_passed": None, "answer": "",
                "answer_errors": ["answer: no verified guidance available"]
                if case.expected.answer_required or case.expected.answer_forbidden else []}
    plan = WorkflowPlan(workflow="NO-TOOL", objective="Evaluate guidance only",
                        decision=decision.model_dump(), status="respond_only")
    state = {
        "messages": [HumanMessage(content=case.prompt)], "decision": decision.model_dump(),
        "plan": plan.model_dump(), "tool_results": [], **result.routing_state,
    }
    response = respond(context, state)
    answer = str(response["messages"][0].content)
    errors = [f"answer_missing: {value}" for value in case.expected.answer_required if value.casefold() not in answer.casefold()]
    errors.extend(f"answer_forbidden: {value}" for value in case.expected.answer_forbidden if value.casefold() in answer.casefold())
    if not answer.strip():
        errors.append("answer: empty")
    if response.get("token_usage"):
        errors.append("answer: selected guidance unexpectedly used the free-response path")
    progress = progress.getvalue() if hasattr(progress, "getvalue") else progress
    return {"answer_evaluated": True, "answer_passed": not errors, "answer": answer, "answer_errors": errors,
            **score_surface(decision, state, progress, answer)}


def evaluate(
    cases: list[RoutingScenario], *, provider, model_name: str,
    source: Literal["fixture", "live"] = "fixture", repeat: int = 1,
    task_token_budget: int = DEFAULT_TASK_TOKEN_BUDGET,
) -> dict:
    if not cases or not 1 <= repeat <= 5:
        raise ValueError("Evaluation requires cases and 1-5 repetitions.")
    replay = isinstance(provider, RepairReplayProvider)
    if replay and any(case.id not in OBSERVED_ISSUES for case in cases):
        raise ValueError("Repair replay supports only the three original cases.")
    policy = ProjectPolicyLoader(PROJECT_ROOT).load()
    prompts = build_graph_prompts(policy)
    recorder = _EventRecorder()
    context = _GraphContext(
        profile_id="routing-evaluation", profile_store=None, episode_store=None,
        project_policy=policy, recorder=recorder, price_catalog=PriceCatalog.from_environment(),
        semantic_interpreter=provider.with_structured_output(SemanticInterpretation, method="function_calling", include_raw=True),
        semantic_reviewer=provider.with_structured_output(SemanticReview, method="function_calling", include_raw=True),
        intent_router=provider.with_structured_output(IntentDecision, method="function_calling", include_raw=False),
        input_content_mapper=None, response_llm=None,
        semantic_model_name=model_name, router_model_name=model_name, response_model_name=model_name,
        semantic_prompt=prompts.semantic, intent_prompt=prompts.intent, response_prompt=prompts.response,
        router_max_tokens=DEFAULT_ROUTER_MAX_TOKENS, response_max_tokens=0,
        task_token_budget=task_token_budget,
    )
    results = []
    for case in cases:
        for trial in range(1, repeat + 1):
            recorder.events.clear()
            if replay:
                provider.case_id = case.id
            # The answer key is deliberately never sent to the runtime or provider.
            with capture_progress() as progress:
                _trace("intent", "Interpreting the request and capability boundaries")
                result = invoke_router(context, {}, case.prompt)
                publish_routing_progress(result.decision, result.routing_state["semantic_goal"], policy, case.prompt)
                row = {**_score(case, result, recorder.events),
                       **_score_answer(case, result, context, progress), "trial": trial}
            row["errors"].extend(row["answer_errors"])
            row["errors"].extend(row.get("interaction_errors", []))
            row["passed"] = not row["errors"]
            row["provider_calls"] = len(result.usage.calls) - (1 if replay and result.usage.calls else 0)
            row["injected_proposal"] = replay
            results.append(row)
    total = len(results)
    repair_trials = sum(item["review_repair_attempted"] for item in results)
    return {
        "metadata": {
            "source": source, "model": model_name, "temperature": 0.0,
            "first_pass_source": "observed_error_reconstruction_not_raw_capture" if replay else source,
            "policy_hash": policy.policy_hash, "repeat": repeat,
            "corpus_sha256": _fingerprint([case.model_dump() for case in cases]),
            "prompt_schema_sha256": _fingerprint({
                "semantic": prompts.semantic, "intent": prompts.intent,
                "reviewer": [str(message.content) for message in build_semantic_reviewer_messages(
                    prompts.semantic, "<evaluation prompt>", None, (),
                )],
                "schemas": [schema.model_json_schema() for schema in (SemanticInterpretation, SemanticReview, IntentDecision)],
            }),
            "scope": "routing_progress_verified_guidance_next_step_no_planner_executor_or_response_model",
        },
        "summary": {
            "cases": len(cases), "trials": total,
            "passed": sum(item["passed"] for item in results),
            "pass_rate": sum(item["passed"] for item in results) / total,
            "route_pass_rate": sum(item["route_passed"] for item in results) / total,
            "semantic_pass_rate": sum(item["semantic_passed"] for item in results) / total,
            "answer_evaluated_count": sum(item["answer_evaluated"] for item in results),
            "answer_failure_count": sum(bool(item["answer_errors"]) for item in results),
            "interaction_failure_count": sum(bool(item.get("interaction_errors")) for item in results),
            "review_repair_attempts": repair_trials,
            "review_repair_validation_rate": sum(item["review_repair_validated"] for item in results) / repair_trials if repair_trials else None,
            "review_repair_rate": sum(item["review_repair_correct"] for item in results) / repair_trials if repair_trials else None,
            "fallback_count": sum(item["status"] == "fallback" for item in results),
            "registry_recovery_count": sum(item["path"] == "registry_recovery" for item in results),
            "unsafe_execution_count": sum(item["should_execute"] or item["action"] != "no_tool" for item in results),
            "provider_calls": sum(item["provider_calls"] for item in results),
            "diagnostics": dict(Counter(code for item in results for code in item["diagnostics"])),
            "by_language": _breakdown(results, "language"),
            "by_category": _breakdown(results, "category"),
            "unstable_cases": [case.id for case in cases if len({
                (item["status"], tuple(item["matched_actions"]), item["passed"],
                 _fingerprint(item["outcome"]), item["path"], item["should_execute"])
                for item in results if item["id"] == case.id
            }) > 1],
        },
        "results": results,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--case", action="append", default=[], help="Select IDs (repeatable).")
    parser.add_argument("--live", action="store_true", help="Explicitly authorize paid provider calls for the selected public prompts.")
    parser.add_argument("--repair-replay", action="store_true", help="Inject reconstructed observed first-pass errors; evaluate reviewer repair, not raw-prompt accuracy.")
    parser.add_argument("--model", default=DEFAULT_ROUTER_MODEL)
    parser.add_argument("--repeat", type=int, choices=range(1, 6), default=1)
    parser.add_argument("--max-calls", type=int, default=12, help="Reject runs whose worst-case call count exceeds this cap.")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        cases = load_scenarios(args.scenarios)
        unknown = set(args.case) - {case.id for case in cases}
        if unknown:
            raise _ConfigurationError(f"Unknown case IDs: {sorted(unknown)}")
        if args.case:
            cases = [case for case in cases if case.id in args.case]
        if args.repair_replay:
            if args.case and any(case.id not in OBSERVED_ISSUES for case in cases):
                raise _ConfigurationError("Repair replay supports original-q1, original-q2 and original-q3 only.")
            cases = [case for case in cases if case.id in OBSERVED_ISSUES]
        if not args.live:
            report = {"mode": "corpus_validation_only", "cases": len(cases), "ids": [case.id for case in cases]}
        else:
            max_calls = len(cases) * args.repeat * (2 if args.repair_replay else 3)
            if max_calls > args.max_calls or not 0 < args.timeout <= 60:
                raise _ConfigurationError(f"Run needs a cap of at least {max_calls} calls and a timeout in (0, 60].")
            model = validate_router_model(args.model)
            if not os.environ.get("OPENROUTER_API_KEY"):
                raise _ConfigurationError("Live evaluation requires OPENROUTER_API_KEY in the environment; no secrets are loaded automatically.")
            provider = build_llm(model, 0.0, max_output_tokens=DEFAULT_ROUTER_MAX_TOKENS, timeout_seconds=args.timeout)
            if args.repair_replay:
                provider = RepairReplayProvider(provider)
            report = evaluate(cases, provider=provider, model_name=model, source="live", repeat=args.repeat)
    except (ValueError, OSError, ImportError) as error:
        # Do not echo provider payloads, credentials, or Pydantic input values.
        message = str(error) if isinstance(error, _ConfigurationError) else type(error).__name__
        print(f"Routing evaluation configuration error: {message}", file=sys.stderr)
        return 2
    if args.json or not args.live:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for item in report["results"]:
            print(f"[{'PASS' if item['passed'] else 'FAIL'}] {item['id']} trial={item['trial']} path={item['path']}")
            for error in item["errors"]:
                print(f"  - {error}")
        print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 0 if not args.live or report["summary"]["passed"] == report["summary"]["trials"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
