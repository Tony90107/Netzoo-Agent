"""Offline replay of the operation-authorization change over recorded requests.

No model, search or analysis is called. Run from the repository root:

    python docs/diagnostics/2026-10-05-operation-authorization/replay.py [--base DIR]

1. Prompts: every recorded user request (tests/routing_scenarios.json, prompt
   fields under docs/research-log, .netzoo/sessions user messages).
2. Helpers (needs --base, a checkout of the tree before the change): how the
   deterministic promotion helpers change on those prompts.
3. Gate: every recorded executing decision (sessions, live corpus rounds,
   traced rows) that the current gate would now refuse.
"""
import argparse, glob, gzip, json, subprocess, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HELPERS = ("has_explicit_execution_request", "has_direct_execution_intent",
           "has_direct_retrieval_request", "is_input_preflight_request")


def prompts() -> list[str]:
    found: dict[str, None] = {}

    def add(text):
        if isinstance(text, str) and text.strip() and len(text) < 20000:
            found.setdefault(text, None)

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                add(value) if key in ("prompt", "task", "user_task") and isinstance(value, str) else walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    for item in json.loads((ROOT / "tests/routing_scenarios.json").read_text()):
        add(item.get("prompt"))
    for path in glob.glob(str(ROOT / "docs/research-log/**/*.json"), recursive=True):
        try:
            walk(json.loads(Path(path).read_text()))
        except Exception:
            pass
    for path in glob.glob(str(ROOT / ".netzoo/sessions/*.json")):
        try:
            data = json.loads(Path(path).read_text())
        except ValueError:
            continue
        for message in data.get("messages", []):
            if message.get("type") in ("human", "HumanMessage") or message.get("role") == "user":
                add(str(message.get("content")))
    return list(found)


_HELPER_SCRIPT = """
import json, sys
sys.path[:0] = [sys.argv[1] + "/scripts"]
from netzoo_agent_core.routing import capability as c
rows = {}
for t in json.load(sys.stdin):
    rows[t] = [getattr(c, name)(t) for name in %r] + [
        c.reconcile_request_mode(t, mode) for mode in ("guidance", "answer", "unknown")]
json.dump(rows, sys.stdout)
""" % (HELPERS,)


def helper_rows(tree: Path, texts: list[str]) -> dict:
    out = subprocess.run([sys.executable, "-c", _HELPER_SCRIPT, str(tree)], input=json.dumps(texts),
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def executing_pairs() -> set[tuple[str, str, str]]:
    sys.path[:0] = [str(ROOT / "docs/research-log/tools")]
    from traces import traced_rows
    pairs = set()
    for path in glob.glob(str(ROOT / ".netzoo/sessions/*.json")):
        try:
            data = json.loads(Path(path).read_text())
        except ValueError:
            continue
        decision = (data.get("plan") or {}).get("decision") or {}
        users = [m.get("content") for m in data.get("messages", [])
                 if m.get("type") in ("human", "HumanMessage") or m.get("role") == "user"]
        if decision.get("should_execute") and users:
            pairs.add(("session", str(users[-1]), decision["action"]))
    corpus = {c["id"]: c["prompt"] for c in json.loads((ROOT / "tests/routing_scenarios.json").read_text())}
    for path in glob.glob(str(ROOT / "docs/research-log/live-*.json")):
        try:
            data = json.loads(Path(path).read_text())
        except Exception:
            continue
        for row in data.get("results", []) if isinstance(data, dict) else []:
            prompt = corpus.get(row.get("id")) or (row.get("_trace") or {}).get("prompt")
            if prompt and row.get("should_execute"):
                pairs.add(("live", prompt, row["action"]))
    for _path, _index, row in traced_rows():
        trace = row.get("_trace") or {}
        decision = trace.get("decision") or {}
        if trace.get("prompt") and decision.get("should_execute"):
            pairs.add(("traced", trace["prompt"], decision["action"]))
    return {pair for pair in pairs if pair[2] != "no_tool"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, help="checkout of the tree before the change")
    args = parser.parse_args()
    texts = prompts()
    print(f"recorded prompts: {len(texts)}")
    if args.base:
        before, after = helper_rows(args.base, texts), helper_rows(ROOT, texts)
        names = [*HELPERS, "reconcile(guidance)", "reconcile(answer)", "reconcile(unknown)"]
        changes = Counter()
        for text in texts:
            for name, old, new in zip(names, before[text], after[text]):
                if old != new:
                    changes[(name, old, new)] += 1
                    print(f"  {name}: {old} -> {new} | {text[:110]!r}")
        print("helper changes:", dict(changes))
    sys.path[:0] = [str(ROOT / "scripts")]
    from netzoo_agent_core.routing.authorization import forbidding_reason, read_operation_authorization
    pairs = executing_pairs()
    refused = [(source, action, reason, prompt) for source, prompt, action in pairs
               if (reason := forbidding_reason(read_operation_authorization(prompt), action))]
    print(f"executing decisions: {len(pairs)} ({len({p for _, p, _ in pairs})} prompts); "
          f"now refused: {len(refused)}")
    for source, action, reason, prompt in refused:
        print(f"  {source} {action} | {reason} | {prompt[:110]!r}")


if __name__ == "__main__":
    main()
