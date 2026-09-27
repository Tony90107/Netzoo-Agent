"""Diagnostic capture: run evaluate_routing.evaluate with full provider I/O and event traces.

Records, per trial: every structured-output call (schema, messages, raw tool-call args,
parsed/parsing_error) and every recorder event payload. Never records credentials.
"""
import json, os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]  # the repository root, wherever it is checked out
sys.path.insert(0, str(ROOT / "scripts"))
import evaluate_routing as er
from netzoo_agent_core.llm import build_llm, validate_router_model
from netzoo_agent_core.contracts import DEFAULT_ROUTER_MAX_TOKENS

TRACE = {"current": None, "trials": []}

def _msg(m):
    return {"type": type(m).__name__, "content": str(m.content)}

class RecordingAdapter:
    def __init__(self, inner, schema_name):
        self.inner, self.schema_name = inner, schema_name
    def invoke(self, messages, *a, **k):
        entry = {"schema": self.schema_name, "messages": [_msg(m) for m in messages]}
        try:
            out = self.inner.invoke(messages, *a, **k)
        except Exception as exc:
            entry["exception"] = f"{type(exc).__name__}: {exc}"[:2000]
            TRACE["current"]["calls"].append(entry); raise
        if isinstance(out, dict):
            raw = out.get("raw")
            entry["raw_tool_calls"] = [dict(name=c.get("name"), args=c.get("args")) for c in (getattr(raw, "tool_calls", None) or [])]
            entry["raw_content"] = str(getattr(raw, "content", ""))[:2000]
            entry["finish_reason"] = (getattr(raw, "response_metadata", {}) or {}).get("finish_reason")
            entry["usage"] = getattr(raw, "usage_metadata", None)
            entry["invalid_tool_calls"] = [dict(name=c.get("name"), error=str(c.get("error"))[:300], args_len=len(str(c.get("args") or ""))) for c in (getattr(raw, "invalid_tool_calls", None) or [])]
            p = out.get("parsed")
            entry["parsed"] = p.model_dump(mode="json") if hasattr(p, "model_dump") else p
            pe = out.get("parsing_error")
            entry["parsing_error"] = f"{type(pe).__name__}: {pe}"[:3000] if pe else None
        else:
            entry["result"] = out.model_dump(mode="json") if hasattr(out, "model_dump") else str(out)
        TRACE["current"]["calls"].append(entry)
        return out

class RecordingProvider:
    def __init__(self, inner): self.inner = inner
    def with_structured_output(self, schema, **kw):
        return RecordingAdapter(self.inner.with_structured_output(schema, **kw), schema.__name__)
    def __getattr__(self, n): return getattr(self.inner, n)

class Rec(er._EventRecorder):
    def append(self, run_id, event_type, node, payload):
        super().append(run_id, event_type, node, payload)
        if TRACE["current"] is not None:
            TRACE["current"]["events"].append({"type": event_type, "payload": json.loads(json.dumps(payload, default=str, ensure_ascii=False))})
er._EventRecorder = Rec

_orig_invoke = er.invoke_router
def traced_invoke(context, state, prompt):
    TRACE["current"] = {"prompt": prompt, "calls": [], "events": []}
    TRACE["trials"].append(TRACE["current"])
    r = _orig_invoke(context, state, prompt)
    d = r.decision
    TRACE["current"]["decision"] = d.model_dump(mode="json")
    TRACE["current"]["reason_code"] = r.reason_code
    return r
er.invoke_router = traced_invoke

def main():
    contract, repeat, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    cases = er.load_scenarios(Path(sys.argv[4]) if len(sys.argv) > 4 else ROOT / "tests/routing_semantic_variants.json")
    ids = sys.argv[5].split(",") if len(sys.argv) > 5 and sys.argv[5] else None
    if ids: cases = [c for c in cases if c.id in ids]
    assert os.environ.get("OPENROUTER_API_KEY"), "missing provider credential in env"
    model = validate_router_model("openai/gpt-4o-mini")
    provider = RecordingProvider(build_llm(model, 0.0, max_output_tokens=DEFAULT_ROUTER_MAX_TOKENS, timeout_seconds=60))
    report = er.evaluate(cases, provider=provider, model_name=model, source="live", repeat=repeat,
                         semantic_contract=contract, review_policy="when_needed")
    for row, tr in zip(report["results"], TRACE["trials"]):
        row["_trace"] = tr
    Path(out).write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str))
    s = report["summary"]
    print(contract, "passed", s["passed"], "/", s["trials"], "route", s["route_pass_rate"], "sem", s["semantic_pass_rate"], "calls", s["provider_calls"], "ungrounded", s["ungrounded_evidence_shapes"])

main()
