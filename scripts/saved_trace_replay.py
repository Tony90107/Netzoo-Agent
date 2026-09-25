"""Strict replay of captured routing provider responses, with coverage accounting."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import evaluate_routing as evaluator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCENARIOS = PROJECT_ROOT / "tests" / "routing_semantic_families.json"


class TraceReplayMismatch(RuntimeError):
    """The current router call is not identical to the captured provider call."""


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _message_signature(message) -> dict[str, str]:
    content = str(getattr(message, "content", ""))
    return {
        "type": type(message).__name__,
        "content_sha256": _content_hash(content),
    }


def _saved_message_signature(message: dict) -> dict[str, str]:
    content_hash = message.get("content_sha256")
    if content_hash is None:
        content_hash = _content_hash(str(message.get("content", "")))
    return {"type": str(message.get("type", "")), "content_sha256": content_hash}


def _current_prompt_schema_hash(contract: str) -> str:
    """Reproduce evaluate_routing's global prompt/schema fingerprint."""
    policy = evaluator.ProjectPolicyLoader(PROJECT_ROOT).load()
    prompts = evaluator.build_graph_prompts(policy)
    schemas = (
        (evaluator.SemanticClaims, evaluator.SemanticClaims,
         evaluator.SemanticClaimRepair)
        if contract == "claims"
        else (evaluator.SemanticInterpretation, evaluator.SemanticReview,
              evaluator.SemanticPatch)
    )
    return evaluator._fingerprint({
        "semantic": prompts.semantic,
        "intent": prompts.intent,
        "reviewer": [
            str(message.content)
            for message in evaluator.build_semantic_reviewer_messages(
                prompts.semantic, "<evaluation prompt>", None, (),
            )
        ],
        "schemas": [
            schema.model_json_schema()
            for schema in (
                (*schemas, evaluator.SemanticDiscriminator, evaluator.IntentDecision)
                if contract == "legacy"
                else (*schemas, evaluator.IntentDecision)
            )
        ],
        "claim_messages": (
            [
                str(message.content)
                for message in evaluator.claim_messages(
                    "<evaluation prompt>",
                    selection_tags={
                        tag
                        for spec in policy.workflows.values()
                        for tag in spec.output_capability.selection_tags
                    },
                )
            ]
            if contract == "claims" else None
        ),
    })


def _normalize_trace(trace: dict) -> tuple[dict, str]:
    """Normalize the current raw trace format and the earlier nested harness format."""
    metadata = trace.get("metadata") or {}
    if metadata.get("capture") == "raw_structured_provider_io_and_routing_events_v1":
        if metadata.get("credentials_recorded") is not False:
            raise ValueError("Trace credentials must be explicitly absent.")
        return trace, "raw_structured_provider_io_and_routing_events_v1"

    # The Sep 23 harness wrote each provider call under result["_trace"], while
    # the evaluator summary lived beside it. It redacted system-message bodies
    # to hashes and stored a global prompt/schema fingerprint instead of a
    # per-call schema fingerprint.
    if (
        metadata.get("semantic_contract") == "legacy"
        and metadata.get("source") == "live"
        and metadata.get("prompt_schema_sha256")
        and trace.get("results")
        and all(isinstance(row.get("_trace"), dict) for row in trace["results"])
    ):
        normalized = deepcopy(trace)
        for row in normalized["results"]:
            recorded = row["_trace"]
            row["prompt"] = recorded.get("prompt")
            row["calls"] = recorded.get("calls") or []
            row["decision"] = recorded.get("decision") or {}
        return normalized, "nested_legacy_live_harness"

    raise ValueError("Trace format is not supported for deterministic saved-response replay.")


