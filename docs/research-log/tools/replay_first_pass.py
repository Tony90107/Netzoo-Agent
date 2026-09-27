"""Replay every recorded first pass that failed the schema (Log 213).

Usage: python docs/research-log/tools/replay_first_pass.py

For each legacy traced trial whose first `SemanticInterpretation` call does
not validate, reports the recorded schema errors, the recorded ending, and --
under the current code -- whether the draft is salvaged, which second call it
leads to (strict evidence supply, patch or whole review) and the issues that
call is asked about. The second call is not answered: this shows the route,
not what a model would write.
"""
import collections
import copy
import hashlib
import json
import sys
from types import SimpleNamespace

from traces import ROOT, traced_rows

sys.path.insert(0, str(ROOT / "scripts"))

from pydantic import ValidationError  # noqa: E402

from workflow_registry import OUTPUT_CAPABILITIES  # noqa: E402
from netzoo_agent_core.contracts import LLMUsage  # noqa: E402
from netzoo_agent_core.contracts.outcomes import SemanticInterpretation  # noqa: E402
from netzoo_agent_core.graph.router_invocation import _invoke_semantic_interpreter  # noqa: E402
from netzoo_agent_core.llm import build_semantic_interpreter_prompt  # noqa: E402


class Stop(Exception):
    """Raised by the second-call stubs once the route is known."""


class Replay:
    def __init__(self, reply):
        self.reply = reply

    def invoke(self, _messages):
        return copy.deepcopy(self.reply)


class Route:
    def __init__(self, taken, name):
        self.taken, self.name = taken, name

    def invoke(self, _messages):
        self.taken.append(self.name)
        raise Stop(self.name)


class Supply:
    def __init__(self, taken):
        self.taken = taken

    def with_structured_output(self, schema, **_options):
        return Route(self.taken, f"strict supply {sorted(schema.model_fields)}")


class Recorder:
    def __init__(self):
        self.events = []

    def append(self, _run_id, event, _node, data):
        self.events.append((event, data))


def route(task: str, first: dict):
    taken, recorder = [], Recorder()
    context = SimpleNamespace(
        semantic_claims=False, semantic_interpreter=Replay(first),
        semantic_patcher=Route(taken, "patch"), semantic_reviewer=Route(taken, "whole review"),
        selection_condition_llm=Supply(taken), semantic_discriminator=None,
        semantic_prompt=build_semantic_interpreter_prompt(), semantic_model_name="offline",
        router_max_tokens=2000, task_token_budget=100000, price_catalog=None, recorder=recorder,
        review_policy="when_needed",
        project_policy=SimpleNamespace(workflows={
            name: SimpleNamespace(output_capability=capability) for name, capability in OUTPUT_CAPABILITIES.items()
        }),
    )
    _invoke_semantic_interpreter(context, {}, task, LLMUsage(budget_tokens=100000))
    events = dict(recorder.events)
    salvaged = events.get("routing.semantic_first_pass_salvaged", {}).get("dropped_evidence")
    retried = events.get("routing.semantic_interpretation_retried") or events.get("routing.semantic_interpretation_rejected") or {}
    return salvaged, taken[0] if taken else "none", retried.get("issues")


def main() -> None:
    routes = collections.Counter(); seen = set()
    for path, _index, row in traced_rows():
        trace = row["_trace"]
        calls = trace.get("calls") or []
        if not calls or calls[0].get("schema") != "SemanticInterpretation" or not calls[0].get("raw_tool_calls"):
            continue
        if calls[0].get("finish_reason") == "injected_recorded_first_pass":  # Log 214 replays these
            continue
        first = calls[0]["raw_tool_calls"][0]["args"]
        # Archived reports repeat some dated ones; count each recording once.
        key = hashlib.sha256(json.dumps([row["id"], first], sort_keys=True).encode()).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        try:
            SemanticInterpretation.model_validate(first)
            continue
        except ValidationError as error:
            recorded = sorted({(".".join(map(str, e["loc"][-2:])), e["type"]) for e in error.errors()})
        salvaged, taken, issues = route(trace["prompt"], first)
        routes[taken.split(" [")[0]] += 1
        print(f"{path.name} {row['id']}: ended {trace.get('reason_code')}")
        print(f"  recorded errors: {recorded}")
        print(f"  salvaged: {salvaged}")
        print(f"  second call: {taken}; issues: {issues}")
    print(f"distinct first passes: {len(seen)}; schema failures by current route: {dict(routes)}")


if __name__ == "__main__":
    main()
