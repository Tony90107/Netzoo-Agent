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
from netzoo_agent_core.contracts.outcomes import (
    SemanticDiscriminator, SemanticInterpretation, SemanticPatch, SemanticReview,
)
from netzoo_agent_core.contracts.semantic_claims import SemanticClaims, SemanticClaimRepair
from netzoo_agent_core.interpretation.claim_prompt import claim_messages
from netzoo_agent_core.graph.context import _GraphContext
from netzoo_agent_core.graph.prompts import build_graph_prompts
from netzoo_agent_core.graph.router_invocation import invoke_router
from netzoo_agent_core.graph.response import respond
from netzoo_agent_core.evaluation.guidance_surface import capture_progress, score_surface
from netzoo_agent_core.interpretation.semantic_goal import publish_routing_progress
from netzoo_agent_core.interpretation.request_integrity import granularity_left_open
from netzoo_agent_core.presentation import _trace
from netzoo_agent_core.llm import build_llm, build_semantic_reviewer_messages, validate_router_model
from netzoo_agent_core.policy import ProjectPolicyLoader
from netzoo_agent_core.pricing import PriceCatalog
from workflow_registry import ArtifactType, EntityType, Granularity, RecommendedAction
from routing_repair_replay import REPLAY_SUITES, RepairReplayProvider, suite_cases

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
    # The dimensions that actually distinguish the expected capability from the
    # others its coarse fields also fit. Without them the corpus states the
    # answer but not what a correct outcome must contain, so a trial where the
    # harness guessed among compatible candidates scored the same as one where
    # the model supplied the discriminator -- and one prompt scored 3/3 with two
    # of its trials naming no distinguishing tag at all.
    # Every prompt in the first twenty-seven asks which tool to use, so the
    # scorer simply required `guidance` of all of them and treated any
    # authorized action as a safety failure. That made the commonest real
    # request -- run this named tool on these files -- impossible to write down,
    # which is why the class went untested while the gate stayed green. The
    # default keeps every existing case scored exactly as before.
    request_mode: Literal["guidance", "execute"] = "guidance"
    required_discriminators: dict[str, list[str]] = Field(default_factory=dict)
    answer_required: list[str] = Field(default_factory=list)
    answer_forbidden: list[str] = Field(default_factory=list)
    require_clarification: bool = False

    @model_validator(mode="after")
    def consistent(self):
        if (self.status in {"exact", "fallback"}) != bool(self.actions):
            raise ValueError("Only exact or fallback expectations may select actions, and must select at least one.")
        permitted = {"regulator_types", "target_types", "selection_tags", "entity_types"}
        unknown = set(self.required_discriminators) - permitted
        if unknown:
            raise ValueError(f"Unknown discriminator dimensions: {sorted(unknown)}")
        if self.required_discriminators and not self.actions:
            raise ValueError("Discriminators only mean something beside an expected action.")
        if set(self.actions) & set(self.forbidden_actions):
            raise ValueError("Expected actions cannot also be forbidden.")
        if len(self.actions) != len(set(self.actions)):
            raise ValueError("Expected actions must be unique.")
        return self


class RoutingScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$")
    language: Literal["en", "zh", "mixed"]
    # `misspelling` and `terse` were added once it was clear the twenty original
    # prompts share two properties no real request has: every content word is
    # spelled correctly, and every one of them states which inputs the user
    # already holds. Neither condition was measured, so neither could fail.
    category: Literal[
        "positive", "negative", "history", "paraphrase", "misspelling", "terse",
    ]
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

    def __init__(self, trace_capture=None):
        self.events: list[dict] = []
        self.trace_capture = trace_capture

    def append(self, _run_id, event_type, _node, payload):
        event = {
            "type": event_type,
            "payload": _json_snapshot(payload),
        }
        self.events.append(event)
        if self.trace_capture is not None:
            self.trace_capture.record_event(event)


def _json_snapshot(value):
    """Copy provider/event data into JSON-safe values without retaining objects."""
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))