class ExactTraceReplayProvider:
    """Inject a captured response only when schema and every message match."""

    def __init__(self, trace: dict):
        self.trace = trace
        self._cases_by_prompt: dict[str, dict] = {}
        self._status: dict[str, dict] = {}
        self._blocked: set[str] = set()
        for trial in trace["results"]:
            prompt = trial["prompt"]
            case_id = trial["id"]
            if prompt in self._cases_by_prompt:
                raise ValueError("Trace replay requires unique prompts per trial.")
            self._cases_by_prompt[prompt] = trial
            self._status[case_id] = {
                "expected_calls": len(trial.get("calls", [])),
                "matched_calls": 0,
                "first_divergence": None,
            }

    def with_structured_output(self, schema, **kwargs):
        replay = self
        include_raw = bool(kwargs.get("include_raw", False))

        class Adapter:
            def invoke(self, messages, *_args, **_kwargs):
                return replay._invoke(schema, include_raw, messages)

        return Adapter()

    def _case_for_messages(self, messages) -> dict | None:
        prompts = {
            str(getattr(message, "content", ""))
            for message in messages
            if type(message).__name__ == "HumanMessage"
        }
        return next(
            (trial for prompt, trial in self._cases_by_prompt.items() if prompt in prompts),
            None,
        )

    def _diverge(self, trial: dict | None, schema_name: str, fields: list[str],
                 expected: dict | None, actual: dict) -> None:
        if trial is None:
            raise TraceReplayMismatch("No captured trial matches this user prompt.")
        case_id = trial["id"]
        status = self._status[case_id]
        if status["first_divergence"] is None:
            status["first_divergence"] = {
                "call_index": status["matched_calls"],
                "fields": fields,
                "expected_schema": expected.get("schema") if expected else None,
                "actual_schema": schema_name,
                "expected_schema_sha256": (
                    expected.get("schema_sha256") if expected else None
                ),
                "actual_schema_sha256": actual.get("schema_sha256"),
                "expected_messages": [
                    _saved_message_signature(item)
                    for item in (expected or {}).get("messages", [])
                ],
                "actual_messages": actual.get("messages", []),
            }
        self._blocked.add(case_id)
        raise TraceReplayMismatch(
            f"Saved trace diverged at {case_id} call {status['matched_calls']}."
        )

    def _invoke(self, schema, include_raw: bool, messages):
        trial = self._case_for_messages(messages)
        if trial is None:
            self._diverge(None, schema.__name__, ["prompt"], None, {})
        case_id = trial["id"]
        status = self._status[case_id]
        if case_id in self._blocked:
            raise TraceReplayMismatch(f"Saved trace replay stopped for {case_id}.")

        calls = trial.get("calls", [])
        call_index = status["matched_calls"]
        actual = {
            "schema_sha256": evaluator._fingerprint(schema.model_json_schema()),
            "messages": [_message_signature(message) for message in messages],
        }
        if call_index >= len(calls):
            self._diverge(trial, schema.__name__, ["unexpected_call"], None, actual)
        expected = calls[call_index]
        fields = []
        if expected.get("schema") != schema.__name__:
            fields.append("schema")
        if (
            "schema_sha256" in expected
            and expected.get("schema_sha256") != actual["schema_sha256"]
        ):
            fields.append("schema_sha256")
        expected_messages = [
            _saved_message_signature(item) for item in expected.get("messages", [])
        ]
        if expected_messages != actual["messages"]:
            fields.append("messages")
        has_raw_capture = "parsed" in expected or "raw_tool_calls" in expected
        if include_raw != has_raw_capture:
            fields.append("include_raw")
        if expected.get("exception"):
            fields.append("captured_exception")
        if include_raw and "parsed" not in expected:
            fields.append("response_shape")
        if not include_raw and "result" not in expected:
            fields.append("response_shape")
        if fields:
            self._diverge(trial, schema.__name__, fields, expected, actual)

        try:
            response = self._saved_response(schema, include_raw, expected)
        except Exception:
            self._diverge(trial, schema.__name__, ["response_shape"], expected, actual)
        status["matched_calls"] += 1
        return response

    @staticmethod
    def _saved_response(schema, include_raw: bool, call: dict):
        if not include_raw:
            if "result" not in call:
                raise TraceReplayMismatch(
                    "Captured call has no parsed result for a non-raw adapter."
                )
            return schema.model_validate(deepcopy(call["result"]))
        if "parsed" not in call:
            raise TraceReplayMismatch(
                "Captured call has no parsed field for a raw adapter."
            )
        raw = SimpleNamespace(
            tool_calls=deepcopy(call.get("raw_tool_calls", [])),
            content=call.get("raw_content", ""),
            response_metadata={"finish_reason": call.get("finish_reason")},
            usage_metadata=deepcopy(call.get("usage") or {}),
            invalid_tool_calls=deepcopy(call.get("invalid_tool_calls", [])),
        )
        parsing_error = call.get("parsing_error")
        return {
            "parsed": deepcopy(call.get("parsed")),
            "raw": raw,
            "parsing_error": RuntimeError(str(parsing_error)) if parsing_error else None,
        }

    def finalize(self) -> dict[str, dict]:
        result = deepcopy(self._status)
        for case_id, status in result.items():
            if status["first_divergence"] is not None:
                status["replay_status"] = "diverged"
            elif status["matched_calls"] == status["expected_calls"]:
                status["replay_status"] = "exact"
            else:
                status["replay_status"] = "incomplete"
                status["missing_calls"] = (
                    status["expected_calls"] - status["matched_calls"]
                )
        return result


