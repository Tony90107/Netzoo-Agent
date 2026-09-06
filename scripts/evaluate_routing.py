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
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation, SemanticPatch, SemanticReview
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


def _evidence_census(events) -> list[dict]:
    """One census row per attempt, from whichever event that attempt ended on.

    An attempt reports through more than one event (a final rejection is also a
    failure), and the first pass reports through `_proposed`, which carries no
    attempt number of its own. Both are collapsed to one row per attempt.
    """
    by_attempt: dict[object, list[dict]] = {}
    for event in events:
        if not event["type"].startswith("routing.semantic_interpretation"):
            continue
        census = event["payload"].get("evidence_census")
        if census is None:
            continue
        attempt = event["payload"].get("attempt", 1)
        if attempt not in by_attempt:
            by_attempt[attempt] = [dict(item, attempt=attempt) for item in census]
    return [row for attempt in sorted(by_attempt, key=str) for row in by_attempt[attempt]]


def _span_hypotheses(result: dict) -> list[str]:
    """Classify each hypothesis that wrote any explicit evidence, as one unit.

    Entries inside one hypothesis are not independent, so the base rate that
    decides whether the explicit-evidence contract can be tightened is stated
    per hypothesis, not per entry.
    """
    classes = []
    for row in result["evidence_census"]:
        with_span, without_span = row["explicit_with_span"], row["explicit_without_span"]
        if not with_span and not without_span:
            continue
        classes.append(
            "all_spanned" if not without_span
            else "none_spanned" if not with_span
            else "mixed"
        )
    return classes


def _ungrounded_by_attempt(result: dict) -> dict:
    """Deduplicate the shapes an attempt reports through more than one event.

    A final rejection is recorded twice, as the rejection and as the failure
    that ends the loop. Counting rows would inflate every total.
    """
    by_attempt: dict[object, list[dict]] = {}
    for entry in result["diagnostic_details"]:
        shapes = entry.get("evidence_shapes") or []
        if shapes and entry.get("attempt") not in by_attempt:
            by_attempt[entry.get("attempt")] = shapes
    return by_attempt


def _ungrounded_shapes(result: dict) -> list[dict]:
    return [shape for shapes in _ungrounded_by_attempt(result).values() for shape in shapes]


def _ungrounded_clusters(result: dict) -> list[str]:
    """Classify each hypothesis that carries ungrounded entries, as one unit."""
    groups: dict[tuple, set] = {}
    for attempt, shapes in _ungrounded_by_attempt(result).items():
        for shape in shapes:
            groups.setdefault((attempt, shape.get("hypothesis")), set()).add(shape.get("span"))
    return [
        "all_absent" if spans == {"absent"}
        else "all_unmatched" if spans == {"unmatched"}
        else "mixed"
        for spans in groups.values()
    ]


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


