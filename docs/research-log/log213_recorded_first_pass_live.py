"""Logs 213, 215 live check: recorded faulty first passes, answered live from the second call on.

Usage: python docs/research-log/log213_recorded_first_pass_live.py <repeat> <out.json> [log213|log215]

The recorded first passes of the chosen set -- log213 (default): the five whose
only schema faults were evidence entries; log215: the one with root-level
assumptions -- are injected verbatim as the first call; the second semantic
call and the intent call go to gpt-4o-mini. Rows carry `_trace` in the traced
harness format; the injected call is marked `finish_reason:
injected_recorded_first_pass`. Needs OPENROUTER_API_KEY in the environment.
"""
import copy
import json
import os
import sys
from pathlib import Path

RESEARCH = Path(__file__).resolve().parent
ROOT = RESEARCH.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(RESEARCH / "tools"))

import evaluate_routing as er  # noqa: E402
from langchain_core.messages import AIMessage  # noqa: E402
from netzoo_agent_core.contracts import DEFAULT_ROUTER_MAX_TOKENS  # noqa: E402
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402
from netzoo_agent_core.llm import build_llm, validate_router_model  # noqa: E402
from pydantic import ValidationError  # noqa: E402
from traces import load_report  # noqa: E402

# set -> (new case id, corpus case id, recording)
RECORDED = {"log213": (
    ("role-tf-ss-en-postfix", "role-tf-ss-en", "live-semantic-trace-2026-09-23-postfix-families32-legacy.json"),
    ("role-tf-ss-en-round3", "role-tf-ss-en", "live-semantic-trace-2026-09-23-round3-families32-legacy.json"),
    ("role-tf-ss-en-log198", "role-tf-ss-en", "live-semantic-trace-2026-09-27-log198-families32-legacy.json"),
    ("case5-en", "case5-en", "live-semantic-trace-2026-09-27-log196-blind-case5-case7-legacy.json"),
    ("t2-none", "t2-none", "archive/2026-09-26-session/trace_log174_live.json.gz"),
), "log215": (
    ("gran-mirna-unstated-control", "gran-mirna-unstated-control",
     "live-semantic-trace-2026-09-27-log208-strict-families32-legacy.json"),
)}
TRACE = {"current": None, "trials": []}


def recorded_first_pass(case_id: str, recording: str) -> tuple[str, dict]:
    for row in load_report(RESEARCH / recording)["results"]:
        calls = (row.get("_trace") or {}).get("calls") or []
        if row["id"] != case_id or not calls or calls[0].get("schema") != "SemanticInterpretation":
            continue
        args = calls[0]["raw_tool_calls"][0]["args"]
        try:
            SemanticInterpretation.model_validate(args)
        except ValidationError:
            return row["_trace"]["prompt"], args
    raise LookupError(f"no failing first pass for {case_id} in {recording}")


def scenarios(recorded) -> list:
    corpus = {case.id: case for case in er.load_scenarios(ROOT / "tests/routing_semantic_families.json")}
    corpus.update({case.id: case for case in er.load_scenarios(RESEARCH / "blind/blind_en.json")})
    cases, firsts = [], []
    for new_id, case_id, recording in recorded:
        prompt, first = recorded_first_pass(case_id, recording)
        base = corpus.get(case_id) or er.RoutingScenario(
            id=case_id, language="en", category="positive", prompt=prompt,
            expected={"status": "ambiguous", "actions": []},
        )
        assert base.prompt == prompt, new_id
        cases.append(base.model_copy(update={"id": new_id}))
        firsts.append(first)
    return cases, firsts


def _msg(message):
    return {"type": type(message).__name__, "content": str(message.content)}


class RecordingAdapter:
    def __init__(self, inner, schema_name):
        self.inner, self.schema_name = inner, schema_name

    def invoke(self, messages, *args, **kwargs):
        entry = {"schema": self.schema_name, "messages": [_msg(m) for m in messages]}
        try:
            out = self.inner.invoke(messages, *args, **kwargs)
        except Exception as exc:
            entry["exception"] = f"{type(exc).__name__}: {exc}"[:2000]
            TRACE["current"]["calls"].append(entry)
            raise
        if isinstance(out, dict):
            raw = out.get("raw")
            entry["raw_tool_calls"] = [dict(name=c.get("name"), args=c.get("args")) for c in (getattr(raw, "tool_calls", None) or [])]
            entry["raw_content"] = str(getattr(raw, "content", ""))[:2000]
            entry["finish_reason"] = (getattr(raw, "response_metadata", {}) or {}).get("finish_reason")
            entry["usage"] = getattr(raw, "usage_metadata", None)
            parsed = out.get("parsed")
            entry["parsed"] = parsed.model_dump(mode="json") if hasattr(parsed, "model_dump") else parsed
            error = out.get("parsing_error")
            entry["parsing_error"] = f"{type(error).__name__}: {error}"[:3000] if error else None
        else:
            entry["result"] = out.model_dump(mode="json") if hasattr(out, "model_dump") else str(out)
        TRACE["current"]["calls"].append(entry)
        return out


