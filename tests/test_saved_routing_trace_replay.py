"""Tests for strict, offline replay of captured routing responses."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from evaluate_routing import _fingerprint, _message_record  # noqa: E402
from saved_trace_replay import (  # noqa: E402
    ExactTraceReplayProvider,
    TraceReplayMismatch,
    _normalize_trace,
)


class SystemMessage:
    def __init__(self, content):
        self.content = content


class HumanMessage:
    def __init__(self, content):
        self.content = content


class SemanticInterpretation:
    @classmethod
    def model_json_schema(cls):
        return {"title": cls.__name__, "type": "object"}


def make_provider(messages):
    call = {
        "schema": SemanticInterpretation.__name__,
        "schema_sha256": _fingerprint(SemanticInterpretation.model_json_schema()),
        "messages": [_message_record(message) for message in messages],
        "parsed": {"request_mode": "guidance"},
        "raw_tool_calls": [{"name": "SemanticInterpretation", "args": {}}],
        "usage": {"input_tokens": 4, "output_tokens": 2},
    }
    trace = {
        "metadata": {"semantic_contract": "legacy"},
        "results": [{
            "id": "case-a",
            "trial": 1,
            "prompt": "hello",
            "calls": [call],
        }],
    }
    return ExactTraceReplayProvider(trace)


def test_saved_response_is_injected_only_for_exact_schema_and_messages():
    messages = [SystemMessage("system rules"), HumanMessage("hello")]
    provider = make_provider(messages)
    adapter = provider.with_structured_output(
        SemanticInterpretation,
        method="function_calling",
        include_raw=True,
    )

    replayed = adapter.invoke(messages)

    assert replayed["parsed"] == {"request_mode": "guidance"}
    status = provider.finalize()["case-a"]
    assert status["replay_status"] == "exact"
    assert status["matched_calls"] == 1


def test_saved_response_is_not_injected_when_messages_differ():
    provider = make_provider([
        SystemMessage("system rules"),
        HumanMessage("hello"),
    ])
    adapter = provider.with_structured_output(
        SemanticInterpretation,
        method="function_calling",
        include_raw=True,
    )

    with pytest.raises(TraceReplayMismatch):
        adapter.invoke([
            SystemMessage("changed system rules"),
            HumanMessage("hello"),
        ])

    status = provider.finalize()["case-a"]
    assert status["replay_status"] == "diverged"
    assert status["matched_calls"] == 0
    assert status["first_divergence"]["fields"] == ["messages"]


def test_saved_parse_error_is_preserved_for_raw_structured_responses():
    messages = [SystemMessage("system rules"), HumanMessage("hello")]
    trace = make_provider(messages).trace
    trace["results"][0]["calls"][0]["parsing_error"] = "recorded parse failure"
    provider = ExactTraceReplayProvider(trace)
    adapter = provider.with_structured_output(
        SemanticInterpretation,
        method="function_calling",
        include_raw=True,
    )

    replayed = adapter.invoke(messages)

    assert isinstance(replayed["parsing_error"], RuntimeError)
    assert str(replayed["parsing_error"]) == "recorded parse failure"


def test_legacy_nested_trace_is_normalized_without_losing_repeated_trials():
    trace = {
        "metadata": {
            "source": "live",
            "semantic_contract": "legacy",
            "prompt_schema_sha256": "historical-fingerprint",
            "repeat": 2,
        },
        "results": [
            {
                "id": "case-a",
                "trial": trial,
                "_trace": {
                    "prompt": "hello",
                    "calls": [{"schema": "SemanticInterpretation"}],
                    "decision": {"capability_match_status": "exact"},
                },
            }
            for trial in (1, 2)
        ],
    }

    normalized, trace_format = _normalize_trace(trace)

    assert trace_format == "nested_legacy_live_harness"
    assert [row["trial"] for row in normalized["results"]] == [1, 2]
    assert [row["prompt"] for row in normalized["results"]] == ["hello", "hello"]
    assert all(row["calls"] == [{"schema": "SemanticInterpretation"}]
               for row in normalized["results"])
