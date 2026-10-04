"""Log 342 O3 and O5: replay recorded decisions through respond() with and without stage 1.

Usage (repository root): python3 docs/research-log/purpose-contract-2026-10-04/replay_stage1.py
O3: every traced decision (tools/traces.py). A reply that changes on a request
with no study-purpose witness is a failure. Decisions whose reply needs the
response model cannot be replayed offline and are counted apart.
O5: the 27 Log 341 decisions (minimal-pairs-2026-10-04/out/s1-decisions.json),
each checked against Log 342's written expectation.
"""
import json
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "docs" / "research-log" / "tools"))
from langchain_core.messages import HumanMessage  # noqa: E402
from evaluate_routing import ProjectPolicyLoader  # noqa: E402
from netzoo_agent_core.contracts import TaskDecision, WorkflowPlan  # noqa: E402
from netzoo_agent_core.graph import response  # noqa: E402
from netzoo_agent_core.interpretation import practical_notes  # noqa: E402
from netzoo_agent_core.routing.study_purpose import StudyPurpose, study_purpose  # noqa: E402
from traces import traced_rows  # noqa: E402

POLICY = ProjectPolicyLoader(ROOT).load()
STAGE1 = (response.with_study_purpose_reply, practical_notes.study_purpose)


def reply(task, decision, stage1):
    response.with_study_purpose_reply, practical_notes.study_purpose = (
        STAGE1 if stage1 else (lambda result, state, reply: result, lambda task: StudyPurpose()))
    plan = WorkflowPlan(workflow="NO-TOOL", objective=task[:200], decision=decision.model_dump(), status="respond_only")
    state = {"decision": decision.model_dump(), "plan": plan.model_dump(), "messages": [HumanMessage(content=task)],
             "tool_results": [], "evaluation": None}
    out = response.respond(SimpleNamespace(project_policy=POLICY), state)
    return str(out["messages"][-1].content), out.get("reply_kind")


def o3():
    counts = Counter()
    changed_without_witness = []
    for path, index, row in traced_rows():
        trace = row.get("_trace") or {}
        task = trace.get("prompt") or row.get("prompt")
        if not task or not trace.get("decision"):
            continue
        try:
            decision = TaskDecision.model_validate(trace["decision"])
        except Exception:
            counts["invalid_decision"] += 1
            continue
        try:
            base, _ = reply(task, decision, False)
            cand, _ = reply(task, decision, True)
        except Exception as error:  # the response-model path needs a provider
            counts[f"not_replayable:{type(error).__name__}"] += 1
            continue
        purpose = study_purpose(task)
        witnessed = purpose.design is not None or bool(purpose.claims)
        counts["replayed"] += 1
        counts["witnessed"] += witnessed
        if base != cand:
            counts["changed"] += 1
            if not witnessed:
                changed_without_witness.append(f"{path.name}#{index}")
    return counts, changed_without_witness


EXPECT = {
    "A1-1": lambda t: "For your question" in t, "A1-2": lambda t: "For your question" in t,
    "A1-3": lambda t: "For your question" not in t,
    "A2-1": lambda t: "48 samples, 49 PANDA runs" in t and "For your question" in t,
    "A2-2": lambda t: "48 samples, 49 PANDA runs" in t and "For your question" in t,
    **{f"A3-{r}": (lambda t: "For your question" in t and "GIRAFFE" in t.split("For your question")[1]) for r in (1, 2, 3)},
    **{f"A4-{r}": (lambda t: t.startswith('About "') and "untreated comparison group" in t.split("\n\n")[0]
                   and "These all fit;" not in t) for r in (1, 2, 3)},
    **{f"B1-{r}": (lambda t: "**COBRA** — Put the group label" in t) for r in (1, 2, 3)},
    **{f"B3-{r}": (lambda t: "could not validate" not in t.casefold() and "No registered workflow builds a model" in t)
       for r in (1, 2, 3)},
}
UNCHANGED = [f"{key}-{r}" for key in ("A0", "A5", "B2") for r in (1, 2, 3)]


def o5():
    recorded = json.loads((ROOT / "docs/research-log/minimal-pairs-2026-10-04/out/s1-decisions.json").read_text())
    rows = []
    for key, item in sorted(recorded.items()):
        decision = TaskDecision.model_validate(item["decision"])
        base, _ = reply(item["prompt"], decision, False)
        cand, kind = reply(item["prompt"], decision, True)
        if key in UNCHANGED:
            ok = base == cand
        elif key in EXPECT:
            ok = EXPECT[key](cand)
        else:
            ok = None
        rows.append((key, kind, ok, base != cand))
    return rows


if __name__ == "__main__":
    counts, bad = o3()
    print("O3:", dict(counts))
    print("O3 changed without a witness:", len(bad), bad[:10])
    rows = o5()
    for key, kind, ok, changed in rows:
        print(f"O5 {key:6} kind={kind:22} changed={changed!s:5} expectation={'n/a' if ok is None else ('PASS' if ok else 'FAIL')}")
    print("O5 failures:", [key for key, _, ok, _ in rows if ok is False])
