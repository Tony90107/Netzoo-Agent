"""Render every recorded decision's reply and card with one tree's code (display fixes, 2026-10-02).

Usage (from the repository root):

  python docs/research-log/test12-2026-10-02/replay_cards.py <scripts dir> <out.json>

Run it once with a checkout of the base commit's `scripts/` and once with the
working tree's, then compare the two outputs with `--diff base.json cand.json [--keys]`.
Each distinct (prompt, decision) from every traced report under
docs/research-log/ (plain or gzip), and from the local TEST_PROMPTS rounds
(`test10-2026-10-03/**/r*-decisions.json`, added in Log 330), is rendered as
`tests/test_reply_cards.py` does: respond() for the full text and reply kind, then build_reply_card().
Nothing calls a model.
"""
import gzip
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
RESEARCH = ROOT / "docs" / "research-log"


def rows():
    for path in sorted((RESEARCH / "test10-2026-10-03").glob("**/r*-decisions.json")):
        for item in json.loads(path.read_text()).values():
            if item.get("decision"):
                yield item["prompt"], item["decision"]
    paths = sorted({*RESEARCH.glob("**/live-*.json"), *RESEARCH.glob("**/live-*.json.gz")})
    for path in paths:
        if ".provider-error" in path.name or ".unpaired" in path.name:  # void by rule, never analyzed
            continue
        opener = gzip.open if path.suffix == ".gz" else open
        try:
            with opener(path, "rt", encoding="utf-8") as handle:
                report = json.load(handle)
        except (OSError, ValueError):
            continue
        for row in report.get("results", []) if isinstance(report, dict) else []:
            trace = row.get("_trace") if isinstance(row, dict) else None
            if trace and trace.get("decision") and trace.get("prompt"):
                yield trace["prompt"], trace["decision"]


def render(scripts: Path, out: Path) -> None:
    sys.path.insert(0, str(scripts))
    from evaluate_routing import ProjectPolicyLoader
    from netzoo_agent_core.cli.follow_up import build_next_turn_prompt
    from netzoo_agent_core.contracts import HumanMessage, TaskDecision, WorkflowPlan
    from netzoo_agent_core.graph import response as response_module
    from netzoo_agent_core.reply_cards import build_reply_card

    policy = ProjectPolicyLoader(ROOT).load()
    seen, results, errors = set(), {}, 0
    for task, raw in rows():
        key = hashlib.sha256(json.dumps([task, raw], sort_keys=True, default=str).encode()).hexdigest()[:16]
        if key in seen:
            continue
        seen.add(key)
        try:
            made = TaskDecision.model_validate(raw)
            plan = WorkflowPlan(workflow="NO-TOOL", objective=task, decision=made.model_dump(), status="respond_only")
            state = {"decision": made.model_dump(), "plan": plan.model_dump(),
                     "messages": [HumanMessage(content=task)], "tool_results": [], "evaluation": None}
            reply = response_module.respond(SimpleNamespace(project_policy=policy, response_llm=None), state)
            result = {**state, "messages": [HumanMessage(content=task), reply["messages"][-1]],
                      "reply_kind": reply["reply_kind"]}
            card = build_reply_card(result, build_next_turn_prompt(result), policy, task=task)
            results[key] = {"task": task, "kind": reply["reply_kind"], "text": str(reply["messages"][-1].content),
                            "card": card.model_dump(mode="json") if card else None}
        except Exception as exc:  # noqa: BLE001 - counted, never hidden
            errors += 1
            results[key] = {"task": task, "error": f"{type(exc).__name__}: {exc}"[:300]}
    out.write_text(json.dumps(results, ensure_ascii=False))
    print("distinct", len(results), "errors", errors)


def diff(base_path: Path, cand_path: Path) -> None:
    base, cand = json.loads(base_path.read_text()), json.loads(cand_path.read_text())
    assert base.keys() == cand.keys()
    changed = {"text": [], "headline": [], "points": [], "order": [], "descriptions": [], "error": []}
    for key in base:
        b, c = base[key], cand[key]
        if "error" in b or "error" in c:
            if b.get("error") != c.get("error"):
                changed["error"].append(key)
            continue
        if b["text"] != c["text"]:
            changed["text"].append(key)
        bc, cc = b["card"] or {}, c["card"] or {}
        if bc.get("headline") != cc.get("headline"):
            changed["headline"].append(key)
        if bc.get("points") != cc.get("points"):
            changed["points"].append(key)
        bo = [o["label"] for o in (bc.get("choices") or {}).get("options", [])]
        co = [o["label"] for o in (cc.get("choices") or {}).get("options", [])]
        if bo != co:
            changed["order"].append(key)
        bd = [o.get("description") for o in (bc.get("choices") or {}).get("options", [])]
        cd = [o.get("description") for o in (cc.get("choices") or {}).get("options", [])]
        if sorted(map(str, bd)) != sorted(map(str, cd)):
            changed["descriptions"].append(key)
    print("distinct", len(base), "errors", sum("error" in v for v in cand.values()))
    for name, keys in changed.items():
        print(f"{name}: {len(keys)}")
    if "--keys" in sys.argv:
        print(json.dumps(changed))


if __name__ == "__main__":
    if sys.argv[1] == "--diff":
        diff(Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        render(Path(sys.argv[1]).resolve(), Path(sys.argv[2]))