class InjectedFirstPass:
    """Answer the first call of trial n with the n-th recorded first pass."""

    def __init__(self, queue, prompts):
        self.queue, self.prompts = queue, prompts

    def invoke(self, messages, *args, **kwargs):
        index = len(TRACE["trials"]) - 1
        assert TRACE["current"]["prompt"] == self.prompts[index]
        raw = AIMessage(content="", tool_calls=[{"name": "SemanticInterpretation", "args": copy.deepcopy(self.queue[index]),
                                                 "id": f"injected-{index}"}],
                        response_metadata={"finish_reason": "injected_recorded_first_pass"})
        return {"raw": raw, "parsed": None, "parsing_error": None}


class Provider:
    def __init__(self, inner, queue, prompts):
        self.inner, self.first = inner, InjectedFirstPass(queue, prompts)

    def with_structured_output(self, schema, **options):
        adapter = self.first if schema is SemanticInterpretation else self.inner.with_structured_output(schema, **options)
        return RecordingAdapter(adapter, schema.__name__)

    def __getattr__(self, name):
        return getattr(self.inner, name)


class Rec(er._EventRecorder):
    def append(self, run_id, event_type, node, payload):
        super().append(run_id, event_type, node, payload)
        if TRACE["current"] is not None:
            TRACE["current"]["events"].append({"type": event_type, "payload": json.loads(json.dumps(payload, default=str, ensure_ascii=False))})


_invoke_router = er.invoke_router


def traced_invoke(context, state, prompt):
    TRACE["current"] = {"prompt": prompt, "calls": [], "events": []}
    TRACE["trials"].append(TRACE["current"])
    result = _invoke_router(context, state, prompt)
    TRACE["current"]["decision"] = result.decision.model_dump(mode="json")
    TRACE["current"]["reason_code"] = result.reason_code
    return result


def main():
    repeat, out = int(sys.argv[1]), Path(sys.argv[2])
    chosen = sys.argv[3] if len(sys.argv) > 3 else "log213"
    assert os.environ.get("OPENROUTER_API_KEY"), "missing provider credential in env"
    er._EventRecorder, er.invoke_router = Rec, traced_invoke
    cases, firsts = scenarios(RECORDED[chosen])
    queue = [first for first in firsts for _ in range(repeat)]
    prompts = [case.prompt for case in cases for _ in range(repeat)]
    model = validate_router_model("openai/gpt-4o-mini")
    provider = Provider(build_llm(model, 0.0, max_output_tokens=DEFAULT_ROUTER_MAX_TOKENS, timeout_seconds=60), queue, prompts)
    report = er.evaluate(cases, provider=provider, model_name=model, source="live", repeat=repeat,
                         semantic_contract="legacy", review_policy="when_needed")
    report["metadata"]["first_pass_source"] = f"recorded_raw_first_pass_injected ({chosen})"
    for row, trace in zip(report["results"], TRACE["trials"]):
        row["_trace"] = trace
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str))
    for row in report["results"]:
        trace = row["_trace"]
        second = trace["calls"][1] if len(trace["calls"]) > 1 else {}
        salvaged = [e["payload"] for e in trace["events"] if e["type"] == "routing.semantic_first_pass_salvaged"]
        print(row["id"], row["trial"], row["status"], row.get("matched_actions"), row.get("hypothesis_actions"),
              trace["reason_code"], "execute" if row.get("should_execute") else "",
              "| salvaged" if salvaged else "| not salvaged", "| second:", second.get("schema"),
              (second.get("usage") or {}).get("total_tokens"))
        print("   ", (row.get("next_step_text") or "")[:220].replace("\n", " "))
    print("DONE")


if __name__ == "__main__":
    main()