def _message_record(message) -> dict:
    content = str(getattr(message, "content", ""))
    result = {"type": type(message).__name__}
    if type(message).__name__ == "SystemMessage":
        result["content_sha256"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
    else:
        result["content"] = content
    return result


def _validation_error_record(error) -> dict:
    record = {"type": type(error).__name__}
    errors = getattr(error, "errors", None)
    if callable(errors):
        record["issues"] = [
            {
                "location": [str(part) for part in item.get("loc", ())],
                "type": str(item.get("type", "unknown")),
            }
            for item in errors()[:20]
        ]
    return record


class _TraceCapture:
    """Opt-in raw structured-call and routing-event capture for one evaluation."""

    def __init__(self):
        self.trials: list[dict] = []
        self.current: dict | None = None

    def begin_trial(self, case_id: str, trial: int, prompt: str) -> None:
        self.current = {
            "id": case_id,
            "trial": trial,
            "prompt": prompt,
            "calls": [],
            "events": [],
        }
        self.trials.append(self.current)

    def record_call(self, call: dict) -> None:
        if self.current is not None:
            self.current["calls"].append(call)

    def record_event(self, event: dict) -> None:
        if self.current is not None:
            self.current["events"].append(event)

    def finish_trial(self, decision, reason_code: str | None) -> None:
        if self.current is not None:
            self.current["decision"] = _json_snapshot(decision.model_dump(mode="json"))
            self.current["reason_code"] = reason_code
            self.current = None

    def document(self, metadata: dict) -> dict:
        return {
            "metadata": {
                **metadata,
                "capture": "raw_structured_provider_io_and_routing_events_v1",
                "credentials_recorded": False,
            },
            "results": self.trials,
        }


class _RecordingAdapter:
    """Capture a structured provider call while preserving its return value."""

    def __init__(self, inner, schema, trace_capture: _TraceCapture):
        self.inner = inner
        self.schema = schema
        self.trace_capture = trace_capture

    def invoke(self, messages, *args, **kwargs):
        entry = {
            "schema": self.schema.__name__,
            "schema_sha256": _fingerprint(self.schema.model_json_schema()),
            "messages": [_message_record(message) for message in messages],
        }
        try:
            output = self.inner.invoke(messages, *args, **kwargs)
        except Exception as error:
            # Provider exception text may contain request data; the type is enough
            # to locate this call without copying headers, credentials, or bodies.
            entry["exception"] = {"type": type(error).__name__}
            self.trace_capture.record_call(entry)
            raise

        if isinstance(output, dict):
            raw = output.get("raw")
            raw_calls = getattr(raw, "tool_calls", None) or []
            entry["raw_tool_calls"] = [
                {"name": item.get("name"), "args": _json_snapshot(item.get("args"))}
                for item in raw_calls
            ]
            entry["raw_content"] = str(getattr(raw, "content", ""))[:2000]
            entry["finish_reason"] = (
                (getattr(raw, "response_metadata", {}) or {}).get("finish_reason")
            )
            entry["usage"] = _json_snapshot(getattr(raw, "usage_metadata", None))
            entry["invalid_tool_calls"] = [
                {
                    "name": item.get("name"),
                    "error_type": type(item.get("error")).__name__,
                    "args_length": len(str(item.get("args") or "")),
                }
                for item in (getattr(raw, "invalid_tool_calls", None) or [])
            ]
            parsed = output.get("parsed")
            entry["parsed"] = _json_snapshot(
                parsed.model_dump(mode="json") if hasattr(parsed, "model_dump") else parsed
            )
            parse_error = output.get("parsing_error")
            entry["parsing_error"] = (
                _validation_error_record(parse_error) if parse_error else None
            )
        else:
            entry["result"] = _json_snapshot(
                output.model_dump(mode="json") if hasattr(output, "model_dump") else output
            )
        self.trace_capture.record_call(entry)
        return output


class _RecordingProvider:
    """Proxy structured-output adapters only when the user requests a trace."""

    def __init__(self, inner, trace_capture: _TraceCapture):
        self.inner = inner
        self.trace_capture = trace_capture

    def with_structured_output(self, schema, **kwargs):
        return _RecordingAdapter(
            self.inner.with_structured_output(schema, **kwargs),
            schema,
            self.trace_capture,
        )

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def __setattr__(self, name, value):
        if name in {"inner", "trace_capture"}:
            object.__setattr__(self, name, value)
        else:
            setattr(self.inner, name, value)


def _write_trace(path: Path, capture: _TraceCapture, metadata: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(capture.document(metadata), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


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


#: The two dimensions whose loss changes which capabilities remain candidates.
#: With both resolved, the mi-RNA sample-specific request has exactly one match;
#: with them `unknown`, the candidate set spreads to four. Fixed here so the
#: measured rate cannot quietly change its own denominator between rounds.
CORE_DIMENSIONS = ("operation", "artifact_type")


def _downgrade_events(events) -> list[dict]:
    return [
        event["payload"] for event in events
        if event["type"] == "routing.outcome_downgraded"
    ]


def _unknown_core(result: dict) -> list[dict]:
    """Why each core dimension of the accepted outcome carries no commitment.

    `never_stated` and `downgraded` are the two situations that reach the same
    `unknown`, and only the second is meaning the run had and dropped. A round
    that reports the bare rate cannot tell them apart, and three documents
    attributed one to the other on that basis.
    """
    outcome = result["outcome"]
    if not outcome:
        return []
    dropped = {
        item["dimension"]: item
        for payload in result["outcome_downgrades"] if payload["comparable"]
        for item in payload["downgrades"]
    }
    # No comparison was made at all -- either the run was accepted on its first
    # pass (nothing to compare against) or correspondence was undefined. Saying
    # "never stated" here would be asserting something unmeasured.
    comparable = any(payload["comparable"] for payload in result["outcome_downgrades"])
    accepted_first = not result["outcome_downgrades"]
    return [
        {
            "dimension": dimension,
            "origin": (
                "downgraded" if dimension in dropped
                else "never_stated" if comparable or accepted_first
                else "uncomparable"
            ),
            "first_pass_span": (dropped.get(dimension) or {}).get("first_pass_span"),
        }
        for dimension in CORE_DIMENSIONS
        if outcome.get(dimension) == "unknown"
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


def _review_patch_payload(event):
    payload = event["payload"]
    keys = (
        "changed_fields", "evidence_removed", "evidence_added",
        "evidence_retired_as_stale", "evidence_additions_dropped",
        "permitted_fields",
        "ignored_instructions", "repairs",
    )
    return {key: payload[key] for key in keys if key in payload}


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
    if (
        expected.require_clarification
        and granularity_left_open(case.prompt)
        and actual_outcome.get("granularity") != "unknown"
    ):
        semantic_errors.append(
            "clarification_consistency: requested_outcome.granularity must remain "
            f"unknown until the user answers, got {actual_outcome.get('granularity')}"
        )
    if expected.require_clarification and granularity_left_open(case.prompt):
        represented = {
            item.outcome.granularity for item in decision.outcome_hypotheses
        }
        missing = sorted(
            {"aggregate", "sample_specific"} - represented
        )
        if missing:
            semantic_errors.append(
                "clarification_consistency: outcome_hypotheses must represent "
                f"both undecided granularity alternatives; missing {missing}"
            )
    # The dimension that actually distinguishes the expected capability. Naming
    # the right tool while omitting it means the harness resolved the tie, not
    # the model: one prompt scored 3/3 with two trials naming no distinguishing
    # tag at all. Recorded separately so that credit is not given for it.
    for dimension, required in (expected.required_discriminators or {}).items():
        present = set(actual_outcome.get(dimension) or [])
        missing = sorted(set(required) - present)
        if missing:
            semantic_errors.append(
                f"discriminator: {dimension} must include {missing}, got {sorted(present)}"
            )
    request_mode = result.routing_state.get("semantic_goal", {}).get("request_mode")
    if request_mode != expected.request_mode:
        semantic_errors.append(
            f"request_mode: expected {expected.request_mode}, got {request_mode}"
        )

    safety_errors = []
    if expected.request_mode == "guidance":
        if decision.should_execute or decision.action != "no_tool":
            safety_errors.append("execution: a guidance case must never authorize an action")
    elif decision.action != "no_tool" and decision.action not in expected.actions:
        # An execute case is allowed to execute, and only the expected capability.
        # Running something else is the failure that matters here.
        safety_errors.append(
            f"execution: expected {expected.actions}, got {decision.action}"
        )
    roles = [call.role for call in result.usage.calls]
    # Legacy routing used three calls (interpreter, optional reviewer, intent).
    # The evidence-backed discriminator is a bounded fourth call used only for
    # a genuine registry tie; keep the cap explicit so it cannot become an
    # unbounded retry loop while still scoring the new contract fairly.
    if len(roles) > 4:
        safety_errors.append("call_limit: routing exceeded semantic/discriminator/intent bound")
    pipeline_errors = [] if result.reason_code == "semantic_registry_intent" else [
        f"pipeline: {result.reason_code}",
    ]
    errors = route_errors + semantic_errors + safety_errors + pipeline_errors
    # A recommendation of a capability the case does not expect, exact or not.
    # A wrong fallback still names a tool to the user; counting only wrong
    # exact matches missed three DRAGON recommendations in one traced round.
    wrong_recommendation = (
        decision.capability_match_status
        if decision.matched_actions
        and set(decision.matched_actions) != set(expected.actions)
        else None
    )
    repair_attempted = any(event["type"] == "routing.semantic_interpretation_rejected"
                           and event["payload"].get("attempt") == 1 for event in events)
    review_call_attempted = "semantic_reviewer" in roles
    review_attempt_reason = (
        "contract_repair" if repair_attempted
        else "semantic_completeness" if review_call_attempted
        else None
    )
    return {
        "review_repair_attempted": repair_attempted,
        "review_repair_validated": repair_attempted and accepted,
        "review_repair_correct": repair_attempted and not semantic_errors and not route_errors,
        "semantic_review_attempted": review_call_attempted,
        "semantic_review_validated": review_call_attempted and accepted,
        "semantic_review_correct": (
            review_call_attempted and not semantic_errors and not route_errors
        ),
        "semantic_review_reason": review_attempt_reason,
        "id": case.id, "language": case.language, "category": case.category,
        "passed": not errors, "route_passed": not route_errors,
        "semantic_passed": not semantic_errors, "errors": errors,
        # Kept apart from the merged list so the summary can count unsafe
        # trials instead of re-deriving them, and so a reader can see which
        # trial was unsafe rather than only how many were.
        "safety_errors": safety_errors,
        "path": "registry_recovery" if recovered else result.reason_code,
        "diagnostics": _diagnostics(events, result.reason_code),
        "diagnostic_details": _diagnostic_details(events),
        "evidence_census": _evidence_census(events),
        # What the accepted interpretation stopped committing to, relative to
        # the first pass, and what the first pass's own quote for that value did
        # (`absent`, `unmatched`, or nothing). An empty list beside
        # `comparable: false` means no comparison was possible, not no loss.
        "outcome_downgrades": _downgrade_events(events),
        # Declared in Log 62 and not built until Log 65: without it the only
        # authorized field write is invisible to the report, and "the model got
        # it right unaided" stops being measurable.
        "restored_fields": [
            dict(item, attempt=event["payload"].get("attempt"))
            for event in events
            if event["type"] == "routing.outcome_input_restored"
            for item in event["payload"].get("restored", [])
        ],
        "wrong_recommendation": wrong_recommendation,
        "status": decision.capability_match_status, "matched_actions": decision.matched_actions,
        # The candidates an ambiguous decision is holding. Without them a report
        # cannot tell "underdetermined, and here are the four it is between"
        # from "resolved nothing at all", and those need opposite responses.
        "hypothesis_actions": decision.hypothesis_actions,
        "clarification_question_asked": bool(decision.clarification_question),
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
            (_review_patch_payload(event)
             for event in events if event["type"] == "routing.semantic_patch_applied"),
            None,
        ),
        "total_tokens": result.usage.total_tokens,
        # Split as well as totalled: the two sides are priced differently and
        # by very different factors, so a cost comparison between models
        # cannot be made from the total alone.
        "input_tokens": result.usage.input_tokens,
        "output_tokens": result.usage.output_tokens,
    }


def _score_answer(case, result, context, progress=""):
    """Exercise the production final guidance node without extra provider calls.

    Unselected/general free-prose answers are outside this bounded evaluator;
    explicitly requiring an answer for such a case fails instead of fabricating a pass.
    """
    decision = result.decision
    # `ambiguous` is the commonest outcome by far -- 69 of 162 trials over two
    # rounds -- and all of it used to leave here unscored, so no report said
    # anything about what the user sees in the commonest case. That is how a
    # problem the answer layer had already solved stayed written down as unfixed
    # across several handoffs. Most of it is answered deterministically by
    # `render_outcome_clarification`, which costs no provider call, so it is
    # scored below; the remainder genuinely needs the response model and stays
    # outside this evaluator -- but it now says so instead of being folded into
    # one undifferentiated `false`.
    deterministic_ambiguity = (
        decision.capability_match_status == "ambiguous"
        and bool(decision.clarification_question)
    )
    if decision.action != "no_tool" or decision.should_execute or not (
        decision.capability_match_status in {"exact", "fallback"}
        and any(action in context.project_policy.workflows for action in decision.matched_actions)
        or decision.rejected_methods or decision.match_basis in {"semantic_validation_recovery", "provider_unavailable"}
        or deterministic_ambiguity
    ):
        return {"answer_evaluated": False, "answer_passed": None, "answer": "",
                "answer_scope": (
                    "response_model" if decision.capability_match_status == "ambiguous"
                    else "out_of_scope"
                ),
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
    # An ambiguous decision holding candidates has to name them. It already did,
    # for 56 of the 69 ambiguous trials in the two rounds that first looked --
    # and nothing recorded that, so neither the fix nor its loss would show.
    errors.extend(
        f"candidate_unnamed: {action}"
        for action in decision.hypothesis_actions
        if decision.capability_match_status == "ambiguous"
        and (spec := context.project_policy.workflows.get(action)) is not None
        and spec.workflow.casefold() not in answer.casefold()
    )
    return {"answer_evaluated": True, "answer_passed": not errors, "answer": answer,
            "answer_errors": errors, "answer_scope": "deterministic",
            **score_surface(decision, state, progress, answer)}


def evaluate(
    cases: list[RoutingScenario], *, provider, model_name: str,
    source: Literal["fixture", "live"] = "fixture", repeat: int = 1,
    task_token_budget: int = DEFAULT_TASK_TOKEN_BUDGET,
    semantic_contract: Literal["claims", "legacy"] = "legacy",
    review_policy: Literal["when_needed", "always"] | None = None,
    trace_capture: _TraceCapture | None = None,
) -> dict:
    if not cases or not 1 <= repeat <= 5:
        raise ValueError("Evaluation requires cases and 1-5 repetitions.")
    replay = isinstance(provider, RepairReplayProvider)
    # Each suite reconstructs a first pass for its own prompts. The role-evidence
    # class does not occur in the three mutation prompts at all -- SAMBAR has no
    # regulator or target -- so the permitted set is the suite's, not a fixed one.
    if replay and any(case.id not in suite_cases(provider.suite) for case in cases):
        raise ValueError("Repair replay supports only the prompts its suite reconstructs.")
    policy = ProjectPolicyLoader(PROJECT_ROOT).load()
    prompts = build_graph_prompts(policy)
    recorder = _EventRecorder(trace_capture)
    if trace_capture is not None:
        provider = _RecordingProvider(provider, trace_capture)
    # Historical fixtures/replay keep their recorded wire format. Live acceptance
    # always exercises the current production contract, unless explicitly replaying.
    review_policy = review_policy or ("when_needed" if source == "live" and not replay else "always")
    schemas = (SemanticClaims, SemanticClaims, SemanticClaimRepair) if semantic_contract == "claims" else (SemanticInterpretation, SemanticReview, SemanticPatch)
    claim_output_options = {"strict": True} if semantic_contract == "claims" else {}
    semantic_interpreter = provider.with_structured_output(
        schemas[0], method="function_calling", include_raw=True,
        **claim_output_options,
    )
    semantic_reviewer = provider.with_structured_output(
        schemas[1], method="function_calling", include_raw=True,
        **claim_output_options,
    )
    semantic_patcher = provider.with_structured_output(
        schemas[2], method="function_calling", include_raw=True,
        **claim_output_options,
    )
    semantic_discriminator = (
        provider.with_structured_output(
            SemanticDiscriminator, method="function_calling", include_raw=True,
        ) if semantic_contract == "legacy" else None
    )
    intent_router = provider.with_structured_output(
        IntentDecision, method="function_calling", include_raw=False,
    )
    context = _GraphContext(
        profile_id="routing-evaluation", profile_store=None, episode_store=None,
        project_policy=policy, recorder=recorder, price_catalog=PriceCatalog.from_environment(),
        semantic_interpreter=semantic_interpreter,
        semantic_reviewer=semantic_reviewer,
        semantic_patcher=semantic_patcher,
        semantic_discriminator=semantic_discriminator,
        selection_condition_llm=provider if semantic_contract == "legacy" else None,
        intent_router=intent_router,
        input_content_mapper=None, response_llm=None,
        semantic_claims=semantic_contract == "claims",
        review_policy=review_policy,
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
            if trace_capture is not None:
                trace_capture.begin_trial(case.id, trial, case.prompt)
            # The answer key is deliberately never sent to the runtime or provider.
            with capture_progress() as progress:
                _trace("intent", "Interpreting the request and capability boundaries")
                result = invoke_router(context, {}, case.prompt)
                publish_routing_progress(result.decision, result.routing_state["semantic_goal"], policy, case.prompt)
                row = {**_score(case, result, recorder.events),
                       **_score_answer(case, result, context, progress), "trial": trial}
            if trace_capture is not None:
                trace_capture.finish_trial(result.decision, result.reason_code)
            row["unknown_core"] = _unknown_core(row)
            row["errors"].extend(row["answer_errors"])
            row["errors"].extend(row.get("interaction_errors", []))
            row["passed"] = not row["errors"]
            row["provider_calls"] = len(result.usage.calls) - (1 if replay and result.usage.calls else 0)
            row["injected_proposal"] = replay
            results.append(row)
    total = len(results)
    repair_trials = sum(item["review_repair_attempted"] for item in results)
    semantic_review_trials = sum(item["semantic_review_attempted"] for item in results)
    prompt_hash_by_id = {case.id: _fingerprint(case.prompt) for case in cases}
    prompt_passes: dict[str, list[bool]] = {}
    for item in results:
        prompt_passes.setdefault(prompt_hash_by_id[item["id"]], []).append(item["passed"])
    return {
        "metadata": {
            "source": source, "model": model_name, "temperature": 0.0,
            "semantic_contract": semantic_contract, "review_policy": review_policy,
            "first_pass_source": "observed_error_reconstruction_not_raw_capture" if replay else source,
            "repair_replay_suite": provider.suite if replay else None,
            "policy_hash": policy.policy_hash, "repeat": repeat,
            "corpus_sha256": _fingerprint([case.model_dump() for case in cases]),
            "prompt_schema_sha256": _fingerprint({
                "semantic": prompts.semantic, "intent": prompts.intent,
                "reviewer": [str(message.content) for message in build_semantic_reviewer_messages(
                    prompts.semantic, "<evaluation prompt>", None, (),
                )],
                "schemas": [schema.model_json_schema() for schema in (*schemas, SemanticDiscriminator, IntentDecision)] if semantic_contract == "legacy" else [schema.model_json_schema() for schema in (*schemas, IntentDecision)],
                "claim_messages": [str(m.content) for m in claim_messages("<evaluation prompt>", selection_tags={t for spec in policy.workflows.values() for t in spec.output_capability.selection_tags})] if semantic_contract == "claims" else None,
            }),
            "scope": "routing_progress_verified_guidance_next_step_no_planner_executor_or_response_model",
            "execution_evaluated": False,
            "biological_output_evaluated": False,
        },
        "summary": {
            "cases": len(cases), "trials": total,
            "unique_prompts": len(prompt_passes),
            "repeat_count": repeat,
            "prompts_passed_every_repeat": sum(
                all(passes) for passes in prompt_passes.values()
            ),
            "prompt_repeat_disagreements": sum(
                len(set(passes)) > 1 for passes in prompt_passes.values()
            ),
            "statistical_unit": (
                "unique prompt; repeats are within-prompt stability checks, "
                "not independent cases"
            ),
            "passed": sum(item["passed"] for item in results),
            "pass_rate": sum(item["passed"] for item in results) / total,
            "route_pass_rate": sum(item["route_passed"] for item in results) / total,
            "semantic_pass_rate": sum(item["semantic_passed"] for item in results) / total,
            "answer_evaluated_count": sum(item["answer_evaluated"] for item in results),
            "answer_failure_count": sum(bool(item["answer_errors"]) for item in results),
            "interaction_failure_count": sum(bool(item.get("interaction_errors")) for item in results),
            "review_repair_attempts": repair_trials,
            # Review calls include both validation repair and semantic
            # completeness checks. Keep this denominator separate from the
            # historical repair metric, which counts only rejected first passes.
            "semantic_review_attempts": semantic_review_trials,
            "semantic_review_reasons": dict(Counter(
                item["semantic_review_reason"] for item in results
                if item["semantic_review_reason"] is not None
            )),
            "semantic_review_validation_rate": (
                sum(item["semantic_review_validated"] for item in results)
                / semantic_review_trials if semantic_review_trials else None
            ),
            "semantic_review_success_rate": (
                sum(item["semantic_review_correct"] for item in results)
                / semantic_review_trials if semantic_review_trials else None
            ),
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
            # Acting is not the same as acting unsafely. This counted every
            # trial that selected a capability, which is correct only while the
            # corpus holds guidance cases alone; once it gained an execute case
            # whose expected result is a named action, the metric reported that
            # correct behavior as an unsafe execution. The per-trial check
            # already distinguishes the two, so defer to it.
            "unsafe_execution_count": sum(bool(item["safety_errors"]) for item in results),
            "wrong_exact_recommendations": sum(
                item["wrong_recommendation"] == "exact" for item in results
            ),
            "wrong_fallback_recommendations": sum(
                item["wrong_recommendation"] not in {None, "exact"} for item in results
            ),
            "executing_trial_count": sum(
                item["should_execute"] or item["action"] != "no_tool" for item in results
            ),
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
            # Every commitment an accepted interpretation stopped carrying,
            # keyed by dimension, where it landed, and what the first pass's own
            # quote for that value did. `grounded` in the third position means
            # the value was never reported ungrounded at all -- so a drop there
            # cannot be blamed on the citation contract.
            "outcome_downgrades": dict(Counter(
                f"{drop['dimension']}:{drop['to_value']}:"
                f"{drop['first_pass_span'] or 'grounded'}"
                for item in results for payload in item["outcome_downgrades"]
                for drop in payload["downgrades"]
            )),
            "trials_with_outcome_downgrade": sum(
                1 for item in results
                if any(payload["downgrades"] for payload in item["outcome_downgrades"])
            ),
            # Why the first pass and the accepted interpretation could not be
            # compared, when they could not. Reported rather than folded into
            # the zero above: "no comparison" and "no loss" are different facts,
            # and merging them is the error this instrument exists to expose.
            "downgrade_not_comparable": dict(Counter(
                str(payload["reason"]) for item in results
                for payload in item["outcome_downgrades"] if not payload["comparable"]
            )),
            # The 8-12% rate, split by which of the two situations produced it.
            # The bare rate was measured on three archived rounds and attributed
            # to a citation failure none of those trials had.
            "unknown_core_origin": dict(Counter(
                f"{entry['dimension']}:{entry['origin']}:"
                f"{entry['first_pass_span'] or 'grounded'}"
                for item in results for entry in item["unknown_core"]
            )),
            "trials_with_unknown_core": sum(
                1 for item in results if item["unknown_core"]
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
    parser.add_argument("--repair-replay-suite", choices=tuple(REPLAY_SUITES),
                        help="Observed failure batch; requires --repair-replay (default: cross-field).")
    parser.add_argument("--model", default=DEFAULT_ROUTER_MODEL)
    parser.add_argument("--semantic-contract", choices=("legacy", "claims"), default="legacy", help="Claims is experimental; legacy preserves the current provider schema.")
    parser.add_argument("--review-policy", choices=("when_needed", "always"), default="when_needed", help="Controlled comparison of review gating with the same schema.")
    parser.add_argument("--repeat", type=int, choices=range(1, 6), default=1)
    parser.add_argument("--max-calls", type=int, default=12, help="Reject runs whose worst-case call count exceeds this cap.")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--trace-out",
        type=Path,
        help=(
            "Save structured provider calls and routing events to this JSON path. "
            "Requires --live; credentials and system prompt text are not recorded."
        ),
    )
    args = parser.parse_args(argv)
    trace_capture = _TraceCapture() if args.trace_out is not None else None
    trace_metadata = {
        "source": "live",
        "model": args.model,
        "semantic_contract": args.semantic_contract,
        "review_policy": args.review_policy,
    }
    try:
        if args.trace_out is not None and not args.live:
            raise _ConfigurationError("--trace-out requires --live.")
        if args.repair_replay_suite and not args.repair_replay:
            raise _ConfigurationError("--repair-replay-suite requires --repair-replay.")
        cases = load_scenarios(args.scenarios)
        unknown = set(args.case) - {case.id for case in cases}
        if unknown:
            raise _ConfigurationError(f"Unknown case IDs: {sorted(unknown)}")
        if args.case:
            cases = [case for case in cases if case.id in args.case]
        if args.repair_replay:
            permitted = suite_cases(args.repair_replay_suite or "cross-field")
            if args.case and any(case.id not in permitted for case in cases):
                raise _ConfigurationError(
                    f"Repair replay suite reconstructs only: {', '.join(sorted(permitted))}."
                )
            cases = [case for case in cases if case.id in permitted]
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
            report = evaluate(cases, provider=provider, model_name=model, source="live", repeat=args.repeat,
                              semantic_contract=args.semantic_contract, review_policy=args.review_policy,
                              trace_capture=trace_capture)
            if args.trace_out is not None:
                report["metadata"]["trace_out"] = str(args.trace_out)
                _write_trace(args.trace_out, trace_capture, report["metadata"])
    except (ValueError, OSError, ImportError) as error:
        if args.trace_out is not None and trace_capture is not None and trace_capture.trials:
            try:
                _write_trace(args.trace_out, trace_capture, trace_metadata)
            except OSError:
                pass
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
        if args.trace_out is not None:
            print(f"Trace saved: {args.trace_out}")
    return 0 if not args.live or report["summary"]["passed"] == report["summary"]["trials"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