def _decision_summary(decision: dict) -> dict:
    outcome = decision.get("requested_outcome") or {}
    return {
        "status": decision.get("capability_match_status"),
        "matched_actions": decision.get("matched_actions", []),
        "hypothesis_actions": decision.get("hypothesis_actions", []),
        "granularity": outcome.get("granularity"),
        "clarification_question_asked": bool(
            decision.get("clarification_question")
        ),
    }


def replay_trace(trace_path: Path, scenarios_path: Path = DEFAULT_SCENARIOS) -> dict:
    raw_trace = json.loads(trace_path.read_text(encoding="utf-8"))
    trace, trace_format = _normalize_trace(raw_trace)
    metadata = trace.get("metadata") or {}
    contract = metadata.get("semantic_contract")
    if contract not in {"legacy", "claims"}:
        raise ValueError("Trace must identify the legacy or claims contract.")
    if trace_format == "nested_legacy_live_harness":
        current_schema_hash = _current_prompt_schema_hash(contract)
        if metadata.get("prompt_schema_sha256") != current_schema_hash:
            raise ValueError(
                "Legacy trace has no per-call schema hashes and its global "
                "prompt/schema fingerprint differs from current source."
            )

    scenarios = evaluator.load_scenarios(scenarios_path)
    scenarios_by_id = {item.id: item for item in scenarios}
    saved_trials = trace.get("results") or []
    if not saved_trials:
        raise ValueError("Trace must contain at least one saved trial.")
    trial_keys = [(item.get("id"), item.get("trial")) for item in saved_trials]
    if len(set(trial_keys)) != len(trial_keys):
        raise ValueError("Trace contains duplicate case/trial pairs.")
    unknown = sorted({item.get("id") for item in saved_trials} - set(scenarios_by_id))
    if unknown:
        raise ValueError(f"Trace cases are missing from the current corpus: {unknown}.")
    saved_case_ids = list(dict.fromkeys(item["id"] for item in saved_trials))
    cases = [scenarios_by_id[case_id] for case_id in saved_case_ids]
    expected_repeats = metadata.get("repeat", 1)
    counts_by_id: dict[str, list[int]] = {}
    for saved in saved_trials:
        counts_by_id.setdefault(saved["id"], []).append(saved.get("trial"))
        case = scenarios_by_id[saved["id"]]
        if saved.get("prompt") != case.prompt:
            raise ValueError(f"Prompt changed for saved case {case.id}.")
    for case_id, trials in counts_by_id.items():
        if sorted(trials) != list(range(1, expected_repeats + 1)):
            raise ValueError(
                f"Saved trials for {case_id} do not match declared repeat count "
                f"{expected_repeats}."
            )

    current_corpus_hash = evaluator._fingerprint(
        [case.model_dump() for case in cases]
    )
    reports_by_trial = {}
    replay_status = {}
    current_metadata = None
    for saved in saved_trials:
        case = scenarios_by_id[saved["id"]]
        one_trial_trace = {"results": [saved]}
        provider = ExactTraceReplayProvider(one_trial_trace)
        report = evaluator.evaluate(
            [case],
            provider=provider,
            model_name=metadata.get("model") or "saved-trace",
            source="fixture",
            repeat=1,
            semantic_contract=contract,
            review_policy=metadata.get("review_policy", "when_needed"),
        )
        key = (saved["id"], saved["trial"])
        reports_by_trial[key] = report["results"][0]
        replay_status[key] = provider.finalize()[saved["id"]]
        if current_metadata is None:
            current_metadata = report["metadata"]
        elif (
            current_metadata["policy_hash"] != report["metadata"]["policy_hash"]
            or current_metadata["prompt_schema_sha256"]
            != report["metadata"]["prompt_schema_sha256"]
        ):
            raise RuntimeError("Routing policy or prompt/schema changed during replay.")

    results = []
    for saved in saved_trials:
        case_id = saved["id"]
        key = (case_id, saved["trial"])
        status = replay_status[key]
        scored = reports_by_trial[key]
        exact = status["replay_status"] == "exact"
        results.append({
            "id": case_id,
            "trial": saved["trial"],
            **status,
            "score_eligible": exact,
            "score": ({
                "passed": scored["passed"],
                "route_passed": scored["route_passed"],
                "semantic_passed": scored["semantic_passed"],
                "errors": scored["errors"],
            } if exact else None),
            "recorded_decision": _decision_summary(saved.get("decision", {})),
            "current_replay_decision": ({
                "status": scored["status"],
                "matched_actions": scored["matched_actions"],
                "granularity": (scored.get("outcome") or {}).get("granularity"),
                "clarification_question_asked": scored[
                    "clarification_question_asked"
                ],
            } if exact else None),
        })

    exact_results = [item for item in results if item["score_eligible"]]
    assert current_metadata is not None
    historical_hashes = {
        "corpus_sha256": metadata.get("corpus_sha256"),
        "policy_hash": metadata.get("policy_hash"),
        "prompt_schema_sha256": metadata.get("prompt_schema_sha256"),
    }
    current_hashes = {
        "corpus_sha256": current_corpus_hash,
        "policy_hash": current_metadata.get("policy_hash"),
        "prompt_schema_sha256": current_metadata.get("prompt_schema_sha256"),
    }
    total_saved_calls = sum(len(item.get("calls", [])) for item in saved_trials)
    calls_matched = sum(item["matched_calls"] for item in replay_status.values())
    result_by_id: dict[str, list[dict]] = {}
    for item in results:
        result_by_id.setdefault(item["id"], []).append(item)
    complete_prompt_groups = [
        group for group in result_by_id.values()
        if all(item["replay_status"] == "exact" for item in group)
    ]
    return {
        "mode": "saved_live_provider_response_replay",
        "trace_format": trace_format,
        "trace": str(trace_path),
        "scenarios": str(scenarios_path),
        "semantic_contract": contract,
        "historical_model": metadata.get("model"),
        "review_policy": metadata.get("review_policy"),
        "new_provider_calls": 0,
        "new_provider_cost_usd": 0,
        "hashes": {
            "historical": historical_hashes,
            "current": current_hashes,
            "matches": {
                key: historical_hashes[key] == current_hashes[key]
                for key in historical_hashes
            },
        },
        "summary": {
            "trials": len(results),
            "unique_prompts": len(result_by_id),
            "exact_full_call_sequences": len(exact_results),
            "diverged_sequences": sum(
                item["replay_status"] == "diverged" for item in results
            ),
            "incomplete_sequences": sum(
                item["replay_status"] == "incomplete" for item in results
            ),
            "score_eligible_trials": len(exact_results),
            "score_eligible_passes": sum(
                item["score"]["passed"] for item in exact_results
            ),
            "score_eligible_failures": sum(
                not item["score"]["passed"] for item in exact_results
            ),
            "captured_calls": total_saved_calls,
            "exactly_replayed_calls": calls_matched,
            "prompt_groups_with_all_repeats_exact": len(complete_prompt_groups),
            "prompt_groups_with_replay_disagreement": sum(
                len({item["score"]["passed"] for item in group}) > 1
                for group in complete_prompt_groups
            ),
            "statistical_unit": (
                "unique prompt; captured repeats are historical model responses, "
                "not fresh live stability trials"
            ),
        },
        "results": results,
        "limitations": [
            "Only identical schema, schema hash, and full message sequences receive captured responses.",
            "Diverged or incomplete trials are excluded from routing and semantic pass denominators.",
            "A replay tests current deterministic routing with historical model responses; it is not a new model trial.",
            "A current/historical policy hash mismatch means route differences may reflect policy drift.",
            "The nested legacy harness format has no per-call schema hashes; it is accepted only when its global prompt/schema fingerprint matches current source.",
            "Pass rates are conditional on exact full-call sequences and must not be extrapolated to uncovered trials.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = replay_trace(args.trace, args.scenarios)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