def _diagnostic_details(events) -> list[dict]:
    """Expose the structured issue codes behind each coarse diagnostic category.

    These are the harness's own ontology-scoped codes and Pydantic error
    locations, already recorded to traces. They are not raw provider messages,
    and a rejected value's content appears only when it is a bare identifier.
    """
    details = []
    for event in events:
        payload = event["payload"]
        if event["type"] == "routing.semantic_interpretation_rejected":
            details.append({
                "attempt": payload.get("attempt"),
                "issues": [str(item) for item in payload.get("issues", [])],
                "shapes": list(payload.get("shapes", [])),
                "evidence_shapes": list(payload.get("evidence_shapes", [])),
            })
        if event["type"] == "routing.semantic_interpreter_failed":
            issues = payload.get("validation_issues", [])
            details.append({
                "attempt": payload.get("attempt"),
                "error_type": payload.get("error_type"),
                "evidence_shapes": list(payload.get("evidence_shapes", [])),
                "issues": [
                    "schema_validation:" + ".".join(item["location"]) + ":" + item["type"]
                    if isinstance(item, dict) else str(item)
                    for item in issues
                ],
                "shapes": [item for item in issues if isinstance(item, dict)],
            })
    return details


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
        "diagnostic_details": _diagnostic_details(events),
        "evidence_census": _evidence_census(events),
        # Declared in Log 62 and not built until Log 65: without it the only
        # authorized field write is invisible to the report, and "the model got
        # it right unaided" stops being measurable.
        "restored_fields": [
            dict(item, attempt=event["payload"].get("attempt"))
            for event in events
            if event["type"] == "routing.outcome_input_restored"
            for item in event["payload"].get("restored", [])
        ],
        "status": decision.capability_match_status, "matched_actions": decision.matched_actions,
        "match_basis": decision.match_basis,
        "rejected_methods": [item.model_dump() for item in decision.rejected_methods],
        "outcome": actual_outcome, "request_mode": request_mode,
        # Any assumption keeps a hypothesis advisory, so a correct outcome can
        # still lose its exact match. The count makes that visible; the text is
        # model prose about the request and is deliberately not recorded.
        "assumption_count": sum(
            len(item.assumptions) for item in decision.outcome_hypotheses
        ),
        "action": decision.action, "should_execute": decision.should_execute,
        "call_roles": roles,
        "call_statuses": [call.status for call in result.usage.calls],
        # Which shape the review actually returned, and what it touched. Without
        # this a round cannot tell whether the field-scoped repair was exercised
        # at all, only whether the run happened to pass.
        "review_repair_shape": next(
            ("patch" for event in events
             if event["type"] == "routing.semantic_patch_applied"),
            "review" if repair_attempted else None,
        ),
        "review_patch": next(
            ({key: event["payload"][key] for key in
              ("changed_fields", "evidence_removed", "evidence_added", "evidence_retired_as_stale")}
             for event in events if event["type"] == "routing.semantic_patch_applied"),
            None,
        ),
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
        semantic_patcher=provider.with_structured_output(SemanticPatch, method="function_calling", include_raw=True),
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
            "repair_replay_suite": provider.suite if replay else None,
            "policy_hash": policy.policy_hash, "repeat": repeat,
            "corpus_sha256": _fingerprint([case.model_dump() for case in cases]),
            "prompt_schema_sha256": _fingerprint({
                "semantic": prompts.semantic, "intent": prompts.intent,
                "reviewer": [str(message.content) for message in build_semantic_reviewer_messages(
                    prompts.semantic, "<evaluation prompt>", None, (),
                )],
                "schemas": [schema.model_json_schema() for schema in (SemanticInterpretation, SemanticReview, SemanticPatch, IntentDecision)],
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
            "review_repair_shapes": dict(Counter(
                item["review_repair_shape"] for item in results
                if item["review_repair_shape"] is not None
            )),
            # The falsification target for the field-scoped repair: schema errors
            # the review introduced that the first attempt did not have.
            "review_introduced_schema_issues": sum(
                len({
                    issue for entry in item["diagnostic_details"]
                    if entry.get("attempt") == 2 for issue in entry["issues"]
                    if issue.startswith("schema_validation:")
                } - {
                    issue for entry in item["diagnostic_details"]
                    if entry.get("attempt") == 1 for issue in entry["issues"]
                })
                for item in results
            ),
            "review_repair_validation_rate": sum(item["review_repair_validated"] for item in results) / repair_trials if repair_trials else None,
            "review_repair_rate": sum(item["review_repair_correct"] for item in results) / repair_trials if repair_trials else None,
            "fallback_count": sum(item["status"] == "fallback" for item in results),
            "registry_recovery_count": sum(item["path"] == "registry_recovery" for item in results),
            "unsafe_execution_count": sum(item["should_execute"] or item["action"] != "no_tool" for item in results),
            "provider_calls": sum(item["provider_calls"] for item in results),
            "diagnostics": dict(Counter(code for item in results for code in item["diagnostics"])),
            # Splits the largest issue family in the live record into the two
            # shapes that call for opposite responses: an explicit entry that
            # supplied no quote at all, versus one whose quote the request does
            # not contain. Nothing before this round recorded the difference.
            "ungrounded_evidence_shapes": dict(Counter(
                str(shape.get("span"))
                for item in results for shape in _ungrounded_shapes(item)
            )),
            # Entries within one hypothesis are not independent -- a model that
            # omits the quote omits it for every dimension it wrote. The
            # per-hypothesis grouping is the unit any criterion should use.
            # Log 47's declared unit: does a hypothesis that writes explicit
            # evidence give every such entry a quote, none of them, or some?
            "evidence_span_hypotheses": dict(Counter(
                cluster for item in results for cluster in _span_hypotheses(item)
            )),
            "evidence_span_entries": dict(Counter({
                "with_span": sum(row["explicit_with_span"] for item in results
                                 for row in item["evidence_census"]),
                "without_span": sum(row["explicit_without_span"] for item in results
                                    for row in item["evidence_census"]),
                "inferred": sum(row["inferred"] for item in results
                                for row in item["evidence_census"]),
            })),
            # How often the one authorized write fired, by field. The unaided
            # rate is the complement: a report with a high count and a high pass
            # rate is not the model getting it right.
            "restored_fields": dict(Counter(
                str(entry["field"]) for item in results
                for entry in item["restored_fields"]
            )),
            "trials_with_restored_fields": sum(
                1 for item in results if item["restored_fields"]
            ),
            "ungrounded_evidence_clusters": dict(Counter(
                cluster for item in results
                for cluster in _ungrounded_clusters(item)
            )),
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
    parser.add_argument("--repair-replay-suite", choices=("cross-field", "missing-required", "missing-input"),
                        help="Observed failure batch; requires --repair-replay (default: cross-field).")
    parser.add_argument("--model", default=DEFAULT_ROUTER_MODEL)
    parser.add_argument("--repeat", type=int, choices=range(1, 6), default=1)
    parser.add_argument("--max-calls", type=int, default=12, help="Reject runs whose worst-case call count exceeds this cap.")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.repair_replay_suite and not args.repair_replay:
            raise _ConfigurationError("--repair-replay-suite requires --repair-replay.")
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
            if args.repair_replay:
                report["repair_replay_suite"] = args.repair_replay_suite or "cross-field"
        else:
            max_calls = len(cases) * args.repeat * (2 if args.repair_replay else 3)
            if max_calls > args.max_calls or not 0 < args.timeout <= 60:
                raise _ConfigurationError(f"Run needs a cap of at least {max_calls} calls and a timeout in (0, 60].")
            model = validate_router_model(args.model)
            if not os.environ.get("OPENROUTER_API_KEY"):
                raise _ConfigurationError("Live evaluation requires OPENROUTER_API_KEY in the environment; no secrets are loaded automatically.")
            provider = build_llm(model, 0.0, max_output_tokens=DEFAULT_ROUTER_MAX_TOKENS, timeout_seconds=args.timeout)
            if args.repair_replay:
                provider = RepairReplayProvider(provider, suite=args.repair_replay_suite or "cross-field")
            report = evaluate(cases, provider=provider, model_name=model, source="live", repeat=args.repeat)
    except (ValueError, OSError, ImportError) as error:
        # Do not echo provider payloads, credentials, or Pydantic input values.
        # A missing dependency is a setup mistake, usually the wrong interpreter,
        # and its module name is neither a payload nor a secret; withholding it
        # only costs debugging time.
        if isinstance(error, _ConfigurationError):
            message = str(error)
        elif isinstance(error, ImportError) and error.name:
            message = f"{type(error).__name__}: {error.name} is missing from this interpreter"
        elif callable(getattr(error, "errors", None)):
            # A located path and code says which contract broke without echoing
            # the value, and a bare type name has now cost three debug rounds.
            located = "; ".join(
                ".".join(str(part) for part in issue.get("loc", ())) + ":" + str(issue.get("type", "unknown"))
                for issue in error.errors()[:5]
            )
            message = f"{type(error).__name__}: {located}"
        else:
            message = type(error).__name__
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
